# Contact Phone Number Resolution Workflow

When a DRAAS user (typically Nishant) asks you to generate a WhatsApp link for someone — or says "find [person]'s number and send them a WhatsApp" — the number is rarely in one obvious place. This workflow defines the ordered search pipeline.

## Trigger

User says: "send a WhatsApp message to X", "get me X's number", "I want to WhatsApp Y", "find Z's contact and encode a wa.me link".

## The pipeline (in order)

### Step 1 — Google People API (direct contacts)

The fastest path: Google's People API returns phone numbers if the contact is in the user's address book.

```python
people = build_service('people', 'v1')
results = people.people().searchContacts(
    query='Full Name',
    pageSize=10,
    readMask='names,emailAddresses,phoneNumbers,organizations'
).execute()
```

If no result, try `connections().list` to scan all contacts (pagination — scan beyond 100):

```python
page_token = None
while True:
    results = people.people().connections().list(
        resourceName='people/me',
        pageSize=1000,
        pageToken=page_token,
        personFields='names,emailAddresses,phoneNumbers'
    ).execute()
    connections = results.get('connections', [])
    for p in connections:
        display = ', '.join(n.get('displayName','') for n in p.get('names',[]))
        if search_term in display.lower():  # found
            break
    page_token = results.get('nextPageToken')
    if not page_token:
        break
```

**Common failures:** (a) People API returns empty even when the contact IS in "My Contacts" — seen with Ashwin Pai who appeared in the CSV sheet with "* myContacts" label but was not found by `connections().list` across 2,175 scanned contacts. (b) `searchContacts` omits results for short/common names. (c) "Other Contacts" (contacts from email auto-save) are NOT returned by `connections().list`.

### Step 2 — Contacts sheets

Nishant maintains two contact sheets on Drive:

| Sheet ID | Name | Structure |
|---|---|---|
| `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g` | NDR DRAAS Google contacts | CSV export of Google Contacts — **53 columns** (name, emails, phones, org, notes) |
| `1fYa-t2RY1siy2qBgAH8uu_Jd2chjJ716BbcpxilpOK0` | NDR CONTACTS | Structured: SL.NO, NAME, COMPANY, DESIGNATION, ADDRESS, TELEPHONE, FAX, MOBILE |

```python
sheets = build_service('sheets', 'v4')

# ALWAYS read to BA (col 53) to capture phone columns — A1:Z500 misses phone numbers
result = sheets.spreadsheets().values().get(
    spreadsheetId='1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g',
    range="'NDR DRAAS Google contacts.csv'!A1:BA500"
).execute()
```

**⚠️ CRITICAL — Phone columns are at col 27–28 (AA–AB), not in A–Z.**
- Col 27 (AA): Phone 1 - Label (e.g. "Mobile")
- Col 28 (AB): Phone 1 - Value (e.g. "+91 9972042131")
- Col 29-38: Phone 2-6 label/value pairs
- See `references/phone-contacts-csv-column-pitfall.md` for the full 53-column map

**For the NDR CONTACTS sheet**, MOBILE is column H (index 7).

When the user says "check around columns E, F, G, H, I" — trust the actual header row. The CSV export's phone columns are at AA–AB (27-28), much further right than the user estimated.

### Step 3 — Gmail thread body mining

For advocates, CA firms, and business contacts not in saved contacts, their phone number is usually in email signatures.

```python
results = gmail.users().messages().list(
    userId='me',
    q='"Full Name" OR "firstname.lastname@domain"',
    maxResults=20
).execute()

import base64, re
phone_pat = re.compile(r'(?:(?:\+91[\s-]?)|(?:91[\s-]?)|(?:0))?([6-9]\d{2,4}[-\s]?\d{3,4}[-\s]?\d{3,4})')

for m in msgs:
    full = gmail.users().messages().get(userId='me', id=m['id'], format='full').execute()
    def decode(p):
        out = []
        if p.get('body',{}).get('data'):
            out.append(base64.urlsafe_b64decode(p['body']['data']).decode('utf-8', errors='replace'))
        for part in p.get('parts', []):
            out.append(decode(part))
        return '\n'.join(out)
    
    body = decode(full.get('payload', {}))
    headers = {h['name']: h['value'] for h in full.get('payload',{}).get('headers',[])}
    full_text = headers.get('From','') + ' ' + headers.get('Subject','') + ' ' + body
    phones = phone_pat.findall(full_text)
```

Format must be `'full'` — `'metadata'` returns headers only, no body/signature.

### Step 4 — Drive full-text search

```python
creds = Credentials.from_authorized_user_file("/data/hermes/google_token.json")
drive = build('drive', 'v3', credentials=creds)
results = drive.files().list(
    q="fullText contains '" + name + "'",
    pageSize=30,
    fields="files(id,name)"
).execute()
```

### Step 5 — Report to user

When no number is found: show name/email/company you found + message draft. Ask user for the mobile number.

```python
from urllib.parse import quote
digits = ''.join(c for c in phone if c.isdigit())
last10 = digits[-10:]
msg_safe = msg.replace('&', '＆')  # full-width &
encoded = quote(msg_safe, safe='')
url = f'https://wa.me/91{last10}?text={encoded}'
```

## When the user corrects you

If the user says "the number is there, check further columns" — they are right. The CSV export has 53 columns and phones start at col 27. Always read to BA (col 53) before declaring a phone number absent.

## Related

- `references/phone-contacts-csv-column-pitfall.md` — Full column map for 53-col CSV export
- `gmail-api-notes.md` — format='full' vs 'metadata' gotcha
