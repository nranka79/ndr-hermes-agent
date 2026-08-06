# Vendor Onboarding + PO-WO Creation Workflow

A repeatable two-step process: register a new vendor in **DRA Vendor Shortlisting**,
then create a **PO-WO** against that vendor for the quoted work — all in the DRA account.

## Step 1: Create the Vendor (Pipeline 531)

**Pipeline:** DRA Vendor Shortlisting (ID: 531) — item name "Vendor"
**Stages:** Prospect → Information Gathered → Market References Checked → General Terms Negotiated → Shortlisted

### Prospect stage — required fields
Only `cf_company_name` is required. Fill as much else as possible from the quotation.

| Field | Identifier | Notes |
|---|---|---|
| Company Name | `cf_company_name` | Required — the vendor's trading name |
| Key Contact Name | `cf_key_contact_name` | Person who signed the quotation |
| Key Contact Designation | `cf_key_contact_designation` | e.g. Proprietor, Director |
| Key Contact Mobile | `cf_key_contact_mobile` | Phone from the quotation letterhead |
| Key Contact Email | `cf_key_contact_email` | Email from the quotation letterhead |
| Company GSTN | `cf_company_gstn` | GSTIN from the quotation |
| Company PAN Number | `cf_company_pan_number` | PAN from the quotation |
| Company Full Address | `cf_company_full_address` | Full registered address |
| Vendor Source Information | `cf_vendor_source_information` | How we found them — e.g. "Quotation submitted for [Project]" |
| Company Business Type | `cf_company_business_type` | Dropdown (6 options) — ask user |
| Vendor Offerings | `cf_vendor_offerings` | Dropdown (172 options) — ask user |
| Company Entity Type | `cf_company_entity_type` | Dropdown (5 options) — ask user |

### Progressive stages need
- **Information Gathered**: key contact details + recent/old client references
- **Market References Checked**: client feedback + quality/timeliness/financial ratings
- **General Terms Negotiated**: payment period, discount, negotiation notes
- **Shortlisted**: review prerequisite (someone approves)

## Step 2: Companies Master — resolve the DRA entity (Pipeline 4475)

**Pipeline:** DRA Companies Master (ID: 4475)

Before creating a PO-WO, find the DRA subsidiary/entity that is issuing the order:

```bash
kelsa_call_tool(tool_name="search_leads", arguments={"pipeline_id": 4475, "query": "Ranka"})
```

**Known entities in this pipeline:**
- DRA Ranka Holdings — ID: 43704455
- DRA Developers & Projects Pvt Ltd. — ID: 2562316
- DRA Realty Pvt Ltd. — ID: 2562312
- DRA Projects Pvt Ltd. — ID: 2765528
- Raj Ranka Ventures — ID: 23400524

## Step 3: Upload the Quotation (S3 → Register → Attach)

Before creating the PO-WO, upload the quotation document.

### 3a. If the source is an image scan (JPG/PNG), convert to PDF first

**CRITICAL: Do NOT upload a JPG with `Content-Type: application/pdf`.** The file will upload to S3 successfully (HTTP 201) but will be unreadable (403 or "file corrupted") when accessed later. The content-type must match the actual file format.

Convert scanned images to a proper PDF using PIL before uploading:

```python
# Convert JPG/PNG scan to PDF
from PIL import Image
img = Image.open('/path/to/scan.jpg')
if img.mode != 'RGB':
    img = img.convert('RGB')
img.save('Quotation_VendorName.pdf', 'PDF', resolution=300)
```

### 3b. Get the upload URL

```python
kelsa_call_tool(tool_name="get_upload_url", arguments={
    "pipeline_id": 537,
    "file_name": "VendorName_Quotation_RefNo.pdf",
    "content_type": "application/pdf"
})
```
Returns S3 POST fields including a `file_url`.

### 3c. POST the file bytes to S3 with curl

