# Area Statement .docx Refinement — Column Removal & Notes

After the initial area statement .docx is created, the user often requests iterative refinements: removing columns, adding notes, reformatting. This reference covers the post-creation editing workflow for .docx files stored on Drive.

## Trigger

- User already has a .docx area statement on Drive and asks to:
  - "Remove [column name] column"
  - "Add notes after the table"
  - "Change layout / orientation"
  - "Add a legend/color key section"
  - Any iterative table refinement

## Key Difference from Google Sheets

The area statement .docx is a **binary .docx file** uploaded to Drive, NOT a native Google Doc. This means:
- **Google Docs API is UNUSABLE** — it returns `"This operation is not supported for this document. The document must not be an Office file."`
- **Must use Drive API** to download the file, edit locally with python-docx, and re-upload

## Workflow

### Step 1: Identify the File Type

```python
from tools.gws_auth import build_service

drive = build_service('drive', 'v3', service_name='google-draas')
meta = drive.files().get(fileId=DOC_ID, fields='id, name, mimeType, webViewLink').execute()
print(f"Name: {meta['name']}")
print(f"MIME: {meta['mimeType']}")
```

- If `mimeType` is `application/vnd.openxmlformats-officedocument.wordprocessingml.document` → it's a binary .docx
- If `mimeType` is `application/vnd.google-apps.document` → it's a native Google Doc (use Docs API)

### Step 2: Download the .docx

Use `files().get_media()` (NOT `export()` which only works for Docs Editors files):

```python
from googleapiclient.http import MediaIoBaseDownload
import io

request = drive.files().get_media(fileId=DOC_ID)
file_content = io.BytesIO()
downloader = MediaIoBaseDownload(file_content, request)
done = False
while not done:
    status, done = downloader.next_chunk()

local_path = '/tmp/area_statement.docx'
with open(local_path, 'wb') as f:
    f.write(file_content.getvalue())
```

### Step 3: Inspect the .docx Structure

```python
from docx import Document
from docx.oxml.ns import qn

doc = Document(local_path)

# List all paragraphs
for i, para in enumerate(doc.paragraphs):
    text = para.text.strip()
    if text:
        print(f"P{i}: [{para.style.name}] {text[:120]}")

# List all tables
for i, table in enumerate(doc.tables):
    print(f"Table {i}: {len(table.rows)} rows x {len(table.columns)} cols")
    header = [cell.text.strip()[:30] for cell in table.rows[0].cells]
    print(f"  Headers: {header}")

# Find the full element structure (tables, paragraphs, section breaks)
body = doc.element.body
children = list(body)
for i, child in enumerate(children):
    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
    text = ''
    if tag == 'p':
        for r in child.findall(qn('w:r')):
            for t in r.findall(qn('w:t')):
                text += t.text or ''
    print(f"  [{i}] {tag}: '{text.strip()[:80]}'")
```

### Step 4: Remove a Column from the Table

python-docx does NOT have a built-in `delete_column()` method. Use the XML approach:

```python
from docx.oxml import OxmlElement
from lxml import etree

def remove_column_from_table(table, col_index):
    """
    Remove a column by index from a python-docx table.
    This removes the corresponding cell from every row.
    """
    for row in table.rows:
        cells = row._tr.findall(qn('w:tc'))
        if col_index < len(cells):
            cell = cells[col_index]
            row._tr.remove(cell)
    # Also update the grid (column count) in the table properties
    tbl_grid = table._tbl.find(qn('w:tblGrid'))
    if tbl_grid is not None:
        grid_cols = tbl_grid.findall(qn('w:gridCol'))
        if col_index < len(grid_cols):
            tbl_grid.remove(grid_cols[col_index])

# Usage: remove the "Shape" column (index 3) and "Remarks" column (index 8)
remove_column_from_table(doc.tables[0], 3)  # Remove Shape column
# After removing index 3, indices shift left
remove_column_from_table(doc.tables[0], 7)  # Remove Remarks column (was index 8, now 7)
```

**Important:** After each removal, all subsequent column indices shift left by 1. Remove rightmost columns first, or remove in order and recalculate indices.

### Step 5: Add Notes After the Table

Insert paragraphs between the last table and the section properties (sectPr):

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

body = doc.element.body
children = list(body)

# Find the section properties index (end of document)
sect_pr_idx = None
for i, child in enumerate(children):
    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
    if tag == 'sectPr':
        sect_pr_idx = i
        break

