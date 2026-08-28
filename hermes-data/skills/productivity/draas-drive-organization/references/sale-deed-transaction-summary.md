# Sale Deed / ATS / GPA Transaction Summary from a Drive Document Folder

Extends `folder-index-spreadsheet.md`: after building a per-survey-number index sheet,
Prakash/NDR often wants (a) a **deed-type classification sheet** (all Sale Deeds / ATS /
GPA from 2012+ with Drive links) and (b) a **per-document transaction summary** (parties,
transaction date, schedule properties, extent). This is the full pipeline, verified on the
**Bestamanahalli** folder (2,391 files, 149 folders, Aug 2026).

## Step 1 — Classify by filename (no OCR needed)

Walk the folder tree (parallel BFS, thread-local services — see `folder-index-spreadsheet.md`),
then classify each file purely from its name:

```python
def classify(name):
    n = name.lower()
    if re.search(r'\bsale\s*deed\b|\bsale\s*dee\b|\bsald deed\b|\bsale-deed\b', n) or re.match(r'^sale\b', n) or 'sale doc' in n:
        return 'SALE DEED'
    if re.search(r'\bats\b', n): return 'ATS'
    if re.search(r'\bgpa\b|\bgeneral power of attorney\b', n): return 'GPA'
    if 'sanchaya' in n and re.search(r'\bs\.?\s?d\.?\b', n): return 'SALE DEED'
    if re.search(r'\bdeed\b|\bpartition\b|\bmortgage\b|\bmortagage\b', n): return 'DEED'
    return None
```

- Exclude `Thumbs.db`, `.onetoc2` notebooks.
- Deed fiscal year lives in the filename: `Doc no 1962-13-14` → FY 2013-14; `Sale 4313-09-10`
  → FY 2009-10. Century heuristic: `y >= 40 → 19yy else 20yy`. Filter `FY >= 2012` for the
  "from 2012 onwards" request.
- Party tag from filename: `sanchaya` → Sanchaya, `\bpk\b` → PK, `mahesh`/`nahar`/`ramesh`/`shiv`.
- Sheet layout that works: top rows = newest reference docs (2026 GPAs/survey lists) tinted gold,
  then FY≥2012 rows sorted by year desc, then no-year files (numbered scan batches like
  `7 Sy138 Sale Deed`) tinted grey with year "n/a (not in filename)". Columns: Sl No / Doc Type /
  Doc No / Year / Survey No / Party / File Name / Drive Link / Date.

## Step 2 — Batch OCR every PDF (background job)

All these scans are image-only; `pdftotext` returns ~0 bytes. Pipeline (see
`ocr-and-documents` skill for pitfalls):

1. Pull the 190 rows (id + metadata) from the index sheet via Sheets API.
2. Download each to `/tmp/bm_docs/NNN.pdf` (zero-padded int from the string Sl No).
3. `pdftotext` probe → if <80 chars, OCR first 3 pages: `pdftoppm -f P -l P -r 200 -png pdf prefix`
   then `tesseract prefix-*.png stdout --psm 6`. **Glob `prefix-*.png` — pdftoppm zero-pads
   page 1 as `-01.png`, a literal `-1.png` glob silently returns nothing.**
4. Save text to `/tmp/bm_docs/text/NNN.txt`, run as `terminal(background=True,
   notify_on_complete=True)`, poll progress with `ls text/*.txt | wc -l`.
5. ~190 docs × 3 pages @200dpi ≈ 25–30 min. Do NOT block; continue after notify.

## Step 3 — Parse transaction metadata from OCR text

Patterns that work on Karnataka registered-deed scans:

- **Date** (priority order):
  1. Deed clause: `made and executed on this the 05th day of September 2014`
  2. Registration footer: `Print Date & Time : 05-09-2014` (very reliable)
  3. Generic `DD-MM-YYYY`, but **reject 09/05/2003 and 09/05/2030** — that's the pre-printed
     "Document Sheet" form-header template stamp, NOT a transaction date.
  Month names OCR badly (`Aprit Roly` for April 2014) — fall back to the print-date footer.
