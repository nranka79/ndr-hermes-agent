# Email-Based Multi-Project Document Tracking

Extract document checklists from Gmail and build comprehensive tracking spreadsheets across multiple workstreams (RERA, bank approvals, project funding).

## When to use this pattern

A user has multiple parallel workstreams (e.g., RERA registration, ICICI pre-approval, Motilal Oswal funding) and needs to:
- Cross-reference what documents were requested vs sent
- Track which items are shared, pending, unclear, or not applicable
- Present a color-coded dashboard per workstream and overall
- Deliver as an Excel spreadsheet on Google Drive

## Workflow

### Phase 1 — Gmail search across all relevant queries

Run multiple targeted queries covering each workstream, then deduplicate by message ID:

```python
queries = [
    "Ranka Amber RERA",
    "Ranka Amber ICICI",
    "Ranka Amber HDFC",
    "Motilal Oswal",
    "RERA consultant",
    "bank pre-approval Ranka",
    # ... per workstream
]

all_ids = set()
for q in queries:
    results = service.users().messages().list(userId='me', q=q, maxResults=50).execute()
    for m in results.get('messages', []):
        all_ids.add(m['id'])
```

### Phase 2 — Extract checklists from email bodies

For each unique message ID, fetch full content and extract:
- Document lists / checklists from the body text (look for numbered lists, tables, bullet points)
- Attachments (PDFs, spreadsheets)
- **Google Drive links** from both plain text and HTML parts:

```python
drive_links = []
def extract_drive_links(part):
    if part['mimeType'] == 'text/plain' and 'data' in part['body']:
        raw = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
        drive_links.extend(re.findall(r'https?://drive\.google\.com[^\s<>)]+', raw))
    elif part['mimeType'] == 'text/html' and 'data' in part['body']:
        raw = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
        drive_links.extend(re.findall(r'https?://drive\.google\.com[^\s<>\"\']+', raw))
    if 'parts' in part:
        for subpart in part['parts']:
            extract_drive_links(subpart)
```

Drive links extracted from emails are often the primary source of documents — the email body itself may just say "find the documents at the link below."

### Phase 3 — Build the tracking matrix

Consolidate all checklists from Motilal Oswal, RERA consultants, bank query emails into a master document list. Cross-reference each item:

| What was requested | Who requested it | Was it sent? | Which email/attachment proves it? | Who needs to send it? |

**Status values:**
- `SENT ✓` — document visibly attached or on shared Drive
- `PENDING 🔴` — requested but no evidence of sending
- `ASSIGNED 🔶` — task assigned to a team member, not yet received back
- `UNCLEAR ⚠️` — might have been sent but attachment not visible or unclear from email thread
- `NOT AVAILABLE 🔴` — explicitly stated as not obtainable
- `NOT APPLICABLE ✅` — not needed for this project

### Phase 4 — Generate color-coded Excel with openpyxl

Build a multi-sheet workbook with one sheet per workstream plus a summary dashboard:

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

green_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
red_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
yellow_fill = PatternFill(start_color='FFEB9C', end_color='FFEB9C', fill_type='solid')
header_fill = PatternFill(start_color='2F5496', end_color='2F5496', fill_type='solid')
header_font = Font(bold=True, color='FFFFFF', size=11)

wb = openpyxl.Workbook()
# Sheet 1: Project A — RERA
# Sheet 2: Project A — Bank X
# Sheet 3: Project B — Bank Y
# Sheet 4: Project A — Funding
# Sheet 5: Summary Dashboard
```

Each sheet has:
- Project metadata header (project name, lender/consultant, contacts, drive links, dates)
- Document table with status color-coding
- Column widths set for readability

### Phase 5 — Upload to Drive and share

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload(path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
meta = {'name': display_name, 'parents': [folder_id]}
uploaded = service.files().create(body=meta, media_body=media, fields='id,webViewLink').execute()

# Make readable by anyone with link
service.permissions().create(
    fileId=uploaded['id'],
    body={'type': 'anyone', 'role': 'reader'},
    sendNotificationEmail=False
).execute()
```

Present both the **web view link** and the **direct download link** so the user can choose.

## Related

This reference is paired with the main `gws-automation` skill — the multi-query search pattern, Drive link extraction, and openpyxl coloring techniques above depend on the build_service patterns documented in the parent skill.

## Known pitfalls

- **Gmail search limits at ~50 results per query** — use `pageToken` for pagination if more results expected
- **Attachments may not be visible in metadata-only fetches** — always use `format='full'` or `format='raw'` to get attachment data
- **Duplicate emails across inbox + sent** — the same message may appear in both `in:inbox` and `in:sent` searches. Deduplicate by message ID
- **Drive links embedded in HTML** — extract from both `text/plain` and `text/html` MIME parts; HTML parts often have different link formats
- **Large threads can timeout** — if a thread has 50+ messages, fetching all bodies may hit the API rate limit. Focus on the first/last messages and ones with attachments
- **Color-coding consistency** — use the same status color scheme across all sheets so the dashboard is meaningful
- **Dashboard percentages** — calculate as `shared_count / total_count * 100` for each sheet, then sum across all sheets for the overall
- **CRITICAL: Per-process independence — do NOT conflate documents across processes.** Each lender/bank/authority process tracks ONLY what was sent TO THAT SPECIFIC PARTY. A building plan shared with ICICI does NOT count as "sent" for Motilal Oswal — each recipient got their own copy. When building tracking spreadsheets with multiple sheets (one per bank/process), each sheet's document list must be independently verified from the emails and attachments sent to that specific recipient. The original checklist from each party defines what they're asking for; only documents attached to emails TO them or placed on a Drive folder explicitly shared WITH them count as "sent" for that process. A document sitting on an internal Drive folder that was never linked to the lender is NOT sent. Templates (e.g., COPMOF, Unit MIS formats) received FROM the lender are not "shared" — they were received and need to be filled and returned.
- **Distinguish templates received FROM the lender vs documents sent TO the lender.** When a lender emails you an Excel template (like a COPMOF or Unit MIS format), that's a document you received, not one you sent. Mark it as "TEMPLATE RECEIVED" rather than "SENT" until the filled copy is returned. This was a key error to avoid.
