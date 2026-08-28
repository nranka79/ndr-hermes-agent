# Gmail Triage — Recent Inbox Review

## Overview
Check the user's Gmail for recent emails requiring action. Best practice: search last 3-5 days, categorize by urgency.

## Search Patterns

```python
from tools.gws_auth import build_service
gmail = build_service('gmail', 'v1')

# Last N days — use `after:` date format
response = gmail.users().messages().list(
    userId='me', 
    q='after:2026/06/09 before:2026/06/13',
    maxResults=50
).execute()
```

## Categorizing Emails

### Rules for classification

| Category | Criteria |
|----------|----------|
| **Action needed** | Unread + inbox + from a person (not noreply/marketing) OR subject contains action keywords |
| **Maybe review** | Unread + inbox but from less critical senders (promos, social) |
| **Info only** | Already read, noreply, social/promotions category, or clearly newsletters |

### Action keywords to scan
```
action, approve, approval, review, pending, reminder, payment, invoice, bill,
due, response, feedback, please, urgent, follow-up, follow up, sign, document,
request, confirmation, confirm, meeting, schedule, proposal, quote, order,
statement, outstanding, overdue
```

### Senders to skip as "info only"
- noreply@ / no-reply@ domains
- Google/Facebook/LinkedIn/Twitter/Instagram automated emails
- Amazon/Flipkart/Zomato/Swiggy/other transactional but non-actionable
- Pure promotions/newsletters (CATEGORY_PROMOTIONS label)

### Work emails to flag (DRAAS-specific)
```
@draas.com, @o3infotech.com, @motilaloswal.com
```
Anything from these domains in inbox is likely action-worthy even if subject seems routine.

## Metadata Extraction

```python
meta = gmail.users().messages().get(
    userId='me', id=msg['id'], format='metadata',
    metadataHeaders=['From', 'Subject', 'Date', 'To', 'Cc']
).execute()

headers = {h['name']: h['value'] for h in meta['payload']['headers']}
labels = meta.get('labelIds', [])
is_unread = 'UNREAD' in labels
is_important = 'IMPORTANT' in labels
is_inbox = 'INBOX' in labels
is_promo = 'CATEGORY_PROMOTIONS' in labels
```

## Output Format

Present to user in categorized groups with clear emoji prefixes:

```
🔴 WORK — Replies/Action Needed:
↳ Person — Subject line (brief context)

📊 Bank Alerts (for reference):
↳ Bank — type of alert

📬 Promo/Newsletters (can ignore):
↳ Sender — subject
```

## Related
- `references/email-forward-comparison-workflow.md` — After triage, forwarding with structured comparison
- `references/cron-conditional-monitor-forward.md` — Automated reply monitoring via cron

- **Bank alerts look like action items** but are usually just transactional notifications. If user doesn't complain about a specific transaction, mark as info.
- **Threaded conversations**: Multiple replies on the same thread will all appear as separate messages. Group by subject line to avoid duplicates.
- **Promos marked UNREAD**: Marketing emails often arrive as unread. Check the sender domain before flagging as action-needed.
- **DRAAS-specific threads**: Multiple people on the same project thread (e.g., Ranka Amber RERA docs) will produce several near-identical entries. Group by project name in the output.
- **User preference**: Nishant prefers concise categorized lists — don't dump raw email data. Group, summarize, and offer to open specific threads.
