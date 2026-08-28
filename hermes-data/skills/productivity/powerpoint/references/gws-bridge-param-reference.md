# GWS Bridge Parameter Reference

The `gws_skill_bridge.call()` function converts keyword arguments into a `types.SimpleNamespace` — **every parameter the underlying function accesses must be explicitly passed**, even if empty. Missing params cause `AttributeError`.

## drive_search

```python
# Search by name/mime (raw_query=True for custom queries)
gws_skill_bridge.call('drive_search', service_name='google-draas',
    raw_query=True,  # REQUIRED — see critical note below
    max=10,           # REQUIRED — page size, no default
    query="name contains 'RANKA Oasis' and mimeType='application/vnd.google-apps.presentation'")

# Full-text search (raw_query=False)
gws_skill_bridge.call('drive_search', service_name='google-draas',
    query="RANKA Oasis presentation",
    raw_query=False,  # REQUIRED — see critical note below
    max=5)
```

**Required:** `query`, `max` (pageSize)
**Required (critical):** `raw_query` — This is NOT truly optional through the bridge. The underlying code does `args.query if args.raw_query else ...` which crashes with `AttributeError: 'types.SimpleNamespace' object has no attribute 'raw_query'` if `raw_query` is omitted from kwargs.

- `raw_query=True`: uses `query` verbatim (your GQL query)
- `raw_query=False`: wraps `query` as `fullText contains '{query}'`

## drive_download

```python
# Export Google-native file as PPTX
gws_skill_bridge.call('drive_download', service_name='google-draas',
    file_id='1ABC...',
    output='/tmp/file.pptx',  # REQUIRED — absolute path, must end in .pptx for export
    export_mime='application/vnd.openxmlformats-officedocument.presentationml.presentation')

# Download binary file as-is
gws_skill_bridge.call('drive_download', service_name='google-draas',
    file_id='1ABC...',
    output='/tmp/file.pdf')
```

**Required:** `file_id`, `output` (local path)
**Optional:** `export_mime` — for Google-native files (Slides, Docs, Sheets). Defaults: Slides → PDF, Docs → PDF, Sheets → CSV.

## drive_upload

```python
gws_skill_bridge.call('drive_upload', service_name='google-draas',
    path='/tmp/file.pptx',         # REQUIRED — local file path (NOT file_path, NOT file)
    name='Presentation Name',      # Optional — display name in Drive
    mime_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',  # Optional
    parent='')                     # Optional — parent folder ID, pass '' if none
```

**Required:** `path`
**Optional:** `name` (defaults to filename), `mime_type` (guessed if omitted), `parent` (folder ID, must be present in kwargs even if empty)

## drive_share

```python
gws_skill_bridge.call('drive_share', service_name='google-draas',
    file_id='1ABC...',
    role='writer',        # 'reader', 'commenter', 'writer'
    type='user',          # 'user', 'group', 'domain', 'anyone'
    email='user@example.com',  # Required when type='user'
    notify=True)
```

**Required:** `file_id`, `role`, `type`, `email` (when type='user')
**Optional:** `notify` (default True)

## drive_delete

```python
gws_skill_bridge.call('drive_delete', service_name='google-draas',
    file_id='1ABC...',
    permanent=False)     # REQUIRED — must be present in kwargs; False = trash, True = permanent delete
```

**Required:** `file_id`, `permanent` (must be explicitly passed — `False` trashes, `True` permanently deletes)

## sheets_get

```python
gws_skill_bridge.call('sheets_get', service_name='google-draas',
    sheet_id='1ABC...',      # REQUIRED — NOT spreadsheet_id, NOT spreadsheetId
    range='A1:Z100')         # Optional — omit or pass None for all data
```

**Required:** `sheet_id` (note: parameter name is `sheet_id` not `spreadsheet_id`)
**Optional:** `range` (A1 notation, defaults to all data if omitted)

## Common Error Patterns

| Error | Cause | Fix |
|-------|-------|-----|
| `'types.SimpleNamespace' object has no attribute 'raw_query'` | Missing `raw_query` — required for ALL drive_search calls through bridge | Add `raw_query=True` or `raw_query=False` |
| `'types.SimpleNamespace' object has no attribute 'max'` | Missing `max` (pageSize) | Add `max=10` |
| `'types.SimpleNamespace' object has no attribute 'output'` | drive_download needs `output` | Add `output='/tmp/file.pptx'` |
| `'types.SimpleNamespace' object has no attribute 'path'` | drive_upload expects `path`, not `file_path` | Rename to `path=` |
| `'types.SimpleNamespace' object has no attribute 'name'` | drive_upload accessing `args.name` | Add `name='...'` |
| `'types.SimpleNamespace' object has no attribute 'parent'` | drive_upload checking `if args.parent` | Add `parent=''` |
| `'types.SimpleNamespace' object has no attribute 'notify'` | drive_share missing `notify` | Add `notify=True` or `notify=False` |
| `Returned value is a JSON string, not a dict` | Bridge captures stdout from `print(json.dumps(...))` | Use `json.loads()` when `result` is a string — check with `type(result)` |

## Pattern: Delete old → Upload as Google Slides (import)

The bridge's `drive_upload` uploads the raw file. To convert PPTX → native Google Slides on upload, use the googleapiclient directly:

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

service = build_service('drive', 'v3', service_name='google-draas')

# Delete previous version
for fid in ['old_file_id_1', 'old_file_id_2']:
    try: service.files().delete(fileId=fid).execute()
    except: pass

# Upload with import conversion
media = MediaFileUpload('/tmp/file.pptx',
    mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
    resumable=True)

body = {
    'name': 'Presentation Name',
    'mimeType': 'application/vnd.google-apps.presentation'
}

result = service.files().create(body=body, media_body=media, fields='id, name, webViewLink').execute()
new_id = result['id']

# Share with the requesting user (CRITICAL — file is owned by authenticated account)
service.permissions().create(
    fileId=new_id,
    body={'type': 'user', 'role': 'writer', 'emailAddress': 'user@example.com'},
    sendNotificationEmail=True
).execute()
```

## Permission/Ownership Note

When uploading via the googleapiclient with `service_name='google-draas'` (typically Nishant's account), the file is created in Nishant's Drive. Sharing with `psingh@draas.com` with `role='writer'` may transfer ownership to Prakash if both are in the same Google Workspace domain. Always add back the original account as a writer after sharing to ensure the authenticated session can still manage the file.
