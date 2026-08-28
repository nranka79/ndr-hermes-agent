# Drive Move-and-Rename Pitfalls & Safe Batch Reorg

Worked through in the Legacy Cataleya document-reorg session (Aug 2026):
31 scanned PDFs moved from `TMP/Legacy` to `Personal/Legacy` (ndr@draas.com),
examined individually, renamed with the date-prefix convention, and a WhatsApp
message delivered with folder + 3 key drawing links shared to a colleague.

## P0 — `files().update()` `addParents`/`removeParents` MUST be comma-joined strings, NOT JSON arrays

The single most destructive gotcha. Google Drive's `files.update` request
accepts `addParents` / `removeParents` as **a comma-separated string of folder
IDs**, not a Python list.

```python
# WRONG — raises HttpError 404 "File not found: [parentId]"
drive.files().update(
    fileId=fid, body={"name": newname},
    addParents=TARGET, removeParents=meta.get("parents"),  # list → 404
    fields="id,name,webViewLink").execute()

# RIGHT — comma-joined string
drive.files().update(
    fileId=fid, body={"name": newname},
    addParents=TARGET,
    removeParents=",".join(remove_parents) if remove_parents else "",
    fields="id,name,webViewLink").execute()
```

Symptoms of the array bug: the whole batch fails mid-run with `404 File not
found: ['<parentId>']` where the offending parent is the folder you're moving
OUT of (it is interpreted as a file id). The `404` is misleading — the file
exists; the param type is wrong.

**Recovery pattern after a near-missed batch:** before re-running, verify each
file's actual `parents` and `trashed` state (`drive.files().get(fileId, fields=
"id,name,parents,trashed")`). If an interrupted run moved some files into a
folder you later trashed, the files inherit `trashed: true` (trashing a folder
trashes its contents). Untrash + re-parent in the recovery pass:
`body={"trashed": False}` combined with the same update call.

## Move + rename in ONE call

Move-and-rename is a single `files().update()` (both `body={"name": ...}` and
`addParents`/`removeParents` together). No need for two round-trips.

## TMP → Personal reorg convention

When the user uploads a batch of documents to `TMP/{Project}` and asks to file
them under `Personal/` with per-document examination + rename:

1. **List the TMP subfolder** — `drive.files().list(q="'<TMP_PROJ>' in parents and trashed = false")`.
2. **Find the Personal/Project target.** Resolve under `My Drive/Personal`
   (folder `0B1Oc8cSaJXPGYkQtYXJDQWVBUVE` on ndr@draas.com). Do NOT blindly
   create a new folder — check `name='<Proj>' and '<PERSONAL>' in parents`
   first; the user may have one already, OR may want you to create exactly one
   (user corrected: "both must be created by you; ensure there is only one").
   If you create one and a duplicate already exists, trash the extra and keep
   a single canonical folder — never leave two same-named folders.
3. **Examine each document** before renaming: `pdftotext -l 3` for text-layer
   docs; `pdftoppm` + tesseract for image-only scans. Identify the real doc
   type (brochure vs sanctioned plan vs NOC vs court order) — don't trust the
   upload filename.
4. **Rename** with the `YYYYMMDD_{Project}_{Type}_{Parties}.pdf` convention,
   disambiguating duplicates with `_dup1`.
5. **Move+rename in one `files().update()`** per the P0 fix.
6. Verify final state — list target folder, confirm TMP is empty.

## Verify a batch move

After the run, list the target folder and count files == expected count; list
the source folder and confirm it's empty. Confirm no files are stranded in a
trashed folder.
