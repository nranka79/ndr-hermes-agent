# Gmail Attachment → Calendar Event + Analysis Pipeline

When a user says "it's in my email" referring to a board meeting notice, EGM notice, or resolution document, and wants:
1. A calendar entry created from it
2. Risk analysis of the resolutions

## Workflow

### Step 1: Find the Email in Gmail

The user typically provides clues: sender domain, subject keywords, date. Build a targeted Gmail query:

```python
from tools.gws_auth import build_service
gmail = build_service("gmail", "v1")

# Search strategies (try in order):
# Strategy A — by sender domain (most specific)
results = gmail.users().messages().list(
    userId='me',
    q='from:compliance@company.in'
).execute()

# Strategy B — by subject keywords
results = gmail.users().messages().list(
    userId='me',
    q='subject:"Board Meeting" OR subject:"EGM" OR subject:"Extraordinary General Meeting"'
).execute()

# Strategy C — broad search + filter
results = gmail.users().messages().list(
    userId='me',
    q='from:compliance@company.in OR (subject:EGM board resolution)'
).execute()
```

### Step 2: Identify the Right Message

Fetch metadata (cheap — no body decoding):

```python
for msg in results.get('messages', [])[:15]:
    md = gmail.users().messages().get(
        userId='me', id=msg['id'],
        format='metadata',
        metadataHeaders=['From', 'Subject', 'Date']
    ).execute()
    headers = {h['name']: h['value'] for h in md['payload']['headers']}
    print(f"{headers.get('Date','')[:25]} | {headers.get('Subject','')[:80]}")
```

When you find a match, get the full message to check for attachments and extract the body:

```python
full = gmail.users().messages().get(userId='me', id=msg_id).execute()

# Check for PDF attachments
def list_attachments(payload):
    found = []
    if 'parts' in payload:
        for part in payload['parts']:
            found.extend(list_attachments(part))
    if payload.get('filename') and payload['filename']:
        found.append(payload)
    return found
```

### Step 3: Download & Extract PDF Content

```python
import base64, re

# Download attachment
att = gmail.users().messages().attachments().get(
    userId='me', messageId=msg_id,
    id=part['body']['attachmentId']
).execute()
file_data = base64.urlsafe_b64decode(att['data'])
filepath = f'/tmp/{part["filename"]}'
with open(filepath, 'wb') as f:
    f.write(file_data)

# Extract text (best-effort)
import subprocess
result = subprocess.run(['pdftotext', filepath, filepath + '.txt'], capture_output=True, text=True)
with open(filepath + '.txt', 'r') as f:
    content = f.read()
```

### Step 4: Parse Meeting Details

Extract these fields from the PDF text:

| Field | How to find | Example |
|-------|-------------|---------|
| **Company** | Notice heading | "DRA AADITHYA SOUTH CITY PROJECTS PRIVATE LIMITED" |
| **Meeting type** | Notice title | "NOTICE OF BOARD MEETING" or "NOTICE OF EXTRA-ORDINARY GENERAL MEETING" |
| **Date** | "held on" | "Friday, the 12th June, 2026" |
| **Time** | "at" | "11.00 a.m." |
| **Venue** | "at the" | "Registered Office of the Company at New No. 109..." |
| **Hybrid option** | "video conferencing" or "MS Teams" or "Zoom" | "with an option to attend through video conferencing (MS Teams)" |
| **Attendees** | "To" section | List of director names |
| **Agenda items** | Numbered items | "6. To consider acceptance of ..." |
| **Loan terms** | Agenda body | Rate, amount, security, tenure, guarantee |

Also check the email body for the actual conferencing link (MS Teams/Zoom URL), which may not be in the PDF:

```python
# From the email body
meeting_links = re.findall(r'https://teams\.microsoft\.com/meet/[^\s<>]+', body_text)
```

### Step 5: Create Calendar Event

```python
from tools.gws_auth import build_service
from datetime import datetime, timezone

cal = build_service("calendar", "v3")

event = {
    'summary': 'Company Name - Meeting Type',
    'location': 'Full address from PDF',
    'description': (
        f'**MEETING TYPE**\n\n'
        f'Date: DATE\nTime: TIME\nType: Hybrid/Physical\n\n'
        f'📍 **Venue:**\nVENUE\n\n'
        f'💻 **MS Teams Link:**\nURL\n\n'
        f'**Attendees:**\n- Person 1\n- Person 2\n\n'
        f'**AGENDA:**\n'
        f'1. Item 1\n'
        f'2. Item 2\n'
        f'...'
    ),
    'start': {'dateTime': '2026-06-12T11:00:00', 'timeZone': 'Asia/Kolkata'},
    'end':   {'dateTime': '2026-06-12T13:00:00', 'timeZone': 'Asia/Kolkata'},
    'attendees': [
        {'email': 'user@draas.com', 'displayName': 'User Name'},
    ],
    'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'popup', 'minutes': 60},
            {'method': 'email', 'minutes': 1440},
        ],
    },
    # Only add Google Meet as a backup — the primary link goes in the description
    'conferenceData': {
        'createRequest': {
            'requestId': f'unique-id-{datetime.now().timestamp()}',
            'conferenceSolutionKey': {'type': 'hangoutsMeet'},
        },
    },
}

created = cal.events().insert(
    calendarId='primary',
    body=event,
    sendUpdates='all',
    conferenceDataVersion=1,
).execute()
```

**⚠️ Always re-fetch to get a working link:**
```python
events = cal.events().list(
    calendarId='primary',
    timeMin='2026-06-12T00:00:00+05:30',
    timeMax='2026-06-13T00:00:00+05:30',
    singleEvents=True,
    orderBy='startTime'
).execute()
for e in events.get('items', []):
    working_link = e['htmlLink']  # Use this, not the one from insert()
```

### Step 6: Risk Analysis

If the meeting agenda includes loan resolutions, present a structured analysis (see `company-due-diligence.md` Phase 9 for full detail):

For each loan resolution, report:
- **Amount & Lender** — who and how much
- **Interest rate** — compare to other resolutions in the same meeting
- **Tenure** — match to project cash flows
- **Security** — what's being pledged
- **Personal guarantee** — who is guaranteeing
- **Purpose** — specific or vague

Flag outliers: if one lender charges 16% while others charge 12.75% or 9%, that warrants scrutiny.

## Common Sources

| Sender Domain | Company Type | Typical Attachments |
|--------------|--------------|-------------------|
| `@drahomes.in` | DRA group entities | Board meeting notices, EGM notices, resolutions, minutes |
| `@compliance.<company>.in` | Corporate compliance | NCD issue notices, loan resolution PDFs |
| External law firms | Legal counsel | Draft resolutions, modified AOA documents |
