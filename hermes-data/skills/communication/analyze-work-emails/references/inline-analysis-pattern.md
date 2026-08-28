# Inline Email Analysis via execute_code (Fallback Pattern)

When the terminal-based script fails (e.g. vault socket issues, missing deps, undefined functions), use `execute_code` instead with `gws_skill_bridge.call('gmail_search', ...)`.

## Key differences from terminal script

| Aspect | terminal/script | execute_code inline |
|--------|----------------|-------------------|
| Auth | `tools.gws_auth.build_service()` | `tools.gws_skill_bridge.call()` |
| Token refresh | Auto (build_service) | Auto (bridge) |
| Works in subprocess? | Yes | No (must be top-level) |
| Data format | Raw `users().messages().get()` response | Pre-parsed: `from`, `subject`, `date`, `snippet`, `labels` all included |

## Critical parameter name
`gmail_search` uses `max=N` (NOT `max_results=N`):
```python
call('gmail_search', service_name='google-draas',
    query='after:2026/07/14', max=80)
```

## Return value is a JSON STRING (verified 2026-08)
Despite the table below saying "clean dict", the bridge actually returns a
JSON-encoded **string**, and empty results come back as the literal string
`"No messages found.\n"`. Always parse defensively:
```python
raw = call('gmail_search', service_name='google-draas', query=query, max=200)
if isinstance(raw, str):
    raw = raw.strip()
    if not raw or raw.lower().startswith('no messages'):
        raw = []
    else:
        raw = json.loads(raw)
```
`gmail_get` returns a JSON string too (has a `body` key; kwarg is `message_id=X`).

## Date query format
- ✅ `after:2026/07/14` (works)
- ❌ `newer_than:2d` (returns 0 results despite valid token)
- ❌ `after:2d ago` (silently ignored by Gmail)

## All returned fields from gmail_search
`gmail_search` calls `list` + individual `get` internally and returns a clean dict per message with these keys:
- `id`, `threadId`, `from`, `to`, `subject`, `date`, `snippet`, `labels`

You do NOT need to call `gmail_get` separately unless you need the full message body.

## Priority heuristic
Use subject + snippet keywords to classify CRITICAL, HIGH, MEDIUM, NORMAL.
For AWAITING RESPONSE: check `'SENT' in labels`.

## Newsletter filtering
```python
NON_WORK_DOMAINS = [
    "noreply", "no-reply", "donotreply", "newsletter",
    "substack.com", "beehiiv.com", "economictimes.com", ...
]
```

## Related Gmail operation parameter traps

After analysis, you may need to draft replies. These GWS bridge parameter traps apply:

| Operation | Correct kwarg | Wrong kwarg (will crash) |
|-----------|--------------|-------------------------|
| `gmail_get` | `message_id=X` | `id=X` or `msg_id=X` |
| `gmail_modify` | `message_id=X` | `id=X` |
| `draft_reply_create` | `message_id=X` (ID of the message being replied to), `cc=...` for reply-all | `thread_id=X` (not accepted — function reads `message_id`) |
| `calendar_create` | `start=ISO`, `end=ISO`, `calendar='primary'`, `attendees=''` (even if empty — non-optional) | `start_time=...` / `end_time=...` |

## Thread discovery for replies

To find the last message ID in a thread for `draft_reply_create`:
```python
from googleapiclient.discovery import build
from tools.gws_auth import build_service

# Get full thread to find latest message
service = build_service('gmail', 'v1', service_name='google-draas')
# Actually, gmail_search already returns the data you need:
msgs = call('gmail_search', service_name='google-draas',
    query='subject:"Your Subject"', max=5)
# msgs[0]['id'] is the latest message in that search result
```

## Cross-references
- `gws-automation` → `references/gws-skill-bridge-gmail-operations.md` — full Gmail API bridge reference
- `gws-automation` → `references/gws-skill-bridge-draft-create.md` — draft creation parameters
