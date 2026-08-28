# Google Sheets — Create and Populate

Pattern for creating a new Google Sheet, setting permissions, and writing structured data with headers, description rows, and data rows.

## Basic Create + Write

```python
from gws_auth import build_service

drive = build_service('drive', 'v3', telegram_id='USER_TG_ID')
sheets = build_service('sheets', 'v4', telegram_id='USER_TG_ID')

# Create sheet
body = {
    'properties': {'title': 'Sheet Title'},
    'sheets': [{'properties': {'title': 'Sheet1 Name'}}]
}
sheet = sheets.spreadsheets().create(body=body, fields='spreadsheetId').execute()
sheet_id = sheet['spreadsheetId']

# Set permissions (anyone with link, reader)
drive.permissions().create(
    fileId=sheet_id,
    body={'type': 'anyone', 'role': 'reader'},
    fields='id'
).execute()

# Write a title row
sheets.spreadsheets().values().update(
    spreadsheetId=sheet_id, range='Sheet1!A1',
    valueInputOption='RAW',
    body={'values': [['TITLE ROW']]}
).execute()

# Write description rows
sheets.spreadsheets().values().update(
    spreadsheetId=sheet_id, range='Sheet1!A3:D5',
    valueInputOption='RAW',
    body={'values': [
        ['DESCRIPTION HEADER'],
        ['Description text explaining the purpose of this sheet.'],
        ['']
    ]}
).execute()

# Write header row
sheets.spreadsheets().values().update(
    spreadsheetId=sheet_id, range='Sheet1!A7:D7',
    valueInputOption='RAW',
    body={'values': [['Col A', 'Col B', 'Col C', 'Col D']]}
).execute()

# Write data rows
sheets.spreadsheets().values().update(
    spreadsheetId=sheet_id, range='Sheet1!A8:D10',
    valueInputOption='RAW',
    body={'values': [
        ['Row 1 A', 'Row 1 B', 'Row 1 C', 'Row 1 D'],
        ['Row 2 A', 'Row 2 B', 'Row 2 C', 'Row 2 D'],
    ]}
).execute()
```

## Best Practices

- **Title row + blank rows + header + data** — this layout gives visual hierarchy in the sheet
- Use `valueInputOption='RAW'` for plain text, or `'USER_ENTERED'` to let Sheets interpret formulas/dates
- Write in batches — Sheets API accepts up to ~10MB per request
- Always set permissions immediately after creation so the file is accessible before anyone tries to open it

## Common Use Cases in Medical Documentation

### "Medical Facts & Corrections" Sheet Pattern
When prescriptions and doctor notes may contain conflicting or incomplete information, create a companion sheet with labeled columns:

```
Date/Period | Category | Fact (absolute) | Source/Rationale
```

With a prominent description at the top:
> "ABSOLUTE FACTS — These notes contain verified facts that overrule any conflicting information in prescriptions or doctor notes."

This pattern is useful when:
- Multiple doctors gave conflicting advice during an episode
- Verbal instructions differ from written prescriptions
- Timeline corrections need to be recorded alongside original documents
- The user needs a single source of truth to share with future specialists

## Pitfalls

- `gridProperties` is a field on `sheets[0].properties` NOT at the top level of the request body. Use `{'properties': {'title': 'Sheet Name'}}` for the sheet, not `{'gridProperties': ...}`
- Sheets API does NOT support merged cells via the `values.update` endpoint — you need `spreadsheets.batchUpdate` with `mergeCells` request for that
- Setting permissions requires Drive scope (drive.file or drive), not just Sheets scope
- If you need the sheet to be editable by others, use `{'role': 'writer'}` instead of `'reader'`
