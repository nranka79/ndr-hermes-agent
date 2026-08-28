When the user asks to file a medical insurance reimbursement claim via email, the workflow spans multiple systems and requires thorough document validation before drafting.

## Trigger Phrases

"claim for reimbursement", "pre-operative expenses", "file a claim", "insurance claim", "Medi Assist", "TPA claim", "hospitalization claim"

## Document Inventory Checklist

Before drafting, locate ALL of the following from Google Drive:

### 1. Invoices/Receipts
Every out-of-pocket expense needs its own invoice. Cross-check claimed amounts against invoices found — missing receipts are the #1 reason TPAs come back asking for more.

### 2. Diagnostic Reports
Each invoice must have a corresponding medical report (test result, consultation note, procedure report) proving the expense was genuinely incurred for the claimed condition.

### 3. Hospitalization Documents
- Discharge Summary (links pre-op to the admission)
- Insurance Authorization Letter (from TPA)
- Hospital Invoice (shows what cashless covered)
- Payment Receipts (shows what was paid out-of-pocket)

### 4. Policy Document
Needed to prove coverage terms, co-pay %, waiting period waivers.

### 5. KYC Documents
- PAN Card (mandatory for claims > ₹25,000)
- Aadhaar / Photo ID
- Canceled Cheque / Bank Passbook (for NEFT)
- Claim Form (Form C — standard IRDAI form)

## Completeness Check

**MUST verify invoice line items** — don't assume the total matches what the user claims. Download each PDF and extract text to see the breakdown. Common gaps:

- A test was done (report exists) but the receipt is missing from Drive
- A single invoice bundles multiple items — check that the claimed amount matches the actual total
- Day-care procedures may have separate OT/investigation bills not yet uploaded

## Escalation / Supplementary Actions

- **Missing KYC docs on Drive** → WhatsApp the person who can provide them (bank for cancelled cheque, insurance portal for Form C)
- **No-Claim Bonus certificate** → Only the insurer can issue this; don't waste time searching for it
- **Claim Form C** — can't be downloaded from public URLs (TPA portals block it). Call the TPA helpline to request it, or download from the Medi Assist customer portal after logging in

## Invoice Verification — Always Read the Actual PDFs

Don't trust filenames or user-provided totals alone. Download each invoice PDF and extract the actual amounts:

1. Find invoices in Drive — check both the patient's main medical folder and any `Invoices` subfolder
2. Download via `drive.files().get_media(fileId=...)` 
3. Convert to PNG: `pdftoppm -png -r 200 invoice.pdf /tmp/out`
4. Read with `vision_analyze` — extract bill number, date, each line item, and the grand total
5. Cross-check the total against what the user claims. A single invoice may bundle multiple items

## Expense Categorization for Pre-hospitalization Claims

Only expenses incurred **before the admission date** qualify as pre-hospitalization. The hospitalization bill (room, OT, surgeon fees, medicines) is billed separately by the hospital to the TPA — it is NOT part of the reimbursement claim.

**Correct categorization for a stapedotomy claim example:**

| Category | What's included |
|----------|----------------|
| **Pre-hospitalization** (before admission) | Pre-op consultations, lab tests, imaging (echo, CT, X-ray), audiometry, PFT/DLCO, anaesthesiology consult, blood tests (D-Dimer, ANA, Anti-CCP) |
| **Hospitalization** (during stay) | Room charges, OT charges, surgeon fees, anaesthetist fees, medicines, consumables — billed by hospital directly to TPA |
| **Patient co-pay** | Any advance paid by patient to hospital (e.g. via credit card) — this is a payment receipt, not a pre-hospitalization expense to claim |

When building the expense table, group by hospital with subtotals:
- **Trustwell subtotal** (all pre-op work done at Trustwell)
- **Manipal subtotal** (all pre-op work done at Manipal)
- **Grand total** (sum of all pre-hospitalization expenses)

## ⚠️ Claim Form C — Scanned Image PDF (critical workflow)

The official IRDAI-standard Claim Form C distributed by TPAs (MediAssist, etc.) is typically a **scanned image PDF** — not a fillable AcroForm with named fields. This means:
- `pymupdf` / `pdfminer` cannot find any AcroFields to fill
- `pymupdf` text extraction returns empty (image-only)
- You cannot programmatically overlay typed text into the form fields with reliable visual alignment

### What to do (in order)

1. **Detect the problem early** — after opening the PDF, check if `doc.get_toc()` returns empty and `page.get_text()` returns only whitespace. If so, it's an image-only scan.

2. **Explain the constraint explicitly** — tell the user: *"The official Claim Form C is a scanned image, not a fillable PDF. There is no standard way to embed typed text into it with correct visual alignment."* Do NOT silently create an alternative format without explanation.

3. **Offer options and get a decision:**
   - **Option A:** Print the blank form, fill it by hand, scan and send.
   - **Option B:** I can create a clean typed PDF with the same fields — won't match the original exactly but all data present.
   - **Option C (preferred by ndr, confirmed 2026-07-16):** Build an **HTML+CSS replica** that looks exactly like the scanned form, fill all fields in the HTML, then convert to PDF via `weasyprint`. This preserves the exact TPA format while being fully typed.

4. **User preference (ndr@draas.com, confirmed 2026-07-16):** When told the form is a scanned image, Nishant asked for **Option C** — build an HTML replica. He rejected the plain typed version (Option B). Offer Option C proactively: *"Since this is a scanned image, I can create an HTML+CSS version that looks identical, fill it in, and convert to PDF."* Do NOT default to Option A or B without mentioning C.

### HTML Replica Recipe

