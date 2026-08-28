# Drive Permission Restriction (DRAAS)

Workflow for restricting Drive files/folders from "anyone with link" to explicit users only — a common request across DRAAS as the user tightens drive security.

## Key Concepts

**Two types of `anyone` permissions:**
- **Direct** — set on the file/folder itself via `permissions.create({type: 'anyone', role: 'reader'})`
- **Inherited** — inherited from a parent folder that has `anyone` access

**Critical constraint:** Inherited permissions CANNOT be deleted at the child level. Google Drive returns:
```
HttpError 403: "The authenticated user cannot delete the permission. If the permission
is inherited, limited access must be leveraged."
```

## Checking Permissions

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

perms = drive.permissions().list(
    fileId='FOLDER_OR_FILE_ID',
    fields='permissions(id,type,role,emailAddress,domain)'
).execute()
for p in perms.get('permissions', []):
    print(f"{p['type']} | {p['role']} | {p.get('emailAddress','-')}")
```

Look for `type='anyone'` — that's public access.

## Restricting a Folder (Direct Permission)

If the `anyone` permission is DIRECT (not inherited), you can delete it:

```python
perms = drive.permissions().list(fileId=FOLDER_ID, fields='permissions(id,type)').execute()
for p in perms.get('permissions', []):
    if p['type'] == 'anyone':
        drive.permissions().delete(fileId=FOLDER_ID, permissionId=p['id']).execute()
        print("✅ Removed public access")
```

After removal, only explicitly-added users can access. The folder link still works but non-authorized users get 403.

## The Inherited Permissions Problem

A subfolder inside a publicly-shared parent folder **inherits** the `anyone` permission and you CANNOT delete it from the child.

**Failed approach:** Creating a "Restricted" subfolder inside a public folder — the child inherits the parent's public access and you can't override it.

**Working approach — move files OUT of the shared parent:**

```python
# 1. Create a new folder OUTSIDE the public parent
new_folder = drive.files().create(body={
    'name': 'Restricted Folder Name',
    'parents': ['ROOT_OR_OTHER_PARENT_ID'],  # NOT the public parent!
    'mimeType': 'application/vnd.google-apps.folder'
}).execute()
new_id = new_folder['id']

# 2. Remove any 'anyone' permission on the new folder (should be direct, not inherited)
perms = drive.permissions().list(fileId=new_id, fields='permissions(id,type)').execute()
for p in perms.get('permissions', []):
    if p['type'] == 'anyone':
        drive.permissions().delete(fileId=new_id, permissionId=p['id']).execute()

# 3. Add explicit users
for email, role in [('user1@draas.com', 'writer'), ('user2@draas.com', 'reader')]:
    drive.permissions().create(
        fileId=new_id,
        body={'type': 'user', 'role': role, 'emailAddress': email},
        sendNotificationEmail=False
    ).execute()

# 4. Move files from public parent to new restricted folder
for file_id in ['FILE_ID_1', 'FILE_ID_2']:
    drive.files().update(
        fileId=file_id,
        addParents=new_id,
        removeParents=PUBLIC_PARENT_ID,
        fields='id,parents'
    ).execute()
```

## Full Restriction Example (Session: Jun 2026)

The **Ranka Iris Customer Legal Set 16MAY16** folder had `anyone | reader` (public). Steps:

1. Checked permissions — found `anyoneWithLink` as **direct** permission
2. Deleted it — `drive.permissions().delete()` succeeded
3. Folder became restricted — only 9 explicit users retained access
4. **For new Sale Deed files** within it: created a separate folder under `RANKA IRIS/` (outside the public folder), moved the Sale Deed files there, restricted that folder

## Domain-Level Permissions (`type='domain'`)

Google Workspace domains can have **domain-level** permissions — these give access to everyone in the @draas.com domain without requiring explicit user-by-user sharing. Unlike `type='anyone'` (public link), domain access is scoped to the organisation but still broader than explicit user sharing.

### Detecting Domain Permissions

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

perms = drive.permissions().list(
    fileId='FILE_OR_FOLDER_ID',
    fields='permissions(id,type,role,domain)'
).execute()
for p in perms.get('permissions', []):
    if p['type'] == 'domain':
        print(f"DOMAIN: {p.get('domain')} → role: {p['role']} (id: {p['id']})")
```

Key indicator: `type='domain'` with `domain='draas.com'` and no `emailAddress`.

### Removing Domain Access + Adding Explicit User

