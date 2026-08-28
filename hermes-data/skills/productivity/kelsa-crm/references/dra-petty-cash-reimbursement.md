# DRA Petty Cash — Reimbursement Worked Example

**Session date:** 2026-07-16
**User:** Nishant Ranka
**Subject:** Roshini's IndiGo flight reimbursement (BLR→DEL + DEL→BLR, work travel)

## Invoice 1 details (outbound leg — extracted from PDF)

| Field | Value |
|------|-------|
| Airline | IndiGo (InterGlobe Aviation) |
| Invoice | KA1262706AU50748 |
| Date | 24-Jun-2026 |
| Passenger | Nishant Ranka |
| PNR | EEQYGX |
| Route | BLR → DEL (Flight 6E-849) |
| Total | ₹21,952 |
| Breakdown | Air Travel ₹19,097 + CGST 2.5% ₹476.50 + SGST 2.5% ₹476.50 + Airport Charges ₹1,902 |

## Invoice 2 details (return leg — extracted from PDF)

| Field | Value |
|------|-------|
| Airline | IndiGo (InterGlobe Aviation) |
| Invoice | DL1262706AZ33565 |
| Date | 24-Jun-2026 |
| Passenger | Roshini Ranka |
| PNR | EEQYGX |
| Route | DEL → BLR (Flight 6E-861) |
| Total | ₹19,161 |
| Breakdown | Air Travel ₹17,509 + CGST 2.5% ₹438 + SGST 2.5% ₹438 + Airport Charges ₹776 |

Combined total for round trip: ₹21,952 + ₹19,161 = **₹41,113**

## Kelsa pipeline

- **Account:** DRA (ID: 5)
- **Pipeline:** DRA Petty Cash (ID: 555)
- **Request Type:** Reimbursement

## Existing record (discovered after initial creation)

Sarthak Sharma had already submitted **both invoices** under a single reimbursement
request in record **#53783021** (DRA Ranka Holdings, ₹41,113).

- URL: https://kelsa.io/555/leads?current_item_id=53783021
- Created by: Sarthak Sharma on 2026-07-16 at 17:42
- Status: Expense Details Submitted, assignee Roshini Ranka
- Description: "Flight Tickets Of RNR From BLR to DLE and Return"
- Invoices attached: both KA1262706AU50748 (outbound) and DL1262706AZ33565 (return)

## What happened to the mistakenly created record

Record **#53784716** was initially created under DRA Realty Pvt Ltd for ₹21,952
(outbound only, via `create_lead`). When the return leg invoice arrived and
`get_lead(53783021)` revealed Sarthak's existing entry, the user's instruction was:

1. **Do NOT** create a second reimbursement for the return leg
2. **Do NOT** edit/update the mistakenly created record's field values
3. **Add one comprehensive note** to #53784716 explaining why it is being retired
4. The note must include: which existing record number, a link to it, the
   specific invoices/amounts, and who created the existing entry
5. Move it to the Retired stage — if the stage ID can't be resolved, the note
   alone is sufficient

**Resolution — note added on 2026-07-16:**
```
Retiring this record — Sarthak Sharma has already submitted both invoices
(outbound BLR→DEL ₹21,952 + return DEL→BLR ₹19,161) under a single reimbursement
request in record #53783021 (DRA Ranka Holdings). Since all invoices are covered
there, this duplicate entry is being retired.
Reference: https://kelsa.io/555/leads?current_item_id=53783021
```

## Lesson: Always check for existing entries first

The `search_leads` call on pipeline 555 with the invoice number as query would have
caught the existing entry before any work was done. This is now a mandatory step
in the skill's workflow (Step 1 of §9).

**Key takeaway:** the invoice number in the PDF filename (e.g. `TaxInvoiceKA1262706AU50748.pdf`)
is a reliable search key. `search_leads(pipeline_id=555, query="KA1262706")` would
have returned #53783021 immediately.

## Practical tip: Reading IndiGo PDF invoices

`vision_analyze` cannot process binary PDF files directly. Use `pdftotext` (part of
poppler-utils, pre-installed on this system) to extract structured text from tax
invoices:

```
pdftotext -layout /path/to/invoice.pdf -
```

This produces clean tabular output with passenger name, flight number, route, fare
breakdown, and GST details — sufficient to populate all Kelsa fields.
