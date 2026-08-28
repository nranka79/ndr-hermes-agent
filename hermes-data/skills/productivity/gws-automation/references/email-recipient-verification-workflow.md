# Email Recipient Verification from Voice / Partial Names

When a DRAAS user (typically Nishant via Telegram voice) says "send this to X, CC Y" or "share this with Z", the names come through voice transcription which regularly mangles names, domains, and email formats. **Do not assume the voice-transcribed email is correct** — verify before creating any draft, sharing any document, or sending anything.

## Common Voice Transcription Errors (DRAAS-specific)

| Voice Said | Actual | Fix |
|---|---|---|
| "Ark Irwin at yahoo.co.it" | arch_arvind2000@yahoo.co.in | Check Gmail history for the real sender |
| "Cincina Gouda S Gouda at draas.com" | Sinchana Gowda <sgowda@draas.com> | Name + email combo was completely wrong |
| "Rahul" (for Vinod Das) | Vinod Kumar Das <vkdas@draas.com> | Nickname mismatch — verify from context |
| "Verden" | Vardhan Ventures | Architectural/company name mangling |
| "Geo Autopay" | Jio Autopay (jio.com) | Brand name homophone (Indian English) |

## The Verification Pipeline (in order)

### Step 1 — Can you find this person in existing Gmail threads?

```python
from tools.gws_auth import build_service
svc = build_service('gmail', 'v1')

# Search for the name as the user said it
result = svc.users().messages().list(
    userId='me',
    q='<name-variant>',
    maxResults=5
).execute()
```

Try multiple variants automatically:
- The name as said (e.g. "Cincina", "Ark", "Kantesh")
- The name with common spelling variations (single/double letters, phonetic variants)
- The name plus the company/project context (e.g. "Cincina Ranka Amber" or "architect Amber")
- The company/domain as said AND common alternatives

### Step 2 — Check the From header of found emails

When messages exist from this person, extract the exact From address from the email headers:

```python
msg = svc.users().messages().get(
    userId='me', id=message_id,
    format='metadata',
    metadataHeaders=['From', 'To', 'Subject']
).execute()
headers = {h['name']: h['value'] for h in msg['payload']['headers']}
actual_email = headers.get('From')  # e.g. "Sinchana Gowda <sgowda@draas.com>"
```

### Step 3 — If no existing threads, check these DRAAS sources

1. **Google People API** — `people.people().searchContacts()` or `connections().list()`
2. **NDR Contacts sheets** — Two sheets on Drive (see `references/contact-phone-resolution-workflow.md` for IDs)
3. **Kelsa Employee Master (DRA, pipeline ID: 4530)** — Check for DRAAS employees
4. **Ask the user** — After exhausting data sources, present what you found and ask for the correct email

### Step 3a — Raw MIME header extraction for hidden recipients

When the visible `To`/`Cc` headers from `format='metadata'` don't include the person you're looking for, the recipient may be hidden in the raw MIME headers (e.g. CC'd but stripped from the Gmail API metadata response, or added inline as "++ Name").

Use `format='raw'` and scan the full RFC 2822 headers:

```python
import base64 as b64

msg = service.users().messages().get(
    userId='me', id=msg_id, format='raw'
).execute()
raw_bytes = b64.urlsafe_b64decode(msg['raw'].encode('utf-8'))
raw_text = raw_bytes.decode('utf-8', errors='replace')

# Scan for target name or email in raw headers
for line in raw_text.split('\n'):
    if 'saurabh' in line.lower() or 'vashishth' in line.lower():
        print(line)
```

This reveals recipients that aren't visible in `format='metadata'` responses. Common cases:
- BCC'd recipients (never shown in metadata)
- CC recipients added inline with "++ Name" in the reply body
- Recipients from email forwarding chains that got compressed by Gmail's API

**Worked example (Jun 2026 — Saurabh Vashishth):**
A search for `"vashish"` in Gmail returned 0 results. But Viraj's email body said "Looping in Saurabh" without an email visible. Using `format='raw'` on that message revealed:
```
CC: Satish Jadhav <satish.jadhav@godrejventure.com>, Amit Saraf
    Saurabh Vashishth <saurabh.vashishth@godrejventure.com>
```
The newline-broken CC header (wrapped across two lines) wasn't parsed by the Gmail API's metadata extractor — only raw header parsing catches this.

**Pattern:**
1. Search Gmail for a message mentioning the person's name
2. Get the message with `format='raw'`
3. Parse the raw MIME text looking for the name in To/CC/BCC lines
4. Confirm the email format before using it

### Step 4 — Verify email domain conventions

DRAAS email patterns:
- `firstname.lastname@draas.com` — standard (e.g. `sgowda@draas.com`, `vkdas@draas.com`)
- Some use `pm2.blr@draas.com`, `sales1.blr@draas.com` — department-based
- External consultants use their personal email (e.g. `kanteshbgme@gmail.com`, `msingh@redsoul.co.in`)
- **Do NOT assume everyone has @draas.com** — Kantesh B G, Manohar Singh, and others use personal emails

### Step 5 — Before creating any draft or sharing any document

1. Confirm the correct email from Gmail history
2. Show the user what you found: "Found Sinchana Gowda as sgowda@draas.com — correct?"
3. Only proceed after implicit or explicit confirmation
4. If the user corrects you, SAVE the correct mapping to memory

## Document Verification (Parallel Pattern)

The same verification principle applies to **documents the user references by name**:

| Voice Said | Actual Document | Reason for Mismatch |
|---|---|---|
| "Sanction plan PDF" | `20260518_Ranka_Amber_Sanctioned_Plan_GBA_BECC_0540_25-26.pdf` (2.4MB) | The smaller "Building Sanction Planpdf" (531KB) was a license document, not the actual drawing |
| "Sanction plan" | The drawing with site plans, floor plans, area details | The license document only shows approval text |

**Verification approach:**
1. Search Drive for documents matching the description
2. If multiple candidates, cross-reference against:
   - Previous email threads that shared this document
   - File size (actual drawings are 2MB+, license documents are ~500KB)
   - File name patterns (`YYYYMMDD_Project_Description.ext`)
3. Present the best candidate and confirm before sharing

## When the User Says "Remember That" or Corrects You

This is a first-class signal. Immediately:
1. Update memory with the correct mapping
2. If it's a systematic pattern (voice mangling specific names), add to this reference
3. Do NOT retry with the wrong data — stop and verify first
