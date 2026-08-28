# Native Google Doc / Sheet → PDF Export (via Drive API)

**Problem:** A Google Doc or Sheet file on Drive needs to be attached to an email as PDF. Unlike .docx files, native Google files cannot be downloaded as PDF via `files().get_media()` — they must be **exported** via `files().export()`.

## Direct Export (No Copy Needed)

Native Google files (Docs, Sheets, Slides) can be exported directly — no temporary copy step needed:

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import io

# Build credentials (see gws-automation SKILL.md for vault access patterns)
creds = Credentials.from_authorized_user_info(token_data)
drive = build('drive', 'v3', credentials=creds)

# Export Google Doc as PDF
request = drive.files().export(
    fileId='<google-doc-file-id>',
    mimeType='application/pdf'
)
fh = io.BytesIO()
fh.write(request.execute())

with open('/tmp/output.pdf', 'wb') as f:
    f.write(fh.getvalue())
```

## MIME Types for Export

| Source Type | Export MIME Type | Notes |
|-------------|-----------------|-------|
| Google Doc (`application/vnd.google-apps.document`) | `application/pdf` | Best for clean PDF output |
| Google Sheet (`application/vnd.google-apps.spreadsheet`) | `application/pdf` | Exports all visible sheets |
| Google Slides (`application/vnd.google-apps.presentation`) | `application/pdf` | Exports as slide PDF |

## Checking File Type Before Export

Always check the mimeType first — attempting to export a binary file (native .pdf, .docx, .jpg) via `export()` will fail:

```python
meta = drive.files().get(fileId=file_id, fields="id, name, mimeType").execute()
mime = meta['mimeType']

if 'document' in mime or 'spreadsheet' in mime or 'presentation' in mime:
    # Google native format — use export()
    request = drive.files().export(fileId=file_id, mimeType='application/pdf')
elif 'pdf' in mime:
    # Already a PDF — use get_media()
    request = drive.files().get_media(fileId=file_id)
else:
    # Other binary — use get_media()
    request = drive.files().get_media(fileId=file_id)

fh = io.BytesIO()
fh.write(request.execute())
```

## Pitfall — Export vs Download

- **`files().export()`** — For Google-native types (Docs, Sheets, Slides). Requires a target mimeType.
- **`files().get_media()`** — For binary file types (PDF, DOCX, JPG, etc.). Downloads as-is.
- Using the wrong one raises `HttpError 403` or `400`.

## Worked Example (Jul 2026)

**Files exported for email attachments to CMS IndusLaw:**

| File | Type on Drive | Export Method | Result |
|------|---------------|--------------|--------|
| `Sevaganapalli Sale Deed Sy No 158 DRA2Suresh Manjunath` | Google Doc | `export(fileId, mimeType='application/pdf')` | 153 KB PDF |
| `Payments Sevaganapalli 16.10.2023 Sale deed No 21201/2023` | Google Sheet | `export(fileId, mimeType='application/pdf')` | 33 KB PDF |
| `Ack Of firm Registration Sevaganapalli Land partners.pdf` | Binary PDF | `get_media(fileId)` | 270 KB PDF |
