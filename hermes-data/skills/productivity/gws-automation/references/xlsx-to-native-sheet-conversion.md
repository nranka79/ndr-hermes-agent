# xlsx → Native Google Sheet Conversion

When a user shares a Google Sheets link that points to an **xlsx file uploaded to Drive**, the Sheets API rejects direct access with:

```
HttpError 400: "This operation is not supported for this document.
The document must not be an Office file."
```

## Detection

The link format `https://docs.google.com/spreadsheets/d/{fileId}` does **not** distinguish between native Sheets and uploaded xlsx files. The error only appears at API-call time.

Use Drive API to check the MIME type before attempting Sheets API access:

```python
drive = build('drive', 'v3', credentials=creds)
file_info = drive.files().get(fileId=FILE_ID, fields='id, name, mimeType').execute()
# mimeType will be: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

## Fix — Convert via Drive API Copy

```python
converted = drive.files().copy(
    fileId=FILE_ID,
    body={
        'name': 'Original Name (Converted)',
        'mimeType': 'application/vnd.google-apps.spreadsheet'
    },
    fields='id, name, mimeType, webViewLink'
).execute()

GSHEET_ID = converted['id']
```

This creates a native Google Sheet that can be read via the Sheets API normally.

## Same Pattern for Other Office Files

The same mimeType override works for all Office-to-Google conversions:

| Source Format | Target mimeType |
|---|---|
| .xlsx / .xls | `application/vnd.google-apps.spreadsheet` |
| .docx / .doc | `application/vnd.google-apps.document` |
| .pptx / .ppt | `application/vnd.google-apps.presentation` |

See also: `references/drive-docx-to-google-doc-conversion.md` for the .docx variant.

## Pitfall — Owner is the Authenticated User

The converted sheet is **owned by whoever authenticated the Drive API call**, not the original file owner. Share the converted sheet with the original owner/team:

```python
perm = {'type': 'user', 'role': 'writer', 'emailAddress': 'ndr@draas.com'}
drive.permissions().create(
    fileId=converted['id'],
    body=perm,
    sendNotificationEmail=False
).execute()
```

## Pitfall — Vault Socket Down

If `build_service()` fails with `FileNotFoundError: No such file or directory` on the vault socket (`/run/gws-vault/vault.sock`), use file-based token fallback:

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import json

token_path = '/data/hermes/users/{telegram_id}/the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)'  # or the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md) etc.
with open(token_path) as f:
    token_data = json.load(f)

creds = Credentials.from_authorized_user_info(token_data)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())

drive = build('drive', 'v3', credentials=creds)
```

Tokens are not files: they live in the gws-vault daemon. Build clients only via tools.gws_auth.build_service(api, version, service_name=...) (see api-references/google-workspace-api/references/token-access-canonical.md).

## Pitfall — Token Lacks Drive Scope (403: insufficient authentication scopes)

The Drive API copy conversion (`drive.files().copy()` with mimeType override) requires the **Drive scope** (`https://www.googleapis.com/auth/drive`). If the OAuth token was granted with only `gmail.modify` + `spreadsheets` scopes (common for DRAAS tokens authorised for email+sheets but not Drive), the copy operation fails with:

```
HttpError 403: "Request had insufficient authentication scopes."
```

**Detection** — check the token's scopes before attempting conversion:

```python
with open(token_path) as f:
    token_data = json.load(f)
print(f"Scopes: {token_data.get('scopes', 'N/A')}")
# If only ['gmail.modify', 'spreadsheets'] — no Drive scope
```

**Workaround — Create a native sheet from scratch via Sheets API**

When Drive scope is unavailable, you cannot convert the xlsx, upload new files, or set Drive permissions. But you **can** create and populate a native Google Sheet using only the `spreadsheets` scope:

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json

# Load token (same vault-down file fallback)
token_path = '/data/hermes/users/{telegram_id}/the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)'
with open(token_path) as f:
    token_data = json.load(f)

creds = Credentials.from_authorized_user_info(token_data)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())

# Step 1 — Create the spreadsheet (WORKING with only spreadsheets scope)
sheets = build('sheets', 'v4', credentials=creds)
spreadsheet = {
    'properties': {'title': 'My Sheet Name'},
    'sheets': [
        {'properties': {'title': 'Tab 1'}},
        {'properties': {'title': 'Tab 2'}},
    ]
}
result = sheets.spreadsheets().create(
    body=spreadsheet,
    fields='spreadsheetId,spreadsheetUrl'
).execute()
SHEET_ID = result['spreadsheetId']
print(f"Created: {result['spreadsheetUrl']}")

# Step 2 — Populate data (also working with spreadsheets scope only)
sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range="'Tab 1'!A1",
    valueInputOption='USER_ENTERED',
    body={'values': [['Header A', 'Header B'], ['Data 1', 'Data 2']]}
).execute()

# Step 3 — Auto-resize columns
sheets.spreadsheets().batchUpdate(
    spreadsheetId=SHEET_ID,
    body={
        'requests': [{
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': 0, 'dimension': 'COLUMNS',
                    'startIndex': 0, 'endIndex': 10
                }
            }
        }]
    }
).execute()
```

**Limitations when Drive scope is unavailable:**
- Cannot share the sheet with other users (no `drive.permissions().create()`)
- Cannot find or search for existing Drive files
- Cannot upload files to Drive
- The sheet is created **in the authenticated user's Drive** — you must tell the user to share it manually with the intended recipient via the web UI
- The sheet's `spreadsheetUrl` is the shareable link — send it to the user: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`

**When to use this pattern vs when to re-authorize:**

| Situation | Best approach |
|-----------|--------------|
| Token has spreadsheets scope, vault socket down, need to write data ASAP | **Create native sheet from scratch** (no Drive ops needed) |
| Token lacks both drive and spreadsheets scopes | **Re-authorize** with the full scope set |
| Need to share the sheet programmatically | **Re-authorize** with Drive scope, or share manually via web UI |
| Data already exists in an xlsx on Drive | Extract data from xlsx locally (download via Drive API if scope available, or re-extract from source), then create native sheet from scratch |

**Tips for large spreadsheets:**
- Define all tabs upfront in the `sheets` array during `spreadsheets().create()` — you cannot rename/remove the default "Sheet1" tab afterward without a separate `batchUpdate`
- Use `ensure_tab()` helper: call `spreadsheets().get()` first, check if tab exists, create via `addSheet` if not found