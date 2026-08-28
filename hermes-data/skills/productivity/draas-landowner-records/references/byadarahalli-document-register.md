# Byadarahalli Document Register — Worked Example

**Source spreadsheet**: `"Satvik Developers(PS) - Byadarahalli Legal Documents"` (ID `1aCTuKcDjH2t8G4ANyJkbhuXbXPPF7yWETQ3weQFsMN4`)
**Tab**: Documents (gid `1629819676`)
**User**: Prakash Singh (PS), works via psingh@draas.com

## Sheet structure

The Documents tab has 3 document sections interleaved with totals rows:

| Section | Rows | Count |
|---------|------|-------|
| SALE DEEDS — REGISTERED | 2–16 | 15 docs |
| Total row (Sale Deeds) | 17 | 24A 34.08G |
| AGREEMENTS / GPA | 18–31 | 12 docs (ATS+GPA pairs + P-series) |
| Total row (Agreements) | 32 | 18A 13G |
| GRAND TOTAL | 33 | 43A 07.08G gross |

Plus 3 non-legal tabs:
- **Extents_By_Survey** (34 rows) — per-survey extent verification (8 cols)
- **RTC_CrossCheck** (30 rows) — deed extent vs RTC comparison (6 cols)
- **Extent_Totals** (49 rows) — aggregated totals by survey with acre-decimal

## Survey-number groups produced

**41/** cluster (all registered same date 03-02-2023):
- 41/11 (0-20G), 41/14 (0-06G), 41/17 (0-05.08G) — 3 sale deeds

**45/** sub-surveys:
- 45/5B (2-00G) — ATS 29-09-2022 + GPA 25-11-2022
- 45/6 (1-00G) — ATS 25-11-2022 + GPA 25-11-2022
- 45/P3 (2-00G) — Title Deed 15-02-1962 (unreg)
- 45/P5 (4-00G) — Agreement Deed 14-11-2005 (unreg)
- 45/P7 (4-00G) — No document uploaded (PENDING)

**175/** cluster (largest sub-survey cluster):
- 175/1 (0-25G), 175/4,6+176/2 (2-04G), 175/5 (0-15G), 175/9 (0-27G) — 4 deeds

**Key multi-survey deeds**:
- `180 & 184/5` (2-35G) — single deed covering both surveys
- `175/4,6,176/2` (2-04G) — deed covers 3 sub-surveys
- `209/1,2,3,4` (3-35G) — single deed covering 4 sub-divisions

**ATS+GPA pairs**:
- 190/3 (both 14-11-2022), 45/5B (ATS 29-09 + GPA 25-11), 45/6 (both 25-11-2022), 216 (both 16-02-2023), 223 (both 11-01-2023)

## Output order

Survey numbers sorted ascending by whole-number then fractional numerator:
41/11 → 41/14 → 41/17 → 45/5B → 45/6 → 45/P3 → 45/P5 → 45/P7 → 174/3 → 175/1 → 175/4,6,176/2 → 175/5 → 175/9 → 180 & 184/5 → 181 → 190/3 → 209/1,2,3,4 → 210 → 216 → 219/4,7 → 219/5,6 → 221/2 → 223

## Telegram-safe formatting template

```
**{Survey No}** — {Extent A.G}

1. **{Document Type}** — {Date} — *{Reg No}*
   {Parties summary}
```

No pipe tables. Use `—` (em dash) section separators between survey groups.

## Notes for future sessions

- The sheet has `03.02.2023` (dots) for row 16 (41/17) vs `03-02-2023` (dashes) for rows 14–15 — normalise both to DD-MM-YYYY on output.
- P-series parcels (45/P3, P5, P7) use a different numbering scheme — they sort after regular 45 sub-surveys.
- 45/P7 has NO uploaded file anywhere on Drive — flag it as pending.
- Total rows (17, 32, 33) should be preserved as a summary but not included in per-survey tables.