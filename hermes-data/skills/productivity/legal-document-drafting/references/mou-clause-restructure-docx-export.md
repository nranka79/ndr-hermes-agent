# MOU Clause Restructure with Yellow Highlighting (Google Doc → .docx Export)

When you need to modify an MOU in Google Docs with **yellow highlighting on all changes**, use this workflow. The Google Docs API (`batchUpdate` with `insertText`) cannot apply `w:highlight` yellow to text — only .docx-level editing via lxml can produce highlighting that Google Docs renders correctly.

## When to use: Docs API vs .docx export

| Scenario | Approach |
|----------|----------|
| Simple find-and-replace text (no highlighting) | Docs API: `batchUpdate` with `replaceAllText` |
| Insert new paragraphs without highlighting | Docs API: `batchUpdate` with `insertText` |
| **Any change requiring yellow highlight** | **.docx export → lxml edit → upload as .docx** |
| Bold/italic formatting changes only | Docs API: `updateTextStyle` |
| Changes to tables inside the document | .docx export (Docs API table editing is fragile) |

## Workflow

### 1. Export the Google Doc as .docx

```python
import os
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseDownload
import io

drive = build_service('drive', 'v3', service_name='google-draas')

request = drive.files().export_media(
    fileId=DOC_ID,
    mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
)
f = io.BytesIO()
downloader = MediaIoBaseDownload(f, request)
done = False
while not done:
    status, done = downloader.next_chunk()

with open('/tmp/mou_original.docx', 'wb') as out:
    out.write(f.getvalue())
```

### 2. Inspect the document structure

Extract all paragraph texts with their index to map landmarks:

```python
import zipfile
from lxml import etree

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

with zipfile.ZipFile('/tmp/mou_original.docx', 'r') as z:
    xml_bytes = z.read('word/document.xml')

tree = etree.fromstring(xml_bytes)
body = tree.find(f'{W}body')
paras = list(body.iter(f'{W}p'))

def get_para_text(p):
    parts = []
    for t in p.iter(f'{W}t'):
        if t.text: parts.append(t.text)
    return ''.join(parts)

for i, p in enumerate(paras):
    txt = get_para_text(p)[:120]
    print(f"P{i:3d}: {txt}")
```

### 3. Helper functions (reusable)

```python
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
NS_XML = '{http://www.w3.org/XML/1998/namespace}space'

def make_hl_run(text, bold=False):
    """Create a w:r with yellow w:highlight"""
    r = etree.Element(f'{W}r')
    rPr = etree.SubElement(r, f'{W}rPr')
    hl = etree.SubElement(rPr, f'{W}highlight')
    hl.set(f'{W}val', 'yellow')
    sz = etree.SubElement(rPr, f'{W}sz')
    sz.set(f'{W}val', '22')
    szCs = etree.SubElement(rPr, f'{W}szCs')
    szCs.set(f'{W}val', '22')
    if bold:
        etree.SubElement(rPr, f'{W}b')
        etree.SubElement(rPr, f'{W}bCs')
    t = etree.SubElement(r, f'{W}t')
    t.set(NS_XML, 'preserve')
    t.text = text
    return r

def make_hl_para(text, bold=False):
    """Full paragraph with yellow highlight"""
    p = etree.Element(f'{W}p')
    pPr = etree.SubElement(p, f'{W}pPr')
    ps = etree.SubElement(pPr, f'{W}pStyle')
    ps.set(f'{W}val', 'Normal')
    sp = etree.SubElement(pPr, f'{W}spacing')
    sp.set(f'{W}after', '120')
    sp.set(f'{W}line', '360')
    sp.set(f'{W}lineRule', 'auto')
    p.append(make_hl_run(text, bold=bold))
    return p

def make_empty_para():
    p = etree.Element(f'{W}p')
    pPr = etree.SubElement(p, f'{W}pPr')
    sp = etree.SubElement(pPr, f'{W}spacing')
    sp.set(f'{W}after', '120')
    sp.set(f'{W}line', '360')
    sp.set(f'{W}lineRule', 'auto')
    return p

def get_para_text(p):
    parts = []
    for t in p.iter(f'{W}t'):
        if t.text: parts.append(t.text)
    return ''.join(parts)

def get_body_index(para_idx, paras_list):
    """Get body child index from paragraph index (counting only w:p elements)"""
    count = 0
    for bi, child in enumerate(list(body)):
        if child.tag == f'{W}p':
            if count == para_idx:
                return bi
            count += 1
    return None

def set_para_text_with_hl(p, text):
    """Replace all runs in an existing paragraph with yellow-highlighted text"""
    for r in list(p.iter(f'{W}r')):
        p.remove(r)
    p.append(make_hl_run(text))
```

### 4. MOU edit patterns

#### Pattern D — Replace a clause paragraph entirely (e.g. Clause 2.2)

Find the paragraph by its text content and replace all runs with a single highlighted run:

```python
# Find by text
for i, p in enumerate(paras):
    if "2.2.INITIAL DEPOSIT" in get_para_text(p):
        target = p
        break

set_para_text_with_hl(target, "2.2. INITIAL DEPOSIT: The Second Party shall pay...")
```

