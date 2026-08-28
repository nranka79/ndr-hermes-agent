# Contact Creation — Dual Flow (People API + Contacts Sheet)

When the user provides a new contact's details (name, email, phone, organisation), you must add them to **both** Google Contacts (People API) **and** the NDR DRAAS contacts sheet. These are independent data stores — adding to one does not sync to the other.

## Prerequisites

- Run via `terminal()` with Hermes venv Python — the `execute_code` sandbox lacks the gws-vault socket
- Use `service_name='google-draas'` (Nishant's primary work account) for both People API and Sheets API
- Set `HERMES_SESSION_USER_ID=<session-user-id>` (Nishant's Telegram ID)

## Step 1: Add to Google Contacts (People API)

```python
from tools.gws_auth import build_service
people = build_service('people', 'v1', service_name='google-draas')

contact = {
    'names': [{'givenName': 'Antony', 'familyName': 'Century Real Estate'}],
    'emailAddresses': [{'value': 'antony.gm@centuryrealestate.in', 'type': 'work'}],
    'organizations': [{'name': 'Century Real Estate', 'title': 'Sales Head'}],
    'phoneNumbers': [{'value': '+91 96069 13114', 'type': 'work'}]
}

created = people.people().createContact(body=contact).execute()
# Returns resourceName like 'people/c1321574240469770094'
```

**Fields to populate when available:**
- `names[].givenName` — first name (required)
- `names[].familyName` — last name
- `emailAddresses[].value` + `.type` — email with label (work/personal)
- `phoneNumbers[].value` + `.type` — phone with label (work/mobile)
- `organizations[].name` + `.title` — company and role

## Step 2: Add to NDR DRAAS Contacts Sheet

**Sheet ID:** `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`
**Tab name:** `NDR DRAAS Google contacts.csv`

The sheet has 39 columns (0-indexed). Build a row array of empty strings then populate the relevant columns:

| Column Index | Header | Value to Write |
|-------------|--------|----------------|
| 0 | First Name | Contact's first name |
| 2 | Last Name | Contact's surname or company |
| 17 | E-mail 1 - Label | `'Work'` or `'Personal'` |
| 18 | E-mail 1 - Value | Email address |
| 27 | Phone 1 - Label | `'Work'` or `'Mobile'` |
| 28 | Phone 1 - Value | Phone number with +91 prefix |

**⚠️ The sheet has 93 columns, not 39** (verified Jul 2026 by reading the header row). The older code in this file padded to 39 — that was wrong even at the time of the original writeup.

```python
sheets = build_service('sheets', 'v4', service_name='google-draas')
SHEET_ID = '1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g'

# Pad to 93 columns (header row length, verified Jul 2026)
new_row = [''] * 93
new_row[0] = 'Antony'
new_row[2] = 'Century Real Estate'
new_row[17] = 'Work'
new_row[18] = 'antony.gm@centuryrealestate.in'
new_row[27] = 'Work'
new_row[28] = '+91 96069 13114'

body = {'values': [new_row]}
result = sheets.spreadsheets().values().append(
    spreadsheetId=SHEET_ID,
    range="'NDR DRAAS Google contacts.csv'!A1",
    valueInputOption='RAW',  # MUST be RAW — see Pitfall below
    insertDataOption='INSERT_ROWS',
    body=body
).execute()
# Returns updatedRange like 'NDR DRAAS Google contacts.csv'!A4208:CO4208
```

**Key details:**
- **`valueInputOption='RAW'` is mandatory** for any string starting with `+` (phone numbers, e.g. `+91 96069 13114`). Sheets parses `+` as a formula start under `USER_ENTERED` and the cell ends up as `#ERROR!`. Applies to BOTH `append()` and `update()`. Full diagnosis and recovery: see `gws-automation` → `references/people-api-contacts.md` → "Phone number starting with `+` causes `#ERROR!`" pitfall. **(The older "Always use USER_ENTERED" guidance in this file is wrong — superseded Jul 2026.)**
- Use `insertDataOption='INSERT_ROWS'` to append at the bottom.
- Row count is ~4209+ as of Jul 2026 — do not read the full sheet first unless needed.
- Phone format in the sheet includes `+` prefix (e.g. `+91 96069 13114`), unlike the WhatsApp format preference.
- **Enrich an existing row rather than appending a duplicate** when the contact already exists in the sheet (e.g. they were added with just first name + phone, and you now have org/title/notes to add). Pattern: search by first name → read the row → build a 93-col array with merged values → `update()` not `append()`. Session example (Jul 2026): Charan existed as "Charan Trustwell Hospital" with just first name + phone, enriched to add Organization/Title/Department/Notes/Labels.

## Pitfalls

### Execution context
The gws-vault socket (`/run/gws-vault/vault.sock`) is **not** available in `execute_code` sandboxes. Always use `terminal()` with the Hermes venv:
```bash
cd /opt/hermes && HERMES_SESSION_USER_ID=<session-user-id> /opt/hermes/.venv/bin/python3 -c "..."
```

### People API scope
`createContact()` requires the `https://www.googleapis.com/auth/contacts` scope. If it fails with `403 Insufficient Permission`, the user needs to re-authorize with the contacts scope added. Check by calling `has_token(tid, 'google-draas')` — if that passes but People API fails, it's a scope issue, not an auth issue.

### Duplicate detection
The People API does NOT prevent duplicate contacts — it creates a new entry every time. The contacts sheet also appends. Before creating, optionally check if the contact already exists:
- People API: `people.people().searchContacts(query='email@domain.com', readMask='names,emailAddresses').execute()`
- Contacts sheet: scan column 18 for the email

### Pitfall — name-only existing contact vs newly created complete contact (Aug 2026)
`searchContacts(query='Nabeel')` returned an existing entry "Nabil Shiraz" with **no phones and no emails** (a shell contact), and the create flow then made a second, complete "Nabeel Shiraz" record — two contacts for one person. When the pre-check finds a name-only shell:
1. Prefer enriching the shell via `updateContact` (fetch it, add phone/org/email, `etag` required) — OR
2. Create the complete contact AND explicitly flag the duplicate to the user ("want me to merge/delete the empty old one?") — do not silently leave both.
Also note: name spelling may differ between the shell (voice-transcribed "Nabil") and the source of truth ("Nabeel" per WhatsApp profile) — keep the contact name the user's own phone/WhatsApp shows, and surface the discrepancy.

### Service name confusion
Always use `service_name='google-draas'` explicitly — the default `build_service('people', 'v1')` without service_name may resolve to the wrong account. Use `EMAIL_TO_SERVICE['ndr@draas.com']` to verify: it maps to `'google-draas'`.
