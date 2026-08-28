# Contact Update — Dual Flow (People API + Contacts Sheet)

When the user corrects or enriches an existing contact, you must update **both** Google Contacts (People API) **and** the NDR DRAAS contacts sheet independently. These stores are not synced — writing to one does not write to the other.

## Typical Triggers

- User says "that name is wrong, it's actually X"
- User provides additional details (address, email, org, title) after you showed them the current entry
- User says "update this contact with the info from this document"

## Prerequisites

- Always use `service_name='google-draas'` (Nishant's primary work account)
- Use `execute_code` (it has the gws-vault socket) — NOT `terminal()` which lacks it
- Both People API and Sheets API use the same service_name

## Step 1: Find the Contact in Both Stores

Before updating, locate the contact's identifiers:

**Google Contacts:** Search with People API and note the `resourceName` (e.g. `people/c5904931612456596499`):

```python
people = build_service('people', 'v1', service_name='google-draas')
results = people.people().searchContacts(query='Vinay Rera', readMask='names,phoneNumbers').execute()
resource_name = results['results'][0]['person']['resourceName']  # 'people/c5904931612456596499'
```

**Contacts Sheet:** Search the sheet for the row number. The sheet has ~4210 rows as of Jul 2026.

```python
result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range="'NDR DRAAS Google contacts.csv'"
).execute()
for i, row in enumerate(result['values']):
    if 'Vinay' in row[0] or 'vinay' in str(row).lower():
        print(f"Row {i} (A1={i+2}): {row[0]}, {row[2]}")
        # i+2 = A1 row number (header is row 1, data starts row 2)
```

## Step 2: Update Google Contacts

Use `updateContact()` with the resource name and **etag** (prevents overwriting concurrent edits). Pass an `updatePersonFields` mask listing which fields to change.

```python
# Fetch existing contact for etag
existing = people.people().get(
    resourceName='people/c5904931612456596499',
    personFields='names'
).execute()

contact = {
    'etag': existing.get('etag'),  # REQUIRED — prevents overwrite conflicts
    'names': [{
        'givenName': 'Vinay',
        'familyName': 'T',
        'unstructuredName': 'Vinay T'
    }],
    'organizations': [{
        'name': 'Venu and Vinay',
        'title': 'Chartered Accountant'
    }],
    'phoneNumbers': [{
        'value': '+91 93412 46770',
        'type': 'mobile'
    }],
    'addresses': [{
        'streetAddress': 'No 1, Ashoka Pride, 4th floor, Ashoka pillar, Jayanagar',
        'city': 'Bengaluru',
        'postalCode': '560011',
        'type': 'work'
    }],
    'biographies': [{
        'value': 'Chartered Accountant at Venu and Vinay. Office above RERA office.',
        'contentType': 'TEXT_PLAIN'
    }]
}

updated = people.people().updateContact(
    resourceName='people/c5904931612456596499',
    updatePersonFields='names,organizations,phoneNumbers,addresses,biographies',
    body=contact
).execute()
```

**Fields for `updatePersonFields`:** comma-separated list matching the top-level keys in `contact`. Common values:
- `names` — givenName, familyName
- `organizations` — company name + title
- `emailAddresses` — email
- `phoneNumbers` — phone
- `addresses` — physical address
- `biographies` — notes

## Step 3: Update the Contacts Sheet

Use `batchUpdate()` with `valueInputOption='USER_ENTERED'` for individual cell ranges. Unlike creation (which uses `append()` with `RAW` to avoid `+` formula issues), updates to specific cells can use `USER_ENTERED` safely for non-phone fields. For phone fields specifically, still use `RAW` or update them via the same cell-range approach.

### Key Column Map (Row 4066 example = 0-indexed row 4065)

| Column | Letter | Header | Example |
|--------|--------|--------|---------|
| 0 | A | First Name | Vinay |
| 2 | C | Last Name | T |
| 10 | K | Organization Name | Venu and Vinay |
| 11 | L | Organization Title | Chartered Accountant |
| 13 | N | Notes | Updated details |
| 39 | AN | Address 1 - Label | Work |
| 40 | AO | Address 1 - Formatted | "No 1, Ashoka Pride..., Bengaluru 560011" |
| 41 | AP | Address 1 - Street | No 1, Ashoka Pride, 4th floor, Ashoka pillar, Jayanagar |
| 42 | AQ | Address 1 - City | Bengaluru |
| 44 | AS | Address 1 - Region | Karnataka |
| 45 | AT | Address 1 - Postal Code | 560011 |
| 46 | AU | Address 1 - Country | IN |

Full 93-column header row can be read at any time:
```python
headers = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range="'NDR DRAAS Google contacts.csv'!A1:BM1"
).execute()['values'][0]
```

### Batch Update Pattern

```python
body = {
    'valueInputOption': 'USER_ENTERED',
    'data': [
        {'range': "'NDR DRAAS Google contacts.csv'!A4066", 'values': [['Vinay']]},
        {'range': "'NDR DRAAS Google contacts.csv'!C4066", 'values': [['T']]},
        {'range': "'NDR DRAAS Google contacts.csv'!K4066", 'values': [['Venu and Vinay']]},
        {'range': "'NDR DRAAS Google contacts.csv'!L4066", 'values': [['Chartered Accountant']]},
        {'range': "'NDR DRAAS Google contacts.csv'!N4066", 'values': [['Chartered Accountant at Venu and Vinay.']]},
        {'range': "'NDR DRAAS Google contacts.csv'!AN4066", 'values': [['Work']]},
        {'range': "'NDR DRAAS Google contacts.csv'!AP4066", 'values': [['No 1, Ashoka Pride, 4th floor, Ashoka pillar, Jayanagar']]},
        {'range': "'NDR DRAAS Google contacts.csv'!AQ4066", 'values': [['Bengaluru']]},
        {'range': "'NDR DRAAS Google contacts.csv'!AS4066", 'values': [['Karnataka']]},
        {'range': "'NDR DRAAS Google contacts.csv'!AT4066", 'values': [['560011']]},
        {'range': "'NDR DRAAS Google contacts.csv'!AU4066", 'values': [['IN']]},
    ]
}
result = sheets.spreadsheets().values().batchUpdate(
    spreadsheetId=SHEET_ID,
    body=body
).execute()
```

**Note on `valueInputOption`:**
- `USER_ENTERED` works for text fields (names, org, city, notes)
- For phone numbers starting with `+`, use a separate cell update with `RAW`: `{'range': "...", 'values': [['+91 93412 46770']]}` and `valueInputOption='RAW'`
- But if the phone number isn't changing, you can skip it — only pass the fields being updated

## Step 4: Verify

After updating, read back and compare:

```python
# Google Contacts
updated = people.people().get(
    resourceName=resource_name,
    personFields='names,organizations,phoneNumbers,addresses'
).execute()
print(updated['names'][0]['displayName'])
print(updated['organizations'][0]['name'], '-', updated['organizations'][0]['title'])

# Sheet
row = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range="'NDR DRAAS Google contacts.csv'!A4066:AU4066"
).execute()['values'][0]
```

## Common Pitfalls

### 0. Phone-added contacts land in google-ahfl, NOT google-draas (Aug 2026)
Contacts added directly on NDR's phone (Google account sync) appear under the **`google-ahfl`** service (`ndr@ahfl.in`), not the primary work account `google-draas`. When a user says "I just added a contact," run `build_service('people', 'v1', service_name='google-ahfl')` first — `searchContacts` across all three accounts (`gws_resolve_account`) is the reliable pattern. Live example: Ketan Vyas (phone-added) was found only in google-ahfl as `people/c6345992331010789330`, invisible to google-draas searchContacts.
Also note: `searchContacts` misses phone-added contacts that landed in "Other Contacts"; a `connections().list` scan with fuzzy name matching is the fallback.

### 0.5. People API `addresses.formatted` is OUTPUT-ONLY — never send it in updateContact
`updateContact` with an address block containing `'formatted': ...` fails with `HttpError 400: Unknown name "formatted" at 'person.addresses[0]'`. Only send structured fields: `streetAddress`, `city`, `region`, `postalCode`, `country`, `type`. The API computes `formattedValue`/`formattedType` itself and returns them in the response — verify from the response, don't pass them in. (Hit live Aug 2026 updating Ketan Vyas's work address.)

