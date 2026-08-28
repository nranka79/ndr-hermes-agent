# TSR Part I Folder Audit (Sevaganapalli / Oasis-print worked example, 2026-08-11)

Prakash sent `DRA-Sevaganapalli-TSR-20251014-V2-SV.pdf` (CMS-IndusLaw, 43 pp) + a Drive folder `Oasis - print`
(psingh-owned, `1sG1KlY-higI7vhoafHmyarS_qIWkspEW`) and asked: does the folder hold every document on the
TSR Part I (DOCUMENTS FURNISHED) list? any duplicates? per-survey FMB/patta coverage? missing list?

## Result shape (what to deliver)
- Status per Part I item: ✅ matched file / ❌ NOT FOUND / ⚠️ mismatch (same doc no, wrong year/type).
- Survey-wise FMB + Patta coverage matrix for the Part III schedule.
- Duplicate pairs list (identical MD5), missing list grouped by type (FMBs / deeds / certificates / pattas).
- Offer to log into MISSING_DOCUMENTS sheet.

## Workflow
1. `pdftotext -layout` the TSR → text file (CMS-IndusLaw PDFs have a text layer — no OCR needed).
2. Parse Part I: slice text between `PART-I` and `PART-II`, then line-regex `^\s*(\d{1,3})\.\s*(.*)$` for
   S.No 1..107; append continuation lines to the current item.
3. Index the Drive folder with the Drive API. psingh-owned folders 404 under ndr's token — run with
   `HERMES_SESSION_USER_ID=psingh` + `service_name='google-draas'` (see draas-drive-organization pitfall).
4. Match each item to filenames by docno+year tokens ANYWHERE in the normalized name. Filename patterns that
   break a strict `No X of Y` regex:
   - `doc no 1834 dtd 26-04-1990` (year in a dtd date)
   - `19950816 Sale deed no.4515.pdf` (year in the 8-digit date prefix)
   - `No 12988 0f 2017` (typo "0f" instead of "of")
   - `GPA 12434 From Sarojaamma & Otrs To Pavankumar.pdf` (no year at all)
   - `doc no.3470.pdf` (no year — docno-only weak match when unique)
   Match rule: docno present AND year present in filename (year may come from `YYYYMMDD` prefix or `dtd YYYY`);
   else docno-only as a weak hit and report it as ⚠️.
5. Duplicates: normalized-name equality + identical byte size → strong suspect; CONFIRM by downloading and
   MD5-hashing. In the worked example 12/16 same-size groups were true dupes; 4 were coincidental — TN patta
   template PDFs share sizes (e.g. Patta 158(1A5) vs 158(1A6), both 156420 bytes, different pattas). Never
   report same-size as duplicate without the MD5 check.
6. Pattas: files named by SURVEY (e.g. `Copy of patta 1581c3.pdf`) are TN e-services printouts with a TEXT
   LAYER: `pdftotext` → `Patta No : 1843`. So `patta 1581c3.pdf` is Patta 1843 (TSR item #95,
   Suresh/Manjunath) — the filename's survey alone is misleading. Always extract the patta number from the
   PDF text, then map to TSR items. Batch: download all patta-named files, `pdftotext` each, table of
   patta-no → surveys → owners.
7. FMBs: bare `Copy of <survey>.pdf` files (e.g. `Copy of 167 1G.pdf`) are ONLINE FMBs — first page via
   `pdftoppm` + vision OCR shows "Survey and Settlement Department, Government of TamilNadu ... Scale 1:263".
   Manual FMBs are paper scans. Explicitly-named FMB files: `Copy of FMB 167-2D.pdf`,
   `Copy of 167(1B)FMB.pdf`, `Copy of fmb 167(1F).pdf`. Multi-doc bundles named
   `20230413-sy.no-...-tax paid receipt,patta applied copy,fmb,udr,patta,adangal.pdf` contain FMB pages — count
   them as FMB coverage for the surveys in the name.
8. Online patta printouts live under "Land ownership details" header; `Copy of Land Registered in DRA Realty
   for Sy no 158.pdf` = Patta 2058 (M/s DRA Realty), etc. Match these to the TSR's "Online Patta No." items.
