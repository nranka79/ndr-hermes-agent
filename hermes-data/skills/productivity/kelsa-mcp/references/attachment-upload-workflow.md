# Kelsa Attachment Upload Workflow

When a pipeline record needs attachment files (invoices, receipts, vouchers, photos), use this 3-step flow. Works for **any pipeline** with attachment-type custom fields.

## Overview

```
get_upload_url  →  curl multipart POST →  register_upload  →  use {url, upload_id, name} in create_lead field_values
```

## Step 1: Get a Presigned Upload URL

Call `get_upload_url` with the pipeline ID, file name, and (optional) content type:

```
mcp_Kelsa_Read_get_upload_url(
  pipeline_id=555,
  file_name="fuel_invoice_innova_1550.jpg",
  content_type="image/jpeg"
)
```

Returns:
- An S3 POST endpoint: `https://kelsa-clients-production.s3.ap-south-1.amazonaws.com`
- A set of form fields (key, policy, signatures, credentials)
- A `file_url` for the final file location

## Step 2: Upload Bytes to S3

Use `curl` with `-F` flags — one flag per form field (including all returned fields), plus the file itself as the last field:

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -F "key=<the returned key>" \
  -F "success_action_status=201" \
  -F "acl=private" \
  -F "x-amz-server-side-encryption=AES256" \
  -F "Content-Type=image/jpeg" \
  -F "policy=<the returned policy>" \
  -F "x-amz-credential=<the returned credential>" \
  -F "x-amz-algorithm=AWS4-HMAC-SHA256" \
  -F "x-amz-date=<the returned date>" \
  -F "x-amz-signature=<the returned signature>" \
  -F "file=@/path/to/file.jpg;filename=display_name.jpg" \
  https://kelsa-clients-production.s3.ap-south-1.amazonaws.com
```

**Success = HTTP 201.** Any other status means the upload failed.

**Common pitfalls:**
- The `file` field **must come last** in the curl `-F` sequence
- The filename after `;filename=` is for display — use a clean name
- Both are JPEGs? Set `Content-Type=image/jpeg`. PDF? `application/pdf`
- The presigned URL is **single-use** and **time-limited** (a few minutes)

## Step 3: Register the Upload

```python
mcp_Kelsa_Read_register_upload(
  pipeline_id=555,
  file_url="https://kelsa-clients-production.s3.ap-south-1.amazonaws.com/uploads/accounts/5/pipelines/555/files/<uuid>/filename.jpg",
  file_name="fuel_invoice_innova_1550.jpg",
  size=<bytes>  # optional
)
```

Returns an attachment value object:
```json
{
  "url": "https://...",
  "upload_id": 11363302,
  "name": "fuel_invoice_innova_1550.jpg"
}
```

## Step 4: Use in create_lead / complete_task

**Single file field:** pass the object directly.

**Multi-file field:** pass as an array:
```json
[
  {"url": "...", "upload_id": 11363302, "name": "file1.jpg"},
  {"url": "...", "upload_id": 11363303, "name": "file2.jpg"}
]
```

Where to set it depends on the pipeline stage:

| When | How |
|------|-----|
| **Creating a new record** (`create_lead`) | Include in `field_values` keyed by the attachment field identifier (e.g. `cf_receipts___vouchers`) |
| **Completing a data_entry task** (`complete_task`) | Include in `lead_field_values` keyed by the field identifier — **only works if the field is in that task's prerequisite field set** |
| **Completing a review task** | `lead_field_values` is **ignored** — must be set during creation |

## Pipeline-Specific Examples

### DRA Petty Cash (Pipeline 555) — Reimbursement

Field: `cf_receipts___vouchers` (Acknowledgement Voucher) — attachment, single-file.

Two files (invoice + payment proof) can be passed as an array:

```json
"cf_receipts___vouchers": [
  {"url": "...invoice.jpg", "upload_id": 11363302, "name": "fuel_invoice_innova_1550.jpg"},
  {"url": "...gpay.jpg", "upload_id": 11363303, "name": "gpay_payment_screenshot_innova_1550.jpg"}
]
```

**Other Petty Cash fields for Reimbursement:**
- `cf_request_type`: `"Reimbursement"` (string, not `{id, label}`)
- `cf_fromcompany`: `{"id": <company_record_id>}` (master field)
- `cf_on_account_of`: `"Admin"` (string — dropdown)
- `cf_amount_requested`: `<number>` (plain number, no ₹)
- `cf_cash_needed_for`: `"Refueling Innova — 32.47L petrol"` (text description)
- `cf_account_to_be_debited`: `"DRA"` (string — dropdown)
- `cf_project`: `{"id": <project_record_id>}` (master field)
- `cf_date`: `"2026-07-02"` (YYYY-MM-DD)
- `cf_name`: `"2026-07-02_Fuel_Innova"` (Petty Cash ID — follows `{date}_{description}` pattern)

**Auto-behaviour for Reimbursement type:** The pipeline has an automation that `stage_jump`s from "Requested" → "Issued & Debited" on entry when Request Type = Reimbursement. This means the record skips the approval stage automatically.

### DRA Invoice Processing (Pipeline 516)

Attachment fields (`cf_upload_invoice`, `cf_attachment_of_po_wo`, etc.) are only settable at creation via the `Post Invoice` data_entry task. See `references/invoice-processing-fields.md`.

## Error Recovery

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| HTTP 403 from S3 upload | Expired presigned URL | Call `get_upload_url` again |
| `register_upload` returns error | `file_url` doesn't match the key used in upload | Use the exact `file_url` returned by `get_upload_url` |
| Attachment shows broken in Kelsa | File wasn't uploaded before `register_upload` | Re-upload and re-register |
| `create_lead` successful but attachment missing | Wrong field identifier | Check with `get_pipeline` for the exact `cf_` identifier |
