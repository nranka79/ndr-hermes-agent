# RTC Extraction → Spreadsheet (batch Kannada land records)

Class of task: user drops a Drive folder of Karnataka RTC (Record of Rights,
Tenancy & Crops) PDFs and wants a survey-wise summary spreadsheet. Worked
2026-08-06 on the LG Champions layout folder (49 RTCs, Doddamarali +
Varamallenahalli, Nandi hobli, Chikkaballapur).

## RTC Form 2 layout (one page, Kannada, Bhoomi portal print)
- Header: ತಾಲ್ಲೂಕು (taluk) / ಹೋಬಳಿ (hobli) / ಗ್ರಾಮ (village), survey no + hissa
- Sec 3 (ಖೇತವಾರು): ಒಟ್ಟು ವಿಸ್ತೀರ್ಣ (total extent), ಪೂಟ್ ಖರಾಬ್ (ಅ) = Kharab A,
  ಪೂಟ್ ಖರಾಬ್ (ಬ) = Kharab B, ಉಳಿದದ್ದು (remaining)
- Sec 4: ಕಂದಾಯ revenue (ಭೂಕಂದಾಯ, ಜೋಡಿ, ಸೆಸ್ಸು, ನೀರಿನ ದರ)
- Sec 9 (ಕಚ್ಚೆ/ಸ್ವಾಧೀನದಾರ): HOLDER names (ಬಿನ್ = son of, ಕೋಂ = wife of) +
  extent + **KHATA number = trailing digits right after the extent**
  (e.g. `1.16.08.00 24` → khata 24; often concatenated `1.16.08.0024`)
- Sec 10: occupancy type (the MR entry that created the holding)
- Sec 11 (ಇತರೆ ಹಕ್ಕುಗಳು ಮತ್ತು ಋಣಗಳು): Rights = MR entries with date+type
  (ಕ್ರಯ/ಖರೀದಿ sale, ದಾನ gift, ವಿಭಜನೆ partition, ಆದೇಶ order, court stays with
  O.S./RSA numbers); Liabilities = co-op/bank loans with ₹ amounts
- Sec 12: cultivation (crops + CULTIVATOR names — cultivators are NOT holders)

## Extent format
- `A.G.00.00` = acres.guntas (1 acre = 40 guntas); THIRD field = anna,
  16 anna = 1 gunta (e.g. 1.16.08.00 = 1A 16G 8 anna = 1A 16.5G)
- Consistency check: total = kharab A + kharab B + remaining. Flag rows that
  don't balance — but remember anna arithmetic before calling it an error
  (1A-17G − 8 anna = 1A-16G-8An is correct, not a mismatch).
- Display convention used: `1A-15G`, `2A-1G-8An`.

## Workflow that works
1. List Drive folder: `files().list(q="'<folder>' in parents and trashed=false",
   pageToken=...)` — **kwarg is `pageToken`, NOT `page_token`** (TypeError).
2. Download all PDFs with `MediaIoBaseDownload` loop (~940KB each, 1 page each).
3. `pdftoppm -png -r 200` → PNGs.
4. Batch tesseract Kannada: `TESSDATA_PREFIX=/data/hermes/tessdata tesseract
   <img> <out> -l kan` → good structure, noisy digits/names (0/6/8, 1/7
   confusions). Use as the skeleton, never as the final answer.
5. Exact extraction: `vision_analyze(image_url=..., also_describe_visually=true)`
   — this flag forces the full vision-model pass (OpenRouter Gemini) which reads
   Kannada RTCs accurately. WITHOUT the flag, free OCR path returns garbage for
   Kannada.
6. Delegate per-image vision calls to parallel subagents (3 × ~17 images,
   vision+file+terminal toolsets, each writing JSON to a group file). Instruct:
   one vision call per image, also_describe_visually=true, quote digits exactly,
   list ALL holders, empty string when a field isn't printed.
7. Merge JSON, run the extent-balance check.
8. Re-verify ambiguous rows YOURSELF with crop+zoom: crop section 9 region
   (≈ x 30–100%, y 13–40% of page), upscale 2–2.2x LANCZOS, vision_analyze
   again. This resolves holder-name and khata disputes definitively.
9. Build sheet via Sheets API: create → values().update(RAW) →
   batchUpdate (bold header, DRA navy bg #1A1A2E / gold text #D4A53C,
   freeze row 1, autoResizeDimensions). Verify by reading values back.

## Pitfalls (all hit live Aug-2026)
- Subagent extraction is a good draft but MUST be spot-checked on a sample:
  - They conflate cultivators (Sec 12) with holders — Var 12 reported 3
    "holders", crop verification showed only 1 real holder in Sec 9.
  - They garble names — Sy 23 "Khushi/Neelagiri" were crop names; the real
    holder is Thopu (ತೋಪು).
  - Full-page vision can drop the father part of a name — Sy 5-1 read as
    "B.C. Muddanna" full-page, crop showed "B.M. Sundar bin B.C. Muddanna".
- Crop too low/narrow misses Sec 9 and hits the cultivation table — crop
  generously (full right half, y 13–40%), then zoom.
- Khata genuinely absent on some RTCs (Var 16). Others have it but the
  extraction missed it — always crop-verify khata before leaving blank.
- Court stays (DC orders, O.S./RSA numbers) and loan charges go into
  Transaction Details; surface them to the user as explicit watch items in the
  final reply — that is the actionable part of the deliverable.
- Filenames encode village + survey no — use them to label rows and to split
  same survey numbers across villages (Doddamarali Sy 12 vs Varamallenahalli
  Sy 12 are different parcels).
- Moving the finished sheet into the source folder may 403 if the folder lives
  on a shared drive / is owned elsewhere — leaving it in the same Drive at
  root is acceptable; just verify ownership and share the link.
