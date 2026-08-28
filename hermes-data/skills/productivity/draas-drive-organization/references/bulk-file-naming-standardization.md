# Bulk File Naming Standardization on Drive

When a Drive folder contains dozens of files with inconsistent filenames (broken extensions, casing errors, spacing issues, typos, duplicate copies), systematically analyze and standardize them.

## Workflow

### 1. Discover the Folder

Drive API folder search by partial name:

```python
# Find by exact folder name
results = drive.files().list(
    q="name='AHFL FILE 10' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    fields='files(id, name, parents, webViewLink)'
).execute()

# Find by partial match (all AHFL FILE folders)
results = drive.files().list(
    q="name contains 'AHFL FILE' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    fields='files(id, name, parents, webViewLink)',
    orderBy='name'
).execute()
```

### 2. List All Files with Full Metadata

Use pagination to get every file. Always include `id`, `name`, `mimeType`, `size`, `modifiedTime`, `webViewLink`:

```python
page_token = None
all_files = []
while True:
    results = drive.files().list(
        q=f"'{FOLDER_ID}' in parents and trashed=false",
        fields='files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)',
        pageSize=100,
        pageToken=page_token,
        orderBy='name'
    ).execute()
    files = results.get('files', [])
    all_files.extend(files)
    page_token = results.get('nextPageToken')
    if not page_token:
        break
```

### 3. Identify Filename Issues

Scan each filename for these common problems:

| Issue | Example | Fix |
|-------|---------|-----|
| **Missing `.pdf` extension** (text directly after name) | `Fernandespdf` | `Fernandes.pdf` |
| **Broken extension** (`.kardesai` instead of `.pdf`) | `Name Jayamangala S.kardesai` | Replace with `.pdf` |
| **Missing space** (`Formof` → `Form of`) | `Formof Declaration` | `Form of Declaration` |
| **Extra spaces** | `No 84 .Name`, `Name. Kavan` | Normalize spacing |
| **Extra dots** (`..pdf`) | `Chavan..pdf` | Remove extra dots |
| **Trailing spaces** before extension | `Raikar .pdf` | Remove trailing space |
| **Lowercase names** where Title Case expected | `name shekhar` | `Name Shekhar` |
| **Typos** | `Rohihi` → `Rohini` | Correct spelling |
| **Dot in wrong place** (`Name.Manjula`) | `Name.Manjula S ramaiah` | `Name_Manjula_S_Ramaiah` |
| **Missing zero-padding** on numbers | `No 84` | `No 084` |
| **Duplicate files** (same form number repeated) | 3× `No 357` | Append `_Copy1`, `_Copy2`, `_Copy3` |
| **Undated files** | `Original challan Receipt.pdf` | Prepend `Undated_` |
| **Patronymic/alias in name** unnecessarily long | `Jitesh Agarwal Son of Laxmandas Agarwal` | Strip to `Jitesh Agarwal` |

### 4. Define the Naming Convention

Standard pattern for legal/declaration documents:

```
YYYYMMDD_Form_of_Declaration_No_NNN_Name_PersonName.pdf
```

- **YYYYMMDD** — 8-digit date prefix (no spaces, no dots)
- **Form_of_Declaration** — fixed document type (Title Case with underscores)
- **No_NNN** — zero-padded form number (3+ digits)
- **Name_PersonName** — person's name in Title Case, underscores for spaces
- Receipt/challan files: `Undated_DescriptiveName.pdf`

### 5. Verify Problematic Files

For filenames with ambiguous content (broken extension, mangled name, weird characters), download and inspect:

```python
request = drive.files().get_media(fileId=file_id)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()
with open(local_path, 'wb') as f:
    f.write(fh.getvalue())
```

If the PDF is a scanned image (no extractable text via pdftotext or pdfminer), **trust the visual content** of the filename itself — the original uploader's naming is the best signal for scanned docs. Use vision_analyze or OCR (tesseract) as a last resort if the filename is truly ambiguous.

### 6. Produce the JSON Mapping

Output a JSON array with every file. Each entry should include:

