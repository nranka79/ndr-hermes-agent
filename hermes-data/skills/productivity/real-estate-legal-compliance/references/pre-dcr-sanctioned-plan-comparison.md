# Pre-DCR vs Sanctioned Building Plan Comparison

**Trigger:** User asks to compare two building plans (last sanctioned plan vs pre-DCR proposed plan) across architectural parameters. Common after submitting a pre-DCR revision for a project.

## Required Documents

Two PDFs needed:
1. **Sanctioned plan** — the last approved BBMP/KIADB/RERA sanction (e.g. PRJ_0987_21-22 for Ranka Northstar)
2. **Pre-DCR (proposed) plan** — newly submitted, NOT yet sanctioned, drawn up as pre-DCR revision

## Accessing Plans

Both are usually on the DRAAS Drive (ndr@draas.com). The **google-draas** OAuth token may not be in the vault — only google-gmail and google-ahfl tokens have been configured. If the DRAAS Drive is inaccessible:

1. Generate an auth URL: `get_auth_url(telegram_id, login_hint="ndr@draas.com")`
2. Send to user to authorize
3. Or ask the user to upload/share the PDFs directly in Telegram

## The 9 Comparison Parameters

When comparing the two plans, evaluate across ALL of these:

| # | Parameter | What to extract from each plan |
|---|-----------|--------------------------------|
| 1 | **Number of floors** | Count above-ground floors (Ground + Upper). Include any mezzanine/stilt separately. |
| 2 | **Total built-up area (BUA)** | Sum of all floor areas in sqm or sqft. Note unit. |
| 3 | **FSI / FR** | Floor Space Index / Floor Ratio. BUA ÷ plot area. Note the sanctioned vs proposed value. |
| 4 | **Number of basement floors** | Count of below-ground floors. Note if used for parking or storage. |
| 5 | **Parking area** | Total area dedicated to parking (basement + stilt + surface) in sqm/sqft. |
| 6 | **Car parking count** | Number of car parking spaces (ECS + open). Note covered vs uncovered. |
| 7 | **Setback area** | Front, Rear, Left, Right setbacks in metres. Note if pre-DCR encroaches on sanctioned setbacks. |
| 8 | **Building height** | Total building height in metres (from ground level to topmost slab/parapet). |
| 9 | **Floor-to-floor height** | Height from slab to slab per floor (typical and ground floor) in metres. |

## Vision Analysis Technique for Single-Plan Extraction

When the user uploads a **single Pre-DCR drawing PDF** and asks you to extract details (not compare), use vision_analyze to extract:

### Extraction Targets

| Data Type | How to Extract |
|-----------|----------------|
| **Building height levels** | Look for the elevation view — it has vertical height markings like `+X.XXX M` alongside the building profile. Extract every level from basement to parapet. These are typically on the left side of the elevation drawing. |
| **Floor count & configuration** | Identify labelled floor plans (e.g. "Lower Basement Floor Plan", "Ground Floor Plan", "Typical 2nd & 4th Floor Plan") |
| **Floor-to-floor height** | Subtract consecutive level values (e.g. +6.299 - +3.374 = ~2.925m) |
| **Room dimensions** | Look for callouts like `3.000 X 3.000M` inside floor plan rooms |
| **Site plan** | Look for "SITE PLAN (Scale 1:500)" — extract orientation, building footprint, approach road |
| **Total height** | From ground level (±0.00) to highest point (Parapet LVL / OHT / Lightning Arrestor) |
| **Basement depths** | Negative level markings (e.g. -2.70 M, -5.75 M) |

### Prompt Pattern for vision_analyze

For best results, use a **two-pass** approach:

Pass 1 — general survey:
```
"Describe this architectural drawing in detail. What can you see in the title block (usually bottom right corner)? What is the project name, developer, architect, date, drawing number, scale? What floor plans are shown? What are the key dimensions, height markings, and measurement callouts you can see?"
```

Pass 2 — specific extraction (after you see the visual analysis):
```
"Read all title blocks, data tables, and written text on this architectural drawing. Focus on: the title block (top/bottom right corner) for project name, address, drawing title, date, scale, drawing number, architect/consultant name. Also look for any schedule/table showing areas, floor-wise details, parking count, FAR calculations."
```

### Known Limitations

- **OCR struggles with small text** in title blocks — engineering drawings use 6-8pt fonts that OCR often misses. Rely on the visual description for title block data.
- **Overlapping text & lines** — dimension callouts overlapping with wall lines cause garbled OCR output. Cross-reference the visual analysis with the OCR text.
- **Multiple floor plans on one sheet** — the drawing may stack 7-8 floor plans + elevation + section + site plan on one A0 sheet. Each area is small and text is compressed.

### Verified Example

**Ranka NorthStar Pre-DCR (Jul 2026):** Extracted from a single-sheet drawing:
- 2 Basements (2nd at -5.75m, 1st at -2.70m) + Ground + 5 Upper Floors + Terrace + Parapet
- Elevation levels: +3.374, +6.299, +9.223, +12.147, +15.071, +17.595 (Terrace), +20.247 (Parapet)
- Floor-to-floor height: ~2.924m between upper floors
- Room sizes from callouts: bedroom 3.000×3.000m, living/dining 3.000×4.000m
- Site Plan at 1:500, elevation/section views present

## WhatsApp Message Template for Architect

When asking the in-house architect (Sinchana Gowda or equivalent) to manually verify:

```
Sinchana — please manually compare the two Ranka Northstar plans across these parameters:

1. Number of floors in each plan
2. Total built-up area (BUA) in each
3. FSI/FR (Floor Space Index / Floor Ratio) in each
4. Number of basement floors in each
5. Total parking area in each
6. Number of car parking spaces in each
7. Setback area — how much setback is being left on all sides in each plan
8. Building height in each
9. Floor-to-floor height in each

Reference plans:
- Last sanctioned: PRJ_0987_21-22
- Latest: Pre-DCR version (recently submitted)
```

## Output Format (Automated Comparison)

If analysing via vision_analyze on both PDFs, present results as a side-by-side table:

| Parameter | Sanctioned Plan (PRJ_0987_21-22) | Pre-DCR (Proposed) | Change |
|-----------|----------------------------------|-------------------:|--------|
| Floors | G+3 | G+4 | +1 floor |
| BUA | X sqm | Y sqm | +Z sqm |
| FSI/FR | 1.80 | 2.10 | +0.30 |
| Basements | 1 | 1 | Same |
| Parking area | A sqm | B sqm | +C sqm |
| Car parking | 22 | 28 | +6 |
| Setbacks F/R/L/R | 3/3/1.5/1.5 m | 2.5/2.5/1.5/1.5 m | Reduced front/rear |
| Building height | 15.0 m | 18.5 m | +3.5 m |
| Floor height | 3.0 m | 3.0 m | Same |

## Known Pitfalls

- **Missing DRAAS Drive OAuth token** — The `google-draas` service token for ndr@draas.com may not exist in the vault. The vault may only have `google-gmail` and `google-ahfl` tokens. If the user's plan PDFs are on ndr@draas.com's Drive, they are unreachable without re-authorization or direct file sharing.
- **Vision analysis on architectural drawings** — PDFs may be large (A0/A1 sheets), scanned, or have fine text that OCR misses. Use vision_analyze with specific questions about each parameter rather than generic "read this PDF".
- **Unit mismatches** — Plans may mix sqm and sqft. Convert: 1 sqm = 10.764 sqft. Always state the unit.
- **Revision naming** — The pre-DCR plan may not be named clearly. Search for "pre DCR", "preDCR", "proposed", "latest", or "revision" variants in the project's Drive folder.
