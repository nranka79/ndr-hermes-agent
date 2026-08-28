# Stale-Thread Follow-Up: Email Draft + WhatsApp Ping

When the user wants to follow up on an existing email thread that received no reply, the pattern is **dual-channel with a specific split** — distinct from the "new instructions" dual-channel pattern where WhatsApp = brief and Email = full details.

## Pattern: Follow-Up on Stale Thread

**Scenario:** An email was sent W+ ago with no response. NDR wants to re-engage the recipient.

The split:
- **Email (reply draft):** Reply-all on the original thread. Full body with numbered questions asking for a status update: who spoken to, contact details, why each resource can help, current progress. This is the working document.
- **WhatsApp (ping):** Short message saying "I've sent a follow-up email on the same thread — please check it and respond urgently with the update." The WhatsApp is purely a notification/re-engagement ping.

## Workflow

### Step 1 — Find the original thread

Search Gmail with a compound query matching the recipients and topic keywords:

```python
q = 'to:anbarasan@draas.com (DTCP OR "group housing" OR subdivision OR relinquished OR OSR)'
results = svc.users().messages().list(userId='me', q=q, maxResults=10).execute()
```

Note the thread may have exactly ONE message (the original sent email) if the recipient never replied. That's normal — the threadId still exists and is valid for a threaded reply.

Always verify the mailbox identity first:
```python
profile = svc.users().getProfile(userId='me').execute()
assert profile['emailAddress'] == 'ndr@draas.com', f'WRONG: {profile["emailAddress"]}'
```

### Step 2 — Create the reply draft

Use the raw Gmail API with `EmailMessage` for threaded replies. **Always set `threadId` explicitly** in the draft body:

```python
from email.message import EmailMessage
import base64
from tools.gws_auth import build_service

svc = build_service('gmail', 'v1', service_name='google-draas')

# Get the original message's Message-ID for threading
orig = svc.users().messages().get(userId='me', id=MSG_ID, format='metadata',
    metadataHeaders=['Message-ID','References']).execute()
head = {h['name']: h['value'] for h in orig['payload']['headers']}
mid = head.get('Message-ID', '')

reply = EmailMessage()
reply.set_content(body_text)
reply['To'] = 'Anbarasan <anbarasan@draas.com>'
reply['Cc'] = 'Prakash Singh <psingh@draas.com>, "Vinod Kumar Das (Rahul)" <vkdas@draas.com>'
reply['From'] = 'Nishant Ranka <ndr@draas.com>'
reply['Subject'] = 'Re: ' + original_subject
reply['In-Reply-To'] = mid
reply['References'] = mid

raw = base64.urlsafe_b64encode(reply.as_bytes()).decode('utf-8')
draft = svc.users().drafts().create(userId='me', body={
    'message': {'raw': raw, 'threadId': THREAD_ID}
}).execute()
```

Verify the draft:
- `draft['message']['threadId']` matches the original thread
- `draft['message']['labelIds']` contains 'DRAFT'
- Check via `drafts().get()` if needed

### Step 3 — Generate WhatsApp ping

Use `whatsapp_link` tool to create a link telling the recipient about the email. Keep it short:

> Following up on my email about [topic]. I've sent you a follow-up email on the same thread — please check and urgently respond with an update. Regards, Nishant

Send the display_link to the user (their own Telegram) — they'll tap it on their phone.

### Step 4 — Present the deliverable

Tell NDR:
1. Draft created — subject, recipients (To + Cc), key questions in the body
2. WhatsApp link generated — with the phone number used
3. The draft is in his Gmail Drafts folder (link: https://mail.google.com/mail/u/0/#drafts)

## Pitfalls

- **Thread with only 1 message (the user's own sent email):** This is normal for threads the recipient never replied to. The threadId is still valid for threading.
- **WhatsApp is a deep link only:** The tool generates a link, it does NOT send a message. Tell NDR it's ready for him to tap and send.
- **Reply-All vs Reply-Sender:** Always confirm the original Cc list and reply-all unless NDR says otherwise. The follow-up context matters to everyone CC'd.
- **No body in the sent message fetch** when format='metadata': Use `messages().get(format='metadata', metadataHeaders=['...'])` — headers are in `payload.headers`. For body content, use `format='full'` and decode base64 from `payload.parts`.
