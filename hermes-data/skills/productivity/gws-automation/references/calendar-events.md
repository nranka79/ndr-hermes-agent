# Calendar Events — Create, Update, and Manage

Covers calendar event operations via the per-user Calendar API: creation with Google Meet, attendee management, updating with patch(), embedding external meeting links (Teams/Zoom) in descriptions.

## Prerequisites

```python
from tools.gws_auth import build_service
# ⚠️ CRITICAL: service_name defaults to "google" which does NOT exist in vault.
# For ndr@draas.com (Nishant), use service_name="google-draas" explicitly.
# If unspecified, you'll get VaultNoTokenError even though the token exists.
calendar = build_service("calendar", "v3", telegram_id="ndr", service_name="google-draas")
```

All times use `pytz` for IST timezone:
```python
import pytz
ist = pytz.timezone('Asia/Kolkata')
```

## Creating an Event with Google Meet

Use `conferenceDataVersion=1` and `conferenceData.createRequest` to auto-create a Google Meet link:

```python
from datetime import datetime

event = {
    'summary': 'Meeting Title',
    'location': 'Venue / Address',
    'description': 'Description text',
    'start': {
        'dateTime': '2026-06-12T18:00:00+05:30',  # ISO 8601 with IST offset
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': '2026-06-12T19:00:00+05:30',
        'timeZone': 'Asia/Kolkata',
    },
    'attendees': [
        {'email': 'person1@example.com', 'displayName': 'Person One'},
        {'email': 'person2@example.com', 'displayName': 'Person Two'},
    ],
    'conferenceData': {
        'createRequest': {
            'conferenceSolutionKey': {'type': 'hangoutsMeet'},
            'requestId': f'unique-id-{datetime.now().timestamp()}'
        }
    },
    'reminders': {
        'useDefault': True
    }
}

created = calendar.events().insert(
    calendarId='primary',
    body=event,
    conferenceDataVersion=1,
    sendUpdates='all'  # sends email invitations to all attendees
).execute()

meet_link = created.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri')
event_id = created.get('id')
```

**Date/Time format tip:** Use ISO 8601 strings with `+05:30` offset directly — avoids needing `pytz` or `ist.localize()`. The `timeZone` field is metadata for display purposes; the actual time is decoded from the ISO offset. This is simpler and sufficient for all IST calendar events.

Key parameters:
- `conferenceDataVersion=1` — enables Google Meet creation
- `sendUpdates='all'` — sends email invites; omit or use 'none' to skip
- `requestId` must be unique per event (use a timestamp)

## Updating an Existing Event (patch)

Use `patch()` to update only specific fields without resending the full event:

```python
result = calendar.events().patch(
    calendarId='primary',
    eventId=event_id,
    body={
        'description': new_description
    }
).execute()
```

`patch()` only modifies the fields you provide — safe for partial updates.

## Adding External Meeting Links to Description

When the organizer shares a Teams/Zoom link, append it to the event description:

```python
new_info = f"""

**🔗 Microsoft Teams Meeting** (for online attendance)

Join: https://teams.microsoft.com/meet/...

Meeting ID: 492 557 968 027 82
Passcode: xxxxxx
"""

updated = calendar.events().patch(
    calendarId='primary',
    eventId=event_id,
    body={'description': current_description + new_info}
).execute()
```

## Adding Drive Document Links to Description

After uploading a document to Drive, link it in the event:

```python
doc_info = f"""

**📄 Attached Document:** filename.docx
Drive Link: {drive_web_link}
"""

calendar.events().patch(
    calendarId='primary',
    eventId=event_id,
    body={'description': current_description + doc_info}
).execute()
```

## Appending a Long Structured Chat Message to Description

**Trigger:** User forwards a WhatsApp/Telegram message (meeting brief, client update, team coordination) and says "add this to today's [meeting name] event description." The message is often structured with numbered points, emoji bullets, and multiple Drive links.

