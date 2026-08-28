# Medical PDF Data Extraction Pipeline

Repeatable pipeline for extracting all lab values from 50+ medical PDFs (spanning a decade) into a structured Google Sheet for trend graphing. Used when the user says "extract everything from all my reports into a spreadsheet."

## Architecture

```
Drive (PDFs) → parallel subagents [OCR + LLM parse] → temp JSON files
    → deterministic merge script → Sheets API (code only, no LLM)
```

## Phase 0: Inventory Existing File Index

The user likely has a "NDR Medical Report Index" sheet (or equivalent) that already lists every PDF filename with date, type, and Drive link. Use this as the manifest:
- Read the sheet to get the full list of lab PDFs with dates and Drive file IDs
- Filter to lab reports only (exclude prescriptions, receipts, letters, imaging-only scans)
- Identify which reports are already captured and which need to be added

## Phase 1: Parallel PDF Download & Extraction

### Subagent Assignment
- ~25-30 lab report PDFs, 5 subagents handling ~5-6 each
- Each subagent downloads from Drive and extracts text

### Extraction Tools
- **Text PDFs** (most Thyrocare/1mg reports): `pdfminer.six` (`pdfminer.high_level.extract_text`)
- **Scanned PDFs** (older reports, handwritten): `marker-pdf` or OCRmyPDF
- **DOCX**: `python-docx`

### Output Format (per PDF, as JSON)
```json
{
  "date": "2026-04-21",
  "file_name": "20260421 NDR R INSFA Wellness 360 Thyrocare.pdf",
  "source": "Thyrocare",
  "package": "INSFA + Wellness 360",
  "tests": [
    {
      "name": "Fasting Insulin",
      "category": "Hormone",
      "value": 5.65,
      "unit": "uU/mL",
      "ref_low": 2.6,
      "ref_high": 24.9,
      "status": "normal"
    },
    {
      "name": "HbA1c",
      "category": "Diabetes",
      "value": 5.6,
      "unit": "%",
      "ref_low": null,
      "ref_high": 5.7,
      "status": "normal"
    }
  ]
}
```

## Phase 2: Deterministic Merge & Normalisation

### Name Normalisation Map
LLM-generated, code-executed. Map provider-specific names to canonical names:
- "HDL Cholesterol - Direct" / "Cholesterol - HDL" / "HDL" → "HDL Cholesterol"
- "LDL Cholesterol - Direct" / "Cholesterol - LDL" / "LDL" → "LDL Cholesterol"
- "Triglycerides" / "TG" / "Serum Triglycerides" → "Triglycerides"
- "Lipoprotein (a)" / "Lp(a)" / "LP-A" → "Lipoprotein (a)"
- "HS-CRP" / "High Sensitivity CRP" / "CRP (HS)" → "hs-CRP"
- "25-OH Vitamin D (Total)" / "Vitamin D" / "25 Hydroxy Vitamin D" → "25-OH Vitamin D"
- "Fasting Glucose" / "FBG" / "Fasting Blood Sugar" → "Fasting Glucose"
- "TSH - Ultrasensitive" / "TSH" / "Thyroid Stimulating Hormone" → "TSH"

### Deduplication
- Same test on same date from same provider → keep one (highest quality / most complete)
- Same test on same date from different providers → average or flag for review

### Category Assignment
- Diabetes: Fasting Glucose, HbA1c, Fasting Insulin
- Lipid: Total Cholesterol, LDL, HDL, Triglycerides, VLDL, Non-HDL, ApoB, ApoA1, Lp(a)
- Inflammation: hs-CRP, Homocysteine, LP-PLA2, Fibrinogen
- Liver: SGOT/AST, SGPT/ALT, GGT, ALP, Bilirubin, Protein
- Kidney: Creatinine, BUN/Urea, eGFR, Uric Acid, Calcium
- Thyroid: T3, T4, TSH
- Hematology: Hb, RBC, WBC, Platelets, ESR, Eosinophils
- Minerals: Iron, Ferritin, Magnesium, Calcium
- Vitamins: Vitamin D, B12, Folate
- Urine: all urine parameters
- Cardiac Imaging: CAC Score, CIMT, Plaque burden

## Phase 3: Sheet Creation

### Target Sheet
- New tab "Lab Values" in existing NDR Medical Report Index sheet
- OR new "NDR Lab Trends" sheet
- Columns: `DATE | TEST NAME | CATEGORY | VALUE | UNIT | REF LOW | REF HIGH | SOURCE FILE`

### Injection Method
- Use `sheets_update` or `sheets_append` via `gws_skill_bridge`
- Write all rows in a single batch API call
- No LLM in the write path — this is pure deterministic code

## Phase 4: Verification
- Count rows written vs expected (one per test-date pair)
- Spot-check 5 random values against source PDFs
- Report coverage: "Extracted X tests from Y reports spanning Z years"

## Naming Convention (for renamed files)
Standard format used in NDR Medical folder:
```
YYYYMMDD NDR R <Description> <Provider>.pdf
```
Where R = Report/Result. Exception: prescriptions use P, advice uses A.

Thyrocare default names like "Nishant Ranka-2.pdf" must be renamed to follow convention, e.g. `20260421 NDR R INSFA Wellness 360 Thyrocare.pdf`.

## Pitfalls
- The existing "NDR Medical Report Index" is a **file-level index** (tracks which PDFs exist), NOT a lab values database. Don't treat its rows as test results.
- Some PDFs are scanned images — require OCR marker-pdf, not just pdfminer.
- Units differ between labs (mg/dL vs mmol/L for glucose). Normalise everything to mg/dL.
- Some older reports may have hand-written corrections — flag for manual review.
- Date formats vary: DD/MM/YYYY in some, datetime objects in XLSX, YYYYMMDD in filenames. Normalise to YYYY-MM-DD.
