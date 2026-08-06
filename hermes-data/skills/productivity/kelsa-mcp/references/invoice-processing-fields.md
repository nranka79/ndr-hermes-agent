# Invoice Processing Pipeline 516 — Field Reference

Confirmed from `get_pipeline(pipeline_id=516)` on Jun 18, 2026.

## Key Attachment Fields

| Display Name | Identifier | Type | Notes |
|-------------|-----------|------|-------|
| Copy of invoice | `cf_upload_invoice` | attachment | The invoice document. Only settable at creation via `data_entry: Post Invoice` task. |
| Attachment of PO/WO | `cf_attachment_of_po_wo` | attachment | Reference PO/WO document. Same update limitation. |
| Proof of completion | `cf_upload_prove_of_completion_of_work` | attachment | Work completion evidence. |
| Proof of quality | `cf_proof_of_quality` | attachment | Quality evidence — can hold multiple Drive links. |
| Copy of Verified Invoice | `cf_copy_of_verified_invoice` | attachment | Uploaded by Accounts after verification. |

## Key Task IDs & Field Sets

### Stage: Invoice received
- **Task:** Post Invoice (data_entry)
- **Updatable fields via complete_task:** PO Type, Invoiced to the Company, Vendor Name, PO Number, Invoice number, Invoice date, Amount, Copy of invoice, Attachment of PO/WO, Description, Projects(Budget), Category, Budget Head, Budget Sub Head, Budget Balance, Invoice to the company, Vendor Scopper
- **This is the only task where `cf_upload_invoice` can be set via API.**

### Stage: Approved by the Issuer of PO/WO
- **Task:** Issuer of PO-WO to verify all details... (review)
- **Fields:** PO Type, Invoiced to the Company, Copy of invoice, Vendor Name, Projects(Budget), PO Number, Category, Budget Head, Budget Sub Head, Budget Balance, Invoiced amount, Yet To be invoiced amount, Attachment of PO/WO, Proof of quality, Proof of completion, Revised Amount Accepted, Amount, Revised Accepted Amount Reason
- ⚠️ Even though `cf_upload_invoice` appears in the field list, `complete_task` on a *review* task ignores `lead_field_values`.

### Stage: Approved by chairman
- **Task:** Verify Correctness of Hard Copy Invoice (data_entry)
- **Updatable fields:** Is Invoice Format Correct, Previous Invoices Checked, Previous debits checked, TDS Deduction, Outstanding Debits, Debit of Unposted Prior GST Credit
- ❌ `cf_upload_invoice` NOT included here — cannot be set.

## Stage Flow

```
Invoice received
  → Post Invoice [data_entry] ← cf_upload_invoice can be set here
  → Approved by the Issuer of PO/WO [review, no field writes]
  → Approved by chairman [review + data_entry for verification]
  → Invoice paid [data_entry for accounting]
```
