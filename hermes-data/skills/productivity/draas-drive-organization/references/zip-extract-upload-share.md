# Zip Archive — Extract, Upload, Share & Notify

Recurring workflow: a zip file of project documents (drawings, approvals, plans) lands in **TMP** from an external party (Godrej, architect, consultant). Steps to process end-to-end.

## Trigger
- User says "uploaded a zip file of [project] plans/approvals to TMP"
- Zip contains mixed file types: DWG, PDF, XLSX, PNG, JPG
- User wants it filed, shared with team, and notified via email reply

## Workflow

### 1. Locate the zip in TMP
```
TMP folder: 18p74II2uL32sNDzDDwXzmlOUdJJOTmE-
```
ALWAYS check recent files in TMP (created today/last 24h). The zip may be large (50-100 MB).

### 2. Identify the correct project folder
Walk the Drive tree to find the right destination folder. For BuxRanka/Godrej Hudson Circle:
```
BuxRanka (1G_Jfh01PI2S5bkPPeRJ1tC7rGNZU-wFn)
  → BuxRanka FAR Matter (13Mtolinwp-k07wLvdZUH4YD5UzHfCg8e)
    → New dated subfolder (e.g. "20260827_Godrej_4.5_FAR_Revised_Plans")
```
For other projects, follow the project's existing folder structure.

### 3. Download & extract
Large zips (>50 MB) need a background terminal process. Use `notify_on_complete=true`:

```python
from googleapiclient.http import MediaIoBaseDownload
import io, zipfile

request = svc.files().get_media(fileId=ZIP_ID)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()

extract_dir = '/tmp/buxranka_4.5far_extracted'
os.makedirs(extract_dir, exist_ok=True)
with zipfile.ZipFile(fh) as zf:
    zf.extractall(extract_dir)
```

### 4. Create structured subfolder
Name format: `YYYYMMDD_Party_Project_Description`
```python
new_folder = svc.files().create(body={
    'name': '20260827_Godrej_4.5_FAR_Revised_Plans',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': [PARENT_FOLDER_ID]
}, fields='id,name,webViewLink').execute()
```

### 5. Bulk upload with MIME types
Walk the extracted directory. Map extensions to MIME types:
- `.pdf` → `application/pdf`
- `.dwg` → `application/acad`
- `.xlsx` → `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `.png` → `image/png`
- `.jpg`/`.jpeg` → `image/jpeg`
- Everything else → `application/octet-stream`

Normalize relative paths as filenames (replace `/` with ` - `):
```python
from googleapiclient.http import MediaFileUpload
media = MediaFileUpload(fp, mimetype=mime, resumable=True)
uploaded = svc.files().create(
    body={'name': rel_path_clean, 'parents': [folder_id]},
    media_body=media,
    fields='id,name'
).execute()
```

### 6. Set permissions
```python
# Team members (writer)
svc.permissions().create(fileId=folder_id, body={
    'type': 'user', 'role': 'writer',
    'emailAddress': 'user@draas.com'
}, sendNotificationEmail=False).execute()

# Anyone with link (reader)
svc.permissions().create(fileId=folder_id, body={
    'type': 'anyone', 'role': 'reader', 'allowFileDiscovery': False
}, sendNotificationEmail=False).execute()
```

**Note:** `expirationTime` is NOT supported on folders in My Drive (403 `cannotSetExpiration`). Set it on individual files inside the folder if time-limited access is required, or use a shared drive.

### 7. Create threaded email draft with link

Find the original email thread from the external party (search Gmail by sender + subject keywords). Create a threaded reply draft:

```python
message = MIMEText(body)
message['To'] = 'recipient@draas.com'
message['From'] = 'ndr@draas.com'
message['Subject'] = 'Re: ' + orig_subject
message['In-Reply-To'] = orig_msg_id
message['References'] = references + ' ' + orig_msg_id
raw = base64.urlsafe_b64encode(message.as_bytes()).decode('ASCII')
draft = gmail.users().drafts().reate(
    userId='me',
    body={'message': {'raw': raw, 'threadId': orig_thread_id}}
).execute()
```

## Pitfalls

- **Large zips time out in foreground terminal() (60s default).** Use background=true + notify_on_complete=true for any zip > 30 MB.
- **Background process runs as a heredoc — escaping breaks.** Write the script to `/tmp/` and execute it, don't inline multi-line heredocs with `&&` continuation.
- **`drive_upload` with `resumable=True`** is critical for files > 5 MB. The `MediaFileUpload` without resumable flag fails silently on large uploads.
- **Expiration dates on Drive folder permissions = 403.** My Drive does not support `expirationTime` on folder-level permissions. Only file-level permissions support it.
- **Verify permission grant** by listing permissions after creation: `svc.permissions().list(fileId=fid).execute()` — the create response is sometimes incomplete (missing `expirationTime` field even when set).