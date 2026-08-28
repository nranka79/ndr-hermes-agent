# Interview Scheduling Workflow — Resume to Calendar + WhatsApp

## When to Use

User provides a candidate's resume PDF and asks to schedule an interview — calendar event with Google Meet, invite guests (including the candidate), attach resume, and notify via WhatsApp.

**Trigger signals:**
- "schedule interview for [candidate name]"
- "calendar the interview" + resume attachment
- "interview at [time] — accounts officer / CA / [role]" + resume PDF

---

## Complete Workflow

### Stage 1 — Extract Candidate Info from Resume PDF

**Problem:** `vision_analyze` only accepts real image files, not PDFs. PDFs must be converted first.

**Working pattern (confirmed June 2026):**
```python
# Convert PDF page 1 to JPG for vision_analyze
from pdf2image import convert_from_path

pages = convert_from_path(
    '/data/hermes/document_cache/doc_XXXXXXXX.pdf',  # actual path from upload
    dpi=150,
    first_page=1,
    last_page=1
)
pages[0].save('/tmp/resume_p1.jpg', 'JPEG')
# Then: vision_analyze('/tmp/resume_p1.jpg', question="Extract full name, email, phone...")
```

Extract: full name, email address, phone number, qualifications, current employer.

**Also search Gmail for other guest email addresses** (e.g., eChamundeshwari at draas.com was found via Gmail search in June 2026 session).

---

### Stage 2 — Upload Resume to Drive

Upload the PDF to Drive so the calendar event description can link to it.

```python
from tools.gws_auth import build_service

drive_svc = build_service('drive', 'v3', telegram_id='<telegram_id>')

meta = {'name': 'Srivatsa_2UPresume.pdf', 'parents': ['root']}
media_body = drive_svc.files().create(
    body=meta,
    media_body=open('/data/hermes/document_cache/doc_XXXXXXXX.pdf', 'rb'),
    fields='id, webViewLink'
).execute()

file_id = media_body.get('id')          # → '1BnLsyz8B3a7jxh_VOwrNxkAIDUeqNZnX'
drive_link = media_body.get('webViewLink')
```

Use `webViewLink` in the calendar event description. Use `id` to construct the preview link: `https://drive.google.com/file/d/<id>/preview`.

---

### Stage 3 — Create Calendar Event with Google Meet

**calendarId:** Always pass `calendarId='primary'` — the API requires it explicitly (omitting it raises `TypeError: Missing required parameter "calendarId"`).

**conferenceDataVersion:** Pass `conferenceDataVersion=1` when creating the event with `conferenceData.createRequest` — otherwise the Meet link is not generated.

**sendUpdates:** Always use `sendUpdates='all'` so all attendees receive the calendar invite by email automatically. This eliminates the need for a separate Gmail send operation.

```python
from datetime import datetime, timedelta

cal_svc = build_service('calendar', 'v3', telegram_id='<telegram_id>')

today = datetime.now().date()
event_time = datetime(today.year, today.month, today.day, 16, 0, 0)  # 4 PM
end_time = event_time + timedelta(hours=1)  # 5 PM

event_body = {
    'summary': 'Interview — TRINADH SRIVATSA. S (Accounts Officer)',
    'description': '''Interview for Accounts Officer Position.

Candidate: TRINADH SRIVATSA. S
Email: stsrologs@gmail.com
Phone: (+91) 6300431110

Resume: https://drive.google.com/file/d/1BnLsyz8B3a7jxh_VOwrNxkAIDUeqNZnX/view''',
    'start': {
        'dateTime': event_time.isoformat(),
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': end_time.isoformat(),
        'timeZone': 'Asia/Kolkata',
    },
    'attendees': [
        {'email': 'candidate@email.com', 'displayName': 'Candidate Name'},
        {'email': 'echamundeshwari@draas.com', 'displayName': 'Eshwari Chamundeshwari'},
        {'email': 'rnr@draas.com', 'displayName': 'Roshini Ranka (R&R)'},
    ],
    'conferenceData': {
        'createRequest': {
            'conferenceSolutionKey': {'type': 'hangoutsMeet'},
            'requestId': f'interview-{candidate}-{today.isoformat()}'
        }
    },
    'sendUpdates': 'all'
}

created_event = cal_svc.events().insert(
    calendarId='primary',
    body=event_body,
    conferenceDataVersion=1,
    sendUpdates='all'
).execute()

event_id = created_event['id']  # → 'hgtu46oliq4jfrt00pu26067q0'
```

