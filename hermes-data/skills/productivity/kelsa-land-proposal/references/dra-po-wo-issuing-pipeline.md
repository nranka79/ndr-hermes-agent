# DRA PO-WO Issuing Pipeline — Reference

## Overview
- **Pipeline name:** DRA PO-WO Issuing (PO-WO)
- **Pipeline ID:** 537
- **Account:** DRA (ID: 5)
- **Lead URL pattern:** `https://kelsa.io/537/leads?current_item_id=<lead_id>`
- **Total leads:** ~1,330 records

## Stages (6)
| # | Stage | Status | Identifier |
|---|-------|--------|------------|
| 1 | PO-WO Created | Active | st_po_wo_created |
| 2 | HoD Approved | Active | st_hod_approved |
| 3 | Chairman Approved | Active | st_chairman_approved |
| 4 | Signed & Issued | Active | st_signed___paid |
| 5 | Cancelled | Retired | st_cancelled |
| 6 | Rejected | Retired | st_rejected |

## Linked Master Pipelines
| Pipeline | ID | Fields | Purpose |
|----------|----|--------|---------|
| DRA Companies Master | 4475 | cf_company_name1 | Company placing the order |
| DRA Vendor Shortlisting | 531 | cf_vendor1, cf_approved_vendor | Vendor being issued the PO |
| DRA Project Budgets | 2033 | cf_company_name_budget, cf_project_new1, cf_category, cf_budget_head, cf_project_new, cf_balance_budget | Budget allocation & balance tracking |

## Key Field Identifiers

### PO/WO Created stage — required fields
| Field | Type | Notes |
|-------|------|-------|
| `cf_po_type` | dropdown (2) | "One Time PO" or similar |
| `cf_company_name1` | master → Companies | Lead ID from Companies Master pipeline (4475) — pass as `{"id": lead_id}` |
| `cf_vendor1` | master → Vendors | Lead ID from Vendor Shortlisting pipeline (531) — pass as `{"id": lead_id}` |
| `cf_why_vendor` | text | Justification for selecting this vendor |
| `cf_jobs` | dropdown (309 options) | E.g. "supply of Container office" |
| `cf_special_instruction___notes` | text | Full PO/WO instructions, clauses, scope — use this field for the detailed terms |
| `cf_due_date` | date | YYYY-MM-DD format |
| `cf_total_value_of_order__without_tax_` | number | In INR, no commas or symbols |
| `cf_total_tax` | number | Tax amount in INR (e.g. 18% GST) |
| `cf_advance_to_be_paid` | number | Advance payment amount |
| `cf_narration` | text | Brief description of the PO/WO |
| `cf_nature_of_order` | dropdown (4) | "Turnkey", "Itemized", etc. |

### PO/WO Created stage — optional but useful fields
| Field | Type | Notes |
|-------|------|-------|
| `cf_company_name_budget` | master → Budgets | Lead ID from Project Budgets pipeline (2033) |
| `cf_project_new1` | text | Project name (e.g. "Ranka Udaya") |
| `cf_category` | text | E.g. "Marketing", "Infrastructure", "Admin & Support" |
| `cf_budget_head` | text | E.g. "Execution", "Creative", "Maintenance" |
| `cf_project_new` | master → Budgets | Budget Sub Head — pass the budget lead ID, NOT a text value |
| `cf_quote_provided` | attachment | Upload vendor's quote PDF via S3 flow |
| `cf_issued_po_wo` | attachment | The final issued PO/WO document (usually .xlsx or .pdf) |
| `cf_status` | dropdown (2) | "Active" typically |
| `cf_cost_justification` | text | Optional cost comparison notes |
| `cf_alternate_quotes` | text | Details of alternate quotes received |
| `cf_key_quality_parameters` | text | Quality standards the vendor must meet |
| `cf_penalties` | text | Delay penalties and liquidated damages terms |

### Financial fields
| Field | Type | Notes |
|-------|------|-------|
| `cf_total_value_of_order__without_tax_` | number | Base amount in INR |
| `cf_total_tax` | number | Tax in INR |
| `cf_total_amount` | number | Auto-calculated? (base + tax) — may be auto-summed |
| `cf_advance_to_be_paid` | number | Advance amount in INR |
| `cf_invoiced_amount1` | number | Linked to Invoice Processing pipeline |
| `cf_yet_to_be_invoice_amount` | number | Remaining to invoice |
| `cf_amount_paid` | number | Already paid |
| `cf_mode_of_payment` | dropdown (5) | NEFT/RTGS, Cheque, etc. |

### Exit / Termination details
| Field | Type | Notes |
|-------|------|-------|
| `cf_exit___termination_details` | text | Exit clauses, termination conditions |

## Prerequisites by Stage

### PO-WO Created
- data_entry: Collect required information
  - Required: cf_po_type, cf_company_name1, cf_vendor1, cf_why_vendor, cf_jobs, cf_special_instruction___notes, cf_due_date, cf_total_value_of_order__without_tax_, cf_total_tax, cf_advance_to_be_paid, cf_narration, cf_nature_of_order
  - Optional: cf_company_name_budget, cf_project_new1, cf_category, cf_budget_head, cf_project_new, cf_balance_budget, cf_cost_justification, cf_quote_provided, cf_issued_po_wo, cf_alternate_quotes_attachments, cf_item_details

