# Drive Notice Folder Workflow

## Use when
User says: "make a folder in my drive", "upload notice to Drive", "create folder for [legal document type]", "put this document in a properly named folder".

## Full Workflow

### Step 1 — Convert PDF to images for vision analysis

`vision_analyze` does NOT support PDFs directly. Must convert to image first.

```python
from pdf2image import convert_from_path
pages = convert_from_path('/path/to/document.pdf', dpi=150)
print(f"Pages: {len(pages)}")
for i, page in enumerate(pages):
    page.save(f'/tmp/doc_p{i+1}.jpg', 'JPEG')
```

Convert at least first 4 pages — legal notices often have critical details spread across pages (header, party names, case numbers, dates).

### Step 2 — Vision analyze for naming

Ask vision for:
- Full document title / type (notice, order, summons, etc.)
- Issuing authority (court, government dept, etc.)
- Date of document
- Case/reference number
- Subject matter (brief)
- Key party names

Naming convention for legal documents:
```
{Year}{Month}{Day}_{IssuingAuthority}_{DocType}_{CaseNo}_{Date}.pdf
```
Example: `20260601_HC_Madras_Notice_CMA742_2026_dated25.05.2026.pdf`

### Step 3 — Create Drive folder if needed

```python
from tools.gws_auth import build_service

drive_svc = build_service('drive', 'v3', telegram_id='<telegram_id>')

folder_meta = {
    'name': 'Notices 2026',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': ['root']  # root = My Drive; use specific parent ID for subfolder
}
created_folder = drive_svc.files().create(body=folder_meta, fields='id, name').execute()
folder_id = created_folder['id']
print('Folder ID:', folder_id)
```

### Step 4 — Upload with correct name

```python
file_meta = {
    'name': 'CMA_742_2026_HC_Madras_Notice_dated_25.05.2026.pdf',
    'parents': [folder_id]
}
media_body = '/data/hermes/document_cache/doc_xxx.pdf'
uploaded = drive_svc.files().create(
    body=file_meta,
    media_body=media_body,
    fields='id, name, webViewLink'
).execute()
print('Uploaded:', uploaded.get('name'))
print('Link:', uploaded.get('webViewLink'))
```

### Step 5 — Present to user with folder link

Always show the folder link so user can access it directly.

## Session Learnings (2026-06-01)

1. **Duplicate notice detection** — Two PDFs may be the same document. When two PDFs arrive with the same timestamp/filename pattern, compare page 1 via vision before uploading. If page 1 content is identical (same case number, same date, same parties), ask user whether the second is a duplicate or a different version.

2. **Folder name from user** — User said "maintain a folder in that you put this name the folder as notice is received from Tamil Nadu in that you mention this folder with name." For notices, a simple `Notices 2026` or `Legal Notices 2026` folder works. Subfolders can be added later if the user specifies.

3. **Naming legal documents** — Always include: issuing authority + document type + case number + date. This makes documents searchable and identifiable in Drive without opening them.

4. **User wants to review before upload** — User said "name the document and I want a separate folder... Maintain a folder in that you put this name the folder as notice is received from Tamil Nadu." Present the proposed filename and folder name to user before uploading.

5. **8-page notice scanned** — The HC Madras notice was 8 pages with blank pages interspersed. Not all pages contain text; some are blank official stationery. Analyze all pages to capture the full document structure.