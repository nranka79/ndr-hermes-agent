# Medication Calendar Update Workflow

When a user says "update Ruhaan's medication schedule" or provides new prescription instructions — **create actual Google Calendar events** (not ICS file) with attendees. This is the "live calendar update" approach, different from the ICS export workflow.

## When to Use This vs. ICS Export

| Approach | When | Deliverable |
|----------|------|-------------|
| **Live Calendar** (this ref) | User wants events ON their calendar with attendees, reminders, notifications | `calendar.events().insert()` via Calendar API |
| **ICS Export** (prescription-to-ics-calendar-workflow.md) | User wants a portable file to share/import themselves | `.ics` file delivered via MEDIA |

## Prerequisites

```python
from tools.gws_auth import build_service
from datetime import datetime, timedelta
import pytz

calendar = build_service('calendar', 'v3', telegram_id='<telegram_id>')
ist = pytz.timezone('Asia/Kolkata')
```

## Step 1 — Find existing medication events to delete

Search by keyword across a wide date range to catch all recurring instances:

```python
start = ist.localize(datetime(2025, 12, 1, 0, 0, 0))
end = ist.localize(datetime(2027, 1, 1, 0, 0, 0))

for keyword in ['Ruhaan', 'medication', 'pump', 'inhaler', 'nebulization']:
    result = calendar.events().list(
        calendarId='primary',
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=False,  # Get recurring event parent, not instances
        q=keyword
    ).execute()
```

**Key:** Use `singleEvents=False` to get the **recurring event parent ID** (not individual instances). This lets you delete the entire series with one call.

Identify which events are medication (to delete) vs. appointments/travel (to keep). Medication events typically have emoji prefixes like 💊, 🔴, 🟡, 🟠, ☀️, 🌙, ❗ and keywords like pump, spray, inhaler, neb, medication, dose.

## Step 2 — Delete old medication events

Delete the recurring event by its parent ID:

```python
calendar.events().delete(calendarId='primary', eventId='<recurring_event_id>').execute()
```

Delete any single (non-recurring) one-time dose events the same way.

## Step 3 — Create new recurring medication events

Each medication dose is a **separate VEVENT** with its own RRULE. Build them with:

```python
today = datetime.now(ist)
start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
end_date = start_date + timedelta(days=365)  # Until next review

attendees = [
    {'email': 'pebblyshark69@gmail.com', 'displayName': 'Ruhaan Ranka'},
    {'email': 'rnr@draas.com', 'displayName': 'Roshni Ranka'},
]

event = calendar.events().insert(calendarId='primary', body={
    'summary': '💊 Ruhaan - <Medication Name> (<Time Label>)',
    'description': '<Dosage instructions>\nDaily at <time>.\nPrescribed by Dr. <Name>.\nNext review: 365 days.',
    'start': {
        'dateTime': f"{start_date.strftime('%Y-%m-%d')}T<HH:MM>:00+05:30",
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': f"{start_date.strftime('%Y-%m-%d')}T<HH:MM+15>:00+05:30",
        'timeZone': 'Asia/Kolkata',
    },
    'recurrence': [
        f'RRULE:FREQ=DAILY;INTERVAL=1;UNTIL={end_date.strftime("%Y%m%d")}T235959Z'
    ],
    'attendees': attendees,
    'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'popup', 'minutes': 10},
        ]
    },
    'visibility': 'default',
}).execute()  # pass sendUpdates='all' to trigger email notifications to attendees
```

### Design Rules

- **15 min duration for pump/nebulization** events (time to actually take the medication)
- **5 min duration for spray** events (quick action)
- **Separate events per dose** — morning, evening, and any extra-time doses each get their own VEVENT with their own RRULE. This ensures two distinct daily reminders.
- **Summary prefix** — Use 💊 for regular medications. Previous schedules used 🔴 (steroids), 🟡 (acid reflux), 🟠 (anti-allergy), ☀️/🌙 (morning/night), ❗ (SOS/rescue) — but the user prefers 💊 as a unified prefix going forward.
- **Attendees** — Always add Ruhaan (pebblyshark69@gmail.com) and Roshni (rnr@draas.com). The existing medication events already follow this pattern.
- **Recurrence** — Daily for 365 days until next review. Use `UNTIL=<YYYYMMDD>T235959Z` in the RRULE.
- **Reminders** — Use a popup 5-10 minutes before each dose. Do NOT use email reminders for these.

