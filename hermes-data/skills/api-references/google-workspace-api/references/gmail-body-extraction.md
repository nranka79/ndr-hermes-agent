# Gmail Body Extraction — Multipart MIME Traversal & HTML Table Parsing

When reading Gmail messages with `format="full"`, the `payload` is a nested tree of MIME parts. A simple `.get("body", {}).get("data")` on the top-level payload will miss content that lives in sub-parts.

## The Problem

Gmail's API returns multipart messages as a tree. The `payload` has a `mimeType` and may have `parts[]`. Each part can itself have `parts[]`. The actual text lives in the leaf nodes.

## Solution: Queue-Based Traversal

Use a BFS (queue) to walk all parts until you find the first text/plain or text/html leaf:

```python
from tools.gws_auth import build_service
import base64

service = build_service("gmail", "v1", service_name="google-draas")

msg = service.users().messages().get(userId="me", id=MSG_ID, format="full").execute()

# --- BFS traversal ---
parts = [msg["payload"]]
body_text = None
while parts:
    part = parts.pop(0)
    mime = part.get("mimeType", "")

    if mime == "text/plain" and part.get("body", {}).get("data"):
        body_text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
        break

    if mime == "text/html" and part.get("body", {}).get("data"):
        body_text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
        break

    # Recurse into sub-parts (multipart/alternative, multipart/mixed, etc.)
    for sub in part.get("parts", []):
        parts.append(sub)
```

### Why BFS?

- text/plain is preferred over text/html (usually listed first in multipart/alternative)
- The queue ensures you find the earliest readable part
- Handles deeply nested structures (e.g. multipart/mixed → multipart/alternative → text/html)

### Without BFS

A naive `msg["payload"]["body"]["data"]` fails silently on any non-trivial message (most sent emails are multipart). Use the queue pattern every time.

## Extracting HTML Tables from Email Bodies

When the email body is HTML with `<table>` elements containing structured data:

### Approach 1: BeautifulSoup (if available)

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(body_text, "html.parser")
tables = soup.find_all("table")
for table in tables:
    rows = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        rows.append(cells)
    # rows is now a list-of-lists, suitable for display or export
```

### Approach 2: Manual Regex (no BS4 dependency)

For simpler tables with consistent `<tr>`/`<td>` structure:

```python
import re

# Extract all table rows
rows = re.findall(r"<tr[^>]*>(.*?)</tr>", body_text, re.DOTALL | re.IGNORECASE)
data = []
for row in rows:
    cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.IGNORECASE)
    # Strip HTML tags from each cell
    cleaned = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
    data.append(cleaned)
```

**Limitations:** Regex fails on nested tables, colspan/rowspan, or malformed HTML. Prefer BS4 when available.

## Service Name Resolution

When `gws_resolve_account` is not available as a tool (tool not present in the current session), do NOT try to access it via MCP tools — Kelsa MCP tools serve Kelsa CRM, not Google auth.

**Fallback — known service names for Nishant:**

| Service Name | Account |
|---|---|
| `google-draas` | ndr@draas.com (primary / work) |
| `google-ahfl` | ndr@ahfl.in (secondary) |
| `google-gmail` | nishantranka@gmail.com (personal) |

```python
# Direct call — bypass resolution
service = build_service("gmail", "v1", service_name="google-draas")
```

For other users, check `/data/hermes/users.json` to find their Telegram ID and known accounts, or try `list_services()` from the vault client.

## Full Working Pattern: Search + Read + Extract

```python
from tools.gws_auth import build_service
import base64, re, json

service = build_service("gmail", "v1", service_name="google-draas")

# 1. Search
results = service.users().messages().list(
    userId="me",
    q="Century Regalia",
    maxResults=10
).execute()

for msg_meta in results.get("messages", []):
    # 2. Get full message
    msg = service.users().messages().get(
        userId="me", id=msg_meta["id"], format="full"
    ).execute()

    # 3. Extract headers
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    subject = headers.get("Subject", "")
    date = headers.get("Date", "")

    # 4. Extract body (BFS)
    body_text = None
    queue = [msg["payload"]]
    while queue:
        part = queue.pop(0)
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            body_text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
            break
        if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
            body_text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
            break
        queue.extend(part.get("parts", []))

    # 5. Extract tables from HTML if needed
    if body_text and "<table" in body_text:
        # Use BS4 or regex to extract table data
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", body_text, re.DOTALL | re.IGNORECASE)
        # ... process rows ...

    print(f"{subject} | {date} | Body length: {len(body_text or '')}")
```

## Pitfalls

1. **Missing `body.data` on the top-level payload** — This is normal for multipart messages. Always traverse `parts[]`.
2. **Empty body** — Some messages have only attachments with no body text. Check for `attachmentId` on parts.
3. **Base64 decoding** — Always use `base64.urlsafe_b64decode()`, not standard `base64.b64decode()`. Gmail uses URL-safe encoding.
4. **Character encoding** — Some messages use quoted-printable or 7bit content-transfer-encoding within the raw body. The Gmail API decodes these automatically when you use `format="full"` — you get the decoded `body.data` in base64.
5. **Very large bodies** — Gmail truncates bodies at ~100KB in the API response. For full content, use `format="raw"` and decode the entire RFC 2822 message.
