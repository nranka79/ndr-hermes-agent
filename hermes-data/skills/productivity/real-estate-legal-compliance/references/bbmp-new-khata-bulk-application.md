# BBMP/GBA New Khata — Bulk Multi-Storey Flat Unit Application

## When to use
A developer (DRAAS) has completed a multi-storey residential building and needs **individual khata** for each apartment in bulk. The portal is bbmp.karnataka.gov.in/newkhata (run under GBA / Bengaluru City Corporations). Use this reference every time (Ranka Amber, Oasis, Udaya, NorthStar, etc.).

## Data sources needed
- **Occupancy Certificate (OC)** — building identification, e-PID, floor-wise as-built gross built-up areas, FAR, coverage, parking, common amenities, dates
- **Commencement Certificate (CC)** — sanctioned LP ref, construction start date
- **Sanctioned Building Plan** (modified/current version, not the original if discrepancies exist) — FAR, coverage, per-floor deductions, parking layout, room schedule
- **Unit Sale Deeds / Allotment letters** — flat number, owner name, carpet area, UDS, parking entitlement (these are NOT in OC/CC/plan)

## Portal form screens (in order)

### Screen 1 — Login
- Mobile + CAPTCHA → OTP (OTP goes to the mobile registered against the e-PID in eKhata system)
- e-PID No. of the parent property

### Screen 2 — "Actual Floors Overall Details" (one row per floor)
Fields: Floor Type (dropdown: Basement / Ground & Above) | Floor Number | Gross Built-Up Area (SqM) | Deduction from Gross Built-Up Area (SqM) | Total Built-Up Area (SqM) [auto] | Deductions: Stair Cases (SqM) | Lift (SqM) | Lift Machine (SqM) | Void (SqM) | Sub Structure (SqM) | Ramp (SqM) | Others (SqM) | Proposed FAR Area (SqM) | Total FAR Area (SqM) [cumulative]

### Screen 3 — "Unit/Flat-wise Actual Break-up" (one row per flat)
Fields: Type of Use of Unit/Flat (Residential) | Unit or Flat Number * | Carpet Area (in SqM) | Built-Up Area (in SqM) | Common Area (in SqM) | Super Built-Up Area (in SqM) | Undivided Share of Land (SqM) | UDS out of Plot Area (SqM) | No. of Car Parking * | Area of each Car Parking Slot (SqM) | Total Car Parking Area (SqM) | Construction Start Date | Construction Completion Date | Usage Category Types | Name of Unit/Flat Owner *

### Screen 4 — OC details for the Tower/Block/Building
Has OC been obtained? (Yes/No) | Tower/Block/Building Name | Number | Scan & Upload OC (≤1 MB, JPG/PDF/PNG) | OC Number * | OC Date * | Floor-wise table: S.No | Floor Type | Floor Number | Gross Built-up Area actually in OC (SqM) | FAR Area Achieved (SqM) | Type of units on the floor | No. of units on the floor | Other use details of the floor in OC | Total Coverage Area (SqM) * | Coverage as % *

### Screen 5 — Tower-wise status + Declaration
Per-tower table: Gross Built-up Area in plan approval / FAR Area Achieved / Actual Gross Built-up Area achieved / A-Khata for which consider | 3 declaration check-boxes | Acknowledgement Preview Form

## Key data-mapping rules

**Floors Overall — deduction split (the plan gives only a single deduction column per floor):**
- **Basements** (gross 454.21 / deduction 443.92): allocate 443.92 to **Sub Structure** (car parking). Net FAR contributed = 10.29.
- **Ground floor** deduction: allocate to **Ramp** (the ramp itself is 3.50 × 16.16 = 56.6 SqM; verify exact allocation with the architect).
- **Floors 1st–13th** deduction 6.08: equals **2 × 8-passenger lift wells (1.60 × 1.90 m = 3.04 SqM each)**. Verified by exact arithmetic — the entire sanctioned deduction column on upper floors IS the two lift wells.
- **Terrace** deduction 51.21: allocate to **Others** (lift machine room + staircase head-room + OHT). Terrace is fully deducted → net contributing FAR = 0.
- **Staircase**: the sanctioned statement does NOT deduct it (stair core stays inside FAR). The staircase is 1.60 m wide, 2 flights, 22 risers. If the portal insists on a stair deduction, have it measured from the plan and re-check FAR.
- **Total deduction** = 1,511.00 SqM; **Net FAR** = 3,700.44 SqM (on a net site of 1,000.59 SqM → FAR = 3.698).

