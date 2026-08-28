# Gmail Query Syntax Quick Reference

Consult this card before writing any `q=` parameter for the Gmail API.

## Date Filters — THE MOST COMMON ERROR

| ✅ Correct | ❌ Wrong | Notes |
|---|---|---|
| `newer_than:2d` | `after:2d ago` | `newer_than:Nd` is the RIGHT operator for relative dates |
| `after:2026/06/29` | `after:29/06/2026` | `after:` takes YYYY/MM/DD with forward slashes |
| `before:2026/07/01` | `before:2d` | `before:` also takes YYYY/MM/DD — not relative |
| `older_than:7d` | `older:7d` | Full operator is `older_than:Nd` |

**Why this matters:** Invalid query syntax like `after:2d ago` is **silently ignored** by Gmail — it returns ALL messages matching the other criteria, with no date filter applied. You won't get an error, just wrong results.

## Quick Operator Reference

### Scope
- `in:inbox` — Inbox only
- `in:sent` — Sent messages
- `in:anywhere` — All mail including spam/trash
- `in:spam` / `in:trash`

### Sender/Recipient
- `from:user@example.com` — From this sender
- `to:user@example.com` — To this recipient
- `cc:user@example.com` — CC'd
- `bcc:user@example.com` — BCC'd

### Subject/Body
- `subject:"exact phrase"` — In subject line (quotes for exact match)
- `subject:(word1 word2)` — All words in subject
- `"exact body text"` — Exact phrase in body

### Attachments
- `has:attachment` — Has any attachment
- `filename:pdf` — Has PDF attachment
- `filename:invoice.pdf` — Attachment with specific name

### Flags
- `is:unread` / `is:read`
- `is:starred`
- `is:important` / `label:important`
- `is:snoozed`

### Labels
- `label:invoices` — Messages with this label
- `label:^smartlabel_receipt` — Auto-category (receipts, etc.)

## Common Combinations

```
# Last week's unread from a specific person
is:unread newer_than:7d from:raghu@example.com

# Recent sent emails with attachments (the user sent)
in:sent newer_than:2d has:attachment

# Find threads about a project in a date range
subject:"Premium FAR" after:2026/06/01 before:2026/07/01

# Exclude automated emails
-from:alerts@ -from:noreply@ -from:newsletter@

# OR groups — use curly braces
{from:alice@example.com from:bob@example.com}
```

## Decision Tree

Need to filter by date?
└── Is it relative? (e.g. "last 2 days", "past week")
    └── Use `newer_than:Nd` or `older_than:Nd`
└── Is it specific dates? (e.g. "June 29 to July 1")
    └── Use `after:YYYY/MM/DD` and `before:YYYY/MM/DD`

## Pitfall — Forwarded Old Emails

Emails forwarded from ndr@drahomes.in to ndr@draas.com land as new messages with today's receipt date. The `newer_than:` filter catches BY RECEIPT DATE, not original send date. An email from 2025 forwarded today matches `newer_than:2d`.

**Fix:** Always validate the `Date` header server-side:
```python
import email.utils
from datetime import datetime, timezone

sent_date_str = headers.get("Date", "")
if sent_date_str:
    parsed = email.utils.parsedate_to_datetime(sent_date_str)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    days_ago = (now - parsed).days
    if days_ago > N:
        skip = True  # old forwarded email
```

## Max Results

Gmail API default is 100, max is 500. For full inbox scans, paginate with `pageToken`.