When building an HTML replica of a scanned claim form:

1. **Convert PDF pages to images** for visual reference:
   ```bash
   pdftoppm -png -r 300 scanned_form.pdf /tmp/form_page
   ```

2. **Analyze each page** with `vision_analyze` — read every field, checkbox, label, table, border. Ask for extreme detail: field positions, character-box layouts, checkbox labels, table column widths.

3. **Build HTML+CSS with character boxes** — the defining visual of Indian claim forms is individual square character boxes. Use this CSS pattern:
   ```css
   .cbox {
     display: inline-flex; align-items: center; justify-content: center;
     width: 9pt; height: 11pt; border: 0.5pt solid #222;
     font-size: 7.5pt; font-family: 'Courier New', monospace;
     text-transform: uppercase; vertical-align: middle;
   }
   ```
   Each character gets its own `<span class="cbox">A</span>`. Empty fields use `class="cbox empty"`.

4. **Checkbox style** — use a small bordered box with a filled checkmark:
   ```css
   .chk-box { width: 9pt; height: 9pt; border: 0.8pt solid #000; display: inline-flex; }
   .chk-box.filled { background: #000; color: #fff; }
   .chk-box.filled::after { content: "\2713"; }
   ```

5. **Convert to PDF** using `weasyprint` (install via `uv pip install weasyprint`):
   ```python
   from weasyprint import HTML
   HTML(filename='form.html').write_pdf('output.pdf')
   ```

6. **Verify** by converting back: `pdftoppm -png -r 200 output.pdf /tmp/check` then `vision_analyze` — verify each section, all filled values, totals, dates.

7. **Upload to Drive** (patient's medical folder / TMP) and attach to the Gmail draft using the raw Gmail API (attachments aren't supported by `draft_create`).

**Key sections to replicate (MediAssist form):**
- **A:** Primary Insured (Policy No, Name, Address — character boxes)
- **B:** Insurance History (Yes/No checkboxes, dates, company name)
- **C:** Patient details (Name, Gender, Age, DOB, Relationship, Occupation)
- **D:** Hospitalization (Hospital name, Room category, Admission/Discharge dates/times)
- **E:** Claim details (Pre-hospitalization expenses amount, Total, Document checklist items)
- **F:** Bills Enclosed table (numbered rows with Bill No, Date, Issued by, Towards, Amount)
- **G:** Bank Account (PAN, Account Number, Bank Name, IFSC)
- **H:** Declaration (Date, Place, Signature line)

**Pitfalls:**
- The form is 1 page (Part A only) — Parts B/C/D/E/F are hospital/guidance pages, skip those
- Use `@page { size: A4; margin: 0; }` and `body { padding: 12mm 14mm; }` to match scanned margins
- Add `@media print { -webkit-print-color-adjust: exact; print-color-adjust: exact; }` so filled checkboxes survive PDF conversion
- Section labels on the right side (SECTION A through H) are a distinctive visual feature — replicate with `writing-mode: vertical-rl` and `transform: rotate(180deg)`
- Historical medical records (prior years) are NOT part of the current claim — only include documents from the current treatment episode

### Attaching the form to the draft

Since `gws_skill_bridge.draft_create` / `draft_reply_create` do NOT support file attachments (see email-drafter SKILL.md pitfall), use the raw Gmail API:

```python
from tools.gws_auth import build_service
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64

gmail = build_service("gmail", "v1", service_name=SERVICE_NAME)
msg = MIMEMultipart("mixed")
# ... build message with body + attachment(s)
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = gmail.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
```

See `references/drive-to-draft-pipeline.md` in this skill for the full attachment-building workflow.

## Email Structure for Claim Draft

### Format: Rich HTML (user preference)

Nishant explicitly requests **rich HTML email body** for claim submissions. Do NOT send plain text. The HTML must be rendered as a proper email (not raw HTML code in the body).

Build with:
```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
msg_alt = MIMEMultipart('alternative')
msg_alt.attach(MIMEText(html_body, 'html'))
```

### Required sections in the HTML email:

1. **Header** (dark background): Policy No., Patient Name, Insurer, Subject line
2. **Patient & Policy Details** table: policy holder, policy no., insurer, sum insured, commencement date, patient DOB, contact, PAN, bank account
3. **Hospitalization Details** table: hospital name, admission/discharge dates/times, room, diagnosis, surgery, surgeon
4. **Expense Table** — hospital-grouped rows:
   - Group by hospital (Trustwell subtotal → Manipal subtotal → Grand total)
   - Use light blue background (`#eef4fb`) for hospital header rows separating the groups
   - Grand total row in dark blue (`#1a3a5c`) with white text
   - Include bill numbers, dates, and detailed descriptions for each line item
5. **Do NOT include** co-pay percentage, NCB calculation, or expected reimbursement amounts. Just state the total and say "We request you to process the reimbursement." Let the insurance company compute what's payable. (User correction 2026-07-16.)
6. **Categorized attachment list** as a numbered table — match numbering to the actual filenames for easy cross-reference
7. **Footer** with sender name and contact

### Attachment numbering convention

```
01_KDR_Claim_Form_Filled.pdf
02_KDR_PAN_Card.pdf
03_KDR_Aadhaar_Card.pdf
04_KDR_Cancelled_Cheque_BankName_AccountNo.pdf
05_HOSPITALNAME_Description_Invoice_BillNo_Amount.pdf
...
```

Number attachments sequentially. Match the numbers to the attachments list in the email body so the TPA officer can cross-reference without downloading everything first.

Invoice filenames should include: hospital abbreviation, description, bill number, and amount for quick identification.
