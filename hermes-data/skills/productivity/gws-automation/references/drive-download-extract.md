# Drive — Download Files & Extract Text from PDFs

Pattern for downloading PDFs from Google Drive and extracting text for data ingestion. Used when you need to read the contents of uploaded medical reports, scanned prescriptions, or any PDF stored in Drive.

## Complete Pipeline

```python
import sys, os, tempfile
sys.path.insert(0, '/opt/hermes/tools')
from gws_auth import build_service

drive = build_service('drive', 'v3', telegram_id='USER_TELEGRAM_ID')

# 1. Download a file from Drive
file_id = "FILE_ID"
request = drive.files().get_media(fileId=file_id)
tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
tmp.write(request.execute())
tmp.close()
pdf_path = tmp.name

# 2. Extract text with pymupdf (best for machine-readable PDFs)
import fitz  # pymupdf
doc = fitz.open(pdf_path)
text = ""
for page in doc:
    text += page.get_text()
doc.close()
print(f"Extracted {len(text)} chars")

# 3. Alternative: pdftotext for column-aligned reports (e.g., PFT tables)
import subprocess
txt_path = pdf_path + '.txt'
subprocess.run(['pdftotext', '-layout', pdf_path, txt_path], capture_output=True)
with open(txt_path) as f:
    layout_text = f.read()

# 4. Clean up
os.unlink(pdf_path)
os.unlink(txt_path)
```

## Handling Google Docs (not PDFs)

Google Docs, Sheets, and Slides stored in Drive have native mime types — you can't download them as PDFs via `get_media()` directly. Use `export()` instead:

```python
# Google Doc → plain text
content = drive.files().export(
    fileId=doc_file_id,
    mimeType='text/plain'
).execute().decode('utf-8')

# Google Doc → PDF
pdf_bytes = drive.files().export(
    fileId=doc_file_id,
    mimeType='application/pdf'
).execute()

# Google Sheet via Sheets API (more reliable than export)
from gws_auth import build_service as build_auth
sheets = build_auth('sheets', 'v4', telegram_id='USER_TELEGRAM_ID')
result = sheets.spreadsheets().values().get(
    spreadsheetId=sheet_id,
    range='Sheet1'
).execute()
rows = result.get('values', [])
```

## Identifying File Types

Before downloading, check mime type to choose the right extraction method:

```python
meta = drive.files().get(
    fileId=file_id,
    fields='id,name,mimeType,size'
).execute()

if meta['mimeType'] == 'application/pdf':
    # Use pymupdf or pdftotext
elif meta['mimeType'] == 'application/vnd.google-apps.document':
    # Use files().export() with text/plain
elif meta['mimeType'] == 'application/vnd.google-apps.spreadsheet':
    # Use Sheets API (most reliable) or export as CSV
elif meta['mimeType'].startswith('image/'):
    # Use OCR (vision_analyze or tesseract)
else:
    print(f"Unknown type: {meta['mimeType']}")
```

## Pitfalls

- **PDF vs Google Doc**: A file named `Report.pdf` may actually be a Google Doc with a PDF name if it was uploaded via Drive's "Upload File" option. Always check `mimeType` before choosing extraction method.
- **Scanned/handwritten PDFs**: `pymupdf.get_text()` returns empty strings for scanned image-based PDFs. Use OCR (tesseract, or `marker-pdf` for complex layouts).

## Scanned PDF → Vision Analysis (for Plans/Drawings/Image-based PDFs)

When a PDF contains no extractable text (approved plans, scanned drawings, image-based documents), use pdftoppm to convert to images, then analyze with `vision_analyze`:

```bash
# 1. Download PDF from Drive (use gws_skill_bridge)
cd /opt/data && uv run python3 -c "
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_skill_bridge import call
print(call('drive_download', service_name='google-draas',
    file_id='FILE_ID', output='/opt/data/plan.pdf'))
"

# 2. Convert to high-res JPEG (300 DPI preserves plan text/labels)
pdftoppm -jpeg -r 300 /opt/data/plan.pdf /opt/data/plan_img

# 3. Analyze with vision tool
# File will be at /opt/data/plan_img-1.jpg
```

**Key tips:**
- **`-r 300`** (300 DPI) is the sweet spot — lower loses label readability, higher creates huge files with marginal benefit.
- **PDF info check first:** `pdfinfo /opt/data/plan.pdf` tells you page count, size, and whether it's image-based.
- **pdftotext check:** Run `pdftotext plan.pdf - | head -5` first. If empty, it's image-based → use pdftoppm pipeline.
- **Multi-page PDFs:** pdftoppm outputs `prefix-N.jpg` for each page. Analyze each page separately.
- **vision_analyze question specificity matters:** Ask explicitly for plot numbers, dimensions, road widths, facing indicators — the model needs the context of what you're looking at (it's a layout plan, not a letter).
- **OCR quality varies:** Engineering drawings with rotated text, diagonal labels, or very small dimensions often OCR poorly. The vision model can still extract meaning from visual layout even when individual characters are garbled.
- **Memory clean-up:** After analysis, remove the large intermediate files: `rm -f /opt/data/plan.pdf /opt/data/plan_img-*.jpg`

**When to use this vs. text-based extraction:**
| File type | Method | Tool |
|---|---|---|
| Text-based PDF (report, letter, ITR) | pdftotext | `pymupdf` or `pdftotext -layout` |
| Scanned document (receipt, prescription) | OCR | `marker-pdf` or tesseract |
| **Approved plan / engineering drawing / layout** | **Image conversion + vision** | **pdftoppm → vision_analyze** |
| Mixed (text + images) | Try pdftotext first, fallback to vision | Both |
- **Google Sheets via export**: Exporting a sheet as CSV or PDF truncates at the sheet's printable area. For full data, always use the Sheets API v4 with `spreadsheets().values().get()`.
- **Large files**: `get_media()` downloads the entire file into memory. For files >50MB, use `MediaIoBaseDownload` with chunking:
  ```python
  from googleapiclient.http import MediaIoBaseDownload
  import io
  fh = io.BytesIO()
  downloader = MediaIoBaseDownload(fh, request)
  done = False
  while not done:
      done = progress = downloader.next_chunk()
  ```
- **File not found**: If `get_media()` returns 404, the file may be in a shared Drive. Add `supportsAllDrives=True` to the request or use `includeItemsFromAllDrives=True` when listing.
- **Token refresh**: For long-running batch processing, tokens may expire. `gws_auth.build_service()` handles refresh automatically if a refresh token is available.
- **Venv Python**: Run extraction scripts with `/opt/hermes/.venv/bin/python3` — the Google API client and pymupdf are installed there, not in system python.