**Pattern:**
1. Find today's event by title keywords (e.g. "Riverstone", "Anwar", "Sumaya")
2. Get the current description
3. Append the message as-is with a clear separator
4. Use `patch()` to update

```python
# Get the event
events = calendar.events().list(
    calendarId='primary',
    timeMin=start_of_day.isoformat(),
    timeMax=end_of_day.isoformat(),
    singleEvents=True
).execute()

event = next(e for e in events['items'] if 'Riverstone' in e['summary'])
current_desc = event.get('description', '')

# The structured message from chat (preserve emoji, bullets, links)
chat_message = """RIVERSTONE — Client Meeting Brief (2 PM with Sumaya Anwar & Anwar Sir)
Prepared by: Bharat Hawaldar

Agenda: ~1 Acre Parcel — Landowner Registered — for Onward Registration

① Sy No 114/7 — 1.04 acres — LANDOWNER — Registered ✅
- Primary recommended option
...
"""

updated_desc = current_desc.strip() + "\n\n---\n\n" + chat_message

calendar.events().patch(
    calendarId='primary',
    eventId=event['id'],
    body={'description': updated_desc}
).execute()
```

**Key detail:** Preserve the original formatting, emoji, numbered lists, and Drive links exactly as the user shared them — do not rephrase or summarize.

## Listing Events for a Day

```python
from datetime import datetime
import pytz

ist = pytz.timezone('Asia/Kolkata')
start = ist.localize(datetime(2026, 6, 12, 0, 0, 0))
end = ist.localize(datetime(2026, 6, 12, 23, 59, 59))

events = calendar.events().list(
    calendarId='primary',
    timeMin=start.isoformat(),
    timeMax=end.isoformat(),
    singleEvents=True,
    orderBy='startTime'
).execute()

for event in events.get('items', []):
    summary = event.get('summary', 'No title')
    start_time = event['start'].get('dateTime', event['start'].get('date'))
    conf = event.get('conferenceData', {})
    has_meet = any(ep.get('entryPointType') == 'video' for ep in conf.get('entryPoints', []))
    print(f"{start_time} | {summary} | Meet: {has_meet} | ID: {event.get('id')}")
```

## Creating Tentative/Placeholder Events (No Confirmed Time)

**Trigger:** User says "set it as a reminder, we don't have a confirmed appointment time" or "create a placeholder event."

Pattern for events that are placeholders/tentative — no fixed time, just a date marker:

```python
event = {
    'summary': 'Event Title (TENTATIVE - BOOK APPT)',
    'description': 'TENTATIVE - Appointment time to be confirmed.\nDetails about what needs to be done.',
    'start': {'date': '2026-06-29', 'timeZone': 'Asia/Kolkata'},
    'end': {'date': '2026-06-30', 'timeZone': 'Asia/Kolkata'},
    'transparency': 'transparent',  # Shows as "free" on calendar, not busy
}
```

Key details:
- Use `'date'` (all-day) instead of `'dateTime'` when there's no confirmed time
- End date = start date + 1 day for a single-day all-day event
- `transparency: 'transparent'` — marks it as free/available, not blocking the day
- Add `(TENTATIVE)` in the title so the user can spot it

## Creating Reminder Events (Action Items)

**Trigger:** User says "set a reminder to book the appointment on [date]."

Create a short timed event (15 min) that acts as a notification:

```python
event = {
    'summary': 'REMINDER: Book Appointment - Dr. Name',
    'description': 'Action: Call [hospital] to book appointment for [patient].\nDoctor: ...\nPhone: ...',
    'start': {'dateTime': '2026-06-22T09:00:00+05:30', 'timeZone': 'Asia/Kolkata'},
    'end': {'dateTime': '2026-06-22T09:15:00+05:30', 'timeZone': 'Asia/Kolkata'},
    'transparency': 'transparent',
}
```

## Adding Attendees with Notifications

