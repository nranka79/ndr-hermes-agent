---
name: project-material-sharing
description: >-
  Share project materials (brochures, images, floor plans, docs) with external
  parties — search across Gmail + Drive for relevant files, download and
  consolidate into a shared Drive folder with expiry-based viewer access, and
  deliver a structured WhatsApp/email message with file links. Covers the
  end-to-end flow from "find the materials" to "send the links".
trigger:
  - "share [project] materials with [contact]"
  - "give [contact] access to [project] files"
  - "send [project] brochure/floor plan/images to [contact]"
  - "create a folder for [contact] with [project] docs"
  - "share everything we have on [project] with [person]"
---

# Project Material Sharing — External Deliverables Packaging

## Overview

When the user asks you to share project materials (brochures, floor plans,
images, renders, documents) with an external party, follow this pipeline:

1. **Find the materials** — search Gmail (all accounts) + Drive for relevant files
2. **Organize** — identify what's already in Drive vs what's only in email attachments
3. **Consolidate** — download email attachments, upload to a shared folder alongside Drive files
4. **Set access** — create a Drive folder, grant viewer permission with expiry (usually 30 days)
5. **Deliver** — generate a WhatsApp deep link (or draft email) with structured file listing

## Step-by-step

### 1. Search for Materials

```python
# Search Gmail across all accounts
from tools.gws_auth import build_service

# For each service you want to search:
for svc_name in ['google-draas', 'google-ahfl', 'google-gmail']:
    service = build_service('gmail', 'v1', service_name=svc_name)
    results = service.users().messages().list(userId='me', q='<search_query>', maxResults=50).execute()
```

**Queries to try:**
- `from:<sender_name> <project> after:2026-02-28` — find specific sender
- `<project> has:attachment after:2026-02-28` — find emails with files
- `<project> brochure OR "floor plan" OR images after:2026-02-28` — broad content search

For Drive, search by name and also check folder contents:
```python
q = "(name contains 'ProjectName') and (name contains 'brochure' or name contains 'floor')"
results = service.files().list(q=q, fields='files(id,name,mimeType,size,webViewLink)').execute()
```

### 2. Check What's Already in Drive

Some materials may already exist in Drive folders. Walk the folder tree to find
photos, brochures, and floor plans:

```python
def list_children(folder_id, indent=2):
    q = "'{}' in parents".format(folder_id)
    results = service.files().list(q=q, fields='files(...)').execute()
    for item in results.get('files', []):
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            list_children(item['id'], indent + 2)
        else:
            print(item['name'])
```

### 3. Download Email Attachments & Upload to Drive

When files only exist as email attachments (not in Drive), download and re-upload:

```python
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import base64, io

# Download from Gmail
attachment = service.users().messages().attachments().get(
    userId='me', messageId=msg_id, id=attachment_id
).execute()
file_data = base64.urlsafe_b64decode(attachment['data'].encode('utf-8'))

# Save locally
with open(local_path, 'wb') as f:
    f.write(file_data)

# Upload to destination folder
media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
uploaded = drive.files().create(
    body={'name': filename, 'parents': [shared_folder_id]},
    media_body=media,
    fields='id,name,webViewLink'
).execute()
```

### 4. Create Shared Folder with Expiry Permission

```python
# Create folder
folder_meta = drive.files().create(body={
    'name': 'Project Name - For Contact Name',
    'mimeType': 'application/vnd.google-apps.folder',
}).execute()
folder_id = folder_meta['id']

# Set permission with expiry
from datetime import datetime, timedelta, timezone
expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

perm = drive.permissions().create(
    fileId=folder_id,
    body={
        'type': 'user',
        'role': 'reader',
        'emailAddress': contact_email,
        'expirationTime': expiry
    },
    sendNotificationEmail=False
).execute()
```

### 5. Generate WhatsApp Message

Use the `whatsapp_link` tool with a structured message listing every file:

```
📁 Folder (all files): <folder_link>
📄 Floor Plans: <file_links>
🖼️ Photographs: <file_links>  
📑 Documents: <file_links>
```

## Pitfalls & Edge Cases

### 🔴 Permission Denied on Drive Files You Don't Own
Files in shared Drives or uploaded by another user may give:
`"Sorry, you do not have permission to share."`

**Workaround:** You cannot share permissions on files you don't own. Instead:
1. Download the file content from Drive (get_media / download)
2. Re-upload it to your newly created shared folder
3. The re-uploaded copy is now yours and inherits the folder's sharing permissions

### 🔴 Shortcuts vs Actual Files
When adding files from other locations into your shared folder, use either:
- **Uploaded copies** (recommended) — the file is physically in your folder, permissions work
- **Shortcuts** (`mimeType: application/vnd.google-apps.shortcut`) — but the target file also needs its own permission grant, which may fail if you don't own it

For reliability, always upload copies of files you don't own.

### 🔴 Large Files
For files > 10 MB, use `resumable=True` in MediaFileUpload to handle large uploads reliably.

### 🔴 WhatsApp Message Length
WhatsApp deep links can exceed Telegram's 4096-char single-message limit. The
`whatsapp_link` tool auto-splits into `parts[]` when needed. Deliver each part
as its own separate Telegram message — never combine parts.

### 🔴 Contact Resolution
Always resolve the recipient's phone/email via `contact_resolver` before sharing.
Use the project name as context for better ranking.
