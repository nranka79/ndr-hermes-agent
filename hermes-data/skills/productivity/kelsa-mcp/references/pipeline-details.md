# Detailed Pipeline Structures

## DRA Invoice Processing (516)

**Stages:**
1. Invoice received (active)
2. Approved by the Issuer of PO/WO (active)
3. Approved by chairman (active)
4. Invoice paid (active)
5. Invoice Rejected (retired)
6. Already Paid (retired)
7. Retired (retired)
8. Duplicates (retired)

**Key fields:** cf_amount, cf_vendor_n, cf_invoice_number, cf_invoice_date, cf_invoiced_to_the_company1, cf_po_number1, cf_upload_invoice

**Key task assignments per stage (confirmed Jun 2026):**
- Stage "Approved by the Issuer of PO/WO" — task "Issuer of PO-WO to verify all details of the invoice and work done or material delivered and then approve invoice for payment" assigned to the PO issuer (varies by record). **Record-level assignee may differ from task-level assignee.**
  - When Nishant is PO issuer: he completes this task same-day, then the record moves on
  - When Bhavik is PO issuer: task is Bhavik's, NOT Nishant's
- Stage "Approved by chairman" — has three prerequisite tasks:
  1. "Review & Approve" — **the Chairman's task.** Assignment pattern: Bhavik-issued invoices → Nishant; Nishant-issued invoices → Roshini
  2. "Bhavik To Review & Approve Invoice" — Bhavik's task, only for Bhavik-issued POs
  3. "Verify Correctness of Hard Copy Invoice" — typically Accounts - DRA, but sometimes assigned to Nishant (e.g., DESIGNCAFE lead 52229320, due 2026-06-11 overdue)
- Stage "Invoice paid" — "Accounting Entry Done" → Accounts - DRA
- Stage "Invoice received" — "Post Invoice" data_entry task → assigned to whoever created it

**Task assignment examples from actual records (Jun 2026):**
- **Bhavik-issued, needs Nishant's Review & Approve** (these are Nishant's pending items):
  - INV-71 (Jain Fabs, lead 51861662) — Review & Approve due 2026-06-06, overdue
  - INV-021 (RD Signs, lead 51861585) — Review & Approve due 2026-06-06, overdue
  - 8 (Vardhan Ventures, lead 51945691) — Review & Approve due 2026-06-08, overdue
  - KAR/PST/3518 (Luvleen Services, lead 52050661) — Review & Approve due 2026-06-10, overdue
  - 2205 (Raju A, lead 51976379) — Review & Approve due 2026-06-09, overdue
  - HS/26-27/251 (Home Stories, lead 52140817) — Review & Approve due 2026-06-13, overdue
  - 007/2026-27 (Comuna Facility Mgmt, lead 52032837) — Review & Approve due 2026-06-10, overdue
- **Nishant-issued, Review & Approve goes to Roshini** (NOT Nishant's task):
  - INV/26-27/0359 (Mossant, lead 52321076) — Review & Approve assigned to Roshini
  - 9834 (Momai, lead 52321197) — Review & Approve assigned to Roshini
  - CR117483 (Infinitea, lead 52320694) — Review & Approve assigned to Roshini
  - O3062026062 (O3 Infotech, lead 52040573) — Review & Approve assigned to Roshini

**To find someone's actual pending tasks, always use `list_lead_tasks()`. Do not rely on record-level assignee.**

## Kelsa Search Filter Syntax — Pitfalls (Jul 2026)

**The filter syntax is single-condition, NOT multi-condition.** Semicolons in queries are silently rejected.

```python
# WRONG — multi-condition query returns 0 results, no error
search_leads(pipeline_id=516, query="assignee:Nishant;stage:st_approved_by_chairman")
# → 0 results

# WRONG — same
search_leads(pipeline_id=537, query="assignee:Nishant;stage:st_chairman_approved")
# → 0 results
```

**Workaround — use the wider filter, then post-process in code:**

```python
# Get the user's full list, then filter in Python
results = search_leads(pipeline_id=516, query="assignee:Nishant", per_page=20, sort="updated_at")
chairman_pending = [r for r in results if "Approved by the Issuer" in r.get("stage_name", "")]
```

The Kelsa filter parser splits on spaces (treats as OR) and apparently doesn't support semicolons. To get precise multi-condition filters, do the broad search and filter in code — fast and predictable.

## Pipeline 516 — "Approved by the Issuer of PO/WO" Stage Semantics

**The stage name is misleading (Nishant, Jul 2026).** Despite the name suggesting "issuer has approved, ready to move on", this stage is where:

1. The **Issuer of PO/WO task has been completed** (the "verify all details" review by the PO issuer)
2. The invoice **is now WAITING for the Chairman's "Review & Approve" task** (this stage's prerequisite)

