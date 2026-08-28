# RERA Consultant Collaboration Workflow

Working with external RERA consultants (e.g., RERA Consultants LLP) who manage the registration filing. The agent acts as the project coordinator, not the RERA expert.

## When this applies

- A dedicated RERA consultant firm is engaged (e.g., RERA Consultants LLP, Shwetha Bhavani)
- They provide document checklists, professional certificate templates, and filing guidance
- The agent's role is to collect and organize documents from the project team, not to fill KRERA forms directly

## Workflow

### Phase 1 — Consultant engagement

The consultant sends:
1. **Proposal** — scope of work, fees (typically ₹XX,XXX per project)
2. **Welcome email** with:
   - Document checklist PDF
   - Professional certificate templates (Form-1 CA, Form-2 Architect, Form-3 Engineer)
   - SIS Information Sheet (project details template)
   - Draft proformas (Allotment Letter, Agreement of Sale)
3. **Invoice** for the engagement fee

### Phase 2 — Document sharing via Google Drive

**Preferred pattern:** Share ONE Google Drive folder with the consultant containing all company and project documents. The consultant reviews the folder and sends back a cleaned-up pending list.

```python
# Share the folder with the consultant
folder_link = "https://drive.google.com/drive/folders/XXXX?usp=sharing"
# Send this link to the consultant with:
# "Please find the documents at the link above. We are organizing
#  the remaining documents and will keep adding to this folder."
```

Typical folder structure:
```
Project Name - RERA/
├── Firm - Company Name/
│   ├── PAN Card.pdf
│   ├── GST Certificate.pdf
│   ├── Certificate of Incorporation.pdf
│   ├── AOA & MOA.pdf
│   ├── Udyam Registration.pdf
│   ├── Board Resolution.pdf (if ready)
│   └── Promoter KYC/
│       ├── Nishant Ranka - PAN.pdf
│       ├── Nishant Ranka - Aadhaar.pdf
│       ├── Roshini Ranka - PAN.pdf
│       └── Roshini Ranka - Aadhaar.pdf
├── Project Legal Documents/
│   ├── JDA with Landowners (Registered).pdf
│   ├── GPA (Registered).pdf
│   ├── EC 2003-2026.pdf
│   ├── Tax Paid Receipts.pdf
│   ├── Building Plan Sanction.pdf
│   └── Building Licence.pdf
└── Project Information/
    ├── Google Map Location.pdf
    ├── Site Photos/
    └── Project Brochure.pdf
```

### Phase 3 — Iterative checklist management

The consultant reviews the Drive folder and sends a **revised pending document list** (typically as a PDF or email body). The list has items in different categories:

### Phase 3a — Extracting the checklist from Gmail attachment

The consultant's pending document list is usually sent as a PDF attachment. Extract it:

```python
import base64
from tools.gws_auth import build_service
gmail = build_service('gmail', 'v1')

# Find the latest email with the checklist
results = gmail.users().messages().list(
    userId='me',
    q="from:shwetha@reraconsultants.in subject:'pending documents' Ranka Amber",
    maxResults=1
).execute()

msg = gmail.users().messages().get(
    userId='me', id=results['messages'][0]['id'], format='full'
).execute()

# Find attachment
for part in msg['payload'].get('parts', []):
    if part.get('filename') and part['filename'].endswith('.pdf'):
        att_id = part['body'].get('attachmentId')
        att = gmail.users().messages().attachments().get(
            userId='me', messageId=msg['id'], id=att_id
        ).execute()
        pdf_bytes = base64.urlsafe_b64decode(att['data'])
        with open('/tmp/consultant_checklist.pdf', 'wb') as f:
            f.write(pdf_bytes)
        print(f"Saved: {part['filename']} ({len(pdf_bytes)} bytes)")
```

OCR the attachment with `pdftotext` to get the structured requirement list.

**Company/Promoter category:**
- PAN, GST, COI, AOA, MOA of the company
- Udyam registration
- Board resolution for the project
- KYC (PAN & Aadhaar) of all directors/promoters

**Land/Title category:**
- ADLR Survey Sketch (certified)
- RTC latest years
- Mutation records (before & after conversion)
- Phodi/Hissa Phodi
- Aakarband
- EC (Encumbrance Certificate)
- Tax paid receipts
- JDA / GPA documents

