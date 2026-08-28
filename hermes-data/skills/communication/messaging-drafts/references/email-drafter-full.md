---
name: email-drafter
description: |
  Drafts new emails, threaded replies, and saved drafts via Gmail API (Python stdlib).
  Auth: per-user OAuth token via gws_auth.py (HERMES_SESSION_USER_ID).
  If token missing, generate auth URL and send to user. NEVER uses SA DWD for Gmail.
  Trigger: "email [name]", "reply to [name]'s email", "draft an email to [name]", "send [name] an email", "save an email draft", "follow-up email"
category: communication
version: 2.1.0
author: ndr@draas.com
---

# Email Drafter

## Critical notes

- `google_workspace_manager` does NOT exist — do not invoke it as a tool or CLI
- All Gmail operations: direct Gmail API via Python stdlib (`urllib.request` + `json`)
- `POST /gmail/v1/users/me/messages.send` returns HTTP 404 on this account — always use the draft workflow instead
- `POST /gmail/v1/users/me/drafts` with `threadId` in the payload body causes HTTP 400 — threading is done via MIME headers only
- For forwarded emails where you need the inner body, use `format=raw` (not `format=full`)

---

## Execution environments — which tool to use

**Always use `terminal` with python3 heredoc for Gmail operations — not `execute_code`.**
`HERMES_SESSION_USER_ID` and other HERMES_ vars are available in terminal.

**Correct pattern — always use terminal:**
```bash
cd /data/hermes && python3 - << 'PYEOF'
import os
from tools.gws_auth import load_credentials, get_auth_url, has_token
from google.auth.transport import requests as google_requests

TELEGRAM_ID = os.environ.get("HERMES_SESSION_USER_ID", "")
if not TELEGRAM_ID or not has_token(TELEGRAM_ID):
    url = get_auth_url(TELEGRAM_ID) if TELEGRAM_ID else "(no session)"
    print(f"GWS_AUTH_NEEDED: {url}")
    exit(1)

creds = load_credentials(TELEGRAM_ID)
creds.refresh(google_requests.Request())
access_token = creds.token
# Now use access_token with urllib ...
PYEOF
```

**If you see `GWS_AUTH_NEEDED:`** — send the printed URL to the user via Telegram and ask them to click it to authorize. Once they complete auth, retry the operation.


---

## Gmail API — stdlib recipe

**Auth: per-user OAuth token via `gws_auth.py`.** Never use SA DWD for Gmail.

```python
import os
from tools.gws_auth import load_credentials, get_auth_url, has_token
from google.auth.transport import requests as google_requests

TELEGRAM_ID = os.environ.get("HERMES_SESSION_USER_ID", "")
if not TELEGRAM_ID or not has_token(TELEGRAM_ID):
    url = get_auth_url(TELEGRAM_ID) if TELEGRAM_ID else "(no session)"
    print(f"GWS_AUTH_NEEDED: {url}")
    exit(1)

creds = load_credentials(TELEGRAM_ID)
creds.refresh(google_requests.Request())
access_token = creds.token
# Use access_token in Authorization: Bearer header with urllib — unchanged from before
```


---

## Common operations

**List/search messages:**
```python
query = urllib.parse.quote('to:@recipientdomain.com subject:keyword after:2026/04/01')
url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=10&q={query}'
req2 = urllib.request.Request(url, headers={'Authorization': f'Bearer {access_token}'})
with urllib.request.urlopen(req2, timeout=15) as resp:
    messages = json.loads(resp.read()).get('messages', [])
```

**Get full message:**
```python
url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=full'
```

**Get full thread (all messages):**
```python
url = f'https://gmail.googleapis.com/gmail/v1/users/me/threads/{thread_id}?format=full'
```

**Trash emails (move to bin):**
```python
trash_url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}/trash'
req = urllib.request.Request(trash_url, method='POST',
    headers={'Authorization': f'Bearer {access_token}'})
with urllib.request.urlopen(req, timeout=15) as resp:
    json.loads(resp.read())
```

