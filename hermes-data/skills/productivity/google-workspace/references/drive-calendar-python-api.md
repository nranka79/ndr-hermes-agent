# Drive & Calendar via tools.gws_auth.build_service()

The CLI-based approach (`google_api.py`) covers most operations, but for
programmatic multi-step workflows (upload a file then update a calendar event
description with the link), use the `tools.gws_auth.build_service()` API
directly from Python. This gives full control over all API parameters.

## Prerequisites

- gws-vault socket must be accessible at `$GWS_VAULT_SOCKET`
  (/run/gws-vault/vault.sock)
- Always set `os.environ['GWS_VAULT_SOCKET']` before calling build_service if
  running outside the Hermes terminal environment (e.g. from execute_code)
- `has_token(telegram_id, service_name)` requires BOTH args:
  - `telegram_id`: the user's Telegram ID (e.g. "ndr")
  - `service_name`: one of "google-draas", "google-ahfl", "google-gmail"
    (resolve via `gws_resolve_account` when uncertain — never hardcode)
- Call `canonical_uid(telegram_id)` to get the vault key (e.g. "ndr-<telegram-id>")
- **`build_service()` signature (verified 2026-08-10):** it takes
  `build_service(api, version, service_name=...)` ONLY. Passing
  `telegram_id='ndr'` raises `TypeError: build_service() got an unexpected
  keyword argument 'telegram_id'`. The old two-arg style shown in older
  service = gws_auth.build_service('drive', 'v3',
                                    service_name='google-draas')
  Identity comes from the session; service_name picks the account token.
- **NEVER hardcode `service_name` as a literal string** in scripts. Call
  the `gws_resolve_account` tool (available in hermes_tools) to pick the
  right account for the task. The snippets below show `service_name='...'`
  only as a placeholder for readability — in real scripts resolve first.
  See "Sheets: Cross-Sheet VLOOKUP" below for the full pattern.

## Drive: Upload File to Known Folder

```python
import sys, os, json
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
from tools import gws_auth
from googleapiclient.http import MediaFileUpload

service = gws_auth.build_service('drive', 'v3', service_name='google-draas')

# Upload with media
media = MediaFileUpload('/tmp/myfile.jpg', mimetype='image/jpeg',
                        resumable=True)
file_meta = {
    'name': 'Urdhva_Housewarming_Invitation.jpg',
    'parents': ['FOLDER_ID']  # Drive folder ID
}
uploaded = service.files().create(
    body=file_meta, media_body=media,
    fields='id,name,webViewLink'
).execute()
# Returns: {"id": "...", "name": "...", "webViewLink": "https://..."}
```

## Drive: Find or Create Folder at Root

```python
# Find folder
results = service.files().list(
    q="name='TMP' and mimeType='application/vnd.google-apps.folder' "
      "and 'root' in parents and trashed=false",
    spaces='drive'
).execute()
files = results.get('files', [])
if files:
    folder_id = files[0]['id']
else:
    folder_meta = {
        'name': 'TMP',
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=folder_meta, fields='id').execute()
    folder_id = folder['id']
```

## Calendar: Create Event with Attendees

```python
from datetime import datetime, timezone, timedelta
import iso8601  # or construct tz-aware datetimes
service = gws_auth.build_service('calendar', 'v3',
                                  service_name='google-draas')

event_body = {
    'summary': 'Event Title',
    'description': 'Multi-line\ndescription',
    'location': 'Full address',
    'start': {
        'dateTime': '2026-07-12T18:00:00+05:30',
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': '2026-07-12T21:00:00+05:30',
        'timeZone': 'Asia/Kolkata',
    },
    'attendees': [{'email': 'rnr@draas.com'}],
}
event = service.events().insert(
    calendarId='primary', body=event_body
).execute()
print(event['htmlLink'])
```

## Calendar: Create Event with Google Meet (conferenceData)

To auto-attach a Google Meet link, add `conferenceData.createRequest` to the
body AND pass `conferenceDataVersion=1` to insert (without it the
conference data is silently ignored). Verified 2026-08-10.

```python
event_body = {
    'summary': 'Review & Discussion',
    'start': {'dateTime': '2026-08-10T12:00:00+05:30', 'timeZone': 'Asia/Kolkata'},
    'end':   {'dateTime': '2026-08-10T13:00:00+05:30', 'timeZone': 'Asia/Kolkata'},
    'attendees': [
        {'email': 'a@kelsa.io', 'displayName': 'A'},
        {'email': 'b@kelsa.io', 'displayName': 'B'},
    ],
    'conferenceData': {
        'createRequest': {
            'requestId': 'unique-string-per-event',   # e.g. 'rv-dental-review-20260810'
            'conferenceSolutionKey': {'type': 'hangoutsMeet'}
        }
    },
}
event = service.events().insert(
    calendarId='primary', body=event_body, conferenceDataVersion=1
).execute()
print(event['hangoutLink'])   # e.g. https://meet.google.com/ige-fdhv-xia
```

