# Proactive Dual-Channel: WhatsApp + Threaded Email for Record

**Trigger:** User says "send a WhatsApp message AND an email to [person] about [topic] — I want to put this on record." The user wants both channels created simultaneously, with the email specifically on an EXISTING thread for documentation purposes.

This is distinct from `cross-channel-response-conversion.md` (which handles the reactive pattern: user already responded on WhatsApp, counterparty then sent an email, convert the WhatsApp reply into an email response).

## Workflow

### Phase 1 — Understand the Record-Keeping Intent

The user explicitly wants the email to "put it on record" / "keep the old email communication chain." This means:

- **WhatsApp** = immediate notification channel
- **Email** = documentation channel, MUST be on the existing thread (Reply), NOT a new email
- Both carry the SAME content, but the email is the permanent record

The user will typically say:
- "give me a whatsapp message as well as an email to this regard because I want to put it on record"
- "try to keep the old email communication chain... let's keep the communication going, so it's all in relevant threads"

### Phase 2 — Find the Existing Thread

Search Gmail for the most relevant existing thread about THIS topic (registration, sharing agreement, etc.), not just the most recent thread from this sender. The right thread is the one that has historically discussed the specific subject matter at hand.

**Method:** Search Gmail across multiple queries:
```python
from tools.gws_auth import build_service
svc = build_service("gmail", "v1", service_name="google-draas")
results = svc.users().messages().list(
    userId='me',
    q='from:person@domain.com subject:"topic keyword"',
    maxResults=5
).execute()
```

For each result, fetch metadata to identify the thread:
```python
msg = svc.users().messages().get(
    userId='me', id=msg['id'],
    format='metadata',
    metadataHeaders=['Subject', 'From', 'To', 'Cc', 'Date']
).execute()
h = {x['name']: x['value'] for x in msg['payload']['headers']}
```

**Selection criteria for the right thread:**
1. Subject contains the topic keywords (e.g. "sharing agreement", "SSA", "registration")
2. Has the relevant participants (landlord/partner + their representatives)
3. Recent activity (within last few months — shows the conversation is live)
4. Avoid threads about unrelated topics even if from the same sender

**Pitfall — multiple threads from same sender:** The same person may have threads on different topics. Don't pick the most recent thread if it's about a different subject. Pick the one whose Subject line matches the current topic.

### Phase 3 — Derive Recipients from Thread

**Send To:** address the primary recipient (the landlord/counterparty) directly.

**CC list:** Include ALL participants from the existing thread:
- The investor/partner — the user will explicitly name them (e.g. Manohar Singh)
- Any colleague who's been part of the thread (e.g. Prakash Singh)
- Derive from the latest message's To/Cc headers, minus self

Check the latest non-self message in the thread for the most up-to-date participant list:
```python
thread = svc.users().threads().get(userId='me', id=THREAD_ID, format='metadata').execute()
for msg in reversed(thread['messages']):
    h = {x['name'].lower(): x['value'] for x in msg['payload']['headers']}
    if 'ndr@' not in h.get('from', '') and 'nishantranka' not in h.get('from', ''):
        to_parts = [a.strip() for a in (h.get('to','') or '').split(',') if a.strip()]
        cc_parts = [a.strip() for a in (h.get('cc','') or '').split(',') if a.strip()]
        break
```

### Phase 4 — Get Threading Headers for Reply

Fetch the latest non-self message's Message-ID, References, and In-Reply-To headers:

```python
latest_msg = svc.users().messages().get(
    userId='me', id=RAGHU_MSG_ID,
    format='metadata',
    metadataHeaders=['Message-ID', 'References', 'In-Reply-To']
).execute()
heads = {x['name'].lower(): x['value'] for x in latest_msg['payload']['headers']}
src_mid = heads.get('message-id', '').strip()
existing_refs = heads.get('references', '').strip()
```

Set In-Reply-To = the counterparty's Message-ID. Set References = existing References + their Message-ID.

### Phase 5 — Create WhatsApp Link

Use the `whatsapp_link` tool (never construct manually). The WhatsApp message carries the same substantive content — shorter, more direct. Send to the primary recipient's phone number (resolve via contact sheet or Gmail thread).

### Phase 6 — Create Threaded Email Draft

Build an EmailMessage with:
- `From:` = the user's work address (ndr@draas.com for DRA business)
- `To:` = the primary recipient (landlord/counterparty)
- `Cc:` = all thread participants minus self
- `Subject:` = `Re: <original thread subject>` (must match for Gmail threading)
- `In-Reply-To:` = counterparty's Message-ID
- `References:` = existing references + counterparty's Message-ID
- `threadId:` = the thread ID (EXPLICIT, not auto-detected — see Pitfall below)

Create via raw Gmail API drafts().create() with the explicit threadId in the body:
```python
draft = svc.users().drafts().create(userId='me', body={
    'message': {'raw': raw, 'threadId': THREAD_ID}
}).execute()
```

**Pitfall — `drafts().create()` may assign a WRONG threadId:** Even with correct In-Reply-To/References, Gmail may auto-assign a new threadId. Fix: pass the source threadId EXPLICITLY in the draft body and verify:
```python
assert draft['message']['threadId'] == THREAD_ID, 'Thread ID mismatch!'
```

**Verify after creation:** Check `labels: ['DRAFT']`, correct From/To/Cc/Subject, threadId matches source, In-Reply-To is set.

### Phase 7 — Deliver to User

Report both deliverables to the user in a single message:
- WhatsApp deep link (tap to open with pre-filled message — NOT sent)
- Email draft location (Drafts folder — NOT sent)
- Who was CC'd on email

## Example (Aug 2026 — Ranka Amber Registration)

**User instruction:** "Send a WhatsApp message and an email to Raghu Iyer. WhatsApp to say he needs to come register the sharing agreement. Email on the existing Ranka Amber SSA thread, CC Manohar Singh and Prakash Singh, for record."

**Thread found:** Subject "Ranka Amber – Supplementary Sharing Agreement: UDS Column Added for Review", 10 messages, active Jun–Aug 2026.

**Recipients derived:** To = Raghu Iyer (oz.iyer@gmail.com), Cc = Manohar Singh (msingh@redsoul.co.in), Prakash Singh (psingh@draas.com).

**Key content in WhatsApp + Email:**
- Sep–Dec = 4 months, target = 4 slabs construction
- Need ₹4–4.5 Cr funding — must come from bank
- Bank won't release finance without registered sharing agreement
- Request day trip — registration takes 1 day
- Pre-load documents, stamp duty, slot booking
- Ask for date confirmation