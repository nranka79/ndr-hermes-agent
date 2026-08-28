# Email Triage / Inbox Analysis — Reference Patterns

Concrete Gmail API patterns for the email triage workflow described in
`SKILL.md §5`. Use these as building blocks; adapt date ranges and queries
per session.

## Build Service

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

service = build_service('gmail', 'v1', service_name='google-draas')
```

Resolve the correct service_name via `gws_resolve_account` when unsure.

## Scan Recent Inbox (last N days)

```python
query = "in:inbox after:2026/07/18"
results = service.users().messages().list(
    userId='me', q=query, maxResults=50
).execute()
msgs = results.get('messages', [])
```

## Get Message Metadata

```python
m = service.users().messages().get(
    userId='me', id=msg['id'],
    format='metadata',
    metadataHeaders=['Subject','From','To','Date']
).execute()
headers = {h['name']: h['value'] for h in m['payload']['headers']}
subj = headers.get('Subject','?')
frm  = headers.get('From','?')
date = headers.get('Date','?')
```

## Check Who Sent Last on Thread

```python
thread = service.users().threads().get(
    userId='me', id=thread_id,
    format='metadata',
    metadataHeaders=['From']
).execute()
last_msg = thread['messages'][-1]
last_headers = {h['name']: h['value'] for h in last_msg['payload']['headers']}
last_from = last_headers.get('From', '')
last_from_user = 'ndr@draas.com' in last_from.lower()
```

**Logic:**
- `last_from_user == False` → needs reply (someone else wrote last)
- `last_from_user == True` → follow-up due (user wrote last, awaiting reply)

## Keyword Search for Action Items

```python
action_q = ("in:inbox (invoice OR bill OR approval OR deadline OR payment "
            "OR 'action required' OR 'please review' OR sign OR execute "
            "OR urgent OR compounding OR notice) after:2026/07/18")
action_results = service.users().messages().list(
    userId='me', q=action_q, maxResults=20
).execute()
```

## Sent Folder — Find Unreplied Threads

```python
sent_results = service.users().messages().list(
    userId='me', q='in:sent after:2026/07/18', maxResults=50
).execute()

# For each sent message, check if user's message is last on thread
processed = set()
for msg in sent_msgs:
    tid = m.get('threadId', '')
    if tid in processed:
        continue
    processed.add(tid)
    thread = service.users().threads().get(...).execute()
    last_from = ...  # check if last message is from user
    if last_from_user:
        flag as follow-up due
```

## Download Email Attachment (PDF)

```python
# Get attachment metadata
att = find_attachment_part(m['payload']['parts'])  # look for .pdf in parts

# Download via Gmail API
att_data = service.users().messages().attachments().get(
    userId='me', messageId=msg_id, id=att['body']['attachmentId']
).execute()
data = base64.urlsafe_b64decode(att_data['data'])

with open('/tmp/document.pdf', 'wb') as f:
    f.write(data)
```

## Scanned PDF — Extract Text via OCR

```python
# 1. Check if PDF has text layer
import fitz
doc = fitz.open('/tmp/document.pdf')
for page in doc:
    text = page.get_text()
    if not text.strip():
        # Scanned image — need OCR
        break

# 2. Convert pages to images
#    (shell command via terminal tool)
#    pdftoppm -png -r 300 input.pdf /tmp/pages/page

# 3. OCR each page via vision_analyze
#    vision_analyze(image_url='/tmp/pages/page-1.png',
#                   question='Extract ALL text from this document')
```

## Sent-Folder Cross-Reference (must do before flagging)

**The most common error is flagging an item as actionable when the user
has already handled it (replied, forwarded, or delegated).** Always
check the sent folder for the same period before reporting.

### Get all sent threads from the period

```python
sent_results = service.users().messages().list(
    userId='me', q='in:sent after:2026/07/18', maxResults=50
).execute()
sent_msgs = sent_results.get('messages', [])
```

### Build a map of thread_ids → user action taken

```python
handled = {}  # thread_id -> summary of what user did
for msg in sent_msgs:
    m = service.users().messages().get(
        userId='me', id=msg['id'],
        format='metadata',
        metadataHeaders=['Subject','To','From','Date']
    ).execute()
    headers = {h['name']: h['value'] for h in m['payload']['headers']}
    tid = m.get('threadId', '')
    subj = headers.get('Subject', '')[:100]
    to = headers.get('To', '')[:80]
    
    is_forward = subj.lower().startswith('fwd:')
    action = 'forwarded' if is_forward else 'replied'
    
    if tid not in handled:
        handled[tid] = {'action': action, 'to': to, 'subject': subj}
```

### Cross-reference with flagged inbox threads

```python
for inbox_item in flagged_threads:
    if inbox_item['thread_id'] in handled:
        # User already acted on this — demote or remove from flag
        skip  # or demote to FYI with note "user forwarded to X"
```

### When threading breaks

If a user composes a fresh reply (not using reply-all), Gmail may give it
a NEW thread ID. To catch this:

```python
# Get subjects of today's sent messages
sent_subjects = set()
for msg in sent_msgs:
    m = service.users().messages().get(
        userId='me', id=msg['id'], format='metadata',
        metadataHeaders=['Subject']
    ).execute()
    h = {h['name']: h['value'] for h in m['payload']['headers']}
    sent_subjects.add(h.get('Subject', '').lower().strip())

# For each flagged inbox thread, check if user sent something with
# a matching subject today (group by normalized subject)
for item in flagged_threads:
    norm = item['subject'].lower().replace('re: ', '').replace('fwd: ', '').strip()
    for s in sent_subjects:
        if norm in s.lower() or s.lower() in norm:
            # User already acted on this topic via a new thread
            pass
```

## Noise Filtering (items to skip in report)

Skip from the actionable categories:
- Automated "Please sign in" / "Please sign out" (daily time-tracker emails)
- Delivery Status Notifications (bounce/ delay reports)
- Routine bank transaction alerts (unless flagged by user)
- Marketing / promotional newsletters
- MS 365 quarantine notifications

## Common Pitfalls

- **Quoting issues in shell**: When passing Python scripts with single quotes
  via `terminal()`, write the script to a `.py` file first, then execute it.
  Shell-escaped f-strings with `{braces}` break.
- **`rfc822msgid:` searches**: Use the exact Message-ID including the angle
  brackets omitted in the header value. E.g. `rfc822msgid:abc@domain.com`
  for `Message-ID: <abc@domain.com>`.
- **`after:` date format**: Use `YYYY/MM/DD`. The Gmail search `after:` is
  inclusive of the date given.
- **Thread count ≠ reply count**: A thread with 2 messages both from the
  user means no reply yet. A thread with 3+ messages where the last is not
  from the user means someone replied.
- **ALWAYS cross-reference sent folder before reporting**: This is the #1
  error to avoid. The user may have forwarded a payment reminder to their
  colleague, or replied on a thread that got a new thread ID. Without
  checking sent items, you'll flag items already handled and waste the
  user's time verifying your work.
- **Forwarded emails are handled, not pending**: When the user forwards
  ("Fwd: ...") an email to someone else, the action item is now with the
  recipient. Note this in the report as "user forwarded to X" rather than
  as a pending action.
- **Don't rely solely on thread IDs**: A reply composed as a fresh email
  (not using reply/reply-all) gets a different thread ID. Match by
  normalized subject keywords as a fallback.
- **Check sent folder for today before reporting**: Query `in:sent
  after:YYYY/MM/DD` with `maxResults=30-50` and compare thread IDs and
  subjects against your flagged inbox items. This catches both threaded
  replies and standalone forwards.