```bash
cat /tmp/Quotation_VendorName.pdf | curl -X POST <s3-bucket-url> \
  -F "key=..." \
  -F "success_action_status=201" \
  -F "acl=private" \
  -F "x-amz-server-side-encryption=AES256" \
  -F "Content-Type=application/pdf" \
  -F "policy=..." \
  -F "x-amz-credential=..." \
  -F "x-amz-algorithm=AWS4-HMAC-SHA256" \
  -F "x-amz-date=..." \
  -F "x-amz-signature=..." \
  -F "file=@/tmp/Quotation_VendorName.pdf;filename=Quotation_VendorName.pdf;type=application/pdf"
```
Include EVERY field from the S3 POST response. The `file` field must come **last**.
On success S3 returns HTTP 201.

### 3d. Register the upload

```python
kelsa_call_tool(tool_name="register_upload", arguments={
    "pipeline_id": 537,
    "file_url": "<the file_url from get_upload_url>",
    "file_name": "VendorName_Quotation_RefNo.pdf",
    "size": <bytes>
})
```
Returns `{url, upload_id, size, name}` — store this object for the attachment field.

### 3e. Note: S3 signed URLs are expected to return 403 on direct access

After `register_upload`, the `url` in the attachment value is an S3 presigned URL. Trying to curl-verify it with `curl -sI <url>` will return `HTTP 403 Forbidden`. This is **normal** — Kelsa serves attachments through their own authenticated proxy, not via direct S3 access. The file will open correctly when clicked from inside the Kelsa web UI. **Do not waste turns re-uploading because a direct S3 curl returned 403.**

## Step 4: Create the PO-WO (Pipeline 537)

**Pipeline:** DRA PO-WO Issuing (ID: 537) — item name "PO-WO"
**Stages:** PO-WO Created → HoD Approved → Chairman Approved → Signed & Issued

### Required fields for PO-WO Created stage

| Field | Identifier | Type | Notes |
|---|---|---|---|
| PO Type | `cf_po_type` | dropdown (2) | "One Time PO" for single engagement |
| Company Name Master | `cf_company_name1` | master → Companies Mstr | `{"id": <company_id>}` from pipeline 4475 |
| Vendor New | `cf_vendor1` | master → Vendor Shortlisting | `{"id": <vendor_id>}` from pipeline 531 |
| Why Vendor | `cf_why_vendor` | text | Justification for selecting this vendor |
| Jobs | `cf_jobs` | dropdown (309) | Search existing records for similar work. "surveying" for survey work. |
| Special Instruction / Notes | `cf_special_instruction___notes` | text | Scope summary, payment breakup, key terms |
| Due Date | `cf_due_date` | date | YYYY-MM-DD. Ask user or use quotation timeline. |
| Total Value (Without Tax) | `cf_total_value_of_order__without_tax_` | number (currency) | Vendor's professional fees only (not pass-through DD) |
| Total Tax | `cf_total_tax` | number (currency) | GST amount |
| Advance To Be Paid | `cf_advance_to_be_paid` | number (currency) | Ask user if quotation doesn't specify |
| Narration | `cf_narration` | text | One-line description of the work |
| Nature of Order | `cf_nature_of_order` | dropdown (4) | **"Work Only"** = services/labour, **"Purchase Only"** = materials/supplies, **"Turnkey"** = work + supply combined |
| Po Number New | `cf_po_number_new` | text | The vendor's quotation reference number (e.g. "1258/DSC/survey/2026"). Makes the PO searchable by vendor ref. ⚠️ **KNOWN LIMITATION**: This field does not persist reliably via the API — `update_lead` returns draft=completed but the value is invisible in `get_lead` output and the Kelsa UI. See §P6 for the workaround. |

### Optional but useful fields
- `cf_quote_provided` — attachment field: pass the `{url, upload_id, size, name}` object from Step 3
- `cf_cost_justification` — text: why this vendor over alternatives
- `cf_alternate_quotes_attachments` — attachment: comparison quotes
- Budget fields (`cf_company_name_budget`, `cf_project_new1`, `cf_category`, `cf_budget_head`, `cf_budget_sub_head`) — master fields to DRA Project Budgets

### PONumber is auto-computed — cannot be set via API

