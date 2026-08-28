# gws_skill_bridge Parameter Mapping Reference

The bridge's `call()` function passes all `**kwargs` directly to `types.SimpleNamespace(**kwargs)`, then dispatches to the underlying `google_api.py` function. Each function accesses specific attribute names that don't always match the natural kwarg names you'd pass.

**Always pass ALL parameters as keyword args to `gws_skill_bridge.call()` — there are no positional args beyond `operation` and `service_name`.**

## Quick Reference — Parameter Name Mismatches

| Bridge call pattern | What you might guess | What's actually expected | Error you'll see if wrong |
|---|---|---|---|
| `drive_search(..., raw_query=True)` | Omit `raw_query` | Must pass `raw_query=True` for raw Drive queries | `AttributeError: 'SimpleNamespace' object has no attribute 'raw_query'` |
| `drive_create_folder(..., parent="ID")` | `parents=["ID"]` | `parent="ID"` (singular) | `AttributeError: 'SimpleNamespace' object has no attribute 'parent'` |
| `drive_upload(..., path="/tmp/file.pdf")` | `file_path="/tmp/file.pdf"` | `path="/tmp/file.pdf"` | `AttributeError: 'SimpleNamespace' object has no attribute 'path'` |
| `sheets_get(..., sheet_id="...")` | `spreadsheet_id="..."` | `sheet_id="..."` | `AttributeError: 'SimpleNamespace' object has no attribute 'sheet_id'` |
| `docs_get(..., doc_id="...")` | `document_id="..."` | `doc_id="..."` | `AttributeError: 'SimpleNamespace' object has no attribute 'doc_id'` |
| `docs_create(..., body="...")` | `content="..."` | `body="..."` | `AttributeError: 'SimpleNamespace' object has no attribute 'body'` |

## Operation-by-Operation Detail

### drive_search
```python
# Full-text search (wraps query in fullText contains '...')
gws("drive_search", service_name="google-draas", query="invoice", raw_query=False, max=20)

# Raw Drive query language (folder listing, mimeType filter, etc.)
gws("drive_search", service_name="google-draas",
    query="'FOLDER_ID' in parents and mimeType='application/pdf'",
    raw_query=True, max=100)
```
- `query` (str) — search string
- `raw_query` (bool, default False) — when True, passes query verbatim to Drive API `q=` parameter; when False, wraps in `fullText contains '...'`
- `max` (int, default 10) — pageSize

### drive_create_folder
```python
# Create at root
gws("drive_create_folder", service_name="google-draas", name="Folder Name", parent="")

# Create inside a folder
gws("drive_create_folder", service_name="google-draas", name="Subfolder", parent="PARENT_FOLDER_ID")
```
- `name` (str, required) — folder name
- `parent` (str) — parent folder ID. Pass empty string `""` to create at root. ⚠️ This attribute MUST be present even if empty or the function crashes with AttributeError.

### drive_upload
```python
gws("drive_upload", service_name="google-draas", path="/tmp/file.pdf", mime_type="application/pdf", name="output.pdf", parent="FOLDER_ID")
```
- `path` (str, required) — local path to file (not `file_path`)
- `mime_type` (str) — MIME type
- `name` (str) — filename in Drive (defaults to local filename)
- `parent` (str) — parent folder ID
- `description` (str)

### drive_get
```python
gws("drive_get", service_name="google-draas", file_id="...")
```
- `file_id` (str, required) — Drive file ID
- Returns JSON with id, name, mimeType, webViewLink, size, modifiedTime, owners, permissions, parents

### drive_download
```python
gws("drive_download", service_name="google-draas", file_id="...", output="/tmp/out.pdf")
```
- `file_id` (str, required)
- `output` (str, required) — local destination path (NOT `dest` or `output_path`)

