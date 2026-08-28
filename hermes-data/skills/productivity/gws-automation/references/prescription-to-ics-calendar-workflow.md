# Prescription-to-Calendar Workflow

When a user provides a medical prescription (Health Check Record, OP note, or consultation summary) and wants calendar events created for every medication dose.

## Decision: ICS File vs. Calendar API

There are TWO approaches — pick based on user's intent:

| Approach | When to use | How | Attendees |
|---|---|---|---|
| **ICS file** | User says "make a file", "share this with [person]", or wants to import into any calendar app | Generate .ics via `write_file`, deliver via MEDIA | ATTENDEE in ICS marks who it's shared with — does NOT send notifications |
| **Calendar API** | User says "add to my calendar", "add [person] as attendee", or wants recurring events with reminders | Use `gws_auth.build_service('calendar', 'v3')` to create events directly on their primary calendar | Real attendees — `sendUpdates='all'` sends email invitations. Use for family/caregiver notification |

**Signal for Calendar API route:** User explicitly mentions attendee names/emails, says "add my wife", or wants reminders/popups. Do NOT use ICS when you have the OAuth token and the user wants live events.

## Calendar API Approach

For direct Google Calendar events with attendees:

1. **Build the service:** `calendar = build_service('calendar', 'v3', telegram_id=...)`
2. **Delete old medication events first** — Find by keyword (patient name, "Ruhaan", "medication") in `q=` parameter, delete each recurring event by ID
3. **Create each dose as a SEPARATE recurring event** — NOT one multi-hour span:
   ```python
   attendees = [
       {'email': 'rnr@draas.com', 'displayName': 'Roshini Ranka'},
       {'email': 'pebblyshark69@gmail.com', 'displayName': 'Ruhaan Ranka'},
   ]
   event = calendar.events().insert(calendarId='primary', body={
       'summary': '💊 Ruhaan - Morning Pump (7 AM)',
       'description': 'One pump in the morning.\nDaily at 7:00 AM.',
       'start': {'dateTime': '2026-06-15T07:00:00+05:30', 'timeZone': 'Asia/Kolkata'},
       'end': {'dateTime': '2026-06-15T07:10:00+05:30', 'timeZone': 'Asia/Kolkata'},
       'recurrence': ['RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20270615T235959Z'],
       'attendees': attendees,
       'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 5}]}
   }).execute()
   ```
4. **Attendee pattern for children's medication:** Primary caregiver (rnr@draas.com) + child (pebblyshark69@gmail.com)

### Temporary Medications Alongside Permanent Schedule

A common pattern: short-course antibiotics or stomach protectants that coexist with the permanent daily regimen at the same time slots.

| Scenario | RRULE | Example |
|---|---|---|
| **Permanent daily** | `FREQ=DAILY;INTERVAL=1;UNTIL=20270615T235959Z` | Nasal Spray 6PM daily for 365 days |
| **Short course (same time slot)** | `FREQ=DAILY;COUNT=2` — separate event | Azhi 500 at 6PM on Jun 16-17 only |
| **Short course (different time)** | `FREQ=DAILY;COUNT=2` — separate event | Lanzole Junior at 7AM on Jun 16-17 only |

**Implementation pattern:** Create short-course events as completely separate recurring events with `COUNT=N`. Do NOT modify the permanent event's RRULE. Add a note in the description clarifying the duration. Same attendee pattern applies.

**Verification point before creating:** Ask the user "Is this a permanent change or a temporary course with end date?" If temporary, get the exact number of days and whether it overlaps or replaces a permanent medication at that time slot.

## ICS File Approach

For portable, shareable .ics files:

**Generate a single .ICS file with all events**, letting the user import it into any calendar app. The ICS file is self-contained and the user can share it with family members.

## Step 1 — Extract prescription data from the document

Use `pdftotext` or OCR to extract:

| Field | Example |
|---|---|
| Patient | Master Ruhaan Ranka |
| Doctor | Dr. Vasunethra Kasargod |
| Hospital | Manipal Hospital Millers Road |
| Date | 23/12/2025 |
| Diagnosis | Bronchial Asthma — Persistent |

**List ALL medications**, not just the main one. Common categories:

| Type | Example | Frequency |
|---|---|---|
| **Maintenance inhaler** | FORACORT 100mcg (Budesonide+Formoterol) 2 puffs | Twice daily (morning + evening) |
| **Rescue inhaler** | LEVOLIN (Levosalbutamol) 2 puffs | As needed for wheeze/breathlessness |
| **Nebulization** | FORAPRL 0.5mg/2ml Respules (Budesonide+Formoterol) 1 respule | As needed if symptoms worsen |
| **Oral steroid** | PREDMET 8mg (Methylprednisolone) | Short course (verify with user) |
| **Anti-allergy** | MONTEK LC Kid (Montelukast+Levocetirizine) | Daily |
| **Immunotherapy (pending)** | SLIT for HDM (from external provider) | Once medication obtained |
| **Follow-up** | Review with PFT | In 3-4 months |

