# Making a Drive file PRIVATE — inherited permissions & the owner-only TMP trick

**Class:** when NDR says "file it in the project folder but make it PRIVATE (not shared with
anyone)" and the project folder is team-shared. Verified 2026-09-23 (BBMP TDR notification).

## The trap
A file uploaded INTO a shared folder inherits the folder's grants. On the NorthStar legal
folder (`Allalsandra Legal opinion`) the folder grants are: sales1/psingh/rnr reader,
admin2 writer, etc. The uploaded file immediately shows:
`permissions.list → [sales1 writer, psingh reader, rnr reader, ndr owner, admin2 writer]`.

You CANNOT strip them per-file:
```python
drv.permissions().delete(fileId=fid, permissionId=pid).execute()
# HttpError 403 "The authenticated user cannot delete the permission. If the permission is
# inherited, limited access must be leveraged ... cannotDeletePermission"
```
Google's API refuses to delete an INHERITED permission on a child file (you'd need to remove
the permission on the PARENT folder, which affects everyone). **Uploading into a team-shared
folder and trying to make the single file private is impossible via the API.**

## The fix — move the file to the owner-only TMP folder
The root `TMP` folder (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`, in Drive ROOT) belongs ONLY to
ndr@draas.com (owner). Move the file there — inherited grants from the old parent fall away:

```python
drv.files().update(fileId=fid, addParents=TMP, removeParents=OLD_FOLDER,
                   fields="id,parents").execute()
perms = drv.permissions().list(fileId=fid, fields="permissions(id,type,role,emailAddress)")
# → [{'role': 'owner', 'emailAddress': 'ndr@draas.com'}]  ← the ONLY entry. Now private.
```

Verify by listing permissions AFTER the move and asserting exactly one owner entry.

## The trade-off to report honestly
- "In the legal folder" and "private" conflict when the legal folder is team-shared. Say so:
  the file sits in TMP (private, owner-only, link works for NDR) OR in the legal folder
  (team-visible). Never claim private while leaving it in a shared folder.
- Drive's webLink still works for NDR even with zero permissions (owner always has access).

## Upload mechanics (Drive API)
- Use `MediaFileUpload` (googleapiclient), NOT raw `io.BytesIO` — `files().create(
  media_body=BytesIO)` raises `TypeError: media_filename must be str or MediaUpload`.
- `filed = drv.files().create(body=meta, media_body=MediaFileUpload(local, mimetype=...),
  fields="id,name,parents,size,createdTime,owners(emailAddress),webViewLink").execute()`
- Always assert identity first: `drv.about().get(fields="user(emailAddress)")` must be
  ndr@draas.com before any write.