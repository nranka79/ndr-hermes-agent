---
name: tn-ec-parsing
description: >
  Parse Tamil Nadu (TN REGINET) Encumbrance Certificate PDFs into structured
  transactions — survey number, document no, type, dates, From/To parties,
  consideration, PR number, and the full survey list per document. Use for
  any TN EC from SROs like Hozur/Bagalur (Sevaganapalli village). Covers the
  pdftotext -bbox extraction method, column zones, entry detection, survey
  schedule parsing, and Prakash's per-survey spreadsheet deliverable format.
metadata:
  hermes:
    tags: [ec, encumbrance, tamilnadu, reginet, sevaganapalli, hosur, parsing, pdftotext, title-due-diligence]
    category: domain
    related_skills: [property-title-due-diligence]
---

# TN EC (Encumbrance Certificate) Parsing — TN REGINET

Tamil Nadu ECs (e.g. Sevaganapalli, Hosur) come from the TN REGINET system
(iText-generated, landscape A4, Tamil). These are NOT Karnataka Kaveri ECs —
different department, layout, language, and SRO data-availability logic.

## The ONE reliable extraction method: pdftotext -bbox

- pdfplumber GARBLES Tamil text (broken ToUnicode for the Tamil font) though
  it gives x-coordinates.
- pdftotext -layout gives correct Tamil but character columns SHIFT between
  the old multi-line entry format and the compact single-line format.
- `pdftotext -bbox file.pdf -` gives BOTH correct Tamil text AND
  x-coordinates. Parse `<word xMin yMin xMax yMax>text</word>` elements.

### CRITICAL gotcha — page tags have NO number attribute

The page tag is `<page width="842.000000" height="595.000000">` — no
`number=` attribute. Track page index by counting `<page ` occurrences in
order. If you ignore pages, words from every page with the same y merge into
one giant line and everything breaks.

### Column zones (page points, landscape A4 ~842x595)

| Zone (x0) | Field |
|---|---|
| <100 | Sr No (standalone small int) |
| 100–215 | Document No & Year (`NNNN/YYYY`) |
| 200–310 | Dates (execution / presentation / registration) |
| 305–412 | Nature |
| 410–532 | Executants (From) — numbered "1.", "2.", ... |
| 532–650 | Claimants (To) — numbered |
| 650+ | Vol.No & Page |
| 400+ (in schedule blocks) | Survey numbers |

### Line grouping

Bucket words by (page, round(y0/4.5)). A 2.5pt bucket is too fine: Sr No and
the first party name on the same visual row sit on slightly different
baselines and split into two lines, breaking entry boundaries.

### Entry detection

1. Candidate starts: lines with a standalone int at x0<100 (Sr No).
2. A candidate is a REAL start iff the block from it to the next candidate
   contains a Document-No word (x0 100–215, `NN/YYYY`) AND
   'Consideration Value'.
3. Dedupe by sr value, keep first occurrence; sequence must be 1..N with no
   gaps.
4. Page-break quirk: the first executant of an entry can sit on the line ABOVE
   the Sr marker — if the line before a start has a standalone `N.` marker at
   x0 410–650, prepend it to the block.

### Survey number extraction

