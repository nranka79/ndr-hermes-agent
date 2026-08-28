# RRP vs SPV — OS 553/2023 Partnership-Deed Status & Case Context

Companion to `references/litigation-case-folder-filing.md` (filing workflow, folder IDs, order
chronology, duplicate detection). THIS file focuses on the **partnership deed / registration
question** — what the record says, what is missing, and where the deeds live on Drive.
Use when NDR asks "is the partnership on record?", "was it registered?", "where's the
partnership deed?", or for s.69 exposure analysis.

## Case summary (brief — see litigation-case-folder-filing.md for full context)

- **Suit:** O.S. No. 553/2023, Court of the Senior Civil Judge & JMFC, Devanahalli
- **Plaintiff:** M/s Ranka Raj Properties (partnership firm) — office No.4, Ranka Chambers,
  No.31, Cunningham Road, Bengaluru-560001
- **Defendants:** Sri Khimji Keshara Patel (D1) + M/s South Pacific Developers & Investments
  LLP (D2, 23 partners incl. Dadlanis & Patel) — D8 = Duru Kishanchand Dadlani
- **Subject:** Specific performance of MOU dated 09.06.2022 — ~30 acres converted + ~55 acres
  agri land, Singrahalli/Ilathur villages, Kundana Hobli, Devanahalli. Consideration ₹75 Cr;
  ₹5 Cr paid on execution; ₹6 Cr further advance due within 3 months; ₹11 Cr total advance;
  12+3 months to close. Alternative relief: refund ₹5 Cr + 18% p.a.
- **MOU parties per MOU itself:** FIRST PART = Khimji Keshara Patel + South Pacific (23 partners);
  SECOND PARTY = "M/s RANKA RAJ PROPERTIES, A PARTNERSHIP FIRM … REPRESENTED BY ITS
  MANAGING PARTNER SHRI DINESH RANKA"

## Partnership deed status (as of Aug 2026 — IMPORTANT)

- **Plaint para 3 (both original & amended):** plaintiff "is a registered partnership firm
  registered under the Indian Partnership Act… The copy of the partnership firm of the
  plaintiff firm is produced at **Annexure A**"
- **BUT the deed is NOT in the case record:** the filed plaint PDF (25 pages) ends at
  verification + schedules — no Annexure A pages. No deed in any case-folder doc, index
  sheet, or court-certified Document ID file. The 28.05.2024 "return of original" memo was
  for the MOU (stamping), not the deed.
- **No s.69 IPA challenge anywhere.** South Pacific's own objection to IA No.4 AFFIRMS:
  "Plaintiff is a Partnership Firm registered under the provisions of Indian Partnership
  Act 1932" — defendants conceded registration on record.
- **Amended-plaint inconsistency:** original plaint says "represented by its partner
  Sri. Shah Rajesh"; amended plaint para 3 says "represented by its managing partner
  Sri. Dinesh Ranka" (cause title still says Shah Rajesh). Partner-authority point untested.

## Deeds that exist on Drive (different entity names!)

- `Ranka Raj Ventures Partnership Deed dtd 20.11.2020` — `1cvDG7PgAHDHPq8ks5j8iXOBDGES5XGzc`
  in `Ranka Raj Ventures (Thondebhavi)` folder (`1gduyvAlQGXWF0v4j13jsbFcG23uKHGSI`).
  Firm name clause: **"Ranka Raj Venture"**. Parties: Dinesh/Manish/Nishant Ranka (First)
  + Shah Rajesh, Priya Shah, Roopesh Shah, Shah Vikash (Second). Capital ₹1,00,007.
  Registered office Jayanagar. E-stamp 27.11.2020 ₹2,000. Byte-identical copies in
  `WhatsApp Documents` (`1GKKyRs-Sfvn51tPXJWoyl5bVT5hszz9g`) and `RRV` (`1xydj77T8p7HZ9lOPng7VVgEHMT1_Tpan`) folders.
- `20201128 Raj Ranka Partnership Deed` — `1yBCcIYw8MG8U52csInw1doI6obiPZNEX` in `Avillion`
  (`1AWR2orvF-E51jbw91_PciJZyp8UY8BbN`) under `RR Ventures` (`1TfePHxL-sNtZ39atyu4PqIELajRLTw9R`).
  8 pages, same parties/capital; firm-name clause OCR also reads "Ranka Raj Venture" —
  likely a re-executed/re-dated copy of the same partnership.
- **Exposure:** firm named in available deeds ("Ranka Raj Venture") ≠ plaintiff's name
  ("Ranka Raj Properties"); deed not physically before the court. If defendants wake up to
  s.69 + name mismatch, maintainability becomes a live fight. To obtain the deed:
  1) certified copy of plaint + Annexure A from Devanahalli court; 2) Registrar of Firms
  Bengaluru Form A extract; 3) NDR's own registration certificate.

## OCR tips specific to these scans

- Case PDFs (plaint, orders) are grayscale scans with no text layer — `pdftotext` returns
  near-zero; go straight to `pdftoppm -r 150 -gray -png` + `tesseract` per page.
- Deed scans (esp. Raj Ranka 28.11.2020) are POOR quality — firm-name clause reads
  "Ranka Raj Venture" via crop+upscale+threshold; page 1 (cover) is often unreadable via
  tesseract. Flag unreadable pages rather than fabricating.
- Naming note: case folder files use `NN_Description.pdf` (01_…31_); the global
  `YYYYMMDD_…` convention does NOT apply inside this folder. New doc filed as
  `32_Orders_IA_No5to7_15Feb2025.pdf` (Drive id `1Di9u0n2hg0l_Wj0DkmbzJ4XizXh7WvFA`).
