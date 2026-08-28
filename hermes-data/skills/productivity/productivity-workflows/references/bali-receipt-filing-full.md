---
name: bali-receipt-filing
description: File a receipt photo or self-created PDF into the Bali May 2026 trip receipts folder in Google Drive. Triggered when user sends a photo or data with text "Bali receipt". No analysis, just filing.
trigger: "Bali receipt"
---

# Bali Receipt Filing

## Trigger
User sends a photo with the text **"Bali receipt"** (or any variant). Photo is filed as PDF in the receipts subfolder. No OCR, no extraction, no analysis — filing only.

Also handles: user describes a purchase verbally and asks to create a self-created PDF receipt.

**If user sends a photo labeled "Bali receipt" without trigger text:** file it immediately without analysis or vision. Create a generic PDF receipt using the details the user provided (location, amount, date). Do NOT attempt vision_analyze — it may fail on images and will block filing.

**Self-created PDF** always uses `new_x='LMARGIN', new_y='NEXT'` (not `ln=True`).

## Fixed Folder IDs

| Field | ID |
|-------|-----|
| Trip folder (Bali May 2026) | `1JvrSZpIeToZT6KBxz4pNDM3GS7-fevWU` |
| receipts subfolder | `1M2PuL6Yp-34Es-6TaQfNiUec4b-Vb0cD` |

**Do NOT search for or create these folders.** Use the IDs above directly.

## Photo Receipt → PDF → Drive

```python
import os, img2pdf, datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TELEGRAM_ID = "ndr"
SCOPES = ['https://www.googleapis.com/auth/drive']
RECEIPTS_FOLDER_ID = "1M2PuL6Yp-34Es-6TaQfNiUec4b-Vb0cD"
cache_dir = "/data/hermes/image_cache"

# Load OAuth
creds = Credentials.from_authorized_user_file(f"/data/hermes/users/{TELEGRAM_ID}/the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)", SCOPES)
if creds.expired:
    from google.auth.transport.requests import Request
    creds.refresh(Request())
drive = build("drive", "v3", credentials=creds)

# Find latest image (skip already-processed ones by checking mtime)
images = sorted(
    [f for f in os.listdir(cache_dir) if f.endswith(('.jpg','.jpeg','.png','.webp'))],
    key=lambda f: os.path.getmtime(os.path.join(cache_dir, f)), reverse=True
)
latest_image = os.path.join(cache_dir, images[0])

# Convert to PDF
pdf_path = latest_image.rsplit('.', 1)[0] + '.pdf'
with open(pdf_path, "wb") as f:
    f.write(img2pdf.convert(latest_image))

# Upload
filename = f"receipt_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
drive.files().create(
    body={"name": filename, "parents": [RECEIPTS_FOLDER_ID]},
    media_body=MediaFileUpload(pdf_path, mimetype="application/pdf"),
    fields="id"
).execute()
os.remove(pdf_path)
```

## Self-Created PDF Receipt (e.g., SIM card purchase)

Use `fpdf` (installed: `2.8.7`) to create a formatted receipt when no official receipt exists:

