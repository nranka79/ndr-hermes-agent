# Mirroring a large LOCAL tree into Drive (thousands of folders + files)

Trigger: *"where are the PDFs created? put them in the evidence folder itself on drive;
I need to see the folder structure."* — the user wants a locally-built tree (email packs,
dossier output, converted archives) **published into an existing Drive folder, structure
preserved**, so they can browse it.

Verified 2026-09-10: 1,989 email folders → **2,850 Drive folders + ~5,500 files
(~3.8 GB)**, completed in ~20 minutes with 8 shard processes, **zero failures**.

Distinct from `bulk-upload-tmp-skip-existing.md` (a handful of files into one TMP
subfolder). This is the *thousands-of-items, nested-tree* case.

## Target layout — mirror beside the originals, don't replace them

The raw source (e.g. `.eml` dumps) already lives in per-account Drive folders. Publish the
converted tree **as a `Readable_Emails/` subfolder inside each account folder**, so the
original and the readable form sit side by side:

```
20260909_Behera_EvidencePack/
  README.md
  INDEX.csv                     <- also push the top-level index/manifest here
  Manifests/
  Documents_Collected/
  Emails_NDR_ndr@draas.com/
    (1,218 original .eml files)
    Readable_Emails/
      0000_20140612_1553_Sender_Subject/
        0000_...\.pdf            <- readable render
        email.txt
        Attachments/
          <original attachment files>
  Emails_Bharat_sales1.blr@draas.com/Readable_Emails/...
```

Why a subfolder rather than dumping 2,400 items at the account level: a flat listing of
1,218 `.eml` + 1,218 folders is unusable. `Readable_Emails/` keeps both forms discoverable.

## Architecture — three scripts, run as one nohup job

1. **Prep script** — creates the per-account target folders and writes their IDs to JSON
   (`/tmp/eml_targets.json`). Run once, serially. Prints each `account -> folderId`.
2. **Shard uploader** — takes `--account X --shard i/N`, mirrors its slice. Process-parallel.
3. **Orchestrator** — a small bash script (`nohup`) that launches N shards per account,
   `wait`s on the PID array, then moves to the next account.

```bash
run_account() {
  local acct=$1 nshards=$2; local pids=()
  for i in $(seq 0 $((nshards-1))); do
    $PY $SCRIPT --account $acct --shard $i/$nshards --logfile /tmp/upload_$acct.log &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait $p; done
}
run_account ndr_draas 8      # 1,218 emails
run_account sales1 6         # 767
run_account ndr_gmail 2
run_account ndr_ahfl 1
```

Launch with `terminal(background=true, notify_on_complete=true)` and tail the per-shard
logs — do **not** block on it.

## CRITICAL — shard across PROCESSES, not threads

`googleapiclient` inside a `ThreadPoolExecutor` **segfaulted** (exit 139, "dumped core")
within a second of the first request — even at `--workers 2`. The identical code with
`--workers 1` (fully serial) completed fine.

**Pattern: one shard = one process.** This is not a workaround tax — it also sidesteps the
GIL and gives each process its own SSL/HTTP connection. Concurrency = number of processes.

## The optimisation that makes this fast — pre-list the parent ONCE

Naive per-file existence checking does a `files().list()` before every upload — that
doubles-to-triples the API cost and dominates runtime.

Instead, at shard start, page through **the target parent's existing children once** and
build a name set:

```python
def existing_children(parent):
    names, token = set(), None
    while True:
        res = drive.files().list(
            q=f"'{parent}' in parents and trashed = false "
              f"and mimeType = 'application/vnd.google-apps.folder'",
            fields='nextPageToken, files(id,name)', pageSize=1000, pageToken=token).execute()
        names.update(f['name'] for f in res.get('files', []))
        token = res.get('nextPageToken')
        if not token: break
    return names
```

Then per email: `if name in have: skip` → else **exactly 1 folder-create + N uploads, no
lookups at all**. Gives idempotent resume *and* minimum API calls in one mechanism.

Also: only use resumable upload for files >5 MB —
`MediaFileUpload(path, mimetype='application/octet-stream', resumable=size > 5*1024*1024)`.
Small files upload ~3x faster non-resumable.

## Measured throughput

- **~0.22–0.28 emails/s per shard** (2–5 files + 1–2 folders each)
- 8 shards ≈ **2 emails/s** → 1,218 emails in ~10 min
- Drive quota is **not** the bottleneck (12,000 queries/60 s); parallelism is bounded by
  the host, so 6–8 shards is the practical sweet spot
- Retry wrapper must swallow `429, 403, 500, 502, 503, rateLimit, backendError, timed out, SSL`
  with exponential backoff — transient 5xx/SSL blips are normal at this volume

## Verification (do these, in this order)

```bash
pgrep -fc upload_shard.py                      # shards still alive
grep -c "SHARD DONE" /tmp/upload_<acct>.log    # per-shard completion
tail -3 /tmp/upload_<acct>.log                 # files=/dirs=/skip=/fail=
```

Then confirm from **Drive**, not from the local tree:

- count child folders under the target (`files().list` paged) vs local folder count
- open ONE sample email folder and print its children + the `Attachments/` children
- confirm `INDEX.csv` / manifest landed at the pack root

## Pitfalls

- **Don't derive the account/group from `relpath` when the source root is the account
  itself.** Passing `<out>/ndr_draas` as the src root made every relpath a bare filename,
  so the grouping defaulted to `misc`. Pass the **parent** root (`<out>`) so
  `ndr_draas/...` survives — or pass the target folder ID explicitly (what the final
  script does).
- **Pre-create shared parent folders in the prep step.** If every shard calls
  `mkfolder(account)` concurrently, Drive allows duplicate folder names and you can end up
  with two `Readable_Emails` folders. Create once, pass the ID via JSON.
- **`files().list` matching is name+parent, not ID.** Quote-escape names (`'` → `\'`) before
  building the `q=` string — email subjects/folder names contain apostrophes routinely.
- **A freshly created folder is empty** — skip all existence checks for its children. Only
  the resume path needs the pre-listed name set.
- **`find <out> -name "*.pdf" | wc -l` counts attachment PDFs too.** 1,989 emails produced
  3,002 PDFs (1,989 renders + 1,013 attachment PDFs). Don't read that as a fan-out bug —
  scope with `-mindepth 3 -maxdepth 3` for email renders only.
- **`nohup` + `&` is fine here** (bash orchestration script), but the *job* must be started
  via `terminal(background=true, notify_on_complete=true)` — never a bare foreground call.
- **Large uploads take ~20 min — answer the user's structural question immediately** (the
  tree diagram + counts) rather than waiting for completion to report anything.
