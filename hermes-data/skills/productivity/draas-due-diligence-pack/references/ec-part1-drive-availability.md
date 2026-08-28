# EC transaction list → PART_I sheet → Drive folder availability cross-check

Worked example 2026-08-13: 131 unique EC documents (from ECs 158/166/167/176/177
Sevaganapalli) checked against PART_I_DocFurnished (DocMatrix workbook
1eVqckk3cCWdN06RNGISTP99WSz-aToCmGcNPIIqaicc) then against a Drive folder.
Result: 64 available in PART_I, 67 not; of those 67, only 12 were in the Drive
folder. Delivered as two new color-coded tabs.

## The three-way match recipe

### 1. EC master list (input)
From the parsed EC dataset (see `ocr-and-documents` ref
`tn-ec-transaction-parsing.md`): 131 unique docs with docno like `434/1976`,
type, date, ECs where it appears.

### 2. Match against PART_I_DocFurnished (or any "docs furnished" sheet)
Headers: `S.No | Date | Document Description | Drive Link | Matched File / Notes | Status`.

- **Extract (docno, year) pairs from each row's text** (description + matched
  file + date column) with MULTIPLE regex patterns, not one strict pattern:
  - `(?:doc|deed|no|number)[\s.:/-]*(\d{3,6})[/\s]*(?:of\s*)?(\d{4})` — "Doc 5585/1980"
  - `(?:no|number)[\s.:/-]*(\d{3,6})(?![\d/])` with year from the DATE column — "No 3470" + date 20.08.1993
  - `(?:20\d{2}|19\d{2})\d{4}[^0-9]*?(?:no|deed)[\s.:/-]*(\d{3,6})` — "20231128 ... NO 22229.pdf"
  - `(\d{3,6})/(\d{3,6})` — "3427/3428 are related" (both numbers + date year)
- **Exact match on (num, year) → AVAILABLE.** Ignore noise pairs like
  `('166','2023')` (survey number + date-year) and `('177','1210')` (from
  "12102001" filename prefix) — they never collide with real docnos.
- **Date + description fuzzy match for ext-index rows lacking doc numbers:**
  rows like "Sale Deed dtd 13-05-2011 ... Sy.no.166_3E" = EC doc 6512/2011
  (13.05.2011). Extract date tokens `DD-MM-YYYY`, `DD.MM.YYYY`, AND `YYYYMMDD`
  from row text; compare against the EC transaction date.
- **PITFALL — YYYYMMDD tokenizer month/day swap:** `20240302` = 2024-03-02
  (year-month-day). A buggy regex `f"{g1}-{g3}-{g2}"` yields 2024-02-03 and
  silently misses real matches. Use `f"{g1}-{g2}-{g3}"`.
- **PITFALL — same-date ≠ same-doc:** rows can share a date but be different
  registered docs: 19345/2023 cancellation listed but EC also has 19344/2023
  and 19346/2023 and 19356/2023 (same 17.10.2023); 4515/1995 listed but EC has
  4512/1995 (same 16.08.1995); 12569/2023 GPA listed but EC has 12669/2023
  release deed (same 07.07.2023). Date-fuzzy hits must be MANUALLY verified —
  a date match alone is NOT a match. Mark as NOT AVAILABLE when the docno
  differs.

### 3. Match against a Drive folder
- **Walk the folder recursively** with the Drive API (`q=f"'{folder_id}' in
  parents"`, pageSize 1000, follow subfolders). DRA project folders are big —
  891 files across root + Legal Opinions / Approval / JDA / firm docs /
  Pattas & FMBs / "Unique Set (291)".
- Extract doc numbers from FILENAMES with the same multi-pattern regexes +
  number-only fallback (`all_doc_number_refs` — any `(?:no|deed|doc)[\s.:/-]*(\d{3,6})`).
- **Number-only matches need type/context verification** (e.g. 9188/2025 gift
  deed = "Copy of 2026 Gift Deed No 9188 DRA Realty SLP & TN Govt Road Related.pdf").
- Same-date different-doc false positives apply here too (19345 file vs 19344 EC doc).
- Prefer the shortest filename when multiple copies exist (root-level over
  "Unique Set (291)/..." duplicates).
- Report format: docno | type | date | ECs | YES/NO | drive filename | drive link.

### 4. Deliver as new tabs (never modify existing sheets)
- Create tab via `batchUpdate` addSheet; write via `values().batchUpdate` (RAW);
  read back and verify row counts.
- Color-code: green fill for AVAILABLE/YES rows, red for NOT AVAILABLE/NO
  (group consecutive same-status rows into one repeatCell range — the
  run-length trick from `tsr-approved-vs-nonapproved.md`).
- Freeze header, bold, autosize. Summary block at bottom (counts per EC).
- When the user replies with a Drive link and asks "are the not-available ones
  in this folder", build a SECOND tab (`EC_vs_Drive_Folder`) with drive status
  + clickable links — do not overwrite the first availability tab.
