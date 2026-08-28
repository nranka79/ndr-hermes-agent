# Scanned Legal PDF → Google Doc (OCR + Docs API)

**When:** User shares a scanned legal document (MOU, agreement, deed) via Telegram and asks you to create a formatted Google Doc version in a specific Drive folder.

## Pipeline

### Step 1 — Receive the document

Telegram file uploads land at `/data/hermes/document_cache/<cache_id>_<name>`. Note the path — you'll need it for OCR.

### Step 2 — OCR the scanned PDF

Check if the PDF has a text layer first:

```bash
pdftotext /path/to/document.pdf - | wc -c
# If < 20 chars → image-based scanned PDF
pdfinfo /path/to/document.pdf  # Check page count
```

Convert to PNGs for vision_analyze:

```bash
mkdir -p /tmp/doc_pages
pdftoppm -png -r 150 -f 1 -l N /path/to/document.pdf /tmp/doc_pages/page
# Produces: page-01.png, page-02.png, ... page-N.png
```

OCR each page with `vision_analyze`:

```python
vision_analyze(
    image_url="/tmp/doc_pages/page-01.png",
    question="Read all text from this page of the MOU/legal document"
)
```

**Pitfalls:**
- `pdftoppm` can be slow for large files (30+ seconds for 10 pages at 200dpi). Use `-r 150` (not 200) to speed up.
- `vision_analyze` calls are per-page — the model has no memory across pages. Compile text from all pages yourself.
- Tabular data (survey schedules, extent tables) may come out garbled. Note illegible cells and add "(refer to scanned PDF for verification)" notes.

### Step 3 — Assemble the document text

Compile the OCR output into clean structured text:
- Preserve the document's section structure (parties → recitals → clauses → schedules → signatures)
- Fix common OCR errors (Rs. vs R$, dates, survey numbers)
- For sections with poor OCR quality (tables, schedules), note "refer to scanned PDF for complete details"

### Step 4 — Create the Google Doc in the target Drive folder

Create via Drive API (not Docs API) so you can specify the parent folder:

```python
from tools.gws_auth import build_service
drive = build_service("drive", "v3")
docs = build_service("docs", "v1")

doc = drive.files().create(
    body={
        "name": "YYYYMMDD_MOU_Party1_Party2_Location",
        "mimeType": "application/vnd.google-apps.document",
        "parents": [TARGET_FOLDER_ID]
    },
    fields="id, name, webViewLink"
).execute()
doc_id = doc['id']
```

### Step 5 — Insert content via Docs API batchUpdate

Insert the full compiled text in a single request:

```python
requests = [{
    "insertText": {
        "location": {"index": 1},
        "text": full_text_content
    }
}]
docs.documents().batchUpdate(
    documentId=doc_id,
    body={"requests": requests}
).execute()
```

### Step 6 — Apply formatting

Query the document to find heading positions:

```python
doc = docs.documents().get(documentId=doc_id).execute()
# Build a position map from the content structure
```

Apply bold, centering, and sizing to key elements:

```python
requests = [
    # Center + bold the title
    {"updateParagraphStyle": {
        "range": {"startIndex": TITLE_START, "endIndex": TITLE_END},
        "paragraphStyle": {"alignment": "CENTER"},
        "fields": "alignment"
    }},
    {"updateTextStyle": {
        "range": {"startIndex": TITLE_START, "endIndex": TITLE_END},
        "textStyle": {"bold": True, "fontSize": {"magnitude": 16, "unit": "PT"}},
        "fields": "bold,fontSize"
    }},
    # Bold section headings (WHEREAS, SCHEDULE, IN WITNESS WHEREOF, etc.)
    {"updateTextStyle": {
        "range": {"startIndex": WHEREAS_START, "endIndex": WHEREAS_END},
        "textStyle": {"bold": True},
        "fields": "bold"
    }},
    # Default line spacing for the full doc
    {"updateParagraphStyle": {
        "range": {"startIndex": 1, "endIndex": TOTAL_LENGTH},
        "paragraphStyle": {"lineSpacing": 115, "spaceBelow": {"magnitude": 6, "unit": "PT"}},
        "fields": "lineSpacing,spaceBelow"
    }}
]
docs.documents().batchUpdate(
    documentId=doc_id,
    body={"requests": requests}
).execute()
```

### Step 7 — Upload the original PDF alongside

Upload the original scanned PDF to the same folder with a properly renamed file:

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload(pdf_path, mimetype='application/pdf', resumable=True)
drive.files().create(
    body={'name': renamed_pdf_name, 'parents': [TARGET_FOLDER_ID]},
    media_body=media,
    fields='id, name, webViewLink'
).execute()
```

### Step 8 — Deliver links

Tell the user what was created. Provide both the Google Doc link and the uploaded PDF link.

## When to use this hybrid approach vs HTML import

| Content type | Approach |
|---|---|
| **Text-heavy legal doc** (MOU, agreement, deed text) | **Hybrid** — OCR → Docs API batchUpdate insert+format. Text is the primary content; tables are secondary. |
| **Table-heavy doc** (financial schedules, rate lists) | **HTML import** — tables with colored headers/alternating rows convert better via HTML. Use if you can reconstruct the content as HTML. |
| **Mixed** (legal doc + survey schedules) | **Hybrid with note** — insert the main text via Docs API, append schedules as plain text with "refer to scanned PDF" warnings for illegible cells. |

## Known limitations

- Docs API batchUpdate cannot create proper table structures — you get plain text with delimiters. For proper table conversion, use HTML import.
- Documents longer than ~10,000 chars may need multiple insertText requests (there's a 1MB request size limit on batchUpdate).
- `vision_analyze` accuracy drops on:
  - Faint/light text (common in scanned legal docs)
  - Mirror text (back-side bleed-through)
  - Small print in schedule tables
- Always verify critical numbers (consideration amounts, survey numbers, dates) — OCR commonly confuses 0/O, 1/I/l, 5/S.
