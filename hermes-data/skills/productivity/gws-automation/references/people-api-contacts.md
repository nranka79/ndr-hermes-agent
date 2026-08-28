# People API — Google Contacts Management

Search, read, and update Google Contacts via the People API v1.

## Build Service

```python
from tools.gws_auth import build_service
people = build_service("people", "v1")
```

Uses the user's OAuth token — no SA needed.

## Search Contacts

```python
# Search by name/email
results = people.people().searchContacts(
    query="Nilesh Prasar",
    pageSize=10,
    readMask="names,phoneNumbers,emailAddresses,organizations"
).execute()

for r in results.get("results", []):
    p = r["person"]
    resource_name = p["resourceName"]
    names = [n["displayName"] for n in p.get("names", [])]
    phones = [ph["value"] for ph in p.get("phoneNumbers", [])]
    emails = [e["value"] for e in p.get("emailAddresses", [])]
```

### Important: Search Granularity
- Queries are partial-match on name/email. "Nilesh Prasar" will find "Nilesh Prasar Kotak Mgr".
- Shorter queries return more results: "Jitu" returns all contacts with "Jitu" anywhere in the name (including "Jitu Mehta", "Jitu Bhai Showoff", etc.)
- Searches by email substring may return empty if the contact's email is stored differently.

### Disambiguation via Email Cross-Reference

When a name search returns multiple contacts, resolve the right one by matching the known email address or domain:

```python
results = people.people().searchContacts(
    query="Kishan", pageSize=10,
    readMask="names,phoneNumbers,emailAddresses"
).execute()

target_email = "kishan@flamebackcapital.com"  # known from email thread
target = None
for r in results.get("results", []):
    person = r["person"]
    emails = [e["value"] for e in person.get("emailAddresses", [])]
    if target_email in emails:
        target = person
        break

phone = target["phoneNumbers"][0]["value"]  # "+919845020921"
```

This is more reliable than name-only matching — partial names (e.g. "Kishan", "Nair") can collide with unrelated contacts.

### Fallback: connections().list() for Full Contact Scan

When `searchContacts()` returns no results or ambiguous results, use `connections().list()` to scan ALL contacts and filter programmatically. This also enables searching by organization name, which `searchContacts()` does not index:

```python
# List all connections (max 1000) and search by org name
connections = people.people().connections().list(
    resourceName='people/me',
    pageSize=1000,
    personFields='names,phoneNumbers,emailAddresses,organizations'
).execute()

target_org = "bodycraft"  # search by partial org name
matches = []
for p in connections.get('connections', []):
    orgs = p.get('organizations', [])
    for org in orgs:
        if target_org.lower() in org.get('name', '').lower():
            names = p.get('names', [])
            match = {
                'name': names[0].get('displayName','') if names else 'No name',
                'email': [e['value'] for e in p.get('emailAddresses', [])],
                'phone': [ph['value'] for ph in p.get('phoneNumbers', [])],
                'org': org.get('name',''),
            }
            matches.append(match)

# Empty result check
if not matches:
    print(f"No contacts found matching org: {target_org}")

# For ambiguous matches, present options to user
for m in matches:
    print(f"{m['name']} | {m['email']} | {m['phone']} | {m['org']}")
```

**Also works for dual-name contacts** — e.g., a person stored as "Sunny Sadhwani" (display name) who also goes by "Rajesh Sadhwani" (email alias). Searching `query="Rajesh Sadhwani"` via `searchContacts` will find "Sunny Sadhwani" if the phone or email is associated with both names.

**Search speed:** `connections().list()` with `pageSize=1000` returns instantly even with 1000 contacts. Use it as a first-resort search when `searchContacts` is unreliable for your query pattern.

**Pitfall:** `connections().list()` requires the `personFields` parameter to specify which data to return. Without it you get only `resourceName` and `etag`. Always include `names,phoneNumbers,emailAddresses,organizations` as a minimum. You cannot paginate beyond 1000 for a single `list()` call — Google limits the total connections returned per request. For contacts exceeding 1000, use `nextPageToken` from the response to paginate.```

```python
results = people.people().searchContacts(
    query="Kishan", pageSize=10,
    readMask="names,phoneNumbers,emailAddresses"
).execute()

