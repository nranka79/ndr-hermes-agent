# Family Contact Enrichment — Full Worked Example

This reference documents the exact Google People API calls used in the July 2026 session where the "Mom" contact was enriched to "Kanta Ranka".

## Problem

Family members are often stored in Google Contacts under a simple label-only entry:
- `givenName: 'Mom'`, no `familyName`
- Phone numbers present but NO email, NO nickname
- `searchContacts('Kanta Ranka')` returns nothing
- `searchContacts('Mom')` finds it immediately

## Prerequisites

```python
# Tools setup
from tools.gws_auth import build_service
people = build_service('people', 'v1', service_name='google-draas')
```

## Step 1: Search by the known family label

```python
results = people.people().searchContacts(
    query='Mom',
    readMask='names,phoneNumbers,emailAddresses,userDefined'
).execute()
```

The search may return multiple hits. Filter to the right one by:
- No `familyName` in the names array (label-only entry)
- Likely to have phone numbers but no emails
- May have `resourceName` starting with `people/c5...` or similar

Output from this session's search:
```
Resource: people/c5719516463267783008
  Names: [('Mom', 'Mom', '', 'CONTACT')]
  Phones: ['+919900133634', '+917676839082']
  Emails: []
  UserDefined: []
```

## Step 2: GET the full contact (for etag)

```python
contact = people.people().get(
    resourceName='people/c5719516463267783008',
    personFields='names,phoneNumbers,emailAddresses,userDefined'
).execute()
```

The `etag` from this GET is mandatory in the update call. Output:
```python
contact['etag']  # e.g. '%EigBAgMEBQYHCAkKCwwNDg8QERITFBUWFxkfISIjJCUmJy40NTc9Pj9AGgQBAgUHIgwwNERISHNaMFBwUT0='
contact['names'][0]  # {'displayName': 'Mom', 'givenName': 'Mom', 'metadata': {...}}
contact['phoneNumbers'][0]['canonicalForm']  # '+919900133634' (primary)
```

## Step 3: UPDATE the contact

```python
updated = people.people().updateContact(
    resourceName='people/c5719516463267783008',
    updatePersonFields='names,emailAddresses,userDefined',
    body={
        'etag': contact['etag'],  # FRESH from step 2
        'names': [{
            'givenName': 'Kanta',
            'familyName': 'Ranka',
            'displayName': 'Kanta Ranka',
        }],
        'phoneNumbers': contact['phoneNumbers'],  # PRESERVE existing numbers
        'emailAddresses': [{
            'value': 'kdr@draas.com',
            'formattedType': 'Home',
            'type': 'home',
        }],
        'userDefined': [{
            'key': 'nickname',
            'value': 'Mom',  # The original searchable label
        }],
    }
).execute()
```

### What happens to each field

| Field | Before | After | Note |
|-------|--------|-------|------|
| `givenName` | `'Mom'` | `'Kanta'` | |
| `familyName` | (none) | `'Ranka'` | Added |
| `displayName` | `'Mom'` | `'Kanta Ranka'` | Auto-computed from given+family |
| `phoneNumbers` | 2 numbers | 2 numbers (same) | Passed through unmodified |
| `emailAddresses` | (none) | `kdr@draas.com` / Home | Added |
| `userDefined` | (none) | `key='nickname', value='Mom'` | Added — preserves searchability |
| `etag` | old | new | Refresh for future edits |

## Step 4: Verify

```python
check = people.people().get(
    resourceName='people/c5719516463267783008',
    personFields='names,emailAddresses,userDefined,phoneNumbers'
).execute()

# Check expected values
assert any(n.get('displayName') == 'Kanta Ranka' for n in check.get('names', []))
assert any(e.get('value') == 'kdr@draas.com' for e in check.get('emailAddresses', []))
assert any(u.get('key') == 'nickname' and u.get('value') == 'Mom' for u in check.get('userDefined', []))
```

## Step 5: Use the enriched contact downstream

```python
# Phone for WhatsApp link
phone = check['phoneNumbers'][0]['canonicalForm']  # '+919900133634'

# Email for Calendar attendee
email = 'kdr@draas.com'  # Works even though it was added via the update
```

## Known family contacts and their enrichment status (as of July 2026)

| Label | Enriched To | Resource Name | Phone (primary) | Email |
|-------|-------------|---------------|-----------------|-------|
| Mom | Kanta Ranka | people/c5719516463267783008 | +919900133634 | kdr@draas.com |
| Roshini | Roshini Ranka | people/c5802455324814642701 | +919845026390 | rnr@draas.com |

## Pitfalls

### Etag staleness
The People API returns `400 FAILED_PRECONDITION` if the `etag` in the body doesn't match the server's current version. If the user edits the contact on their phone between your GET and UPDATE, you'll get this error. Fix: re-GET and retry with the new etag.

### `updatePersonFields` must match the body
The `updatePersonFields` parameter is a comma-separated list of which field masks to update. If you include a field in the body but NOT in `updatePersonFields`, it's silently ignored. Conversely, if you list a field in `updatePersonFields` but it's absent from the body, that field is DELETED on the contact.

Safe pattern: `updatePersonFields='names,emailAddresses,userDefined'` matches the three fields being changed. `phoneNumbers` is passed through but not in the mask — it stays as-is.

### Nickname via userDefined is NOT a true nickname
The People API v1 has no dedicated `nickname` property. The `userDefined` field is a general-purpose key-value store. In the Google Contacts UI, it shows under "Custom" with the key visible. This is the closest you can get via API — but the user may see it listed as `nickname: Mom` rather than in the dedicated "Nickname" field.

### Family label searches are case-insensitive but must match exactly
`query='mom'` and `query='Mom'` both find the same contact (People API is case-insensitive). But `query='mommy'` or `query='mother'` will miss it. Use the exact label the user uses in conversation. The NDR family uses:
- "Mom" → Kanta Ranka
- "Roshini" → Roshini Ranka
- "Dad" / "Sanjeev" → Sanjeev Ranka (but he's stored under his real name, not a label)