**Unit-wise — pre-fill rules:**
- Built-Up Area = per-floor OC as-built gross (not sanctioned net FAR; about 280 SqM per floor for a 4BHK).
- Flat numbers: floor-wise convention (201 = 2nd floor #01; 301 = 3rd floor #01; ... 1301 = 13th floor). Verify against sale deeds.
- UDS out of Plot Area = plot area ÷ units (e.g., 1,000.59 ÷ 12 = 83.38 SqM each, equal share). Reconcile against sale deed proportion.
- Construction start = CC date; completion = OC date.
- Parking: plan norm 2 per flat × 12 = 24; surplus above that is visitor/common. Slot area = 2.50 × 5.00 m standard (12.50 SqM).
- Owner names, carpet area, common area, super built-up, exact UDS, parking allotment → **from sale deeds** (yellow cells).

**OC screen — floor-wise as-built vs FAR:**
- As-built gross per floor from OC; FAR achieved uses the sanctioned net-FAR distribution (the OC does not itemise FAR floor-wise).
- Site verification: the OC's printed coverage % and the land area may compute slightly differently (e.g. 17.09% OC vs 16.64% plan). Use the OC's printed figure.

## Document conflicts to flag (every project check)
1. **Site area** — plan title block often carries a larger area (e.g. 1,851.00 SQM) while the modified site plan shows the net area used for FAR/coverage (e.g. 1,000.59 SQM). The difference is typically road-widening / ROW. Verify against title deed — this feeds UDS.
2. **Unit count** — plan parking notes may say "13 UNITS = 26 CARS" while OC lists 12 residential units. The 13th unit may be the 1st floor. OC is authoritative for the khata.
3. **Plan area totals reconciliation** — if the plan sheet carries two tables (original approval + modified), only the modified table adds up correctly. Flag the mismatch and use only the modified table.
4. **13-unit column naming** — the OC table has a 1st floor with full unit-sized FAR; if OC does not list it as residential, confirm its use before filing.

## Deliverable format — two accepted shapes

**Shape A — portal-order fill workbook (video-screen derived):**
- Sheet 1: "APPLICATION DATA (FILL)" — sections in portal order, each section with the corresponding video screen embedded to the right, colour legend (GREEN = verified from document · YELLOW = from sale deed · ORANGE = derived — confirm)
- Sheet 2: "VIDEO SCREENS (REFERENCE)" — full-size screenshots from the training video, captioned
- All totals cross-checked (floor gross sum, FAR sum, UDS sum, parking sum against OC/plan)

**Shape B — the GBA sample spreadsheet ("Smple excel sheet for multi unit khata.xlsx", verified Oct 2026).** When the user supplies this exact 2-sheet template, fill it directly — its columns differ from the portal screens above, so map carefully:

| Sheet | Column | Source / rule |
|---|---|---|
| `unit data` | A Type Of Use | "Residential" |
| | B Unit Type/Flat Type | "Residential Flat (3/3.5/4 BHK — confirm from sale deed)" |
| | C Unit/Flat Number | floor+unit convention (201…1301 for a 12-floor tower); VERIFY vs sale deeds |
| | D Built-Up Area (SqM) | per-floor OC as-built gross (~280 for a 4BHK; Ranka Iris: 281.52 even / 279.96 odd floors) |
| | E Private Open Balconies / F Terraces / G Lawn | NOT in OC — from sale deed / architect statement (leave yellow) |
| | H Carpet Area | from sale deed / area statement (leave yellow) |
| | I Common Area | from sale deed / area statement (leave yellow) |
| | J Super Built-Up Area | **formula stays in template: =D + ((E+F+G)*0.33) + I** — do NOT overwrite with a value |
| | K UDS, out of 1,000.59 sqm site | Ranka Iris verified: 83.3825 = 1,000.59/12 equal share (confirm plot area vs title deed — title block said 1,851.00) |
| | L No of Car Parking | 2 per flat (confirm vs sale deed entitlement) |
| | M Area of Each Slot | 12.50 (2.50 × 5.00 m) |
| | N Total Parking Area | **formula stays: =L*M** (25.00 per flat) |
| | O Area of Parking Slot | only for type=Parking rows — leave blank for Residential |

`floor data` (delete the placeholder floor-number rows the template pre-fills to 40; keep exactly the building's floors):

| Column | Source / rule |
|---|---|
| A Floor Number | label rows B1/B2/B3/GF/1st…13th/Terrace (replace the template's numeric 1–40) |
| B Floor Gross BUA (F-GUBA) | modified/final sanction area statement (Ranka Iris: B1–B3 454.21, GF 166.50, 1st 271.82, 2nd/4th/6th/8th/10th/12th 280.04, 3rd/5th/7th/9th/11th/13th 279.84, Terrace 51.21) |
| C Floor Cutouts in F-GUBA | 0 for this building (kept formula =MAX(B-C,0)) |
| D F-TUBA | formula stays |
| E Stair Cases | 0 — staircase kept inside FAR on this plan |
| F Lift | 6.08 on 1st–13th (2 × 1.60×1.90 m 8-passenger wells) |
| G Lift Machine | **51.21 on Terrace** — this template has NO "Others" head, so terrace machine+OHT goes under Lift Machine |
| H Void | 0 |
| I Sub Structure | 443.92 per basement (B1/B2/B3 car parking) |
| J Ramp | 48.99 at GF |
| K Parking | 0 (basement parking already inside Sub Structure) |
| L Refuge / M Common Service | 0 |
| N Proposed FAR | formula stays =MAX(D - SUM(E:M), 0) |
| O No of Units/Slots | B1=9, B2=10, B3=11 parking slots; 2nd–13th=1 unit; GF/1st/Terrace=0 |
| P Carpet other than tenements | 0 |

Totals reconcile: gross 5,211.44 − deductions 1,511.00 = net FAR 3,700.44 SqM (on 1,000.59 sqm site → FAR 3.698). Add a TOTAL row with SUM formulas. When filling, **never overwrite the template's J/N/D formulas** — write only the source values (unit D/E/F/G/I/K/L/M and floor B/C/E–M/O/P), keep formula cells untouched. Colour-code: GREEN = verified from OC/CC/plan · YELLOW = to confirm from sale deed. Save as `Ranka_Iris_Multi_Unit_Khata_Filled.xlsx` under `/data/hermes/document_cache/ranka_iris/`.