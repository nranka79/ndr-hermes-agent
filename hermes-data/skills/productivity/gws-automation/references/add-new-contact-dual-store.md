# Add New Contact — Dual Store (People API + Contacts Sheet)

When a user sends a contact screenshot/image and says "add this to my Google contacts and the contacts sheet", you must write to **two independent stores**. They do NOT sync.

## Step 0 — Check for Duplicates FIRST

**CRITICAL — user preference (Nishant, Jun 2026):** Before creating ANY new contact, search both stores for existing records by **phone number**. The user explicitly corrected: *"I think the contact was already there under a different name, can you please check that, so we don't have duplication."*

### Search People API by phone number

```python
from tools.gws_auth import build_service
people = build_service('people', 'v1')

# Search by name (People API doesn't support phone-based search directly)
results = people.people().searchContacts(
    query="+919983460447",  # Search by the phone number
    readMask='names,phoneNumbers'
).execute()
matches = results.get('results', [])
if matches:
    for m in matches:
        p = m['person']
        print(f"Found: {p.get('names', [{}])[0].get('displayName')} — {[ph['value'] for ph in p.get('phoneNumbers', [])]}")
```

**Note:** `searchContacts()` only searches "My Contacts", not "Other Contacts". An empty People API result does NOT guarantee the contact is new — continue to sheet search.

### Search the NDR DRAAS contacts sheet by phone number

```python
sheets = build_service('sheets', 'v4')
SHEET_ID = '1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g'
result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID, range="'NDR DRAAS Google contacts.csv'"
).execute()
rows = result.get('values', [])
# Phone columns: Phone 1 Value at idx 27, Phone 2 at idx 30, Phone 3 at idx 33
phone_cols = [27, 30, 33]
target_phone = "99834460447"  # digits only, no + or spaces
for i, row in enumerate(rows):
    for col in phone_cols:
        if col < len(row) and target_phone in row[col].replace(' ', '').replace('+', '').replace('-', ''):
            print(f"Duplicate found at row {i+1}: {row[0]} — {row[col]}")
```

### What to report

Present the search results clearly:

```
✅ Checked for duplicates before adding:
- Google Contacts: [Found/Not found]
- NDR DRAAS sheet: [Found/Not found]
- Existing "Rakesh" entries (same name, different numbers): [listed if any]
```

Only proceed to create the contact after confirming no duplicate exists. If a duplicate is found, update the existing record instead (see "Update Existing Contact" section below).

### Pitfall — User may say "under a different name"

The user sometimes knows a contact was added under a different spelling/alias. Example: "Rakesh" may already exist as "Rakesh Bali Architect" or under their company name. Always search People API by:
1. **Phone number** (most reliable unique identifier) — search as a string
2. **Name** (case-insensitive partial match)
3. **Email** (if available from visiting card)

### Pattern: Create Placeholder Name Then Update With Details

When the user says "add this contact as [Placeholder Name]" then immediately says "rename to [Real Name] with [Company] and [Title]", the cleanest approach is to do it in **two steps within the same script**:

1. **Create** the contact with the placeholder name + email only
2. **Append** a row to the contacts sheet with the placeholder info
3. **Immediately update** both stores with the corrected name, company, and title

This avoids the contact appearing in searches with the wrong name during the gap between creation and rename.

```python
# Step 1 — Create with placeholder
name = "Ravi Off Boy"  # placeholder — user said this first
contact = people.people().createContact(body={
    "names": [{"givenName": "Ravi", "familyName": "Off Boy", "displayName": "Ravi Off Boy"}],
    "emailAddresses": [{"value": "ravivenkatesh666@gmail.com", "type": "work"}]
}).execute()
resource_name = contact.get('resourceName')
etag = contact.get('etag')

# Step 2 — Sheet append
sheets.spreadsheets().values().append(
    spreadsheetId=SHEET_ID, range="'NDR DRAAS Google contacts.csv'!A:CO",
    valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS',
    body={'values': [row]}  # placeholder row
).execute()

# Step 3 — Update with real details (uses etag from step 1)
people.people().updateContact(
    resourceName=resource_name,
    updatePersonFields="names,emailAddresses,organizations",
    body={
        "etag": etag,
        "names": [{"givenName": "Ravi", "familyName": "Venkatesh", "displayName": "Ravi Venkatesh"}],
        "emailAddresses": [{"value": "ravivenkatesh666@gmail.com", "type": "work"}],
        "organizations": [{"name": "DRA Realty Pvt Ltd", "title": "Office Assistant", "type": "work"}]
    }
).execute()

# Step 4 — Update sheet row with corrected info
updated_row = [''] * 93
updated_row[0] = 'Ravi'
updated_row[1] = 'Venkatesh'  # corrected family name
updated_row[10] = 'DRA Realty Pvt Ltd'
updated_row[11] = 'Office Assistant'
sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range=f"'NDR DRAAS Google contacts.csv'!A{row_num}:IR{row_num}",
    valueInputOption='USER_ENTERED',
    body={'values': [updated_row]}
).execute()
```

