# Sub-Registrar Letter — Guidance Value Authentication

## Purpose
Draft letters to the Sub-Registrar requesting authentication of the current guidance value for a property, for Stamp Duty / Registration purposes.

## Property Description Format
Use a table for clarity:

| Particulars | Details |
|---|---|
| Plot No. | [current plot number + historical identifiers] |
| Khata No. | [current and past khata numbers] |
| BBMP PID | [current BBMP property ID] |
| Locality | [layout, village, hobli, city] |
| Dimensions (Site) | [E-W] m × [N-S] m |
| Approach Passage | [dimensions] on the [direction], giving access to the [road width] road on the [direction] |
| Total Approx. Area | [sq.ft] |

### Boundary Table Format
| Direction | Abutting Property |
|---|---|
| East | [neighbour details] |
| West | [neighbour details] |
| North | [neighbour details] |
| South | [neighbour details] |

## Company Details — Cross-Verification from ITR Documents

When populating the sender's company details for DRA Realty Pvt Ltd:

### ITR PDF Page Map (DRA Realty — 23-27 page scanned PDFs)

| Data | Page(s) | Source Section |
|---|---|---|
| **PAN** | Page 1 | ITR Acknowledgement header |
| **Company Name** | Page 1 | ITR Acknowledgement header |
| **Correspondence Address** | Page 1 | ITR Acknowledgement — "Address" field (used for income tax correspondence, may differ from registered office) |
| **Date of Incorporation** | Computation page (~page 2-3 of FY 2024-25) | Schedule header under "Previous Year" / "Date of Incorporation" |
| **Registered Office (Statutory)** | Balance Sheet header (page 14 in FY 2024-25, page 12 in FY 2022-23) | Appears before the Balance Sheet as company letterhead: `[Address], CIN, PAN` |
| **CIN** | Balance Sheet header | Same page as registered office |
| **Directors (Current)** | Balance Sheet header | Listed under "Directors" |
| **Director Name** | Page 1 / last page | Digital signature block: "digitally signed by [NAME]" |
| **Balance Sheet figures** | ~pages 14-15 | Equity & Liabilities / Assets (Rupees in Thousands) |
| **P&L figures** | ~pages 16-17 | Revenue, Expenses, Profit before Tax |
| **Notes / Schedules** | ~pages 17-22 | Breakup of reserves, borrowings, fixed assets |

### Extraction Workflow

1. **Locate ITR PDFs** in Google Drive — search: `"DRA Realty ITR Statement of Income P&L Balance Sheet"` (stored under `sales1.blr@draas.com`)
   - Naming pattern: `Copy of DRA Realty ITR Statement of Income P&L Balance Sheet Auditor Report FY 20XX 20XX.pdf`
   - Typically 2 versions per year (original + "Copy of Copy")
2. **Download** via Drive API: `service.files().get_media(fileId=...).execute()`
3. **Convert pages** from scanned PDFs:
   ```bash
   pdftoppm -f 1 -l 5 -r 300 -png input.pdf output_prefix     # pages 1-5 for company info
   pdftoppm -f 12 -l 22 -r 400 -png input.pdf output_hr        # high-res for financial data
   ```
4. **Run OCR** on relevant pages:
   ```bash
   tesseract <page.png> - -l eng
   ```
5. **Key fields to extract** — and cross-verify across 3 years' ITR PDFs (consistent address = reliable; variant reading = OCR error)

### ⚠️ Address Discrepancy Pattern (DRA Realty)

DRA Realty has **two different addresses** across its ITR documents. This is NOT an error — they serve different purposes:

| Source | Address | Purpose |
|---|---|---|
| **Balance Sheet** (all 3 FYs) | **201A/202BA, Queens Corner, No.3, Queens Road, Bangalore - 560 001** | Statutory Registered Office (MCA, RERA) |
| **ITR Acknowledgement** (all 3 FYs) | No.4A/B, Ranka Chambers, No.31, Cunningham Road, Bengaluru - 560 052 / No.44/B (OCR variant) | Income Tax correspondence address |

**Rule:** Use the **Balance Sheet address** for legal documents, letters to government authorities, and RERA filings. The ITR acknowledgement address is for income tax correspondence only.

CIN: **U70100KA2011PTC058105** (consistent across all 3 years' balance sheets)

## RERA Cash Flow Statement — Cross-Verification Against ITR Data

When cross-checking a RERA Cash Flow Statement against audited ITR financials:

### Steps
1. Extract P&L figures from ITR Balance Sheet + P&L (pages 14-17)
2. Compare each Cash Flow Statement line item against the ITR equivalent:
   - **Net Profit/(Loss) before Tax** → ITR P&L "Profit before tax" (note: CFS values in Rupees, ITR in Thousands → multiply × 1000)
   - **Depreciation** → ITR P&L "Depreciation and Amortization Expenses"
   - **Purchase of Fixed Assets** → Balance Sheet fixed asset increase year-over-year
   - **Proceeds from Share Capital/Loans** → Balance Sheet short-term borrowings change
3. Flag any [___] entries in the CFS as incomplete — the P&L can fill PBT and Depreciation, but full working capital changes require AS-3 Cash Flow classification

### Verification Table Format

| CFS Line Item | CFS Amount (₹) | ITR Source | ITR Amount (₹'000s) | Status |
|---|---|---|---|---|
| Net Profit before Tax | 10,69,77,000 | P&L FY 23-24 | 1,06,977 | ✅ Exact Match |
| Adjustments for Depreciation | 20,000 | P&L FY 23-24 | 20 | ✅ Exact Match |

### Known Cross-Verification Results (DRA Realty, verified Jun 2026)

| Year | FY 22-23 | FY 23-24 | FY 24-25 |
|---|---|---|---|
| PBT | ₹21,60,000 ✅ | ₹10,69,77,000 ✅ | ₹(2,15,60,000) ✅ (rounds to CFS 2,15,59,815) |
| Depreciation | Nil ✅ | ₹20,000 ✅ | ₹3,44,000 ✅ (CFS 3,44,092 — minor rounding) |
| Fixed Assets purchased | Nil ✅ | ₹3,57,000 ✅ | ₹24,49,000 (derived from BS) |

## Change-Highlighting Convention
When a draft is updated based on source-document verification, append a change-log table:

| # | What Changed | Source Document |
|---|---|---|
| 1 | [specific field added/updated] | [which ITR/PDF page] |
| 2 | ... | ... |

This gives the user an audit trail of what was verified vs. assumed.

## Common Pitfalls
- ITR PDFs are often **scanned/image-based** — pdftotext returns empty. Always use pdftoppm + tesseract.
- OCR may produce variant readings (e.g. `44/B` vs `4A/B`) — cross-check across multiple years' ITRs.
- **Two address sources:** ITR Acknowledgement vs Balance Sheet letterhead — use Balance Sheet address for official letters.
- Confirm whether the document on the shared Google Doc link is actually the correct document before proceeding; the link title may not match expectations.
- **Cash Flow Statement figures are in Rupees** (no thousands separator) while ITR P&L tables are in **Rupees in Thousands** — always ×1000 when comparing.
- **Directors change year-over-year** — Bhavik Ranka (FY 22-23) vs Kishan Murjani Nair (FY 24-25) — use the latest balance sheet for current director names.
