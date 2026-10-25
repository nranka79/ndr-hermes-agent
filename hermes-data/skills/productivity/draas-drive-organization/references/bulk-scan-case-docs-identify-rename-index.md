# Bulk Scan Case Docs: Identify → Rename → Index

Worked example 2026-09-12: the 32-doc OS 553/2023 scan bundle in
"Rajesh Shah Vs SP Partners Case Docs" (`1VSZQrOsOI82rR88TLm1phGXvLAw-b2Ai`,
subfolder of Ivc kimji `1_7Cx0MyZkm7Z5RaNwzqdhJxUHElq8a5a`).

## Trigger
NDR uploads a folder of unattributed scanned PDFs named `pdf.1.pdf … pdf.N.pdf`
(usually "case related documents" for a property/matter) and wants each examined,
renamed per naming convention, plus a spreadsheet index (new name, link, summary)
in the same folder.

## Workflow (verified, 32 files, zero failures)
1. **Context first**: `session_search` the case name — often only the same request
   retried, so resolve the matter via `draas-drive-organization` references first
   (ivc-colaso-rrv-rrp-context.md disambiguates RRV vs RRP and the Colaso spelling).
2. **Download all**: terminal() with
   `HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3`, `_load_credentials_direct('google-draas')`,
   `files().list(q="'<FOLDER>' in parents and trashed=false")` then `get_media`
   per file to /tmp. Print `about().get(fields='user')` first, verify count == N.
3. **Text-layer probe**: `pdftotext -layout` per file — near-zero chars ⇒ scan.
   (All 32 were scans here.)
4. **Render**: `pdftoppm -f 1 -l 1 -r 150 -png` page 1, plus page 2 (`p${n}b`) when
   pages ≥ 2. 150 dpi is adequate for court-doc OCR.
5. **OCR**: tesseract per render: `for img in pages/p*-*.png; do tesseract "$img" ocr/$(basename "$img" .png); done`.
   PITFALL: pdftoppm output names are inconsistent (`p1-01.png` zero-padded vs
   `p3-1.png`) — list with `ls pages/ | sort -V`, never assume the file name.
6. **Identify from OCR**: read page-1 text per doc; disambiguate duplicate-looking
   plaints by rendering the LAST page too (`pdfinfo` page count → `pdftoppm -f N -l N`)
   — plaint copies differ by verification date / schedule tail (31.05.2023 vs 16.03.2024).
7. **Name assignment**: litigation case folder convention `NN_Description.pdf`
   (01..32, NOT YYYYMMDD). NN = the original pdf.N order preserves the upload sequence
   and makes old→new reporting trivial.
8. **Rename — THE PITFALL**: NEVER hand-copy file IDs from an earlier listing into
   the rename dict. The first attempt mis-mapped pdf.2/pdf.31/pdf.32 IDs. Always
   re-fetch `name→id` inside the same script and key NEW names by OLD name.
   `files().update(fileId, body={'name': ...})` preserves links.
9. **Index sheet**: create via
   `drive.files().create(name=..., mimeType='application/vnd.google-apps.spreadsheet', parents=[FOLDER])`,
   then Sheets `values().update` with header
   `[Sl No, Old File Name, New File Name, Drive Link, Summary]` + N rows (link =
   fresh webViewLink), then batchUpdate formatting (bold/frozen header, column
   widths, WRAP on summary column). Title per convention:
   `YYYYMMDD_Entity_Document_Index_...`.
10. **Verify**: `values().get` → rows == N+1 and every link starts with
    `https://drive.google.com/file/d/`. Then report old→new list + sheet link +
    folder link in chat.

## Pitfalls
- `vision_analyze` may be unconfigured ("no LLM keys configured", 503 no_provider) —
  the tesseract-per-render fallback is the path; do NOT loop on vision calls.
- Hand-built ID maps drift between turns; fetch the mapping in-script (step 8).
- Same-looking scans (multiple plaint copies) need the last-page render to tell
  versions apart.

## What the OS 553 "Rajesh Shah Vs SP Partners" bundle contains (32 scans)
1 Order Sheet (filed 31.05.2023) · 2 Amended Plaint · 3 Plaint Verification ·
4/6 Verifying Affidavits (notaries Devanahalli / Basaveshwara Nagar) ·
5 Plaint w/ schedule · 7 Parties list · 8 Affidavit for IA3 (sale agreement→sale deed
prayer correction) · 9 D2 Objections to IA3 (Deepu Dadlani) · 10 Plaint copy ·
11 Affidavit in support of plaint (75 Cr lands, MOU 09.06.2022) ·
12 Memo of death of D4 Gull Gobindaram Dadlani (12.09.2024) ·
13/14 O22R4 LR application + affidavit · 15/16 O22R9 set-aside-abatement + affidavit ·
17/18 s.5 Limitation condonation (15.06.2025) + affidavit ·
19 D2 (SPDIL) Written Statement O8R1 · 20 D2 Objections IA1 ·
21 Objections IA4 (Mahesh Dadlani D6a — cites MFA 8318/2023) ·
22 Amended plaint copy (16.03.2024) · 23 Affidavit plaint + amended plaint ·
24 s.5 condonation (05.01.2024) · 25/26 D8 LR affidavit + D8(a) objections
(D8 died 04.12.2021 pre-suit → nullity argument) · 27 D2 Objections IA4 ·
28 RONALD COLASO impleadment application O.I R.10 (08.04.2025, proposed D26,
claims ~53 ac 9 guntas) · 29/30 objections to impleadment (D2 / plaintiff) ·
31 Order IA1 injunction REJECTED (29.11.2023) · 32 Order plaint amendment ALLOWED
(09.02.2024).

## IDs
- Folder: `1VSZQrOsOI82rR88TLm1phGXvLAw-b2Ai` (parent Ivc kimji `1_7Cx0MyZkm7Z5RaNwzqdhJxUHElq8a5a`)
- Index sheet: `1b_NuegMwfzGAbT-vsyKVPcB5B_7gyhAM6AVqxfCLAUw`