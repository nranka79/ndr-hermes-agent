# PPTX → PDF Conversion via Google Drive

Convert PowerPoint files (.pptx) to PDF when LibreOffice is unavailable (Docker containers, headless servers). Uses Google Drive API: upload as Google Slides → export as PDF.

## Prerequisites

- `tools.gws_auth.build_service()` with a valid token
- `googleapiclient.http.MediaFileUpload`
- Python environment with `google-api-python-client` (available in Hermes venv)

## Workflow

```python
import sys, os
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'

from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

# 1. Build Drive service
drive = build_service('drive', 'v3', telegram_id='<tg_id>', service_name='<resolved_account>')

# 2. Find or create TMP folder
results = drive.files().list(
    q="name='TMP' and mimeType='application/vnd.google-apps.folder' "
      "and 'root' in parents and trashed=false",
    spaces='drive'
).execute()
files = results.get('files', [])
folder_id = files[0]['id'] if files else None
if not folder_id:
    folder = drive.files().create(
        body={'name': 'TMP', 'mimeType': 'application/vnd.google-apps.folder'},
        fields='id'
    ).execute()
    folder_id = folder['id']

# 3. Upload PPTX as Google Slides (auto-converts)
media = MediaFileUpload(
    '/path/to/file.pptx',
    mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
    resumable=True
)
slides = drive.files().create(
    body={
        'name': 'Presentation Name',
        'parents': [folder_id],
        'mimeType': 'application/vnd.google-apps.presentation'
    },
    media_body=media,
    fields='id,name,mimeType,webViewLink'
).execute()
slides_id = slides['id']

# 4. Export as PDF
pdf_bytes = drive.files().export(fileId=slides_id, mimeType='application/pdf').execute()

# 5. Upload PDF to Drive TMP (optional — or return bytes to user)
with open('/tmp/output.pdf', 'wb') as f:
    f.write(pdf_bytes)

pdf_media = MediaFileUpload('/tmp/output.pdf', mimetype='application/pdf', resumable=True)
pdf_file = drive.files().create(
    body={'name': 'Presentation Name.pdf', 'parents': [folder_id]},
    media_body=pdf_media,
    fields='id,name,size,webViewLink'
).execute()
pdf_id = pdf_file['id']

print(f"PDF ID: {pdf_id}")
print(f"Link: {pdf_file['webViewLink']}")

# 6. Cleanup — Slides file stays in Drive (reclaimable from trash if needed)
os.remove('/tmp/output.pdf')
```

## Key Points

- **Upload MIME type**: `application/vnd.openxmlformats-officedocument.presentationml.presentation` (.pptx)
- **Slides MIME type**: `application/vnd.google-apps.presentation` (triggers auto-conversion)
- **Export MIME type**: `application/pdf` (Drive handles the rendering)
- Files land in the user's TMP folder (per Nishant's preference — files never go to Drive root)
- The intermediate Google Slides file stays in Drive TMP — can be kept or cleaned up later
- No LibreOffice or external tools needed

## Known Issues

- **Format fidelity**: Complex animations, embedded fonts, speaker notes, and transition effects may not survive the Slides conversion. For exact layout preservation, LibreOffice is still preferred.
- **Size limits**: Standard Drive limits apply (10MB for .pptx upload, 25MB for PDF export through free tier).
- **Scanned WOs via PDF → image**: The reverse workflow (extracting text from scanned PDF WOs) uses pymupdf + vision_analyze — see `kelsa-mcp/references/invoice-wo-payment-verification.md` Step 3.6.
