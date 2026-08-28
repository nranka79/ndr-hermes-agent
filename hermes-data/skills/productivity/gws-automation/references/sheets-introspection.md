# Sheets Introspection

Read the structure and content of a Google Sheet programmatically.

## List All Sheets (Tabs) with Grid Properties

```python
import sys
sys.path.insert(0, '/opt/hermes/tools')
from gws_auth import build_service

sheets = build_service('sheets', 'v4', telegram_id='USER_TELEGRAM_ID')
sheet_id = 'SPREADSHEET_ID_FROM_URL'  # e.g. '1MF0kWgkdxoKbiJOcAFKemwT8UPBQKdL4oKndZtWHRv0'

# Get all sheet names and grid dimensions
result = sheets.spreadsheets().get(
    spreadsheetId=sheet_id,
    fields='sheets.properties'
).execute()

for s in result.get('sheets', []):
    p = s.get('properties', {})
    print(f"Sheet: {p.get('title')} | "
          f"Rows: {p['gridProperties'].get('rowCount')} | "
          f"Cols: {p['gridProperties'].get('columnCount')} | "
          f"Frozen: {p['gridProperties'].get('frozenRowCount', 0)}")
```

## Read a Range from a Sheet

```python
result = sheets.spreadsheets().values().get(
    spreadsheetId=sheet_id,
    range="'Sheet Name'!A1:Z50"  # Sheet name in quotes if has spaces
).execute()

rows = result.get('values', [])
for i, row in enumerate(rows):
    print(f"Row {i+1}: {row}")
```

## Sheet URL → ID

- URL format: `https://docs.google.com/spreadsheets/d/1MF0kWgkdxoKbiJOcAFKemwT8UPBQKdL4oKndZtWHRv0/edit`
- The ID is the segment between `/d/` and `/edit`: `1MF0kWgkdxoKbiJOcAFKemwT8UPBQKdL4oKndZtWHRv0`

## Common Patterns

| Task | Method | Range format |
|---|---|---|
| Read header row | `values().get(range="'Sheet'!A1:Z1")` | First row only |
| Read full sheet | `values().get(range="'Sheet'!A:Z")` | All rows |
| Check row count | `get(fields='sheets.properties.gridProperties.rowCount')` | Metadata only |
| Write to sheet | `values().update(range="'Sheet'!A1", body={'values': [['data']]}, valueInputOption='USER_ENTERED')` | Must specify range |

## Pitfalls

- Sheet names with spaces/special chars must be wrapped in single quotes: `'Sy No 87'!A1`
- Empty cells are omitted from the `values` array — a row with [A=foo, C=baz] returns `['foo', None, None, 'baz']`? Actually the API omits trailing empty cells. Use `majorDimension='COLUMNS'` or pre-fill with None checks.
- `frozenRowCount` is only available via the `get()` metadata call, not from `values().get()`.
- **Special characters cause 400 errors:** The em-dash (—), curly quotes, and other non-ASCII Unicode typographic characters in cell VALUES cause a 400 "Invalid values" error when writing via the Sheets API. Use simple ASCII equivalents: hyphen (`-`) instead of em-dash (`—`), straight quotes instead of curly quotes. This applies to cell content, not sheet/tab names. Always sanitize strings before writing them to Sheets if they might contain rich-text typographic characters.
- **🚨 sheetId is NOT always 0 for batchUpdate.** When a Google Sheet is created by importing an .xlsx file, the default sheet gets a random numeric ID (e.g. 271248360), NOT 0. If you hardcode `'sheetId': 0` in a `batchUpdate` request, you get: `Invalid requests[0].repeatCell: No grid with id: 0`. Always fetch the actual sheet ID first:
  ```python
  spreadsheet = sheets.spreadsheets().get(
      spreadsheetId=SHEET_ID,
      fields='sheets.properties'
  ).execute()
  gid = spreadsheet['sheets'][0]['properties']['sheetId']
  # Use gid (not 0) in all batchUpdate requests
  ```
  Sheets created via `sheets.spreadsheets().create()` start with sheetId=0, but imported .xlsx files do not.

- **🚨 Column letter off-by-one with `chr(64+col)`.** When computing Excel column letters from 0-indexed column numbers, `chr(64+col)` gives the WRONG letter. 0-indexed 4 = column E, but `chr(64+4)` = chr(68) = 'D'. The correct formula is `chr(64+col+1)`:
  ```python
  col_0indexed = 4  # start date column
  excel_letter = chr(64 + col_0indexed + 1)  # 'E', correct
  wrong = chr(64 + col_0indexed)              # 'D', wrong — writes to wrong column
  ```
  This is easy to miss because `chr(64+1)='A'` works at column 0 but falls behind by 1 for every column beyond that. Always test with a cell you can verify visually after the first batch write.
