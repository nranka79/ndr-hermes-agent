# People API: finding a contact's email by name

## When to use
User says "X's email is on my <account> account, find it" — the lookup happens
in Google contacts (People API), NOT in the contact registry spreadsheet
(the registry is for phone lookup; email search goes through People API or the
registry sheet depending on the ask — see `contact-phone-lookup` skill).

## Working pattern (contacts scope only)
The OAuth grant for these accounts includes `contacts` but NOT `profile`.
So `people/me` with `personFields='emailAddresses'` 403s:

```
HttpError 403 ... "The caller does not have permission to request \"people/me\".
Request requires one of the following scopes: [profile]."
```

That is expected — do NOT treat it as a broken token or chase profile scope.
Use `searchContacts` instead, which works with the contacts scope:

```python
from tools.gws_auth import build_service
people = build_service('people', 'v1', service_name='google-draas')  # correct service per account
res = people.people().searchContacts(
    query='Salman Khalid',
    readMask='names,emailAddresses,phoneNumbers,organizations'
).execute()
for r in res.get('results', []):
    p = r.get('person', {})
    # p['names'][0]['displayName'], p['emailAddresses'][0]['value'],
    # p['phoneNumbers'][0]['value'], p.get('organizations')
```

## Pitfalls
- Run via `terminal()`, not `execute_code` — the sandbox lacks the vault
  socket env var (standard GWS rule).
- Duplicate contacts are common: one entry has the email, a sibling entry has
  only a phone. Cross-check phones (e.g. 98454 vs 98455 — near-identical
  numbers may be data-entry typos for the same person). Pick the entry WITH
  the email, and confirm the phone matches what the user expects.
- Contacts search honors the account isolation rule: for DRAAS contacts use
  `service_name='google-draas'` (never ahfl.in unless asked). The user said
  "on my Dras account" → google-draas, resolved via `gws_resolve_account`
  semantics (EMAIL_TO_SERVICE) — never hand-type a service name guess.
- `HERMES_SESSION_USER_ID=ndr` (slug) prefix is required in terminal for
  correct session identity, same as every GWS operation.
