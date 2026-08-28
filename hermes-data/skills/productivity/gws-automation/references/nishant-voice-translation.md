# Nishant Voice Message Translation — Calendar Event Creation

Nishant often sends meeting requests via **voice messages** on Telegram. The speech-to-text can garble proper nouns, company names, and domains. This reference documents known garbled → correct mappings.

## Known Garbled-to-Correct Mappings

| Garbled (STT Output) | Correct Meaning | Source / How to Decode |
|---|---|---|
| "yellow eye" / "the yellow eye" | **theyelloweye.com** domain | Nishant Prakash's company domain. Check Gmail for emails from `nishantprakash@theyelloweye.com` |
| "Diary Reality" / "diary realty" | **DRA Realty** | Standard voice garbling of "DRA Realty" |
| "Jiraffe" / "jiraffe" / "giraffe" | **JIRAFFE** (likely a company name in Balaji Land deal) | Confirmed in Gmail subject: "Ranka Oasis Balaji Land Jiraffe JD Deal IRR" |
| "Gmail email address" (for a person who also has a work domain) | Person's personal Gmail | Check Google Sheets share notifications. E.g., Nishant Prakash's Gmail `nishantprakash1@gmail.com` was found via his Google Sheets share request |
| "Prakash Singh" (when you already talk to Prakash) | **Prakash** the person, not Nishant Prakash | Context-dependent — Nishant might refer to a different "Nishant Prakash" |
| "Aamir" in voice | **Aamir Khan** (partner) | Cross-reference from memory: `aamirkhan@me.com` / `+919845881652` |
| "Salman" in voice | **Salman Khalid** (partner) | `salman@redificedevelopers.com` / `+919845532593` |

## Workflow for Creating Events from Nishant's Voice Messages

### 1. Parse the request components

Nishant's typical voice meeting request contains:
- **Who:** Meeting with [Person/Company]
- **Title:** Usually involves the project/company name (often garbled)
- **Attendee emails:** May mention "one Gmail" (personal) + "one email" (work domain) for the same person
- **Location:** Often garbled — "Diary Reality" = DRA Realty
- **Time:** Usually explicitly stated ("today")

### 2. Resolve attendee email addresses

**Primary method — Gmail search:**
```python
gmail = build_service('gmail', 'v1', telegram_id='ndr')
results = gmail.users().messages().list(
    userId='me', q='[person name] [domain/company]', maxResults=5
).execute()
```

**Look for these email patterns:**
- Google Sheets/Docs share notifications — `drive-shares-dm-noreply@google.com` — these show the person's email in the body
- Direct emails from the person — check `From`, `To`, `Cc` headers
- Apple Calendar invites — `noreply@email.apple.com` — often show both email addresses

**Commonly found email pairs for DRAAS associates:**
| Person | Work Email | Personal Email |
|---|---|---|
| Nishant Prakash | nishantprakash@theyelloweye.com | nishantprakash1@gmail.com |

### 3. Resolve garbled location

When Nishant says "Diary Reality" or similar:
- **Map to:** DRA Realty (the DRAAS office/meeting location)
- Use as `location: "DRA Realty"` in the calendar event

### 4. Create the calendar event

```python
from tools.gws_auth import build_service
from datetime import datetime, timedelta
import pytz

cal = build_service('calendar', 'v3', telegram_id='ndr')
tz = pytz.timezone('Asia/Kolkata')

# Default to 1:00 PM if time is implied, otherwise use explicit time
event_start = tz.localize(datetime(now.year, now.month, now.day, 13, 0, 0))
event_end = event_start + timedelta(hours=1)

event = {
    'summary': 'Meeting with [Person] - [PROJECT] [Topic]',
    'location': 'DRA Realty',
    'description': 'Meeting regarding [details]',
    'start': {'dateTime': event_start.isoformat(), 'timeZone': 'Asia/Kolkata'},
    'end': {'dateTime': event_end.isoformat(), 'timeZone': 'Asia/Kolkata'},
    'attendees': [
        {'email': 'nishantprakash@theyelloweye.com'},
        {'email': 'nishantprakash1@gmail.com'},
    ],
}

created = cal.events().insert(
    calendarId='primary', body=event, sendUpdates='all'
).execute()
```

### 5. Present confirmation

Format as a table showing all resolved fields:

| Field | Detail |
|---|---|
| **Title** | Meeting with Nishant Prakash - JIRAFFE Balaji Land commercial finalization |
| **Date** | Today, July 6, 2026 |
| **Time** | 1:00 PM – 2:00 PM IST |
| **Location** | DRA Realty |
| **Attendees** | nishantprakash@theyelloweye.com, nishantprakash1@gmail.com |

## Pitfalls

- **Multiple "Nishant" persons:** Nishant Ranka (the CEO/NDR) vs Nishant Prakash (associate/partner). Voice-to-text can confuse them. Context: "meeting with Nishant Prakash" means the associate, not Ranka himself.
- **No explicit time in voice:** When Nishant says "today" without a time, default to **1:00 PM** (lunchtime slot) — this is the most common meeting default in context. If that's already past, set it 15-30 min from now.
- **Email confusion:** The same person may share a Google Sheet from their personal Gmail but correspond via their work domain. Add BOTH emails as attendees.
- **Voice garbling patterns:** Nishant's voice messages commonly garble: company names (Jiraffe, Blinkit, Zepto, Instamart), domain names (theyelloweye.com), location names (Gandhinagar, Yelahanka, Nature's Basket).
