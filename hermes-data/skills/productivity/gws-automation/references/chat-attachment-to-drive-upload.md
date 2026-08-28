# Chat Attachment → Drive Upload (Telegram Images & Files)

When a user sends an image or file via Telegram (or another chat channel) and asks you to upload it to Google Drive, the actual file may or may not be accessible on disk. This reference covers the discovery and fallback workflow.

## The Core Problem

When a user attaches an image to a Telegram message, the Hermes system processes it through the vision model — describing its contents back to you. **However, the original file is not always persisted to disk.** You'll see a detailed visual description of the image in your context, but no file path to upload.

This typically manifests as:
- A long image description injected into the user's message
- No corresponding file on disk at any known location
- You can describe the image but cannot upload the actual file to Drive

## Discovery — Check These Locations First

```bash
# 1. Document cache (most common for Telegram attachments)
ls -la /data/hermes/document_cache/

# 2. Hermes data root (some Telegram files land here)
find /data/hermes -maxdepth 3 -newer /data/hermes -name "*.jpg" -o -name "*.png" -o -name "*.jpeg" -o -name "*.pdf" 2>/dev/null

# 3. System data directory (common for recent-file drops)
find /opt/data -maxdepth 3 -newer /opt/data -type f \( -iname "*.jpg" -o -iname "*.png" -o -iname "*.jpeg" -o -iname "*.pdf" \) 2>/dev/null

# 4. Temporary uploads
ls -la /mnt/uploads/ 2>/dev/null; ls -la /opt/data/uploads/ 2>/dev/null

# 5. Telegram-specific gateway drops
find /opt/hermes -maxdepth 5 -newer /opt/hermes/hermes_data -name "*.jpg" -o -name "*.png" 2>/dev/null
```

Also check the session's state.db (if available) for Telegram upload metadata — the system may have logged the original file ID even if the file itself wasn't saved.

## When the File Is Not Found

If none of the above locations contain the file, the image was consumed by the vision model but the raw file was discarded. **Do not fabricate the file or generate a substitute.** Instead:

1. **Tell the user clearly**: "The image you attached was described to me but the actual file wasn't saved to disk, so I can't upload it to Drive."

2. **Ask them to re-send the file**: "Could you please re-send the image as a file attachment? I'll upload it to Drive once it's received."

3. **Alternative approaches** (ask the user which works):
   - If the image is in Google Photos or a shared album: use `browser_use_cloud` to navigate to it and download
   - If they have the image on their phone: re-send via Telegram
   - If it was from a website or social media: share the source URL so you can download it from there

## When the File IS Found (General Upload)

If the file exists on disk, upload it using the standard Drive upload pattern:

```python
from googleapiclient.http import MediaFileUpload

# Determine target folder — use TMP for temporary files
results = drive.files().list(
    q="name='TMP' and mimeType='application/vnd.google-apps.folder' and 'root' in parents and trashed=false",
    fields="files(id, name, webViewLink)"
).execute()
tmp_folder = results.get('files', [{}])[0] if results.get('files') else None

# Upload
media = MediaFileUpload(LOCAL_PATH, mimetype=MIME_TYPE, resumable=True)
body = {
    'name': DRIVE_NAME,
    'parents': [tmp_folder['id']] if tmp_folder else []
}
uploaded = drive.files().create(
    body=body, media_body=media,
    fields='id, name, webViewLink'
).execute()

drive_link = uploaded['webViewLink']
```

Common MIME types:
| Extension | MIME Type |
|-----------|-----------|
| .jpg/.jpeg | image/jpeg |
| .png | image/png |
| .pdf | application/pdf |
| .webp | image/webp |

## Example: Housewarming Invitation Workflow

A concrete example of the full flow:

1. User sends an invitation image via Telegram + asks to create a calendar event with the image in Drive
2. The image is described by vision but the file is not on disk
3. **Action**: Ask user to re-send the image as a Telegram file attachment
4. Once the file arrives, check `/data/hermes/document_cache/` for the cached upload
5. Upload the file to the existing TMP folder on Drive (root-level folder, typically already exists)
6. Create the calendar event with the Drive link in the description
7. Add the user's family members as attendees

## Relation to Existing References

This reference covers the **chat → Drive** upload path. For Gmail → Drive (email attachments), see `gmail-attachment-to-drive-upload.md`. For general Drive upload patterns, see `drive-file-upload.md`. For creating calendar events with Drive links in descriptions, see `calendar-events.md` → "Adding Drive Document Links to Description."
