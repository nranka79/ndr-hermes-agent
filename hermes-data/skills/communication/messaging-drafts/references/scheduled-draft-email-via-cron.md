# Scheduled Draft Email via Cron + Calendar Reminder

Create a calendar reminder event + cron job that auto-creates a draft email on a future date.

**Trigger:** "Set a reminder for [date/time] to send an email to [person] about [topic]"

## Workflow

1. **Parse the schedule** — Identify:
   - Calendar event date (the actual event/reminder date, e.g. "next week Thursday")
   - Email send date and time (may be the day before the event, e.g. "Wednesday 9 PM" for a Thursday event)
   - Recipient, topic, and email body content

2. **Create calendar event(s)** — Use `gws_skill_bridge.call('calendar_create', ...)` for each reminder. These serve as the user's visual reminder in Google Calendar.

   **Required bridge parameters** (all are required or the bridge crashes with AttributeError):
   ```python
   from tools.gws_skill_bridge import call
   call('calendar_create', service_name='google-draas',
        summary='🔔 [Topic]',
        start='YYYY-MM-DDTHH:MM:00+05:30',
        end='YYYY-MM-DDTHH:MM:00+05:30',
        description='[details]',
        location='',        # MUST pass empty string
        attendees='',       # MUST pass empty string
        calendar='primary') # MUST pass 'primary'
   ```

3. **Create cron job(s)** for the automated draft — Use the `cronjob` tool with:
   - `schedule`: ISO timestamp **in UTC** (convert from IST: IST - 5h30m = UTC. Example: 9 PM IST = 15:30 UTC, 9 AM IST = 03:30 UTC)
   - `prompt`: Self-contained instructions for the cron agent to create a draft email via gws_skill_bridge (the cron agent has NO prior conversation context)
   - `enabled_toolsets`: `["terminal"]` (terminal access is needed for the bridge)
   - `deliver`: `"origin"` (notify the user when the cron fires)

## Cron Prompt Structure

The cron job prompt must be **completely self-contained** — the cron agent has no memory of prior conversations:

```
Create a draft email in Nishant Ranka's Gmail (ndr@draas.com) and notify him on Telegram.

DRAFT EMAIL DETAILS:
- To: [Full Name <email>]
- Subject: [Subject line]
- Body:
[Full email body]

INSTRUCTIONS (call these directly at the top level, NOT through a nested subprocess):
1. Import: from tools.gws_skill_bridge import call
2. Call: call('draft_create', service_name='google-draas', to='[Full Name <email>]', subject='[Subject]', body='[Body]')
3. Print the draft ID in your response.

Your final response will be delivered to Nishant on Telegram.
```

## UTC/IST Conversion Table

| IST | UTC | Common Use |
|-----|-----|------------|
| 9:00 AM | 03:30 | Morning follow-up |
| 9:00 PM | 15:30 | Evening reminder email |

## Pitfalls

- **Cron schedule in UTC**: The cronjob tool's `schedule` parameter is interpreted as UTC. Always convert IST to UTC (IST = UTC + 5:30). If you set the schedule without converting, the email fires 5.5 hours early.
- **Bridge parameters**: `calendar_create` requires `location=""`, `attendees=""`, AND `calendar="primary"` — omitting any causes AttributeError because the bridge's SimpleNamespace doesn't have defaults.
- **Cron agents have no memory**: Every correction, name spelling, email address, and tone preference must be embedded in the cron prompt itself. The cron job does not inherit your session context.
- **Drafts only**: The cron job creates a DRAFT email (via `draft_create`), not a sent message. The user must review and send from Gmail Drafts. The hard rule against autonomous sending applies to cron agents too.
- **One-shot vs recurring**: When the user says "send an email on [date]" without saying "every week", use a one-shot cron job (ISO timestamp schedule). The cronjob tool defaults to `repeat='once'` for ISO timestamps.
- **Manohar's Kelsa email**: Confirmed (Jul 2026) — all Kelsa-related emails to Manohar Singh go to `msingh@kelsa.io`, not his other addresses (`msingh@o3infotech.com`, `msingh@ircaindia.com`).
