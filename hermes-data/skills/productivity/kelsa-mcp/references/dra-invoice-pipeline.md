# DRA Invoice Processing Pipeline (ID 516)

DRAAS invoice approval workflow. 3,495 records total. 342 in the chairman-approval stage (66 with arrival dates). (Verified 2026-07-31.)

## Stage flow (in order)

1. **Invoice received** (`st_invoice_received`) — entry prereq: `Post Invoice` (data_entry). Entry automations auto-assign per company (e.g. `cf_invoiced_to_the_company1:ahfl` → creator; DRA Developers → user 9153; default → user 162).
2. **Approved by the Issuer of PO/WO** (`st_approved_by_the_issuer_of_po_wo`) — review prereq: issuer verifies invoice/work done. Entry automation `set_timestamp` → **`cf_arrival_for_approval`** ("Received for Approval on") — this field is set when the record ENTERS this stage, so it doubles as a "posted for approval" recency proxy.
3. **Approved  by chairman** (`st_approved__by_chairman`) — note the DOUBLE SPACE in the real name. THREE prereqs:
   - `review: Review & Approve` (the chairman's task — Nishant)
   - `data_entry: Verify Correctness of Hard Copy Invoice` (accounts; fields: format correct, previous invoices/debits checked, TDS, outstanding debits)
   - `review: Bhavik To Review & Approve Invoice` (Bhavik Ranka)
   → A record can sit here with the chairman's approval ALREADY completed, blocked on Bhavik's review or accounts verification. Always check Outstanding Prerequisites + Recent Activity before reporting "awaiting your approval".
4. **Invoice paid** (`st_invoice_paid`) — prereq: `Accounting Entry Done` (`cf_accouting_entry_done`, `cf_narration`).

Retired: Invoice Rejected, Already Paid, Retired, Duplicates.

## Auto-approval mechanism (chairman stage)

- `cf_arrival_for_approval` — date received for approval
- `cf_date_for_auto_approval` — datetime, ~2 days after arrival at 09:00 (e.g. arrival 2026-06-23 → auto 2026-06-25T09:00)
- `cf_date_for_auto_progress` + `cf_auto_progress1` (checkbox) — auto-progress mechanism

## Key field identifiers

| Field | Identifier |
|---|---|
| Amount | `cf_amount` |
| Vendor | `cf_vendor_n` (master → dra_vendor_shortlisting) |
| Invoice no. / date | `cf_invoice_number` / `cf_invoice_date` |
| Invoice copy | `cf_upload_invoice` (attachment) |
| PO/WO attachment | `cf_attachment_of_po_wo` |
| PO no. / PO type | `cf_po_number1` (master → dra_po_wo_issuing) / `cf_invoice_against` (dropdown: One Time PO / Recurring PO / No PO) |
| Invoiced-to company | `cf_invoiced_to_the_company1` (master → dra_companies_master); values seen: `Dra realty pvt ltd.`, `Dra developers & projects pvt ltd.`, `Dra projects pvt ltd.`, `Dra thindlu land partners`, `Sevaganapalli land partners`, `Terra greens llp`, `Westbury hospitality pvt ltd`, `ahfl` |
| Budget linkage | `cf_projects_budget`, `cf_category1`, `cf_budget_head3`, `cf_budget_sub_head3` (masters → dra_project_budgets) |
| Received for approval | `cf_arrival_for_approval` |
| Revised amount | `cf_amount_accepted`, `cf_revised_accepted_amount_reason` |
| TDS / net payable | `cf_tds_deduction`, `cf_net_payable_amount` |
| Payment | `cf_payment_mode`, `cf_payment_date`, `cf_total_amount_paid` |

## Useful searches (verified 2026-07-31)

- Chairman queue: `search_leads(pipeline_id=516, query="stage:Approved  by chairman", per_page=50)` → 342 results
- With arrival date: `query="stage:Approved  by chairman;cf_arrival_for_approval?"` → 66 results
- Note: `sort: cf_arrival_for_approval` did NOT reorder results (came back in creation order) — use `get_lead` on the newest lead IDs to compare arrival dates.
- Recent across all stages: `search_leads(pipeline_id=516, sort="created", order="desc", per_page=25)` — new invoices sit in stages 1–2 before reaching the chairman.
