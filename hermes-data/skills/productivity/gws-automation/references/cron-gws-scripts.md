# Cron GWS Scripts — Service Name & Self-Healing

This reference covers a recurring pitfall: **cron jobs that call `build_service()` without an explicit `service_name` fail because there is no session context.** Unlike interactive sessions (where `HERMES_SESSION_USER_ID` + default service resolution works), cron jobs have none of that wiring — they run as a fresh Hermes invocation with no active session.

## The Two Failure Modes

### Failure 1: Missing `service_name` → `VaultNoTokenError`

**Symptom:**
```
VaultNoTokenError: No google token for user ndr-[REDACTED-TID]. Authorize first.
```

**Root cause:** `build_service('gmail', 'v1')` without a `service_name` resolves to the vault's default service key (`"google"`). In interactive sessions the session context overwrites this with the configured account's service name (e.g. `google-draas`). In cron context, the default is used — and it doesn't match any stored token.

**Fix — always pass `service_name` explicitly:**
```python
from tools.gws_auth import build_service

# ✅ Works in cron context
gmail = build_service('gmail', 'v1', service_name='google-draas')

# ❌ Fails in cron context (no session to resolve the default)
gmail = build_service('gmail', 'v1')
```

The valid service names for DRAAS are:
- `google-draas` → ndr@draas.com (primary work)
- `google-ahfl` → ndr@ahfl.in (secondary work)
- `google-gmail` → nishantranka@gmail.com (personal)

### Failure 2: Script file wiped from filesystem → `No such file or directory`

**Symptom:**
```
/opt/hermes/.venv/bin/python3: can't open file '/opt/data/scripts/cleanup-signin-emails.py': [Errno 2] No such file or directory
```

**Root cause:** Scripts placed at `/opt/data/scripts/` may not persist across container rebuilds (Docker ephemeral storage). A cron job that references the script path will fail silently until someone recreates it.

**Self-healing pattern — recreate from session history:**
```python
# When the script is missing, search session history for its code:
from hermes_tools import session_search
result = session_search(query="cleanup sign-in emails script")
# Then recreate from the recovered code with the service_name fix.
```

## Boilerplate for Cron-Ready GWS Scripts

Use this template for any GWS script that will run via cron. Key requirements:
1. **Explicit `service_name`** — never rely on the default
2. **No `dateutil` dependency** — use stdlib only (the cron environment may not have it)
3. **Trash via label, not delete** — batchModify with `TRASH` label (recoverable)
4. **Batch processing** — process in groups of 50 to avoid Gmail API rate limits

```python
#!/opt/hermes/.venv/bin/python3
"""Boilerplate cron script for GWS operations — delete/process emails.

Explicit service_name is REQUIRED in cron context (no session to resolve default).
"""
import sys, os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

# ⚠️ MUST specify service_name explicitly — cron has no session context
gmail = build_service('gmail', 'v1', service_name='google-draas')

SUBJECT = '"your subject here"'
CUTOFF = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
query = f'subject:{SUBJECT} before:{CUTOFF[:10]}'

page_token = None
total_processed = 0
batch = []

while True:
    results = gmail.users().messages().list(
        userId='me', q=query, pageToken=page_token,
        maxResults=500, fields='nextPageToken,messages/id'
    ).execute()
    msgs = results.get('messages', [])
    if not msgs:
        break
    for m in msgs:
        batch.append(m['id'])
        if len(batch) >= 50:
            gmail.users().messages().batchModify(
                userId='me',
                body={'ids': batch, 'addLabelIds': ['TRASH'],
                      'removeLabelIds': ['INBOX', 'UNREAD']}
            ).execute()
            total_processed += len(batch)
            batch = []
    page_token = results.get('nextPageToken')
    if not page_token:
        break

if batch:
    gmail.users().messages().batchModify(
        userId='me',
        body={'ids': batch, 'addLabelIds': ['TRASH'],
              'removeLabelIds': ['INBOX', 'UNREAD']}
    ).execute()
    total_processed += len(batch)

print(f'Done. Processed: {total_processed}')
```

## Cron Job Creation Notes

When creating the cron job via `cronjob(action='create', ...)`:
- The `HERMES_SESSION_USER_ID` must be set in the command prefix
- The script path must use `/opt/data/scripts/` (which may be ephemeral)
- If the script is large, embed a self-recovery instruction in the cron prompt: "if script not found, recreate from session history with session_search"

**Example cron creation pattern:**
```python
cronjob(action='create',
    name='Cleanup sign-in reminder emails',
    schedule='30 4 * * *',  # 10:00 AM IST
    prompt='Run the sign-in email cleanup script. '
           'Execute: cd /opt/data && HERMES_SESSION_USER_ID=[REDACTED-TID] '
           '/opt/hermes/.venv/bin/python3 scripts/cleanup-signin-emails.py'
)
```

## Recovery When the Cron Job Reports "File Not Found"

1. **Search session history** — `session_search(query="cleanup sign-in emails script")` to find where the script was originally written
2. **Scroll to the write event** — find the `write_file` call with the full script code
3. **Recreate the file** — `write_file(path='/opt/data/scripts/...', content=...)`
4. **Fix the service_name** — ensure `build_service()` includes `service_name='google-draas'` (or the correct one)
5. **Run it** — `terminal(command='HERMES_SESSION_USER_ID=... /opt/hermes/.venv/bin/python3 ...')`
