# Reading Project Area Statement Sheets

## When to use

The user asks for total super built-up area (SUBA), carpet area (CPA), or built-up area (BUA) from a project's area statement spreadsheet. Or asks to find the "execution area statement" / "sanctioned area statement" for a project.

## Drive search strategy

Project area statements are typically named with a date prefix and "Area statement" in the name:

```
YYYYMMDD [Project Name] Area statement
```

Search for multiple name variants:
```python
queries = [
    "name contains 'Area statement' and name contains '[Project]'",
    "name contains '[Project]' and name contains 'area'",
    "name contains '[Project]' and (mimeType contains 'spreadsheet')",
]

# Also check subfolders named after the project
folder_q = "name contains '[Project]' and mimeType = 'application/vnd.google-apps.folder'"
```

## Reading the sheet data

Use the Sheets API directly (not just Drive):

```python
from googleapiclient.discovery import build
sheets = build('sheets', 'v4', credentials=drive._http.credentials)

result = sheets.spreadsheets().values().get(
    spreadsheetId=sheet_id,
    range='A:Z'  # or a specific sheet range
).execute()
rows = result.get('values', [])
```

## Common column structure (construction area statements)

| Col | Header | Description |
|-----|--------|-------------|
| A | S.NO | Serial number |
| B | FLOOR | Floor level (First, Second, Third, Fourth) |
| C | UNIT TYPE | Unit type code (G12, F11, H31, etc.) |
| D | Developer/landowner Share | DEV or LO |
| E | BHK +T | Unit configuration (2BHK+2T, 3BHK+3T, 4BHK+4T) |
| F | FLAT NUMBER | Unit number |
| G | FACING | Direction (EAST, WEST) |
| H | Vastu Score | 1-5 scale |
| I | CPA SQM | Carpet Area in sqm |
| J | CPA SQFT | Carpet Area in sqft |
| K | COMMON AREA | Common area allocation in sqm |
| L | BALCONY SQM | Balcony area in sqm |
| M | UTILITY SQM | Utility area in sqm |
| N | BUA SQM | Built-up area in sqm |
| O | SUBA ON SQM | Super Built-up Area in sqm |
| P | SUBA IN SQFT | Super Built-up Area in sqft |
| Q-R | Undivided Share | UDS values |

## Finding totals row

The last rows of the sheet contain aggregate totals, with empty S.NO and empty UNIT TYPE:

```python
# Print first 15 rows to understand structure
for i, row in enumerate(rows[:15]):
    print(f'Row {i+1}: {row}')

# Print last 10 rows (totals typically here)
if len(rows) > 15:
    for i, row in enumerate(rows[-10:], len(rows)-10):
        print(f'Row {i+1}: {row}')
```

Typical totals: S.NO is empty, UNIT TYPE is empty, and the row contains sums for all numeric columns.

## Worked example — Ranka North Star area statement

Sheet: `20250105 Ranka North Star Area statement` (modified 2026-06-30)
- 61 rows of data
- Row 58 contains unit-level totals: SUBA = 8,834 SQM / 95,053.84 SQFT
- Additional rows below the totals row may contain:
  - Land Area (44,920 SQFT)
  - Common Area (2,266.52 SQM)
  - Other aggregates

## Reporting

Present the key figures clearly:
- **Total Super Built Up Area (SUBA):** X SQM / Y SQFT
- **Total Built Up Area (BUA):** X SQM
- **Total Carpet Area (CPA):** X SQM / Y SQFT
- **Total Balcony:** X SQM
- **Total Utility:** X SQM
- **Common Area:** X SQM
- **Undivided Share (UDS):** X SQFT

Always include the Google Sheet link so the user can verify.