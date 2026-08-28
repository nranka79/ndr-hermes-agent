# Email Draft Pattern — Save as Gmail Draft for User Review

## When to Use

Whenever the user asks you to draft an email and does NOT explicitly say "send it" or "go ahead and send." The default workflow is: **draft → save → user reviews → user sends**.

This applies to:
- Reply-all emails on existing threads
- New emails to external parties
- Any email where the user provides content but wants to see the draft first

## Critical Rule

**Never send an email without explicit user approval.** The user has repeatedly stated: "prepare the draft and leave it in my draft, I will review there, make any corrections and send it."

Sending without approval = violating a hard user preference.

## Workflow

### 0. Threading setup (for reply-to-existing-thread emails)

When the user says "reply to the same thread" / "maintain the same thread" / "reply to all":

1. **Find the thread** — use the thread ID from the most recent message in the chain
   ```python
   thread = gmail.users().threads().get(userId='me', id=thread_id).execute()
   latest_msg = thread['messages'][-1]
   ```

2. **Get the parent Message-ID** for In-Reply-To and References headers
   ```python
   parent = gmail.users().messages().get(
       userId='me', id=latest_msg['id'],
       format='metadata',
       metadataHeaders=['Message-ID']
   ).execute()
   parent_headers = {h['name']: h['value'] for h in parent['payload']['headers']}
   parent_msg_id = parent_headers['Message-ID']
   ```

3. **Set headers and threadId on the draft**
   ```python
   msg['In-Reply-To'] = parent_msg_id
   msg['References'] = parent_msg_id
   # In the draft body:
   draft_body = {'message': {'raw': raw, 'threadId': thread_id}}
   draft = gmail.users().drafts().create(userId='me', body=draft_body).execute()
   ```

4. **Adding extra CC recipients** to a reply — add them to `msg['Cc']` alongside any existing CCs from the original thread. Gmail preserves the original To/Cc from the MIME headers when the draft is opened.

### 1. Build the MIME message

```python
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

message = MIMEMultipart('alternative')
message['To'] = 'recipient@example.com'
message['Cc'] = 'cc@example.com'
message['Subject'] = 'Subject Line Here'

# Both plain text and HTML versions
message.attach(MIMEText(body_text, 'plain'))
message.attach(MIMEText(f'<html><body>{body_html}</body></html>', 'html'))

raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
```

### 2. Handle CC recipients

Add `message['Cc']` with a comma-separated string of email addresses. Gmail's API respects the CC header in the draft — the recipients will see it when the draft is opened.

### 3. Save as draft (not send)

```python
from tools.gws_auth import build_service
gmail = build_service('gmail', 'v1')

draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw}}
).execute()

print(f"Draft saved! ID: {draft['id']}")
```

### 4. Attaching files to drafts — MIME Multipart Pattern

You **can** attach files to Gmail drafts. Build a full MIME multipart/mixed message with MIMEBase parts — the `raw` base64 payload supports attachments just like sending.

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import email.encoders, base64

message = MIMEMultipart('mixed')

# Text/HTML body (use multipart/alternative for both)
alt_part = MIMEMultipart('alternative')
alt_part.attach(MIMEText(body_text, 'plain', 'utf-8'))
alt_part.attach(MIMEText(body_html, 'html', 'utf-8'))
message.attach(alt_part)

# Attach files — one MIMEBase per file
for file_id, file_name, mime_type in files_to_attach:
    file_data = drive.files().get_media(fileId=file_id).execute()
    maintype, subtype = mime_type.split('/')
    attachment = MIMEBase(maintype, subtype)
    attachment.set_payload(file_data)
    email.encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment', filename=file_name)
    message.attach(attachment)

raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw, 'threadId': thread_id}}
).execute()
```

This works for files under Gmail's 25MB total limit. For PDFs, DWGs, and small images — all good.

### 5. Large Attachments (>25MB) — Drive Sharing + Cron Expiry

When the total attachment size exceeds Gmail's **25MB limit** (e.g., 90+ site photos at ~2MB each = 180MB):

1. **Upload files to a Drive folder** (or use existing folder)
2. **Share the folder** with specific users + "anyone with link":
   ```python
   # Specific users
   drive.permissions().create(fileId=folder_id, body={
       'type': 'user', 'role': 'reader', 'emailAddress': 'user@example.com'
   }, sendNotificationEmail=False).execute()
   
   # Anyone with link (temporary)
   drive.permissions().create(fileId=folder_id, body={
       'type': 'anyone', 'role': 'reader'
   }).execute()
   ```
3. **Include Drive folder link in email body** — list key files with individual links
4. **Add a note in the email** that the link expires on a specific date
5. **Set a cron job** to revoke "anyone with link" after expiry:
   ```python
   # Script (e.g., revoke_plans_access.py):
   drive.permissions().delete(fileId=folder_id, permissionId='anyoneWithLink').execute()
   ```
   Schedule via cronjob tool:
   ```
   cronjob(action='create', no_agent=True, schedule='YYYY-MM-DDTHH:MM:SS', script='revoke_plans_access.py')
   ```
   
   The "anyoneWithLink" permission ID is the actual Drive API permission ID for the public access grant. Specific user permissions remain intact after revocation.

### 5. Inform the user

Always tell the user:
- The draft has been saved to their Gmail Drafts folder
- Key details: To, CC, Subject
- That they can review, edit, and send from there

## User's preferred structure for external emails

- **To:** Primary recipient
- **CC:** Secondary/related parties
- **Subject:** ProjectName – Topic Description
- **Body:** Direct opening → facts/context → clear ask → polite close with name

Sign-off: "Best regards,\nNishant Ranka\nDirector, DRA Realty Private Limited"

## Direct send (after explicit user approval)

When the user explicitly says "send it", "send that draft out now", "go ahead and send", or any clear instruction to send rather than save as draft:

1. **Do NOT save as draft first.** Send directly via `users().messages().send()` with the threadId.
2. **Build the MIME message** the same way as a draft (To, Cc, Subject, In-Reply-To, References, body).
3. **Encode and send with threadId:**
   ```python
   raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
   result = gmail.users().messages().send(
       userId='me',
       body={'raw': raw, 'threadId': thread_id}
   ).execute()
   ```
4. **Verify thread attachment** — fetch the sent message and assert its `threadId` matches:
   ```python
   sent = gmail.users().messages().get(userId='me', id=result['id']).execute()
   assert sent['threadId'] == thread_id
   ```

### Decision flow

| User says | What to do |
|---|---|
| "draft this" / "prepare an email" / no clear instruction | Save as draft via `drafts().create()` — user reviews and sends |
| "send it" / "send that out" / "go ahead and send" | Send directly via `messages().send()` with threadId |
| "save as draft first" | Explicit draft request — use `drafts().create()` |
| "show me the draft" / "let me see it first" | Save as draft, then tell user to check their drafts folder |

### Multi-turn refinement pattern

When the user provides rough content that needs iterative refinement before sending:

1. **First pass** — compose a draft based on their initial instructions
2. **Present for review** — share the content in chat for feedback
3. **Incorporate corrections** — apply structural/tonal/content corrections the user provides
4. **Wait for explicit "send"** — do NOT send until the user says "send it" or equivalent. After each refinement round, re-present and wait.
5. **Send** — once user says "send", use the direct send pattern above with threadId

## Pitfalls

- **Do NOT send without explicit user approval.** Save as draft is the default. Only use `messages().send()` when the user clearly says "send."
- **Do NOT promise the user you'll send later.** Once it's a draft, it's theirs to manage.
- **CC headers must be in the MIME message, not in the API call.** Gmail's draft/send API reads To/Cc from the MIME headers.
- **ThreadId is required for reply-all sends.** Without it, the sent message starts a new thread, breaking the conversation chain.
- **Multi-turn refinement**: After each round of content correction, re-present the updated draft. Do not assume the latest round is final — wait for "send" or "looks good."
