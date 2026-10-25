# Bulk upload to Drive (many files → TMP folder)

> **Maintenance note:** `SKILL.md` for this skill is at the ~100k character
> limit, so body edits are REJECTED until it sheds content. Put new material in
> `references/*.md` (like this file) and keep SKILL.md edits to one short
> pointer line. If you have a substantive addition for the main body, split an
> existing section out to a reference file first.

**Trigger:** "download all the images from <site> into a folder on my TMP drive",
or any task producing dozens-to-hundreds of local files that then need to land
in a Drive folder. Verified 2026-09-19 with a 727-file / 2.3 GB image haul
(11 subfolders) into a new `Uchalagollahalli` folder inside TMP.

## The identity pitfall — use `gws.py`, not `build_service`

A standalone Python script launched as a **subprocess** has no Hermes session
identity, so the vault cannot resolve which user's token to hand out:

```
tools.gws_vault_client.VaultNoTokenError:
No google token for user ndr-7449813913. Authorize first.
```

This is an **identity** failure, not an auth failure. Do NOT respond by sending
the user an OAuth link or re-authorizing — the account is fine (verify with the
`resolve` op below, which shows `has_token: true` for all three accounts).

**Use the wrapper**, which carries the session through:

```bash
python3 /opt/data/gws.py <op> google-draas '<json-args>'
python3 /opt/data/gws.py resolve                 # list accounts + token status
python3 /opt/data/gws.py drive_create_folder google-draas '{"name":"X","parent":"<parent-id>"}'
python3 /opt/data/gws.py drive_upload google-draas '{"path":"/tmp/a.jpg","parent":"<folder-id>"}'
python3 /opt/data/gws.py drive_delete google-draas '{"file_id":"<id>"}'
```

`build_service(...)` is correct **inside** a normal agent tool call
(`execute_code` / the native gws tools) where the session is present — it's only
the detached-subprocess case that needs the wrapper.

### Direct `build_service` subprocess variant (verified 2026-10-08)

Binary image uploads (e.g. a 115-photo reference library) work from a
standalone script too, when run with the Hermes venv python so `tools` and its
vault access resolve:

```bash
/opt/hermes/.venv/bin/python3 upload_script.py
```

with `sys.path.insert(0, "/opt/hermes")` at the top, then
`from tools.gws_auth import build_service` and
`from googleapiclient.http import MediaFileUpload`. The vault resolves the
token correctly in this context (the identity failure above happens in other
interpreters / without the venv). Per-file calls:

```python
svc = build_service("drive", "v3", service_name="google-draas")
media = MediaFileUpload(path, mimetype=MIME.get(ext, "application/octet-stream"))
f = svc.files().create(body={"name": name, "parents": [parent_id]},
                       media_body=media, fields="id,name,size").execute()
```

MIME by extension: jpg/jpeg→image/jpeg, png, webp, gif, md→text/markdown,
json→application/json. Write the whole run to a file (not heredocs — see
Pitfall C), save the returned id map to JSON so the link pass needs no
re-search, and verify by re-listing children per subfolder afterwards
(three-counts-agree rule below still applies).

## The script shape that works

A bash driver + the wrapper per file. Two phases, because folder creation and
upload are separate calls:

```bash
GWS="python3 /opt/data/gws.py"
PARENT=<tmp-subfolder-id>
: > subfolders.txt

# Phase 1 — one Drive subfolder per local directory
for d in "$ROOT"/*/; do
  name=$(basename "$d")
  out=$($GWS drive_create_folder google-draas "{\"name\":\"$name\",\"parent\":\"$PARENT\"}" 2>&1 | tr -d '\n')
  fid=$(printf '%s' "$out" | sed -n 's/.*"id": "\([^"]*\)".*/\1/p')
  printf '%s\t%s\n' "$name" "$fid" >> subfolders.txt
done

# Phase 2 — upload, JSON-encode the path (filenames contain spaces)
while IFS=$'\t' read -r name fid; do
  for f in "$ROOT/$name"/*; do
    res=$($GWS drive_upload google-draas \
      "{\"path\":$(python3 -c 'import json,sys;print(json.dumps(sys.argv[1]))' "$f"),\"parent\":\"$fid\"}" 2>&1)
    printf '%s' "$res" | grep -q '"status": "uploaded"' || echo "$f FAILED" >> failed.txt
  done
done < subfolders.txt
```

