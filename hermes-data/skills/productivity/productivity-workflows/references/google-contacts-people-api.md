# Google Contacts — People API Quick-Reference

## Core Task: Add Contact + Notes (Two-Step Required)

Google People API does **not** accept a plain-text `notes` field on contact creation.
You MUST use a two-step pattern.

### Step 1 — Create contact (no notes)

```python
import requests, json

with open('/data/hermes/google_token.json') as f:
    d = json.load(f)
headers = {'Authorization': 'Bearer ' + d['access_token']}

payload = {
    "names": [{"givenName": "G.", "familyName": "Venkatesh"}],
    "phoneNumbers": [{"value": "+91 96115 01955", "type": "mobile"}],
    "emailAddresses": [{"value": "venkateshg.surveyor@gmail.com", "type": "home"}],
    "organizations": [{"name": "Surveyor & Loss Assessor", "type": "work"}],
    "addresses": [{"streetAddress": "No 321/A, Shop No-2, Ground Floor, Manjunatha Nilaya, 4th B Cross, Kaggadasapura, C V Raman Nagar Post",
                   "city": "Bangalore", "postalCode": "560093", "type": "home"}]
}
resp = requests.post(
    'https://people.googleapis.com/v1/people/connections:createContact',
    headers=headers, json=payload
)
resource_id = resp.json()['resourceName'].replace('people/', '')
# e.g. 'c2203997730023703418'
```

### Step 2 — Fetch etag, then PATCH notes

```python
# 2a. GET to retrieve etag (required for all PATCH operations)
resp = requests.get(
    f'https://people.googleapis.com/v1/people/{resource_id}',
    headers=headers,
    params={'personFields': 'userDefined'}
)
person = resp.json()
etag = person['etag']  # e.g. '#RviCLZ8nDi4='

# 2b. PATCH notes via userDefined field
note_text = "Surveyor for Jaguar car insurance. Contacted on 25 May 2026..."
patch_payload = {
    "userDefined": [{"key": "Notes", "value": note_text}]
}
resp = requests.patch(
    f'https://people.googleapis.com/v1/people/{resource_id}:updateContact',
    headers=headers,
    params={'updatePersonFields': 'userDefined'},  # NOT personFields!
    json=patch_payload
)
# Status 200 = success
```

## Critical API Gotchas

| Mistake | Correct |
|---------|---------|
| `params={'personFields': ...}` on PATCH | `params={'updatePersonFields': ...}` |
| Trying to set `notes` on creation | Use `userDefined` field via separate PATCH |
| PATCH without etag in body | Get etag first via GET, People API requires it |
| `people/` prefix on resource ID in PATCH URL | PATCH URL needs full `:updateContact` suffix, ID without `people/` prefix works |
| PATCH with stale etag | Get fresh etag before each PATCH |

## Query Parameters: `personFields` vs `updatePersonFields`

- **`personFields`** — used on GET (read): controls which fields are returned
- **`updatePersonFields`** — used on PATCH `:updateContact` (write): declares which fields to update

Never confuse the two on PATCH calls.

## Finding an Existing Contact's Resource ID

```python
resp = requests.get(
    'https://people.googleapis.com/v1/people/me/connections',
    headers=headers,
    params={
        'personFields': 'names,emailAddresses,phoneNumbers',
        'pageSize': 100
    }
)
for person in resp.json().get('connections', []):
    for name in person.get('names', []):
        if 'Venkatesh' in name.get('displayName', ''):
            print(person['resourceName'])  # e.g. 'people/c2203997730023703418'
            print(person['etag'])
```

## Fields Available on Creation

These CAN be set in the initial POST (no PATCH needed):
- `names`, `phoneNumbers`, `emailAddresses`, `organizations`, `addresses`, `urls`, `occupations`, `jobs`

These require a separate PATCH:
- `userDefined` (custom fields like Notes)
- `biographies`
- `relations`
- `interests`

## Token Refresh

```python
import requests, json
with open('/data/hermes/google_token.json') as f:
    d = json.load(f)
# If token is expired, refresh via token_uri
if d.get('expiry', '') < datetime.now().isoformat():
    resp = requests.post(d['token_uri'], data={
        'grant_type': 'refresh_token',
        'refresh_token': d['refresh_token'],
        'client_id': d['client_id'],
        'client_secret': d['client_secret']
    })
    d['access_token'] = resp.json()['access_token']
    # Update expiry...
```

## Google Sheet Row Append (for contacts registry)

```
Sheet ID: 1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g
Tab: "NDR DRAAS Google contacts.csv"
Append: POST https://sheets.googleapis.com/v4/spreadsheets/{sheetId}/values/{range}:append
Value input option: USER_ENTERED
```

## Credentials

- Token file: `/data/hermes/google_token.json` (OAuth2 user token for Gmail/Contacts/Calendar)
- **NOT** `gws_sa.py` — that is for shared business data only (sheets), not personal user data (contacts)