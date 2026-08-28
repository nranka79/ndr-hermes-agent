# Gmail Search — Corporate Compliance & Statutory Meeting Notices

**Class of task:** Find an email notice about a statutory meeting (AGM, EGM, Board Meeting, Creditors Meeting) sent by a compliance department (e.g. `compliance@drahomes.in`, `compliance@draas.com`, or external CS firms).

## Trigger patterns

User asks: "Check if the notice/agenda for [meeting type] on [date] included [specific item]" or "Find the email from [sender] about [meeting]."

## Search strategy (try in order)

### 1. Start precise, then broaden

```python
# First attempt — exact sender + meeting type + date
call("gmail_search", service_name="google-draas",
    query="from:compliance@drahomes.in \"AGM\" \"30 July\"")

# If no results, drop the date and search by sender + meeting keyword
call("gmail_search", service_name="google-draas",
    query="from:compliance@drahomes.in \"Annual General Meeting\" 2026")

# Broaden further — drop year constraint
call("gmail_search", service_name="google-draas",
    query="from:compliance@drahomes.in notice")

# Try alternate sender addresses
call("gmail_search", service_name="google-draas",
    query="from:compliance@draas.com \"30th July\" meeting")
```

### 2. Try different meeting type phrasings

Users often conflate AGM / EGM / Board Meeting / Shareholders Meeting. Search for all variants:

```python
queries = [
    f"from:{sender} \"AGM\" OR \"Annual General\"",
    f"from:{sender} \"EGM\" OR \"Extraordinary\" OR \"Extra-ordinary\"",
    f"from:{sender} \"Board Meeting\"",
    f"from:{sender} \"shareholder\" meeting",
    f"from:{sender} {date_term}",
]
```

### 3. Check ALL known user accounts — including personal Gmail

The notice may not go to the user's primary inbox. Always resolve ALL accounts first with `gws_resolve_account()` (no args), then search each one. Personal Gmail accounts (e.g. `nishantranka@gmail.com` → `google-gmail`) are frequently missed but just as likely to receive compliance emails.

```python
# Step 1: Discover all accounts
# gws_resolve_account() with no args lists every known account
# Common DRAAS accounts:
# - google-draas (ndr@draas.com)
# - google-ahfl (ndr@ahfl.in)
# - google-gmail (nishantranka@gmail.com)
# - pm2.blr@draas.com (project manager)
# - psingh@draas.com (Prakash Singh)
# - sales1.blr@draas.com (sales team)

# Step 2: Search each one systematically
for acct in ["google-draas", "google-ahfl", "google-gmail"]:
    result = call("gmail_search", service_name=acct, query=...)
```

**Don't assume** the user's personal Gmail account mirrors their DRAAS inbox. Compliance emails sent to `ndr@drahomes.in` typically appear in the DRAAS account (primary alias), but communications from external counsel, third-party CS firms, or forwarded copies of statutory notices may land in the personal Gmail account instead.

### 4. For specific agenda items, read the subject + snippet carefully

The `gmail_search` result includes `snippet` (first ~120 chars of the email body or attachment filename context). For compliance notices, the snippet often reveals the meeting's purpose even when the body is elsewhere:

| Snippet clue | Meeting purpose |
|---|---|
| `"for issuance of NCDs on Private placement"` | EGM for debt issuance |
| `"alteration for Share transfer"` | AoA amendment for share transfer |
| `"Compulsory Transfer of Shares"` | Share transfer resolution (often removed after deliberation) |
| `"appointment of Auditor"` | AGM routine business |
| `"adoption of Financial Statements"` | AGM standard item |

### 5. Search for specific agenda language when you know what you're looking for

```python
# Known agenda keywords
call("gmail_search", service_name="google-draas",
    query="from:compliance@drahomes.in \"shorter notice\" EGM")
call("gmail_search", service_name="google-draas",
    query="from:compliance@drahomes.in \"amendment\" OR \"AoA\" OR \"Articles\"")
call("gmail_search", service_name="google-draas",
    query="from:compliance@drahomes.in \"special resolution\"")
```

## Key limitation: Attachment-only emails have empty body

**Critical pitfall:** Compliance notices are frequently sent as PDF attachments with **no body text**. When you call `gmail_get(message_id=...)` on such emails, the output is:

```json
{"id": "...", "body": "", ...}  
```

There is no HTML or plain-text body to read. The **only** signals are:
- **Subject line** — often contains meeting type, date, company name, and purpose
- **Snippet** — Gmail's excerpt from the attachment filename or any preceding content
- **Attachment** — the actual PDF/Word notice, which needs to be downloaded separately

### How to handle

If the snippet is informative enough (e.g. `"Dear Shareholders, Please find attached the Notice of EGM for issuance of NCDs"`), you can answer based on snippet + subject alone without downloading the attachment.

If you need the full agenda, the attachment must be downloaded and read. **`gmail_get` returns empty body** for these emails — use the raw MIME extraction technique below.

#### Complete: extract PDF/DOCX attachment from an attachment-only email

**✅ Works from both `execute_code` AND `terminal()`** — call `build_service()` at the top level of your script, not through a nested `terminal()` call.

The vault Unix socket IS available to `execute_code`'s sandbox child process (it's a direct child of the agent, not a subprocess-of-a-subprocess). The constraint is only against nesting: calling `terminal()` from within `execute_code` to run a second Python script that itself tries `build_service()` will fail because the second subprocess doesn't inherit the vault socket. Keep `build_service()` calls in your main script — never shell out to another process for auth.

```python

```python
import base64, email, json, os, subprocess, zipfile
from email import policy

