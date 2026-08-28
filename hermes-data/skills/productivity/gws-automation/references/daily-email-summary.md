# Daily Email Summary

Summarize all emails received today — categorized by action required vs FYI.

## Trigger

User asks: "summarize my emails for the day", "what came in today", "any emails I need to respond to", "daily email summary"

## Workflow

```
1. Fetch today's emails  → Gmail API (q=f'after:{today}')
2. Filter out SENT emails → exclude label 'SENT'
3. Read bodies of key emails → identify actionable ones
4. Categorize:
   🔴 Requires Action — emails needing a reply, payment, approval, or decision
   🟡 FYI / On CC — user is copied but no direct action needed
   ⚪ Info / Newsletters — promos, newsletters, bank alerts
5. Present structured summary
```

## Example Output Skeleton

```
Daily Email Summary — [Date]

🔴 Requires Action
1. [Subject] — [brief context of what needs to be done] [link]
2. ...

🟡 FYI / On CC
1. [Subject] — [brief context] [link]

⚪ Info / Newsletters
- Newsletters, promos, alerts (list)
```

## Key Points

- Read body text of potentially actionable emails to provide meaningful context
- Check if the user is on To or Cc line to determine action level
- For forwarded emails, note who forwarded and what the original was about
- Always provide Gmail links so user can open directly
- Flag undeliverable/bounce emails immediately as high priority
