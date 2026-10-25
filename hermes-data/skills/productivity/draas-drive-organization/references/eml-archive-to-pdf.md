# Raw .eml dump → readable PDFs (+ attachments) — mailbox-export conversion

Trigger: "there is no way for me to see the email files / I don't have a viewer" after a
bulk `.eml` dump lands in an evidence pack. NDR wants each email as a **readable PDF**,
its **attachments extracted**, one **folder per email**, plus a top-level index.

Verified 2026-09-10 on the Mirabilis/Behera evidence pack: **1,989 .eml across 4 accounts
(ndr_draas 1,218 / sales1 767 / ndr_ahfl 2 / ndr_gmail 2), 5.5 GB source → 3.8 GB output,
1,989 PDFs + 1,989 email.txt, 861 emails with attachments (1,506 attachment files), 0 errors.**

## Answer NDR's ideation question first

He asks "first let's ideate — is that possible, how, what tool?" Answer with the tool
choice + the output shape, then run it. Do not just describe.

## Tool choice

| Job | Tool | Why |
|---|---|---|
| email HTML → A4 PDF | **WeasyPrint** | already installed; embeds base64/`cid:` inline images; faithful header/body/quote render |
| split headers/body/attachments | stdlib `email.parser.BytesParser(policy=policy.default)` | no deps |
| sanitize pathological HTML | BeautifulSoup (`html.parser`) | depth-capping fallback layer |
| parallel fan-out | `ProcessPoolExecutor(max_workers=3)` | ~0.12 s/email measured |

A full headless Chrome may be present but the ARM build core-dumps on x86 — do not rely on it.

## Output layout

```
<out>/<account>/<NNNN_YYYYMMDD_HHMM_sender_subject>/
    <same name>.pdf      <- readable render (headers table + body + attachment list)
    email.txt            <- plain-text dump (grep target)
    Attachments/         <- every attachment as its original file
<out>/INDEX.csv
```

`INDEX.csv` columns: `account, folder, src, status, date, from, to, subject, n_att,
attachments, att_bytes, behera, pdf, error` — one row per email, so the shortlist can be
filtered without opening PDFs.

Attachment filename collisions get a `_2` suffix; sanitize names the same way as folders.

## THE critical fix — WeasyPrint `RecursionError` on deeply-nested HTML

Marketing/newsletter emails (nested `<div>`/`<table>` chains) blow WeasyPrint's layout
recursion. Symptom in the error log: `RecursionError: maximum recursion depth exceeded`,
traceback repeating through `weasyprint/css/__init__.py` `__missing__` → `parent_style[key]`.
This killed 122/1,989 emails on the first pass.

Three-layer render, in order (layer 1 fixed **all** 122 — cost nothing else):

```python
import sys, threading

def render_in_thread(fn, stack_mb=512, recursion=1_000_000):
    """Run fn() in a thread with a big C stack — deep layouts exhaust the stack, not just
    sys.getrecursionlimit()."""
    out = {}
    def runner():
        old = sys.getrecursionlimit()
        sys.setrecursionlimit(recursion)
        try: out["ok"] = fn()
        except BaseException as e: out["err"] = e
        finally: sys.setrecursionlimit(old)
    try: threading.stack_size(stack_mb * 1024 * 1024)
    except (ValueError, RuntimeError): threading.stack_size(64 * 1024 * 1024)
    t = threading.Thread(target=runner); t.start(); t.join()
    if "err" in out: raise out["err"]
    return out.get("ok")
```

- **Layer 1** — big-stack thread (above). Fixes the failures; **raise the limit AND the stack**,
  the recursionlimit alone is not enough.
- **Layer 2** — `sanitize_html(doc)`: BeautifulSoup, drop `script/noscript/iframe/object/embed/
  meta/link/base`, then repeatedly `unwrap()` elements nested deeper than ~70 until stable.
  Keeps content, drops the boxes.
- **Layer 3** — render the `email.txt` plain text as a `<pre>` PDF. Always works; never leave a
  failed email with no render.

## Repair pass (don't re-run the whole job)

