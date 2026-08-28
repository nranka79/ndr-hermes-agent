# DOCX-to-PDF Export via Google Drive Conversion

**Problem:** User's .docx files stored on Google Drive need to be sent as clean PDFs on Telegram.

**Do NOT** download the docx and convert locally with pymupdf/fitz — the manual approach cuts off edges, has font rendering issues, and produces low-quality output.

**Correct approach — use Google's own conversion engine:**

## Step 1: Copy the .docx as a Google Doc

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseDownload

drive = build_service("drive", "v3")

copied = drive.files().copy(
    fileId="<original-docx-file-id>",
    body={
        'name': 'temp_export_doc',
        'mimeType': 'application/vnd.google-apps.document'
    },
    fields='id,name'
).execute()
temp_id = copied['id']
```

## Step 2: Export the Google Doc as PDF

```python
request = drive.files().export_media(fileId=temp_id, mimeType='application/pdf')
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    _, done = downloader.next_chunk()

fh.seek(0)
out_path = "/tmp/exported_document.pdf"
with open(out_path, 'wb') as f:
    f.write(fh.read())
```

## Step 3: Clean up the temporary Google Doc

```python
drive.files().delete(fileId=temp_id).execute()
```

## Step 4: Deliver via Telegram

```python
MEDIA:/tmp/exported_document.pdf
```

## Why this works

| Method | Quality | Edge Cutoff? | Fonts | Speed |
|--------|---------|-------------|-------|-------|
| Google Drive export | Original formatting | No | Native fonts | ~5s |
| fitz/pymupdf manual | Poor | Yes (edges cut) | Substituted | ~2s |

## Limitation

The .docx must be stored in Google Drive. Files outside Drive (downloaded via Gmail attachment) need to be **uploaded to Drive first**, then exported.

## Worked example (Jun 2026)

.dox file: `RRV vs SPD - Master Notes v4 COMPLETE - OS 553.docx`
- First attempt: fitz conversion → user reported "edges are cut off, text is cut off"
- Second attempt: Google Drive copy-to-Doc → export → PDF → user confirmed clean output (383 KB vs 128 KB manual)
