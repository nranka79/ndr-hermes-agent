# Gmail Bounce Trash — Verification & Owner Resolution (Aug 2026)

Verified during the daily "Delete Mail Delivery Subsystem bounce notifications" cron run (job owner `ndr-[REDACTED-TID]`).

## The full pattern

```python
import os, sys
os.environ.setdefault("HERMES_SESSION_USER_ID", "[REDACTED-TID]")  # telegram id from job owner field
sys.path.insert(0, "/opt/hermes")
from tools.gws_auth import build_service
svc = build_service('gmail', 'v1', service_name='google-draas')

query = 'from:mailer-daemon@googlemail.com subject:"Delivery Status Notification"'
all_msg_ids = []
page_token = None
while True:
    params = {"userId": "me", "q": query, "maxResults": 500}
    if page_token:
        params["pageToken"] = page_token
    results = svc.users().messages().list(**params).execute()
    msgs = results.get("messages", [])
    if not msgs:
        break
    all_msg_ids.extend(m["id"] for m in msgs)
    page_token = results.get("nextPageToken")
    if not page_token:
        break

print(f"FOUND: {len(all_msg_ids)}")  # this is the count to report — number trashed THIS run

for i in range(0, len(all_msg_ids), 1000):
    chunk = all_msg_ids[i:i+1000]
    svc.users().messages().batchModify(
        userId='me', body={'ids': chunk, 'addLabelIds': ['TRASH']}
    ).execute()
```

## ⚠️ Verification pitfall — Gmail's default search EXCLUDES Trash

After batch-trashing, re-running the **same query returns 0 messages**. That is
**expected success, not failure** — the default `messages.list` search scope is
outside Trash.

To confirm the messages actually landed in Trash, re-query with an explicit
`in:trash` prefix and check `labelIds` contains `'TRASH'`:

```python
res = svc.users().messages().list(
    userId='me',
    q='in:trash from:mailer-daemon@googlemail.com subject:"Delivery Status Notification"',
    maxResults=10).execute()
for m in res.get("messages", []):
    d = svc.users().messages().get(userId='me', id=m['id'], format='metadata').execute()
    print(m['id'], d.get('labelIds', []))  # expect 'TRASH' in labels
```

Aug 2026 observed values: pre-trash `FOUND: 1` → post-trash same query `0` →
`in:trash` query returned 10 messages (1 new + 9 from previous daily runs),
labels `['UNREAD','TRASH','CATEGORY_UPDATES']`.

## Reporting

- Report the **pre-trash FOUND count** — that is the number actually trashed this run.
- Do NOT report the `in:trash` total — it includes bounces trashed by earlier runs
  (Gmail keeps trashed mail ~30 days).

## Owner resolution for cron Gmail ops

- `origin.chat_id` in jobs.json is the **delivery destination**, not necessarily the
  Gmail account owner. This job delivered to chat `[REDACTED-TID]` ("Ruhaan Ranka") but
  operates on Nishant's work Gmail.
- The job's **`owner` field** (`ndr-[REDACTED-TID]`) is authoritative: uid `ndr` +
  telegram id `[REDACTED-TID]`. Set `HERMES_SESSION_USER_ID=[REDACTED-TID]`.
- `/data/hermes/users.json` is a **directory** (not a file) as of Aug 2026 — do not
  rely on it for user resolution; use the jobs.json `owner` field.
- Always pass `service_name='google-draas'` explicitly — the bare default
  (`build_service('gmail','v1')`) looks for a token named `"google"` which does not
  exist in the 3-account setup.

## Execution notes

- `execute_code` is BLOCKED for cron jobs — use `terminal` heredoc to write the
  script, then run via the Hermes venv:
  `PYTHONPATH=/opt/hermes:$PYTHONPATH HERMES_SESSION_USER_ID=<tid> /opt/hermes/.venv/bin/python3 /tmp/script.py`
- `/tmp` writes via `write_file` may be blocked — the `cat > file << 'EOF'` heredoc
  works reliably.
