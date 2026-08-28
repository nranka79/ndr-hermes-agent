# gws_skill_bridge Gmail Operations — kwarg/arg-name mismatch trap

**Status:** Working pattern, confirmed Jul 2026. Complements `gws-skill-bridge-drive-operations.md` and `gws-skill-bridge-draft-create.md`.

## What the bridge does (recap)

`tools.gws_skill_bridge.call(operation, **kwargs)` wraps kwargs into a `SimpleNamespace` and passes it to the skill function. The skill reads `args.<name>` — so your kwarg name IS the attribute name. The Drive and Draft bridges have well-known `AttributeError: 'SimpleNamespace' object has no attribute 'X'` traps; **Gmail ops have the same traps but no existing reference doc**.

## Operations & the kwarg names that ACTUALLY work

Discovered empirically by reading `/data/hermes/skills/productivity/google-workspace/scripts/google_api.py` and confirming the `AttributeError` traces.

| Operation | Working kwargs | What bit me |
|---|---|---|
| `gmail_search` | `query=...`, `max=...` | First call tried `max_results=20` → `AttributeError: ... has no attribute 'max'`. The skill reads `args.max`. |
| `gmail_get` | `message_id=...`, `format=...` | First call tried `id=msg_id` → `AttributeError: ... has no attribute 'message_id'`. The skill reads `args.message_id`. `format` is optional, default works. |
| `gmail_labels` | none | No required args. |
| `gmail_modify` | `message_id=...`, `add_labels=...`, `remove_labels=...` | First call tried `id=msg_id` → same `message_id` requirement. |
| `draft_create` | `to=...`, `subject=...`, `body=...`, `from_=...` (note trailing underscore), `cc=...`, `bcc=...`, `html=...` (NOT `html_body`) | See `gws-skill-bridge-draft-create.md` for full details. |
| `draft_reply_create` | `message_id=...`, `body=...`, `from_=...` | Bridges threading automatically. |

**Blocklisted operations:** `gmail_send` and `gmail_reply` always raise `PermissionError`. Use `draft_create` and `draft_reply_create` instead.

## Working Gmail search recipe

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_skill_bridge import call

# Subject search — use Gmail search syntax
result = call("gmail_search", service_name="google-draas",
              query='subject:"Millers Road India Chai Office Building"',
              max=20)
print(result)  # JSON array of {id, threadId, from, to, subject, date, snippet, labels}
```

**`max` is required.** Without it, the bridge crashes before even hitting the API. Default of 10 doesn't auto-apply.

## Working Gmail get recipe

```python
result = call("gmail_get", service_name="google-draas",
              message_id=msg_id, format="full")
data = result  # JSON string, parse with json.loads()

# JSON shape:
# {"id", "threadId", "from", "to", "subject", "date", "labels", "body"}
```

**Critical: the body returned is plain text only** (Gmail's `text/plain` part, decoded). HTML body is stripped. For HTML you need to use the raw Gmail API via `build_service` directly:

```python
from tools.gws_auth import build_service
import base64

gmail = build_service('gmail', 'v1', service_name='google-draas')
msg = gmail.users().messages().get(userId='me', id=msg_id, format='full').execute()

def extract_body(parts, mime='text/plain'):
    out = ''
    for p in (parts or []):
        if p.get('mimeType') == mime:
            data = p.get('body', {}).get('data', '')
            if data:
                out += base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        if 'parts' in p:
            out += extract_body(p['parts'], mime)
    return out

plain = extract_body(msg['payload'].get('parts', []), 'text/plain')
html  = extract_body(msg['payload'].get('parts', []), 'text/html')
```

## Working Gmail modify recipe

```python
# Mark as read
call("gmail_modify", service_name="google-draas",
     message_id=msg_id, remove_labels="UNREAD")

# Move to spam
call("gmail_modify", service_name="google-draas",
     message_id=msg_id, add_labels="SPAM", remove_labels="INBOX")

# Bulk modify — loop, no batch endpoint
for mid in message_ids:
    call("gmail_modify", service_name="google-draas",
         message_id=mid, remove_labels="UNREAD")
```

## Date filters and search syntax

Use full Gmail search operators — same as the web UI:

| Operator | Example |
|---|---|
| `from:` | `from:akber@ahindia.com` |
| `to:` | `to:ndr@draas.com` |
| `subject:` | `subject:"Millers Road"` (quoted for multi-word) |
| `newer_than:` | `newer_than:30d` |
| `older_than:` | `older_than:1y` |
| `has:attachment` | `has:attachment filename:pdf` |
| `is:unread` | `is:unread is:important` |
| `label:` | `label:ahfl` (per-account forwarded label) |
| `in:` | `in:anywhere` (includes spam/trash) |
| `OR` / `AND` | `from:akber OR from:atheeq` |

Combine with parentheses: `subject:"Millers Road" (from:akber OR from:atheeq) newer_than:60d`

## Service-name trap for multi-account users (Nishant)

| Gmail account | service_name |
|---|---|
| ndr@draas.com (primary work) | `google-draas` |
| ndr@ahfl.in (secondary work) | `google-ahfl` |
| nishantranka@gmail.com (personal) | `google-gmail` |

Always pass `service_name` explicitly. The bridge default is `google-draas` which is correct for Nishant's primary account but wrong if he's asked you to check a different one.

## Common failure modes

1. **`AttributeError: ... has no attribute 'max'`** — forgot to pass `max=...` to `gmail_search`. Always pass it.
2. **`AttributeError: ... has no attribute 'message_id'`** — passed `id=...` instead of `message_id=...` to `gmail_get` or `gmail_modify`.
3. **Empty results when results should exist** — wrong `service_name`. The bridge default is `google-draas`. If the email is on a different account, switch with `service_name="google-ahfl"` etc.
4. **PermissionError for `gmail_send`** — blocked by design. Use `draft_create` to stage the email for human review.
5. **Token errors** — see `references/gws-auth-post-authorization-diagnostics.md` for the vault-vs-resolver diagnostic flow.

## Cross-references

- `gws-skill-bridge-drive-operations.md` — same kwarg/arg-name trap for Drive ops
- `gws-skill-bridge-draft-create.md` — same trap for `draft_create` (note `from_` trailing underscore and `html` not `html_body`)
- `gws-auth-post-authorization-diagnostics.md` — what to do when vault says token is missing
- `gmail-thread-reply-pattern.md` — sending a reply to an existing thread (uses `draft_reply_create` with `threadId` from the original)
