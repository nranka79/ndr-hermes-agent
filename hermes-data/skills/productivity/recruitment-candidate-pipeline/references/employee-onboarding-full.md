---
name: employee-onboarding
description: "Employee onboarding for DRAAS — after offer acceptance, before the employee starts. Covers extracting employee details from Gmail (offer letter docx attachments) & Drive (resume PDFs), adding to Google Contacts via People API, updating the NDR DRAAS contacts sheet (employees tab + main contacts CSV tab), and creating a WhatsApp welcome message with email account credentials and group email info."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Employee Onboarding — DRAAS

Post-offer, pre-joining phase. Picks up where `recruitment-candidate-pipeline` (resume intake → hiring tracking) ends, and feeds into `employee-review-analysis` (compensation/performance reviews).

## When to load this skill

Trigger signals:
- "create an account for [name]" / "set up email for [name]"
- "add [name] to my contacts" (in context of a new hire)
- "send welcome message to [name]" with account setup info
- "I've given her/him an offer letter, find details"
- "onboard [name]"

## Data sources (in order)

### 1. Gmail — Offer Letter & Correspondence

Search Gmail for the employee's name + "offer letter" or "offer of employment":

```python
from tools.gws_auth import build_service
service = build_service('gmail', 'v1', service_name='google-draas')
results = service.users().messages().list(userId='me', q='<NAME> offer letter', maxResults=10).execute()
```

**Key fields from offer letter emails:**
- **Name** — from email headers or document body
- **Phone** — often in the offer letter document text
- **Role / Title** — Content Creator, Sales Executive, etc.
- **CTC** — monthly pay breakdown (base + attendance allowance)
- **DOJ** — joining date
- **Manager** — reporting manager's name
- **Department** — Marketing, Sales, etc.
- **Personal Email** — from the employee's reply email address (Neha <esotericarts.ani@gmail.com>)

**Important:** The offer letter is often sent as a **.docx** attachment (not PDF). The Gmail API returns the attachment ID; download it and extract text:

```python
# Download docx attachment
att = service.users().messages().attachments().get(userId='me', messageId=MSG_ID, id=ATTACH_ID).execute()
data = base64.urlsafe_b64decode(att['data'])
with open('/tmp/offer.docx', 'wb') as f:
    f.write(data)

# Extract text via python-docx, or fallback to zipfile + XML:
import zipfile, xml.etree.ElementTree as ET
with zipfile.ZipFile('/tmp/offer.docx') as z:
    with z.open('word/document.xml') as f:
        tree = ET.parse(f)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        text_parts = []
        for t in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if t.text:
                text_parts.append(t.text)
        full_text = ' '.join(text_parts)
```

### 2. Google Drive — Resume PDF

Search Drive for the employee's resume:

```python
results = service.files().list(q="name contains '<LAST_NAME>' and name contains 'Resume'").execute()
for f in results.get('files', []):
    print(f['name'], f['id'], f['mimeType'])

# Download and extract text
request = service.files().get_media(fileId=FILE_ID)
import io
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()
```

The resume provides:
- **Phone** (if not in offer letter)
- **City / Location** (e.g. "Bangalore - 37, Karnataka")
- **Education** (degrees, institutions)
- **Skills / Experience**
- **Full residential address** — offer letter often says "[address to be confirmed at joining]", so the resume's city is the best available until joining formalities

### 3. Gmail correspondence thread

All email threads between the employer (ndr@draas.com / rnr@draas.com) and the candidate contain additional context:
- Negotiation history (CTC clarification, role changes)
- Joining date confirmation
- Any special requests (working hours, remote work)
- Request for official email ID (the employee may have asked for it)

## Google Contacts — Add via People API

Add a full contact entry via the Google People API:

```python
people_service = build_service('people', 'v1', service_name='google-draas')

contact = {
    "names": [{
        "givenName": "<First>",
        "middleName": "<Middle>",
        "familyName": "<Last>",
        "displayName": "<Full Name>"
    }],
    "emailAddresses": [
        {"type": "work", "value": "<new.company.email@draas.com>"},
        {"type": "personal", "value": "<personal.email@gmail.com>"}
    ],
    "phoneNumbers": [{"type": "mobile", "value": "+91 <phone>"}],
    "organizations": [{
        "name": "DRA Realty Private Limited",
        "title": "<Job Title>",
        "department": "<Department>"
    }],
    "addresses": [{
        "city": "<City>",
        "region": "<State>",
        "country": "India"
    }],
    "biographies": [{
        "value": "Reports to <Manager Name> (<manager.email>@draas.com). Part of <group>@draas.com group email.",
        "contentType": "TEXT_PLAIN"
    }]
}

created = people_service.people().createContact(body=contact).execute()
```

## NDR DRAAS Google Contacts Sheet — Two Tab Update

Sheet ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`

### Tab 1: `employees` — Simple row append

Columns: `name, email, phone, role, telegram_id, notes`

```python
row = ['<Full Name>', '<nVaddadi@draas.com>', '+91<phone>', 'employee', '',
       '<Job Title>, Reports to <Manager> (<email>), <Dept> Dept']
