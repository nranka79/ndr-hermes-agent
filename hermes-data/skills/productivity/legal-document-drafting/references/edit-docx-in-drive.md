# Editing .docx Files Stored in Google Drive

## When to Use This

When documents are stored as **binary .docx files** (mimeType: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`) in Google Drive — not as Google Docs — and you need to fix typos, update IFSC codes, swap account numbers, fill placeholders, or make targeted text changes.

This applies to documents whose Drive URL looks like:
`https://docs.google.com/document/d/.../edit` (Google Docs wrapper around a .docx)
but the Drive API returns mimeType `.docx` rather than `application/vnd.google-apps.document`.

## Technique: Download → XML edit → Re-zip → Upload

### 1. Download the .docx bytes

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseUpload
drive = build_service("drive", "v3")

request = drive.files().get_media(fileId=FILE_ID)
content = request.execute()  # raw bytes of the .docx
```

### 2. Modify the XML inside the docx

A .docx file is a ZIP archive. The document text lives in `word/document.xml`. Edit it with ElementTree:

```python
import zipfile, io
from xml.etree import ElementTree as ET

z = zipfile.ZipFile(io.BytesIO(content))
xml_bytes = z.read("word/document.xml")
root = ET.fromstring(xml_bytes)

# Namespace for WordprocessingML
ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

# Find and replace text in <w:t> elements
for t_elem in root.iter(f'{{{ns}}}t'):
    if t_elem.text and OLD_TEXT in t_elem.text:
        t_elem.text = t_elem.text.replace(OLD_TEXT, NEW_TEXT)

# Serialize back
new_xml = ET.tostring(root, encoding='unicode', xml_declaration=True)
```

### 3. Rebuild the docx ZIP

```python
output = io.BytesIO()
with zipfile.ZipFile(io.BytesIO(content), 'r') as zin:
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = new_xml.encode('utf-8')
            zout.writestr(item, data)
```

### 4. Upload the modified bytes back to Drive

```python
media = MediaIoBaseUpload(
    io.BytesIO(output.getvalue()),
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True
)
file_metadata = {
    'name': 'ORIGINAL_NAME - CORRECTED.docx',
    'parents': [PARENT_FOLDER_ID]
}
uploaded = drive.files().create(
    body=file_metadata,
    media_body=media,
    fields='id, name, webViewLink'
).execute()
```

### 5. Shortcut: multiple replacements in one pass

```python
replacements = [
    ("Account Number: KKBK0000431", "Account Number: 8551119394"),
    ("IFSC Code: KKBK0008068", "IFSC Code: KKBK0000431"),
]
for old, new in replacements:
    for t_elem in root.iter(f'{{{ns}}}t'):
        if t_elem.text and old in t_elem.text:
            t_elem.text = t_elem.text.replace(old, new)
```

## Pitfalls

- **Run-splitting**: docx XML often splits words across multiple `<w:r>` (run) elements. A search string like `"KKBK0000"` might be split as `"KKBK"` + `"0000"` across two `<w:t>` tags. Use the raw XML string (not ElementTree) with regex to find such split text before attempting replacements. If a replacement is not found, dump the XML to search for split text patterns.
- **Namespace**: Always use `{http://schemas.openxmlformats.org/wordprocessingml/2006/main}` prefix, not bare tag names. Python's `{ns}` syntax works.
- **Export vs get_media**: If the file is a real Google Doc (mimeType `application/vnd.google-apps.document`), use `drive.files().export_media()` instead. If it's a binary docx, use `get_media()`. Check mimeType with `drive.files().get(fileId=FILE_ID, fields="id, name, mimeType")`.
- **Formatting preserved**: This technique preserves all formatting, headers, footers, images, and other elements because only the `word/document.xml` is touched inside the ZIP.
- **New file, not overwrite**: Always upload as a new file with "- CORRECTED" suffix rather than overwriting the original, so the user can diff before accepting changes.
