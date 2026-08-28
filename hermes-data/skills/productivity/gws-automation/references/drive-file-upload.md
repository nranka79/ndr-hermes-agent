# Drive File Upload — DRAAS Naming Conventions

Uploading files to Google Drive with correct naming, folder targeting, and permission sharing.

## Standard File Naming Convention (DRAAS)

Nishant uses two naming styles depending on context:

### 1. Sanctioned/Structured Documents
`YYYYMMDD_ProjectName_Description_Author.ext`

Examples:
- `20260616_RankaOasis_MarketingOffice_3DRenders_Bhuvanesh.pdf`
- `20260616_RankaOasis_MarketingOffice_3DRenders_ChatGPT_Earthy.jpg`
- `20260316_RankaOasis_G+2_Villa_Render_V2.png`

Pattern elements:
- **Date** (YYYYMMDD) — date of the document/content, not upload date
- **Project** (PascalCase with underscore separation) — RankaOasis, RankaAmber, etc.
- **Description** (descriptive segment) — MarketingOffice, 3DRenders, G+2_Villa
- **Author/Variant** (optional) — Bhuvanesh, ChatGPT_Earthy, V2
- **Extension** — lowercase

### 2. Marketing/Collateral Files
`Descriptive Natural Language Name.ext`

Examples:
- `Ranka Oasis Marketing Office 3D Render ChatGPT Earthy.jpg`

Nishant prefers this full descriptive name for files that are shared with external parties (landowners, buyers, marketing team) — the name should be self-explanatory without needing folder context.

## Upload Workflow

### 1. Find the target folder

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

# Search by folder name (use quotes for exact match)
results = drive.files().list(
    q="name = 'Marketing Office Renders' and mimeType = 'application/vnd.google-apps.folder'",
    fields='files(id, name, webViewLink)'
).execute()
```

If there are multiple folders with the same name, check the parent hierarchy to confirm the right one.

### 2. Upload the file

```python
from googleapiclient.http import MediaFileUpload

FILE_PATH = '/path/to/local/file.jpg'
FOLDER_ID = 'target_folder_id_here'
FILE_NAME = 'Convention_Correct_Name.jpg'

media = MediaFileUpload(FILE_PATH, mimetype='image/jpeg', resumable=True)
file_metadata = {
    'name': FILE_NAME,
    'parents': [FOLDER_ID],
    'description': 'Brief description of what this is'  # optional but helpful
}

file = drive.files().create(
    body=file_metadata,
    media_body=media,
    fields='id, name, webViewLink, size'
).execute()

print(f"Link: {file['webViewLink']}")
```

### 3. Share with viewers (if needed)

```python
from datetime import datetime, timedelta, timezone

expiry = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()

for email in ['recipient@example.com']:
    perm = drive.permissions().create(
        fileId=file['id'],
        body={
            'type': 'user',
            'role': 'reader',
            'emailAddress': email,
            'expirationTime': expiry
        },
        sendNotificationEmail=False
    ).execute()
```

## MIME Type Mapping

| File type | MIME type |
|-----------|-----------|
| `.jpg` / `.jpeg` | `image/jpeg` |
| `.png` | `image/png` |
| `.pdf` | `application/pdf` |
| `.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

## Pitfalls

- **Existing permissions cannot get expiry added via update** — `permissions.update()` with `expirationTime` fails silently (returns `expires=N/A`). Expiry only works when creating a **new** permission via `permissions.create()`.
- **Expiry may not apply to `writer` role** — if the user already has `writer` access (pre-existing), adding expiry requires creating a fresh `reader` permission, which conflicts with the existing higher-role permission. For writer-collaborators, accept that expiry cannot be enforced via the API.
- **Domain restriction blocks external sharing** — if the recipient's email domain (e.g. `bitanz.com`) blocks receiving external shares, share via their personal Gmail instead (e.g. `oz.iyer@gmail.com`).
- **Use `MediaFileUpload` with `resumable=True`** for files over ~5MB; simple `MediaFileUpload` for smaller files.
- **Always verify the upload** — print the file name, size, and webViewLink from the API response to confirm the upload succeeded and landed in the correct folder.