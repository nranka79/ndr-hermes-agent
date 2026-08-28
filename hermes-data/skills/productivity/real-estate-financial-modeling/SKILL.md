---
name: real-estate-financial-modeling
description: >-
  Build and update DRA real-estate project financial models in Excel
  (openpyxl): project-finance / debt-equity sections, monthly financing
  schedules, equity IRR, sensitivity grids, P&L comparison blocks. Covers DM
  (development management) models, JDA models and plotted-layout models for
  DRA / DRAAS projects.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [financial-model, openpyxl, excel, project-finance, real-estate, draas, equity-irr, sensitivity]
    category: productivity
    related_skills: [professional-documents, draas-landowner-records, real-estate-company-valuation-ipo, draas-landowner-proposals]
---

# Real Estate Financial Modeling (Excel / openpyxl)

Trigger: the user (Prakash Singh / DRAAS research) asks to "update this model", "add a project finance section", "what's the profitability with debt", build a JDA/DM financial model, or wants equity/financing costs editable in an xlsx. Also triggers on "arrive at the actual land cost / landowner realisation after X% profit" — land-cost back-solve models, usually delivered as editable Google Sheets (see references/sheets-api-land-cost-model.md).

## Workflow

### 1. Inspect the existing workbook first — never guess

Load with `openpyxl.load_workbook(path, data_only=False)` and dump EVERY sheet: cell values AND formulas (formulas, not just cached values). Note the workbook's own styling conventions and match them — DRA workbooks use:
- Editable input: Arial 10, **blue font 0000FF + yellow fill FFFFCC**
- Calculated formula: black text, no fill
- Cross-sheet link: **green 008000**
- Sheet title: Arial 16 bold white on navy **1F3864**
- Section header: Arial 12 bold white on gold **C99A2E**
- Notes: Arial 8 gray 666666
- ₹ amount format: `#,##0;\(#,##0\);\-` ; ₹ Cr: `#,##0.0` ; %: `0.0%`
- Convention: percentages stored as DECIMALS (0.52) with the unit ("%") in the unit column — NOT percent-formatted cells (sensitivity grids are the exception)

### 2. Replicate the math in Python BEFORE building

There is no LibreOffice recalc available for validation. Rebuild the model's logic in a Python script (phased revenue, cost build-up, P&L), then the financed scenario, and print expected values. These are the numbers you report to the user — never report numbers you haven't actually computed.

### 3. The project-finance section layout (proven, 6 sections)

Insert a new sheet after Cost Summary. Sections:
1. **Financing structure (INPUTS, yellow editable)**: Total dev cost (link), Debt %, Equity %, check row (B7+B8), Loan Amount, Equity Contribution, Cash equity (non-land) = B8 × (total cost − land), Interest rate, Loan tenure, Moratorium (default = construction period), Processing fee %, Other fees, Project start date.
2. **Monthly schedule (48 rows)**: Month | Revenue | Dev Cost | Debt Drawdown | Equity Drawdown | Interest | Principal | Net Cash | Cumulative Cash | Debt Outstanding | Cumulative Equity | Cash Balance | Date (XIRR) | Equity CF (PF) | Equity CF (All-Equity).
3. **Financing cost summary**: IDC (interest m1–24), post-construction interest, total interest, fee, TOTAL FINANCING COST (+ ₹ Cr + ₹/saleable sqft columns).
4. **Profitability**: revenue − dev cost − financing cost = NET PROFIT AFTER FINANCING; margin; ₹/acre; ₹/sqft; ROE; Equity IRR (XIRR); Project ROC; Peak Debt; Project-life DSCR; all-equity comparison + financing drag.
5. **Comparison table**: 100% Equity vs Project Finance (NP, margin, equity, ROE, IRR, financing cost, peak debt).
6. **Sensitivity grid**: ROE by Debt% (rows) × interest rate (cols).

