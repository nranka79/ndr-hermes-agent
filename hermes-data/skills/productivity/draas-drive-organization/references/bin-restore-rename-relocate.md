# Bin (Trash) Restore → Rename → Relocate

Workflow for "I deleted it, it's in the bin, restore it but put it in the
right folder and rename it" (NDR pattern, e.g. Ranka Iris marketing
collaterals, 2026-08-31).

## Recipe

1. **Find it in trash** — `files().list(q="trashed=true and name contains '<X>'", fields='files(id,name,mimeType,parents,modifiedTime)')`. Deleted folders keep their child files with `parents=[folder_id]` and `trashed=true` — the children are listed too, so you get a full inventory in one query.
2. **Restore** — `files().update(fileId=<id>, body={'trashed': False})`. Just flipping the flag restores the whole folder; children come back with it.
3. **Rename** — `files().update(fileId=<id>, body={'name': '<new name>'})`. NDR's naming rule applies (YYYYMMDD_Entity_Description for new artifacts, but for renamed legacy collateral folders a plain descriptive name like `Ranka Iris - Ninth Floor Collaterals` is what he asked for — he said "don't call it Harsha Naidu, just call it ninth floor related collaterals").
4. **Move** — `files().update(fileId=<id>, addParents=<target>, removeParents='root')` (or the old parent id).
5. **Verify children survived** — list `'<folder_id>' in parents` and count; report count + key files + share link.

## Critical pitfall — restored folder must land in an NDR-OWNED target

The restored property is owned by **ndr@draas.com** (the trash on another
account behaves differently). When NDR says "put it in the Ranka Iris
folder", do NOT pick a folder owned by another DRAAS account:

- `Ranka Iris Collaterals` = owned by **sales1.blr@draas.com** → `files().update(addParents=...)` returns **403 insufficientFilePermissions**
- `Ranka Iris ` (root) = owned by **admin2.blr@draas.com** → same 403

Always check the target's owner first:
`files().get(fileId=target, fields='id,name,owners(emailAddress)')`.
Pick a target **owned by ndr** so he keeps full sharing/control. Worked
example: restored into `RankaIris → Marketing` (id `1LwWw-ZtdPYdtO3C_13A8mqM1Mf9QE6k5`, ndr-owned), NOT the sales1-owned "Ranka Iris Collaterals".

## Post-restore sharing check

Restored folders keep their old permission set. The Ranka Iris example had
`propcare.harsha@gmail.com` (reader) still linked from when the folder was
built for Harsha Naidu. If the folder is being repurposed for new
recipients, list permissions
(`permissions().list(fileId=...)`) and ASK whether to revoke stale
recipients before sharing onward.

## "Make sure it's got the latest pictures"

Before delivering, scan for newer project media:
`files().list(q="(name contains 'Iris') and trashed=false and modifiedTime > '<~1 month>'", supportsAllDrives=True, includeItemsFromAllDrives=True)`
and compare modifiedTime vs the restored set. Report whether anything newer
exists (duplicates elsewhere) or the restored set is already the latest.

## Worked example (2026-08-31)

- Deleted: `Ranka Iris - For Harsha Naidu` (id `15wD6DBX1OO0rButnWzIZeU6qoX25tlfy`), 14 files (typical odd floor, even floor plans, sanction plan, all-apartment plans, prelim presentation, exterior render, 8 site photos)
- Restored + renamed → `Ranka Iris - Ninth Floor Collaterals`
- Moved into `RankaIris → Marketing` (ndr-owned)
- Link preserved pattern: https://drive.google.com/drive/folders/<id>