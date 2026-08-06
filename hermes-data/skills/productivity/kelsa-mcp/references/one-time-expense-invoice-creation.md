# One-Time / Reimbursement Expense Invoice Creation (Pipeline 516)

For expenses that are neither vendor invoices with POs nor statutory demands — personal travel, taxi receipts, ad-hoc purchases, reimbursement claims.

## When to use this pattern

- A user has a receipt from a **one-off service** (taxi, toll, meal, courier, parking)
- The "vendor" isn't a recurring supplier — it's a taxi aggregator, a government counter, a retail shop
- The receipt has a **known entity to bill** (e.g., DRA Ranka Holdings, DRA Realty, Nishant Ranka)
- No PO exists (and none needed)

## Full Workflow

### Step 1 — Get the receipt file ready

If the receipt is an image the user shared in Telegram, copy it from the image cache:

```python
import shutil
shutil.copy2("/data/hermes/image_cache/img_XXXX.jpg", "/opt/data/descriptive_name.jpg")
```

### Step 2 — Upload receipt to Kelsa S3

```python
# Step 2a — Get presigned upload URL
get_upload_url(
    pipeline_id=516,
    file_name="Descriptive_Name.jpg",
    content_type="image/jpeg"
)
# Returns S3 POST fields + file_url

# Step 2b — Upload bytes to S3 (curl in terminal)
curl -s -X POST https://kelsa-clients-production.s3.ap-south-1.amazonaws.com \
  -F "key=..." \
  -F "success_action_status=201" \
  -F "acl=private" \
  -F "x-amz-server-side-encryption=AES256" \
  -F "Content-Type=image/jpeg" \
  -F "policy=..." \
  -F "x-amz-credential=..." \
  -F "x-amz-algorithm=AWS4-HMAC-SHA256" \
  -F "x-amz-date=..." \
  -F "x-amz-signature=..." \
  -F "file=@/opt/data/descriptive_name.jpg"

# Step 2c — Register the upload
register_upload(
    pipeline_id=516,
    file_url="https://kelsa-clients-production.s3.ap-south-1.amazonaws.com/uploads/...",
    file_name="Descriptive_Name.jpg",
    size=132725
)
# Returns {"url": "...", "upload_id": N, "size": N, "name": "..."}
# Pass this object to cf_upload_invoice
```

### Step 3 — Find or create the vendor

**First, search the vendor pipeline (531) for an existing vendor:**

```python
search_leads(pipeline_id=531, query="Delhi Traffic")
search_leads(pipeline_id=531, query="Taxi")
search_leads(pipeline_id=531, query="HumPum")
```

**If vendor doesn't exist, create one with minimum fields:**

The "Prospect" stage data_entry requires: Company Name, Key Contact Name, Key Contact Mobile, Key Contact Designation, Vendor Offerings, Vendor Source Information.

```python
create_lead(
    pipeline_id=531,
    field_values={
        "cf_company_name": "Delhi Traffic Police - Prepaid Taxi (HumPum)",
        "cf_key_contact_name": "Delhi Traffic Police",
        "cf_key_contact_designation": "Prepaid Taxi Service",
        "cf_key_contact_mobile": "+91600138743",
        "cf_vendor_offerings": "Transport - Prepaid Taxi",
        "cf_vendor_source_information": "One-off use for Delhi Airport to AIIMS trip"
    },
    name="Delhi Traffic Police - Prepaid Taxi (HumPum)"
)
# Save returned record ID for the invoice
```

**Key points for minimum vendor creation:**
- Vendor Offerings accepts broad category strings
- The vendor stays in "Prospect" with outstanding prerequisites — acceptable for one-off
- Pass `{"id": VENDOR_RECORD_ID}` as `cf_vendor_n` in the invoice

**Common one-off vendor naming:**

| Expense Type | Company Name |
|-------------|-------------|
| Delhi prepaid taxi | Delhi Traffic Police - Prepaid Taxi (HumPum) |
| Uber/Ola ride | Uber India / Ola Cabs |
| Toll payment | NHAI - [Toll Plaza Name] |
| Courier | [Courier Company] |
| Restaurant/meal | [Restaurant Name] |

### Step 4 — Find the company entity to bill

Search DRA Companies Master (4475):

```python
search_leads(pipeline_id=4475, query="Ranka Holdings")
```

**Known entity IDs (verified Jul 2026):** DRA Ranka Holdings = 43704455, DRA Developers & Projects Pvt Ltd = 2562316, DRA Projects Pvt Ltd = 2765528, DRA Realty Pvt Ltd = 2562312

### Step 5 — Create the invoice

```python
create_lead(
    pipeline_id=516,
    name="Delhi Taxi - Airport to AIIMS - ₹524",
    field_values={
        "cf_amount": 524,
        "cf_description": "Delhi Airport T3 to AIIMS — Prepaid Taxi (Sedan AC). Ref: 600138743, OTP 914542.",
        "cf_invoice_date": "2026-07-02",
        "cf_invoice_number": "DLH-TAXI-02JUL2026",
        "cf_invoiced_to_the_company1": {"id": 43704455},
        "cf_vendor_n": {"id": VENDOR_ID},
        "cf_upload_invoice": {"url": "...", "upload_id": N, "size": N, "name": "..."}
    }
)
```

### Step 6 — Verify

```python
get_draft_status(draft_id=...)
search_leads(pipeline_id=516, query="DLH-TAXI-02JUL2026")
```

## Differences from Statutory Invoice Workflow

| Aspect | One-Off Expense | Statutory Invoice |
|--------|----------------|-------------------|
| Vendor | Created ad-hoc (min fields) | Already in vendor master |
| PO Type | Not set | "No PO" (explicit) |
| Budget path | Not required | Required |
| Attachment | S3 upload flow | Drive link string |
| Amount | Small (< ₹5K) | Can be large |

## Pitfalls

- **Vendor name variants** — Search phonetic variants before creating (e.g., "HumPum", "Humpum", "Delhi Prepaid")
- **Master field format** — Use `{"id": NUMBER}` not `{"id": "STRING"}`
- **Amount** — Plain number, no ₹ or commas. ₹524 → `524`
- **Date** — `YYYY-MM-DD` string
- **Record name** — Avoid `/ \ : * ? " < > |`
