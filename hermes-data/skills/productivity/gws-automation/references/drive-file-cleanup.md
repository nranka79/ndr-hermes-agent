# Drive File Cleanup — Zero-byte & Duplicate Deletion

**When to use this:** User asks to clean up Drive files — delete zero-byte files, remove exact-duplicate files (same MD5), find and remove "Untitled" documents/spreadsheets/presentations.

## Workflow

### Step 1: Verify before deleting

Always verify file metadata before deleting. The Drive API returns `size` as a string — parse it to int:

```python
from tools.gws_auth import build_service
service = build_service("drive", "v3")
meta = service.files().get(fileId="<id>", fields="id, name, size, mimeType, trashed").execute()
size = int(meta.get("size", 0))  # 0 = zero-byte
```

### Step 2: Batch delete

Use a single Python script (via `write_file` + `terminal` with herd venv) to check then delete:

```python
for fid in file_ids:
    meta = service.files().get(fileId=fid, fields="name").execute()
    name = meta.get("name", "?")
    service.files().delete(fileId=fid).execute()
    print(f"DELETED: {name}")
```

### Step 3: Confirm results

Print deleted count vs total, list any errors.

## Common Patterns

### Pattern 1 — Zero-byte files
- User shares Drive file IDs
- Verify each returns `size = 0`
- Delete each via `files().delete()`
- Report results per file

### Pattern 2 — Exact MD5 duplicates
- User has already identified duplicates by MD5 checksum
- No need to re-verify MD5 — trust their identification
- Delete matching files from their ID list

### Pattern 3 — "Untitled" files (default-created empty docs)
Search by exact name:
```python
query = "((name = 'Untitled document' or name = 'Untitled spreadsheet' or name = 'Untitled presentation') and trashed=false)"
```
- Google Drive names default-created files "Untitled document", "Untitled spreadsheet", "Untitled presentation"
- Use `name = '<exact>'` (case-insensitive in Drive API) NOT `name contains 'Untitled'` (too broad — catches "Pages from Untitled-2.pdf", etc.)
- Some may have 1–3 KB of content (auto-generated metadata) — confirm before deleting

### Pattern 4 — File list from user (Gmail/doc links)
Extract file IDs from URLs:
```python
import re
file_ids = [re.search(r'/d/([^/]+)', url).group(1) for url in url_list]
```

## Pitfalls

- **FileNotFound (404):** Already deleted. Move on silently.
- **Permission denied:** User may not own the file. Report the error.
- **Rate limits:** Batch no more than 20–30 deletes per script. If more, split across runs.
- **Context-compacted file IDs:** Drive file IDs from compacted contexts may have corrupted trailing characters. Always re-list folder before write operations. See `references/drive-permission-restriction.md` in gws-automation for the verified-ID workflow.
