# Interview Scheduling — Calendar + Meet + Resume Workflow

## Session Context (2026-06-01)

Candidate: TRINADH SRIVATSA. S — CA Final (Group 2 result awaited), articleship at Rao & Manoj Associates, Visakhapatnam. Position: Accounts Officer (NOT "CA" — user corrected).

4 MLID guests:
- MLID 1: Candidate — stsrivatsa@gmail.com | phone from resume: +91 6300431110
- MLID 2: Eshwari Chamundeshwari — echamundeshwari@draas.com | phone: TBD (user to confirm)
- MLID 3: R-N-R (Roshini Ranka) — rnr@draas.com | phone: +91 9845026390
- MLID 4: N-D-R (Nishant Ranka) — ndr@draas.com | phone: +91 9880055634

Time: 4:00 PM – 5:00 PM IST (rescheduled from 3 PM — user said "reschedule it 4-5 instead of 3-4")
Meet: https://meet.google.com/sua-xoqc-fja
Resume: https://drive.google.com/file/d/1BnLsyz8B3a7jxh_VOwrNxkAIDUeqNZnX/view

User workflow: list all corrections → ask confirmation → only then apply to calendar.

---

## Full Workflow

### Step 1 — Extract candidate info from resume PDF

`vision_analyze` does NOT support PDFs directly — must convert to image first.

```python
from pdf2image import convert_from_path
pages = convert_from_path('/path/to/resume.pdf', dpi=200, first_page=1, last_page=1)
pages[0].save('/tmp/resume_p1.jpg', 'JPEG')
```

Then `vision_analyze(image_url='/tmp/resume_p1.jpg', question="Extract full name, email, phone, education, experience")`

Key fields: full name, email, phone, location, CA Final groups + result status, articleship firm + duration + responsibilities.

### Step 2 — Resolve guest emails via Gmail search

When a guest email isn't in the contacts sheet, search Gmail:

```python
from tools.gws_auth import build_service
svc = build_service('gmail', 'v1', telegram_id='<telegram_id>')
results = svc.users().messages().list(userId='me', q='e-chamundeshwari', maxResults=5).execute()
for m in results.get('messages', []):
    msg = svc.users().messages().get(userId='me', id=m['id'], format='metadata',
        metadataHeaders=['From', 'Subject']).execute()
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    print(headers.get('From', ''))  # e.g. "Eshwari Chamundeshwari <echamundeshwari@draas.com>"
```

If Gmail search returns nothing: ask the user directly. User confirmed R&R email as rnr@draas.com when Gmail couldn't find "rate.trust" domain.

### Step 3 — Upload resume to Drive

```python
drive_svc = build_service('drive', 'v3', telegram_id='<telegram_id>')
meta = {'name': 'Resume.pdf', 'parents': ['root']}
drive_file = drive_svc.files().create(body=meta, media_body=resume_path, fields='id,webViewLink').execute()
resume_link = f"https://drive.google.com/file/d/{drive_file['id']}/view"
```

Use the Drive link in the calendar event description.

### Step 4 — Create Google Calendar event with Meet

```python
from datetime import datetime, timedelta

cal_svc = build_service('calendar', 'v3', telegram_id='<telegram_id>')
today = datetime.now().date()
event_time = datetime(today.year, today.month, today.day, 15, 0, 0)  # 3 PM IST
end_time = event_time + timedelta(hours=1)

event_body = {
    'summary': 'Interview — [Candidate Name] ([Position])',
    'description': f'''Interview for [Position].

Candidate: [Full Name]
Email: [email]
Phone: [phone]
Location: [city]

Qualifications:
• [education details]

Experience: [years] at [firm name]
• [key responsibilities]

Resume: {resume_link}''',
    'start': {'dateTime': event_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
    'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
    'attendees': [
        {'email': 'candidate@email.com', 'displayName': 'Candidate Name'},
        {'email': 'echamundeshwari@draas.com'},
        {'email': 'rnr@draas.com'},
    ],
    'conferenceData': {'createRequest': {
        'conferenceSolutionKey': {'type': 'hangoutsMeet'},
        'requestId': f'interview-{candidate_name}-{today.isoformat()}'
    }},
    'sendUpdates': 'all'
}

created = cal_svc.events().insert(
    calendarId='primary',  # REQUIRED — without this: TypeError: Missing required parameter "calendarId"
    body=event_body,
    conferenceDataVersion=1
).execute()

print('Event ID:', created['id'])
print('HTML Link:', created.get('htmlLink', ''))
```

### Step 5 — If Meet link not auto-generated, patch it

```python
patched = cal_svc.events().patch(
    calendarId='primary',
    eventId=created['id'],
    body={'conferenceData': {'createRequest': {
        'conferenceSolutionKey': {'type': 'hangoutsMeet'},
        'requestId': f'interview-{candidate_name}-patch-{datetime.now().date().isoformat()}'
    }}},
    conferenceDataVersion=1
).execute()

entry_points = patched.get('conferenceData', {}).get('entryPoints', [])
meet_link = next((ep['uri'] for ep in entry_points if ep.get('entryPointType') == 'video'), '')
print('Meet link:', meet_link)
```

### Step 6 — Confirm with user BEFORE making any calendar changes

**CRITICAL — user workflow for multi-guest calendar changes:**

User wants to see ALL corrections listed clearly, THEN explicitly confirm before any live changes are made.