## Step 2 — Interpret the dosing schedule

Decode clinic handwriting patterns. Common formats found in Indian pulmonology OPD slips:

| Written as | Interpretation |
|---|---|
| `2 PUFFS--0--2PUFFS---DAILY` | 2 puffs morning, 0 midday, 2 puffs evening = **twice daily** |
| `1-1-1-1` | Up to 4 times daily (as needed for rescue meds) |
| `DAILY TILL NEXT VISIT` | Ongoing — set as recurring event with an end date (next review) |
| `REVIEW AFTER 3-4 MONTHS` | Single reminder event at target date |
| `TO CONSIDER X` | Pending decision — create as a single reminder to act |

**Confirm with the user before finalizing** for any ambiguous dosing (e.g. steroid courses).

## Step 3 — Create the .ICS file

Use the `write_file` tool to create a valid iCalendar (RFC 5545) file.

### Headers

```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Hermes//Medication Schedule//EN
METHOD:PUBLISH
X-WR-CALNAME:PatientName - Medication Schedule
X-WR-TIMEZONE:Asia/Kolkata
```

### Timezone definition (Asia/Kolkata)

```ics
BEGIN:VTIMEZONE
TZID:Asia/Kolkata
X-LIC-LOCATION:Asia/Kolkata
BEGIN:STANDARD
TZOFFSETFROM:+0530
TZOFFSETTO:+0530
TZNAME:IST
DTSTART:19700101T000000
END:STANDARD
END:VTIMEZONE
```

### Event structure with RRULE

For daily maintenance medications:

```ics
BEGIN:VEVENT
DTSTART;TZID=Asia/Kolkata:20260609T080000
DTEND;TZID=Asia/Kolkata:20260609T081500
RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20260930T235959
SUMMARY:PatientName - FORACORT 100mcg Morning Dose
DESCRIPTION:Medication: FORACORT 100mcg (Formoterol + Budesonide)\n
 Dose: 2 puffs via ZEROSTAT VT Spacer\n
 After use: Rinse mouth / gargle with water\n\n
 Prescribed by: Dr. X\n Hospital: Y\n Date: DD/MM/YYYY
LOCATION:Home
ATTENDEE;CN=Roshni Ranka;ROLE=OPT-PARTICIPANT;PARTSTAT=NEEDS-ACTION:mailto:rnr@draas.com
TRANSP:OPAQUE
PRIORITY:1
END:VEVENT
```

For as-needed / rescue medications (weekly reminder, not daily):

```ics
BEGIN:VEVENT
DTSTART;TZID=Asia/Kolkata:20260609T120000
DTEND;TZID=Asia/Kolkata:20260609T121500
RRULE:FREQ=WEEKLY;INTERVAL=1;BYDAY=MO;UNTIL=20260930T235959
SUMMARY:❗ PatientName - LEVOLIN Rescue Inhaler (Keep handy)
DESCRIPTION:Rescue Inhaler - As needed only\n
 Medication: LEVOLIN 2 puffs (Levosalbutamol)\n
 Use ONLY if: Severe breathlessness / coughing / wheezing\n
 Max frequency: Up to 4 times daily\n\n
 Keep inhaler with patient at school & home.
LOCATION:Home / School Bag
ATTENDEE;CN=Roshni Ranka;ROLE=OPT-PARTICIPANT;PARTSTAT=NEEDS-ACTION:mailto:rnr@draas.com
TRANSP:OPAQUE
END:VEVENT
```

### Event types to include

| # | Type | RRULE | Duration |
|---|------|-------|----------|
| 1 | **Maintenance AM** — 2 puffs | DAILY 8:00 AM | Till next review |
| 2 | **Maintenance PM** — 2 puffs | DAILY 8:00 PM | Till next review |
| 3 | **Nebulization backup** — if symptoms worsen | WEEKLY Mon reminder | Till next review |
| 4 | **Rescue inhaler** — as needed | WEEKLY Mon reminder | Till next review |
| 5 | **SLIT / pending action** — contact provider | Single event tomorrow | One-time |
| 6 | **Follow-up review** — with PFT | Single event in 3-4 months | One-time |

### Key design rules

