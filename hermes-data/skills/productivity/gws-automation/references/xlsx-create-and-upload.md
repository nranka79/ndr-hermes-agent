# Create .xlsx → Upload to Drive (Structured Data from Document Extraction)

Full pattern: extract structured data from PDFs/docs → create formatted .xlsx with openpyxl → upload to Drive folder.

## Use cases
- Insurance policy details grouped by vehicle/property
- Document index / case file summary for a legal matter
- Employee records extracted from multiple sources
- Any "extract data from PDFs → structured spreadsheet" task
- **Document index from photo/image** — user sends a photo of a printed property document index; extract via vision_analyze, create categorized xlsx with Original/Photocopy and Handed Over columns

## Phase 1 — Extract data from source documents

For PDFs in Drive:

```python
from tools.gws_auth import build_service

service = build_service('drive', 'v3')

# Download
request = service.files().get_media(fileId=FILE_ID)
with open("/tmp/source.pdf", "wb") as f:
    f.write(request.execute())

# Extract text
import fitz
doc = fitz.open("/tmp/source.pdf")
text = ""
for page in doc:
    text += page.get_text()
doc.close()
```

**If the PDF is scanned (no extractable text):**
- Use tesseract (via ocrmypdf or pdftoppm + tesseract CLI) — see `ocr-and-documents` skill's `references/tesseract-ocr-workflow.md`
- Or render pages with `pdf2image` + vision API — see `ocr-and-documents` skill references

**If the PDF has text (pymupdf returns content):**
- Use fitz to extract; parse key fields with string search / regex
- Insurance policies typically have: Policy No, Insured Name, Vehicle Details, Period, Premium, IDV, NCB, Deductibles

## Phase 2 — Create .xlsx with openpyxl

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

wb = Workbook()
ws = wb.active
ws.title = "Data"

# Styles
header_font = Font(name='Calibri', bold=True, size=14, color='FFFFFF')
header_fill = PatternFill(start_color='2F5496', end_color='2F5496', fill_type='solid')
section_font = Font(name='Calibri', bold=True, size=12, color='2F5496')
section_fill = PatternFill(start_color='D6E4F0', end_color='D6E4F0', fill_type='solid')
label_font = Font(name='Calibri', bold=True, size=11)
value_font = Font(name='Calibri', size=11)
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

# Title row
ws.merge_cells('A1:B1')
ws['A1'] = 'Vehicle Insurance — BMW X1 (KA03ND7705)'
ws['A1'].font = header_font
ws['A1'].fill = header_fill
ws['A1'].alignment = Alignment(horizontal='center')
ws.row_dimensions[1].height = 30

# Data rows — section headers + label/value pairs
row = 3
for section_name, items in data_sections:
    # Section header
    ws.merge_cells(f'A{row}:B{row}')
    ws[f'A{row}'] = section_name
    ws[f'A{row}'].font = section_font
    ws[f'A{row}'].fill = section_fill
    row += 1

    for label, value in items:
        ws[f'A{row}'] = label
        ws[f'A{row}'].font = label_font
        ws[f'A{row}'].border = thin_border
        ws[f'B{row}'] = str(value)
        ws[f'B{row}'].font = value_font
        ws[f'B{row}'].border = thin_border
        row += 1

    row += 1  # Gap between sections

# Column widths
ws.column_dimensions['A'].width = 35
ws.column_dimensions['B'].width = 50

wb.save("/tmp/output.xlsx")
```

**⚠️ Ensure openpyxl is installed** — it's not part of the Hermes venv by default:

```bash
uv pip install openpyxl --python /opt/hermes/.venv/bin/python
```

**Data structure pattern** — organize extracted fields into labelled sections:

```python
data_sections = [
    ('Policy Information', [
        ('Insurance Company', 'TATA AIG General Insurance'),
        ('Policy Number', '6200834569'),
        ('Insured Name', 'KANTA RANKA'),
        ('Period', '27/11/2025 to 26/11/2026'),
        ('Premium (Incl GST)', '₹ 20,583'),
    ]),
    ('Vehicle Details', [
        ('Registration Number', 'KA 03 ND 7705'),
        ('Make/Model', 'BMW X1 SERIES'),
        ('Fuel Type', 'DIESEL'),
        ('Engine Number', '0185Y180'),
        ('Chassis Number', 'WBAHU1701J5L40276'),
    ]),
]
```

## Phase 3 — Upload to Drive folder

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

service = build_service('drive', 'v3')
folder_id = 'TARGET_FOLDER_ID'  # From Drive link or search

file_metadata = {
    'name': 'BMW_X1_Insurance_KA03ND7705.xlsx',
    'parents': [folder_id],
}

media = MediaFileUpload(
    "/tmp/output.xlsx",
    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    resumable=True
)

uploaded = service.files().create(
    body=file_metadata,
    media_body=media,
    fields='id, name, webViewLink'
).execute()

print(f"Uploaded: {uploaded['name']}")
print(f"Link: {uploaded['webViewLink']}")
```