**List today's emails (top N, with full header detail):**
```python
import re
from datetime import datetime, timezone, timedelta

ist = timezone(timedelta(hours=5, minutes=30))
today_start = datetime(2026, 5, 6, 0, 0, 0, tzinfo=ist).astimezone(timezone.utc)
today_str = today_start.strftime('%Y/%m/%d')

query = f'after:{today_str} in:inbox'
url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=20&q={urllib.parse.quote(query)}'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {access_token}'})
with urllib.request.urlopen(req, timeout=15) as resp:
    result = json.loads(resp.read())

for m in result.get('messages', []):
    mid = m['id']
    # Fetch full headers + snippet
    full_url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{mid}?format=full'
    req2 = urllib.request.Request(full_url, headers={'Authorization': f'Bearer {access_token}'})
    with urllib.request.urlopen(req2, timeout=15) as resp:
        data = json.loads(resp.read())
    
    headers = {h['name']: h['value'] for h in data['payload']['headers']}
    labels = data.get('labelIds', [])
    snippet = data.get('snippet', '')
    
    # Classify
    if 'CATEGORY_PROMOTIONS' in labels:
        cat = '📢 Promotional'
    elif 'CATEGORY_PERSONAL' in labels:
        cat = '🏦 Transactional'
    elif 'CATEGORY_UPDATES' in labels:
        cat = '📋 Updates'
    elif 'IMPORTANT' in labels:
        cat = '💼 Work'
    else:
        cat = '📧 General'
    
    # Clean snippet HTML entities
    snippet = re.sub(r'&#39;', "'", snippet)
    snippet = re.sub(r'&amp;', '&', snippet)
    
    print(f"Category: {cat}")
    print(f"From: {headers.get('From', '')}")
    print(f"To: {headers.get('To', '')}")
    print(f"Cc: {headers.get('Cc', '')}")
    print(f"Subject: {headers.get('Subject', '')}")
    print(f"Date: {headers.get('Date', '')}")
    print(f"Summary: {snippet}")
```

**Classify email type (promotional vs transactional):**
```python
# Check labelIds for Gmail's native categories
labels = data.get('labelIds', [])
if 'CATEGORY_PROMOTIONS' in labels:
    category = 'promotional'
elif 'CATEGORY_UPDATES' in labels:
    category = 'transactional/updates'
elif 'CATEGORY_PERSONAL' in labels:
    category = 'personal'
# Also check raw email for list-unsubscribe (strong promo signal)
raw_url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=raw'
# ...fetch raw, decode...
is_promo = 'list-unsubscribe' in raw_email.lower()
```

---

## 1. Trigger Conditions

Activate on: "email [name]", "reply to [name]'s email", "draft an email to [name]", "send [name] an email", "save an email draft", "follow-up email"

**Account:** session user's email from 'User Profile -> Email (Google Workspace)'. NEVER ndr@draas.com unless Nishant is requesting.

---

## 2. Stage 1 — Context Gathering

### For a NEW email
Always use `contact_resolver` — never guess an email address. Confirm the resolved contact with the user before drafting.

### For a REPLY (existing thread)
1. Search by recipient domain + subject keyword to find the thread
2. Fetch full thread to get `threadId`, participants, and all prior messages
3. Present context before drafting: who, subject, last message date, participants

---

## 3. Stage 2 — Draft

### Work email tone
- No greeting, straight to the point
- Numbered tasks if there are asks
- No boilerplate ("Hope you're well", "Dear [name]") unless asked
- Subject: `[Project/Entity]: one-line description`

### Personal / casual tone (Roshni Ranka / "RO")
- Warmer, no subject prefix
- Plain text is fine

Always show the draft and wait for explicit "send" before doing anything further.

---

## 4. Stage 3 — Draft vs Send

### Creating a draft (new email)
```python
mime_msg = MIMEText(body, 'plain')
mime_msg['to'] = to_addr
mime_msg['cc'] = cc_addr  # optional
mime_msg['subject'] = subject
raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()

draft_payload = {
    "message": {
        "raw": raw,
        "payload": {
            "headers": [
                {"name": "Bcc", "value": bcc_addr}  # BCC goes in headers, not top-level
            ]
        }
    }
}  # NO threadId
url = 'https://gmail.googleapis.com/gmail/v1/users/me/drafts'
data = json.dumps(draft_payload).encode()
req = urllib.request.Request(url, data=data,
    headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=15) as resp:
    result = json.loads(resp.read())
# result['id'] = draft ID
```

**BCC in drafts:** The Gmail API drafts endpoint **accepts `Bcc` in the message payload headers**. Set it as:
```python
"Bcc": "aamirkhan@me.com"  # or any BCC recipient
```
Do NOT pass `bcc` as a top-level field — it belongs in `payload.headers`.

After saving, tell the user the draft is ready at `https://mail.google.com/mail/u/0/#drafts`. They add any additional BCC recipients manually before sending.

