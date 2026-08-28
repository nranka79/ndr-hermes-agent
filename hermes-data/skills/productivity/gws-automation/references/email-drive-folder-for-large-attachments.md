# Email with Drive Folder Share (for Large File Collections)

**When:** You need to send many/large files via email but they exceed Gmail's 25MB attachment limit (e.g., 90+ site photos totaling 200MB+). Or the user says "attach all files from this folder."

**Rule of thumb:** Gmail's API + MIME attachments cap at ~25MB total. Any collection of images, DWGs, or mixed-media files will almost certainly exceed this. **Do not try to attach them directly — share a Drive folder instead.**

## Hybrid Approach: Direct Attachments + Drive Folder

When the collection is too large for email but **some files are small** enough to attach, use a hybrid:

1. **Attach small files directly** — PDFs under 25MB total can be attached via MIME
2. **Share large collections via Drive folder** — photos, images, and other media go in the folder link
3. **Include individual file links** in the email body so recipients can click straight to key files

```python
import base64, email.encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase

message = MIMEMultipart('mixed')
# ... set headers as usual ...

# Attach small files directly
for file_id, file_name, mime_type in [('id1', 'doc.pdf', 'application/pdf'), ('id2', 'drawing.dwg', 'application/x-autocad')]:
    file_data = drive.files().get_media(fileId=file_id).execute()
    maintype, subtype = mime_type.split('/')
    attachment = MIMEBase(maintype, subtype)
    attachment.set_payload(file_data)
    email.encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment', filename=file_name)
    message.attach(attachment)

# For the body, include Drive links to the key files AND the full folder
dwg_link = "https://drive.google.com/file/d/<file_id>/view"
folder_link = "https://drive.google.com/drive/folders/<folder_id>"
body = f"... links to individual files + full folder link ..."
```

## Workflow

### 1. Share the Drive Folder with Recipients

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

# Grant each recipient view access
for email_addr in ['recipient@example.com', 'cc-person@example.com']:
    drive.permissions().create(
        fileId='<folder_id>',
        body={'type': 'user', 'role': 'reader', 'emailAddress': email_addr},
        sendNotificationEmail=False   # Don't spam them with notifications
    ).execute()
```

Optional: add `anyone` with link as fallback if you don't want to manage individual permissions:
```python
drive.permissions().create(
    fileId='<folder_id>',
    body={'type': 'anyone', 'role': 'reader'}
).execute()
```

### 2. Build the Reply-All Draft (on existing thread)

```python
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

message = MIMEMultipart('mixed')
message['To'] = 'sender@company.com'
message['Cc'] = 'cc1@company.com, cc2@company.com'
message['Subject'] = 'Re: Original Subject Line'
message['In-Reply-To'] = '<latest-msg-id@mail.gmail.com>'
message['References'] = '<latest-msg-id@mail.gmail.com>'

folder_link = f"https://drive.google.com/drive/folders/<folder_id>"

# Plain text body
body_text = f"""Dear Team,

[Brief message as instructed by user]

The following are available in the shared Drive folder:
- [List of file categories with descriptions]

Drive Folder Link: {folder_link}

[Closing]
"""

# HTML body (richer formatting)
body_html = f"""<html><body>
<p>Dear Team,</p>
<p>[Brief message]</p>
<ul>
<li>Category 1 — description</li>
<li>Category 2 — description</li>
</ul>
<p>Drive Folder Link: <a href='{folder_link}'>{folder_link}</a></p>
<p>[Closing]</p>
</body></html>"""

message.attach(MIMEText(body_text, 'plain'))
message.attach(MIMEText(body_html, 'html'))

raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

gmail = build_service('gmail', 'v1')
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw, 'threadId': '<thread_id>'}}
).execute()
```

### 3. Present for Approval First

Before creating the draft, always present to the user:

```
## Summary for approval

**Reply-To:** admin@company.com
**CC:** purva@company.com, rnr@draas.com
**Subject:** Re: Interior Design Firm — Scope & Requirements

**Files being shared (N files, ~X MB total):**
• AutoCAD drawing (.dwg)
• Floor Plans (FF, GF) — PDF
• Old Floor Plan — PDF
• Site photographs (N images)
• Interior Design Doc

**Body:**
[full email body text]

**Approve?**
```

Only create the draft after the user says "go ahead" or "approved."

### 4. What to Share vs What to Exclude

- Check if the user said **"except the DWG file"** or any other exclusion
- DWG files cannot be rendered in-browser so recipients may not need them if they only need PDF/JPEG
- If the user says "all content from the plans folder except the DWG" = all files minus the .dwg

## Pitfalls

- **Gmail drafts cannot attach files via the API** — the `email-draft-save-pattern.md` reference already notes this. Always use Drive sharing instead.
- **Large permission grants** — adding many individual permissions triggers rate limits. If >10 recipients, use `anyone` with link instead.
- **List what you're sharing in the email body** — recipients need to know what's in the folder without having to browse it blind.
- **Don't promise direct attachments** — if the user says "attach all files," check the total size first and explain Drive sharing if over 25MB.
- **CC already on thread** — when replying-all, the original To/CC recipients are automatically included. You only need to add extra CCs that aren't already on the thread.
- **User approval required** — always present the full summary (To, CC, Subject, Body, File list) before creating the draft. Do not create the draft in the presentation step.
