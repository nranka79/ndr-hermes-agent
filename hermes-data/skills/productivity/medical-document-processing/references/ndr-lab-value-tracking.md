# NDR Lab Value Tracking — Concrete Setup (verified 17 Aug 2026)

## Drive locations (google-draas account)

- **NDR Medical folder**: `0B1Oc8cSaJXPGT1JPMVlfajFnTmc`
  (user calls it "MyMedicalRecords folder")
- **NDR Medical Report Index spreadsheet**: `1gsIQXoVis0TG3eCZFmg0AVzCPG525doPK0ifTIqz2rg`
  - Tab `Sheet1` — report index. Header: SL.NO | TYPE | DATE | REPORT NAME | LINK.
    Dates in mixed formats historically; recent rows use ISO `YYYY-MM-DD`.
    SL.NO is sequential int (was 180 after adding the 16 Aug 2026 report).
  - Tab `Lab Values` — parameter log. Header: DATE | TEST NAME | CATEGORY | VALUE | UNIT | REF LOW | REF HIGH.
    Data spans 2014→2026, ~540+ rows before 16 Aug 2026 additions.
- Second stale copy of the index exists at `1fLF1oiHtnvMoOaJiD7J9h-pYiBL4Klh2qE9UwPPSo6k` — do not append there; use the one inside the NDR Medical folder.

## Family medical index sheets (report indexes ONLY — no Lab Values tab)

- KDR (Kanta Ranka): `1DjfOon0dY74ReAREt5GAPpPNWM464lYvJYrESqiUB2g`
- RNR (Roshini): `1rhK4XONTYmBmYpRyKMpLFMn4UupLJ_Gufv02RmE570E` (also `1VB6FsfTAOiDc8p2X7v2o94zTGERhocRtzK4eiOPXhxA`)
- RVR (Rivaan Ranka): `1YJ8iYEAHCVjBRaaE_iU3_Q8aEJZ1aSP_WXNk0w7RXyA`
- Ruhaan: `1E14iA3xDdoBaC0Sdlim6r6MipmSzNkKqFLaV2dXvHQU` — tabs are `Reports & Prescriptions`, `BILLS` (not Sheet1)
- Family folders: KDR Medical `0B1Oc8cSaJXPGUUtVbTJHb0Y3V2s`, RNR Medical `0B1Oc8cSaJXPGUDBMR3Z1MGJZeWc`,
  Rivaan Medical `0BymF3UUrZZYKVFY2UzkxUEI0UlU`, Ruhaan Medical `0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k`,
  DDR Medical `1cLMGwITTiCJUykA0iMVZ_vMNMbuyVr2n`, SDR `1vlBNdEASVttKjmIDJ4Syg4NqlZrYYqTi`, SMR `1Aas2UVWqu_v4o1FtzcmBHHsI_st907AK`

## Canonical TEST NAME vocabulary (use these, not lab headers)

Diabetes: Fasting Glucose, HbA1c, Average Blood Glucose, Fasting Insulin
Lipid: Total Cholesterol, HDL Cholesterol, LDL Cholesterol, Triglycerides, TC/HDL Ratio, LDL/HDL Ratio, Non-HDL Cholesterol, VLDL Cholesterol, Trig/HDL Ratio, HDL/LDL Ratio
Cardiac Risk: Homocysteine, Lipoprotein (a), hs-CRP, Apolipoprotein A1, Apolipoprotein B, ApoB/ApoA1 Ratio
CBC: Hemoglobin, Hematocrit, RBC, MCV, MCH, MCHC, RDW-SD, RDW-CV, WBC, Neutrophils, Lymphocytes, Monocytes, Eosinophils, Basophils (+ Absolute variants), Platelets, MPV, PDW, PLCR, PCT, ESR
Iron Studies: Iron, Ferritin, TIBC, Transferrin Saturation, UIBC
Kidney: Creatinine, BUN, Uric Acid, eGFR, Calcium (category Bone)
Liver: Alkaline Phosphatase, Bilirubin Total/Direct/Indirect, GGT, AST (SGOT), ALT (SGPT), SGOT / SGPT RATIO, Total Protein, Albumin, Globulin, A/G Ratio
Thyroid: T3, T4, TSH
Vitamins: Vitamin D, Vitamin B12, Folate
Minerals: Zinc, Copper, Magnesium, Sodium, Chloride
Hormones: Testosterone
Urine: Urine pH, Urine Specific Gravity (only numeric ones; rest qualitative ABSENT → skip)

## Worked example — 16 Aug 2026 "Healthy 2026 Package + INSFA + Homocysteine + Testosterone"

- Uploaded as `20260816 NDR R Healthy 2026 Package + INSFA + Homocysteine + Testosterone.pdf` → NDR Medical folder
- Index row SL.NO=180, DATE 2026-08-16
- 81 Lab Values rows appended in one batch (DATE '2026-08-16' for all)
- Key results that drove the trend analysis:
  - HbA1c 5.9% (ref <5.7) — highest since Jan 2023; FBS 96.5 (up from 85/90/94)
  - Eosinophils 5.5% (ref 1–6) — first NORMAL in 2 years (was 14.3/11.1/8.3/7.9/11.4)
  - Lp(a) 95.3 (ref <30) — stable genetic, same as 82–100 range for 8 years
  - Zinc 60.97 (ref 70–115), Copper 58.55 (ref 63.5–150) — low, trending down
  - Vitamin D 29.4 (ref 30–100) — insufficiency, chronic
  - Homocysteine 16.99 (ref <15) — first above 15 in the modern series
  - TSH 4.18 (ref 0.54–5.3) — upper edge, rising from 2.9–3.4
  - Lipids excellent: TC 155, LDL 78.85, HDL 61, TG 73
- Trend grouping pitfall: sheet has `WBC` AND `TOTAL LEUCOCYTE COUNT (WBC)`, `Platelets` AND `Platelet Count`, `HDL CHOLESTEROL - DIRECT` AND `HDL Cholesterol`, `LDL CHOLESTEROL - DIRECT` AND `LDL Cholesterol`. Normalize before grouping.
- Junk rows to ignore: `Urine pH = 45.23` (2025-01-06), Apo columns swapped (2026-01-15 ApoA1=68/ApoB=0.5).

## Append code pattern (Sheets API)

```python
sheets.spreadsheets().values().append(
    spreadsheetId=SID, range='Lab Values!A1:G1',
    valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS',
    body={'values': rows}   # list of [date, name, cat, value, unit, ref_lo, ref_hi]
).execute()
```
Same pattern for Sheet1 `A1:E1`. Upload PDF with MediaFileUpload + supportsAllDrives=True,
fields='id,webViewLink', strip `?usp=drivesdk` from the link before storing.
