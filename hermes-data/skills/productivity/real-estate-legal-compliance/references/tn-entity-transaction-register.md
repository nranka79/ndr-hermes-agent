# TN Entity Transaction Register — worked example (Saveganapalli / DRA Realty, 2026-09-16)

Building a **verified transaction register** for one entity ("list every sale deed / exchange deed /
agreement where DRA Realty is purchaser, or any transaction in DRA Realty's name, in Sevaganapalli
village survey numbers") from the **Saveganapalli Legal Docs** Drive folder
(`1jOcoVXgUTdHc4qcoQduLTr3aSeArTPgx`, owner presales.blr@draas.com, ~296 files + 2 subfolders).
Load this when the user asks to verify/audit an entity's land purchases from a legal-docs folder.

## Deliverable shape (what Prakash expects)

A survey-wise table split into: **A. registered purchase deeds** (doc no, date, SRO, surveys+extents,
vendors→vendee, consideration, patta), **B. agreement-only purchases** (NOT registered — say so
loudly), **C. other entity transactions** (reconstitution, SPA, MOU, gifts), **D. verification flags**
(patta gaps, Master Data staleness, filename-vs-content mismatches). End with the consolidated
acquisition trail. Cross-check every deed against: the current patta extracts, the Master Data
workbook, and the investor-portfolio workbook — not just the filename.

## Verified DRA Realty trail (reference data)

- **SD 19171/2023** (14.10.2023, SRO Hosur) — Sy 14/7 part (Ac 0.23) — Puttamma@Vinodha, Pushpamma,
  Ambuja → DRA Realty — ₹30,00,000. Patta 1442.
- **SD 19172/2023** (14.10.2023, SRO Hosur) — Sy 14/2 (Ac 0.72 full) — same vendors → DRA Realty — ₹85,00,000.
- **Exchange 4292/2024** (16.02.2024, SRO Hosur) — DRA gave UP Sy 14/2 + 14/7B (the two parcels just
  bought in Oct 2023); DRA RECEIVED from Venkatamma (w/o late Kencha Reddy): 176/1B2 (0.16), 176/2B
  (0.22), 177/1A (0.26) → later sub-divided 176/1B2D, 176/2B4A, 177/1A1A, 177/1A1B. Chain:
  Clover Estates (3428/2004) → Kencha Reddy (4879/2004) → heirs' partition 1611/2024 → Venkatamma.
- **SD 21785/2024** (14.11.2024, SRO Hosur) — Sy 158/1C3 (0.25) + 158/1C4 (0.38) + 158/1C6 (0.10) +
  158/1C9A (0.25) = **98 cents** — Y. Suresh Reddy, Y. Manjunath Reddy + sons → DRA Realty — ₹98,00,000.
  = **Patta 2058** (e-Registry: 10.00 + 15.50 + 4.00 + 10.00 ares = 39.50 ares ≈ 98c). Purchased via
  SPA holder Rajendra (SPA 0558/2023).
- **AOS Doc 11809** (18.06.2024) — Sy 168/1 **0.95 ac** — Purushothama Reddy + minors → DRA Realty —
  agreed ₹2,00,00,000, advance paid ₹1,10,00,000 (cheque 000320 Kotak). **NOT REGISTERED** — agreement
  + advance only (matches Master Data "168/1A 0.95 — Agreement to sell").
- **Reconstitution Deed 21.11.2023** (unregistered) — DRA Realty **95%**, Nishant Ranka 4%, Srinivas
  Krishnappa 1% partner of Sevaganapalli Land Partners (firm SJN-F490-2023-24). This is the "SP" firm
  — NOT the DRA Muthanallur / DRA KAAJ line.
- **SPA No 0558/2023** (21.12.2023) — DRA Realty → Rajendra S.V., for registering TN purchases.
- **MOU 07.05.2024** — DRA Realty (developer) × Krishnappa Venkataramappa family / K Harish → JDA
  precursor for 177/1B, 177/2A1 (later JDA 6157/2025).

SLP-track deeds in the same folder that are NOT DRA purchases (do not misattribute):
- `20231016 sale deed (7.53 acres)` = **21201/2023, vendee Sevaganapalli Land Partners** (big 16.10.2023 aggregation).
- `20240302 SaleDeed for sy no.166/2B` = vendee **SLP** (Suresh/Manjunath → SLP), not DRA.
- Addendum Exchange 12.11.2024 = Suresh/Manjunath ↔ **SLP** (₹1.5 Cr extra consideration via DRA cheques).

## Hard-won pitfalls

1. **Filename ≠ content. Verify inside the deed.** The folder file named `20231016 sale deed (7.53
   acres)`.pdf is vendee SLP (21201/2023), and `20240302 SaleDeed for sy no.166/2B` is SLP, not DRA —
   yet the Kagganur Master Data workbook still labels 166/2B "DRA Realty — Sale Deed". Master Data rows
   go stale; the registered deed is the truth. Flag the stale row and offer to fix the workbook. Also,
   file titled "..._0.23 cents" can be a deed whose recital says Ac 0.58 total (0.23 = part sold /
   Hec.0.23.5 misread); always read the SCHEDULE OF PROPERTY section for the conveyed extent.
2. **Patta extract vs deed claims — compare ROW BY ROW, don't assume.** Patta 2000 (176/1B2D 6.47,
   176/2B4A 9.11, 177/1A1A 1.02 ares = 16.60 ares) shows only **3 rows — 177/1A1B is NOT on it** even
   though the Plot 119 deed chain claims all four surveys via Exchange 4292/2024. Sub-division patta
   mutation may be pending. Report as a ⚠️ gap, offer to pull a current EC/patta to close it.
