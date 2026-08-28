# Family Lab Values Tracking System

DRAAS family medical records pipeline: every lab report is renamed, filed to the member's
Medical folder on Drive, indexed in the member's Medical Report Index spreadsheet, and every
parameter is appended to that spreadsheet's **Lab Values** tab for trend tracking.

## Members map (as of Aug 2026)

| Member | Medical folder (Drive id) | Report Index spreadsheet id | Index tab | File prefix |
|---|---|---|---|---|
| NDR (Nishant) | `0B1Oc8cSaJXPGT1JPMVlfajFnTmc` | `1gsIQXoVis0TG3eCZFmg0AVzCPG525doPK0ifTIqz2rg` | Sheet1 | `NDR` |
| KDR (Kanta) | `0B1Oc8cSaJXPGUUtVbTJHb0Y3V2s` | `1DjfOon0dY74ReAREt5GAPpPNWM464lYvJYrESqiUB2g` | Sheet1 | `KDR` |
| RNR (Roshini) | `0B1Oc8cSaJXPGUDBMR3Z1MGJZeWc` | `1rhK4XONTYmBmYpRyKMpLFMn4UupLJ_Gufv02RmE570E` | Sheet1 | `RNR` |
| RVR (Rivaan) | `0BymF3UUrZZYKVFY2UzkxUEI0UlU` | `1YJ8iYEAHCVjBRaaE_iU3_Q8aEJZ1aSP_WXNk0w7RXyA` | Sheet1 | `RVR` |
| Ruhaan | `0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k` | `1E14iA3xDdoBaC0Sdlim6r6MipmSzNkKqFLaV2dXvHQU` | Reports & Prescriptions (+ BILLS) | `Ruhaan` |

Receipts/invoices: **NDR Medical > Invoices** = `1vy22sktwa1aD4bYDRpCad38lxM5P3RGT` (payer is NDR).

Duplicate/legacy index sheets exist for some members (KDR: `1cd4kwHb_QumUKxw-7hCpoeFeruKCcjyNqVKWud4FvVA`;
RNR: `1VB6FsfTAOiDc8p2X7v2o94zTGERhocRtzK4eiOPXhxA`). **Canonical sheet = the one whose Drive
parent is the member's Medical folder.** Verify by checking `parents` on the file.

## Lab Values tab schema

```
DATE | TEST NAME | CATEGORY | VALUE | UNIT | REF LOW | REF HIGH
```

- Dates as ISO (YYYY-MM-DD). Header bolded + frozen row 1, 1000-row grid.
- Create the tab if missing: Sheets API `addSheet` with title 'Lab Values'.

## Pipeline per report

1. `pdftotext -layout file.pdf out.txt` — Thyrocare/RLS reports (Healthy 2026 Package, CORT,
   HBA, etc.) have a text layer; no OCR needed. The "Tests Outside Reference Range" summary is
   usually on page 3 — grab those flags first.
2. Rename: `YYYYMMDD <Prefix> R <Test> <Lab>.pdf` — e.g. `20260816 NDR R Cortisol.pdf`,
   `20260816 RVR R Healthy 2026 Package.pdf`. Multi-test: plus-separated
   `20260816 NDR R Healthy 2026 Package + INSFA + Homocysteine + Testosterone.pdf`.
3. Upload via Drive API `MediaFileUpload`, `supportsAllDrives=True`, parent = member's folder.
4. Index: read index tab, compute max SL.NO (numeric parse — values come back as strings),
   append row `[sl, 'REPORT', date, filename, link]` with USER_ENTERED + INSERT_ROWS.
   Ruhaan's index has 6 columns (duplicate REPORT NAME col F) — append A:F.
5. Extract parameters → normalized TEST NAME (below), category, value, unit, refs. Keep
   `<`-prefixed values as text (e.g. `<1.003`). USER_ENTERED keeps numeric strings as numbers.
6. Append to `Lab Values!A1:G1` in one `values().append` call.
7. Trend analysis: pull member's historical rows grouped by TEST NAME, compare last 1–3 prior
   readings, flag out-of-range + trends, give a retest recommendation. Cross-family snapshot
   (same test across members) is a nice bonus the user likes.

## Normalized test names (use EXACTLY so trends line up)

- **Diabetes:** Fasting Glucose, HbA1c, Average Blood Glucose, Fasting Insulin
- **Lipid:** Total Cholesterol, HDL Cholesterol, LDL Cholesterol, Triglycerides, TC/HDL Ratio,
  Trig/HDL Ratio, LDL/HDL Ratio, HDL/LDL Ratio, Non-HDL Cholesterol, VLDL Cholesterol
- **Cardiac Risk:** Homocysteine, Lipoprotein (a), hs-CRP, Apolipoprotein A1, Apolipoprotein B,
  ApoB/ApoA1 Ratio
