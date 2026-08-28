# Absolute Sale Deed — Recital Removal & Renumbering

## Session Reference

Verified on: Ranka Oasis Plot 119 Absolute Sale Deed (Aug 2026)

## The Workflow

### Step 1: Download the .docx from Drive

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

service = build_service("drive", "v3", service_name="google-draas")
request = service.files().get_media(fileId=FILE_ID)
content = request.execute()

with open("/tmp/deed.docx", "wb") as f:
    f.write(content)
```

### Step 2: Remove Unnecessary Recitals (XML Element Removal)

The most reliable approach is lxml on the raw document.xml:

```python
import shutil, zipfile
from lxml import etree

nsmap = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

shutil.copy('/tmp/deed.docx', '/tmp/deed_updated.docx')

with zipfile.ZipFile('/tmp/deed_updated.docx', 'r') as zin:
    doc_xml = zin.read('word/document.xml')
    all_files = {name: zin.read(name) for name in zin.namelist()}

root = etree.fromstring(doc_xml)
body = root.find('.//w:body', nsmap)
paras = body.findall('w:p', nsmap)

def get_para_text(p):
    texts = p.findall('.//w:t', nsmap)
    return ''.join(t.text or '' for t in texts)

# Find recitals by text content, then remove them
for idx in sorted([101, 102], reverse=True):  # Remove in reverse order!
    para = paras[idx]
    body.remove(para)
```

**Critical: Remove in reverse order** so indices don't shift as you delete.

### Step 3: Renumber Remaining Recitals

After removal, find the affected paragraphs and update their roman numeral prefixes:

```python
# Re-parse to get new indices
new_xml_bytes = etree.tostring(root)
new_root = etree.fromstring(new_xml_bytes)
new_body = new_root.find('.//w:body', nsmap)
new_paras = new_body.findall('w:p', nsmap)

# Map: old_prefix -> new_prefix
old_new = {
    '(x)  Mortgage without Possession': '(viii)  Mortgage without Possession',
    '(xi)  Joint Development Agreement': '(ix)  Joint Development Agreement',
    '(xii)  Irrevocable General Power of Attorney': '(x)  Irrevocable General Power of Attorney',
}

for p in new_paras:
    t = get_para_text(p).strip()
    for old_prefix, new_prefix in old_new.items():
        if t.startswith(old_prefix):
            # Find the first w:t element with roman numeral text
            runs = p.findall('.//w:r', nsmap)
            for run in runs:
                texts = run.findall('.//w:t', nsmap)
                for t_elem in texts:
                    if t_elem.text and t_elem.text.startswith('(') and ')' in t_elem.text:
                        parts = t_elem.text.split(')', 1)
                        if len(parts) == 2:
                            numeral = parts[0].strip('( ')
                            new_numeral = {'x': 'viii', 'xi': 'ix', 'xii': 'x'}.get(numeral.lower())
                            if new_numeral:
                                t_elem.text = '(' + new_numeral + ')' + parts[1]
                                break
                    break  # Only need first text-bearing run
            break
```

### Step 4: Fix Cross-References

Search for "Recital (xi)" strings throughout and update:

```python
all_texts = p.findall('.//w:t', nsmap)
for t_elem in all_texts:
    if t_elem.text and 'Recital (xi)' in t_elem.text:
        t_elem.text = t_elem.text.replace('Recital (xi)', 'Recital (ix)')
```

### Step 5: Yellow Highlighting for Google Docs

**USE `<w:highlight w:val="yellow"/>`** — NOT `<w:shd>`. Google Docs maps the highlight element to its native text highlighter. `w:shd` with fill=FFFF00 creates a paragraph shading that often doesn't display as visible yellow in Google Docs.

```python
# CORRECT — adds native text highlighter
hl = etree.SubElement(rpr, '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}highlight')
hl.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', 'yellow')
```

### Step 6: Add RERA Registration Details

Extract from the RERA certificate PDF:

```python
# Use vision_analyze on the first page
# Format: TNRERA/XX/L0/XXXX/YYYY dated DD.MM.YYYY
```

Then modify two locations in the sale deed:
1. **Project Registration section** — replace "under process" placeholder sentence
2. **RERA Compliance recital** — add the number and date

Keep text concise — NDR preference: "just RERA number is good enough with RERA date."

### Step 7: Save & Upload

```python
new_xml_bytes = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)

with zipfile.ZipFile('/tmp/deed_updated.docx', 'w', zipfile.ZIP_DEFLATED) as zout:
    for name, content in all_files.items():
        if name == 'word/document.xml':
            zout.writestr(name, new_xml_bytes)
        else:
            zout.writestr(name, content)

# Upload
media = MediaFileUpload("/tmp/deed_updated.docx",
    mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    resumable=True)
service.files().update(fileId=FILE_ID, media_body=media).execute()
```

## Key Domain Rules (NDR's Preference)

- **SPA and Other's Deed recitals are NOT needed** in the main absolute sale deed title flow. Only include: Sale Deeds, Exchange Deeds, JDAs, GPAs, and Mortgage Deeds that directly affect the property being conveyed.
- **Concise recitals:** don't exhaustively list every party/investor. Focus on: doc type, date, doc no, SRO, parties (concise), survey nos, extent, purpose.
- **"just RERA number is good enough with RERA date"** — a single line with the registration number and date, not a lengthy compliance paragraph.

## Pitfalls

| Pitfall | Fix |
|---------|-----|
| Recital text spans multiple `<w:r>` elements | Search all runs, not just the first. Or rebuild paragraph text in one run. |
| XML namespace prefix (`w:`) not declared | Always define `nsmap{'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}` |
| UTF-8 encoding in XML declaration | Pass `xml_declaration=True, encoding='UTF-8', standalone=True` to `etree.tostring()` |
| w:shd with fill=FFFF00 doesn't show in Google Docs | Use `<w:highlight w:val="yellow"/>` instead |
| Cross-reference to old recital number missed | Search ALL paragraphs for the old roman numeral string — they can be in paragraph text, not just the recital header |