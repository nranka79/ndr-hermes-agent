# TSR Part I → Drive Folder Audit (missing docs / duplicates / FMB-patta coverage)

When Prakash/ndr sends a Title Search Report (TSR) PDF + a Drive folder link and asks
"does this folder have all the documents furnished, any duplicates, are all survey FMBs
and pattas there, list missing" — the Sevaganapalli TSR (CMS-IndusLaw, Oct-2025) audit
worked like this. Worked example: folder "Oasis - print" (262 flat files, no subfolders),
TSR Part I = 107 items.

## Access (identity override — REQUIRED for psingh folders)

Folder link 404s under ndr's token (`File not found`) — it belongs to psingh@draas.com.
Run all GWS scripts with:
```
HERMES_SESSION_USER_ID=psingh python3 - <<'PY'
...
creds = _load_credentials_direct('google-draas')   # resolves to psingh@draas.com
PY
```
Verify with `svc.about().get(fields='user')` → emailAddress. (See draas-drive-organization
pitfall for the full diagnostic chain.)

## Step 1 — Parse TSR Part I (107 items)

- Slice `txt[find('PART-I') : find('PART-II')]`, then split on `^\s*(\d{1,3})\.\s*` with
  1 ≤ num ≤ 107. Continuation lines append to current item.
- Extract Part III survey schedule from the `PART – III` → `PART – IV` slice ONLY:
  `re.finditer(r'Survey No\.\s*([\d/]+[A-Za-z0-9/]*\s*[\d/½]*[A-Za-z]*)\s*measuring', part3)`
  — 34 surveys on Sevaganapalli. Handle the `176/1B2D part` variant (strip 'part').

## Step 2 — Match documents (the matcher engine)

Extract (docno, year) candidate pairs from BOTH TSR items and folder filenames, then match
docno + year ANYWHERE in the filename — NOT strict regex. Strict regex produces false
negatives on real DRA filenames:
- `doc no 1834 dtd 26-04-1990` (year inside dtd date)
- `Sale deed no. 4515` (bare docno, no year token)
- `2011123 Agreement of Sale No 12988 0f 2017` ("0f" typo for "of")
- `Release Deed Certified Copy no  4796` (double space)

Robust pattern set per filename: `no X of YYYY`, `no X/YYYY`, `no X YYYY`, `doc no X dtd
YYYY`, plus a bare-number fallback that requires the TSR year to be present in the same
filename. Match docno+year; fall back to docno-only only when unique.

Person-name matching for death certs / LHCs — spelling variants are the norm:
- Guvva Reddy = "Goova Reddy" file
- G.Nagi Reddy = "Nagareddy son of Guvareddy" file
- Yellamma ≠ Yella Reddy — do NOT let prefix matching conflate them
Match on first-name token ≥5 chars, not substring of the full person string.

## Step 3 — Pattas: the number is in the PDF TEXT, not the filename (key insight)

TN e-services patta PDFs have real text layers ("Tamil Nadu Govt / Department of Revenue /
Land ownership details…"). Filenames name the SURVEY; the PDF body carries the patta number.
Batch-download all `patta`-named files, run `pdftotext -layout`, regex
`Patta No\s*:?\s*([\w/-]+)` (also try `[Pp]atta\s*(?:No|Number|no)?\.?\s*:?\s*(\d+)` on
multi-page scans). Worked examples:
- "Copy of patta 1581c3.pdf" = **Patta No 1843** (TSR #95, Suresh/Manjunath) — NOT #85's 1842
- "Copy of Patta 158(1B2).pdf" = 471, "Copy of patta 158(1A4).pdf" = 725 (→ TSR #94/#96's
  "Patta 725 for 1C9A / 1B2" are NOT matched by the 1A4 file — report as missing)
- "Copy of Patta 1672B.pdf" / "patta158(1B5).pdf" = 204 (Billa/Billaretti — matches TSR #103)
- Multi-survey pattas repeat: Patta 25 appears under 167(1E), 167 2C, 158(1A5), 158(1A6), 158(1B3)
  — same-number files ≠ duplicates, they're one patta covering several surveys.

Online patta PDFs hide under "Land Registered" names — check before declaring online pattas
missing: "Copy of Land Registered in DRA Realty for Sy no 158.pdf" = Patta 2058 (TSR #102),
"land Registered under DRA Realty in TN.pdf" = 2000, "under Sevaganapalli land Partners.pdf"
= 1922.

## Step 4 — FMBs: bare "Copy of <survey>.pdf" files ARE online FMBs

The flat files named just `Copy of 167 1G.pdf`, `Copy of 158 1A1A.pdf`, `Copy of 1663A.pdf`
are TN online FMB printouts (Survey and Settlement Dept, "Scale 1:263", ~146-160 KB).
Confirm one with `pdftoppm -f 1 -l 1 -r 120 -png file.pdf page` then `vision_analyze` on the
PNG — **vision_analyze cannot read PDFs directly** ("Only real image files are supported"),
always pdftoppm first. Files explicitly named `...fmb...` or `FMB 167-2D` are the manual FMBs.

## Step 5 — Duplicates: size-group first, then MD5-verify

Filename normalization misses same-content/different-name copies. Group ALL files by byte
size; groups >1 are candidates (scanned PDFs of the same doc have identical bytes). Then
download and MD5-hash only the candidates. In Oasis-print: 12 confirmed identical pairs, e.g.
- "Copy of EC from 19750101 To 20230304 SyNo.158/1.pdf" == "Copy of EC from 01011975-03042023.pdf" (15,092,489 B)
- "GPA 12434 From Sarojaamma…" == "Copy of GPA From Sarojaamma…" (1,159,414 B)
- "Copy of partition dude survey number 167_2…" == "Copy of 19610610 partition deed sy no. 167/2&1508/1…"
CAUTION: equal byte size alone is NOT proof for TN patta printouts — different surveys can
share template byte size (156,420 B for Patta 158(1A5) vs 158(1A6) — different docs). MD5 is
the arbiter.

## Step 6 — Deliverable

Prakash asked for the missing list "here" (in chat) — deliver in Telegram bullets grouped by
type: FMBs missing (by survey), deeds missing (TSR # + docno), certificates missing, patta
numbers not present as listed. Add a short survey-wise FMB/patta coverage verdict (Part III
surveys) and the verified duplicate pairs. Offer to log into the DocMatrix MISSING_DOCUMENTS
sheet rather than doing it unprompted.
