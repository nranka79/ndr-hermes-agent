# GWS API Quirks — learned from real sessions (NDR, google-draas)

## Vault / build_service from execute_code (CRITICAL)

- `build_service('drive', 'v3')` with the DEFAULT service_name FAILS:
  `VaultNoTokenError: No google token for user ndr-<tgid>`. You MUST resolve the
  account first with `gws_resolve_account` (or `gws_resolve_account(account='draas')`)
  and pass the vault key explicitly:
  `build_service('drive', 'v3', service_name='google-draas')`.
- Also set `os.environ['HERMES_SESSION_USER_ID'] = '<telegram_id>'` at the top of
  the script (e.g. `7449813913` for Nishant) — otherwise `_current_telegram_id()`
  may fall back to a raw channel id that the vault can't resolve.
- Every Google surface (Gmail, Calendar, Drive, Docs, Sheets, People) goes through
  the same per-user vault token. Correct service_name per account:
  google-draas (ndr@draas.com), google-ahfl (ndr@ahfl.in), google-gmail (nishantranka@gmail.com).

## Drive comments API (reviewing comments on a Google Doc)

- `drive.comments().list(fileId=...)` — the `resolved` field is NOT valid for
  comments in Drive API v3 (only replies have it). Requesting
  `fields='comments(...resolved...)'` returns 400 "Invalid field selection resolved".
  Use: `fields='comments(id,author(displayName,emailAddress),content,quotedFileContent,anchor,createdTime,replies(id,author(displayName,emailAddress),content,createdTime))'`.
- To map a comment anchor to document location, dump the doc via
  `docs.documents().get()` and correlate the `quotedFileContent.value` text with
  paragraph text; the anchor `kix.xxx` alone is not human-readable.
- Comment author email is often absent (displayName only) — don't rely on email for identification.

## Gmail drafts

- `gmail.users().drafts().create(userId='me', body={'message': {'raw': ...}})`
  needs the FULL MIME message (headers To/Subject/From baked into the raw MIME,
  base64 urlsafe). Passing `'to'`/`'subject'` keys inside the message dict does NOT
  set MIME headers — the draft shows up without To/Subject. Build with
  `MIMEText(...)` + `msg['To']`, `msg['Subject']`, `msg['From']`, then
  `base64.urlsafe_b64encode(msg.as_bytes()).decode()`.
- If you created a malformed draft, delete it (`drafts().delete`) and recreate —
  no way to patch headers in place.

## People API / Google Contacts

- `people.people().searchContacts(query=..., readMask='names,emailAddresses,phoneNumbers,addresses,organizations,biographies,metadata')`
  returns 0..N persons; search by surname is the reliable finder.
- `updateContact` requires the current `etag` in the body (fetch person first with
  personFields incl. metadata to get `etag`).
- Custom address labels: the Address schema has NO `customType` field — sending it
  fails 400 "Unknown name customType". And `type: 'custom'` alone renders as generic
  "Custom". The WORKING pattern for a free-text label like "Old": pass the label
  string directly as `type` (e.g. `'type': 'Old'`) — the API accepts arbitrary
  type strings and Google Contacts displays them. Verified 2026-08.
- When updating addresses via updatePersonFields='addresses', you send the FULL
  address list (it replaces, not merges) — preserve existing addresses and reclassify
  rather than drop them (e.g. old home → 'Old' label, keep Vodafone 'other').

## Calendar

- `cal.events().insert(calendarId='primary', body=..., sendUpdates='all')` sends
  invites to attendees automatically (Roshni rnr@draas.com, kids' gmail). Patch
  later with `events().patch` to add location/description without re-inviting.
- Reminder sub-events (fasting prep etc.) with 0-min popup override work well for
  "prepare the night before / morning of" nudges.

## Sheets (contact registry + trackers)

- The registry "NDR DRAAS Google contacts.csv" is a Google Contacts CSV export:
  headers row 1, address columns are at fixed offsets
  (Address1 Label col 40 AN … Address1 Country col 47 AU; Address2 Label col 49 AW …
  Address2 Extended col 57 BE; Address3 Label col 58 BF … Extended col 66 BN).
  Update with `spreadsheets().values().update(range="'NDR DRAAS Google contacts.csv'!AN718:AU718", valueInputOption='USER_ENTERED')`.
  Row numbers are 1-based INCLUDING the header row (a person at "row 718" in the
  sheet = sheet row 718; verify against surrounding name cells before writing).
