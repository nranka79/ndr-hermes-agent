# HTML → Google Doc Import & Rich Email Drafting

## Rich Google Doc from HTML

The most reliable way to create a Google Doc with preserved formatting (tables, colors, headers, links, bold/italic) is to **upload HTML and convert** via the Drive API:

```python
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', telegram_id='USER_TG_ID')
media = MediaFileUpload('file.html', mimetype='text/html', resumable=True)
body = {
    'name': 'Doc Title',
    'mimeType': 'application/vnd.google-apps.document',
    'parents': [FOLDER_ID]
}
doc = drive.files().create(body=body, media_body=media, fields='id,name,webViewLink').execute()
doc_id = doc['id']
drive.permissions().create(fileId=doc_id, body={'type': 'anyone', 'role': 'reader'}, fields='id').execute()
```

**HTML formatting that converts well:**
- `<h1>` through `<h3>` with inline `style="color: #xx; border-bottom: ..."`
- `<table>` with inline `style="border-collapse: collapse"` — `cellpadding` and `cellspacing` attributes help
- `<th>` with `style="background: #color; color: white; padding: 5px 8px"`
- `<td>` with `style="padding: 4px 8px; border: 1px solid #ccc"`
- `<div>` with `style="background: ...; border: ...; border-left: ..."` for callout boxes
- `<ul>` / `<li>` for lists
- `<b>`, `<i>`, `<a href="...">` for links
- Inline styles: `style="color: ...; font-size: ...; font-weight: bold"`

**⚠️ Known limitations (table rows get dropped):**
- Long table rows (200+ chars in a cell) with **bold spans** (`<b>` tags) mixed inside long text **AND** alternating row backgrounds (`<tr style="background: ...">`) — the entire row can be silently dropped by Google Docs import
- Fix: remove row-level `background` styles from the problematic table, and remove `<b>` tags from inside long table cell text. Keep formatting simple in large tables.
- Alternating row colors: use `cellpadding` and simple `border` instead of per-row background colors for big tables

## Email: HTML Body + PDF Attachment

Create a Gmail draft with rich HTML body and PDF attached:

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import base64

msg = MIMEMultipart('mixed')
msg['To'] = 'recipient@example.com'
msg['Cc'] = 'cc@example.com'
msg['Subject'] = 'Subject Line'

# Multipart alternative: plain text fallback + HTML
alt = MIMEMultipart('alternative')
alt.attach(MIMEText("Plain text fallback", 'plain'))
alt.attach(MIMEText(html_body_string, 'html'))
msg.attach(alt)

# Attach PDF
with open('file.pdf', 'rb') as f:
    att = MIMEBase('application', 'pdf')
    att.set_payload(f.read())
    encoders.encode_base64(att)
    att.add_header('Content-Disposition', 'attachment', filename='document_name.pdf')
    msg.attach(att)

# Send as draft
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = gmail.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
```
