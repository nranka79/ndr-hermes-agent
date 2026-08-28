# WhatsApp Link via Drive HTML Page (for long messages)

**When to use:** A WhatsApp `wa.me` or `api.whatsapp.com/send` URL is too long for Telegram to transmit as a single message — it gets split across multiple messages, breaking the link.

## The Problem

Telegram has a practical message length limit. When you generate a WhatsApp link with a long pre-filled message (e.g., a list of 20 document links), the URL can exceed this limit and get truncated across messages. The recipient gets a broken link.

## The Solution

Create a simple HTML page with a WhatsApp button, upload it to a Drive temp folder, and share the Drive link instead. The HTML file renders as a clickable page in the browser.

## Workflow

### Step 1: Create the HTML page

```python
import urllib.parse

# Your long WhatsApp message
message = """Line 1 of message
Line 2 of message
...
Last line"""

encoded = urllib.parse.quote(message)
whatsapp_url = f'https://wa.me/919900093813?text={encoded}'

html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Send to [Name]</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 720px; margin: 40px auto; padding: 20px; background: #f5f5f5; }}
        .card {{ background: white; border-radius: 16px; padding: 32px; text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
        .btn {{ display: inline-block; background: #25D366; color: white; text-decoration: none; padding: 16px 40px; border-radius: 50px; font-size: 18px; font-weight: 600; }}
        .btn:hover {{ background: #1da851; }}
        .preview {{ background: #f9f9f9; border-radius: 12px; padding: 16px; margin-top: 24px; text-align: left; font-size: 13px; max-height: 300px; overflow-y: auto; border: 1px solid #eee; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>📄 [Title]</h1>
        <p>[Description of what's being shared]</p>
        <a class="btn" href="{whatsapp_url}" target="_blank">📤 Open WhatsApp → Send</a>
        <p class="note" style="font-size:13px;color:#888;margin-top:20px;">Clicking opens WhatsApp with the message pre-filled. Just hit send.</p>
        <div class="preview"><strong>Message preview:</strong><br>[brief summary of contents]</div>
    </div>
</body>
</html>'''

with open('/opt/data/send_to_person.html', 'w') as f:
    f.write(html_content)
```

### Step 2: Upload to Drive temp folder

Use the existing temp folder (ask the user or use an existing convention — do NOT create new folders unnecessarily):

```python
from googleapiclient.http import MediaFileUpload
media = MediaFileUpload('/opt/data/send_to_person.html', mimetype='text/html')
uploaded = drive.files().create(
    body={
        'name': 'Send_Docs_2_Person_via_WhatsApp.html',
        'parents': ['<existing_temp_folder_id>'],  # Use existing temp folder, don't create new
        'description': 'WhatsApp link page - click to open pre-filled message'
    },
    media_body=media,
    fields='id, webViewLink'
).execute()
```

### Step 3: Share the Drive link

```python
drive.permissions().create(
    fileId=uploaded['id'],
    body={'type': 'user', 'role': 'reader', 'emailAddress': 'ndr@draas.com'},
    sendNotificationEmail=False
).execute()

print(f'Open in Drive: {uploaded["webViewLink"]}')
```

### Step 4: Delete after use

Once the user confirms they sent the WhatsApp, delete the HTML file from Drive (and locally):

```python
drive.files().delete(fileId=uploaded['id']).execute()
import os; os.remove('/opt/data/send_to_person.html')
```

## Pitfalls

- **Don't create new temp folders** — the user already has a temp folder on Drive. Ask where to put it. Creating unnecessary folders annoys the user.
- **Message length check** — WhatsApp wa.me links have a practical limit. Messages over ~3000 chars may still fail on mobile WhatsApp. Keep the message under 2500 chars when possible.
- **Preview vs full message** — Include a brief summary in the HTML preview section so the user can quickly verify what they're about to send without counting 20 links.
- **Delete after use** — WhatsApp HTML pages are ephemeral. Once sent and confirmed, clean up immediately. Do not leave them on Drive.
- **Use api.whatsapp.com/send when user prefers it** — Some users prefer `api.whatsapp.com/send` over `wa.me`. Check user preference. The query parameters are identical; only the domain changes.
- **Ampersand rule** — The `&` character in WhatsApp query strings can break Android link parsing. Use Fullwidth `＆` (U+FF06, URL-encoded `%EF%BC%86`) when `&` is unavoidable, or replace with the word "and".