- **HARD STOP at the boundary description.** The schedule section ends when
  `எல்லை விபரங்கள்` (or `Boundary Details`) appears — everything after is
  neighbor-plot references (e.g. "EAST : Land in Survey No. 176/285", "Road
  No. 04 ComesUnderSy.No.166/2B2"), NOT the transaction's survey list. `break`
  the scan on that label. Without this, boundary text pollutes surveys with
  plausible-looking refs (176/285, 176/2B4B, 66/2B2, 165, 159, 158/1C8...)
  and the output looks "reasonable" but is wrong.
- Old format: `Survey No./புல எண் : 101/9, 115/3, ...` at x0≥414. Match on
  'Survey No.' only (Tamil label "புல எண்" is often on a SEPARATE line).
  Continuation lines may carry a label (Village & Street / Property Type) in
  the LEFT zone — check the RIGHT zone only, and accept a line only if it is
  a *pure* survey list (strip `[\d/,.:;\sA-Za-z-]+` → nothing left). Keep
  slashed tokens AND standalone whole surveys on the same line (e.g.
  "104, 111, 39" beside 102/9, 103/3 — these are real whole survey nos).
- Modern format: `Survey No-Extent/புல எண்-விஸ்தீர்ணம்: 176/1B2 - 16.0
  CENTS; ...` — scan ALL `NN/NNX` tokens; do NOT require "- XX.X CENTS" on
  the same line because extent values wrap across lines (this drops surveys
  like 158/1A1B whose "- 50.0 CENTS" lands on the next physical line).
- Modern continuation: the extent list wraps across lines whose LEFT zone
  carries labels (Property Type / Village & Street). Accept the RIGHT zone
  only if it is a pure survey/extent list — reject lines containing
  EAST/WEST/NORTH/SOUTH, Road, Proposal, Sites, Mtr, ComesUnder, Land in,
  மேற்கு/கிழக்கு/வடக்கு/தெற்கு, Park, Boundary, Survey No, Schedule,
  Remarks, Consideration; then strip survey tokens + extent words
  (CENTS/ACRE/SQUARE/FEET/HECT) and require nothing meaningful left.
- **Old-format continuation must NOT run on modern entries** — gate it with
  `not modern`. Otherwise "50.0 CENTS; 158/1C1 - 69.0 CENTS..." extent lines
  leak standalone values (50, 69, 19, 54...) as fake surveys.
- **Never `continue` past the `SURVEY NUMBER:` remark rule.** In
  `parse_schedules`, the modern-continuation block used `continue` when the
  right zone contained a keyword, which silently skipped the bottom
  `SURVEY NUMBER: 167/2C, Dry.Ext...` rule and lost remarks surveys (e.g.
  177/1A1A). Use `if right and not any(...)` — not `continue`.
- `SURVEY NUMBER: 167/2C, Dry.Ext...` inside schedule remarks (modern
  subdivision descriptions in gift/settlement deeds). Note the number can sit
  on the NEXT bbox line after "SURVEY NUMBER:" (line-split differs per EC) —
  the cross-EC union covers this.
- **Final noise filter (dedupe pass):** drop single-digit standalone tokens
  (page artifacts), zero padding (`0{2,4}`), and year-like tokens
  (`\d{1,4}/\d{4}` — e.g. "1/2025" from ROC application numbers). Do NOT
  drop 2-digit standalone values (39, 96, 104, 111, 137, 182, 183, 184, 185
  are valid whole survey numbers in this village).
- **Cross-EC union for the master table:** the same document appears in
  several per-survey ECs and each EC's survey list may differ slightly due to
  page-break truncation. For the Master tab, take the UNION of that doc's
  survey lists across all ECs (e.g. 9188/2025 → 19 surveys from 5 ECs;
  per-EC lists were 11–18).
- Combined deeds (partition/gift/settlement) list MANY surveys — that is how
  one document legitimately appears in several per-survey ECs. This is the
  basis of the "group under document no" requirement.

### Consideration block

After the 'Consideration Value' label line, values appear on the next line(s):
consideration x 100–310, market value x 310–530, PR numbers x 530+. Skip
label lines, STOP when hitting a 'Schedule ... Details' line. Old format uses
"ரூ. 3,224/-", modern uses "Rs. 15,27,50,000/-" or "-". PR numbers are
comma-separated prior-doc references like "1611/2024, 4292/2024".

### Data availability

Page 1 header shows the Data Availability Period, which can span TWO SROs:
e.g. "Hozur Sub Registrar Office: From 01-Aug-1975 To 16-Feb-2025" then
"Bagalur Sub Registrar Office: From 17-Feb-2025 To 12-Aug-2026". Search
period covers both.

## Validation

- Entry count MUST equal the "Number of Entries/பதிவுகளின் எண்ணிக்கை" footer
  (e.g. EC158→52, EC166→35, EC167→15, EC176→29, EC177→39).
- Sr sequence must be 1..N with no gaps (write a checker).
- Every entry must have a non-empty survey list.
- Spot-check parties and survey schedules against raw PDF lines for a sample
  of entries in each format (old multi-line vs compact single-line).

## Deliverable format (Prakash, per-survey EC verification)

Excel workbook, one tab per survey no + Master tab + Summary tab:

- Per-survey tab columns: Sl No | Sy No | Sub-number(s) | Type of Transaction
  | Transaction Date | From Party Name | To Party Name | Document No. |
  Other Sy Nos in same doc | Consideration | PR Number
- Master (All Docs) tab: unique documents deduped by doc no, with ALL survey
  numbers grouped in one column plus 'Appears in ECs' column — satisfies the
  user's rule: "if same document has multiple survey nos, show them under the
  document no together to avoid repeated entries."
- Summary tab: per-survey entry counts, unique doc counts, search periods.
- First build locally as .xlsx via openpyxl (use the uv venv python —
  `/opt/data/.venv/bin/python` — execute_code's sandbox python lacks openpyxl;
  dump the workbook to JSON with the venv, then push rows to Sheets from
  execute_code). Verify footer counts row-for-row before delivery.

### Delivery: DocMatrix spreadsheet-append (user's actual preference, 2026-08-13)

When the user gives a DocMatrix spreadsheet link (main workbook
`1eVqckk3cCWdN06RNGISTP99WSz-aToCmGcNPIIqaicc`) and says "add as new sheet",
CREATE NEW TABS — never modify existing tabs (user: "don't change anything").
Only NDR's google-draas token exists, but that is fine: the DocMatrix
workbook is the shared company workbook, and the user explicitly supplied the
link — that is the go-ahead to write into THIS workbook via google-draas.
Do NOT create files anywhere else in NDR's Drive.

- Tab naming convention (consistent, prefixed): `EC_Summary`, `EC_Sy158`,
  `EC_Sy166`, `EC_Sy167`, `EC_Sy176`, `EC_Sy177`, `EC_Master_AllDocs` (gids
  stored in the reference file).
- Create tabs with one `spreadsheets().batchUpdate` of `addSheet` requests
  (gridProperties rowCount ~1000, columnCount 12).
- Write all tabs with ONE `values().batchUpdate` (valueInputOption "RAW",
  `data` array of {range, values}) — avoids 60/min Sheets API limits.
- Verify: read back each tab and compare row count against source.
- Formatting (new tabs only): freeze header row (frozenRowCount 1), bold
  header with light background via repeatCell, autoResizeDimensions for the
  data columns.
- **Pitfall:** `spreadsheets().get(...).execute()['sheets']` is a list of
  dicts — the title/id live at `sheet['properties']['title']` and
  `sheet['properties']['sheetId']`, NOT at top level (KeyError 'title' on the
  first attempt).
- Delivery channel: send the spreadsheet link + per-tab `?gid=...` links in
  code blocks (Telegram breaks bare URLs). Keep the local xlsx as backup.

## Post-delivery audit: EC docs vs PART_I_DocFurnished (available/not-available)

Prakash commonly follows the tab-append with: "verify and list out all the
documents whether in PartI sheet — those documents are there and not there,
add new tab as available / not available." This compares the EC Master doc
list against the workbook's `PART_I_DocFurnished` tab (the documents-furnished
log) and writes a NEW tab (never touches PART_I itself).

