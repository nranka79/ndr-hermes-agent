# Litigation Case Folder Filing — O.S.No.553/2023 (RRP vs SPV) worked example

Template for filing court documents into DRAAS litigation case folders on Drive.

## Case context — O.S.No.553/2023 (e-courts case no: KABR310007152023)
- Plaintiff: M/s **Ranka Raj Properties (RRP)**, by partner Sri Shah Rajesh
- Defendants: Sri **Khimji Keshara Patel** & Ors (incl. South Pacific Developers & Investments LLP = D2)
- Court: Addl. Sr. Civil Judge & JMFC, Devanahalli (Judge Sri Praveen Nayak, LLM)
- Subject: Specific performance of MOU **09.06.2022** — ~30 acres converted land, Singarahalli & Ilathur Villages, Kundana Hobli, Devanahalli. ₹75 Cr total; ₹5 Cr paid at execution; ₹6 Cr due within 3 months (by ~09.09.2022); ₹11 Cr = advance; 12+3 months to close; 18% p.a. refund clause
- Alternative relief (via IA III): refund of ₹5 Cr + 18% p.a. from MOU date

## Drive location
- Root property folder: **IVC-KIMJI-250123** = `12J4OEBDdI25jDeV72AFoHZVVqjeH6r06`
- **OS 553 case folder: "RRP vs SPV"** = `1H0EIER-W17_9cTHYfbd1dV4XsUv4stiI` (child of IVC-KIMJI-250123)
- **Document Index sheet:** "RRP vs SPV – OS 553 Document Index" = `1ZwyKQ-Ujmdar5VPijmgTdeJntaPPlCn4Vs8QB8vmwBM` (single tab Sheet1; 38 rows; page ranges refer to a compiled bundle PDF, NOT the individual files)
- Sibling folders: "Ivc kimji" = `1_7Cx0MyZkm7Z5RaNwzqdhJxUHElq8a5a` (property/title diligence: ECs, conversion orders, writ petitions), "communication Letters" = `1nq21pQ--7HPZFs9UxALeMJrKpsEa2oqO`
- All under google-draas (ndr@draas.com)

## Naming convention — numbered-prefix, NOT YYYYMMDD
Case folders use `NN_Description.pdf` ordered sequence (01–31 present as of Aug 2026):
- Examples: `20_Order_IA_No1_GMFC_OS553.pdf`, `07_Orders_IA_No3_9Feb2024.pdf`, `06_Orders_IA_No2_Rules5to7.pdf`
- New filing = highest NN + 1 → `32_Orders_IA_No5to7_15Feb2025.pdf`
- Some unnumbered stragglers exist (MFA judgments, MOU, Karnataka Stamp Act orders, Master Notes, `IA_No4_Order39_Rules1and2_16Mar2024.pdf`) — numbered files are the court-filed sequence; keep appending at the end of the sequence
- Ask before updating the Document Index sheet — it uses compiled-bundle page ranges, not per-file numbers

## Orders status (as of Aug 2026)
- **IA No.I** (29.11.2023): injunction REJECTED — MOU unstamped; "agreement to enter into agreement" not specifically enforceable (KB Jayaram, Speech & Software, Salarpuria); plaintiff's ₹6 Cr DD late (03.10.2022 vs 09.09.2022 deadline). Confirmed by HC **MFA 8318/2023** (dismissed). Filed: `20_Order_IA_No1_GMFC_OS553.pdf`
- **IA No.II** (Rules 5–7, order 15.02.2025): filed `06_Orders_IA_No2_Rules5to7.pdf`
- **IA No.III** (09.02.2024): plaint amendment ALLOWED — prayer 1 "sale agreement"→"sale deed"; alternative refund ₹5 Cr + 18% p.a. added via s.22(2) SRA proviso (available at any stage). Filed: `07_Orders_IA_No3_9Feb2024.pdf`
- **IA No.IV** (Order 39 R1&2, 16.03.2024): filed unnumbered
- **IA No.V–VII** (15.02.2025): bring LR of deceased **Defendant 8** on record — ALLOWED on cost ₹3,000; amendment + amended plaint by 07.04.2025. Filed Aug 2026 as `32_Orders_IA_No5to7_15Feb2025.pdf`
- **Danger flag:** D8 death date inconsistent across own filings (04.02.2022 vs 04.12.2022; defendants say 04.12.2021 — BEFORE suit institution 31.05.2023). If pre-suit death, suit against D8 is a nullity; LR substitution may not cure it; court itself noted separate impleadment remains open. Defendants will press this at trial.
- Stamp route already in bundle: District Registrar s.33 order 19.06.2024 + s.41 certificate 28.06.2024

## Duplicate-detection workflow — run BEFORE filing any uploaded court order
1. List the target case folder contents first (`'<folder_id>' in parents and trashed = false`).
2. Uploaded orders frequently duplicate already-filed scans under different filenames. Verify:
   - Text layer: `pdftotext -layout` on both → compare case no / date / IA number / final ORDER block language.
   - Existing copies are usually scans (pdftotext returns empty) → `pdftoppm -f 1 -l 1 -r 100 -png` first (or last) page, then `tesseract <render> stdout`; match on the e-courts header (e.g. KABR310007152023) + final ORDER text.
   - `pdfinfo` page count is a WEAK signal only — a scan may bundle extra pages (e.g. IA III order + appended verifying affidavit = 11 pages vs 10-page order PDF).
   - `vision_analyze` may be unconfigured — tesseract is the reliable fallback for scan comparison.
3. File only genuinely-new orders; report dupes to the user with their existing Drive links; offer to upload text-layer versions if wanted (don't create duplicates unprompted).
4. After upload, verify: `files().get` parent chain (file → RRP vs SPV → IVC-KIMJI-250123) and confirm `canAddChildren` on the target folder before creating.
