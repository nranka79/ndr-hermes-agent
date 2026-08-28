# One-Shot Telegram Reminders via Cron

A recurring pattern: the user needs a single reminder at a specific time (not recurring). Use the cronjob tool with an ISO timestamp schedule to trigger a Telegram message.

## Pattern

### 1. Determine the time

Server runs in **UTC**. Convert IST (Asia/Kolkata = UTC+5:30) to UTC:

```python
# 9 AM IST = 3:30 AM UTC
# 6 PM IST = 12:30 PM UTC
```

### 2. Create the cron job

```python
cronjob(
    action='create',
    name='Human-readable name like "Call Ashwin Pai reminder"',
    schedule='2026-06-09T03:30:00',  # ISO timestamp = 9:00 AM IST
    prompt='self-contained instruction with all context: who to call, what number, what to say. Cron runs fresh with no session memory.',
    # deliver = 'origin' by default = current chat
)
```

Key parameters:
- `schedule`: ISO 8601 timestamp for one-shot (`YYYY-MM-DDTHH:MM:SS`)
- `prompt`: MUST be self-contained — cron runs in a fresh session with no access to conversation history. Include phone numbers, names, exact message text.
- `deliver`: defaults to `'origin'` (the chat that created the job). No need to set explicitly for Telegram DMs.

### 3. Verify

The job shows `repeat: "once"` and `next_run_at` in the response. Check that:
- The next_run_at UTC time matches your intended IST time (e.g., `03:30:00+00:00` for 9 AM IST)
- The job is `enabled: true` and not `paused`

## Pitfalls

- **Timezone default:** The cron scheduler accepts ISO timestamps but displays them in UTC. A `schedule='2026-06-09T09:00:00'` fires at 9 AM UTC = 2:30 PM IST unless you explicitly input UTC. **Always compute UTC equivalent** for the desired IST time.
- **Self-contained prompt:** The cron agent has NO memory of your conversation. Every detail (phone number, name, context, exact message text) must be in the prompt string. Do not assume the cron will "know" anything from the session.
- **One-shot vs recurring:** One-shot jobs auto-remove after firing. Check `repeat: "once"` in the response. Recurring jobs need a cron expression like `'0 9 * * *'`.
- **Cannot update schedule** — you can only replace it. If you set the wrong time, use `action='update'` with the same `job_id` and the corrected schedule.
