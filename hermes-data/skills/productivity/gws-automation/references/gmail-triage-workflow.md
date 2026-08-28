# Gmail Inbox Triage — Identify Actionable Emails

When the user asks "show me emails that need my attention" or "find emails requiring action/reply":

## Approach

### 1. Fetch Recent Emails (past 3 days typically)

```python
from tools.gws_auth import build_service
gmail = build_service('gmail', 'v1')

response = gmail.users().messages().list(
    userId='me', q='after:2026/06/09 before:2026/06/13', maxResults=50
).execute()
```

### 2. Classify Each Email

Extract headers and labels, then classify into categories:

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

### 3. Filtering Rules

| Category | Rule | Action |
|----------|------|--------|
| **Work / Needs Action** | From a person (not noreply), in INBOX, unread OR subject has action keywords | Show first, flag urgent |
| **Maybe / Needs Review** | In INBOX, unread, but from non-critical sender | Show second |
| **Bank Alerts / Transactional** | From `bankalerts@` domains | Show for reference only, one-liner |
| **Promo / Newsletter** | CATEGORY_PROMOTIONS, or from known marketing senders | Hide (unless unread and important) |

**Action keywords in subject:** action, approve, approval, review, pending, reminder, payment, invoice, bill, due, response, feedback, please, urgent, follow-up, sign, document, request, confirmation, confirm, meeting, schedule, proposal, quote, outstanding, overdue

### 4. Known Filter Patterns

```python
# Skip these domains unless specifically asked
promo_domains = ['@marketing.', '@mail.', '@info.', '@noreply']
noreply_patterns = ['noreply', 'no-reply', 'notifications@']

# Skip promo categories (but check unread first)
if 'CATEGORY_PROMOTIONS' in labels:
    # Still show if unread AND important
    if not (is_unread and is_important):
        skip = True

# Bank alerts: always show as info/reference
bank_domains = ['bankalerts@', '@kotak.bank.in', '@hdfcbank.bank.in']
```

### 5. Output Format

Present in clean categorized groups:

```
🔴 WORK — Replies/Action Needed:
  • [Sender] — [Subject] (brief context)

📊 Bank Alerts (for reference):
  • [Bank] — [type] [amount] [date]

📬 Promo/Newsletters (can ignore):
  [list of senders, no details needed]
```

Keep each item to one line if possible. Group by project/topic when multiple replies exist on the same thread.

## Pitfalls

- **Thread grouping**: Multiple replies on the same thread from different people should be grouped under one topic heading, not listed individually.
- **Gmail category labels**: Some emails have CATEGORY_PROMOTIONS or CATEGORY_SOCIAL labels even though they're important. Always check unread+important flags before hiding.
- **Noreply exceptions**: Some noreply senders (e.g., `noreply@manipalhospitals.com`) send medical invoices that the user DOES want to see. Override the noreply rule for known medical/insurance domains.
- **Date query format**: Gmail's `after:` and `before:` use YYYY/MM/DD format, not YYYY-MM-DD.