**⚠️ MediaFileUpload, NOT raw file handle:**
```python
# ❌ WRONG — TypeError: media_filename must be str or MediaUpload
file = service.files().create(body=..., media_body=open(path, 'rb'))

# ✅ CORRECT
from googleapiclient.http import MediaFileUpload
media = MediaFileUpload(path, mimetype=mime, resumable=True)
file = service.files().create(body=..., media_body=media)
```

**⚠️ Upload sequentially, NOT in parallel** — parallel uploads (ThreadPoolExecutor) cause timeout errors for files >1MB. Upload one file at a time with individual `files().create()` calls.

**Naming convention for insurance data:**
`{VehicleModel}_Insurance_{RegNo}.xlsx` — e.g., `BMW_X1_Insurance_KA03ND7705.xlsx`

## Document Index from Photo/Image — FULL WORKFLOW

When the user sends a **photo or image of a printed document index** (e.g., a property document list) and asks to create an Excel sheet.

### 🚨 CRITICAL RULE: Never overwrite user co-edits

If the user will also edit the sheet directly in Google Sheets (filling in columns like Original/Photocopy, Handed Over, etc.):
1. **Convert to a native Google Sheet** on first upload (not an .xlsx file)
2. **Use Sheets API only** for all subsequent additions — never `files().update()`
3. `files().update()` **replaces the entire file** and destroys any cell edits the user made in the browser
4. **Leave user-managed columns blank** — fill only SI No., Particulars, Document No., Date

**Detection:** Check the file's MIME type before operating:
```python
drive.files().get(fileId=FILE_ID, fields='mimeType').execute()
# 'application/vnd.google-apps.spreadsheet' = native Google Sheet ✅
# 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' = .xlsx ⚠️
```

### Step 1 — Extract via vision_analyze

Extract the full tabular list: `vision_analyze(image_url=..., question="Extract full document list: serial number, particulars, document number, date for each row.")`

Each row typically has: SI No., Particulars, Document No. (optional), Date (optional).

### Step 2 — Add Extra Categorization Columns

Users typically want additional columns beyond what's in the original image:
- **Original / Photocopy** — whether the physical copy is original or a photocopy
- **Handed Over (Yes/No)** — whether the document has been handed over
- **Document No.** — extracted from the image if legible, blank otherwise
- **Remarks** — free-text notes for any additional context

**⚠️ Fill these with empty strings unless the user explicitly tells you to populate them.** Many users (especially Bharat) prefer to fill these manually. Your job is to extract from the photo and append — nothing more.

### Step 3 — Create Table-Format xlsx (with openpyxl)

Use a flat table with columns, not key-value pairs:

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

wb = Workbook()
ws = wb.active
ws.title = "PROJECT Documents"

header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
header_font = Font(bold=True, size=11, color="FFFFFF")
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

# Title row
ws.merge_cells('A1:G1')
ws['A1'] = 'INDEX OF DOCUMENTS — PROJECT NAME'
ws['A1'].font = Font(bold=True, size=14)
ws['A1'].alignment = Alignment(horizontal='center')

# Headers (row 3)
headers = ['SI No.', 'Particulars', 'Document No.', 'Date',
           'Original / Photocopy', 'Handed Over (Yes/No)', 'Remarks']
for col, h in enumerate(headers, 1):
    cell = ws.cell(row=3, column=col, value=h)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    cell.border = thin_border

