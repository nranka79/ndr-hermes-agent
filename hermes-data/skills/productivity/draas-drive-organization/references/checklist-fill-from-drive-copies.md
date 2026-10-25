# Fill a document checklist from a Drive master folder (COPIES in a new share folder)

Verified 2026-10-07 (Sarthak admin3.blr): master folder "Master data for all Projects
Pre Approval" (4 project subfolders) + `DRA_Realty_Document_Checklist.xlsx` with 33
rows of requested documents. User instruction: check every row against the master
folder, and **do NOT paste the original master links into the checklist** — copy the
available documents into a NEW folder and link the COPIES, so only the new folder is
shared externally.

## Key technique: xlsx on Drive is NOT a native Sheets file

- `spreadsheets().get()` on an .xlsx returns:
  `HttpError 400 ... "This operation is not supported for this document. The document
  must not be an Office file."` — do not retry the Sheets API.
- Instead: `drive.files().get_media(fileId=...)` → save bytes → parse with **openpyxl**
  (available in the Hermes venv; `load_workbook('/tmp/x.xlsx', data_only=True)`).
- To edit and re-upload IN PLACE (keeping the original share link): edit the workbook,
  `wb.save()`, then `drive.files().update(fileId=..., media_body=MediaFileUpload(...))`.
  The existing `ouid` share link and permissions survive.

## Drive shortcut trap (blocked copies)

A master folder may contain **shortcuts** (`mimeType: application/vnd.google-apps.shortcut`),
not real files. `list` returns `shortcutDetails.targetId` etc., BUT the target file may
not be readable by the session user:

- Copying the shortcut id fails or copies a useless stub; copying the target id returns
  `HttpError 404 File not found` when the session account lacks access to the target.
- Probe first: `files().get(fileId=target_id, fields='id,name,owners')` — 404 means the
  copy will fail. Diagnose per-file, then tell the user the doc EXISTS but the underlying
  file isn't in their account's access (owner must grant access or move real copies into
  the master folder). Don't silently leave those rows blank or claim they're missing.
- In the share run here: all 8 Ranka Udaya rows were shortcut-blocked; Amber + Oasis
  (real files) copied fine, 16 rows marked Yes.

## Checklist row-map pitfall

Checklist sheets have **merged banner rows** (A:G). `openpyxl` exposes them as
`MergedCell` (read-only `value`). You cannot iterate blindly — build an explicit
row→item map from the actual layout (header at row 4, banners at 5/13/18/28/38, item
rows 6–11 / 14–16 / 19–26 / 29–36 / 39–46 in this file). Writing to a merged cell raises
`AttributeError: 'MergedCell' object attribute 'value' is read-only`.

## Copy & fill recipe (worked)

1. Walk the master folder tree with `list(q="'<folder>' in parents and trashed=false",
   pageSize=300, fields='files(id,name,mimeType,size,shortcutDetails)')`, recurse into
   `application/vnd.google-apps.folder`, keep shortcut targets.
2. Build a selection map: checklist item → candidate files by keyword match on name
   (project-scoped). Keep the mapping data-driven and print candidates for eyeball check.
3. Create ONE new root folder (`parents: ['root']` — a master folder shared into the
   account may report no parents, so create at root) + one subfolder per checklist row:
   `f"{item} {title}"`.
4. Copy with `files().copy(fileId=src, body={'name': f"{item}_{name}", 'parents': [sub]})`
   — resolves shortcut to real file when the target IS accessible.
5. Fill the xlsx columns D (Available? Yes/No/Yes*), E (link to the COPY subfolder —
   `https://drive.google.com/drive/folders/<id>`), F (remarks), G (Last Updated);
   green fill for Yes, orange for No/Yes*.
6. Re-upload in place via `files().update`; verify permissions (`anyone writer` is how
   these checklist files are often shared).

## Deliverable reporting

Give the user: share-folder link, checklist link, status counts (Yes / Missing / Blocked),
the exact missing list, and the blocked-shortcut explanation with the fix (grant access).
Do NOT paste master-folder links anywhere in the deliverable — the user's share intent
is the point of the copy step.