Notes:
- `requestId` must be unique per event (use a descriptive slug — it is not
  user-visible but collisions can fail).
- `hangoutLink` in the response is the Meet URL to share with the user.
- Attendee emails for Kelsa team members are NOT in Google contacts under
  plain names — see kelsa-crm skill §14 for resolving them.

## Calendar: Create Event with Google Meet (verified Aug 2026)

To auto-attach a Google Meet link, add `conferenceData` to the body AND pass `conferenceDataVersion=1` to insert — without the version param the conference is silently ignored:

```python
event_body = {
    'summary': 'Review & Discussion',
    'description': 'Multi-line\ndescription',
    'start': {'dateTime': '2026-08-10T12:00:00+05:30', 'timeZone': 'Asia/Kolkata'},
    'end':   {'dateTime': '2026-08-10T13:00:00+05:30', 'timeZone': 'Asia/Kolkata'},
    'attendees': [
        {'email': 'ashwin@kelsa.io', 'displayName': 'Ashwin Hegde'},
    ],
    'conferenceData': {
        'createRequest': {
            'requestId': 'rv-dental-review-20260810',  # any unique string
            'conferenceSolutionKey': {'type': 'hangoutsMeet'}
        }
    },
}
event = service.events().insert(calendarId='primary', body=event_body, conferenceDataVersion=1).execute()
# event['hangoutLink'] → 'https://meet.google.com/xxx-yyy-zzz'
```

Confirmed: attendees get auto-invite emails, `hangoutLink` is returned in the insert response, and `event['htmlLink']` is the calendar link. `requestId` must be unique per event (reuse across events can cause 409 conflicts on retries).

## Calendar: Update Event Description (Patch)

```python
service.events().patch(
    calendarId='primary',
    eventId='EVENT_ID_FROM_CREATE',
    body={'description': 'New description text'}
).execute()
```

## Calendar: Search Existing Events

```python
events = service.events().list(
    calendarId='primary',
    timeMin='2026-07-12T00:00:00+05:30',
    timeMax='2026-07-12T23:59:59+05:30',
    q='Urdhva',
    singleEvents=True,
    orderBy='startTime'
).execute()
items = events.get('items', [])
for e in items:
    print(e['id'], e['summary'], e.get('htmlLink', ''))
```

## Sheets: Cross-Sheet VLOOKUP (Python)

When you need to pull data from one spreadsheet into another (or another
sheet/tab in the same workbook) — the equivalent of a SQL JOIN or a Google
Sheets VLOOKUP across files — `gws_bridge sheets` doesn't have a clean
multi-source primitive. Use the API directly.

**Use case:** Spreadsheet A has a "Plot Details" tab with N rows of source
data (Plot No in col A, B..H are the fields). Spreadsheet B has a related
"Plot Details" tab keyed on the same Plot No in col A. You want to append
SS1's data to SS2 starting at column N (so existing SS2 data is preserved
and SS1 data lands in N, N+1, N+2, ...).

**Pattern (verified working):**

