# Gmail Forwarding via API (message/rfc822)

Forwarding an email via the Gmail API requires a different MIME structure than sending a new email. The original message must be attached as a `message/rfc822` part so Gmail displays it as a forwarded message (with the folded-paperclip icon and quoted original).

## Pattern

```python
import email
import email.mime.text
import email.mime.multipart
import email.mime.message
import base64
from email import policy

# 1. Get the original raw email
result = gmail.users().messages().get(userId='me', id=ORIGINAL_MSG_ID, format='raw').execute()
original_raw = base64.urlsafe_b64decode(result['raw'].encode('UTF-8'))
orig_msg = email.message_from_bytes(original_raw, policy=policy.default)

# 2. Build the outer message
outer = email.mime.multipart.MIMEMultipart('mixed', policy=policy.default)
outer['To'] = 'recipient@example.com'
outer['From'] = 'Your Name <you@example.com>'
outer['Cc'] = 'cc@example.com'
outer['Subject'] = 'Fwd: Original Subject Line'

# 3. Attach the new body (your message on top)
body_text = "Your message content here..."
body_part = email.mime.text.MIMEText(body_text, 'plain', 'utf-8')
outer.attach(body_part)

# 4. Attach the original email as forwarded message
# Use message/rfc822 type — this is what makes Gmail treat it as a forward
orig_attachment = email.mime.message.MIMEMessage(orig_msg, 'rfc822', policy=policy.default)
orig_attachment.add_header('Content-Disposition', 'attachment', filename='Forwarded message.eml')
outer.attach(orig_attachment)

# 5. Encode and create draft/send
encoded = base64.urlsafe_b64encode(outer.as_bytes()).decode('UTF-8')
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': encoded}}
).execute()
```

## Threading (Reply within a thread)

To create a reply that appears in the same conversation thread:

```python
# Add In-Reply-To and References headers matching the message being replied to
outer['In-Reply-To'] = '<original-message-id@mail.gmail.com>'
outer['References'] = '<parent-message-id@mail.gmail.com> <original-message-id@mail.gmail.com>'

# Pass the threadId when creating the draft
draft = gmail.users().drafts().create(
    userId='me',
    body={
        'message': {
            'raw': encoded,
            'threadId': 'THREAD_ID'  # from the original thread
        }
    }
).execute()
```

## Key Points

- **message/rfc822** is the critical MIME type — without it, the original email appears as a .eml file attachment rather than a proper forward
- `email.mime.message.MIMEMessage` wraps an already-parsed email.message object correctly as a sub-message
- The outer `MIMEMultipart('mixed')` allows both the body text and the forwarded message as separate parts
- Forwarded messages do NOT need `In-Reply-To`/`References` unless you want them in the same thread
- Use `policy=policy.default` for proper RFC compliance (line-wrapping, non-ASCII handling)
- For **new forward** (not reply), the original headers in `orig_msg` carry the sender, date, and subject — the outer message just adds your commentary on top