# Data (from extracted list)
documents = [
    (1, "Example Document", "DOC-001", "23.07.2015"),
]
for row_idx, (si, desc, doc_no, date) in enumerate(documents, 4):
    for col, val in enumerate([si, desc, doc_no, date, "", "", ""], 1):
        cell = ws.cell(row=row_idx, column=col, value=val)
        cell.border = thin_border
        cell.alignment = Alignment(wrap_text=True, vertical='top')
        if col == 1:
            cell.alignment = Alignment(horizontal='center', vertical='top')

# Column widths: SI No, Particulars, Doc No, Date, Orig/Copy, Handed, Remarks
col_widths = [8, 55, 18, 15, 18, 18, 30]
for i in range(1, 8):
    ws.column_dimensions[chr(64 + i)].width = col_widths[i-1]

wb.save("/tmp/ProjectName_Document_Index.xlsx")
```

**Naming:** `{PropertyName}_Document_Index.xlsx` — e.g., `Dharwad_Property_Document_Index.xlsx`

### Step 4 — Upload to Drive & Deliver Link

For Bharat (and DRAAS users generally), **upload to Drive and share the link** rather than sending the raw file.

**Choose the right upload method:**

**Option A — Quick upload as xlsx** (use when the user will NOT edit the sheet directly):
```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3')

media = MediaFileUpload("/tmp/ProjectName_Document_Index.xlsx",
    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    resumable=True)
uploaded = drive.files().create(
    body={'name': 'Dharwad_Property_Document_Index.xlsx'},
    media_body=media,
    fields='id, name, webViewLink'
).execute()

drive.permissions().create(
    fileId=uploaded['id'],
    body={'type': 'anyone', 'role': 'reader'}
).execute()

print(f"Link: {uploaded['webViewLink']}")
```

**Option B — Upload as native Google Sheet** (use when the user WILL co-edit in browser — **preferred for document indexes**):
```python
media = MediaFileUpload("/tmp/ProjectName_Document_Index.xlsx",
    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    resumable=True)
uploaded = drive.files().create(
    body={
        'name': 'ProjectName_Document_Index',  # no .xlsx extension
        'mimeType': 'application/vnd.google-apps.spreadsheet'
    },
    media_body=media,
    fields='id, name, webViewLink'
).execute()

drive.permissions().create(
    fileId=uploaded['id'],
    body={'type': 'anyone', 'role': 'reader'}
).execute()
# Save sheet_id for future Sheets API calls
sheet_id = uploaded['id']
```

**🚨 Once uploaded as native sheet, never use files().update() on it.** Use Sheets API `spreadsheets().values().append()` instead (see Phase 3c).

### Step 5 — Cleanup

```python
import os; os.remove("/tmp/ProjectName_Document_Index.xlsx")
```

## ⚠️ CRITICAL: xlsx files vs native Google Sheets — know the difference

| Format | Drive MIME type | Editable in browser? | Sheets API? | files().update() safe? |
|--------|----------------|----------------------|-------------|----------------------|
| .xlsx file | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | Yes (Google converts on-the-fly) | ❌ No | ❌ **Overwrites user edits** |
| Native Google Sheet | `application/vnd.google-apps.spreadsheet` | Yes | ✅ Yes | N/A (use Sheets API) |

**🚨 CRITICAL PITFALL:** If you uploaded an .xlsx via `files().create()`, the user can open and edit it in Google Sheets browser interface. But if you then call `files().update()` to replace the file, ALL user edits in the browser are **permanently lost** — the entire file is replaced.

**Always convert to a native Google Sheet first if the user will also edit the sheet.** Use Sheets API (`spreadsheets().values().append()` / `.update()`) for all subsequent modifications.

## Phase 3b — Update existing xlsx in-place (add rows)

🚨 **USE ONLY if the user has NOT made any edits directly in Google Sheets.** If the user has edited the sheet, see Phase 3c instead.

Workflow: load xlsx → append rows → `files().update()` same file ID.

```python
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Side
from googleapiclient.http import MediaFileUpload
from tools.gws_auth import build_service

wb = load_workbook("/tmp/ProjectName_Document_Index.xlsx")
ws = wb.active
next_row = ws.max_row + 1

thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)
wrap_align = Alignment(wrap_text=True, vertical='top')
center_align = Alignment(horizontal='center', vertical='top')

