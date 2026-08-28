# PPTX → Google Slides: Two Upload Approaches

## Credential Loading: When the Sandbox Can't Reach the Vault

The `gws_skill_bridge` and `gws_auth` modules do NOT work when called from inside `terminal()` — they need the vault Unix socket / RPC stubs that only `execute_code` sandbox provides. However, the sandbox's `hermes_tools` stub may be missing `gws_fetch_token`, causing `ImportError`.

**Working fallback — standalone script via terminal() with venv:**

```python
#!/opt/hermes/.venv/bin/python3
import sys, os
sys.path.insert(0, '/opt/hermes/tools')
from gws_auth import load_credentials
from googleapiclient.discovery import build

# The telegram_id comes from the session environment
telegram_id = os.environ.get('HERMES_SESSION_USER_ID', '[REDACTED-TID]')
creds = load_credentials(telegram_id, 'google-draas')

drive = build('drive', 'v3', credentials=creds)
# ... use drive service normally
```

**Key points:**
- Always use `/opt/hermes/.venv/bin/python3` — the system Python is PEP 668 managed
- `HERMES_SESSION_USER_ID` (or `HERMES_SESSION_CHAT_ID`) carries the correct telegram ID in the terminal() environment
- `service_name` is your mapped GWS account (resolve via the `gws_resolve_account` tool, but once known `google-draas` works for Prakash)
- Write the script to `/tmp/`, run via `terminal('/opt/hermes/.venv/bin/python3 /tmp/script.py')`

## Option A: Direct Multipart Upload (existing skill guidance)

Upload PPTX content with metadata that sets `mimeType: application/vnd.google-apps.presentation`. Google Drive auto-converts.

See the main SKILL.md for the raw HTTP multipart example (works without googleapiclient).

## Option B: Upload then Copy (simpler, more reliable)

This two-step approach avoids multipart encoding issues:

1. **Upload** the PPTX file as-is (gets stored as `application/vnd.openxmlformats-officedocument.presentationml.presentation`)
2. **Copy** with `mimeType` override to trigger Google-native conversion

```python
from tools.gws_auth import build_service

drive = build_service('drive', 'v3', service_name='google-draas')

# Step 1: Upload as PPTX
from googleapiclient.http import MediaFileUpload
media = MediaFileUpload('/tmp/deck.pptx',
    mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
    resumable=True)
uploaded = drive.files().create(
    body={'name': 'My Presentation'},
    media_body=media,
    fields='id, mimeType'
).execute()
pptx_id = uploaded['id']

# Step 2: Copy with Slides mimeType to convert
converted = drive.files().copy(
    fileId=pptx_id,
    body={
        'name': 'My Presentation',
        'mimeType': 'application/vnd.google-apps.presentation'
    },
    fields='id, name, mimeType, webViewLink'
).execute()

# Step 3: Delete intermediate PPTX
drive.files().delete(fileId=pptx_id).execute()

print(f"Link: {converted['webViewLink']}")

## Option C: Delete + Create (replacing an existing Google Slides file)

Use when you need to **replace** an existing native Google Slides file with an updated PPTX. Do NOT use `drive.files().update()` — it returns HTTP 200 but does **not** convert the PPTX content into Slides format; the file's content stays unchanged.

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', service_name='google-draas')
old_file_id = "1ABC..."

# 1. Delete old file
drive.files().delete(fileId=old_file_id).execute()

# 2. Upload PPTX with conversion to Google Slides
media = MediaFileUpload('/tmp/updated.pptx',
    mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
    resumable=True)

body = {
    'name': 'Presentation Name',
    'mimeType': 'application/vnd.google-apps.presentation'
}

result = drive.files().create(
    body=body,
    media_body=media,
    fields='id, name, mimeType, webViewLink'
).execute()

new_id = result['id']
print(f"✓ New file: {new_id}")

# 3. Re-share (old permissions are gone with the old file)
drive.permissions().create(
    fileId=new_id,
    body={'type': 'user', 'role': 'writer', 'emailAddress': 'user@example.com'},
    sendNotificationEmail=True
).execute()
```

**⚠️ Important:** Deleting and recreating means:
- The file gets a **new ID** — deliver the new link to the user
- **Permissions are lost** — re-share with the requesting user
- The old file is permanently deleted — make sure you don't need it

## ⚠️ Operational pitfall: Replacing files causes "page not found" confusion

**Do NOT delete the old file before the user confirms the replacement works.**

When you re-upload a file to fix an issue (e.g. adding hyperlinks, fixing formatting), the natural flow is:

1. Upload fixed version → new Google Slides file with new ID
2. Share both old and new with `anyoneWithLink`
3. Deliver **both links** to the user and tell them the old one will be deprecated
4. Wait for user confirmation that the new one opens
5. THEN delete the old file

**Why this matters:** If you delete file A immediately after creating file B, the user may still be trying to open file A from your earlier message. The error they see is "page not found" — even though the file exists on the backend, the ID they clicked is already gone.

```python
# STEP 1: Upload new version (don't delete old yet)
body = {
    'name': 'Presentation Name',
    'mimeType': 'application/vnd.google-apps.presentation'
}
media = MediaFileUpload('/tmp/updated.pptx', 
    mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
    resumable=True)
new_file = drive.files().create(body=body, media_body=media, fields='id, name, webViewLink').execute()
new_id = new_file['id']

# STEP 2: Share new file
drive.permissions().create(fileId=new_id, body={'role': 'reader', 'type': 'anyone'}).execute()

# STEP 3: Deliver link, get confirmation, THEN delete old
# drive.files().delete(fileId=old_id).execute()  # ← only after user says "new one works"
```

**Fallback when links fail:** If the link doesn't open despite file being owned by the user and shared as `anyoneWithLink`, tell the user to **search by filename in their Google Drive** (`drive.google.com`). The file IS there — it was created under their own account. Searching bypasses any link-rendering or redirect issues.

## ⚠️ Bridge quirk: All optional params required

When using `gws_skill_bridge.call('drive_upload', ...)`, you MUST pass **all** optional parameters explicitly, even if empty:

```python
# CORRECT — passes every optional param
call('drive_upload', service_name='google-draas',
     path='/tmp/deck.pptx',
     name='My Deck',
     mime_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
     parent='')            # ← required even when empty
```

```python
# WRONG — 'parent' missing → AttributeError: no attribute 'parent'
call('drive_upload', service_name='google-draas',
     path='/tmp/deck.pptx',
     name='My Deck')
```

Same requirement applies to `drive_delete` (needs `permanent=False`), `drive_download` (needs `output=`), and other bridge operations with optional params. The `call()` function creates a `SimpleNamespace` from kwargs — any param the underlying function reads must exist in the namespace.
