# Ranka Oasis — Investor Report Data Sources (workbooks, Sep 2026)

The two Google Sheets that carry the canonical project-land data used for the
Ranka Oasis investor lands report (and reusable for any future
"approved vs not-approved / owner split / registered deeds" ask on
Sevaganapalli land).

## 1. Investor portfolio workbook — per-project land master

`20260707_DRA_Group_Investor_Portfolio_All_Projects`
ID `1wDKS0SxtY0EF_-JUe2BfXzLSSwh4J5fo4y0sI_brFfw`

Tabs (sheetId → title): 1664236874 RankaUdaya · 1443251368 Ranka Amber ·
752253398 **Ranka Oasis** · 903813657 Ranka NorthStar · 1528630995 Project Summary.

Per-project tab layout (Ranka Oasis, rows ~3–145; values().get works normally
on this workbook):
- Row 7: location address (survey list!)
- **B. Land Details** — DRA owned Phase I 6.58 ac / Phase II 2.33 ac; JDA 0.95/0.50
- **G. Approvals** — Plan Sanction ref, RERA status
- **H. Summary of Total Land Parcel** — owner × extent (SLP 746c/7.46, DRA 140c/1.40, JDA 95c Ramesh Reddy, 50c K Harish, total 1031c/10.31)
- **I. Summary of Lands in the approved plan** — survey | cents | owner | type (Owned/JDA) | legal opinions (19 rows, total 751.5c)
- **J. Summary of Lands not in approved plan** — same shape (10 rows, 279.5c)

Use I + J as the authoritative approval-wise parcel lists; H as the owner-summary.
Parcels in I+J always reconcile to H (751.5 + 279.5 = 1031c ✓).

## 2. Legal documents matrix — per-parcel registered deeds

`20260809 Ranka Oasis - Survey-wise Legal Documents Matrix`
ID `1eVqckk3cCWdN06RNGISTP99WSz-aToCmGcNPIIqaicc`

**TRAP: the tab the user links ('Documents as per CMS report', gid 2041900373)
is EMPTY** (both Sheets API `values().get` and xlsx export show 0 rows). The
registered-document data actually lives in:
- **PART_I_DocFurnished** (173 rows) — the 107-doc CMS/TSR list: S.No | Date | Document Description | Drive Link | Matched file | Status. This is the doc-number + date register.
- **34 per-survey tabs** (`Sy_158_1C9A`, `Sy_166_3A`, … `Sy_177_1A1B`, incl. `Sy_167_2C`, `Sy_168_1A`) — each with header `SURVEY: … | OWNER: … | ✅/❌ APPROVED`, then repetitive doc-type rows (Title Deed / Chain of Title / Patta / FMB / EC …) repeating the same file list under each category, plus `From Index:` rows. The rows that matter for vesting: **"Title Deed (current owner)"** and **"Sale Deed (to DRA Realty / Exchange to DRA)"** — these carry the acquisition deed with date.
- PART_V_FlowOnTitle (1007 rows), MISSING_DOCUMENTS, EC_* tabs.

**Sheets API quirk:** this workbook (like the ownership-master workbook
1THJ4LvKyOB0GZIPamNLqkSBciCHqUki4_S1BLQ6jjCA) returns EMPTY from
`spreadsheets().values().get`. Always export-and-parse locally:
`drive.files().export_media(fileId, mimeType=xlsx)` → zipfile → sharedStrings +
sheet XML per tab (stdlib recipe; openpyxl may be absent). Read `workbook.xml`
for tab→sheetN.xml mapping (order differs from tab order), count rows per sheet
to find where data sits (some tabs are 0-row decoys).

## Building the per-parcel registered-deed column + register

- Vesting deed per parcel comes from the matrix per-survey rows + PART_I:
  - DRA block: SD 21785/2024 (14-11-2024, 158/1C3·1C4·1C6·1C9A combined), Exchange 4292/2024 (01-03-2024, 177/1A·176/2B·176/1B2)
  - SLP block: SD 14-07-2023 (Ramappa & ors → DRA SLP: 166/3D·3F·164/1A1B·167/1H·2D), SD 1326/1996 + 4106/1996, AOS 7834/2023 (166/3), SD 4515/1995 (166/3E), Exchange 3906/2025 (167/2C)
  - JV lands: JDA 7963/2025 + GPA 915/2026 (Ramesh Reddy: 166/1·167/1G·168/1B); JDA 6157/2025 + GPA 6158/2025 (K Harish: 177/1B·177/2A1)
- Combined deeds cover several parcels — cite the combined ref on each row and list it once in the register ("comb. w/ 1C3, 1C4, 1C6").
- Discrepancy flags to report (workbook vs CMS matrix): 158/1C5 (workbook DRA vs matrix Suresh/Manjunath, no title deed), 167/2C (same), 166/2B2 (workbook SLP vs master-data DRA); ownership-summary 7.46/1.40 vs parcel-sum 7.21/1.65 (25-cent attribution; totals equal).

## Related

- Ownership master workbook (`Saveganapalli Kagganur Sy No Master Data`) →
  `references/seveganapalli-ownership-master-data.md` (same export-parse pattern).
- Survey-wise extent schedule → `references/survey-wise-land-extent-schedule.md`.