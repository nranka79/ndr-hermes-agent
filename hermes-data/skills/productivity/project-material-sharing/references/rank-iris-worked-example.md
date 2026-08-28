# Ranka Iris — Worked Example

Concrete example of sharing Ranka Iris project materials with Harsha Naidu.
Use as reference for similar "find organize share WhatsApp" workflows.

## Search Phase

### Gmail — find emails with attachments

```python
from tools.gws_auth import build_service
import base64, io
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# Search draas.com for Iris emails
service = build_service('gmail', 'v1', service_name='google-draas')
results = service.users().messages().list(
    userId='me',
    q='Iris after:2026-02-28',
    maxResults=50
).execute()

# Get full message with attachments
msg = service.users().messages().get(
    userId='me', id=msg_id, format='full'
).execute()

# Extract attachments
def find_attachments(part, attach_list):
    if part.get('filename') and part['filename']:
        attach_list.append({
            'filename': part['filename'],
            'mimeType': part.get('mimeType',''),
            'size': part.get('body',{}).get('size',0),
            'attachmentId': part.get('body',{}).get('attachmentId',''),
        })
    if 'parts' in part:
        for p in part['parts']:
            find_attachments(p, attach_list)

attachments = []
find_attachments(msg['payload'], attachments)
```

### Drive — search for files

```python
# Files
results = drive.files().list(
    q="(name contains 'Ranka' and name contains 'Iris') and "
      "(name contains 'brochure' or name contains 'floor' or name contains 'photo')",
    fields='files(id,name,mimeType,size,webViewLink)',
    pageSize=30
).execute()

# Folders — walk tree
q3 = "name contains 'Iris' and mimeType = 'application/vnd.google-apps.folder'"
folders = drive.files().list(q=q3, ...).execute()

def list_children(folder_id, indent=2):
    q = "'{}' in parents".format(folder_id)
    results = drive.files().list(q=q, fields='files(...)').execute()
    ...
```

## Sharing Phase

### Create folder and set 30-day viewer permission

```python
folder_meta = drive.files().create(body={
    'name': 'Ranka Iris - For Harsha Naidu',
    'mimeType': 'application/vnd.google-apps.folder',
}).execute()
folder_id = folder_meta['id']

from datetime import datetime, timedelta, timezone
expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

perm = drive.permissions().create(
    fileId=folder_id,
    body={
        'type': 'user',
        'role': 'reader',
        'emailAddress': 'propcare.harsha@gmail.com',
        'expirationTime': expiry
    },
    sendNotificationEmail=False
).execute()
```

### Upload email attachments to shared folder

```python
for att in iris_attachments:
    # Download from Gmail
    attachment = service.users().messages().attachments().get(
        userId='me', messageId=msg_id, id=att['attachmentId']
    ).execute()
    file_data = base64.urlsafe_b64decode(attachment['data'].encode('utf-8'))
    local_path = '/tmp/{}'.format(att['filename'])
    with open(local_path, 'wb') as f:
        f.write(file_data)

    # Upload to Drive
    media = MediaFileUpload(local_path, mimetype=att['mimeType'], resumable=True)
    uploaded = drive.files().create(
        body={'name': att['filename'], 'parents': [folder_id]},
        media_body=media,
        fields='id,name,webViewLink'
    ).execute()
```

### Download Drive files and upload to shared folder

```python
# Files owned by others need downloading + re-uploading (can't share permissions)
for name, file_id, mime in files_to_get:
    request = drive.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    data = fh.read()
    local_path = '/tmp/{}'.format(name.replace('/', '_'))
    with open(local_path, 'wb') as f:
        f.write(data)

    media = MediaFileUpload(local_path, mimetype=mime, resumable=True)
    uploaded = drive.files().create(
        body={'name': name, 'parents': [folder_id]},
        media_body=media,
        fields='id,name,webViewLink'
    ).execute()
```

## Permissions Error Pattern

When attempting `drive.permissions().create()` on a file you don't own:

```
HttpError 400: "Bad Request. User message: Sorry, you do not have permission to share."
```

**Fix:** Download the file (get_media) and re-upload it. The copy is now yours and
inherits the folder's permissions. Do NOT try to create shortcuts — those still
require permission on the target file.

## Delivered to Harsha Naidu

- **Contact:** propcare.harsha@gmail.com / +91 9980994788
- **Folder:** Ranka Iris - For Harsha Naidu
- **Expiry:** 30 days (Sep 27, 2026)
- **Contents:** 9 photos (exterior, flat ×2, common ×2, gym ×2, balcony ×2), All Apartment Floor Plans PDF, Typical Odd Floor Plan, DHCES Even Floor Plans, Prelim Presentation, Sanction Plan
