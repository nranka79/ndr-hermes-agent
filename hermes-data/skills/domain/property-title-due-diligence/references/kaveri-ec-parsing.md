# Kaveri EC Parsing — concrete patterns (from Besthamanahalli / Sanchaya Additional EC sessions)

## Row segmentation (consolidated/additional ECs)
Two row-marker families — split on BOTH, or the second family merges into one segment:

```python
segs = re.split(r'(?=(?:Note:\s*\[|\n\d{1,3}\s*Property Number\s*:))', text)
segs = [s for s in segs if s.strip()][1:]   # drop the header segment
```

- `Note: [Schedule A: ] Sy No 103, ...` — the common family (Schedule A/1/2/.../11)
- `NN Property Number : 140*2 ...` — newer rows, NO "Note:" prefix; doc token is a single full registration number

## Page-break junk stripping
Every page break injects a footer block that pollutes the middle of rows:

```python
p = re.sub(r'Page\s+\d+\s+Of\s+\d+', ' ', p)
p = re.sub(r'Only For Information.*?1\s*2\s*3\s*4\s*5\s*6\s*7\s*8\s*9', ' ', p, flags=re.S)
# drop long Kannada-only header lines, but KEEP Kannada inside parties (ಬಿನ್ father names)
if re.fullmatch(r'[\u0c80-\u0cff][\u0c80-\u0cff\s]{5,}', s): continue
```

## Field regexes (all with re.S where noted)
```python
DATE_RE   = re.compile(r'(\d{2})-(\d{2})-(\d{4})\s+Article\s+Name\s*:')
ARTICLE_RE= re.compile(r'Article\s+Name\s*:\s*(.*?);;', re.S)
CONS_RE   = re.compile(r'Consideration\s+A\s*m\s*o\s*u\s*n\s*t\s*:\s*(\d[\d,]*)', re.S)
MV_RE     = re.compile(r'Market\s+Value\s*:\s*(\d[\d,]*)', re.S)
SURVEY_RE = re.compile(r'(?i)(?:Sy\.?\s*/?\s*No\.?|Survey\s*No\.?|Converted\s*Survey\s*No\.?|bearing\s*Survey\s*No\.?|SURVEY\s*No\.?)\s*[:\s]*([0-9]{1,3}(?:/[0-9]{1,2}(?:[A-Z])?)?)')
```

## Doc number formats — BOTH appear
1. 3-field line: `13 CMPD60 CMP-1-03309-2012-13` (page | short doc | book)
2. Single full registration token: `12 ABL-1-03366-2025-26` (page | book/doc combined; no short code)
```python
DOC_RE     = re.compile(r'(?m)^\s*(\d{1,2})\s+([A-Z]{2,4}\d{2,4})\s+([A-Z]{2,4}-\d{1,2}-\d{4,5}-\d{4}-\d{2})\s*$')
DOC_ANY    = re.compile(r'(\d{1,2})\s+([A-Z]{2,4}\d{2,4})\s+([A-Z]{2,4}-\d{1,2}-\d{4,5}-\d{4}-\d{2})')  # embedded in party text
DOC_SINGLE = re.compile(r'(\d{1,2})\s+((?:[A-Z]{2,4}-\d{1,2}-\d{4,5}-\d{4}-\d{2}))')
```
When the single-token fallback matches, doc_no = book_no = the token (2 groups only — guard `group(3)`).

## Party splitting (line-aware)
- Party-start token list: `M/s | M/S | Sri | Smt | Mrs | Mr | Ms | Tetron | SUTRA | KUSMITHA | MITHUN | ANAND | GOGINENI | SHIVAPPA | DILIP | VENKATADRI | HARISH | MAHADEVAPPA | YALLAPPA | RAMAKRISHNA | PRASHANTH | SRINIVASA | VISHWANATH | Swarnadhara | Concept | Vijaya | Srinivasraju | SANCHAYA`
- **Skip a token line whose PREVIOUS line is a signature keyword** (prevents "Signatory Mr.X" being read as a new party):
  `(Rep by|Repby|REP BY|Signatory|Authori[sz]ed|Represent|Managing|is Rep|GPA Holder)`
- **Merge honorific repetitions** of the same company (e.g. `Ms.M/s. SANCHAYA` then `Sri.M/s. SANCHAYA` = ONE party): merge a start line matching `^(?:Ms|Sri|Smt|Mrs|Mr)?\.?\s*M/?s\.?\s*SANCHAYA` into the previous block if the previous block also starts with a Sanchaya line.
- party1 = lines before the LAST block start; party2 = from last block to end.
- EC lists parties in document order: party1 = transferor/executant, party2 = counterparty.

