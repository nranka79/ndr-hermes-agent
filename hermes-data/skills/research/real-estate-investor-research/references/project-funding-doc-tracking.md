# Project Funding Document Tracking — Multi-Party Workflow

## The Core Rule: Per-Process Isolation

**A document shared with Party A does NOT count as "sent" for Party B.** Each bank, NBFC, RERA consultant, or investor has its own checklist. They must be tracked independently.

The user will correct you if you conflate them — this happened in June 2026 when Motilal Oswal's pending checklist was compared against documents sent to ICICI Bank. Each party's status column must reflect only what was sent to that specific party.

## Workflow

### 1. Identify All Processes

For a real estate project, funding typically involves:

| Process | Party | Key Contact |
|---------|-------|-------------|
| RERA Registration | RERA Consultants LLP | Project-specific consultant |
| Bank Pre-approval A | ICICI / HDFC / etc. | RM + Credit team |
| Bank Pre-approval B | Another bank | Different RM, different checklist |
| Project Funding | NBFC / HFC (e.g., Motilal Oswal HF) | Relationship Manager |
| Alternative Funding | VS&A Advisors, etc. | Structured finance advisor |

### 2. Search Gmail Per-Process

Run separate Gmail searches for each party:

```python
queries = [
    '"Ranka Amber" "reraconsultants"',           # RERA
    '"Ranka Amber" "icici.bank"',                 # ICICI Bank
    '"Ranka Amber" "motilaloswal"',               # Motilal Oswal
    '"Ranka Amber" "HDFC" pre-approval',          # HDFC
]
```

For each query, extract:
- The checklist/requirement email FROM the party (what they asked for)
- The response email TO the party (what was sent)
- Attachment filenames (concrete proof of what was shared)

### 3. Build a Per-Process Spreadsheet

Use openpyxl with:
- **One sheet per process** (never combine)
- Columns: `#`, `Document`, `Requested By [Party]?`, `Sent To [Party]?`, `Date`, `Notes`
- Status colors: `SHARED ✓` (green), `PENDING 🔴` (red), `ASSIGNED 🔶` (yellow), `UNCLEAR ⚠️` (yellow)

### 4. Key Traps to Avoid

| Mistake | Why It's Wrong | Fix |
|---------|----------------|-----|
| Marking "Enterprise data.xlsx" as SENT | That file was a TEMPLATE RECEIVED from MOHFL, not sent by us | Check direction: did the party send it to us, or we to them? |
| Calling a company a "Corporation" when it's a "Council" | Chikkaballapur CMC = City Municipal Council, not Corporation | Verify exact entity name from official sources |
| Claiming "Shared via Drive" without confirming the party received Drive access | The Drive link may not have been shared with that specific party | Check email CCs and permissions |
| Saying "Covered by Bharat ✓" without verifying attachments were actually present | Emails may say "attached" but Gmail attachment extraction may miss files | Always list attachment filenames explicitly |

### 5. Gmail Extraction Pattern

```python
from tools.gws_auth import build_service
import base64, re
from email import message_from_bytes

service = build_service("gmail", "v1")

# Search with party-specific query
results = service.users().messages().list(userId='me', q='Ranka Amber motilaloswal', maxResults=50).execute()

for m in results.get('messages', []):
    msg = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    
    # Extract body
    body_parts = []
    attachments = []
    
    def extract_parts(part):
        if 'parts' in part:
            for subpart in part['parts']:
                extract_parts(subpart)
        elif part['mimeType'] == 'text/plain' and 'data' in part['body']:
            body_parts.append(base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace'))
        elif 'filename' in part and part['filename']:
            attachments.append(part['filename'])
    
    extract_parts(msg['payload'])
    body = '\n'.join(body_parts)
    subject = headers.get('Subject', '')
    from_h = headers.get('From', '')
```

### 6. Drive Folder Organization for Banking Docs

When creating a banking documents folder:

```
Ranka Amber - Banking documents folder/
├── YYYY-MM-DD, Village, Document Description, RegNo.pdf
└── Ranka Amber — Index of Documents.xlsx
```

**Filename format:** `YYYY-MM-DD, Village Name, Document Description, Registered Document No..ext`

**File copy pattern (Drive-to-Drive):**
Use `service.files().copy(fileId=src_id, body={'name': new_name, 'parents': [target_folder_id]})`.

**Oversized files (>20 MB):** Delete from banking folder and link to original source in the index spreadsheet instead.

**For legal opinions / title reports hosted in a separate folder:** Link to the source folder directly rather than re-copying. Note the source folder link in the index.

### 7. Spreadsheet Index Requirements

| Column | Content |
|--------|---------|
| Sl No | Sequential |
| Document Date | YYYY-MM-DD or "—" if unknown |
| Village | Project village name |
| Document Description | Clear descriptive name |
| Parties Involved | All identified parties |
| Aadhar No | From document (or "—" if not extractable) |
| PAN No | From document (or "—" if not extractable) |
| Document Link | Clickable hyperlink to the file in the banking folder |

**Clickable links:** Set both the value AND hyperlink property:
```python
ws.cell(row, col).value = url
ws.cell(row, col).hyperlink = url
ws.cell(row, col).font = Font(color='0563C1', underline='single')
```

### 8. Checklist-Driven Status Tracking

When a party sends multiple follow-ups (e.g., MOHFL sent checklists on 29 Apr, 25 May, and 12 Jun), the latest checklist is the authoritative source. Compare it against:
- What the previous response claimed to have sent
- What attachments are actually visible in the email thread
- What the user's manager confirmed as covered

Document-level status options:
- `SENT ✓` — attachment or Drive link confirmed in email to that party
- `PENDING 🔴` — explicitly requested by the party, not yet sent
- `ASSIGNED 🔶` — internal assignee identified, document not yet received
- `UNCLEAR ⚠️` — mentioned but attachment not visible in Gmail
- `NOT AVAILABLE 🔴` — party was told it's not available (e.g., NOCs)
- `NOT APPLICABLE ✅` — party accepted it's not required
- `CLARIFIED ⚠️` — responded with explanation instead of document
- `HELD` — kept pending until filing stage (RERA consultants)
