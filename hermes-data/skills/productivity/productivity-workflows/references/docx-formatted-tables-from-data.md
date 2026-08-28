# DOCX — Formatted Tables & Structured Documents from Data

When the user asks for a **Word document (.docx)** from structured data — tables extracted from emails, timeline conversions, itemized checklists, requisition lists, status trackers.

## Environment Setup

The system venv is read-only. Always create a temporary venv:

```bash
cd /opt/data && uv venv --clear /tmp/docx_venv 2>/dev/null
source /tmp/docx_venv/bin/activate && uv pip install python-docx
```

Run scripts with `source /tmp/docx_venv/bin/activate && python3 script.py`.

## Core Pattern: Table from Data List

Structure your data as a list of tuples where each row has a `row_type` to distinguish section headers from data rows:

```python
rows_data = [
    # ("seq", "cat", "document", "adv_status", "your_status", "row_type")
    ("",     "A",  "SECTION TITLE", "", "", "section"),
    ("1",    "A",  "Document description...", "PENDING", "", "normal"),
    ("2",    "A",  "Another document...", "RECEIVED ✓", "", "normal"),
]
```

Then build the table in one pass.

## Table Construction Recipe

### 1. Add the table

```python
num_rows = len(rows_data)
table = doc.add_table(rows=num_rows + 1, cols=5)
table.style = 'Table Grid'
table.alignment = WD_TABLE_ALIGNMENT.CENTER
```

### 2. Set column widths (total ~7.5" for A4 with 1.5cm margins)

```python
col_widths = [0.35, 0.3, 3.85, 1.2, 1.8]  # inches
for i, cw in enumerate(col_widths):
    cells[i].width = Inches(cw)
```

### 3. Header row — dark blue with white text

```python
header_texts = ['#', 'Cat', 'Document Required', 'Adv. Status', 'Your Status / Remarks']
for i, ht in enumerate(header_texts):
    cell = table.rows[0].cells[i]
    add_cell_text(cell, ht, size=7, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF), align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell_shading(cell, "1F4E79")
    set_cell_border(cell, top="1F4E79", left="1F4E79", bottom="1F4E79", right="1F4E79")
```

### 4. Merge section header rows

```python
merged = cells[0].merge(cells[1]).merge(cells[2]).merge(cells[3]).merge(cells[4])
add_cell_text(merged, f"  {section_title}", size=8, bold=True, color=RGBColor(0x1F, 0x4E, 0x79))
set_cell_shading(merged, "D6E4F0")
```

### 5. Status color coding

```python
is_received = "RECEIVED" in adv_status
adv_color = RGBColor(0x1B, 0x7A, 0x2B) if is_received else RGBColor(0xCC, 0x66, 0x00)
add_cell_text(cell_adv, adv_status, size=7, bold=is_received, color=adv_color, align=WD_ALIGN_PARAGRAPH.CENTER)
if is_received:
    set_cell_shading(cell_adv, "E8F5E9")  # green background
```

### 6. Editable column styling

```python
add_cell_text(cell_your, "", size=7)
set_cell_shading(cell_your, "FFFDE7")  # light yellow
```

## Helper Functions (battery-included)

```python
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

def set_cell_shading(cell, color):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def set_cell_border(cell, **kwargs):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    parts = ''.join(
        f'<w:{e} w:val="single" w:sz="4" w:space="0" w:color="{c}"/>'
        for e, c in kwargs.items()
    )
    borders = parse_xml(f'<w:tcBorders {nsdecls("w")}>{parts}</w:tcBorders>')
    tcPr.append(borders)

def add_cell_text(cell, text, size=8, bold=False, color=RGBColor(0x1a, 0x1a, 0x1a), align=None):
    cell.text = ''
    p = cell.paragraphs[0]
    if align:
        p.alignment = align
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(str(text))
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.name = 'Calibri'
    r.font.color.rgb = color
```

**⚠️ CRITICAL — Never chain `.bold = True` after `add_run()`:**
```python
# BROKEN: returns True, breaks subsequent calls
p.add_run('text').bold = True  # .bold returns True

# CORRECT
r = p.add_run('text')
r.bold = True
```

## Structuring Complex Documents (e.g., HTML timeline → DOCX)

When converting a styled HTML page to DOCX, map each HTML section type to a DOCX pattern:

| HTML Section | DOCX Pattern |
|---|---|
| Title + subtitle | Centered `<h1>` styled paragraph |
| Summary cards (grid) | Table with colored cells, compact text |
| Key-value pairs (info grid) | Paragraphs with bold label + normal value (`add_info_row`) |
| Timeline items | Date (small, bold, colored) → Title (medium bold) → Body (normal) → Source (italic, small) |
| Phase labels | Left-aligned heading with underline |
| Data tables | `doc.add_table()` with `Table Grid` style |
| Footer | Small, centered, italic |

**`add_info_row` pattern for key-value pairs:**
```python
def add_info_row(label, value):
    p = doc.add_paragraph()
    r1 = p.add_run(label + ":  ")
    r1.font.bold = True
    r1.font.size = Pt(11)
    r1.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    r2 = p.add_run(value)
    r2.font.size = Pt(11)
    r2.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
    p.paragraph_format.space_after = Pt(4)
```

## Upload DOCX to Google Drive

After saving the local .docx file, upload and get a shareable link:

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

service = build_service('drive', 'v3')
media = MediaFileUpload(local_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
meta = {'name': 'FileName.docx', 'description': '...'}
uploaded = service.files().create(body=meta, media_body=media, fields='id,name,webViewLink').execute()
service.permissions().create(fileId=uploaded['id'], body={'type': 'anyone', 'role': 'reader'}).execute()
print(uploaded['webViewLink'])
```

## Known Pitfalls

- **`set_cell_border` XML building**: Build ALL `<w:bottom>`, `<w:top>`, etc. elements into ONE string then parse once. Parsing empty `<w:tcBorders>` then appending child elements separately causes XMLSyntaxError.
- **No `<ol>` / `<li>` in HTML import** (that's Google Docs, not relevant for python-docx — in DOCX you control lists directly via `doc.add_paragraph(text, style='List Bullet')`).
- **Calibri is the safest font** — works in all Word versions. Set once in Normal style: `style.font.name = 'Calibri'`.
- **Cell width must be set before populating text** — set all cells' `.width = Inches(cw)` before calling `add_cell_text`.
- **Table Grid style provides visible borders** — always set `table.style = 'Table Grid'` unless you want borderless tables.
- **Temporary venv does not persist** across terminal calls — re-source every time.

## Worked Examples

- `Gunjur_Sy40_Additional_Requisition_List.docx` — 52-item, 14-section table with colored status, merged section headers, editable column. Generated from an email table.
- `Bin_Mangala_Binnamangala_Property_Timeline.docx` — 20-year timeline HTML → DOCX conversion with cards, phases, info grids, and tables.
