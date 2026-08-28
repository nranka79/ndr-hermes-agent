# Drive Duplicate Analysis — MD5/CRC Matching + Google Sheet

When a user wants to identify duplicate files in a Google Drive folder, clean up zero-byte/failed uploads, or organize a cluttered root directory.

## Pattern Overview

1. List all files in the target folder via Drive API
2. Get metadata: `name`, `size`, `md5Checksum`, `modifiedTime`, `webViewLink`
3. Group by **MD5 checksum** (exact content duplicates) — only works for uploaded binary files, not Google-native Docs/Sheets
4. Group by **filename similarity** (near-duplicates / versioned files)
5. Identify **zero-byte files** (failed uploads)
6. Create a multi-tab Google Sheet with unique serial numbers per file, links, and modified dates
7. User picks serial numbers to delete; you delete by file ID

## Step 1 — List All Files

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3', telegram_id='USER_TG_ID')

all_files = []
page_token = None
while True:
    results = drive.files().list(
        q="'root' in parents and trashed = false",
        spaces='drive',
        fields='nextPageToken, files(id, name, mimeType, size, md5Checksum, modifiedTime, createdTime, webViewLink, owners)',
        pageSize=1000,
        pageToken=page_token,
        orderBy='name'
    ).execute()
    batch = results.get('files', [])
    all_files.extend(batch)
    page_token = results.get('nextPageToken')
    if not page_token:
        break
```

- Use `pageSize=1000` to minimize API calls
- `'root' in parents` for root folder
- For other folders: `'<folder_id>' in parents`
- `md5Checksum` is only populated for uploaded binary files (PDFs, images, DOCX, etc.)
- Google-native files (Docs/Sheets/Slides) have `md5Checksum: null`

## Step 2 — Group by MD5 for Exact Duplicates

```python
from collections import defaultdict
md5_groups = defaultdict(list)
for f in all_files:
    if f.get('md5Checksum'):
        md5_groups[f['md5Checksum']].append(f)

md5_dupes = {k: v for k, v in md5_groups.items() if len(v) > 1}
```

- Sort each group by `modifiedTime` (descending) → first entry is LATEST
- Tag remaining entries as DUPLICATE
- Skip zero-byte MD5 group (`d41d8cd98f00b204e9800998ecf8427e` = empty file MD5) — handle separately

## Step 3 — Group by Same/Similar Filename

**Exact same filename (different content):**
```python
name_groups = defaultdict(list)
for f in all_files:
    name_groups[f['name'].lower()].append(f)
same_name = {k: v for k, v in name_groups.items() if len(v) > 1}
```

**Similar name (versioned documents):**
```python
def normalize_name(name):
    """Strip dates, version numbers, 'draft'/'final' to find base name"""
    import re
    n = name.lower()
    n = re.sub(r'\.[a-z0-9]+$', '', n)           # Remove extension
    n = re.sub(r'\d{8}|\d{4}-\d{2}-\d{2}', '', n) # Remove dates
    n = re.sub(r'[\(\[][vV]?\d+[\)\]]', '', n)    # Remove version markers
    n = re.sub(r'\b(draft|final|copy|new|v\d+)\b', '', n)
    n = re.sub(r'\s*\(converted[^)]*\)', '', n)   # Remove Google Docs conversion tags
    n = re.sub(r'\s+', ' ', n).strip()
    return n
```

## Step 4 — Identify Zero-Byte / Failed Uploads

```python
zero_byte = [f for f in all_files if f.get('size') is not None and int(f['size']) == 0]
```

These are typically:
- Failed property tax receipt uploads (same file tried multiple times)
- Test/scratch files
- Very old placeholder files

Group by base filename to show all copies of each failed upload.

## Step 5 — Create Google Sheet with Serial Numbers

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3', telegram_id='USER_TG_ID')
sheets = build_service('sheets', 'v4', telegram_id='USER_TG_ID')

# Create sheet
body = {
    'properties': {'title': 'Drive Root — Duplicate File Analysis'},
    'sheets': [
        {'properties': {'title': 'EXACT MD5 DUPLICATES'}},
        {'properties': {'title': 'ZERO-BYTE FILES'}},
        {'properties': {'title': 'SAME NAME - DIFF CONTENT'}},
        {'properties': {'title': 'NEAR-DUPLICATES'}},
    ]
}
created = sheets.spreadsheets().create(body=body).execute()
ss_id = created['spreadsheetId']
```

**Required columns:**
```
Serial No | Group ID | Description | File Name | Modified Date | Drive Link | Size (bytes) | MD5 Checksum | Status
```

**Key design rules:**
- **Serial No** must be globally unique across ALL tabs (increment a shared counter) — user will reference these to request deletion
- **Modified Date** should be a proper date string (`YYYY-MM-DD HH:MM`) so user can sort by column in Google Sheets
- **Drive Link** — use `f.get('webViewLink', '')`
- **Status** — `LATEST` (keep), `DUPLICATE` (delete candidate), `OLDER-VERSION`, `DUPLICATE-ZERO`
- **Group ID** — encodes the duplicate group key (e.g., `EXACT-MD5-a1b2c3d4`, `SAME-NAME-termsheet`, `ZERO-BYTE`, `NEAR-DUPE-muthanallur`)
- **Description** — brief human explanation of what the group is ("Legal order — 3 identical copies, different filenames", "Failed upload — property tax receipt PDF")

Write data using `sheets.spreadsheets().values().update()` with `valueInputOption='USER_ENTERED'` so dates are sortable.

## Step 6 — Delete Files by Serial Number

```python
# Look up serial → file ID from your data
for file_id in ids_to_delete:
    drive.files().delete(fileId=file_id).execute()
```

## Pitfalls

- **`md5Checksum` is `null` for Google-native files** (Docs, Sheets, Slides, Forms) — these files are stored as blobs and don't expose a content hash. For these, use name + size matching only.
- **`md5Checksum` can be `null` in the API response even for binary files** if the file was just created — retry or check `modifiedTime` delta.
- **Zero-byte MD5 constant:** `d41d8cd98f00b204e9800998ecf8427e` — all empty files have this hash. Always group and handle separately, don't mix with genuine duplicates.
- **Google Sheets API `valueInputOption`** — Use `'USER_ENTERED'` for date-formatted strings (they get auto-parsed as dates). Use `'RAW'` for plain text links and descriptions.
- **Batch size:** Sheets API accepts up to ~10MB per write. 1,680 rows of 9 columns is fine in a single request.
- **Column width:** After writing, call `spreadsheets.batchUpdate` with `updateDimensionProperties` to widen the Drive Link column (450px) and File Name column (350px) — default column width truncates long filenames and URLs.
- **`None` sizes:** Some files (especially Google-native) have `size: null`. Handle with `int(f.get('size', 0) or 0)`.
