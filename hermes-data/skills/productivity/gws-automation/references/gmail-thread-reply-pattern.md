# Gmail Thread Reply Pattern

**Pattern:** User says "reply to that email thread" — send a new message as part of an existing Gmail thread so all participants see it in-context.

## Steps

### 1. Identify the thread

Find any message in the thread via Gmail search. All messages sharing the same subject line (with Re:/Fwd:) and conversation history share a `threadId`:

```python
from tools.gws_auth import build_service
service = build_service('gmail', 'v1')

result = service.users().messages().list(
    userId='me',
    q='subject:"BESCOM Power Supply Update" from:pm2.blr@draas.com',
    maxResults=5
).execute()
thread_id = result['messages'][0]['threadId']  # Shared across all replies
```

### 2. Compose and send with `threadId`

```python
import base64
from email.message import EmailMessage

msg = EmailMessage()
msg['To'] = 'Recipient Name <email@example.com>'
msg['Cc'] = 'Other Recipient <other@example.com>'
msg['Subject'] = 'Re: Original Subject Line'  # Must match thread subject
msg['From'] = 'Sender Name <ndr@draas.com>'
msg.set_content('''
Email body here.
''')

encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

result = service.users().messages().send(
    userId='me',
    body={
        'raw': encoded,
        'threadId': thread_id  # ← This is the key parameter
    }
).execute()
print(f'Sent! Message ID: {result["id"]}')
```

### 3. Key requirements

- **`threadId`** must be correct — it links the new message into the existing conversation in Gmail's UI
- **Subject** should match the thread's current subject (using `Re:` prefix) — Gmail threads by subject + message-id chain
- **`To`/`Cc`** — include the people who should see it. The message appears in the thread regardless, but they won't get a notification unless addressed or already subscribed
- **`From`** — must be the authenticated user's address (can be an alias if configured in Gmail)
- **No need for `In-Reply-To` or `References` headers** — `threadId` in the API body is sufficient to attach to the correct thread

### Worked example (Jun 2026 — BESCOM thread)

A 5-message thread existed (Anbu → Nishant → Eshwari) under threadId `19ecba31eaea93ca`. A new urgent reply was sent with:

```python
msg['To'] = 'Anbarasan M <anbarasan@draas.com>, Anbarasan M <pm2.blr@draas.com>'
msg['Cc'] = 'Eshwari Chamundeshwari <echamundeshwari@draas.com>, Bhavik Ranka <bhavik@draas.com>'
msg['Subject'] = 'Re: BESCOM Power Supply Update - Ranka Iris / Project Status'

body = {
    'raw': encoded,
    'threadId': '19ecba31eaea93ca'
}
```

Delivery verification:
```python
sent = service.users().messages().get(userId='me', id=sent_id).execute()
assert sent['threadId'] == original_thread_id  # Confirms thread attachment
```

## Pitfalls

- **Multiple threads with the same subject** — Gmail's subject-based search can return messages from different threads that share a subject line. When `messages().list()` returns results with different `threadId` values, scroll through the latest message from each to find the one whose participants match the conversation. Always verify you're using the threadId from the correct message (most recent reply in the right chain).
- **Non-existent `threadId`** — Gmail API returns success but creates a new thread (orphaned). Always verify by fetching the sent message and checking its `threadId`.
- **Subject mismatch** — if the subject doesn't match the thread, Gmail may start a new conversation even with the correct threadId. Use `Re: <exact subject>`.
- **Alias sends** — if sending from `ndr@drahomes.in` (alias) while authenticated as `ndr@draas.com`, the email is sent from the alias address but Gmail may break the thread. Prefer the primary authenticated address unless the user explicitly requests the alias.
- **Duplicate delivery** — `To` and `Cc` recipients get the email; anyone already on the thread sees it in their inbox. Avoid adding people who shouldn't be notified.