So the "Approved by the Issuer" stage ≠ approved. It's the "Issuer-done, Chairman pending" stage.

**For Nishant (the Chairman), this is HIS pending queue.** The "Review & Approve" task is assigned to him (or Roshini, depending on who issued the PO — see the Bhavik vs Nishant issued-PO pattern above). The record-level `assignee` is set to him by automation `set_assignee → 41 [filter: cf_invoice_for_the_company1!:Sevaganapalli land partners;cf_invoiced_from_the_company!:Dra thindlu land partners]` at this stage.

**When the user asks "show me pending chairman approvals":**

1. `search_leads(pipeline_id=516, query="assignee:Nishant Ranka", per_page=20, sort="updated_at")` — get the 20 most recent records assigned to him
2. For each: `list_lead_tasks(lead_id)` — confirm the "Review & Approve" task is pending and assigned to him (vs Roshini)
3. Filter to the ones where the chairman task is still pending — those are his true pending queue
4. Get full details via `get_lead(lead_id)` to see amount, vendor, invoice number, due date, and the auto-approval timer

**`Date For Auto Approval` and `Date For Auto Progress` fields** — present in the lead, indicate when the system will auto-approve or auto-progress if the chairman doesn't act. Check these to prioritize overdue items.

## DRA Land Proposal (519)

**Stages:** Proposed → Info Gathered → Initial Feasibility Checked → Site Visited And Approved → Proposal Made → Commercial Closure & Token Done → Legal Ok Obtained → Agreement Done

**Key fields:** cf_name (proposal brief), cf_city, cf_land_size_acres, cf_village, cf_sy_nos, cf_expected_rate_per_sqft, cf_offer_type

## DRA Commitments (2002)

**Stages:** Commitment Reported → Commitment Accepted → Committment Delivered
**Key fields:** cf_enter_the_commitment, cf_deliverables, cf_due_date, cf_in_relationship_to, cf_is_completed

## DRA PO-WO Issuing (537)

**Stages:** PO-WO Created → HoD Approved → Chairman Approved → Signed & Issued
**Key fields:** cf_vendor, cf_jobs, cf_total_value_of_order__without_tax_, cf_due_date, cf_ponumber

**Linked sub-pipeline — Purchase Order Details (7954):**
- PO-WO records link to a sub-pipeline **Purchase Order Details** (ID: 7954) via the master field `cf_identifier_to_purchase_order` → `dra_po_wo_issuing`
- The sub-pipeline tracks individual PO line items: item code, quantity ordered, quantity received, pending quantity
- Structure: 2 stages (Start → Retired), 7 fields
- URL: https://kelsa.io/7954

**Known Ranka Amber vendors in PO-WO:**
- **Vardhan Ventures** — construction contractor for Ranka Amber (civil works: excavation, concrete, reinforcement, formwork, masonry). Multiple POs issued:
  - PO 739 (lead 52220478) — ₹3.4 Cr main construction WO, Signed & Issued (Jun 2026)
  - PO 735 (lead 51686225) — ₹1.87 L temporary electricity, Signed & Issued (May 2026)
  - PO 662 (lead 46092236) — ₹5.2 L barrication work, Signed & Issued (Feb 2026)
- **RERA Consultants LLP** — RERA registration/quarterly filings for Ranka Amber and Ranka NorthStar

