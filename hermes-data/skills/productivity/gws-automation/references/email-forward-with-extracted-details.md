# Forward Colleague Email with Extracted Details (Process & Forward)

When a colleague emails a document (sanction letter, invoice, payment notice, report) that needs to be actioned by finance/accounts:

## Workflow

### 1. Find the email
Search Gmail for the specific email by sender + keywords:
```python
results = gmail.users().messages().list(
    userId='me',
    q='from:colleague@draas.com "Ranka Iris" payment',
    maxResults=10
).execute()
```

### 2. Read the email body
Get full text to understand context before extracting from attachments.

### 3. Extract from attachments
If the attachment is a PDF:
- Try `pdftotext -layout` first (fast, text-based PDFs)
- If empty → `pymupdf` to check for text layer
- If 0 chars + has images → `pdftoppm -jpeg -r 200` → `vision_analyze` on each page
- If the PDF is on Gmail, download via `messages().attachments().get()` first

### 4. Pull out the key details
Extract:
- **What** is being paid (purpose, reference number)
- **How much** (itemized breakdown + total)
- **Where** to pay (bank details, DD payable at, online portal)
- **Deadline** (due date, validity period)
- **Reference** (application ID, account ID, sanction number)

### 5. Draft the forward
Structure the forwarding note:
- **Salutation** — address the recipient (accounts person)
- **Context** — one line: what the original email is about
- **Table of amounts** — itemized breakdown with total highlighted
- **Payment method** — where/how to pay
- **Reference numbers** — for tracking
- **Action required** — clear ask

### 6. Attach the original as forwarded message
Use `message/rfc822` MIME type (see `references/gmail-forwarding-pattern.md` for the technical implementation). This preserves the thread and shows the original as a proper forward.

### 7. Threading
- Get the `threadId` from the original message
- Set `In-Reply-To` and `References` headers to keep it in thread
- Pass `threadId` in the create/send API call

### 8. Confirm before sending (Nishant's preference)
Show the draft to Nishant first — amounts, methodology, recipients, CC — and wait for approval before sending.

## Example structure
```
To: Eshwari Chamundeshwari
CC: Bhavik Ranka, Anbarasan M
Subject: Fwd: [Original Subject]

Eshwari,

Please find below/attached the [document type] for [project].

Payment details:

1. Item A                          ₹X,XX,XXX.00
2. Item B                          ₹X,XXX.00
3. Item C                          ₹X,XX,XXX.00
   ───────────────────────────────
   TOTAL                           ₹X,XX,XXX.00

Payment method: [DD/Bank transfer/NEFT] to [details]
Reference: [Sanction/Application/Account ID]
Due: [Date]

Please arrange and confirm.

Regards,
Nishant
```