## Direction semantics (from → to) by article
- Sale / Agreement of Sale: P1 → P2 (transferor → transferee)
- DTD (Deposit of Title Deeds = loan): P1 (borrower/owner) → P2 (lender)
- Discharge Deed: P1 (lender discharging) → P2 (borrower/owner)
- Cancellation Deed: P1 (party whose rights are cancelled) → P2 (other party)
- Consent Deed: P1 (consenting) → P2 (beneficiary)

## Page-break column interleaving — the killer bug
Kaveri column layout emits doc number / consideration BETWEEN party fragments when a row spans a page break. Symptom: party1 starts with article text ("Agreement of Sale of Immovable Property...") or contains "Market Value". **Repair strategy**: group rows by (doc_no, article); copy parties from a clean sibling row (all rows of one document share identical parties). Detect contamination with:
```python
if re.match(r'^(Agreement of Sale|Cancellation Deed|Discharge Deed|Sale;;|DTD;;|Consent|Market)', p1): bad
if re.search(r'(Market\s*Value|Consideration|Article\s+Name|issued by Special|Measuirng|of Converted Land|Vide Conversion|Sy\.?/?\s*No\.?\s*\d)', p1): bad
```
Sibling repair is a POST-PASS (after parsing all rows), and must be re-run whenever the parser changes — it silently drops if the parse order changes.

## Article types observed (200-row consolidated EC)
Agreement of Sale of Immovable Property (Possession not given) 73 | Cancellation Deed 42 | DTD 34 | Sale 30 | Discharge Deed 20 | Consent Deed 1

## Survey cleanup
- `*` suffix on old-set surveys = re-survey marker (normalize away before comparing)
- Trailing `m` glued from "measuring" (e.g. `Sy no 133/2measuring` → "133/2m"): clean post-hoc with a regex that stops before `measur`
- `Sy/No 82/3` slash variant needs the `/` in the survey regex
- Sort transactions by ISO date (yyyy-mm-dd), NOT dd-mm-yyyy strings (lexical sort is wrong)

## Comparison across EC sets (per survey)
- old docs = regex `Doc\s+([A-Z]{2,4}\d{2,4}|[A-Z]{2,4}-\d{1,2}-\d{4,5}-\d{4}-\d{2})` from the old dataset's transaction strings
- missing = old-only docs, extra = new-only docs; flag surveys with 0 transactions in the new EC entirely
- Expected gaps (NOT red flags): pre-buyer history in an additional/party-centric EC — 2006–2011 original-owner sales, 2015 MABA DTDs, 2018 CMPD213/214 discharges
- Worth flagging: missing RECENT docs (2022+ discharges, 2023+ cancellations) and open agreements with no cancellation/sale after

## Deliverable shape (DRA/Prakash convention)
- Sheet per survey (Sl No, Survey No, New Survey No, Village, EC No. = "Not printed", EC period, transactions oldest→latest, Remarks with ⚠ + yellow highlight)
- Sheet per transaction (one row per transaction: DATE, Type, Doc No (Book), From, To, Consideration, Market Value, Property)
- Sheet comparison (per survey: in-old? in-new? counts, flow oldest→newest with from→to, remarks, flags, issues)
- Spreadsheet link delivered in a code block (Telegram breaks URLs); file shared with psingh@draas.com; EC No. not printed on Kaveri print-view certs

### CLEAR v2 deliverable (user-approved Aug 2026 — Besthamanahalli EC review)
User rejected the first comparison sheet ("Can't understand the comparison sheet") and asked to regenerate with clear transaction history + land extent. Approved shape:
- **Survey Master**: one row per survey — Sl No | Survey No | Extent (A-G-A) | Total Guntas | Total Acres | Landowners (RTC) | In Old 71 ECs? | In New EC? | # Old Txns | # New Txns | Red Flags. Row colors: red = OPEN DTD, amber = flag/missing, grey = extent unavailable.
- **Transaction History**: FLAT ledger merging BOTH EC sets (one row per txn) — Survey | Extent | Date | Type | Doc | From→To | Consideration | MV | EC Source. Sort GLOBALLY by date DESC (newest first), NOT by survey number — user corrected this explicitly ("from newest dates to old, not survey no wise").
- **Comparison & Red Flags**: per-survey row with a multi-line Transaction History cell — each txn as `▶ DD-MM-YYYY | Type | Doc` + `From:` + `To:` + `₹:`. Sort ROWS by the survey's newest txn date DESC (82/4 14-10-2025 on top), tie-break by survey no.
- **Land extent columns are mandatory** ("add Land extent as well"). Sources: RTC Survey Extents tab of the Survey Number Document Index (A-G-A, guntas, acres, landowners) for Sy ≤ 102/6; MOU Schedule summary table as fallback for FP1 lands; grey out surveys with no extent and tell the user which RTCs are missing.
- Normalize survey keys: RTC uses dash (`80-1`), EC uses slash (`80/1`), `m` suffix = re-survey marker (strip for matching, but KEEP separate rows for `81/1` vs `81/1m` — they carry different in-old/in-new flags).

