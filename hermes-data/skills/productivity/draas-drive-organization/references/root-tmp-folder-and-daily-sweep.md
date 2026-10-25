# Root TMP Folder + the "Clean Up Everything I Made Today" Sweep

## The root TMP folder id — verify it, it has changed

**Current TMP folder id: `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`** (verified 2026-09-14).

The older id `0B1Oc8cSaJXPGMFFCRWtqQ2lqSDQ` returned **404** on lookup as of
2026-09-14 — it no longer exists. Do not trust a hardcoded id from a stale
reference or an older session note.

**Do this instead:** list root folders and match on the NAME.

```python
r = drive.files().list(
    q="mimeType='application/vnd.google-apps.folder' and 'root' in parents and trashed=false",
    fields='files(id,name)', pageSize=200).execute()
tmp = next((f['id'] for f in r['files'] if f['name'] == 'TMP'), None)
if not tmp:
    tmp = drive.files().create(
        body={'name': 'TMP', 'mimeType': 'application/vnd.google-apps.folder'},
        fields='id').execute()['id']
```

Recreation is cheap and safe. A missing TMP folder is a config state, not a
blocker — create it and file into it.

## Sweep-then-file pattern

Trigger: *"all the files created today, rename them using my naming convention,
and if there's no appropriate folder put them in temp so we don't pollute My
Drive root."*

1. **Enumerate files created today, and PAGINATE.** A `files().list` on
   `createdTime` caps around 100 results on the first page. The artifact created
   *latest* in the day is exactly the one the first page misses — that was the
   vendor shortlist sheet and the renders in the 2026-09-14 sweep (118 files
   total). Always follow `nextPageToken` to the end before classifying.
2. **Resolve every root-level file's PARENT FOLDER BY ID**, never by guessing
   from the filename. `files().get(fileId=..., fields='parents')` then resolve
   each parent id to a name. The parent name is what tells you whether a correct
   home already exists.
3. **Only genuinely homeless files go to TMP.** A file whose correct
   entity/project folder ALREADY EXISTS gets moved straight there — do not park
   it in TMP to defer the decision. TMP applies only when there is no appropriate
   folder anywhere.
   - 2026-09-14 worked example: the procurement/vendor-shortlist sheet had **no
     Procurement folder under any entity** → TMP was correct. The NVIDIA
     Inception pitch deck had a home in the **O3 Infotech** folder → moved
     directly there, not via TMP.
4. **Consolidate a scattered topic into ONE folder.** When one subject's files
   sit under two different parents, pull them together so the research pack
   travels as a unit. 2026-09-14: four Westbury/Kagganur PDFs were extracted from
   the PLS folder into the Palm Paradise research folder.
5. **Rename per convention:** `YYYYMMDD_<Project>_<Descriptive_Name>`.

## Gotchas hit during the sweep

- **`ownerNames` is not a valid field** in a v3 `files().list` `fields=` string in
  this environment — including it makes the call fail. Drop it; resolve
  ownership/parents via a separate `files().get(fields='parents')` when needed.
- **A file can be a "root-level" item while genuinely belonging to a subfolder
  elsewhere** — which is why step 2 resolves the parent rather than trusting that
  "at root" means "no home exists".
- **TMP → project moves need all FOUR parent operations**, not just
  `addParents`: set `addParents=<target>` and `removeParents=<source>` in one
  `files().update`, then re-read `parents` to confirm the move landed.
- **Verify after every move** by re-listing the target folder and checking the
  item is present with the new name, and that the source no longer holds it.

## URL-encoding trap for filenames with spaces

When re-registering an attachment (e.g. onto a Kelsa record) whose filename
contains **spaces**, store the **fully URL-encoded** URL. A raw-space filename
produced a double-encoded, broken download link on the Kelsa WO record — the link
rendered in the UI but 404'd on click (caught and fixed 2026-09-14). The stored
form must match how the platform originally encoded it.
