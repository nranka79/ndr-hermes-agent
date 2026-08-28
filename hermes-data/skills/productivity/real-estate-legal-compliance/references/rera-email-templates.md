# RERA Document Request Emails

Standard email templates for requesting RERA registration documents from the DRAAS team. Three separate emails with clear responsibilities.

## Email Destinations

| Email | To | CC | Documents Requested |
|-------|---|----|-------------------|
| **1** | Eshwari (echamundeshwari@draas.com) | NDR (ndr@draas.com) | Form 1 CA Certificate, Cash Flow Statement, Director's Report |
| **2** | Anbu/Anbarasan (pm2.blr@draas.com) | NDR (ndr@draas.com) | Form 2 Architect, Form 3 Engineer, Water Source, Common Area & Amenities, Area Statement, Construction Cost Abstract, Work Done Certificate |
| **3** | NDR (ndr@draas.com) | — | Board Resolution, Project Details, Organisation Structure, Allotment Letter, Agreement to Sale Proforma, Source of Funds |

## Standard Email Body Structure

### Opening
```
Dear [Name],

As part of the RERA registration documentation for Project [Project Name], please prepare the following documents on priority:

[Numbered document list]
```

### Action Items (same for all three emails)
- Fill the required data for each document
- Get certified by the required certifier (CA/Architect/Engineer as applicable)
- Ensure all documents are signed and company seal affixed
- Print and send:
  a) Scanned copy (PDF) via email
  b) Hard copy to the requesting person's desk
- Wherever a certifier is involved, attach:
  a) KYC of the certifier (scanned + hard copy)
  b) Their signed & sealed draft on their letterhead
- Attach their work order / assignment letter / authorization from DRA Realty Pvt Ltd (either as authorized signatory or as per their contract) for the project

### Closing
```
Please coordinate and get these done at the earliest so we can proceed with the RERA submission.

Regards,
Prakash Singh
```

## Implementation Pattern (Gmail API)

```python
from email.message import EmailMessage
import base64

svc = build_service('gmail', 'v1', telegram_id='<sender_telegram_id>')

msg = EmailMessage()
msg['To'] = 'recipient@draas.com'
msg['Cc'] = 'ndr@draas.com'
msg['Subject'] = f'RERA Documents — [Document Types] — [Project Name] — {datetime.now().strftime("%d %B %Y")}'

body = """..."""  # see template above
msg.set_content(body)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
sent = svc.users().messages().send(userId='me', body={'raw': raw}).execute()
```

## Sender Setup

For Prakash Singh (psingh@draas.com, TG:psingh) — full GWS OAuth token. Use `tools.gws_auth.build_service('gmail', 'v1', telegram_id='psingh')`.
