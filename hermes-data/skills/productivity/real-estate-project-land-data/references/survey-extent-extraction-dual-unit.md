# Survey-wise Land Extent Extraction — TSR + JDAs + Legal Opinions → Dual-Unit Spreadsheet

**Worked example (2026-08-31, Sevaganapalli / Ranka Oasis, DRA folder `1sG1KlY-higI7vhoafHmyarS_qIWkspEW`):**
Prakash shared a project Drive folder and asked to "verify all the schedule properties and extract the
total land extent of each survey no, list in a new spreadsheet in hec/ares and acre/cent, plus total of
all extent — for Sevaganapalli land partners, DRA Realty and DRA Realty JDA lands".

## Scope rule (user correction, 2026-08-31)
When the user says "check only this drive links" / "scan only the documents drive links shared with you",
treat the SHARED FOLDER as the only source. Do NOT pull the investor portfolio workbook, prior-session
sheets, or other Drive locations as cross-reference — even if a loaded skill (e.g. draas-due-diligence-pack)
mentions them as canonical sources. Verification means: the documents inside that folder, and nothing else.
Prakash repeated the folder link and the scope instruction twice when I started reaching for other sources.

## Source documents inside the folder → what each carries
| Doc | What it gives | Extraction |
|---|---|---|
| TSR Part III "SCHEDULE OF PROPERTY" | Item No + Survey No + extent (Ac) per item, and a **final owner table** (Sl.No / Survey No / Extent / Owner/s / Patta No) | `pdftotext -layout` (text layer) + regex; use the final table as authoritative (owners!) |
| Legal opinions (advocate scans, e.g. Jeevanandam, N Manjunath) | "Survey No: X, an extent of H.A.C Hec Or Acre X.Y Cents [full extent]" | `pdftoppm -png -r 150` + `tesseract` |
| JDA agreements (scanned) | Schedule page: "SCHEDULE: DESCRIPTION OF THE PROPERTY ... aggregating to Ac X.Y" + per-survey extents | tesseract; schedule is usually near the END of the deed |
| ILR (TN Integrated Land Record) | Per-survey extent in H.A.C + patta + owner (owner name printable English even though text layer is Tamil) | `pdftotext` — grep owner; extent columns garbled, cross-check |
| Sale deed (text layer) | Schedule of Property with both units | `pdftotext -layout` |
| DTCP layout approval / sanction | Approved survey list + total (e.g. 304.16 ares = 30,416 sqm = 7.51 Ac, 130 plots) | scan → tesseract/vision |

## Units — the "hec/ares" and "acre/cent" the user asks for
- **Hec-Ares-Cent (H.A.C)**: TN/Karnataka metric triple `Hec.0.14.50` = 0 ha, 14 ares, 50 centiares.
- **Acre-Cent**: `Ac.0.36` = 0.36 ac = 36 cents (1 ac = 100 cents).
- Conversion constants: `1 ac = 0.404686 ha = 40.4686 ares`.
- Registration docs give BOTH: "Hec.0.14.0 (or) Ac.0.35" — build both display formats from a decimal-acre
  value so the sheet is self-consistent:
  - `fmt_cent(ac)`: `int(ac)`-`round((ac-int(ac))*100)` (watch 100-cent carry → +1 acre).
  - `fmt_hec(ac)`: decompose `ac*0.404686` into h / a / c with carry on 100.

## TSR Part III parsing (text layer)
```python
pat = re.compile(r"Item No\.\s*(\d+)\s*\n\s*Survey No\.\s*([0-9A-Za-z/]+)\s*measuring\s*([0-9¼½¾.\s]+?)\s*Acres", re.I)
# fraction glyphs: ¼→.25, ½→.5, ¾→.75 before float()
# "part" items parse too: "Survey No. 176/1B2D part measuring 0.03 ½ Acres"
```
Pitfall: the declared header total (12.74 Ac) vs sum of parsed items (12.36 in the first pass) — the
difference is unparsed fraction items + missing items; the END-OF-TSR owner table (34 rows in this case)
is the authoritative reconciliation source. Always read it.

## Sheet build pattern + the two traps that bit (2026-08-31)
1. `sheets.spreadsheets().create()` → the returned spreadsheet's default sheet id is **NOT 0**.
   `batchUpdate` with hardcoded `sheetId: 0` fails `400 Invalid requests[0].updateSheetProperties: No sheet with id: 0`.
   Fix: `meta = sheets.spreadsheets().get(spreadsheetId=sid).execute(); sheet_id = meta['sheets'][0]['properties']['sheetId']`.
2. Writing `0-36` / `0-04-05` style strings with `valueInputOption='USER_ENTERED'` silently converts them
   to DATES (read-back showed `2000-04-05`). Fix: write numeric columns (decimal Ac, decimal Hec) with
   USER_ENTERED, then RE-WRITE the text-format columns (Ac-Cent, Hec-A-C) with `valueInputOption='RAW'`.
   Verify by read-back and check the format columns are still strings.

## Result shape (Sevaganapalli totals, 2026-08-31)
- SLP (Sevaganapalli Land Partners): 7.33 Ac (17 TSR items incl 167/2D; plus 166/2B2 via SD 4350/2024 — layout survey NOT in TSR)
- DRA Realty: 1.505 Ac (TSR items + 177/1A1A — layout-only, patta 2000)
- Seller/partner lands per TSR (Suresh & Manjunath Reddy, Billa Reddy, Ravindra Reddy): 4.035 Ac
- JDA Ramesh Reddy (JDA 7963/2025): 166/1 0.35 + 167/1G 0.07 + 168/1B 0.53 = 0.95 Ac — NONE in TSR
- JDA K Harish (JDA 6157/2025): 177/1B 32.30c (Hec 0.1307) + 177/2A1 17.70c (Hec 0.0730) = 0.50 Ac
- GRAND TOTAL: 14.32 Ac = 14-32 Ac-Cent = 5-79-51 Hec-A-C
- TSR Part III reconciles: declared 12.74 = 12.87 sum (which includes 166/2B2 + 177/1A1A) − 0.13 layout-only extents. Report both the declared total and the reconciliation note.
- Flag discrepancies rather than silently picking a source (e.g. 176/1B2D: TSR 0.03½ acquired vs Jeevanandam opinion Hec 0.06.47 full extent — used TSR-acquired extent, noted the difference).