Points that matter:
- **JSON-encode the file path** — filenames with spaces break naive interpolation.
- Success test is `'"status": "uploaded"'` in the returned JSON.
- **Don't trust the return string alone for anything critical** — spot-check by
  re-listing the folder's children afterwards.
- Print a `name N/total` progress line every 50 files; the job runs for many
  minutes and silent output looks like a hang.
- Persist `subfolders.txt` — it's the resume map (folder name → Drive id) if the
  run is interrupted, and re-running phase 1 blindly creates duplicate folders.

## Runtime characteristics

- ~727 large JPEGs ≈ **320-360 files in ~10 min** through the wrapper. Run as
  `terminal(background=True, notify_on_complete=True)`; a foreground call dies
  at the 180 s timeout.
- Zero failures is achievable (727/727 here) — if you see accumulating failures,
  stop and check the wrapper's stderr rather than letting it churn.
- The wrapper prints `[]` (empty JSON) for a `drive_search` with no matches —
  that is a legitimate empty result, not an error.

## Pitfall A — verify a *just-created* folder by ID, never by a remembered parent

**Do not assume the folder id you have in the script is the folder you just
created.** On the 2026-09-19 haul the id used for the upload loop was the **TMP
root** id, not the new `Uchalagollahalli` child — so a "verify the folder"
pass listed the *entire TMP root* (696 files, dozens of unrelated sibling
folders) instead of the 11 subfolders being verified. The output looked
plausible at a glance, which is what makes it dangerous.

Worse: **TMP already contained an unrelated pre-existing folder with the same
name** (`Uchalagollahalli`, 13 images from an earlier RERA/plans dump). So
"find the folder by name" is also ambiguous — a `name contains` search can
return the stale one.

Do all three of these before verifying or uploading:

1. **Capture the id from the create call's own output** — parse `"id"` out of
   the `drive_create_folder` return, don't carry a parent id forward by hand.
2. **Disambiguate by name *and* count *and* creation time.** Locate the folder,
   then confirm `createdTime` is today's run and the parent is TMP:

```python
r = svc.files().list(
    q="name contains 'X' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    fields="files(id,name,createdTime,parents)", pageSize=50).execute()["files"]
for f in r:
    par = svc.files().get(fileId=f["parents"][0], fields="id,name").execute()
    print(f["name"], f["id"], f["createdTime"], "parent:", par.get("name"))
```

3. **Sanity-check the shape of what you listed.** If a "subfolder count" comes
   back as dozens of mixed files and `.md`/`.wav`/`.pdf` siblings, you are
   looking at TMP root, not your haul. Stop and re-locate.

`drive_search` via the wrapper is NOT a general Drive query — it wraps your
string in `fullText contains '...'`, so a `'<id>' in parents` query returns
`HttpError 400 Invalid Value`. Use `build_service` inside a normal agent tool
call (session present) for real `q=` queries; `drive_search` is for text search.

**There is no `drive_list` operation on the wrapper or the bridge.** The bridge's
dispatchable set lives in `_OWN_OPERATIONS` (`gws_skill_bridge.py`) plus the
underlying skill's own functions — `drive_get`, `drive_search`,
`drive_create_folder`, `drive_upload`, `drive_delete`, `drive_share`,
`drive_download`. Calling `python3 /opt/data/gws.py drive_list ...` raises
`AttributeError: Unknown gws_skill_bridge operation: 'drive_list'`. When you need
a real `q=` listing with fields/pagination, three options in order of
preference:

1. `build_service("drive", "v3", service_name="google-draas")` **inside** an
   `execute_code` tool call (session present) — full Drive API, best for the
   verification and link passes.
2. The native `gws_*` tools.
3. The wrapper's `drive_get` for a single known file id.

Also: a `drive_search` that filters by name does a **full-text match, not a name
match** — searching for `Uchalagollahalli` returned an unrelated spreadsheet
(`NDR_Master_Task_Tracker`) while the actual folder was a different id. Never
conclude "the folder doesn't exist" from a `drive_search` miss; re-query by
`q="name = '...'"` via `build_service`.

## Pitfall C — heredocs and inline Python quoting inside `execute_code` shells

Two recurring time-sinks when driving this from `execute_code`:

- **`terminal("... <'")` heredoc inside an already-quoted command stalls.** A
  `python3 - <<'PY'` heredoc embedded in a loop hung the upload driver and had to
  be killed (which is what created the duplicate-folder mess in Pitfall B). Write
  the script to a file with `write_file` and run `python3 /path/script.py`
  instead.