```python
event = {
    ...
    'attendees': [
        {'email': 'rnr@draas.com', 'displayName': 'Roshni Ranka'},
        {'email': 'pebblyshark69@gmail.com', 'displayName': 'Ruhaan Ranka'},
    ],
    'sendUpdates': 'all',  # Sends email invites to all attendees
}
```

- `sendUpdates='all'` — sends email invitations to every attendee
- Without this parameter, attendees are added but NOT notified
- Display names are optional but helpful in the calendar UI

## Multi-Day Events — Separate Events Per Day with Invite Text

**Pattern:** User shares an invite message and says "create calendar events for this on both days, add the full invite text as the description, add [person] as attendee."

Create one event per day rather than a recurring event — this lets attendees manage each day independently:

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

calendar = build_service('calendar', 'v3')

invite_text = """Hi [emoji]

I'm putting together a small coffee meet on Thursday and Friday 25th and 26th June at 4.00pm...

[Full invite message as shared by user — preserved verbatim]
"""

title = "Coffee Meet — Speaker Name | Topic"
location = "Venue Name"

attendees = [
    {"email": "person@example.com", "displayName": "Person Name"}
]

dates = [("Thursday", "2026-06-25"), ("Friday", "2026-06-26")]

for day_name, date_str in dates:
    event = {
        "summary": title,
        "location": location,
        "description": invite_text,
        "start": {"dateTime": f"{date_str}T16:00:00+05:30", "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": f"{date_str}T17:00:00+05:30", "timeZone": "Asia/Kolkata"},
        "attendees": attendees,
        "reminders": {"useDefault": True},
    }
    created = calendar.events().insert(
        calendarId="primary",
        body=event,
        sendUpdates="all"
    ).execute()
```

Key rules:
- **Use the invite text verbatim as the description** — do not summarize or rephrase. The user wants the exact wording preserved.
- **One event per day** — not a multi-day single event or a recurring series
- **sendUpdates='all'** — sends email invitations so attendees get notified
- **IST timezone** — always use `Asia/Kolkata` and `+05:30` offset

## Custom Reminder Overrides

Replace default reminders with custom timing:

```python
event = {
    ...
    'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'email', 'minutes': 10080},  # 1 week before (10080 min)
            {'method': 'popup', 'minutes': 1440},   # 1 day before (1440 min)
            {'method': 'popup', 'minutes': 120},    # 2 hours before
        ]
    }
}
```

Common reminder intervals:
| Duration | Minutes |
|----------|---------|
| 1 week | 10080 |
| 2 days | 2880 |
| 1 day | 1440 |
| 2 hours | 120 |
| 1 hour | 60 |

## Complete Pattern: Tentative Event + Reminder Pair

When a user says "set a reminder to book the appointment and also mark the date":

1. Create a **reminder event** on the date they should book (e.g., 1 week before)
2. Create a **tentative placeholder event** on the actual appointment date
3. Add relevant family members as attendees to both

```python
# Reminder to book (e.g., 22 Jun)
reminder = calendar.events().insert(calendarId='primary', body={
    'summary': 'REMINDER: Book Appointment with Dr. Name',
    ...
    'attendees': [{'email': 'rnr@draas.com'}],
    'sendUpdates': 'all',
    'transparency': 'transparent',
}).execute()