When the user wants to tighten security from "anyone @draas.com can edit" to "only specific named users can view":

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

doc_ids = ['DOC_ID_1', 'DOC_ID_2']  # one or more docs
target_email = 'user@draas.com'

for doc_id in doc_ids:
    file = drive.files().get(fileId=doc_id, fields='permissions').execute()
    
    # 1. Remove domain-wide permission
    for perm in file.get('permissions', []):
        if perm.get('type') == 'domain':
            drive.permissions().delete(
                fileId=doc_id, permissionId=perm['id']
            ).execute()
    
    # 2. Add explicit user as viewer
    drive.permissions().create(
        fileId=doc_id,
        body={'type': 'user', 'role': 'reader', 'emailAddress': target_email},
        sendNotificationEmail=False
    ).execute()
```

**Caveat — owner matters:** The caller must have sufficient permissions on the document:
- **Owner** can always manage permissions
- **Writer** can manage permissions IF the file's sharing settings allow it (controlled by `writersCanShare` field — default `true` for files owned by the same domain)
- **Reader** cannot modify permissions

### After Restriction — What Remains

After removing domain access, the document retains only explicitly-added user permissions:
- Owner
- Users with explicit `type='user'` permissions (writer/reader/commenter)
- The new viewer you just added

No one else in the domain can find or access the document unless explicitly shared.

### Comparison: `anyone` vs `domain`

| Permission Type | Scope | Removal | Typical Role |
|---|---|---|---|
| `type='anyone'` | Public internet — anyone with link | Direct `permissions.delete()` | reader |
| `type='domain'` | Entire @draas.com org | Direct `permissions.delete()` | writer/reader |
| `type='user'` | Single named user | Direct `permissions.delete()` | owner/writer/reader |

## Domain-wide Restriction Pattern (Legacy)

For systematically restricting all files (as planned by user):
- Scan via `files.list` with `fields='files(id, name, permissions)'` — permissions come embedded (no extra API calls)
- Filter: `type='anyone'` → delete the permission
- Filter: `type=user` with non-@draas.com email → flag for review or add expiration
- Use `permissions.update()` with `expirationTime` for time-bound external access
- BFS crawl from root, checkpointing progress for incremental runs

## Verified Caveats (Jun 2026)

- Direct `anyone` permission deletions work immediately — no propagation delay
- Moving files to a new parent strips inherited permissions from the old parent
- The parent folder's `anyone` status does NOT retroactively affect files already moved out
- `type='anyone'` permissions show as `id='anyoneWithLink'` in the list response

## Cron-Based Time-Limited Public Sharing (Folder-Level)

For sharing a **folder** publicly for a fixed period (e.g., "anyone with link can view for 1 week"), use a cron job to revoke the `anyone` permission instead of `expirationTime` (which doesn't work on `type='anyone'` folder permissions).

### Pattern

**Phase 1 — Set up sharing:**
```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')
folder_id = 'FOLDER_ID'

# Add specific users (permanent)
for email in ['user1@example.com', 'user2@example.com']:
    drive.permissions().create(
        fileId=folder_id,
        body={'type': 'user', 'role': 'reader', 'emailAddress': email},
        sendNotificationEmail=False
    ).execute()

# Add anyone-with-link (temporary)
drive.permissions().create(
    fileId=folder_id,
    body={'type': 'anyone', 'role': 'reader'}
).execute()
```

**Revocation script** (save as `~/.hermes/scripts/revoke_public_access.py`):
```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')
drive.permissions().delete(fileId='FOLDER_ID', permissionId='anyoneWithLink').execute()
print("✅ Removed 'Anyone with link' access.")
```

**Cron job** (no_agent=True — script output delivered verbatim):
```python
cronjob(action='create',
    name='Revoke Public Access',
    no_agent=True,
    schedule='2026-06-28T23:59:00',
    script='revoke_public_access.py')
