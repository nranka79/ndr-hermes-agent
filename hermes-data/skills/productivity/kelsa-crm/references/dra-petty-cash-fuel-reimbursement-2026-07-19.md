# DRA Petty Cash — Fuel Reimbursement Worked Example

**Session date:** 2026-07-19
**User:** Nishant Ranka
**Subject:** BMW 7705 diesel refill reimbursement

## Invoice details (extracted from receipt photo)

| Field | Value |
|---|---|
| Station | HP Bharathi S/S, #5 Rajbhavan Road, Bangalore |
| Bill No | 158674-ORGNL |
| Date | 19 Jul 2026 |
| Time | 14:31 |
| Vehicle | BMW 7705 (KA-05-MF-7705) |
| Fuel | Diesel — 39.12L @ ₹98.80/L |
| Total | **₹3,865.05** |
| Paid via | Kotak credit card (Nishant Ranka) |
| Odometer | 25,721 km |

## Kelsa pipeline

- **Account:** DRA (ID: 5)
- **Pipeline:** DRA Petty Cash (ID: 555)
- **Request Type:** Reimbursement
- **Company:** DRA Realty Pvt Ltd. (Companies Master ID: 2562312)

## Created record

- **Record ID:** #53855933
- **Name:** 2026-07-19_Nishant Ranka
- **Link:** https://kelsa.io/555/leads?current_item_id=53855933
- **Stage:** Expense Details Submitted (auto-advanced by pipeline automation)
- **Assignee:** Roshini Ranka (set by automation)

## Field values used

| Field | Identifier | Value |
|---|---|---|
| Request Type | `cf_request_type` | `"Reimbursement"` |
| FromCompany | `cf_fromcompany` | `{"id": 2562312}` (DRA Realty Pvt Ltd) |
| From Account Of | `cf_on_account_of` | `"Admin"` |
| Amount Requested | `cf_amount_requested` | `3865` (integer) |
| Cash needed for | `cf_cash_needed_for` | `"Diesel refill — BMW 7705 at HP Bharathi S/S, Rajbhavan Road. 39.12L @ ₹98.80/L. Odometer: 25,721 km. Paid via Kotak CC by Nishant Ranka."` |
| Account to be debited | `cf_account_to_be_debited` | `"DRA"` |
| Date | `cf_date` | `"2026-07-19"` |
| Invoice | `cf_receipts___vouchers` | attachment object from `register_upload` |

## Key learnings from this session

### 1. Scope issue (write access required)

The initial authorization only granted `mcp:read` scope. Writing to Kelsa records requires **`mcp:write`** scope as well. Fix: generate a new auth URL with `scope=mcp:read mcp:write` and re-authorize.

See the Kelsa skill's §12 (Scope Management) for the full procedure.

### 2. S3 upload with httpx

The S3 presigned POST needs `data=` for form fields and `files=` for the file **as separate arguments**:

```python
# ✓ Correct
resp = await client.post(upload_url, data=fields, files={"file": (name, bytes, mime)})

# ✗ Wrong — causes 400 RequestHeaderSectionTooLarge
data["file"] = (name, bytes, mime)
resp = await client.post(upload_url, data=data)
```

### 3. Duplicate check performed

Searched by: "7705", "3865", "Bharathi", "BMW" — no existing duplicate found for this invoice.

### 4. Auto-advance for Reimbursement type

Setting `cf_request_type: "Reimbursement"` triggers the pipeline automation to jump:
`Requested → Issued & Debited → Expense Details Submitted` (skips approval stages automatically). Record lands at "Expense Details Submitted" with Roshini Ranka as assignee. Outstanding data-entry prerequisite ("Submit Details") is normal.