- **Nested-quote gymnastics in `python3 -c` break Drive queries.** Building
  `"'%s' in parents" % s["id"]` through a shell-escaped one-liner produced
  `KeyError: '"\'id\'"'`. Same fix: `write_file` the script (plain Python, no
  shell escaping), then run it. The lint on `write_file` catches syntax errors
  before the run.

Rule of thumb: **anything longer than a single short command goes in a file, not
in a quoted shell argument.**

## Pitfall B — an aborted run silently duplicates folders and leaves partials

On the same run an earlier, **stalled and killed** upload driver had already
created some subfolders before dying. The fresh run created a *second* copy of
those names. Result verified after the fact:

- `Ananta-Bliss-Bale` existed twice, **60 files each** (both complete).
- `Ananta-Bliss-Taksu` existed twice — one folder with **67** files, the other
  with only **9** (the partial from the aborted run).

Net: the folder listing read `13 subfolders / 796 images / 2.63 GB` against an
expected `11 / 727 / 2.45 GB`. **A count that is higher than expected is as much
a bug signal as one that is lower** — duplicates, not just gaps.

Cleanup recipe (delete the duplicate, then the folder):

```python
for fid in duplicate_folder_ids:
    for f in svc.files().list(q=f"'{fid}' in parents and trashed=false",
                              fields="files(id)", pageSize=1000).execute()["files"]:
        svc.files().delete(fileId=f["id"]).execute()
    svc.files().delete(fileId=fid).execute()
```

Decide which copy to keep by **file count vs the local source**, and
`createdTime` (earlier = the stale aborted run). To prevent the duplicate in the
first place: persist `subfolders.txt` as the resume map and, on restart, REUSE
the ids in it rather than re-running phase 1 blindly.

## Final verification — three counts must agree

Before declaring done, assert this identity and report it:

**local files == Drive files, per subfolder, and in total.**

```python
total = 0
for f in top_level_subfolders:
    n = count children of f            # paginate: orderBy="name", nextPageToken
    total += n
    print(f["name"], n)
print("TOTAL", total)
```

Flag any subfolder whose Drive count ≠ local count. In this session that check
is exactly what caught the 9-file partial. Also confirm subfolder count ==
number of source listings (11), and re-check the folder-name disambiguation
above if it doesn't.

## Structure convention


Mirror the source organisation: one TMP folder for the whole haul, one
subfolder per source entity (per listing / per property / per project), files
inside. Confirm the per-folder file counts against the source before declaring
done, and report the local path + Drive folder id so a follow-up move out of TMP
is cheap.

## Reporting the haul back to NDR — clickable links, flat list

After any bulk Drive haul, expect NDR to come back with **"give me links to the
folder where the subfolders and the images are created"** (asked verbatim
2026-09-19). Deliver it pre-emptively in the completion message so the follow-up
never happens. What he wants:

- **One link to the main folder** (the TMP folder for the whole haul) —
  `https://drive.google.com/drive/folders/<top-folder-id>`, stated first.
- **One link per subfolder, with its file count on the same line** — so he can
  eyeball that each listing/property is complete without opening anything.
- Construct from the folder `id` alone. The bare
  `https://drive.google.com/drive/folders/<id>` form needs no `webViewLink`
  fetch, no sharing call, and works for any folder in the account.

Produce it from ids, not by re-searching by name (same-name ambiguity — see
Pitfall A). One pass, top-level then children:

```python
top = svc.files().get(fileId=TOP_ID, fields="id,name").execute()
print(top["name"], "https://drive.google.com/drive/folders/" + top["id"])
subs = svc.files().list(q="'%s' in parents and trashed = false" % TOP_ID,
        fields="files(id,name,mimeType)", orderBy="name", pageSize=200).execute()["files"]
for s in subs:
    n = len(svc.files().list(q="'%s' in parents and trashed=false" % s["id"],
            fields="files(id)", pageSize=1000).execute()["files"])
    print(s["name"], n, "https://drive.google.com/drive/folders/" + s["id"])
```

Two further points from that exchange:

- **These counts satisfy the three-counts-agree verification in the same
  breath.** The link pass IS the live post-cleanup verification — run it after
  duplicate cleanup, never quote counts from before the cleanup.
- **Name the folders so the brand/project leads**, not the unit
  (`Ananta-Bliss-Bale`, not `Bale`). The 2026-09-19 haul was uploaded with
  unit-first names and had to be renamed after the fact; get it right at creation
  so the reported links are stable.
