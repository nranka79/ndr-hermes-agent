# Email Body Link Extraction

When a user says "there's a link in that email, can you give it to me" or "extract the link from the sign-in email":

## Workflow

1. **Find the right email** — use `format="full"` (not `format="metadata"`) to get the message body
2. **Decode the body** — walk the payload tree recursively, base64-url-decode each `body.data`
3. **Extract URLs** — regex `https?://[^\s<>"]+` to find all links
4. **Return the link** — present it clickable in Telegram

## Code Pattern

```python
from tools.gws_auth import build_service
import base64, re
from datetime import datetime, timezone

svc = build_service("gmail", "v1")
today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

# Find the email by subject/query
result = svc.users().messages().list(
    userId="me", q="subject:\"sign in\" after:..."  # adjust query
).execute()

msg = svc.users().messages().get(
    userId="me", id=result["messages"][0]["id"], format="full"
).execute()

# Decode body recursively
def decode_body(payload):
    out = []
    if payload.get("body", {}).get("data"):
        out.append(base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace"))
    for part in payload.get("parts", []):
        out.append(decode_body(part))
    return "\n".join(out)

body = decode_body(msg["payload"])
urls = re.findall(r'https?://[^\s<>"]+', body)
# urls[0] is the link you want
```

## Pitfalls

- **`format="metadata"` returns headers only** — no body, no links. Always use `format="full"`.
- **Nested MIME parts** — HTML emails have separate text/plain and text/html parts; walk recursively.
- **Short links** — use larger regex if the link may be truncated at newline boundaries.
- **Multiple links** — return all, let the user pick, or match by context (e.g. "sign in" in surrounding text).