1. Read the FULL `PART_I_DocFurnished!A1:F999`. Header row 2: S.No | Date |
   Document Description | Drive Link | Matched File / Notes | Status. Rows
   ~111–154 are "Added from ext index" — often NO doc number, only a
   description carrying a date (e.g. "Sale Deed dtd 13-05-2011 ... Sy.no.166_3E").
2. Extract candidate doc numbers from each row's description+filename text:
   - `(?:doc|deed|no|number)[\s.:/-]*(\d{3,6})[/\s]*(?:of\s*)?(\d{4})` — "Doc
     5585/1980", "No.1287 of 1999", "doc no.3076/2001"
   - standalone `no XXXX` (no year) — take the year from the Date column
   - `YYYYMMDD...NO XXXX` filename prefixes — year from the leading 8 digits
   - `NNNN/NNNN` pairs — both numbers, year from Date column ("3427/3428 are
     related" → both count)
   - Guard against false positives: survey numbers ("158", "166") and bare
     years ("2023") will be extracted too — harmless since EC doc nos are
     always `NNN/YYYY` and won't collide.
3. Exact match = EC doc no `(num, year)` found in the PART_I lookup. ~60/131
   matched exactly.
4. Date-fuzzy pass for the rest: build date tokens from PART_I text
   (DD-MM-YYYY, DD.MM.YYYY, YYYYMMDD) and compare against the EC txn date.
   **Pitfall — YYYYMMDD tokenizer:** `20240302` is 2024-03-02 (year-month-day,
   `group(1)-group(2)-group(3)`); writing it as year-day-month silently loses
   matches (missed 4350/2024 → row 157 "20240302 SaleDeed ... sy no.166/2B").
5. **Same-date ≠ same-doc.** A date hit that resolves to a DIFFERENT doc
   number is NOT a match: 19344/19346/19356/2023 vs 19345/2023 (same day
   17-10-2023), 4512/1995 vs 4515/1995, 12588/2010 vs 12586/2010, 12669/2023
   vs 12569/2023. Only accept the date+description match when the ext-index
   row describes the same party/type/survey (e.g. 6512/2011 → "Sale Deed dtd
   13-05-2011 ... Prasad Reddy to B.V.Narayana Reddy Sy.no.166_3E"). These
   verified date matches are few (4/131 in the Sevaganapalli set) — keep them
   in an explicit dict, not inferred.
6. New tab `EC_vs_PART_I_Availability` (never rename/edit existing tabs):
   Sl No | Document No. | Type | Transaction date | Appears in ECs | Status
   (AVAILABLE / NOT AVAILABLE) | Match basis | PART_I S.No | PART_I
   Description | PART_I Status, sorted Available-first (year then number),
   plus a summary block at the bottom (total / available / not-available).
   Color-code the Status column: green (available), red (not available).
   Sevaganapalli result: 64 available (60 doc-no + 4 date/desc), 67 not
   available; the big 2025–26 docs (7049/2025 mortgage, 9188/2025 gift) are
   genuinely not furnished yet — report them as not available, don't guess.

## Post-delivery audit #2: EC docs vs Drive folder (available / not available)

Prakash follows the PART_I audit with: "check this folder and identify if not
available documents are in this folder" — pass a Google Drive folder link and
match the NOT-AVAILABLE EC docs against the files inside (the actual scanned
deeds). Write a NEW tab `EC_vs_Drive_Folder` (never touch existing tabs).

1. **Recursively list the folder** with `drive.files().list(q="'<id>' in
   parents")` walking subfolders (pageSize 1000, nextPageToken loop). The
   Sevaganapalli folder had 891 files across root + Legal Opinions / Approval
   1. **Recursively list the folder** with `drive.files().list(q="'<id>' in parents")` walking subfolders (pageSize 1000, nextPageToken loop). The Sevaganapalli folder had 891 files across root + Legal Opinions / Approval documents / JDA documents / firm docs / Pattas & FMBs / "Unique Set (291)".
      - **RE-WALK, don't trust stored counts.** A later session re-walking the SAME folder id found 303 files / 5 subfolders (Approval documents, DRA firm docs, JDA documents, Legal Opinions, SLP firm docs) — the "891" figure had come from an earlier, broader walk (incl. Pattas & FMBs / Unique Set copies that had since been consolidated to 291, see folder-dedup-clean-set). Always report the ACTUAL walk count you just produced; never repeat a stored number for a folder you have not re-walked this session.
   2. **Find the folder by name first.** `name contains 'OASIS'` matches 15 folders (Ranka Oasis variants) — disambiguate with the distinctive word from the user's request (`name contains 'PRINT'` → exactly 1: "Oasis - print" = `1sG1KlY-higI7vhoafHmyarS_qIWkspEW`), then verify via parents. Never assume the first OASIS hit is the target.
   3. **Extract doc numbers from FILENAMES** (same regex family as PART_I, plus):
      - `(?:doc|deed|no|number)[\s.:/#\-_]*(\\d{3,6})[/\-_](?:of\s*)?(19|20)\\d{2}`
      - `NO XXXX (YYYY)` / `NO XXXX_YYYY` (year in parens or underscore)
      - `YYYYMMDD ... NO XXXX` filename prefixes → year from leading digits
      - `NO XXXX dtd|dated YYYY`
      - **Filename separators vary wildly — a strict `NNNN/YYYY` regex misses most.** Real forms seen in the Oasis-print folder: `5268_1980`, `6921-2004`, "No.2334/1981", "No.1287 of 1999", "No.2542 of 2006", `2597_1995`, `22229_2023`, "No 21785(2024)", "no.3320/16" (**2-digit year** = 3320/2016), "16102023 Sale deed 21201" (**date-prefix carries the year**, no year token after the number), "2025 Gift Deed No 9196" (**number and year far apart, no separator**), "No 12988 0f 2017" (typo '0f'). Robust matcher: extract ALL (num, year) pairs with separator/word forms; then a fallback that pairs a standalone number token with a standalone year token anywhere in the name ("exactly one big number + exactly one year" heuristic). Then REVIEW the full filename dump manually — automated matchers will still miss date-prefix years like 21201/2023.
      - **Protect slashes inside filenames** — replace `/` with ` / ` before regexing, or `434/1976.pdf` names parse wrong.
   4. **Same-date ≠ same-doc applies here too.** Drive filenames share dates with different docs: 19345/2023 (cancellation) vs 19344/19346/19356/2023, 4515/1995 vs 4512/1995, 12569/2023 POA vs 12669/2023 release. Only accept when doc number (or unambiguous number+type like "Gift Deed No 9188") matches.
   5. **"In the folder" vs "in Drive somewhere" — check parents.** A drive-wide `name contains '<number>'` search finds files that live in OTHER folders (ALL Legal Files, Saveganapalli Legal Docs, Gifts Deeds - Govt, Certified Copies Shared, Ranka Oasis - Banking documents). When the user asks "is this in folder X", a file found drive-wide but whose `files().get(parents)` points elsewhere is NOT in X — report it as "in Drive but not in this folder" (434/1976 → ALL Legal Files; 1706/1986 settlement → ALL Legal Files / Saveganapalli Legal Docs, while the folder only has the 1706/1980 sale deed — same number, different year AND different deed).
   6. **Flag year-label mismatches, don't claim a match.** Drive file "Copy of 2026 Gift Deed No 9188 ..." vs EC doc 9188/2025: the number matches but the year label differs — report "present but titled 2026; EC says 9188/2025" rather than a clean YES.
   7. New tab columns: Sl No | Document No. | Type | Transaction date | Appears
      in ECs | In Drive Folder? (YES/NO) | Drive File Name | Drive Link
      (`https://drive.google.com/file/d/<id>/view`). Color YES green / NO red.
      Sevaganapalli result: 12/67 found in folder (incl. 5268/1980, 2334/1981,
      1505/1977, 1702/1991, 2110/1998, 2916/2015, 7963/2025 JDA, 8004/2013,
      6157/6158/2025 JDA+GPA, 9188/2025, 9196/2025 in Approval documents);
      55 genuinely absent. A follow-up "check these 52 doc numbers" run found 35
      of 52 in the same folder (the rest split: 2 elsewhere in Drive, 15 missing
      entirely) — report the three buckets, not just yes/no.

## Per-sub-survey separation (Prakash: "separate transactions based on each survey no, new sheet")

After the master/audit tabs, Prakash lists specific sub-survey numbers (e.g. the
19 covered by the 9188/2025 gift deed: 158/1C9A, 158/1C9B, 166/1, 166/2B2,
166/3A–F, 166/3E1–E2, 167/2C, 167/2D, 167/1G, 168/1B, 176/1B2D, 176/2B4A,
177/1A1A, 177/1A1B) and asks to separate ALL transactions per sub-number, each
with its LAND EXTENT, as a new tab.

- Tab: `EC_By_Survey_SubNo`. Layout: a summary block at top (Sl No | Survey No
  | Land Extent | Owner/Notes | No. of Transactions), then 19 colored section
  headers (survey + extent), each followed by its own transaction table
  (Sl No, Doc No, Type, Date, From, To, Consideration, ECs) sorted
  chronologically. Never modify existing tabs.
- **Matching logic — parent roll-up.** A doc matches a target sub-number by
  EXACT survey match OR a parent covering the sub-division (177/1 docs roll
  into 177/1A1A; 158/1 docs roll into both 158/1C9A and 158/1C9B). This is
  the reverse of the master-tab grouping rule and is what makes old
  whole-survey docs (434/1976 mortgage on 158/1) appear under every child
  sub-number. Without roll-up, old docs vanish from the sub-number tables.
- **Extent sources, in order.** (1) DocMatrix per-subnumber tab headers
  (e.g. `SURVEY: 158/1C9A | 0.25 Ac | PATTA 2058`), (2) the 9188/2025 gift
  deed survey-no–extent schedule in the EC text for sub-numbers without a
  tab, (3) cross-check against tab values (166/3A: 56.00 ares = 1.38 Ac).
  Sub-numbers that are road/local-body-area portions (166/2B2 — "Road No.4 &
  Park 1 come under 166/2B2 + 166/3D + 166/3F") have NO standalone extent —
  report them as Road/LBA portion, don't invent a figure.
- Verification: total transaction rows across sections should be a sensible
  partition of the master doc list; each section's count reported in the
  summary block. Deliver gid link in a code block (Telegram breaks URLs).

## Tamil → English transliteration (Prakash: "convert the Tamil language to English in all EC sheets")

EC party names, institutional names, and EC register abbreviations are in
Tamil script. After delivery, Prakash asks to convert them to English in all
EC tabs. Technique that worked (580 cells, 0 leftover Tamil):

1. **Extract all unique Tamil runs** (regex `[\u0B80-\u0BFF]+` over every
   cell) — Sevaganapalli had 270 distinct runs; most are Reddy-family names
   composed of reusable tokens (ரெட்டி→Reddy, ராமப்பா→Ramappa,
   கிருஷ்ணா→Krishna, வெங்கடேச→Venkatesa, லக்ஷ்மண→Lakshmana, ...).
2. **Abbreviation PRE-PASS before the run map** — the EC register
   abbreviations contain ASCII punctuation (( முத. ), (இ.க.), த+கா, த.கா)
   which splits Tamil runs at the dots/pluses. Handle them FIRST with regex
   on the full cell text:
   - `(முத.)` → `(First party)` — executant/principal marker
   - `(முக.)` → `(Agent)` — முகவர்
   - `(இ.க.)` → `(Natural Guardian)` — இயற்கை காவலர் (guardian of minors)
   - `த+கா` / `த.கா` → `Father & Guardian` (guardian markers; also handle
     the plain no-parens form so "வெங்கடரமணப்பா த+கா" doesn't become
     "Father & Guardian+Guardian")
   - `(மைனர்)` → `(minor)`, `(கார்டியன்)` → `(Guardian)`,
     `(பவர்ஏஐண்ட்)` → `(Power Agent)`, `(ஏஜண்டு)` → `(Agent)`
   - `(எ)` / `(அ)` → `(alias)` — "லக்ஷ்மம்மா (எ) அம்மையம்மா"
   - `மேற்படி நபர்கள்` → `the above persons`
   - `ரூ.` → `Rs.` (all considerations)
   - `என்கிற` → `alias`
3. **Run-level map with longest-first matching** — sort keys by length desc;
   exact full-run match first, then substring for keys len≥2, then single
   Tamil chars ONLY as exact leftover fallback. **Do NOT single-char-replace
   inside unmapped runs** — missing compound keys cause garbage (missing
   `கொத்தப்பள்ளி` mangled the co-op name into
   "GuardianொFather&Guardian..."; missing `நாரயணரெட்டி` produced
   "NAரயணReddy" because நா→NA fired inside it).
4. **Phrase keys with spaces** applied before run matching: பலவித நோக்க →
   Multi-purpose, கோ ஆப்ரேடிவ் → Co-operative.
5. Institutional names worth pre-mapping: அரசு (தமிழ் நாடு) → Government
   (Tamil Nadu); ஒசூர் கூட்டுறவு நிலவள வங்கி லிட் → Hosur Co-operative Land
   Development Bank Ltd; கொத்தப்பள்ளி ... கூட்டுறவு ... சங்கம் → Kothapalli
   ... Co-operative ... Society; கிளவர் எஸ்டேட் (பி) லிட் → Clover Estate
   (P) Ltd.
6. Apply to the EC tabs in place via `values().batchUpdate` (RAW), then
   read back and assert 0 cells match `[\u0B80-\u0BFF]`. Keep doc numbers /
   dates / surveys untouched. Full 270-run glossary + abbreviations in
   `references/tamil-transliteration-glossary.md`.