### 1. Missing etag causes rejection
Google People API `updateContact()` **requires** the `etag` from the current version. Always fetch it first:
```python
existing = people.people().get(resourceName=..., personFields='names').execute()
contact['etag'] = existing.get('etag')
```
Without it you get: `"Request must contain only etag of latest resource"`.

### 2. Sheet row number confusion
A1 notation is 1-indexed with header = row 1. If searching gave you 0-indexed row 4065, the A1 row is 4066. Always verify by reading back a cell after writing.

### 3. Address columns beyond current row length
If the existing row only has 29 values (common for old contacts with just name + phone), writing to column AN (index 39) or beyond works fine — the API expands the row. But you MUST use exact column letters in the range string.

### 4. Contact vs row mismatch
The contact may exist in Google Contacts but NOT in the sheet, or vice versa. Check both independently. If it only exists in one, add to the other using the creation flow.

### 5. Name correction vs enrichment
- **Correction** (this session): "Vinay Rera" → "Vinay T". Means overwriting name fields.
- **Enrichment** (adding missing data): Existing "Vinay" gets org, title, address added. Only update the new fields — leave existing data intact.
- The batch update approach handles both — just include or exclude cells as needed.

### 6. Notes column is col 14 (O), NOT col 13 (N) — verify live header first

The sheet header (read `'...csv'!A1:BM1` before writing) shows:
- col 13 = **Birthday** (N)
- col 14 = **Notes** (O)

