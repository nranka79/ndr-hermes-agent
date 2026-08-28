# Cron — Conditional Monitor & Forward

Pattern: Set up a daily cron job that monitors Gmail for a specific reply (e.g., bank statements from a contact), forwards it to a recipient when found, and then self-terminates.

## When to Use

- You've sent a request and are waiting for a reply with attachments (bank statements, documents, etc.)
- The reply needs to be forwarded to someone else automatically
- You don't want to manually check daily

## Setup

### 1. Create the cron job

```bash
cronjob(
    action='create',
    name='Kanta Ranka Statements - Check & Forward',
    schedule='0 12 * * *',        # Daily at 12:00 PM (UTC) = 5:30 PM IST
    prompt='''Daily check: Has [sender] replied to [topic] request thread?
Check Gmail for any reply from [sender email] with [topic/or attachments].

If a reply with statements/attachments IS found:
1. Forward the email to [recipient email]
2. Print a success message saying "... Job complete."
3. Self-terminate: cronjob(action='list') to find this job's ID, 
   then cronjob(action='remove', job_id='<this-job-id>')

If NO reply is found: Stay completely silent. Print nothing.'''
)
```

### 2. The prompt design

Key principles for the prompt:

- **Self-contained** — the cron has no chat context; everything must be in the prompt
- **Binary outcome** — either forward + report + terminate, or stay silent (no notification = nothing happened)
- **Explicit search query** — include the sender email, subject keywords, and date range
- **Self-termination logic** — instruct the agent to `cronjob(action='list')` → find itself → `cronjob(action='remove', ...)`

### 3. Self-termination approaches

| Approach | How it works | Risk |
|----------|-------------|------|
| **Option A: Manual removal** | Cron reports success to user, then user asks agent to remove it | Low — reliable, user sees confirmation |
| **Option B: Self-removal** | Cron removes itself via `cronjob(action='remove')` after forwarding | Medium — if removal call fails silently, job keeps running |

Option A is recommended for reliability. Option B works when the prompt explicitly instructs:
```
# After forwarding:
cronjob(action='list')  # find job_id
cronjob(action='remove', job_id='<id>')  # remove self
```

### 4. Pitfalls

- **Time zone mismatch:** Cron schedule is in UTC. `0 12 * * *` = 12:00 UTC = 5:30 PM IST. For 12:00 PM IST, use `30 6 * * *` (6:30 UTC)
- **Silent until success:** The user won't hear anything until the reply is found. This is intentional — don't make it report "nothing found today" or it becomes noise
- **Reply threading:** The sender might reply to a different thread. Use a broad search that catches any email from the sender to the user about the topic
- **Attachment detection:** Check if the reply has attachments (`parts` with `filename`), not just the reply text — statements need PDF/XLSX attachments
- **Forwarded email format:** When forwarding via Gmail API, include the original email's `Message-ID` in `In-Reply-To` and `References` headers to maintain thread continuity for the recipient

### 5. Concrete example (Jun 2026 — Nilesh Prasar/Kanta Ranka)

**Scenario:** Nishant requested Kanta Ranka bank statements from Nilesh Prasar (Kotak Bank). No reply received. A follow-up was sent on 13 Jun.

**Cron setup:**
- Schedule: `0 12 * * *` (daily 12 PM UTC / 5:30 PM IST)
- Checks for any reply from Nilesh.Prasar@kotak.com with Kanta Ranka statements
- If found: forwards to Roshni Ranka (rnr@draas.com), reports success
- If not found: stays silent
- Termination: Option A (manual removal on success report)

**Gmail query for the check:**
```
from:Nilesh.Prasar@kotak.com subject:Kanta OR subject:Ranka OR subject:statement
```
