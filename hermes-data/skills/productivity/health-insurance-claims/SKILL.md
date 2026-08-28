---
name: health-insurance-claims
description: |-
  File health insurance reimbursement claims (pre-hospitalization, post-hospitalization, and main hospitalization) with TPAs and insurers.
  Covers: locating policy documents in Drive, finding invoices/reports, compiling expense totals,
  validating documents for claim completeness, drafting comprehensive claim emails with attachment checklists,
  and escalating disputes up the grievance ladder.
  Trigger: "claim", "reimbursement", "TPA claim", "insurance claim", "file claim", "pre-operative expenses", "infusion confirmation", "KIRAN PAP", "Medybiz", "Keytruda", "Patient Assistance Program"
metadata:
  hermes:
    tags: [insurance, claim, reimbursement, tpa, health-insurance, medical-bills, email-draft]
category: productivity
version: 1.0.0
author: ndr@draas.com
---

# Health Insurance Claims

## Trigger Conditions

Activate when the user says anything like:
- "File a claim for Kanta's hospitalization expenses"
- "Prepare reimbursement for pre-operative expenses"
- "Draft an email to the TPA with all invoices"
- "Help me submit a health insurance claim"
- "Pre-operative claim for stapedotomy"
- Any mention of Medi Assist, Royal Sundaram, Star Health, TPA, claim form

## Stage 1 — Gather Policy & TPA Info

1. **Locate the policy reference document in Google Drive**
   - Search the `TMP` folder or the relevant medical folder (`KDR Medical`, `RNR Medical`, etc.)
   - The document naming pattern is: `[Patient] — [Insurer] [Plan] — Claim Contacts & Procedures`
   - Example: `Kanta Ranka — Royal Sundaram Lifeline Elite Insurance — Claim Contacts & Procedures`
   - This document contains: policy number, sum insured, co-payment %, TPA contact details, escalation matrix

2. **Extract TPA contact info**
   - Look for:
     - **TPA Name** (e.g. Medi Assist Insurance TPA Pvt. Ltd)
     - **Claims Email** (primary submission address)
     - **Customer Care Email** (for CC)
     - **Toll-free Helpline**
     - **Physical address for claim submission**
     - **Claim Form** — note if Form C (or equivalent) is required

3. **Note key policy terms**
   - Co-payment percentage (e.g. 20% — insured pays this portion)
   - Pre-existing disease waiting period waivers
   - Pre-hospitalization coverage window (typically 30 days before admission)
   - Post-hospitalization coverage window (typically 60-90 days after discharge)
   - Sum insured + any NCB/no-claim bonus enhancement

4. **Determine the registered email on the policy (FROM address)**
   - The policy schedule PDF typically lists only the **mobile number**, not the registered email
   - To find the registered email:
     a. Call `gws_resolve_account()` to list all authorized accounts
     b. Search each Gmail account for policy delivery / renewal emails from the insurer (e.g. `from:care@royalsundaram.in`, `from:customer.services@royalsundaram.in`)
     c. The email inbox that received the policy schedule PDF or renewal confirmation is the registered email
   - If the registered email cannot be determined, default to the user's primary business email (e.g. `ndr@draas.com`)
   - **For the FROM address in the Gmail draft:** send FROM the email address that is registered with the policy, not necessarily the TPA contact or the sender's preferred email. If the policy is in the insured's name but managed by the user, AND the policy mobile is the user's number, the user's business email is the safest default.

## Stage 2 — Locate All Documents in Drive

### Invoices (within coverage window)

Search the patient's medical folder (e.g. `KDR Medical`) for:
- All invoices dated within the pre-hospitalization window (30 days before admission)
- Look for filenames containing: `Invoice`, `Receipt`, `Payment`, `Bill`
- Pattern match: `[Date]_[PatientInitials]_[Description]_Invoice/Receipt_*`

Also check the `Invoices` subfolder if one exists.

### Medical Reports

Search for all diagnostic/consultation reports within the same window:
- OPD / consultation notes (look for doctor names matching the treating team)
- Lab test reports (blood, urine, pathology)
- Imaging reports (X-ray, CT, MRI, Echo, ECG, audiometry)
- Pre-anesthesia evaluation reports
- Discharge summary (after hospitalization)
- Any medical records compilation document

### Hospitalization Documents (for cross-reference in claim email)
- Discharge summary
- Itemized hospital bill
- Payment receipts (credit card, cash, bank transfer)
- Discharge clearance certificate
- Insurance authorization / pre-auth letter from TPA

### Policy Document
- Search for the policy wording PDF (typically named `[Insurer]-[Plan]_[patient]_[policy-number]_[year].pdf`)

## Stage 2b — OPD / ongoing-medication invoices (file + insurer-direct reimbursement guidance)

For pharmacy/medicine invoices from ongoing treatment (not tied to a hospitalization claim):

1. **Deskew & rebuild the scan first** — scanned invoices arrive slightly skewed (0–2°). Run `scripts/deskew_invoice_pdf.py` (300 dpi render → Hough/line-detection angle with projection-profile fallback → rotate → rebuild via img2pdf with JPEG q≈92). PNG pages bloat to ~10 MB; JPEG keeps ~3–4 MB at legible 300 dpi.
   **Pitfall:** `cv2.minAreaRect` reports 0° on whole-page invoice blobs; vision-model tilt estimates are unreliable at sub-degree level (direction flip-flops CW vs CCW). Trust two CV methods that agree; verify by re-rendering one page and asking vision "is it straight now".
