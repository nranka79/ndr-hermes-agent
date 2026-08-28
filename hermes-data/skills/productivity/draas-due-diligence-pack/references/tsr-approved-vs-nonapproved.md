# TSR Approved vs Non-Approved Survey Classification (2026-08-10 worked example)

> ⚠️ **SUPERSEDED / CORRECTED the same day.** The 34-survey TSR Part III set below was the FIRST pass. Prakash corrected it: "The approved survey nos are ones taken layout plan approval. Those in the approved layout to be separated." The authoritative approved set is the **DTCP Layout Plan Approval** — 19 surveys, 30,416 sq.m / 7.52 Ac, 130 plots (layout refs SWP/DTCP/KRISHNAGIRI/LAYOUT NO. 03/2026 & 02/2026, dt. 13.01.2026):
> **158/1C9A, 158/1C9B, 166/1, 166/2B2, 166/3A, 166/3B, 166/3C, 166/3D, 166/3E1, 166/3E2, 166/3F, 167/1G, 167/2C, 167/2D, 168/1B, 176/1B2D, 176/2B4A, 177/1A1A, 177/1A1B.**
> Differences vs the old TSR set: 166/1, 166/2B2, 167/1G, 168/1B, 177/1A1A are approved but NOT in TSR Part III; ~20 TSR Part III surveys (158/1A1A–1C7, 167/1A–1I, 167/2B, 168/1A) are owned but OUTSIDE the approved layout (likely Phase 2). The classification below is kept only as the historical first-pass / regex-extraction reference.
>
> Delivery ordering (user preference): **approved survey nos FIRST in the sheet, then non-approved** — not survey-number order.

Sevaganapalli workbook (`1eVqckk3cCWdN06RNGISTP99WSz-aToCmGcNPIIqaicc`), CMS Induslaw TSR "DRA-Sevaganapalli-TSR-20251014 V2".

## Source PDF → approved list

`pdftotext -layout "DRA-Sevaganapalli-TSR-20251014- V2-SV (2).pdf" /tmp/tsr_text.txt`

**Critical**: extract the approved schedule from Part III ONLY:

```python
m = re.search(r'PART\s*[-–]\s*III.*?(?=PART\s*[-–]\s*IV)', text, re.S | re.I)
part3 = m.group(0)
items = re.split(r'Item No\.\s*\d+', part3)
# each block: "Survey No. 158/1A1A measuring 0.36 Acres, bounded on ..."
```

Pitfall: naive regex over the WHOLE TSR matched 93–106 tokens because boundary descriptions ("North By Land in Survey No. 158/1C4, 158/1C3…") repeat every adjacent survey. Part III isolation gives exactly 34.

Pitfall: `Survey No. 176/1B2D part measuring 0.03 ½ Acres` — the `part` keyword and `0.03 ½` spacing break naive patterns. Either handle `(part)?` and split on `½`, or add the item manually. Approved total = 34 items ≈ 12.74 Ac (matches TSR cover).

## The 34 approved (Part III schedule)

158/1A1A, 158/1A1B, 158/1B2, 158/1B3, 158/1B4, 158/1B5, 158/1C1, 158/1C2, 158/1C3, 158/1C4, 158/1C5, 158/1C6, 158/1C7, 158/1C9A, 158/1C9B, 166/3A, 166/3B, 166/3C, 166/3D, 166/3E1, 166/3E2, 166/3F, 167/1A, 167/1D, 167/1E, 167/1H, 167/1I, 167/2B, 167/2C, 167/2D, 168/1A, 176/1B2D (part), 176/2B4A, 177/1A1B

## Classification buckets

### NON-APPROVED — parent/origin surveys (needed for flow, not schedule properties)
158/1 (origin of all 158), 158/1A1 (parent of 1A1A+1A1B), 158/1B (parent of 1B2-1B5), 158/1C (parent of 1C1-1C9B), 158/1C9 (parent of 1C9A+1C9B), 166/3 (parent of 3A-3F), 166/3E (parent of 3E1+3E2), 168/1 (parent of 168/1A), 176/1, 176/1B, 176/1B2 (parents of 176/1B2D), 176/2, 176/2B (parents of 176/2B4A), 177/1, 177/1A (parents of 177/1A1B)

