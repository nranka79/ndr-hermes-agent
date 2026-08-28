# Dual Contact Update: Sheet + Google Contacts (People API)

When NDR asks to update/add a contact's info (especially email) to **both** the NDR DRAAS Google contacts spreadsheet AND Google Contacts via People API, follow this two-step workflow.

## Step 1: Update the Contacts Sheet

The sheet is at `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`, tab `NDR DRAAS Google contacts.csv`.

### Key columns (0-indexed, verified Aug 2026):
| Col | Letter | Field |
|-----|--------|-------|
| 17 | R | E-mail 1 - Label |
| 18 | S | E-mail 1 - Value |
| 19 | T | E-mail 2 - Label |
| 20 | U | E-mail 2 - Value |
| 27 | AB | Phone 1 - Label |
| 28 | AC | Phone 1 - Value |
| 31 | AF | Phone 3 - Label |
| 32 | AG | Phone 3 - Value |
| 91 | CN | voice_misspellings |

```python
from tools.gws_auth import build_service
service = build_service('sheets', 'v4', service_name='google-draas')
sheet_id = '1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g'
sheet_name = 'NDR DRAAS Google contacts.csv'

# Update email at row 34, col U (E-mail 2 - Value)
service.spreadsheets().values().update(
    spreadsheetId=sheet_id,
    range=f"'{sheet_name}'!U34",
    valueInputOption='USER_ENTERED',
    body={'values': [['aagney@kelsa.io']]}
).execute()
```

Rows are 1-indexed in the API (header is row 1, data starts at row 2).

## Step 2: Update Google Contacts (People API)

Use `service_name='google-draas'` for the People API.

### Search for existing contact by email:
```python
search = people.people().searchContacts(
    query='aagneysingh6145@gmail.com',
    readMask='names,emailAddresses'
).execute()
```

The response returns `results[0].person.resourceName` — e.g. `people/c8676517920289949046`.

### Add email to existing contact:
```python
contact = people.people().get(
    resourceName=resource_name,
    personFields='emailAddresses,names'
).execute()

existing_emails = contact.get('emailAddresses', [])
existing_emails.append({'value': 'new@email.com', 'type': 'work'})

updated = people.people().updateContact(
    resourceName=resource_name,
    updatePersonFields='emailAddresses',
    body={'emailAddresses': existing_emails, 'etag': contact.get('etag')}
).execute()
```

### Create new contact if not found:
```python
new_contact = {
    'names': [{'givenName': 'First', 'familyName': 'Last'}],
    'emailAddresses': [
        {'value': 'existing@email.com', 'type': 'home'},
        {'value': 'new@email.com', 'type': 'work'}
    ]
}
created = people.people().createContact(body=new_contact).execute()
```

## Pitfalls

### `noun_learner` tool errors on voice misspellings
The `noun_learner` tool with `action='learn_correction'` may fail with:
```
Error writing misspelling: name 'VOCAB_CORRECTIONS_TAB' is not defined
```
**Fix:** Fall back to direct Sheets API update on the `voice_misspellings` column (col 91 = CN). Write comma-separated misspellings: `'agne, agne singh, rehi agne'`

### `readMask` must NOT include `resourceName`
The People API `searchContacts.readMask` does NOT accept `resourceName` as a valid path. Valid paths: `names`, `emailAddresses`, `phoneNumbers`, `organizations`, `addresses`, etc. The `resourceName` is returned automatically — you don't need to request it.

### Email label conventions
- Value `'* Home'` in the Label column = primary/home email
- Value `'* Work'` in the Label column = work email
- When adding via People API, use `'type': 'home'` or `'type': 'work'`
- The sheet stores labels with an asterisk prefix (`* Home`, `* Work`) — replicate that in the Label column when adding rows