### Creating a draft in an existing thread (reply)
```python
mime_msg = MIMEText(body, 'plain')
mime_msg['to'] = to_addr
mime_msg['cc'] = cc_addr
mime_msg['subject'] = subject
# Threading via MIME headers — NOT threadId in payload (causes HTTP 400)
mime_msg['In-Reply-To'] = original_message_id
mime_msg['References'] = original_message_id
raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()

draft_payload = {"message": {"raw": raw}}  # NO threadId
url = 'https://gmail.googleapis.com/gmail/v1/users/me/drafts'
# ...POST
```

### Sending — googleapiclient WORKS, urllib FAILS

**The urllib/stdlib approach** (`POST /gmail/v1/users/me/messages.send`) returns HTTP 404 on this account — confirmed reproducible. Do NOT use it for sending.

**The googleapiclient approach** (`gws_auth.build_service` → `gmail.users().messages().send()`) DOES work for sending. Confirmed working Jun 2026:

```python
from tools.gws_auth import build_service
gmail = build_service('gmail', 'v1')
sent = gmail.users().messages().send(userId='me', body={'raw': raw}).execute()
# Returns {'id': '...', 'threadId': '...'} — works!
```

**Decision:**
| Approach | Send Support | Draft Support | When to Use |
|----------|-------------|---------------|-------------|
| `gws_auth.build_service` + googleapiclient | ✅ Works | ✅ Works | Sending HTML emails, sending new messages, any send operation |
| urllib stdlib (`urllib.request` + `json`) | ❌ 404 | ✅ Works | Creating drafts (new or threaded), searching, listing, trashing |