### drive_delete
```python
# Trash (dafault) — MUST pass permanent= explicitly
gws("drive_delete", service_name="google-draas", file_id="...", permanent=False)

# Permanent delete (skip trash)
gws("drive_delete", service_name="google-draas", file_id="...", permanent=True)
```
- `file_id` (str, required) — Drive file ID
- `permanent` (bool) — **MUST be passed explicitly.** If omitted, the bridge raises `AttributeError: 'SimpleNamespace' object has no attribute 'permanent'`. Pass `False` to trash, `True` to permanently delete.

### drive_share
```python
gws("drive_share", service_name="google-draas", file_id="...", email="user@example.com", role="reader")
```
- `file_id` (str, required)
- `email` (str, required) — user email to share with
- `role` (str) — "reader", "writer", "commenter", "owner"
- `notify` (bool) — send notification email (default True)
```python
gws("drive_delete", service_name="google-draas", file_id="...")
```
- `file_id` (str, required)

### sheets_get
```python
gws("sheets_get", service_name="google-draas", sheet_id="SPREADSHEET_ID", range="Sheet1!A1:Z100")
```
- `sheet_id` (str, required) — the spreadsheet ID (not `spreadsheet_id`)
- `range` (str, default "A1:Z1000") — A1 notation range

### sheets_update / sheets_append / sheets_create
```python
gws("sheets_update", service_name="google-draas", sheet_id="...", range="A1", values=[["Header1","Header2"]])
gws("sheets_append", service_name="google-draas", sheet_id="...", range="A1", values=[["row1col1","row1col2"]])
gws("sheets_create", service_name="google-draas", title="New Sheet Name")
```
- `sheet_id` (str, required for update/append)
- `range` (str)
- `values` (list of lists, required for update/append)
- `title` (str, required for create)
- All use `sheet_id` not `spreadsheet_id`

### docs_get / docs_create / docs_append
```python
gws("docs_get", service_name="google-draas", doc_id="DOCUMENT_ID")
gws("docs_create", service_name="google-draas", title="Doc Title", body="Content here", parent="FOLDER_ID")
gws("docs_append", service_name="google-draas", doc_id="...", text="More content", section="...")
```
- `doc_id` (str) — not `document_id`
- `body` (str) — for docs_create, not `content`
- `parent` (str) — for docs_create, OPTIONAL folder ID; verified working 2026-08 (new doc lands directly in the target folder, same as `drive_create_folder`'s `parent`)
- `text` (str) — for docs_append
- `section` (str) — for docs_append (optional, section title)

### gmail_search
```python
gws("gmail_search", service_name="google-draas", query="from:someone subject:invoice newer_than:7d", max=10)
```
- `query` (str) — Gmail native search syntax
- `max` (int, default 10)

### gmail_get / gmail_modify / gmail_labels
```python
gws("gmail_get", service_name="google-draas", message_id="...")
gws("gmail_modify", service_name="google-draas", message_id="...", add_labels=["INBOX"], remove_labels=["UNREAD"])
gws("gmail_labels", service_name="google-draas")
```
- `message_id` (str) — Gmail message ID
- `add_labels` / `remove_labels` (list of str)

### calendar_list / calendar_create / calendar_delete
```python
gws("calendar_list", service_name="google-draas", max=20)
gws("calendar_create", service_name="google-draas", summary="Event", start="2026-07-16T10:00:00+05:30", end="2026-07-16T11:00:00+05:30")
gws("calendar_delete", service_name="google-draas", calendar="primary", event_id="...")
```
- `summary` (str) — event title
- `start` / `end` (ISO datetime string)
- `calendar` (str, default "primary")
- `event_id` (str)

### contacts_list
```python
gws("contacts_list", service_name="google-draas", query="name", max=30)
```
- `query` (str) — search query
- `max` (int, default 30)

## Root Cause

The bridge builds `types.SimpleNamespace(**kwargs)` at line 730-731 of `/opt/hermes/tools/gws_skill_bridge.py`. Each underlying function in `/data/hermes/skills/productivity/google-workspace/scripts/google_api.py` accesses explicit attribute names. There is NO normalization layer — the attribute name in the function body IS the parameter name you must pass. There is no documentation in the bridge that tells you which names to use; the only source of truth is the function signatures in google_api.py.