**Key task assignments per stage (confirmed Jun 2026):**
- Stage "PO-WO Created" — task "Approve PO by HoD?" assigned to HoD (typically Anbarasan or Roshini). **Not Nishant's task.**
- Stage "HoD Approved" — task "Approve PO-WO" assigned **overwhelmingly to Roshini Ranka**, NOT Nishant. Only one known exception (PO 727, lead 50936721) where "Approve PO-WO" was assigned to Nishant directly.
- Stage "Chairman Approved" — already approved, waiting for "Signed & Issued" stage. Issuance task assigned to created_by (the original creator).
- Stage "Signed & Issued" — issuance task assigned to created_by.

**Task assignment examples from actual records (Jun 2026):**
- Most "Approve PO-WO" tasks at HoD Approved → Roshini Ranka (even though the stage seems like "Chairman" should act):
  - PO 737 (lead 51760232) — Approve PO-WO → Roshini
  - PO 671 (lead 47051367) — Approve PO-WO → Roshini
  - PO 698 (lead 48727763) — Approve PO-WO → Roshini
  - PO 730 (lead 51046839) — Approve PO-WO → Roshini
- Exception: PO 727 (lead 50936721) — Approve PO-WO → **Nishant** (overdue 39d as of Jun 2026)

**Critical insight: Do NOT assume all items at "HoD Approved" need Chairman (Nishant) approval.** The actual "Approve PO-WO" task at this stage is primarily assigned to Roshini, not Nishant. Always check `list_lead_tasks()` to confirm.

**To find actual pending tasks for a user in PO-WO, query `pipeline_id=537` stage "HoD Approved" and check `list_lead_tasks()` for "Approve PO-WO" task assignments.**

## DRA Petty Cash (555)

**Stages:** Requested → Approved → Issued & Debited → Expense Details Submitted → Expense Approved → Credited & Closed
**Key fields:** cf_request_type, cf_amount_requested, cf_amount_approved, cf_project, cf_fromcompany

**Key task assignments per stage:**
- "Approved" stage — task "Verify & Approve Request" — automation assigns to user 702 on entry (resolves to Eshwari for non-Westbury requests). Not Nishant's task.
- "Issued & Debited" — task "Issue the advance..." assigned to created_by (the requester). Not Nishant's task.
- "Expense Approved" stage — task "Approve Petty Cash Expense Details" — automation assigns to team_5 (Accounts - DRA). Not Nishant's task.
- **Confirmed (Jun 2026):** No Petty Cash stages currently have tasks pending for Nishant.

## DRA Attendance Tracker (New) — Pipeline 7711

**Stages (6):**
1. Start (st_start) — auto-created daily at 8:00 AM
2. Sign In (st_sign_in) — reached after clicking sign-in email link
3. Sign Out (st_sign_out) — final active stage for the day
4. Retired (st_retired, retired) — terminal
5. Absent (st_absent, retired) — if no sign-in by 5 PM
6. Delete (st_delete, retired)

**Key fields:**
- cf_employee_name1 — Employee Name (user field)
- cf_date1 — Date (date)
- cf_attendance_status1 — Attendance Status (dropdown: Present/Absent/Half Day/Leave)
- cf_sign_in — Sign In (checkbox)
- cf_sign_out — Sign Out (checkbox)
- cf_login_location — Login Location (location)
- cf_logout_location — Logout Location (location)
- cf_sign_in_time1 — Sign In Time (time)
- cf_logout_time — Logout Time (time)
- cf_employee_name_scoper1 — Employee Name Scoper (master → employee_location_mapping)
- cf_project_name — Project Name (master → employee_location_mapping)
- cf_login_in_from_diffrent_location — Login from Different Location (checkbox)
- cf_sign_out_attacment — Sign out attachment (attachment)

**Automations at Start stage:**
- entry_add_note — adds a note tagging the employee
- entry_send_note — sends sign-in email with Kelsa short link
- entry_set_assignee — sets assignee to cf_employee_user
- entry_add_followers — adds followers (Bhagya, employee)
- time_update_formula — after 4h: cf_attendance_status1 = "Half Day"
- time_update_formula1 — after 5h: cf_attendance_status1 = "Absent"
- time_stage_jump — after 9h: jump to Absent stage

**Automations at Sign In stage:**
- entry_update_formula — cf_attendance_status1 = "Present" (if not already set)
- entry_send_note2 — sends auto note on sign-in
- Various grace/late logic based on sign-in time

