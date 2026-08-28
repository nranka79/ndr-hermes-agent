# gws_auth as Sheets Fallback (when SA key is unavailable)

## Problem
`tools.gws_sa.build_service("sheets", "v4", "ndr@draas.com")` raises:
```
KeyError: 'GOOGLE_SA_KEY'
```

This means the service account credentials env var is not set in the current environment.

## Fix
Fall back to `tools.gws_auth.build_service("sheets", "v4")` which uses the session user's OAuth token.

### Important differences
| Aspect | gws_sa (SA DWD) | gws_auth (OAuth) |
|--------|-----------------|-------------------|
| Identity | Impersonates `ndr@draas.com` | Uses whoever authorized the session's token |
| Sheet location | ndr@draas.com's Drive | The authenticated user's Drive (e.g., vkdas@draas.com) |
| Access | ndr can see it immediately | Need to share manually |

### Sharing after creation
After creating the sheet via gws_auth, share it with ndr@draas.com:
```python
drive = build_service("drive", "v3")
drive.permissions().create(
    fileId=sheet_id,
    body={'type': 'user', 'role': 'writer', 'emailAddress': 'ndr@draas.com'},
    sendNotificationEmail=False,
    fields='id'
).execute()
```

## Detection
Run `env | grep GOOGLE_SA_KEY` — if empty, SA DWD is not available and you'll hit this error.
Run `drive.about().get(fields='user').execute()` to see which user the current token authenticates as.

## Drive upload permissions
When uploading files to a Drive folder, the authenticated user must have **write** access to the parent folder.
If the folder is owned by a different user (e.g., ndr@draas.com) and the token is for another user (e.g., vkdas@draas.com),
the upload fails with:
```
HttpError 403: "Insufficient permissions for the specified parent."
```

**Fix:** Create a new folder in the authenticated user's Drive root, upload there, and share the folder with the intended recipient:
```python
folder = drive.files().create(body={
    'name': 'Folder Name',
    'mimeType': 'application/vnd.google-apps.folder'
}, fields='id, name, webViewLink').execute()

drive.permissions().create(
    fileId=folder['id'],
    body={'type': 'user', 'role': 'writer', 'emailAddress': 'ndr@draas.com'},
    sendNotificationEmail=False
).execute()
```

## How to check who owns the current token
```python
drive = build_service("drive", "v3")
about = drive.about().get(fields='user').execute()
print(f"Authenticated as: {about['user']['emailAddress']}")
```

## Verified
- Jun 2026: Allalsandra PDF extraction — token authenticated as vkdas@draas.com, target folder owned by ndr@draas.com → 403 error. Fix: created new folder in vkdas's Drive, uploaded there, shared with ndr.
