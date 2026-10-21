# Multi-Unit Khata Bifurcation — Area Statement Workflow

## When to Use

- User uploads or references the BBMP multi-unit khata area statement Excel template and asks to fill it for a project (3 basements + GF + 13 floors + terrace, multiple residential units, one club floor).
- User asks to "fill the khata bifurcation sheet" with available data, identify gaps, and get the architect to measure the rest from the as-built DWG.
- Any task where the deliverable is the **floor-by-floor + unit-by-unit area statement** needed for khata bifurcation / e-Khata submission.

## Source Documents & What They Provide

| Document | Provides |
|---|---|
| **Occupancy Certificate (OC)** | F-TUBA (Floor Total Built-Up Area) per floor in Sq.M — always filled first |
| **Sale Agreements** | SUBA (Super Built-Up Area) & UDS per unit in Sq.Ft — contract authority |
| **Area Chart (internal working)** | BUA, Carpet, Balcony, Common per unit type in Sq.Ft |
| **Parking Allocation Sheet** | Parking slot numbers & allocation per unit |
| **As-Built DWG** | F-GUBA (Gross), cutouts, staircase, lift, voids, ramp, parking areas — needs manual measurement |

## Excel Sheet Anatomy

### Sheet 1: Floor Data

| Col | Label | Source |
|---|---|---|
| A | Floor Number | Floor name (B1, B2, B3, GF, 1st-13th, Terrace) |
| B | Floor Gross Built-Up Area (F-GUBA) SqM | **From DWG** — entire P-line incl. balcony, excl. cutouts |
| C | Floor Cutouts Deductions in F-GUBA SqM | **From DWG** |
| D | Floor Total Built-Up Area (F-TUBA) SqM | **From OC** = F-GUBA - Cutouts - Deductions |
| E | Stair Cases SqM | **From DWG** |
| F | Lift SqM | **From DWG** |
| G | Lift Machine SqM | **From DWG** |
| H | Void SqM | **From DWG** |
| I | Sub Structure SqM | **From DWG** |
| J | Ramp SqM | **From DWG** (basements only) |
| K | Parking SqM | **From DWG** (basements only) |
| L | Refuge Area SqM | **From DWG** |
| M | Common Service Area SqM | **From DWG** |
| N | Proposed FAR Area SqM | Computed |
| O | No of Units / Parking Slots | From project plan |
| P | Carpet Area other than Tenements SqM | Computed |

### Sheet 2: Unit Data

| Col | Label | Source |
|---|---|---|
| A | Type Of Use | Residential / Amenity/Club |
| B | Unit Type/Flat Type | Even/Odd/Club |
| C | Unit/Flat Number | From plan |
| D | Built-Up Area SqM | Area Chart (SqFt / 10.764) |
| E | Private Open Balconies SqM | Area Chart (0 if none) |
| F | Private Open Terraces SqM | Usually 0 |
| G | Private Open Lawn SqM | 0 for apartments |
| H | Carpet Area SqM | Area Chart |
| I | Common Area SqM | Area Chart |
| J | Super Built-Up Area SqM | **Sale Agreements** |
| K | Undivided Share of Land SqM | **Sale Agreements** |
| L | No of Car Parking | Parking sheet |
| M | Area of Each Car Parking Slot | Slot numbers |
| N | Total Area for Car Parking Slot | Computed |
| O | Area of Parking Slot | For parking-type only |

## Key Rules

### F-TUBA = F-GUBA - Cutouts - Deductions

**Upper floors:** F-GUBA = entire P-line. Deduct staircase (front + emergency exit at back), lift, voids, common areas.

**Basements:** Same P-line but deduct ramp, parking, ducts near ramp corner.

**Ground floor:** Parking is in basement. F-GUBA ≈ F-TUBA (no deductions).

### Sq.Ft → Sq.M

Sq.M = Sq.Ft / 10.764. Round to 2 decimal places. If the user prefers working in Sq.Ft, add a formula-based conversion sheet.

## What the Architect Measures from the DWG

Send a clear brief with the Excel + DWG access:

1. **F-GUBA per floor** — full P-line area including balcony, excluding cutouts
2. **Cutouts & Deductions** — openings through slab (courtyards, light wells, ducts)
3. **Staircase areas** — front main + back emergency exit, per floor
4. **Lift shaft** area per floor
5. **Lift machine room** area (terrace or top floor)
6. **Voids** — any other openings
7. **Ramp area** (basement floors only)
8. **Parking area** (basement floors only)
9. **Refuge area** (if applicable)
10. **Common service area** (electrical rooms, transformer, generator)

**Basement instruction:** Cut out ramp + parking + ducts near ramp corner from gross.
**Upper floor instruction:** Cut out staircase (front + back) + lift + common areas from P-line.
**Ground floor:** No deductions.

## Naming Convention

```
YYYYMMDD_ProjectName_KhataBifurcation_AreaStatement.xlsx
```

## Email Brief Template

Cover these points in the email:
- Link to partially-filled Excel (OC data + unit data + parking filled)
- Link to as-built DWG
- Numbered list: what to measure per floor
- All values in Sq.M
- Create formula conversion sheet (÷10.764) if preferred
- Private Open Terraces = 0, Private Open Lawn = 0
- Coordinate with the engineer who prepared the DWG (cc Bhuvanesh)

## Worked Example

See the session-specific reference or search session_history for "Ranka Iris Khata Bifurcation" (Oct 2026) — full worked example with Ranka Iris: 3B+GF+13F+Terrace, 12 residential units, parking allocation per flat.