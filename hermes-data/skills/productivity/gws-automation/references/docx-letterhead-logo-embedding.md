# DOCX Letterhead with Logo Embedding

When generating company letterhead documents (Board Resolutions, Org Structure, RERA compliance letters), embed the company logo into the DOCX header using python-docx.

## Prerequisites

```bash
uv pip install python-docx Pillow
```

## Step 1 — Acquire the Logo Image

The user typically sends the logo as a JPG/PNG attachment. If `vision_analyze` is unavailable, identify the logo content with PIL + tesseract:

```python
from PIL import Image

img = Image.open("/path/to/logo.jpg")
# Sample key zones to detect colors
w, h = img.size
for x, y, name in [
    (w//4, h//4, "upper-left"),
    (3*w//4, h//4, "upper-right"),
    (w//4, 3*h//4, "lower-left"),
    (3*w//4, 3*h//4, "lower-right"),
    (w//2, h//2, "center"),
]:
    r, g, b = img.getpixel((x, y))
    print(f"{name}: RGB({r},{g},{b})")

# OCR the logo text
import subprocess
result = subprocess.run(
    ["tesseract", "/path/to/logo.jpg", "stdout"],
    capture_output=True, text=True, timeout=10
)
print(result.stdout)  # e.g. "DRA\n\nHOME OF PRIDE"
```

Save as PNG for DOCX insertion:
```python
img.save("/data/hermes/document_cache/DRA_Logo.png", "PNG")
```

## Step 2 — Build the Letterhead Header Function

The core function creates a two-row table in the document header:

```python
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

def create_letterhead_header(doc, logo_path):
    """Add letterhead to the first section header"""
    section = doc.sections[0]
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.header_distance = Cm(0.5)

    header = section.header
    header.is_linked_to_previous = False

    # Clear existing header content
    for p in header.paragraphs:
        p.clear()
    for tbl in header.tables:
        tbl._element.getparent().remove(tbl._element)

    # Create 2-row, 2-col table
    tbl = header.add_table(rows=2, cols=2, width=Inches(6.5))
    tbl.autofit = True

    # Remove table borders
    for row in tbl.rows:
        for cell in row.cells:
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcBorders = OxmlElement('w:tcBorders')
            for border_name in ['top', 'left', 'bottom', 'right']:
                border = OxmlElement(f'w:{border_name}')
                border.set(qn('w:val'), 'nil')
                tcBorders.append(border)
            tcPr.append(tcBorders)

    # Row 0, Col 0: Logo
    logo_cell = tbl.cell(0, 0)
    logo_para = logo_cell.paragraphs[0]
    logo_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if os.path.exists(logo_path):
        run = logo_para.add_run()
        run.add_picture(logo_path, width=Inches(1.2))

    # Row 0, Col 1: Company Info
    info_cell = tbl.cell(0, 1)
    info_para = info_cell.paragraphs[0]
    info_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    run = info_para.add_run('DRA REALTY PRIVATE LIMITED')
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0x1A, 0x3C, 0x6E)  # Navy blue
    run.font.name = 'Calibri'

    info_para2 = info_cell.add_paragraph()
    info_para2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run2 = info_para2.add_run('''Corporate Office: No. 82/1, JC Industrial Layout,
Kanchapura Main Road, Kanakapura Road,
Bengaluru - 560062
Phone: +91-9000299200 | Email: info@draas.com
GST: 29AALCD9962L1ZW | CIN: U45209KA2014PTC074068''')
    run2.font.size = Pt(7)
    run2.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    run2.font.name = 'Calibri'

    # Row 1 (merged): Horizontal separator line
    line_cell = tbl.cell(1, 0)
    line_cell2 = tbl.cell(1, 1)
    line_cell.merge(line_cell2)

    # Add bottom border to merged cell
    tc = line_cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '12')
    bottom.set(qn('w:color'), '1A3C6E')
    bottom.set(qn('w:space'), '1')
    tcBorders.append(bottom)
    tcPr.append(tcBorders)

    # Set column widths
    for row in tbl.rows:
        row.cells[0].width = Inches(1.5)
        row.cells[1].width = Inches(5.0)

    return doc
```

