# Drive Duplicate File Analysis & Cleanup Workflow

When the user asks to find duplicate files on their Google Drive, organize root-level clutter, or identify redundant copies.

## Trigger phrases
- "find duplicates on my drive"
- "clean up my drive root"
- "which files are the same"
- "find duplicate documents"

## Workflow

### Step 1 — List all files in the target location

Use the Drive API with pagination. For root folder: `q="'root' in parents and trashed = false"`.

```python
drive = build_service('drive', 'v3', telegram_id='...')
all_files = []
page_token = None
while True:
    results = drive.files().list(
        q="'root' in parents and trashed = false",
        spaces='drive',
        fields='nextPageToken, files(id, name, mimeType, size, md5Checksum, modifiedTime, webViewLink)',
        pageSize=1000, pageToken=page_token
    ).execute()
    all_files.extend(results.get('files', []))
    page_token = results.get('nextPageToken')
    if not page_token: break
```

### Step 2 — Three-pronged duplicate detection

| Method | Key | What it finds |
|---|---|---|
| **Exact MD5** | `f['md5Checksum']` | Identical content (binary files only) |
| **Same filename** | `f['name'].lower()` | Same name, possibly different versions |
| **Normalized name** | Strip dates, version numbers, (converted) suffixes | Near-duplicates: V1/V2/V3, Draft/Final |

Key normalization for near-duplicate matching:
```python
def normalize(name):
    n = name.lower()
    n = re.sub(r'\.[a-z0-9]+$', '', n)           # strip extension
    n = re.sub(r'\d{8}|\d{4}-\d{2}-\d{2}', '', n) # strip dates
    n = re.sub(r'[\(\[][vV]?\d+[\)\]]', '', n)    # strip version numbers
    n = re.sub(r'\b(draft|final|copy|new|v\d+)\b', '', n)
    n = re.sub(r'\s*\(converted[^)]*\)', '', n)   # strip Google Docs conversion markers
    return re.sub(r'\s+', ' ', n).strip()
```

### Step 3 — Identify latest version within each group

Sort each group by `modifiedTime` descending. Mark the first entry as `LATEST`, all others as `DUPLICATE` or `OLDER-VERSION`.

### Step 4 — Special: Zero-byte files

Files with `size == 0` and non-null MD5 `d41d8cd98f00b204e9800998ecf8427e` (empty content hash) are failed uploads or test artifacts. Group separately — always safe to delete.

### Step 5 — Create structured review sheet

Create a Google Sheet with tabs for each duplicate category. Each row needs:

| Column | Purpose |
|---|---|
| **Serial No** | Unique identifier for the user to reference |
| **Group ID** | Groups related copies (e.g., EXACT-MD5-a1b2c3d4 or SAME-NAME-termsheet) |
| **Description** | What this group/file represents |
| **File Name** | The actual filename |
| **Modified Date** | ISO date — must be sortable |
| **Drive Link** | Clickable URL |
| **Size (bytes)** | File size |
| **MD5 Checksum** | First 16 chars of hash (or "Google-Doc" for native files) |
| **Status** | LATEST / DUPLICATE / OLDER-VERSION |

Write using `sheets.spreadsheets().values().update()` with `valueInputOption='USER_ENTERED'` so dates are sortable.

### Step 6 — Deletion workflow

User provides serial numbers of files to delete. Delete using:
```python
drive.files().delete(fileId=file_id).execute()
```
Confirm each deletion. For bulk deletion, batch by calling delete in a loop.

## Pitfalls

- **Google-native files (Docs/Sheets/Slides) have NO md5Checksum** — they can only be compared by name, not content. Tag these as "Google-Doc" in the MD5 column.
- **Zero-byte MD5 `d41d8cd98f00`** is not unique — 18+ zero-byte files may share this hash. Group them separately from real content duplicates.
- **Rate limits:** Drive API allows ~10 queries/second. Pagination with pageSize=1000 is the most efficient approach. A root with 1680 files took 2 pages.
- **Google Docs converted from uploaded .docx** — Drive creates two entries: the raw .docx and a Google Doc with "(converted - date)" appended to the name. Both have different content (one is binary, one is native). Flag these for user review but note they're NOT content duplicates.