**Rule of thumb:** Use `build_service` + googleapiclient for sending. Use the stdlib approach (which doesn't need the googleapiclient dependency from terminal) for drafts, search, and bulk operations.

### HTML Email with Styled Tables — Confirmed Working (Jun 2026)

Send richly formatted HTML emails with styled tables using `MIMEText(body, 'html')`:

```python
from tools.gws_auth import build_service
from email.mime.text import MIMEText
import base64

gmail = build_service('gmail', 'v1')

html_body = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 680px; margin: 0 auto; padding: 20px;">

<!-- Content with styled tables -->

<table style="width: 100%; border-collapse: collapse;">
  <thead>
    <tr style="background-color: #1a1a2e; color: white;">
      <th style="padding: 10px; border: 1px solid #ddd;">#</th>
      <th style="padding: 10px; border: 1px solid #ddd;">Item</th>
      <th style="padding: 10px; border: 1px solid #ddd;">Yes/No</th>
    </tr>
  </thead>
  <tbody>
    <tr style="background-color: #f9f9f9;">
      <td style="padding: 10px; border: 1px solid #ddd;">1</td>
      <td style="padding: 10px; border: 1px solid #ddd;">Requirement description</td>
      <td style="padding: 10px; border: 1px solid #ddd;">☐</td>
    </tr>
  </tbody>
</table>

</body>
</html>"""

mime_msg = MIMEText(html_body, 'html')
mime_msg['to'] = 'recipient@example.com'
mime_msg['subject'] = 'Subject Line'
mime_msg['from'] = 'sender@example.com'

raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode()
sent = gmail.users().messages().send(userId='me', body={'raw': raw}).execute()
```

**Verified patterns:**
- `MIMEText(body, 'html')` renders inline CSS and styled tables correctly in Gmail
- Tables with alternating row backgrounds improve readability for checklists
- Use `☐` (U+2610) for unchecked checkbox symbols in HTML tables
- Keep `max-width: 680px` for good mobile rendering
- Gmail strips `<style>` tags from `<head>` — use inline `style=` attributes on elements instead
- Full HTML doctype + `<html><body>` wrapper works fine in Gmail

### Sending confirmation

After a successful send, always confirm to the user:
> Sent! Subject: [subject] → [recipient]

---

## Supporting files
- `references/zodiac-hotels-liquidation.md` — ZHPL (Zodiac Hotels) entity context, participants, thread details, and decision summary. Populated from session on 2026-05-05.
- `references/bounce-notification-patterns.md` — Mailer-daemon bounce patterns: invalid domain vs address-not-found vs former employee addresses. Includes @findingform.design leaver list and cleanup query.
- `references/resignation-acceptance-workflow.md` — Full step-by-step workflow for drafting legally solid resignation acceptance emails: finding the resignation, locating employment documents, extracting legal terms, cross-checking notice periods, structuring the draft, and saving to Gmail. Includes TruBld case data.
- `references/bali-trip-2026.md` — Bali trip context
- `references/royal-sundaram-kanta-ranka-2025.md` — Insurance claim context

### Scripts
- `scripts/bulk-trash-bounces.py` — Reusable bulk trash script for mailer-daemon bounce notifications. Handles pagination automatically, resolves TELEGRAM_ID from `HERMES_SESSION_KEY` fallback, safe for daily cron.

- **`GWS_AUTH_NEEDED` output means auth URL was printed to stdout, not an error.** When the auth check runs, if the token is missing, the Python script prints `GWS_AUTH_NEEDED: https://auth.url...` and exits 1. This is NOT a Python traceback — it is an instruction. The correct response is to extract the URL and send it to the user via Telegram, then retry after they authorize. Never try to "debug" the Python script when this pattern appears.
- **Mailer-daemon bounce notifications accumulate fast.** When sending to non-existent recipients (e.g. @findingform.design addresses for people who left), Gmail generates multiple identical bounce emails per failed delivery attempt. These pile up in inbox. Proactively trash them — or set up a daily cron to handle them.
- **Never trust `threadId` in the drafts API body** — it causes HTTP 400. Threading only works via MIME `In-Reply-To`/`References` headers, and even then the draft must be manually opened and sent from the original thread composer.
- **Use `format=raw` for forwarded email inner bodies** — `format=full` strips the RFC822 wrapper.
- **`pdftotext` returns empty on scanned/image-based PDFs** — the text extraction will show 0 bytes. Always check file size first (`wc -c`), then try `pdfinfo` to confirm page count. For scanned PDFs, fall back to OCR with `tesseract` or use `pymupdf` (fitz) which handles image layers better. See `pdf-page-extraction` skill for the full workflow.
- **Multi-email drafting: confirm threading strategy per email.** When the user asks for two or more emails about the same topic (e.g. stern email to surveyor + cooperative email to insurance manager), do NOT assume they both go in the same thread or both as new emails. Confirm per-email:
  - "Email A (to surveyor): new separate email? Or reply in existing thread?"
  - "Email B (to manager): reply in existing thread? Or new email?"
  
  Example (Jun 2026): Nishant wanted the Venkatesh email as a separate new email, and the Azim email as a reply in the existing insurance claim thread. If you assume both are new or both are replies, you waste a round trip. Explicitly confirm threading per recipient before drafting.

---

## Cron integration

This skill's Gmail API operations (search, trash, list) are safe to embed in cron prompts for recurring email hygiene tasks:
- Daily bounce notification cleanup: `from:mailer-daemon@googlemail.com subject:"Delivery Status Notification"` → trash
- Weekly promotional digest: summarize top emails by category

---

## Pitfalls

- **BCC in draft creation:** The Gmail API drafts endpoint does NOT accept `bcc` as a top-level field. To add BCC recipients when creating a draft, include `Bcc` in `payload.headers`:
  ```python
  "payload": {"headers": [{"name": "Bcc", "value": "bcc@example.com"}]}
  ```
  Do NOT use `"bcc": "bcc@example.com"` at the top level of the message object — it will be silently ignored. After creating the draft, direct the user to open `https://mail.google.com/mail/u/0/#drafts` and they can add additional BCC recipients manually before sending.
- **Gmail search with multiple conditions may return 0 results** even when matching messages exist. If one query returns 0, split into single-condition queries and examine each independently. E.g., `from:jeet.kumar@housing.com subject:microsite` → 0; but `from:jeet.kumar@housing.com` alone → finds the thread.
- **`build_service()` returns a Resource object, not a service with `.credentials`** — always use `load_credentials()` then `discovery.build(..., credentials=creds)` separately.
- **Bulk operations require pagination** — Gmail API caps at 500 messages per search call regardless of `maxResults`. When trashing or listing large batches, always loop on `nextPageToken` until exhausted. `resultSizeEstimate` is approximate; do not rely on it for exact counts.
- **Cron sessions: `HERMES_SESSION_USER_ID` may be empty** — cron jobs set `HERMES_SESSION_KEY=agent:main:telegram:dm:<telegram_id>` but not `HERMES_SESSION_USER_ID`. If `has_token(TELEGRAM_ID)` fails with an empty string, extract the Telegram ID from `HERMES_SESSION_KEY` (format: `agent:main:telegram:dm:<numeric_id>`) and use it directly as the fallback `TELEGRAM_ID`.

## Drafting checklist

Before presenting the draft, confirm:
- [ ] Thread identified and threadId extracted (for replies)
- [ ] Correct recipient(s) and CC
- [ ] Tone matches the recipient (work vs personal)
- [ ] Draft created in Gmail Drafts — NOT sent automatically
- [ ] Draft link shared with user for manual send
