# "Anyone with the link" permissions — what Drive actually allows

Verified 2026-10-17 while sharing a travel-agent folder (Kanta Ranka visa documents).

## 🔴 You CANNOT put an expiry date on an anyone-with-link permission

```
svc.permissions().create(
    fileId=fid,
    body={'type':'anyone','role':'reader',
          'expirationTime':'2026-10-24T10:00:00.000Z'})
```

returns:

```
HttpError 403 ... "Expiration dates cannot be set on domain or anyone type permissions."
Details: [{'reason': 'cannotSetExpirationOnAnyoneOrDomain'}]
```

This is a hard Drive rule, not a quota or a config issue. `expirationTime` is only valid on
`type: 'user'` and `type: 'group'` permissions.

### So the pattern is: share open, then schedule the close

1. Create the permission **without** `expirationTime`:
   ```python
   svc.permissions().create(fileId=fid,
       body={'type':'anyone','role':'reader'},
       fields='id,type,role').execute()
   # -> {'id': 'anyoneWithLink', 'type': 'anyone', 'role': 'reader'}
   ```
2. Immediately schedule the revocation — a one-shot `cronjob` with `enabled_toolsets:
   ["terminal","file"]` whose prompt names the folder id and tells the future agent to
   `permissions().delete(fileId=..., permissionId='anyoneWithLink')` and then **read the
   permissions back** to confirm only the owner (plus known readers) remain.
3. Tell NDR the link does **not** auto-expire, and give him the date the revoke job runs.
   Never say "the link works for one week" as though Drive enforces it — that was an earlier
   mistake. The window is enforced by the job, not by Google.

A cron row is the right vehicle here — the revocation must happen whether or not NDR is in a
session that day. Prefer it over a next-agent-action row when the date is fixed and the action
is purely mechanical.

## Share a SUBSET, not the whole pack

When someone asks for two or three specific documents (a bank, a visa agent, a landlord),
do **not** open the master evidence pack to them. Instead:

1. Create a small folder **inside root TMP** (never My Drive root — see the HARD RULE).
2. `files().copy(fileId=src, body={'parents':[new_folder]})` each requested file into it.
   Copy, don't re-parent — the originals stay private in the master pack.
3. Share **that** folder anyone-with-link.
4. Send the folder link.

## Other constraints worth remembering

- `gws_drive_permissions_add` (the native tool) supports only `user | domain`. Creating an
  `anyone` permission MUST go through `build_service('drive','v3',...)` in `terminal` /
  `execute_code` — this is the sanctioned GWS path, not hand-rolled credentials.
- Moving a folder under TMP preserves the folder **id**, so any link already handed out keeps
  working. Moving is always safe; never re-create-and-delete a shared folder to relocate it.
- Verify before reporting success: `permissions().list(fileId=...)` and show the actual rows.
  An `anyoneWithLink` entry is visible as `{'id':'anyoneWithLink','type':'anyone','role':'reader'}`.

## Revocation snippet

```python
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
svc = build_service('drive', 'v3', service_name='google-draas')

perms = svc.permissions().list(fileId=FOLDER_ID,
    fields='permissions(id,type,role,emailAddress)').execute()['permissions']
for p in perms:
    if p['type'] == 'anyone':
        svc.permissions().delete(fileId=FOLDER_ID, permissionId=p['id']).execute()

print(svc.permissions().list(fileId=FOLDER_ID,
    fields='permissions(id,type,role,emailAddress)').execute()['permissions'])
```
