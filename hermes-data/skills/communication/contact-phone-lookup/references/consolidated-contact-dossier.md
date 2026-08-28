# Consolidated Contact Dossier — Find All Contacts Associated with a Person/Entity

**When the user asks for "all contacts related to [person/entity/hospital]", do NOT just look up one contact.** Search across ALL sources to find every associated person and compile a structured dossier.

## Trigger Phrases

- "Check my contacts for X and give me the list"
- "Give me all the contacts related to X"
- "I want to share all contacts for X with someone"
- "Find everyone associated with [hospital/company/doctor]"
- "I need a WhatsApp-copyable list of contacts for X"

## Search Protocol — Run ALL Sources in Parallel

### 1. Google People API — All 3 Accounts

```python
from tools.gws_auth import build_service

for acct in ['google-draas', 'google-ahfl', 'google-gmail']:
    try:
        svc = build_service('people', 'v1', service_name=acct)
        # Search for the primary name AND related terms
        for query in ['Haldipur', 'Trustwell', 'Sridhar', 'Charan']:
            resp = svc.people().searchContacts(
                query=query, pageSize=30,
                readMask='names,emailAddresses,phoneNumbers,organizations,biographies'
            ).execute()
            # Collect results
    except Exception as e:
        # Account may have expired token — skip gracefully, note it
        print(f'{acct}: {e}')
```

### 2. NDR DRAAS Google Contacts Sheet

Sheet ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`
Sheet name: `NDR DRAAS Google contacts.csv`

Search every row for the primary name AND related entities (hospital name, coordinator names etc). Use range `A:AM` to capture all phone columns (cols 27–38).

```python
service = build_service('sheets', 'v4', service_name='google-draas')
result = service.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range="NDR DRAAS Google contacts.csv!A:AM"
).execute()
rows = result.get('values', [])
for i, row in enumerate(rows):
    row_text = '|'.join([str(c) for c in row])
    if 'haldipur' in row_text.lower() or 'trustwell' in row_text.lower():
        # Found associated contact — capture all columns
```

### 3. Gmail — Search for Email Threads Mentioning the Person

Search across all 3 accounts for the person's name. This reveals:
- Associated contacts (people cc'd, replied to)
- Role context (who coordinates what)
- Hospital/entity emails (e.g., `insurance@trustwellhospitals.com`)

```python
service = build_service('gmail', 'v1', service_name='google-draas')
resp = service.users().messages().list(
    userId='me', q='Haldipur', maxResults=20
).execute()
```

## Output Format — WhatsApp-Copyable Markdown Block

The user wants to copy-paste into WhatsApp. Format as a clean markdown code block.

**Structure:**
1. Bold header with the primary person's name highlighted
2. Primary person's contact details (all numbers, email, org)
3. Each associated coordinator/contact with their role description and phone
4. Hospital/entity main contact info (address, email, etc.)

**Example from this session (Aug 2026):**

```
*DR. DEEPAK HALDIPUR - TRUSTWELL HOSPITAL CONTACTS*

Dr. Deepak Haldipur (ENT Specialist)
Trustwell Hospital, J.C. Road, Bengaluru
Phone: +91 80 45666789
Phone: +91 80 45666851
Email: customercare@trustwellhospitals.com

Sridhar (Operations Coordinator - Dr. Haldipur)
Coordinates ENT surgeries, pre-authorisation, scheduling
Phone: +91 94497 84569

Charan (Insurance Coordinator - Trustwell Hospital)
Insurance desk, pre-auth/cashless processing
Phone: +91 98452 52011
Email: insurance@trustwellhospitals.com

Elumali (Dr Haldipur Trustwell - assistant/staff)
Phone: +91 99020 12550

Trustwell Hospital Main
Address: No.5, J.C. Road, Bengaluru - 560 002
UHID for Kanta Ranka: TWH-74537
```

**Key formatting rules:**
- Use `*bold*` for the header (WhatsApp supports *bold*)
- Each contact has: Name (Role), description, phone, email
- Group related contacts together
- Keep it concise — no long explanations, no filler text
- Lead with the answer, not a preamble

## Technical Approach — Write Python Scripts to File, Run via terminal()

The `execute_code` sandbox has issues with escaped quotes in multiline f-strings. When you need to write complex Python that calls `build_service`, use `write_file` to create a `.py` script, then run it via `terminal()`.

**Pattern:**

```python
# 1. Write the script
write_file('/tmp/search_contacts.py', '''
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
# ... full script ...
''')

# 2. Run it
terminal('cd /opt/hermes && python3 /tmp/search_contacts.py', timeout=30)
```

**Why this works:**
- `write_file` handles the content cleanly without escaping issues
- `cd /opt/hermes` ensures the import path is correct
- `terminal()` captures stdout/stderr
- The script can be long and complex without hitting execute_code limits

## Pitfalls

### Pitfall — google-ahfl Token May Be Expired
The google-ahfl account (`ndr@ahfl.in`) often has an expired/revoked token. When this happens:
- Catch the `invalid_grant` error gracefully
- Note in your output that the account was unavailable
- Do NOT fail the whole search — continue with draas and gmail accounts
- The user will need to re-authorize ahfl separately

### Pitfall — Sheet Range Must Include Phone Columns
When querying the contacts sheet, `A:Z` misses phone columns (27+). Always use `A:AM` to capture all 6 phone pairs.

### Pitfall — searchContacts() Only Searches My Contacts
The People API `searchContacts()` only searches "My Contacts", not "Other Contacts". If a contact exists but isn't found, try `connections().list()` as fallback, or check the contacts sheet.

### Pitfall — Voice Transcription Errors
When the user dictates the name via voice, expect transcription errors (e.g., "Haldipur" → may be phonetically correct, but "Sridhar" → "Sreedhar", "Charan" → "Chetan"). Search with partial tokens and phonetic variants.

### Pitfall — Don't Just Search the Primary Name
Search for the hospital/entity name too. The primary contact may be under the doctor's name, but coordinators might be under the hospital name or role title (e.g., "Charan Trustwell Hospital" rather than "Charan Dr Haldipur").

## Session Example (Aug 2026)

User asked: "Check my contacts and emails for trustful hospital doctor Haldipur. Give me a list as a markdown code section WhatsApp which I can copy and paste."

Result: Compiled 5 contacts (Dr. Haldipur, Sridhar op coordinator, Charan insurance, Elumali staff, Trustwell Hospital main) from People API (draas + gmail accounts), contacts sheet, and Gmail threads about Kanta Ranka's ear surgery in July 2026.