target_email = "kishan@flamebackcapital.com"  # known from email thread
target = None
for r in results.get("results", []):
    person = r["person"]
    emails = [e["value"] for e in person.get("emailAddresses", [])]
    if target_email in emails:
        target = person
        break

phone = target["phoneNumbers"][0]["value"]  # "+919845020921"
```

This is more reliable than name-only matching — partial names (e.g. "Kishan", "Nair") can collide with unrelated contacts.

## Update Contact

Use `updatePersonFields` to specify which fields to update (comma-separated). The `etag` from the existing contact is required for optimistic concurrency.

```python
updated = people.people().updateContact(
    resourceName="people/c7449768736708908189",  # from search result
    updatePersonFields="names,phoneNumbers,organizations",
    body={
        "etag": "%EgoBAgkLDC43PT4/GgECIgxxVmlLSE9RWHZGdz0=",
        "names": [
            {
                "givenName": "Nilesh",
                "familyName": "Prasar",
                "unstructuredName": "Nilesh Prasar"
            }
        ],
        "phoneNumbers": [
            {"value": "+91 99059 54753", "type": "mobile"},
            {"value": "+91 8095506021", "type": "work"}
        ],
        "organizations": [
            {
                "name": "Kotak Mahindra Bank",
                "title": "Deputy Vice President - Branch Manager",
                "type": "work"
            }
        ]
    }
).execute()
```

## Known Contact Entries (Discovered Jun 2026)

| Name | Key | Phone | Email |
|------|-----|-------|-------|
| Jitu Virwani | people/c6513055202931002610 | +91 9844065000 | jitu@embassyindia.com |
| Nagaveni | — | +91 9844007300 | nagaveni@embassyindia.com |
| Ashwin Pai | — | +91 9972042131 | ashwin.pai@centuryrealestate.in |
| Nilesh Prasar | people/c7449768736708908189 | +91 99059 54753 / +91 8095506021 | Nilesh.Prasar@kotak.com |
| Anbarasan (Anbu) | — | +91 8150029900 | pm2.blr@draas.com |

## WhatsApp Link from Found Contact

After identifying the right contact, generate a WhatsApp link with `whatsapp_link` tool, pre-filling the message with context from the email thread:

```python
# From your toolset — use the whatsapp_link tool, not manual URL construction
# whatsapp_link(phone=phone, text=message)
# The tool accepts any phone format (strips non-digits) and builds the wa.me URL
```

Common message structure: reference the specific transaction/thread → state what you know → ask a focused question. Keep pre-filled messages concise — WhatsApp renders the link preview, not the full text.

## Contact Source of Truth — Sheet Only

DRAAS maintains exactly **one** contacts spreadsheet:

**NDR DRAAS Google contacts** — `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`
   - Tab: `NDR DRAAS Google contacts.csv` (93 columns, 4200+ rows)
   - Other tabs: projects, land_proposals, entities, topics, vocab_corrections, employees
   - This is the canonical raw-contact export sheet. Use for lookups and updates.
   - Build the People API body from the `person` object's `etag` for updateContact

**⚠️ No other contact sheets are maintained.** Any other sheet named like "NDR CONTACTS" (`1fYa-t2RY1siy2qBgAH8uu_Jd2chjJ716BbcpxilpOK0` — ~12 rows) is stale and irrelevant.

## Dual-Update Pattern — Contact from Visiting Card / Image

When adding or updating contact data from a visiting card photo or image, always update **both** Google Contacts (People API) **and** the contacts sheet. The sheet feeds lookup workflows; People API feeds WhatsApp/Gmail auto-complete.

### Workflow
1. **Extract phone** from image (OCR or vision)
2. **Search both sources**: People API (`searchContacts` then `connections().list()` fallback) + Sheets query
3. **Present current vs proposed** field mapping to user before writing
4. **Update simultaneously**:
   - People API: `people().updateContact()` with `etag` and `updatePersonFields`
   - Sheet: `sheets.spreadsheets().values().update()` with full 93-column row

### Search by Phone via connections().list()

`searchContacts(query=phone)` often fails for phone numbers. The reliable fallback is scanning all connections:

```python
connections = people.people().connections().list(
    resourceName='people/me',
    pageSize=1000,
    personFields='names,phoneNumbers,emailAddresses,organizations,biographies,addresses'
).execute()

