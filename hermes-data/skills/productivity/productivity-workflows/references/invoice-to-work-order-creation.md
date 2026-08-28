# Invoice → Work Order / PO Creation Pipeline

When a user uploads an invoice and asks to create a Purchase Order (PO) or Work Order against it.

## Step 1 — Extract Invoice Details

Use OCR (pdftoppm + tesseract for scanned PDFs, pdftotext for text PDFs) to extract:
- Vendor name, address, GSTIN, PAN
- Invoice number, date
- Description of services/goods, SAC code
- Amount breakdown: base value, GST (CGST/SGST/IGST), TDS, net payable
- Bank details (account, IFSC, beneficiary)

## Step 2 — Find PO/Work Order Template

Search the user's Drive for a PO format or existing work order as reference:
```python
drive.files().list(
    q="(name contains 'PO' or name contains 'Work Order') and trashed=false",
    fields="files(id, name)"
)
```

Prefer recent Work Orders from the same project (e.g., Ranka Amber Work Order for "DRA Amber Execution").

## Step 3 — Create DOCX Document

Use `python-docx` (install via `uv pip install python-docx`). Structure:
- **Header**: WORK ORDER title centered
- **Work Order details**: No, Date, GSTIN
- **To**: Vendor name, address, GSTIN, PAN
- **Subject**: Clear description referencing the project
- **Scope table**: Project name, location, invoice reference, scope of work, work value, GST, TDS, net payable
- **Payment Details table**: Bank name, account number, IFSC, beneficiary
- **Terms and Conditions**: 5-6 bullet points
- **SAC Code**
- **Signature block**: "For DRA REALTY PRIVATE LIMITED", Authorised Signatory, date, place

### Key python-docx patterns:
```python
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
# Bold run: r = p.add_run('text'); r.bold = True
# Colored header: r.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
# Table: doc.add_table(rows=N, cols=2); table.style = 'Table Grid'
# Bullet list: doc.add_paragraph(text, style='List Bullet')
```

**⚠️ Trailing-chaining pitfall:** `p.add_run('text').bold = True` sets bold and returns `True` (bool), breaking subsequent `.font` calls. Always split:
```python
r = p.add_run('text')
r.bold = True
```

## Step 4 — Upload to Drive

Upload the DOCX to Drive, ideally in a relevant project folder (e.g., "Amber Execution" for Amber project work orders):

```python
# Upload
media = MediaFileUpload(local_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
f = drive.files().create(body=file_meta, media_body=media, fields='id, name').execute()

# Move to specific folder
drive.files().update(
    fileId=f['id'],
    addParents=target_folder_id,
    removeParents=','.join(f.get('parents', []))
).execute()
```

## Reference — Designage Consultants Work Order (Jun 2026)

| Field | Value |
|---|---|
| Invoice No | B/1386/38/2026 dated 10-06-2026 |
| Vendor | Designage Consultants Pvt Ltd, Pune |
| Project | DRA Amber Execution |
| Scope | RCC Detailing — Structural Engineering Drawings (Final Bill) |
| Work Value | Rs. 2,50,000 |
| IGST 18% | Rs. 45,000 |
| TDS 10% | Rs. 25,000 |
| Net Payable | Rs. 2,70,000 |
| SAC Code | 998331 |
| Vendor GSTIN | 27AAJCD4531F1ZS |
| DRA Realty GSTIN | 29AAPCS9730H1ZO |
| Bank | IDFC FIRST BANK, A/C 79011076607, IFSC IDFB0041352 |