2. **Rename** per user convention: `YYYYMMDD_Patient_Description.pdf` (underscores only, no spaces/em-dashes).
3. **Upload** to the patient's Medical folder → **Invoices subfolder** (find via Drive query `name contains '<Patient>'`; e.g. `Murjani Medical Invoices`).
4. **Append rows to the patient's invoice-index spreadsheet** (e.g. "Index of <Patient> Medical Expepnse Invoices" — keep the original mis-spelling; never rename). Columns: `Date of Invoice (MM/DD/YYYY) | Institute | Invoice Type | Amount | Reimbursed? | To be Claim | Additional Notes`; To-be-claim uses `=if(NOT(E{r}),D{r},0)`. The sheet ends with an empty row then a TOTAL row of SUM formulas — **insert data rows before TOTAL** (`spreadsheets().batchUpdate` → `insertDimension`, startIndex = 0-based empty-row index), write values with `USER_ENTERED`, then extend the TOTAL SUM ranges (`sum(D2:D26)` / `sum(F2:F26)` style) and verify with both `valueRenderOption=FORMULA` and `FORMATTED_VALUE` readbacks.
5. **Reimbursement-guidance email (draft only — never send):**
   - Recipients = insurer addresses from the previous intimation thread (Star Health: `reimbursement.blr@starhealth.in` + `Customer.NEFT@starhealth.biz`; Cc the family member's email used in that thread). If no named person appears, treat the insurer's reimbursement desk as "the coordinator we wrote to earlier".
   - Body: cite policy number + prior intimation ref (e.g. CIR/2026/141133/1527709); small HTML table of the invoices; attach the deskewed PDF; ask (1) is this OPD/medicine class reimbursable under the policy, (2) if yes the claim procedure (forms/documents/channel/timelines), (3) club with existing claims or register separate intimations.
   - **Do not assert claimability.** Standard hospitalisation floaters exclude routine OPD medicine; the email asks the insurer to confirm and advise the route.
   - Build with raw Gmail API (`build_service('gmail','v1')`), same pattern as Stage 6.

## Stage 2c — Patient Assistance Program (PAP) / Drug Manufacturer Infusion Confirmation

For patients receiving medication through manufacturer Patient Assistance Programs 
(e.g. MSD/KIRAN Keytruda PAP via Medybiz Pharma). This is a **separate workflow** 
from TPA/insurance claims — the correspondence goes to the PAP administrator, not the insurer.

### Key differences from TPA claims

| Aspect | TPA Claim | PAP Infusion Confirmation |
|--------|-----------|---------------------------|
| **Recipient** | TPA / insurer (e.g. Star Health) | PAP administrator (e.g. Medybiz Pharma) |
| **Email account** | Usually google-draas (ndr@draas.com) | May be google-ahfl (ndr@ahfl.in) — **check thread history first** |
| **Document** | Invoices, reports, claim forms | Signed Infusion Confirmation Form + Prescription |
| **Goal** | Reimbursement | OTP for next cycle delivery + drug supply |
| **Thread** | New email each claim | Persistent ticket thread (e.g. Ticket No: 7027) |

### Determine which Google account

PAP correspondence often uses a different email than the user's primary business account. 
Before drafting, check:
1. `gws_resolve_account()` to list all authorized accounts
2. Search each account for the PAP's ticket/subject
3. The account that received prior PAP emails is the correct one to send FROM

### Determine the CC list

Extract from a message in the existing thread using `format='full'` and reading headers:
```python
headers = {h['name'].lower(): h['value'] for h in msg['payload']['headers']}
cc = headers.get('cc', '')
```
Established CC participants (e.g. patient family, prescribing doctor, internal team) 
must stay on the reply. Established pattern for Charitra Murjani / Medybiz:
`charitrakamath@gmail.com, rmurjani@gmail.com, anniekbaa@gmail.com, rnr@draas.com`

### Build the reply-all draft with PDF attachment

Always use the **raw Gmail API** (`build_service('gmail', 'v1')`) — gws_skill_bridge 
does not support attachments or In-Reply-To threading.

**Workflow:**

1. **Find the most recent message in the thread to reply to** — extract its `Message-ID` header
2. **Set threading headers:**
   ```python
   msg['In-Reply-To'] = '<most_recent_message_id@domain>'
   msg['References'] = '<prior_reply_id@domain> <most_recent_message_id@domain>'
   ```
3. **CC list** must exactly match the established thread CCs
4. **Attach the PDF** as MIMEBase/application-pdf with encode_base64
5. **Create draft** via `gmail.users().drafts().create()`

**Working pattern:**
```python
from tools.gws_auth import build_service
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import email.encoders, base64

gmail = build_service('gmail', 'v1', service_name='google-ahfl')  # or correct account

msg = MIMEMultipart('mixed')
msg['To'] = 'papadministrator@example.com'
msg['Cc'] = 'patientfamily@gmail.com, doctor@gmail.com, internal@draas.com'
msg['From'] = 'Sender Name <ndr@ahfl.in>'
msg['Subject'] = 'RE : [Ticket No:XXXX] Original Subject'

# Threading — extract from the email being replied to
msg['In-Reply-To'] = '<original_message_id@outlook.com>'
msg['References'] = '<prior_reply@mail.gmail.com> <original_message_id@outlook.com>'

# Body
text_part = MIMEText(body_text, 'plain', 'utf-8')
msg.attach(text_part)

# Attach PDF
with open('/path/to/document.pdf', 'rb') as f:
    att = MIMEBase('application', 'pdf')
    att.set_payload(f.read())
    email.encoders.encode_base64(att)
    att.add_header('Content-Disposition', 'attachment', filename='filename.pdf')
    msg.attach(att)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
draft = gmail.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
```

**Before creating, delete any existing draft with the same subject** to avoid duplicates:
```python
drafts = gmail.users().drafts().list(userId='me').execute()
for d in drafts.get('drafts', []):
    draft_data = gmail.users().drafts().get(userId='me', id=d['id'], format='minimal').execute()
    subj = next((h['value'] for h in draft_data['message']['payload']['headers'] if h['name'] == 'Subject'), '')
    if 'Ticket No:7027' in subj:  # match your ticket number
        gmail.users().drafts().delete(userId='me', id=d['id']).execute()
        break
```

### Verify draft threading

After creation, verify the draft will merge into the existing thread:
- `gmail.users().drafts().get(id=DRAFT_ID)` — check threadId matches the original thread
- If threadId is new, the In-Reply-To/References headers were wrong — delete and rebuild

### Key pitfall — Outlook Message-ID format

PAP administrators often use Microsoft/Outlook mail servers. Their Message-IDs look like:
`<SE3PR04MB94560DF7767F005B49A97D228DAD2@SE3PR04MB9456.apcprd04.prod.outlook.com>`
These are valid — include them verbatim in In-Reply-To and References.

Gmail uses a different format:
`<CAFP-FxdO4XT2RJuPDD8Jo_Ku7KCmme_xhSQCQMxVG2noXjj-3A@mail.gmail.com>`
Both formats work together in the References chain — Gmail handles cross-provider threading.

### When the form scan is rejected (cutoff/incomplete)

The PAP administrator may ask to "share the full image" if the previous submission
had a cropped/partial scan. The response workflow:
1. Re-scan the physical form — ensure the entire document is visible
2. Upload to Drive TMP with naming convention: `YYYYMMDD_Patient_Infusion_Confirmation_Full.pdf`
3. Reply-all on the existing ticket thread with the corrected attachment
4. Apologise briefly, state this is the complete version
5. Request: (a) urgent processing, (b) OTP sharing, (c) no delay to the scheduled infusion

### Reference file

For Charitra Murjani's specific Medybiz/KIRAN PAP details (SPS ID, ticket number,
CC list, scheduling pattern, phone numbers), see `references/charitra-star-health.md` 
under the "Medybiz / KIRAN Patient Access Program" section.