Write a repair script that walks the source tree, recomputes each target path, and reprocesses
only emails whose PDF is missing or <800 bytes. Idempotent — safe to re-run.

Measure before committing: run `--limit 120` against the real tree to get s/email and scale the
output size (the 122-file repair took ~1 min at 3 workers).

## Verification (do all of these)

```bash
find <out> -mindepth 3 -maxdepth 3 -name "*.pdf" -size +800c | wc -l   # email renders
find <out> -name email.txt | wc -l
find <out> -name ERROR.txt | wc -l                                     # must be 0
```

- **`-maxdepth 2` under-counts to ~3** — email PDFs live 3 levels down (`out/account/folder/x.pdf`).
  If your count looks impossibly low, it is the depth, not the job.
- **`email.txt` count ≠ email count** only when `.txt` attachments exist (1,989 txt total vs
  1,867 `email.txt` on the first pass) — check which before declaring missing output.
- After a repair pass, `INDEX.csv` rows still say `error` and have an **empty `pdf` field**
  (the error path never sets it). Rebuild status by deriving the path from `account` + `folder`:

  ```python
  pdf = os.path.join(out, acct, folder, folder[:110] + ".pdf")
  if os.path.exists(pdf) and os.path.getsize(pdf) > 800: row['status'] = 'ok'
  ```

- **A failed smoke test leaves a stray folder.** The error handler `mkdir`s the output dir even
  when the *source* path was wrong (FileNotFoundError), producing a near-identical folder
  holding only `ERROR.txt`. `safe_name` does NOT collapse spaces, so a path mistyped with
  ` - ` instead of `_-_` yields a *second* folder beside the real one. Delete strays before
  reporting counts.

## The entity flag is a filter, not a verdict

Flagging (`Sabyasachi|Behera|B1-203|Damayanthi|6093` over subject + from/to + attachment names
+ first ~20k of body) surfaced 236/1,989 — riddled with false positives:

- same surname, different customer (Ipsita Behera, flat A-1002)
- a 2017 sales lead also called Sabyasachi
- a brand homonym (Tata CLiQ "Sabyasachi Fine Jewellery" — unrelated to the client)
- threads that merely *quote* the person (E-302 / other units)
- amounts or IDs that collide (an Aadhaar number containing `6093`)

Always read ±70 chars of context around each hit, then hand-prune to the true cluster. Report
the flag as a search aid and name the noise you saw — never present the raw flag count as the
answer.

## Publishing the tree to Drive (the follow-up NDR always asks for)

The conversion produces a local tree; NDR's next message is inevitably *"where are the
PDFs? put them in the evidence folder on drive, I need to see the folder structure."*
Don't wait to be asked twice, and don't wait for the upload to finish before answering —
give him the tree diagram, file counts and target link immediately, then run the upload in
the background.

Layout that works: a **`Readable_Emails/` subfolder inside each account folder on Drive**,
mirroring the local per-email folders (PDF + `email.txt` + `Attachments/`), with the raw
`.eml` files left in place alongside. Also push `INDEX.csv` to the pack root.

Mechanics (process sharding, the parent-pre-list optimisation, throughput, verification,
and the segfault trap) are in **`references/bulk-drive-tree-mirror-upload.md`**.

## Other pitfalls

- **Remote images are placeholders, not fetched.** WeasyPrint does not download Gmail
  trackers/spacer pixels; `cid:`-embedded images DO render. Correct for a compliance/record
  pack — say so explicitly rather than letting NDR discover it. Only switch renderers if he
  actually wants remote images pulled.
- **Never equate attachment count with email count.** 861 of 1,989 emails had attachments;
  folder/attachment counts differ legitimately.
- **Trash nothing.** This pipeline only writes new output; it must never touch the source
  `.eml` tree.
- **Check disk before starting** (`df -h`). 5.5 GB source produced 3.8 GB output; the VPS runs
  tight.
- Deliver the counts + location + the flag caveat, then offer the next step (prune the folders
  to the genuine cluster, or zip the shortlist for Drive upload) rather than doing it unasked.
