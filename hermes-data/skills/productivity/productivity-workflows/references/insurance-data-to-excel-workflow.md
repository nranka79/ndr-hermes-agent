# Insurance Data → Consolidated Excel Workflow

Extract insurance policy data from PDFs in a Google Drive folder → create a single consolidated Excel summary → upload back.

**Trigger**: User shares a Drive folder link containing insurance PDFs and asks to "make a sheet" or "extract important data."

## Step 1: List Drive Folder Contents

```python
from tools.gws_auth import build_service
service = build_service("drive", "v3")

results = service.files().list(
    q=f"'{FOLDER_ID}' in parents and trashed=false",
    fields="files(id, name, mimeType, size, modifiedTime)",
    pageSize=100
).execute()
```

Identify which PDFs belong to each vehicle by filename (reg numbers, make/model names).

## Step 2: Download Each PDF

```python
request = service.files().get_media(fileId=FILE_ID)
with open("/tmp/local_copy.pdf", "wb") as f:
    f.write(request.execute())
```

## Step 3: Extract Text

**For text-based PDFs** (BMW X1, Jaguar NICL — ~80% of insurer PDFs):
```python
import fitz
doc = fitz.open("/tmp/local_copy.pdf")
for page in doc:
    text = page.get_text()
    if text.strip():
        print(text)
```

**For scanned/image PDFs** (some Vento, Innova — poor text layer):
```bash
tesseract /tmp/page_image.png /tmp/output --psm 6 -l eng
cat /tmp/output.txt
```

**⚠️ OCR quality varies.** Tesseract on scanned insurance documents can be unreliable — especially for small print, tables, and Hindi/English mixed text. If OCR produces garbage, fall back to:
- `ocrmypdf --force-ocr` for full-document OCR
- Or extract data from file naming patterns (reg no in filename, insurer in document title)

## Step 4: Compile Data per Vehicle

Key fields to capture per vehicle (from Indian motor insurance policies):

| Field | Source | Notes |
|-------|--------|-------|
| Vehicle name | Filename + document text | Cross-reference both |
| Reg No | Certificate of Insurance / Vehicle Details section | Often in filename too |
| Insurer | Document header / footer | TATA AIG, National Insurance, Bajaj Allianz, etc. |
| Policy No | Policy Schedule page | Usually a 10-16 digit number |
| Insured Name | Insured Details section | Usually the registered owner |
| Period From/To | Period of Insurance section | Format DD/MM/YYYY |
| Premium | Premium summary / Receipt | Check for "incl GST" |
| IDV | Vehicle Details or IDV section | Insured Declared Value |
| NCB % | Schedule of Premium - Discounts | No Claim Bonus percentage |
| Fuel / CC | Vehicle Details | Petrol/Diesel + engine CC |
| Mfg Year | Vehicle Details | Manufacturing year |
| Engine / Chassis | Certificate of Insurance | Critical for claims |
| Add-on covers | Schedule of Premium section | Key replacement, RSA, etc. |
| TP limits | Limits of Liability section | Usually ₹7,50,000 for property |
| PA cover | Limits of Liability | Usually ₹15,00,000 |
| Nominee | Nomination Details | Name + relationship |

## Step 5: Create One Consolidated Excel File

**⚠️ CRITICAL USER PREFERENCE: ONE FILE, NOT MULTIPLE.** Users consistently prefer a single master spreadsheet with all vehicles in one place — NOT separate files per vehicle. Always consolidate.

### Structure

**Sheet 1: Summary** — All vehicles side-by-side in a table with key columns:
- Vehicle, Reg No, Insurer, Policy No, Period, Premium, IDV, NCB, Fuel, Year, Model

**Sheet 2: Detailed View** — One block per vehicle with labeled sections:
- Policy Info, Vehicle Details, Coverage & IDV, Premium Breakup, Add-on Covers

### openpyxl formatting

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

wb = Workbook()
ws = wb.active

