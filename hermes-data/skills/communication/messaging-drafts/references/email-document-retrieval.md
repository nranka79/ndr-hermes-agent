# Email Document Retrieval — Find & Extract When User Says "It's In My Email"

**Trigger:** User says "the [document/notice/resolution] is in my email from [sender clue]" or "I sent it to [recipient] — find it in my sent mail."

## Workflow

### 1. Parse the Email Clue

Extract from the voice message:
- **Sender domain/email** — e.g. "compliance at pra-homes.in" → `compliance@drahomes.in`
- **Subject keywords** — e.g. "board resolution", "EGM", "OC shared"
- **Recipient** — who it was sent to (helps scope the search)
- **Date** — "yesterday", "last week", "June 2026"
- **Attachment type** — PDF, DOCX, etc.

**Pitfall — domain correction:** The user may say "pra-homes.in" but the actual domain is "drahomes.in". Always try both variations if the first search returns nothing. Also check for `.in` vs `.com`, and alternate spellings.

### 2. Search Gmail

```python
from tools.gws_auth import build_service
service = build_service("gmail", "v1")

# Build query from parsed clues — use Gmail search syntax
results = service.users().messages().list(
    userId='me',
    q='from:compliance@drahomes.in subject:"EGM" OR subject:"Board Resolution"'
).execute()
```

**Search tips:**
- Use `from:` + `subject:` for narrowest results
- If subject is uncertain, search with `from:` + a content keyword
- Limit with `maxResults` — fetch metadata first (format='metadata'), not full bodies
- For sent mail, use `from:ndr@draas.com` (or the user's email)

### 3. Identify the Right Message

Check metadata headers to confirm:
```python
md = service.users().messages().get(userId='me', id=msg['id'],
    format='metadata',
    metadataHeaders=['From','To','Subject','Date']).execute()
```

Show the user a shortlist if multiple match — don't assume you picked the right one.

### 4. Get the Full Message (Including Message-ID for Replies)

Use `format='raw'` to get the full raw email with all headers:
```python
raw = service.users().messages().get(userId='me', id=msg_id, format='raw').execute()
email_bytes = base64.urlsafe_b64decode(raw['raw'].encode('utf-8'))
```

This reveals the `Message-ID`, `References`, `In-Reply-To` headers needed for threaded replies — these are NOT available in metadata format.

**Pitfall:** `format='metadata'` returns an empty `Message-ID`. Always use `format='raw'` and decode to get the real Message-ID.

### 5. Download Attachments

```python
parts = [msg_data['payload']]
while parts:
    part = parts.pop(0)
    if 'parts' in part:
        parts.extend(part['parts'])
    if part.get('filename') and part['filename'].endswith('.pdf'):
        if 'attachmentId' in part.get('body', {}):
            att = service.users().messages().attachments().get(
                userId='me', messageId=msg_id, id=part['body']['attachmentId']
            ).execute()
            file_data = base64.urlsafe_b64decode(att['data'])
            with open(f'/tmp/{filename}', 'wb') as f:
                f.write(file_data)
```

### 6. Extract Text from PDF Attachments

Use `pdftotext` (available at `/usr/bin/pdftotext`):
```bash
pdftotext /tmp/filename.pdf /tmp/filename.txt
```

If the PDF is image-based/scanned, `pdftotext` may return 0 bytes. Try `strings` for limited extraction, or note that OCR is needed.

### 7. Act on the Extracted Data

Common post-extraction actions:
- **Create calendar event** — when the document contains a meeting date/time/link (EGM notice, board meeting agenda)
- **Draft email reply** — when the user wants to respond in the same thread
- **Generate WhatsApp message** — when the user wants to share extracted details
- **Risk analysis** — when the document is a board resolution, the user may want minority-shareholder perspective analysis

## Example: EGM Notice → Calendar Event

Extract from the PDF:
1. Company name, date, time
2. Meeting type (EGM, Board Meeting) and agenda items
3. Venue and hybrid meeting link (Zoom, MS Teams)
4. Attendees listed

Then create the calendar event with all details including the conferencing link.

## Example: Board Resolution → Risk Analysis

Extract:
1. Each resolution item (loan approval, NCD issuance, etc.)
2. Key terms: interest rate, amount, tenure, security, personal guarantees
3. Related party angles — does the lender connect to any director/family?
4. Overall debt stacking across multiple agenda items

Then present risk analysis by item from the user's stated perspective (e.g., minority shareholder).

## Session History — Check for Previous Attempts Before Re-searching

When the user says "the board resolution I referred to" or "the email I mentioned", check session_search FIRST before re-searching Gmail. They may have referenced it in a prior turn that was compacted away.
