# Allalsandra / Ranka North Star — death cert & succession discovery (Aug 2026)

NDR asked: find the death certificate of the mother of V. Swaminathan (one of
the Ranka North Star / Allalsandra, Sy No 14/1 landowners). Discovery path and
records map below.

## ANSWER (verified 2026-08-21)

The mother is **Smt. V. Rangamal (Rangammel)**, wife of Late Sri.
R. Venkataraman, ~91 y/o at JDA signing, resident of Mumbai — "V Rangamal" in
the GPA rows, "V. Rangammel" in the JDA. Connection to Swaminathan (mother →
son):
- Will 56/2009-2010 dated 13.11.2009 "Between v Rangamal in favor of
  Swaminathan" (index Non-Avail row 124)
- GPA 132/2009-10 dated 13.11.2009 BY v Rangamal in favor of V Swaminathan
  (index Non-Avail row 125)
- Death certificate dated **01.04.2019** — index row 244 (main index,
  File 6, Anup-Shah avail status NO) and Non-Avail row 129 ("V Ranggamal")

OTHER death certs in the same index (do not confuse):
- Melada Hanumaiah (row 245, File 6, avail YES — different owner)
- Nagalakshmi, 18.02.2007 (row 279 / Non-Avail row 149, File 8, avail NO)

STATUS: the Rangamal death cert is a PHYSICAL document in binder File 6.
There is NO scan on Drive and NO fullText hit. It is flagged "NO" in the Anup
Shah avail column = not in the scanned opinion set. Recommended action:
pull File 6, scan, upload, close the gap.

## Source of truth: the index spreadsheet

**Sheet:** `20250203 Allalsandra Northstar Legal Docs Verified In MDR Possession`
**ID:** `1mmTJJiBTaLUdKXte9j-VnRuSu1uL8YchjV3M8ZP_u3M`

Tabs (5):
1. `Balance Documents` — 26 rows, financial + basic approval checklist (NOT the doc index)
2. `Noc Docs verified` — 9 rows
3. `Allalsandra Index inc MDR & Anup Doc's` — **312 rows × 9 cols** = the master index
   Columns: Sl no | Doctype | Doc No | Date | No of Pages | Remarks |
   File NO | ANUP SHAH (AVAIL STATUS) | Final Verification
4. `Non Avail Doc in Anup shah Opinion` — 176 rows × 10 cols, one row per doc
   Columns: (blank) | Doctype | Doc No | Date | Description | Site N0 |
   No of Pages | Remarks | File NO
5. `Avail in Anupshah opinion` — 130 rows × 7 cols

Read with: `build_service("sheets","v4")` → `spreadsheets().values().get(
spreadsheetId=..., range=f"{tab}")`. Run from execute_code or
`HERMES_SESSION_USER_ID=7449813913` prefixed terminal.

## CRITICAL — NDR correction (2026-08-21): always cite the exact row

When asked "which index / which row", I initially answered from memory
("File 4 / File 5 in the index") WITHOUT having read the spreadsheet. NDR
called it out verbatim: "where did you get this information from which index
are we referring to and which row of the index". 

RULE: **Never state index contents without a live read of the sheet. Every**
**claim about a binder file (File N) or a doc reference must cite the exact**
**tab + row number that was read.** If you haven't read it, say so and read it.

## Family / landowner structure (Allalsandra Sy 14/1, sites 1-10)

JDA dated 07.02.2014, parties (owners) — representative of V. Swaminathan's
family group (Swaminathan served as GPA holder for most):
1. Smt. R. Geeta Swaminathan, w/o V. Swaminathan — Site 1
2. Smt. Kankshita (Kanishtha) Swaminathan, d/o V. Swaminathan — Sites 6 & 10
3. Smt. V. Rangamal (Rangammel), w/o Late R. Venkataraman — the MOTHER
4. A. S. Vaidyanathan — Site 2
5. Smt. Lakshmi Vaidyanathan — Site 3
6. Sri. Sreeraman Vaidyanathan — Site 5
7. Sunder Padmanabhan — Site 4

NOTE — discrepancy flagged to NDR: JDA text lists Geeta as "wife of
V. Swaminathan" while NDR says Geeta is the DAUGHTER and Rukmini was the
wife. Unresolved; verify against deeds before any title reliance.

## Alias references (ASK NDR to disambiguate)

- `ALN/NAY/SR/60-2016-17` + `61-2016-17` = actually `LLN(NY)SR 60/16-17` /
  `61/16-17` on the index (Bangalore DC letterhead read). Also written
  `ALN(NAY)SR/60/2016-17`. Physical only: File 4 rows 172-175 (applications
  01.07.2016 + endorsements 04.09.2017), File 5 rows 193-194 (DC letters
  13.01.2017), 214-215 (endorsements 05.06.2017), 227-228 (demand note +
  memorandum 2017/18), File 7 row 253 (endorsement 06.01.2018). No scans.
- Scripts/OCR read "Kankshita" / "Kanishtha" / "Kanshitha" / "Kankshitha"
  interchangeably for the same daughter — treat as one person.

## Drive search reality (scanned bundle)

- `fullText contains 'X'` only matches text Google has already OCR'd. Scanned
  NAPS2 bundles have NO text layer → zero fullText hits no matter what's in
  them. Use NAME search + the index spreadsheet, not fullText, for scanned sets.
- Organized numbered bundle `01_Index` … `28_Search_Reports_2020` lives in
  folder id `1KOy9rVGX1PE5H--9Q0yh1KmUSWBiuyFp` (title opinion, sale deeds
  sites 1-4 / 5-8, khata, endorsements, litigation OS files, EC parts 1-2,
  RTC/pahani, revenue survey, conversion, amalgamation JDA, etc.). `22_GPA_
  Will_Gift_Deeds.pdf` (40 pages) contains the 2003 site GPAs to V. Swaminathan
  + consent deeds — NOT the Rangamal death cert (checked via pdftoppm+tesseract).
- 291-page NAPS2 `Allalsandra Docs Legal Set.pdf`
  (id `1ABXJZX6I5P324iuslD8QiAVoq3C2ebrB`) is image-only; OCR largely fails
  on handwriting. Index spreadsheet is the reliable map.

## Rename-by-date nuance (DWG / brochure files)

For CAD/brochure files with no readable content: date prefix comes from
earliest Drive createdTime/modifiedTime (e.g. `Fire Sanction.dwg` →
`20151113_Fire_Sanction.dwg`, `Ranka NorthStar E-Brochure.PDF` →
`20150611_Ranka_NorthStar_E-Brochure.pdf` — created 2015-06-11). Leave names
alone when they already embed a date (e.g. `WD_24M_DRA_..._07-05-2026.dwg`).