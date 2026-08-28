# Family Legal Document Sharing Email Pattern

**When to use:** NDR wants to share court-filing documents (succession petition, GPA, Vakalatnama, etc.) with extended family (brother-in-law, sister, sister-in-law) for review and signature.

**Validated:** 2026-08-27 — Succession Petition for Dinesh Ranka estate, docs from Sanjay H. Sethiya & Associates (Law Square)

## Key Characteristics

- **Sender:** ndr@draas.com (not personal Gmail — the content is DRA estate/company governance)
- **To:** Brother-in-law (the primary decision-maker/spouse)
- **Cc:** Sister + sister-in-law (the family members with direct shareholding interest)
- **Tone:** Warm family address ("Dear Jai ji") but structured, business-like content
- **Plain text** (not HTML — this is a family document-sharing, not a corporate brief)

## Structure

### 1. Opening
Warm, personal greeting. Acknowledge the relationship context.

> Dear Jai ji,
> 
> I hope this email finds you well.

### 2. Context — what we're doing
One paragraph: what action is being taken, who prepared the docs, and why.

> As discussed, we are proceeding with the filing of the Succession Petition for the estate of late Dad (Shri Dinesh Ranka). We have engaged [Law Firm] and they have prepared the draft documents for us.

### 3. Numbered document list
Match the user's own numbering. Each entry: document name, source, purpose.

> I am sharing the following documents from their office for your review:
> 
> 1. [Document Name] — [purpose/description]
> 2. [Document Name] — [purpose/description]
> 3. [Document Name] — [purpose/description]

### 4. Specific addition to the filing
If the user wants to add a specific asset/account to the petition scope, state it clearly.

> We will be specifically adding the [Bank/Account] of Dad to the petition so that the bank sees clearly that we have applied for succession insofar as that account is concerned.

### 5. Additional document (if any)
Separate from the court-filing docs. Usually the Letter of Understanding / Cooperation Agreement.

> Additionally, I am also attaching:
> 4. [Document Name] — [context]. Request you to kindly review it and let me know if it is in order. If yes, I will request all of us to sign it and keep it for our records.

### 6. Specific action requests
Be explicit about what the recipient needs to do:
- Review documents
- Sign where needed
- Who will give GPA to whom
- Who will handle which family member

> Request you to kindly review the above documents at your earliest convenience and let me know if I can get the signatures from everyone. For [Sister], I am requesting a GPA in my favour to attend on her behalf. [Brother] and [Brother] — I will speak to them separately.

### 7. Bank follow-up plan
If the filing enables a bank release, explain:
- What bank/account
- Who the contact is
- What help you need from the recipient

> Once the succession petition is filed, I plan to approach [Bank] at the senior level through [Banker Name], who says he will try to see if [Bank] can be convinced to release the [Account] based on this. If anything is required at the top level with [Bank] — any connect through [Contact] or any other senior contact you may have — I request your kind assistance.

### 8. Close
Warm, forward-looking.

> I hope you find all the above in order. Please let me know your thoughts.
> 
> Warm regards,
> Nishant

## Attachments

Attach the documents as MIME attachments via raw Gmail API (bridge doesn't support attachments):

```python
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import base64

msg = MIMEMultipart('mixed')
msg.attach(MIMEText(body, 'plain', 'utf-8'))
msg['To'] = 'Name <email@domain.com>'
msg['Cc'] = 'Name2 <email2@domain.com>, Name3 <email3@domain.com>'
msg['Subject'] = 'Subject Line'
msg['From'] = 'Nishant Ranka <ndr@draas.com>'

for local_path, display_name in attachments:
    with open(local_path, 'rb') as f:
        file_data = f.read()
    part = MIMEBase('application', 'vnd.openxmlformats-officedocument.wordprocessingml.document')
    part.set_payload(file_data)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename=display_name)
    msg.attach(part)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('ascii')
draft = svc.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
```

## Document Sources

When the user says "documents from the lawyer's office", the documents may come from:
- **Email attachments** from the law firm (download via Gmail API)
- **Existing Drive files** (Vakalatnama, older versions on Drive)
- **Converted files** (.md → .docx for the LOU/Cooperation Agreement)

## Subject Line Pattern

`DRA Family: [Document Purpose] — For Your Review`