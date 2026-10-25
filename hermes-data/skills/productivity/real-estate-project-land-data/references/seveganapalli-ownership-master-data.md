# Sevaganapalli / Ranka Oasis — Ownership Master Data shortcuts (verified 2026-09-04)

Use these pre-built tables BEFORE re-deriving ownership from TSR/JDA/opinion scans. They
answer the recurring asks directly: "split of land held between the Company and the Firm",
"which surveys are registered / in the approved layout", "who owns each survey".

## THE master table — `Saveganapalli Kagganur Lands Sy No Master Data`

- → `https://docs.google.com/spreadsheets/d/1THJ4LvKyOB0GZIPamNLqkSBciCHqUki4_S1BLQ6jjCA/edit`
  (xlsx export works: `drive.files().export_media(file_id, mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')` — the Sheets API `values().get` on this workbook TIMES OUT, export-and-parse locally instead.)
- 7 tabs: `Ownership details (Registered)` · `Sevaganapalli` (994-row survey/FMB/patta index) · `Saveganapalli Final Shape List` · `Sheet10` · `Extended Survey Nos` · `VGP Survey Nos` · `Sheet7` (investor subdivision allocation A–H).
- Tab 1 `Ownership details (Registered)` IS the owner-split answer — columns:
  `Sl.No | Survey Number | Extent in Acres (as per Present Patta) | Including in DD | Belongs To | Ownership Vide`
  - `Belongs To` values seen: **DRA Realty**, **Sevaganapalli Land Partners**, **DRA Sevaganapalli Land Partners**, unregistered agreement rows; blank = advance-paid/discussion only.
  - `Ownership Vide`: Exchange Deed / Sale Deed / Agreement to sell / Advance Paid / Discussions.
  - `Including in DD` = Y/N flag (registered & in the DTCP/development deal vs not-yet).
  - Row sample (2026-09-04 read): 176/1B2 0.07½ DRA Realty (Exchange Deed) · 158/1A1A 0.36 SLP (Sale Deed) · 158/1B1 1.01 unregistered agreement (Advance Paid) · 177/1A 0.26 DRA Realty (Exchange Deed) · 168/1A 0.95 DRA Realty (Agreement to sell) · 166/3A 1.38 SLP (Sale Deed).
- Parsing recipe when openpyxl is unavailable: stdlib `zipfile` + `ElementTree` — resolve `xl/sharedStrings.xml` (cells with `t="s"` hold an INDEX into shared strings, not the literal), map `xl/worksheets/sheetN.xml` to tab names via `xl/workbook.xml` sheet order. See `real-estate-financial-modeling` → `references/xlsx-stdlib-parse.md`.

## Other pre-built Sevaganapalli artifacts (Drive, ndr@draas.com)

- **Sevaganapalli Land Partners** folder → `104VWF9-XdeLX612NjHE9s2-92KTpmz77` (organized 00-10 subfolders: Legal_and_Title, Partnership_and_Firm_Docs, Approvals_and_Regulatory, Engineering_and_Design, Investors_and_Finance, Acquisitions, etc.).
- **DTCP / layout approval set:**
  - `20260113 Ranka Oasis Sevaganapalli Layout Plan – DTCP Krishnagiri` → `1pJ9upN71y3gegmZWa4WtFJSzcbpCmurI` (1-page Tamil scan, NO text layer — `pdftotext` returns ~0 lines).
  - `20260330 Ranka Oasis Sevaganapalli Layout Planning Sanction – Sevaganapalli Panchayat & DTCP Krishnagiri` → `1hqAPCZTj829ceph0JioCKayY7uxhTQ2I` (3-page English; the readable approved-surveys authority; the OCR-clean route).
  - `RANKA OASIS - TOTAL PROJECT LAND AREA PLAN 26714.pdf` → `1JJcv_dXafUyO_yL_kBR2F-wKo0MJGP4L` (also mostly graphic; use the sanction letter).
- **JDA deeds:** `20251031 JDA NO 7963 Btwn DRA Realty & Ramesh Reddy` (166/1 0.35 · 167/1G 0.07 · 168/1B 0.53) and `20250925 JDA NO 6157 Btwn DRA Realty & K Harish` (177/1B 32.30c · 177/2A1 17.70c) — the "JV Land" answer (Ramesh Reddy + Harish rows = JDA/JV land; parent-held surveys in `Ownership details` = registered title).
- **Loan-cum-investment agreement family** (SLP-Hosur, 2025): `1mDddzmA230xwp-UDCa_-PT-Fei3w9FcOmOi5lc1Obgg` (FM Review v1 01.04.2025), `1uVSXAKpvtskUvZe0Aw5cIlbug-NTn3UI9AJeSurpuFI` (FM Draft, Madhu NDR Fox comments), `1xkO8LLyoJrW7Luk6Id_A5V7ld38lI_hcBrsc6Oachn8` (Draft v1 13.03.2025).

