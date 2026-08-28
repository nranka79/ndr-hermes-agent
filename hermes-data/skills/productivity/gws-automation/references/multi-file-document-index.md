# Multi-File Document Index from Multiple Photos

Pattern: user sends 2+ photos of printed document index pages (File No. 1, File No. 2, etc.) and wants them combined into a single spreadsheet with section headers.

## Trigger
- User sends photos of property document indexes labeled "File No. 1", "File No. 2", etc.
- User says "add these to the same sheet below the existing ones"

## Workflow

### 1. Extract each photo with vision_analyze
```
vision_analyze(image_url=photo_path, question="Extract full table: SI No., Particulars, Document No., Date for each row.")
```

### 2. Create the xlsx with section headers per file number
```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

wb = Workbook()
ws = wb.active

# Style setup (standard header, border, etc.)
section_fill = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
section_font = Font(bold=True, size=12, color="2F5496")

ws.merge_cells('A1:G1')
ws['A1'] = 'INDEX OF DOCUMENTS — PROPERTY NAME'
ws['A1'].font = Font(bold=True, size=14)

row = 3
headers = ['SI No.', 'Particulars', 'Document No.', 'Date',
           'Original / Photocopy', 'Handed Over (Yes/No)', 'Remarks']
# ... write headers ...

row = 4
# FILE NO. 2 section first (if user sent it first)
ws.merge_cells(f'A{row}:G{row}')
ws[f'A{row}'] = 'FILE NO. 2'
ws[f'A{row}'].font = section_font
ws[f'A{row}'].fill = section_fill
row += 1

# File No. 2 documents ...

row += 1
# FILE NO. 1 section
ws.merge_cells(f'A{row}:G{row}')
ws[f'A{row}'] = 'FILE NO. 1'
ws[f'A{row}'].font = section_font
ws[f'A{row}'].fill = section_fill
row += 1

# File No. 1 documents ...
```

### 3. Upload as native Google Sheet (co-editing safe)
Use `mimeType='application/vnd.google-apps.spreadsheet'` so the user can fill in Original/Photocopy and Handed Over columns without risk of overwrite.

### 4. Append additional file numbers later via Sheets API
When user sends a third photo ("File No. 3"), use Sheets API to append:

```python
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4')

# First append a section header row
sheets.spreadsheets().values().append(
    spreadsheetId=sheet_id,
    range='A:G',
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body={'values': [['FILE NO. 3', '', '', '', '', '', '']]}
).execute()

# Then append document rows
new_rows = [
    [1, "Document description", "DOC-001", "01.01.2020", "", "", ""],
]
sheets.spreadsheets().values().append(
    spreadsheetId=sheet_id,
    range='A:G',
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body={'values': new_rows}
).execute()
```

## Pitfalls

- **Never use `files().update()`** if the user is co-editing the sheet in Google Sheets. This replaces the entire file and wipes their edits. Convert to native Google Sheet + use Sheets API.
- **File numbering confusion:** The user may call the first photo "File No. 2" and the second photo "File No. 1" — preserve their ordering exactly as they describe.
- **Dates:** Some entries may be handwritten or faded. Leave blank and flag to the user. Don't guess.
- **Section styling:** Use light blue section fill (D6E4F0) to visually distinguish file number sections from data rows.