The **PONumber** field (`cf_ponumber`) is an **auto-computed formula field**. Kelsa generates it as:
```
<Company Name>-<Vendor Name>-<Vendor ID>
```
You **cannot overwrite** it via `update_lead`. Any update call against `cf_ponumber` returns draft=completed but the value is silently ignored.

If the Company Name Master (`cf_company_name1`) wasn't linked during `create_lead`, the prefix will be blank:
```
-Digital Survey Consultants-749   # bad — company prefix missing
```
This cannot be fixed retroactively via the API for the same record. Create a new PO-WO with a properly linked `cf_company_name1` if the prefix matters.

### Workaround for PO number visibility (when direct field writes fail)

Both `cf_ponumber` (auto-computed) and `cf_po_number_new` (unreliable API persistence) may not show the vendor's quotation ref number. To make it visible and searchable:

1. **Include the ref in the Narration field** — this field always persists and shows in the Kelsa UI:
   ```python
   "cf_narration": "DGPS Survey... | Vendor Quotation Ref: 1258/DSC/survey/2026"
   ```

2. **Add a note on the record** — visible in the activity log:
   ```python
   add_note(lead_id=53736602, text="Vendor Quotation Ref: 1258/DSC/survey/2026 — Use this as PO reference")
   ```

3. **Search will still work** — `search_leads(pipeline_id=537, query="1258/DSC")` matches against Narration, Special Notes, and other text fields.

### The create call
```python
kelsa_call_tool(tool_name="create_lead", arguments={
    "pipeline_id": 537,
    "assignee_id": "me",  # or specific user ID
    "name": "DGPS Survey - Ranka Northstar",  # descriptive title
    "field_values": {
        "cf_po_type": "One Time PO",         # dropdown — use exact string
        "cf_company_name1": {"id": 43704455}, # master — linked record ID
        "cf_vendor1": {"id": 53736306},       # master — vendor record ID
        "cf_nature_of_order": "Work Only",    # dropdown — NOT "Services"
        "cf_jobs": "surveying",
        "cf_why_vendor": "...",
        "cf_special_instruction___notes": "...",
        "cf_due_date": "2026-10-15",
        "cf_total_value_of_order__without_tax_": 550000,
        "cf_total_tax": 99000,
        "cf_advance_to_be_paid": 50000,
        "cf_narration": "DGPS Survey for NOCs...",
        "cf_quote_provided": {"url": "...", "upload_id": 11479528, "size": 183000, "name": "..."}
    }
})
```

## Pitfalls

### P1. Nature of Order does NOT accept "Services"
Despite the user saying "services only", the dropdown options are:
- **"Work Only"** — for professional services, labour, consultancy
- **"Purchase Only"** — for materials, supplies, goods
- **"Turnkey"** — work + supply combined
- (4th option unknown — verify against pipeline schema)

If you pass "Services", Kelsa returns `Validation failed: Invalid dropdown value for Nature of Order`.

### P2. Master fields need `{"id": <integer>}`, not names
Company name, vendor, and budget fields are master-type links. They need:
```python
{"id": 43704455}  # correct
```
Not:
```python
"DRA Ranka Holdings"  # wrong — will silently fail to link
```
After creation, verify by checking if the `PONumber` field includes the company prefix (e.g. `"Dra developers & projects pvt ltd.-Vendor Name-749"`). If it starts with `"-Vendor Name-749"`, the company master link didn't take.

### P3. Create_lead returns a draft ID, not a lead ID
Always poll `get_draft_status(draft_id)` until it reports "completed" or "failed".
Failed drafts tell you exactly which field value was invalid.

### P4. Vendor pipeline fields have field-set prerequisites
The "Information Gathered" stage requires the entire `fs_vendor_company_info` field set to be complete (key contact, address, etc.). You can't skip to a later stage without these — ask the user for missing info.

### P5. The quotation may mix vendor fees and pass-through DD payments
For NOC-related work, some costs are paid directly to government departments via DD.
Only the vendor's professional fees are subject to GST. The DD component is pass-through.
Present the breakup clearly to the user:
- Vendor fees (GST applicable): ₹X
- DD to departments (no GST): ₹Y
