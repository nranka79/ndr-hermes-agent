# Email Triage — Code Patterns

Canonical Python snippets for email analysis via the Gmail API. Copy-paste ready.

## Prerequisites

```python
from tools.gws_auth import build_service
from datetime import datetime, timezone, timedelta
import base64
```

## 1. Fetch messages from last N hours

```python
gmail = build_service('gmail', 'v1', service_name='google-draas')  # resolve first
now = datetime.now(timezone.utc)
cutoff = now - timedelta(hours=48)

results = gmail.users().messages().list(
    userId='me', q=f"after:{int(cutoff.timestamp())}", maxResults=50
).execute()
msgs = results.get('messages', [])
```

## 2. Extract metadata from a message

```python
def get_metadata(gmail, msg_id):
    msg = gmail.users().messages().get(
        userId='me', id=msg_id, format='metadata',
        metadataHeaders=['From','To','Cc','Subject','Date']
    ).execute()
    hdrs = {h['name']: h['value'] for h in msg['payload']['headers']}
    ts = int(msg['internalDate']) / 1000
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return {
        'id': msg_id,
        'threadId': msg['threadId'],
        'from': hdrs.get('From', ''),
        'to': hdrs.get('To', ''),
        'cc': hdrs.get('Cc', ''),
        'subject': hdrs.get('Subject', '(no subject)'),
        'date': dt,
        'labels': msg.get('labelIds', []),
        'is_inbox': 'INBOX' in msg.get('labelIds', []),
        'is_sent': 'SENT' in msg.get('labelIds', []),
        'is_draft': 'DRAFT' in msg.get('labelIds', []),
    }
```

## 3. Extract plain text body from a message

Handles multipart/mixed, multipart/alternative, and single-part messages:

```python
def extract_plain_text(full_msg):
    """Walk MIME parts to find text/plain content."""
    parts_text = []

    def walk(parts):
        for p in parts or []:
            if p['mimeType'] == 'text/plain' and 'data' in p.get('body', {}):
                parts_text.append(
                    base64.urlsafe_b64decode(p['body']['data']).decode('utf-8', errors='replace')
                )
            elif 'parts' in p:
                walk(p['parts'])
            elif p['mimeType'] == 'multipart/alternative' and 'parts' in p:
                # text/plain preferred over text/html
                plain = [sp for sp in p['parts'] if sp['mimeType'] == 'text/plain']
                if plain:
                    walk(plain)
                else:
                    walk(p['parts'])

    walk(full_msg['payload'].get('parts', []))
    return '\n---\n'.join(parts_text) if parts_text else '(no plain text body)'
```

Usage:
```python
full = gmail.users().messages().get(userId='me', id=msg_id, format='full').execute()
body = extract_plain_text(full)
```

## 4. Check if a sent email received any reply

```python
def check_for_reply(gmail, sent_msg_id):
    """Returns True if someone other than NDR has replied in the thread."""
    msg = gmail.users().messages().get(userId='me', id=sent_msg_id, format='minimal').execute()
    thread = gmail.users().threads().get(
        userId='me', id=msg['threadId'], format='metadata',
        metadataHeaders=['From', 'Subject', 'Date']
    ).execute()
    for tm in thread.get('messages', []):
        hdrs = {h['name']: h['value'] for h in tm['payload']['headers']}
        sender = hdrs.get('From', '')
        if 'ndr@draas.com' not in sender and 'Nishant Ranka' not in sender:
            return True
    return False
```

## 5. Parse a bounce notification

```python
def parse_bounce(raw):
    """Extract failed recipient from a Mail Delivery Subsystem bounce."""
    import re
    m = re.search(r'Final-Recipient:\s*rfc822;\s*(\S+)', raw)
    failed_addr = m.group(1) if m else None

    m = re.search(r'Status:\s*([\d.]+)', raw)
    status = m.group(1) if m else None

    m = re.search(r'Diagnostic-Code:\s*.*?((?:550|551|552|553|554)[^;\n]*)', raw)
    diagnostic = m.group(1).strip() if m else None

    return {'failed_recipient': failed_addr, 'status': status, 'diagnostic': diagnostic}
```

## 6. List drafts

```python
drafts = gmail.users().drafts().list(userId='me', maxResults=20).execute()
for d in drafts.get('drafts', []):
    draft = gmail.users().drafts().get(userId='me', id=d['id'], format='full').execute()
    hdrs = {h['name']: h['value'] for h in draft['message']['payload']['headers']}
    print(f"Draft: {hdrs.get('Subject')} → {hdrs.get('To')}")
    #    Note: draft['message']['payload'], not draft['payload']!
```

## 7. Detect auto-reply vs human reply

An email that looks like a reply (subject starts with Re:) but contains no
`text/plain` body and whose `Return-Path` points to a marketing platform
(e.g. `em3324.bigbasket.com`, `bounces+...@sendgrid.com`) is an auto-reply,
not a human response. Classify as "auto-reply received" and note it as
awaiting a real human reply.

```python
def is_auto_reply(gmail, msg_id):
    """Heuristic: empty text/plain + marketing Return-Path = auto-reply."""
    full = gmail.users().messages().get(userId='me', id=msg_id, format='raw').execute()
    raw = base64.urlsafe_b64decode(full['raw']).decode('utf-8', errors='replace')
    body = extract_plain_text(full)
    has_text = bool(body and body != '(no plain text body)')
    is_marketing = 'bounces+' in raw[:2000] or 'sendgrid' in raw[:2000] or 'adjetter' in raw[:2000]
    return (not has_text) or is_marketing
```

## 8. Detect bounced sent emails

Gmail bounces arrive in SEPARATE threads (not threaded to the original).
Cross-reference:

```python
# Step 1: collect all bounce failed-recipient addresses
bounces_raw = gmail.users().messages().list(
    userId='me', q='from:mailer-daemon@googlemail.com ' + f'after:{int(cutoff.timestamp())}',
    maxResults=20
).execute()

bounced_addrs = set()
for m in bounces_raw.get('messages', []):
    full = gmail.users().messages().get(userId='me', id=m['id'], format='raw').execute()
    raw = base64.urlsafe_b64decode(full['raw']).decode('utf-8', errors='replace')
    info = parse_bounce(raw)
    if info['failed_recipient']:
        bounced_addrs.add(info['failed_recipient'])

# Step 2: cross-reference against sent emails
bounced_sent = [se for se in sent_emails if se['to'] in bounced_addrs]
```
