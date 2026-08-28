# TN EC → Per-Survey Transaction Tables → DocMatrix (Sevaganapalli pattern)

Complete pipeline for batch Tamil Nadu Registration Dept EC PDFs (one EC per survey
number, e.g. Sy 158/166/167/176/177 from Hozur SRO → Bagalur SRO, search period
1975–2026) into verified transaction tables, English transliteration, and Google
Sheets tabs in the DRA DocMatrix workbook. Verified Aug 2026 on 5 ECs: 170 entries,
131 unique registered documents.

## 1. Text extraction — pdftotext -bbox, NOT pdfplumber

- **pdfplumber garbles Tamil** (font encoding). `pdftotext -bbox` renders Tamil
  correctly AND gives word coordinates. Parser input = bbox XML.
- Column classification by **x-position** (pdftotext -bbox units), not character
  columns: executant ≈ x=414, claimant ≈ x=546. Compact-format entries shift
  character columns but x-positions are stable.
- Line grouping: **discrete y-bucket clustering** (coarse enough that same-row
  words land in one bucket). Running-average clustering merges everything; too-fine
  buckets split rows. Page tracking: `<page width=...>` has NO `number` attribute —
  track page transitions yourself.
- Entry-start detection: keep a Sr-line candidate ONLY if the following block
  contains a doc no + a "Consideration Value" line. Look-ahead-only detection
  backfires (grabs boundary text). Also: first executant can sit on the line ABOVE
  the Sr marker (page-break quirk) — look one line above.
- Survey list continuation: accept continuation tokens ONLY if they contain `/`.
  **Hard stop at boundary-description text (எல்லை விபரங்கள்)** — neighboring-plot
  refs (e.g. 176/285, 176/2B4B) are boundaries, NOT transaction surveys.
  Old-format Tamil label "புல எண்" can sit on its own line above the number.
- Consideration: stop scan at Schedule lines, take only the first real value line.
- Name cleanup: strip standalone page-number artifacts (e.g. standalone "35") from
  the name zone; page-number artifacts bleed into names at page breaks.
- **Verification is footer-count based**: EC footer "Number of Entries" is
  authoritative (158:52, 166:35, 167:15, 176:29, 177:39 = 170). Filename counts
  mislead.

## 2. Master doc table (dedupe across ECs)

- Same registered doc appears in multiple ECs (its schedule lists many surveys).
  Master table = each unique doc ONCE with all survey nos grouped in one column +
  "Appears in ECs" column. 170 entries → 131 unique docs, 29 docs in 2+ ECs.
- Multi-EC docs (Aug 2026 set): 9188/2025 Gift deed (DRA Realty → TN Governor/panchayat,
  all 5 ECs, 19 surveys), 22229/2023 Partition (4 ECs), 7049/2025 Mortgage
  (Sevaganapalli Land Partners → lenders), 5268/1980, 6594/1980, 21201/2023 (3 ECs each).

## 3. Tamil → English transliteration (party names + EC boilerplate)

- **Run-level dictionary, longest-match-first**: map contiguous Tamil runs to
  English. Exact full-run match first, then multi-char keys (len≥2), then leftover
  single chars only if they are exact known single-char keys.
- **Abbreviation pre-pass BEFORE the run regex** — Tamil runs split at ASCII
  separators (parens, dots, `+`, `&`), so handle whole patterns first:
  - (முத.) / (முதல்வர்) → (First party) — i.e. executant/principal
  - (முக.) / (முகவர்) / (ஏஜண்டு) → (Agent)
  - (இ.க.) → (Natural Guardian)
  - (த+கா) / (த.கா) / (த&கா) / (த&amp;கா) → (Father & Guardian) — also PLAIN (no
    parens) forms: `த+கா` alone at line end → "Father & Guardian" (regex-paren-only
    misses it and produces "Father & Guardian+Guardian")
  - (மைனர்)/(மைனர்கள்) → (minor)/(minors); (கார்டியன்) → (Guardian);
    (பவர்ஏஐண்ட்) → (Power Agent); (எ)/(அ) → (alias); என்கிற → alias
  - மேற்படி நபர்கள் → the above persons; ரூ. → Rs.
