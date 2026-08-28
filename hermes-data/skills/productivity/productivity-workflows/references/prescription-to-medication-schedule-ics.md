# Prescription / Health Record → Medication Schedule ICS

When a user provides a prescription or health record (scanned PDF, photo, or existing Drive file) and asks to create a detailed medication schedule with calendar events, use this workflow.

## Trigger

- "Give me a detailed schedule of all treatment and medication"
- "Make relevant calendar events as a .ics file"
- "Add attendee [name] to each event so it goes into their calendar"

## Phase 1 — Extract Medication Data

Use OCR (tesseract via `pdftotext`) on the document to extract:

| Field | Example |
|-------|---------|
| Patient name | MSTR RUHAAN RANKA |
| Doctor | Dr. Vasunethra Kasargod |
| Hospital | Manipal Hospital Millers Road |
| Date | 23/12/2025 |
| Diagnosis | Bronchial Asthma — Persistent |

Then parse each medication line:

```python
# From OCR output, extract structured medication data:
medications = [
    {
        "name": "FORACORT 100mcg (Formoterol + Budesonide)",
        "device": "ZEROSTAT VT Spacer",
        "dose": "2 puffs",
        "schedule": "Morning 8 AM, Evening 8 PM",
        "duration": "Daily till next visit",
        "instructions": "Rinse mouth / gargle with water after use",
        "type": "maintenance"
    },
    {
        "name": "LEVOLIN 2 puffs (Levosalbutamol)",
        "dose": "2 puffs",
        "schedule": "As needed (max 1-1-1-1 = 4 times daily)",
        "trigger": "Severe breathlessness / cough / wheeze",
        "type": "rescue"
    }
]
```

**⚠️ OCR artifacts in dosing:** The raw OCR often produces garbled dosing strings like `"2 PUFFS--0--2PUFFS---DAILY"`. The `--0--` is typically an OCR artifact from a dash or bullet point between doses — interpreted as "2 puffs morning, 2 puffs evening" (not 2-0-2). Verify with the user if unclear.

## Phase 2 — Present Schedule to User

Show a structured summary table before creating events:

```
| Time | Medication | Dose | Duration |
|------|-----------|:----:|----------|
| 8:00 AM | FORACORT 100mcg via spacer | 2 puffs | Daily till next review |
| 8:00 PM | FORACORT 100mcg via spacer | 2 puffs | Daily till next review |
| As needed | LEVOLIN rescue inhaler | 2 puffs | Only if breathless/cough/wheeze |
```

## Phase 3 — Create ICS File

Create a single `.ics` file with:
- **Recurring daily events** for maintenance medications (using `RRULE:FREQ=DAILY`)
- **Weekly reminder events** for as-needed rescue medications
- **One-time events** for pending treatments (SLIT, follow-up appointments)
- All events in `Asia/Kolkata` timezone

### ICS Template

```python
from datetime import datetime, timedelta

ics_lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Hermes//Medication Schedule//EN",
    "X-WR-CALNAME:Ruhaan - Medication Schedule",
    "X-WR-TIMEZONE:Asia/Kolkata",
    "",
    "BEGIN:VTIMEZONE",
    "TZID:Asia/Kolkata",
    "X-LIC-LOCATION:Asia/Kolkata",
    "BEGIN:STANDARD",
    "TZOFFSETFROM:+0530",
    "TZOFFSETTO:+0530",
    "TZNAME:IST",
    "DTSTART:19700101T000000",
    "END:STANDARD",
    "END:VTIMEZONE",
]

def make_medication_event(uid, start_dt, duration_min, summary, description, 
                           rrule=None, attendee_email=None, location="Home", priority=1):
    """Create a VEVENT block for a medication schedule."""
    lines = ["BEGIN:VEVENT"]
    lines.append(f"DTSTART;TZID=Asia/Kolkata:{start_dt}")
    
    start = datetime.strptime(start_dt, "%Y%m%dT%H%M%S")
    end = start + timedelta(minutes=duration_min)
    lines.append(f"DTEND;TZID=Asia/Kolkata:{end.strftime('%Y%m%dT%H%M%S')}")
    
    if rrule:
        lines.append(f"RRULE:{rrule}")
    
    lines.append(f"SUMMARY:{summary}")
    lines.append(f"DESCRIPTION:{description}")
    lines.append(f"LOCATION:{location}")
    
    if attendee_email:
        lines.append(f"ATTENDEE;CN=Roshni Ranka;ROLE=OPT-PARTICIPANT;PARTSTAT=NEEDS-ACTION:mailto:{attendee_email}")
    
    lines.append("TRANSP:OPAQUE")
    lines.append(f"PRIORITY:{priority}")
    lines.append("END:VEVENT")
    return "\n".join(lines)

events = [
    make_medication_event(
        uid="1",
        start_dt="20260609T080000",
        duration_min=15,
        summary="Ruhaan - FORACORT 100mcg Morning Dose",
        description="FORACORT 100mcg (Formoterol + Budesonide)\nDose: 2 puffs via ZEROSTAT VT Spacer\nGargle after use",
        rrule="FREQ=DAILY;INTERVAL=1;UNTIL=20260930T235959",
        attendee_email="rnr@draas.com"
    ),
]

ics_lines.append("\n".join(events))
ics_lines.append("END:VCALENDAR")
ics_content = "\n".join(ics_lines)
```

### Attendee Handling

- **Roshni Ranka (rnr@draas.com):** Add as ATTENDEE on every event so it appears on her calendar
- **Ruhaan (the patient):** For minors without email, mention in SUMMARY or DESCRIPTION — don't add as ATTENDEE
- Use `ROLE=OPT-PARTICIPANT` and `PARTSTAT=NEEDS-ACTION`

## Phase 4 — Deliver

Send the ICS file via `MEDIA:` path in the response. The file opens natively on iPhone Calendar, Google Calendar, and Outlook.

## Phase 5 — Medication Summary

Along with the ICS, present a clear text summary with: medication name, dose, schedule, duration, special instructions, pending treatments, and follow-up date.

## Pitfalls

- **OCR garbled dosing** — `"0"` chars like `2--0--2` are formatting artifacts, not zero doses
- **Minor patient without email** — Don't add as ATTENDEE; use title/description
- **RRULE termination** — Set end date matching follow-up interval, not indefinite
- **Time zone** — Always use `TZID=Asia/Kolkata` for IST
