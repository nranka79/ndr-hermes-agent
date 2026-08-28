# EC Document Cataloging — Recursive Drive Folder Scan

**Type:** Document Indexing | **Trigger:** User provides a Drive folder containing survey-number-organized subfolders and asks you to extract all EC (Encumbrance Certificate) documents with Drive links.

## When to Use This Reference

- User shares a Drive folder link containing `Sy No` / `Sy.no` / `Survey No` subfolders
- User asks to "extract all EC from each survey no folder" or "generate a spreadsheet with drive links"
- The folder is structured as: `Project Root → Survey No Folders → [Subfolders] → Documents`
- You need to catalog the documents WITHOUT downloading — just capture names, dates, and Drive links

## Key Difference from EC Compilation & Merging

| This Reference | `ec-compilation-merging.md` |
|---|---|
| **Scan-only** — produce index with Drive links | **Download** — produce merged PDF |
| Recursive folder tree traversal | Flat `files.list()` search |
| EC filename pattern matching + exclusion rules | Downloading by name match |
| Output: Google Sheet / CSV with links | Output: merged PDF file |

## Workflow

### Step 1: Authenticate and Identify the Folder

For Byadarahalli-style projects (shared from Nishant's Drive), use Nishant's token:

```python
import os
os.environ['HERMES_SESSION_USER_ID'] = 'ndr'
from tools.gws_auth import build_service
drive_svc = build_service('drive', 'v3', telegram_id='ndr')
folder_id = 'FOLDER_ID_FROM_URL'  # From drive.google.com/drive/u/0/folders/{ID}
```

### Step 2: List All Survey Number Subfolders

```python
query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
result = drive_svc.files().list(q=query, fields='files(id, name)', pageSize=100).execute()
survey_folders = result.get('files', [])
```

### Step 3: Recursive EC Scan with Strict Pattern Matching

**EC detection patterns** (case-insensitive): `EC` at start, `EC ` (space after), `EC.`, `EC-`, `_EC`, "ENCUMBRANCE".

**Exclusions** (false positives that contain "EC" but aren't ECs): Files with RECEIPT, PATTA, RECORD, SURVEY, KHATA, KHATHA, or STRR in name — UNLESS the filename starts with `EC` or has `EC `/ `EC-` (e.g., "EC And Receipt..." = include).

**Recursive traversal:** Enter each survey folder → recurse into subfolders → collect matching files with their Drive links.

### Step 4: Date Range Extraction from Filenames

| Pattern | Example |
|---------|---------|
| `(\d{2}[-\./]\d{2}[-\./]\d{4})\s*to\s*(\d{2}[-\./]\d{2}[-\./]\d{4})` | `01-04-2004 to 23-06-2022` |
| `(\d{4})\s*to\s*(\d{4})` | `1950 to 2004` |

### Step 5: Token Expiry Recovery

**Problem:** Scanning succeeds but Sheet creation fails with `RefreshError: invalid_grant`.

**Fix:** Save scanned data to CSV immediately after Step 3. Generate auth URL for re-authorization via terminal():
```python
cd /opt/hermes && /opt/hermes/.venv/bin/python3 -c "
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import get_auth_url
print(get_auth_url('ndr'))
"
```
After re-auth, reconstruct from CSV → create Sheet.

## Byadarahalli Reference Data (verified Jul 2026)

- **23 survey folders** in root, some with nested subfolders (190 Series has sub-division folders)
- **87 EC documents** (strict filter)
- **Top 5:** Sy.no.221/2 (14), Sy.no.175/1,5,9 (6), Sy.no.219/4,219/7 (6), Sy.no.174/3 (5), Sy.no.180 & 184/5 (5)
- **Surveys with 1 EC:** Sy.no.41/14, Sy.no.182/1,2, Sy.no.218/1,2,3, Sy No 192/2

## Pitfalls

1. **Save data to CSV before attempting Sheet creation** — token may expire mid-work
2. **Broad matching over-includes** (127 raw hits vs 87 genuine ECs) — always apply exclusion rules
3. **Subfolder naming inconsistency** — `Sy.no.`, `Sy.No.`, with/without spaces — just record as-is
4. **Date parsing** — handle dots, underscores, and single-digit formats in filenames