**Project/Approval category:**
- Approved building plan / plan sanction
- Building licence
- RERA registration acknowledgment (from previous projects if relevant)
- Completion certificate / OC (for completed phases)

**⚠️ Agricultural land vs developed plot:** If the project site is in an approved layout / BBMP jurisdiction (not agricultural land), push back on land title documents that apply only to agricultural properties. The RERA consultant will mark those as "keep pending until filing stage" or remove them.

**Blue-highlighted items** in the consultant's PDF list are typically marked as "may not be required for registration" — the consultant will verify with their legal team and remove unnecessary items.

### Phase 4 — Document readiness assessment

Once the consultant's checklist is received, assess each available document against three quality criteria:

| Criteria | What to check via OCR/vision | RERA Requirement |
|----------|-------------------------------|------------------|
| **Signed** | Look for signature image/ink marks at the bottom | Board Resolutions, Letters, Forms need authorized signatory |
| **Self-attested** | Look for "Self-attested" stamp or signature across ID | Aadhaar, PAN copies must be self-attested |
| **Company seal/stamp** | Look for circular/rectangular stamp impression | Letterhead documents need company seal |
| **Letterhead** | Check for company name/logo/address at top | Letters, certificates must be on letterhead |
| **Data filled** | Check that blanks are filled (dates, amounts, names) | Forms 1-3, Allotment Letters, Proformas |

For each item on the consultant's checklist, categorize as:
- **Available ✅** — Signed, attested, sealed, complete
- **Needs Fix 🟡** — Available but missing signature/seal/data
- **Pending ❌** — Not available at all

Build a tracking sheet:

```python
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4')

headers = ['Category', 'Required Document', 'Status', 'File Name',
           'Drive Link', 'Signed?', 'Self-Attested?', 'Sealed?', 'Remarks']
rows = [headers]

# For each requirement from the consultant's list, check if a file exists
# that matches. Compare by name patterns and OCR content.
for item in consultant_list:
    matching_file = find_matching_file(item['name'], available_files)
    if matching_file:
        status = assess_document_quality(matching_file)
        rows.append([...])
    else:
        rows.append([item['category'], item['name'], 'Pending', '', '', '', '', '', 'Not available in folder'])
```

### Phase 4a — Consultant re-review notes

The consultant may reply to shared documents with specific issues found. These often appear in the email body (not just the attachment). For example:
- "Photo is not self-attested" → resend with self-attestation
- "Board resolution date doesn't match" → correct date
- "Form 2 needs architect's seal" → send back to architect
- "Signature differs from ID proof" → get consistent signature

Always read the email body of the consultant's reply — it contains the actionable findings that the attachment alone may not capture. Extract the email body via:

```python
for part in msg['payload'].get('parts', []):
    if part['mimeType'] == 'text/plain':
        data = part['body'].get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            print(body)
```

**Color coding in consultant emails:**
- **Blue highlighted items** in the pending list — "may not be required; keep till filing stage"
- **Red/Highlighted notes** in the email body — specific issues with received documents that need correction

### Phase 5 — Professional certificates (templates → certifiers)

The consultant provides draft templates for certificates that need to be certified by external professionals:

| Certificate | Certifier | To Be Filled By | Data Source |
|------------|-----------|-----------------|-------------|
| Form-1 CA | Company CA | Accounts team (Eshwari) | Project financials, cost estimates |
| Form-2 Architect | Licensed Architect | Engineering team (Anbu) → Architect | Plan sanction, area statement |
| Form-3 Engineer | Licensed Engineer | Engineering team (Anbu) → Engineer | Plan sanction, cost abstract |
| Allotment Letter | Company | Nishant / Coordinator | Project specs, unit details |
| Agreement of Sale | Company/Legal | Nishant / Legal | Project specs, legal structure |

The coordinator sends assignment emails splitting these across the team (Accounts, Engineering, Management) — template in the parent skill under "Phase 0 — Delegate & collect certified documents."

