# Gmail Date-Based Email Briefing

**Trigger:** User says "brief me about the mail I received on [date]" or "give me the brief about the mail from [sender/date]."

## Workflow

### Step 1 — Search by Date

Use Gmail's `after:` / `before:` syntax with the specific date:

```python
from tools.gws_auth import build_service
gmail = build_service("gmail", "v1")
results = gmail.users().messages().list(
    userId="me",
    q="after:2026/06/08 before:2026/06/09",
    maxResults=30
).execute()
```

**Format:** `after:YYYY/MM/DD before:YYYY/MM/DD` — the `before:` date should be the NEXT day to capture the full 24-hour window.

### Step 2 — Present a Scannable List

For each result, show: **Subject** (truncated ~80 chars) | **From** (truncated ~60 chars) | **To** | **Cc** | **Date**.

```python
for msg in msgs:
    m = gmail.users().messages().get(
        userId="me", id=msg["id"], format="metadata",
        metadataHeaders=["From","To","Cc","Subject","Date"]
    ).execute()
    headers = {h["name"]: h["value"] for h in m["payload"]["headers"]}
```

**Format in Telegram:**
```
Subj: {subject[:90]}
From: {from[:60]}
To: {to[:60]}
Cc: {cc[:60]}
Date: {date}
```

### Step 3 — Identify the Right Email

If there are multiple emails, let the user confirm which one. Common patterns:
- If the user gave a specific date and topic (e.g. "Ranka Iris OC"), match it against subjects
- Voice transcriptions may mangle sender names — search broadly and list all matches
- If a GWS token maps to a different user than the session user (e.g. token for vkdas@draas.com but session profile is pm2.blr@draas.com), the emails shown will belong to the token user, not the session user

### Step 4 — Fetch Full Body

Use `format='raw'` to get the full RFC822 message, then parse with `email` module:

```python
m = gmail.users().messages().get(userId="me", id=msg_id, format="raw").execute()
raw_b64 = m.get("raw", "")
raw_bytes = base64.urlsafe_b64decode(raw_b64 + "==")
mail = email.message_from_bytes(raw_bytes)
```

Extract body from `text/plain` or `text/html` parts.

### Step 5 — Present Structured Brief

Format consistently:

```
**📧 {Subject}**
**From:** {From}
**To:** {To} | **Cc:** {Cc}
**Date:** {Date}

**Brief:** {2-3 sentence summary}

{Key points in bullets}
```

**Voice name resolution pitfall:** Users may say names that don't match the email display name. "Tirtha" → Theertha A, "Aravind" → Arvind Jain. Search broadly by domain/company when the name seems off.

### Step 6 — Ask if They Want to Respond

After the brief, always offer:
- Draft a reply
- Save reply as Gmail draft (user preference)
- Take action based on email content
