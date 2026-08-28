# DRA Invoice Processing Pipeline — Reference

## Overview
- **Pipeline name:** DRA Invoice Processing
- **Type:** Invoice
- **Pipeline ID:** 516
- **Account:** DRA (ID: 5)
- **Lead URL pattern:** `https://kelsa.io/516/leads?current_item_id=<lead_id>`
- **Total leads:** ~3,480 records

## Stages
| # | Stage | Status | Stage ID |
|---|-------|--------|----------|
| 1 | Invoice received | Active | st_invoice_received |
| 2 | Approved by the Issuer of PO/WO | Active | st_approved_by_the_issuer_of_po_wo |
| 3 | Approved by chairman | Active | st_approved__by_chairman |
| 4 | Invoice paid | Active | st_invoice_paid |
| 5 | Invoice Rejected | Retired | st_invoice_rejected |
| 6 | Already Paid | Retired | st_already_paid |
| 7 | Retired | Retired | st_retired |
| 8 | Duplicates | Retired | st_duplicates |

## Linked Master Pipelines
| Pipeline | ID | Field | Purpose |
|----------|----|-------|---------|
| DRA Companies Master | 4475 | cf_invoiced_to_the_company1 | Company being invoiced (e.g. DRA Realty Pvt Ltd) |
| DRA Vendor Shortlisting | 531 | cf_vendor_n | Vendor/supplier (must exist before creating invoice) |
| DRA PO-WO Issuing | 537 | cf_po_number1 | Purchase Order / Work Order reference |
| DRA Project Budgets | - | cf_projects_budget, cf_category1, etc. | Budget allocation fields |

## Key Field Identifiers

### Required (Invoice received stage)
- `cf_description` (text) — description of the invoice
- `cf_invoiced_to_the_company1` (master → Companies) — company record
- `cf_vendor_n` (master → Vendors) — vendor record
- `cf_invoice_number` (text) — invoice number
- `cf_invoice_date` (date) — invoice date (YYYY-MM-DD)
- `cf_amount` (number) — invoice amount in INR (no commas/symbols)
- `cf_upload_invoice` (attachment) — scanned invoice image

### Optional (recommended for reimbursement cases)
- `cf_narration` (text) — free-form notes about payment/processing
- `cf_description_final` (text) — final description after review
- `cf_payment_mode` (dropdown) — Credit Card, Cheque, NEFT/RTGS, Cash, etc.
- `cf_payment_done_by` (text) — who made the payment
- `cf_payment_date` (date) — when it was paid
- `cf_total_amount_paid` (number) — amount paid (may differ from invoice)

### Acceptance Details — Field Set
- `cf_upload_prove_of_completion_of_work` (Proof of completion) — attachment, **single-file or URL link**. Accepts plain `{"url": "https://...", "name": "label"}` — no upload_id needed for Drive links.
- `cf_proof_of_quality` (Proof of quality) — attachment, **multi-file field**. Pass an array of upload/URL objects to attach multiple photos or documents.
- `cf_notes` (text) — approval notes
- `cf_budget_head_number` (text) — budget reference number
- `cf_amount_accepted` (number) — revised accepted amount (only set when different from invoice amount; setting equal to cf_amount causes validation failure)
- `cf_revised_accepted_amount_reason` (text) — reason for revised amount

### Payment Details — Field Set
- `cf_payment_date` (date) — date of payment
- `cf_payment_mode` (dropdown — options: Credit Card, Cheque, Demand Draft, NEFT/RTGS, Cash, UPI)
- `cf_payment_done_by` (text) — who made the payment
- `cf_payment_date` (date)
- `cf_payment_mode` (dropdown — options: Credit Card, Cheque, Demand Draft, NEFT/RTGS, Cash, UPI, etc.)
- `cf_payment_done_by` (text)
- `cf_payment_details` (attachment) — cancelled cheque / payment receipt
- `cf_total_amount_paid` (number)
- `cf_net_payable_amount1` (number)

## Known Company Lead IDs (DRA Companies Master - 4475)
- DRA Realty Pvt Ltd → 2562312

## Common Scenarios

### 1. Fuel/Petrol expense — already paid on NDR's Kotak CC
1. Search/create vendor in DRA Vendor Shortlisting (531)
2. Upload invoice image via S3 flow
3. Create invoice with description, company=DRA Realty, vendor, amount
4. Add note: "ALREADY PAID on NDR Kotak Credit Card..."
5. Update narration with payment details

### 2. Vendor invoice — needs approval
1. Ensure vendor exists in Shortlisting
2. Upload invoice + PO/WO attachment
3. Create invoice record — automation assigns to PO issuer
4. Follow standard approval flow through the pipeline stages

## Automation Rules
- Records invoiced to "DRA Realty Pvt Ltd" auto-assigned to user ID 11652
- Records invoiced to "ahfl" auto-assigned to created_by
- Records invoiced to "Dra developers & projects pvt ltd" auto-assigned to user 9153
- Followers auto-added: Nishant Ranka, Bhagya, Eshwari, Roshini Ranka, Bharat H, Engineering team
- Entry to "Approved by chairman" triggers timestamp + create_record automations

## S3 Upload Flow (Same as Land Proposals)
```
get_upload_url(pipeline_id=516, file_name, content_type)
  → returns S3 endpoint + form fields + file_url
  → POST file bytes as multipart/form-data to S3
  → register_upload(pipeline_id=516, file_url, file_name)
  → returns attachment value {url, upload_id, size, name}
  → use in cf_upload_invoice field value
```
