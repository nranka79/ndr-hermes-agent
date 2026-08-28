---
name: draas-expense-reimbursement
description: "Process expense receipts and invoices for DRA Group companies: capture payment proof, identify payer/reimbursement entity, file to TMP, create processing note with reimbursement instructions."
tags: [draas, expense, reimbursement, invoice, accounts, billing]
metadata:
  hermes:
    tags: [draas, expense, reimbursement, invoice, accounts, billing]
    category: productivity
    related_skills: [google-workspace, draas-landowner-records]
---

# DRA Group Expense & Reimbursement Processing

When a user shares a payment receipt, invoice, or expense proof (fuel bill, vendor payment, travel expense, etc.) and says "post to invoice processing pipeline" or "process this expense", use this workflow.

## When to load

- User shares a receipt/invoice image and says "process this", "file this invoice", "post to invoice pipeline"
- User says "this was paid on my card — need reimbursement from [entity]"
- User sends a fuel/bill/expense receipt and gives instructions on which entity to debit
- Trigger phrases: "invoice processing", "reimbursement", "file this invoice", "expense bill"

## Standard workflow

### Phase 1 — Extract receipt details from the image

The receipt text is usually auto-extracted by the platform OCR. If not, call `vision_analyze(image_url)` to extract the text.

Capture these fields from the receipt:

