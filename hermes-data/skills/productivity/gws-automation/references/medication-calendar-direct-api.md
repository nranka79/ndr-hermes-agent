# Medication Calendar — Direct API Workflow

When the user dictates a medication schedule via voice (or text) and wants actual Google Calendar events created with attendees — **use the Calendar API directly** (not ICS). This gives real-time reminders, attendee invitations, and calendar visibility for the whole family.

## When to use this

- User says "make calendar events for Ruhaan's medications" or similar family-medication request
- User wants specific family members (spouse, child) as attendees on every event
- User provides the medication schedule verbally (often via voice message, requiring iterative clarification)
- Short-course medications (Azhi, steroids) need to coexist with ongoing daily medications

## Workflow

### Step 1 — Parse the medication schedule from voice

Voice-dictated medication instructions are inherently ambiguous. **Do NOT assume you got it right on the first pass.** Common ambiguity sources:

| Voice phrase | Possible meanings |
|---|---|
| "New pump at 6, nasal spray at 9" vs "New pump at 9, nasal spray at 6" | Pump vs Spray time swap — most common error |
| "One in the morning one in the evening" | Could be same med twice, or two different meds |
| "For 2 more days" vs "for the rest of his life" | Course duration often mixed with ongoing meds |
| "Azhi" / "Azzi" / "Azee" | Azithromycin (antibiotic) — voice varies |

**Always parse into a structured schedule and present for confirmation before creating anything.**

### Step 2 — Present for confirmation BEFORE creating

This is the critical gate. The user explicitly asked "show me the final medication entries before we make the calendar entries" after the third round of correction. Follow this pattern:

```
📋 Proposed Schedule:

**Ongoing — Daily (until next review):**
• 7:00 AM — Morning Pump
• 6:00 PM — Nasal Spray (once daily only)
• 9:00 PM — New Pump

**Short course — Jun 16-17 only:**
• 7:00 AM — Lanzole Junior
• 6:00 PM — Azhi 500

Attendees: Roshini (rnr@draas.com), Ruhaan (pebblyshark69@gmail.com)

Correct?
```

Wait for explicit confirmation. Do NOT create events on the first pass — the schedule WILL change after the user reviews it.

### Step 3 — Delete existing medication events first

Before creating new events, find and delete all existing recurring medication events to avoid duplicates:

```python
# Find existing Ruhaan medication events
result = calendar.events().list(
    calendarId='primary',
    timeMin=start.isoformat(),
    timeMax=end.isoformat(),
    singleEvents=False,
    q='Ruhaan'
).execute()

# Filter for medication events (💊 icon or medication keywords)
med_event_ids = [e['id'] for e in result.get('items', [])
                 if '💊' in e.get('summary', '')]

# Delete each one
for eid in med_event_ids:
    calendar.events().delete(calendarId='primary', eventId=eid).execute()
```

**Key:** Deleting the parent recurring event deletes the entire series. No need to delete individual instances.

### Step 4 — Create new recurring events

Use the Calendar API `insert()` with `recurrence` (RRULE) for ongoing medications:

```python
from datetime import datetime, timedelta
import pytz

ist = pytz.timezone('Asia/Kolkata')
today = datetime.now(ist).replace(hour=0, minute=0, second=0, microsecond=0)
end_date = today + timedelta(days=365)  # until next review

attendees = [
    {'email': 'pebblyshark69@gmail.com', 'displayName': 'Ruhaan Ranka'},
    {'email': 'rnr@draas.com', 'displayName': 'Roshini Ranka'},
]

event = calendar.events().insert(calendarId='primary', body={
    'summary': '💊 Ruhaan - Morning Pump (7 AM)',
    'description': 'Pump medication — one pump in the morning.\nDaily at 7:00 AM.',
    'start': {
        'dateTime': f"{today.strftime('%Y-%m-%d')}T07:00:00+05:30",
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': f"{today.strftime('%Y-%m-%d')}T07:10:00+05:30",
        'timeZone': 'Asia/Kolkata',
    },
    'recurrence': [
        f'RRULE:FREQ=DAILY;INTERVAL=1;UNTIL={end_date.strftime("%Y%m%d")}T235959Z'
    ],
    'attendees': attendees,
    'reminders': {
        'useDefault': False,
        'overrides': [{'method': 'popup', 'minutes': 5}]
    }
}).execute()
```

### Step 5 — Handle short-course medications alongside ongoing ones

Short courses (Azhi 500 for 5 days, Lanzole for 2 days) need separate events with COUNT instead of UNTIL:

```python
# Short course — 2 days only
short_event = calendar.events().insert(calendarId='primary', body={
    'summary': '💊 Ruhaan - Azhi 500 (6 PM)',
    'description': 'Azithromycin 500mg — Day 4 & 5 of course.',
    'start': {
        'dateTime': f"{tomorrow.strftime('%Y-%m-%d')}T18:00:00+05:30",
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': f"{tomorrow.strftime('%Y-%m-%d')}T18:15:00+05:30",
        'timeZone': 'Asia/Kolkata',
    },
    'recurrence': ['RRULE:FREQ=DAILY;COUNT=2'],
    'attendees': attendees,
}).execute()
```

### Step 6 — Verify final state

After creating, list all upcoming medication events to confirm:

```python
result = calendar.events().list(
    calendarId='primary',
    timeMin=start.isoformat(),
    timeMax=end.isoformat(),
    singleEvents=False,
    q='💊'
).execute()

for e in result.get('items', []):
    s = e['start'].get('dateTime', e['start'].get('date'))
    rec = e.get('recurrence', ['N'])[0][:60] if e.get('recurrence') else 'N'
    print(f"{s} | {e.get('summary')} | {rec}")
```

## Technical notes

- **PYTHONPATH required for terminal:** Scripts must run with `PYTHONPATH=/opt/hermes:$PYTHONPATH /opt/hermes/.venv/bin/python3 script.py` to find the `tools` module and its Google API dependencies.
- **RRULE format:** `FREQ=DAILY;INTERVAL=1;UNTIL=20270615T235959Z` — UNTIL must be in UTC (Z suffix).
- **Attendee notifications:** Calendar API auto-sends email invitations when `attendees` field is populated. No `sendUpdates` parameter needed — it defaults to sending.
- **Event icon prefix:** Use `💊 Ruhaan - <Medication> (<Time>)` as the naming convention so events are easily searchable and scannable.

## Pitfalls

- **Voice-time ambiguity is the #1 error source.** The user will say times in one order but mean another. Always present the full schedule for confirmation before creating.
- **"Pump" vs "Spray" confusion.** The user may say "pump" for a nasal spray device or a pump inhaler. Don't assume you know which is which until confirmed.
- **Short courses with ongoing meds at the same time.** When Azhi is at 6 PM and Nasal Spray is also at 6 PM, create them as TWO separate events (not combined) so each has its own independent reminder.
- **Deleting recurring events is irreversible.** Always present the deletion plan to the user before executing. Show the list of event titles that will be removed.
- **Attendee email confirmation.** Family attendee emails (Roshini = rnr@draas.com, Ruhaan = pebblyshark69@gmail.com) are stable — confirm once per session, save to memory for reuse.
