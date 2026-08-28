# DRA Invoice Processing (Pipeline 516) — approval workflow

Vendor invoice approval in the DRA account (ID 5), pipeline 516 (DRA Invoice Processing,
8 stages, 60 fields). Verified 2026-08-14 on invoice 0-11 (Vardhan Ventures, ₹11,25,625,
steel supply for Amber Project, record 54660837).

## The recurring document shape

The "Copy of invoice" attachment is USUALLY a single multi-page scanned PDF containing:

- page 1 → vendor's own invoice (e.g. Vardhan Ventures bill)
- page 2 → the supplier's tax invoice / slip (e.g. Lakshmi Steel Traders LS/26-27/1994)
  with the truck number (e.g. KA05AR6134) — this is the **proof of delivery**
- page 3 → mill test certificate (e.g. Shri Tirupati Steel STSCL/26/976, IS 1786:2008,
  Fe 550 TMT) — this is the **proof of quality**

The pipeline's two mandatory attachment fields for the Post Invoice data-entry are:
- `cf_proof_of_quality` (Proof of quality) → the test certificate page
- `cf_upload_prove_of_completion_of_work` (Proof of completion) → the supplier slip / delivery page

Until both are filled, the record sits at "Invoice received" with outstanding
prerequisite `[data_entry] Post Invoice (prerequisite ID: 170)`.

## Steps

1. **Fetch the record**: `get_lead(pipeline_id: 516, lead_id: <id>)`. Read the signed
   "Copy of invoice" S3 URL.
2. **Download** the invoice PDF with a browser User-Agent (curl -A "Mozilla/5.0 …").
3. **Inspect pages**: the PDFs are usually scanned images — `page.get_text()` returns
   empty. Render each page to PNG (`fitz` / pymupdf, dpi=150) and use vision analysis
   (OpenRouter `google/gemini-2.5-flash` — see vision note below) to classify what each
   page is and extract quantities/specs.
4. **Extract separate PDFs** with pymupdf `insert_pdf`:
   ```python
   import fitz
   doc = fitz.open('invoice.pdf')
   p2 = fitz.open(); p2.insert_pdf(doc, from_page=1, to_page=1); p2.save('proof_of_delivery_p2.pdf')
   p3 = fitz.open(); p3.insert_pdf(doc, from_page=2, to_page=2); p3.save('proof_of_quality_p3.pdf')
   ```
5. **Upload both files** (full flow — the presigned URL is single-use, do it in one script):
   - `get_upload_url(pipeline_id: 516, file_name, content_type: application/pdf)` →
     returns POST fields + `file_url`
   - POST multipart/form-data to the S3 bucket (all fields + `file` last) → expect HTTP 201
   - `register_upload(pipeline_id: 516, file_url, file_name, size)` → returns attachment
     value object `{url, upload_id, size, name}`
   - `update_lead(pipeline_id: 516, lead_id, field_values: {cf_proof_of_quality: {...}, cf_upload_prove_of_completion_of_work: {...}})`
   - Poll `get_draft_status` until the update draft completes.
6. **Verify** (`get_lead`) that both fields now show the S3 URLs.
7. **Verify quantity & spec** (line-item level, not just totals):
   - Invoice quantity vs supplier slip quantity vs test-cert quantity — e.g. invoice
     19,240 kg total = slip 19,240 kg = cert 19.240 MT; per-size lines match too.
   - Test cert grade/spec vs invoice description — e.g. invoice "TMT Bars HSN 72142090
     sizes 8/10/12/16/20 mm" ↔ cert "IS 1786:2008 Fe 550, same 5 sizes, bend/rebend OK".
8. **Add a note** (`add_note`) documenting the verification: quantity check, quality
   check, what was attached, and that the invoice was approved. NDR expects this
   verification note as a comment on the record.
9. **Approve**: `complete_task(pipeline_id: 516, task_id: <Issuer approval task id>,
   note_text: 'Approved by NDR after verification…')`. The task id comes from
   `list_lead_tasks` — the "Issuer of PO-WO to verify all details of the invoice and
   work done or material delivered and then approve invoice for payment" review task.
   The record then advances to **"Approved by the Issuer of PO/WO"**.
10. **Leave the chairman step for Roshini**: a "Review & Approve" task (assigned to
    Roshini Ranka) appears next; do not complete it on NDR's behalf.

## Pitfalls

- **`get_upload_url` response JSON parsing**: the response text embeds a single JSON
  object of POST fields. A regex expecting `{ ... } }` (two closing braces) FAILS —
  the object has only one closing brace. Parse by brace-balancing from the first `{`,
  or `json.loads` the balanced span. (Burned a first upload attempt on this.)
- **Vision model**: `google/gemini-2.0-flash` returns `400 "not a valid model ID"` on
  this OpenRouter account. The configured vision model is **`google/gemini-2.5-flash`**
  (config.yaml `model.vision` / `auxiliary.vision`). Always use 2.5-flash when calling
  OpenRouter directly with base64 images. The `vision_analyze` tool may not be present
  in a session — the direct OpenRouter POST with `data:image/png;base64,...` works fine.
- **Vault token**: Kelsa MCP calls need `HERMES_SESSION_USER_ID=[REDACTED-TID]` (ndr) +
  `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock`; `get_valid_access_token()` reads the
  session identity. Only ndr (and rnr, for read) hold `mcp-kelsa-read`.
- **S3 downloads**: the signed "Copy of invoice" URL needs a browser User-Agent header,
  else some clients reject it.