```python
from fpdf import FPDF
import warnings

pdf = FPDF(orientation='P', unit='mm', format='A5')
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_font('Helvetica', 'B', 16)
pdf.cell(0, 8, 'RECEIPT', new_x='LMARGIN', new_y='NEXT', align='C')
pdf.set_font('Helvetica', '', 10)
pdf.cell(0, 6, 'Bali, Indonesia - May 2026', new_x='LMARGIN', new_y='NEXT', align='C')
pdf.ln(4)

# Table header
pdf.set_fill_color(26, 60, 94)
pdf.set_text_color(255, 255, 255)
pdf.set_font('Helvetica', 'B', 9)
pdf.cell(60, 7, 'Item', border=1, fill=True)
pdf.cell(65, 7, 'Description', border=1, fill=True)
pdf.cell(15, 7, 'Qty', border=1, fill=True, align='C')
pdf.cell(40, 7, 'Amount (IDR)', border=1, fill=True, align='R')
pdf.ln()

# Rows
pdf.set_text_color(0, 0, 0)
pdf.set_font('Helvetica', '', 9)
for i, (item, desc, qty, amt) in enumerate([("SIM Card - 7-Day Package","21 GB, 10-com package","1","250,000")] * 4):
    fill = (i % 2 == 0)
    pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
    pdf.cell(60, 6, item, border=1, fill=fill)
    pdf.cell(65, 6, desc, border=1, fill=fill)
    pdf.cell(15, 6, qty, border=1, fill=fill, align='C')
    pdf.cell(40, 6, amt, border=1, fill=fill, align='R')
    pdf.ln()

pdf.set_fill_color(26, 60, 94)
pdf.set_text_color(255, 255, 255)
pdf.set_font('Helvetica', 'B', 9)
pdf.cell(125, 7, '', border=1, fill=True)
pdf.cell(15, 7, 'TOTAL', border=1, fill=True, align='C')
pdf.cell(40, 7, '1,000,000', border=1, fill=True, align='R')
pdf.ln(10)

pdf.set_text_color(0, 0, 0)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Recipients:', new_x='LMARGIN', new_y='NEXT')
pdf.set_font('Helvetica', '', 10)
for name in ['Ruhaan Ranka', 'Rivaan Ranka', 'Roshini Ranka']:
    pdf.cell(0, 6, '  - ' + name, new_x='LMARGIN', new_y='NEXT')
pdf.ln(3)
for line in ['Date: May 9, 2026','Location: Bali, Indonesia','Currency: Indonesian Rupiah (IDR)','Paid via: Cash','1,000,000 IDR = approx. Rs 5,400 INR']:
    pdf.cell(0, 6, line, new_x='LMARGIN', new_y='NEXT')

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    pdf_bytes = pdf.output()

with open("/tmp/sim_receipt.pdf", "wb") as f:
    f.write(pdf_bytes)

drive.files().create(
    body={"name": "receipt_20260509_SIM_cards_4x_IDR_250000.pdf", "parents": [RECEIPTS_FOLDER_ID]},
    media_body=MediaFileUpload("/tmp/sim_receipt.pdf", mimetype="application/pdf"),
    fields="id"
).execute()
os.remove("/tmp/sim_receipt.pdf")
```

## Voice-Described Receipt (No Photo)

When user describes a purchase verbally and asks to create a receipt (no photo provided):

**Trigger phrases (not exclusive):** "make a receipt", "file a receipt", "create and file", "you can file that", "file this"

**Format used (consistent across all receipts):**
- Header: "RECEIPT" (bold, centered) + "Bali, Indonesia - May 2026" below
- 4-column table: Item | Description | Qty | Amount (IDR)
- Total row (blue header row, right-aligned amount)
- Paid by: Nishant Ranka
- Date, Location, Currency, Paid via: Cash
- INR conversion line: `X IDR = approx. Rs Y INR (at 185 IDR/INR)`
- File as PDF to receipts folder

**Naming convention:**
`receipt_YYYYMMDD_ItemName_IDR_Amount.pdf`
- Underscores, no spaces, no special punctuation except hyphens between party names
- Amount without commas: `IDR_1000000` not `IDR_1,000,000`
- e.g. `receipt_20260510_ATV_photos_4bikes_IDR_1000000.pdf`
- For tips: include recipient name, e.g. `receipt_20260510_Jackie_raftguide_tip_IDR_100000.pdf`

**Multi-item receipts:** When user says "X amount per bike, 4 bikes" — compute total = per-unit × quantity automatically. List each unit as a separate line item (Bike 1, Bike 2...) for clarity, each with its per-unit amount.

**Receipt link format:** `https://drive.google.com/file/d/{file_id}/view` — get `file_id` from the upload result.

**Appending a row to the sheet (with balance formula):**
```python
# First append the data row (no balance value yet)
result = sheets.spreadsheets().values().append(
    spreadsheetId=spreadsheet_id,
    range="Sheet1!A:J",
    valueInputOption="USER_ENTERED",
    body={"values": [row_data]}
).execute()
updated_range = result['updates']['updatedRange']  # e.g. "Sheet1!A30:J30"
# Parse row number from range
import re
row_num = int(re.search(r'!A(\d+)', updated_range).group(1))
prev_row = row_num - 1

# Then set the balance formula for the new row
sheets.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    range=f"Sheet1!H{row_num}",
    valueInputOption="FORMULA",
    body={"values": [[f"=H{prev_row}-F{row_num}+G{row_num}"]]}
).execute()
```