### HoD Approved
- review: Approve PO by HoD?
  - Required: cf_issued_po_wo, cf_vendor1, cf_company_name1, cf_company_name_budget, cf_project_new1, cf_category, cf_budget_head, cf_project_new, cf_balance_budget, cf_advance_to_be_paid, cf_total_amount

### Chairman Approved
- review: Approve PO-WO
  - Readonly review of: cf_ponumber, cf_issued_po_wo, cf_advance_to_be_paid, cf_nature_of_order, cf_type_of_job, cf_jobs, cf_due_date, cf_why_vendor, cf_quote_provided, cf_cost_justification, cf_alternate_quotes, cf_special_instruction___notes

### Signed & Issued
- data_entry: Issue PO
  - Required: cf_issued_po_wo, cf_ponumber, cf_nature_of_order
  - Optional: cf_jobs, cf_special_instruction___notes

## Automation Rules
- **PO-WO Created:** Auto-assigns to created_by, auto-followers added (Anbarasan, Nishant Ranka, Roshini Ranka)
- **HoD Approved:** Auto-assigns to user 2270 (Bhagya)
- **Chairman Approved:** Auto-followers added. If budget related to DRA Realty, auto-assigns to Eshwari (702). If advance > 0, auto-creates a record in another pipeline
- **Signed & Issued:** Auto-assigns back to created_by

## Common Patterns

### Creating a PO/WO from a vendor quote
1. **Check vendor exists** in Vendor Shortlisting (531) — if not, create first
2. **Update vendor contact** if the quote has different contact info
3. **Upload quote PDF** via S3 flow → register_upload → get attachment value
4. **Create lead** in pipeline 537 with field_values mapping:
   ```python
   kelsa_call_tool(tool_name="create_lead", arguments={
       "pipeline_id": 537,
       "name": "Vendor Name - Description - Project",
       "field_values": {
           "cf_company_name1": {"id": company_lead_id},
           "cf_vendor1": {"id": vendor_lead_id},
           "cf_nature_of_order": "Turnkey",
           "cf_po_type": "One Time PO",
           "cf_jobs": "supply of Container office",
           "cf_total_value_of_order__without_tax_": 442000,
           "cf_total_tax": 79560,
           "cf_advance_to_be_paid": 221000,
           "cf_due_date": "2026-08-10",
           "cf_why_vendor": "Reason for selecting this vendor",
           "cf_special_instruction___notes": "Full PO clauses...",
           "cf_narration": "Brief description",
           "cf_quote_provided": {"url": "...", "upload_id": 123, "name": "quote.pdf"},
           "cf_status": "Active",
           # Budget mapping (optional):
           "cf_company_name_budget": {"id": budget_lead_id},
           "cf_project_new1": "Ranka Udaya",
           "cf_category": "Marketing",
           "cf_budget_head": "Execution",
           "cf_project_new": {"id": budget_lead_id},  # master field, pass ID not text
       }
   })
   ```
5. **Add comprehensive note** with detailed scope, quality parameters, and clauses — @mention the assignee using `@[Name](id)` format
6. **Change assignee** to the person responsible via `update_lead(lead_id, assignee_id="682")`

### Adding notes with @mentions
Use `list_users(pipeline_id=537)` to get user IDs and mention format:
```python
kelsa_call_tool(tool_name="add_note", arguments={
    "lead_id": lead_id,
    "text": "@[Anbarasan](682) — URGENT: Please review the PO terms..."
})
```

### Updating Special Instructions after creation
The `cf_special_instruction___notes` field can be updated after creation:
```python
kelsa_call_tool(tool_name="update_lead", arguments={
    "lead_id": lead_id,
    "field_values": {
        "cf_special_instruction___notes": "Updated instructions text..."
    }
})
```

## Known Pitfalls

1. **Budget Sub Head is a master field, not text.** `cf_project_new` maps to DRA Project Budgets pipeline — you must pass the budget lead ID (`{"id": budget_lead_id}`), not a text string. Passing text like "Miscellaneous" causes a validation failure: "Invalid master value for Budget Sub Head".
2. **Budget must exist before referencing.** If you create a PO/WO with a budget reference that doesn't exist or has insufficient balance, the draft will fail. Search the Project Budgets pipeline first to find the right budget item.
3. **cf_special_instruction___notes is required at PO-WO Created stage.** Don't leave it as a placeholder — the full PO terms belong here. Update it via `update_lead` if you need to add more after creation.
4. **Don't create a PO/WO without a vendor.** The vendor must first exist in Vendor Shortlisting (531). `cf_vendor1` accepts `{"id": vendor_lead_id}` — the lead ID from the vendor pipeline, not the company name string.
5. **Draft processing is async.** After `create_lead` or `update_lead`, always poll with `get_draft_status` to confirm it completed or catch validation errors.
6. **S3 upload URL is single-use and expires quickly.** Upload immediately after `get_upload_url`. Don't batch multiple get_upload_url calls before uploading.