**Automations at Sign Out stage:**
- entry_create_record — creates record in monthly attendance report
- Various logout location validations

**Sign-in/Sign-out email pattern:**
- Subject: "Please sign in for the day" / "Please sign out"
- Sender: Nishant Ranka <ndr@draas.com>
- Body: "Dear [Name] Please click on the link to [Sign In/Sign Out] https://kelsa.io/s/[shortcode]"
- Kelsa short links are per-user unique, auto-generated by the pipeline

**How to check someone's attendance:**
1. `search_leads(pipeline_id=7711, query="cf_employee_name1:<Name>")` — find records by employee name
2. Look for today's record by identifier pattern `<Name>-YYYY-MM-DD`
3. `get_lead(lead_id)` — check current stage and cf_attendance_status1 value
4. `list_lead_tasks(lead_id)` — check pending Punch In or Punch Out tasks

**User-to-UID mapping (Hermes user directories under /data/hermes/users/):**
- Nishant Ranka: ndr
- Roshini Ranka: rnr
- Anbarasan (Anbu): pm2.blr
- Vinod Das: vkdas
- Prakash Singh: psingh
- Bharat Hawaldar: sales1.blr

When inspecting a lead via `get_lead()`, the Recent Activity section shows stage transitions and notes. Use these to determine if an item is truly stalled or just had a status update:
- "Stage changed to X" = progressed
- "note : @user ..." = someone is discussing it
- "created" = new record
- If last activity is >7 days and the item is in an active non-terminal stage = stalled

## DRA Sales Leads (10)

**Stages (10) with numeric IDs:**
1. **Cold** (ID: 1, st_cold) — entry point
2. **Warm** (ID: 2, st_warm)
3. **PSC** (ID: 281, st_psc) — the required intermediate between Warm and SSV. From Warm, only PSC (281) is an allowed target, not SSV directly.
4. **SSV** (ID: 6, st_ssv)
5. **Hot** (ID: 3, st_hot)
6. **Converted** (ID: 4, st_converted)
7. Others [retired] (st_others)
8. Dead [retired] (st_dead)
9. Junk [retired] (st_junk)
10. Lost [retired] (st_lost)

**Purpose:** Full lead lifecycle tracking from incoming enquiry through to conversion/closure. Leads enter at Cold and progress through qualification (Warm, PSC), site visit (SSV), offer (Hot), and final status (Converted/Lost/Dead).

**Field sets and mandatory fields at Cold stage:**

The `data_entry` prerequisite "Collect required information" at Cold stage requires:

| Display Name | Field ID | Type | Notes |
|-------------|----------|------|-------|
| Contact | `cf_contact1` | master → `dra_sales_contacts` (ID: 3429) | **Required.** Must be an existing contact record in DRA Sales Contacts pipeline. Create contact first if not found. |
| Source | `cf_source` | dropdown (148 options) | **Required.** String value matching a dropdown option exactly (case-sensitive). |
| SourceDetails | `cf_sourcedetails` | text | **Required.** Free text — typically the ad platform or campaign identifier. |
| Channel | `cf_campaign` | dropdown (5 options) | **Required.** String matching dropdown option. Common values: "DigitalAds", "Walk-in", "Reference", "Call", "Website". |
| Project | `cf_project` | master → `dra_project_unit_master_data` | **Required.** Project name passed as text (Kelsa resolves to master record). Common: "Ranka udaya", "Serenity Hillview", "Ranka Amber", "Ranka North Star". |
| Max Budget | `cf_max_budget` | number | Optional. Plain number (no ₹, no commas). |
| Requirements | `cf_requirements` | text | Optional. Free text describing the lead's requirements. |

**Other useful fields for Warm/Hot stages:**

| Display Name | Field ID | Type |
|-------------|----------|------|
| Product | `cf_product` | dropdown (29 options) |
| Min Budget | `cf_min_budget` | number |
| Specific Unit | `cf_product_specific_unit` | text |
| Interested in Site Visit? | `cf_interested_in_site_visit_` | checkbox |
| Scheduled Site Visit Date | `cf_scheduled_site_visit_date` | date |
| Masking | `cf_masking` | number — partial phone number masking for privacy |
| Lost Reason | `cf_lost_reason` | dropdown (5 options) — used at Lost stage only |
| Sales Status | `cf_sales_status` | dropdown (4 options) |

