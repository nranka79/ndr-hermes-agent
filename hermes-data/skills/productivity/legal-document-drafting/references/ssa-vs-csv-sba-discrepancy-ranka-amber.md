# SSA v3 vs Area Statement CSV — SBA Discrepancy Pattern (June 2026)

## Finding
When cross-checking Ranka Amber's SSA v3 (Clause 7 / Schedule B) against the Google Sheets Area Statement (downloaded as CSV), the **per-unit SBA figures do NOT match**:

| Unit | CSV SBA (sq.ft) | SSA Schedule B SBA | Difference |
|------|-----------------|---------------------|------------|
| 101 | 1,486 | 1,687 | +201 |
| 102 | 1,518 | 1,712 | +194 |
| 103 | 1,288 | 1,468 | +180 |
| 104 | 1,058 | 1,219 | +161 |
| 105 | 1,313 | 1,504 | +191 |
| 201 | 1,570 | 1,792 | +222 |
| 202 | 1,605 | 1,820 | +215 |
| 301 | 1,486 | 1,792 | +306 |

**Total FAR (27,543.25 sq.ft) matches exactly** between CSV and SSA — confirming the CSV was used as the source for the overall total, but the per-unit SBA in the SSA was taken from a different/earlier version of the area sheet.

## Root Cause Hypothesis
The SSA v3 was drafted from an earlier version of the area statement where SBA was calculated differently (possibly including terrace/FAR loadings per floor that were later removed or reallocated). The CSV currently available ("Area Statement - Ranka Amber (April 2026)") appears to be a subsequent update that changed per-unit SBA values.

## Implication
When citing SSA values for per-unit SBA, the source is the **SSA Schedule B itself**, not the current CSV. When citing BUA in sq.m, the source is the **CSV col 16** ("Area in Sqm From Plan Sanction Table") which matches SSA Schedule B exactly.

## Pattern for Cross-Checks
- **BUA (sq.m)**: CSV col 16 → SSA Schedule B (exact match)
- **Carpet area**: CSV col 10 or col 14 → SSA Schedule B (to be verified)
- **SBA (sq.ft)**: SSA Schedule B directly (CSV does NOT match)
- **Total FAR**: CSV "Total FAR" row → SSA Clause 6 (exact match)

## Aug 2026 Update — Execution Area Statement Verification (gid=0 spreadsheet)
The spreadsheet "Ranka Amber - Execution Plan Area Statement April 2026" (`1PKzB3CCSKZvWpxkcKAVBhI8XGnj626_ax5w9yvvLy3U`, tab 0 "Amber - Execution Area Statement") was verified against three sources:

- **vs Architect Certified Area Statement** (`20260608 Ranka Amber Area Statement Certified.docx`, `1lo2o3ntWbmyO_WZDo7m7-AFb5WsaPnAT`, Ar. Bhuvanesh Krishnan / Finding Form Design): ✅ carpet + balcony match ALL 20 units within ±1 sqft rounding. Certified totals: Carpet 23,438.91 / Balcony 2,137.43 / Common 4,235.44 / Saleable 31,936.53 sqft; FSI 1.97.
- **vs Approved Plan Sanction** (`Amber Plan Sanction GBA_BECC_0540_25-26 (2).pdf`, `1v-aLlu9LVH3aILRiTvu3fnFJw4vIExLT`): ✅ totals match — BUA 3,383.17 sq.m, FAR 2,559.82 sq.m, plot 1,300.58 sq.m (14,000 sqft). Per-unit BUA differs because sanction UnitBUA (121.73/124.68/108.21/90.94/110.71 sq.m for GF1–GF5) = unit-only BUA, while spreadsheet BUA column (1362/1396/1214/1045/1247 sft) = plinth area incl. walls/balconies.
- **vs SSA Schedule B**: unit 202 = 1,830 in spreadsheet vs 1,820 in SSA Schedule B (+10) — FLAG.
- **Saleable area basis**: SSA Clause 8 total saleable 27,543.25 sft ≠ spreadsheet Super BUA total 31,853 sft — different metrics; flag which one the bank should rely on.

### Key pitfall — SSA doc 404s
The SSA v3 Google Doc IDs from prior sessions (`1e2sZ9k6m4J3b8V7n0H5fL2wP1tR6dY8`, `1EnY77qQ-UXeMV7Pr49l6kiK_RTITK_jQ09gvljTthWI`) return **File not found** — do NOT rely on them. When the SSA is missing, verify against the **architect-certified area statement** (carpet/balcony per-unit) + **plan sanction** (totals) as the authoritative fallback pair.

## Files in This Session
- CSV: `1PG-Gn4b0lCZCXXktksqxFXnOeImG_vb-SugMcwUwuWU` (Area Statement - Ranka Amber April 2026)
- SSA v3: `1e2sZ9k6m4J3b8V7n0H5fL2wP1tR6dY8` (Ranka Amber SSA FINAL v3) — 404
- BBMP Sanction: `1aaNKuSd01zDgfiAGzELC2IQP75rghht2` (Amber Sanction.pdf)
- Execution Area Statement spreadsheet: `1PKzB3CCSKZvWpxkcKAVBhI8XGnj626_ax5w9yvvLy3U` (tab 0 gid=0)
- Certified area statement: `1lo2o3ntWbmyO_WZDo7m7-AFb5WsaPnAT` (docx)
- Plan sanction PDF: `1v-aLlu9LVH3aILRiTvu3fnFJw4vIExLT`