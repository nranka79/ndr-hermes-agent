# Drive — Batch Setting "Anyone with Link" Permissions

Pattern for **adding** public "Anyone with Link" access to a set of Drive files. The complementary operation to the restriction pattern in `drive-permission-restriction.md` (which *removes* public access).

## Use Case

You've created a document dossier (PDF, report, or collection) that needs to be shared with external parties — clients, doctors, vendors, consultants. Each source document in the dossier needs "Anyone with Link (Reader)" so the external party can click through to verify source data.

## Pattern: Batch Set Anyone-with-Link

```python
import sys
sys.path.insert(0, '/opt/hermes/tools')
from gws_auth import build_service

drive = build_service('drive', 'v3', telegram_id='USER_TELEGRAM_ID')

file_ids = [
    "FILE_ID_1",
    "FILE_ID_2",
    # ... up to any number
]

for fid in file_ids:
    # Check existing permissions first
    perms = drive.permissions().list(
        fileId=fid,
        fields='permissions(id,type,role)'
    ).execute()
    existing_roles = {p['type']: p['role'] for p in perms.get('permissions', [])}
    
    if existing_roles.get('anyone') == 'reader':
        print(f"✅ Already shared: {fid}")
    else:
        if 'anyone' in existing_roles:
            # Update existing anyone permission
            perm_id = [p['id'] for p in perms['permissions'] if p['type'] == 'anyone'][0]
            drive.permissions().update(
                fileId=fid,
                permissionId=perm_id,
                body={'role': 'reader'}
            ).execute()
        else:
            # Create new anyone permission
            drive.permissions().create(
                fileId=fid,
                body={'type': 'anyone', 'role': 'reader'},
                fields='id'
            ).execute()
        print(f"✅ Set to Anyone with Link: {fid}")
```

## Verify the File Is Accessible

After setting permissions, verify the direct link works:

```python
link = f"https://drive.google.com/file/d/{file_id}/view"
print(f"Share this link: {link}")
```

## One-at-a-Time (Single File)

```python
drive.permissions().create(
    fileId='FILE_ID',
    body={'type': 'anyone', 'role': 'reader'},
    fields='id'
).execute()
```

## Pitfalls

- **Inherited permissions**: If a parent folder already has `anyone` access, child files inherit it automatically and don't need explicit permissions. Setting `anyone` at the child level is redundant but harmless.
- **No notification**: Setting `type='anyone'` does NOT send email notifications — the user just needs the link.
- **Folder-level vs file-level**: Setting `anyone` on a folder makes all current and future contents accessible. For precision, set permissions on individual files instead.
- **Quota**: Each `permissions.create()` call counts against Drive API quota. For very large batches (1000+), consider rate-limiting or using the Drive API's batch endpoint.
- **Reader only**: For external sharing to verify source data, always use `role='reader'`. Never use `writer` for publicly shared links.