target_phone = "9845040621"  # digits only, strip +91
for p in connections.get('connections', []):
    for ph in p.get("phoneNumbers", []):
        raw = ph.get("value", "").replace(" ", "").replace("-", "").replace("+91", "")
        if target_phone in raw:
            # Found — use p.get('resourceName') and p.get('etag') for update
```

### Sheet Update — Full Row 
```python
row = [''] * 93  # Always pad to 93 columns
row[0]  = 'Mahendra'       # First Name
row[1]  = 'Kumar'          # Middle Name
row[2]  = 'Jain'           # Last Name
row[6]  = 'Mr.'            # Name Prefix
row[9]  = 'Mahendra Kumar Jain'  # File As
row[10] = 'M K Silk Creations'   # Organization Name
row[11] = 'Manufacturer & Exporter'  # Title
row[14] = 'Notes about contact'  # Notes
row[17] = 'Work'           # E-mail 1 - Label
row[18] = 'accounts@mksilk.com'  # E-mail 1 - Value

sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range=f"'{TAB}'!A{row_num}:IR{row_num}",
    valueInputOption='USER_ENTERED',
    body={'values': [row]}
).execute()
```

## Address Type Limitation — No Custom Types, But Custom Labels via `formattedType`

The People API v1 only supports three address types: `home`, `work`, and `other`. Attempting to use `customType` with `type='custom'` returns:

```
HttpError 400: Unknown name "customType" at 'person.addresses[0]': Cannot find field.
```

**However**, you CAN set a custom display label for addresses using the `formattedType` field alongside a valid `type`. Even though the API constrains `type` to `home/work/other`, the `formattedType` renders as the visible label in Google Contacts UI:

```python
addr = {
    'type': 'work',                    # Must be home/work/other
    'formattedType': 'Hospital Address',  # Custom label — displays in UI
    'formattedValue': 'Dr. BRA IRCH Building, AIIMS Hospital, Ansari Nagar, New Delhi - 110029',
    'streetAddress': 'Room No. 216, Second Floor, IRCH Building, AIIMS Hospital',
    'city': 'New Delhi',
    'region': 'Delhi',
    'postalCode': '110029',
    'country': 'India'
}
```

**When to use:** Any address that is neither a home nor a standard work address — "Hospital Address", "Clinic", "Branch Office", "Warehouse", "Vacation Home". The `formattedType` field is purely display-side — it survives `updateContact()` and shows as the address label in Google Contacts.

**Pitfall:** This applies ONLY to `addresses`. Other repeatable fields (phoneNumbers, emailAddresses) do NOT have a `formattedType` equivalent — for those, only the supported `type` values (home, work, other, mobile) are available.

## Create New Contact

When creating a contact for someone who doesn't exist yet in Google Contacts, use `people().createContact()`:

```python
new_contact = {
    "names": [{
        "givenName": "Manisha",
        "familyName": "Loonker",
        "displayName": "Manisha Loonker"
    }],
    "phoneNumbers": [{"value": "+91 9945055525", "type": "mobile"}],
    "addresses": [{
        "type": "other",
        "streetAddress": "True Blue Napa Valley, Villa 41C",
        "extendedAddress": "Nitte Meenakshi College Rd, BSF Campus",
        "city": "Yelahanka",
        "region": "Bengaluru",
        "postalCode": "560064",
        "country": "India",
        "countryCode": "IN"
    }]
}

