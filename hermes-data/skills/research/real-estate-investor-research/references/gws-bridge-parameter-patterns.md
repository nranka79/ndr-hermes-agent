# GWS Bridge — Required Parameters Per Operation

The `gws_skill_bridge.call()` creates `types.SimpleNamespace(**kwargs)` from your keyword arguments. **Every parameter the underlying `google_api.py` function accesses must be present in your kwargs — even if you set it to `None`.** Missing params cause `AttributeError`.

## drive_upload

```python
call('drive_upload', service_name='google-draas',
     path='/tmp/file.pptx',        # required
     mime_type='application/vnd.google-apps.presentation',  # for Slides conversion
     name='Project Name',          # optional — defaults to filename
     parent=None)                  # REQUIRED — pass None for root
```
Error if missing: `AttributeError: 'types.SimpleNamespace' object has no attribute 'parent'`

## drive_share

```python
call('drive_share', service_name='google-draas',
     file_id='...',                # required
     type='user',                  # required — 'user', 'group', 'domain', 'anyone'
     role='writer',                # required — 'reader', 'commenter', 'writer'
     email='user@example.com',     # required when type='user'
     notify=False)                 # optional — True sends email
```
Error if missing: `AttributeError: 'types.SimpleNamespace' object has no attribute 'type'`

## drive_search

```python
# For custom queries:
call('drive_search', service_name='google-draas',
     query="name contains 'Project' and trashed = false",
     raw_query=True,               # REQUIRED — without this, bridge wraps in fullText contains
     max=10)                       # page size — NOT optional
```
Error if missing `raw_query=True`: bridge wraps your query as `fullText contains 'your query'` which breaks `name contains` and `'folder_id' in parents` syntax.

## drive_download

```python
call('drive_download', service_name='google-draas',
     file_id='...',                # required
     output='/tmp/file.pptx',      # required — local path to save
     export_mime='application/vnd.openxmlformats-officedocument.presentationml.presentation')  # for Google-native files
```
Error if missing `output`: `AttributeError: 'types.SimpleNamespace' object has no attribute 'output'`

## docs_get

```python
call('docs_get', service_name='google-draas',
     doc_id='...')                 # required — note: doc_id, NOT document_id
```
Error if using wrong key: `AttributeError: 'types.SimpleNamespace' object has no attribute 'doc_id'`

## General rule

Before calling ANY operation on the bridge, read the underlying function's signature in `/data/hermes/skills/productivity/google-workspace/scripts/google_api.py` and pass EVERY parameter it references. The bridge has no defaults — every arg must come from your call.
