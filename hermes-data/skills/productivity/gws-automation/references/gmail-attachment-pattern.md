# Gmail Draft with PDF Attachment (MIME Multipart)

Create a Gmail draft that includes a PDF attachment (exported from Google Docs) using MIME multipart encoding.

## Workflow

```
1. Export Google Doc → PDF  (drive.files().export_media)
2. Build MIME multipart message
3. Encode as base64 → create draft
```

## Step-by-Step

### 1. Export Google Doc as PDF

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

doc_id = '1bss3lzXoUAk02xHTSIvdlOmB1-XzSlX8cH3HGImK-bU'
request = drive.files().export_media(fileId=doc_id, mimeType='application/pdf')
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()

with open('/tmp/output.pdf', 'wb') as f:
    f.write(fh.getvalue())
```

### 2. Build MIME Multipart Message with Attachment

```python
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import email.encoders

msg = MIMEMultipart('mixed')
msg['To'] = 'Recipient Name <email@example.com>'
msg['Cc'] = 'CC1 <cc1@example.com>, CC2 <cc2@example.com>'
msg['Subject'] = 'Your Subject Here'
msg['From'] = 'Nishant Ranka <ndr@draas.com>'

# Body
msg_alt = MIMEMultipart('alternative')
msg_alt.attach(MIMEText(body_text, 'plain'))
msg.attach(msg_alt)

# PDF attachment
with open('/tmp/output.pdf', 'rb') as f:
    pdf_data = f.read()

attachment = MIMEBase('application', 'pdf')
attachment.set_payload(pdf_data)
attachment.add_header('Content-Disposition', 'attachment', filename='Your_Filename.pdf')
email.encoders.encode_base64(attachment)
msg.attach(attachment)
```

### 3. Create Draft in Gmail

```python
from tools.gws_auth import build_service
import base64

gmail = build_service('gmail', 'v1')

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw}}
).execute()
print(f"Draft ID: {draft['id']}")
```

## Key Points

- Use `MIMEMultipart('mixed')` for attachments (top level) + `MIMEMultipart('alternative')` for body
- Base64 encode the attachment with `email.encoders.encode_base64()`
- For reply-all on a thread: include `In-Reply-To` and `References` headers matching the original message
- File size limit: Gmail accepts up to 25MB
- The `msg.as_bytes()` method produces proper line-wrapped base64 content
