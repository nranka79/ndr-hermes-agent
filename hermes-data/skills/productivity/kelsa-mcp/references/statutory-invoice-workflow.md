# Statutory/Utility Invoice Posting — DRA Invoice Processing (Pipeline 516)

**Verified Jun 2026** — BESCOM Power Sanction cum Demand Challan as worked example.

## Common Statutory Invoices in DRA

| Type | Issuer | Example |
|------|--------|---------|
| BESCOM Demand Challan | BESCOM | Power sanction letter with payment demand |
| BWSSB NOC Fee | BWSSB | Water/sewerage connection fees |
| BBMP CC/OC Fee | BBMP | Building/occupancy certificate fees |
| RERA Registration Fee | RERA | Project registration charges |

## Workflow

### Step 1 — Identify document type

Statutory letters are often **hybrid** — they combine a sanction/approval AND a payment demand. Use vision/OCR to confirm:

- Look for "You are requested to pay", "DD payable at", "within X days"
- Extract the **total amount demanded** (the payment section, not the sanction section)
- Confirm with user if ambiguous

**BESCOM example:** Page 1 = power sanction (380.87 KW), Page 2 = demand for ₹4,68,255 with full breakdown plus Page 6 = deposit amount schedule across 15 accounts totalling ₹3,14,120 MMD.

**BESCOM payment breakdown:**
| Item | Amount |
|---|---|
| MMD (15 accounts) | ₹3,14,120 |
| Transformer Testing | ₹1,000 |
| RMU Pre-commissioning Test | ₹4,080 |
| 5% Supervisory Charges | ₹1,49,055 |
| **Total** | **₹4,68,255** |

**Payment method:** Demand Draft (DD) payable at office of O&M E6 INDRANAGAR, BESCOM
**Deadline:** 90 days from date of sanction letter

**Reference details to extract:**
- Sanction No (appears on the letter head)
- Application ID
- Account ID
- Sanction date
- Consumer name (the company entity)

### Step 2 — File in Drive

Rename per convention reflecting the confirmed type. **Must include survey numbers** if project-related, and reflect the specific document subtype (e.g., "DemandChallan" not just "SanctionLetter").

**Pattern:** `YYYYMMDD_Project_Company_DocumentType_Details.pdf`
**Example:** `20260618_RankaIris_DRA Developers_BESCOM_PowerSanction_DemandChallan.pdf`

File under the project's **Sanction Documents** folder (e.g., RankaIris → Sanction Documents).

### Step 3 — Forward payment email

Forward to **Eshwari Chamundeshwari** (echamundeshwari@draas.com) with exact amount breakdown and payment method. CC **Bhavik Ranka** (bhavik@draas.com) and the **original sender**. Keep on **same thread** (use `threadId` in the Gmail API send call). Attach the BESCOM PDF to the forwarded email.

**Email body should include:**
- Total amount (prominently)
- Itemised breakdown
- Payment method (DD/Bank transfer/etc.)
- Reference numbers
- Due date

### Step 4 — Find the right budget item (preferred) OR confirm with user

**Preferred approach — search the budget master first.**

Before presenting options to the user, search the `dra_project_budgets` pipeline (ID: 2033) for an existing budget item that matches:

```
search_leads(pipeline_id: 2033, query: "<project> <category> <keyword>")
```

Example for BESCOM power sanction:
```
search_leads(pipeline_id: 2033, query: "iris Approvals BESCOM")
```

This can find a perfect match like `Ranka Iris-Designing & Approvals-Approvals-BESCOM Approvals for HT & LT - Charge / Connection` (record ID 20764187, budget ₹17,50,000). Pass the budget record ID to `cf_projects_budget` and the other budget fields cascade.

**Fallback — present options to user only if no budget item matches exactly.**

The cascade to present:

1. **Projects(Budget)** — e.g., "iris", "Ranka amber", "Riverstone farms", "General overhead"
2. **Category** — e.g., "Designing & Approvals", "execution", "Misc / Probables / Contingency"
3. **Budget Head** — depends on Category selection
4. **Budget Sub Head** — depends on Budget Head selection

**Confirmed path for utility/statutory invoices (Jun 2026):**
| Level | Confirmed Value |
|---|---|
| PO Type | No PO |
| Projects(Budget) | Project name (e.g., iris, Ranka amber) |
| Category | Designing & Approvals |
| Budget Head | Approvals (the appropriate head for sanction/approval related charges) |
| Budget Sub Head | Ask user — options vary |

**Known Budget Heads under "Designing & Approvals" category:**
- **Drawings** → Sub Head: "Final Architectural Drawings - Detailed GFCs"
- **Consultant** → (no sub-head in examples)
- **Approvals** → Sub Head: "Modification of Plan" (and potentially others)

For a BESCOM power sanction demand, the recommended path is Category: Designing & Approvals → Budget Head: Approvals.

### Step 5 — Create Kelsa Invoice record

Use `create_lead` on pipeline 516 (Account 5). Compile all field values and present to user for confirmation before creating.

**Mandatory fields for "Post Invoice" data_entry task at "Invoice received" stage:**