from tools.gws_auth import build_service

# 1. Get the raw message (MIME format)
service = build_service("gmail", "v1", service_name="google-draas")
msg = service.users().messages().get(userId='me', id='MESSAGE_ID', format='raw').execute()
raw_bytes = base64.urlsafe_b64decode(msg['raw'].encode('ASCII'))

# 2. Parse MIME and find the PDF/DOCX part
mime_msg = email.message_from_bytes(raw_bytes, policy=policy.default)
for part in mime_msg.walk():
    fn = part.get_filename()
    if fn and (fn.endswith('.pdf') or fn.endswith('.docx')):
        payload = part.get_content()
        payload_bytes = payload.encode('utf-8') if isinstance(payload, str) else payload
        
        # Save to temp file
        ext = fn.split('.')[-1]
        tmp_path = f'/tmp/egm_attachment.{ext}'
        with open(tmp_path, 'wb') as f:
            f.write(payload_bytes)
        
        # 3. Extract text
        if ext == 'pdf':
            result = subprocess.run(['pdftotext', tmp_path, '-'], 
                                  capture_output=True, text=True)
            text = result.stdout
        elif ext == 'docx':
            import zipfile
            with zipfile.ZipFile(tmp_path) as z:
                xml = z.read('word/document.xml').decode('utf-8')
                # Extract text between XML tags
                import re
                text = re.sub(r'<[^>]+>', ' ', xml)
                text = re.sub(r'\s+', ' ', text).strip()
        
        print(f"=== Extracted text from {fn} ===")
        print(text)
        break
```

**Alternative: save the raw email to disk for inspection**
```python
with open('/tmp/raw_email.txt', 'wb') as f:
    f.write(raw_bytes)
# Then examine with: head -c 5000 /tmp/raw_email.txt
```

#### Alternative: use `gmail_get` with `format="full"` (when it works)

For emails that DO have body text (not attachment-only), the standard bridge call works:
```python
result = call("gmail_get", service_name="google-draas", message_id="...")
print(result["body"])  # plain text body when present
```

But for compliance notice emails that are purely attachment-based, `body` will be empty string `""` — in that case, the raw MIME approach above is the only path.

## Common compliance email domain patterns for DRAAS

| Sender | Used for | Notes |
|---|---|---|
| `compliance@drahomes.in` | DRA Aadithya South City Projects (DRAASCPPL), DRA Aadithya Projects (DRAAPPL), Truliv Properties | Primary compliance team. Sends board meeting notices, EGMs, AGMs, minute drafts. |
| `compliance@draas.com` | Historical — older notices (pre-2025) | Earlier name: "CORPORATE SECRETARIAL - DRA HOMES" |
| `info@complianceexpert.in` | Third-party ROC filing reminders | Notices about due dates, DIR-3 KYC, AGM deadlines — not actual meeting notices |
| `mundhara_co@yahoo.co.in` | Mundhara & Co. (Company Secretaries) | Share transfer, dematerialization, statutory filings |
| `Vineeth Mundhara` (via compliance@drahomes.in) | Share-related matters | Duplicate certificates, demat, shareholding patterns |

## Distinguishing meeting types from subject lines

| Subject pattern | Meeting type |
|---|---|
| `"Annual General Meeting"` or `"AGM"` | AGM — held annually within 6 months of financial year end |
| `"Extra-ordinary General Meeting"` or `"EGM"` | EGM — any general meeting that isn't the AGM |
| `"Notice of EGM"` | EGM — specific notice with explanatory statement |
| `"Board Meeting"` | Board of Directors meeting — not a shareholders' meeting |
| `"Shorter Notice"` + `"Board Meeting"` | Board meeting called on shorter notice (less than 7 days) |
| `"Minutes of Board Meeting"` | Draft minutes circulated after a board meeting |

## Answering "did the notice/include X item" and reporting absence

### When the email IS found
- Subject + snippet often answer the question directly (e.g. "for issuance of NCDs" = no AoA amendment)
- Download attachment and read full agenda (see attachment extraction above) for definitive answer

### When NO email is found across all accounts

**Don't just say "not found." Give the user actionable diagnostics.** Structure your report:

1. **Summary** — what was searched (accounts, senders, date ranges, query patterns)
2. **Closest matches** — list any nearby emails that could be conflated (e.g. "EGM on 28th July for NCDs" vs what the user recalled)
3. **Possibilities** — typical reasons the email doesn't exist:
   - Not yet sent (meeting is still upcoming, draft in progress)
   - Wrong meeting type (user said AGM, actual notice says EGM/Board Meeting)
   - Wrong sender domain (e.g. `compliance@draas.com` vs `compliance@drahomes.in`, or external CS firm like `mundhara_co@yahoo.co.in`)
   - Wrong date (user may be off by a few days)
   - Delivered via physical post / WhatsApp instead of email
   - Discussion happened verbally or via voice call, not in writing
4. **Next steps to offer**:
   - Download and read attachment of closest match to confirm
   - Check Trash/Archive
   - Search Drive for the filed notice
   - Ask the user to forward the email if it exists elsewhere

### User often misremembers details — search flexible variants

| What user may say | What to actually search |
|---|---|
| "AGM on 30th July" | Also check: EGM, Board Meeting, Shareholders Meeting. Also check: 28th, 29th, 31st July |
| "compliance drahomes.in" | Also check: compliance@draas.com, corporate secretarial, specific CS firm names |
| "amendment of AoA" | Also search: alteration, modification, shorter notice, special resolution |
| "Raj/Ranjeeth shared a draft" | Discussion may have been via voice/WhatsApp — no email trail exists |
