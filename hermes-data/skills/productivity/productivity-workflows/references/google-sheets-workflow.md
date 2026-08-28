# Google Sheets Workflow — Absorbed from productivity/google-sheets-workflow

## What This Reference Covers

Google Sheets API v4 — reading, appending, updating rows, finding sheet structure, Drive folder spreadsheet creation, formatting.

**Skill status:** Absorbed into `productivity-workflows` umbrella (2026-05-29). Original at `productivity/google-sheets-workflow/`.

## Core Tools

- `from tools.gws_auth import build_service` — for personal workspace sheets
- `build_service("sheets", "v4")` → returns Resource object with `.spreadsheets()` access
- For shared DRAAS data: `from tools.gws_sa import build_service` (SA DWD, subject: ndr@draas.com)

## Standard Workflow

1. **Locate file** — `drive.files().list` with `name contains 'TARGET' and trashed=false`
2. **Read structure** — `spreadsheets().get(includeGridData=True)` for row/column counts
3. **Read data** — `values().get(range="'Sheet'!A1:J50")`
4. **Prepare & confirm** — always present update table before writing to shared sheets
5. **Write** — `values().update()` for specific cells; `values().append()` for end-of-sheet

## Critical Pitfalls

- **`append` ignores your range row hint** — it goes to bottom of existing data. Use `update()` with explicit cell reference for positional writes.
- **`fields` syntax doesn't work for sheet titles** — don't use `'sheets(title,properties)'` in get(). Inspect `response['sheets'][i]['properties']['title']` directly.
- **Calendar API version is lowercase `v3`** — `build_service('calendar', 'V3')` fails. Use `v3` lowercase.
- **Use `datetime.now(datetime.UTC)` not `datetime.utcnow()`** — latter is deprecated.
- **Auth failures** — `FileNotFoundError` from `build_service` means user hasn't authorized yet. Call `tools.gws_auth.get_auth_url(telegram_id)`.

## Create Spreadsheet in Drive Folder

```python
drive_service = build_service("drive", "v3")
spreadsheet = drive_service.files().create(
    body={
        "name": "Spreadsheet Name",
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": ["<folder_id>"]  # ← folder ID, not spreadsheet ID
    },
    fields="id, name, webViewLink"
).execute()
```

## Format Header Row Bold

```python
sheets_service.spreadsheets().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={"requests": [{
        "repeatCell": {
            "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1,
                      "startColumnIndex": 0, "endColumnIndex": 5},
            "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
            "fields": "userEnteredFormat.textFormat.bold"
        }
    }]}
)
```

## Auto-Resize Columns

```python
sheets_service.spreadsheets().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={"requests": [{
        "autoResizeDimensions": {
            "dimensions": {"sheetId": 0, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 5}
        }
    }]}
)
```

## Confirm-Before-Write Pattern

When updating shared sheets, always present a confirmation table first:
```
| Row | Field | Current Value | New Value |
|-----|-------|--------------|-----------|
| 2   | Floor | GF1          | GF2       |
```