| Kelsa Field | Identifier | Value (BESCOM example) |
|-------------|-----------|------------------------|
| Invoiced to the Company | `cf_invoiced_to_the_company1` | "Dra developers & projects pvt ltd." (look up actual value in pipeline fields) |
| Vendor Name | `cf_vendor_n` | "BESCOM" (or appropriate issuer) |
| PO Type | `cf_invoice_against` | "No PO" (statutory demands have no PO) |
| Invoice number | `cf_invoice_number` | Sanction reference number |
| Invoice date | `cf_invoice_date` | Date on the letter |
| Amount | `cf_amount` | Total demanded (numeric, no commas/symbols) |
| Description | `cf_description` | Brief: "BESCOM power sanction demand — 380.87 KW — Ranka Iris" |
| Copy of invoice | `cf_upload_invoice` | Drive link to the filed document (see Step 6) |
| Projects(Budget) | `cf_projects_budget` | Project name (master lookup) |
| Category | `cf_category1` | Category name (master lookup) |
| Budget Head | `cf_budget_head3` | Head name (master lookup) |
| Budget Sub Head | `cf_budget_sub_head3` | Sub head name (master lookup) |

### Step 6 — Attachment: Drive link in create_lead

`cf_upload_invoice` (Copy of invoice) is an **attachment** field. **`create_lead` accepts URL strings directly** for attachment fields — pass the Drive webViewLink as a string value:

```python
"cf_upload_invoice": "https://drive.google.com/file/d/FILE_ID/view?usp=drivesdk"
```

This places the Drive link into the Kelsa record's attachment field. No manual workaround needed — confirmed working Jun 2026 with a BESCOM demand challan.

## Precautions — `create_lead` with Master Fields

**⚠️ Silent failure risk (confirmed Jun 2026):** Passing `{"id": RECORD_ID}` for master fields (company, vendor, budget) does NOT guarantee the record will be created. The API queues the draft but may silently fail if:
- The ID doesn't match an active option in that field's dropdown/master configuration
- The budget-item path (Project → Category → Head → Sub Head) is incomplete or invalid
- The field expects a specific scoped relationship between the selected values

**Validation before calling `create_lead`:**
1. **Always search the target master pipeline first** — e.g., `search_leads(pipeline_id=4475, query="DRA Developers")` to find the company record ID. Do not hardcode IDs from previous sessions.
2. **For budget fields**, search `dra_project_budgets` (2033) for an exact budget item match that already has the correct Project+Category+Head+SubHead combination. Pass that budget record's ID to `cf_projects_budget` and let it cascade if the fields are scoped.
3. **If the `create_lead` call returns "queued" but the record never appears**, the field values are likely wrong. Do NOT re-submit identical data — adjust the values and try again.

## File Naming Convention for Statutory Documents

Documents must reflect the **confirmed document subtype**, not just the issuer name. A BESCOM letter that sanctions power AND demands payment is a **Demand Challan**, not a "SanctionLetter" — confirm with the user if ambiguous.

**Pattern:** `YYYYMMDD_Project_Company_DocumentSubtype.pdf`
- Include survey numbers if project-related land/property documents
- Include the company entity name (e.g., "DRA Developers") for company-specific invoices
- Use "DemandChallan" or "DemandNote" for payment demands, "SanctionLetter" for approvals-only

**BESCOM Demand Challan example:** `20260618_RankaIris_DRA Developers_BESCOM_PowerSanction_DemandChallan.pdf`

```python
create_lead(
    pipeline_id=516,
    field_values={
        "cf_invoiced_to_the_company1": {"id": COMPANY_ID},  # Resolve from pipeline field options
        "cf_vendor_n": {"id": VENDOR_ID},                   # Resolve from pipeline field options
        "cf_invoice_against": "No PO",
        "cf_amount": 468255,
        "cf_invoice_date": "2026-06-18",
        "cf_invoice_number": "BESCOM/NC_MCPWRSA/3658914951/18-06-2026",
        "cf_description": "BESCOM power sanction demand — 380.87 KW — Ranka Iris",
        "cf_projects_budget": {"id": BUDGET_PROJECT_ID},    # Resolve from master
        "cf_category1": {"id": CATEGORY_ID},                # Resolve from master
        "cf_budget_head3": {"id": BUDGET_HEAD_ID},          # Resolve from master
        "cf_budget_sub_head3": {"id": BUDGET_SUB_HEAD_ID},  # Resolve from master
        "cf_upload_invoice": "https://drive.google.com/file/d/FILE_ID/view"
    }
)
```

**Pitfall:** Master field values (budget lookups) need `{"id": ID}` format, not free text. The actual IDs are not exposed by the MCP `get_pipeline` or `get_lead` calls — the master IDs live in the connected Kelsa master tables. You may need to search existing records to find the correct value.

## Confirmation protocol

**Always present the full proposed field values to the user before calling `create_lead`.** The user explicitly said: "Present all the final values for all mandatory fields and I can tell you whether to go ahead."

Exception: if the user says "send it right away" or "go ahead", create the record without re-confirming.
