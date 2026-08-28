# Email Thread → Document Compliance Tracker (DOCX)

**Class:** Workflow — Extract document checklists from Gmail email threads, compare requested vs sent items, produce structured DOCX compliance report.

**Trigger:** User asks "check my emails for [topic/funding/project], make a list comparing documents required vs sent vs pending" or similar compliance-tracking requests.

## Workflow

### Phase 1 — Discover the relevant thread

Search Gmail with targeted queries. For Indian real-estate project funding threads, try:

```python
from tools.gws_auth import build_service
service = build_service("gmail", "v1")

queries = [
    "Motilal Oswal",
    '"project funding" checklist',
    '"data required" funding project',
]

all_ids = set()
for q in queries:
    results = service.users().messages().list(userId='me', q=q, maxResults=50).execute()
    for m in results.get('messages', []):
        all_ids.add(m['id'])
```

Then fetch metadata (From, To, Subject, Date, Message-ID, In-Reply-To, References) to reconstruct the thread:

```python
for mid in sorted(all_ids):
    msg = service.users().messages().get(userId='me', id=mid, format='metadata',
        metadataHeaders=['From','To','Subject','Date','References','Message-ID','In-Reply-To']).execute()
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
```

Save to `motilal_email_metadata.json` for later processing.

### Phase 2 — Fetch full bodies + attachments

Use `format='full'` (NOT `'raw'`) to get the proper payload structure. Walk MIME parts recursively:

```python
body_parts = []
attachments = []

def extract_parts(part):
    if 'parts' in part:
        for subpart in part['parts']:
            extract_parts(subpart)
    elif part['mimeType'] == 'text/plain' and 'data' in part['body']:
        body_parts.append(base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace'))
    elif 'filename' in part and part['filename']:
        fn = part['filename']
        if 'attachmentId' in part['body']:
            att = service.users().messages().attachments().get(
                userId='me', messageId=mid, id=part['body']['attachmentId']).execute()
            att_data = base64.urlsafe_b64decode(att['data'])
            # Save to local cache
            safe_fn = re.sub(r'[^a-zA-Z0-9._-]', '_', fn)
            with open(f'/tmp/{mid}_{safe_fn}', 'wb') as af:
                af.write(att_data)

extract_parts(msg['payload'])
```

**⚠️ Pitfall — `format='raw'` vs `format='full'`:**
Using `format='raw'` returns a base64-encoded RFC 2822 message. The `payload` structure is NOT in the API response directly — only after decoding the raw bytes and parsing with `email.message_from_bytes()`. Use `format='full'` for the standard `payload` structure with `parts`, `mimeType`, `body.data`, and `body.attachmentId`. This avoids the extra parsing step and is more reliable for attachment download.

### Phase 3 — Reconstruct the checklist from email bodies

The key insight: Motilal Oswal-type checklists come in **waves**:

1. **Wave 1 (initial):** Full checklist — all documents across all categories
2. **Wave 2 (follow-up):** Only pending items since last submission
3. **Wave 3 (second follow-up):** Refined pending list after reviewing submitted docs

Parse each email body for numbered lists, section headers, and document names. Extract:
- Original checklist items from Wave 1 (group-level + project-level)
- Follow-up pending items from Wave 2
- Second follow-up with new items from Wave 3

### Phase 4 — Build the DOCX tracker

Use `python-docx` with a table-based layout:

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document()

# Title
doc.add_heading('Motilal Oswal Project Funding — Document Tracking', level=0)

# Meta table (lender, contact, projects, purpose, dates)
meta = doc.add_table(rows=6, cols=2)
# ... fill rows

# Section 1: Original checklist — table with columns: #, Document, Details, Status, Remarks
table1 = doc.add_table(rows=len(items)+1, cols=5)
table1.style = 'Light Grid Accent 1'

# Section 2: Follow-up checklists with comparison
# Section 3: Summary — what is still PENDING with priority markers (🔴 P1, ⚠️ P6)
# Section 4: Email thread timeline
```

**Key DOCX patterns:**
- `table.style = 'Light Grid Accent 1'` for professional look
- Bold headers using `cell.paragraphs[0].runs[0].bold = True`
- Color-code status: `🔴 PENDING`, `⚠️ UNCLEAR`, `SENT ✓`
- Add "Responsible" column in summary section
- Use `doc.add_paragraph('• text', style='List Bullet')` for bullet lists

### Phase 5 — Status classification rules

| Source | Meaning |
|--------|---------|
| **SENT ✓** | Attachment visible in sent email OR body explicitly confirms it was provided |
| **⚠️ UNCLEAR** | Body says "covered" but no attachment visible in Gmail |
| **🔴 PENDING** | Explicitly listed as pending in latest follow-up email AND no evidence of sending |
| **NEW** | Appears in Wave 3 but not in Wave 1 or 2 — genuinely new requirement |

## Status annotations from the user

When the user (senior person) reviews your draft analysis and marks items as "NOT SURE IF SENT" or adds notes in their reply:
- Preserve those annotations in the tracker — they are authoritative
- The user knows their own records better than what Gmail's attachment API reveals
- Add a separate "Prakash's Notes" column or footnote for these annotations

## Verified session

**Jun 2026 — Motilal Oswal Home Finance Ltd / Ranka Amber funding:**
- 10 emails across 3 checklists (29 Apr, 25 May, 12 Jun)
- 38-item tracker covering Group docs, Project docs, KYC, financials
- DOCX delivered to Prakash Singh (psingh@draas.com)
- Full scripts: `/opt/data/search_motilal.py`, `/opt/data/fetch_motilal_full.py`, `/opt/data/build_docx_tracker.py`
- Source data: `/opt/data/motilal_email_metadata.json`, `/opt/data/motilal_emails_full.json`
