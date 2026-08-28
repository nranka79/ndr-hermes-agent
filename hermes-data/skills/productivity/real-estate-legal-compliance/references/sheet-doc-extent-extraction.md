# Sheet → Documents → Per-Survey Extent Extraction

**Trigger:** User shares a Google Sheet (document index) listing survey numbers, document names, and Drive links (sale deeds / agreements / GPAs), and asks to "extract all survey nos and land extents as per the documents" / "scan all documents and get exact extents of each survey no".

**Verified:** Aug 2026, Satvik Developers — Byadarahalli Legal Documents (25 docs, sheet `1aCTuKcDjH2t8G4ANyJkbhuXbXPPF7yWETQ3weQFsMN4`, tab 'Documents').

## Workflow

1. **Read the index sheet.** `sheets.spreadsheets().values().get(range="'Documents'!A1:Z200", valueRenderOption='UNFORMATTED_VALUE')` for structure. Then **re-read with `valueRenderOption='FORMULA'`** to get FULL hyperlink/file-IDs — the displayed value truncates Drive URLs mid-ID (false 404s if used directly). Extract file_id with `re.search(r'[-\w]{25,}', link)`.

2. **Verify every file** via `drive.files().get(fileId=..., fields='id,name,mimeType,size')` — confirms the sheet's link matches a real Drive file and gives the authoritative filename. All should be `application/pdf`.

3. **Download all** with `drive.files().get_media()` + `MediaIoBaseDownload` into `/tmp/<project>_docs/` with row-prefixed names (`02_Sale_deed...pdf`).

4. **Probe text layer** with `pdftotext -l 2 file - | wc -c` + `pdfinfo` for page count. Deeds from the Karnataka registration system are mostly scans with a PARTIAL OCR text layer (1,200–2,300 chars on 11–20 pages) — enough to read recitals via pdftotext directly. `len=0` = pure scan → OCR (below). Kannada-language docs give garbled Devanagari-ish junk from eng OCR → needs `kan` tessdata.

5. **Extract from text-layer docs** — the deed recital is the authoritative extent source:
   ```regex
   (?:The Vendors? are the absolute owners? of the|bearing) Sy\.?\s*No\.?\s*
   (\d+[A-Za-z0-9/.]*)\s*(?:\(Old Sy\.?\s*No\.?\s*[^)]*\))?\s*,?
   measuring to an extent of ([\d\-\.]+)\s*(Acres?|Guntas?)?\s*([\d\-\.]*\s*Guntas?)?...
   ```
   Standard clause: **"bearing Sy. No. 219/5 (Old Sy. No. 45 & 219 & 219/1), measuring to an extent of 0-07 Guntas"**. Formats: `0-07 Guntas`, `3 Acres 34 Guntas + 0-06 Guntas of A kharab land`, `1Acre 29 Guntas`, `0-05.08 Guntas`, `02-00 (ಎರಡು ಎಕರೆ)` (Kannada, = 2 Acres 0 Guntas). Extent format is **Acres-Guntas** (`0-07` = 7 guntas; `A G` = acres guntas, 40 guntas = 1 acre).

6. **Multi-survey deeds** use **"ITEM NO. 1 / 2 / 3 OF THE SCHEDULE PROPERTY"** blocks — each item has its own Sy No + extent. Parse each item separately; a single deed can cover 3+ distinct surveys (e.g. 175/4 + 175/6 + 176/2 in one sale deed).

7. **Cross-check flow-of-title parent extents.** Each deed narrates the parent survey (e.g. "larger extent 5 Acres in Sy No. 175 → partitioned 0-15G / 0-24G / 2A 04G..."). Distinguish *parent/root* extent from the *subdivided schedule property* extent — the delivered per-survey table must list the schedule (conveyed) extent, not the parent.

8. **Pure scans (len=0)** → `pdftoppm -png -r 200 file.pdf /tmp/png_<row>` then `tesseract <page> stdout --psm 6 -l eng`. Property clause usually on page 3–4 (after party list). For 30+ page GPAs with dozens of executants, the schedule clause is well into the doc (page 19+); search OCR output for `bearing|extent|measur|acre|gunta`.

9. **Kannada docs** → download `kan.traineddata` into a writable tessdata dir and use `-l kan+eng` (see `references/kannada-land-doc-ocr-patterns.md` extent section).

10. **Deliver** — compile a new tab (`Extents_By_Survey`) in the SAME spreadsheet (ADD-NEW-TABS-ONLY rule — never edit existing tabs), columns: S.No | Survey No (sheet) | Document | Reg No | Date | Survey as per document | Extent as per document | Notes. Row-wise expansion for multi-item deeds (merge first col). Format header bold on navy. Present per-survey summary in chat + total (convert A-G to decimal acres: `A + G/40`).

## Pitfalls

- **Sheet's Survey Number column can be WRONG vs the actual deed.** Verified twice in Byadarahalli: sheet said `175/4,6,8` but deed No. 8940 actually conveys **175/4, 175/6, 176/2** (no 175/8 at all); sheet row said `209/1,2,3,4` but the doc (No. 5911) is **Sy 210, 4 Acres** (duplicate of the next row). ALWAYS read the deed's own recital/schedule and flag mismatches to the user with ⚠ — never silently trust the index.
- **OCR garbling of survey numbers**: `173/4` ↔ `175/4`, `131`/`i31`/`181`, `13/4`↔`18/4`, `45/6`↔`45/5B`, `Sy Nö.15`↔`Sy. No. 45`. When a number looks off, cross-check against the deed's filename, the "Old Sy. No." parent, and boundary neighbors (`East by: Sy 175/5; West by: 175/3`).
- **Two rows can be the same document** (same Reg No + same file content under different sheet rows) — dedupe by registration number + content, not filename.
- **Excel-serial dates** in sheet Date columns (e.g. `45231` = 11-01-2023). Convert when compiling; trust the deed's own date clause.
- **Kharab land**: extents often stated as `3 Acres 34 Guntas and 0-06 Guntas of A kharab` — report both the net and kharab parts; totals should use the net usable figure but the kharab must stay visible.
- **Registration sheet header date is a template artifact** (printed `09-05-2003`/`09-05-2030` on every page) — NOT the transaction date. Use the "made and executed on this the X day of..." clause.
