# Contact Update — Dual Source (Google Contacts + Sheet)

## When to Use

**Trigger:** User says "update [name]'s contact", "correct [name]'s phone/name/email", "fix the number for [name]" — applies to DRAAS business contacts in Nishant's address book.

**Always update BOTH Google Contacts (People API) AND the NDR DRAAS Google contacts sheet.** One-source updates get corrected in the next lookup.

## Resolution Order

1. **Google Contacts (People API)** — the canonical source for the contact record
2. **NDR DRAAS Google contacts sheet** — the business sheet used by DRAAS staff for lookups

## Google Contacts Update — People API

### Pre-requisites

```python
import os
os.environ["HERMES_SESSION_USER_ID"] = "ndr"  # Nishant's TG ID
from tools.gws_auth import build_service
people = build_service("people", "v1")
```

### Step 1: Find the contact

```python
# Search by email or name
results = people.people().searchContacts(
    query="vivekchanda54@gmail.com",  # or name
    readMask="names,emailAddresses,phoneNumbers"
).execute()
resource = results["results"][0]["person"]["resourceName"]
```

### Step 2: Get full person (including etag)

```python
person = people.people().get(
    resourceName=resource,
    personFields="names,phoneNumbers,emailAddresses,organizations,metadata"
).execute()
etag = person.get("etag", "")
```

### Step 3: Update with etag

**CRITICAL:** `updateContact` REQUIRES `person.etag` in the request body. Without it, Google returns:
```
HttpError 400: "Request must set person.etag or person.metadata.sources.etag for the source that is being updated."
```

```python
update_body = {
    "etag": etag,  # REQUIRED — from Step 2
    "names": [
        {
            "givenName": "Vivek",
            "familyName": "Chandra",
            "displayName": "Vivek Chandra"
        }
    ],
    "phoneNumbers": [
        {
            "value": "+918790300904",
            "type": "mobile"
        }
    ]
}

result = people.people().updateContact(
    resourceName=resource,
    updatePersonFields="names,phoneNumbers,emailAddresses",
    body=update_body
).execute()
```

`updatePersonFields` is a comma-separated list of fields to patch. Valid field names match the People API person field names (e.g. `names`, `phoneNumbers`, `emailAddresses`, `organizations`).

### Common Pitfalls

| Error | Cause | Fix |
|-------|-------|-----|
| 400 "etag required" | `etag` missing from request body | Include `person["etag"]` from GET response |
| 400 "invalid updatePersonFields" | Mask uses sheet-style field names | Use People API field names only (`names`, `phoneNumbers`, `emailAddresses`) |
| 403 "Insufficient authentication scopes" | Token lacks `contacts` scope | Re-authorize with contacts scope; check token scopes first |

## Sheet Update — Google Sheets API

### Pre-requisites

```python
sheets = build_service("sheets", "v4")
SHEET_ID = "1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g"
SHEET_NAME = "NDR DRAAS Google contacts.csv"
```

### Step 1: Locate the row

Search the sheet by name or email to find the row number:

```python
result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range=SHEET_NAME,
    valueRenderOption="FORMATTED_VALUE"
).execute()
rows = result.get("values", [])
headers = rows[0]
data = rows[1:]

for i, row in enumerate(data, start=2):
    def g(idx): return row[idx] if idx < len(row) else ''
    email = g(17)  # E-mail 1 - Value
    if "vivekchanda54@gmail.com" in email:
        row_num = i
        break
```

### Step 2: Update specific cells via batchUpdate

Use `batchUpdate` with `USER_ENTERED` to update individual cells without touching the rest of the row:

```python
body = {
    "valueInputOption": "USER_ENTERED",
    "data": [
        {"range": f"NDR DRAAS Google contacts.csv!A{row_num}", "values": [["Vivek"]]},       # First Name
        {"range": f"NDR DRAAS Google contacts.csv!C{row_num}", "values": [["Chandra"]]},      # Last Name
        {"range": f"NDR DRAAS Google contacts.csv!AB{row_num}", "values": [["918790300904"]]},# Phone 1 - Value
    ]
}
result = sheets.spreadsheets().values().batchUpdate(
    spreadsheetId=SHEET_ID,
    body=body
).execute()
```

### Column Reference (Key Columns for Updates)

| Col Letter | Col Index | Header | Notes |
|-----------|-----------|--------|-------|
| A | 0 | First Name | Update when splitting merged names |
| C | 2 | Last Name | Often empty when name was entered as single field |
| K | 10 | Organization Name | |
| L | 11 | Organization Title | |
| O | 14 | Notes | |
| S | 18 | E-mail 1 - Value | Primary email |
| AA | 27 | Phone 1 - Label | e.g. "Mobile" |
| **AB** | **28** | **Phone 1 - Value** | **Most common phone update target** |

**Always verify column header names via `headers[index]` before writing.** Do not hardcode column letters — they may shift.

### Step 3: Verify

Always read back the updated row after writing:

```python
result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range=f"NDR DRAAS Google contacts.csv!A{row_num}:AM{row_num}",
    valueRenderOption="FORMATTED_VALUE"
).execute()
updated = result.get("values", [[]])[0]
print(f"First Name: {updated[0]} | Last Name: {updated[2]} | Phone: {updated[28]}")
```

## Name Splitting Pattern

DRAAS contacts are often stored with merged first+last names (a Google Contacts export artifact). When a contact shows with no last name:

| Stored As | Should Be | Fix |
|-----------|-----------|-----|
| "Vivekchanda" | First: "Vivek", Last: "Chandra" | Update both sources |
| "Parthasarathy SP" | First: "Parthasarathy", Last: "SP" | Only if user confirms split |

**Always split the name at the obvious first capital letter boundary** (Vivek + Chandra, not Vivekc + handa). Update both Google Contacts and the sheet with the split values.

## Full Workflow Example (Vivek Chandra, June 2026)

1. **Find contact:** Sheets API CSV search for "vivek" → Row 4197: `First Name: Vivekchanda`, `Last Name: ""`, `Phone: 918790300904`
2. **Find in People API:** `searchContacts(query="vivekchanda54@gmail.com")` → resource `people/c76532875042133923` with same data
3. **Get etag:** `people.people().get()` → extract `etag`
4. **Update Google Contacts:** `updateContact(updatePersonFields="names,phoneNumbers", body={etag, names: [{givenName, familyName}], phoneNumbers})`
5. **Update sheet:** `batchUpdate` with two cell ranges (`A4197`, `C4197`) setting First/Last Name
6. **Generate WhatsApp link** with the corrected phone number after confirming with user
