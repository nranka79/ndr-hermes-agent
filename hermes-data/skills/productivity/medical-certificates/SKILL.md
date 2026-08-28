---
name: medical-certificates
description: "Draft medical certificates and doctor's letters for patients — patient details, doctor details, medical background, purpose of certificate, signature block. For DRAAS users (Nishant/Roshini). Also covers medical records management: filing scanned prescriptions to Drive, parsing medication schedules, and creating ICS calendar events."
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [medical, certificate, doctor-letter, PDF, insurance, productivity, prescription, medication-schedule, ICS]
    related_skills: [ocr-and-documents, nano-pdf, google-workspace, web-appointment-booking]
---

# Medical Certificate Creation

Create medical certificates / doctor's letters for patients — formatted for the doctor to put on their letterhead, sign, and return.

## Trigger

When user shares WhatsApp conversation with their doctor and asks for a draft certificate/letter they can present to the doctor for signing.

## Required Information

Before drafting, collect:
1. **Patient name, DOB, residential address** — ask directly, or retrieve from DRAAS contracts/passport/ID documents
2. **Doctor's name and credentials** — from the conversation
3. **Medical details** — condition, medication, test results from the conversation
4. **Purpose of certificate** — insurance renewal, visa application, employer requirement, etc.
5. **Doctor's preferred signing format** — "To Whomsoever It May Concern" vs addressed letter

## Word Document Generation (preferred over PDF)

Nishant prefers `.docx` over `.pdf` for doctor drafts — he asks to share with the doctor who then puts it on their letterhead. **Always offer .docx first.**

Install `python-docx` if not available:
```bash
pip install python-docx -q
```

```python
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import datetime

doc = Document()
for section in doc.sections:
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1.2)
    section.right_margin = Inches(1.2)

# Title
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('TO WHOMSOEVER IT MAY CONCERN')
run.bold = True
run.font.size = Pt(14)

# Patient Details section
doc.add_paragraph()
patient_heading = doc.add_paragraph()
patient_heading.add_run('Patient Details:').bold = True
doc.add_paragraph('Name: [Patient Name]')
doc.add_paragraph('Date of Birth: [DOB]')
doc.add_paragraph('Residential Address: [Address]')
# ... continue building sections

output_path = '/data/hermes/cron/output/Medical_Certificate.docx'
doc.save(output_path)
```

**Delivery: ALWAYS send as Telegram file attachment first** — `MEDIA:/path/to/file.docx` via send_message. Do not upload to Drive unless Telegram delivery fails.

## PDF Generation with ReportLab

Use `reportlab` only when specifically requested, or as a fallback:

```bash
pip install reportlab -q
```

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors
import datetime
```

**Install reportlab if not available:**
```bash
pip install reportlab -q
```

## Standard Certificate Structure

1. **Header**: "TO WHOMSOEVER IT MAY CONCERN" (or addressed letter format)
2. **Date line**: date of certificate
3. **Patient Details**: Name, DOB, Residential Address
4. **Subject line**: Certificate purpose (e.g., "Medical Certificate – Medication Details for Insurance Purpose")
5. **Doctor identification**: "I, Dr. [Name] ([Degree]), am writing as attending physician of [Patient]"
6. **Medical Background**: Condition, medication, test results, family history context
7. **Purpose clarification**: Why the certificate is being issued
8. **Recommendation/Conclusion**: Statement clearing the patient or recommending the action
9. **Signature block**: Yours faithfully, Doctor name, degree, place, signature line, seal/stamp

## Delivery to User

**DOCX first, PDF on request only.** Nishant's explicit preference: ".docx file which I can share with him and he'll put it on his own letterhead."

1. Send as Telegram file attachment: `MEDIA:/data/hermes/cron/output/Medical_Certificate.docx`
2. If Telegram delivery fails → upload to Drive and share the link
3. Never default to Drive when Telegram is available

## Insurance Revival / Claim — Document Audit & Response Workflow

When the task involves an insurance policy revival or claim (not creating a new certificate), the workflow is fundamentally different:

### Phase 1 — Find the Latest Communication from the Insurer
- Search Gmail for the insurer's domain (e.g. `bos.bajajlife.com`, `icicipru.com`, `hdfclife.com`) with `in:inbox`
- Identify the latest **incoming** email — this is the authoritative request (not the user's own draft replies)
- Extract: policy number, underwriter requirements, contact person, date

### Phase 2 — Audit What Was Actually Sent
- **Do NOT trust the email body's claim of what was attached.** Always fetch the message with `format='full'` and inspect `payload.parts` for actual filenames and attachment data
- Common discrepancy: the email body says "Doctor's Prescription attached" but the actual attachment is a "Medical Certificate" (narrative note, not an Rx)
- Cross-reference attached filenames against what Drive has — the user may have attached an older or different version than intended

### Phase 3 — Locate Existing Documents on Drive
- Search Drive for: `NDR P` (prescriptions), `NDR Aarogyam` (Thyrocare), `NDR Lipid` (lipid profiles)
- Check the `NDR Medical Report Index` spreadsheet (xlsx uploaded to Drive) for a complete inventory
- For each document: confirm the file exists, get its Drive link, note its date and what it contains
- Determine the LATEST available document of each type (e.g. latest full body checkup, latest Rx)

### Phase 4 — Construct the Response Email
- **Include only the documents that were actually NOT sent before** (avoid sending duplicates)
- If the actual Rx was not sent but a doctor's note was, say: "Prescription to follow shortly" and send Rx in a separate email
- Request copies of reports from the insurer's diagnostic centre (TMT, blood tests) if the user doesn't have them
- Thread the reply to the latest incoming email from the insurer for continuity

### Phase 5 — Track Outstanding Items
- Note what's been sent (sent date, policy number)
- Note what's still pending (prescription update, new Rx from doctor, reports from insurer)
- Save to user memory for cross-session tracking if the case spans multiple conversations

### Common Pitfalls — Insurance Revival
- **"Prescription" vs "Doctor's Note":** An Rx has a drug name, dose, dosage schedule, and doctor's signature. A "To Whomsoever It May Concern" certificate is a narrative — insurers may not accept it as a prescription.
- **Statin dosage discrepancies:** The user's actual Rx may say 40mg (Rosuvastatin) while a doctor's note says 10mg (Atorvastatin) — these are different drugs and doses. Clarify with the doctor before sending.
- **Test reports from insurer's diagnostic centre:** Insurers send users to specific labs for TMT + blood tests. The user often doesn't get copies — explicitly request these in the response email.
- **Multiple user draft replies:** The user may have sent multiple follow-up emails (asking for clarification, providing partial docs) that haven't been responded to. Track the thread chronology so you know which email you're replying to.

---

# Medical Records Management — Prescription-to-Calendar Workflow

This workflow covers receiving a scanned prescription (Adobe Scan, photo, or PDF), extracting medication details, filing to the patient's Drive folder, and creating an ICS calendar with recurring medication events.

## Trigger

When the user uploads a medical document (new prescription, health check record, pharmacy invoice) from a doctor visit and asks to:
- "File this in the medical folder"
- "Create a medication schedule"
- "Add to calendar with reminders"

## Phase 1 — Identify the Document

### Extract Hospital Registration Number (IP/OP No, UHID, Patient No)

Hospital PDFs (OPD records, cash memos, prescriptions) always carry a **Patient Registration Number** — sometimes called IP No, OP No, UHID, or Patient No. This is essential for cross-referencing records.

**Where to find it across document types:**

| Document Type | Field Name | Example |
|---|---|---|
| OPD History & Findings | "Patient No" or top-right corner | `772843` |
| Prescription | "Pt. No." after hospital name | `772843` |
| Blood Test Report | "IP/OP No" in the patient info block | `772843` |
| Cash Memo / Bill | "Ptn. No" near patient name | `772843` |

**Extraction pattern:**

```python
import fitz  # pymupdf
doc = fitz.open(local_pdf_path)
text = ""
for page in doc:
    text += page.get_text()

# Search patterns
import re
patterns = [
    r'Patient\s*No[\.\:]*\s*(\d{4,10})',
    r'Pt\.?\s*No[\.\:]*\s*(\d{4,10})',
    r'Ptn\.?\s*No[\.\:]*\s*(\d{4,10})',
    r'IP\s*/\s*OP\s*No[\.\:]*\s*(\d{4,10})',
    r'UHID[\.\:]*\s*(\d{4,10})',
]
for p in patterns:
    match = re.search(p, text)
    if match:
        reg_no = match.group(1)
        break
