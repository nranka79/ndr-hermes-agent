# Gmail Draft in Thread — Save Draft (Not Send)

Use this workflow when the user says "save it in my reply to the draft only" or "save as draft, I will correct and send myself."

## Workflow

### 1. Find the original email
```python
from tools.gws_auth import build_service
gmail = build_service("gmail", "v1")

# Search by subject or sender
results = gmail.users().messages().list(
    userId="me", q='subject:"Ranka Iris — OC Shared"', maxResults=1
).execute()
msg_id = results["messages"][0]["id"]

# Get metadata including Message-ID and thread ID
m = gmail.users().messages().get(
    userId="me", id=msg_id, format="metadata",
    metadataHeaders=["Message-ID", "Subject", "From", "To", "Cc"]
).execute()
headers = {h["name"]: h["value"] for h in m["payload"]["headers"]}
thread_id = m["threadId"]
original_msg_id = headers.get("Message-ID", "")
```

### 2. Create the draft (threaded reply)
```python
from email.mime.text import MIMEText
import base64

msg = MIMEText("""Your reply body here""", 'plain')

# Set headers — manually include Cc from original
msg['To'] = 'ndr@draas.com'
msg['Cc'] = 'bhavik@draas.com, bhavik.92@gmail.com'
msg['Subject'] = 'Re: Original Subject'
msg['In-Reply-To'] = original_msg_id
msg['References'] = original_msg_id

# Encode
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

# Create draft in the SAME thread
draft_body = {
    'message': {
        'raw': raw,
        'threadId': thread_id
    }
}
draft = gmail.users().drafts().create(userId='me', body=draft_body).execute()
print(f'Draft created! ID: {draft["id"]}')
```

### 3. Tell the user
- Draft is in Gmail → **Drafts** folder
- It is **in the same thread** (not a new email)
- User opens, corrects, and sends

## Critical Details

- **threadId** — keeps draft in the existing conversation. Without it, draft becomes a new thread.
- **In-Reply-To / References** — ensures proper threading when sent.
- **Cc must be manually set** — Gmail API does not auto-inherit Cc from the original message.
- Use `MIMEText` for plain text; `MIMEMultipart` from `email.mime.multipart` for attachments.
- `msg.as_bytes()` — the correct encoding method. Do NOT use `email.generator.Generator`.

## User Preference (Anbu, Jun 2026)

When Anbu says "save to draft" — do NOT send. Save as Gmail Draft only. He will open the draft in Gmail, make corrections directly, then send himself. This is his preferred workflow for reviewing and polishing responses.