#### Pattern E — Insert new clauses between existing clauses (e.g. new Clause 3.6)

Build new highlighted paragraphs and insert at the correct body position:

```python
new_paras = []
new_paras.append(make_hl_para("3.6. NEW HEADING:", bold=True))
new_paras.append(make_hl_para("(a) Text of sub-clause..."))
new_paras.append(make_hl_para("(b) More text..."))
new_paras.append(make_empty_para())

# Find body index of paragraph AFTER insertion point
b_next = get_body_index(idx_of_next_clause, paras)

# Insert in reverse order to maintain sequence
for new_p in reversed(new_paras):
    body.insert(b_next, new_p)
```

#### Pattern F — Append text to an existing paragraph (e.g. Clause 4.3 Grade A devs)

Add a new yellow-highlighted run at the end of the existing paragraph:

```python
para = paras[target_idx]
runs = list(para.iter(f'{W}r'))
if runs:
    hl_run = make_hl_run(" New text to append at the end. ")
    para.insert(list(para).index(runs[-1]) + 1, hl_run)
```

#### Pattern G — Remove a clause range and replace with new content

Find the start and end para indices, remove all body children in that range, then insert replacements:

```python
b_start = get_body_index(start_idx, paras)
b_end_exclusive = get_body_index(end_idx, paras)

# Remove
children_to_remove = []
for i, child in enumerate(list(body)):
    if i >= b_start and i < b_end_exclusive:
        children_to_remove.append(child)
for child in children_to_remove:
    body.remove(child)

# Insert replacements (in reverse order)
for new_p in reversed(new_replacement_paras):
    body.insert(b_start, new_p)
```

#### Pattern H — Update numerical references across the document

After changing a key figure (e.g. Rs. 10 Cr → Rs. 2 Cr), scan all paragraphs for stale references and fix them:

```python
for p in paras:
    txt = get_para_text(p)
    if "10,00,00,000" in txt or "Ten Crores" in txt:
        set_para_text_with_hl(p, txt.replace("10,00,00,000", "2,00,00,000").replace("Ten Crores", "Two Crores Only"))
```

### 5. Save and repack .docx

```python
# Save XML
tree.write(xml_path, xml_declaration=True, encoding='UTF-8')

# Repack zip
os.chdir(tmp_dir)
with zipfile.ZipFile('/tmp/mou_updated.docx', 'w', zipfile.ZIP_DEFLATED) as outzip:
    for dirpath, _, filenames in os.walk('.'):
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            outzip.write(full, os.path.relpath(full, '.'))
```

### 6. Upload .docx to Drive as a new file

Do NOT use `files().update()` for this workflow (the source is a Google Doc, not a .docx). Create a new file:

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload(
    '/tmp/mou_updated.docx',
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True
)

new_file = {
    'name': 'Original Name - UPDATED.docx',
    'description': 'Updated with changes highlighted in YELLOW.',
    'mimeType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

f = drive.files().create(body=new_file, media_body=media,
    fields='id,name,webViewLink').execute()
```

### 7. Verify highlighting

Re-read the uploaded .docx and check every changed paragraph has `<w:highlight w:val="yellow">`:

```python
with zipfile.ZipFile('/tmp/mou_updated.docx', 'r') as z:
    xml_bytes = z.read('word/document.xml')
vtree = etree.fromstring(xml_bytes)
vbody = vtree.find(f'{W}body')
vparas = list(vbody.iter(f'{W}p'))

hl_count = sum(len(p.findall(f'.//{W}highlight')) for p in vparas)
print(f"Total highlight elements: {hl_count}")
```

## Pitfalls

- **Yellow shading vs highlight**: `WD_COLOR_INDEX.YELLOW` in python-docx creates `<w:shd w:fill="yellow">` (paragraph shading) which Google Docs does NOT render as yellow highlighting. Google Docs only recognises `<w:highlight w:val="yellow">`. Always edit raw XML with lxml, never use python-docx for yellow highlighting.

- **Index shifting after modifications**: After inserting/removing body children, the `paras` list (from `body.iter(...)`) is stale. Re-parse it after each major edit to get correct indices for subsequent operations.

- **Reverse-order insertion**: When inserting multiple paragraphs at the same position, insert in reverse order so the first element ends up at the correct position.

- **Empty paragraph spacing**: Insert `make_empty_para()` between clause headings and sub-clauses for visual clarity — without them, highlighted clauses run together in Google Docs.

- **Google Doc → .docx conversion quirks**: Tables in the original Google Doc become table XML in the .docx. The `w:p` elements inside table cells won't appear in `body.iter(f'{W}p')`. If you need to edit text inside tables, traverse `w:tbl` elements separately.

- **Upload as new file, not in-place**: The source is a native Google Doc (.gdoc), not a .docx on Drive. `files().update()` on the Google Doc ID would replace it with a .docx, breaking the link for anyone viewing it as a Google Doc. Always create a new file with a clear "[UPDATED]" name suffix and share the new link.

- **Verify after every major edit**: After removing and replacing a clause range, verify the paragraph count and highlight count before the next edit. A bug in index calculation can silently corrupt nearby text.