# Drive Folder → Sheet Index Document Audit

Cross-reference a Google Sheet index (document checklist) against actual files in a Drive folder to audit document readiness and update the sheet statuses.

## When to use

- User shares a Google Sheet that lists required documents with statuses
- User points to a Drive folder where documents should be stored
- Goal: verify which documents are actually present and update the sheet

## Workflow

### 1. Build services (both needed)

```python
import sys
sys.path.insert(0, '/opt/hermes')
os.environ['HERMES_SESSION_USER_ID'] = 'psingh'  # or the user's Telegram ID
from tools.gws_auth import build_service

sheets = build_service('sheets', 'v4')
drive = build_service('drive', 'v3')
```

**Important:** Set `HERMES_SESSION_USER_ID` explicitly in the env — terminal subprocesses don't auto-inherit it. Use the user's Telegram ID from context.

### 2. Read the sheet index

```python
sid = 'SPREADSHEET_ID'
data = sheets.spreadsheets().values().get(spreadsheetId=sid, range='A:H').execute()
values = data.get('values', [])
```

Column layout is typically:
- A = Item #
- B = Category
- C = Required Document
- D = Updated Status
- E = File Name
- F = Drive Link
- G = Folder Location
- H = Remarks

### 3. List all files in the target Drive folder recursively

```python
def list_all_files(folder_id, indent=0):
    query = f"'{folder_id}' in parents and trashed=false"
    page_token = None
    while True:
        results = drive.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType)',
            pageSize=200,
            pageToken=page_token
        ).execute()
        for f in results.get('files', []):
            if f['mimeType'] == 'application/vnd.google-apps.folder':
                list_all_files(f['id'], indent + 1)
            else:
                files.append(f)
        page_token = results.get('nextPageToken')
        if not page_token:
            break
```

### 4. Cross-reference: map sheet rows to folder files

Build a lookup dict from file names in the folder. For each sheet row:
- Search the folder file list by keywords (document name, entity name)
- Update status: ✅ Available / ⚠️ Needs Fix / ❌ Pending
- Update file name, Drive link, and folder location columns

### 5. Batch-update the sheet

```python
updates = [
    {'range': 'D5:H5', 'values': [['✅ Available', 'File Name.pdf', 'https://...', 'Folder', 'Remarks']]},
    # ... one per changed row
]
for upd in updates:
    sheets.spreadsheets().values().update(
        spreadsheetId=sid,
        range=upd['range'],
        valueInputOption='USER_ENTERED',
        body={'values': upd['values']}
    ).execute()
```

## Pitfalls

### Sheet row numbering (1-indexed vs 0-indexed)

This is the most common error. Google Sheets A1 notation is **1-indexed**, but Python list indexing is **0-indexed**.

| Data row (0-indexed) | Sheet row (A1) | Content |
|---|---|---|
| `values[0]` | Row 1 (A1) | Header |
| `values[4]` | Row 5 (A5) | 1d — Land owners Aadhaar |

If you're updating row 1d (data index 4), the range is `D5:H5`, **not** `D4:H4`. Using the wrong index overwrites the wrong row silently.

**Double-check before applying:** Print the current row content at your target sheet row to verify:
```python
row_data = sheets.spreadsheets().values().get(
    spreadsheetId=sid, range=f'A{target_row}:H{target_row}'
).execute().get('values', [[]])[0]
print(f"Will overwrite: {row_data}")
```

### Partial file name matches

Folder file names are often similar but not identical to document checklist descriptions. Use substring/keyword matching, not exact match. Keep a manual mapping for ambiguous cases.

### Rate limits

Google Sheets API has write limits. Batch reads (one `get` for the full range) then write only changed rows. For 5-10 row updates, individual `update()` calls are fine. For 50+ rows, batch the writes into fewer calls.

### File not found vs file exists but wrong format

A .docx file that hasn't been signed is functionally different from a signed PDF. Distinguish in the status:
- ✅ Available = signed/completed file exists
- ⚠️ Needs Fix = file exists but needs changes (wrong format, needs signature, mismatch)
- ❌ Pending = file not found at all
