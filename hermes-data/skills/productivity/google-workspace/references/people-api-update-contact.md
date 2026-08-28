# People API updateContact: etag requirement + userDefined fields (worked 25-Aug-2026)

Adding a custom field (e.g. a Google Maps link) to an existing Google Contact via
`people().people().updateContact()`.

## The etag gotcha (two failed attempts before working)

- **FAILURE 1:** `updateContact(updatePersonFields='userDefined', body={'userDefined': [...]})`
  → `HttpError 400: "Request must set person.etag or person.metadata.sources.etag for the
  source that is being updated."`
- **FAILURE 2 (wrong fix):** fetching the etag with `personFields='etag'` → `HttpError 400:
  "Invalid personFields mask path: etag"`. **`etag` is NOT a valid personFields path.**
- **WORKING FIX:** fetch with any normal personFields value (e.g. `personFields='names'`),
  which returns the etag automatically, then include it in the update body:

```python
cur = people.people().get(resourceName=rn, personFields='names').execute()
upd = people.people().updateContact(
    resourceName=rn, updatePersonFields='userDefined',
    body={'etag': cur.get('etag'),
          'userDefined': [{'key': 'Google Maps', 'value': maps_url}]}).execute()
```

Key rule: **`etag` is read automatically and must be echoed back in the UPDATE body — never
request it as a personFields mask.**

## Storing a Google Maps link on a contact

- Use `userDefined` (custom field) — renders in Google Contacts UI as "Google Maps: <url>".
  Do NOT put it in `urls` (that's for websites) or `biographies` (notes) if you want it as a
  structured field.
- Resolve the maps shortlink FIRST to verify it points where the user says (`urllib HEAD` →
  parse `@lat,lng` or the place string). For RT Nagar the goo.gl link resolved to
  "Shriram Whitehouse, Ganesha Block, Govindaraj Garden, RT Nagar, Bengaluru" — matching the
  stated "White House Apartments, R.T. Nagar".

## Online contact sheet — verified column map (NDR DRAAS Google contacts, id 1XbSRA...oV9g)

Header row 1, 93 columns (0-indexed cell position → column letter → meaning):
- 0/A First Name, 1/B Middle, 2/C Last, 14/O Notes, 16/Q Labels
- 17/R E-mail 1 - Label, 18/S E-mail 1 - Value, 19/T, 20/U E-mail 2 - Value, 21/V, 22/W E-mail 3 - Value
- 27/AB Phone 1 - Label, 28/AC Phone 1 - Value, 29/AD, 30/AE Phone 2 - Value, 31/AF, 32/AG Phone 3
- **39/AN Address 1 - Label, 40/AO Address 1 - Formatted, 41/AP Street, 42/AQ City, 44/AS Region,
  45/AT Postal Code, 46/AU Country** (43=PO Box, 47=Extended)
- 48–56 Address 2 block (Label AW / Formatted AX ...), 57–65 Address 3 block
- 78/Au Project Association, 79/Av Land Proposal Association, 80/Aw Topic Association,
  81/Ax Address As, 82/Ay Alias, 83/Az People Association, 84/A{ Conversation History
- 87/CJ Custom Field 1 - Label, 88/CK Custom Field 1 - Value (good home for "Google Maps" link)
- 89/CL Custom Field 2 - Label, 90/CM Custom Field 2 - Value
- 91 voice_misspellings, 92 contact_score

Note: older skill notes mention "CH=Nickname, CI=Notes" — those letters are WRONG per this
verified read; the authoritative map is above.

## Verify-before-write lesson

The user asked to "add the address" for Charitra + Nenumal Murjani — but the address was
ALREADY present in both People API (home, primary) and the sheet (rows 718/2268, Address 1
complete). The only genuinely missing piece was the maps link. Always read current state first
and report what already exists — don't blindly write duplicates.