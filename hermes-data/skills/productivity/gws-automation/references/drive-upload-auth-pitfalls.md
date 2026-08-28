# Drive Upload & Auth Pitfalls

## 1. Drive upload to another user's folder fails

**Symptom:** `HttpError 403: "Insufficient permissions for the specified parent"` when calling `drive.files().create()` with `parents: [FOLDER_ID]`.

**Root cause:** The authenticated OAuth user (e.g., vkdas@draas.com via `gws_auth.build_service`) does NOT own the target folder. The folder is owned by ndr@draas.com. Even though the authenticated user can see and read the folder, `files().create()` with `parents` referencing it fails.

**Detection:** Check the authenticated user before uploading:
```python
drive = build_service("drive", "v3")
about = drive.about().get(fields='user').execute()
print(f"Authenticated as: {about['user']['emailAddress']}")
```

**Fix:**
1. Create a new folder in the authenticated user's Drive root (omit `parents`)
2. Upload all files there
3. Share the folder with ndr@draas.com as `writer`:
```python
folder = drive.files().create(body={
    "name": "Project Name - Extracted PDFs",
    "mimeType": "application/vnd.google-apps.folder"
}, fields="id, webViewLink").execute()

drive.permissions().create(
    fileId=folder["id"],
    body={"type": "user", "role": "writer", "emailAddress": "ndr@draas.com"},
    sendNotificationEmail=False
).execute()
```
4. Also share any spreadsheet created in that folder the same way

**Verified:** Jun 2026 — Allalsandra extraction, vkdas@draas.com token, folder owned by ndr@draas.com.

## 2. SA DWD key not configured

**Symptom:** `gws_sa.build_service("sheets", "v4", "ndr@draas.com")` raises `KeyError: 'GOOGLE_SA_KEY'`.

**Cause:** The service account credentials are not set in the environment (env var `GOOGLE_SA_KEY` is missing).

**Fix:** Fall back to `gws_auth.build_service("sheets", "v4")`. The per-user OAuth token includes the Sheets scope and can create/update spreadsheets in the user's own Drive. Note the spreadsheet will be owned by the authenticated user (e.g., vkdas@draas.com), not ndr@draas.com — share it explicitly.

## 3. Service Account impersonation limitation

The SA DWD impersonates ndr@draas.com for shared Sheets. Without the key configured, you cannot:
- Write to the contacts registry sheet as ndr@draas.com
- Access any shared sheet that requires ndr@draas.com's identity

**Workaround:** Use `gws_auth.build_service("sheets", "v4")` to create a new sheet in the authenticated user's Drive, populate it, and share it.