new_docs = [
    (13, "Document Name 1", "DOC-013", "15.06.2013"),
    (14, "Document Name 2", "", "28.09.2020"),
]
for si, desc, doc_no, date in new_docs:
    vals = [si, desc, doc_no, date, "", "", ""]
    for col, val in enumerate(vals, 1):
        cell = ws.cell(row=next_row, column=col, value=val)
        cell.border = thin_border
        cell.alignment = wrap_align if col != 1 else center_align
    next_row += 1

wb.save("/tmp/ProjectName_Document_Index.xlsx")

drive = build_service('drive', 'v3')
media = MediaFileUpload(
    "/tmp/ProjectName_Document_Index.xlsx",
    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    resumable=True
)
updated = drive.files().update(
    fileId='PREVIOUSLY_UPLOADED_FILE_ID',
    media_body=media,
    fields='id, name, webViewLink'
).execute()
print(f"✅ Updated: {updated['name']}")
print(f"🔗 {updated['webViewLink']}")
```

**⚠️ Preserves permissions.** If already set to `anyone: reader`, the public link continues working.

## Phase 3c — Convert to native Google Sheet + append via Sheets API (co-editing safe)

Use this when the **user will make edits directly in Google Sheets** alongside your programmatic updates. This approach never replaces the whole file — it targets specific rows/columns.

### Step 1 — Import xlsx as a native Google Sheet

Upload with `mimeType='application/vnd.google-apps.spreadsheet'` instead of the xlsx MIME type:

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3')

# Export existing xlsx from Drive first (if already uploaded as xlsx)
request = drive.files().get_media(fileId='XLSX_FILE_ID')
with open('/tmp/export.xlsx', 'wb') as f:
    f.write(request.execute())

# Re-upload as native Google Sheet
media = MediaFileUpload(
    '/tmp/export.xlsx',
    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    resumable=True
)
new_file = drive.files().create(
    body={
        'name': 'Friendly Sheet Name (no .xlsx extension)',
        'mimeType': 'application/vnd.google-apps.spreadsheet'
    },
    media_body=media,
    fields='id, name, mimeType, webViewLink'
).execute()

sheet_id = new_file['id']
print(f"🔗 {new_file['webViewLink']}")

# Copy public sharing
drive.permissions().create(
    fileId=sheet_id,
    body={'type': 'anyone', 'role': 'reader'}
).execute()
```

### Step 2 — Append rows via Sheets API (never replaces data)

```python
from tools.gws_auth import build_service

sheets = build_service('sheets', 'v4')

new_rows = [
    [13, "Document Name 1", "DOC-013", "15.06.2013", "", "", ""],
    [14, "Document Name 2", "", "28.09.2020", "", "", ""],
]

sheets.spreadsheets().values().append(
    spreadsheetId=sheet_id,
    range='A:G',  # find the first empty row in columns A-G
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body={'values': new_rows}
).execute()
```

### Step 3 — Update specific cells (e.g., fill in Original/Copy column for a range)

```python
# Update Original/Photocopy column (E) for rows 4-15
sheets.spreadsheets().values().update(
    spreadsheetId=sheet_id,
    range='E4:E15',
    valueInputOption='USER_ENTERED',
    body={'values': [['Original'], ['Photocopy'], ['Original'], ...]}
).execute()
```

### Key differences from files().update()

| Action | files().update() (xlsx) | Sheets API (native sheet) |
|--------|------------------------|---------------------------|
| Append rows | Replaces entire file | Appends only, existing data untouched |
| User edits | WIPED on next update | Preserved |
| Sheet formatting | All formatting replaced | Existing formatting preserved |
| Multiple collaborators | Only one person's changes | True collaborative editing |

### Detection — is the file a native sheet or xlsx?

```python
file_meta = drive.files().get(fileId='FILE_ID', fields='mimeType').execute()
mime = file_meta['mimeType']
if 'spreadsheet' in mime:
    print("Native Google Sheet — use Sheets API")
elif 'openxml' in mime:
    print("xlsx file — use files().update() or convert to native sheet")
```

## Phase 4 — Verify

List folder contents to confirm all files landed:

```python
results = service.files().list(
    q=f"'{folder_id}' in parents and trashed=false",
    fields='files(id, name)'
).execute()
for f in results.get('files', []):
    print(f"  {f['name']}")
```
