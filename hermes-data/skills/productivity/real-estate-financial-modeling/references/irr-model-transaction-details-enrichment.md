# IRR Model — Add Investor-Workbook Transaction Details & Assumptions

Trigger: user links a tab in the DRA "Project Costing & IRR Model" Google Sheet and says
"ADD ASSUMPTIONS FOR ALL THE PROJECTS AND PROJECT TRANSACTION DETAILS as per Investor...
spreadsheet". The investor workbook is `20260707_DRA_Group_Investor_Portfolio_All_Projects`.

## The investor workbook structure (what "transaction details" means here)

Each project tab of the investor workbook carries A–H "block" sections (NOT numbered 1,2,3 —
they use A./B./C./D./E./F./G./H. prefixes):

- **A. Project Identity** — Group Name, Project Executing Entity, Registered Office, Project Name, Location Address, Project Description
- **B. Land Details** — Land Area (sqft), Type (Freehold/Leasehold/Dev right), JD Share (LO:Dev), FSI, (sometimes TDR, plottal area)
- **C. Structure Specification** — Total Built-up (Construction Area), Total FAR / Saleable Area, No. of Buildings
- **D. Sharing Ratio (JV)** — Developer's Share vs Landowner's Share (saleable area + no. of flats)
- **E. Break up of Units** — construction start, expected completion, no. of floors, no. of units, avg area/unit, saleable area
- **F. Approvals Status** — Plan Sanction, RERA, Commencement, Electricity, Water/Sewage, Telecom, Height, HAL, Fire & Safety, Env, PCB (most listed as NA)
- **G. Profitability (PRE-financing)** — Total Sales Value, Total Dev Cost, Amount Invested by Developer (Refundable+Non-Refundable), Refundable on Completion, Profit, Profit % on Cost
- **H. Sales Details (Developer share)** — Sold block (units, area, agreement value, received, balance, achieved price) + Unsold block (units, area, est rate, sale value) + Total block

Note the tab names differ between the two workbooks (investor uses `RankaUdaya` no-space, `Ranka Oasis`, `Ranka Amber`, `Ranka NorthStar`; IRR model uses `Ranka Udaya`, `Ranka Amber`, `Ranka Oasis P1`, `Ranka NorthStar`). Map them explicitly.

## Workflow

1. **Dump EVERY investor-workbook project tab** via `values().get(FORMATTED_VALUE)` — these are the source of the A–H blocks. Keep the raw labels/values verbatim.
2. **Dump the current IRR model tabs** to find the last row of each (they ended at row 122 = Section E sensitivity grid). Blocks are appended at a fixed `START_ROW = 125` (leave rows 123–124 blank as a spacer).
3. Build a **per-project dict**: `{section_label: [(label, value), ...]}`. Convert each section into block rows: title row, source-note row, then per section a header row followed by label/value pairs.
4. Write to `'<Tab>'!A{start}:B{end}` with `USER_ENTERED`. Re-read to confirm.
5. **Style** in a separate batchUpdate pass: block title bold navy, each section header row = navy fill + white bold text, label column (A) bold. Fetch real sheetIds from `spreadsheets().get()` for the repeatCell ranges.
6. **Consolidated tab** (user asked "both"): create a new `Transaction Details` sheet, columns = the 4 projects, rows = attribute → value per project. Organize under the same A–H section headers, plus a bonus "F. FINANCED — after financing (IRR Model Sec D)" block (NP-after-financing, Eq IRR, Prj IRR, ROE, DSCR) so pre-financing (investor) and financed (model) sit side-by-side for comparison.

## Pitfalls

- **Pre-financing vs financed confusion**: the investor workbook's G-profitability is PRE-financing (Sales − Dev Cost), but the IRR model's Section D is AFTER financing. When you show both in a consolidated tab, tag them explicitly ("pre-financing (Investor Workbook)" vs "after financing (IRR Model, Sec D)") so the numbers don't look contradictory (e.g. Oasis dev cost ₹213.88 pre vs ₹223.31 model cost build-up → financed NP ₹74.57).
- **Oasis is the complex one**: it has Phase I/II columns, owned-land vs JDA-land tables, survey-number lists, and a consolidated-profitability block. For the transaction-details enrichment, trim to the Phase I (model scope) essentials + land-parcel summary; keep it readable rather than mirroring every survey number.
- **Values land as numbers not strings** (e.g. FSI "2.00" → "2", profit % "36.2%" → "36.20%"). That's fine — read back with FORMATTED_VALUE for display. Don't fight it.
- **Numeric cells lose leading-zero formatting** — acceptable; present values as-is.

## Verification trick — Docs-API paragraphs vs TABLES

When you "verify the DPR was updated" you must check BOTH:
- **Narrative paragraphs** — plain text (the DPR funding narrative still carried a stale "…are to be computed from the project financial model once finalised" sentence AFTER the 7.5 table was populated — the two contradict). Scan for `to be computed` / `are to be computed` across every `paragraph` element.
- **Actual table cells** — the 7.5 metrics live in tables, which are NOT captured by dumping only `paragraph` elements. You must walk the body recursively (`table` → `tableRows` → `tableCells` → `content` → `paragraph` → `textRun`) to find the real values. A text dump that shows only paragraphs will MISS the populated table and can falsely look like nothing changed.

Deleting a stale standalone paragraph: find its `elements[0].startIndex`..`elements[-1].endIndex` (end includes trailing newline) and `deleteContentRange` on `[start, end)`. Re-scan for the phrase after to confirm all docs are clean.

## Filling Docs-API table cells — send insertText in DESCENDING index order

When inserting a brand-new table via `insertTable` then filling its cells in a single `batchUpdate`, all cell indices are computed from the same doc snapshot but `insertText` requests apply sequentially against the evolving document — inserting into cell (0,0) first shifts every later cell's true position, so all values land crammed into the first cell of row 0 ("PaFYFYFY To₹ ₹ ₹ 0Bu..." garbage). **Sort the (cell_start_index, text) pairs DESCENDING by index** before building the request list; then each insert happens at a position that earlier (higher-index) inserts never disturb. Solid workflow: (1) `deleteContentRange` over any corrupted region, (2) insert intro paragraph, (3) re-read, insert table after it, (4) re-read, fill cells descending, repeat for each table, insert trailing notes. Always re-read (`documents().get`) between structural steps — never trust earlier snapshots after a mutation. Same pitfall applies to Sheets API `values().update`: batch cell writes with ascending row indices are fine there (ranges, not absolute offsets), but Docs API is offset-based and unforgiving.
