# DRA Investor Portfolio Spreadsheet — Tab Schema (verified Aug 2026)

Spreadsheet: `20260707_DRA_Group_Investor_Portfolio_All_Projects` — id `1wDKS0SxtY0EF_-JUe2BfXzLSSwh4J5fo4y0sI_brFfw`
Tabs: `RankaUdaya`, `Ranka Amber`, `Ranka Oasis`, `Ranka NorthStar`, `Project Summary` (gid 1528630995).

All per-project tabs follow the same labeled row layout. Rows are 0-indexed in the values() array; add 1 for spreadsheet rows in formulas/ranges. Rows below are 0-based.

## Common layout (Amber / Udaya / NorthStar style)

| Rows | Block | Key fields |
|---|---|---|
| 2–8 | A. Entity & project | Group Name, Executing Entity, Registered Office, Project Name, Location Address, Project Description |
| 9–15 | B. Land Details | Land Area (sq.ft), Freehold/Leasehold, JD Share (LO:Dev), FSI / FAR, TDR |
| 16–19 | C. Structure Spec | Total Built-up, Total FAR/Saleable, No. of Buildings |
| 20–25 | D. Sharing Ratio (JV) | Developer's Share / Landowner's Share (area + units) |
| 26–37 | E. Unit breakup | Construction start date, expected completion, floors, unit count, avg area, total saleable |
| 38–52 | F. Approvals | Plan sanction, RERA, CC, Electricity, Water/Sewage, Telecom, Height, HAL, Fire, Environment, PCB — status text |
| 53–61 | G. Profitability | Total Sales Value, Total Development Cost, Amount Invested by Developer, Refundable amount, Profit, Profit % on cost |
| 62–end | H. Sales Details | Sold (units, area, agreement value, received, balance, achieved price) / Unsold (units, area, est. rate, sale value) / Total |

## Oasis tab differences (Ranka Oasis)

- Land block has multi-column PHASE I / PHASE II tables: DRA Owned Lands (area ac/sqft, residential area, FAR, BUA, no. of villas) vs **JDA Lands** (units + dev/landowner share).
- `DRA - CONSOLIDATED AREA SHARE - All Phases` table (Own Lands vs JDA Lands residential + BUA).
- Profitability is split a/b/c: owned-land profitability, JDA-land profitability, consolidated.
- Approvals block is later in the sheet (rows ~91+): Plan Sanction = DTCP Approved No 11996/2022/A4 dt 13/01/2026; RERA approval in process (note: checklist file shows RERA cert 07-Aug-2026 — trust the latest dated file).
- Survey schedule near the end: `Summary of Lands in the approved plan (Phase I)` — Sy.No, cents, owner, transaction type, legal opinion(s).

## Project Summary tab

Columns: Metric | Ranka Udaya | Ranka Amber | Ranka Oasis | Ranka NorthStar | TOTAL | UoM
Rows: Location, Project Type, Sharing Structure, Total Saleable Area, Total Units, Developer's Share, Gross Sales Value (Cr), Total Cost (Cr), Projected Profit (Cr), Profit Margin, Current Status + Project Description rows + company profile rows.
Use for the combined-portfolio numbers (575.21 Cr GAV, 370.83 Cr cost, 204.38 Cr profit).

## Known quirks

- Header labels inconsistent across tabs (Oasis uses different section letters, e.g. `E.` appears before `D.`); always read FORMATTED_VALUE and cross-check label text, not column positions.
- Some cells carry trailing spaces/newlines ("RANKA UDAYA \n").
- `Average Sales Price` UoM mislabeled "INR Cr" in some tabs — it's ₹/sq.ft.
- Amber total saleable appears as 30,700 (sheet) though topline docs say saleable 27,543 / FAR 2,559.82 sqm — use the sheet for DPR consistency, flag discrepancies.