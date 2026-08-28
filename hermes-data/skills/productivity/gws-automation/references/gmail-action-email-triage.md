# Gmail Action-Required Email Triage

Quick pattern to scan Gmail inbox and separate actionable emails from info-only/promotions.

## Approach

```python
gmail = build_service('gmail', 'v1')

# Get recent emails
response = gmail.users().messages().list(
    userId='me', q='after:YYYY/MM/DD', maxResults=50
).execute()

# Classify
for msg in response.get('messages', []):
    meta = gmail.users().messages().get(
        userId='me', id=msg['id'], format='metadata',
        metadataHeaders=['From', 'Subject', 'Date']
    ).execute()
    headers = {h['name']: h['value'] for h in meta['payload']['headers']}
    labels = meta.get('labelIds', [])
    
    is_unread = 'UNREAD' in labels
    is_inbox = 'INBOX' in labels
    is_promo = 'CATEGORY_PROMOTIONS' in labels
    
    # Skip promos/social unless important
    # Check subject for action keywords
    # Check if from a known person (not noreply/noreply)
```

## Classification Rules

| Category | Heuristic |
|----------|-----------|
| **Action required** | Unread + Inbox + from known person OR subject contains action keywords (action, approve, review, pending, payment, invoice, proposal, urgent, etc.) |
| **Maybe** | Unread + Inbox but no clear action keywords |
| **Info only** | Read emails, promotions, social, noreply, newsletters |

## Action Keywords

```
['action', 'approve', 'approval', 'review', 'pending', 'reminder',
 'payment', 'invoice', 'bill', 'due', 'response', 'feedback', 'please',
 'urgent', 'follow-up', 'sign', 'document', 'request', 'confirmation',
 'confirm', 'meeting', 'schedule', 'proposal', 'quote', 'order',
 'statement', 'outstanding', 'overdue']
```

## Known Senders to Filter Out

- `noreply@` / `no-reply@`
- `bankalerts@` — bank transaction alerts (usually info-only unless unusual)
- Marketing: any `@marketing.*`, `@go.*` domains
- Known newsletter domains

## Output Format

Present a **categorized bullet list** — not a flat dump. Group by project/topic when multiple emails share a thread. Lead with the WORK items, then bank alerts (for reference), then promotions (can ignore).
