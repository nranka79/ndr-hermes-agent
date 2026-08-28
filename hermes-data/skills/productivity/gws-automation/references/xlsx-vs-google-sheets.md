# `.xlsx` (binary) vs Google Sheets (native) — Read Pattern

**Pitfall:** A `.xlsx` file uploaded to Drive is a **binary** file, NOT a Google Sheet. The two common errors:

1. `sheets.spreadsheets().get(spreadsheetId=...)` → `HttpError 400 "This operation is not supported for this document. The document must not be an Office file."`
2. `drive.files().export(fileId, mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')` → same 400 error

## Working pattern — download + openpyxl

```python
import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive"]
TOKEN_PATH = Path(os.environ.get("HERMES_HOME", "/data/hermes")) / "users" / os.environ["HERMES_SESSION_USER_ID"] / "the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)"
creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    TOKEN_PATH.write_text(creds.to_json())

drive = build("drive", "v3", credentials=creds)

# 1. Download via get_media (NOT export)
resp = drive.files().get_media(fileId="<XLSX_FILE_ID>").execute()
with open("/tmp/file.xlsx", "wb") as f:
    f.write(resp)

# 2. Install openpyxl if missing
# uv pip install openpyxl --python /opt/hermes/.venv/bin/python3

# 3. Parse
import openpyxl
wb = openpyxl.load_workbook("/tmp/file.xlsx", data_only=True)
for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]
    print(f"=== Sheet: {sheet_name} ===")
    for row in ws.iter_rows(values_only=True):
        if any(c is not None and str(c).strip() for c in row):
            print(row)
```

## How to tell the difference

| mimeType in Drive | What it is | How to read |
|---|---|---|
| `application/vnd.google-apps.spreadsheet` | Native Google Sheet | Sheets API `sheets.spreadsheets().values().get(...)` |
| `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | Binary .xlsx (Excel) | `get_media` + `openpyxl` |
| `application/vnd.ms-excel` | Old .xls (Excel 97-2003) | `get_media` + `xlrd` (legacy) |

Always check the mimeType first: `drive.files().get(fileId=..., fields="mimeType")` — one extra call beats a wasted Sheets API attempt.

## Session example (04 Jun 2026)

`NDR Medical Report Index - Updated.xlsx` (file ID `1wfk9UlWo0DW-9Lf4kU5txkgTm-1OYtes`) — 99 rows of medical reports + prescriptions indexed with dates, types, names, and Drive links. Confirmed used as ground truth for "what medical files does Nishant have on file" before claiming any prescription is/isn't in Drive. Sheets API on it returns 400; download + openpyxl works.
