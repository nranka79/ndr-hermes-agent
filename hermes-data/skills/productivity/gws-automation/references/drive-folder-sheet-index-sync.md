# Drive Folder ↔ Spreadsheet Index Cross-Reference

When a Drive folder contains files tracked by an index spreadsheet, this pattern finds what's missing from the index and adds it.

## Use Case
- Medical report folders with an RR Medical Report Index sheet
- Document depositories with a master index
- Any folder where files exist but the index is incomplete

## Steps

### 1. List all files in the Drive folder

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

FOLDER_ID = "0B1Oc8cSaJXPG..."
page_token = None
folder_files = {}
while True:
    response = drive.files().list(
        q=f"'{FOLDER_ID}' in parents and trashed=false",
        spaces='drive',
        fields='nextPageToken, files(id, name, mimeType, size, md5Checksum)',
        pageToken=page_token,
        orderBy='name'
    ).execute()
    for f in response.get('files', []):
        folder_files[f['name']] = f
    page_token = response.get('nextPageToken')
    if not page_token:
        break
```

### 2. Read existing index spreadsheet

```python
sheets = build_service('sheets', 'v4')
result = sheets.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="SheetName"
).execute()
rows = result.get('values', [])
```

### 3. Extract all file IDs already indexed

Links are typically in a column formatted as `https://drive.google.com/file/d/FILE_ID/view`.

```python
import re
indexed_file_ids = set()
for row in rows[1:]:  # skip header
    if len(row) >= 5:
        link = row[4]  # column E typically holds the link
        for pattern in [r'/file/d/([a-zA-Z0-9_-]+)',
                        r'/spreadsheets/d/([a-zA-Z0-9_-]+)',
                        r'/document/d/([a-zA-Z0-9_-]+)']:
            m = re.search(pattern, link)
            if m:
                indexed_file_ids.add(m.group(1))
```

### 4. Get MD5 checksums of indexed files (catch renamed duplicates)

Some files in the folder are byte-identical to already-indexed files but have different names (e.g. pipeline-renamed copies with underscores vs human-readable names).

```python
indexed_md5s = set()
for fid in indexed_file_ids:
    try:
        f = drive.files().get(fileId=fid, fields='md5Checksum').execute()
        if f.get('md5Checksum'):
            indexed_md5s.add(f['md5Checksum'])
    except:
        pass  # file may be deleted or inaccessible
```

### 5. Find truly missing files

```python
skip_names = {"RR Medical Report Index (Ruhaan Ranka)", "non-medical files to skip"}
seen_md5 = set()
files_to_add = []

for name, f in sorted(folder_files.items()):
    if name in skip_names:
        continue
    fid = f['id']
    md5 = f.get('md5Checksum', '')
    if fid in indexed_file_ids:
        continue
    if md5 and md5 in indexed_md5s:
        continue        # already indexed under different name
    if md5 and md5 in seen_md5:
        continue        # duplicate within the folder
    if md5:
        seen_md5.add(md5)
    files_to_add.append((name, fid))
```

### 6. Build new rows and batch update

```python
last_sl_no = max(int(r[0]) for r in rows[1:] if r and r[0].isdigit())
new_rows = []

for name, fid in files_to_add:
    last_sl_no += 1
    link = f"https://drive.google.com/file/d/{fid}/view"
    # Parse date from filename if possible
    m = re.match(r'(\d{8})', name)
    date_str = f"{d}/{mth}/{y}" if m and valid_year(y) else ""
    new_rows.append([str(last_sl_no), rtype, date_str, name, link, name])

body = {
    "valueInputOption": "USER_ENTERED",
    "data": [{
        "range": f"SheetName!A{len(rows)+1}:F{len(rows)+len(new_rows)}",
        "majorDimension": "ROWS",
        "values": new_rows
    }]
}
sheets.spreadsheets().values().batchUpdate(
    spreadsheetId=SPREADSHEET_ID, body=body
).execute()
```

## Type Inference from Filename

For medical report indexes, infer the TYPE column from filename patterns:

| Pattern | Type |
|---------|------|
| `X RAY`, `CT SCAN`, `MRI`, `ULTRASONOGRAPHY`, `USG`, `ULTRASOUND`, `OPG`, `DENTAL PANO` | `RADIOLOGY REPORT` |
| ` P ` (before hospital name) | `PRESCRIPTION` |
| ` A ` (before hospital name) | `ADVISE` |
| ` P/A ` | `PRESCRIPTION / ADVISE` |
| `BILL`, `PHARMACY INVOICE` | `BILL` |
| Everything else | `REPORT` |

## Pitfalls
- **Duplicate files with different names**: The underscore-pipeline copies (e.g. `20240506_Ruhaan...pdf` vs `20240506 Ruhaan...pdf`) are byte-identical. Always check MD5, not just file ID.
- **Non-medical files in the folder**: Skip index spreadsheets themselves, address lists, audio recordings.
- **Date extraction from filename**: `YYYYMMDD` at the start of the filename. Validate year (should be between 2010-2030 for current records). Invalid dates → leave date blank.
- **Batch update size**: Sheets API accepts up to ~500 rows per batchUpdate call. For larger updates, chunk into batches of 200.
