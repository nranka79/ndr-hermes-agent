# Employee Compensation Analysis — Multi-Source Workflow

**Class:** Multi-source employee data gathering → structured Google Doc with market benchmarks

**Trigger:** User asks to "review salary / compensation / incentives for employee X" or "analyze all work done by employee Y".

## Workflow Overview

```
Gmail (salary history, work emails)
  ├── WhatsApp chat exports (work scope, task patterns)
  ├── Drive (JD docs, KPI sheets, CTC data)
  ├── Sheets (Chennai/DRA Aadithya salary comparables, incentive policies)
  ├── Web research (market benchmarks via Naukri, Aon, Randstad, TeamLease, Michael Page)
  └── Google Doc (compiled analysis with recommendations)
```

## Phase 1 — Gmail: Salary History & Work Scope

### Search queries
```python
# Salary-related emails
query = "(from:pm2.blr@draas.com OR to:pm2.blr@draas.com OR from:anbarasan@draas.com OR to:anbarasan@draas.com) after:2023/1/1"
```

### Pagination pattern
```python
# Gmail API pagination — maxResults=500, use nextPageToken
all_ids = []
page_token = None
while True:
    params = {'userId': 'me', 'q': query, 'maxResults': 500}
    if page_token:
        params['pageToken'] = page_token
    result = svc.users().messages().list(**params).execute()
    all_ids.extend([m['id'] for m in result.get('messages', [])])
    page_token = result.get('nextPageToken')
    if not page_token:
        break
```

### Header extraction (cheap, no body)
```python
# Fetch with format='metadata' for headers only
msg = svc.users().messages().get(
    userId='me', id=msg_id, format='metadata',
    metadataHeaders=['From','To','Cc','Subject','Date']
).execute()
```

### Role classification
Classify each email by Anbu's role: SENDER (authored), TO (directly addressed), CC (informed). Filter out:
- Daily attendance sign-in/out notifications ("Please sign in for the day", "Please sign out")
- Leave applications where employee is only CC'd as team lead

### Salary revision data extraction
When emails contain salary figures, fetch the FULL body (format='full') and extract:
- Base Pay, Attendance Pay, Performance/Incentive Pay
- Effective date
- Entity (which company pays)
- Any notes about advances/loans adjustability

**Pitfall:** Salary data is often in forwarded/threaded emails — the actual revision figures may be in an earlier message within the same thread ID, not the newest message. Use `svc.users().threads().get(userId='me', id=thread_id)` to get the full thread, then scan each message for monetary figures.

## Phase 2 — WhatsApp Chat Analysis

WhatsApp exports come as `.txt` files. Analyze for:

### Work categorization
- Engineering & site supervision (daily plans, structural, MEP)
- Land procurement (negotiations, JDA, sale deeds)
- Legal & approvals (court cases, HNDT, BDO, RERA, BBMP)
- Team management (interviews, vendor mgmt)
- Business development (investor terms, leasing)

### Communication pattern
- Response timeliness
- Task acknowledgement level
- Preferred communication mode (WhatsApp vs call vs email)

### Loan/advance mentions
Search WhatsApp text for keywords: `loan`, `advance`, `transfer`, `HDFC`, `account`

## Phase 3 — Drive: JD Docs, KPIs, CTC Data

### Search for relevant documents
```python
# Search by name
result = drive.files().list(
    q="name contains 'Engineering' or name contains 'Director' or name contains 'JD'",
    fields="files(id,name,mimeType)"
).execute()

# Search by content
result = drive.files().list(
    q="fullText contains 'engineering head' and (name contains 'JD' or name contains 'KPI')",
    fields="files(id,name,mimeType)"
).execute()
```

### Read Google Docs (native)
```python
docs = build('docs', 'v1', credentials=creds)
content = docs.documents().get(documentId=doc_id).execute()
# Walk body['content'] for paragraphs
```

### Read Google Sheets (native)
```python
sheets = build('sheets', 'v4', credentials=creds)
rows = sheets.spreadsheets().values().get(
    spreadsheetId=sheet_id, range='Sheet1!A1:F100'
).execute().get('values', [])
```

### Read .xlsx files (binary — NOT Sheets API)
```python
import openpyxl
from googleapiclient.http import MediaIoBaseDownload
import io

# Step 1: Download binary via get_media
request = drive.files().get_media(fileId=xlsx_id)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()

# Step 2: Parse with openpyxl
wb = openpyxl.load_workbook(io.BytesIO(fh.getvalue()), data_only=True)
ws = wb.active
for row in ws.iter_rows(values_only=True):
    print(row)
```

**Pitfall:** `.xlsx` files in Drive have mimeType `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`. Cannot use `sheets.spreadsheets().get()` — returns 400. Must use `drive.files().get_media()` + `openpyxl`.

## Phase 4 — Web Research

Search for market benchmarks from:
- **Aon India Salary Survey** — sector-wise increment data
- **Randstad India** — salary trends by industry
- **TeamLease** — salary guides by sector
- **Michael Page India** — salary benchmarks for senior roles
- **Naukri.com** — active job listings with salary ranges
- **AmbitionBox** — employee-reported salaries
- **Glassdoor** — salary estimates

### Key metrics to capture
- Market salary range for comparable role (minimum, median, maximum)
- Sector average annual increment %
- Time between salary revisions (market norm)
- Commute/travel allowance norms
- Incentive/bonus structure patterns

### Presenting findings
For each finding, cite the source name and provide a stable URL (search result page, not a specific listing that will expire).

## Phase 5 — Google Doc Creation

### Create folder structure (if needed)
```python
# Check if Analysis & Review folder exists under HR
drive.files().list(
    q="name='Analysis & Review' and '<hr_folder_id>' in parents and trashed=false",
    fields="files(id,name)"
).execute()
```