Also add a "P&L — with project finance" block to the existing P&L Summary sheet (reference the new sheet, don't overwrite the all-equity base case) and pointer notes on Assumptions / Land Value sheets.

### 4. Key modeling decisions (the non-obvious ones)

- **Brief-vs-model reconciliation is step ZERO for JD/term-sheet work.** When NDR briefs deal terms (voice) and an existing IRR sheet covers the same deal, build a mismatch table BEFORE any drafting: brief term → model cell/value → match/mismatch → action. Proven mismatches on Ranka Oasis × Jiraaf (24-Aug-2026): investor share 37% vs briefed 38%; "less 2 acres goodwill" vs model flat ₹2.0 Cr (~₹11.4 Cr vs ₹2.0 Cr — changes net consideration by ~₹10 Cr); Q1–Q2 zero-sales requested but a developer-only scenario sheet still books early sales; 81.5/18.5 sales ratio modeled as 80/20; price floor ₹8,000 from Q3 breached (model caps at ₹8,500, opens at ₹4,500–7,000); NPV negative for the investor-JD scenario while developer-only is positive. Never silently pick one number — flag each as a numbered confirm-question to NDR (see `draas-landowner-proposals` → `references/ranka-oasis-jiraaf-term-sheet.md` for the worked table and full intake).

- **Loan sizing must be self-consistent**: draw debt as `debt% × monthly dev cost` over the FULL tenure (not just construction), so total drawn == Loan Amount exactly. Revenue-linked costs (marketing/RERA/DM fee = 24% of revenue in the DM model) occur months 25–42 and are self-funded by revenue, but drawing on them keeps the balance sheet consistent.
- **Interest**: monthly rate on opening balance (`=J{r-1}*$B$13/12`); principal repayment `=MIN(loan/(tenure-moratorium), balance)` after moratorium.
- **XIRR convention**: sponsor equity drawn with costs (negative), recovered with net profit at project end (positive). ROE = NP/Equity (project-life, not annualized).
- **Project-life DSCR** = (Revenue − Sponsor Equity) / (Total Interest + Total Principal). Naive (Rev − Dev)/debt-service gives ~0.45× and looks broken — the correct numerator excludes the equity-funded portion of cost.
- **Sensitivity grid exactness trick**: with fixed cost phasing, total interest scales EXACTLY linearly with debt% × rate. So grid cell = `interest = $A{row} × B$112 × $B$76/($B$7*$B$13)` (B76 = base total interest, B7 = base debt%, B13 = base rate) and the grid matches the monthly schedule exactly — no "approximate" caveat needed.
- **Equity IRR all-equity comparison**: equity draws = dev cost m1–24, terminal = total dev cost + NP at m42.
- **Land is a cost in these models** (P&L treats land at cost) — the sponsor equity therefore includes the land contribution. Add a "cash equity (non-land)" line so the landowner sees the actual cash they must inject.
- **DRA capital policy (24-Aug-2026, applies to DPR 6.2/7.2/7.4 tables too)**: where project land is OWNED by the developer → land value counts as developer equity; add 25% of total development cost as capital equity; the balance = 75% debt from investors/institutions. JDA projects (land NOT owned) have no land equity — just 25% capital equity / 75% debt. Worked per-project numbers, user-confirmed parameters (11%/72-mo debt, velocity 30+10+10+10+15+15, Amber goodwill/IFRSD paid = equity + NDR ~₹2 Cr, Udaya ₹4,000/sqft) and the **Oasis Phase 1 = 7.53 ac** scoping correction are in `real-estate-dpr` (dpr-generation) → `references/docs-api-financial-tables.md`.

### 5. Build, verify, deliver

- Write the build script with `write_file` — NOT a shell heredoc. Formulas contain `&` which trips Hermes' backgrounding guard (`'&' backgrounding` error) and `;`/quotes break other shells.
- After building, read back the workbook (formulas + fills) and confirm structure; confirm expected numbers via your Python replication (Section 2) and report them.
- Deliver the updated xlsx alongside a summary with **both scenarios** (all-equity vs financed) and any sensitivity range.

### 6. Google Sheets API variant — editable live model (land-cost back-solve)

When the user says "make an editable model to tweak" (Prakash's recurring ask), deliver a **Google Sheet** built via the Sheets API, not an xlsx. Create a NEW spreadsheet (keep the user's original intact), write values with `valueInputOption="USER_ENTERED"` so formulas evaluate live, then share with the requesting user as writer. Full worked recipe + row layout + pitfalls: `references/sheets-api-land-cost-model.md`.

Non-negotiable build rules (all three bit on the Palya 2A6G build):
- **Track rows dynamically** — build the rows list with a `KEY[label] = len(rows)` dict and generate every formula from KEY references. Hardcoding row numbers produces `#REF!` everywhere the moment a blank spacer row shifts the layout (first build had 15+ #REF! cells).
- **Order matters in Sheets API styling: number formats LAST.** A later `updateCells` with `fields='userEnteredFormat'` and only bold/fill on a range that INCLUDES column B silently wipes the `numberFormat` (and any other userEnteredFormat keys) on those cells. Apply bold/fill passes first, then re-apply number formats in a final pass, or scope bold passes to the label column (A) only.
- **Summary cross-sheet refs to sheets with spaces need quoted names** — `='Ranka Udaya'!B107`, not `=Ranka Udaya!B107` (the latter is `#ERROR!`).
- **Default XIRR sign trap**: an all-equity project CF built as `revenue − cost` can be positive in every month (no sign change → XIRR returns #NUM! / None). Use the invested-capital convention instead: negative cost draws each month, terminal = total cost + unlevered NP at the last revenue month.
- **User-confirmed capital split may override the 25/75 rule per project** — e.g. Amber's 4.00 equity / 6.70 debt (goodwill/IFRSD already paid = equity, not 25% of dev cost). Store `debtp = loan/dev` per project rather than assuming 0.75.
- **Get the real sheetId** from `spreadsheets().get()` metadata before any `repeatCell`/`batchUpdate` formatting — `sheetId: 0` fails with "No grid with id: 0".
- **Never start a label cell with "+"** — Sheets parses a leading `+` as a formula → `#ERROR!`. Write "Non-Refundable Goodwill (add)" instead.
- **Cross-sheet FORMULA cells do NOT inherit the source's number format — apply formats to the destination.** A summary tab linking to per-project tabs (e.g. `='Ranka Udaya'!B110` for Equity IRR, source = 0.5184 percent-formatted) displays the raw decimal by default: `1` (rounded to int), `Dec-1899`/`Jan-1900` (interpreted as a date serial), or `950.00%` — unless you explicitly `repeatCell` the number format (`0.0%`, `#,##0.00`, `0.00`, `mmm-yy`) onto the destination formula cells. Do this as a separate repeatCell pass over the summary value columns (B:E) keyed by each attribute's intended unit. Diagnose wrong-looking values by reading `valueRenderOption='FORMULA'` (confirms what was written) vs `FORMATTED_VALUE` (confirms what's shown); a `#ERROR!` usually means unquoted sheet name, a weird number/date usually means missing destination format.
- **Date cells are stored inconsistently across tabs (text "10.07.2025" on some, raw date-serial ints on others).** A single date format applied to a summary formula cell therefore renders inconsistently (Udaya text stays "10.07.2025", Oasis/NorthStar serials show via the format you pick). Also, source serials can encode the wrong year (46203 = 30-Jun-2026, not 2030) while the tab displays it as "Jun-30" via custom format — so cross-sheet date links can surface a source-data inconsistency. Flag it rather than silently forcing a format; simplest robust display is static text matching the source label when the source is unreliable.
- **Verify by read-back**: `values().get(valueRenderOption='FORMATTED_VALUE')` returns computed numbers — cross-check them against the Python replication (Section 2) before reporting; also read back with `FORMULA` to confirm formulas landed as intended.
- **REORDER formula-heavy blocks with `moveDimension` (ROWS), NOT manual formula rewrite.** When the user asks to reorder blocks inside a working model (e.g. move the investor transaction-details block from below the IRR model up to the top, matching the Project Summary), never try to regenerate every `$B$18`/`A25`/`SUM(G25:G96)`/`XIRR(L25:L96)` reference with shifted row numbers — that's error-prone (#REF!/#VALUE! everywhere). Instead use the Sheets API `moveDimension` request once per block: `{"moveDimension":{"source":{"sheetId":<gid>,"dimension":"ROWS","startIndex":<rowIdx>,"endIndex":<rowIdx>},"destinationIndex":0}}` (0-based, endIndex exclusive). Sheets then auto-adjusts BOTH the internal formulas of the moved/shifted rows AND any external cross-sheet references (e.g. from Project Summary) to the new locations. Verify by read-back (FORMATTED_VALUE) that Section C/D/E outputs (Total Interest, NP, ROE, Eq/Prj IRR, DSCR, sensitivity) are unchanged and no `#REF!`/`#VALUE!` appeared — the only tolerated error is the inherent `#DIV/0!` on the 100%-debt sensitivity row, which exists before any move.

Back-solve structure (proven, Palya 2A6G): A. Inputs (yellow, editable incl. TARGET PROFIT %) → B. Derived (SBUA, dev/LO split) → C. Dev revenue (sales − GST + LO recoveries) → Costs (JD + construction + marketing + land) → D. Back-solve: Max Allowable Land Cost = Revenue/(1+target) − fixed costs, per acre, psft → E. LO realisation (land + goodwill + deposits) → F. Scenario table 25/30/35% → G. Sensitivity land cost 0–25 Cr vs profit %. LO share input = 0 for cash land-cost model; set 0.40 to switch to 60:40 JDA (LO recoveries auto-kick in).

### Adding investor-workbook transaction details & assumptions to the IRR model

Trigger: user links an IRR-model tab and asks to "ADD ASSUMPTIONS / PROJECT TRANSACTION DETAILS as per Investor... spreadsheet". Push `references/irr-model-transaction-details-enrichment.md`. Pull the A–H blocks (Project Identity, Land Details, Structure Spec, Sharing Ratio, Unit Break-up, Approvals, pre-financing Profitability, Sales Details) from `20260707_DRA_Group_Investor_Portfolio_All_Projects`, append as a new SECTION per project tab (below the sensitivity grid), plus a consolidated comparison tab if asked. Tag pre-financing (investor) vs after-financing (IRR model) numbers explicitly to avoid false contradictions.

## Entity Financial Verification from ITR / Balance Sheet PDFs

Trigger: the user (Prakash Singh / DRAAS) asks to "verify ITR and financial documents of each entity", "list assets/liabilities/loans/shareholders", "check financial data across all entities", or "extract and verify financial statements from Drive PDFs".

### 1. Locate financial documents on Drive

DRA entities' financial documents are stored in the `Firm Related Documents` folder or subfolders like `Financial Documents For DRA Realty`. Search pattern:
```
name contains 'ITR' or name contains 'Balance' or name contains 'financial' or name contains 'tax' or name contains 'P&L'
```
Key filenames include `"ITR Statement of Income P&L Balance Sheet Auditor Report"` and `"Copy of DRA Realty ITR..."`.

### 2. The PDF extraction pipeline (for scanned/image PDFs)

ITR acknowledgements and financial statements are NOT text-searchable PDFs — they are scanned images inside PDF wrappers. Do NOT try pdftotext or OCR libraries directly.

```
pdftoppm -png -r 300 <input.pdf> <output_prefix>
```

Then feed each page image to `vision_analyze()` with specific extraction prompts:

| Page type | Prompt strategy |
|-----------|----------------|
| **ITR Acknowledgement** (page 1) | "Extract ALL data: PAN, name, total income, business loss, tax paid, refund due, assessment year, signatory" |
| **Balance Sheet** | "Extract EVERY number, label, rupee amount for both years (31.03.20XX and 31.03.20YY). All figures in Rupees in Thousands unless otherwise noted." |
| **Profit & Loss** | "Extract ALL data — income, expenses, profit/loss, depreciation, tax — for both comparative years." |
| **Notes to Accounts** (Share Capital, Reserves, Borrowings, Provisions) | "Extract ALL numbers, labels, rupee amounts. This is Note X showing [Share Capital / Borrowings / Investments]." |
| **Auditor's Report** | Skip narrative pages (auditor responsibilities, CARO compliance). Extract only pages with actual schedules/notes. |

### 3. What to extract per entity type

**Private Limited Company:**
- Share capital (authorised, issued, paid-up)
- Shareholding pattern (≥5% holders, promoter holdings)
- Reserves & surplus (movement over 3 years: brought forward + current year)
- Short-term borrowings — separate into: loans from directors vs loans from others vs car loans
- Non-current investments — list each investee entity with ₹ amount
- Fixed assets (net)
- Cash & bank (cash in hand, balance with scheduled banks)
- Other current assets — list each line item (loans & advance asset, land advances, IVC holdings, TDS receivables)
- Short-term provisions (tax, TDS, GST, professional charges, audit fees — each line item)
- Net profit/loss trajectory over 3 years
- Tax paid, refund due
- Contingent liabilities (per auditor: "NIL" is the norm for DRA entities)
- Bank accounts (name, account no, IFSC, type)
- Directors' DIN numbers and PAN

**Partnership Firm:**
- Partnership deed date & registration number
- Partner names & profit-sharing ratio (track changes through reconstitutions)
- Reconstitution history (retirements, incoming partners)
- PAN/TAN/GST (all available)
- Note: ITR/financials are commonly MISSING from Drive — flag this as "⚠️ Not found on Drive — may need to source from Eshwari's emails or the firm's accountant"

### 4. Cross-verification (critical step)

Independent verification between three sources:
1. **ITR acknowledgement** — gives total income, business loss, tax paid
2. **Balance Sheet** — gives assets, liabilities, equity
3. **P&L Statement** — gives revenue, expenses, net profit/loss

Check that:
- ITR total income ≈ P&L total income
- ITR business loss ≈ P&L net loss
- ITR tax paid ≈ P&L current tax provision
- Balance Sheet total (assets) = total (equity + liabilities)
- Reserves & Surplus (current) = brought forward + current period P&L - transfers

### 5. Entity-level findings to report

Always present per-entity with:
- ✅ **Verified** (audited financials found, cross-referenced, no discrepancies)
- ⚠️ **Partial** (legal/registration docs found, no financials)
- ❌ **Not found** (no documents at all)

For each verified entity, surface:
- **Shareholders** — name, shares, % holding, whether promoter
- **Loans from directors** — amount, purpose (e.g. "for Ranka Amber project"), trend over years
- **Institutional loans** — bank name, type (car loan / OD / term loan), amount
- **Contingent liabilities** — per auditor's report (usually NIL for DRA entities)
- **Investment portfolio** — investee entities and amounts (shows where the entity has deployed capital into joint ventures)

### 6. Key DRA-specific conventions (discovered)

- All amounts in audited reports are **Rupees in Thousands** — multiply by 1,000 for actual ₹
- DRA Realty's short-term borrowings are **overwhelmingly NDR's personal loans** (₹23.76 Cr by 31.03.2025), not bank loans
- DRA Realty's non-current investments flow through: Westburry Hospitality — Seveganapalli Land Partners — added DRA Thindlu
- Partnership firm financials are consistently **not on Drive** — check Eshwari's email ITR zips
- Auditor: Y.T. Gandhi & Associates (Firm Regn 010990S) for all 3 years
- Directors: Nishant Ranka (DIN 00298854), Kishan Murjani Nair (DIN 05005329)
- Shareholding: Nishant Ranka 50%, Roshini Ranka 50% (5,000 shares, ₹100 face value)

### 7. Pitfalls

- **Don't skip pages** — Balance Sheet and P&L are sometimes just 1-2 pages in a 10+ page PDF; the rest is auditor's narrative. Quickly scan all PNGs via vision to pick out the actual data pages (look for tables with ₹ amounts).
- **The "Rupees in Thousands" trap** — every number in the Balance Sheet/P&L is in thousands. ₹500 = ₹5,00,000. State actual rupees in final output.
- **ITR acknowledgement business loss = 0 does not mean P&L shows a loss** — some FYs had income but the ITR only shows the final computed total. Cross-ref with the P&L sheet.
- **Investment in partnership firms on Balance Sheet** is listed as "Non-current Investments" — these represent the capital deployed by DRA Realty into the JDA partnership firms.
- **Loan account ledgers** (e.g. NDR — DRA Realty) are separate Google Sheets or PDFs, not part of the audited books. Check the "Loan Account" named files in Drive for real-time outstanding.
- The DRA Realty loan ledger for Ranka Amber showed ₹18.19 Cr on 14-Aug-2025 vs Balance Sheet ₹23.76 Cr on 31-Mar-2025 — the difference may be repayments in Apr-Jul 2025 or additional loan accounts not captured in one ledger.
- **No external bank term loans** — DRA entities have minimal institutional borrowing. Always note this prominently when comparing against listed peers.

## References

- `references/dm-project-finance-example.md` — worked DM 15-acre example: sheet layout with row numbers, exact formulas, expected ₹ Cr values, styling constants, and the sensitivity K-trick formula.
- `references/sheets-api-land-cost-model.md` — editable Google Sheets land-cost back-solve model (Palya 2A6G worked example): dynamic row-tracking build recipe, back-solve section layout, worked ₹ Cr numbers, and the three silent build killers (#REF! / No grid with id: 0 / leading-+ labels).
- `references/irr-model-transaction-details-enrichment.md` — append investor-workbook transaction-details (A–H blocks) as per-project sections + a consolidated comparison tab to the DRA Project Costing & IRR Model. Includes the Docs-API verification trick (dump table cells recursively, not just paragraphs) and the pre-financing-vs-financed tagging rule.
- `references/valuation-ipo.md` — full company valuation & IPO-readiness workflow (financial extraction, SEBI ICDR Reg 6.1 checklist, peer multiples, valuation approaches, synthesis).
- `references/comparable-company-multiples.md` — expandable database of listed real-estate peer multiples to reuse across valuation analyses.
- `references/xlsx-stdlib-parse.md` — parse a finished xlsx WITHOUT openpyxl (stdlib zipfile + regex): sharedStrings index resolution (cells with `t="s"` store an INDEX into `xl/sharedStrings.xml`, not the literal value — naive `<v>` extraction returns garbage), merged-cell row alignment, document_cache filenames with spaces/&. Use when openpyxl is unavailable in the sandbox.
- `references/dra-entity-financial-verification-example.md` — complete worked example from the 22-Aug-2026 session: DRA Realty 3-year extracted financials (Balance Sheet, P&L, shareholding, loan accounts, investments), plus the partnership firms' status and all Drive document links.
