# Self-Terminating Poll-and-Forward Cron Pattern

**Trigger:** "Create a cron that checks [condition] daily at [time], and when [event] happens, do [action], then stop."

## Pattern Overview

A self-terminating cron follows this lifecycle:
1. **Create** the cron job with a recurring schedule (e.g. daily at 12 PM)
2. **Each tick** checks if a condition is met (e.g. email received with attachments)
3. **If condition met:** Take action (forward, notify, archive) -> the cron session calls `cronjob(action='remove', job_id='<this-job-id>')` to self-terminate -> reports success
4. **If condition NOT met:** Stay silent - no output, no delivery

## Why Self-Termination?

The user mentally models this as "set it and forget it" - they don't want to remember to come back and kill the job. Self-removal via `cronjob(action='remove')` in the same session that detects the condition eliminates follow-up.

## Implementation

### Step 1 - Create the Cron Job
```
cronjob(
    action='create',
    name='Descriptive Name',
    prompt='''...''',
    schedule='0 12 * * *'  # daily at 12 PM UTC
)
```

### Step 2 - Craft the Prompt

The prompt must be **self-contained** - the cron session has no context from the parent conversation. Example structure:

```
Daily check: Has [Person] replied to [thread/topic]? Check Gmail for any reply from [email] with [criteria/attachments].

If a reply with [criteria] IS found:
1. [Action: forward email, save to Drive, notify, etc.]
2. Print success message saying "[description]. Job complete."
3. Then call cronjob(action='list') to find this job's ID, and cronjob(action='remove', job_id='<this-job-id>') to self-terminate.

If NO reply is found: Stay completely silent - print nothing. Do not send any message.
```

### Step 3 - Self-Removal Trick
The cron session cannot use `execute_code` (blocked for cron) and does not know its own `job_id`. Use this pattern: call `cronjob(action='list')` to find this job's ID (match by name), then `cronjob(action='remove', job_id='<found-id>')` to self-terminate.

The agent searches for its own job by name in the list output, extracts the ID, and removes itself.

## Safety Considerations

- **Self-removal can fail silently** - if the removal API call fails, the job keeps running. The prompt should print a success message BEFORE attempting removal, so at minimum the delivery confirms the action succeeded even if removal fails.
- **`cronjob(action='remove')` is allowed** - the safety rule says "cron-run sessions should not recursively schedule more cron jobs" (i.e. create new ones), but removing the current job is not scheduling and is permitted.
- **Fallback:** If self-removal is unreliable in the environment, report success to the user and let them (or the parent agent) remove the job manually.

## Verified Working Example (Jun 2026)

**Goal:** Check daily if Nilesh Prasar (Kotak Bank) replied with Kanta Ranka bank statements -> forward to Roshni -> stop.

**Schedule:** Daily at 12 PM

**Prompt:**
```
Daily check: Has Nilesh Prasar (Nilesh.Prasar@kotak.com) replied to the Kanta Ranka bank statement request thread? Check Gmail for any reply from Nilesh Prasar with Kanta Ranka statements or attachments since the last check.

If a reply with statements/attachments IS found:
1. Forward the email to Roshni Ranka (rnr@draas.com)
2. Print a success message saying "Kanta Ranka statements received and forwarded to Roshni (rnr@draas.com). Job complete."
3. Then call cronjob(action='list') to find this job's ID, and cronjob(action='remove', job_id='<this-job-id>') to self-terminate.

If NO reply is found: Stay completely silent - print nothing. Do not send any message.
```

**Result:** Ran daily at 12 PM until Nilesh replied. When matched, forwarded statements to Roshni with all 3 PDF attachments, reported success, and self-removed in the same tick.