# Sevaganapalli EC Set (2026-08-13) — Worked Example

Five TN REGINET ECs for Sevaganapalli village (Hozur SRO → Bagalur SRO),
filed one per survey number. Prakash's request: "Verify all the transactions
and generate a spreadsheet for each survey nos" with a transactions table and
the rule "if same document has multiple survey nos, show under the document no
which survey nos are there to be put together to avoid repeated entries."

## Files & expected entry counts (validate against footer)

| EC | Survey | Entries (footer) | Search period |
|----|--------|------------------|---------------|
| EC 158.pdf | 158 | 52 | 01-Aug-1975 to 12-Aug-2026 |
| EC 166.pdf | 166 | 35 | 01-Apr-1975 to 12-Aug-2026 |
| EC 167.pdf | 167 | 15 | 01-Apr-1975 to 12-Aug-2026 |
| EC 176.pdf | 176 | 29 | 01-Aug-1975 to 12-Aug-2026 |
| EC 177.pdf | 177 | 39 | 01-Apr-1975 to 12-Aug-2026 |

Data availability spans two SROs: Hozur SRO up to 16-Feb-2025, then Bagalur
SRO from 17-Feb-2025.

## Result

131 unique registered documents (after dedup by doc no across the 5 ECs,
unioning each doc's survey list across the ECs it appears in — per-EC lists
of the same doc differ slightly due to page-break truncation; e.g. 9188/2025
per-EC survey counts were 11–18 but the union is 19).
Multiple-survey documents (why the master/grouping tab matters):

- 9188/2025 Gift deed (M/S DRA REALTY PVT.LTD → THE GOVERNOR / panchayat,
  layout roads+gift) — appears in ALL 5 ECs; covers 158/1C9A, 158/1C9B,
  166/1, 166/2B2, 166/3A–F, 167/1G, 167/2C–D, 168/1B, 176/1B2D, 176/2B4A,
  177/1A1A, 177/1A1B, ...
- 22229/2023 Partition deed — 4 ECs (158, 166, 167, 176)
- 7049/2025 Mortgage (M/S SEVAGANAPALLI LAND PARTNERS → 9 lenders) — 3 ECs
- 5268/1980, 6594/1980, 21201/2023 Sale/Partition — 3 ECs
- 4292/2024 Exchange Deed (DRA REALTY ↔ VENKATAMMA) — ECs 176, 177
- 2931/2026 Release deed (NARAYANA REDDY → VENKATESH REDDY) — ECs 176, 177

## DRA-relevant modern chain (Sevaganapalli Land Partners / DRA Realty)

- 21201/2023 Sale deed (J. VENKATASWAMI REDDY → M/S.SEVAGANAPALLI LAND
  PARTNERS)
- 22229/2023 Partition deed (Yella Reddy family)
- 4292/2024 Exchange Deed (DRA REALTY ↔ VENKATAMMA)
- 4350/2024 Sale deed (→ SEVAGANAPALLI LAND PARTNERS)
- 7049/2025 Mortgage (LAND PARTNERS, M.D. Nishant Ranka → lenders incl.
  Prathyusha Vuppala, Bhagavan Krishna Paduchuri, Ajay Singh Bist, ...)
- 7963/2025 Others (RAMESH REDDY → DRA REALTY PRIVATE LIMITED)
- 9188/2025 Gift deed (DRA REALTY → Governor/panchayat — roads, LBA, parks)
- 2931/2026 Release deed (NARAYANA REDDY → VENKATESH REDDY)

## Parser notes specific to this set

