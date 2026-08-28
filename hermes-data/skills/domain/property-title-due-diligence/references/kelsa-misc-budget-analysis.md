# Kelsa: Budget-hierarchy & "Miscellaneous" usage analysis (invoices / PO-WO)

Session-proven workflow (Aug 2026) for: "analyze where we used Miscellaneous in budgets on
invoices / PO-WO, why, and produce ≥20 samples from each pipeline."

## Pipelines (account DRA, id 5)
- **516 DRA Invoice Processing** — Invoice, 8 stages, ~3,500 records.
- **537 DRA PO-WO Issuing** — PO-WO, 6 stages, ~757 records.
- **2033 DRA Project Budgets** — Budget Item master; the budget hierarchy lives here:
  Company Name → Projects → Category (12 dropdown opts) → Budget Head (118 dropdown opts)
  → Budget SubHead (text). BudgetFull = "<Project>-<Category>-<Head>-<SubHead>" (e.g.
  "General Overhead-Business Development-Miscellaneous-Individual").

## Field identifiers (from get_pipeline)
Invoice 516 budget fields (all master → dra_project_budgets):
- cf_projects_budget (Projects(Budget)), cf_category1 (Category), cf_budget_head3 (Budget Head),
  cf_budget_sub_head3 (Budget Sub Head), cf_budget_balance (Budget Balance)
- SECOND budget set in "Budgeting & Analysis" section: cf_budget_head11, cf_budgetid — search
  these too; a handful of records only populate these.

PO-WO 537 budget fields (master → dra_project_budgets):
- cf_company_name_budget, cf_project_new1 (Project), cf_category (Category),
  cf_budget_head (Budget Head), cf_project_new (Budget Sub Head — yes, it's the SUB HEAD,
  despite the name), cf_balance_budget.

Budget master 2033:
- cf_category (12 opts), cf_budget_head_dd (118 opts), cf_budget_subhead (free text).

## Search semantics — critical
- Master-linked fields search by the LINKED RECORD's display name, not by a controlled value
  list. `cf_budget_head3:Miscellaneous` matched 85 invoices because they link to a budget
  record whose BudgetFull contains "Miscellaneous".
- Search is CASE-SENSITIVE-ish / exact-token; variants that all mean "misc" must be swept
  separately: `Miscellaneous`, `misc`, `misc - unbudgeted`, `unbudgeted`,
  `misc / probables / contingency`, `external - miscellaneous`.
- `get_stats(group_by=cf_...)` is the fastest way to enumerate what values actually exist per
  field (e.g. invoice cf_category1: N/A 2374, unbudgeted 334, misc/probables/contingency 73,
  business development 111...). Run it on cf_category, cf_budget_head, cf_budget_sub_head
  for BOTH pipelines before picking samples — the top misc bucket is often category "Unbudgeted"
  + subhead "Misc - Unbudgeted" (334 invoices), not Budget Head "Miscellaneous" (85).

## Sample workflow
1. list_pipelines(account_id=5) → find 516 / 537 / 2033.
2. get_pipeline on each → field ids + stages.
3. get_stats group_by each budget field on both pipelines → distribution map.
4. search_leads(pipeline, query="cf_budget_head3:Miscellaneous", per_page=100) etc. per variant.
5. get_lead on a representative spread (varied vendors/amounts/levels) — 20–25 per pipeline.
   Capture: vendor, amount, invoice/PO no, date, Projects/Category/Head/SubHead actually set,
   Description/Narration (tells you the real product/service), stage.
6. Classify each record into why-it-landed-in-misc buckets (see below).

## Root-cause taxonomy observed (DRA, FY23–FY26)
- **No granular overhead head in master**: budget heads are almost all project-execution
  (civil-*, electrical, landscape, drawings, structure, marketing collaterals). No heads for
  travel, telecom, insurance, vehicle O&M, office supplies, legal retainers, software → falls
  to the catch-all node.
- **Company-level catch-all node**: Westbury "General Overhead → Business Development →
  Miscellaneous → Individual" (₹3.0 Cr budget) absorbed 85 invoices — flights (Cleartrip,
  Yatra, MakeMyTrip, Vistara), hotels (Booking.com, JW Marriott, ITC Goa, Oberoi), IKEA,
  car servicing, all as "No PO" reimbursements.
- **Genuinely unplanned one-offs (legitimate misc)**: office kombucha, ChromeBook via Amazon,
  one-off AI-platform WO, first Tally install.
- **Small recurring ops bills defaulted to "Unbudgeted"**: milk ₹2–3k/mo, flowers, stationery,
  Airtel mobiles → 334-invoice Unbudgeted bucket.
- **Enforcement gap**: budget fields optional at record creation (data-entry prerequisite marks
  them "optional"), required only at HoD approval; nothing caps misc or forces justification.

## Remediation pattern to include in deliverables
Add overhead heads (Travel & Conveyance, Business Entertainment, Gifts & Corporate Relations,
Telecom & Internet, Vehicle O&M, Office Supplies, Software & IT, Professional Fees, Marketing,
Contingency), split the catch-all, make budget fields mandatory at creation + require a misc
justification note, target <5% invoice count / <2% value on misc after retro-classification.
