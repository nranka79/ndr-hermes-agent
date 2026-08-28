# Email Forward with CC + Custom Context (Vendor Invoice → Internal)

**Trigger:** User says "forward this email from [sender] to [internal person]" with:
- Specific CC list (original sender + additional parties)
- Custom body explaining the arrangement
- Original attachment(s) to include

## Workflow

### 1. Identify the source email

Get the source email's full details:
- Message-ID (for In-Reply-To / References headers — needed to thread the forward)
- Original From/To/Cc
- Attachment(s) — download any PDF attachments that need to be included

Use `gmail.users().messages().get(userId='me', id=msg_id)` in `format='full'` or `format='raw'` to get headers and attachment data.

### 2. Present full draft for confirmation (per `confirm-before-actions` rule)

Show structured summary BEFORE composing:

```
Forward TO:   Dharmesh Ranka (ddr@draas.com)
CC:
  • accounts@pattanshetti.in
  • br.krishna.advocate@gmail.com (BR Krishna)
  • jayanth@pattanshetti.in (Jayanth Pattanshetti)
  • [other CCs]

Body draft:
[Draft text]

Attachment(s): [file names from original]
```

Wait for explicit "yes send it" before composing.

### 3. Compose using EmailMessage

```python
from email.message import EmailMessage
import base64

msg = EmailMessage()
msg["From"] = "Nishant Ranka <ndr@draas.com>"
msg["To"] = "ddr@draas.com"
msg["Cc"] = "accounts@pattanshetti.in, br.krishna.advocate@gmail.com, jayanth@pattanshetti.in"
msg["Subject"] = "Fwd: [original subject]"

msg.set_content("Body text...\n\nThanks,\nNishant")

# Forward the original as an attachment — attach the PDF
with open('/tmp/invoice.pdf', 'rb') as f:
    pdf_data = f.read()
msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename='Invoice.pdf')

raw_b64 = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8').replace('+','-').replace('/','_').replace('=','')
service.users().messages().send(userId='me', body={'raw': raw_b64}).execute()
```

**CRITICAL:** `msg.as_bytes()` — NOT `BytesIO` + `flatten`.

### 4. Pitfall — CC list from voice dictation

When the user dictates CCs via voice:
- Transcribe carefully — similar-sounding names cause errors
- Confirm each CC address with the user before sending
- Cross-check against known contacts (People API / contacts sheet) before accepting the voice transcription verbatim

### 5. Pitfall — Invoice attachment from source email

The original invoice PDF may need to be downloaded from the Gmail API via the `attachmentId`. Steps:
1. Parse the message parts to find the `attachmentId` for the PDF
2. Call `service.users().messages().attachments().get(userId='me', messageId=msg_id, id=attachmentId)`
3. Decode with `base64.urlsafe_b64decode(data)`
4. Save to `/tmp/{filename}.pdf`
5. Attach to the new email

**Always confirm with the user which attachment(s) to include** — don't assume all attachments are meant to be forwarded.