```

**⚠️ The scanned page is authoritative.** The date from the PDF's form (hospital-printed date) is the real date of visit, not the Adobe Scan filename date which is the scan date and may differ.

Use `pdftotext` for Adobe Scan PDFs or `pytesseract` for images to extract text:

```python
import subprocess
result = subprocess.run(["pdftotext", pdf_path, "-"], capture_output=True, text=True, timeout=10)
text = result.stdout
```

Key fields to extract:
- **Patient name** — Master/Ms/Mr [Name]
- **Date** — DD/MM/YYYY format on the document
- **Doctor** — Full name + specialization
- **Hospital** — Name + location
- **Diagnosis** — e.g., BR ASTHMA PERSISTENT - EXACERBATION
- **Medications** — Each drug name, strength, dosing schedule, duration
- **Other instructions** — Follow-up interval, special notes

**⚠️ Doctor name transcription trap:** Voice transcriptions of Indian medical names are unreliable. The actual doctor name from the PDF/email is authoritative. (Session example: voice said "Dr. Vasundhara Rajya" → actual name from the PDF was **Dr. Vasunethra Kasargod**, MBBS MD Pulmonary Medicine, Reg. No. 87920, Manipal Hospital Millers Road.) Always read the actual document, not the voice transcription.

## Phase 2 — Rename per Convention

Format: `YYYYMMDD_Patient_Hospital_Doctor_Description.pdf`

Examples from this session:
- `20260609_Ruhaan_ManipalHospital_DrVasunethraKasargod_Prescription_AsthmaExacerbation.pdf`
- `20240529_Ruhaan_ManipalHospital_SkinPrickTest_SPT_HDM_Allergy.pdf`
- `20251223_Ruhaan_ManipalHospital_DrVasunethraKasargod_HealthCheckRecord_AsthmaReview.pdf`
- `20250904_Ruhaan_ManipalHospital_PharmacyInvoice_ForaprlRespules_Nebulization.pdf`

## Phase 3 — Parse Prescription Dosing Schedule

Indian prescriptions use a compact notation for dosing. The format is **three numbers separated by hyphens** representing **Morning - Afternoon - Night**:

| Notation | Meaning |
|----------|---------|
| **1-0-0** | 1 dose in the morning only |
| **0-0-1** | 1 dose at night only |
| **1-0-1** | 1 dose morning + 1 dose night |
| **1-1-1** | 3 times daily (morning + afternoon + night) |
| **1-1-1-1** | 4 times daily |
| **2P-0-2P** | 2 puffs morning + 2 puffs night (inhaler) |

Each medication also has:
- **Duration** — "5 days", "10 days", "15 days", or "DAILY TILL NEXT VISIT"
- **Timing** — "before food" / "after food"
- **Special instructions** — "gargle with water", "followed by..."

Example parsing from this session:
```
TAB PREDMET [METHYLPREDNISOLONE] 16MG 1-0-0 --- 5 DAYS --- AFTER FOOD
→ PREDMET 16mg: 1 tab morning, 5 days, after food

NEB FORAPRL 0.5MG [FORMOTEROL + BUDESONIDE] 1-0-1 --- 10 DAYS
→ FORAPRL nebulization: 1 respule morning + 1 respule night, 10 days

METER DOSE INHALER FORACORT 100MCG 2P-0-2P --- DAILY
→ FORACORT inhaler: 2 puffs morning + 2 puffs night, daily maintenance

MDI LEVOLIN 0.63 [LEVOSALBUTAMOL] 1-1-1-1 --- IF SEVERE BREATHLESSNESS
→ LEVOLIN rescue: 1 respule up to 4x daily, as needed only
```

## Phase 4 — Upload to Drive Medical Folder

**Step 0: Confirm destination folder with user first.**

Before uploading, tell the user which folder you've identified and share its link. Let them approve before executing the upload. They may want to confirm subfolder placement (root vs "Invoices and Bills") or correct the patient folder.

Example: *"I'll upload this to the **Ruhaan Medical** folder — link here. Shall I proceed?"*

Only execute the upload after the user confirms.

**Folder structure (DRAAS Family):**
```
Personal/
├── Ruhaan Medical/    (folder ID: 0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k)
└── Rivaan Medical/    (search under Personal/)
```

The `Personal` root folder is `0B1Oc8cSaJXPGYkQtYXJDQWVBUVE`.

Check for duplicates before uploading using MD5 or exact filename match:
```python
existing = drive.files().list(
    q=f"'{folder_id}' in parents and name='{filename}' and trashed=false",
    fields="files(id, name)"
).execute()
```

## Phase 5 — Add Notes to Existing PDF

Scanned medical PDFs (Adobe Scan) are image-based and cannot be directly edited. Use two methods:

1. **Drive file description** — Set the `description` field on the file
2. **Companion .txt file** — Upload alongside the PDF in the same folder, named with same date prefix + "Note" suffix

```python
# Example: companion note file
note_filename = "20251223_Ruhaan_ManipalHospital_DrVasunethraKasargod_Note_SLIT_Contact.txt"
with open(note_path, "w") as f:
    f.write("SLIT (Sublingual Immunotherapy) recommended by Dr. Vasunethra Kasargod.\n")
    f.write("Contact: Jagdish — +91 97425 32343\n")
```

## ⚠️ Critical Gate — Present Full Schedule Before Any Calendar Changes

When the user asks you to create, update, or replace medication calendar events, **you MUST present the complete proposed schedule to the user for confirmation BEFORE executing any API calls.** Do not assume you parsed the timings correctly — this is the #1 source of corrections.

### Confirmation presentation format

Show a structured table with:
- Each event's time, name, recurrence pattern, and duration
- Any temporary additional meds (short courses like Azhi/Lanzole) and their date range
- Which existing events will be deleted (if replacing an old schedule)
- Attendees list

**Wait for explicit confirmation before calling the Calendar API.** A "that looks right" or "correct" from the user is sufficient. Presenting and confirming in the same turn means showing the table, then asking "Proceed?" — do NOT create events without this step.

### Multi-round correction pattern

The user may correct timings across 2-3 rounds (e.g., "new pump is at 9 PM not 6 PM", "nasal spray is once at 6 PM, not twice"). Handle this by:
1. After each correction, present the **full updated schedule** — not just the changed line
2. Never assume you understood the full picture from a single correction
3. Once the user confirms "perfect" or equivalent, THEN execute

**Real example (Jun 2026 — Ruhaan new medication setup):**
- Round 1: User said "new pump at 6 PM, nasal spray morning+night" → I created wrong events
- Round 2: User corrected "new pump at 9 PM, nasal spray at 6 PM once daily, morning is pump not spray" → I recreated
- Round 3: User confirmed "perfect" after seeing the full corrected schedule
- Lesson: Presenting the full table on Round 1 would have saved 2 rounds of corrections.

## Direct Calendar API Creation (Alternative to ICS)

When the user wants medication events created directly on THEIR Google Calendar (not an ICS file to import), use the Calendar API instead of generating an ICS file. This has TWO advantages:
1. Attendees are added correctly (ICS imports silently strip ATTENDEE properties)
2. No manual import step for the user

### Short-Course Medication Events (Individual or Recurring)

For short antibiotic/steroid courses (e.g., Augmentin 625 BD × 3 days = 6 doses), you have two approaches:

**Option A — Individual events (best for visible reminders):**
Creates separate events, each with its own popup reminder. Better for short courses where the user sees each dose individually on the calendar.

```python
from tools.gws_auth import build_service
calendar = build_service("calendar", "v3")
tz = 'Asia/Kolkata'
attendees = [
    {'email': 'pebblyshark69@gmail.com', 'displayName': 'Ruhaan Ranka'},
    {'email': 'rnr@draas.com', 'displayName': 'Roshini Ranka'},
]

doses = [
    ('2026-06-21', 19, 'Night (Dose 1 of 6)'),
    ('2026-06-22', 7,  'Morning (Dose 2 of 6)'),
    ('2026-06-22', 19, 'Night (Dose 3 of 6)'),
    ('2026-06-23', 7,  'Morning (Dose 4 of 6)'),
    ('2026-06-23', 19, 'Night (Dose 5 of 6)'),
    ('2026-06-24', 7,  'Morning (Dose 6 of 6)'),
]

for date_str, hour, label in doses:
    event = {
        'summary': f'💊 Augmentin 625 - Ruhaan {label}',
        'description': 'Ruhaan — Augmentin 625 mg (after food)\n3-day course: morning 7am & night 7pm',
        'start': {'dateTime': f'{date_str}T{hour:02d}:00:00+05:30', 'timeZone': tz},
        'end': {'dateTime': f'{date_str}T{hour:02d}:15:00+05:30', 'timeZone': tz},
        'reminders': {'useDefault': False, 'overrides': [{'method': 'popup', 'minutes': 15}]},
        'attendees': attendees,
    }
    calendar.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
```

**Option B — Recurring events (more compact, one per dose-time):**
Creates 2 recurring events (one for morning, one for night) with COUNT=3.

```python
morning_event = calendar.events().insert(calendarId='primary', body={
    'summary': '💊 Ruhaan - Augmentin 625 (Morning)',
    'start': {'dateTime': '2026-06-22T07:00:00+05:30', 'timeZone': tz},
    'end': {'dateTime': '2026-06-22T07:15:00+05:30', 'timeZone': tz},
    'recurrence': ['RRULE:FREQ=DAILY;COUNT=3'],
    'attendees': attendees,
}).execute()
```

**When to use which:**
| Scenario | Approach |
|---|---|
| 2-3 day course (6 doses or fewer) | Option A — individual events, one per dose |
| 5-7 day course with BD/TID schedule | Option A or B — both work |
| 14+ day or indefinite course | Option B — recurring with COUNT or UNTIL |
| User says "remind us every time" | Option A — each dose is explicit |

For all cases: **always present the full schedule to the user for confirmation before creating.**

### Workflow

**Step 0 — Present full schedule for confirmation** (see ⚠️ Critical Gate above)

**Step 1 — Delete old medication events**
If replacing an existing schedule, identify all recurring medication events by searching the calendar and delete them:
```python
from tools.gws_auth import build_service
calendar = build_service("calendar", "v3", telegram_id="<telegram_id>")
from datetime import datetime, timedelta
import pytz

