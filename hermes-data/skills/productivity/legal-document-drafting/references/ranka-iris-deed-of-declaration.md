# Ranka Iris — Deed of Declaration under Karnataka Apartment Ownership Act, 1972

**Session:** June 2026 — Nishant Ranka  
**Project:** Ranka Iris (Domlur, Bangalore)  
**Document Type:** Deed of Declaration (28 clauses + Schedule A + Bye-laws framework)  
**Template Source:** RAQ Final Deed of Declaration Draft (DRA sister project)

## Context

The user wanted a **Deed of Declaration** (also called Deed of Adherence) for the **Ranka Iris** condominium to submit the property to the Karnataka Apartment Ownership Act, 1972. No such document existed for this project. An existing template from the RAQ (Ranka Aquagreens) sister project was found on Drive and adapted.

## Key Steps

### 1. Search Drive for Existing Documents
- Searched with: "deed of adherence", "deed of declaration", "apartment ownership", "Karnataka Apartment"
- Found: RAQ Final Deed of Declaration Draft (28 clauses), Karnataka Apartment Ownership Act (full text), Registered sample deeds from other projects
- Confirmed: Ranka Iris sale agreement (Clause 19) states the project IS governed under the Act
- Confirmed: No existing Deed of Declaration for Ranka Iris itself

### 2. Gather Project Data from Multiple Drive Sources

| Source | Data Found |
|--------|-----------|
| Occupancy Certificate (OC) | BBMP/Addl.Dir/JD North/0037/2013-14, 29-Apr-2026, 12 residential units |
| Area Chart (Excel) | Per-unit areas: Carpet 2,240.06, Balcony 463.06, BUA 2,843.68, Common 669.34, SBUA 3,513.02 |
| Structural Stability Certificate | Form IX — Vankata Siva Prasad (Engr), Reg. BCC/BLJ.6/S.E.186/15-16 |
| Sanctioned Plan | Permit 26822, 02-Sep-2013, BBMP |
| Fire CC | KSFES/CC/069/2026, 17-Feb-2026 |

### 3. Multi-Agent Parallel Drafting

**Pattern:** Use `delegate_task` with 3 parallel agents per batch to draft different clause sections, then assemble.

**Batch 1 (parallel):**
- Agent A: Clauses 1-7 (Preliminary, Property, Building, Common Areas)
- Agent B: Clauses 8-14 (Rights, Undivided Interest, Administration)
- Agent C: Clauses 15-22 (Financial, Compliance, Maintenance)

**Batch 2 (parallel):**
- Agent D: Clauses 23-28 (Damage, Default, Execution Block)
- Agent E: Schedule A (Apartment-by-apartment data table)

**Assembly:** Python-docx script that combines all outputs into a formatted `.docx`, uploaded to Drive.

### 4. Data Reconciliation (CRITICAL)

The OC stated 12 residential units, but the building has GF + 13 floors. The area chart listed "Typical Floors 2-12."

**Reconciliation method:** Cross-reference UDS totals against site area.
- Site area: 10,622.28 sqft
- UDS per unit: 861.28 sqft
- 12 × 861.28 = 10,335.36 sqft ✅ (closely matches site area)
- 14 × 861.28 = 12,057.92 sqft ❌ (exceeds site area)

→ **Conclusion: 12 units is correct.** The Schedule A should show 12 rows.

### 5. Document Structure

