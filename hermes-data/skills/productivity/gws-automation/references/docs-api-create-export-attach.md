# Google Doc Create → Export as PDF → Attach to Email

Full workflow for creating a Google Doc in a Drive folder, writing content, exporting as PDF, and attaching to a Reply-All Gmail draft.

## Phases

### 1. Create Google Doc in Specific Folder

```python
from tools.gws_auth import build_service

drive = build_service('drive', 'v3')
docs = build_service('docs', 'v1')

folder_id = '0B1Oc8cSaJXPGVzA4bDZBN0U4c0U'  # R&D → Bangalore
doc_meta = {
    'name': '20260615_Document_Title_Summary',
    'parents': [folder_id],
    'mimeType': 'application/vnd.google-apps.document'
}
doc = drive.files().create(body=doc_meta, fields='id, name, webViewLink').execute()
doc_id = doc['id']
```

### 2. Write Content via Docs API

Use `batchUpdate` with `insertText`:
```python
full_text = """HEADING TEXT

Section 1...
Section 2...
"""

requests = [{
    'insertText': {
        'location': {'index': 1},
        'text': full_text
    }
}]
docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

**Note:** Docs API `batchUpdate` has limits. For very long documents (>10K chars), split into multiple `insertText` requests.

### 3. Export Google Doc as PDF

```python
import io
from googleapiclient.http import MediaIoBaseDownload

request = drive.files().export_media(fileId=doc_id, mimeType='application/pdf')
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()

with open('/tmp/exported_document.pdf', 'wb') as f:
    f.write(fh.getvalue())
```

### 4. Attach PDF to Reply-All Gmail Draft

```python
import base64, email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import email.encoders

# Build email with PDF attachment
msg = MIMEMultipart('mixed')
msg['To'] = 'Primary Recipient <email@example.com>'
msg['Cc'] = 'CC1 <cc1@example.com>, CC2 <cc2@example.com>'
msg['Subject'] = 'RE: Original Subject'
msg['From'] = 'Nishant Ranka <ndr@draas.com>'

# Plain text body
msg_alt = MIMEMultipart('alternative')
msg_alt.attach(MIMEText(body_text, 'plain'))
msg.attach(msg_alt)

# Attach PDF
import os
with open('/tmp/exported_document.pdf', 'rb') as f:
    pdf_data = f.read()

attachment = MIMEBase('application', 'pdf')
attachment.set_payload(pdf_data)
attachment.add_header('Content-Disposition', 'attachment', filename='Document_Summary.pdf')
email.encoders.encode_base64(attachment)
msg.attach(attachment)

# Save as draft
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw}}
).execute()
```

### 5. CRITICAL: Use `msg.as_bytes()`

DO NOT use `email.generator.Generator(BytesIO()).flatten(msg)` — raises `TypeError: a bytes-like object is required, not 'str'`.

Always use:
```python
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8').replace('+','-').replace('/','_').replace('=','')
```

### Threading (Reply-All)

To thread the reply in the same conversation:
- Keep the same Subject: prefix (`RE: `)
- Include the original recipients in To/Cc
- No `In-Reply-To` / `References` headers are needed if you're creating a draft in a different account than the original thread — the user will drag it into the correct thread manually
- Gmail groups by subject line anyway

### Pitfall — Different Gmail Account Than Original Thread

If the original email thread lives in ndr@drahomes.in but you're authenticated as ndr@draas.com:
- You cannot set `threadId` (leads to 404)
- Compose as a fresh email with same subject and all participants
- Note to user: "I couldn't link this to the original thread (different account), but the recipients and subject are the same"
- The user can drag the draft into the correct thread on their end

### Complete Session Example (Jun 2026)

This pattern was used successfully for the Premium FAR Division Bench judgment:
1. Extracted text from 5712-line legal PDF via `pdftotext`
2. Spawned 3 delegate_task agents to analyze different sections in parallel
3. Compiled findings into a comprehensive Google Doc summary
4. Exported as PDF (93KB)
5. Created Reply-All Gmail draft with PDF attachment to Smitakshi Ghosh + Viraj Majithia + 5 CC recipients
6. All paragraph-level citations from the original judgment preserved in the summary
