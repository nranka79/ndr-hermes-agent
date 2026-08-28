# Calendar — Teams Meeting (Non-Interview) Workflow

## Session Context (2026-06-02)

User sent meeting invite as text (not image/PDF):
- Title: **Depond Capital, Vani Vilas — Dash MOU Discussion**
- Date/Time: Wed 3 June 2026, 17:30–18:00 IST (from an invite screenshot — user pasted it as text)
- Teams link: `https://teams.live.com/meet/9367341206393?p=WaceaO65F763A2h8fh`
- Attendees: Amit (Depond Capital, `amithshekar@gmail.com`), Mehrenosh (Depond Capital, `mehernosh.bharucha@nipponindiaim.com`)

**Workflow triggered by:** user pasting the meeting details (not forwarding an invite attachment).

---

## Full Workflow

### Step 1 — Confirm all details with user BEFORE creating

User workflow for calendar events: list ALL details clearly, then explicitly ask for confirmation before any live calendar change. Do NOT create the event until user confirms.

Required fields to confirm:
- Event title
- Date and time (with timezone — always IST for this user)
- Meeting link (Teams / Meet / Zoom)
- Attendee names and email addresses (all of them)

**Pattern:** Plain text reply listing the details → ask "Confirm to create?" → wait for user "yes/go ahead" → only then call Calendar API.

### Step 2 — Create the calendar event

```python
from tools.gws_auth import build_service

calendar = build_service('calendar', 'v3')

event_body = {
    'summary': 'Depond Capital, Vani Vilas — Dash MOU Discussion',
    'location': 'Online (Microsoft Teams)',
    'description': (
        'Meeting link: https://teams.live.com/meet/9367341206393?p=WaceaO65F763A2h8fh\n\n'
        'Attendees:\n'
        '- Amit (Depond Capital) — amithshekar@gmail.com\n'
        '- Mehrenosh (Depond Capital) — mehernosh.bharucha@nipponindiaim.com\n\n'
        'Platform: Microsoft Teams\n'
        'Note: MOU Discussion with Depond Capital for Vani Vilas project (Dash)'
    ),
    'start': {
        'dateTime': '2026-06-03T17:30:00+05:30',
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': '2026-06-03T18:00:00+05:30',
        'timeZone': 'Asia/Kolkata',
    },
    'attendees': [
        {'email': 'amithshekar@gmail.com', 'displayName': 'Amit (Depond Capital)'},
        {'email': 'mehernosh.bharucha@nipponindiaim.com', 'displayName': 'Mehrenosh Bharucha (Depond Capital)'},
    ],
}

created = calendar.events().insert(
    calendarId='primary',  # REQUIRED
    body=event_body,
    sendUpdates='all'
).execute()

print("Event ID:", created['id'])
```

### Step 3 — Add attendee update if needed (after user confirms email)

If an attendee email wasn't available at creation time, add them via `events().patch`:

```python
updated = calendar.events().patch(
    calendarId='primary',
    eventId='<event_id>',
    body={
        'attendees': [
            {'email': 'amithshekar@gmail.com', 'displayName': 'Amit (Depond Capital)'},
            {'email': 'mehernosh.bharucha@nipponindiaim.com', 'displayName': 'Mehrenosh Bharucha (Depond Capital)'},
        ]
    }
).execute()
```

### Step 4 — Verify event link

After `events().insert()`, re-fetch the event to confirm the `htmlLink`. The `htmlLink` returned directly from `insert()` may produce broken links. Verify by fetching the event by ID:

```python
verified = calendar.events().get(
    calendarId='primary',
    eventId=created['id'],
    fields='summary,start,end,location,htmlLink'
).execute()
print("Calendar link:", verified.get('htmlLink'))
```

---

## User Preferences (confirmed June 2026)

1. **Confirm all details before creating events** — user wants to review the full summary before any live change. Do NOT auto-create and report after.
2. **Always return the calendar event link** — user expects the Google Calendar link immediately after creation.
3. **Attendee email discovery** — if an attendee is not in Gmail or Drive contacts, ask the user directly (do not make multiple failed searches before asking).
4. **MS Teams links** — when user provides a Teams link, store it in the `location` or `description`. Calendar API does not auto-generate Teams links for non-Google Meet platforms.
5. **Event title format** — user uses "Depond Capital, Vani Vilas — Dash MOU Discussion" with em dash (—). Mirror this exactly.

---

## Confirmed Gotchas

1. **`calendarId='primary'` is REQUIRED** — `events().insert()` without it raises `TypeError: Missing required parameter "calendarId"`.
2. **MS Teams links are NOT auto-generated** — unlike Google Meet (via `conferenceData`), MS Teams links must be manually added to the event description. Calendar API cannot generate Teams links.
3. **Events().get() with `fields` parameter** — can return 400 if invalid field names are used. Use only documented field names. `htmlLink` is valid; `modifiedDate` is NOT.
4. **User confirms by text response** — "yes", "go ahead", "create it" — any explicit affirmative. Not a button press or interactive confirmation.