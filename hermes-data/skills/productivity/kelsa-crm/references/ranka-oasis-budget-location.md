# Ranka Oasis Budget — Where the Numbers Live (2026-07-31)

## The core problem

Kelsa DRA Project Budgets (pipeline 2033) contains **182 Ranka Oasis budget
lines** (structure only — Category / Budget Head / Budget SubHead) but every
line has `cf_budget_amount = 0`. Verified via:
- `get_stats(pipeline_id=2033, group_by="cf_category", stat_field="cf_budget_amount", stat="sum", query="Ranka Oasis")` → sum=0 for all 6 categories
- `search_leads(pipeline_id=2033, query="Ranka Oasis;cf_budget_amount>0")` → 0 results
- Individual `get_lead` calls → "Budget Amount: 0" on every sampled line
- Snapshot sheet "DRA Realty Kelsa Budget Heads & Categories" (2025-12-05) also shows 0 for all 182 Oasis rows (other projects like Ranka Iris DO have amounts)

**Lesson: Kelsa budget pipeline = structure for Oasis; the amounts were never
entered there.** Always cross-check Drive before reporting a total.

## Drive files holding the real budget

| File | Type | What it holds |
|---|---|---|
| **Ranka OASIS Residential_Layout_Budget Sheet** (`1ufpqy2fD1YBcXvlbFIXiZOob3WYGpgxiGEKDx0UKR_I`, Kantesha-owned copy, 2026-03-03) | spreadsheet | **The macro budget.** Tab "Residential Layout Budget". Total ₹8,14,93,450 pre-GST / ₹9,61,62,271 incl 18% GST. |
| Same sheet, contractor copy (`1QmwE3AayGbrHUBcMjJQMUjA0yQ97L4KF2SRlhg2R00U`) | spreadsheet | Owned by paramvahconstructionag — **404s from ndr@draas.com token**. Use the Kantesha copy. |
| xlsx copy (`1_6eDBaSzHSIv12ZfDrppRanfhsmDpPAA`) | sheet | Also 404s. |
| RANKA OASIS Master File List v6 (`1ZoMZ2rgRmWanL5EiUbdhguZjqm7lxzFc802YcuCetkM`) | spreadsheet | Index of all project files; budget sheets listed under category "Financial/BOQ". Best entry point for finding budget files. |
| Ranka Oasis Budget Requirement (`1EpxRuPQscXhnlEY3TTpJvX0PGQ_PgRXOu_l22cbArfM`) | spreadsheet | **Old partial (2024)** — only Legal & Handling (₹241L), Initial Setup (₹15L), Execution (₹190L) across 3 tabs. Do not use as the total. |
| Saveganapalli Ranka Oasis Investor Costing Proposal (`11DLbtqJMyhdahI7VOiSsjxiduQicOc_PovZoN710nxk`) | spreadsheet | Assumptions: Land ₹3.0 Cr, Infra ₹1.26 Cr, construction ₹2,750/sqft + GST 18%, sellable area efficiency 57%. |

## Macro budget totals (from the 2026-03-03 sheet)

| Section | Pre-GST (₹) | Incl GST (₹) |
|---|---|---|
| 1. Pre-Construction & Approvals | 0 (amounts unfilled) | 0 |
| 2. Design Services | 17,44,650 | 20,58,687 |
| 3. Site Development & Infrastructure | 6,79,66,200 | 8,02,00,116 |
| 7. Sales, Marketing & Admin | 72,08,800 | 85,06,384 |
| 8. Contingency & Escalation | 45,73,800 | 53,97,084 |
| **GRAND TOTAL** | **8,14,93,450** | **9,61,62,271** |

Sections 4/5/6 are missing entirely from the sheet (numbering jumps 3 → 7) —
likely land/finance/legal costs not in this macro sheet. Flag this when quoting
the total.

## Ranka Oasis project master

- DRA Projects Master (4476): `RO01` = Ranka Oasis, Sevaganapalli Land Partners,
  Project Type: Layouts, Location 10.787649, 77.915934.

## Recurring pattern for other projects

To answer "what's the total budget / first-level breakup for project X":
1. `get_stats(pipeline_id=2033, group_by="cf_category", stat_field="cf_budget_amount", stat="sum", query="<project>")`
2. If sum=0 → search Drive for the budget spreadsheet (Master File List index helps)
3. First-level breakup = Category; BudgetFull naming = `Project-Category-Head-SubHead`
