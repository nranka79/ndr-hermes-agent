# Drive: Legal Document Search, Download & Text Analysis

Workflow for finding legal/court documents in Google Drive — searching by
multiple name variants, downloading candidate PDFs, and extracting/searching
within their text content.

## Use Case

A user has case-related documents scanned/filed in Drive (court orders,
sale deeds, RTCs, petitions) and needs to find a specific document by its
legal citation (e.g. "Rule 43-J Confirmation Order", "Order 43 Rule 1(j)",
"OS 93/2019 order"). The filename may not match the legal reference.

## Phase 1: Multi-query Drive Search

Never rely on a single query. Search with **every variant** the document
might have been filed under.

```python
# Via gws_skill_bridge (requires raw_query=False and max=N to avoid
# SimpleNamespace AttributeError — see gws-bridge-pitfalls.md#6)
from tools.gws_skill_bridge import call
import json

queries = [
    'exact phrase from user',
    'variant spelling',
    'abbreviation',
    'case number (OS 93, 274, 196)',
    'property name (Gunjur, Hurulagurki)',
    'legal citation (43-J, Order 43)',
    'document type (confirmation, order, petition)',
]

for q in queries:
    result = call('drive_search', query=q, raw_query=False, max=20,
                  service_name='google-draas')
    files = json.loads(result) if isinstance(result, str) else result
    if files:
        for f in files:
            print(f['name'], '|', f.get('webViewLink', ''))
```

## Phase 2: Search Inside Specific Folders

When you identify the right folder (by name or parent relationship), list
its contents directly:

```python
# Raw query using parent folder ID
result = call('drive_search',
    query="'FOLDER_ID' in parents",
    raw_query=True, max=50, service_name='google-draas')
```

To get folder metadata first:

```python
# drive_get returns a JSON string — parse it
result = json.loads(call('drive_get', file_id='FOLDER_ID',
                         service_name='google-draas'))
print(result['name'], result['webViewLink'])
```

## Phase 3: Download Candidate PDFs

