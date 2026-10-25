# Time-limited viewer sharing on Drive (and the cross-owner problem)

Use when NDR says: "give him viewer access, 30-day / 90-day", "share these
documents with <external person>", or any time-boxed external share.

## 1. The native tool cannot set an expiry — use build_service

`gws_drive_permissions_add` takes only `role` and `email`. It cannot set
`expirationTime`. For a time-boxed grant, go through the sanctioned client:

```python
import datetime, sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service          # NEVER hand-build credentials
drive = build_service('drive', 'v3', service_name='google-draas')

exp = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=90)) \
        .strftime('%Y-%m-%dT%H:%M:%S.000Z')       # RFC3339, UTC, mandatory format

drive.permissions().create(
    fileId=FID, sendNotificationEmail=False,
    body={'type': 'user', 'role': 'reader',
          'emailAddress': EMAIL, 'expirationTime': exp},
    fields='id,role,expirationTime').execute()
```

Notes
- `expirationTime` is only valid for `reader` / `commenter` / `writer`.
  It is rejected for `owner`.
- `sendNotificationEmail=False` keeps Google from spamming the recipient —
  NDR sends the link himself in the email body.
- Always `import sys; sys.path.insert(0,'/opt/hermes')` and run with
  `env -u PYTHONPATH /opt/hermes/.venv/bin/python3` (PYTHONPATH shadowing —
  see the GWS notes in memory).

## 2. Verify, never assume

Read the permission back before reporting success:

```python
perms = drive.permissions().list(
    fileId=FID, fields='permissions(emailAddress,role,expirationTime)',
    supportsAllDrives=True).execute().get('permissions', [])
hit = [p for p in perms if (p.get('emailAddress') or '').lower() == EMAIL]
```

Report a file → role → expiry line per document. "Shared" without a read-back
is not evidence.

## 3. Files owned by another DRA account cannot be shared (canShare=false)

Symptom:

```
HttpError 400 ... "Sorry, you do not have permission to share."
```

Cause: the file is owned by another account (very common — `sales1.blr@draas.com`
holds most signed JDA / addendum / agreement scans) and ndr@draas.com has only
viewer rights. `capabilities.canShare` is `false`. Domain membership does NOT
grant share rights.

Diagnose:
```python
drive.files().get(fileId=FID, supportsAllDrives=True,
    fields='name,owners,capabilities(canShare)').execute()
```

Fix — make a copy you own, then share the copy:

```python
c = drive.files().copy(fileId=SRC, fields='id,name,owners(emailAddress)',
        body={'name': ORIG_NAME + ' (share copy).pdf',
              'parents': [FOLDER_OWNED_BY_NDR]}).execute()
```

- Copy into an **existing** folder owned by NDR — do NOT create a new folder
  (hard rule: new files go to TMP, or into the project's own existing folder).
- Name the copy so the provenance is obvious (`... (share copy).pdf`).
- The copy is a byte-identical duplicate of the signed PDF; the original is
  left untouched.
- Tell NDR which links are copies and why — do not let him discover it.

## 4. Pitfalls

- **Never retype a Drive folder/file ID.** Copy-paste from the listing or
  re-resolve it (`files().list(q="name = 'X' and mimeType = 'application/vnd.google-apps.folder'")`).
  A single dropped character returns a confusing `404 File not found` that
  names the *parent*, not the file you typed.
- **Links in the email must be the `/file/d/<ID>/view` form** (or
  `/drive/folders/<ID>` for folders, `/document/d/<ID>/view`,
  `/spreadsheets/d/<ID>/view`). Verify after creating the draft by decoding
  the `text/html` part and regexing `href="..."` — a truncated link in a
  23 KB HTML body is easy to miss.
- Sharing a folder shares everything inside it — good for a plan set, bad if
  the folder has internal working files. Check the folder contents first.
