# Renaming a tab / copying a workbook - permission-first recipe

**Never assume `sheetId: 0`.** It is only correct when that happens to be the first
tab's real id. Resolve it by title:

```python
from tools.gws_auth import load_credentials
from tools.gws_ops import sheets_get_tabs, sheets_rename_tab
creds = load_credentials("google-gmail")
print(sheets_get_tabs(creds, SID)["tabs"])          # sheetId | title | rows | cols
print(sheets_rename_tab(creds, SID, "Sheet1", "Report Index"))
```

`gws_sheets_rename_tab` does the whole safe sequence: reads the spreadsheet, resolves
`sheetId` by title, checks the file's `capabilities.canEdit`, then `batchUpdate`s
`updateSheetProperties` and reads the tabs back.

## Permission pre-check (do this before any structural edit)

```python
drive = build_service("drive", "v3", service_name="google-gmail")
meta = drive.files().get(
    fileId=SID,
    fields="id,name,owners(emailAddress),capabilities(canEdit)",
).execute()
```

- `canEdit: false` -> a `batchUpdate`/`values` write returns
  `403 "The caller does not have permission"`. Do not retry. Ask the owner for edit
  access, or work on a workbook owned by the session user.
- `canCopy: true` is **not** a guarantee. An external viewer can still get
  `403 ... reason: insufficientFilePermissions` on `files.copy`, even with
  `supportsAllDrives=True`. This is an owner/domain policy, not a bug. Do not retry
  the copy; create a new workbook owned by the session user or ask the owner.

Real case (2026-11-15, Rivaan): a workbook owned by `sbari@draas.com` had
`canEdit: false`, so `spreadsheets/1YJ8.../batchUpdate` returned
`403 The caller does not have permission`, and `files/1YJ8.../copy` returned
`403 insufficientFilePermissions` despite `canCopy: true`. The correct fallback was a
new workbook owned by `rankarivaan@gmail.com`.

## Copying

```python
f = drive.files().copy(
    fileId=SRC,
    body={"name": NEW_NAME},
    supportsAllDrives=True,
    fields="id,name,webViewLink,owners(emailAddress),capabilities(canEdit)",
).execute()
```

Check the returned `owners` is the session user (or that `canEdit` is true) before
writing to the copy. If the copy 403s, do not loop; fall back as above.

## Values-write gotcha

`NaN`/`Infinity` are not valid JSON. `json.dumps(float("nan"))` emits bare `NaN`, and
Sheets rejects the whole `values().batchUpdate` with
`400 Invalid JSON payload received. Unexpected token ... NaN`. Sanitise at the append
boundary:

```python
def cell(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return ""
    return v
```

Then batch-update in chunks (the Sheets read quota is 60/min per user; read each tab
once and write in batches).
