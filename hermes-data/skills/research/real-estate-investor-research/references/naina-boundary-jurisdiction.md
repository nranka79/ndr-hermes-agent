# NAINA (Namma Bengaluru Infrastructure Authority) — Boundary & Jurisdiction

## What is NAINA?

**NAINA** = **Namma Bengaluru Infrastructure Authority** (ನಮ್ಮ ಬೆಂಗಳೂರು ಮೂಲಸೌಕರ್ಯ ಪ್ರಾಧಿಕಾರ)

A planning authority established by the Karnataka government (2016-17) specifically for the **Bangalore International Airport Area Planning Authority** — the belt around Kempegowda International Airport (KIA) along the NH44 corridor. It functions as the dedicated urban development authority for the airport influence zone.

## Jurisdiction Boundary

NAINA's jurisdiction is **limited to**:

| Taluk | District Side | Notes |
|-------|--------------|-------|
| **Bengaluru North Taluk** | Bengaluru Urban | Parts of the taluk nearest to the airport |
| **Devanahalli Taluk** | Bengaluru Rural | The airport-centric zone |

**NAINA ends at the Devanahalli Taluk border** — once a parcel crosses into **Chikkaballapur District**, NAINA has **no authority**.

## Land Outside NAINA — Who Governs?

For parcels in **Chikkaballapur District** (or beyond the Devanahalli taluk border):

| Authority | Role |
|-----------|------|
| **Chikkaballapur City Corporation (CCC)** | Acts as the **Local Planning Authority (LPA)** — sanctions building plans, layouts, and development permissions |
| **Chikkaballapur LPA / DTCP** | For areas outside CCC limits, the District Town & Country Planning authority |
| **BDA Revised Master Plan 2031** | Overarching land-use zoning at the metropolitan level (applies to the entire BMA) |
| **Deputy Commissioner — Chikkaballapur** | Revenue conversion (Ag→Non-Ag under KLR Act Sec 95) |

## How to Determine NAINA Applicability

When a user asks "is this land inside or outside NAINA?":

1. **Check the district** — If the village/taluk falls in **Chikkaballapur District**, it is OUTSIDE NAINA.
2. **Check the taluk** — If the taluk is **Devanahalli** or **Bengaluru North**, it MAY be inside NAINA (still need to verify exact village boundaries within NAINA notification).
3. **Check coordinates** — NAINA's GIS boundary can be cross-referenced with the Karnataka government's NAINA notification maps.
4. **Known NAINA-covered villages**: Parts of Yelahanka, Devanahalli, and specific villages on the Bengaluru Rural side of the border.

## Critical Constraint — Applies Regardless of Authority

**Airport Height Restriction Zone (AAI/KIA Funnel):**
Whether inside NAINA or under Chikkaballapur LPA, any land near KIA falls under the **Kempegowda International Airport Height Restriction Funnel**. This is regulated by the **Airports Authority of India (AAI)** and is independent of the planning authority:
- Maximum building height is severely limited (~G+2 or G+3, approx. 12–15m max AGL)
- Exact limit depends on proximity to Runway 09/27 approach path
- This is a binding limitation that caps development potential regardless of which planning authority approves the plan

## Worked Examples

| Parcel | District | Taluk | NAINA? | Planning Authority |
|--------|----------|-------|--------|-------------------|
| **Nandi Cross (13.37°N, 77.72°E)** | Chikkaballapur | Chikkaballapur | ❌ No | Chikkaballapur LPA / CCC |
| **Yaluvahalli, Sy 11 & 13** | Chikkaballapur | Chikkaballapur | ❌ No | Chikkaballapur LPA / CCC |
| **Devanahalli town** | Bengaluru Rural | Devanahalli | ✅ Yes (likely) | NAINA |
| **Yelahanka** | Bengaluru Urban | Bengaluru North | ✅ Yes (partial) | NAINA / BDA |

## Key Implication for DRAAS

Since NAINA doesn't apply to Chikkaballapur parcels:
- **No NAINA-specific layout approval process**
- **No NAINA-specific FAR or development charges**
- Direct dealing with **Chikkaballapur LPA / CCC** for approvals
- But **airport height restrictions remain** — always flag this
- BDA RMP 2031 land-use zoning is the guiding master plan at the metro level

## Related References
- BDA RMP 2031: See `kaval-byrasandra-irr-case-study.md` for FAR by road width in BBMP areas
- KIADB norms: See `kiadb-feb2026-norms-research.md` for KIADB-ruled land near the airport corridor
- Airport height zone: Verify with AAI obstruction chart for KIA Runway 09/27
