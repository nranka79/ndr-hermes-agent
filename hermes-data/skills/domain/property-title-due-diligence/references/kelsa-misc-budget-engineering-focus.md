# Kelsa Misc-Budget Analysis — Engineering-Focused Re-analysis & Budget-Tree Mapping

Follow-up to `kelsa-misc-budget-analysis`. When the user asks to re-analyze misc/unbudgeted usage with **engineering-only scope** (civil, execution, electrical, plumbing, MEP, finishing, site works) and to **map records into the new budget tree**, use this workflow.

## Scope filters (user-defined, 2026-08)
- INCLUDE only: engineering / civil / execution / electrical / plumbing / MEP / finishing / construction-site work.
- EXCLUDE: hotels, travel, transport, catering, kombucha, legal fees, retail/stationery, IT/software, land-sale brokerage, and **any unbudgeted bill under ₹50,000**.
- Amount floor: only records > ₹50,000 (user: "ignore any bill marked as unbudgeted which is under 50,000 rupees").

## Query recipe (DRA account id 5)
Pipelines: Invoice Processing = 516, PO-WO Issuing = 537, Project Budgets = 2033 (budget tree).

Invoice misc variants (516):
- `cf_category1:Unbudgeted;cf_amount>50000`
- `cf_budget_head3:Miscellaneous;cf_amount>50000` (mostly Westbury BD — out of engineering scope)
- `cf_budget_sub_head3:misc;cf_amount>50000`
- `cf_budget_sub_head3:Unbudgeted;cf_amount>50000` (Taal land invoices)

PO/WO misc variants (537):
- `cf_category:Unbudgeted;cf_total_amount>50000`
- `cf_budget_head:Miscellaneous;cf_total_amount>50000`
- `cf_budget_head:misc;cf_total_amount>50000`
- `cf_project_new:misc;cf_total_amount>50000` (sub-head misc — RPL Landscape/Misc cluster)

## Record link format (CRITICAL for the "give me links" requirement)
Every Kelsa record has a direct link: `https://kelsa.io/<pipeline_id>/leads?current_item_id=<lead_id>`
- Invoices: `https://kelsa.io/516/leads?current_item_id=<id>`
- PO/WOs: `https://kelsa.io/537/leads?current_item_id=<id>`
- Embed these in the Google Doc rows — the user explicitly wants clickable links to each referenced invoice/PO.

## Classification
Pull `get_lead` for candidates. Judge engineering-relevance by: description text, vendor name, `Jobs` field (PO), and attachment filenames (e.g. "labour bill civil work", "Edwardian Chambers Execution.dwg", "borewell"). Typical engineering vendors seen: M&M construction, PARAMVAH, PMR Developers, Vardhan, Trubld, shree raksha construction, RVM infrastructure, NRK cement, sundaram borewell, sri samrudhi borewells, P.M.R Developers, Duraimurugan (labour), Harsha Greens (grass pavers), A.J. Architects.

EXCLUDE even if large: O3 Infotech (IT), Spectra (broadband), Rameshwaram/Sreenath (catering), legal firms, Yatra/travel, brokerage/commission invoices (K Siva Subramanian "commission", S Vinod Kumar "brokerage", Manimagalai "commission").

## New budget tree structure (pipeline 2033, as of 2026-08)
- Hierarchy: Project → Category (12 options) → Budget Head (118 dropdown) → Budget SubHead (free text = item level). `BudgetFull` = `Project-Category-Head-SubHead`.
- Fields: cf_company_name, cf_projects, cf_category, cf_budget_head_dd, cf_budget_subhead, cf_budgetfull, cf_budget_amount, cf_balance_budget.
- 1399 budget records. Rich Execution trees EXIST for: Ranka Amber, Serenity Estate, Ranka Oasis, RPL (Ranka Palm Lakeside, 248 records, older + new). Execution heads include Civil-* (flooring, plastering, steel, joinery, glass, masonry, concrete, painting, waterproofing), Plumbing-*, Electrical-*, Fire Protection, Landscape, Infrastructure, Compound Wall, Structure, Site Preparation/Site Cleaning, Survey, Consultant, Borewell (RPL has "Test-Borewell-Test" only), Design.
- GAPS (projects with NO execution tree, only Unbudgeted node): TAAL Land (only `TAAL Land-Unbudgeted-Unbudgeted-Unbudgeted`), Pride Cross Winds Home-1 (only `Unbudgeted-Unbudgeted-Suspense`).
- GAP heads to create (flagged in doc): Execution → Consultant → QS/PMC; Borewell → Drilling & Pumps (proper, not "Test"); Site Preparation → Earthwork/JCB; Infrastructure → Roads; Boundary & Fencing; Infrastructure → Civil Labour; Landscape → Hardscape; Civil → Finishing/Interiors.
- EXISTING nodes that fit cleanly: Execution → Design → Architect (Ranka Oasis), Execution → Landscape → Softscape, Execution → Site Preparation → Temporary Protection/Barrication (RPL), Execution → Infrastructure → STP/Waste Management (RPL), Execution → Landscape → Irrigation (Amber), Execution → Survey (Oasis), Execution → Compound Wall (RPL/Amber).

## Google Doc delivery
- Previous session: build whole doc as HTML → Drive API import (MediaIoBaseUpload) — single call, no rate limits. Used for the engineering-focus doc (id 1iVhDlshMraiKK1-f4Wmc5jEdUZ1TwFoNur6y3ELlhB4).
- This session: **append a section to an EXISTING doc** (budget-tree mapping) via Docs API `batchUpdate` with ONE `insertText` request at `document end - 1` (body.content[-1].endIndex minus 1). Single insert = no rate-limit issue; avoids the per-cell table writes that hit quota before. Works for text/bullets; use a table-free bullet format for appended sections.
- Verify after append: fetch doc, walk body content recursively (tables are separate elements from paragraphs — searching paragraphs alone misses table content).

## Doc sharing preference (user instruction, 2026-08)
- Use WORK accounts ONLY for DRA staff: Kantesh = kanteshbg@draas.com, Anbu/Anbarasan = pm2.blr@draas.com.
- Remove personal gmail access if previously granted (removed kanteshbgme@gmail.com from the old doc).
- Re-send WhatsApp with doc link after updates; use whatsapp_link tool (never hand-encode). Kantesh +91 95918 01389, Anbu +91 81500 29900.