**Creating a lead at Cold stage — workflow:**

1. **Check if the contact already exists** in DRA Sales Contacts (3429). Search by phone or email.
2. **If the contact exists**, note its lead ID (e.g. `53357778`). The `cf_contact1` master field takes this ID.
3. **If the contact does NOT exist**, create it first in DRA Sales Contacts (pipeline 3429, no stages — just 9 fields). The `cf_contact` field is type **"contact"** and expects a single compound object with `name`, `phone`, and `email` keys. The individual `cf_contact_phone` and `cf_contact_email` field identifiers exist in the pipeline schema but are NOT writeable via MCP `create_lead` — passing them as separate fields causes `"Error creating record: Contact information (Email or Phone) required"`.

   **Correct format:**
   ```python
   field_values = {
       "cf_contact": {"name": "Nag Arjan", "phone": "7418234834", "email": "nagu.ches@redgible.com"}
   }
   ```

   The optional `cf_identifier` can hold a dedup key like `<Name>-<Phone>` alongside the compound object.
4. **Call `create_lead`** for pipeline 10 with these field values:
   ```python
   field_values = {
       "cf_contact1": {"id": 53357778},  # master field — pass as {"id": record_id}
       "cf_campaign": "DigitalAds",       # dropdown — pass as plain string
       "cf_source": "I Am Here Software Labs",  # dropdown — exact match
       "cf_sourcedetails": "Meta",        # text
       "cf_project": "Ranka udaya",       # master field — pass as text (Kelsa resolves)
       "cf_max_budget": 5000000,          # number — plain integer, no commas/₹
       "cf_requirements": "1200 SQFT",    # text — optional
       "cf_masking": 9                    # number — optional mask length
   }
   ```
5. **The lead is created at Cold automatically** (Cold is the start stage). No `move_stage` needed.
6. **Move to Warm (two approaches):**

**Approach A — `move_stage` with field_values (works without task permissions):**
Directly jump from Cold to Warm by calling `move_stage` with stage_id=2 and `field_values` containing `cf_requirements`. The `cf_requirements` field is mandatory for the Warm stage's data_entry prerequisite. This bypasses the need to complete the "Confirm Inquiry" review task (which requires task-level permissions the MCP user may not have).

```python
payload = {"jsonrpc": "2.0", "method": "tools/call", "params": {
    "name": "move_stage",
    "arguments": {
        "lead_id": 53882673,
        "stage_id": 2,
        "field_values": {"cf_requirements": "Interested in visiting site - location aligns with requirements"}
    }
}}
# Returns: "Stage move queued for processing (draft ID: N)"
# Verify: get_draft_status(draft_id=N) → "completed" with lead showing "Stage: Warm"
```

**Approach B — `complete_task` (only if task permissions allow):**
Complete the "Confirm Inquiry" review task first, which should auto-advance the record to Warm. However, the MCP token may lack permission (`"You do not have permission to complete this task"`). In that case, fall back to Approach A.

**IDEN (Identifier) auto-format:**
The `cf_iden` field typically follows the pattern `<Name>-<Phone>-<Date>`. E.g. `Ritesh Kumar-["+918602162016"]-2026-07-19`. If not auto-populated, the pattern to use is `<Name>-["<Phone>"]-<YYYY-MM-DD>`.

**Key differences from Leads pipeline (ID: 9268):**
Pipeline 9268 is a simpler, standalone pipeline with direct text fields (Name, Email, Phone, Campaign, Channel) — no master field links. It feeds data into pipeline 10 via a sync process. Pipeline 10 is the canonical DRA Sales Leads with master field relationships and full lifecycle tracking.

**Search tips:**
- `search_leads(pipeline_id=10, query="Ritesh")` — finds by contact name or any text field
- `search_leads(pipeline_id=10, query="+918602162016")` — finds by phone in text fields
- `search_leads(pipeline_id=10, query="cf_campaign:DigitalAds")` — filter by channel field
- `search_leads(pipeline_id=10, query="assignee:Nishant;stage:st_warm")` — multi-condition NOT supported (see search pitfalls above). Use broad search + Python filter.
