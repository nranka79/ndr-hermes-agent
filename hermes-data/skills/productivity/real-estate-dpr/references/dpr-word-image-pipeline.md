# Word (.docx) DPR pipeline — images, area tables, entities, coordinates (24-Aug-2026)

User requirement (verbatim drift): "REDO IN A PROFESSIONAL STANDARD TEMPLATE FOR DPR, RE-GENERATE FOR EACH PROJECT IN A WORD FORMAT ONLY", then "Insert Approved plans image, Project renders, site images, remove consultant profile section", "Floor plans(Images), area statements(table), all the ANNEXUREs images NOT as attachments", "CHeck the Entity structure - Name the partners in the entity", "ADD : PROJECT LOCATION GOOGLE CORDINATES AND LAT / LONG", "ADD RERA CERTIFICATES IMAGES FOR RANKA UDAYA, OASIS, AMBER".

Deliverable = **.docx uploaded as Word** (do NOT convert to native Google Docs when user says "Word format only").

## Canonical per-project assets (found on Drive under psingh@draas.com)

| Project | Approved plan image | Floor/layout plan | Render | RERA cert | CAS / area source |
|---|---|---|---|---|---|
| Amber | `AMBER SANCTION 07.05.2026.pdf` / `Amber Plan Sanction GBA_BECC_0540_25-26 (2).pdf` | GFC floor PDFs (`Amber Final GFC 18.07.26-*Floor Plan.pdf`, `-TYPICAL FLOORING LAYOUT.pdf`) | portfolio deck p14 | `20260703 PRMKARERA1251446PR050826008859.pdf` | `Ranka Amber - Customer Area Statement.pdf` (Annexure-A) |
| Udaya | `20250505 Approved Layout Plan.pdf` (DTCP 90/2025) | `Ranka Udaya Brochure.pdf.pdf` (layout pages) | poster 1Lr7KCWBbfmMaC (aerial) | `20260218 RERA ORDER (1).pdf` | plottal 48,751 / dev 46,451 sq.ft |
| Oasis | `Sevaganapalli Layout Phase 1 & 2.png` (PNG already!) | `Ranka - Nature's Promise - Corrected Layout-Model 10.01.26.pdf` | portfolio deck p15 | `20260807 Ranka Oasis Rera.pdf` | `20260819_RANKA_OASIS_Customer_Area_Statement.docx` (**docx, not PDF!**) |
| NorthStar | `PRJ_0987_21-22.pdf` | `PDF_LAYOUT_NORTHSTAR_03.03.24 (2).pdf` | portfolio deck p12 | none (to be applied) | saleable 78,612 / dev 54,170 sq.ft |

Portfolio deck = `/tmp/dra_portfolio.pdf` (52 pp): map pages via `pdftotext -f N -l N -layout` per page; renders at p12 (NorthStar), p14 (Amber), p15 (Oasis). Render at ~100 DPI for embedding.