- **CBC:** Hemoglobin, Hematocrit, RBC, MCV, MCH, MCHC, RDW-SD, RDW-CV, WBC, Neutrophils,
  Lymphocytes, Monocytes, Eosinophils, Basophils, Neutrophils Absolute, Lymphocytes Absolute,
  Monocytes Absolute, Basophils Absolute, Eosinophils Absolute, Platelets, MPV, PDW, PLCR,
  PCT, ESR
- **Iron Studies:** Iron, Ferritin, TIBC, Transferrin Saturation, UIBC
- **Kidney:** Creatinine, BUN, Uric Acid, eGFR, Calcium (category Bone)
- **Liver:** Alkaline Phosphatase, Bilirubin Total, Bilirubin Direct, Bilirubin Indirect, GGT,
  AST (SGOT), ALT (SGPT), SGOT / SGPT RATIO, Total Protein, Albumin, Globulin, A/G Ratio
- **Thyroid:** T3, T4, TSH
- **Vitamins:** Vitamin D, Vitamin B12, Folate
- **Minerals:** Zinc, Copper, Magnesium, Sodium, Chloride
- **Hormones:** Testosterone, Cortisol
- **Immunology:** Total IgE
- **Urine:** Urine pH, Urine Specific Gravity

## Pitfalls

- **`sheetId: None` in batchUpdate fails on some spreadsheets.** After creating a Lab Values
  tab, the second batchUpdate for freeze/bold with `sheetId: None` raises
  `Invalid requests[0].updateSheetProperties: No sheet with id: 0` on spreadsheets whose first
  tab's id isn't 0 (e.g. Ruhaan's index). Fix: re-fetch the spreadsheet, read the created tab's
  real `properties.sheetId`, and use it in the formatting requests.
- **Duplicate index sheets** — always prefer the one inside the member's Medical folder.
- **Interim reports**: labs release before all tests finish ("N Processing"). File + track the
  Ready parameters anyway; list pending tests in the summary (e.g. Ruhaan HDM allergy panel).
- **Receipts**: payment receipts (Thyrocare VL…) are filed in NDR Medical > Invoices with
  TYPE=INVOICE in NDR's index; description lists exactly which patient/tests the receipt covers
  (family-wide receipts name every member covered).
- **Age-specific refs**: children's ranges differ (MPV 7.5–8.3 in kids vs 6.5–12 in adults;
  ALP 127–403 for teens; creatinine lower). Keep the report's own reference range.

- **Allergy panel (APHDF/APHDP) naming and tracking.** RLS/Thyrocare report codes APHDF and
  APHDP stand for Allergy Panel House Dust Mite D.Farinae and D.Pteronyssinus respectively
  (Phadia ImmunoCAP technology). Values are in kUA/L, interpreted via RAST class scale:
  Class 0 (<0.35) = absent/undetectable, Class 1 (0.35–0.7) = low, Class 2 (0.7–3.5) =
  moderate, Class 3 (3.5–17.5) = high, etc. Use test names like
  `Allergen sp IgE - HDM D.Pteronyssinus` and `Allergen sp IgE - HDM D.Farinae` with
  category `Allergy`, unit `kUA/L`, ref_low `0`, ref_high `0.35`. Always note the RAST
  class in the summary.

- **`(Complete).pdf` suffix for updated reports.** When the user uploads an updated/complete
  version of a previously tracked report (same date, same patient, superseding an earlier
  partial upload), name the new file with `(Complete).pdf` appended — e.g.
  `20260816 RNR R Healthy 2026 Package + Jaanch Female Hormone (Complete).pdf`. Then trash
  the old file from Drive. For Ruhaan specifically, if the new report includes additional
  tests not captured in the old filename (e.g. APHDF/APHDP Dust Mite panel now included),
  update the filename to reflect all tests:
  `20260816 Ruhaan R Healthy 2026 Package + Total IgE + Dust Mite Allergy Panel.pdf`.

- **RLS/Thyrocare test code mapping.** The reports use abbreviated test codes that map to
  human-readable names. Known mappings (as of Aug 2026): INSFA = Insulin Fasting,
  HOMO = Homocysteine, TEST = Testosterone, TIGE = Total IgE, APHDF = House Dust Mite
  (D.Farinae) Allergy Panel, APHDP = House Dust Mite (D.Pteronyssinus) Allergy Panel,
  CORT = Cortisol. Use the full name in filename and Lab Values, not the abbreviation.

- **Derived ratios rarely in reports.** TC/HDL, LDL/HDL, Trig/HDL, HDL/LDL, ApoB/ApoA1,
  SGOT/SGPT, and A/G ratios are calculated values that Healthy 2026 package PDFs almost
  never print. Don't flag them as "orphan" parameters when comparing a new report to the
  sheet — they were already computed and tracked from the earlier pass. Focus comparison
  on raw measured parameters only.

## Observed family patterns (Aug 2026, for trend context)