# Styles
hdr_fill = PatternFill(start_color='2F5496', end_color='2F5496', fill_type='solid')
sec_fill = PatternFill(start_color='D6E4F0', end_color='D6E4F0', fill_type='solid')
tb = Border(left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin'))
alt_fill = PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type='solid')
```

### Vehicle block writing pattern

```python
def write_block(ws, start, title, sections):
    # Title row
    ws.merge_cells(f'A{start}:D{start}')
    cell = ws.cell(row=start, column=1, value=title)
    cell.font = Font(name='Calibri', bold=True, size=12, color='FFFFFF')
    cell.fill = PatternFill(start_color='2F5496', end_color='2F5496', fill_type='solid')
    
    r = start + 1
    for sec_name, items in sections:
        # Section header
        ws.merge_cells(f'A{r}:D{r}')
        ws.cell(row=r, column=1, value=sec_name).font = Font(bold=True, size=10)
        ws.cell(row=r, column=1).fill = sec_fill
        r += 1
        # Key-value rows
        for label, value in items:
            ws.cell(row=r, column=1, value=label).font = Font(bold=True)
            ws.merge_cells(f'B{r}:D{r}')
            ws.cell(row=r, column=2, value=str(value))
            r += 1
        r += 1  # spacing
    return r + 1
```

## Step 6: Upload Back

Delete any existing version first to avoid duplicates:

```python
from googleapiclient.http import MediaFileUpload

# Delete old
old = service.files().list(
    q=f"'{FOLDER_ID}' in parents and name='DRAAS_Vehicle_Insurance_Master.xlsx'",
    fields="files(id)"
).execute()
for f in old.get('files', []):
    service.files().delete(fileId=f['id']).execute()

# Upload new
media = MediaFileUpload("/tmp/master.xlsx",
    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
file = service.files().create(
    body={"name": "DRAAS_Vehicle_Insurance_Master.xlsx", "parents": [FOLDER_ID]},
    media_body=media,
    fields="id, name, webViewLink"
).execute()
```

## Pitfalls

1. **User wants ONE sheet, not per-vehicle files.** This was explicitly corrected in Jun 2026. Always consolidate into a single Excel unless told otherwise.

2. **Scanned PDFs (Vento, Innova) may have poor OCR.** Tesseract on scanned insurance PDFs produces unreliable text — especially for small print premium tables and Hindi/English mixed documents. The vehicle reg no in the filename is usually the most reliable identifier. Note limitations clearly in the sheet.

3. **Updated policies may appear mid-workflow.** Check the folder for recently-added files (modifiedTime close to now) that supersede older ones. The user may upload an updated policy while you're working.

4. **Vento vs Innova naming.** Toyota Innova PDFs may be named just "Innova" — map to "Toyota" per user reference. "Java/Jagur" in voice messages = "Jaguar."

5. **IMT/TA Endorsement codes.** Indian motor policies list applicable endorsements as codes (IMT 28, IMT 22, TA 08, TA 19, etc.). Include these in the detailed view when found — they define policy scope.

6. **File naming for the Excel.** Use a descriptive name like `DRAAS_Vehicle_Insurance_Master.xlsx` — generic enough that it stays valid when policies are renewed.

7. **Policy period detection.** Indian policies often have separate start/end dates for OD (Own Damage) and TP (Third Party) coverages. They may differ by a few days — capture the TP dates as primary.

## Session Worked Example (June 2026)

- Folder ID: `16R5MtZRoQrLM64Hpxejuij_wV08hfQ4E`
- 4 vehicles: BMW X1 (KA03ND7705, TATA AIG), VW Vento (KA05MT9001, TATA AIG), Toyota Innova (KA04NE1550, Bajaj Allianz), Jaguar XJ L (KA04MR1001, National Insurance)
- Vento had two PDFs — old National Insurance policy + updated TATA AIG policy (added same day)
- Output: `DRAAS_Vehicle_Insurance_Master.xlsx` with Summary + Detailed View sheets