```
DEED OF DECLARATION
Clause 1 — Preliminary (Parties as Grantors: Landowner + Developer)
Clause 2 — Purpose (Submission to Karnataka Apartment Ownership Act, 1972)
Clause 3 — Description of Schedule Property (Sy.No., boundaries, Khata, OC, Fire CC, FAR)
Clause 4 — Description of the Building (3B+G+UF, basement, 12 units, 13th floor terrace)
Clause 5 — Apartment Ownership (per Section 3 of the Act)
Clause 6 — Area Statement (total SBUA breakdown)
Clause 7 — Condominium Name & Common Areas (General + Restricted)
Clause 8 — Undivided Interest in Common Areas
Clause 9 — Restricted Common Areas Rights
Clause 10 — Voting Representation (per Bye-laws)
Clause 11 — Interest as on Date of Declaration
Clause 12 — Administration (per Deed + Bye-laws Exhibit B)
Clause 13 — Plan of Apartment Ownership
Clause 14 — Common Areas Undivided (no partition)
Clause 15 — Change in Undivided Interest (75% consent)
Clause 16 — Inseparable Interest
Clause 17 — Compliance with Deed, Bye-laws, Resolutions
Clause 18 — Revocation and Amendment
Clause 19 — No Exemption from Common Expenses
Clause 20 — Monthly Maintenance Charges
Clause 21 — Charge for Unpaid Sums
Clause 22 — Binding Effect and Restrictions on Use
Clause 23 — Damage or Destruction
Clause 24 — Mortgagee Sale
Clause 25 — Voluntary Conveyance
Clause 26 — Stamp Duty and Registration
Clause 27 — Voting Rights
Clause 28 — Default Interest (12% p.a.)
Execution Block (Witnesses, Grantor signatures)
SCHEDULE A — Apartment Details Table (12 apartments)
EXHIBIT B — Bye-laws (framework)
```

### 6. Common Areas Listed (Ranka Iris)

**General Common Areas (17 items):** Land parcel, basements, ramps, lift lobbies, staircases, elevators, water supply, pumps/tanks, transformer, generator, STP, fire fighting, security room, common lighting, communication rooms, electrical rooms, all other common facilities.

**Restricted Common Areas (15 items):** Foundation, main walls, RCC columns, slabs, beams, sanitary shafts, fire shafts, concealed wiring, plumbing, sumps, OHTs, electrical/communication ducts, structural frame, terrace common areas (excluding exclusive 13th floor terrace of 2,119 sqft).

## Delivery

- Final document saved to Ranka Iris Drive folder (`1i59Ph3FmPwWF33fVIBXVclswnDF_FLXp`)
- Filename: `20260607_Ranka_Iris_Deed_of_Declaration_Draft.docx`
- File ID: `1qk23oL5acO8oEeumqTiM4748TXni3ian`
- Drive Link: https://docs.google.com/document/d/1qk23oL5acO8oEeumqTiM4748TXni3ian/edit?usp=drivesdk

## Placeholders to Fill

1. Landowner name (Grantor No. 1)
2. Boundary descriptions (E/W/N/S)
3. Director name for DRA Developers
4. Execution date
5. Floor 13 unit % undivided interest (needs recalculation due to larger SBUA including terrace)
6. Car park numbers per apartment
7. Full Bye-laws (Exhibit B) — RAQ template available

## Pitfalls

- **Apartment count discrepancy:** The building has multiple floors but the OC said 12 units. Cross-reference UDS total vs site area to determine correct count. Do NOT assume each floor has one apartment.
- **Template adaptation:** When using a sister-project template (RAQ → Ranka Iris), the party names, property description, building specs, and areas must be COMPLETELY replaced. The template structure (28 clauses) and concepts (General/Restricted Common Areas) carry over but all data changes.
- **Parallel agent coordination:** When using delegate_task for multiple clause drafts, provide EACH agent with: (1) the template structure, (2) full project data, (3) the specific clauses they're drafting, (4) the relevant Act sections. Missing context = inconsistent drafting.
- **Schedule A reconciliation:** % Undivided Interest must total 100%. Verify by summing all percentages after drafting. If 12 units each have 8.33%, total = 99.96% (rounding is acceptable).
- **Registered document failure mode:** Some Indian legal documents (esp. registered JDAs, family deeds) fail pymupdf text extraction due to their registered document format. Always try pdftotext + vision as fallback.

## Applicable Act

Karnataka Apartment Ownership Act, 1972 (Karnataka Act No. 11 of 1973)

Key sections for a Deed of Declaration:
- **Section 3:** Status of apartments (heritable and transferable)
- **Section 6:** Common areas and facilities (remain undivided, no partition)
- **Section 7:** Compliance with covenants, bye-laws
- **Section 11:** Contents of Declaration (must include land description, building description, apartment details, common areas, % undivided interest, calculation basis)
- **Section 12:** Contents of Deeds of Apartments
- **Section 13:** Registration requirements
- **Section 16:** Bye-laws and their contents
- **Section 17:** No waiver of common areas use to avoid contribution
- **Section 19:** Charge on property for common expenses
- **Section 22:** Disposition on destruction/damage