- **Morning and evening events are SEPARATE VEVENTs** with their own RRULEs — not one event spanning 12 hours. This ensures the user gets two distinct reminders daily.
- **Use `\n` (literal backslash-n) in DESCRIPTION** for multi-line text. Do NOT use actual newlines — ICS spec requires line folding.
- **No table syntax in DESCRIPTION** — ICS doesn't support HTML. Use labeled key: value pairs or bullet-style lines.
- **Timezones matter** — Always define `VTIMEZONE` for `Asia/Kolkata` and use `DTSTART;TZID=Asia/Kolkata` instead of UTC offsets. This ensures the events stay at the correct local time year-round regardless of DST.
- **ATTENDEE format** — `ATTENDEE;CN=DisplayName;ROLE=OPT-PARTICIPANT;PARTSTAT=NEEDS-ACTION:mailto:email@domain.com`
- **PATSTAT=NEEDS-ACTION** means the attendee has not yet responded — this is correct for newly shared calendar entries.

## Step 4 — Validate the ICS

```python
with open("file.ics") as f:
    content = f.read()
assert content.startswith("BEGIN:VCALENDAR")
assert content.endswith("END:VCALENDAR\n") or content.endswith("END:VCALENDAR")
assert content.count("BEGIN:VEVENT") == content.count("END:VEVENT")
```

Check that:
- `BEGIN:VCALENDAR` / `END:VCALENDAR` are present
- Every `BEGIN:VEVENT` has a matching `END:VEVENT`
- Each VEVENT has `DTSTART`, `DTEND`, `SUMMARY`, `DESCRIPTION`

## Step 5 — Deliver via MEDIA

```python
write_file(path="/data/hermes/cron/output/patient_medication_schedule.ics", content=ics_content)
# Then include MEDIA:/data/hermes/cron/output/patient_medication_schedule.ics in your Telegram response
```

MEDIA delivery sends the ICS as a file the user can tap → open in Calendar app → import all events at once.

## Step 6 — Present the schedule to the user

Along with the file, show a markdown summary table so the user can review before importing:

```
📋 Medication Schedule — Patient Name

| Time | Medication | Dose | Duration |
|------|-----------|:----:|----------|
| 8:00 AM | FORACORT 100mcg via spacer | 2 puffs | Daily |
| 8:00 PM | FORACORT 100mcg via spacer | 2 puffs | Daily |
| As needed | LEVOLIN rescue inhaler | 2 puffs | Only if symptoms |
| Pending | SLIT for HDM — Contact Provider | — | Start once meds obtained |

Events in file: 5 (maintenance AM, maintenance PM, rescue reminder, SLIT follow-up, doctor review)
Attendee: Roshni Ranka (rnr@draas.com)
```

## Pitfalls

- **User may only reference one document but expect ALL medications** — The Dec 2025 Health Check Record only lists inhalers; the Sep 2025 pharmacy invoice lists additional tablets (PREDMET, RAZO, MONTEK LC). Always check both the most recent Health Check Record AND the most recent pharmacy invoice for a complete picture. Present the full list and ask the user to confirm which are current.
- **"Today's prescription" date mismatch** — The user may refer to a document as "today's" even though the date on it is months old (e.g., they just scanned a Dec 2025 document today). Don't argue about the date — work with the content they provided.
- **ICS `END:VCALENDAR` validation** — The Python one-liner `content.endswith("END:VCALENDAR")` may return False if there's a trailing newline. ICS specs tolerate trailing newlines — the file is valid.
- **ATTENDEE emails** — ICS ATTENDEE properties don't actually send emails; they just mark who the event is shared with. The user will need to share the ICS separately if they want others to get notifications. For DRAAS: the primary caregiver (Roshni, rnr@draas.com) is the attendee.

## Pitfall — Voice-Dictated Medication Schedules: Confirm Before Execution

**Problem:** When a user dictates a medication schedule via voice (especially for a child's complex regimen), the times and medication types are highly error-prone in transcription. In one session (Jun 2026), the schedule went through **3 corrections** before getting right:

1. First pass: New Pump at 6PM, Nasal Spray at 7AM and 9PM
2. Corrected: Nasal Spray at 6PM (once daily), New Pump at 9PM
3. Final: Morning Pump at 7AM, Nasal Spray at 6PM (once daily), New Pump at 9PM

**Fix — Always present a structured summary for confirmation before creating or deleting any events:**

1. **Parse the voice dictation** into a clear medication-by-time table
2. **Show the summary** in Telegram before any API calls:
   ```
   Schedule I parsed:
   • 7:00 AM — Morning Pump (daily)
   • 6:00 PM — Nasal Spray (daily) + Azhi 500 (Jun 15-17 only)
   • 9:00 PM — New Pump (daily)
   Attendees: Mother + Child
   ```
3. **Wait for explicit confirmation** before deleting old events or creating new ones
4. **Key verification points** to check mentally:
   - Are AM/PM times correct? (6PM vs 9PM are easily confused in voice)
   - Is it "once daily" or "twice daily"?
   - Is this a permanent change or temporary addition (like a short-course antibiotic)?
   - Are there short-term medications alongside long-term ones?
5. **After confirmation**, delete ALL old medication events first, then create new ones — never mix old and new.