- **Parties** (sale deed): `BY: <vendor>` ... `HEREINAFTER CALLED THE "VENDOR"` ...
  `IN FAVOUR OF : <purchaser>`. Cut party strings at `Aged about | S/o | W/o | Having its |
  Represented by | PAN | CIN:` and strip leading OCR junk (`^[\W_0-9]*`).
- **GPA parties**: `By this General Power of Attorney: <grantor> ... Do hereby appoint
  <attorney>` or `KNOW ALL MEN BY THESE PRESENTS THAT, WE <grantor> ... constitute, nominate
  and appoint <attorney>`.
- **Survey numbers**: `Sy No. 82-3`, `Survey No. 93`, `Sy.No. 93` — collect unique, cap ~10.
- **Extent**: `(\d+)\s*(?:acres?|Acre)` and `A-G guntas` patterns (only ~60/190 deeds state
  extent in text; the folder name often carries it — keep the Survey No column from the folder).

## Step 4 — Build the Transaction Summary sheet

Columns: Sl No / Doc Type / Doc No / Transaction Date / Party 1 (Seller-Grantor) /
Party 2 (Buyer-Attorney) / Survey Numbers / Extent / Transaction Summary / File Name / Drive Link.

- One-line summary: `SALE DEED (05/09/2014): Concept Infraestate Pvt Ltd → Sanchaya Land &
  Estate Pvt Ltd. Properties: Sy 99/5`.
- Tint grey rows lacking a date so the user can see extraction gaps at a glance.
- Reuse the same spreadsheet (add a tab) so the existing link stays valid.

## Bestamanahalli transaction chain (worked example, Aug 2026)

The 190 deeds reconstruct a 3-stage aggregation:
1. **2011–2012:** landowners (Chikkaramaiah/Ramakka, Ramaswamy, N. Krishnappa, Dontheneni
   Ravinder Rao, K. Muniyappa…) → **Mr. Prateek Kumar** (aggregator front) via ATS + sale deeds.
2. **2013–2014:** Prateek Kumar / Concept Infraestate Pvt Ltd → **M/s Sanchaya Land & Estate
   Pvt Ltd** (the bulk: Sy 98/99, 101, 134–142, 138…).
3. **2025:** Irrevocable GPA Sanchaya → **Pavanchand Nahar** (28/08/2025, 42 pp) + survey lists
   for Nahar (31 sy, 8A-37G) and Maheshanna (8 sy, 2A-16G).

Key IDs:
- Source folder `bestamanahalli` = `1MV5ceU-lNXl6ve5YOI4nzmMqPfEko0ne` (owner admin2.blr@draas.com)
- Newer "Bestamanahalli Land documents" = `1oK9ZijD9j8JjnUfmjQcma2EV5PnEv60P` (psingh, has the 2026 GPA scans)
- Index spreadsheet (delivered, 92 tabs after this work) = `1CYCeHdk2VfeVfSJzI6o56rQj6bbq5yuHYzR8rg-y6ug`
  (a duplicate `1eucBSi0EocvQUambdg_BhQQERhRBWZwt9mOOMRHoy6k` exists — use the delivered one)
- Use `HERMES_SESSION_USER_ID=psingh` + `service_name='google-draas'` (resolves to psingh@draas.com)

## Pitfalls

- **Two same-named spreadsheets**: "Bestamanahalli - Survey Number Document Index" exists twice
  (created minutes apart 2026-08-03). Always check `createdTime`/which one was delivered in the
  session before appending; both live in the same parent folder `0AL2CQJbQpzglUk9PVA`.
- **`f'{sl:03d}'` on sheet values** — Sheets returns row numbers as strings; cast `int()` first
  or you get `ValueError: Unknown format code 'd'`.
- **Party-name bleed**: OCR drags address lines into the party block. The marker-cut list above
  handles it; spot-check ~10 rows after building the sheet.
- **Ramesh Reddy caveat**: a party named "Ramesh (DRA?) Reddy" may NOT be in this folder at all —
  Ramesh Reddy GPA/JDA files live under Sevaganapalli / Ranka Oasis (different projects). Don't
  merge them into the Bestamanahalli sheet without asking.
