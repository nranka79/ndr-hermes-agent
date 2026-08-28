# RERA Cash Flow Statement — Cross-Verification Against Audited ITR Data

## Purpose

When a RERA Cash Flow Statement (CFS) is prepared from audited financial statements, the figures must cross-verify against the company's Income Tax Return (ITR) documents. This reference captures the workflow for extracting ITR data from scanned PDFs and matching it against the CFS.

## When to Use

- User shares a RERA Cash Flow Statement docx/PDF and asks to "verify" or "cross-check" it
- A CFS has [___] or blank entries for the latest financial year that need to be filled
- You need the company's registered office, PAN, CIN, or director names for a RERA submission and the user has pointed to ITR documents

## Workflow

### Step 1: Locate and Download ITR PDFs

Search Google Drive for DRA Realty ITR documents:

```python
from tools.gws_auth import build_service
service = build_service('drive', 'v3')
results = service.files().list(
    q="name contains 'ITR' and fullText contains 'DRA Realty'",
    pageSize=20
).execute()
```

Typical naming: `Copy of DRA Realty ITR Statement of Income P&L Balance Sheet Auditor Report FY 20XX 20XX.pdf`
Stored under: `sales1.blr@draas.com`
Expected: 3-6 files (original + duplicates for FY 2022-23, 2023-24, 2024-25)

### Step 2: Extract from Scanned PDFs

ITR PDFs are scanned images — pdftotext returns empty. Use pdftoppm + tesseract:

```bash
# Company info pages (low-res is fine)
pdftoppm -f 1 -l 5 -r 300 -png input.pdf itr_ocr/pages

# Financial statement pages (higher res needed)
pdftoppm -f 12 -l 22 -r 400 -png input.pdf itr_ocr/financials

# OCR
tesseract itr_ocr/pages-01.png - -l eng
```

### Step 3: ITR PDF Page Map (DRA Realty — verified Jun 2026)

| Content | Page (FY 2024-25) | Page (FY 2022-23) |
|---|---|---|
| ITR Acknowledgement (PAN, Name, Address) | 1 | 1 |
| Computation / Schedule (D.O.I., PAN again) | ~2-3 | ~2-3 |
| Auditor's Report | 2-5 | 2-5 |
| CARO Annexure | 6-11 | 6-11 |
| **Company Header (Addr, CIN, PAN, Directors)** | **13-14** | **21** |
| **Balance Sheet** | **14-15** | **22** |
| **P&L Statement** | **16-17** | **23** |
| Notes & Schedules | 17-23 | 24-27 |

### Step 4: Extract Key Fields

#### From ITR Acknowledgement (Page 1):
- **PAN:** AAPCS9730H (DRA Realty — consistent across all years)
- **Legal Name:** DRA REALTY PRIVATE LIMITED
- **Correspondence Address:** No.4A/B, Ranka Chambers, No.31, Cunningham Road, Bengaluru

Note: The ITR acknowledgement address is for income tax correspondence. The statutory registered office is on the Balance Sheet letterhead.

#### From Balance Sheet Header (Pages 13-14):  
- **Registered Office:** 201A/202BA, Queens Corner, No.3, Queens Road, Bangalore - 560 001
- **CIN:** U70100KA2011PTC058105
- **Directors:** Nishant Ranka (DIN: 00298854), [Current Co-Director — changes across years]
- **Former Name:** SOUTHCITY RETAIL PLUS PVT LTD

#### From P&L (Pages 16-17):
- Revenue from operations
- Other Income
- Total Income
- Employee benefit expenses
- Other expenses
- Depreciation and Amortization
- **Profit/(Loss) before tax**
- Tax Expense
- **Profit/(Loss) for the period**

⚠️ **Unit conversion:** Balance Sheet and P&L in **Rupees in Thousands**. Multiply by 1000 to get Rupees.

### Step 5: Cross-Verify CFS Against ITR

For each CFS line item, find the corresponding ITR value:

| CFS Line | ITR Source | Formula |
|---|---|---|
| Net Profit/(Loss) before Tax | P&L: "Profit/(Loss) before tax" | ITR value × 1000 |
| Adjustments for Depreciation | P&L: "Depreciation and Amortization Expenses" | ITR value × 1000 |
| Operating Profit before WC Changes | PBT + Depreciation | Computed |
| Purchase of Fixed Assets | BS: fixed assets (current year - previous year) | Difference × 1000 |
| Proceeds from Share Capital / Loans | BS: Short-term borrowings (current - previous) | Difference × 1000 |

### Step 6: RERA CFS Completeness Check

A CFS must have figures for **all three financial years** in each line. If the latest year shows [___], check whether the ITR P&L and Balance Sheet are available to compute the values.

If only P&L and BS are available (not the full Cash Flow statement), the following can be filled:
1. **PBT** ✓ (directly from P&L)
2. **Depreciation** ✓ (directly from P&L)
3. **Operating Profit before WC Changes** = PBT + Depreciation
4. **Fixed Assets purchased** = BS fixed assets YoY change
5. **Borrowing proceeds** = BS short-term borrowings YoY change

Working Capital Changes and Net Cash from Operations require full AS-3 classification which needs more detail than P&L alone provides.

## Verified Results (DRA Realty, Jun 2026)

| Line Item | FY 2022-23 | FY 2023-24 | FY 2024-25 |
|---|---|---|---|
| PBT (CFS) | ₹21,60,000 ✅ | ₹10,69,77,000 ✅ | ₹(2,15,59,815) ✅ |
| PBT (ITR × 1000) | ₹21,60,000 | ₹10,69,77,000 | ₹(2,15,60,000) |
| Depreciation (CFS) | Nil ✅ | ₹20,000 ✅ | ₹3,44,092 ✅ |
| Depreciation (ITR × 1000) | Nil | ₹20,000 | ₹3,44,000 |
| Fixed Assets purchased | Nil ✅ | ₹3,57,000 ✅ | ₹24,49,000 ⚠️ (from BS) |
| Borrowing change | ₹78,000 | ₹(88,83,000) ✅ | ₹14,20,19,000 ⚠️ (from BS) |

## Known Pitfalls

1. **Directors change year-over-year:** FY 2022-23 lists Bhavik Ranka; FY 2024-25 lists Kishan Murjani Nair. Always use the **latest** balance sheet for current directors.
2. **Two addresses:** ITR acknowledgement (correspondence) vs Balance Sheet header (registered office). Use the Balance Sheet address for RERA/legal filings.
3. **OCR variance:** `44/B` vs `4A/B` appeared across different years' OCR — cross-check against the Balance Sheet letterhead which is more consistent.
4. **Rounding:** ITR values in ₹'000s — expect ±0.1% differences when comparing to CFS values in ₹.
5. **Scanned PDFs only:** pdftotext returns form feeds only. Must use pdftoppm + tesseract.
6. **Copy vs Original:** Drive may have "Copy of" and "Copy of Copy of" versions — prefer the shorter name (single "Copy of") for the original.
