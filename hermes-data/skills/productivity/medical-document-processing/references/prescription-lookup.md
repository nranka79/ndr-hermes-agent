# Existing-Prescription / Medication Lookup (family medical estate)

Task class: "find the `<medicine>` prescription for `<family member>`" / "which doctor
prescribed X, and when" — lookup over the family medical Drive estate, DISTINCT from
processing/filing a NEW document. Voice examples: "Ruhaan ke liye Azithromycin ki photo,
pichhle 6 mahine" (Azithromycin prescription picture, last 6 months).

## Search ladder (fastest → definitive)

1. **session_search** `"<member> <drug>"` — usually returns research/analysis docs, NOT the
   prescription itself (the weekly asthma-scan cron and diagnosis files mention drugs only in
   passing). Cheap, but rarely the answer for scans.
2. **/data/hermes/projects/medical/** — holds only ANALYSIS docs (`*Diagnosis-2026-08.md`,
   `Medical-Analysis-Enhanced-2026-08.md`, `Medical-Trend-Analysis-2026-08.md`); no raw
   prescriptions live here.
3. **Drive fullText** `fullText contains '<drug>'` — finds Google-native docs/spreadsheets
   but **MISSES scanned PDFs** (Drive does not index image-based/Adobe-Scan PDFs). A useful
   probe; not definitive. Same for `name contains 'azithro'` — filenames rarely carry the
   generic drug name.
4. **Walk the member's Medical folder** (folder IDs in SKILL.md Stage 3.1):
   `q="'<folder_id>' in parents"` listing, then filename-filter for `Prescription` + doctor /
   hospital hints. Prescription filenames conventionally encode
   `YYYYMMDD_<Member>_<Hospital>_Prescription_<Doctor>.pdf` — read the folder listing and pick
   candidates by date-range + doctor rather than by drug name.
5. **Download candidate(s) → verify** with `files().get_media` → `pdftoppm -png -r 150` →
   `vision_analyze` asking explicitly for doctor, hospital, date, patient, and ALL medications
   with doses. Brand names vary (AZEE = Azithromycin) — confirm the actual drug from the OCR
   text, not the filename.

## Worked example (2026-08-25): Ruhaan's Azithromycin prescription

- Voice: "Azithromycin picture within last 6 months, Dr Bharat Kumar Reddy, for Ruhaan".
- Drive fullText `azithromycin` → 7 hits, all docs/sheets (Second Opinion Dossier v2/v3,
  Medical Notes & Corrections sheet, cumulative recommendations) — NO PDF.
- Listing **Ruhaan Medical** folder (`0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k`) →
  `20260613_Ruhaan_ShishuHospital_Prescription_DrBharatReddy.pdf`
  (id `1d290p65d9w5ndX-gHdZNvGbiygBOG-bx`).
- OCR confirmed: **Shishuka Children's Specialty Hospital** (Kalyan Nagar), **Dr Bharath
  Reddy** (MBBS, MD(Paed), DNB, Regn 80542), Mast Ruhaan Ranka 14y, first visit 13/06/2026:
  - **AZEE 500MG tab (= Azithromycin)** — 1 morning, after food, 5 days ← the target
  - Foracort Inhaler 100 — 2 puffs, 1 month
  - Levolin Inhaler — 2 puffs, 5 days
  - Junior Lanzol 30MG — 1 before food, 5 days
- Delivered: Drive link + MEDIA render of the page PNG (user wanted "link + what the picture is").

## Domain notes

- **"ShishuHospital" in filenames = Shishuka Children's Specialty Hospital**, #938 Ring
  Service Road, Kalyan Nagar, Bangalore (ph 8660821311). Ruhaan's paediatrician there is
  **Dr Bharath Kumar Reddy**; sibling file `20260613_Ruhaan_ShishuHospital_FENO_Spirometry_DrBharatReddy.pdf`.
- **Common brand→drug resolutions seen in family prescriptions:** AZEE 500MG = Azithromycin;
  Augmentin 625 = amoxicillin-clavulanate; Foracort = budesonide+formoterol inhaler; Levolin =
  levosalbutamol inhaler; Junior Lanzol = lansoprazole.
- Voice glossary: "Azitro Maisan / Azitro" → Azithromycin; "Bharat Kumar Reddy" → Dr Bharath
  Reddy (Shishuka); "Tars" → Towers, "Flow Plan" → Floor Plan (Drive property-doc searches).
- Prescription PDFs are single-page Adobe Scans — `pdftoppm -png -r 150` renders are fine for
  vision_analyze; keep the ≤1600px resize rule for anything larger.
- If the member has multiple candidate prescriptions (BMJ, Manipal, Shishuka), verify each;
  report which one actually contains the drug rather than assuming the newest.