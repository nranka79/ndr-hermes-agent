# Oasis plot-facing verification — DTCP approval print (2026-09-11)

Task: user uploaded `2026_01_13__Sevaganapalli__DTCP_Layout_Plan_Approval___Krishnagiri.pdf`
and asked "extract each plot facing from this sanctioned plan" into the
`DTCP Approved Plan (13.01.2026)` tab of `20260910 Ranka Oasis Unit Nomenclature – Phase I`
(spreadsheet `1rLNLCs9aJafH6gkBWs5VH1Mw9GvS9zzD1olsQ2Pk_x0`).
Master Inventory sheet (`1jHjOIUQSMVwVQewFES2d77D9SaHK2DcUbbTBvwwRH8o`, tab
`As per sanction layout`) was used as the dims source.

## Document anatomy (the recurring trap)

The "DTCP Layout Plan Approval" file is a **1-page letter-size approval LETTER**,
not a plottable layout sheet:

- Producer `Microsoft Print To PDF` → **no text layer** (`pdftotext` ≈ empty),
  **no embedded raster** (only a 201×201 logo/stamp), but **~8,700 vector
  drawings** — thousands of tiny glyph-fill rectangles (median ~1.6×1.6 pt) =
  outlined text. Signature of a print-as-vector PDF: never pdftotext it, render
  at 300 DPI and OCR/vision.
- Left half of the page = small **plot layout drawing** (plots 1–130, hatched
  road bands: 10.00 / 9.00 / 7.20 m layout roads, 6.60 m panchayat road at the
  south entry, Parks 1 & 2, TANGEDCO pocket) + a **land boundary line diagram**
  (survey nos + side dimensions like 76.00 / 36.00 / 15.03 / 44.80 m).
- Right half = Tamil approval text, area statement, 15 conditions, signatures.
- Sanction numbers (useful for notes): ROC RJDVYJD1/2026/TCP dt 13.01.2026; SWP
  Layout No. 03/2026 & 02/2026. Area statement: site 30,416.00 sq.m, roads
  10,193.49, net 20,222.51, OSR park 2,065.91 (10.21%), public utility 106.63
  (0.52%), TANGEDCO 247.48 (1.22%), 130 house sites; variable plots 36, 79,
  82–86, 93–115, 124, 130 = 2,161.27 (10.68%).

## KEY finding — facing cannot be read off the print

The approval print has **NO north arrow and NO facing labels** on plots.
Per-plot facing on the sheet is a **derived** value: the road-frontage side of
each plot, north-up, using the same orientation as the `As per sanction layout`
dims transcription (E/W/N/S columns). State this on the sheet instead of
pretending the values were labeled.

## Right scope when the print is tiny

Do NOT try to re-derive a full 130-row facing table from a letter-size print —
vision model reads **flip frontage sides between zoom passes/tiles** (same plot
read Left then Right; verified on plots 21, 81, 82, 86, 87, 90, 91). Instead:

1. Read the drawing's **road/block structure** (which road runs where, which
   plot blocks sit either side).
2. **Block-verify the existing facing column** against that structure — e.g.
   Ranka Oasis: entry road south → plots 6–8 South; middle 10.00 m road →
   56–62 North; 9.00 m internal road → 81–86 East / 87–92 West; next 9.00 m
   road → 93–102 East / 103–115 West; top-right 10.00 m & 7.20 m roads →
   116–130; plot 6 fronts Park 1 (not a road).
3. Append **source-note rows** under the tab's existing note (e.g. rows 134–136)
   documenting the sanction reference, the derivation rule, and the ambiguous
   plots. Do NOT overwrite values on shaky reads — keep Master values and flag.
4. Offer the full-size master plan (on Drive: `Oasis Master Plan 10.09.26-Sheet
   1.pdf`) for a readable per-plot re-read.

## Working vision path when vision_analyze is down

`vision_analyze` returned `503 no LLM keys configured` (dead OpenRouter vision
key). Working fallback = the ocr-and-documents ladder Step 2b:
`LLM_FREE_POOL` (container env, JSON array) → entries with `provider == "gemini"`
→ direct AI Studio `generateContent` with model `gemini-3-flash-preview` +
`inline_data` base64 JPEG (not a data URL). It read the Tamil page, the plot
numbers, road widths and block frontages reliably at full-page and crop scale.
Tile the drawing region into overlapping crops (2×3), upscale 1.7–2.2× LANCZOS,
prompt with an explicit plot# → frontage-side table. Note: tesseract has only
`eng`/`osd` locally — no Tamil traineddata; the Gemini pool key is the only
Tamil-capable read path unless TESSDATA_PREFIX kan/tam is installed.

## Sheet-write mechanics

- `_load_credentials_direct` now takes **one** positional arg
  (`service_name='google-draas'`); the old 2-arg form
  `(user_id, service_name)` raises `TypeError: takes from 0 to 1 positional
  arguments`. Run via `terminal()` (not execute_code sandbox) with
  `sys.path.insert(0, '/opt/hermes')`.
- Append notes with `values().update` on explicit rows (A134:A136) using
  USER_ENTERED; verify readback before reporting.