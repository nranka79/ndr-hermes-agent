# Reading .docx Files from Drive Without python-docx

When `python-docx` cannot be installed (permission denied on venv, no pip access, etc.), you can still **read** .docx file content using only Python stdlib: `zipfile` + `xml.etree.ElementTree`.

This works because .docx is a ZIP archive containing `word/document.xml` (and optionally `word/header*.xml`, `word/footer*.xml`).

## .doc file caveat — check magic bytes first

Some `.doc` files (saved by newer Word versions or Word Online) are actually **ZIP-based OOXML** (PK header `50 4B 03 04`), NOT the traditional OLE2 binary format (D0 CF 11 E0). You can use the same zipfile+XML approach on them — the file extension is misleading.

Check magic bytes before deciding the extraction strategy:

```python
with open('file.doc', 'rb') as f:
    header = f.read(4)

if header == b'PK\x03\x04':
    # ZIP-based OOXML (.docx disguised as .doc) — use zipfile+XML
    ...
elif header == b'\xD0\xCF\x11\xE0':
    # OLE2 binary format — needs antiword/catdoc or LibreOffice
    ...
```

**When this happens:** Advocates' offices often send .doc files that are actually saved in OOXML format. The zipfile approach works on these.

## When to use

- You need to **inspect** the text content of a .docx or ZIP-based .doc file on Drive or from an email attachment
- `python-docx` is not installed and you can't install it
- You only need **read** access — this approach does NOT support editing/saving

## Complete Pattern

```python
import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('/tmp/file.docx', 'r') as z:
    with z.open('word/document.xml') as f:
        tree = ET.parse(f)

root = tree.getroot()
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

# Get all paragraphs
for i, para in enumerate(root.findall('.//w:p', ns)):
    texts = []
    for t in para.findall('.//w:t', ns):
        if t.text:
            texts.append(t.text)
    text = ''.join(texts).strip()
    if text:
        print(f"P{i}: {text}")
```

## Download from Drive First

Always download via `drive.files().get_media()` before parsing:

```python
from tools.gws_auth import build_service

drive = build_service('drive', 'v3')
doc_id = 'FILE_ID'

request = drive.files().get_media(fileId=doc_id)
file_bytes = request.execute()

with open('/tmp/file.docx', 'wb') as f:
    f.write(file_bytes)
```

Or use `BytesIO` to avoid writing to disk:

```python
import io
from googleapiclient.http import MediaIoBaseDownload

fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    _, done = downloader.next_chunk()

fh.seek(0)
with zipfile.ZipFile(fh, 'r') as z:
    with z.open('word/document.xml') as f:
        tree = ET.parse(f)
```

## Handling Tables in .docx

To extract table content:

```python
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
for table in root.findall('.//w:tbl', ns):
    for row in table.findall('.//w:tr', ns):
        cells = []
        for cell in row.findall('.//w:tc', ns):
            texts = []
            for p in cell.findall('.//w:p', ns):
                for t in p.findall('.//w:t', ns):
                    if t.text:
                        texts.append(t.text)
            cells.append(''.join(texts).strip())
        print(' | '.join(cells))
```

## Limitations

- **Read-only** — you cannot edit or save with this approach. Use `python-docx` for modifications.
- **No formatting info** — XML-raw parsing loses font, size, color, bold/italic styling unless you explicitly walk `w:rPr` elements.
- **No images** — images are stored as separate files in the ZIP (under `word/media/`).
- **Headers/footers** are in separate files: `word/header1.xml`, `word/footer1.xml`. Parse them the same way.
- **Nested tables** — `w:tbl` elements can nest; track the depth if you need hierarchical extraction.

## Why python-docx might fail to install

```text
error: Failed to install: python_docx-x.x.x-py3-none-any.whl
  Caused by: Failed to create directory `/opt/hermes/.venv/lib/python3.13/site-packages/docx`
  Caused by: failed to create directory `/opt/hermes/.venv/lib/python3.13/site-packages/docx`: Permission denied (os error 13)
```

This happens when Hermes runs as a non-root user and the system venv is owned by root. The zipfile fallback bypasses this entirely.

## Related

- `references/docx-modify-reupload-drive.md` — when you CAN install python-docx and need to modify + re-upload
- `references/drive-download-extract.md` — general Drive file download patterns