```

**Key points:**
- `no_agent=True` skips the LLM entirely
- The `anyone` permission ID is always `anyoneWithLink`
- Specific user permissions survive deletion
- Test the script manually before scheduling

### When to use cron-based vs expirationTime

| Approach | Best for | Since |
|----------|----------|-------|
| `expirationTime` on `type='user'` | Per-user, single file, binary type | Works on PDFs, not Google Docs |
| Cron-based `type='anyone'` | Folder-level public sharing, any file type | Works universally |
| Manual revocation | Ad-hoc, no advance schedule | User asks "remove access now" |

## Time-Limited Sharing for Binary Files (Confirmed Working — Jun 2026)

Setting `expirationTime` on Drive permissions **works for PDFs and binary files** but is **silently ignored for Google Docs/Sheets/Slides** on this workspace plan. Use this pattern when sharing sensitive documents (GPAs, sale deeds, legal docs) with external parties on a time-bound basis.

### Confirmed Working — PDF with 7-day expiry

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

file_id = 'FILE_ID'  # PDF or other binary file
from datetime import datetime, timedelta, timezone
expiry = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

permission = {
    'type': 'user',
    'role': 'reader',               # viewer-only
    'emailAddress': 'user@example.com',
    'expirationTime': expiry
}

result = drive.permissions().create(
    fileId=file_id,
    body=permission,
    sendNotificationEmail=False     # OK for users with Google accounts
).execute()
```

**Verify the permission was created with expiry:**
```python
perms = drive.permissions().list(
    fileId=file_id,
    fields='permissions(id,type,role,emailAddress,expirationTime)'
).execute()
for p in perms.get('permissions', []):
    print(f"{p.get('emailAddress','')} | {p.get('role')} | expires: {p.get('expirationTime','never')}")
```

### What works vs what doesn't

| File Type | `expirationTime` Behaviour | Verified |
|-----------|---------------------------|----------|
| PDF | ✅ Fully supported — permission auto-expires on the set date | Jun 2026 |
| Images (.jpg, .png) | ✅ Likely supported (same binary file class as PDF) | Not tested |
| Google Doc/Sheet/Slide | ❌ Silently ignored — parameter accepted but never expires | Jun 2026 |
| .docx/.xlsx uploaded to Drive | ⚠️ Unknown — may work if stored as binary | Not tested |

### Practical Pattern (External Document Sharing)

1. **Set viewer-only access with expiry** when the user says "share this document with [Person] for viewing, one week access"
2. **Also grant editor access to the user (ndr@draas.com)** so they retain permanent access even after the expiry
3. **Generate a shareable webViewLink** via `drive.files().get(fileId=..., fields='webViewLink')`
4. **Deliver the link** via WhatsApp or Telegram
5. **Note the expiry date** to the user so they know when access will be revoked

**Real example (Jun 2026):** GPA document (`20260610_Riverstone_GPA_Sy114-10A-10B_ShreeMahakasiEnterprises.pdf`) shared with Manohar Singh (msingh@redsoul.co.in) as viewer-only with 7-day expiry. Permission created successfully with `expirationTime` set.

```python
from datetime import datetime, timedelta, timezone
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

file_id = '1HNbSaecibCDvuJHXeSZkBIu-bK7HBtfM'
expiry = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

perm = drive.permissions().create(
    fileId=file_id,
    body={
        'type': 'user',
        'role': 'reader',
        'emailAddress': 'msingh@redsoul.co.in',
        'expirationTime': expiry
    },
    sendNotificationEmail=False
).execute()

# webViewLink for sharing
file = drive.files().get(fileId=file_id, fields='webViewLink').execute()
link = file['webViewLink']
```

## Sharing with Non-Google-Account Users

When sharing with email addresses that don't have Google Workspace accounts (including @draas.com addresses that haven't been created as Google users yet):

```python
# This will FAIL with a 400 error:
drive.permissions().create(
    fileId=FILE_ID,
    body={'type': 'user', 'role': 'reader', 'emailAddress': 'newuser@draas.com'},
    sendNotificationEmail=False  # ERROR: must notify if no Google account
).execute()
```

**Error:**
```
HttpError 400: "You are trying to invite X@draas.com. As there is no
Google Account associated with this email address, you must tick the
'Notify people' box to invite this recipient."
```

**Fix:** Remove `sendNotificationEmail=False` (defaults to `True`):

```python
drive.permissions().create(
    fileId=FILE_ID,
    body={'type': 'user', 'role': 'reader', 'emailAddress': 'newuser@draas.com'},
).execute()  # sendNotificationEmail defaults to True — works!
```

This sends a Drive sharing invitation email to the address, allowing them to access the file even without a Google account login. The user clicks the link in the email to view.

**⚠️ Combining expiry with non-Google-account sharing:** When sharing with non-Google-account users, `expirationTime` + `sendNotificationEmail=False` causes a conflict — the API requires sending a notification if the user has no Google account. To add time-bound access for non-Google-account users, set `sendNotificationEmail=True` (default) and include `expirationTime`. The invitation email will include the expiry info, and access will auto-revoke on the set date.