3. **Docx parsing: namespace prefix may be `ns0:` not `w:`.** `RankaOasis_Plot119_AbsoluteSaleDeed_*.docx`
   files parse to zero text with regex `<w:p`/`<w:t>` because the XML uses `<ns0:p>`/`<ns0:t>`.
   Use ElementTree namespace-aware parsing (`{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p`)
   or regex on `<ns0:t>` directly.
4. **Google-native docs vs binary docx — different download paths.** `mimeType application/vnd.google-apps.document`
   requires `files().export_media(...)` (text/plain or docx export); binary `.docx` files require
   `get_media`. Export on a binary gives HTTP 403 "Export only supports Docs Editors files" — that error
   tells you it's a binary, switch to get_media.
5. **tesseract on TN deed scans: pass `--psm 3`.** The gift-deed pages returned EMPTY with default PSM;
   `tesseract <png> stdout --psm 3` read them cleanly. Always loop pages with `--psm 3` on scan-sourced
   TN deeds.
6. **pdftoppm zero-pads filenames (`-01`) — check the actual names before looping OCR.** The recon deed
   produced `recon-1.png` (no zero pad) while the exchange deed produced `ex4292-01.png`; a loop hard-coded
   to `-01` silently OCR'd nothing. `ls` the renders first or glob `*` — never assume the pad width.
7. **Vendee section may be deep in the document.** In the 148-page 7.53-acre deed, OCRing pages 1-4
   (vendor list) showed no vendee; the vendee line ("M/s.SEVAGANAPALLI LAND PARTNERS") appeared around
   page 29-30, and pages 37-50. Grep the accumulated OCR, don't stop at page 4.
8. **Consideration details live in the deed body**: exact cheques/UTRs/dates (e.g. SD 21785/2024 paid
   via Kotak cheques 000513/000519 dat. 14.11.2024) are in the text — extract them; they're useful for
   the register and for tracing funding.

## Cross-source verification order

1. Deed scan/text (parties, doc no, date, survey, extent, consideration) — ground truth.
2. Patta extract (e-Registry) — current recorded owner + survey rows; compare row-by-row vs deed claims.
3. Master Data workbook (Kagganur/Seve Ganapalli ownership tab) — sanity check; flag stale rows.
4. Investor Portfolio `Ranka Oasis` tab — approved/non-approved classification, summary vs parcel-sum
   attribution shifts (±22-25c on 158/1C9A/1C3) — do not silently pick a side.
5. Legal folder inventory (draas-due-diligence-pack) for the JDA/opinion cross-refs if needed.