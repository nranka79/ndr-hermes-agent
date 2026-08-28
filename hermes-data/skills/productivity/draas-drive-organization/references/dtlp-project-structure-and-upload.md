# DTLP Project Structure & Upload Workflow

## DRA Thindulu Land Partners (DTLP) — Folder Taxonomy

DRA Thindulu Land Partners (DTLP) projects follow a numbered-subfolder taxonomy:

```
DRA Thindulu Land Partners (DTLP)/
├── [Project Name e.g. Ranka Udaya]/
│   ├── 01_Title_and_Legal_Opinions
│   ├── 02_Approvals
│   ├── 03_Marketing_Collaterals
│   ├── 04_Sanction_Drawings
│   ├── 05_Execution_Documents_and_Drawings
│   └── 06_Customer_Documents
```

**Marketing Collaterals** (03_Marketing_Collaterals) is where marketing PPTX, brochures, brand films, social media content, and WhatsApp messaging templates live.

## Uploading a File to a Marketing Collaterals Folder with Permissions

This is the pattern used for uploading a draft marketing file (e.g. WhatsApp content pillars deck) to a project's 03_Marketing_Collaterals folder and sharing it with a collaborator.

### Pattern (from terminal() — vault socket is available)

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import _load_credentials_direct
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

creds = _load_credentials_direct('google-draas')
service = build('drive', 'v3', credentials=creds)

# 1. Upload to the target folder
folder_id = "1fRYtiqclzInfz2rVZHFNziou9KSEg77B"  # 03_Marketing_Collaterals
file_metadata = {
    'name': "Project Name - Content Description - Draft.pptx",
    'parents': [folder_id]
}
media = MediaFileUpload(
    '/local/path/to/file.pptx',
    mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
)
uploaded = service.files().create(
    body=file_metadata,
    media_body=media,
    fields='id, name, webViewLink, parents'
).execute()
file_id = uploaded['id']
public_link = uploaded['webViewLink']

# 2. Anyone-with-link view access (no discovery)
service.permissions().create(
    fileId=file_id,
    body={'type': 'anyone', 'role': 'reader', 'allowFileDiscovery': False},
    sendNotificationEmail=False
).execute()

# 3. Check if collaborator already has folder access
folder_perms = service.permissions().list(
    fileId=folder_id,
    fields='permissions(id, emailAddress, role, type)'
).execute()
existing = [p for p in folder_perms.get('permissions', [])
            if p.get('emailAddress', '').lower() == collaborator_email]

# 4. If no existing access, add editor on the file itself
if not existing:
    service.permissions().create(
        fileId=file_id,
        body={'type': 'user', 'role': 'writer', 'emailAddress': collaborator_email},
        sendNotificationEmail=False
    ).execute()

print(f"Link: {public_link}")
```

### Key points

- **`terminal()` not `execute_code`** — the vault socket (`/run/gws-vault/vault.sock`) is available in `terminal()` but NOT in the `execute_code` sandbox. Always use `terminal()` for Drive API operations.
- **`sendNotificationEmail=False`** — avoids spamming the collaborator with Drive notifications for draft files.
- **`allowFileDiscovery: False`** on the anyone-link permission prevents the file from appearing in search results; only direct link access works.
- **File-level permissions** are set when the collaborator doesn't have folder-level access. If they need ongoing access to multiple files, it's better to share the folder itself.