- **Pitfalls (all hit in practice):**
  - Missing compound keys let single-char fallbacks mangle long words
    (கொத்தப்பள்ளி → garbage). Always add full compound words first.
  - Unicode variants of the same name are separate keys: நாரயணரெட்டி vs
    நாராயணரெட்டி (ய vs யா — one has ஆ, one doesn't) — add BOTH.
  - Phrase keys with spaces (பலவித நோக்க → Multi-purpose, கோ ஆப்ரேடிவ் →
    Co-operative) applied separately before the run regex.
  - Company/body names: அரசு (தமிழ் நாடு) → Government (Tamil Nadu); ஒசூர்
    கூட்டுறவு நிலவள வங்கி லிட் → Hosur Co-operative Land Development Bank Ltd;
    கிளவர் எஸ்டேட் → Clover Estate; கொத்தப்பள்ளி ... சங்கம் → Kothapalli ...
    Society.
- After conversion, read back the sheet and assert 0 Tamil chars remain.

## 4. DocMatrix workbook integration (1eVqckk3cCWdN06RNGISTP99WSz-aToCmGcNPIIqaicc)

- **User rule (Prakash): ADD NEW TABS ONLY — NEVER modify/edit existing tabs.**
  He said verbatim "Add as new sheet don't change anything". New data always lands
  in fresh tabs; existing tabs stay byte-identical.
- Tab naming used: EC_Summary, EC_Sy158/166/167/176/177 (per-survey txn tables),
  EC_Master_AllDocs (131 unique docs), EC_vs_PART_I_Availability, EC_vs_Drive_Folder,
  EC_By_Survey_SubNo.
- Per-survey txn table columns: Sl No | Sy No | Sub-number(s) | Type of transaction |
  Transaction date | From party (Executants) | To party (Claimants) | Document No. |
  Other Sy Nos in same doc (amber) | Consideration | PR Number. Chronological order.
- **Land extents per sub-number** come from TWO places:
  1. Existing `Sy_<no>_<sub>` tabs — row 1 header `SURVEY: X | N Ac | PATTA n |
     OWNER: Y | status` (extent + patta + owner in one cell).
  2. The 9188/2025 gift deed schedule (Survey No–Extent lines + Dry.Ext per survey
     in remarks) — authoritative for sub-numbers without their own tab
     (e.g. 166/1=35.0c, 167/1G=7.0c, 168/1B=53.0c, 177/1A1A=2.5c). Cross-check the
     two; 166/2B2 is road/LBA only (no standalone extent).
- **Availability cross-check vs PART_I_DocFurnished** (S.No|Date|Description|Link|
  Matched File|Status, ~157 rows): extract doc numbers from description+file+date
  via regex `(?:doc|deed|no|number)[\s.:/-]*(\d{3,6})...(\d{4})` + YYYYMMDD date
  tokens. Ext-index rows often lack doc numbers → **date+description fuzzy match**.
  ⚠️ Same-date ≠ same doc: 19344/19346/19356/2023 vs 19345/2023, 4512/1995 vs
  4515/1995, 12669/2023 release vs 12569/2023 GPA — verify party/type before
  declaring a match.
- **Drive-folder check**: recursive file list (paginate 1000/page), doc-no regex on
  filenames; number-only fallback verified against doc type/context (e.g. "Gift
  Deed No 9188" file = 9188/2025 gift). Read-only — never rename/move in the source
  folder.
- **Per-sub-number separation (EC_By_Survey_SubNo)**: parent-prefix rule — a doc
  whose survey list contains X covers every sub-number starting with X + "/"
  (167/1 covers 167/1G; 177/1 covers 177/1A1A; 166/2B covers 166/2B2). Exact match
  OR `target.startswith(doc_survey)`.

## 5. Sheets API notes

- `values().batchUpdate` body: `{"valueInputOption": "RAW", "data": [{range, values}]}`.
- Create tabs via `spreadsheets().batchUpdate` addSheet; format via repeatCell +
  autoResizeDimensions; get sheetId via `spreadsheets().get(fields='sheets.properties')`
  → `p['properties']['sheetId']` (properties is nested).
- Rate limit 60/min; on 429 wait 60s.
- Row-count verification: read back each tab after write and compare to source.

## Key data (Aug 2026 Sevaganapalli set)

- ECs: 158 (52), 166 (35), 167 (15), 176 (29), 177 (39). SRO lineage Hozur → Bagalur.
- 9188/2025 gift deed covers: 158/1C9A, 158/1C9B, 166/1, 166/2B2, 166/3A–3F,
  167/1G, 167/2C, 167/2D, 168/1B, 176/1B2D, 176/2B4A, 177/1A1A, 177/1A1B.