Use `gws_auth.build_service` directly (via `terminal()`, NOT `execute_code`
— see gws-bridge-pitfalls.md#2):

```python
import sys, os, io
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseDownload

svc = build_service('drive', 'v3', service_name='google-draas')
request = svc.files().get_media(fileId='FILE_ID')
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()

with open('/tmp/output.pdf', 'wb') as f:
    f.write(fh.getvalue())
```

**Known issues:**
- `drive_download` bridge operation has missing `output` kwarg — pass
  `output=''` as workaround, or use `build_service` as above (preferred)
- For large files (>10MB), `get_media` with `MediaIoBaseDownload` handles
  chunking automatically

**⚠️ `export()` vs `get_media()` — Use the right download method:**
- `files().export(fileId=..., mimeType=...)` works ONLY for Google-native
  Docs Editors files (Docs, Sheets, Slides, Drawings). Calling it on a
  native PDF/JPEG/DOCX returns **`HttpError 403: Export only supports
  Docs Editors files.`**
- `files().get_media(fileId=...)` works for ALL files — use this for
  PDFs, images, .docx, .xlsx, and any non-Google file. It downloads the
  binary content as-is.
- **Rule of thumb:** When in doubt about the file type, use `get_media()`.
  `export()` is only needed when converting a Google Doc/Sheet/Slide to a
  different format (e.g., Doc → PDF, Sheet → CSV).

## Phase 4: Text Extraction & Keyword Search

### Text-based PDFs (pdftotext)

```bash
# Extract all text
pdftotext /tmp/doc.pdf - | grep -i 'search term'

# Check how much extractable text exists (if 0, it's a scanned image)
pdftotext /tmp/doc.pdf - | wc -c

# Search for multiple patterns
pdftotext /tmp/doc.pdf - | grep -iE '43[-\s]?J|order 43|43.*confirmation'
```

### Scanned/Image PDFs (tesseract OCR)

```bash
# Convert pages to images then OCR
pdftoppm /tmp/doc.pdf /tmp/page -png
for p in /tmp/page-*.png; do
    tesseract "$p" stdout 2>/dev/null
done | grep -i 'search term'
```

Or use the `ocr-and-documents` skill's `references/tesseract-bulk-ocr.md`
for bulk workflows.

## Phase 4b: Visual Identification of Scanned Drawing PDFs

CAD-exported drawings (boundary surveys, site plans, layout drawings) are
often **1-page PDFs with NO text layer** — `pdftotext` returns empty and
filenames can mislead. Two files named similarly (e.g. "NorthStar Allalasandra
Site Digital Survey Drawing.pdf" vs "20260803_..._MainRoad_NH44_JudicialLayout
_Survey.pdf") may be completely different document classes. Render pages to
PNG and OCR/vision-check before reporting:

```bash
# Hermes venv has pymupdf. Render first page(s) at 120dpi:
/opt/hermes/.venv/bin/python3 - << 'PYEOF'
import pymupdf  # NOT 'fitz' (deprecated alias)
for name in ["candidate_A.pdf", "candidate_B.pdf"]:
    doc = pymupdf.open(name)
    print(name, doc.page_count)
    for i in range(min(2, doc.page_count)):
        doc[i].get_pixmap(dpi=120).save(name.replace('.pdf', f'_p{i+1}.png'))
    doc.close()
PYEOF
```

Then call `vision_analyze` on each rendered PNG asking: *"What does this
drawing show? Is it a boundary survey? What title/scale/surveyor/area
statement is visible?"* The OCR will return the title block — surveyor name
& date, site survey number, area statement (sqm/sqft/acres-guntas) — which is
what actually identifies the document.

**Pitfalls:**
- **"Survey" in filename ≠ boundary survey.** A "MainRoad_NH44_JudicialLayout
  Survey.pdf" is a topographic ROAD survey (chainages, TBM points); the
  boundary survey of the site itself is a separate document. Check the title
  block, not the filename.
- Use `vision_analyze` (free OCR path) rather than tesseract for quick
  identification of one or two pages — it returns the title-block text
  directly.
- `.dwg` sibling files often sit next to the PDF version of the same drawing
  (e.g. `...Site Digital Survey Drawing.dwg`); the PDF is the deliverable
  the user wants, but the pairing confirms they're the same drawing.
- When candidates live in different folders, resolve `parents` on each file
  (`svc.files().get(fileId=..., fields='parents')` then walk up) to report
  which project folder a file belongs to — users often ask "part of <project
  name>".

## Phase 4c: Property Unit / Sale-Deed Discovery (avoid fullText overmatch)

When the user asks "is there a sale deed for unit 201-202A of <project>?", the
naive `fullText contains '<project>' and fullText contains '201'` query
**floods back dozens of unrelated files** — Drive tokenizes unit numbers
broadly and shared/team drives pollute results (share certificates, unrelated
sale deeds, financial spreadsheets all matched this session for "Queens
Corner" + "201"). Don't trust fullText for number+property lookups.

**Reliable sequence:**

```python
# 1) Broad find of the project's folders/known deed files by NAME (name
#    contains is much tighter than fullText contains):
svc.files().list(q="name contains 'Queens' and name contains 'Corner'",
                 pageSize=50, fields='files(id,name,mimeType,modifiedTime)')
# 2) List a known project folder's contents by parent ID to enumerate units:
svc.files().list(q="'FOLDER_ID' in parents", pageSize=200,
                 fields='files(id,name,mimeType,modifiedTime)')
# 3) Narrow name-based probes per unit token (201, 202, 201A, 202B, 302A...):
q = "(name contains 'Queen' or name contains 'QC') and name contains '202'"
```

**Confirm the unit from the DEED BODY, not the filename.** A file named
"2025082025 Release deed of Queens Corner.pdf" could be any unit. Download the
candidate (`build_service` + `get_media` for PDFs; `export` text/plain for
Google Docs) and read its **"SCHEDULE OF PROPERTIES"** section — the
description line names the unit and floor, e.g. *"office premises bearing
No. 202 B 'A, situated in Block A, 2nd Floor of the building known as Queens
Corner, at No. 3, Queens Road"*.

**Deed-type matters — report it honestly.** A **Release Deed** (family
settlement / FSA where heirs release their undivided share to other heirs) is
NOT a sale deed. When the user asks for a "sale deed" and the Drive only holds
a release deed for that unit, say so explicitly and distinguish:
- ✅ actual **Sale Deed** (vendor→purchaser transfer) — only one unit may have one
- ✅ **Release Deed** — document exists but not a sale
- ❌ the specific unit's sale deed is simply not on Drive (report "no standalone
  sale deed for X on file", note it may be only physically registered)

Property-tax receipts by unit (e.g. `QC_302_Property Tax Receipt 20xx-yy.pdf`)
confirm a unit number exists even without its deed — useful when reconciling
which units are documented vs which are missing.

## Phase 5: Cross-reference with Document Indexes

Many property/case folders contain a master index spreadsheet. Read it to
find document-to-case mappings:

```python
from tools.gws_auth import build_service
svc = build_service('sheets', 'v4', service_name='google-draas')
result = svc.spreadsheets().values().get(
    spreadsheetId='SHEET_ID', range='A1:G100'
).execute()
for row in result.get('values', []):
    print(row)
```

**⚠️ Sheets API only works with native Google Sheets (mimeType:
application/vnd.google-apps.spreadsheet).** If the index is an uploaded
.xlsx file (mimeType: application/vnd.openxmlformats-officedocument.
spreadsheetml.sheet), the Sheets API returns **`HttpError 400: This
operation is not supported for this document. The document must not be
an Office file.`**

To read uploaded .xlsx files, either:
1. **Download the file** via `files().get_media()` and open with
   `openpyxl` (available in Hermes venv) or `pandas.read_excel()`.
2. **Convert to native Sheets** by re-uploading as a Google Sheet
   (import — not just upload — via Drive API with
   `mimeType='application/vnd.google-apps.spreadsheet'`). This creates
   a new Sheet and makes the data readable via the Sheets API. Check
   with the user before creating duplicates in their Drive.

## Rules for this Workflow

1. **Search all variants** — the legal citation, case number, property name,
   misspelling, and document type should all be separate queries. Don't
   assume filenames match legal citations.
2. **Check folder indexes** — if a folder has a spreadsheet named "Index"
   or "List of Doc", read it first — it maps descriptions to file links.
3. **Extract text before reporting** — "not found by name" ≠ "not in Drive."
   A scanned PDF titled "Application Under Order" may contain Order 43-J
   language inside. Download and check.
4. **Report what DOES exist** — when the target isn't found, list the closest
   related documents found so the user can assess alternatives.
5. **Use terminal(), not execute_code** — `gws_skill_bridge.call()` and
   `gws_auth.build_service()` both fail from execute_code because the
   sandbox lacks `GWS_VAULT_SOCKET` and the `gws_fetch_token` stub.
6. **Prefer build_service over the bridge for downloads** — the bridge's
   `drive_download` has missing-kwarg issues (SimpleNamespace). Using
   `build_service('drive', 'v3')` with `MediaIoBaseDownload` is more
   reliable.