Pattern to follow:
1. List ALL corrections with before/after for each
2. List all 4 MLID guests with their confirmed emails
3. State time, Meet link, position clearly
4. Ask: "**Confirm to proceed with all changes?**"
5. Only after user says "yes / go ahead" → apply changes to calendar + send WhatsApp

Do NOT use `send_message` for user confirmations — it fails with cross-user blocking. Plain text reply is the reliable delivery mechanism. Only use `send_message` for automated push to external contacts (candidate, guests).

---

## Confirmed Gotchas (from 2026-06-01 session)

1. **`calendarId='primary'` is REQUIRED** — `events().insert()` without it raises `TypeError: Missing required parameter "calendarId"`

2. **`conferenceDataRequested` is NOT valid for `events().get()`** — raises `TypeError: Got an unexpected keyword argument 'conferenceDataRequested'`. Use `events().patch()` with `conferenceDataVersion=1` to add Meet after creation.

3. **`send_message` fails for user-facing confirmations** — "Platform 'telegram' is not configured" or cross-user blocking. Plain text reply is the reliable delivery mechanism in this session. Only use `send_message` for automated push.

4. **Gmail search is the fallback for contact resolution** — People API may not have all DRA contacts. e-chamundeshwari@draas.com found via Gmail; R&R email required user clarification (rnr@draas.com confirmed by user).

---

## Email Addresses Discovered This Session

| Person | MLID | Email |
|--------|------|-------|
| TRINADH SRIVATSA. S (Candidate) | MLID 1 | stsrivatsa@gmail.com |
| Eshwari Chamundeshwari | MLID 2 | echamundeshwari@draas.com |
| Roshini Ranka (R&R) | MLID 3 | rnr@draas.com |
| Nishant Ranka (N-D-R) | MLID 4 | ndr@draas.com |

## Session Learnings (2026-06-01)

1. **MLID terminology** — User refers to meeting invite guests as "MLID 1, 2, 3, 4". Candidate is MLID 1, then E-Chamundeshwari, R-N-R, N-D-R follow. When scheduling multi-guest interviews, explicitly label each guest by MLID number.

2. **User requires pre-confirmation before any calendar changes** — Even when the user says "go ahead", they first want a complete list of all corrections laid out clearly, then a separate "confirm to proceed" prompt. Do NOT make changes to live calendar events until user explicitly says "yes" to the full correction list. The pattern: (a) list all corrections, (b) ask "confirm all changes?", (c) only then apply.

3. **Voice transcription of email** — Candidate email was initially misread as stsrologs@gmail.com (voice: "S T S R I V A T S A"). Always verify email domains from the resume PDF via vision, never trust single-pass voice transcription. Correct email: stsrivatsa@gmail.com.

4. **Position title** — User said "it is not a CA post, it is accounts officer post". Capture exact position title from user, do not infer from resume. "Accounts Officer" not "CA".

5. **Time change** — From 3 PM to 4 PM (user said "reschedule it 4-5 instead of 3-4"). Always confirm the full corrected time range: "4:00 PM – 5:00 PM IST" not just "4 PM".

---

## Session Learnings (2026-06-02 — Neha / Diary Reality Interview)

1. **"Gallantry" = user's term for a calendar event/invite** — When the user says "make a gallantry event", they mean create a Google Calendar event. Use the word "Gallantry" in the event title when the user explicitly uses it (e.g., "Diary Reality — Neha Final Interview (Gallantry)"). Mirror the user's exact wording in the title.

2. **Diary Reality Office — known location** — User has held multiple interviews at Diary Reality Office (Gollahalli, Yelahanka). This is a confirmed recurring interview venue. Do NOT search gbrain for the address — use what has been established across sessions.

3. **Include shortlister name in description** — User says "candidate shortlisted by [name]". Always include the shortlisters name in the event description (e.g., "Shortlisted by: Gauri Singh, DRAAS HR").

4. **Always give calendar event link after creation** — User expects the calendar event link immediately after creating the event. Re-fetch the event by listing that day's events to get the correct HTML link — do not trust the `htmlLink` returned directly from `insert()` (it may produce broken links). Verify by listing events before returning link.

5. **Gauri Singh confirmed as DRAAS HR** — email `gaurisingh@draas.com` (assumed, not yet verified against contacts sheet — verify before sending candidate communications). Shortlisted Neha for Content Developer role.

5. **Gauri Singh — DRAAS HR, not `gaurisingh@draas.com`** — Contacts show her as "Gowri Singh" (spelling varies). Confirmed working emails: `gowrisingh72@yahoo.com` (primary), `gowrisingh1341@gmail.com`. Always search People API for "Gowri Singh" if `gaurisingh` search returns nothing. She shortlists candidates for DRAAS roles.

6. **Roshini email — use `rnr@truss.com` not `rnr@draas.com`** — Roshini prefers her personal email for calendar invites. `rnr@truss.com` is her primary. Also `rnr@draas.com`, `roshiniranka@gmail.com`. NEVER use `roshini.ranka@draas.com` — that form doesn't exist.

7. **Neha — Content Developer candidate** — Final interview and onboarding discussion at Diary Reality Office. Include "Final Interview & Onboarding" in event title/description. Include shortlister name in description.

8. **Calendar event link verification** — After `events().insert()`, always re-fetch the event list for that day to get the confirmed `htmlLink`. The link returned directly from `insert()` may be broken. Verify before returning to user.