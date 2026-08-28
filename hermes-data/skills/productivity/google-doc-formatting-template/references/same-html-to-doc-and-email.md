# Same HTML → Google Doc + Email Pattern

## When to Use

When you need to create BOTH a formatted Google Doc AND an email body from the same content — common for appointment letters, offer letters, briefing notes, and formal correspondence where the user wants:
- A "print-quality" document saved to Drive
- An HTML email the user can review and send
- Visual consistency between the two

## Workflow

### Step 1: Write ONE Complete HTML Document

Design it as if it were a print document — full letterhead, tables, callout boxes, signature block. This HTML serves as the master source.

**Design system proven for DRAAS appointment letters (30 Jun 2026):**

| Element | Style |
|---------|-------|
| Letterhead company name | 20pt Arial Bold, `#1a3a5c`, centered, uppercase, letter-spacing 1.5px |
| Letterhead details | 7.5pt Arial, `#777`, centered |
| Letterhead bottom border | 3px solid `#1a3a5c` |
| Document title | 16pt Arial Bold, `#1a3a5c`, centered, uppercase, letter-spacing 2px |
| Section header `<h2>` | 11pt Arial Bold, `#1a3a5c`, `background:#e8edf2`, `border-left:4px solid #1a3a5c`, `padding:7px 12px`, uppercase |
| Body text | 11pt Georgia/serif, `#1a1a1a`, line-height 1.55, justified |
| Table header row | `background:#1a3a5c`, white text, 9pt Arial Bold |
| Table rows | `border-bottom:1px solid #ddd`, padding 7px 10px |
| Total rows | `font-weight:700`, `border-top:2px solid #1a3a5c`, `border-bottom:2px solid #1a3a5c`, `background:#f5f7fa` |
| Callout boxes | `background:#f8f9fb`, `border-left:3px solid #1a3a5c`, `padding:10px 14px` |
| Signature | Flex layout, two directors side by side |

**CRITICAL:** No `<ol>` or `<li>` for numbered lists — Google Docs import mangled them. Use `<ul>` with `list-style-type: disc` for bullets, and manual `<p><strong>1.</strong> text</p>` for numbered items.

### Step 2: Upload HTML as Google Doc

```python
from googleapiclient.http import MediaFileUpload
drive = build_service('drive', 'v3')

# Delete old version first
try:
    drive.files().delete(fileId=OLD_DOC_ID).execute()
except:
    pass

# Upload
media = MediaFileUpload('/path/to/master.html', mimetype='text/html', resumable=True)
body = {
    'name': 'YYYYMMDD_DescriptiveName',
    'parents': ['FOLDER_ID'],  # e.g. HR folder
    'mimeType': 'application/vnd.google-apps.document'
}
doc = drive.files().create(body=body, media_body=media, fields='id,name,webViewLink').execute()
print(f"Doc created: {doc['webViewLink']}")
```

### Step 3: Adapt Same HTML for Email Body

Create an email-specific version from the same HTML. Adaptations needed:

1. **Strip the full letterhead** — replace with a simpler `<h1>` subject line
2. **Add email-specific elements:**
   - Clickable document links with Drive share URLs
   - "Please review and sign" call-to-action box
   - Simplified signature (just the sender, not both directors)
3. **Adapt styling for email clients:**
   - Constrain width: `max-width:650px; margin:auto`
   - Use table-based layout where possible (some email clients strip flex)
   - Keep CSS inline (no `<style>` — some email clients strip `<head>`)
   - Use `#1a3a5c` for link colors
4. **Remove items that don't make sense in email:**
   - Footer disclaimer (already handled by email signature)
   - Document reference details

### Step 4: Create Gmail Draft

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64

msg = MIMEMultipart('alternative')
msg['Subject'] = 'Subject Line'
msg['From'] = 'Sender <sender@draas.com>'
msg['To'] = 'recipient@draas.com'
msg['Cc'] = 'cc@draas.com'

plain_text = """Plain text fallback version with links"""
html_part = MIMEText(email_html, 'html')
plain_part = MIMEText(plain_text, 'plain')
msg.attach(plain_part)
msg.attach(html_part)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
gmail = build_service('gmail', 'v1')
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw}}
).execute()
```

### Step 5: Share the Google Doc

```python
# Share as editor/reader to the recipient
drive.permissions().create(
    fileId=DOC_ID,
    body={'type': 'user', 'role': 'writer', 'emailAddress': 'recipient@draas.com'},
    sendNotificationEmail=False
).execute()
```

## Why Not Just Attach the Doc to the Email?

- Google Docs cannot be attached natively to Gmail (they're not files in the traditional sense)
- The user prefers Drive-share access over emailed attachments for formal documents
- The HR Policy is shared separately (viewer access, not attached) for independent sign-off
- The email body itself serves as a summary/cover note with links, not a document container

## Pitfalls

- **Email client CSS support:** `<style>` blocks in `<head>` are stripped by some email clients. Keep critical styles inline. Gmail web supports embedded `<style>` but Gmail mobile and Outlook web have different behavior. Best practice: use inline styles for layout-critical properties, `<style>` for typography/margins.
- **₹ symbol:** Use `&#8377;` HTML entity for the Rupee sign. Don't assume the raw ₹ symbol renders correctly in all email clients.
- **Doc vs email divergence:** Once the Google Doc is created and shared, don't edit the HTML email body to contain different info. The email is a cover note with links; the doc is the source of truth. If content changes, update the doc, not the email.
- **MIMEMultipart order:** Attach plain text FIRST, then HTML. Email clients that don't support HTML fall back to plain text.