Use `pymupdf` to read each invoice PDF and extract the amount:
```python
import pymupdf, re
doc = pymupdf.open(stream=content)  # or from file
text = ''
for page in doc:
    text += page.get_text()
doc.close()

# Find amounts (handle various formats)
# Look for "Amount in words" or "Total" / "Net Amt" / "Paid Amt" lines
amounts = re.findall(r'[₹]\s*[\d,]+\.?\d*', text)
```

**Pitfall — amounts may be in "words" section** (e.g. "Fifteen Thousand Seven Hundred Thirty Rupees Only" = ₹15,730). Extract from both the numeric total line AND the words line. Cross-verify.

**Pitfall — PDF text extraction may be incomplete** due to column-based layouts. The individual line items may appear in different order than shown on the visual invoice. Always check the "Bill Total", "Net Amt.", "Paid Amt." row for the final figure.

**Pitfall — policy discounts** (e.g. Manipal Hospital applies a policy discount before final paid amount). Report the GROSS amount and the NET PAID amount separately. The claim amount is the net paid by the patient.

## Stage 4 — Compile & Validate

### Build the expense summary table

```
# | Date       | Provider       | Particulars                       | Amount
--|------------|----------------|-----------------------------------|--------
1 | 09/07/2026 | Trustwell Hosp | Wax Removal + PTA                 | ₹2,740
2 | 09/07/2026 | Trustwell Hosp | Lab Tests + OP Consultation       | ₹15,730
--|------------|----------------|-----------------------------------|--------
  |            | **Total**      |                                   | **₹45,010**
  |            | Co-pay (20%)   |                                   | ₹9,002
  |            | **Net Expect** |                                   | **₹36,008**
```

### Validate each document
- Is it dated within the coverage window (30 days pre-admission)?
- Is the expense directly related to the condition treated (diagnosis match)?
- Does the invoice have patient name matching the insured?
- Is there a corresponding medical report for each diagnostic test?
- Are prescriptions attached for pharmacy bills?

**Pitfall — non-standard tests need justification:** Tests like CT Pulmonary Angiogram (pre-op for ear surgery) or autoimmune panels (ANA, Anti-CCP, ANCA) are not standard pre-operative workups for otosclerosis/stapedotomy. These may be queried by the TPA. If possible, include a brief clinical justification from the ordering doctor. Include them in the claim regardless — the TPA will decide admissibility.

### Determine the registered email (FROM address)
The policy schedule PDF typically lists only the **mobile number**, not the registered email. To find the registered email:

1. Call `gws_resolve_account()` to list all authorized Google accounts
2. For each account, search Gmail for policy delivery/renewal emails:
   - `from:care@[insurer].in` or `from:no-reply@[insurer].in`
   - Search the policy number (e.g. `LLA0016946000107`)
3. The email inbox that received the policy schedule PDF or renewal confirmation is the registered address
4. Set the Gmail draft's FROM header to this email address, not the user's preferred email

**Fallback:** If the registered email cannot be determined from any mailbox, the safest default is the user's primary business email — especially if the policy mobile number matches the user's mobile number (indicating the user manages the policy). Add a note in the output saying the registered email couldn't be verified from the policy documents.

### Handling newly discovered invoices mid-process
If the user sends an additional invoice after the draft is already built:

1. **If the draft has NOT been sent:** Rebuild the complete draft with the new invoice included. Delete the old draft first. Update the claim total.
2. **If the draft HAS been sent:** Create a supplementary/follow-up draft (Subject: "Supplementary documents — [patient] — [policy] — Re: [original claim ref]"). Do NOT rebuild the original — the TPA already has it.
3. Always upload the new invoice to Drive TMP with a proper descriptive filename before attaching.

### Coordinating missing financial documents
When bank account details (cancelled cheque, IFSC, account number) are missing:

