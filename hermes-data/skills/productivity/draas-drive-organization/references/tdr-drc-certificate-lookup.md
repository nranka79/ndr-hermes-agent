# TDR / DRC Certificate Lookup (Bangalore, BDA/BBMP)

Trigger: user asks for a TDR certificate / development rights certificate / "TDR transferred from <person> to <company> and utilised in <project>". Worked 2026-09-06 for Ranka Iris (Dinesh Ranka → DRA Developers & Projects Pvt Ltd).

## Domain naming (critical — search "TDR" MISSES the file)

- Bangalore TDR certificates are **Development Rights Certificates (DRC)**, issued by BDA/BBMP under Sec 14-B of the Karnataka Town & Country Planning Act 1961. "TDR" is the concept; "DRC" is what the paper and the files are called.
- Drive/Gmail name/fullText searches for `TDR` find *threads and folders about* TDR but rarely the certificate scan itself. Use `name contains 'DRC'`, `name contains 'development right'`, `name contains 'utilization'` too.
- The certificate's front is a **bilingual printed form (Kannada/English), hand-filled** — holder name, surrendered land, possession receipt no/date, zone, F.A.R. credit in sqm, issue date. Bottom note: *"Please verify the counter folio of this certificate for authentication."*
- The transfer/endorsement history lives on the **BACK = counter folio**, a pre-printed table titled **"UTILISATION OF DEVELOPMENT RIGHT CERTIFICATE"** with **handwritten blue-ink entries**: sl no/folio, DRC no, date & sanction no, Name of the Transferer, buildable area per DRC, transfer/utilisation area, balance, Name & address of the Transferee(s), transfer-fee receipt no & date, utilisation date, stamp. This is the "ruled notebook page" the user remembers.

## Search ladder (worth it for old/pre-digital certificates)

1. Cross-account Gmail search (all 3 vault accounts) with variants: `"tdr certificate"`, `tdr`, `"dinesh ranka"`, `"DRA Developers and Projects"`, `"<project>" tdr`, `"transferable development rights"`, `subject:tdr`, `has:attachment tdr`, `tdr before:YYYY after:YYYY`. Usually finds THREADS that reference the TDR, not the scan.
2. Drive name searches in every account: `name contains 'TDR'`, `name contains 'tdr'`, `name contains 'DRC'`, `name contains 'utilization'`, `name contains 'certificate' and fullText contains 'tdr'`, `fullText contains '<person>' and fullText contains 'development'`, plus `name contains 'TDR' and trashed=true`.
3. **The breakthrough query: `name contains 'DRC'`** → front/back certificate scans + "DRC letter.docx" + "DRC List and Utilization Certificate List (TDR BY BDA)" folder.
4. **OCR the project's BBMP sanction plan** — the sanction sheet carries a **"TDR Utilized" table**: DRC No. / Date of sanction / Name of the Transferer / Name of the Transferee / zone-wise areas (B/C zone sqm). This gives the authoritative cert number + parties even when the certificate scan is missing. Sanction PDFs are 2–6 pages; `pdftoppm -r 100 -gray -png` + tesseract finds the table quickly.
5. **vision_analyze on the DRC scans** (front and back). Front yields cert no, holder, surrendered-land details, F.A.R. credit. Back (handwritten counter folio) is ~unreadable by tesseract but well-read by vision_analyze (gemini flash handles blue-ink handwriting + Kannada title).
6. **Companion "DRC letter.docx"** — letters surrendering the ORIGINAL DRC to the authority (via a consultant) name the receiving project (BBMP **LP No.**), the DDs paid for transfer/utilization fees, and the promise to return the original after back-side entries. This ties cert → project definitively.
7. Verify parent chain before attributing (duplicate-name folders exist): cert scans often sit under `<Project>/LegalSet`.

## Worked example — Ranka Iris TDR (Dinesh Ranka → DRA Developers & Projects Pvt Ltd)

- **DRC No. 001498, Folio 40**, BBMP; holder **Sri Dinesh Ranka S/o Devaraj H. Ranka**, #634 Ranka Park, 4-5-6 Lal Bagh Road, Bangalore 560027; issued **17.02.2011** (Commissioner S. Siddaiah); land surrendered 3339.6 sqm, possession receipt 7371/10.11 dt 08.02.2011, Residential Ring II zone; F.A.R. credit **5616.06 sqm**.
- Back (counter folio) entry: transfer **1579.92 sqm** → **M/s DRA Developers & Projects Pvt. Ltd., #302A Queens Corner, #3 Queens Road, Bangalore 560001**; balance **4036.14 sqm**; utilisation date **22-5-13**; transfer-fee receipt 219373 (06.09.12, Syndicate Bank); BBMP Mahadevapura Zone stamp.
- Sanction `022 BBMP Sanction RankaIris 02SEP13` (4 pages, 11.7 MB scan) page 4: DRC 40/001498, areas 4036.14 (C zone) / 2688.08 (B) / 1199.02 (B) / 2235.79 (C) / 1489.04 (B).
- `DRC letter.docx` (06 Aug 2013, ndr for DRA Developers & Projects → G R Consulting / Archana): surrenders ORIGINAL DRC so BBMP notes the utilization for the **Domlur project bearing LP No. 37/12-13** (= Ranka Iris); DDs ₹5,00,000 (KSAB & Other Const Workers Welfare Fund) + ₹11,08,000 (Commissioner BBMP, JDTP North) on Syndicate Bank.
- Drive locations (google-draas): `DRC Certicicate - 1.jpg` (back, id 0B1Oc8cSaJXPGYXpnNk1KTHFwNzZNaW9MMS05SWg4YnBLM1dz), `DRC Certificate.jpg` (front, id 0B1Oc8cSaJXPGMjNQOVVnNEwxZ21nMEpCck1jc0liZC1oVHRF) in **RankaIris > LegalSet** (folder 0B1Oc8cSaJXPGVHRLaTY5dkZnZ2c, parent RankaIris 0B1Oc8cSaJXPGdy04dWxlbE9JR1k); files created 2013-08-08, re-saved 2016-05-14. `DRC letter.docx` (id 0BymF3UUrZZYKTWE5bzMteW05UXM) in RankaIris root (folder 0BymF3UUrZZYKNXotNlRWTm45TzQ).

## Pitfalls

- Gmail search "dinesh ranka tdr" is mostly ITAT/ITR/board-notice noise — the certificate was never emailed; it lives on Drive as jpg scans (created when uploaded to Drive, 2013; re-saved 2016).
- **Original physical DRC was handed to BBMP via consultant (Aug 2013) for endorsement**; the surrender letter asks for its return — the physical original may never have come back. Flag this to the user if they need the original for registration/RERA work.
- tesseract has only `eng` locally — no Kannada. Use vision_analyze for bilingual/handwritten DRCs; tesseract only for the typed sanction-plan table.
- Don't attribute the wrong TDR: `TDR- Panathur/Gunjur/Kodigehally`, `TDR Crescent Road`, `Velu TDR Files`, `BuxRanka TDR*`, `DRC List and Utilization Certificate List (TDR BY BDA)` are separate transactions/portfolios — walk parents up to the project folder before citing.
- Combine front+back scans into one PDF for delivery: `img2pdf` (available in Hermes venv) on the two jpgs.