ist = pytz.timezone('Asia/Kolkata')
start = ist.localize(datetime(2025, 12, 1, 0, 0, 0))
end = ist.localize(datetime(2027, 1, 1, 0, 0, 0))

result = calendar.events().list(
    calendarId='primary',
    timeMin=start.isoformat(),
    timeMax=end.isoformat(),
    singleEvents=False,
    q='Ruhaan'  # or patient name
).execute()

# Filter for medication-specific events (look for 💊 or medication keywords)
for e in result.get('items', []):
    if '💊' in e.get('summary', '') or 'medication' in e.get('summary', '').lower():
        calendar.events().delete(calendarId='primary', eventId=e['id']).execute()
```

**Step 2 — Create recurring events with attendees**
```python
attendees = [
    {'email': 'pebblyshark69@gmail.com', 'displayName': 'Ruhaan Ranka'},
    {'email': 'rnr@draas.com', 'displayName': 'Roshini Ranka'},
]

today = datetime.now(ist).replace(hour=0, minute=0, second=0, microsecond=0)
end_date = today + timedelta(days=365)

event = calendar.events().insert(calendarId='primary', body={
    'summary': '💊 Ruhaan - Morning Pump (7 AM)',
    'description': 'Pump medication — one pump in the morning.\nDaily at 7:00 AM.\nPrescribed by Dr. Srikanta J T.',
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

**Key details for direct Calendar API:**
- Use `'dateTime'` with `+05:30` offset for IST times
- Duration: 5-15 minutes per event (just enough for the reminder)
- RRULE with `UNTIL` for the end date
- `attendees` array with both parent and child emails
- `reminders.overrides` for custom notification timing

**Step 3 — Create short-course additional events**
For temporary medications (e.g., Azhi 500 for 3 days, Lanzole Junior for 2 days):
```python
tomorrow = today + timedelta(days=1)
short_event = calendar.events().insert(calendarId='primary', body={
    'summary': '💊 Ruhaan - Azhi 500 (6 PM)',
    'description': 'Azithromycin 500mg — Day 4 & 5 of course.\nTake at 6:00 PM.\nJun 16 & 17 only.',
    'start': {
        'dateTime': f"{tomorrow.strftime('%Y-%m-%d')}T18:00:00+05:30",
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': f"{tomorrow.strftime('%Y-%m-%d')}T18:15:00+05:30",
        'timeZone': 'Asia/Kolkata',
    },
    'recurrence': [
        'RRULE:FREQ=DAILY;COUNT=2'  # Only 2 occurrences
    ],
    'attendees': attendees,
}).execute()
```

### When to use Direct Calendar API vs ICS

| Scenario | Use |
|----------|-----|
| User says "create calendar events" or "add to my calendar" | Direct Calendar API |
| User says "give me an ICS file to import" | ICS file generation |
| User has attendees they want invited | Direct Calendar API (ICS strips attendees) |
| User wants to share with someone who doesn't use Google Calendar | ICS file |

## Phase 6 — Create ICS Medication Calendar

When the user says "create calendar events" or "make an ICS file" for the medication schedule:

### Step 1 — Build the event list

Each medication becomes one or more events:
- **Daily maintenance meds** (e.g., FORACORT 2 puffs AM + PM) → recurring daily with RRULE
- **Short-course meds** (e.g., PREDMET 5 days) → recurring daily with UNTIL date
- **As-needed meds** (e.g., LEVOLIN SOS) → weekly reminder only
- **One-off first dose** (e.g., "take PREDMET now at 3:30 PM") → single event
- **Follow-up appointments** → single future event

### Step 2 — Handle user timing adjustments

The user may shift the first dose timing (e.g., "it's 3:30 PM now, give PREDMET and RABEPRAZOLE immediately today, then shift to morning from tomorrow"). Handle this with:
- **Today event**: single VEVENT at the adjusted time
- **Recurring events starting tomorrow**: RRULE with DTSTART = next day
- **Overlapping events at the same time**: create separate VEVENTs (they merge visually in the calendar but carry distinct descriptions)

### Step 3 — Construct VELEMENTs with rich descriptions

Each event must include in its DESCRIPTION:
- **Medication name, strength, dose** — e.g., "FORAPRL 0.5mg/2ml Respule (Budesonide + Formoterol)"
- **What it does** — e.g., "Budesonide = steroid to reduce airway inflammation. Formoterol = long-acting bronchodilator."
- **When and how to take** — with/without food, gargle after, etc.
- **Doctor who prescribed** — name, hospital, date

### Step 4 — Add Attendees

The user expects both family members as attendees. Add via ATTENDEE property:
```
ATTENDEE;CN=Roshni Ranka;ROLE=OPT-PARTICIPANT;PARTSTAT=NEEDS-ACTION:mailto:rnr@draas.com
```

Roshi's email: `rnr@draas.com`. For minor children (Ruhaan/Rivaan), note in the description — no separate email needed.

### Step 5 — Set timezone and recurrence

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

For recurring events:
```
RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20260618T235959
```

### Step 6 — Deliver

Send the ICS file via Telegram:
```
send_message(message="MEDIA:/data/hermes/cron/output/ruhaan_treatment_plan.ics", target="telegram")
```

**⚠️ If the user doesn't see the file:** The MEDIA: path in a message that also contains text may not render. Send the ICS as a **standalone message** with only the MEDIA: path.

### Complete ICS Structure for a Multi-Medication Schedule

```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Hermes//Patient Treatment Plan//EN
METHOD:PUBLISH
X-WR-CALNAME:Ruhaan - Treatment Plan
X-WR-TIMEZONE:Asia/Kolkata
BEGIN:VTIMEZONE
TZID:Asia/Kolkata
...
END:VTIMEZONE
BEGIN:VEVENT
DTSTART;TZID=Asia/Kolkata:20260610T080000
DTEND;TZID=Asia/Kolkata:20260610T081500
RRULE:FREQ=DAILY;INTERVAL=1;UNTIL=20260613T235959
SUMMARY:[ICON] Patient - Drug Name Dose (Timing)
DESCRIPTION:Full medication details...\nWhy this drug...\nInstructions...
ATTENDEE;CN=Roshni Ranka;...:mailto:rnr@draas.com
TRANSP:OPAQUE
PRIORITY:1
END:VEVENT
...more VEVENTs...
END:VCALENDAR
```

ICS files should use `\n` for line breaks in DESCRIPTION fields (not literal newlines within a line, which breaks the ICS format).

## Phase 7 — Pending Lab Result Follow-up Reminders

When a user uploads one test report and asks for reminders to follow up on **related pending results** (same visit, separate tests), use this pattern:

### Typical Scenario

- User uploads report A (e.g., blood test report from Jain Hospital)
- User asks: "Remind me today at 7PM to check with [contact person] if report B (IGG levels) has come"
- User also asks: "And remind me Monday 2PM to check again"

### Steps

1. **Upload report A** to the medical folder (with confirmation per Phase 4 Step 0)
2. **Create one-shot cron reminders** for each follow-up time:

   ```python
   cronjob(action='create',
       name='Patient - Pending Report Follow-up (Contact Person)',
       schedule='2026-06-13T13:30:00',  # 7PM IST = 13:30 UTC
       prompt='This is a reminder for [User]: Check with [Contact Person] whether [Patient]'s [specific test] report from [Hospital] has come. Follow up. Deliver to origin chat.')
   ```

### Timezone Handling (CRITICAL)

The cron `schedule` field interprets bare ISO timestamps as **UTC**. IST is UTC+5:30, so convert:

| IST Time | UTC Schedule Value |
|----------|-------------------|
| 7:00 PM | `2026-06-13T13:30:00` |
| 2:00 PM | `2026-06-15T08:30:00` |
| 9:00 AM | `2026-06-15T03:30:00` |

Formula: `UTC = IST - 5h30m`. Never pass IST timestamps directly without conversion.

### Reminder Chain Pattern

When the user wants **escalating follow-ups** (multiple reminders for the same pending item):

```
Reminder 1: Same day evening — "first check, mild urgency"
Reminder 2: Next business day afternoon — "escalated check, stronger urgency"
```

Create separate one-shot cron jobs for each. Keep names descriptive:
- `Ruhaan IGG report - check Ravi (today 7pm)`
- `Ruhaan IGG report - followup (Monday 2pm)`

## Creating Google Contacts from Medical Documents

When processing medical documents (prescriptions, consultation advice, invoices, reports), extract contact information for the doctor and their support staff and add them to the user's Google Contacts.

### When to Create Contacts

| Cue | Example |
|-----|---------|
| New doctor appears on a document | Dr. Deepak Haldipur, ENT at Trustwell |
| Coordinator/assistant phone circled on prescription | "Sridhar 9449784569 — Opns Coordinator" |
| Hospital/Clinic details on document header | Trustwell Hospital, No.5 J.C. Road, BLR |

### Extraction Sources

- **Prescription/Consultation Advice header**: Doctor name, specialization, clinic phone, hospital address
- **Doctor's stamp/signature area**: Registration number, degrees, phone
- **Margin notes or circled numbers**: Coordinator/assistant contact (common on Indian Rx pads)
- **Invoice footer**: Hospital GST, registered office address, emergency number

### Contact Data to Capture

```python
contact = {
    "names": [{
        "givenName": "Deepak",
        "familyName": "Haldipur",
        "honorificPrefix": "Dr.",
        "displayName": "Dr. Deepak Haldipur"
    }],
    "organizations": [{
        "name": "Trustwell Hospital",
        "title": "Consultant ENT Specialist",
        "department": "ENT Department"
    }],
    "phoneNumbers": [
        {"value": "+91 80 45666789", "type": "work"},
        {"value": "+91 80 45666851", "type": "work"},
    ],
    "emailAddresses": [{"value": "customercare@trustwellhospitals.com", "type": "work"}],
    "addresses": [{
        "streetAddress": "No.5, J.C. Road",
        "city": "Bengaluru",
        "region": "Karnataka", "postalCode": "560002", "country": "India",
        "type": "work"
    }],
    "urls": [{"value": "https://www.trustwellhospitals.com", "type": "work"}],
    "biographies": [{
        "value": "ENT specialist at Trustwell Hospital, Bangalore. Specialises in audiology, otosclerosis, and ear surgeries.",
        "contentType": "TEXT_PLAIN"
    }]
}
```

### Procedure

1. Extract from document (OCR or text extraction)
2. Create via People API:
   ```python
   people = build_service('people', 'v1')
   created = people.people().createContact(body=contact).execute()
   resource_name = created.get('resourceName')
   ```
3. Confirm to user with: `"👤 [Name] added to your Google Contacts — [phone] — [title] at [org]"`
4. For coordinators/assistants, set `"relations": [{"person": "Dr. X", "type": "assistant"}]`

### What NOT to Do

- Don't create contacts for hospitals that are already known (Trustwell, Manipal, etc.) unless it's a specific doctor you haven't saved before
- Don't overwrite existing contacts — People API creates new ones; deduplication is manual
- Don't guess emails — only include if explicitly on the document or hospital website
- For Sridhar-type contacts (operations coordinator), use a descriptive title: "Operations Coordinator — Dr. Deepak Haldipur (ENT)"

---

## KDR Medical Records — Drive Filing Workflow (DRAAS-specific, Nishant family)

**Nishant / KDR's family (Kanta Ranka) is a recurring medical-records user.** When Nishant shares scanned prescriptions, OPD notes, lab reports, or invoices for KDR or NDR:

### Drive Folder Structure (Nishant's personal Drive)

**Actual path** (verified 11 Jul 2026):

```
Personal/                              = 0B1Oc8cSaJXPGYkQtYXJDQWVBUVE
└── KDR Docs/                          = 1uzkxqMfHqBKu4GvEgaN8rHP8WJSRWbna
    └── KDR Medical/                   = 0B1Oc8cSaJXPGUUtVbTJHb0Y3V2s
        ├── Prescriptions, OPD notes, lab reports, advices, test results  (root)
        └── Invoices/                  = 1jNhEYEe1i2bEdcvQ2Lg9GG2XH4b9mpnu
            (bills, payment receipts, GST invoices)
```

- **KDR Docs (parent of KDR Medical)** = `1uzkxqMfHqBKu4GvEgaN8rHP8WJSRWbna`
- **KDR Medical (root for reports)** = `0B1Oc8cSaJXPGUUtVbTJHb0Y3V2s`
- **KDR Medical/Invoices** = `1jNhEYEe1i2bEdcvQ2Lg9GG2XH4b9mpnu`

**Naming pitfall:** the parent folder is **"KDR Docs"** (not just "KDR"). A Drive search for `name='KDR'` returns nothing — use `name='KDR Docs'` or traverse from Personal.

### Filename Convention

`<YYYYMMDD>_<Hospital/Clinic>_<Patient>_<DocType>_<Particulars>_<Amount>.pdf`

Examples (used in production, Jul 2026):
- `20260711_Manipal_MillersRoad_KantaRanka_Receipt_CTPulmonaryAngiogram_Rs16000.pdf`
- `20260711_Manipal_MillersRoad_KantaRanka_Receipt_BloodTests_Rs9840.pdf`
- `20260710_Manipal_MillersRoad_KantaRanka_OPDNotes_DrVasunethraKasargod.pdf`
- `20260709_KDR_AnaesthesiologyConsult_Invoice_Trustwell.pdf`

### Sharing + Accounting Rule

- **Invoices always shared with Eshwari + Roshni** (work @draas.com addresses — see messaging-drafts umbrella).
- Accounting entry for KDR medical expenses: **Dr KDR / Cr NDR** (always — NDR funds the family medical expenses).
- KDR pre-OT medical expenses (pulm clearance, blood work, anaesthetist consults) are **claimable from insurance** as pre-op costs. File with this intent — keep all bills together in Invoices/ with a chronological sub-folder if volume grows.
- Before filing, propose new names and target folder, **wait for explicit confirmation** — never auto-file. This is part of the standard `confirm-before-actions` rule for DRAAS file ops.

## Pre-Op Surgery Clearance Compilation (Pre-Surgical Report Package)

When coordinating an upcoming surgery (e.g., KDR stapedectomy Jul 2026) — Nishant often wants to:
1. Identify and file all completed pre-op workup reports
2. Compile a single message to the doctor's operations coordinator (insurance pre-auth, etc.)
3. Generate shareable Drive links for each report so the coordinator can download

### Workflow

**Step 1 — Identify the cohort of pre-op reports**
List files in the medical folder, filter to recent ones (typically last 7-14 days), then OCR/text-extract each to identify what it is. Common pre-op items for stapedectomy / ENT surgery:
- Audiological evaluation (PTA)
- 2D Echo (look for PASP if PH is in history — KDR has mild PH baseline)
- ECG
- Chest X-ray PA view
- Blood panel (Hb, platelet, PT/INR, aPTT, serum creatinine, sGOT, TSH, HbA1c, viral markers)
- Anaesthesia pre-op evaluation
- Specialist clearances (pulmonology, cardiology) — for any flagged concerns
- Additional workup (CT pulmonary angiogram, immunology panel) triggered by flags

**Step 2 — Classify each and rename if needed**

Recent uploads often have minor naming issues (extra space, missing extension, missing hospital name). Rename via:
```python
drive.files().update(fileId=fid, body={'name': new_name}).execute()
```
**Common fixes seen in production:**
- Stray space before `.pdf` (e.g., `20260711 KDR CT Pulm Angiogram .pdf`) → strip and add hospital name
- Missing `.pdf` extension (e.g., `20260710_KDR_Blood_test_Trustwell_Hospital`) → append
- Missing hospital segment → add `<Hospital>_<Patient>` segment

Convention: `YYYYMMDD_Patient_Hospital_Doctor_DocType_Particulars.pdf`
Examples (from KDR Jul 2026 pre-op cohort):
- `20260711_KDR_CTPulmonaryAngiogram_Manipal_MillersRoad.pdf`
- `20260710_KDR_BloodTest_Trustwell_Hospital.pdf`
- `20260710_Manipal_MillersRoad_KantaRanka_OPDNotes_DrVasunethraKasargod.pdf`
- `20260709_KDR_2DEcho_Report_Trustwell.pdf`
- `20260709_KDR_DrHaldipur_ConsultationAdvice_Trustwell.pdf`

**Step 3 — Generate shareable links for the coordinator message**

For each report that will be linked in the message, set "anyone with link: viewer" and fetch the webViewLink:
```python
for fid, name in key_reports:
    drive.permissions().create(
        fileId=fid,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()
    meta = drive.files().get(fileId=fid, fields='id,name,webViewLink').execute()
    print(meta['name'], meta['webViewLink'])
```
The returned `webViewLink` is what to paste into the message — anyone with the link can view, no sign-in required.

**Step 4 — Compile the coordinator message**

Key sections to include:
- **Header**: Patient name, UHID/Reg No, planned surgery, date, surgeon, hospital
- **Workup summary** in chronological order: which tests done, where, key findings
- **Flagged concerns and resolutions** (e.g., "echo showed PASP 54 → CTPA showed no PE, no PH → cleared")
- **Pending items** (e.g., "anaesthesia page-2 sign-off being confirmed")
- **Outstanding requests** (e.g., insurance/TPA desk number, pre-auth contact)
- **Link list** with one Drive link per key report

**Honesty gate:** if a key clearance (e.g., anaesthetist's final sign-off) is on a hand-written page that OCR can't reliably read, **say so explicitly** in the message. Do not invent a clearance. Suggest the user confirm with that doctor's office directly.

### Coordinator message template (extends the Surgery Coordination Message above)

The basic Surgery Coordination template asks for time / fasting / insurance number. The **pre-op clearance compilation** variant goes further — it documents completed workup. Add to the template:

```
PRE-OP WORKUP COMPLETED (since [date]):
- [Audiometry / ECG / 2D Echo / CXR / Bloods / Anaesthesia eval] — [date] at [hospital]
- [Specialist clearance X] — [date] at [hospital], key finding
- [Additional workup] triggered by [flag] — [date] at [hospital], key finding: [resolution]

PATIENT IS CLEARED FOR [procedure] UNDER [anaesthesia type] SUBJECT TO:
- [Pending item 1 — e.g., anaesthesia final sign-off]
- [Pending item 2 — e.g., insurance pre-auth confirmation]

REPORTS ATTACHED: [Drive link list]

REQUEST: please share the insurance/TPA desk contact so we can start pre-authorisation on Monday.
```

## OCR Pipeline for Scanned Medical PDFs (Hand-Written / Image-Based)

Many medical reports come back as scanned images (Adobe Scan, CamScanner, or hospital-archived image PDFs). When pymupdf text extraction returns very little text, fall back to rendering pages as PNG and running vision analysis.

### Detection

```python
import pymupdf
doc = pymupdf.open(pdf_path)
text = ''.join(p.get_text() for p in doc)
if len(text.strip()) < 50:  # Scanned image — no embedded text
    # Fall back to vision
```

### Render + vision pipeline

```python
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=180)
    pix.save(f'/tmp/preview_p{i+1}.png')
    # Then vision_analyze each PNG, ask specific questions per page
```

Use **dpi=180** as a good balance between file size and OCR legibility. Lower dpi (e.g., 100) loses hand-written text; higher dpi (e.g., 300) makes files huge without much accuracy gain.

### What works / what doesn't

- **Printed forms (typed or computer-generated)**: pymupdf text extraction usually succeeds. No need to render.
- **Hand-written clinical notes / pre-op eval page 2**: pymupdf returns empty. Render to PNG and use `vision_analyze` with a targeted question.
- **CT / MRI / X-ray films**: pymupdf returns empty (films are images, not text). For radiology reports, look for a separate "report" PDF in the same folder; for the films themselves, the radiologist's report is what matters clinically.
- **CamScanner "Scanned by CamScanner" stamp**: indicates image-based PDF — fall back to vision pipeline.
- **Hospital letterhead with printed text on the first page + a hand-written continuation on page 2**: mixed — extract page 1 text, render page 2 to PNG for vision.

### Targeted vision questions for medical reports

Don't ask "what's in this image?" — get specific. For an anaesthesia pre-op eval, ask:
- "Patient name, date, ASA grade, airway assessment, and the anaesthesiologist's verdict on fitness for surgery under GA? Quote the final recommendation verbatim."

For a CT Pulmonary Angiogram report, ask:
- "Patient name, date, clinical indication, full findings, and final impression. Does it show any PE, pulmonary hypertension, or contraindication to surgery under GA? Quote the impression verbatim."

Specific questions force the vision model to return the actual diagnostic text rather than a generic description.

## Voice-Transcription Pitfalls (Nishant)

Nishant dictates filenames + amounts by voice. Common garbles to catch before filing:
- "Kandaranka" → **Kanta Ranka** (KDR's wife, 68F, Embassy Habitat 1503, Bangalore-52)
- "Ishwari" / "Eshwari" → **Eshwari Chamundeshwari** (accounts, echamundeshwari@draas.com)
- "Diweli" → **Dr Sunil Dwivedi** (cardio, Manipal Millers Rd)
- "Adobe something something" → CamScanner / Adobe Scan PDFs — fall back to OCR-vision pipeline above
- Always confirm patient name + hospital + amount before writing to Drive.

## WhatsApp Medical Contact Messages

When the user needs to contact a healthcare provider (doctor, pharmacist, SLIT medication supplier, operation coordinator) about a patient's treatment:

### Message Template

```
Hi [Name],

Dr. [Doctor Full Name] ([Specialty], [Hospital]) has recommended that we get in touch with you regarding [treatment purpose].

Patient Details:
Name: Master/Ms/Mr [Patient Name]
Age: [Age] yrs
Diagnosis: [Diagnosis]
Consulting Doctor: Dr. [Doctor Name], [Hospital]

[Specific request details]

Please let us know the next steps.

Thanks,
Nishant Ranka
```

### Surgery Coordination Message Template

When coordinating a scheduled surgery/procedure with a doctor's operations coordinator:

```
Dear [Coordinator Name],

Dr. [Doctor Name] ([Hospital]) has confirmed [Patient Name]'s [surgery type] for this coming [Day] — [Date].

Patient details:
• Name: [Patient Name] (Mr./Mrs.)
• Reg No: [Hospital Registration Number]
• UHID: [Patient UHID]

We are at the hospital today ([Date]) completing all the prescribed tests and meeting Dr. [Doctor Name]. Happy to share all test reports if you need.

A few things we need from your end:
1. What time should we come in on [Day]?
2. Should [patient] come on an empty stomach?
3. Please share the insurance desk number so we can forward the insurance copy and they can begin the pre-authorisation process.

Kindly advise. Thank you!
```

The coordinator's number is typically circled on the prescription or consultation advice header, alongside the doctor's direct line.

### Delivery

Generate a WhatsApp link using `api.whatsapp.com/send` format (not wa.me — per user preference):
```python
import urllib.parse
phone = "91XXXXXXXXXX"  # No +, no spaces
msg = message.replace("&", "\uFF06")  # Full-width ampersand
encoded = urllib.parse.quote(msg, safe='')
link = f"https://api.whatsapp.com/send?phone={phone}&text={encoded}"
```

## Document Classification Workflow

When receiving scanned medical documents from a visit, classify each document and file accordingly:

### Classification Decision Tree

```
Is it a pharmacy/OP tax invoice with payment details?
  YES → Move to "Invoices and Bills" subfolder (or "Invoices" for NDR/KDR — see drive-folder-organization reference)
  NO  → Is it a laboratory requisition form?
          YES → Keep in root (it's a medical form/request)
          NO  → Is it a prescription (drug name + dosage + schedule)?
                  YES → Keep in root
                  NO  → Is it a test report (PFT, blood work, X-ray)?
                          YES → Keep in root
                          NO  → Is it a doctor's consultation note/advisory?
                                  YES → Keep in root
                                  NO  → Is it an OP bill / payment receipt?
                                          YES → Move to "Invoices" (NDR/KDR) or "Invoices and Bills" (others)
```

### Proactive Invoice Sweep (Move ALL Historical Invoices)

When creating an Invoices subfolder for a patient, do NOT just move the newly uploaded files — proactively identify and move ALL existing invoice/receipt/bill files from the medical root:

1. List all files in the medical folder root
2. Identify files with keywords: `Bill`, `Receipt`, `Invoice`, `OPBill`, `Payment`
3. Check for files with naming pattern `NDR/KDR Receipt` or `NDR/KDR Bill` (older naming conventions)
4. Move every identified file into the Invoices subfolder in one batch
5. Verify: list Invoices/ contents, confirm expected count matches

```python
drive.files().update(
    fileId=fid,
    addParents=invoices_folder_id,
    removeParents=medical_folder_id
).execute()
```

This avoids the user having to say "and check if any other invoices are there" later.

### Granting File Access to Team Members

For DRAAS medical invoice files, Nishant expects Eshwari (echamundeshwari@draas.com) and Roshni (rnr@draas.com) to have viewer access. Grant on every new batch of invoices:

```python
for fid, fname in invoice_files:
    for email in ['echamundeshwari@draas.com', 'rnr@draas.com']:
        drive.permissions().create(
            fileId=fid,
            body={'type': 'user', 'role': 'reader', 'emailAddress': email},
            sendNotificationEmail=False
        ).execute()
```

Always use `sendNotificationEmail=False` to avoid spamming them with individual file notifications.

### Invoice/Bill Identification (filename-based)

| Filename contains | Classification |
|---|---|
| `Invoice`, `Bill`, `OPBill`, `Receipt` | Move to Invoices (NDR/KDR: "Invoices"; others: "Invoices and Bills") |
| `Prescription`, `Rx` | Keep in root |
| `PFT`, `Pulmonary`, `Test`, `X-ray`, `Ultrasound` | Keep in root |
| `HealthCheck`, `FollowUp`, `FirstVisit`, `Consultation` | Keep in root |
| `LaboratoryRequisitionForm`, `LabReq`, `Requisition` | Keep in root (clinical, not financial) |

### ⚠️ Consultation Advice vs Lab Requisition Distinction

A document listing tests (Hb%, CBC, PT/INR, etc.) with a doctor's name and OP consultation header IS a **Consultation Advice** — not a "lab prescription" or "lab requisition." Label it with `_ConsultationAdvice_` in the filename. Only standalone lab forms (no doctor name, no consultation fee) are "Lab Requisitions."

## Folder Structure

```
[Patient] Medical/
├── Prescriptions, Reports, Advisories, Test Results, Lab Forms  (root)
└── Invoices/  (NDR, KDR) — or — Invoices and Bills/ (other family members)
```

**Note:** For Nishant (NDR) and Kanta Ranka (KDR), the subfolder is named simply **"Invoices"**. For others (Ruhaan, Rivaan, Roshni, etc.), use "Invoices and Bills" if the existing naming uses that.

## Updating the Medical Report Index Spreadsheet

Each family member has a **Medical Report Index** spreadsheet that serves as the master registry of all medical documents. After uploading a new document, add an entry here.

### Ruhaan's Medical Report Index

- **Spreadsheet ID:** `1E14iA3xDdoBaC0Sdlim6r6MipmSzNkKqFLaV2dXvHQU`
- **Columns:** Sl. No | TYPE | DATE | REPORT NAME | LINK | REPORT NAME (short)
- **Available types:** PRESCRIPTION / OPD, REPORT, RADIOLOGY REPORT, BILL, ADVISE, PRESCRIPTION, DENTAL PANO REPORT, etc.

```python
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4')
ss_id = '1E14iA3xDdoBaC0Sdlim6r6MipmSzNkKqFLaV2dXvHQU'

# Get next Sl No
res = sheets.spreadsheets().values().get(spreadsheetId=ss_id, range='A:A').execute()
nums = [int(r[0]) for r in res.get('values', [])[1:] if r and r[0].isdigit()]
next_no = max(nums) + 1 if nums else 1

# Add row
new_row = [
    str(next_no),
    'PRESCRIPTION / OPD',
    '21/06/2026',
    '20260621 Ruhaan Ranka BMJH Prescription Augmentin 625 - Splinter Removal',
    'https://drive.google.com/file/d/.../view',
    '20260621 Ruhaan BMJH Prescription Augmentin'
]
sheets.spreadsheets().values().append(
    spreadsheetId=ss_id, range='A:F',
    valueInputOption='USER_ENTERED',
    body={'values': [new_row]}
).execute()
```

### Ruhaan's Medical Notes & Corrections

- **Spreadsheet ID:** `1wNADzWJjdjkqgu4WT0_-uKq2kHBSo3rGuTMoPjpfMKE`
- **Columns:** Date | Type | Description | Source/Link
- This is a freeform log for clinical notes, clarifications, and corrections
- Use for narrative descriptions of events (injury description, clinical context, follow-up notes)

```python
note = [
    '21 Jun 2026',
    'Minor Surgery / Splinter Removal',
    'Stepped on a branch which pivoted and hit left knee. Small splinter embedded — could not remove at home. Taken to Bhagwan Mahaveer Jain Hospital where localized surgery under local anesthesia was performed to remove splinter. Prescribed Augmentin 625 mg BD × 3 days.',
    'Bhagwan Mahaveer Jain Hospital — Patient No 772843 — Photo: link'
]
sheets.spreadsheets().values().append(
    spreadsheetId=ss_id2, range='A:D',
    valueInputOption='USER_ENTERED',
    body={'values': [note]}
).execute()
```

| Patient / Resource | Folder / Sheet | ID |
|---------|------------|-----------|
| Ruhaan Ranka | Ruhaan Medical (folder) | `0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k` |
| Ruhaan Ranka | Medical Report Index (sheet) | `1E14iA3xDdoBaC0Sdlim6r6MipmSzNkKqFLaV2dXvHQU` |
| Ruhaan Ranka | Medical Notes & Corrections (sheet) | `1wNADzWJjdjkqgu4WT0_-uKq2kHBSo3rGuTMoPjpfMKE` — freeform narrative log for full incident descriptions |
| Rivaan Ranka | Rivaan Medical (folder) | (search under Personal/) |
| Personal root | Personal | `0B1Oc8cSaJXPGYkQtYXJDQWVBUVE` |

## Minor Surgery / Injury Documentation

When a patient has a minor surgical procedure (e.g., splinter removal under local anaesthesia), document it across BOTH the Medical Report Index AND the Medical Notes & Corrections sheet with cross-referenced links.

**Workflow:**
1. **Classify each document:** Photo and OPD history → keep in medical root folder. Prescription → keep in root. Cash memo/bill → move to "Invoices and Bills" subfolder.
2. **Add to Medical Report Index:** One row per document with TYPE = PRESCRIPTION/OPD or BILL.
3. **Add narrative entry to Medical Notes & Corrections:** Full description of incident + ALL relevant Drive links (photo, prescription, bill, OPD record) in column D.
4. **Cross-reference:** The Notes & Corrections column D should contain all links from the visit, making it a single-entry lookup for the full incident. |

## Known Hospitals & Naming Conventions

| Hospital | Short code | Address | Notes |
|----------|-----------|---------|-------|
| Manipal Hospital, Millers Road | `ManipalHospital` | Millers Road, Vasanthnagar, BLR | Dr. Vasunethra Kasargod, Dr. Satish KS |
| Manipal Hospital, Yelahanka | `ManipalHospitalYelahanka` | Sy No.23/3, Next to Brigade Honda, Venkatala Village, Yelahanka Hobli, BLR-64 | Dr. Srikanta J T — Paediatric Pulmonology (MBBS, DCH, DNB, Fellowship Ped Pulmonology & Sleep Med - Singapore). Phone: 080 2121 2121 |
| Manipal Hospital, Old Airport Road | `ManipalHospital` | HAL Old Airport Road, Kodihalli, BLR | Dr. Srikanta J T (pulmonologist) |
| Bhagwan Mahaveer Jain Hospital (BMJ) | `BMJHospital` | #17 Millers Road, Vasanthnagar, BLR-52 | Dr. Bharat Reddy (pulmonologist), Dr. Nishant Hiremath. Central Pharmacy. GSTIN: 29AAATBO895L1ZC |
| Aster Hospital | `AsterHospital` | (various locations) | Dr. Priyanka (pulmonologist), Dr. Kavitha Bhat |
| Shishu Children's Hospital | `ShishuHospital` | #30, 1st Main Rd, Near Banaswadi PS, BLR-43 | Dr. Y. Bharath Reddy (pediatric pulmonologist). Phone: 080-4247-2424 |

## Naming Pattern for Scanned Documents

```
YYYYMMDD_Patient_ShortCode_Description.pdf
```

Examples:
- `20260612_Ruhaan_BMJHospital_LaboratoryRequisitionForm.pdf`
- `20260612_Ruhaan_BMJHospital_Prescription.pdf`
- `20260612_Ruhaan_BMJHospital_PharmacyInvoice_Duolin_TusqDX_Predmet.pdf`
- `20260717_Ruhaan_ManipalHospital_PFT_DrSatishKS_PulmonaryFunction.pdf`
- `20261223_Ruhaan_ManipalHospital_HealthCheckRecord_AsthmaReview.pdf`
- `20260904_Ruhaan_ManipalHospital_PharmacyInvoice_ForaprlRespules_Nebulization.pdf`
- `20260615_Ruhaan_ManipalHospitalYelahanka_OPDRecord_DrSrikantaJT.pdf`

## Medical Records Compilation (Multi-Report Archive PDF)

For compiling ALL medical records for one patient into a single PDF with summary, timeline, index, and full reports in chronological order — see `references/medical-records-compilation-workflow.md`.

**Key rule: SEPARATE PDFs per person.** Never combine multiple patients into one file.

## Ruhaan Current Medication Regime (as of 15 Jun 2026 — Dr. Srikanta JT)

| Medication | Dose | Frequency | Purpose |
|---|---|---|---|
| **Niveoli 120 mcg** (fine-particle ICS/LABA) | 1 puff | BD (morning + evening) | Replaced Foracort 100. Fine-particle targets small airways. |
| **Fluticone FT Nasal Spray** (Fluticasone) | 1 spray each nostril | 6 PM daily — lifelong | "If the nose is not settled, the asthma cannot be settled." Controls viral rhinitis. |
| **Levolin 50 mcg** (Levosalbutamol) | 3 puffs | Every 4th hourly × 3-5d + SOS | Rescue bronchodilator |
| **Tab Allegra 120 mg** (Fexofenadine) | 1 tab | OD × 3-5d if cold present | Antihistamine |
| **AZEE 500 mg** (Azithromycin — anti-inflammatory) | 1 tab | 1-0-0 × 5d at first sign of viral-triggered cough not settling with Levolin | Anti-neutrophilic effect. NOT for antibiotic effect. |

## Ruhaan Clinical History (15 Jun 2026 — Dr. Srikanta JT)

**Diagnosis:** Bronchial Asthma — Persistent — with Neutrophilic Phenotype (Viral-Triggered)
- T2-low, non-eosinophilic asthma
- Triggered by viral respiratory infections, distinct from baseline eosinophilic asthma
- Steroid-resistant exacerbations respond to azithromycin (anti-inflammatory effect)
- Small airway disease confirmed: persistently low FEF25-75 (50-76% pred) across 6 PFTs over 2 years
- Allergic rhinitis is a critical comorbidity: "If the nose is not settled, the asthma cannot be settled" — nasal spray (Fluticone FT) is lifelong

**AZEE Protocol activation criteria:**
1. Cough persists despite Levolin rescue
2. Cough not settling with Niveoli maintenance pump
3. Known/suspected viral respiratory infection
4. Cough follows daytime-only, sleep-free pattern
Do not wait. Early initiation = shorter episode.

## Gmail Search for Medical Records

Manipal Hospital Millers Road sends from `noreply@manipalhospitals.com` with standardized subject lines:
- "Pharmacy Tax Invoice" — medication purchase receipts
- "OP-Bill Receipt" — consultation bills

Search pattern:
```python
q = '"Pharmacy Tax Invoice" Ruhaan after:2025/9/3 before:2025/9/5'
q2 = '"OP-Bill Receipt" Ruhaan after:2025/9/3 before:2025/9/5'
```

Download attachments via:
```python
att = gmail.users().messages().attachments().get(
    userId="me", messageId=msg_id, id=attachment_id
).execute()
data = base64.urlsafe_b64decode(att["data"])
```

## Family Calendar Attendee Email Reference

When creating calendar events for DRAAS family members' medical treatments, use these confirmed emails:

| Person | Email | Notes |
|--------|-------|-------|
| Roshni Ranka (wife) | rnr@draas.com | Primary caregiver — always add |
| Ruhaan Ranka (elder son) | pebblyshark69@gmail.com | Minor — added as optional attendee |
| Rivaan Ranka (younger son) | rankarivaan@gmail.com | Minor — added as optional attendee |

## ICS → Calendar Attendee Limitation (CRITICAL)

**Google Calendar silently strips ATTENDEE properties from .ics file imports.** When a user imports an ICS file (even one with valid `ATTENDEE;CN=Roshni Ranka;ROLE=OPT-PARTICIPANT;PARTSTAT=NEEDS-ACTION:mailto:rnr@draas.com` lines), the attendees do NOT get added to the events. The calendar creates the events with the titles, descriptions, and recurrence, but the attendee list is empty.

**This is NOT a bug in the ICS format** — it's a deliberate Google Calendar design choice to prevent unsolicited invites via file import. The behavior is consistent across Google Calendar web, Android, and iOS.

### Workflow for attendee management

When the user wants calendar events WITH attendees, DO NOT rely on ATTENDEE in the ICS. Instead use a **two-phase approach**:

**Phase 1: Generate and deliver the ICS file** (for the events, descriptions, and recurrence):
```python
send_message(message="MEDIA:/path/to/file.ics", target="telegram")
```
The user imports this to create all events. Attendees will be empty.

**Phase 2: Add attendees via Calendar API after user confirms events are created**:
```python
from tools.gws_auth import build_service
calendar = build_service("calendar", "v3")

# Search for events by title keyword (e.g., "Ruhaan")
from datetime import datetime, timezone, timedelta
now = datetime.now(timezone.utc)
end = now + timedelta(days=120)
events = calendar.events().list(
    calendarId="primary",
    timeMin=now.isoformat(),
    timeMax=end.isoformat(),
    q="Ruhaan",
    singleEvents=True,
    orderBy="startTime"
).execute()

# Get unique recurring event base IDs to avoid updating every instance
seen_base_ids = set()
for e in events.get("items", []):
    eid = e["id"]
    base_id = eid.rsplit("_", 1)[0] if "_" in eid else eid
    if base_id not in seen_base_ids:
        seen_base_ids.add(base_id)
        # Update the recurring event series
        existing = calendar.events().get(calendarId="primary", eventId=eid).execute()
        existing["attendees"] = [
            {"email": "rnr@draas.com", "displayName": "Roshni Ranka", "responseStatus": "needsAction"},
            {"email": "pebblyshark69@gmail.com", "displayName": "Ruhaan Ranka", "responseStatus": "needsAction"},
        ]
        calendar.events().update(
            calendarId="primary",
            eventId=eid,
            body=existing,
            sendUpdates="all"
        ).execute()
```

**⚠️ PITFALL: Updating one instance of a recurring series does NOT affect all instances.** Recurring events created from ICS import have a base ID (e.g., `ab12345`) that's shared across all instances. When you `events().get()` on the base ID, you get the series master — updating it propagates to all future instances. However, each instance may have its own suffix (e.g., `_20260610T023000Z`). To update the entire series, find the base ID (before the `_` suffix) and update THAT event. The `sendUpdates='all'` will send email notifications to all attendees.

**If you can't find a clean series master ID**, update each instance individually by iterating over them. This is slower but guaranteed to work.

### When to use Phase 2 vs. just Phase 1

| User request | Use | 
|---|---|
| "Give me an ICS file to add to my calendar" | Phase 1 only — they'll see events, no attendees | 
| "Create calendar events with Roshni as attendee" | Phase 1 + Phase 2 — deliver ICS first, then API-update attendees |
| "Add my wife as attendee to the events already on my calendar" | Phase 2 only — search and update existing events |

## First-Dose Timing Adjustment Pattern

When a medication course starts mid-day (not at the standard morning dose time), handle the first day differently from the rest:

```python
# Today (e.g., 3:30 PM): first dose NOW
first_dose = {
    "DTSTART;TZID=Asia/Kolkata": "20260609T153000",
    "SUMMARY": "First Dose NOW - PREDMET + RABEPRAZOLE",
    # ... One-time event, no RRULE
}

# Tomorrow onwards: shift to standard 8 AM timing
daily_doses = {
    "DTSTART;TZID=Asia/Kolkata": "20260610T080000",
    "RRULE": "FREQ=DAILY;INTERVAL=1;UNTIL=20260613T235959",
    "SUMMARY": "PREDMET 16mg (Morning)",
    # ...
}
```

Always create separate VEVENTs for the first-day ad-hoc timing and the regular recurring schedule starting the next day.

## Prescription Dosing Notation Reference

Indian prescriptions use a compact three-number format: **Morning - Afternoon - Night**.

| Notation | Meaning | 
|----------|---------|
| **1-0-0** | 1 dose in the morning only |
| **0-0-1** | 1 dose at night only |
| **0-0-1** | 1 dose at night only |
| **1-0-1** | 1 dose morning + 1 dose night |
| **1-1-1** | 3 times daily (morning + afternoon + night) |
| **1-1-1-1** | Up to 4 times daily (as needed rescue) |
| **2P-0-2P** | 2 puffs morning + 2 puffs night (inhaler) |

Duration suffixes: `---5 DAYS`, `---10 DAYS`, `---15 DAYS`, or `---DAILY TILL NEXT VISIT`.

Timing suffixes: `AFTER FOOD`, `BEFORE FOOD`, `B/F` (before food).

Special instructions: `FOLLOWED BY GARGLES WITH WATER` (for inhaled steroids).

- **Duplicate uploads**: The user may upload the same file twice with different temp names (e.g., two "Adobe Scan 09 Jun 2026 (2).pdf" with different hash prefixes). Compare MD5 checksums before processing.
- **Wrong file for "today's prescription"**: The user may upload a document from a prior visit (e.g., Dec 2025) and call it "today's." OCR the date from the document and confirm if it differs from what the user expects.
- **Scanner-date confusion**: Adobe Scan files are named by scan date, not document date. The actual document date is inside the PDF (from the hospital's form), not the filename.
- **Circle-marked numbers on prescriptions**: Indian prescriptions often have coordinator/assistant phone numbers circled or underlined in the header margin. These are key contacts (operations coordinator, discharge planner) — extract and save them as Google Contacts.
- **Missing medications in document**: The user may refer to medications from a prior visit (e.g., Sep 2025 invoice) that aren't in the current prescription. Present only what the current document says, then ask if there are additional meds from elsewhere.
- **Voice-to-text name corruption**: Indian doctor names frequently get mis-transcribed by voice. Always read the PDF to confirm (e.g., "Vasundhara Rajya" → "Vasunethra Kasargod"; "Anbarasan" → "Anbarasan M").
- **Calendar file visibility**: ICS files sent via MEDIA: in a multi-line message may not render as a download link. Send as a standalone message with only the MEDIA: path.

## Pitfalls

- **Wrong doctor name**: Always confirm from the WhatsApp conversation — do not guess spelling (e.g., "Das" vs "Tass")
- **Incomplete patient info**: If user doesn't provide DOB/address, ask before drafting — don't substitute from memory
- **Don't OCR documents the user already explained**: When the user uploads a document AND verbally describes what it is (e.g., "this is the structural stability certificate signed by Prashant Giri"), take their description at face value. Do not waste time running OCR/vision on the document to confirm what they've already told you. Proceed directly to naming, filing, and confirming with the user.
- **Drive upload failures**: For DRAAS Google Workspace, do NOT use a service account. Use the per-user OAuth token via `build_service(api, version, service_name='google-draas')` (or `google-ahfl` / `google-gmail`). If a vault lookup fails, call `gws_resolve_account` to find the correct service_name — never guess or hardcode a service name.
- **MEDIA path not rendering**: If a file sent via MEDIA: in a Telegram message doesn't appear, resend as a standalone message with only the MEDIA: path and nothing else
- **ICS file delivery**: The user opens the .ics file from Telegram chat on their phone, which prompts their default calendar app to import all events. Ensure the file is valid ICS format (starts with `BEGIN:VCALENDAR`, ends with `END:VCALENDAR`).
- **Indian-numbering ₹-unit misread (CRITICAL — confirmed KDR insurance, Jul 2026)**: Indian financial documents use lakh/crore grouping with comma separators every two digits from the right (Western uses three). Always parse the full string and convert to a human-readable ₹ figure with the unit BEFORE quoting it to the user or writing it into a message. The number `1,50,00,000` means **₹1.5 Crore (15 million / 1,50,00,000)**, NOT ₹15 lakh and NOT ₹15,000,000 Western. The number `12,00,000` is ₹12 lakh. The number `2,09,731` is ₹2.09 lakh (≈₹2.1 lakh), NOT ₹20.9 lakh. The number `5,000` could be either ₹5,000 or ₹50,000 depending on context (no extra grouping digit). See `references/indian-currency-number-format.md` for the full conversion table, common insurance/premium patterns, and a verification routine to run before sending any ₹ figure to the user. **Real failure case (KDR Royal Sundaram renewal, 30 Mar 2026): I quoted "₹15,00,000 Sum Insured" — the user immediately caught it: actual was ₹1,50,00,000 (₹1.5 Cr). I had read `1,50,00,000` as `15,00,000` by mentally dropping one comma. Always do the unit check.**

## Reference Files

- `references/cloud-document-extraction-from-browser.md` — Extract documents from cloud viewers (Adobe Scan, etc.) when direct download is blocked — canvas → chunked data URL → img2pdf → Drive upload. Use when the user shares an Adobe Scan link instead of the PDF file itself.
- `references/medical-certificate-template.md` — Full template with all sections, "To Whomsoever It May Concern" and addressed letter formats, quick-fill variable table, Indian insurance certificate special notes
| `references/comprehensive-medical-brief.md` | Create an A4-printable HTML medical brief for specialist consultations — chronological history, all lab data with colour-coded status, document links, and page breaks. Trigger: user is preparing for a doctor visit and needs everything in one printable/phone-openable file. |
| `references/verbal-prescription-phone-consultation.md` | Record a phone consultation prescription on Drive: visiting card OCR, pharmacy invoice extraction, verbal prescription document creation, doctor contact saved to Google Contacts + DRAAS sheet. Covers the back-to-back neb protocol (Levolin 0.63 + Budecort 0.5) for Ruhaan asthma exacerbation. |
| `references/multi-prescription-synthesis-workflow.md` | Synthesize multiple sequential prescriptions (3+ doctors over 3-5 days) into a single unified schedule. Later prescriptions override earlier ones — this reference covers the override chain logic, conflict resolution across prescribers (ER vs specialist vs telephonic), and a structured timeline output format. |
| `references/multi-prescription-synthesis-workflow.md` | Synthesize multiple sequential prescriptions (3+ doctors over 3-5 days) into a single unified schedule. Later prescriptions override earlier ones — this reference covers the override chain logic, conflict resolution across prescribers (ER vs specialist vs telephonic), and a structured timeline output format. |
| `references/missing-medical-report-cross-document-search.md` | Missing test/scan report — search Drive broadly, find references in clinical notes and aggregated medical summaries. Trigger: user asks about a specific past test that doesn't have its own PDF in the medical folder. |
| `references/medical-records-data-audit.md` | Cross-document data point audit — search all existing medical reports (blood work, health checks, consultation notes, invoices) for a specific field/value (blood group, HbA1c, vaccination date, etc.) with gap analysis and actionable next steps. Trigger: user asks "check all reports for X" across a patient's medical folder. |
| `references/medical-journey-narrative.md` | Create a narrative medical journey Google Doc for family awareness (e.g. "Note for Kanpur Babaji"). Section 1: Latest condition. Section 2: Full medical timeline. Includes personal/social context and photo link. Trigger: user needs a comprehensive health summary for a family member, not a specialist. |
| `references/keytruda-pap-delivery-monitoring.md` | Keytruda PAP drug delivery / OTP monitoring + prescription resubmission — check the caregiver's secondary email (ndr@ahfl.in) for delivery updates from Medybiz Pharma (kiranpapv3@medybizpharma.com), read thread status, report silence gaps, recommend follow-up. Also covers drafting resubmission email with polite-but-firm tone when prescription is rejected (name not visible, etc.), attaching cleaner scan to Gmail draft in ahfl.in account. Trigger: user says "check for emails about Keytruda delivery/OTP for Charitra/Chinky", drug delivery is expected today, or a cleaner prescription needs to be submitted. |
| `references/indian-currency-number-format.md` | Indian lakh/crore number convention and the comma-every-2-digits rule. Conversion table, sanity-check anchors for insurance policy figures (premium, SI, CB), and a pre-send verification routine. Use whenever extracting or quoting any ₹ figure from an Indian financial document (insurance policies, hospital bills, sale deeds, bank statements). |
| `references/new-medication-research-from-prescription.md` | Identifying a new medication (e.g., TKI) from user-described clues (dose, side effects, doctor's description) when OCR fails on handwritten prescriptions. Covers Axitinib identification matrix, PubMed/browser research workflow for Pembro+TKI combinations, and medical dossier update. Includes key published evidence for Pembro+Axitinib in ASPS (Wilky et al. Lancet Oncol 2019). |
| `references/treatment-monitoring-protocol.md` | Creating a patient-facing treatment monitoring protocol as a rich HTML email — test schedule with frequency + justifications, detailed at-home symptom checklist with what-to-look-for guidance, CSS formatting for Gmail, and draft creation workflow. Trigger: user wants a "list of tests with reasons" and "symptoms to watch" for someone on a drug regimen. |

---

# Genetic Variant Monitoring (ClinVar)

For patients with identified genetic variants that may be reclassified over time (particularly relevant for Ruhaan's GATA2 variant).

## Pattern: Periodic Reclassification Check

Set up TWO things in parallel:

### 1. Calendar Reminder (every 6 months)
```python
cal = build_service('calendar', 'v3')
event = {
    'summary': '🔬 Ruhaan - Check GATA2 ClinVar Reclassification (VCV000858280)',
    'description': '''Check ClinVar entry VCV000858280 for GATA2 variant reclassification.
Gene: GATA2 (3q21.3)
Current Status: Conflicting classifications of pathogenicity
Last Evaluated: 10 Nov 2025
ClinVar URL: https://www.ncbi.nlm.nih.gov/clinvar/variation/858280/
API: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=clinvar&id=858280&retmode=json''',
    'recurrence': ['RRULE:FREQ=MONTHLY;INTERVAL=6;BYMONTHDAY=1;BYHOUR=9;BYMINUTE=0'],
    'reminders': {
        'overrides': [
            {'method': 'email', 'minutes': 1440},
            {'method': 'popup', 'minutes': 30},
        ]
    },
    'attendees': [{'email': 'ndr@draas.com'}, {'email': 'rnr@draas.com'}]
}
cal.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
```

### 2. Cron Job (same schedule) — Automated API check
Create a cron job (via `cronjob(action='create')`) that:
- Fetches the ClinVar entry via NCBI E-utils API
- Compares current classification + SCV count against last known status
- Reports to the origin chat if anything changed
- Stays silent if unchanged (no news = good news)

```python
# Cron prompt template
prompt = '''Check ClinVar entry VCV######## for the [GENE] variant ([VARIANT NAME]) to see if its classification has changed.
Steps:
1. Fetch: curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=clinvar&id=VCV_ID&retmode=json"
2. Extract germline_classification.description and last_evaluated date
3. Count SCV submissions
4. Compare with last known status
If changed, flag as ACTION REQUIRED. Include URL: https://www.ncbi.nlm.nih.gov/clinvar/variation/VCV_ID/'''
```

### ClinVar Entry for Ruhaan (VCV000858280)
- **Gene:** GATA2 (3q21.3)
- **Variant:** NM_032638.5(GATA2):c.331CAC[2] (p.His113del) — Microsatellite, inframe deletion
- **Current:** Conflicting classifications of pathogenicity (last evaluated 2025/11/10)
- **Associated:** Deafness-lymphedema-leukemia syndrome (OMIM 614038), Monocytopenia with susceptibility to infections (OMIM 614172)
- **SCV submissions:** 3 (SCV002069215, SCV005124143, SCV001229003)
- **ClinVar URL:** https://www.ncbi.nlm.nih.gov/clinvar/variation/858280/
- **API:** https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=clinvar&id=858280&retmode=json

---

# Periodic Condition Review Reminder Pattern

For setting reminders about specific medical follow-up actions (e.g., "Review Ruhaan Asthma Condition" with research-backed action items).

### Pattern
```python
# 1. Create cron job for the reminder date
cronjob(action='create',
    name='Review Patient Condition',
    schedule='2026-06-30T03:30:00',  # 9 AM IST = 3:30 UTC
    prompt='''Send the following reminder to Nishant:
Title: 🔬 Review Ruhaan Asthma Condition

[Full research-backed action items here...]

Deliver to origin chat.''')

# 2. Create calendar event with same title
cal.events().insert(calendarId='primary', body={
    'summary': '🔬 Review Ruhaan Asthma Condition',
    'description': '''Action items with clinical context...
1. IOS testing: Push for Impulse Oscillometry at next PFT
2. Extrafine ICS: Discuss Fostair switch if small airway disease persists''',
    'start': {'dateTime': '2026-06-30T09:00:00', 'timeZone': 'Asia/Kolkata'},
    ...
}).execute()
```

Use both parallel: cron job delivers the reminder as a Telegram message here, calendar event provides the structured description for reference.

## Related Skills

- `web-appointment-booking` — Book doctor appointments on Practo/hospital portals (precedes medical records filing)
- `ocr-and-documents` — PDF extraction and medical document filing to Drive (naming conventions, folder structure, crop-upload pipeline)
- `nano-pdf` — Edit PDF text if doctor returns signed certificate with errors
- `google-workspace` — For Drive upload when Telegram fails