**When to use this pattern:** Only when the user gives you a placeholder name first and then explicitly says "rename" or "update" with new details. If the user says the full name upfront, just create with the correct name in one step.

### Pitfall — People API `searchContacts()` with `+` in phone number

The `+` sign in phone numbers can cause People API search to miss matches. Either:
- Search by name alone, then verify the phone from results
- Search with the number stripped: `"99834460447"` without `+91`

## Store 1: Google Contacts (People API)

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pathlib import Path

TOKEN_PATH = Path("the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)")
SCOPES = ["https://www.googleapis.com/auth/contacts"]

creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    TOKEN_PATH.write_text(creds.to_json())

people = build("people", "v1", credentials=creds)

contact = {
    "names": [{"givenName": "FirstName", "familyName": ""}],
    "phoneNumbers": [{"value": "+91XXXXXXXXXX", "type": "mobile"}],
    "emailAddresses": [{"value": "email@example.com"}],
    "biographies": [{
        "value": "Notes about the contact — role, company, relationship.",
        "contentType": "TEXT_PLAIN"
    }]
}

created = people.people().createContact(body=contact).execute()
```

## Store 2: NDR DRAAS Google contacts Sheet

Sheet ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`. Tab: `NDR DRAAS Google contacts.csv`.

**IMPORTANT:** Access the sheet via the user's own OAuth token (which has `spreadsheets` scope). SA DWD (`gws_sa`) requires `GOOGLE_SA_KEY` env var which is NOT set — do NOT use it.

### Column map (93 cols, A-CO, verified Jun 2026)

| Idx | Col | Field |
|-----|-----|-------|
| 0   | A   | First Name |
| 9   | J   | File As |
| 10  | K   | Organization Name |
| 11  | L   | Organization Title |
| 14  | O   | Notes |
| 16  | Q   | Labels (use `"* myContacts"`) |
| 17  | R   | E-mail 1 - Label (`"Work"`) |
| 18  | S   | E-mail 1 - Value |
| 26  | AA  | Phone 1 - Label (`"Mobile"`) |
| 27  | AB  | Phone 1 - Value |

### Append

```python
creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    TOKEN_PATH.write_text(creds.to_json())

sheets = build("sheets", "v4", credentials=creds)
new_row = [""] * 93
new_row[0] = "FirstName"
new_row[10] = "Company"       # ⚠️ Col K, NOT col J (File As)
new_row[11] = "Title"         # ⚠️ Col L, NOT col K
new_row[14] = "Notes"
new_row[16] = "* myContacts"
new_row[17] = "Work"
new_row[18] = "email@domain.com"
new_row[26] = "Mobile"
new_row[27] = "+91XXXXXXXXXX"

sheets.spreadsheets().values().append(
    spreadsheetId=SHEET_ID,
    range="'NDR DRAAS Google contacts.csv'!A:CO",
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body={'values': [new_row]}
).execute()
```

## Appending Notes to Existing Contacts (Dual Store — Added Jun 2026)

**User expectation (Nishant):** When asked to "add notes to their contact", update BOTH Google Contacts AND the sheet. Preserve existing notes and APPEND the new entry with a date stamp — never overwrite.

### Read + Append Pattern

Since the user expects both stores to have the same history, always read the current notes first, append the new note with a date stamp, then write back to both stores.

### Store 1: Google Contacts (People API)