# Tentative placeholder (e.g., 29 Jun)
placeholder = calendar.events().insert(calendarId='primary', body={
    'summary': 'Patient - Appointment with Dr. Name (TENTATIVE - BOOK APPT)',
    'start': {'date': '2026-06-29'},
    'end': {'date': '2026-06-30'},
    'attendees': [{'email': 'rnr@draas.com'}],
    'sendUpdates': 'all',
    'transparency': 'transparent',
}).execute()
```

## Finding Attendee Emails from Gmail Thread CC Headers

**Trigger:** User says "create a calendar event with [Team Name] team — attendees are [Name 1], [Name 2], [Name 3]" and you need their email addresses.

**Problem:** The user gives names but not emails. Rather than asking for each one (wasteful round-trips), mine the emails from recent Gmail correspondence with that team.

### Workflow

1. **Search Gmail** for the team/company name + project keywords:
   ```python
   results = service.users().messages().list(userId='me', q='godrej venture hudson modification', maxResults=3).execute()
   ```

2. **Get the most recent thread** that CCs the full team — emails where multiple team members appear in CC are the most valuable. Look for the richest CC list:
   ```python
   full = service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['From', 'To', 'Cc', 'Subject', 'Date']).execute()
   headers = {h['name']: h['value'] for h in full['payload']['headers']}
   ```

3. **Extract and match** — Parse the CC header and match names the user gave:
   ```python
   import email.utils
   cc_header = headers.get('Cc', '')
   parsed = email.utils.getaddresses([cc_header])
   ```

4. **Map user names to found emails** — Cross-reference the parsed addresses against the names the user provided:
   - User said "Harsimran, Saurabh, Vashish, Amit"
   - Found: Harsimran Singh, Saurabh Vashishth, Amit Saraf
   - Map: confirm compound names (Saurabh+Vashish = Saurabh Vashishth)

5. **Present with context**: "Found these from the [Team] email thread — confirm they're the right people?"

### Common patterns

- **Compound names:** "Saurabh Vashish" (user said two words) may be one person with full name "Saurabh Vashishth" — check the CC header
- **Partial first names:** "Vashish" vs Saurabh Vashishth — confirm they're one person
- **Different domain:** Check whether the email domain is the current one or an older one
- **Spelling differences:** Trust email header names over voice transcription

### When Gmail search returns nothing

1. Try broader queries — company domain or project name only
2. Check contacts sheet / People API
3. Ask the user as last resort

### What NOT to do

- ❌ Don't ask the user for each email separately — wastes round trips
- ❌ Don't assume names without verifying via Gmail

## Creating Placeholder Events When Attendee Email Is Unknown

**Trigger:** User names an attendee (e.g., "Vinit of Jiraffe Capital") whose email you cannot find.

### Resolution: Create the event without the attendee + add details in description

```python
event = {
    'summary': 'Meeting with Vinit — Jiraffe Capital',
    'description': 'Meeting at Taj Vivanta, MG Road.\n\nAttendees:\n- Nishant Ranka\n- Prakash Singh\n- Vinit (Jiraffe Capital)\n\n⚠️ Vinit\'s email not found. Add as attendee once email is available.',
    'location': 'Taj Vivanta, MG Road, Bangalore',
    'start': {'dateTime': '2026-06-30T15:45:00+05:30', 'timeZone': 'Asia/Kolkata'},
    'end': {'dateTime': '2026-06-30T16:45:00+05:30', 'timeZone': 'Asia/Kolkata'},
}
```

### Best practice

- Document the unknown email in the description — user can fill it in
- Flag it with ⚠️ — "Add as attendee once email is available"
- Suggest next step: "If you share [Name]'s email, I can add them to the event invite"

### When it's acceptable

- User asked you to "add a meeting" — they want the event on their calendar
- The attendee email may be with a different contact you can add later
- Primary purpose is blocking time, not sending invitations

## ⚠️ Pre-Creation Confirmation Workflow — CRITICAL RULE

**User preference (Nishant, confirmed Jul 2026):** ALL event details must be confirmed with the user BEFORE calling the Calendar API. Do NOT create first and ask later.

**Wrong:**
- User: "Calendar event for 28th July, 8:30pm, discussion with Sadeq Ali, add Google Meet."
- You: "Done! Event created."
- → User: "You should have confirmed the email first."

**Correct workflow:**
1. **Gather all details** — date, time, title, Google Meet, attendee emails
2. **If attendee email is unknown, find it first** — search Gmail across accounts (see "Email Discovery via Gmail Search" below), then present for confirmation
3. **Present a summary** with ALL fields for user approval
4. **Wait for explicit confirmation** before calling `events().insert()`

Summary template:
```
Title: Discussion — Nishant & [Attendee]
Date: Tue, 28 July 2026
Time: 8:30 PM – 9:30 PM IST
Google Meet: ✓
Attendees: You <your@email.com>
           [Attendee] <attendee@email.com>
