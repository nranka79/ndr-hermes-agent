# Post-Send Follow-Up Draft on Same Thread

Use when the user has already sent an email themselves (manually, not via agent), and now wants you to create a follow-up reply-all draft on the **same thread**.

## Trigger

User says something like:
- "I've already sent the email. Delete the draft you created and prepare a follow-up reply-all on the same thread."
- "Send a follow-up marking Roshini and Chitra in CC to the same thread, not a new thread."
- "Reply all to the Kiran email, marking [Person A] and [Person B] just having the CC."

## Workflow Overview

```
1. Delete any previously-created draft (if one exists)
   └─ gmail.users().drafts().list() → drafts().delete()

2. Find the sent email → get threadId
   └─ Search Sent Mail: gmail.users().messages().list(q="from:me to:[recipient]")

3. Find CC recipients — they may NOT be on the sent email itself
   └─ User may have sent a separate FORWARD of the same email with the CCs
   └─ Search for the forwarded version(s) to extract CC email addresses

4. Create a reply-all draft with correct To, CC, threadId
   └─ MIMEText with In-Reply-To + References headers pointing to the sent message
   └─ CC manually set (Gmail API doesn't auto-inherit)
   └─ threadId set to keep draft in the same conversation
```

## Step-by-Step

### 1. Delete previous draft

```python
from tools.gws_auth import build_service
gmail = build_service("gmail", "v1", service_key="google-ahfl")

drafts = gmail.users().drafts().list(userId="me").execute()
for d in drafts.get("drafts", []):
    dr = gmail.users().drafts().get(userId="me", id=d["id"]).execute()
    msg = dr.get("message", {})
    headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
    print(f"Deleting draft: {d['id']} — {headers.get('Subject', 'N/A')}")
    gmail.users().drafts().delete(userId="me", id=d["id"]).execute()
```

### 2. Find sent email → extract threadId + Message-ID

```python
results = gmail.users().messages().list(
    userId="me",
    q="from:ndr@ahfl.in to:kiranpapv3@medybizpharma.com"
).execute()
sent_id = results["messages"][0]["id"]

# Get in full to extract headers + body
m = gmail.users().messages().get(userId="me", id=sent_id, format="raw").execute()
import base64
from email import message_from_bytes
msg_bytes = base64.urlsafe_b64decode(m["raw"].encode("UTF-8"))
email_msg = message_from_bytes(msg_bytes)

thread_id = m["threadId"]
sent_msg_id = email_msg["Message-ID"]
```

### 3. Find CC recipients from forwarded version

The sent email may have NO CC recipients (To-only). The user may have separately forwarded the same email to the people they want CC'd on the follow-up.

```python
# Search for the forwarded version
fwd_results = gmail.users().messages().list(
    userId="me",
    q="subject:\"Fwd: Infusion\" to:rnr@draas.com"
).execute()
if fwd_results.get("messages"):
    fwd_id = fwd_results["messages"][0]["id"]
    fwd = gmail.users().messages().get(userId="me", id=fwd_id, format="raw").execute()
    fwd_bytes = base64.urlsafe_b64decode(fwd["raw"].encode("UTF-8"))
    fwd_email = message_from_bytes(fwd_bytes)
    # Extract To recipients from the forward
    print(fwd_email["To"])  # "rnr@draas.com, charitrakamath@gmail.com"
```

### 4. Create the reply-all draft

```python
from email.mime.text import MIMEText
import base64

body = """Dear Team,

[Follow-up body text with urgency/time-bound ask]

Warm regards,
Nishant Ranka"""

msg = MIMEText(body)
msg["To"] = "kiranpapv3@medybizpharma.com"
msg["Cc"] = "rnr@draas.com, charitrakamath@gmail.com"
msg["Subject"] = "Re: Infusion Confirmation – Charitra Murjani – Updated Prescription Attached"
msg["References"] = sent_msg_id
msg["In-Reply-To"] = sent_msg_id

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("UTF-8")
draft_body = {"message": {"raw": raw, "threadId": thread_id}}
draft = gmail.users().drafts().create(userId="me", body=draft_body).execute()
print(f"Draft created: {draft['id']} in thread {thread_id}")
```

### 5. Verify

```python
d = gmail.users().drafts().get(userId="me", id=draft["id"], format="full").execute()
headers = {h["name"]: h["value"] for h in d["message"]["payload"]["headers"]}
print(f"To: {headers.get('To')}")
print(f"Cc: {headers.get('Cc')}")
print(f"Thread ID: {d['message'].get('threadId')}")
```

## Key Differences from "Save Draft Before Send" (gmail-draft-in-thread.md)

| Aspect | Save Draft (before send) | Post-Send Follow-Up |
|--------|-------------------------|---------------------|
| Trigger | "Save to draft, I'll send" | "I've already sent, now create follow-up reply" |
| Initial state | No email sent yet | Email already sent by user |
| Draft to delete | None | Delete the agent's previous draft |
| ThreadId source | From email user wanted to reply to | From user's OWN sent mail |
| CC source | From the original email being replied to | From a parallel forwarded message user sent separately |
| In-Reply-To | Original email's Message-ID | User's own sent Message-ID |
| Urgency framing | Usually no | Often has time-bound ask (e.g., "before 12pm today") |

## Pitfalls

- **CCs may not be on the sent email itself.** The user may have sent the primary email To-only, then forwarded to CC targets separately. Always check forwarded messages in the same time period.
- **threadId is on the sent message, not the draft.** Once the user sends, the draft is gone and the sent message owns the threadId. Search through sent mail.
- **service_key matters.** Use the correct secondary account key (e.g., `google-ahfl`) if the email was sent from that account. Don't default to `google` (primary).
- **User expects the draft to appear in the same thread.** Without threadId + correct In-Reply-To, the draft creates a new disconnected thread. Double-check these headers.
