# Modify Existing Office DOCX on Drive and Re-upload

Pattern for downloading an existing .docx file from Google Drive, making targeted text/table changes with python-docx, and uploading the modified version back — replacing the original file.

## When to use this

- User asks to "update this agreement/letter with details from X"
- The file on Drive is an Office .docx (MIME: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`)
- The Google Docs API won't work (it's not a native Google Doc)
- You need to make surgical text replacements or insert tables into an existing template

## Complete Pipeline

```python
import sys, io
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
import docx
from googleapiclient.http import MediaIoBaseUpload

# 1. Download from Drive
s = build_service('drive', 'v3')
doc_id = 'FILE_ID_GOES_HERE'
request = s.files().get_media(fileId=doc_id)
content = request.execute()
d = docx.Document(io.BytesIO(content))

# 2. Modify paragraphs
for i, para in enumerate(d.paragraphs):
    print(f"P{i}: {para.text[:100]}")  # inspect first

# 3. Replace text preserving formatting
def replace_para(para, old, new):
    """Replace old→new in a paragraph while keeping run formatting."""
    full = para.text
    if old not in full:
        return False
    if para.runs:
        # Preserve first run's formatting
        font_name = para.runs[0].font.name
        font_size = para.runs[0].font.size
        bold = para.runs[0].bold
        for run in para.runs:
            run.text = ''
        para.runs[0].text = full.replace(old, new)
        para.runs[0].font.name = font_name
        para.runs[0].font.size = font_size
        if bold is not None:
            para.runs[0].bold = bold
    return True

# 4. Upload back to Drive (replace)
output = io.BytesIO()
d.save(output)
output.seek(0)
media = MediaIoBaseUpload(
    output,
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True
)
updated = s.files().update(fileId=doc_id, media_body=media).execute()
```

## Handling Duplicated Template Text

KRERA templates and other Indian real estate proformas often have text duplicated 2–4 times in the same paragraph (copy-paste artifacts from the template source). Example:

```
"Date: 08-06-2026Date: 08-06-2026"
"1,300.58 sq.mt. (14,000 sqft)1,300.58 sq.mt. (14,000 sqft)1,300.58 sq.mt. (14,000 sqft)"
```

**Fix approach:** Replace the entire duplicated string with a single copy:
```python
replace_para(para,
    "1,300.58 sq.mt. (14,000 sqft)1,300.58 sq.mt. (14,000 sqft)1,300.58 sq.mt. (14,000 sqft)",
    "1,300.58 sq.mt. (14,000 sqft)")
```

For severe duplication (4+ copies), use regex:
```python
import re
new_text = re.sub(r'^(Rs\. _______________________ \[Booking Amount[^\]]+\])(?:[^\]]+\])*', r'\1', para.text)
```

**Verification pass:** After all replacements, scan the document for any remaining duplicated patterns:
```python
import re
for i, para in enumerate(d.paragraphs):
    t = para.text.strip()
    if re.search(r'(\w{3,})\1', t):  # consecutive word-level repetition
        issues.append((i, t[:150]))
```

## Inserting Tables at Specific Paragraph Positions

python-docx's `add_table()` appends to the end of the document body. To place a table at a specific position (e.g. between two paragraphs), use XML manipulation:

```python
from docx.oxml.ns import qn

# Option A: Add table at end, then move it
table = d.add_table(rows=N, cols=M)
tbl_elem = table._tbl

# Find the reference paragraph
for para in d.paragraphs:
    if "TARGET TEXT" in para.text:
        para._element.addnext(tbl_elem)
        # or: para._element.addprevious(tbl_elem) for before
        break

# Option B: Build table inline at insertion point
# Create XML table element and insert directly
table_xml = docx.oxml.OxmlElement('w:tbl')
# ... build rows and cells ...
ref_elem = d.paragraphs[idx]._element
ref_elem.addnext(table_xml)  # insert after
```

### Building Table Cells with Formatted Text

```python
def make_cell(text, bold=False, size=8, align='center'):
    tc = docx.oxml.OxmlElement('w:tc')
    tcPr = docx.oxml.OxmlElement('w:tcPr')
    tcWidth = docx.oxml.OxmlElement('w:tcW')
    tcWidth.set(qn('w:w'), '0')
    tcWidth.set(qn('w:type'), 'auto')
    tcPr.append(tcWidth)
    tc.append(tcPr)

    p = docx.oxml.OxmlElement('w:p')
    pPr = docx.oxml.OxmlElement('w:pPr')
    jc = docx.oxml.OxmlElement('w:jc')
    jc.set(qn('w:val'), align)
    pPr.append(jc)
    p.append(pPr)

    r = docx.oxml.OxmlElement('w:r')
    rPr = docx.oxml.OxmlElement('w:rPr')
    if bold:
        b = docx.oxml.OxmlElement('w:b')
        rPr.append(b)
    sz = docx.oxml.OxmlElement('w:sz')
    sz.set(qn('w:val'), str(size * 2))  # half-points
    rPr.append(sz)
    r.append(rPr)

    t = docx.oxml.OxmlElement('w:t')
    t.text = text
    t.set(qn('xml:space'), 'preserve')
    r.append(t)
    p.append(r)
    tc.append(p)
    return tc
```

### Table Borders via XML

```python
tblPr = docx.oxml.OxmlElement('w:tblPr')
tblBorders = docx.oxml.OxmlElement('w:tblBorders')
for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
    border = docx.oxml.OxmlElement(f'w:{border_name}')
    border.set(qn('w:val'), 'single')
    border.set(qn('w:sz'), '4')
    border.set(qn('w:space'), '0')
    border.set(qn('w:color'), '000000')
    tblBorders.append(border)
tblPr.append(tblBorders)
table.insert(0, tblPr)
```

## Removing Elements (Paragraphs/Tables)

Remove a paragraph:
```python
para._element.getparent().remove(para._element)
```

Find and remove a specific table by its first cell content:
```python
body = d.element.body
for tbl in body.findall(qn('w:tbl')):
    first_rows = tbl.findall(qn('w:tr'))
    if first_rows:
        first_cells = first_rows[0].findall(qn('w:tc'))
        if first_cells:
            paras = first_cells[0].findall(qn('w:p'))
            if paras:
                texts = paras[0].findall(qn('w:r'))
                for t_elem in texts:
                    t_elems = t_elem.findall(qn('w:t'))
                    for t_text in t_elems:
                        if t_text.text and "SIGNATURE" in t_text.text:
                            body.remove(tbl)
                            break
```

## Alternative: Raw XML Manipulation (No python-docx)

When python-docx fails (permission denied, extreme run-splitting, or documents with complex formatting that python-docx corrupts), manipulate the docx XML directly via zipfile + ElementTree.

### Simple Text Replacement (Across All `<w:t>` Elements)

Use when the text to replace is simple and appears in one or more `<w:t>` runs:

```python
import sys, zipfile, io
from xml.etree import ElementTree as ET
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseUpload

drive = build_service('drive', 'v3')

# 1. Download original
request = drive.files().get_media(fileId='FILE_ID')
content = request.execute()

# 2. Modify XML
z = zipfile.ZipFile(io.BytesIO(content))
xml_bytes = z.read('word/document.xml')
root = ET.fromstring(xml_bytes)

ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
for t_elem in root.iter(f'{{{ns}}}t'):
    if t_elem.text and 'OLD_TEXT' in t_elem.text:
        t_elem.text = t_elem.text.replace('OLD_TEXT', 'NEW_TEXT')

new_xml = ET.tostring(root, encoding='unicode', xml_declaration=True)

# 3. Rebuild docx
output = io.BytesIO()
with zipfile.ZipFile(io.BytesIO(content), 'r') as zin:
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == 'word/document.xml':
                data = new_xml.encode('utf-8')
            zout.writestr(item, data)

# 4. Upload as NEW file (use create, not update, unless replacing)
media = MediaIoBaseUpload(
    io.BytesIO(output.getvalue()),
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True
)
result = drive.files().create(
    body={'name': 'NEW_NAME.docx', 'parents': ['FOLDER_ID']},
    media_body=media,
    fields='id, name, webViewLink'
).execute()
```

### Paragraph-Targeted Insertion (Find Paragraph → Insert After Anchor Run)

When you need to insert text at a specific position within a specific paragraph (e.g., add "as represented by their GPA Holder..." after "Bangalore East" in the landowner description paragraph):

```python
def insert_in_paragraph(root, search_text, anchor_text, insert_text):
    """Insert insert_text after the run containing anchor_text in the 
    first paragraph whose joined text contains search_text."""
    ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    for p in root.iter(f'{{{ns}}}p'):
        runs = list(p.iter(f'{{{ns}}}r'))
        full = ''.join(''.join(t.text or '' for t in r.iter(f'{{{ns}}}t')) for r in runs)
        if search_text not in full:
            continue
        for r in runs:
            r_text = ''.join(t.text or '' for t in r.iter(f'{{{ns}}}t'))
            if anchor_text in r_text:
                t_elems = list(r.iter(f'{{{ns}}}t'))
                if t_elems:
                    t_elems[-1].text = (t_elems[-1].text or '') + insert_text
                    return 1
        break
    return 0

# Usage
count = insert_in_paragraph(root,
    search_text="Landowners of the Plot No. 1-B, Khatha No. 4/124",
    anchor_text="Bangalore East",
    insert_text=", as represented by...")
```

### Inspecting Run Structure First

Always inspect the raw XML run structure before attempting modifications — text may be split across many runs:

```python
all_paras = re.findall(r'<w:p[ >].*?</w:p>', xml_str, re.DOTALL)
for i, para in enumerate(all_paras):
    texts = re.findall(r'<w:t[^>]*>([^<]*)</w:t>', para)
    joined = ''.join(texts)
    if 'KEY_PHRASE' in joined:
        print(f"=== Paragraph {i} ===")
        for j, t in enumerate(texts):
            print(f"  Run [{j}]: '{t}'")
```

### When Incremental Fixes Fail — Rebuild from Original

If multiple incremental modifications make the document messy (displaced text, broken runs), discard the working copy and rebuild from the original file with ALL changes applied in one pass:

```python
# Single function that does ALL replacements + paragraph inserts
def rebuild_from_original(file_id, replacements_dict, para_inserts_list):
    request = drive.files().get_media(fileId=file_id)  # ALWAYS use original file_id
    content = request.execute()
    # ... apply all changes in one pass
    # Upload as new file with a fresh name
```

This avoids the cumulative error problem where fix #3 undoes fix #1.

## Pitfalls

1. **Run splitting** — DOCX templates may split a single logical word across multiple runs (e.g. "Rs." in 3 runs: `R`, `s`, `.`). Simple `para.text` based replacement works at the paragraph level, but if the split is across runs, replace the full paragraph text in the first run and clear the rest.
2. **Formatting loss** — Clearing all runs and writing to the first one loses per-run formatting differences (different colors/sizes per word). The `replace_para` helper above preserves first-run formatting, which is acceptable for uniform paragraphs.
3. **Table at document end** — `d.add_table()` always appends to the end. Use XML `addnext`/`addprevious` to reposition. These work on sibling elements within the document body.
4. **`addnext` ordering** — If inserting a heading paragraph AND a table, insert them in reverse order (table first, then heading above it) because `addnext` inserts immediately after:
   ```python
   ref_elem.addnext(table_elem)      # table after ref
   ref_elem.addnext(heading_elem)    # heading after ref, pushing table down
   ```
5. **Upload overwrites** — `drive.files().update(fileId=doc_id, media_body=media)` replaces the file entirely. The old version is not recoverable from the API (Drive keeps version history in the UI). For destructive operations, consider creating a copy first.
6. **Venv required** — All GWS + docx operations need `/opt/hermes/.venv/bin/python3`. System python lacks `googleapiclient`, `python-docx`, etc.
