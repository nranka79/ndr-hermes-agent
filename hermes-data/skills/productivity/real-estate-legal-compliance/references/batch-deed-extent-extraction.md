# Batch Registered-Deed Extent Extraction (survey → exact extent)

**Trigger:** User shares a Google Sheet listing registered deeds/agreements (columns: Survey Number, Document Name, Document Link, Document Type, Registration No, Date) and asks to "extract all survey nos and exact land extents as per the documents, scan all the documents." Verified 2026-08-14 on the Satvik Developers — Byadarahalli Legal Documents sheet (25 docs, Devanahalli taluk).

## Pipeline

1. **Read the sheet, then re-read links with FORMULA render.**
   - First pass: `spreadsheets().values().get(range="'Documents'!A1:F30")` to see the rows.
   - The Document Link column is often **truncated in display** (`.../1Q4EC8du_q0NIrtGZB73l_c1Xtmk`). Re-read with `valueRenderOption='FORMULA'` to get the full hyperlink, then regex-extract the file ID: `re.search(r'[-\w]{25,}', link)`.
   - Verify every file exists: `drive.files().get(fileId=..., fields='id,name,mimeType,size')` — catches false 404s from truncated IDs.

2. **Download all PDFs** via `drive.files().get_media()` + `MediaIoBaseDownload` into `/tmp/<row>_<name>.pdf`. Use the spreadsheet row number as a filename prefix so results map back to rows.

3. **Probe text layer first** (`pdftotext -l 2 file.pdf -` → char count):
   - Most Karnataka registered deeds have a **partial OCR'd text layer** (Kannada registration header garbage + readable English recitals). `pdftotext` works — no vision needed.
   - Pure scans return `<100` chars → `pdftoppm -png -r 200` + tesseract.
   - Kannada-only deeds (agreements/GPA in Kannada) return garbled Kannada via `-l eng` → use Kannada tessdata (`TESSDATA_PREFIX=/tmp/tessdata tesseract img stdout --psm 6 -l kan+eng`). See `ocr-and-documents` §Kannada OCR.

4. **Find the extent recital with regex** — the key sentence is consistent:
   `bearing Sy. No. X (Old Sy. No. Y), measuring to an extent of N Acres / Guntas`
   Search: `re.finditer(r'bearing.{0,30}Sy\.?\s*No\.?\s*[^,]{0,80}', text, re.IGNORECASE)`.
   Also pull the SCHEDULE section (`ALL THAT PIECE AND PARCEL`) for the final word.

5. **Watch the multi-item deeds (ITEM NO. 1/2/3).** A single registered deed can convey MULTIPLE survey numbers, each with its own extent. The sheet's "Survey Number" column may be WRONG or incomplete:
   - Satvik 20-10-2022 deed (sheet said "175/4,6,8") actually conveys **175/4 (0-04G), 175/6 (0-20G), 176/2 (1A 20G)** — no 175/8 at all, and 176/2 wasn't listed.
   - Sheet row "209/1,2,3,4" (doc No. 5911) is actually **Sy 210, 4 Acres** — same as the next row (duplicate).
   - **Always report the per-document survey+extent as authoritative and flag sheet-column discrepancies.**

6. **Cross-check against RTCs** if the user says "yes" to reconciliation: Drive search `fullText contains '<village>' and name contains 'RTC'`, match by survey, compare extents. See `rtc-form16-reading.md` §RTC batch OCR.

## Extent formats encountered

| Format in deed | Meaning |
|---|---|
| `0-07 Guntas` / `0.07` | 7 guntas |
| `1 Acre 13 Guntas` / `1A 13G` | 1 acre 13 guntas |
| `3 Acres 34 Guntas + 0-06 G A-kharab` | net 3A34G + 6G kharab deduction |
| `02-00 (ಎರಡು ಎಕರೆ)` (Kannada) | 2 acres 00 guntas |

## Pitfalls

- **Recital vs FLOW OF TITLE discrepancy:** Sy 181 deed recital says 3A 34G + 0-06G kharab; flow-of-title section says originally 3A 35G + 05G kharab. The SCHEDULE section is authoritative — use it, note the variance.
- **Multi-executant GPA (34+ people):** the property schedule appears on a LATER page (GPA Sy 216: page 19-21 of 33), not page 1-3. OCR pages beyond the party list.
- **Duplicates in sheet:** two rows can reference the same document (same reg No., same file content, different file IDs) — dedupe by content, flag in notes.
- **Kannada extent parse:** `02-00 (ಎರಡು ಎಕರೆ)` — the number is the reliable part; Kannada words confirm acres vs guntas (ಎಕರೆ = acre).
- **Delivery:** append findings as a NEW tab (`Extents_By_Survey`) in the same spreadsheet — never edit existing tabs (Prakash rule). Format header row bold navy. Lead the chat summary with the per-survey extents, then the ⚠ discrepancies, then the aggregate acreage (sum of per-survey extents in decimal acres; 1 gunta = 1/40 acre).
