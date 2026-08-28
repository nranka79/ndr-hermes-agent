# Updating Non-Google-Native File Content on Drive

Google Docs/Sheets/Slides (native files) can be exported, modified, and re-imported. But plain-uploaded files like HTML, PDF, JPG, or MP4 need a different approach to update in place.

## The Right Way: `files().update()`

Use `drive.files().update(fileId=..., media_body=...)` — this **preserves the file ID**, sharing permissions, and any links pointing to it.

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

service = build_service('drive', 'v3', service_name='google-draas')

media = MediaFileUpload('/path/to/updated.html', mimetype='text/html', resumable=True)
result = service.files().update(
    fileId='EXISTING_FILE_ID',
    media_body=media,
    fields='id,name,webViewLink'
).execute()

print(f"Updated: {result['name']} (ID unchanged)")
```

**Why this matters:**
- If someone shared a link to the old version, the link still works
- The file keeps its original creation date (not reset)

## The Wrong Way: delete + re-create

```python
# Breaks links and sharing — new file ID
service.files().delete(fileId=old_id).execute()
result = service.files().create(body=metadata, media_body=media).execute()
```

Only use delete+re-create when you don't have the file ID and can't look it up.

## Downloading non-Google-native files before editing

Use `get_media()` (NOT `export()`, which only works for native Docs/Sheets/Slides):

```python
import io
from googleapiclient.http import MediaIoBaseDownload

request = service.files().get_media(fileId=file_id)
content = io.BytesIO()
downloader = MediaIoBaseDownload(content, request)
done = False
while not done:
    _, done = downloader.next_chunk()

html = content.getvalue().decode('utf-8')
```

**Correct download method per file type:**

| File Type | Native Google Doc? | Download Method |
|-----------|-------------------|----------------|
| Google Doc, Sheet, Slide | Yes | `export(fileId=..., mimeType=...)` |
| HTML, PDF, JPG, MP4, ZIP | No | `get_media(fileId=...)` |

## Complete workflow: download → edit → re-upload

```python
import io
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from tools.gws_auth import build_service

svc = build_service('drive', 'v3', service_name='google-draas')
file_id = 'YOUR_FILE_ID'

# 1. Download
request = svc.files().get_media(fileId=file_id)
buf = io.BytesIO()
downloader = MediaIoBaseDownload(buf, request)
done = False
while not done:
    _, done = downloader.next_chunk()
content = buf.getvalue().decode('utf-8')

# 2. Edit locally
with open('/tmp/updated.html', 'w') as f:
    f.write(content)

# 3. Update in place (same file ID, same links)
media = MediaFileUpload('/tmp/updated.html', mimetype='text/html', resumable=True)
result = svc.files().update(fileId=file_id, media_body=media, fields='id,name,webViewLink').execute()
print(f"Updated: {result['name']} at {result['webViewLink']}")
```