```python
from tools.gws_auth import build_service
people = build_service('people', 'v1')

# 1. Find the contact
result = people.people().searchContacts(
    query="Shekhar Raghuvanshi",  # search by name
    pageSize=1,
    readMask='names,biographies'
).execute()
person = result['results'][0]['person']
resource = person['resourceName']

# 2. Get current notes (biographies field) — need full fetch for etag
full = people.people().get(
    resourceName=resource,
    personFields='biographies'
).execute()
existing_note = full.get('biographies', [{}])[0].get('value', '') if full.get('biographies') else ''

# 3. Append new note with date stamp
new_entry = f"\n29 Jun 2026: Met at DRA Realty office at 3pm to discuss Ranka Oasis marketing partnership. Meeting organized by Prakash Singh."
updated_note = existing_note + new_entry

# 4. Update — etag is REQUIRED
update_body = {
    "etag": full.get("etag"),
    "biographies": [{"value": updated_note, "contentType": "TEXT_PLAIN"}]
}
people.people().updateContact(
    resourceName=resource,
    updatePersonFields='biographies',
    body=update_body
).execute()
```

**Key requirements:**
- `etag` is mandatory — always `get()` first to obtain it
- Preserve existing text; append new content with `\n` separator + date prefix
- `updatePersonFields='biographies'` — only update the notes field, leave everything else untouched

### Store 2: NDR DRAAS Google contacts Sheet

```python
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4')
SHEET_ID = '1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g'
RANGE = "'NDR DRAAS Google contacts.csv'"

# 1. Read current notes from column O
result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range=f"{RANGE}!O3355"  # row 3355 = Shekhar's row
).execute()
existing = result.get('values', [['']])[0][0] if result.get('values') else ''

# 2. Append with date stamp
new_entry = "\n29 Jun 2026: Met at DRA Realty office at 3pm to discuss Ranka Oasis marketing partnership. Meeting organized by Prakash Singh."
updated = existing + new_entry

# 3. Write back using RAW (not USER_ENTERED — avoids formula parsing issues)
sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range=f"{RANGE}!O3355",
    valueInputOption='RAW',
    body={'values': [[updated]]}
).execute()
```

**Finding the correct row:** Use `batchGet` to scan column A for matching names:
```python
result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range=f"{RANGE}!A:Z"
).execute()
for i, row in enumerate(result.get('values', [])):
    if row and ('Shekhar' in row[0] or 'shekhar' in row[0].lower()):
        print(f"Row {i+1}: {row[0]}")  # +1 for 1-indexed sheet row
```

**Important:** Sheet rows are 1-indexed (row 1 = header). The API returns 0-indexed arrays, so add 1 when constructing the range.

### Combined Verification

```python
# Verify People API
p = people.people().get(resourceName=resource, personFields='biographies').execute()
print(f"People API notes: {p.get('biographies', [{}])[0].get('value', 'N/A')}")

# Verify Sheet
r = sheets.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=f"{RANGE}!O3355").execute()
print(f"Sheet notes: {r.get('values', [['N/A']])[0][0]}")
```

## Update Existing Contact

When the user provides corrected info for a contact already in both stores, update — don't delete and re-add.

### Store 1: Google Contacts (People API)

Search by name or phone, then update:

```python
people = build("people", "v1", credentials=creds)

# Search for the contact
results = people.people().searchContacts(
    query="Bhaskar Shetty +918880473555",
    pageSize=1,
    readMask="names,organizations,biographies,phoneNumbers"
).execute()
contacts = results.get("results", [])

if contacts:
    resource_name = contacts[0]["person"]["resourceName"]
    
    # Get the current person (needed for etag)
    person = people.people().get(
        resourceName=resource_name,
        personFields="names,organizations,biographies,phoneNumbers"
    ).execute()
    
    update_body = {
        "etag": person["etag"],
        "names": [{"givenName": "Bhaskar", "middleName": "BN", "familyName": "Shetty"}],
        "organizations": [{"name": "Spectral Insights Pvt. Ltd.", "title": "Director - Supply Chain Management"}],
        "biographies": [{"value": "Updated notes here.", "contentType": "TEXT_PLAIN"}],
        "phoneNumbers": [{"type": "mobile", "value": "+918880473555"}]
    }
    
    result = people.people().updateContact(
        resourceName=resource_name,
        updatePersonFields="names,organizations,biographies,phoneNumbers",
        body=update_body
    ).execute()
```

