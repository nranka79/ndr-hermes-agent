# Gmail Attachment → Drive Upload Workflow

Download a signed document (or any attachment) from a Gmail email and upload it to a specific Drive folder, then share it — all in one script.

## Full Script Template

```python
import sys, json, os, base64
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

SERVICE_NAME = 'google-draas'  # resolve via gws_resolve_account first

# 1. Find the email with the attachment
gmail = build_service('gmail', 'v1', service_name=SERVICE_NAME)
results = gmail.users().messages().list(
    userId='me',
    q='from:sunderp_2002@hotmail.com subject:"Record of Agreed Commercial Terms"',
    maxResults=5
).execute()

msg_id = results['messages'][0]['id']
msg = gmail.users().messages().get(userId='me', id=msg_id, format='full').execute()

# 2. Find the attachment part
def find_attachment(parts):
    for p in parts:
        fn = p.get('filename', '')
        if fn and p.get('mimeType') == 'application/pdf':
            body = p.get('body', {})
            att_id = body.get('attachmentId')
            if att_id:
                return fn, att_id
        if 'parts' in p:
            result = find_attachment(p['parts'])
            if result:
                return result
    return None

payload = msg.get('payload', {})
fn, att_id = find_attachment(payload.get('parts', []))

# 3. Download the attachment
att = gmail.users().messages().attachments().get(
    userId='me', messageId=msg_id, id=att_id
).execute()
file_bytes = base64.urlsafe_b64decode(att['data'])

# 4. Save locally
local_path = '/tmp/signed_document.pdf'
with open(local_path, 'wb') as f:
    f.write(file_bytes)

# 5. Upload to Drive folder
drive = build_service('drive', 'v3', service_name=SERVICE_NAME)
media = MediaFileUpload(local_path, mimetype='application/pdf', resumable=True)
file_meta = {
    'name': f'20260716_Signed_{fn}',
    'parents': ['FOLDER_ID'],  # target Drive folder ID
    'description': 'Signed document received via email on DD MMM YYYY'
}
uploaded = drive.files().create(
    body=file_meta, media_body=media,
    fields='id,name,webViewLink,size'
).execute()

# 6. Share with specific users (viewer access)
for email in ['echamundeshwari@draas.com', 'rnr@draas.com']:
    drive.permissions().create(
        fileId=uploaded['id'],
        body={'type': 'user', 'role': 'reader', 'emailAddress': email},
        sendNotificationEmail=False
    ).execute()

print(f"Uploaded: {uploaded['webViewLink']}")
```

## Key Points

- **Use `terminal()` to run this script**, not `execute_code()` — the `.venv` has all the google API deps. Write the script to a file first, then run with:
  ```bash
  cd /opt/hermes && .venv/bin/python3 /tmp/my_script.py
  ```
- **`attachments().get()` needs BOTH `userId` AND `messageId`** — the attachmentId alone is not scoped enough
- **`base64.urlsafe_b64decode()`** — Gmail returns URL-safe base64, not standard
- **`MediaFileUpload`** from `googleapiclient.http` — use it for binary files; set `resumable=True` for >5MB
- **Description field** on Drive files — add a description with the source email date for traceability
- **`sendNotificationEmail=False`** — avoids spamming users with Drive notification emails
- **Always share the parent folder too** for discoverability (the user needs to find it again later)

## Pitfalls

- The plain-text email body is in a `text/plain` part decoded with `base64.urlsafe_b64decode(data).decode('utf-8')`
- Gmail truncates `text/plain` at ~32KB — for longer emails, use the `text/html` part or the `snippet` field
- `attachments().get()` returns `data` as a URL-safe base64 string for attachments under ~1MB; larger attachments return only an `attachmentId` — in that case, you need to call `.get()` with that ID to fetch in chunks (but for typical signed PDFs under 1MB, it's fine)
- `parents` array in Drive file_meta — this determines the folder; if omitted the file lands in root
- If the file already exists with the same name in the target folder, Drive creates a new revision — no conflict error
