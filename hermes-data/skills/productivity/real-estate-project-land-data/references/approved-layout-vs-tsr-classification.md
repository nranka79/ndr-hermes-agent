# Approved Layout vs TSR Classification — Sevaganapalli Worked Example (Aug 2026)

## The correction

Prakash uploaded `DRA-Sevaganapalli-TSR-20251014-V2-SV (2).pdf` (CMS Induslaw Title Search Report) and asked to "separate the non-approved survey nos from the approved ones in all the sheets". The first pass used TSR Part III as the approved set — **wrong**. His follow-up: *"The approved survey nos are ones taken layout plan approval. Those in the approved layout to be separated."*

Lesson: **"approved" = DTCP Layout Plan Approval survey list**, which differs from the TSR title-opinion schedule.

## Two authoritative documents (both found in Drive)

| Document | Drive name pattern | Readability |
|---|---|---|
| DTCP Layout Plan Approval | `2026-01-13, Sevaganapalli, DTCP Layout Plan Approval — Krishnagiri, —.pdf` (two copies exist; same bytes) | 1-page Tamil scan, NO text layer, vision OCR garbles → useless for survey list |
| Layout Planning Sanction | `2026-03-30, Sevaganapalli, Layout Planning Sanction — Panchayat & DTCP, —.pdf` (and `20260330 Ranka Oasis Sevaganapalli Layout Planning Sanction – Sevaganapalli Panchayat & DTCP Krishnagiri – Nishant Ranka.pdf`) | 3 pages; **pages 1–2 OCR cleanly in English** — the survey list is verbatim in a "Land Bearing S.F.No ..." sentence |

Both sizes matched across duplicate filenames (1158058 bytes / 2413146 bytes) — good dedupe check.

## The approved survey list (19 surveys, 30,416 sq.m = 7.52 Ac, 130 residential plots)

SWP/DTCP/KRISHNAGIRI/LAYOUT NO. **03/2026 & 02/2026** dated 13.01.2026; Panchayat Planning Permission No. 03/2025 dated 30.03.2026; Panchayat Resolution No. 10 dt 02.02.2026.

```
158/1C9A, 158/1C9B,
166/1, 166/2B2, 166/3A, 166/3B, 166/3C, 166/3D, 166/3E1, 166/3E2, 166/3F,
167/1G, 167/2C, 167/2D,
168/1B,
176/1B2D, 176/2B4A,
177/1A1A, 177/1A1B
```

Key cross-checks visible in the sanction letter:
- "30416.00 sq.m" total, "Residential Plots: 1 to 130 (plot extent: 17802.49 Sq.m)"
- Roads donated to Panchayat via Gift Deeds 9188/2025 and 9196/2025 (Hosur Sub-Registrar)
- Layout Approval Fee ₹5,23,228/- dated 25.03.2026

## TSR Part III vs Layout — the diff (why the first pass was wrong)

**In LAYOUT but NOT in TSR Part III (5):** 166/1, 166/2B2, 167/1G, 168/1B, 177/1A1A
**In TSR Part III but NOT in LAYOUT (20):** 158/1A1A, 158/1A1B, 158/1B2, 158/1B3, 158/1B4, 158/1B5, 158/1C1, 158/1C2, 158/1C3, 158/1C4, 158/1C5, 158/1C6, 158/1C7, 167/1A, 167/1D, 167/1E, 167/1H, 167/1I, 167/2B, 168/1A

The 20 excluded are owned/held land outside the approved layout — flag for Phase 2 check (`Sevaganapalli Layout Phase 1 & 2.png` exists on Drive and shows phase boundaries).

## Workbook-wide classification mechanics

1. Enumerate all sheets via `spreadsheets().get()`.
2. Read each sheet `A1:Z1000` with `valueRenderOption=FORMATTED_VALUE`.
3. Regex survey tokens: `\b(\d{1,3}(?:\(\d+\))?(?:/[0-9]+[A-Z]*(?:[A-Z0-9]*)?)+)\b` (normalize `.lower().replace(" ","").replace("(part)","")`).
4. Classify: token in approved_set → APPROVED; in FALSE_POSITIVES map → NOT A SURVEY; in REASONS map → NON-APPROVED (parent/origin vs adjacent/boundary).
5. FALSE_POSITIVES seen: `248/1995`, `260/1989`, `300/2004`, `365/2009`, `393/2004` (doc numbers), `353/320` (revenue/docket), `176/1995` (doc no), `03/2016`, `14/95` (cert reg nos), fractions `1/10`, `1/10th`, `1/3rd`, `2/3`, `2/3rd`, `2/8`, `3/9`, `4/10`, `5/11`, `6/7/12/13` (S.No row), combined notations `167/1E/167/1F`, `167/1H/167/1I/168/1A/168/1B`, `158/1C9B/159/1C9B` (rename note), `176/177` (block shorthand).

## Sheet writes (final state)

- **`APPROVED_VS_NONAPPROVED`** (new sheet): 100 rows = header + 19 APPROVED + 57 NON-APPROVED + 23 NOT A SURVEY. Columns: S.No | Survey No | Status (Approved Layout) | Extent (Ac) | Reason / Note | Appears in Sheets (count) | Sheets. Status column C colored green/red/grey via `repeatCell` with `userEnteredFormat.backgroundColor`. Totals block at row 101: "TOTAL — APPROVED LAND (Layout Approval) 7.52 Acres — 30,416 sq.m per DTCP Layout Approval 03/2026 & 02/2026 (dt 13.01.2026) — 130 residential plots". Legend below.
- **`PART_V_FlowOnTitle`** col U "Approved Plan Status (Layout)": 249 ✅ / 355 ❌ (605 rows), colored.
- **`PART_V_Flat_Backup`** col T: 37 ✅ / 70 ❌ (115 rows), colored.
- **All 34 `Sy_*` headers** (row 1): append `| ✅ APPROVED` or `| ❌ NON-APPROVED` after stripping any old badge (regex `\s*\|\s*(✅ APPROVED|❌ NON-APPROVED)\s*$`).

## Rate-limit pattern (Sheets API 60 writes/min)

- Values updates: pace with `time.sleep(1-2)` between calls.
- batchUpdate: group consecutive same-status rows into single `repeatCell` ranges (grouped_ranges helper), 15 requests per batch, sleep 2s between; on 429 sleep 30s and retry (up to 3 attempts). Grouping 605 rows → ~20 requests instead of 600.

## Pitfalls hit

- First pass colored with the WRONG approved set (TSR). Fix: regenerate status column entirely (clear + rewrite), not patch.
- Writing a 13-row totals block starting at A101 with a leading blank row shifted content — verify readback after writes; the clear+rewrite approach (`values().clear` then `update`) is more reliable than incremental moves.
- OCR on Tamil approval PDFs: don't fight it. Flip/rotate/crop attempts produced garbage. Go find the English sanction letter instead.