- Elevated Lp(a): NDR ~95–100 mg/dL and Rivaan 79.9 (genetic pattern); Ruhaan 17.6 — spared.
- Both boys (Rivaan, Ruhaan) showed lab-flagged mild neutropenia/lymphocytosis ("recheck with
  fresh sample") — likely transient/post-viral.
- Low Vitamin D across NDR (29.4) and Ruhaan (20.9); sufficient in Rivaan (31.7).
- HbA1c in prediabetic range: NDR 5.9, Ruhaan 5.8 (Rivaan 5.5 normal).
- Cortisol (morning ref 6.7–22.6 µg/dL): NDR 13.09, Roshini 13.89 — both normal.

## Historical backfill (trajectory mode) — ALL-parameter extraction

If a member's Lab Values tab has only ONE date (e.g. sheets created Aug 2026 for RNR/Ruhaan/
RVR), backfill EVERY parameter from every historical report before doing trajectory analysis.
The user explicitly corrected (Aug 2026): "each report has over 107 parameters... why did we
add only 32 rows?" — the expectation is ~80 rows per report date, matching the full parameter
set of the latest report. Do NOT curate to "key tracked params only."

**Dual cross-validation pipeline (validated Aug 2026, 16 reports, 967 params, 0 mismatches):**
This is a standing requirement for ALL lab report extractions, not just backfills. Every
parameter must be cross-checked twice: once via OCR/extracted text, once via vision from the
page image, and only where both agree is the value accepted.

1. **Text extraction:** Extract text from each report PDF (pdftotext or pymupdf). Send the
   full text to Gemini 2.5 Flash via `call_openrouter_model` with model
   `google/gemini-2.5-flash`, max_tokens=8000, temperature=0. Prompt: "Extract ALL lab test
   results from this medical report text. Return ONLY a valid JSON array. Each element:
   {'test_name': 'standard name', 'value': 'value', 'unit': 'unit', 'ref_low': '', 'ref_high': ''}".
   Include up to ~60K chars of text. The model normalizes test names automatically.

2. **Vision extraction (cross-validation):** Render each data-page of the report PDF to a PNG
   image (pymupdf `page.get_pixmap(dpi=200)`, then `base64.b64encode(pix.tobytes('png')).decode()`).
   Filter to pages containing test results (check for indicators like 'mg/dL', 'g/dL', 'U/L',
   'HbA1c', 'CHOLESTEROL', 'GLUCOSE' — skip cover pages, T&C pages, legend pages). Send each
   page image to Gemini 2.5 Flash vision via OpenRouter's multimodal API:
   ```python
   data_url = f"data:image/png;base64,{base64_image}"
   data = {
       'model': 'google/gemini-2.5-flash',
       'messages': [{'role': 'user', 'content': [
           {'type': 'text', 'text': 'Extract ALL lab test results visible on this page...'},
           {'type': 'image_url', 'image_url': {'url': data_url}}
       ]}],
       'max_tokens': 4000, 'temperature': 0
   }
   resp = requests.post('https://openrouter.ai/api/v1/chat/completions', ...)
   ```

3. **Compare (per-section):** For each test that appears in both extractions, compare the
   numeric value string. Key rule: the vision extraction should target the **same section of the
   report** as the text extraction — render the specific page or crop that contains the matching
   test block, not the whole report at once. This ensures the comparison is section-level, not
   just report-level (the user's explicit instruction: "running only that particular snapshot of
   that section through again vision model"). **Accept only parameters where both methods agree
   on the value.** Mismatches get flagged for review with both the text and vision values
   shown.

4. **Append** cross-validated rows to the member's Lab Values tab using the SAME normalized
   TEST NAME + category vocabulary as the existing rows.

5. **Handle failures gracefully:** If a report's text extraction produces invalid JSON, retry
   with a shorter text (remove the heavy-metals ICP-MS section if present — it's the most
   common source of JSON parse errors). Vision-only extraction is a valid fallback when text
   parsing fails repeatedly.

Worked example (Aug 2026): RNR backfilled 700 rows across 9 dates (2018-2026, 8 reports),
Ruhaan 174 rows across 7 dates (6 reports), RVR 152 rows across 3 dates (2 reports) — all
cross-validated with 0 mismatches. Cost: ~$0.01-0.02 per report via OpenRouter Gemini 2.5
Flash.

## Thyrocare/RLS parsing: values precede test names

In `pdftotext -layout` output of Thyrocare/RLS reports the VALUE line comes BEFORE the TEST
NAME (`METHOD\nVALUE\nUNIT\nTESTNAME`) — opposite of most reports, so forward-looking parsers
drop everything. Use a BACKWARD-LOOKING scan: for each all-caps TEST NAME line (len>4, not
ending ':'), look back 1–2 lines for a numeric VALUE, capture unit/ref after. Filter noise:
lipid category rows (`NORMAL: <150`, `DESIRABLE: <200`, `OPTIMAL: <100`), method rows
(`PHOTOMETRY: 92.2`, `E.C.L.I.A: 28.5`), and category headers (`DIABETES`, `LIPID`) collide
with real names — whitelist against the member's existing TEST NAME vocabulary. Cross-check
key readings against the "Tests Outside Reference Range" summary (page ~3) before trusting
the parser.
