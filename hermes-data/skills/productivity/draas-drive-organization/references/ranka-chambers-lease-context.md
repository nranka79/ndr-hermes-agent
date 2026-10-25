# Ranka Chambers — Lease / Lease-Cum-Construction Context

NDR's Ranka Chambers building: 31 Cunningham Road, Bengaluru 560052 (Syed Aviuddin owned the land; M/s Nandi Enterprises = lessees incl. **Arun B. Ranka**). Two lease deeds exist on Drive; both are **scanned PDFs (no text layer)**.

## Documents
- `Ranka Chambers - 14-Aug-1984 Lease Deed.pdf` (id `1nqSCdevsNZYXzkbWkrryafTQMvayfrAQ`, 11 pages) — **the main lease-cum-construction agreement**
- `Ranka Chambers - 18-Jun-1986 Lease Deed.pdf` (id `1xmKIlpPx3dsZjcnHM6CBF-PKwYu-z61b`, 8 pages) — adjoining property lease
- Related: `Ranka Chambers` folder (id `1VXv-8dh9mhCkDKBTPxlMVCEZA52msgFR` — just 3 WhatsApp JPEGs); `DRA Ranka Chambers Office Documents Index` spreadsheet (id `1B6epZ8BMc9xl4rJJwYBXJRTPRFvHDR7u-8qlUotEskk` — tab `Consolidated Files Docs Data` is a PHYSICAL-file index of Ranka-Stero/Ranka-Stelo customer files, NOT lease terms; don't expect lease dates there)

## 1984 Lease Deed (verified 2026-09-02)
- **Deed date: 4th day of August 1984** (deed text; filename says 14-Aug-1984 = likely registration date — OCR + vision on p1 confirm "4th day of August")
- Lessor: Syed Aviuddin, s/o Late S.D. Mohiuddin; Lessees: partners of M/s Nandi Enterprises — T.M. Narasimhan, Chandrasekar, **Arun B. Ranka** (s/o Banwarlal Ranka), Kanthilal G. Bafna
- Recitals: prior lease dtd 11.11.1976 (regd 1529/76-77); partition deed 1.8.1984; partnership reconstitution 2.5.1984; surrender of old lease 4.8.84 (regd 1341/84-85)
- **Term: 60 years** from date of deed (clauses 1 & 4 of WITNESSETH: "period of sixty years from the date of this deed"; hold/enjoy for sixty years)
- **Lease-cum-construction:** lessees may demolish existing constructions and build a business complex; constructions become the lessor's absolute property after expiry (clause 16); first option to lessees on renewal/sale (clauses 13/15)
- Rent: Rs 700/month; lessor may mortgage/assign; possession already delivered
- **End date: ~3/4 Aug 2044** (handwritten "1984 → 2044" annotation on stamp paper corroborates)
- Schedule: property bearing No.31 adjacent, Cunningham Road (Sampangi Ramaswamy Temple St / City Station, Corp Div No.44), bounded N: Cunningham Road, S: portion of No.31 retained by lessor, E: private road right-of-way, W: No.32 Cunningham Road

## 1986 Lease Deed (adjoining property)
- Deed date: 18 Jun 1986; rent **Rs 50/month payable from 1-7-1986** until end of term
- **Term: 58 years** from execution (clause 3) → **end ~17/18 Jun 2044**
- **Auto-extension clause (clause 4):** if the 1984 lease period is extended by mutual consent, this lease extends automatically to stay consistent with it

## As of 2 Sep 2026 (today)
- 1984 deed: ~42 years elapsed, **~17 years 11 months left** (terminates ~Aug 2044)
- 1986 deed: ~40 years elapsed, **~17 years 9 months left** (terminates ~Jun 2044)

## Extraction technique for 1980s scanned deeds
- `pdftotext` returns ~empty (scans). Use `pdftoppm -r 200 -png -f N -l M` then `tesseract img stdout --psm 6`
- OCR quality is poor on these (faded type, tilted pages): **verify critical clauses with vision_analyze on the rendered PNG** — it read the deed-date line, rent clause, term (58 and 60 years), and extension clause reliably where tesseract gave fragments
- Term/date clauses sit mid-deed (p1 date line, p4-5 operative clauses on 1986 deed; p4-8 on 1984); signature screens are p6-11 (1984) / p6-8 (1986) and are mostly stamps
- Note: `convert`/`magick` are NOT installed for rotation — image orientation issues should be handled via pdftoppm + re-OCR, Python PIL crop, or vision_analyze