**⚠️ Common blocker:** The CA, Architect, and Engineer often do NOT have the project details to fill their own certificates. The coordinator must fill the data in the templates FIRST, then send the pre-filled drafts to the certifier for review, seal, and signature.

### Phase 6 — Filing

Once all documents are collected from the team and certified by the respective professionals, the coordinator sends everything to the RERA consultant for filing. The consultant:
1. Submits the application online
2. Provides the RERA acknowledgment number
3. Handles any objections/queries from the RERA authority

## Key contacts (confirmed)

| Firm | Contact | Email | Role |
|------|---------|-------|------|
| RERA Consultants LLP | Shwetha Bhavani R M | shwetha@reraconsultants.in | Operations Associate — document checklist, revisions |
| RERA Consultants LLP | Jyothi R | sales@reraconsultants.in | Sales/Proposal |
| RERA Consultants LLP | (Accounts) | — | Sends invoices via Zoho Books |

## Known pitfalls

- **Consultant checklist PDFs may have color coding** — blue-highlighted items are tentative, not mandatory. Always read the email body for context.
- **Agricultural land document requests** — consultants often request land records (ADLR sketch, RTC, Mutation, Phodi) by default. If the site is in an approved layout under BBMP jurisdiction, these may not apply. Push back politely.
- **Professional certifiers need pre-filled drafts** — don't just forward blank templates to the CA/Architect/Engineer. Fill in the project-specific data first, then ask them to review, seal, and sign.
- **Multiple revision rounds** — expect 3-4 rounds of pending list revisions as the consultant reviews new documents added to the Drive folder. Each round is faster than the last.
- **Invoice first, then work** — the consultant typically sends an invoice for the engagement fee and expects payment before active filing begins.
- **Same Drive folder reused** — the initial folder shared with the consultant grows as new documents are added. Always add to the SAME folder, not create new ones, to keep the consultant's view consistent.
- **Email body contains revision notes, not just the attachment** — the consultant's reply email often has critical findings in the body text (e.g. "Photo not self-attested", "Board resolution date mismatch"). The PDF attachment has the checklist, but the email body has the QUALITY assessment. Extract BOTH.
- **Pending list PDF may be password protected or have image-only content** — if `pdftotext` returns nothing, use `pdftoppm` + `tesseract` on the first 2 pages. The checklist format is usually a simple table that OCR handles well.
- **🔴 New project vs ongoing project — Form type matters.** The required Architect and Engineer forms depend on the project's RERA stage:
  | Stage | Architect Form | Engineer Form |
  |-------|---------------|--------------|
  | **New project** (not yet started) | Form 2 | Form 3 |
  | **Ongoing project** (construction already began) | Form 5 | Form 6 |
  
  If the consultant's initial checklist asks for Form 2 & Form 3, do NOT assume the project is new. Ask the project coordinator whether construction has started. If it has, the consultant must revise their requirement — Form 5/6 apply instead. Submitting Form 2/3 for an ongoing project will be rejected by KRERA. This mistake can cause weeks of delay. Confirm the project stage BEFORE sending templates to the Architect/Engineer.
- **Data consistency checks between documents.** The consultant will cross-reference data across ALL submitted documents. Common mismatches that get flagged:
  - **Project end date** — must be identical across Allotment Letter, Agreement of Sale, SIS Excel, and Project Details Letter. Even a 1-day difference gets flagged.
  - **Carpet area** — must match exactly between the Architect-certified Area Statement and the SIS Excel. Discrepancies as small as 1 sq ft get noted.
  - **Land cost** — the Project Land Cost Letter must show Guidance Value calculation, not just a number. The consultant expects the land cost to be computed as per Sub-Registrar's Guidance Value × total land extent.
  - **Source of Funds** — must cover total project cost (land acquisition + approval costs + construction cost). A letter stating only construction cost is incomplete.
  
  When the consultant flags these, they appear in the email body text (not the attachment). Always read the email body of the reply for these specific quality findings.
- **Documents marked "Given" in your email but not in the Drive folder.** When the project coordinator tells the consultant "document X has been given" but it's not actually in the shared Drive folder, the consultant will list it as pending in the next revision. If you're building a readiness index, always verify actual file presence in the Drive folder against what was claimed — do not rely on email statements alone.
