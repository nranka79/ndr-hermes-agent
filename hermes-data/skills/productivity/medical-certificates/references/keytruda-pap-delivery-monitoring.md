# Keytruda PAP Drug Delivery / OTP Monitoring & Cycle Submission

## Trigger
User asks to check their secondary email account (e.g., ndr@ahfl.in) for delivery updates, OTP, or communication about a **Patient Assistance Program (PAP)** drug like Keytruda (pembrolizumab). Also triggers when user uploads scanned ICF + prescription documents and asks to file + email.

## Context
- **Patient:** Charitra Murjani (also known as Charitra Kamath)
- **Email (confirmed via thread history):** charitrakamath@gmail.com
- **Drug:** Keytruda (pembrolizumab) — PAP via KIRAN program
- **Coordinator:** Medybiz Pharma (kiranpapv3@medybizpharma.com)
- **Patient ID:** SPS1868282
- **Ticket No:** 7027
- **Toll-free:** 1800 210 2983

## People (confirmed CCs for emails)
| Role | Name | Email |
|------|------|-------|
| Patient | Charitra Murjani (Kamath) | charitrakamath@gmail.com |
| Patient's sister | Roshni Murjani | rmurjani@gmail.com |
| Oncologist | Dr. Annie K. Baa | anniekbaa@gmail.com |
| Family | Roshni Ranka (RNR) | rnr@draas.com |

**Charitra's email verification:** NDR asked to confirm through contacts + thread history. The email charitrakamath@gmail.com has been used in every prior cycle email on this thread. Google contacts (google-draas) also list yahoo addresses (charitra_murjani@yahoo.com, Charitramurjani77@yahoo.com) but those were NOT used in the email thread — always use charitrakamath@gmail.com unless NDR explicitly says otherwise.

## Cycle Submission Workflow (full pipeline)

When NDR uploads two scanned PDFs (Infusion Confirmation Form + Prescription) and asks to submit to the Kiran PAP program:

### Phase 1 — OCR & Extract Documents

Both documents are scanned images (no embedded text). Use pymupdf to detect page type:
```python
import pymupdf
doc = pymupdf.open('/path/to/pdf')
for page in doc:
    text = page.get_text()
    images = page.get_images()
    # text_len==0 and images > 0 = scanned page
```

Extract via pdftotext first. If empty, render at 150 DPI JPEG (NOT 200+ DPI PNG — memory killer) and use vision_analyze.

Document 1 is typically the **Infusion Confirmation Form**:
- Patient name, SPS ID, Cycle number
- Infusion date (DDMMYYYY format)
- Number of vials (free + paid)
- Doctor name + signature
- Submission email: kiranpapv3@medybizpharma.com

Document 2 is typically the **Prescription**:
- Patient name, age, hospital
- Drug name (Inj. Pembrolizumab 200 mg)
- **Next scheduled infusion date** (critical — this is the date you request availability for)
- Doctor name + credentials + stamp

### Phase 2 — Rename & Upload to Murjani Medical Folder

**Murjani Medical folder ID:** `1erVpDFXh9tdJuhsN5N36Zt69yjX4QG-V`

**Naming convention** (study existing files in the folder first):
```
YYYYMMDD Charitra Keytruda Infusion Confirmation MSD.pdf
YYYYMMDD Charitra Pembrolizumab Prescription St Johns.pdf
```

Example from this session:
- `20260812 Charitra Keytruda Infusion Confirmation MSD.pdf` (ICF for Cycle 12, infused 12 Aug)
- `20260812 Charitra Pembrolizumab Prescription St Johns.pdf` (prescription dated 12 Aug, next infusion 02 Sep)

Upload using google-draas Drive:
```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', service_name='google-draas')
file_meta = {'name': filename, 'parents': ['1erVpDFXh9tdJuhsN5N36Zt69yjX4QG-V']}
media = MediaFileUpload(local_path, mimetype='application/pdf')
uploaded = drive.files().create(body=file_meta, media_body=media, fields='id,name,webViewLink').execute()
```

### Phase 3 — Create Reply-All Draft on Existing Thread

**IMPORTANT:** This MUST be a **reply-all on the existing thread**, not a new email. The thread ID from prior cycles is `19f657773f75c067`. Do NOT create a new thread.

Email details:
- **From account:** ndr@ahfl.in (via google-ahfl)
- **To:** kiranpapv3@medybizpharma.com
- **Cc:** charitrakamath@gmail.com, rmurjani@gmail.com, anniekbaa@gmail.com, rnr@draas.com
- **Subject:** `RE : [Ticket No:7027] Infusion Confirmation Form and Prescription` (same as thread)
- **Attachments:** Both renamed PDFs

**Headers required for threaded reply:**
```python
message['In-Reply-To'] = msg_id_header   # Message-ID of the email you're replying to
message['References'] = f"{references} {in_reply_to}"  # Accumulated references
```