## Step 4 — Present summary to user

After execution, show:

```
✅ Old medication events deleted: X
✅ New events created: Y
Attendees: Ruhaan (pebblyshark69@gmail.com), Roshni (rnr@draas.com)
Valid until: DD Mon YYYY

New schedule:
• 💊 <Medication> at <time> — daily
• 💊 <Medication> at <time> — daily
• 💊 <Medication> at <time> — daily
```

## Short-Course Medication (Antibiotics / Acute Rx)

For short medication courses (3-7 days of BD/TDS dosing like Augmentin, antibiotics, post-op meds), **do NOT use recurring events**. Create individual one-shot events per dose.

### Pattern — BD (twice daily) × 3 days

```python
doses = [
    ('2026-06-21', 19, 'Night (Dose 1 of 6)'),   # 7pm today
    ('2026-06-22', 7,  'Morning (Dose 2 of 6)'),  # 7am
    ('2026-06-22', 19, 'Night (Dose 3 of 6)'),    # 7pm
    ('2026-06-23', 7,  'Morning (Dose 4 of 6)'),  # 7am
    ('2026-06-23', 19, 'Night (Dose 5 of 6)'),    # 7pm
    ('2026-06-24', 7,  'Morning (Dose 6 of 6)'),  # 7am (last dose)
]

attendees = [
    {'email': 'rnr@draas.com', 'displayName': 'Roshni Ranka'},
    {'email': 'ruhaanr.2030@gsuite.aditi.edu.in', 'displayName': 'Ruhaan Ranka'},
]

for date_str, hour, label in doses:
    event = calendar.events().insert(calendarId='primary', body={
        'summary': f'💊 Augmentin 625 — Ruhaan {label}',
        'description': 'After food. Post-op antibiotic course.',
        'start': {'dateTime': f'{date_str}T{hour:02d}:00:00+05:30', 'timeZone': 'Asia/Kolkata'},
        'end':   {'dateTime': f'{date_str}T{hour:02d}:15:00+05:30', 'timeZone': 'Asia/Kolkata'},
        'attendees': attendees,
        'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 15}]},
        'visibility': 'default',
    }).execute()  # use sendUpdates='all' to email attendees
```

### Time conventions for BD courses

| Dose | Time | Reminder |
|------|------|----------|
| **Morning** | 7:00 AM | 15-min popup |
| **Night** | 7:00 PM | 15-min popup |

### Key differences from recurring Rx

| Aspect | Long-term (recurring) | Short-course (per-dose) |
|--------|----------------------|------------------------|
| Event type | Single recurring VEVENT with RRULE | N individual one-shot events |
| Attendee notification | `sendUpdates='all'` optional | `sendUpdates='all'` recommended (short window) |
| Summary prefix | 💊 (unified) | 💊 + medication name |
| Duration | 5-15 min | 15 min |
| Reminder | 5-10 min popup | 15 min popup (more urgent) |
| Schedule | Per medication rules | Fixed 7am/7pm for BD |

## Pitfalls

- **singleEvents vs recurring** — When searching, `singleEvents=False` returns the recurring event parent. `singleEvents=True` returns individual instances. To delete an entire series, you need the parent event ID. To find the parent, search with `singleEvents=False`.
- **Deleting recurring series** — Calling `delete()` on a recurring event's parent ID removes the entire series. There is no way to undo this via API.
- **Attendee emails** — The user's wife is Roshni/Rochney Ranka (rnr@draas.com). Her personal email is rmurjani@gmail.com. Ruhaan's personal email is pebblyshark69@gmail.com. For calendar events, use rnr@draas.com for Roshni (she accesses this account for calendar notifications).
- **`sendUpdates='all'` sends real emails** — Passing `sendUpdates='all'` to `events().insert()` triggers an email invitation to every attendee. For medication reminders this is intentional and desired — do NOT use `sendUpdates='none'` which suppresses all attendee notifications.
- **Remember confirm-before-actions** — The messaging-drafts skill's confirm-before-actions rule applies to calendar events. Present the planned changes to the user before executing deletions and creations.
- **User may say "wife" but mean Roshni** — "Rochney" in voice transcription maps to "Roshni" (rnr@draas.com). The user's wife's professional name at DRAAS is Roshni Ranka.
