# Drive Recursive File Listing

List all files/folders recursively from a Google Drive folder, traversing sub-folders with pagination.

## Pattern

```python
import sys
sys.path.insert(0, '/opt/hermes/tools')
from gws_auth import build_service

drive = build_service('drive', 'v3', telegram_id='USER_TELEGRAM_ID')

def list_all(parent_id, indent=0):
    """Recursively list all files/folders under parent_id."""
    items = []
    page_token = None
    while True:
        q = f"'{parent_id}' in parents and trashed=false"
        results = drive.files().list(
            q=q,
            pageSize=100,
            fields='nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime)',
            pageToken=page_token
        ).execute()
        for f in results.get('files', []):
            items.append({
                'name': f['name'],
                'id': f['id'],
                'mime_type': f['mimeType'],
                'size': f.get('size', ''),
                'modified': f.get('modifiedTime', ''),
                'indent': indent
            })
            if f['mimeType'] == 'application/vnd.google-apps.folder':
                items.extend(list_all(f['id'], indent + 1))
        page_token = results.get('nextPageToken')
        if not page_token:
            break
    return items

# Usage
folder_id = 'FOLDER_ID_FROM_DRIVE_URL'
# Extract from: https://drive.google.com/drive/folders/1UJRwQa2G8LZTnYesXa_H9Yzv0vNT3EWi
all_items = list_all(folder_id)
print(f"Total items: {len(all_items)}")
```

## Key Points

- **Pagination**: Always use `pageToken` loop — Google Drive returns max 100 files per page.
- **Sub-folder recursion**: Check `mimeType == 'application/vnd.google-apps.folder'` and recurse into it.
- **Fields**: Use explicit `fields` parameter to minimize API quota usage.
- **Trashed files**: Always add `trashed=false` to avoid counting deleted files.
- **Telegram ID**: Pass `telegram_id` explicitly when calling from terminal context (not available via HERMES_SESSION_USER_ID).
- **Venv Python**: Run with `/opt/hermes/.venv/bin/python3` — the Google API client libraries are installed there, not in system python.

## Drive URL → Folder ID

- URL format: `https://drive.google.com/drive/folders/1UJRwQa2G8LZTnYesXa_H9Yzv0vNT3EWi`
- The folder ID is the path segment after `/folders/`: `1UJRwQa2G8LZTnYesXa_H9Yzv0vNT3EWi`

---

## Beyond Listing: Organizing Files at Scale

When the task involves restructuring hundreds of files (moving to new folders, renaming), use these additional patterns.

### Create a Folder

```python
meta = {
    'name': 'Sy No 87',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': [ROOT_FOLDER_ID]
}
f = drive.files().create(body=meta, fields='id,name').execute()
folder_id = f['id']
```

### Rename a File or Folder

```python
drive.files().update(fileId=file_id, body={'name': 'New Name.pdf'}).execute()
```

### Move a File Between Folders

```python
drive.files().update(
    fileId=file_id,
    addParents=target_folder_id,
    removeParents=source_folder_id,
    fields='id'
).execute()
```

### Pitfall — API Timeouts on Bulk Moves

Each `files().update()` with `addParents`/`removeParents` is a separate HTTP request. Moving 50+ files in a single Python invocation may timeout (60s+). Same applies to `files().copy()`. Strategies:

1. **Batch in small groups:** 10–20 files per invocation
2. **Present the mapping first:** Generate a "File X → Folder Y" table for the user to approve before executing
3. **Skip moves, focus on the sheet:** Drive file links (`https://drive.google.com/file/d/FILE_ID/view`) work regardless of folder. The inventory sheet with links is often more valuable than the folder structure

### Copy a File to a New Folder with a New Name

```python
drive.files().copy(
    fileId=original_file_id,
    body={
        'name': 'New Name for Cleaned Copy.pdf',
        'parents': [target_folder_id]
    }
).execute()
```

**Why this matters:** Google Drive file names are file-level, not folder-level. Renaming a file changes it everywhere. To have different names in different folders (e.g., original = "202605281825.pdf", cleaned = "2026/05/28, Sy 87, Bomvachanahalli, EC.pdf"), you must COPY the file. The original stays untouched with its original name.

### Batch File Classification from Filenames

When hundreds of files need sorting into folders, classify by filename patterns:

```python
import re

def classify_to_folder(filename, known_folders):
    \"\"\"Map a filename to its target folder based on embedded identifiers.\"\"\"
    n = filename.rsplit('.', 1)[0] if '.' in filename else filename
    
    # Pattern: 'Sy No XXX' or friendly variant
    m = re.search(r'(?:Sy|SY|sy)\s*(?:No|no|NO)?\s*[.:]?\s*([\d/]+)', n)
    if m:
        key = m.group(1).replace('-', '/')
        return key if key in known_folders else key.split('/')[0]
    
    # Pattern: leading number (e.g., '103_5.pdf')
    m = re.match(r'(\d{2,3})(?:[_-](\d+))?', n)
    if m:
        base = m.group(1)
        sub = m.group(2)
        if sub:
            full = f"{base}/{sub}"
            if full in known_folders:
                return full
        return base
    
    return None  # Unclassifiable
```

### Get file's direct view link

```python
link = f"https://drive.google.com/file/d/{file_id}/view"
```