**To retrieve the Meet link after creation** (conferenceData may not be in the insert response):
```python
# Patch the event to force Meet generation
patched = cal_svc.events().patch(
    calendarId='primary',
    eventId=event_id,
    body={'conferenceData': {
        'createRequest': {
            'conferenceSolutionKey': {'type': 'hangoutsMeet'},
            'requestId': f'interview-{candidate}-patch-{datetime.now().date().isoformat()}'
        }
    }},
    conferenceDataVersion=1
).execute()

entry_points = patched.get('conferenceData', {}).get('entryPoints', [])
for ep in entry_points:
    if ep.get('entryPointType') == 'videoBridge':
        meet_link = ep.get('uri', '')  # → 'https://meet.google.com/sua-xoqc-fja'
```

---

### Stage 4 — Reschedule / Update Event

**Reschedule (change time only):**
```python
new_time = datetime(today.year, today.month, today.day, 16, 0, 0)  # new time
new_end = new_time + timedelta(hours=1)

cal_svc.events().patch(
    calendarId='primary',
    eventId=event_id,
    body={
        'start': {'dateTime': new_time.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': new_end.isoformat(), 'timeZone': 'Asia/Kolkata'},
    }
).execute()
# sendUpdates='all' is default for patch — attendees will be notified of the time change
```

**Update title (change position):**
```python
cal_svc.events().patch(
    calendarId='primary',
    eventId=event_id,
    body={
        'summary': 'Interview — TRINADH SRIVATSA. S (Accounts Officer)',  # corrected from CA Final
    }
).execute()
```

---

### Stage 5 — Send WhatsApp to Candidate

**Always present the wa.me link to the user for confirmation before sending.** Do NOT send automatically.

**For interview notification, include:**
- Candidate's name
- Position title (corrected: NOT "CA" — confirm with user)
- Date, time (IST)
- Google Meet link
- Request to keep resume ready

```python
from urllib.parse import quote

message = f"""Dear Mr. {first_name},

Namaste! Greetings from DRA Group.

We are pleased to inform you that your interview for the {position} position has been scheduled.

📅 Date: June 1, 2026 (Monday)
🕒 Time: 4:00 PM IST
🔗 Google Meet: {meet_link}

Please join the meeting at the scheduled time. Kindly keep your resume and relevant documents handy for the discussion.

We look forward to speaking with you.

Best regards,
DRA Group HR Team"""

message = message.replace("&", "\uFF06")  # fullwidth ampersand fix
encoded = quote(message, safe='')
wa_link = f"https://api.whatsapp.com/send?phone=91{phone}&text={encoded}"
```

**Position correction rule (from June 2026 session):** User corrected "CA Final" to "Accounts Officer" mid-session. Always confirm the exact job title with the user before generating the WhatsApp message.

---

## Variant: In-Person Final Interview / Onboarding Meeting

**When to use this variant (vs. the standard resume-based workflow):**
- User says "final meeting", "final interview", "onboarding", "coming to meet me"
- No resume PDF attached — candidate already shortlisted
- Location is a real office address, not a video call
- Attendees include the hiring manager (who shortlisted) + spouse + candidate

**Differences from standard interview workflow:**

| Aspect | Standard (video) | In-Person Final |
|--------|-----------------|-----------------|
| Resume PDF | Yes — convert to JPG, extract info | No — candidate already known |
| Meeting link | Google Meet generated | None — use location field |
| Attendees | Candidate + HR + spouse | Candidate + hiring manager (e.g. Gauri Singh type) + spouse |
| Event title | "Interview — [Name] ([Role])" | "Final Interview — [Name] ([Role])" or "[Role] Final Meeting" |
| Description | Resume link + interview details | Context: shortlisted by [manager], final discussion + onboarding |
| WhatsApp content | Meet link | Location + time (no Meet link) |

