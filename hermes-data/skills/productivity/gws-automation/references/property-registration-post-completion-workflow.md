# Property Registration Post-Completion Workflow

**Trigger:** User reports that a flat/apartment has been registered (sale deed executed and registered). They need task-delegation emails sent, letters drafted, and documents shared with the team.

**Used by:** Nishant Ranka (NDR), DRA Realty

## Workflow stages

### Stage 1 — Gather Facts from the Sale Deed

The sale deed (Google Doc or PDF) contains everything needed. Extract:

| Field | Source |
|---|---|
| Registration details (Doc No, SRO, Date) | Sale deed / registration stamp on PDF |
| Property address (flat #, project, street, ward) | Sale deed Schedule |
| Purchaser name, PAN, Aadhaar | Sale deed parties section |
| Seller name, PAN | Sale deed parties section |
| Khata No, BBMP Property ID, ULPIN | Sale deed Schedule |
| BESCOM RR No, Account ID | Sale deed clauses |
| SBUA, undivided share, parking slot | Sale deed Schedule |
| Sale consideration | Sale deed clause 1 |

**PDF extraction:** For registered PDFs that are scanned, use `pdftoppm` + `tesseract` or render pages with PyMuPDF + OCR. The Google Doc version of the sale deed (if available) is faster to read.

### Stage 2 — Prepare Drive Folder

Create a folder under the project's existing Drive structure:

- Check the Drive folder inventory reference at `references/drive-folders-914-embassy-habitat.md` for the project's parent folder IDs
- Create a subfolder named `E{flat_no} - Post Registration` (e.g. `E914 - Post Registration`) under the Sale Agreements folder
- If the user says "E114" but the flat is E914, it's likely a speech-recognition error — use the actual flat number

Create these Google Docs in the folder:

1. **Letter to Association** — `YYYYMMDD E{flat_no} Letter to Association - Ownership Change to {Owner Name}`
   - Include owner PAN and Aadhaar for the Association's records (confirmed preference from Nishant, Jun 2026)
   - Owner should sign directly (not an authorized representative)
   - CC to the project's management committee / secretary
2. **Tasks and Instructions for Parties** — `YYYYMMDD E{flat_no} - Tasks and Instructions for {Name}`
   - List tasks with BBMP/BESCOM reference numbers, document names, and process notes
3. **Property Details and Document Inventory** — `YYYYMMDD E{flat_no} - Property Details and Document Inventory`
   - Reference sheet with all extracted fields and links to existing docs on Drive

### Stage 3 — Share Drive Documents

Add editor access (`role: "writer"`) for every team member who needs to work on the documents:

```python
permission = {
    "type": "user",
    "role": "writer",
    "emailAddress": recipient_email
}
drive.permissions().create(
    fileId=file_id,
    body=permission,
    sendNotificationEmail=...,  # see pitfall below
    emailMessage="DRA Realty: Documents for E{flat_no} - please review"
).execute()
```

**⚠️ PITFALL — Non-Google-account emails require notification.** If the recipient's domain is NOT a Google Workspace / Gmail account, `sendNotificationEmail=False` causes a 400 error. You MUST set `sendNotificationEmail=True` (Google forces the notification for non-Google accounts). For @draas.com users, test with `sendNotificationEmail=False` first — if it fails, retry with `True`.

**⚠️ PITFALL — Verify emails before sending.** When the user dictates an email address in a voice message, it's easy to mishear. Always:
  - Parse carefully (V-K-D-A-S vs V-K-D-A-A-S)
  - If uncertain about spelling, ask the user to confirm before proceeding
  - Check the user's memory/profile for known email patterns (@draas.com vs @drahomes.com vs @drahomes.in)
  - The Google Drive sharing API will give a 400 if the email doesn't belong to a valid user, but won't tell you it's the wrong *intended* user

### Stage 4 — Send the Primary Email

Use the per-user Gmail token (user who owns the transaction, typically ndr@draas.com). Build a MIME multipart message with:

- **To:** Primary task-doer (e.g. Rahul)
- **CC:** Coordinator (e.g. Bharat) and property owner (e.g. Roshni)
- **Subject:** `Flat No. {flat_no} ({project}) - Registered in {owner_name} Name: Priority Tasks`
- **HTML body** with:
  - Registration announcement (Doc No, date, SRO)
  - Task 1: eKhata transfer (Khata No, BBMP ID, process)
  - Task 2: BESCOM meter transfer (RR No, Account ID, docs available)
  - Reference to other tasks (letter to association, etc.)
  - Links to all Drive documents
  - Link to the shared Drive folder

**MIME construction:**
```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.generator import BytesGenerator
from io import BytesIO
import base64

msg = MIMEMultipart('mixed')
msg['To'] = primary_email
msg['Cc'] = ', '.join(cc_emails)
msg['Subject'] = subject

alt = MIMEMultipart('alternative')
alt.attach(MIMEText(html_body, 'html', 'utf-8'))
msg.attach(alt)

buf = BytesIO()
BytesGenerator(buf).flatten(msg)
raw = base64.urlsafe_b64encode(buf.getvalue()).decode()

sent = gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
```

### Stage 5 — Send Follow-up Email (Role Clarification)

If the user clarifies division of responsibilities (e.g. "Bharat coordinates only, Roshni signs the letter"), send a second email:

- **Subject:** `Re: Flat No. {flat_no} ({project}) - Role Clarification for Association Letter and Updated Docs`
- **Same To/CC** as primary
- Detail the specific coordination steps and who does what

**Common role division pattern (Nishant's preference, Jun 2026):**
| Person | Tasks |
|---|---|
| **Field employee** (e.g. Rahul) | eKhata transfer + BESCOM meter transfer (legwork with govt offices) |
| **Coordinator** (e.g. Bharat) | Print letter, get owner's signature, submit to Association, obtain acknowledgement, scan + file. Also provide sale deed copy to field employee. |
| **Owner** (e.g. Roshni) | Sign the Association letter directly; review docs |

### Stage 6 — Telegram Follow-ups

After emails are sent, notify all parties on Telegram with:
- Key tasks specific to each recipient
- Drive folder link
- Links to key documents (letter to association, tasks doc)
- Note that email has been sent

Send individual messages to each person (not a group message) so each sees their own responsibilities.

### Stage 7 — Document Updates

If the user asks for corrections (wrong email, missing PAN/Aadhaar, wrong signatory):

1. **Update the Google Docs** using `replaceAllText` in `documents().batchUpdate()` — this doesn't shift indices and is safe for text swaps
2. **Fix Drive sharing** — remove old email permission (find via `permissions().list()` and `permissions().delete()`), add new email
3. **Resend email** to corrected address
4. **Send Telegram correction** to affected parties

### Key pitfalls specific to this workflow

- **Email address corrections are expensive.** Getting it wrong means 3+ extra tool calls (remove share, add share, update docs, resend email, Telegram). Always verify dictated email addresses before the first send.
- **`replaceAllText` is the right tool** for correcting content in Google Docs. It's idempotent and index-safe. Don't use `deleteContentRange` + `insertText` for text corrections.
- **The Association letter must include owner PAN/Aadhaar** — Nishant confirmed this preference (Jun 2026). Include both in the letter body and in a structured owner details section.
- **The signatory should be the owner** (not a representative) unless the user explicitly says otherwise. Nishant corrected this: Bharat coordinates, Roshni signs.
