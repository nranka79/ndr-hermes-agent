# ITR Data Extraction for Legal & RERA Documents

Extract company details and financial figures from scanned ITR PDFs for use in legal letters, Sub-registrar correspondence, and RERA filings (Cash Flow Statement, Director's Report).

## Workflow

### 1. Locate ITR Documents on Drive

Search with: `name contains 'DRA Realty' and name contains 'ITR'`

ITRs are typically stored under `sales1.blr@draas.com`. Look for PDFs named:
- `DRA Realty ITR Statement of Income P&L Balance Sheet Auditor Report FY 20XX-XX.pdf`

Prefer the **original** copy (not "Copy of Copy") — they are smaller and cleaner.

### 2. Extract Text via OCR

ITR PDFs are scanned/image-based. Use `pdftoppm` + `tesseract`:

```bash
# Convert first 5 pages to PNG at 300 DPI
pdftoppm -f 1 -l 5 -r 300 -png input.pdf output_prefix

# OCR each page
tesseract output_prefix-01.png - -l eng 2>/dev/null
```

Pages to target:
- **Page 1** → ITR Acknowledgement (PAN, company name, filing address, director, total income)
- **Page 2** → Auditor's Report (verifies statutory auditor)
- **Page ~13–14** → Balance Sheet header (registered office, CIN, PAN, directors, former name)
- **Page ~15** → Balance Sheet (equity, liabilities, assets)
- **Page ~16** → Profit & Loss statement (revenue, expenses, PBT, PAT, depreciation)
- **Page ~17+** → Notes to accounts (shareholding pattern, reserve details, borrowings)

Use 400 DPI (`-r 400`) for better accuracy on financial tables.

### 3. Extractable Information

| Field | Where to Find |
|---|---|
| **Legal Name** | ITR Acknowledgement page 1 |
| **Registered Office** | Balance Sheet header page (NOT ITR acknowledgement — that's filing address) |
| **CIN** | Balance Sheet header |
| **PAN** | ITR Acknowledgement + Balance Sheet header (cross-verify) |
| **Date of Incorporation** | ITR Schedule page / computation page |
| **Directors** | Balance Sheet header (current year's directors) |
| **Former Name** | Balance Sheet header (e.g. "Formerly Known as X") |
| **Share Capital** | Balance Sheet (Shareholders' Funds section) |
| **Revenue / Total Income** | Profit & Loss statement |
| **PBT / PAT** | Profit & Loss statement |
| **Depreciation** | Profit & Loss statement |
| **Current Tax** | Profit & Loss statement |
| **Fixed Assets** | Balance Sheet |
| **Borrowings** | Balance Sheet (Short-term / Long-term borrowings) |
| **Auditor** | Auditor's Report page |

### 4. ⚠️ Address Discrepancy — Critical

The **ITR Acknowledgement** (page 1) shows a **filing/correspondence address** which may differ from the **statutory registered office** on the **Balance Sheet header**.

- **ITR Acknowledgement address** → Correspondence/filing address (less authoritative)
- **Balance Sheet header address** → Statutory registered office (authoritative for legal docs)

Cross-check all 3 years' Balance Sheets — the registered office is consistent across audited statements.

### 5. Cross-Verify Figures

For each financial figure in the target document:

1. Extract from ITR P&L (in Rupees Thousands)
2. Multiply by 1000 to get Rupees
3. Compare against the figure in the target document
4. Minor rounding differences (₹100–₹500) are acceptable — these are due to P&L being in thousands

Example: ITR shows PBT = 1,06,977 (thousands) → ₹10,69,77,000 in the document ✓

### 6. Update Document with Change Highlighting

For .docx files (most RERA filings):

```bash
# Set up python-docx in a temp venv (system pip is blocked)
uv venv .docx_venv
source .docx_venv/bin/activate
uv pip install python-docx
```

Then use `python-docx` to:
- Locate the financial summary table by checking header row text
- Replace `[___]` placeholders with actual figures
- Set changed cells in **blue** font color (`RGBColor(0x1A, 0x6F, 0xD2)`)
- Add a **Change Summary** box at the top of the document
- Insert company details (CIN, PAN, Registered Office) if missing

### 7. Upload Back to Google Drive

```python
from googleapiclient.http import MediaFileUpload
service.files().update(fileId=original_file_id, media_body=media).execute()
```

This replaces the original file in-place (Drive keeps version history).

### Common Pitfalls

- **Scanned pages 6+ are often blank** for tesseract (they contain image-only tables around balance sheet/P&L). Use 400 DPI for these.
- **FY 2024-25 figures** are often incomplete in RERA drafts — the ITR for AY 2025-26 is the authoritative source.
- **Director changes across years** — Balance Sheet shows directors for that specific year. Use the most recent year's data.
- **Share capital format** — ITR shows in thousands (e.g. 500 = ₹5,00,000 for 5,000 shares of ₹100 each)
