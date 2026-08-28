# Editing Existing .docx Files on Drive (In-Place Updates)

This reference covers the full workflow for editing a .docx file already stored on Drive — fixing paragraph spacing, filling text blanks, updating the date — then re-uploading to preserve the same link.

## When to Use This

- The file on Drive is a native **.docx** (MIME: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`), not a Google Doc
- The Docs API returns: `"This operation is not supported for this document. The document must not be an Office file."`
- You need to edit **content** and **formatting** (not just viewing)

## Complete Workflow

### Step 1: Check file type and resolve account

```python
drive = build_service('drive', 'v3', service_name='google-draas')
meta = drive.files().get(fileId=FILE_ID, fields='id,name,mimeType,webViewLink').execute()
print(meta['mimeType'])  # Should be application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

### Step 2: Download the .docx

```python
from googleapiclient.http import MediaIoBaseDownload
import io

req = drive.files().get_media(fileId=FILE_ID)
fh = io.BytesIO()
dl = MediaIoBaseDownload(fh, req)
done = False
while not done:
    status, done = dl.next_chunk()
with open('original.docx', 'wb') as f:
    f.write(fh.getvalue())
```

### Step 3: Inspect paragraph structure with python-docx

```python
from docx import Document
from docx.shared import Pt

doc = Document('original.docx')
for i, para in enumerate(doc.paragraphs):
    pf = para.paragraph_format
    if para.text.strip():
        print(f"P{i:2d} | ls={pf.line_spacing} sa={pf.space_after} sb={pf.space_before} | {para.text[:60]!r}")
```

### Step 4: Check the raw XML for docDefaults (spacing root cause)

```python
import zipfile, re
with zipfile.ZipFile('original.docx', 'r') as z:
    doc_xml = z.read('word/document.xml').decode('utf-8')

# Look for docDefaults spacing
dd = re.search(r'<w:docDefaults>.*?</w:docDefaults>', doc_xml, re.DOTALL)
if dd:
    print(dd.group(0))  # Shows w:after, w:line values

# Check if pPr exists on any paragraphs
paras = re.findall(r'<w:p\b.*?</w:p>', doc_xml, re.DOTALL)
for i, p in enumerate(paras[:10]):
    ppr = re.search(r'<w:pPr>.*?</w:pPr>', p, re.DOTALL)
    print(f"P{i}: pPr={'YES' if ppr else 'NO'}")
```

### Step 5: CRITICAL PITFALL — python-docx spacing writes silently fail

```python
# THIS DOES NOT RELIABLY WORK:
doc = Document('original.docx')
for para in doc.paragraphs:
    para.paragraph_format.space_after = Pt(0)
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.line_spacing = 1.0
doc.save('fixed.docx')

# VERIFY - if pPr is still missing from XML, the settings were NOT written:
with zipfile.ZipFile('fixed.docx', 'r') as z:
    xml = z.read('word/document.xml').decode('utf-8')
paras = re.findall(r'<w:p\b.*?</w:p>', xml, re.DOTALL)
for i, p in enumerate(paras[:5]):
    ppr = re.search(r'<w:pPr>.*?</w:pPr>', p, re.DOTALL)
    spacing_in = '<w:spacing' in (ppr.group(0) if ppr else '')
    print(f"P{i}: pPr={bool(ppr)} spacing={spacing_in}")
```

**Fix: use lxml for direct XML manipulation**

```python
import zipfile, io
from lxml import etree

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

with zipfile.ZipFile('original.docx', 'r') as z:
    doc_xml = z.read('word/document.xml')

root = etree.fromstring(doc_xml)
body = root.find(f'.//{W}body')
paras = list(body.findall(f'{W}p'))

for i, p in enumerate(paras):
    ppr = p.find(f'{W}pPr')
    if ppr is None:
        ppr = etree.SubElement(p, f'{W}pPr')
        p.insert(0, ppr)
    spacing = ppr.find(f'{W}spacing')
    if spacing is None:
        spacing = etree.SubElement(ppr, f'{W}spacing')
        ppr.append(spacing)
    
    # Clear any existing attrs and set our own
    for attr in list(spacing.attrib.keys()):
        del spacing.attrib[attr]
    spacing.set(f'{W}line', '240')        # 240 = single spacing
    spacing.set(f'{W}lineRule', 'auto')
    spacing.set(f'{W}after', '0')
    spacing.set(f'{W}before', '0')

# Write back to zip
xml_bytes = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
buffer = io.BytesIO()
with zipfile.ZipFile('original.docx', 'r') as zin:
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == 'word/document.xml':
                data = xml_bytes
            zout.writestr(item, data)
with open('fixed.docx', 'wb') as f:
    f.write(buffer.getvalue())
```

### Step 6: Fill text across multiple runs (dots/blanks pitfall)

Placeholders like `…………` are often split across adjacent `<w:r>` runs. Simple `replace()` on paragraph text only hits one run. Fix: iterate each run.

```python
from lxml import etree

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

for j, r in enumerate(runs_on_paragraph):
    t = r.find(f'{W}t')
    if t is not None and t.text and '…' in t.text:
        # First dot run → death date
        t.text = t.text.replace('………', '20th July 2022')
        t.text = t.text.rstrip('.…')
    # If run becomes empty, remove it:
    if not t.text.strip():
        paragraph_element.remove(r)
```

**Pattern for the date (which is on the same line as "From")**:

```python
# Date is typically in runs on P0:
# Run 0: "From", Run 1: "   {spaces}2", Run 2: "nd", Run 3: " July 2026"
p0_runs = list(p0.iter(f'{W}r'))
for j, r in enumerate(p0_runs):
    t = r.find(f'{W}t')
    if t is not None:
        if j == 1:  t.text = t.text.rstrip('2')
        elif j == 2:  t.text = '17th'
        elif j == 3:  t.text = ' August 2026'
```

### Step 7: Use a "FILLED" reference doc to extract known values

When a previously filled version exists on Drive, download it to see exactly what values go where:

```python
# Search for the filled version
results = drive.files().list(
    q="name contains 'Giving Effect' and name contains 'FILLED'",
    fields='files(id,name)'
).execute()

# Download and extract filled values
from docx import Document
filled_doc = Document('filled.docx')
for para in filled_doc.paragraphs:
    if 'passed away on' in para.text.lower():
        print(para.text)  # Shows: "Mr Dinesh ... passed away on 20th July 2022 ... Pan number is AHVPR5168E"
```

### Step 8: Upload in-place (same file ID, same link)

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload('fixed.docx',
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True)
updated = drive.files().update(
    fileId=FILE_ID,
    media_body=media,
    body={'name': 'Updated File Name.docx'},
    fields='id,name,mimeType,size,modifiedTime'
).execute()
print("Link preserved:", f"https://docs.google.com/document/d/{FILE_ID}/edit")
```

### Step 9: Visual verification (render + vision_analyze)

```python
# Convert to temp Google Doc and export PDF
media2 = MediaFileUpload('fixed.docx',
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True)
temp_doc = drive.files().create(
    body={'name': 'TMP_render', 'mimeType': 'application/vnd.google-apps.document'},
    media_body=media2, fields='id'
).execute()

req = drive.files().export_media(fileId=temp_doc['id'], mimeType='application/pdf')
# ... download ...
drive.files().delete(fileId=temp_doc['id']).execute()  # cleanup

# Render to PNG and verify
# pdftoppm -png -r 200 verify.pdf verify_page
# vision_analyze(image_url='verify_page-1.png', question='...')
```

## Understanding docDefaults Spacing Values

The document defaults live in `word/styles.xml` (NOT `word/document.xml`):

```xml
<w:docDefaults>
  <w:pPrDefault>
    <w:pPr>
      <w:spacing w:after="160" w:line="259" w:lineRule="auto"/>
    </w:pPr>
  </w:pPrDefault>
</w:docDefaults>
```

| Attribute | Value | Meaning |
|-----------|-------|---------|
| `w:after` | 160 | 160 twips ≈ 8pt space after each paragraph |
| `w:line` | 259 | 259/240 = 1.08 line spacing (slightly more than single) |
| `w:lineRule` | auto | Auto line spacing (font-size-based) |
| `w:line="240"` | 240 | 240/240 = **1.0** — true single spacing |

To override these per-paragraph, you MUST add explicit `<w:pPr><w:spacing .../></w:pPr>` via lxml — python-docx may not write them.