1. Search Google Contacts for the person who handles financial documents (e.g. "Eshwari" + phone)
2. Draft a WhatsApp message requesting the specific document (cancelled cheque from insured's account, any account)
3. Include context: insurer name, policy number, TPA name, reason (NEFT reimbursement)
4. When the document arrives, upload to Drive TMP and add to the draft

### Identify gaps (critical)
Standard KYC / mandatory docs the patient must provide:
1. **Claim Form (Form C)** — filled and signed by the insured
2. **PAN Card** copy of insured
3. **Aadhaar Card** / Photo ID of insured
4. **Canceled Cheque** or Bank Passbook copy (for NEFT reimbursement)
5. **Policy Document** copy (available in Drive)

Without these, the TPA will not process the claim.

## Stage 5 — Delegate Review (optional but recommended)

For complex claims with 20+ documents, delegate to a sub-agent for review before drafting:

```
delegate_task(
    goal="Review all medical documents for [patient]'s claim submission to [TPA].",
    context="""[Full details of all documents, amounts, dates, providers, policy info, TPA info]...
    Please verify:
    1. Are all documents sufficient for a comprehensive claim?
    2. What documents are missing?
    3. Are all reports properly linked to the pre-operative period?
    4. Any duplicates or exclusion-worthy items?
    5. Is the total correct?
    """
)
```

## Stage 5b — Fill the Claim Form (Form C / TPA Claim Form)

The TPA's claim form (usually called "Form C", "Reimbursement Claim Form", or similar) is typically a **scanned PDF image** without fillable AcroForm fields. Never attempt pixel-perfect text overlay on a scanned image — the result is illegible and misaligned.

### Approach A: HTML+CSS Replica (Preferred — User-Validated)

The user's preferred approach: recreate the scanned form as an HTML+CSS page that **visually matches the original** (character boxes, checkboxes, section layout) with all data pre-filled, then convert to PDF via WeasyPrint.

**Workflow:**

1. **Convert the scanned claim form PDF to images** for reference:
   ```bash
   pdftoppm -png -r 300 input.pdf /tmp/claim_form_page
   ```

2. **Analyze each page** with `vision_analyze()` — ask for an extreme-detailed description of every field, label, checkbox, table, and section position.

3. **Build the HTML replica** using CSS character boxes for text fields:
   ```css
   .cbox {
     display: inline-flex;
     align-items: center;
     justify-content: center;
     width: 9pt;
     height: 11pt;
     border: 0.5pt solid #222;
     font-size: 7.5pt;
     font-family: 'Courier New', monospace;
     text-transform: uppercase;
     vertical-align: middle;
     margin: 0;
     padding: 0;
   }
   .cbox.empty { border-color: #888; }
   ```

4. **Fill every field** with the actual data using character boxes:
   ```html
   <span class="lbl">Policy No.:</span>
   <span class="cbox">L</span><span class="cbox">L</span><span class="cbox">A</span>...
   ```

5. **Checkboxes** — use a filled/unfilled box pattern:
   ```css
   .chk-box { width: 9pt; height: 9pt; border: 0.8pt solid #000; display: inline-flex; }
   .chk-box.filled { background: #000; color: #fff; }
   .chk-box.filled::after { content: "✓"; }
   ```

6. **Convert to PDF** using WeasyPrint:
   ```python
   from weasyprint import HTML
   HTML(filename=filepath).write_pdf(output_pdf_path)
   ```
   Install with `uv pip install weasyprint`.

7. **Upload the result** to Drive TMP and attach to the claim email.

**Layout rules for the HTML replica:**
- Use `font-family: 'Courier New', Courier, monospace` for character boxes (matches mono-width typed forms)
- Use `font-family: Arial, Helvetica, sans-serif` for labels and section titles
- A4 page size: `210mm × 297mm` with `12-14mm` padding
- Add `@media print { -webkit-print-color-adjust: exact; }` so filled checkboxes render in print/PDF
- Section labels on the right can be done with `writing-mode: vertical-rl` (the user hasn't needed these so far — they're decorative)

**Critical: Number formatting in character boxes**
- Do NOT place commas (`,`) in their own character boxes. When a number doesn't fit neatly into the available boxes, omit commas entirely and fill only the digits.
- Right-align when there are extra boxes: leave the leftmost box(es) empty, fill remaining with digits.
- Example: Sum Insured ₹1,50,00,000 in 9 boxes → `[_][1][5][0][0][0][0][0][0]`, NOT `[1][5][0][,][0][0][,][0][0][0]`.
- The user explicitly rejected comma-in-character-box: "just fill in the digits."

### Approach B: Clean Typed PDF (Alternative)
When the user doesn't need the form to look exactly like the original, create a professional typed PDF:
1. Use pymupdf's `page.insert_text()` with a built-in font
2. Include all sections from the original form
3. Note any fields left blank (e.g. "PAN attached separately", "Awaiting cancelled cheque")
4. Upload to Drive TMP and attach alongside the original blank form

### Locating the blank Claim Form
- Check the TPA's website (e.g. `www.mediassist.in` → Customer Zone → Forms)
- Call the TPA helpline and ask them to email the form
- Check if a previous claim form for the same insurer already exists on Drive
- If the form has a different insurer's name, it's the wrong one — get the correct insurer's form

### What to leave blank (user adds manually)
1. Signature — physical signature of insured required
2. PAN — if PAN card is attached separately, note this on the form

### Filling Bank Details from Cancelled Cheque

When the user sends a cancelled cheque image:

1. **Rotate and straighten** the image using PIL:
   ```python
   from PIL import Image
   img = Image.open(cheque_path)
   rotated = img.rotate(90, expand=True, fillcolor='white')  # adjust angle as needed
   rotated.save(straightened_path, quality=95, dpi=(300,300))
   ```

2. **Convert to PDF** (the user wants PDF, not JPEG):
   ```python
   rotated.save(pdf_path, 'PDF', resolution=300)
   ```

3. **Read the text** with `vision_analyze()` to extract:
   - Account holder name (e.g. "KANTA RANKA")
   - Account number (e.g. "4447921904")
   - Bank name & branch (e.g. "Kotak Mahindra Bank, Infantry Rd")
   - IFSC code (e.g. "KKBK0008059")

4. **Update the claim form HTML** with the extracted bank details:
   - Replace empty placeholder boxes with filled character boxes
   - Remove "(Awaiting cancelled cheque)" text

5. **Upload both** the cheque PDF and the updated claim form to the Patient's Medical folder on Drive.

## Stage 6 — Draft the Claim Email

### Always use `draft_create` (never send directly)

Create a draft in the user's work Gmail using the raw Gmail API. Use `build_service('gmail', 'v1', service_name='...')` — the gws_skill_bridge does NOT support creating drafts with complex MIME or attachments.

For the full attachment workflow reference, see `references/drive-files-to-gmail-attachment.md`.

### Email body format: HTML (user preference)

The user prefers a **rich HTML email body** with styled tables, not plain text. Build the email body as an HTML string and attach it as a `MIMEText(..., 'html')` part alongside the `MIMEMultipart('alternative')` wrapper.

**Structure the HTML email with:**
- A colored header block (dark navy `#1a3a5c`) with claim title, policy, and hospital
- Patient & Policy Details table
- Hospitalization Details table
- Expense table with color-coded hospital groupings (e.g. light blue `#eef4fb` for each hospital's section)
- Subtotals per hospital, bold grand total (white-on-navy)
- No co-pay/NCB mentioned in the email — just state the total claimed amount. Let the insurance calculate co-pay.
- Attachment checklist as a numbered table
- Professional footer with sender name, email, phone

**CSS for the email:**
```html
<style>
  body { font-family: Arial, sans-serif; font-size: 10pt; color: #222; }
  .header { background: #1a3a5c; color: #fff; padding: 14px 20px; }
  .section-title { font-size: 10pt; font-weight: bold; color: #1a3a5c; border-bottom: 2px solid #1a3a5c; }
  table.invoice-table { width: 100%; border-collapse: collapse; }
  table.invoice-table th { background: #e8edf2; border: 1px solid #ccc; }
  table.invoice-table td { border: 1px solid #ccc; }
  .subtotal { background: #f5f7fa; font-weight: bold; }
  .grand-total { background: #1a3a5c; color: #fff; font-weight: bold; }
</style>
```

**Building the MIME:**
```python
msg = MIMEMultipart('mixed')
msg['To'] = 'claims@mediassistindia.com'
msg['Cc'] = 'customercare@mediassistindia.com'
msg['From'] = 'ndr@draas.com'
msg['Subject'] = '...'

msg_alt = MIMEMultipart('alternative')
msg_alt.attach(MIMEText(html_body, 'html'))
msg.attach(msg_alt)
```

### Key communication preferences for this user
- **Do NOT mention co-payment percentage or expected net amount** in the email. State only the total claimed amount. The user's position: "Let them tell us that 20% is scope and so they are reimbursing the balance. Let it be on the insurance to do that. Let us not put that in the email."
- **Do NOT mention NCB (No Claim Bonus)** separately — let the insurance calculate their own numbers.
- Use formal but direct language. No filler, no apologies.
- List all invoice amounts with proper ₹ separators in the email table (commas in email are fine — the no-commas rule only applies to character boxes in the claim form).
- Include hospital subtotals (e.g. Trustwell Subtotal, Manipal Subtotal) so the total is clearly traceable.
- **Direct-claim framing (25-Aug-2026 user rule):** when the user wants reimbursement for ongoing / post-hospitalisation expenses, submit a DIRECT CLAIM — never write "please advise whether claimable". NDR's explicit position: *make a claim and let them refuse it.* Frame the expenses under the applicable benefit (e.g. ongoing post-hospitalisation treatment), state the total claimed, cite policy + prior intimation refs, attach invoices + prescriptions + discharge summaries, and ask them to register the claim and return a claim number. A refusal is a legitimate outcome — it becomes the basis for a Stage-7 escalation. See `references/charitra-star-health-claim.md` for the worked example.

### Adding file attachments from Drive to the draft

You CAN attach files programmatically when creating a draft. The approach:

1. Download each PDF from Drive via `drive.files().get_media(fileId=ID).execute()`
2. Build a `MIMEMultipart('mixed')` message with:
   - `MIMEText` for the email body (plain text)
   - `MIMEBase` for each PDF attachment, using `email.encoders.encode_base64()`
3. Upload via `gmail.users().drafts().create()`

**Working pattern:**

```python
from tools.gws_auth import build_service
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import email.encoders, base64, os

drive = build_service('drive', 'v3', service_name='google-draas')
gmail = build_service('gmail', 'v1', service_name='google-draas')

# Download files from Drive
temp_dir = '/opt/data/claim_docs/'
os.makedirs(temp_dir, exist_ok=True)
drive_files = {
    'file_id_123': '01_Invoice_Description.pdf',
    'file_id_456': '02_Report_Description.pdf',
}
for fid, fname in drive_files.items():
    content = drive.files().get_media(fileId=fid).execute()
    with open(os.path.join(temp_dir, fname), 'wb') as f:
        f.write(content)

# Build MIME mixed message
msg = MIMEMultipart('mixed')
msg['To'] = 'claims@mediassistindia.com'
msg['Cc'] = 'customercare@mediassistindia.com'
msg['From'] = 'Sender Name <sender@email.com>'
msg['Subject'] = 'Reimbursement Claim — [subject]'

# Plain text body
text_part = MIMEText(body_text, 'plain', 'utf-8')
msg.attach(text_part)

# Attachments
for fname in sorted(os.listdir(temp_dir)):
    filepath = os.path.join(temp_dir, fname)
    with open(filepath, 'rb') as f:
        att = MIMEBase('application', 'pdf')
        att.set_payload(f.read())
        email.encoders.encode_base64(att)
        att.add_header('Content-Disposition', 'attachment', filename=fname)
        msg.attach(att)

# Encode and create draft
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw}}
).execute()
```

**Before creating a new draft with the same subject**, delete the old draft first:
```python
drafts = gmail.users().drafts().list(userId='me').execute()
for d in drafts.get('drafts', []):
    draft_data = gmail.users().drafts().get(userId='me', id=d['id'], format='minimal').execute()
    msg_data = draft_data['message']
    subject = next((h['value'] for h in msg_data['payload']['headers'] if h['name'] == 'Subject'), '')
    if 'POLICY_NO' in subject:  # match your policy number
        gmail.users().drafts().delete(userId='me', id=d['id']).execute()
        break
```

**Important:** Draft attachment adds real PDFs to the Gmail draft — they appear as actual files in the Drafts folder, not as links. The user can open the draft in Gmail and see all files already attached, ready to review and send.

- **When NDR says "make a claim", DO NOT draft an advisory email asking whether an expense is claimable.** Frame it as a direct reimbursement claim under the applicable category (e.g. ongoing post-hospitalisation treatment), attach the full supporting set, state the amount claimed, and ask for claim registration + a claim number. NDR's explicit instruction (Aug 2026): *"make a claim and let them refuse it"* — a clean refusal is a usable basis for escalation (Stage 7); a hedged question is not.
- **Ongoing OPD / monthly medicine purchases** usually fall outside standard hospitalisation floaters (e.g. Star Super Surplus). When NDR wants them claimed, anchor to ongoing treatment: cite the latest hospitalisation(s) + discharge summaries, attach contemporaneous prescriptions + infusion confirmations alongside the pharmacy invoices, and state the claim as post-hospitalisation treatment. Expect possible refusal (dates may fall outside the standard 60–90 day post-discharge window) — be ready to escalate.
- **Charitra Murjani (Star Health):** use `references/charitra-star-health-claim-template.md` for policy numbers, the BLR reimbursement desk contacts, Drive filing locations, and the invoice index sheet.

### Email structure (comprehensive — TPA should never need to come back)

1. **Header**: Re: claim type, patient details, policy number, hospital, dates
2. **Patient & Policy Info block**: Name, DOB, Policy No, Insurer, Procedure, Surgeon, Hospital, Admission/Discharge dates, Pre-auth ref
3. **Expense Summary Table**: Ordered list with date, provider, item description, amount. Show total, co-pay, net expected.
4. **Document Attachment Checklist**: Group documents into categories (A: Invoices, B: Diagnostic Reports, C: Consultation Records, D: Hospitalization docs for cross-ref, E: KYC/Policy docs). Number each item. Mark which are attached and which need to be added manually by the user.
5. **Closing**: Payment instruction, contact info.

### Sender name in signature
Use the user's relationship to the insured (e.g. "Son of Insured") so the TPA understands the relationship.

### User verification
After draft creation, verify it exists:
```python
draft = gmail.users().drafts().get(userId='me', id=DRAFT_ID, format='minimal').execute()
```

Report to the user:
- Draft ID
- Total claim amount
- Number of documents listed
- Which docs are ready to attach vs need manual addition
- Instructions to open Drafts folder, attach files, and send

## Stage 7 — Handle TPA Response & Escalation

After submitting the initial claim, the TPA may respond with:
- A request to **use their portal** to re-submit documents already emailed
- A demand for **original physical documents** (discharge summary, bills, reports)
- A specific **query for a missing document** (cancelled cheque, PAN, Aadhaar)
- A significant **delay** (13+ days) before any substantive response
- An **auto-acknowledgment** promising 24-48 hour response that was not honoured

### 7.1 — When TPA Asks for Portal Re-submission

The TPA may ignore the email submission and direct you to their portal. This is a common procedural gap. Strategy:

1. **Do not re-submit on the portal** — this duplicates effort the policyholder already completed
2. **Reply-all to the thread** including all original participants
3. **Politely but firmly point out** that all documents were submitted via email on [date]
4. **CC the insurance broker/advisor** (e.g. Sudhish K T from Ashwin Bni Insurance for Royal Sundaram policies)
5. **Quote the original submission date and document count** to establish the record

### 7.2 — When TPA Demands Original Documents

TPAs commonly ask for original hospital bills, discharge summary, and reports to be couriered to their office. Response strategy:

1. **Research IRDAI guidelines** before drafting the reply (see `references/irdai-guidelines-original-documents.md`)
2. **Cite** the IRDAI Master Circular on Health Insurance Business (May 2024) — insurers/TPAs must collect documents from hospitals, not from the insured
3. **Offer a compromise**: notarized copies in lieu of originals
4. **State** that original medical records are personal health data the policyholder is entitled to retain
5. **Do NOT courier originals** unless absolutely necessary and the TPA confirms they will be returned

Key IRDAI references to cite:
- **IRDAI/HLT/CIR/PRO/84/5/2024** (29 May 2024) — Master Circular on Health Insurance Business
- **IRDAI/PP&GR/CIR/MISC/117/9/2024** (5 Sep 2024) — Master Circular on Protection of Policyholders' Interests

### 7.3 — TPA Delay Escalation Framework

When the TPA misses their promised response timeline:

1. **Send a reminder** after 7 business days if no response (document the date)
2. **After 13+ days without substantive response**, escalate:
   - **Level 1:** Reply to the thread, CC the insurance broker/advisor, express disappointment
   - **Level 2:** CC the insurer directly (e.g. `care@royalsundaram.in` for Royal Sundaram)
   - **Level 3:** Mention IRDAI grievance portal (`bimabharosa.irdai.gov.in`) if the delay continues
   - **Level 4:** Insurance Ombudsman (award limit: ₹50 lakhs; binding on insurer up to ₹30 lakhs)
3. **Always keep the insurance intermediary (broker/advisor) in the loop** — they have commercial leverage with the TPA

### 7.3b — Responding to TPA Queries Requesting a Specific Document

The TPA/insurer may send a query email asking for a specific missing document (cancelled cheque, PAN, ID proof, invoice). This is a **different workflow** from user-initiated escalation — the response is cooperative, not confrontational.

**IMPORTANT — Auto-generated emails redirect to a different contact (validated 2026-08-27, Kanta Ranka / Royal Sundaram):** The query email may come from an auto-generated address (e.g. `Healthclaims.support@royalsundaram.in`) that says "Please do not reply to this email address." The attached query PDF contains the actual contact email (e.g. `customer.services@royalsundaram.in`). When this happens:

1. The reply is a **FRESH email** to the advertised contact address — NOT a threaded reply to the auto-generated sender's thread. Since the auto-generated email is not monitored, threading into it serves no purpose.
2. Extract the query PDF with `pdftotext` to get the claim number, policy number, and the correct contact email.
3. CC the broker/advisor and any other recipients from the original correspondence.
4. Include ALL claim details in the body (claim number, policy number, patient name, hospital, dates) so the insurer can process without cross-referencing.
5. Do NOT set In-Reply-To or References from the auto-generated email — this is a standalone forward to a new address.

**Workflow:**

1. **Find the query email** — search Gmail by sender domain (`q='from:healthclaims.support@royalsundaram.in'`) or subject keywords (`q='Query' AND 'Kanta'`). Query emails typically have a reference number in the subject (e.g. `Query IH26005962CSL01`) and a PDF attachment with the query letter.

2. **Identify what document is requested** — check the email body or the attached query PDF. Common asks: cancelled cheque for NEFT, PAN, Aadhaar, missing invoice.

3. **Locate the document on Drive first** — it may already exist from a prior claim submission. Search Drive with `q="name contains 'PatientInitial' and name contains '<document keyword>'"` (e.g. "cheque" or "cancelled"). Check the patient's Medical folder, Invoices subfolder, and TMP folder. The cancelled cheque for Kanta Ranka lives at ID `1wa_DJn1Z_d-jY6MsXpxjqJDPqU2ggvzA` — `20260716_KDR_Cancelled_Cheque_Kotak_4447921904.pdf`.

4. **Check who the original query was sent To/CC** — the broker/advisor on the original thread (e.g. Sudhish KT / sudhish@eurydice.co.in for Royal Sundaram) should stay on the reply.

5. **Determine the reply-To address** — follow the email's instruction: "Please do not reply to this email address. For queries, contact us at care@insurer.in." Reply goes to the contact address given, NOT the sender's address.

6. **CC list** — keep the broker/advisor from the original thread + add any new recipient the user names. **Pitfall — voice dictation merges name and email** (e.g. "Sarthakadmin3.blr@draas.com" = Sarthak at admin3.blr@draas.com). Resolve the actual email from thread headers or the `contact_resolver` tool, not the merged string.

7. **Download the document** — `drive.files().get_media(fileId=ID).execute()` → save to `/tmp/`.

8. **Create threaded draft** via raw Gmail API (`MIMEMultipart('mixed')`):
   - Body: "Please find attached the [document] as requested in Query [Ref]. Kindly process the claim accordingly."
   - `In-Reply-To` + `References` = query email's Message-ID (for threading)
   - To = contact address from step 5; Cc = broker + new recipients
   - Subject = `Re: [original query subject]`
   - Attach the downloaded PDF as MIMEBase part

9. **Verify** — `drafts().get()`: check To, Cc, threading, attachment present in payload parts.

10. **Report** — draft link in Drafts folder, recipient list, attachment name.

### 7.4 — Drafting the Escalation Reply

**Recipients:** Reply-all to the thread — include the TPA, insurer, broker/advisor, and internal team

**Key points to cover:**
1. Original submission date and what was submitted
2. TPA's promised response timeline vs actual response time
3. The specific frustration (portal re-submission, original documents demand)
4. IRDAI guideline citations (see above)
5. Request for the broker/advisor to intervene

**Template email structure:**
```
Subject: Re: [Original subject]
To: TPA customer care / claims
CC: Broker/advisor, internal team

Dear Team,

This is in response to your email dated [date].

1. I submitted the complete claim with all supporting documents 
   via email on [original date]. Every bill, report, and the 
   claim form was attached to that email.

2. Your team took [X] days to respond — only after I sent a 
   reminder on [reminder date]. Your auto-acknowledgment promised 
   a response within 24 to 48 hours. That timeline was not met.

3. Now you are asking me to [portal re-submission / send originals]. 
   This is merely a procedural hurdle. I have already provided 
   everything requested.

[If originals demanded:]
Per the IRDAI Master Circular on Health Insurance Business 
(Ref: IRDAI/HLT/CIR/PRO/84/5/2024, dated 29 May 2024), insurers 
and TPAs must collect documents from hospitals directly, not 
from the insured. The Master Circular on Protection of 
Policyholders' Interests (Ref: IRDAI/PP&GR/CIR/MISC/117/9/2024, 
dated 5 September 2024) reinforces this.

There is no IRDAI requirement mandating that a policyholder must 
submit original medical records. I am willing to provide 
notarized copies in lieu of originals.

[Name] — I request you to kindly step in and resolve this matter.

Regards,
[Nishant Ranka]
```

## Pitfalls

- **pymupdf available only via Hermes venv:** The system python3 does NOT have pymupdf installed. Use `/opt/hermes/.venv/bin/python3` (or `uv run python3`) for all pymupdf operations.
- **Scanned claim forms have no fillable fields:** The TPA's claim form PDF is typically a scanned image (page has images but no AcroForm widgets). pymupdf `page.widgets()` returns empty. Use the HTML+CSS replica approach instead (see Stage 5b).
- **Multiple coinsurers/co-pay:** If the patient has a top-up plan or co-insurance, the claim may need to be filed with the primary insurer first. Confirm the claim sequence.
- **Pre-auth already issued for hospitalization:** The pre-operative claim is a separate reimbursement even if cashless was used for the main hospital bill. The pre-auth letter amount is for hospitalization only — pre-op out-of-pocket expenses need a separate reimbursement claim.
- **Policy discount on invoices:** Some hospitals (like Manipal) apply a "policy discount" reducing the gross amount. The net paid amount is what the patient actually paid and should be claimed.
- **Attaching files from Drive to Gmail drafts:** The gws_skill_bridge does NOT support attachments, but the raw Gmail API does. Download files from Drive via `build_service('drive', 'v3').files().get_media(fileId=ID).execute()`, build a `MIMEMultipart('mixed')` with `MIMEBase` attachments, and create the draft via `gmail.users().drafts().create()`. See Stage 6 for the full working pattern. Validated on 16 July 2026 with 25 PDFs totaling ~20 MB.
- **File IDs needed for Drive downloads:** When downloading PDFs from Drive by file name, first search for the exact file to get its ID, then download by ID. Hardcoded IDs guessed from filenames will 404.
- **Amount extraction from PDFs:** Text from table-based invoices may have line items and totals in hard-to-parse positions. Always look for "Amount in words", "Bill Total", "Net Amt.", "Paid Amt." rows and cross-verify with the spelled-out amount.
- **Old draft blocking new one:** If a previous draft with the same subject exists, the new one gets created alongside it — you end up with two (or more) drafts with nearly identical content. Always list existing drafts, match by subject, delete the old one, then create the new one. See Stage 6 for the delete-then-create pattern.
- **Registered email on policy not in PDF:** The policy schedule PDF typically does NOT show the registered email address, only the mobile. Search all authorized Gmail accounts (`gws_resolve_account()` then `build_service('gmail', 'v1')` each) for policy delivery emails from the insurer. The inbox that received the policy confirmation is the registered email. Default to the user's primary business email if not found.
- **Verify Sum Insured from the policy schedule, not memory:** The sum insured I recorded in memory (₹27L) was wrong — the actual is ₹1.5 Crore. Always read the policy schedule PDF or the user's policy reference document to get the actual sum insured, co-pay, and NCB amounts. Do not rely on values remembered from prior conversations. Create a file listing reference (`references/<patient>-<insurer>-claim-template.md`) with verified values from the policy document after confirming with the user.
- **Commas in character-box fields:** Never put commas (`,`) in individual character boxes on the claim form. When a number is too long to fit with commas, omit the commas entirely and fill with digits only. Right-align when there are extra boxes.
- **Cancelled cheque image processing:** The user may send a photo of a cancelled cheque taken from their phone. Use PIL to rotate/straighten, convert to PDF, upload to the patient's medical folder in Drive, extract bank details via OCR, and fill them into the claim form. The user expects the cheque to be properly oriented and in PDF format.
- **WeasyPrint for HTML→PDF conversion:** Install via `uv pip install weasyprint`. The HTML file must be a complete standalone document with embedded CSS. WeasyPrint renders it at A4 size. Always verify the output by converting a page to PNG and checking with vision_analyze.
- **Vision analysis of scanned PDFs:** The vision_analyze tool cannot read PDFs directly. First convert the PDF page(s) to PNG images using `pdftoppm -png -r 200 input.pdf /tmp/output_prefix`, then analyze the resulting PNG files.
- **Gmail References header extraction from raw MIME:** When extracting the `References` header from a `format='raw'` Gmail message, do NOT use a naive regex search on the decoded MIME text — the raw MIME may contain DKIM signatures and other metadata between headers that get mixed into the References value. Instead, use `format='full'` and access `msg['payload']['headers']` directly (where each header is a `{name, value}` dict). Example:
  ```python
  msg = service.users().messages().get(userId='me', id=MSG_ID, format='full').execute()
  headers = {h['name'].lower(): h['value'] for h in msg['payload']['headers']}
  references = headers.get('references', '')
  in_reply_to = headers.get('message-id', '')
  ```
  This returns clean header values without DKIM or encoding artifacts.
- **All invoice PDFs must be attached individually:** Do not rely on filenames matching a list. After downloading from Drive, check each file exists and is readable before attaching. Missing files cause the email to go out incomplete.

- **Deskew of scanned invoices:** `cv2.minAreaRect` returns 0° on full-page invoice blobs (blob is rectangular), and vision-model tilt estimates are unreliable at sub-degree scale (they contradicted themselves CW vs CCW). Use Hough line detection on the invoice's own table lines (long horizontal edges), falling back to projection-profile variance; two agreeing CV methods is ground truth. Rebuild with img2pdf; convert rendered pages to JPEG quality ~92 first, else the PDF balloons to ~10 MB.
- **Invoice-index sheets end with a TOTAL row:** never append data rows after it — use `insertDimension` (ROWS, before the empty row that precedes TOTAL), write the rows, then extend the TOTAL SUM ranges and re-verify both FORMULA and FORMATTED_VALUE views. A plain append leaves new rows out of the totals (or overwrites TOTAL).
- **"The insurance coordinator we wrote to earlier"** is often just the insurer's reimbursement-desk inbox from a prior intimation email — search Gmail for the insurer's intimation addresses (e.g. `Customer.NEFT@starhealth.biz`, `reimbursement.blr@starhealth.in`) and inspect thread attachments before assuming a named person exists (a WhatsApp-screenshot attachment can be just a logo).
- **Google Sheets may store invoice dates as date serials in some cells and text in others in the same batch** (locale-dependent parse) — visually identical in the formatted view; do not fight it, but keep the same MM/DD/YYYY string format for consistency.

## Related Skills

- `email-drafter` — for general business/personal email drafting (this skill handles insurance-specific emails)
- `ocr-and-documents` — for OCR processing of scanned invoice/report PDFs

## Reference Files

- `references/irdai-guidelines-original-documents.md` — IRDAI guidelines on original documents for health insurance claims, policyholder rights, and citation formats for escalation emails. Load before drafting a reply when the TPA demands original medical records or portal re-submission.
- `references/kdr-royal-sundaram-claim-template.md` — Specific claim template for Kanta Ranka's Royal Sundaram policy
- `references/charitra-star-health-claim.md` — Charitra Murjani's Star Health (Star Super Surplus Floater) policy details, BLR reimbursement desk contacts, and the Jul–Aug 2026 post-hospitalisation medicine claim worked example
- `references/charitra-star-health-claim-template.md` — Charitra Murjani's Star Health policy numbers, BLR reimbursement desk contacts, Drive filing locations, and the invoice index sheet
- `references/drive-files-to-gmail-attachment.md` — Full working pattern for attaching Drive PDFs to Gmail drafts
- `references/charitra-star-health.md` — Charitra Murjani / Star Health specifics: policy numbers, sum insured, reimbursement-desk emails, prior claim intimation, Drive folder + invoice-index sheet IDs, pharmacy (load before any Charitra medical-invoice or Star Health task)
- `scripts/deskew_invoice_pdf.py` — deskew + rebuild a scanned invoice/medical PDF (Hough + projection-profile angle detection, JPEG-page rebuild to keep size sane)
