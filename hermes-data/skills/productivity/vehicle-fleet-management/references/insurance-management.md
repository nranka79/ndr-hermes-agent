---
name: vehicle-insurance-management
description: "Manage DRAAS fleet vehicle insurance documents — upload policy PDFs to the shared Drive folder, update the master XLSX sheet across all 3 sheets (Summary, Detailed View, PDF Links Index), and create calendar reminder events with attendees and PDF links."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Vehicle Insurance Management (DRAAS Fleet)

Class-level skill for any session that needs to file, update, or track vehicle insurance policies for the DRAAS fleet. The fleet includes Toyota Innova Hycross, BMW X1, Volkswagen Vento, Jaguar XJ L, and others.

## When to load this skill

Triggers (any one):
- "upload/put/save this insurance to the folder"
- "update the Toyota/BMW/Jaguar/Vento insurance details into the Excel sheet"
- "calendar a task / reminder for insurance renewal"
- "vehicle insurance folder"
- "add the policy to the master sheet"

## Key locations

| Resource | ID / Link |
|---|---|
| **Vehicle Insurance Folder** (Drive) | `16R5MtZRoQrLM64Hpxejuij_wV08hfQ4E` |
| **Master XLSX** (`DRAAS_Vehicle_Insurance_Master.xlsx`) | `1tLZRVTyrQR1iu4aSNTawVuf4JkEjXgi5` (in Bharat's Drive) |
| **Drive API** | `tools.gws_auth.build_service("drive", "v3", telegram_id="sales1.blr")` |
| **Sheets for XLSX** | Use openpyxl, NOT Sheets API — it's an .xlsx file, not a Google Sheet |

## ⚠️ PITFALL #1 — XLSX is NOT a Google Sheet

The master file is an `.xlsx` file stored in Drive, NOT a Google Sheet. You cannot use the Sheets API on it. Use:

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import io

drive = build_service("drive", "v3", telegram_id="sales1.blr")

# Download
request = drive.files().get_media(fileId=MASTER_FILE_ID)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()

# Edit with openpyxl
fh.seek(0)
import openpyxl
wb = openpyxl.load_workbook(io.BytesIO(fh.read()))
# ... edit ...
wb.save("/tmp/updated.xlsx")

# Upload back
media = MediaFileUpload("/tmp/updated.xlsx",
    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    resumable=True)
drive.files().update(fileId=MASTER_FILE_ID, media_body=media).execute()
```

## Master sheet structure

The XLSX has **3 sheets**:

### Sheet 1: Summary
- Row 1: Title
- Row 2: Subtitle
- Row 3: Empty
- Row 4: Headers (Vehicle, Reg No., Insurer, Policy No., Period From, Period To, Premium (Rs), IDV (Rs), NCB, Fuel, Mfg Year, Policy PDF Link, URL)
- Row 5+: One row per vehicle

**Update approach:** Find the vehicle row by scanning column 9 (Make/Model, e.g. "TOYOTA / INNOVA..."), then update specific columns by index.

### Sheet 2: Detailed View
- Sectioned blocks per vehicle with headers: Policy Info, Vehicle, Coverage/Premium Breakup
- Each block has merged cells (B:D merged for value columns)
- Vehicles appear in order: BMW → Vento → Innova → Jaguar

**Update approach:** Scan rows for "Toyota Innova" in column A. Update label-value pairs by matching label text. The value cell is Column B (which is part of merged range B:D — writing to Column C or D will error).

### Sheet 3: PDF Links Index
- Table with columns: Vehicle, PDF File Name, Open PDF, Google Drive Link
- Each vehicle may have multiple rows (Current, Old, Previous)

**Update approach:** Find the Innova row by scanning column A for "Innova", update columns A-D.

## ⚠️ PITFALL #2 — openpyxl merged cells

The Detailed View sheet uses extensive merged cell ranges (B:D for values). Writing to any cell in a merged range OTHER than the top-left cell raises `AttributeError: 'MergedCell' object attribute 'value' is read-only`.

**Fix — always write to Column B (the top-left of merged range B:D):**
```python
# ✅ CORRECT — writes to the merged B:D range
ws2.cell(row=74, column=2, value='Tata AIG General Insurance')

# ❌ WRONG — will crash on merged cells
ws2.cell(row=74, column=3, value='something')  # MergedCell error!
```

If you need to split a merged cell to write multiple values (e.g. link in column D), unmerge first:
```python
# Unmerge before writing
for merged_range in list(ws2.merged_cells.ranges):
    if str(merged_range) == 'B72:D72':
        ws2.unmerge_cells(str(merged_range))
# Now you can write to B, C, D individually
ws2.cell(row=72, column=2, value='Label')
ws2.cell(row=72, column=3, value='URL')
```

## PDF naming convention

Follow the existing file naming in the folder:
```
Vehicle_RegNo_Insurer_Period.pdf
# Examples:
Innova HYCROSS_KA04NE1550_TataAIG_2025-26.pdf
Innova KA04NE1550.pdf (old policy)
Vento KA05MT9001.pdf
Tata_AIG_Motor_Policy_BMW x1
```

Don't replace old PDFs — add new ones alongside. The old files serve as history.

## Calendar reminder events

When the user asks to set renewal reminders:

```python
calendar = build_service("calendar", "v3", telegram_id="sales1.blr")

DESCRIPTION = f"""Insurance Renewal — Vehicle Name KA XX XX XXXX
Policy details...
📄 Policy PDF: {PDF_LINK}"""

attendees = [
    {"email": "rnr@draas.com"},
    {"email": "sales1.blr@draas.com"},
]

# Create all-day events on specific reminder dates
event = {
    "summary": "Insurance Renewal Reminder - Vehicle Name (Day 1)",
    "description": DESCRIPTION,
    "start": {"date": "2026-07-10", "timeZone": "Asia/Kolkata"},
    "end": {"date": "2026-07-10", "timeZone": "Asia/Kolkata"},
    "attendees": attendees,
    "reminders": {
        "useDefault": False,
        "overrides": [
            {"method": "popup", "minutes": 60},
            {"method": "popup", "minutes": 1440},
        ]
    },
}

created = calendar.events().insert(
    calendarId="primary",
    body=event,
    sendNotifications=True,
    sendUpdates="all"
).execute()
```

Always include `sendUpdates="all"` so both Bharat (sales1.blr) and Roshni (rnr@draas.com) receive email notifications.

## Common pitfalls

### openpyxl import path
`openpyxl` is NOT installed in the system Python or `/opt/data/.venv`. It lives at `/opt/hermes/.venv/lib/python3.13/site-packages/openpyxl`. When running from terminal, add this to PYTHONPATH:
```bash
PYTHONPATH=/opt/hermes:/opt/hermes/.venv/lib/python3.13/site-packages python3 script.py
```

### Download vs Export
`.xlsx` files are binary — use `drive.files().get_media()`, NOT `drive.files().export()`. Export only works on Google Docs Editors files (Docs, Sheets, Slides), not uploaded Office files. Export returns `"Export only supports Docs Editors files"`.

### Merged cell traps
Always check `ws.merged_cells.ranges` before writing to column C or D in the Detailed View sheet. The B:D merge is consistent across all vehicle blocks.

### Calendar attendees
Both `rnr@draas.com` (Roshni) and `sales1.blr@draas.com` (Bharat) are the standard attendees for DRAAS vehicle insurance reminders.

### Personal Drive access
The master XLSX and insurance folder are on **Bharat's personal Google Drive**, NOT the DRAAS workspace (`google-draas`). The `google-draas` service_name cannot access them (404/403). If you get a "File not found" or "permission" error when trying to reach the master XLSX or insurance folder, this is the reason. The user (Bharat H) needs to either:
- Share the specific files with `sales1.blr@draas.com` (Editor), OR
- Authorize his personal Gmail with Hermes via OAuth so you can use `service_name='google-gmail'`, OR
- Provide the data directly
