# Editing an Existing .docx on Drive (Spacing + Text Blanks)

For files that are **native .docx** (Office files) on Google Drive — NOT native Google Docs. The Docs API refuses them with `"This operation is not supported for this document. The document must not be an Office file."`

## When to use this

- The user wants formatting fixes (line spacing, paragraph gaps) on an existing .docx uploaded to Drive
- The user wants blanks (dates, PAN numbers, names) filled in from a FILLED copy of the same document
- The user wants a visual review of the document before/after changes ("review from a vision perspective")

## The python-docx trap: `paragraph_format` settings silently DON'T persist

**Observed 2026-08-17:** `para.paragraph_format.line_spacing = 1.0` and `para.paragraph_format.space_after = Pt(0)` do NOT write `<w:spacing>` elements into the XML. Re-reading the file shows all properties as `None`. The XML has no `<w:pPr>` blocks at all — spacing is inherited from `docDefaults`:

```xml
<w:docDefaults><w:pPrDefault><w:pPr>
  <w:spacing w:after="160" w:line="259" w:lineRule="auto"/>
</w:pPr></w:pPrDefault></w:docDefaults>
```

- `w:line="259"` = 259/240 = **1.08 line spacing** (slightly more than single)
- `w:after="160"` = 160 twips = **8pt space after** each paragraph

This is what makes the address block lines look separated and the body paragraphs airy.

## The fix: direct lxml XML manipulation of `document.xml`

```python
import zipfile, io, shutil
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

# Work on a copy
shutil.copy('original.docx', 'clean.docx')

with zipfile.ZipFile('clean.docx', 'r') as z:
    doc_xml = z.read('word/document.xml')

root = etree.fromstring(doc_xml)
body = root.find(f'.//{{{W}}}body')
paras = list(body.findall(f'{{{W}}}p'))

for i, p in enumerate(paras):
    # Get or create pPr
    ppr = p.find(f'{{{W}}}pPr')
    if ppr is None:
        ppr = etree.SubElement(p, f'{{{W}}}pPr')
        p.insert(0, ppr)
    
    # Get or create spacing element
    spacing = ppr.find(f'{{{W}}}spacing')
    if spacing is None:
        spacing = etree.SubElement(ppr, f'{{{W}}}spacing')
        ppr.append(spacing)
    
    # Clear all existing spacing attributes
    for attr in list(spacing.attrib.keys()):
        del spacing.attrib[attr]
    
    # Set spacing attributes
    spacing.set(f'{{{W}}}line', '240')       # 240 = single spacing
    spacing.set(f'{{{W}}}lineRule', 'auto')
    spacing.set(f'{{{W}}}after', '0')         # no space after paragraph
    spacing.set(f'{{{W}}}before', '0')        # no space before paragraph

# Write back to the zip
xml_bytes = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
buffer = io.BytesIO()
with zipfile.ZipFile('clean.docx', 'r') as zin:
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == 'word/document.xml':
                data = xml_bytes
            zout.writestr(item, data)
with open('clean.docx', 'wb') as f:
    f.write(buffer.getvalue())
```

### Common spacing values

| Setting | `w:line` | `w:lineRule` | Effect |
|---------|----------|--------------|--------|
| Single | 240 | auto | Tight single spacing |
| 1.15 | 276 | auto | Default in most modern word processors |
| 1.5 | 360 | auto | One-and-a-half spacing |
| Double | 480 | auto | Double spacing |

## Filling text blanks (ellipsis / dots)

**Key insight: the dots (……) are often split across MULTIPLE runs.** A single "……\n" placeholder can be in 2-3 separate `<w:r>` elements, so `replaceAllText`-style replacement fails. Must iterate runs individually:

```python
# The original has runs like:
# Run 3: " Ranks passed away on ………"
# Run 4: "….."
# Run 11: " representing him before tax authorities and my Pan number is ……….."

# Replace per-run, checking for the dots
for j, r in enumerate(p10_runs):
    t = r.find(f'{{{W}t}}')
    if t is not None and t.text and '…' in t.text:
        if 'Ranks passed away on' in t.text:
            # Replace dots with the death date, keep text before
            t.text = ' Ranks passed away on 20th July 2022'
        elif 'my Pan number is' in t.text:
            t.text = ' representing him before tax authorities and my Pan number is AHVPR5168E'
        elif t.text.strip() in ('…', '…..', '...'):
            # Remove leftover dots-only runs
            p10.remove(r)
```

## In-place re-upload (preserving file ID and link)

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', service_name='google-draas')
file_id = 'EXISTING_FILE_ID'

media = MediaFileUpload('clean.docx',
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True)
updated = drive.files().update(
    fileId=file_id,
    media_body=media,
    body={'name': 'New Name - Updated Date.docx'},  # can rename simultaneously
    fields='id,name,mimeType,size,modifiedTime'
).execute()
```

## Visual verification workflow

Since the file is a .docx, you can't use the Docs API to read it. For visual review:

1. **Convert to Google Doc (temp)** → **export PDF** → **pdftoppm PNG** → **vision_analyze**:

```python
# Step 1: Convert .docx → Google Doc (temp)
media2 = MediaFileUpload('clean.docx',
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True)
temp_doc = drive.files().create(
    body={'name': 'TMP_render', 'mimeType': 'application/vnd.google-apps.document'},
    media_body=media2, fields='id'
).execute()
temp_id = temp_doc['id']

# Step 2: Export to PDF
req = drive.files().export_media(fileId=temp_id, mimeType='application/pdf')
fh = io.BytesIO()
dl = MediaIoBaseDownload(fh, req)
done = False
while not done:
    status, done = dl.next_chunk()
with open('verify.pdf', 'wb') as f:
    f.write(fh.getvalue())

# Step 3: Convert to PNG
import subprocess
subprocess.run(['pdftoppm', '-png', '-r', '200', 'verify.pdf', 'verify'], check=True)

# Step 4: Clean up temp doc
drive.files().delete(fileId=temp_id).execute()

# Step 5: vision_analyze on verify-1.png
```

2. **For comparing before/after:** do the same workflow on the original .docx first, save the PNG, then re-run after editing. Ask vision_analyze specific questions about line spacing, text content, and date.

## Workflow summary

```
Download .docx from Drive → 
  Inspect XML (docDefaults for spacing, runs for text) →
    Edit spacing via lxml (create pPr + spacing element) →
      Fill text blanks per-run (dots split across runs) →
        Upload in-place via files().update() (same link) →
          Visual verify: temp Google Doc → PDF → PNG → vision_analyze
```