**Backfilling receipt links:** If a receipt file exists in the Drive folder but its row in the sheet has no link, search for the file in the folder, get its `id`, construct the Drive link, and update `Sheet1!J{row}` via `values.batchUpdate`.

## After Filing a Receipt

1. Create and upload PDF to receipts folder
2. Append data row to spreadsheet (no balance value in the append call)
3. Set balance formula in `H{new_row}` using `values.update` with `valueInputOption="FORMULA"`
4. Update `bali-cash-tracking` skill with the new expense/credit amount
5. If a physical photo was uploaded, also note the receipt in the cash tracking skill

## Multi-item Receipts

When user says "X amount per bike, 4 bikes" — compute total = per-unit × quantity automatically. List each unit as a separate line item (Bike 1, Bike 2...) for clarity, each with its per-unit amount.

## Adding Rows to the Expenses Ledger Spreadsheet

After filing a receipt, ALSO add a row to the Expenses Ledger Google Sheet:

**Find spreadsheet by Drive search** (do NOT hardcode the ID — it changes):
```python
results = drive.files().list(
    q="'1JvrSZpIeToZT6KBxz4pNDM3GS7-fevWU' in parents and mimeType='application/vnd.google-apps.spreadsheet' and name contains 'Expenses Ledger'",
## Spreadsheet Format (Updated May 12, 2026)

**Spreadsheet:** `Bali May 2026 - Expenses Ledger` in Drive folder `1JvrSZpIeToZT6KBxz4pNDM3GS7-fevWU`
**Sheet:** `Sheet1`
**Find by search each time — do NOT hardcode spreadsheet ID** (it changes):
```python
results = drive.files().list(
    q="'1JvrSZpIeToZT6KBxz4pNDM3GS7-fevWU' in parents and mimeType='application/vnd.google-apps.spreadsheet' and name contains 'Expenses Ledger'",
    fields="files(id,name)"
).execute()
spreadsheet_id = results['files'][0]['id']
```

**Columns (A→J):** DATE | TIME | TYPE | DESCRIPTION | CATEGORY | DEBIT (IDR) | CREDIT (IDR) | BALANCE (IDR) | NOTES | RECEIPT

**Key rules:**
- **DEBIT = positive numbers only** (expenses, costs — no negative signs)
- **CREDIT = positive numbers only** (money in, currency exchange)
- **BALANCE formula:** `=H{prev_row}-F{new_row}+G{new_row}` — simply copy the formula from the previous row to the new row
- After appending the data row, use `values.batchUpdate` to set the balance formula for the new row
- Receipt column: full Google Drive link `https://drive.google.com/file/d/{file_id}/view`
- Get receipt file_id from the uploaded file result, then construct the link

**Note:** Vision tool (`vision_analyze`) may fail with model ID errors — do not rely on it for receipt processing. Create from voice description directly.

---

## Trigger

User sends a photo with the text **"Bali receipt"** (or any variant). Photo is filed as PDF in the receipts subfolder. No OCR, no extraction, no analysis — filing only.

Also handles: user describes a purchase verbally and asks to create a self-created PDF receipt.

**If user sends a photo labeled "Bali receipt" without trigger text:** file it immediately without analysis or vision. Create a generic PDF receipt using the details the user provided (location, amount, date). Do NOT attempt vision_analyze — it may fail on images and will block filing.

**Self-created PDF** always uses `new_x='LMARGIN', new_y='NEXT'` (not `ln=True`).

## Telegram KML File Handling

Telegram does not accept `.kml` uploads. Two workarounds:
1. User renames `.kml` → `.xml` before sending (KML is valid XML)
2. User pastes KML content as a text message

When receiving KML, fix coordinates (lon,lat → lat,lon) before sending back to Google Maps. See `references/kml-coordinate-fix.md`.

## Notes

- **No OCR, no analysis** — filing only
- **`fpdf` installed** (`2.8.7`) — use `new_x='LMARGIN', new_y='NEXT'` (not `ln=True`)
- **`img2pdf` installed** for photo-to-PDF conversion
- **Use `Credentials.from_authorized_user_file()`** — `from_authorized_user_json` does not exist in google-auth >= 2.x
- **Do NOT use `tools.gws_auth.build_service()`** — it uses the removed `from_authorized_user_json` and raises `AttributeError`
- **Receipts go to `receipts/` subfolder** — not Temp or Permanent. Temp/Permanent are for travel documents (visas, itineraries, etc.)