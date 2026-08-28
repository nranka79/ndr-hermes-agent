# Executing-Entity Financial Blocks in DPRs (Section 1.3)

Worked pattern for adding audited entity financials (ITR summary + Balance Sheet Position) to the 4 Ranka DPRs. Verified 2026-08-25 — all 4 DPRs updated with the DRA Realty Pvt Ltd BS-position block.

## DPR → executing entity / partner mapping

| DPR | Doc ID | Executing entity | DRA Realty role | Block added |
|-----|--------|------------------|-----------------|-------------|
| Amber | `1QMgsSPcbmoK_biVETwC9_snybOvNYAKxqLEK2mQUMdg` | DRA Realty Pvt Ltd | executing entity | BS position (1.3) |
| Oasis | `1LzqovfQml3oDDes2Y6frv7hLywN7mcIcF02zGFP-y_o` | Seveganapalli Land Partners (exec entity 1 = DRA Realty) | 95% partner of SLP | BS position after 1.3.1 DRA Realty ITR table |
| Udaya | `1f9p6LybHfEwh-8rOgDlyZfbT3iIyZGrignIih9IcGbU` | DRA Thindlu Land Partners | 51% partner | BS position after DRA Realty ITR table |
| NorthStar | `1pJeVQo3wOlcOdgiEflf07xGRORlYxllX5Fj7kiBrR4Q` | DRA Ranka Holdings | NOT a partner (Ranka family: Manish 71.25% / NDR 21.25% / Mamata 7.50%) | added anyway for consistency — flag to user |

## DRA Realty audited statements (source PDFs on Drive)

Folder "Financial Related Documents For Dra realty" (`179cOA58o3tua5kbpzklpQRXQWwbaYg0a`):
- `Copy of Copy of DRA Realty ITR Statement of Income P&L Balance Sheet Auditor Report For FY 2023 2024.pdf` — `1QlbsNOt9le09vwUTZWR6OB4z_cSJx-g4`
- `Copy of Copy of DRA Realty ITR ... FY 2022 2023.pdf` — `1Es89mH-d7PE94T3McuzZtHb_gODWgUtZ`
- `Copy of Copy of Dra Realty ITR ... FY 2024 2025.pdf` — `1_t-YTjoxNXGuPU69ac4TMq9vWjLQf6HU`

NO FY 2025-26 DRA Realty audited statement exists on Drive (searched 2026-08-25) — cap at FY24-25.

Other entities' financials (context): Seveganapalli ITR-5s and Thindlu ITR-5s in their firm folders; Ranka Holdings has NO ITRs anywhere (flag "ITRs pending", never invent).

## Balance-Sheet Position table (11 rows × 4 cols) — verified DRA Realty data, ₹ units

Columns: `Particulars | FY 2022-23 | FY 2023-24 | FY 2024-25` (mirror the ITR table's FY columns).

- Share Capital | ₹ 5,00,000 | ₹ 5,00,000 | ₹ 5,00,000
- Reserves & Surplus | (₹ 28,33,000) | ₹ 8,32,31,000 | ₹ 6,16,71,000
- Short-term Borrowings | ₹ 10,55,30,000 | ₹ 9,66,47,000 | ₹ 23,86,66,000
- Provisions & Other Liabilities | ₹ 2,00,000 | ₹ 45,91,000 | ₹ 39,23,000
- Total Liabilities | ₹ 10,33,98,000 | ₹ 18,49,69,000 | ₹ 30,47,61,000
- Fixed Assets | — | ₹ 3,57,000 | ₹ 28,06,000
- Non-current Investments | ₹ 10,02,94,000 | ₹ 13,27,60,000 | ₹ 23,32,24,000
- Cash & Bank | ₹ 3,74,000 | ₹ 1,98,52,000 | ₹ 2,19,91,000
- Advances & Other Current Assets | ₹ 27,29,000 | ₹ 3,20,00,000 | ₹ 4,67,39,000
- Total Assets | ₹ 10,33,98,000 | ₹ 18,49,69,000 | ₹ 30,47,61,000

Reconciliation: assets = liabilities each year (₹10.34 Cr / ₹18.50 Cr / ₹30.48 Cr). Borrowings are mostly director/group loans (FY25: directors ₹2,37,622K + others ₹1,045K); investments = group land vehicles (FY25: Seveganapalli ₹1,93,169K + Thindlu ₹40,055K); reserves moved (2,833)→83,231→61,671 via P&L. Auditor: Y.T. Gandhi & Associates (statements dated 11-Sep-2023 / 04-Sep-2024 / 08-Sep-2025).

Source note paragraph used (bold label above it): "Source: Audited financial statements (Y.T. Gandhi & Associates, Chartered Accountants) — FY 2022-23 (dated 11-Sep-2023), FY 2023-24 (dated 04-Sep-2024), FY 2024-25 (dated 08-Sep-2025). Figures in ₹. Group land-vehicle investments as at 31-Mar-2025: Seveganapalli Land Partners ₹19.32 Cr + DRA Thindlu Land Partners ₹4.01 Cr; other current assets include land advances (Hosur TAAL ₹1.19 Cr, Maragundanhalli ₹0.49 Cr, Poojan Agrahara ₹1.50 Cr)."

## Docs API insertion sequence (proven — do in this order)

1. `insertText` label at the start index of the "Audited documents:" paragraph — label text ends with `\n` so it becomes its own paragraph before that line.
2. RE-READ the doc, find "Audited documents" start (index shifted); `insertTable` (rows=11, columns=4) at that point.
3. RE-READ; `insertText` source note at the "Audited documents" start.
4. RE-READ; locate the table with `len(tableRows) == 11` (the doc has many other tables — filter by row count); build `insertText` requests at `cell['startIndex'] + 1` for all 44 cells, then SORT DESCENDING by index and send in one batch (the proven Docs API table-fill recipe — never ascending).
5. Bold header row + the "Balance Sheet Position" label via `updateTextStyle` (fields: 'bold').
6. Verify by re-reading and dumping the 11-row table; confirm each value and totals.

Finding the target table: earlier attempt accidentally picked the Executive Summary table when matching by preceding paragraph text — use row-count filter (`== 11`) instead of text-context matching; there is exactly one 11-row table after insertion.

## OCR extraction recipe (used for the raw numbers)

```python
# render grayscale 250 DPI, preprocess PIL, tesseract --psm 6, keyword-locate BS pages
from PIL import Image, ImageOps, ImageEnhance
# pdftoppm -r 250 -gray FY22_23.pdf pages/FY22_23_p
# autocontrast(cutoff=1) -> Contrast(1.6) -> Sharpness(1.5) -> save png
# tesseract enh.png ocr/base --psm 6
# keywords: 'BALANCE SHEET','EQUITY AND LIABILITIES','ASSETS','Reserves','Non-current'
```

Notes pages (e.g. FY24-25 p-18/19) give borrowings/investments composition — read them for the source note. Mind the "Rupees in Thousands" header — multiply by 1000.