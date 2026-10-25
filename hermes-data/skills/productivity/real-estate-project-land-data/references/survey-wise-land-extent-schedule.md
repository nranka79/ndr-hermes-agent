# Survey-wise Land Extent Schedule (TSR + JDAs + Opinions → dual-unit sheet)

**Trigger:** User shares a project Drive folder containing a TSR, JDAs, legal opinions, ILRs and registered deeds, and asks to "verify all the schedule properties", "extract the total land extent of each survey no", "list in a new spreadsheet in hec/ares and acre/cent with total of all extents". Worked example: Ranka Oasis / Sevaganapalli, 2026-08-31, folder `1sG1KlY-higI7vhoafHmyarS_qIWkspEW`, output sheet `1P1FadaUHfQ8674aqjkFv0uyFOmW2INSz3jr6rgLr3_o`.

## Scope discipline (Prakash correction, 2026-08-31)

When the user says "from above documents" / "check only this drive links" / "get the total land extents as per these registered documents", derive **ALL** data from the shared folder **ONLY**. Do NOT pull extents/owners from other workbooks (investor portfolio sheet, earlier session data, Drive search hits outside the folder). Extents and owners must trace to documents inside the folder. If a piece of data is not in the folder, say so rather than borrowing it.

## Document inventory (typical project folder)

| Doc | Format | How to read |
|-----|--------|-------------|
| TSR (IndusLaw) | text layer | `pdftotext -layout` — authoritative held-land list |
| JDAs | scans | `pdftoppm -png -r 150` → `tesseract` (installed at /usr/bin/tesseract) — schedule page near middle/end |
| Legal opinions (SLP 7.22 Ac, Jeevanandam 7.52 Ac) | scans | same OCR pipeline |
| DTCP layout approval | Tamil scan | opinion's English schedule is the readable authority |
| ILR PDFs | Tamil text layer, English owner names embedded | `pdftotext -layout` + grep for owner/extent |
| Registered sale deeds | sometimes text layer | `pdftotext -layout`; grep SCHEDULE section |

## Step 1 — TSR Part III