### Old-set party splitting (from→to, 71-EC strings)
Old-set txn strings are `DD.MM.YYYY: Type — ₹X | Doc YYY | Parties: FROM TO` with parties CONCATENATED (no arrow). Split at the LAST eligible party-start token:
- Token regex: M/s, M/S, Sri/Smt/Mrs/Mr/Ms/Kumari/Master/Miss + known company/person names (SANCHAYA, SUTRA, TETRON, MABA, DILIP, VENKATADRI, HARISH, MAHADEVAPPA, YALLAPPA, RAMAKRISHNA, PRASHANTH, SRINIVASA, VISHWANATH, Swarnadhara, Concept, Vijaya, Srinivasraju, GOGINENI, KUSMITHA, MITHUN, ANAND, SHIVAPPA, Prateek, Chowdappa, Venugopal)
- SKIP tokens immediately preceded by signature keywords: `Rep by | Rep. | by its | by | S/o | D/o | W/o | ಬಿನ್ | GPA Holder | SPA Holder | Signatory | Authorized | Represent | Managing | is Rep | s/o | d/o | w/o`
- Back up from the token start to include a leading `M/S ` prefix (`M/S SANCHAYA` → start at M/S)
- Where the split fails (To empty), keep the full string; garbled Kannada/OCR in old scans is source-data quality, not a parsing bug.

## User legibility preference — CLEAR v2 layout (07-Aug-2026 correction)
Prakash could NOT follow the v1 comparison sheet (jam-packed "Transaction Flow" blob of concatenated parties). When he asks to "make clear transaction history" / "re-generate the spreadsheet", rebuild as:
1. **Survey Master** — one row per survey: Sl No | Survey No | Extent (A-G-A) | Total Guntas | Total Acres | Landowners | In Old? | In New? | #Old | #New | Red Flags. Fill: red = OPEN DTD, amber = flag/missing txn, grey = no extent data.
2. **Transaction History** — flat one-row-per-transaction ledger MERGED from both EC sets: Survey | Extent | Date | Type | Doc | From → To | Consideration | MV | Source (Old 71 ECs / New EC). Sort by survey number (numeric, not lexical) then ISO date. This is the sheet the user actually reads — keep it filterable by Survey No.
3. **Comparison & Red Flags** — keep the flow column COMPACT: one token per txn `DD-MM-YYYY Type [DOC]` joined with → (e.g. `26-04-2012 Agmt [ABLD102] → 29-08-2012 Sale [...]`). Never paste full party strings into the flow column.
Always add land extent columns to every sheet (Survey Master, Transaction ledger, Comparison).

## Land extent sourcing (Besthamanahalli pattern)
- Primary source: "Bestamanahalli - Survey Number Document Index" spreadsheet → "RTC Survey Extents" tab (Sl No, Survey No, Extent Acre-Gunta-Anas, Total Guntas, Total Acres, File Name, Drive Link, Landowners EN + KN). Covers only the low survey range (Besthamanahalli: up to Sy 102/6 ≈ 80 records) — the index was built from RTC PDFs on Drive.
- Fallback: the MOU "SUMMARY TABLE" (in the schedule-properties doc) gives per-survey extents for aggregated FP lands ("09 Guntas", "01 Acre (40 Guntas)") — convert: 1 acre = 40 guntas; multi-survey rows like "133/4, 134/1, 134/2, 134/3, 135/1" share the combined extent.
- Surveys with NO extent source: leave blank, grey the row, and TELL the user explicitly which surveys are uncovered (do not silently omit) — offer to fill when RTCs for the higher survey numbers are provided.

## Survey-number normalization pitfall (m-suffix rows)
EC sets use slash ("81/1"), RTC index uses dash ("80-1") — normalize dash→slash for lookup. BUT "m"-suffixed entries (81/1 vs 81/1m, 85/3 vs 85/3m, 98/2 vs 98/2m, 99/2m/3m/4m, 100/1m, 86/1m, 133/2m) are DISTINCT comparison rows — one is old-only, the other new-only (81/1 = in old 71 ECs with 4 txns; 81/1m = only in new consolidated EC with 1 txn). Do NOT collapse them when building the Survey Master: first build merged them and silently lost the in-old/in-new presence flags. Keep display survey names as-is; strip `m`/`*` ONLY for extent-map lookup.
