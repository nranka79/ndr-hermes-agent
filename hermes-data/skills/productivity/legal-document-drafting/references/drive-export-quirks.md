# Google Drive Export — mimeType → Method Mapping

## The Rule

| mimeType | File Type | Method |
|----------|-----------|--------|
| `application/vnd.google-apps.document` | Google Docs | `export_media(mimeType='text/plain')` |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `.docx` stored as Google Doc | `export_media(mimeType='text/plain')` |
| `application/msword` | `.doc` binary | `get_media(fileId=ID)` — then convert |
| `application/pdf` | PDF | `get_media(fileId=ID)` |

## The Critical Gotcha

`application/msword` files are NOT Google Docs format. Calling `export_media` on them throws:
```
HttpError 403: "Export only supports Docs Editors files."
```

Use `get_media` for `.doc` files. Then convert:
- `antiword /tmp/file.doc` (CLI)
- `python-docx` library (Python, for `.docx`)

## `.docx` That Are Google Docs

Sometimes a `.docx` uploaded to Drive is stored as `application/vnd.openxmlformats-officedocument.wordprocessingml.document` but is actually a Google Doc (auto-converted on upload). In this case `get_media` works too (returns binary `.docx`).

**Safe pattern:** Try `get_media` first for binary formats, `export_media` for Google Docs formats.

## Code Snippet

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

# Get file metadata first
file_info = drive.files().get(
    fileId=file_id,
    fields='id, name, mimeType, size'
).execute()
mime = file_info['mimeType']

if mime == 'application/msword':
    result = drive.files().get_media(fileId=file_id)
    content = result.execute()
    with open('/tmp/draft.doc', 'wb') as f:
        f.write(content)
elif mime in ('application/vnd.google-apps.document',
              'application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
    result = drive.files().export_media(fileId=file_id, mimeType='text/plain')
    content = result.execute().decode('utf-8')
elif mime == 'application/pdf':
    result = drive.files().get_media(fileId=file_id)
    content = result.execute()
    with open('/tmp/draft.pdf', 'wb') as f:
        f.write(content)
```

## Size Check

A `size: '0'` in file metadata means the file has no content in Google Drive storage (e.g., `.doc` binary not re-uploaded after conversion). Download will succeed but return empty bytes. In that case, fall back to finding the same content in another format (e.g., the Google Docs version of the same document).
