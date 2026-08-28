# Edit .docx Files in Google Drive with XML Manipulation

## When to Use

When you need to make text corrections inside .docx files stored in Google Drive — fixing typos, updating bank account numbers/IFSC codes, filling placeholders in RERA affidavits, or patching any text inside a Word document stored in Drive.

These are NOT Google Docs (mimeType `application/vnd.openxmlformats-officedocument.wordprocessingml.document`). The Docs API refuses them. The only way is: download bytes → modify XML → upload copy.

## Workflow

### 1. Download from Drive

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseUpload
import io, zipfile
from xml.etree import ElementTree as ET

drive = build_service("drive", "v3")
request = drive.files().get_media(fileId="FILE_ID")
content = request.execute()
```

### 2. Read All Paragraphs

```python
z = zipfile.ZipFile(io.BytesIO(content))
xml_bytes = z.read("word/document.xml")
root = ET.fromstring(xml_bytes)

texts = []
for p in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
    para_text = ''.join(t.text or '' for t in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
    if para_text.strip():
        texts.append(para_text)
```

### 3. Find & Replace (works per `<w:t>` run)

```python
for t_elem in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
    if t_elem.text and "OLD" in t_elem.text:
        t_elem.text = t_elem.text.replace("OLD", "NEW")
```

Multiple changes at once on the same XML tree:

```python
for old, new in [("A", "B"), ("C", "D")]:
    for t in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
        if t.text and old in t.text:
            t.text = t.text.replace(old, new)
```

### 4. Rebuild Zip

```python
new_xml = ET.tostring(root, encoding='unicode', xml_declaration=True)
output = io.BytesIO()
with zipfile.ZipFile(io.BytesIO(content), 'r') as zin:
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = new_xml.encode('utf-8')
            zout.writestr(item, data)
```

### 5. Upload Corrected Copy

```python
media = MediaIoBaseUpload(io.BytesIO(output.getvalue()),
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True)
uploaded = drive.files().create(
    body={'name': 'FILENAME - CORRECTED.docx', 'parents': ['FOLDER_ID']},
    media_body=media, fields='id, name, webViewLink'
).execute()
```

## Pitfalls

- **Split runs**: Text may be split across adjacent `<w:t>` elements. Simple `t.text` replacement won't catch cross-run matches. Search the concatenated paragraph text if needed.
- **Always create a copy**: Upload as "- CORRECTED.docx", never overwrite the original.
- **Google Docs disguise**: Some files show `docs.google.com/document/d/...` links but are actually .docx (get_media works, export doesn't).
