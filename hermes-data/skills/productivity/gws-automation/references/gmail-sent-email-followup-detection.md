# Sent Email Follow-Up Detection

**Use when:** User wants to find emails they've sent that are awaiting replies — for follow-ups, reminders, or status tracking.

## Strategy: Thread-count + sender analysis

The best approach for Gmail API:

1. Search sent emails from the user within a date range
2. Get the thread ID for each sent email
3. Fetch the thread to count messages
4. If thread has only the sent email (count=1) → no reply
5. If thread has multiple messages, check if any are from someone other than the user

### Python implementation

```python
from tools.gws_auth import build_service
from datetime import datetime, timedelta
import base64

gmail = build_service("gmail", "v1")

def extract_body(payload):
    """Extract plain text from a Gmail message payload recursively."""
    text = ""
    if payload.get("body", {}).get("data"):
        text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            text = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            break
        if part.get("parts"):
            t = extract_body(part)
            if t:
                text = t
                break
    return text

date_from = (datetime.utcnow() - timedelta(days=15)).strftime("%Y/%m/%d")
query = f"from:user@domain.com after:{date_from}"

results = gmail.users().messages().list(userId="me", q=query, maxResults=200).execute()

awaiting_reply = []
for msg in results.get("messages", []):
    full = gmail.users().messages().get(userId="me", id=msg["id"], format="full").execute()
    headers = {h["name"]: h["value"] for h in full.get("payload", {}).get("headers", [])}
    subject = headers.get("Subject", "")
    
    # Skip auto-generated emails (attendance, daily reports, system notifications)
    auto_patterns = ["Please sign in", "Please sign out", "Daily report", "Auto-generated"]
    if any(p in subject for p in auto_patterns):
        continue
    
    # Check thread for external replies
    thread_id = full.get("threadId", "")
    thread = gmail.users().threads().get(userId="me", id=thread_id, format="full").execute()
    
    has_external_reply = False
    for tm in thread.get("messages", []):
        hdrs = {h["name"]: h["value"] for h in tm.get("payload", {}).get("headers", [])}
        sender = hdrs.get("From", "")
        if "user@domain.com" not in sender:
            has_external_reply = True
            break
    
    if not has_external_reply:
        # Get the last message Nishant sent in the thread (his final ask)
        nishant_msgs = [tm for tm in thread["messages"] 
                        if "ndr@draas.com" in str(tm) or "ndr@drahomes.in" in str(tm)]
        last_msg_body = ""
        if nishant_msgs:
            last_msg_body = extract_body(nishant_msgs[-1].get("payload", {}))
        
        awaiting_reply.append({
            "subject": subject,
            "to": headers.get("To"),
            "date": headers.get("Date"),
            "body_preview": last_msg_body[:500]  # Show the last ask for context
        })
```

## Filtering noise

- Auto-generated emails (attendance trackers, daily reports, system notifications) should be filtered out by subject/pattern
- Use `format="metadata"` for the get() call — much faster than `format="full"` and gives you all headers
- For body content analysis (checking if the email asks a question, requests a reply), use `format="full"` only after filtering candidates

## Pitfalls
- A thread may have multiple messages from the user (e.g., follow-ups they sent) without any external reply — still counts as "awaiting reply"
- Gmail's `from:` search covers the From header — use the user's primary email, not aliases
- 100-200 message limit is usually sufficient for 15 days; for longer periods, use pagination (nextPageToken)