- Isolate the section: split text on `PART – III` / `PART – IV`.
- Item regex: `Item No\.\s*(\d+)\s*\n\s*Survey No\.\s*([0-9A-Za-z/]+)\s*measuring\s*([0-9¼½¾.\s]+?)\s*Acres`
- **Fractions break the strict regex**: `0.02½`, `0.34½`, `176/1B2D part measuring 0.03 ½`. Replace ½→.5, ¼→.25, ¾→.75 BEFORE float(). Expect a couple of unparsed items (Sevaganapalli: 33/34 parsed via regex; 158/1C7 0.34½ and 176/1B2D 0.03½ needed manual handling).
- **The owner summary table at the END of Part III is the authoritative owner+patta source** (columns: Sl.No | Survey No | Extent | Owner/s | Patta No). Parse that table rather than the narrative paragraphs. It also reveals the seller/partner buckets (individuals still on patta: Suresh & Y.Manjunath Reddy, Billa Reddy, Ravindra Reddy).
- Sum of parsed items should ≈ the declared header total (12.74 Ac). A shortfall = unparsed fraction items, not evidence of missing land.
- Item numbers may skip (#13 sits between #12 and #14 in the summary table) — trust the summary table numbering.

## Step 2 — JDA schedules (scans)

OCR the schedule page. Capture BOTH the aggregate and the per-survey split:

- **JDA 7963 (Ramesh Reddy → DRA Realty)**: total Hec.0.38.5 (or) Ac.0.95. Items: 166/1 = 0.35 (Hec 0.14.0), 167/1G = 0.07 (Hec 0.03.0), 168/1B = 0.53 (Hec 0.21.5, out of 168/1 total Hec 0.60.0 / Ac 1.48).
- **JDA 6157 (K Harish & family → DRA Realty)**: total Ac.0.50 (Fifty Cents, Hec 0.2037). Items: 177/1B = 32.30 cents (Hec 0.1307, out of parent Ac 1.04, Patta 984), 177/2A1 = 17.70 cents (Hec 0.0730, Patta 310).

## Step 3 — Legal opinions

- SLP 7.22 Ac opinion (N. Manjunath): 17 surveys, all owner = M/s. Sevaganapalli Land Partners. Use its Hec+Ac pairs as cross-check for SLP rows.
- Jeevanandam 7.52 Ac opinion (13.12.2025): 1st items = owned/approved-layout land, 2nd items = JDA land (166/1, 167/1G, 168/1B). This English schedule is the readable version of the Tamil DTCP approval. It adds surveys NOT in the TSR Part III (the approved-layout-only set: 166/2B2 0.10, 177/1A1A 0.03).

## Step 4 — ILR cross-check (Tamil text layer)

ILR PDFs carry Tamil with ENGLISH owner names and patta numbers embedded (e.g. `M/S. SEVAGANAPALLI LAND PARTNERS` / `M/S DRA REALTY PRIVATE LIMITED`, extent like `0.0-4.05`, patta `1941`). Use them to pin ownership of surveys missing from the TSR: 166/2B2 → SLP, patta 1941; 177/1A1A → DRA Realty, patta 2000; 177/1A1B → DRA Realty, patta 2000.

## Step 5 — Registered deeds

Registered sale deeds confirm actual acquisition (vendor → purchaser). E.g. SD 4350/2024: Sy 166/2B2, extent Ac 0.10, vendors Suresh Reddy & Y.Manjunath Reddy, vendee Sevaganapalli Land Partners. Mortgage deeds (e.g. 7049/2025, Schedule A: 166/3C 1.19, 158/1C9B 0.69, 158/1C9A 0.25, 167/2C 0.35, 167/2D 0.06 = Ac 2.54) corroborate ownership + patta.

## Step 6 — Reconciliation & dual-unit conversion

- **TSR owned total** = sum(SLP + DRA + seller/partner rows) ≈ declared 12.74 Ac.
- Keep three totals distinct: TSR-held (12.74), owned incl. layout-only extras (12.87 = +166/2B2 0.10 + 177/1A1A 0.03), grand total incl. JDA (14.32 = +0.95 Ramesh Reddy + 0.50 K Harish).
- Conversions: 1 Ac = 0.404686 Ha. Ac-Cent: `0-36` (integer acres, rounded cents). Hec-A-C: `0-14-57` (h=int(hec); (hec-h)*100 → a=int; round((rem-a)*100) → c; carry on 100).

## Step 7 — Sheet build (Sheets API pitfalls that bit)

- **Created spreadsheet's first sheetId is NOT always 0.** `spreadsheets().create()` then ALWAYS `spreadsheets().get()` → `sheets[0].properties.sheetId` before any batchUpdate referencing it (real case: 707851286; hardcoding 0 → 400 "No sheet with id: 0").
- **Hec-A-C strings like `0-04-05` auto-convert to DATES under USER_ENTERED** and read back as `2000-04-05`. Write ONLY the Ac-Cent and Hec-A-C columns with `valueInputOption='RAW'` after the main USER_ENTERED write. Numeric columns (Ac decimal, Hec decimal) stay USER_ENTERED.
- Batch batchUpdate requests ~40 per call with `time.sleep(1)`.
- Freeze header row; bold + fill subtotal/GRAND/TSR rows via repeatCell.

## Output shape (Prakash's expectation)

Columns: `S.No | Survey No | Extent (Ac - decimal) | Extent (Acres-Cents) | Extent (Hec - decimal) | Extent (Hec-Ares-Cent) | Owner / Acquirer | Category | Patta No | Source Document (registered) | Notes`.

Category subtotal rows for: SLP / DRA / Seller-Partner (per TSR) / JDA-Ramesh Reddy / JDA-K Harish, then `GRAND TOTAL (ALL SURVEYS)` and `TSR PART III TOTAL` rows for reconciliation. Flag discrepancies in Notes (e.g. 176/1B2D: TSR 0.03½ vs Jeevanandam opinion Hec 0.06.47 full extent — use the acquired extent, note the difference).