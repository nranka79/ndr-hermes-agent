# Email Reporting — Absorbed from productivity/email-reporting

## What This Reference Covers

Fetch Gmail messages and render them as a rich HTML report — per-email summaries, action flags, Gmail deep links, and Telegram reply shortcuts. For DRAAS users (Nishant/Roshini).

**Skill status:** Absorbed into `productivity-workflows` umbrella (2026-05-29). Original at `productivity/email-reporting/`.

## When to Use

- Daily email briefing requests
- "Summarize my emails" / "What did I receive today?"
- Email action item tracking

## Workflow

1. **Fetch message IDs** — use `gws_auth.build_service('gmail', 'v1')` (per-user OAuth, NOT SA key)
2. **Fetch full details** — `messages.get(format='full')` per ID
3. **Classify** — work | personal | security | banking | finance
4. **Build HTML report** — dark-themed, self-contained, click-to-expand cards
5. **Deliver** — `MEDIA:/tmp/email_report_{DDMMYYYY}.html` via Telegram

## Gmail API Auth Pattern

```python
from tools.gws_auth import build_service
service = build_service('gmail', 'v1')
# NOT gws_sa — per-user OAuth required for Gmail
```

## Critical Bug Fix

`google-auth ≥2.x` removed `from_authorized_user_json`. If `gws_auth.py` raises `AttributeError: type object 'Credentials' has no attribute 'from_authorized_user_json'`:
```python
# OLD (broken): creds = Credentials.from_authorized_user_json(path.read_text(), scopes)
# NEW (correct): creds = Credentials.from_authorized_user_file(path, scopes)
# Note: path is already a Path object — pass directly, NOT .read_text()
```

## Gmail Search Query Format

Use `after:YYYY/MM/DD before:YYYY/MM/DD` — **slashes, not dashes**.

## Attachment Retrieval Pattern

```python
# Step 1: Search
results = service.users().messages().list(userId='me', q='from:target@example.com').execute()
# Step 2: Get attachmentId
msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
for p in msg['payload']['parts']:
    if p.get('filename') and p.get('body', {}).get('attachmentId'):
        att_id = p['body']['attachmentId']
# Step 3: Download
att = service.users().messages().attachments().get(userId='me', messageId=msg_id, id=att_id).execute()
data = base64.urlsafe_b64decode(att.get('data', '') + '==')
```

## Related Reference Files

- `references/gmail-search-syntax.md` — Gmail search operators
- `references/case-handover-workflow.md` — Multi-year email chain analysis for case handover