Get these from the last email in the thread:
```python
last_msg = service.users().messages().get(userId='me', id=LAST_MSG_ID, format='metadata').execute()
headers = {h['name']: h['value'] for h in last_msg['payload']['headers']}
msg_id_header = headers.get('Message-ID', '')
references = headers.get('References', '')
```

**Draft creation (never send — always draft):**
```python
draft = service.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw, 'threadId': THREAD_ID}}
).execute()
```

### Phase 4 — Email Body Template

Key message points in the draft:
1. Share Cycle N Infusion Confirmation Form (confirming infusion on [date])
2. Share Prescription for next scheduled infusion on [date]
3. **Request:**
   - Confirm KeyTRUDA will be made available on the scheduled infusion date
   - Verify that name, signature, hospital info on both documents are in order
4. **Reason for advance request:** Past issues with discrepancies caused last-minute delays
5. **Deadline:** Request confirmation by **tomorrow** to avoid surprises

Politeness tone: respectful but firm on the deadline ask.

### Phase 5 — Verify & Report Back

Tell NDR:
- ✓ Files renamed and uploaded to Murjani Medical folder (list names + links)
- ✓ Draft created in ndr@ahfl.in Drafts folder
- ✓ Reply-all on the existing thread
- ✓ CCs confirmed
- Provide link to Gmail Drafts: https://mail.google.com/mail/u/0/#drafts

## Email Monitoring Workflow

### 1. Access the correct email account
The drug delivery correspondence lives in ndr@ahfl.in (not ndr@draas.com):
```python
from tools.gws_auth import build_service
gmail = build_service('gmail', 'v1', service_name='google-ahfl')
```

### 2. Search for relevant emails
```python
# Primary search — from the PAP coordinator
results = gmail.users().messages().list(
    userId='me',
    q='from:(kiranpapv3@medybizpharma.com) Keytruda'
).execute()

# Also search for OTP/delivery
results2 = gmail.users().messages().list(
    userId='me',
    q='(delivery OR OTP) Keytruda'
).execute()

# Recent 48-hour check
results3 = gmail.users().messages().list(
    userId='me',
    q='(kiranpap OR medybiz) after:YYYY/MM/DD'
).execute()
```

### 3. Read the full thread to understand status
The PAP process follows a pattern:
1. User submits infusion confirmation + prescription
2. Medybiz acknowledges and says "executive will validate and confirm delivery date"
3. **No further communication until delivery OTP is generated** — the OTP email arrives when the drug is dispatched
4. Infusion is scheduled on a known date (e.g., 1st of the month)

**Common scenario:** User submits docs 11+ days before infusion, acknowledges receipt from Medybiz, then silence until the day before infusion when the OTP should arrive. If no OTP by the day before, user needs to chase.

### 4. If no recent emails
Check the last known status from the thread:
- What was the last email? (from user or Medybiz)
- When was it?
- What was agreed?
- What is the next infusion date?

Report the status clearly:
| Date | From | What Happened |
|---|---|---|
| [Date] | User → Medybiz | Submitted docs, asked for OTP |
| [Date] | Medybiz | Acknowledged receipt |
| ... | **SILENT** | No follow-up for [X] days |

### 5. Prescription Rejection / Resubmission Workflow

When Medybiz rejects the prescription (e.g., name not clearly visible) and a cleaner version needs to be sent:

#### a. Identify the issue
If the user gets a rejection reason (via phone call, not email), extract exactly what was wrong:
- Name not visible? Need clearer scan
- Wrong format? Need specific layout
- Missing signature? Doctor must re-sign

#### b. Prepare the cleaned version
- If the user uploads a new scan, save it to the patient's Drive medical folder first using the naming convention: `YYYYMMDD Charitra {DocType} {Hospital}.pdf`
- Example: `20260722 Charitra Pembrolizumab Prescription St Johns.pdf` → Murjani Medical folder

#### c. Draft the resubmission email
Tone: polite but firm. Key points to include:
1. **State the timeline gap** — initial submission was on [date], you heard nothing back until you proactively called [today]
2. **No OTP, no delivery confirmation, no rejection notification** — this should have been communicated
3. **Patient context** — on continuous treatment cycle, critical care at St. John's, legitimate recognized patient
4. **The fix** — cleaner scanned version attached
5. **Urgency** — infusion is scheduled for today; request immediate processing and delivery
6. **No further delays** — request no other procedural holds

#### d. Create the draft
Use the secondary email account (ndr@ahfl.in) to create a Gmail draft with the prescription attached:
```python
gmail = build_service("gmail", "v1", service_name="google-ahfl")
# Build MIMEMultipart with attachment
# Use drafts().create() — not send()
```

**Important:** Save as draft, not send. The user will review and send from their ahfl.in mailbox.

## Key Sender Details
- **PAP team:** kiranpapv3@medybizpharma.com
- **Contact people:** Karthik Kulkarni, Javeriya Abdul, Thoyadakshi, Punith Pooviah, Deepthi Nayak
- **Email subject prefix:** `[Ticket No:7027]` or `SPS1868282`
- **Delivery OTP timing:** Medybiz sends OTP via email when drug is dispatched (must be 72+ hours before infusion)