### NON-APPROVED — adjacent/boundary surveys (mentioned in TSR as boundaries only, NOT owned)
158/1A2, 158/1A5, 158/1B1, 158/1B6, 158/1C8, 158/2, 159/1C9B (revenue re-numbering of 158/1C9B — same parcel!), 166/1, 166/2A, 166/2B, 166/2B2, 166/2C, 167/1B, 167/1C, 167/1F, 167/1G, 167/2A, 168/1B, 168/2A2, 176/1A1, 176/1B2C, 176/2B4B, 176/2B5, 176/7, 177/1A1A (only 177/1A1B is approved!), 177/1A2, 177/2

### NOT A SURVEY — false positives (filter out!)
| Token | What it actually is |
|---|---|
| 248/1995, 260/1989, 300/2004, 365/2009, 393/2004, 176/1995 | Doc registration numbers (Sale Deed 248 of 1995 etc.) |
| 03/2016, 14/95 | Reg numbers (Death Certificates) |
| 1/10, 1/10th, 1/3rd, 2/3, 2/3rd, 2/8, 3/9, 4/10, 5/11 | Share fractions |
| 158/1C9B/159/1C9B | rename note (same parcel) |
| 167/1E/167/1F, 167/1H/167/1I/168/1A/168/1B | combined notation in a legal-opinion title |
| 176/177 | "176/177 block" shorthand |
| 353/320 | Patta/revenue docket no |
| 6/7/12/13 | row of S.No values |

## Delivery pattern

1. **Consolidated sheet** `APPROVED_VS_NONAPPROVED`: S.No | Survey No | Status (Approved Plan) | Extent (Ac) | Reason / Note | Appears in Sheets (count) | Sheets. Row 1 header, color-code the Status column by bucket (green/red/grey), bold header, freeze row 1, legend at the bottom (rows after data).
2. **Status column on main flow sheets**: PART_V_FlowOnTitle col U (after 19-col schema), PART_V_Flat_Backup col T. Per-row survey detection: scan cols B (Survey stage), C (Flow tree), A (Family) for `\b(158|166|167|168|176|177)/[0-9]+[A-Za-z0-9]*(\(?part\)?)?\b`; annexure rows (`📎 158/1A1A`) inherit from col B. Result: all 34 survey-header + annexure rows → ✅ APPROVED; origin/parent rows (158/1A1 ORIGIN, 166/3E ORIGIN, 176/1+177/1A acquisition block) → ❌ NON-APPROVED.
3. **Sy_\* sheet badges**: append `| ✅ APPROVED` to each Sy_ sheet's row-1 header (derive survey from sheet name `Sy_158_1A1A` → `158/1A1A`, replace `_` with `/`).

## Sheets API rate-limit trick (hit in this session)

720 per-row `repeatCell` color requests → **429 RATE_LIMIT** (Sheets 60 writes/min/user). Fix: run-length encode the status column into contiguous ranges (consecutive rows with the same status = one request):

```python
def grouped_ranges(status_list):
    runs = []
    i = 1  # skip header
    while i < len(status_list):
        st = status_list[i]
        j = i
        while j < len(status_list) and status_list[j] == st:
            j += 1
        if st:
            runs.append((i, j, st))
        i = j
    return runs
```

Result: 24 requests instead of 720. Retry loop on 429 with `time.sleep(30)` up to 3 attempts, batch ~15 requests per call with `time.sleep(3)` between.

## User-preference takeaways

- "Non-approved" ≠ title defect. The non-approved surveys are parents + boundary parcels outside the approved layout extent. With the corrected DTCP-layout set the buckets were **19 APPROVED / 57 NON-APPROVED / 23 NOT A SURVEY** (first-pass TSR-based numbers were 34/42/23 — superseded). State this explicitly in the delivery.
- New docs in PART_I go under their specific survey numbers — never a flat append (user corrected this).
- Approved survey nos go FIRST in the APPROVED_VS_NONAPPROVED sheet, then non-approved (ordering preference).
