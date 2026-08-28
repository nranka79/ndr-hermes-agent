# PO Payment Tracking — Cross-Pipeline Workflow

When a user asks "has vendor X been paid?" or "check payment status", the answer requires cross-referencing two pipelines. This is not visible from a single record.

## Workflow

### Step 1 — Find the PO in DRA PO-WO Issuing (537)

Search by vendor name, PO number, or amount:

```python
session.call_tool("search_leads", arguments={
    "pipeline_id": 537,
    "query": "VendorName"  # or partial name
})
```

**Key PO fields (from get_lead):**

| Field | Identifier | What it tells you |
|-------|-----------|-------------------|
| Vendor New | `cf_vendor_new` (display) | Vendor name |
| Total Value (Without Tax) | `cf_total_value_of_order__without_tax_` | Base amount |
| Total Tax | `cf_tax_amount` (display) | Tax component |
| Total Amount | `cf_total_amount` (display) | Grand total |
| Advance To Be Paid | `cf_advance_to_be_paid` | Advance amount per PO |
| PO Stage | `stage` | PO-WO Created → HoD Approved → Chairman Approved → Signed & Issued |
| Invoice amount | `cf_invoiced_amount` (display) | Total invoiced against this PO |
| Yet to be invoice amount | `cf_yet_to_be_invoice_amount` (display) | Shows negative when fully invoiced |

Note: Stage names are misleading — "PO-WO Created" means no approval yet, not "creation is done."

### Step 2 — Find the Invoice in DRA Invoice Processing (516)

Search by vendor name, PO number, or PO record ID:

```python
# By vendor name
session.call_tool("search_leads", arguments={
    "pipeline_id": 516,
    "query": "sidphoto"
})

# By PO number
session.call_tool("search_leads", arguments={
    "pipeline_id": 516,
    "query": "743"  # PO number or part of it
})
```

The invoice record name often follows the pattern `{InvoiceNumber}_{Company}_{Vendor}` (e.g. `E080_Dra realty pvt ltd.sidphoto.in`).

### Step 3 — Check Invoice Payment Status

Get the full invoice details:

```python
result = session.call_tool("get_lead", arguments={"lead_id": <invoice_lead_id>})
```

**Key invoice fields for payment status:**

| Field | What it tells you |
|-------|------------------|
| Amount | ₹11,800 — the invoice amount |
| Stage | Where it is in the approval pipeline |
| Assignee | Who it's waiting on |
| Invoiced amount / Yet to be invoice amount | Booking/reconciliation info |
| Advance Recovered | Any advance already accounted for |
| TDS Deduction | TDS applied |
| Outstanding Debits | Remaining balance |

**Invoice stages (516) and what they mean for payment:**

| Stage | Payment Status |
|-------|---------------|
| Invoice received | Fresh — no action taken |
| Approved by Issuer of PO/WO | PO issuer approved, waiting for Chairman |
| Approved by chairman | Chairman approved, awaiting payment processing |
| Invoice paid | ✅ Payment completed |

### Step 4 — Read Notes & Events for Payment Confirmation

`get_lead` shows recent activity (last ~5 events). Use `list_lead_events` for full history:

```python
session.call_tool("list_lead_events", arguments={"lead_id": <invoice_lead_id>})
```

**Signal patterns in notes/events:**

| Signal | Meaning |
|--------|---------|
| `"₹5,000 advance already paid"` (from Nishant) | Advance was paid separately |
| `"Please clear the balance amount"` (from Nishant to Eshwari) | Balance pending clearance |
| `"Confirmed with Nishant"` | Cross-verification that payment happened |
| "Task completed: Review & Approve" | Stage prerequisite cleared |
| "Stage changed to ..." | Record moved forward in pipeline |

### Step 5 — Synthesize the Answer

Combine PO amount + advance + invoice stage + notes to give a complete picture:

```
PO Amount: ₹11,800 (₹10,000 + ₹1,800 tax)
Advance: ₹5,000 (per PO terms)
Invoice: ₹11,800, at "Approved by Issuer" stage
From notes: ₹5,000 advance already paid (confirmed by Nishant)
Balance: ~₹6,800 — Eshwari was asked to clear, still pending
```

## Example — SidPhoto (Jul 2026)

**PO #743** (pipeline 537) — sidphoto.in, Serenity Hillview drone photography
- ₹11,800 total, 50% advance (₹5,000)
- Stage: PO-WO Created (not yet approved)
- Work order issued: Drone photography work order PDF

**Invoice E080** (pipeline 516) — same vendor
- ₹11,800 invoiced
- Stage: Approved by the Issuer of PO/WO (assigned to Nishant for Chairman approval)
- Roshini approved on Jun 25

**Payment outcome from notes:**
- ₹5,000 advance **already paid** to SidPhoto (Nishant confirmed Jul 16)
- ₹6,800 balance — Eshwari asked to clear, pending

## Pitfalls

- **PO stage ≠ payment status.** A PO at "PO-WO Created" just means the purchase request was entered. Payment happens against the invoice, not the PO.
- **Invoice stage ≠ actual money movement.** "Approved by chairman" means approval, not disbursement. Payment happens at "Invoice paid" stage (usually involves Eshwari/Accounts).
- **Advance payments may be made outside Kelsa.** The PO may say "50% advance" but the actual advance disbursement may not be tracked in any Kelsa field. Check notes for confirmation.
- **Negative "Yet to be invoiced" amounts** (e.g. -₹11,800) mean the invoiced amount exceeds the PO amount — a data entry quirk, not necessarily a problem.
- **Notes are the authoritative source.** Payment confirmation (₹5,000 paid, balance pending) often lives in Nishant's notes on the invoice, not in structured fields.
- **Check both lists** — `get_lead` only shows the last ~5 events. Use `list_lead_events` for full history.