## Step 3 — Add Standard Footer

```python
def add_footer_line(doc):
    section = doc.sections[0]
    footer = section.footer
    footer.is_linked_to_previous = False

    for p in footer.paragraphs:
        p.clear()

    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Thin top border on footer
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    top = OxmlElement('w:top')
    top.set(qn('w:val'), 'single')
    top.set(qn('w:sz'), '4')
    top.set(qn('w:color'), '999999')
    top.set(qn('w:space'), '6')
    pBdr.append(top)
    pPr.append(pBdr)

    run = p.add_run('DRA Realty Private Limited | RERA REG: PENDING | This is a system-generated document')
    run.font.size = Pt(6)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
    run.font.name = 'Calibri'
```

## Step 4 — Signature Block

```python
def add_stamp_signature_block(doc, title, name):
    p = doc.add_paragraph()
    p.add_run('\n')

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run('Authorized Signatory')
    run.bold = True
    run.font.size = Pt(10)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(f'\n\n\n({name})')
    run.font.size = Pt(10)

    p = doc.add_paragraph()
    run = p.add_run(title)
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    p = doc.add_paragraph()
    run = p.add_run('For DRA Realty Private Limited')
    run.bold = True
    run.font.size = Pt(9)
```

## Step 5 — Batch Process Multiple Documents

```python
LOGO_PATH = '/path/to/DRA_Logo.png'
DOCS_DIR = '/data/hermes/document_cache/'

LETTERHEAD_DOCS = [
    '01_Work_Order.docx',
    '03_Project_Details.docx',
    # ... all letterhead docs
]

for doc_name in LETTERHEAD_DOCS:
    doc_path = os.path.join(DOCS_DIR, doc_name)
    if not os.path.exists(doc_path):
        continue
    doc = Document(doc_path)
    create_letterhead_header(doc, LOGO_PATH)
    add_footer_line(doc)
    doc.save(doc_path)
    print(f"OK: {doc_name}")
```

## Step 6 — Upload to Drive

When per-user OAuth is unavailable (no `the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)` for the requesting user), use the global Drive token:

```python
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN_PATH = "/data/hermes/google_token.json"
FOLDER_ID = "1ksA8AvQfvC-Dwoq5goKPPTSQaw7CW8XJ"  # project folder ID

creds = Credentials.from_authorized_user_file(
    TOKEN_PATH, ["https://www.googleapis.com/auth/drive"]
)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    json.dump(json.loads(creds.to_json()), open(TOKEN_PATH, "w"), indent=2)

drive = build("drive", "v3", credentials=creds)

# Check if file exists first, update or create
query = f"'{FOLDER_ID}' in parents and name = '{drive_name}' and trashed = false"
existing = drive.files().list(q=query, fields="files(id, name)").execute().get("files", [])

if existing:
    drive.files().update(fileId=existing[0]["id"], media_body=media).execute()
else:
    drive.files().create(body=file_meta, media_body=media, fields="id, webViewLink").execute()
```

## Common Letterhead Fields for DRA Realty

| Field | Value |
|-------|-------|
| Company Name | DRA REALTY PRIVATE LIMITED |
| Corporate Office | No. 82/1, JC Industrial Layout, Kanchapura Main Road, Kanakapura Road, Bengaluru - 560062 |
| Phone | +91-9000299200 |
| Email | info@draas.com |
| GST | 29AALCD9962L1ZW |
| CIN | U45209KA2014PTC074068 |
| Brand Color (Navy) | `#1A3C6E` |
| Brand Color (Gold) | `#F7B519` (from logo pixel analysis) |

## Pitfalls

1. **`execute_code` can't run DOCX scripts with header tables** — Some complex python-docx operations (table in header, OxmlElement modifications) may silently fail in `execute_code` sandbox. Always run via `terminal(command="python3 /tmp/script.py")`.
2. **Logo image too large** — Scale logo to `Inches(1.0–1.5)`. Larger sizes overflow the header on mobile or narrow layouts.
3. **Header distance** — Set `header_distance = Cm(0.5)` to prevent logo from being cut off at top of page.
4. **Footer line** — Use `Pt(6)` for footer text so it doesn't crowd the document body.