### Create document
```python
docs = build('docs', 'v1', credentials=creds)
doc = docs.documents().create(body={'title': 'Employee Name — Comprehensive Review & Analysis'}).execute()
doc_id = doc['documentId']

# Move to target folder
drive.files().update(
    fileId=doc_id,
    addParents=target_folder_id,
    removeParents='root',
    fields='id,parents'
).execute()
```

### Populate with structured sections

Document sections:
1. **Executive Summary** — one-paragraph overview of the analysis and key recommendation
2. **Employee Profile** — name, email, tenure, designation, current salary
3. **Salary History** — timeline table of all revisions with amounts, entities, effective dates
4. **Work Scope Analysis** — categorized by function (Engineering, Land BD, Legal/Approvals, Team Mgmt) with project names
5. **Communication & Engagement Pattern** — email vs WhatsApp behaviour, response times
6. **Comparable Salary Data** — internal (Chennai CTC sheet) and external (market benchmarks)
7. **Incentive Structures** — BDM, Liaison, Sales policies from Drive
8. **Company Context** — turnover, engineering spend, growth trajectory
9. **Loans & Advances** — any records found, pending inputs
10. **Compensation Analysis — Supporting Data** — market position, increment cadence, role scope premium
11. **Recommendations** — proposed structure with components, KPI framework, incentive recommendations, loan write-off approach
12. **Sources & References** — all URLs cited
13. **Next Steps** — what's pending, what needs user confirmation

### Insert content via Docs API

**⚠️ Execution pattern: write_file + terminal (NOT execute_code)**

`execute_code` is blocked for Google API calls in many contexts (cron, long-running ops). Always use this pattern instead:

```python
# Step 1: Write script to file (in the session)
script_content = '''#!/opt/hermes/.venv/bin/python
import json, base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)') as f:
    creds_data = json.load(f)
creds = Credentials.from_authorized_user_info(creds_data)
docs = build('docs', 'v1', credentials=creds)

doc_id = "YOUR_DOC_ID"

# Get current document end
doc = docs.documents().get(documentId=doc_id).execute()
end = doc['body']['content'][-1]['endIndex'] - 1

# Insert text
requests = [{
    "insertText": {
        "location": {"index": end},
        "text": ''' + "''' + full_content + '''" + '''
    }
}]
docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
print("Done")
'''

# Step 2: Write to file
write_file(path='/opt/data/update_doc.py', content=script_content)

# Step 3: Execute via terminal
terminal('cd /opt/data && /opt/hermes/.venv/bin/python update_doc.py', timeout=60)
```

**Pitfall:** String escaping in f-strings with triple-quoted content requires careful handling. Either:
- Use `\"\"\"` for the script delimiter and raw strings for inner content
- Or write content to a `.py` file then construct the script body separately

**Pitfall:** `insertText` at `endIndex - 1` is correct — the last element is a trailing newline, so inserting at `endIndex` would land after it.

### Post-creation: Adding new sections to existing document

When the user asks to add more content to an already-populated document:

```python
# 1. Get current end index
doc = docs.documents().get(documentId=doc_id).execute()
end = doc['body']['content'][-1]['endIndex'] - 1

# 2. Insert new section at the end
requests = [{
    "insertText": {
        "location": {"index": end},
        "text": "\\n\\n## NEW SECTION TITLE\\n\\nContent here..."
    }
}]
docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
```

Each update creates a new `endIndex` — always re-fetch the document before adding another section. Do NOT cache the end index across multiple updates.

### Content design pattern: Complex tables in Docs API

Google Docs API does not have a native `insertTable` that works well with text-based inserts from the `batchUpdate` endpoint for large content. **Best approach:** Format table content as pre-formatted text with clear column separators using pipe/dash structures in plain text:

```
Component | Amount | Frequency | Notes
Base Pay | ₹85,000 | Monthly | Fixed
```

The user can format it properly once they open the document. Trying to use the `insertTable` request with `createTable` is more complex and fragile. For tabular data, plain text alignment with clear row separators (`━━━━` lines) works best.

## Key Pitfalls

1. **Gmail API resultSizeEstimate is unreliable** — it's an estimate, not a count. Always paginate through ALL pages with `nextPageToken` to get the actual total.

2. **Format metadata vs full** — `format='metadata'` is fast for headers but returns NO body text. For salary figures, loan mentions, or any content extraction, you need `format='full'` which is slower but includes the body. Use a two-pass approach: metadata pass for discovery, full pass only on messages that match your content criteria.

3. **OAuth token timeout on large messages** — fetching format='full' for messages with large attachments can timeout. Workaround: write a standalone script that loads the token directly from `/data/hermes/users/{telegram_id}/the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)`, builds the service manually, and processes messages one at a time with a 0.3–0.5s sleep between calls.

4. **Content size limits** — Google Docs API has a 50MB document size limit and 1MB per single `insertText` request. For very large documents, split content into multiple batchUpdate calls.

5. **Salary data in forwarded threads** — the email containing actual salary figures may be the FORWARDED original, not the top-level message. Always search the entire thread (`threads().get()`) when you find a salary-related subject line.

6. **CTC file may be .xlsx not Google Sheets** — check mimeType before attempting to read. .xlsx files must be downloaded via `get_media()` and parsed with `openpyxl`.

7. **WhatsApp media is omitted** — WhatsApp exports show `<Media omitted>` for all photos, videos, and files. Only text content is available for analysis. In the compensation context, this means vCard contacts mentioned in chat won't have phone numbers accessible.

8. **`build_service` timeout** — The `tools.gws_auth.build_service()` helper may timeout on long-running batch operations (fetching 400+ messages with format='full'). Workaround: use the direct OAuth token loading pattern (documented in gws-automation skill) for sustained batch operations.
