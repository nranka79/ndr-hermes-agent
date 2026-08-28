# Deed of Declaration — Karnataka Apartment Ownership Act, 1972

## Overview
A Deed of Declaration is the foundational document submitted under the Karnataka Apartment Ownership Act, 1972 (KAOA) to create a Condominium Regime. Once registered, each apartment becomes a heritable and transferable immovable property under Section 3 of the Act.

## Key Differences from Sale Deeds / Lease Deeds
| Aspect | Sale/Lease Deed | Deed of Declaration |
|--------|----------------|---------------------|
| **Purpose** | Transfer rights between parties | Submit entire building to Act |
| **Parties** | Vendor/Vendee or Lessor/Lessee | Grantor (Owner+Developer) |
| **Schedule** | Plot/unit dimensions | Per-apartment area table (Schedule A) |
| **Annexures** | Title docs, EC | Floor plans, Bye-laws (Exhibit B) |
| **Registration** | Sub-Registrar | Mandatory under Section 13 |

## Section 11 — Required Contents of a Declaration
(a) Description of the land with building name
(b) Description of the building
(c) Number of floors, basements, and apartments
(d) Description of each apartment with area, location
(e) Description of common areas and facilities
(f) Description of restricted common areas
(g) Value and percentage of undivided interest
(h) Basis for calculating undivided interest

## Section 16 — Bye-laws Required Contents (Exhibit B)
1. Election of Board of Managers — powers and duties
2. Method of calling meetings
3. Procedure for meetings and voting
4. Method of collecting contributions for common expenses
5. Maintenance, repair and replacement of common areas
6. Keeping of accounts and audit
7. Regulating use of apartments and common areas
8. Fines and penalties
9. Amendment of Bye-laws
10. Arbitration of disputes

## Drafting Workflow

### Phase 1 — Research & Template Gathering
1. Search Drive for existing Deed of Declaration from sister projects (e.g., RAQ/Ranka Aquagreens template)
2. Search Drive for the full KAOA Act text
3. Search Drive for the project's sale agreement (confirms whether project is governed under KAOA)
4. Search Drive for sanctioned plan, OC, Fire CC, and area spreadsheets

### Phase 2 — Data Collection
- Number of apartments (verify against OC — not just floor count)
- Per-unit areas: Carpet, Balcony, BUA, Common, SBUA, UDS
- Total site area
- % Undivided Interest = (Unit SBUA ÷ Total SBUA) × 100
- Total UDS should approximate total site area (cross-check)
- List of common areas and facilities unique to the project
- Structural engineer details (for Form IX reference)
- OC number, date, issuing authority
- Fire CC number, date

### Phase 3 — Multi-Agent Drafting (parallel)
Use `delegate_task` with 3 concurrent agents per batch:

**Batch 1 (3 agents parallel):**
- Agent A: Clauses 1-7 (Preliminary, Property, Building, Common Areas)
- Agent B: Clauses 8-14 (Rights, Interests, Administration, Covenants)
- Agent C: Clauses 15-22 (Financial, Compliance, Obligations)

**Batch 2 (2 agents parallel):**
- Agent D: Clauses 23-28 (Damage, Default, Execution) + Exhibit B framework
- Agent E: Schedule A (Apartment-by-apartment table)

**Assembly:** Compile all clauses, fix apartment count (verify against OC), add Schedule A + Exhibit B, format in python-docx, upload to Drive.

### Phase 4 — Template Adaptation
When adapting a template from a sister project:
- Replace ALL project names (e.g., "RANKA AQUAGREENS" → "RANKA IRIS")
- Update property descriptions, survey numbers, khata numbers
- Adjust committee sizes proportionally (RAQ: 7-15 for 100 units → 3-5 for 12 units)
- Adjust quorum requirements (RAQ: 50 owners → 51% or 5 members for small projects)
- Update association name (e.g., RAGAOA → RIAOA)

## Schedule A Format
Required columns per Section 11(g)(h):
| Sl.No. | Apt No. | Floor | Type | Carpet (sqft) | Balcony (sqft) | BUA (sqft) | Common (sqft) | SBUA (sqft) | Terrace (sqft) | UDS (sqft) | % Interest | Car Parks |

Key checks:
- **Verify unit count against OC** — don't assume one unit per floor
- Total UDS × units should ≈ total site area
- 13th/top floor often has exclusive terrace — higher SBUA, proportional UDS recalculation needed
- Car parks listed but numbers left as placeholders

## Common Grantor Structures
| Scenario | Grantor Setup |
|----------|--------------|
| **Outright purchase** — Developer bought land | Single Grantor: Developer Company |
| **Joint Development** — Landowner + Developer | Two Grantors: Owner + Developer |
| **Company-owned** — Developer is sole owner | Single Grantor: Developer (as Owner & Developer) |

## Pitfalls
- ❌ Don't assume apartment count from floor count — verify against OC
- ❌ Don't use wrong Grantor structure — check title deeds to determine if land was bought outright or via JDA
- ❌ Don't leave area values unverified — cross-check UDS totals against site area
- ❌ Don't forget to update committee sizes and quorum for small buildings (fewer units = smaller committee)
- ❌ Don't put Grantor No.1 as individual when DRA owns the land outright
- ❌ Always include a note about the 13th floor terrace unit needing proportional UDS recalculation
