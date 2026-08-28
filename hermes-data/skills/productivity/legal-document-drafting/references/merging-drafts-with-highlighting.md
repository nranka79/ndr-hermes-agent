# Merging Two Legal Draft Versions (with Yellow Highlighting)

## Use Case
User provides a newer/third-party draft and says "merge this with ours, keep all headers/sections." The deliverable is a single merged doc with changes from the user's draft highlighted in yellow.

## Workflow

### 1. Download Both Drafts
```python
from tools.gws_auth import build_service, load_credentials

drive_service = build_service("drive", "v3", service_name="google-draas")
# Download as .docx binary
request = drive_service.files().get_media(fileId=DOC_ID)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
while not done:
    status, done = downloader.next_chunk()
with open("local.docx", "wb") as f:
    f.write(fh.getvalue())
```

### 2. Extract Text for Comparison
```python
from docx import Document
doc = Document(path)
text = "\n".join(p.text for p in doc.paragraphs)
```

### 3. Build Merged Draft with python-docx
**Rule: Use the user's (newer) draft as the structural template.** Keep their:
- Party roles and definitions (VENDOR/CONFIRMING PARTY assignments)
- Section header names and sequence
- Recital order and numbering
- Schedules format

Add our content into their framework where theirs is sparse or missing. Remove duplication.

### 4. Yellow Highlighting Technique
```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_run(para, text, bold=False, highlight=False):
    run = para.add_run(text)
    if bold:
        run.bold = True
    if highlight:
        rPr = run._element.get_or_add_rPr()
        hl = OxmlElement('w:highlight')
        hl.set(qn('w:val'), 'yellow')
        rPr.append(hl)
    return run

def add_mixed_para(doc, parts):
    """parts = [(text, {format_kwargs}), ...]"""
    para = doc.add_paragraph()
    for text, fmt in parts:
        add_run(para, text, **fmt)
    return para
```

The `add_mixed_para` function handles inline mixed formatting — bold label + normal body within one paragraph, e.g.:
```python
add_mixed_para(doc, [
    ("(i)  Title:", {"bold": True, "highlight": True}),
    ("The VENDOR has good title...", {"highlight": True}),
])
```

### 5. Upload to Google Drive (preserves highlighting)
```python
media = MediaFileUpload(file_path,
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True)

file = drive_service.files().create(
    body={'name': 'doc_name', 'mimeType': 'application/vnd.google-apps.document'},
    media_body=media, fields='id, webViewLink').execute()
```

**This preserves yellow highlighting** — verified via Docs API:
```python
doc = docs_service.documents().get(documentId=file_id).execute()
for item in doc["body"]["content"]:
    if "paragraph" in item:
        for elem in item["paragraph"]["elements"]:
            ts = elem.get("textRun", {}).get("textStyle", {})
            bg = ts.get("backgroundColor", {})
            rgb = bg.get("color", {}).get("rgbColor", {})
            if rgb.get("red", 0) > 0.8 and rgb.get("green", 0) > 0.8:
                # This is yellow highlighted
```

### 6. Set Document Permissions
```python
drive_service.permissions().create(
    fileId=file_id,
    body={'type': 'anyone', 'role': 'writer', 'allowFileDiscovery': False}).execute()
```

## Pitfalls
- docx → Google Docs conversion uses **pip install python-docx** (NOT docx or python_docx)
- `add_mixed_para` requires each part to be `(text_dict)` format — NOT `("label:", "body", {"bold": True})` (3-tuple breaks unpacking)
- Google Docs API v1 stores background colours in `textRun.textStyle.backgroundColor.color.rgbColor` — not in the legacy `weightedFontFamily` field
- Tables in python-docx DO NOT preserve highlighting through the Google Docs API — only paragraph runs do
- If the merged .docx file size drops significantly (e.g. 592KB → 20KB), styles/formatting from the source docx may be lost. The python-docx library rebuilds formatting fresh