```

**Only after user says "yes" / "confirm" / "proceed"** — call the API.

**Adding multiple emails for the same guest:** When an attendee uses two email addresses, add both as separate attendee entries.

## Email Discovery via Gmail Search (When Contact Missing)

**Trigger:** User names an attendee whose email isn't in Google Contacts or the contacts sheet.

**Pattern — search Gmail across all accounts for emails from/to that person:**

1. **Start with the DRAAS work account** (most business correspondence):
```python
svc = build_service("gmail", "v1", service_name="google-draas")
results = svc.users().messages().list(userId="me", q="Saadeq OR Sadeq", maxResults=10).execute()
```

2. **Check headers** — extract From/To/Cc:
```python
for msg in msgs:
    data = svc.users().messages().get(userId="me", id=msg["id"], format="metadata", metadataHeaders=["From", "To"]).execute()
    headers = {h["name"]: h["value"] for h in data["payload"]["headers"]}
    print(headers.get("From"))
```

3. **If not found, try other accounts** — `service_name="google-gmail"`, `service_name="google-ahfl"`

4. **Try name variants** — voice transcription may produce different spellings: Sadik/Sadiq/Saadeq/Sadeq, Mohamed/Mohammed/Mohammad

5. **Present what you found** and confirm with user

**Why this works:** Google Contacts stores manually saved contacts. Gmail stores every email ever sent/received. For business contacts, the work Gmail account almost always has the email from a prior thread, even if the contact was never saved.

## User Preference — Property Visit Event Naming (Nishant)\n\nWhen creating calendar events for **property visits** (sites, land parcels, projects), the title must include the **key person/authority being met** — not just the property name.\n\n**Correct:**\n- `Visit North Star Property with JDTP Nagrajappa` ✅\n- `Visit Ranka Amber with Town Planning Officer` ✅\n\n**Wrong:**\n- `Visit North Star Property` ❌ — missing the authority/person\n- `North Star Property Visit` ❌ — generic, misses context\n\n**Rationale:** The key person met (JDTP, BBMP officer, architect, landowner, investor) is the critical context — without it, the event title is ambiguous and the user can't tell at a glance what the meeting is about.\n\n**If the user omits the person's name in their request but context from the conversation makes it clear (e.g., prior discussion mentioned JDTP Nagrajappa for this visit), include it anyway.** Always carry forward relevant context from the same conversation.\n\n**When in doubt, clarify:** If two different people/authorities could be the subject, ask the user which to include.\n\n## Pitfalls\n\n- **conferenceData on update:** You cannot add a Google Meet to an existing event via patch — Meet is only generated on create. To add a meeting link to an existing event, append it to the description as an external link.
- **Existing meeting link provided by user:** When the user provides a specific meeting link (Teams, Zoom, etc.), do NOT also add `conferenceData` to create a Google Meet. Omit `conferenceData` entirely and put their meeting details in the `description` field. Having two video links (their Teams + your auto-generated Meet) is confusing and wasteful.
- **sendUpdates='all'** sends real emails to all attendees. For internal testing or events that don't need notification, omit this parameter.
- **requestId uniqueness:** If you reuse the same requestId, the API may return a cached/duplicate event. Always suffix with `datetime.now().timestamp()` or a UUID.
- **Patch vs Update:** Use `patch()` (sends only changed fields) not `update()` (sends full replacement). Patch avoids accidentally clearing conference data or other auto-generated fields.
- **Event deletion:** If you delete and recreate an event with the same title but want a new Meet link, use a different requestId.
- **Description length:** Very long descriptions (1500+ chars) are fine — the Calendar API handles them. No truncation needed.
- **Event matching by keyword:** When searching for an event by a voice-transcribed name, try multiple keyword variants. "Sumaya" might be in the event title as "Sumeya" or "Sumaya".
