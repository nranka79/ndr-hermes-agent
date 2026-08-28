# Document Creation → Share → Notify via WhatsApp

End-to-end workflow for creating a Google Doc with structured content, setting user-specific permissions, and generating a WhatsApp notification link for the stakeholder.

Used for: architect covering letters, draft agreements, proforma documents where the recipient needs to review/edit, then the user notifies them via WhatsApp.

## Workflow

### 1. Find the Recipient's Email

When the user says an email like "v.k.bk at finding form" and you don't have it:

```python
# Search Drive for documents owned by that entity
results = drive.files().list(
    q="name contains 'Finding Form' and trashed=false",
    fields="files(id, name, owners)"
).execute()
# Check the 'owners' field for emailAddress
```

`owners[0]['emailAddress']` reveals the exact email. Common DRAAS domains: `@draas.com`, `@findingform.design`, `@gmail.com`.

### 2. Create the Google Doc in Target Folder

Always create via **Drive API** (not Docs API) so you can specify the parent folder:

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

doc_file = drive.files().create(body={
    'name': 'YYYYMMDD_Project_DocumentType_DRAFT',
    'mimeType': 'application/vnd.google-apps.document',
    'parents': [TARGET_FOLDER_ID]
}, fields='id, name, webViewLink').execute()
doc_id = doc_file['id']
```

### 3. Populate Content via Docs API

Wait ~1s after creation, then insert text:

```python
docs = build_service('docs', 'v1')
doc_info = docs.documents().get(documentId=doc_id).execute()
end_index = doc_info['body']['content'][-1]['endIndex']

docs.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': [{
        'insertText': {
            'location': {'index': end_index - 1},
            'text': FULL_CONTENT
        }
    }]}
).execute()
```

- Use `end_index - 1` to insert before the trailing newline
- For a fresh empty doc, index 1 also works

### 4. Set User-Specific Permissions (with optional expiry)

**Reader (viewer)** for the stakeholder to see:
```python
drive.permissions().create(
    fileId=FILE_ID,
    body={'type': 'user', 'role': 'reader', 'emailAddress': 'email@domain.com'},
    sendNotificationEmail=False  # Don't spam — notification goes via WhatsApp
).execute()
```

**Reader with time-limited access (1-week expiry):**
```python
from datetime import datetime, timedelta, timezone
expiry = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

drive.permissions().create(
    fileId=FILE_ID,
    body={
        'type': 'user',
        'role': 'reader',
        'emailAddress': 'recipient@domain.com',
        'expirationTime': expiry
    },
    sendNotificationEmail=False
).execute()
```

**Writer (editor)** when the stakeholder needs to edit the draft:
```python
drive.permissions().create(
    fileId=FILE_ID,
    body={'type': 'user', 'role': 'writer', 'emailAddress': 'email@domain.com'},
    sendNotificationEmail=False
).execute()
```

**Any public reader** (only when explicitly asked):
```python
drive.permissions().create(
    fileId=FILE_ID,
    body={'type': 'anyone', 'role': 'reader'}
).execute()
```

### 4a. Permission Verification — Check Existing Access

Before granting new permissions, verify what's already set:
```python
perms = drive.permissions().list(
    fileId=FILE_ID,
    fields='permissions(id, type, emailAddress, role, expirationTime)'
).execute()
for p in perms.get('permissions', []):
    print(f'{p.get("type")} - {p.get("emailAddress","")} - {p.get("role")} - expires: {p.get("expirationTime","never")}')
```

### 5. Collect and Return Links

```python
# Doc link
doc_link = f"https://docs.google.com/document/d/{doc_id}/edit"
# File link (PDFs, images, etc.)
file_link = f"https://drive.google.com/file/d/{file_id}/view"
```

Return both links to the user clearly labelled.

### 6. Generate WhatsApp Message Link

Use the `whatsapp_link` tool with a pre-filled message:

```python
whatsapp_link(
    phone=None,  # User will add the recipient's number
    text=f"""Hi [Name], I've shared two files on Google Drive for your review:

1. *Document A* (viewer access): [description]
2. *Draft Letter* (editor access): [description]

Please review and update. Thanks!"""
)
```

### 7. Hand Over the Final WhatsApp Link

Give the user:
- The Google Doc link (editor access for stakeholder)
- The supporting file link (viewer access for stakeholder)  
- The WhatsApp link to send

The user will forward the WhatsApp link (or copy the message text) to the stakeholder. Since `sendNotificationEmail=False`, the stakeholder won't get an email notification — the WhatsApp message is the notification.

## Pitfalls

- **sendNotificationEmail=False** — Always set this. The WhatsApp message IS the notification. Drive email notifications are noisy and confusing.
- **wait ~1 second** between doc creation and content insert — the doc may not be immediately writable via Docs API
- **Permission deletion removed from refs** — Don't delete existing permissions unless explicitly asked; you're adding a new user, not restricting existing access
- **No phone for WhatsApp link** — Generate the link without phone (phone=None) and let the user choose the recipient from their contacts
- **Owners array may be empty** on files you don't own — use `sharingUser` field for secondary owner info
