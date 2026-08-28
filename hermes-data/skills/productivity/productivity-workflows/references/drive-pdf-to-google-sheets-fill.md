# Drive PDF → Google Sheets Fill Workflow

## When to Use

Extracting structured data from Drive PDFs (master plans, sanction letters, area statements) and filling it into a Google Sheets project data spreadsheet. Trigger: user says "fill these details" or "extract from Drive into spreadsheet."

## Pattern This Session Established (Ranka Oasis, June 2026)

**Steps:**
1. Get spreadsheet ID from user (share link or direct)
2. `values.get(range='SheetName!A1:Z5')` — read row 1 to confirm column headers
3. Identify which rows already have values vs. which need filling
4. For each unfilled row, search Drive for relevant document
5. Download PDF via `drive.files().get_media(fileId)` (binary) or `export_media` (Google Docs)
6. `pdftotext` for text PDFs; `pdftoppm` + `pdf2image` + `vision_analyze` for layout/image PDFs
7. Extract figures from vision output
8. Batch fill via `values.update()` — confirm each field before writing

**Key lesson (Bharat, June 2026):** When user says "you will find details in the approved plans folder," FIRST search Drive for "Approved Plans" or "Master Plan" by exact name, THEN browse the folder structure. The Ranka Oasis Master Plan was at `1yLBO1NbMiH2qmB8wkdkkt9SNIIlOOZW6` — found by searching `name contains 'Master Plan' and trashed=false` then filtering for "Ranka Oasis."

## PDF to Vision Extraction Pattern

```python
# Step 1: Download PDF from Drive
r = requests.get(
    f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media",
    headers={"Authorization": f"Bearer {access_token}"}
)
with open('/tmp/doc.pdf', 'wb') as f:
    f.write(r.content)

# Step 2: Convert to image
from pdf2image import convert_from_path
pages = convert_from_path('/tmp/doc.pdf', dpi=150)
pages[0].save('/tmp/doc_page1.jpg', 'JPEG', quality=85)

# Step 3: vision_analyze
# Ask for: total land area, plot count, road widths, amenities, unit count, floor details
```

## Google Sheets Fill Pattern

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from tools.gws_auth import build_service

sheets = build_service('sheets', 'v4')

# Read first to confirm structure
result = sheets.spreadsheets().values().get(
    spreadsheetId='<id>',
    range="'SheetName'!A1:Z10"
).execute()

# Update specific cell
sheets.spreadsheets().values().update(
    spreadsheetId='<id>',
    range="'SheetName'!C12",  # Land Area cell
    valueInputOption='USER_ENTERED',
    body={'values': [['12,74,520 sq ft (12.74 acres)']]}
).execute()
```

## Confirm-Before-Write Rule

When filling shared/project sheets, ALWAYS present extracted values and ask confirmation:
```
Land Area: 12.74 acres (~5,55,000 sq ft)
FSI: 2.0
Total BUA: [from sanction — still need to extract]
No. of Units: 138 plots
```

Wait for user to say "fill it" or "yes" before writing.

## Ranka Oasis Specific Data (June 2026)

Extracted from Master Plan PDF (vision):
- Total plots: 138
- Land area: ~186,352 sq ft (~4.28 acres) from drawing; Master Reference says ~12.74 acres total across 6 survey numbers
- Roads: 7M (internal), 10M (main)
- Amenities: 3 Parks, Clubhouse, Transformer Yard, Entrance Portal

Still needed from Drive (not yet extracted):
- DTCP Layout Plan → land area per survey number
- DTCP Layout Sanction → FSI, building configuration, approval numbers
- RERA registration → total saleable area, project start/completion dates
- Geotechnical report → soil data (not for spreadsheet but for engineering folder)

## Drive Search for Ranka Oasis Engineering Data

```python
# Find all files in Engineering folder
drive.list_folder('1wrwSgW8IYzNMP085knPUhFkkVzctqaiv')

# Find DTCP sanction docs
drive.files().list(q="name contains 'DTCP' and name contains 'Sevaganapalli'")

# Find layout plan
drive.files().list(q="name contains 'Layout Plan' and name contains 'Ranka Oasis'")

# Find RERA docs
drive.files().list(q="name contains 'RERA' and name contains 'Oasis'")
```