result = sheets.spreadsheets().values().append(
    spreadsheetId=SHEET_ID, range='employees!A:F',
    valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS',
    body={'values': [row]}
).execute()
```

### Tab 2: `NDR DRAAS Google contacts.csv` — Full row with 93 columns

Key column indices (0-based):
| Col | Field | Value |
|-----|-------|-------|
| 0 | First Name | Sai |
| 1 | Middle Name | Neha |
| 2 | Last Name | Vaddadi |
| 9 | File As | `Vaddadi, Sai Neha` |
| 10 | Organization Name | DRA Realty Private Limited |
| 11 | Organization Title | Content Creator |
| 12 | Organization Department | Marketing |
| 14 | Notes | Reports to... Part of X group email. |
| 17 | E-mail 1 - Label | Work |
| 18 | E-mail 1 - Value | nVaddadi@draas.com |
| 19 | E-mail 2 - Label | Personal |
| 20 | E-mail 2 - Value | personal@email.com |
| 27 | Phone 1 - Label | Mobile |
| 28 | Phone 1 - Value | +917899398273 |
| 42 | Address 1 - City | Bangalore |
| 44 | Address 1 - Region | Karnataka |

**Important:** Use `insertDataOption='INSERT_ROWS'` (append mode), not `update`. The sheet has a fixed grid — `update` fails if the grid is at capacity. Append auto-expands.

```python
row_data = [None] * 93  # 93-column array
row_data[0] = 'Sai'
# ... populate fields ...
result = sheets.spreadsheets().values().append(
    spreadsheetId=SHEET_ID,
    range="'NDR DRAAS Google contacts.csv'!A:A",
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body={'values': [row_data]}
).execute()
```

## Welcome WhatsApp Message

Create a wa.me link with the onboarding message. See `messaging-drafts` skill for the full WhatsApp workflow (tone rules, ampersand substitution, character limits).

**Message structure (always verify with the user before generating the link):**

1. Greeting — welcome to DRA Realty
2. Company email: `<username>@draas.com`
3. Temporary password: `<password>`
4. Login steps:
   - Go to gmail.com
   - Enter username
   - Enter temporary password
   - Reset password (forced)
   - Use email going forward
5. Group email info: `<group>@draas.com` — explain purpose
6. Closing — welcome aboard

**Delivery:** Generate a single wa.me link via URL encoding, or if the message exceeds ~1,200 chars, use the HTML chunked delivery pattern (see `messaging-drafts` references/whatsapp-chunked-message-html.md).

```python
import urllib.parse
message = "Hi <Name>, ..."
encoded = urllib.parse.quote(message)
url = f"https://wa.me/91<phone>?text={encoded}"
```

## Pitfalls

### 1. Phone number missing from records

The offer letter often says *"[address to be confirmed at joining]"* for the residential address. The phone number is usually present. If not found in Gmail (offer letter text), check:
- Resume PDF in Drive
- Any correspondence thread with the employee
- Kelsa employee records

Use `contact-phone-lookup` skill for the structured lookup order.

### 2. Email convention at DRAAS

Nishant's convention: **first initial + last name** @draas.com
- Sai Neha Vaddadi → nVaddadi@draas.com
- Confirm with Nishant before assuming — email IDs can deviate from strict convention

### 3. Sheet grid limits on main contacts CSV tab

The `NDR DRAAS Google contacts.csv` tab has a fixed grid. Using `.values().update()` with a row beyond the existing grid range throws a 400 error. Always use `.values().append()` with `insertDataOption='INSERT_ROWS'` which auto-expands the grid.

### 4. Offer letter may be a .docx, not PDF

Gmail attachment MIME types differ. Check `part['mimeType']` — `application/vnd.openxmlformats-officedocument.wordprocessingml.document` = .docx. Use the zipfile+XML extraction method (python-docx may not be installed).

### 5. Resume may be a Google Doc (not a downloadable PDF)

Some resumes are stored as `application/vnd.google-apps.document`. Export via Drive API's `export` with `mimeType='text/plain'`.

### 6. Cross-verify the phone number

Before generating any wa.me URL, cross-check the phone number from at least two independent sources (offer letter, resume, email signature). A single-source digit error creates a broken WhatsApp link. See `contact-phone-lookup` for the verification chain.

### 7. Always ask for the temporary password

Nishant creates the Google Workspace account himself (no admin access for the agent). The temporary password must come from him before generating the WhatsApp message — do not invent or guess one.

### 8. Employee may have an existing personal email request

Check Gmail for any "Request for Official Email ID" thread from the employee — they may have proactively asked for a company email weeks before onboarding. Mention this when presenting the onboarding plan.

## Related skills

- `recruitment-candidate-pipeline` — Pre-joining: resume intake → hiring sheet → candidate tracking
- `dra-employment-documents` — Offer letter drafting (upstream of this skill)
- `messaging-drafts` — WhatsApp message drafting, tone rules, character limits, chunked delivery
- `google-workspace` / `gws-automation` — GWS auth and service building patterns
- `contact-phone-lookup` — Structured phone number verification chain
- `employee-review-analysis` — Post-onboarding: comp review, performance analysis