def make_paragraph(text, bold=False, font_size=9, font_name='Calibri'):
    """Create a clean w:p element with given text."""
    p = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    spacing = OxmlElement('w:spacing')
    spacing.set(qn('w:after'), '60')  # 3pt after
    spacing.set(qn('w:line'), '240')
    spacing.set(qn('w:lineRule'), 'auto')
    pPr.append(spacing)
    p.append(pPr)
    
    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), font_name)
    rFonts.set(qn('w:hAnsi'), font_name)
    rPr.append(rFonts)
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), str(font_size * 2))
    rPr.append(sz)
    if bold:
        b = OxmlElement('w:b')
        rPr.append(b)
    r.append(rPr)
    t = OxmlElement('w:t')
    t.set(qn('xml:space'), 'preserve')
    t.text = text
    r.append(t)
    p.append(r)
    return p

# Insert notes — insert in reverse order so they appear in the right sequence
notes = [
    "",  # blank line before notes
    "NOTES:",
    "1. All dimensions are in feet and inches as per the approved Master Plan.",
    "2. Plot areas are calculated from the approved layout and are subject to actual physical verification at the site.",
    "3. Villa FSI and Villa SBUA are indicative and subject to final design approval by the architect and statutory authorities.",
    "4. Corner plots are identified with 🟨 YELLOW. Standard plots with 🟩 GREEN. North-South plots with 🟦 BLUE. Amenity areas with 🟪 PURPLE.",
    "5. The layout is subject to DTCP and RERA approvals as applicable.",
    "6. All measurements are subject to recheck at the time of registration and possession.",
]
for note_text in reversed(notes):
    p_elem = make_paragraph(note_text, bold=(note_text == "NOTES:"))
    body.insert(sect_pr_idx, p_elem)
```

### Step 6: Save and Upload

```python
doc.save(local_path)

# Upload back to Drive (update existing file)
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload(
    local_path,
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True
)
updated = drive.files().update(fileId=DOC_ID, media_body=media).execute()
print(f"Updated: {updated.get('id')}")
print(f"Link: https://docs.google.com/document/d/{updated.get('id')}/edit")
```

### Step 7: Verify

Re-download and re-parse the file to confirm the column removal and notes insertion worked:

```python
request = drive.files().get_media(fileId=DOC_ID)
verify_content = io.BytesIO()
downloader = MediaIoBaseDownload(verify_content, request)
done = False
while not done:
    status, done = downloader.next_chunk()

with open('/tmp/verify.docx', 'wb') as f:
    f.write(verify_content.getvalue())

doc2 = Document('/tmp/verify.docx')
for i, p in enumerate(doc2.paragraphs):
    text = p.text.strip()
    if text:
        print(f"P{i}: {text[:120]}")
for i, table in enumerate(doc2.tables):
    header = [cell.text.strip()[:30] for cell in table.rows[0].cells]
    print(f"Table {i} headers: {header}")
```

## Standard Notes for Area Statements

When the user says "add notes after the table," use these standard notes unless they specify otherwise:

```
NOTES:
1. All dimensions are in feet and inches as per the approved Master Plan.
2. Plot areas are calculated from the approved layout and are subject to actual physical verification at the site.
3. Villa FSI (Gross / Visible / Restricted) and Villa SBUA (Gross / Visible / Restricted) are indicative and subject to final design approval by the architect and statutory authorities.
4. Corner plots are identified with 🟨 YELLOW highlighting. Standard plots with 🟩 GREEN. North-South plots with 🟦 BLUE. Amenity areas with 🟪 PURPLE.
5. The layout is subject to DTCP and RERA approvals as applicable.
6. All measurements are subject to recheck at the time of registration and possession.
```

## Common Column Removal Patterns (Ranka Oasis Area Statement)

| Column | Position | Reason for Removal |
|--------|----------|-------------------|
| Shape | Typically col 3 | Redundant — dimensions already convey shape |
| Remarks | Typically last col | Data moved to notes section or legend |
| Survey No | Varies | Not on master plan; added separately |

## Pitfalls

- **Column indices shift after each removal.** Remove rightmost columns first, or recalculate indices after each removal. If you remove index 3 first, the column that was at index 8 is now at index 7.
- **Google Docs API does NOT work on .docx files.** The error `"This operation is not supported for this document. The document must not be an Office file."` means you must use the Drive API download/edit/upload cycle instead.
- **python-docx has no `delete_column()` method.** You must remove the `w:tc` elements from each row's `w:tr` AND the `w:gridCol` from `w:tblGrid`. Both are required — removing cells alone leaves a grid with wrong column count.
- **Section properties (`sectPr`) is always the last child** of `w:body`. Insert notes before it, not after. If you insert after it, the notes won't render.
- **File size can increase** after multiple edits because python-docx preserves the full XML tree. Each edit adds new elements without removing old ones. For heavily-edited files, consider regenerating the docx from scratch.
- **Always verify the upload** by re-downloading and re-parsing. The Drive API's `update()` returns success even if the file was corrupted locally.
- **Font size in half-points**: In OOXML, `w:sz` value = font_size × 2. So 9pt → `w:val="18"`, 10pt → `w:val="20"`.