## RERA facts (all obtained except NorthStar)
- Amber: PRM/KA/RERA/1251/446/PR/050826/008859 dt 03-07-2026 (Karnataka RERA; applicant DRA Realty Pvt Ltd; address Plot 1-B, D'Silva Layout, Pattandur Agrahara, Whitefield)
- Udaya: TNRERA/30/LO/0642/2026 dt 18-02-2026 (layout of 38 house sites, Sy 240/3A Sevaganapalli, Hosur Taluk)
- Oasis: TNRERA/30/LO/3130/2026 dt 07-08-2026 (layout of 130 house sites; valid till 31-03-2027; promoters: DRA Realty + Ramesh Reddy + Seveganapalli Land Partners) — **Oasis RERA was 'in process' in older drafts; it is now REGISTERED — always re-check Drive before writing 'in process'**
- NorthStar: to be applied after PRJ/0987/21-22 sanction

## Entity / partner structure (from RERA Form C + builder profiles + partnership deeds)
- DRA Realty Pvt Ltd: CIN U70100KA2011PTC058105, PAN AAPCS9730H, GST 29AAPCS9730H1ZO. Directors: Nishant Dinesh Ranka (46, promoter), Kishan Nair Murjani (37, CFA, Flameback Capital)
- DRA Thindlu Land Partners (PAN AAXFD2296G, est 27-08-2024): Nishant Ranka 49% + DRA Realty Pvt Ltd 51%
- Oasis promoters (TNRERA Form C): DRA Realty (rep. NDR), Ramesh Reddy, Seveganapalli Land Partners (rep. NDR)
- DRA Ranka Holdings: Partnership Deed 06-07-2020 (Dinesh Ranka + Manish Ranka) + Addendum 25-01-2021 + Addendum 17-09-2022 (Nishant/Mamata/Ranjeeth) + Reconstitution 22-07-2025 → current: Nishant Ranka, Roshini Ranka, Manish Ranka
- Builder profiles = Google Docs; export text via `files().export(mimeType='text/plain')` (get_media 403s on download-disabled shares)
- Scanned partnership deeds → `pdftoppm -png -r 130 -f 1 -l 1` + vision_analyze OCR (they're image PDFs; pdftotext returns nothing)

## Coordinates (Google maps link = https://www.google.com/maps?q=lat,lng)
- Amber: 12.9876, 77.7378 — Pattandur Agrahara/Whitefield (Nominatim hit)
- Udaya & Oasis: 12.8310, 77.8658 — Sevaganapalli village has NO Nominatim entry; use Bagalur (nearest mapped locality) and mark "verify pin"
- NorthStar: 13.0912, 77.5864 — Allalasandra, Yelahanka
- Always label rural/village coords "locality centre / verify pin" to stay honest.

## python-docx embedding helpers
- `add_image(doc, path, caption, width=5.9)`: `doc.add_picture(path, width=Inches(width))`, center the last paragraph, then an italic grey caption para (8.5pt). If file missing → red placeholder `[ Image not available — caption ]`.
- Gallery: `add_gallery(doc, [(path, cap), ...])` — placeholder when empty list ("Site photographs to be provided").
- Section numbering after deletion: remove 4.3 "Contractor & Consultant Details" then renumber 4.4 → 4.3 (no gaps).
- Word is fine with 20 tables + 13 images per doc (~5–8 MB); convert PDF→PNG at 100–130 DPI for balance.

## Pitfalls hit in-session
1. **"CAS PDF" that is really a docx** — Oasis "CAS.pdf" download was a ZIP (`PK\x03\x04` magic). ALWAYS `head -c 8 file | xxd` before pdftoppm. If ZIP → parse with zipfile (`word/document.xml` → regex `<w:t>`), build the area-statement TABLE from the extracted figures.
2. **Drive 403 on get_media**: Google-native files (docs) and export-disabled shares return 403 → use `files().export(fileId, mimeType='text/plain')` for docs; for binary files check sharing setting.
3. **Delete 403 on another owner's files**: old DPRs in the Word folder were ndr@draas.com-owned; delete fails under psingh. Don't fight — create a fresh folder, `files().update(addParents=newFolder, removeParents=oldFolder)` your own new files, share the new folder.
4. **pdftoppm on corrupt PDF**: one download came back as HTML error page; re-download via a second get_media pass fixed it.
5. **filename bug**: `proj['name'].replace(' ','')` on 'RANKA AMBER' yields 'RANKAAMBER' → strip the 'RANKA ' prefix: `short = name.replace('RANKA ','').replace(' ','')`.
6. Gov certificates (RERA Form C etc.) carry richer address/entity info than marketing decks — read pages 1–2 fully before finalising approvals/entity tables.

## Verification before delivery
- Re-open each .docx with python-docx; assert: consultant heading gone, `tables>=20`, `inline_shapes>=5`, 'Google Map Coordinates' & 'Partners / Directors' & 'RERA Registration Certificate' present (search table cells too — paragraph scan misses table text).
- Then upload to a NEW shared folder, `permissions anyone->writer`, deliver folder + per-file links.