## What answers the standard investor questions (Jiraaf/Vishwas style)

1. "Split of land held between Company and Firm" → Tab 1 `Ownership details (Registered)` grouped by `Belongs To` (registered surveys only; JDA rows flagged separately).
2. "Guidance value of parcels" → NOT in this workbook — pull from Anbu (anbarasan@draas.com) or TN govt guideline-value source; no consolidated guidance table exists on Drive for Sevaganapalli (2026-09-04 check).
3. "Estimated investment & potential return" → Jiraffe JD Deal IRR model Summary tab (see `real-estate-financial-modeling` → `dra-irr-model-file-inventory.md`).

## Survey-list → extent extract (acres+cents) from the source sheets (verified 2026-09-15)

When NDR sends a plain survey-number list ("for each sy no give the exact extent in acres
and cents mentioned in that spreadsheet, then total it") — do NOT re-derive from TSR/JDA
scans. Work from the registered-extent spreadsheets, in this order:

1. **Primary: Kagganur Master Data tab `Ownership details (Registered)`** (id above) —
   column `Extent in Acres (as per Present Patta)` holds the A.Cents figures as entered
   (e.g. `0.69` = 0 ac 69 c; `1.38` = 1 ac 38 c). Add tab `Sevaganapalli` for the exact
   Ares/SQM breakdown + FMB/Patta links + Reg Status (`Done` / `Not Done`).
2. **Newer registered sub-divisions NOT in Master Data** (158/1C9A, 166/2B2, 176/1B2D,
   176/2B4A, 177/1A1A) → **`DRA Sevaganapalli Project Breakdown by Survey number`**
   (id `1gfAFQMnuxNmm4HrxA5uARkLriHaSju_xUmRl6xdJWa8`, owner madhu.ga@gmail.com — reachable
   via Bharat's DWD). Its `Area in Hectares` column is HH-AA format (`0-38.50` = 0 ha 38.5
   ares = 3850 sqm); convert via SQM/40.4686 → cents, or read the same survey's row from
   `Registered Sy No Details` which states A.C direct.
3. **Corroborating sheets (all consistent on the core registered block):**
   - `Sevaganapalli Reg Sy Nos` → `1NFRMQOmQCWCK6VGn7qleHs_w2qlUrqoXfn4uBM0EJF0` (Bharat) — same columns as Master Data tab 1, 26 rows.
   - `Sevaganapalli Registered Sy No Details` → `1DZO4C863HSp2zhvAD7D7evBwV8WMW7U_l3RBSuPIHrU` (Bharat) — Extent (Hectares) `0.14.50` form + Extent (Acres/Cents) + Assessment + remarks; Sheet2 = RTC dry-land classification (167/2C reads 0.36 here).
   - `Sevaganapalli Accounts` → `1sVYK9ZpnUqsf5v_OmfH0AC-dQhMbfAa_PD3UqS8U-NA` (admin2.blr@draas.com, NOT on Bharat's drive — impersonate admin2 directly). Tab `Sy.no extend` lists the registered sale-deed extents (totals 7.53 ac); Statement Sheet = per-seller payments, ₹44.66 Cr sale-deed total, ₹11.54 Cr total spend on SLP 7.53 ac, ₹153.28 L/ac.

### Known cross-sheet discrepancies to FLAG (never silently pick a side)

- **167/2C**: 0.35 (Registered Sy No Details Sheet1) vs 0.36 (same sheet Sheet2 + Sheet7, patta 35.8c) — confirm at registration.
- **166/1, 167/1G, 168/1B**: marked `Advance Paid` / `Discussions` (NOT registered) in Master Data — 168/1B also has an internal inconsistency (computed 0.478 ac vs 0.53 stated).
- **177/1A1A** (2.5c, DRA Breakdown "Entry") is DISTINCT from 177/1A1 (23.5c, Registered Sy No Details) — don't merge.
- **166/2B2** (4.05 ares, P1 registered) is distinct from 166/2B (13.5 ares, 0.30 ac) — two different subdivisions.
- Master Data + Reg Sy Nos list `158/1C9B` but NOT `158/1C9A`; the DRA Breakdown is the only sheet that registers 158/1C9A (10 ares = 0.25 ac). Sheet7's `167/1C9A` row is a typo for 158/1C9A.

### Deliverable shape NDR expects for "extract from the spreadsheet"

HTML table (self-contained file, inline CSS): survey number | extent A.C | acres | cents |
source sheet | what it is/remarks — then a TOTAL row in acres+cents. Every value must cite
the exact source sheet; flag non-registered rows AND cross-sheet conflicts in the remarks
column, and confirm truncated survey lists (his message cut off at "177/" — I delivered
177/1A1A and asked for any further 177/… numbers).