- Old-format entries (1976–2009ish) put the Sr No, dates, doc no, nature,
  and numbered parties on separate rows; compact entries (e.g. EC158 #27
  8713/2009, EC176 #29 2931/2026) pack everything on one line — the x0 zones
  stay identical, only the -layout character columns shift. That is why
  -bbox (x-coordinates) is required.
- The first executant can appear on the line ABOVE the Sr marker (page-break
  baseline quirk, e.g. EC167 entry 2 = 6594/1980, executant 1 எம்.
  நாராயணரெட்டி).
- Page numbers can bleed into the executant zone as a stray standalone number
  (e.g. "35" inside EC158 entry 27's executant list) — strip trailing
  standalone 1-3 digit tokens from names.
- Old-format survey lists wrap across pages with continuation lines that have
  only slash tokens in the right zone; the modern gift deed puts
  "SURVEY NUMBER: 158/1C9A, Dry.Ext..." inside schedule remarks.

## Pitfalls hit during the 2026-08-13 re-parse (fixes in parse_tn_ec.py)

- **Boundary-section pollution (biggest bug):** the first pass harvested
  neighbor-plot refs from the எல்லை விபரங்கள் / Boundary Details block
  (176/285, 176/2B4B, 66/2B2, 165, 159, 176/1B2C, 177/1A2, 158/1C8, ...)
  into the survey lists. The fix is a HARD STOP: break the schedule scan the
  moment a line contains எல்லை or Boundary. EC158 #39 7733/2023 also leaked
  "385" (an electricity connection number) and extent values from remarks.
- **Old-format continuation truncation:** requiring left zone (x<400) blank
  missed continuation lines where the LEFT zone carries the Village &
  Street/Property Type label on the same visual row (e.g. 6594/1980 lost
  102/9, 103/3, 104, 111, 116/2, 150/1, 152/7, 155/1, 158/1B, 16/4, 16/5,
  39). Fix: evaluate the RIGHT zone only and require the line to be a pure
  survey list.
- **Modern continuation leaks extent values:** the modern Survey No-Extent
  list wraps across lines; the OLD-format continuation rule must be gated
  `not modern`, otherwise "50.0 CENTS; 158/1C1 - 69.0 CENTS" lines leak 50,
  69, 19, 54... as fake surveys (hit on 21201/2023 and 12669/2023).
- **Extent wrap drops surveys:** 21201/2023 lost 158/1A1B because its
  "- 50.0 CENTS" was on the next physical line — scan all NN/NNX tokens on
  the Survey No-Extent line rather than requiring the extent suffix inline.
- **`continue` skips the SURVEY NUMBER remark rule:** the modern continuation
  used `continue` when the right zone had a keyword, which skipped the bottom
  `SURVEY NUMBER:` rule and dropped 177/1A1A from 9188/2025 in every EC.
- **Noise filter:** drop single-digit standalone, zero-padding, and year-like
  tokens (`\d{1,4}/\d{4}` like "1/2025" from ROC numbers) — but KEEP 2-digit
  standalone values (39, 96, 104, 111, 137, 182, 183, 184, 185 are valid
  whole surveys in Sevaganapalli).
- **Validation that caught it all:** noise-token regex sweep over the parsed
  JSON (standalone 1-2 digit / year-like) plus footer entry-count match
  (52/35/15/29/39) and no-duplicate-doc check in the master tab.

## Delivery record — DocMatrix workbook (2026-08-13)

Prakash asked to add the workbook as new tabs in the existing DocMatrix
spreadsheet (main workbook `1eVqckk3cCWdN06RNGISTP99WSz-aToCmGcNPIIqaicc`,
gid=1065886649 was just the tab he was viewing — PART_I_DocFurnished). New
tabs created via addSheet, existing tabs untouched:

| Tab | gid |
|-----|-----|
| EC_Summary | 1825839584 |
| EC_Sy158 | 1532847956 |
| EC_Sy166 | 1305634569 |
| EC_Sy167 | 1596932796 |
| EC_Sy176 | 140789374 |
| EC_Sy177 | 1761265850 |
| EC_Master_AllDocs | 1516818009 |

3,173 cells written in one values().batchUpdate; read-back verified row
counts (18/53/36/16/30/40/132). Formatting: frozen header, bold + light
background, autosized columns. Local xlsx backup kept at
`/tmp/Sevaganapalli_EC_Transactions_158_166_167_176_177.xlsx`.

## PART_I availability audit (2026-08-13, second user request)

Prakash then asked: verify which of the EC docs are in the PART_I_DocFurnished
sheet — add a new tab as available / not available. Result tab
`EC_vs_PART_I_Availability` (gid=1955370540), 1,327 cells, header frozen,
status col color-coded (green/red).

**Result: 64 AVAILABLE / 67 NOT AVAILABLE (of 131 unique docs).**
- 60 exact doc-no matches (regex extraction from PART_I desc+filename).
- 4 date+description matches (ext-index rows that lack doc numbers):
  - 6512/2011 → PART_I row 147 "Sale Deed dtd 13-05-2011 ... Prasad Reddy to
    B.V.Narayana Reddy - Sy.no.166_3E"
  - 9656/2023 → row 140 "Sale agmt dtd 26-05-2023 b/w Radha & Kishore
    Kumar.V - Sy.no.158(1A1)"
  - 12098/2023 → row 144 "GPA dtd 01-07-2023 b/w Venkataswami & others to
    Pavan Kumar - Sy.no.166_3F"
  - 4350/2024 → row 157 "20240302 SaleDeed for sy no.166/2B" (caught only
    after fixing the YYYYMMDD tokenizer to year-month-day)
- NOT AVAILABLE per EC: 158→17, 166→13, 167→5, 176→19, 177→31. Includes the
  big recent docs not yet furnished: 7049/2025 mortgage, 9188/2025 gift
  (all 5 ECs), 9196/2025, 5804/2026, 2931/2026, 6157/6158/2025, 7963/2025.
- False-positive traps (same-date, different doc — NOT matches): 19344/2023,
  19346/2023, 19356/2023 vs 19345/2023 (all 17-10-2023); 4512/1995 vs
  4515/1995; 12588/2010 vs 12586/2010; 12669/2023 vs 12569/2023 (release vs
  POA both 07-07-2023).

## Drive-folder availability audit (2026-08-13, third user request)

Prakash then passed a Drive folder
(`1sG1KlY-higI7vhoafHmyarS_qIWkspEW`) and asked to check whether the 67
NOT-AVAILABLE docs are inside. Recursive walk found 891 files (root + Legal
Opinions 6 / Approval documents 5 / JDA documents 4 / firm docs 14 / Pattas
& FMBs 161 / "Unique Set (291)" 291 + copies). Result tab
`EC_vs_Drive_Folder` (gid=1529603772), 544 cells, YES green / NO red.

**Result: 12 of the 67 are in the folder, 55 are not.**

| Doc | Where |
|---|---|
| 5268/1980 Partition | Unique Set (291) — 3 copies incl. EC for Sy 167 |
| 2334/1981 Settlement | Unique Set + root |
| 1505/1977 Settlement | Unique Set (Sy 166/3) |
| 1702/1991 Sale deed | Unique Set (Sy 164/1A) |
| 2110/1998 Agreement | Unique Set (Sy 166/3) |
| 2916/2015 Gift settlement | Unique Set |
| 7963/2025 JDA | JDA documents (DRA Realty × Ramesh Reddy) |
| 8004/2013 Deed of Release | Unique Set |
| 6157/2025 JDA | JDA documents (DRA Realty × K Harish) |
| 6158/2025 GPA | JDA documents (Harish JDA) |
| 9188/2025 Gift deed | Approval documents (TN Govt road related) |
| 9196/2025 Gift deed | Approval documents (TN Electricity Board) |

Number-only filename matches that were FALSE (same number, different doc):
"Partition Deed ... Document No.1287 of 1999" is NOT 1287/1995 (different
year AND type — that file is the 1999 partition, EC doc 1287/1995 is a sale
deed). Same-date filenames that were FALSE: 19345/2023 cancellation vs
19344/19346/19356/2023; 4515/1995 vs 4512/1995; 12569/2023 GPA vs 12669/2023
release deed.

## Per-sub-survey separation with extents (2026-08-13, fifth user request)

Prakash listed 19 sub-survey numbers (exactly the 9188/2025 gift-deed
coverage: 158/1C9A, 158/1C9B, 166/1, 166/2B2, 166/3A–F, 166/3E1, 166/3E2,
167/2C, 167/2D, 167/1G, 168/1B, 176/1B2D, 176/2B4A, 177/1A1A, 177/1A1B) and
asked: "separate all the transactions based on each survey nos above — NEW
SHEET, with each survey no land extent." Result tab `EC_By_Survey_SubNo`
(gid=88001984), 1,776 cells: summary block (19 rows: survey | extent |
owner/notes | txn count) + 19 colored section headers each with its own
chronological transaction table.

- **Extents** from two sources, cross-checked: (1) DocMatrix per-subnumber
  tab headers (`SURVEY: 158/1C9A | 0.25 Ac | PATTA 2058`) for 14 surveys;
  (2) the 9188/2025 gift deed Survey No–Extent schedule in the EC text for
  the 5 without tabs (166/1 = 35 cents, 167/1G = 7 cents, 168/1B = 53 cents,
  177/1A1A = 2.5 cents). 166/2B2 = Road No.4 & Park 1 portion under
  166/2B2+166/3D+166/3F — no standalone extent (report as Road/LBA).
- **Parent roll-up** made old whole-survey docs appear under children:
  434/1976 mortgage on 158/1 → listed under BOTH 158/1C9A and 158/1C9B.
- Txn counts per section: 158/1C9A=13, 158/1C9B=17, 166/1=5, 166/2B2=7,
  166/3A=9, 3B=9, 3C=10, 3D=10, 3E1=14, 3E2=13, 3F=12, 167/2C=5, 167/2D=7,
  167/1G=5, 168/1B=4, 176/1B2D=14, 176/2B4A=9, 177/1A1A=13, 177/1A1B=12.

## Oasis-print folder re-check (2026-08-13, sixth user request)

Prakash pasted 52 doc numbers ("434/1976 ... 5804/2026") and asked "does this
documents in the OASIS - PRINT folder". Folder resolved by name search:
`name contains 'PRINT'` → exactly 1 hit = "Oasis - print"
(`1sG1KlY-higI7vhoafHmyarS_qIWkspEW`; `name contains 'OASIS'` matches 15
folders — disambiguate with the distinctive word).

**RE-WALK found 303 files / 5 subfolders (Approval documents, DRA Realty
firm docs, JDA documents, Legal Opinions, SLP firm docs) — NOT the 891 from
the earlier audit.** The 891 figure had included Pattas & FMBs / Unique Set
copies that were consolidated to 291 in a prior cleanup (see
folder-dedup-clean-set); the live tree is 303.

Result: **35 of 52 in the folder, 2 elsewhere in Drive, 15 missing entirely.**
- Strict `NNNN/YYYY` regex matched only 22 — filenames use `_` (`5268_1980`,
  `2597_1995`, `22229_2023`), `-` (`6921-2004`), "No.1287 of 1999",
  "No.2542 of 2006", "No 21785(2024)", **2-digit year** `3320/16`, and
  **date-prefix year** `16102023 Sale deed 21201` (= 21201/2023).
  "2025 Gift Deed No 9196" = number + year far apart (heuristic: exactly one
  big number + exactly one year token in the name pairs them). "No 12988 0f
  2017" typo ('0f'). Loose token match (num AND year both present anywhere)
  still missed 21201/2023 and 9196/2025 — manual filename dump review needed.
- **Parents check split the misses:** 434/1976 → "ALL Legal Files" +
  "(Newly added Documents Dec 20 2024)"; 1706/1986 settlement → "ALL Legal
  Files" + "Saveganapalli Legal Docs" (the folder only has the 1706/1980
  sale deed — same number, DIFFERENT year AND deed).
- **Year-label mismatch:** "Copy of 2026 Gift Deed No 9188 DRA Realty SLP &
  TN Govt Road Related.pdf" in Approval documents vs EC doc 9188/2025 —
  reported as present-but-titled-2026, not a clean YES.
- Missing entirely (15): 440/2005, 5865/2005, 6053/2005, 6802/2005,
  13334/2008, 8713/2009, 12586/2010, 12588/2010, 15992/2012, 13063/2021,
  9656/2023, 19344/2023, 19356/2023, 7049/2025, 5804/2026.

## Tamil → English conversion (2026-08-13, fourth user request)

Prakash: "convert the Tamil language to English of the names and others in
all EC sheets." Applied in place to the 6 EC tabs (EC_Sy158/166/167/176/177 +
EC_Master_AllDocs); 580 cells converted, 0 Tamil chars remaining after
read-back verification. Doc numbers / dates / surveys untouched.

- 226 unique Tamil cells → 270 unique Tamil runs; transliteration map built
  run-level with longest-first matching + abbreviation pre-pass (see
  `tamil-transliteration-glossary.md`).
- Notable conversions: மேற்படி நபர்கள் → the above persons (many partition
  entries); அரசு (தமிழ் நாடு) → Government (Tamil Nadu); Kothapalli
  co-operative society names (2 spellings); Hosur Co-operative Land
  Development Bank Ltd; (முத.) → (First party), (முக.) → (Agent),
  (இ.க.) → (Natural Guardian), த+கா → Father & Guardian; ரூ. → Rs.
- 2 leftover cells fixed by adding the missing compound key
  `நாரயணரெட்டி` (the ஆ-less variant) — the single-char நா→NA fallback had
  mangled it to "NAரயணReddy".