An older draft of this reference claimed Notes = col 13/N. Trusting it wrote
the note into a contact's **Birthday** cell, silently clobbering that field.
**Rule: ALWAYS print `vals[0]` (the header row) and locate the Notes column
index at write time.** For the NDR DRAAS Google contacts sheet, Notes is
`O<row>` — the row-offset example at the top of this file (col 13 = N) is
stale; the live header is authoritative.

### 7. A1 row offset depends on the values() call shape — read back before/after

`values().get(spreadsheetId, range="'...csv'")` WITHOUT an A1 range returns
ALL rows starting at the header: `values()[0]` IS the header row, so a
0-indexed row `i` = A1 row `i+1`. The "i+2" convention in this file only
applies when you query `range="...!A2:..."` (data starting at row 2).
A row-offset mistake writes into the NEIGHBOURING contact's cells — real
failure (Aug 2026): targeting A1=4120 hit "Viswanath Yehlanka MLA" instead
of "Vishwas Rao" at A1=4119.

**Protocol:** (1) read the full sheet, (2) locate the row by CONTENT
(col 0 match), (3) compute A1 as `i+1`, (4) after the write, read back the
same range and verify col 0 matches the intended contact AND the changed
cell holds the new value. If a neighbouring row was hit, restore it from
People API (source of truth — e.g. `birthdays` empty ⇒ Birthday cell should
be empty) before re-writing the correct row.

### 8. People API does NOT support custom phone labels — free-text labels live in the sheet only

Google People API `PhoneNumber` has NO `customType` field (hit live Aug 2026
updating Puneeth Gill: `updateContact` with `customType: 'USA'` → HttpError 400
"Unknown name customType at 'person.phone_numbers[0]'"). Phone `type` accepts
only the predefined enum (mobile, work, home, homeFax, workFax, otherFax,
pager, workMobile, workPager, main, googleVoice, other). Custom labels like
"IND" / "USA" / "Wapp" are expressible ONLY in the NDR DRAAS contacts sheet
(cols 27-38, free text).

**Consequence:** when the user asks to rename a phone label to something
non-standard (e.g. "rename the Indian number to IND") or label a number
"USA", Google Contacts gets a standard `type` (mobile/work) and the sheet
carries the custom label. Say so in the report — don't silently pretend the
custom label is in both stores. If the user insists the label appear in
Google Contacts too, it can't via API; that's a product limitation of the
People API.

### 9. `updateContactPhoto` response may omit `photos` — verify by re-fetch

After `people.people().updateContactPhoto(resourceName=..., body={'photoBytes': base64})` the returned Person may have `resourceName: None` / `photos: None` even when the upload succeeded. The reliable check is a follow-up `people().get(..., personFields='photos')` — the `photos[0].url` will differ from the pre-update URL (both were `lh3.googleusercontent.com/...`, the path component changes). Never report "photo updated" off the update response alone.

## Session Example (Jul 2026)

**Starting state:** Contact "Vinay Rera" in both stores — name was wrong, labeled as "Rera Consultant" with just name + phone.

**Correction from user:** "Vinay T, Venu and Vinay, Chartered Accountants. No 1, Ashoka Pride, 4th floor, Ashoka pillar, Jayanagar, Bengaluru 560011. M-9341246770."

**Google Contacts update:**
- Changed givenName to "Vinay", familyName to "T"
- Updated organizations: Venu and Vinay — Chartered Accountant
- Added work address with street, city, region, postal code
- Updated biography with corrected info

**Sheet update (row A4066):**
- 12 cells batch-updated: A (First Name), C (Last Name), K (Org), L (Title), N (Notes), AN-AU (Address 1 fields: label, formatted, street, city, region, postal code, country)
- Phone field left unchanged (same number)