**⚠️ etag is required** — the updateContact call fails without `etag` matching the current server state. Always fetch the person first to get the etag, don't cache it.

### Store 2: NDR DRAAS Google contacts Sheet

Use `batchUpdate` to update specific cells by row number:

```python
updates = {
    "valueInputOption": "USER_ENTERED",
    "data": [
        {"range": "'NDR DRAAS Google contacts.csv'!B4199", "values": [["BN"]]},            # Middle Name
        {"range": "'NDR DRAAS Google contacts.csv'!K4199", "values": [["New Company"]]},    # Org Name (col K)
        {"range": "'NDR DRAAS Google contacts.csv'!L4199", "values": [["New Title"]]},      # Title (col L)
        {"range": "'NDR DRAAS Google contacts.csv'!O4199", "values": [["New notes"]]},      # Notes
    ]
}

sheets.spreadsheets().values().batchUpdate(
    spreadsheetId=SHEET_ID, body=updates
).execute()
```

## Pattern: Existing in People API, Not in Sheet

When a contact already exists in Google Contacts (People API) but not in the NDR CONTACTS sheet:

1. **Update the People API contact** (don't create a duplicate) — use `get` → `updateContact`
2. **Append to NDR CONTACTS sheet** as a new row (since it's missing)
3. If the People API contact has a different phone than expected, keep BOTH numbers — mark the existing one as `mobile` and the email-sig one as `work`

**Concrete example (Jun 2026 — Nilesh Prasar):**
- People API had: `"Nilesh Prasar Kotak Mgr"` with `+91 99059 54753` (type: other, unorganized name)
- Gmail signature had: `+91-8095506021` with proper title (DVP - Kotak Mahindra Bank)
- Action: Updated People API contact (structured name, org, both phones with correct types) + appended row to NDR CONTACTS sheet

## Pitfalls

### 1. Phone number starting with `+` causes formula `#ERROR!` in Sheets

When writing a phone number like `+91 99059 54753` to a Google Sheet using `valueInputOption='USER_ENTERED'`, Sheets interprets it as a formula (cells starting with `+` are formulas). 

**Fix:** Use `valueInputOption='RAW'` instead, or write the number without the `+` prefix in a plain-text column:
```python
# WRONG — produces #ERROR! in the cell:
sheets.spreadsheets().values().update(
    ..., valueInputOption='USER_ENTERED', body={'values': [['+91 99059 54753']]})

# RIGHT — use RAW to bypass formula parsing:
sheets.spreadsheets().values().update(
    ..., valueInputOption='RAW', body={'values': [['+91 99059 54753']]})
```

**Alternative:** Write as text by using a leading space or storing in the notes column if the column format is already text.

### 2. Off-by-one on Organization Name (Col K, index 10) vs File As (Col J, index 9)

**This is the most common mistake when appending contacts.** The Google Contacts export layout places `File As` at column J (index 9) and `Organization Name` at column K (index 10). It's extremely easy to write the company name into the File As column by accident.

**Symptoms of this bug:** Company name shows up in the `File As` column in the sheet instead of `Organization Name`. The contact may still look fine in Google Contacts (which syncs independently), but the sheet has misaligned data.

**How it happens — code before/after:**
```python
# WRONG — Org Name written to File As column:
row[9] = "Company"   # ❌ Col J = File As, not Org Name
row[10] = "Title"    # ❌ Col K = Org Name, not Title

# RIGHT — correct columns:
row[10] = "Company"  # ✅ Col K = Organization Name
row[11] = "Title"    # ✅ Col L = Organization Title
```

**Verification:** After appending, read back the row and confirm:
- Company name appears in column K (index 10), not column J (index 9)
- Title appears in column L (index 11), not column K (index 10)

### 2. Searching with phone number containing `+`

The People API `searchContacts` query with a `+` sign (e.g. `+918880473555`) may fail to match. Search by name alone instead, then verify the phone from the results.

### 3. gws_sa unavailable — GOOGLE_SA_KEY not set

Use user OAuth token for sheets access instead.

### 4. Use append, not direct update — sheet auto-extends on append.

### 5. Notes field — in People API use `biographies[].value`; in sheet use column O (idx 14).

### 6. Phone label — `"Mobile"` (idx 26), not "mobile" or "Cell".

### 7. Email label — `"Work"` (idx 17).
