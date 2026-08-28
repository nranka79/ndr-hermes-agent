# Worked Example: Ranka Udaya KB Audit (August 2026)

## Context

- **Original doc**: Ranka Udaya — Project Facts and FAQs (NDR's existing Google Doc)
- **Source material**: Joyce AI training FAQ questions + NDR briefings from 16 August 2026
- **User**: Bharat (DRAAS team member, works on KB docs for Joyce AI training)
- **User directive**: "Do not touch the original. Create a new companion doc with all updates highlighted yellow, each citing its source reference."

## Gap Analysis Performed

The KB was compared against Joyce AI FAQ questions + NDR Aug 16 briefings. Gaps found across **16 categories**:

### Category A: Outdated/Contradicted (highest priority)

| Gap | KB Said | NDR Said |
|-----|---------|----------|
| Developer identity | "DRA Group (Dinesh Ranka & Associates)" | Ranka Group — five-decade legacy, rebranded as DRA Homes |
| Building height | "G+1/G+2/G+3 subject to Panchayat norms" | G+4 comfortably per TN BTCP norms |
| 6-month construction | "cannot be committed" | CAN commit — plot ready, 15-20 min online approval |
| Bus stop info | "does not provide exact distance" | Excite Gate/Ambedkar Circle, 3-4 min from project |
| Adjoining land | "does not provide a verified answer" | West=Exide, East=golf course, North=road, South=Exide |
| Storm-water drainage | "does not provide a verified description" | Underground drains fully provided |
| Electrical infrastructure | "street lighting only" | Underground cabling with feeder-pillar boxes, no overhead wires |
| Bank finance | "HDFC, SBI, ICICI" all equal | ICICI pre-approved only; HDFC/SBI "in process" |

### Category B: Missing Answers

| Missing Topic | NDR's Answer |
|---------------|-------------|
| Drive-time ladder | 9/10/12/15/16/2 min from project gate |
| Rental yield / 8-room program | 8×1-BHK at ₹8-10k/month per room = ~10% yield; golf club LOI for 20 rooms |
| Exide plant → lithium-ion battery | Conversion to battery cell plant — massive value add |
| Compound wall maintenance | No maintenance normally; adjoining wall repair = owner cost |
| Investment "Economics 101" framing | Finite supply, growing demand → demand-supply mismatch → no-brainer investment |

### Category C: Missing Tone/Style

| Missing Directive | Details |
|-------------------|---------|
| PEPPY / HIGH-ENERGY tone | Every answer loaded with positive reframing + FOMO + psychology |
| Developer project count framing | 50+ lakh sq.ft delivered directly + indirectly |

## Companion Document Created

- Title: "Ranka Udaya — Updated Project Facts and FAQs (v2 — With Corrections & Sources)"
- Doc ID: `1Bii40vBH4iX0FCKtoKvD2WH_OyeZsxYOb1dOMyR62hg`
- Contains: full original KB content preserved exactly + 15 update blocks + 1 new section

## API Technique Used

Instead of HTML import (which would require rebuilding the entire document), used Docs API:
1. `documents().create()` — blank document
2. `batchUpdate` with `insertText` — all content at once
3. `batchUpdate` with `updateTextStyle` (15 requests + 2 extra, in groups of 5) — yellow highlights

## Yellow Highlight Implementation

```python
"updateTextStyle": {
    "range": {
        "startIndex": 1 + flat_text_position,  # Docs API is 1-indexed
        "endIndex": 1 + flat_text_end
    },
    "textStyle": {
        "backgroundColor": {
            "color": {
                "rgbColor": {"red": 1.0, "green": 1.0, "blue": 0.0}
            }
        }
    },
    "fields": "backgroundColor"
}
```

Markers found via regex `[UPDATE` in the flat-extracted text, each block extended to include its `Source: ...` line.

## Output Presented to User

A summary table showing all 15 updates grouped by: Developer Identity, Building Height, Location, Infrastructure, Legal, Finance, Investment Thesis, Tone Directive — each with a brief description of what changed.