created = service.people().createContact(body=new_contact).execute()
print(f"Created: {created.get('resourceName')}")
```

**Note:** Unlike updateContact, createContact does NOT require an `etag`. The `resourceName` is returned in the response — save it for future updates.

### Full-Featured Create Example (all fields)

When creating a professional contact with title, organization, honorific, and address, use the correct field names — the API rejects invalid ones with `400`:

```python
contact = {
    "names": [{
        "givenName": "Sameer",          # First name
        "familyName": "Rastogi",        # Last name
        "honorificPrefix": "Dr.",       # ✅ CORRECT — NOT "prefix" (400 error)
        "displayName": "Dr. Sameer Rastogi",
        "displayNameLastFirst": "Rastogi, Dr. Sameer"
    }],
    "emailAddresses": [{
        "type": "work",
        "value": "samdoc_mamc@yahoo.com"
    }],
    "phoneNumbers": [{
        "type": "mobile",
        "value": "+919953307551"
    }],
    "organizations": [{
        "type": "work",
        "name": "AIIMS New Delhi",
        "title": "Professor, Sarcoma Medical Oncology",
        "department": "Dr. B. R. A. Institute Rotary Cancer Hospital (IRCH)"
    }],
    "addresses": [{
        "type": "work",                 # Only work/home/other — no custom types
        "streetAddress": "Ansari Nagar East, AIIMS",
        "city": "New Delhi",
        "region": "Delhi",
        "postalCode": "110029",
        "country": "India",
        "countryCode": "IN"
        # Do NOT include "formatted" — it's read-only, causes 400 on write
    }]
}

created = people.people().createContact(
    body=contact,
    personFields="names,emailAddresses,phoneNumbers,organizations,addresses"
).execute()
```

**⚠️ `honorificPrefix` NOT `prefix`** — The field `"prefix": "Dr."` causes a 400 error: `Unknown name "prefix" at 'person.names[0]': Cannot find field.` The correct field name is `"honorificPrefix"`.

**⚠️ Address `formatted` is read-only** — Including `"formatted": "..."` in an address object causes a 400 error on create/write. Google computes the formatted address from the individual fields. Only set `streetAddress`, `city`, `region`, `postalCode`, `country`, `countryCode`.

## Delete Duplicate Contact

When you find a garbled/duplicate contact entry, use `deleteContact()`:

```python
# Get the resourceName from search first
search = people.people().searchContacts(
    query="Annie Mam Irch Sameer Rastogi",
    readMask="names"
).execute()

if search.get('results'):
    resource_name = search['results'][0]['person']['resourceName']
    people.people().deleteContact(resourceName=resource_name).execute()
    print(f"Deleted: {resource_name}")
```

**Note:** `deleteContact()` does NOT require an etag. It permanently removes the contact with no undo.

## Pitfalls

- **`readMask` vs `personFields`** — `searchContacts()` uses `readMask` parameter (comma-separated field names); `connections().list()` uses `personFields` parameter. They are NOT interchangeable — using the wrong one causes errors.
- **`honorificPrefix` NOT `prefix`** — The name field for title/honorific is `honorificPrefix`, not `prefix`.
- **Addresses: `formatted` is read-only** — Google computes the formatted address. Only write individual fields (`streetAddress`, `city`, `region`, `postalCode`, `country`).
- **Addresses: no custom types** — Only `home`, `work`, `other`. Custom labels like "Bungalow" are not supported via API on write.
- **Phone number starting with `+` causes `#ERROR!` in Sheets** if using `valueInputOption='USER_ENTERED'` — Sheets parses `+91...` as a formula. Use `valueInputOption='RAW'` or prepend with `'` to force text. If you already wrote cells with `USER_ENTERED` and they show `#ERROR!`, the recovery pattern is: clear the cells first (`spreadsheets().values().clear()`), then re-write with `RAW` input option. (Clearing + re-writing with `RAW` prevents the formula parser from re-triggering on the existing error state.)
- **`searchContacts` is not a full-text search of all stored fields** — it searches names, email addresses, and phone numbers. It does NOT search notes, addresses, or custom fields.
- **Contacts with unstructured names** (e.g., "Nilesh Prasar Kotak Mgr" stored as a single `unstructuredName`) will still match on any substring. After updating to structured names (`givenName` + `familyName`), future searches remain case-insensitive.
- **Email signature phone numbers may be wrong** — Always verify with the user before using for WhatsApp links.
