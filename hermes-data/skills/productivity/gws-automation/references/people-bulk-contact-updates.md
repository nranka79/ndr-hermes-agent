# People API — Bulk Contact Updates (add address/URL to many contacts, strip emails)

Verified 2026-08-10 (DRA office-address rollout + departed-employees cleanup).

## Use case
NDR asks to touch a whole class of contacts at once:
- "Add the DRA office address + map link to Nishant, Roshini and every employee with a @draas.com email"
- "Delete the @draas.com addresses of employees no longer with us" (keep their personal emails)

## Non-negotiable setup (both cases)

1. **Pin the session user.** The terminal env `HERMES_SESSION_USER_ID` can resolve to
   the WRONG vault user (observed: `[REDACTED-TID]` → psingh, not ndr). Symptom:
   `VaultNoTokenError: No google-gmail token for user psingh-...` even though the
   session IS ndr. Before any bulk op, verify identity by listing a marker contact
   (Papaji / Roshini Ranka) and ALWAYS run with:
   ```python
   os.environ['HERMES_SESSION_USER_ID'] = 'ndr'
   os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
   ```
2. **`build_service` signature is `build_service(api, version, service_name=...)` —
   NO `telegram_id` kwarg.** Older skill references showing
   `build_service('people','v1', telegram_id='ndr', service_name='google-draas')`
   are STALE: it raises `TypeError: build_service() got an unexpected keyword
   argument 'telegram_id'`. Call it as `build_service('people','v1', service_name='google-draas')`.
3. Service names: `google-draas` (ndr@draas.com), `google-gmail`
   (nishantranka@gmail.com), `google-ahfl` (ndr@ahfl.in). Work contact book =
   google-draas; personal contacts mirror into google-gmail. Run BOTH when the
   user says "all contacts".

## Listing all contacts with an email-domain filter

`people().searchContacts(query=...)` only matches name/email fragments and is
unreliable for domain-wide enumeration. Use paginated `connections().list` and
filter in Python:

```python
svc = build_service('people', 'v1', service_name='google-draas')
token = None
while True:
    res = svc.people().connections().list(
        resourceName='people/me', pageSize=1000, pageToken=token,
        personFields='names,emailAddresses'
    ).execute()
    for p in res.get('connections', []):
        emails = [e.get('value','') for e in p.get('emailAddresses', [])]
        if any(e.lower().endswith('@draas.com') for e in emails):
            ...  # collect resourceName + displayName + emails
    token = res.get('nextPageToken')
    if not token:
        break
```

Expected scale: ~53 draas.com contacts in google-draas, ~46 in google-gmail
(≈55 unique people; some people exist in BOTH accounts as separate resources).

## Adding an address + URL (append, never clobber)

- Addresses/URLs are **replaced wholesale** by `updateContact` — you MUST fetch
  the existing `addresses`/`urls` first and append.
- `updateContact` requires `etag` from the freshly-fetched person; pass
  `updatePersonFields='addresses,urls'`.
- Custom `type` strings work for addresses and urls (e.g. `'DRA'`,
  `'DRA Map'`) — no enum restriction observed (matches earlier customType note).
- Idempotency: check `any(a.get('type')=='DRA' and '<street>' in a.get('formattedValue','') ...)`
  before appending so re-runs skip already-updated contacts.

```python
full = svc.people().get(resourceName=rn, personFields='names,emailAddresses,addresses,urls').execute()
addrs = full.get('addresses', [])
urls  = full.get('urls', [])
if not has_dra_addr:
    addrs.append({'type': 'DRA', 'formattedValue': DRA_ADDR, 'country': 'India'})
if not has_map:
    urls.append({'type': 'DRA Map', 'value': DRA_MAP})
svc.people().updateContact(
    resourceName=rn,
    updatePersonFields='addresses,urls',
    body={'resourceName': rn, 'etag': full.get('etag'),
          'addresses': addrs, 'urls': urls}
).execute()
```

## Removing emails (departed-employees cleanup)

Filter to contacts whose displayName (normalized: lowercase, strip `.`/`,`) is in
the departed set, fetch full person, **keep only emails NOT ending in
`@draas.com`** (or whatever domain was flagged — NDR's ask was "delete the
draas.com addresses", so @drahomes.in / @ahfl.in / @draestates.com and personal
gmails were deliberately preserved), then `updateContact(updatePersonFields='emailAddresses')`.

- Voice-dictated names are fuzzy: "Prakash S.P." → **Prakash C** (departed),
  NOT Prakash Singh (current, psingh@draas.com — land team). Always protect
  current employees and say out loud which interpretation you applied.
- "Meena Nair" → Bina Nair, "Chetanel" → Chetan L, "Nagraj Ramamurti" →
  Nagarajan Ramamoorthy, "Agne" → Aagney Singh. Normalized-name matching against
  the live connection list is the reliable resolver.

## Timeouts and resume

A full pass (~100 get+update pairs across 2 accounts) can exceed a 300 s
foreground timeout. Run the update loop, then a **verification pass** that lists
`with_dra/total` — contacts already updated are skipped by the idempotency check,
so simply re-running the same script finishes the remainder:
```
DRAAS: updated=0 skipped=53 failed=0   →  verify: 53/53 have DRA address + map link
GMAIL: updated=24 skipped=22 failed=0  →  verify: 46/46
```
Verify by re-reading `addresses`/`urls` from `connections().list`, not by
trusting the update loop's own counts.

## Calendar events with Google Meet (same build_service)

`build_service('calendar','v3', service_name='google-draas')` + `conferenceDataVersion=1`:

```python
body = {
    'summary': '...',
    'description': '...',
    'start': {'dateTime': '2026-08-10T12:00:00+05:30', 'timeZone': 'Asia/Kolkata'},
    'end':   {'dateTime': '2026-08-10T13:00:00+05:30', 'timeZone': 'Asia/Kolkata'},
    'attendees': [{'email': 'x@y.io', 'displayName': 'X'}],
    'conferenceData': {'createRequest': {
        'requestId': 'unique-per-event',           # REQUIRED — must differ per insert
        'conferenceSolutionKey': {'type': 'hangoutsMeet'}}},
}
event = svc.events().insert(calendarId='primary', body=body, conferenceDataVersion=1).execute()
# event['hangoutLink'] → https://meet.google.com/xxx-yyy-zzz
```
Pitfall: reusing the same `requestId` across events makes Google return the
SAME meet link / error. Generate a fresh one (timestamp + purpose) each time.