```python
import sys, os
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
from tools.gws_auth import build_service

# Resolve service_name via gws_resolve_account first — never hardcode.
svc = build_service('sheets', 'v4', service_name='<RESOLVED_ACCOUNT>')

SS_SOURCE = '<source spreadsheet id>'
SS_TARGET = '<target spreadsheet id>'
SHEET     = "'Plot Details'"  # quote if name has spaces

# 1. Read source (key column A + the data columns you want, e.g. A..H)
src = svc.spreadsheets().values().get(
    spreadsheetId=SS_SOURCE, range=f'{SHEET}!A1:H100'
).execute()
src_rows = src.get('values', [])
header_src = src_rows[0]
key_col_idx = 0          # Plot No is column A
data_col_start = 1       # data starts at column B
data_col_end   = len(header_src)  # or hardcode 8 for A..H

# 2. Build lookup: key -> list of data values
lookup = {}
for row in src_rows[1:]:
    if len(row) <= key_col_idx or not row[key_col_idx].strip():
        continue
    key = row[key_col_idx].strip()
    # Pad short rows so every entry is exactly the same width
    padded = (row + [''] * (data_col_end + 1))[:data_col_end + 1]
    lookup[key] = padded[data_col_start:]   # slice to data columns

# 3. Read target to know the row count AND get the keys
tgt = svc.spreadsheets().values().get(
    spreadsheetId=SS_TARGET, range=f'{SHEET}!A1:M100'
).execute()
tgt_rows = tgt.get('values', [])

# 4. Build the new columns (write payload). For a header at row 1:
NEW_HEADER = [f"{h} (SS1)" for h in header_src[data_col_start:]]
new_rows = [NEW_HEADER]
matched, unmatched = 0, []
for ridx, row in enumerate(tgt_rows[1:], start=2):
    key = row[0].strip() if row else ''
    if key in lookup:
        new_rows.append(lookup[key])
        matched += 1
    else:
        new_rows.append([''] * len(NEW_HEADER))  # blank for missing keys
        unmatched.append((ridx, key))

# 5. CRITICAL — payload width must EXACTLY match target row count.
# If new_rows has fewer entries than tgt_rows, pad with blanks.
# If it has more, truncate.
if len(new_rows) < len(tgt_rows):
    new_rows.extend([[''] * len(NEW_HEADER)] * (len(tgt_rows) - len(new_rows)))
new_rows = new_rows[:len(tgt_rows)]

# 6. Write. Range MUST cover exactly len(new_rows) rows starting at N1.
end_col = chr(ord('A') + data_col_end - 1)  # e.g. 'H' for col index 7
end_row = len(new_rows)                     # rows 1..N, so N1..N{end_row}
write_range = f'{SHEET}!N1:{end_col}{end_row}'

resp = svc.spreadsheets().values().update(
    spreadsheetId=SS_TARGET,
    range=write_range,
    valueInputOption='USER_ENTERED',  # parses "5,473.72" and "2.83%" correctly
    body={'values': new_rows},
).execute()
print(f"Updated {resp.get('updatedCells')} cells in {resp.get('updatedRange')}")
print(f"Matched: {matched}/{len(tgt_rows)-1}  Unmatched: {unmatched}")
```

**Key gotchas (these have bitten real scripts):**

- **Off-by-one on the write range.** If your `new_rows` has the header at
  index 0 and 40 data rows in indices 1..40, writing to `N1:T40` is correct
  (40 rows = 1 header + 39 data, but if you have 40 data rows that's N1:T41).
  The API returns `400 "tried writing to row N+1"` if the range is one row
  too short. Always compute `end_row = len(new_rows)` and double-check.
- **USER_ENTERED vs RAW.** Use `USER_ENTERED` so strings like `"5,473.72"`,
  `"2.83%"`, and `"E"` parse as numbers/percents/text. `RAW` writes
  everything as literal strings.
- **Pad short rows in the source.** Google Sheets `values().get()` truncates
  trailing empty cells. A row with only column A filled will be a 1-element
  list, not 8. Pad to `header_width` before slicing, or every column past
  the last filled cell will silently disappear from the lookup.
- **Quote sheet names with spaces.** `'Plot Details'!A1:H100` not
  `Plot Details!A1:H100` (the space breaks the A1 range syntax).
- **Match keys as strings.** Source `"1"` and target `"1"` match; source
  `1` (int) and target `"1"` (str) won't if you used `dict` with mixed
  types. `.strip()` both sides and keep them as strings.
- **Always confirm before writing to a live shared sheet** (Rule 1 in
  SKILL.md). Show the column mapping, row count, and which spreadsheet
  ID before calling `.values().update(...)`. If the user can see the
  mapping, they can catch a wrong key column or a column-shift mistake
  before you commit it.

## Common Pitfalls

- `execute_code` (sandbox) does NOT have `GWS_VAULT_SOCKET` set AND its
  generated `hermes_tools.py` stub lacks `gws_fetch_token`. **Both**
  `gws_skill_bridge.call()` and `gws_auth.build_service()` fail from
  `execute_code`. Always use `terminal()` with the Hermes venv for
  Google API calls (`/opt/hermes/.venv/bin/python`).
- `has_token` requires TWO args: `has_token(telegram_id, service_name)`.
  Calling with one arg (`has_token(service_name)`) fails with
  "no identity mapping" — this is NOT the vault being down.
- When the user sends an image inline (not as a file/document), the vision
  system reads it but the bytes never hit the filesystem. To get a Drive link
  for such an image, ask the user to share via Google Drive link or re-send
  the image as a document attachment.
- **Never write to a live Google Sheet without showing the user the plan
  first** (recipient, file ID, columns affected, row count). The user can
  always see the diff via Sheet version history, but it's a shared doc —
  confirm before mutating.
- For multi-account work (e.g. reading from `google-draas` and writing to
  `google-ahfl`), resolve both `service_name`s via `gws_resolve_account`
  and call `build_service` separately for each account. The vault key
  determines whose token is used; there is no "merge" service.
