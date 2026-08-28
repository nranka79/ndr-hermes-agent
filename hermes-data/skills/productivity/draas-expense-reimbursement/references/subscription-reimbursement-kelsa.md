# Recurring Software / AI Subscription Reimbursement (Kelsa 555)

Recipe for filing a monthly recurring software/AI-cloud subscription paid personally by
NDR that DRA Realty Pvt Ltd should reimburse (worked example: OpenCode Go, Aug 2026).

## Recognition
- Vendor bills in USD (Stripe/own billing — "OpenCode Go / Anomaly", OpenRouter, etc.)
  **or now directly in INR** (OpenCode Go switched to INR billing in Aug 2026 cycle)
- Monthly recurring, small amount (~$10–30 USD / ₹929–₹999 INR), paid by NDR on
  personal card (Kotak, HDFC) or UPI
- Purpose: AI model / cloud credits used for internal DRA work
- User wants BOTH the invoice AND the payment receipt attached (invoice = what's owed,
  receipt = proof of payment)

## Kelsa entry (DRA Petty Cash, pipeline 555)

Duplicate-check first: `search_leads(pipeline_id=555, query="<invoice no.>")` and by
vendor name. Then create a Reimbursement-type lead with:

| Field | Identifier | Value |
|---|---|---|
| Name | (record name) | `YYYY-MM-DD_Nishant Ranka` |
| Request Type | `cf_request_type` | `"Reimbursement"` |
| FromCompany | `cf_fromcompany` | `{"id": 2562312}` (DRA Realty Pvt Ltd) |
| Amount Requested | `cf_amount_requested` | integer in INR (convert USD if billed in USD, or use direct INR amount if billed locally) |
| Cash needed for | `cf_cash_needed_for` | vendor + what: "OpenCode Go monthly subscription (cloud/token credits) for AI model used on internal DRA work, Aug 19–Sep 19 2026" |
| Other expense tags | `cf_other_expense_tags` | `"tech"` (verified option for software/AI subscriptions) |
| Account to be debited | `cf_account_to_be_debited` | `"dra realty pvt ltd"` (verified dropdown value) |
| Date | `cf_date` | invoice issue date |
| Narration | `cf_narration` | payment context; note it is a REQUIRED Requested-stage field |
| Invoice + Receipt | `cf_receipts___vouchers` | array of BOTH files (invoice AND receipt) from `register_upload` |

## Notes / follow-up for accounts team
Add a note (or `cf_cash_needed_for` text) instructing Eshwari (Ishwari) / Sarthak to
make the accounting entry and reimburse NDR's account, and record that payment came
from NDR's personal account (Kotak credit card or HDFC bank UPI, depending on the
billing cycle).

## Pitfall
The record auto-advances to "Expense Details Submitted" (assignee Roshini Ranka) and
auto-fills Amount Approved — same behaviour as the standard reimbursement flow. The
only outstanding prerequisite is the recipient's data-entry "Submit Details of Petty
Cash Advance", which is expected.

## Billing pattern variation (OpenCode Go / Anomaly)

The vendor has been observed billing in two modes. Check the invoice to determine
which applies:

| Cycle | Invoice | Amount | Currency | Payment Method | Card/Bank | Notes |
|---|---|---|---|---|---|---|
| Aug 19–Sep 19 2026 | W8UHMURF0002 | ₹994.29 | USD → INR | Kotak Credit Card | Kotak | $10.00 converted at 99.4292 incl 4% fee |
| Aug 26–Sep 26 2026 | 3HNMSJ7E-0006 | ₹929.00 | INR direct | UPI (auto-pay) | HDFC Bank | No conversion fee; ₹65 cheaper |

The Aug 26 cycle shows the vendor switched to local INR billing, eliminating the
USD conversion fee. Future months may follow either pattern — verify the invoice
currency before creating the Kelsa record.
