# Bharat Hawaldar — Workflow Preferences (Document Editing)

Preferences specific to working with Bharat Hawaldar (sales1.blr@draas.com) on DRAAS document editing tasks.

## Always Duplicate Before Editing

**Rule:** Never modify an original document. Always create a copy via the Drive API first, then edit the copy.

Bharat explicitly stated: *"Create a duplicate of it and then try because I don't want you to do anything on the original."*

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

copy_meta = {'name': f'{original_name} - WITH TABLE'}  # append descriptive suffix
copied = drive.files().copy(fileId=ORIGINAL_ID, body=copy_meta, fields='id, name, webViewLink').execute()
new_id = copied['id']
```

**Suffix convention:** Append a descriptive suffix like ` - WITH TABLE`, ` - FILLED`, ` - REVISED` to the copy name so the original is clearly distinguishable in Drive.

## Drive Upload Delivery — Primary Method for Created Files

**Preference:** When creating files (Excel sheets, PDFs, documents), **go straight to Drive upload + shareable link** as the primary delivery method. Do not send raw files via MEDIA first.

Bharat explicitly asks for "the link of the document" when a file is created. The Drive link is his preferred way to access and share deliverables.

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3')
media = MediaFileUpload(local_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', resumable=True)
uploaded = drive.files().create(body={'name': filename}, media_body=media, fields='id, name, webViewLink').execute()
drive.permissions().create(fileId=uploaded['id'], body={'type': 'anyone', 'role': 'reader'}).execute()
link = f"https://drive.google.com/file/d/{uploaded['id']}/view"
```

**Only fall back to MEDIA: delivery when Drive upload is not available** (no auth, no folder context). Do NOT try MEDIA first and then Drive — start with Drive.

## Document Index from Photos — Extract & Append Only (Never Touch User Columns)

**Rule:** When Bharat sends photos of printed document indexes for property files:

1. **Extract** via vision_analyze — get SI No., Particulars, Document No., Date for each row
2. **Append** as a new "FILE NO. X" section at the bottom of the existing sheet
3. **Leave BLANK** the columns: Original/Photocopy, Handed Over (Yes/No), Remarks
4. **Never** modify any existing rows or cells — Bharat handles those columns manually

Bharat explicitly said: *"I will be keeping the edits like whether it is the original or the next thing... you just need to take the details of photo and I will take that and see."*

**Workflow:**
```python
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4')

# 1. Find last row
result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID, range='A:A').execute()
last_row = len(result.get('values', []))
start_row = last_row + 1

# 2. Insert section header
sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range=f'A{start_row}:G{start_row}',
    valueInputOption='USER_ENTERED',
    body={'values': [['FILE NO. X — Property Name', '', '', '', '', '', '']]}
).execute()

# 3. Append document rows (only cols A-D filled; E-G left blank for user)
data_start = start_row + 1
doc_rows = [[si, desc, doc_no, date, '', '', ''] for si, desc, doc_no, date in extracted_docs]
sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range=f'A{data_start}:G{data_start + len(doc_rows) - 1}',
    valueInputOption='USER_ENTERED',
    body={'values': doc_rows}
).execute()
```

**🚨 CRITICAL:** Never use `files().update()` on a sheet that Bharat co-edits — it wipes all his manual changes. If the file is still an .xlsx, convert it to a native Google Sheet first (see `xlsx-create-and-upload` reference, Phase 3c).

## Calendar Events Over Cron Jobs for Reminders

**Rule:** When Bharat asks for a reminder/task notification, create a Google Calendar event — do NOT use Hermes cron jobs.

Bharat explicitly asked for notifications via Google Calendar rather than cron-based reminders. Steps:

1. Build the Calendar service: `from tools.gws_auth import build_service` then `calendar = build_service("calendar", "v3")`
2. Create a short (15-30 min) event on the target date/time with:
   - `'summary'` — clear title with context
   - `'description'` — to-do items in the body
   - `'transparency': 'transparent'` — shows as free on calendar
   - Popup reminder 10 min before
3. If a cron job was already created for the same purpose, remove it with `cronjob(action='remove', job_id=...)` before creating the calendar event.

**Watch out:** The Hermes environment needs the right Python — use `/opt/hermes/.venv/bin/python3` or `PYTHONPATH=/opt/hermes:$PYTHONPATH` when running calendar scripts via terminal(), or import via `from tools.gws_auth import build_service` inside execute_code().