```json
{
  "old_name": "20190802  Form of Declaration No 148 Name Leonara John Fernandespdf",
  "new_name": "20190802_Form_of_Declaration_No_148_Name_Leonara_John_Fernandes.pdf",
  "file_id": "151EjyavYam41PYlm9sOTmYux_1rxA_Gc",
  "size_mb": 2.8,
  "description": "Fixed broken extension ('Fernandespdf' → 'Fernandes.pdf'). Removed double space after date."
}
```

**Description field** should itemise every fix applied so the user can review and approve before renaming is executed.

### 7. Rename (after user approval)

Once the JSON mapping is approved, rename files on Drive (one by one):

```python
for item in data:
    drive.files().update(
        fileId=item['file_id'],
        body={'name': item['new_name']}
    ).execute()
```

### 8. Create Master Index (Google Sheet)

After all files are renamed, create a Google Sheet inside the parent folder as master index:

```python
# Create sheet in parent folder
sheet_meta = drive.files().create(
    body={'name': 'AHFL_Master_Index',
          'parents': [PARENT_FOLDER_ID],
          'mimeType': 'application/vnd.google-apps.spreadsheet'},
    fields='id,webViewLink'
).execute()

# Write header + data
sheets = build('sheets', 'v4', credentials=creds)
header = ['New File Name', 'Sub-Folder', 'Folder Link', 'File Link', 'Description']
sheets.spreadsheets().values().update(
    spreadsheetId=sheet_id, range='A1', valueInputOption='RAW',
    body={'values': [header] + rows}
).execute()
```

Index columns: File Name, Sub-Folder, Folder Link (clickable), File Link (clickable), Description.

## Scaling: Parallel Sub-Agent Analysis for 100+ Files

When a single folder tree has 100+ files across sub-folders, use `delegate_task` with tasks array for parallel analysis:

1. **Batch folders into groups of ≤3** (max parallel children): batch 1 = folders A,B,C; batch 2 = folders D,E,F
2. **Each sub-agent gets** the full file list (name, ID, size, date) for its assigned folder(s) and returns JSON: `[{old_name, new_name, folder, description}, ...]`
3. **Parent merges** all JSON outputs, detects cross-folder duplicate-new-name conflicts, appends suffixes
4. **Parent executes** `drive.files().update(fileId, body={'name': new_name})` for each file
5. **Parent creates** master index sheet (see §8)

**Pitfalls for parallel analysis**: Sub-agents cannot call Drive API — they return proposals. Max 3 concurrent. Cross-folder duplicate detection is the parent's responsibility. Each sub-agent writes its output to a JSON file; parent reads them all back.

## Vault Token Access (Cross-User)

When session user differs from token owner, bypass session-context auth:

```python
from tools.gws_vault_client import get_token
from google.oauth2.credentials import Credentials

CANONICAL_UID = 'ndr-[REDACTED-TID]'  # from canonical_uid()
token_json = get_token(CANONICAL_UID, 'google-draas', session_uid=CANONICAL_UID)
creds = Credentials.from_authorized_user_info(json.loads(token_json))
drive = build('drive', 'v3', credentials=creds)
```

Only use when you know the canonical UID from `canonical_uid()` resolution. Never hardcode raw Telegram IDs.

## Pitfalls

- **Never rename without user review first** — some filename oddities may be intentional (e.g., legal document abbreviations). The JSON mapping is a proposal, not an execution plan.
- **Scanned PDFs have no extractable text** — you cannot verify the person's name from the PDF content. The original Drive filename is your only signal. If in doubt, note the uncertainty in the description.
- **Drive allows duplicate names** — the same folder can have multiple files named `No 357`. Distinguish by `file_id`, not by name. Append `_Copy1/2/3` to disambiguate.
- **`parents='X' in parents` query may return 0** for a folder that exists and has files (known Drive API quirk). Verify by name-search + parent-filter as fallback.
- **Cross-account ownership** — if the folder is owned by an external account (e.g., `bk@findingform.design`), `files().update()` to rename may fail with permission errors. Renaming requires `canEdit` capability. Check before attempting.
- **Pagination** — `files().list()` returns at most 100 files per page. Always use `pageToken` loop for folders with >100 items.

## Related

- `document-version-chronology.md` — Building timelines from Drive metadata (complements file identification step)
- `drive-file-rename-move.md` — Technical details on Drive rename/move operations and permission boundaries