| Field | Example from fuel receipt |
|-------|--------------------------|
| Vendor/Station | HP — Bharathi Service |
| Address | Rajbavan Road, Bangalore |
| Receipt/Invoice No. | G4145 |
| Date | 15/07/26 |
| Time | 15:40 |
| Product/Service | Petrol |
| Rate per unit | ₹110.89/L |
| Quantity | 36.07 L |
| **Total Amount** | **₹3,999.80** |
| Payment Mode | Kotak Credit Card (NDR's personal card) |

### Phase 2 — Identify payer and reimbursement flow

Listen carefully to the user's instructions — they will specify:
- **Who paid** (e.g. "paid on my Kotak credit card" = NDR paid personally)
- **Which entity should reimburse** (e.g. "reimbursement from DRA Realty Private Limited")
- **Which entity to post the invoice to** (e.g. "post to DRA Realty Private Limited")

Common patterns:
- NDR pays on personal card → reimbursement from DRA Realty / DRA Group entity
- Company pays directly → no reimbursement needed, file as company expense
- User says "file this in Kelsa / post a reimbursement in Kelsa" → **skip the
  TMP staging below and go straight to the Kelsa DRA Petty Cash pipeline (555)
  workflow in the `kelsa-crm` skill §10** (duplicate check → S3 upload →
  create_lead with Request Type=Reimbursement). TMP + processing note is the
  fallback for "process this expense" without a Kelsa instruction.

### Phase 2.5 — Crop the receipt image and convert to PDF (before filing)

The user frequently wants the receipt cropped (photo has dark/extra background)
and delivered as PDF before it is filed. Do this BEFORE any Kelsa/Drive upload:

1. Run the recipe in `references/receipt-image-cropping.md` — it uses pure-PIL
   row/column darkness profiling to find the receipt content zone when a naive
   `getbbox()` crop returns None (which happens on photos of receipts on dark
   surfaces — the whole frame has mid-gray values so content-thresholding fails).
2. Always save BOTH a cropped JPG (for preview) and a PDF (for filing/attachment).
3. Verify the crop by re-running `vision_analyze` on the cropped JPG and
   confirming the amount/vendor/date survived before uploading it anywhere.
4. Name per convention: `<YYYYMMDD>_<Vendor>_<Desc>_<Amount>.pdf`
   (e.g. `20260811_MaverickFarmerCoffee_FnB_557.pdf`).

### Phase 3 — Upload to Drive

Per policy, all new documents go to the **TMP folder** first:

1. **Upload the receipt image** to TMP:
   ```python
   file_meta = {
       'name': f'{date}_{vendor}_Invoice_{product}_{amount}.jpg',
       'parents': ['18p74II2uL32sNDzDDwXzmlOUdJJOTmE-']  # TMP folder ID
   }
   media = MediaFileUpload(image_path, mimetype='image/jpeg')
   drive.files().create(body=file_meta, media_body=media, ...).execute()
   ```

2. **Create an Invoice Processing Note** (Google Doc) in TMP:
   - Invoice Details: vendor, date, product/service, receipt no., amount
   - Payment Details: who paid, on which card, payment status (PAID)
   - Reimbursement Instruction: reimburse FROM which entity, reimburse TO whom
   - Vehicle/Project reference (if applicable)
   - Links to attached receipt image

### Phase 4 — Name convention for files

Use a consistent naming pattern:

```
<YYYYMMDD>_<Vendor>_<Product/Desc>_<Amount>_<Context>.<ext>
```

Examples:
- `20260715_HP_Fuel_Invoice_Petrol_3999.80_Innova.jpg`
- `20260715_Invoice_Processing_NOTE - HP Fuel - DRA Realty`

### Phase 5 — Invoice Processing Note template content

```text
INVOICE PROCESSING NOTE
Date: <today>

=== INVOICE DETAILS ===
Invoice Type: <Fuel / Travel / Vendor / etc.>
Vendor: <Name>, <Address>
Receipt No.: <number>
Date of Purchase: <date>
Time: <time>
Product/Service: <description>
Rate: <Rs. per unit>
Quantity: <volume/units>
Total Amount: <Rs. X>
Vehicle/Project: <reference>

=== PAYMENT DETAILS ===
Paid By: <Person Name (NDR)>
Mode: <Card / Cash / UPI>
Payment Status: PAID

=== REIMBURSEMENT ===
Reimburse From: <Entity Name (e.g. DRA Realty Private Limited)>
Reimburse To: <Person Name (e.g. Nishant Ranka)>
Reason: <e.g. Fuel for Innova - Company vehicle expense>

=== ATTACHMENTS ===
1. <Receipt image filename (same folder)>
```

### When the destination is Kelsa (not Drive TMP)

NDR frequently says "file this in Kelsa" / "post this reimbursement" — that means the
**DRA Petty Cash pipeline (555)** workflow, NOT the Drive TMP + processing-note flow
above. See `kelsa-crm` skill §10 for the exact create path (duplicate check →
get_pipeline → company master lookup → S3 upload → create_lead).

**User preference (verified 2026-08-11): before filing, crop the receipt image and
convert it to PDF.** When NDR shares a phone photo of a slip/cheque, he expects:
1. Crop to the receipt content (trim dark background/surface)
2. Contrast-enhance for legibility (autocontrast + slight contrast boost)
3. Convert to PDF — name `YYYYMMDD_Vendor_Desc_Amount.pdf`
4. Attach THAT PDF as `cf_receipts___vouchers` in Kelsa

The ₹557 Maverick & Farmer Coffee F&B filing (2026-08-11) followed exactly this path:
cropped JPG → `20260811_MaverickFarmerCoffee_FnB_557.pdf` → S3 upload → reimbursement
record created with tag `f&b`, debited to DRA Realty Pvt Ltd.

### GWS environment setup

Since system python has PEP 668 and no system `google-api-python-client`:

```bash
uv venv /tmp/gwsvenv
uv pip install --python /tmp/gwsvenv/bin/python google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

Then run scripts with:
```bash
PYTHONPATH=/opt/hermes:/tmp/gwsvenv/lib/python3.13/site-packages /tmp/gwsvenv/bin/python /tmp/script.py
```

## Pitfalls

- **Verify the actual file bytes are accessible BEFORE starting a Kelsa create + S3 upload (2026-08-20).** The Kelsa reimbursement record requires the real receipt/invoice PDF bytes for `get_upload_url` → S3 POST → `register_upload`. When the user shares files via the upload interface, the bytes may NOT be reachable on the host filesystem — only the extracted text may come through (with opaque resource IDs, not paths). Before doing any Kelsa work, confirm you can physically read the PDF file (check `/data/hermes/document_cache/`, `/tmp`, and the attachments interface), and if not, ask the user to re-send the PDFs first. Building a faithful invoice PDF from extracted text is acceptable when you HAVE the full text (name it and file it), but never fabricate the *receipt* content you don't have — request the real file. Don't create the reimbursement record until the attachment bytes are in hand.
- **Always resolve the GWS account first** — call `gws_resolve_account()` before any Drive/Gmail operation
- **vision_analyze works on images only**, not PDFs. For scanned PDF invoices, use `pdftotext` (poppler-utils) or the ocr-and-documents skill
- **TMP folder is for initial staging only** — the permanent filing (under the entity's own folder structure) is the accounts team's call, not the agent's. Don't create permanent expense folders under entity drives unless explicitly told to.
- **The user may say "post it to [entity]"** but mean the invoice is to be filed *under* that entity's account, not physically placed in that entity's Drive folder. When in doubt, TMP + processing note is the right approach — accounts will move it to the final location.
- **Fuel receipts often have multiple amounts** — check: Rate × Volume = Total Amount. Use the calculated total, not any stray "Atot" or "Vtot" accumulator values on the receipt.

## References

- `references/subscription-reimbursement-kelsa.md` — recurring software/AI-cloud subscription reimbursement (OpenCode Go worked example): USD billing, dual invoice+receipt attachment, verified `tech` tag and `dra realty pvt ltd` debit value, accounts-team note pattern.