**Example event body (in-person final):**
```python
event_body = {
    'summary': 'Final Interview — Neha (Content Developer)',
    'description': '''Final interview and onboarding discussion.

Candidate: Neha
Position: Content Developer
Shortlisted by: Gauri Singh

Venue: Diary Reality Office
Date: June 2, 2026 | Time: 10:30 AM IST''',
    'location': {'address': 'Diary Reality Office'},
    'start': {'dateTime': '2026-06-02T10:30:00+05:30', 'timeZone': 'Asia/Kolkata'},
    'end': {'dateTime': '2026-06-02T11:30:00+05:30', 'timeZone': 'Asia/Kolkata'},
    'attendees': [
        {'email': 'candidate@draas.com', 'displayName': 'Neha'},
        {'email': 'gaurisingh@draas.com', 'displayName': 'Gauri Singh'},
        {'email': 'rnr@draas.com', 'displayName': 'Roshini Ranka'},
    ],
    'sendUpdates': 'all'
}
# Note: no conferenceData for in-person meetings
```

**Formatting the event description** (from June 2026 formatting session):
- Section headers → HEADING_2 style via Google Docs API `updateParagraphStyle`
- Signatory/role lines → bold via `updateTextStyle`
- Clean `**bold**` Markdown markers from Google Docs text runs (use `replaceAllText` on the document body)

---

## Common Email Lookups

| Person | Email | Source |
|--------|-------|--------|
| Eshwari Chamundeshwari | echamundeshwari@draas.com | Gmail search |
| Roshini Ranka (R&R) | rnr@draas.com | User provided |
| Candidate | From resume PDF | vision_analyze |

---

## Pitfalls

- **`conferenceDataRequested` not a valid parameter** on `events().get()` — use `events().patch()` with `conferenceDataVersion=1` to retrieve/generate the Meet link after insert.
- **`calendarId='primary'` is required** — omitting raises `TypeError: Missing required parameter "calendarId"`.
- **Event ID from insert() may produce broken links** — the event ID returned by `events().insert()` can produce calendar links that don't resolve properly. Always re-fetch the event list after creation (`events().list()`) to get the correct, verified event ID and HTMLEventLink before returning to the user. See the Calendar event links memory rule.
- **Gmail send API returns HTTP 404** on this account — do NOT attempt `POST /gmail/v1/users/me/messages.send`. For interview scheduling, use Calendar's `sendUpdates='all'` which sends email invites to all attendees automatically. This is the correct delivery path.
- **Always confirm job title with user** — user may say "CA" when they mean "Accounts Officer" or vice versa. Get explicit confirmation before drafting WhatsApp or creating calendar event.
- **Resume PDF → vision_analyze**: Convert with pdf2image first (dpi=150), save to /tmp, then pass the JPG to vision_analyze. Direct PDF to vision_analyze raises "Only real image files supported."
- **File ID corruption from context compaction** — compacted context can corrupt Drive file IDs (one wrong char in middle + one at end). Always re-list the target folder before any Drive write operation (rename, update, share). List by parent folder, match by filename, use the freshly-listed ID.
- **Google Docs formatting — HEADING_2 on wrong paragraphs**: When formatting letter-style documents via Docs API, the address/header lines (`Date:`, `To,`, `Dear [Name],`, `Re:`) get assigned HEADING_2 style automatically by the API's style inference. These should be NORMAL_TEXT. Re-read the document after formatting and patch any incorrectly-styled paragraphs. Use `updateParagraphStyle` with `namedStyleType: 'NORMAL_TEXT'` to fix.

---

## HR Candidate Tracking Doc (for post-interview notes)

After the interview, record outcome in the HR Candidates doc:
- Doc ID: `1UjMKcIDeoEb3wPHkrOyRnUh-hAq38sYVBJhcFe40APo`
- Fields: Name, Status, Communication, Skills, Joining, Key Concern, Notes
- See `references/hr-candidate-tracking.md` for full pattern