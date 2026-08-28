# Copy Files From a Shared (External) Drive Folder

**When:** Someone shares a Drive folder link with you (owned by another user), and you need to copy all its contents into your own Drive.

This is **different from moving files within your own Drive** — you cannot `addParents`/`removeParents` on files you don't own. Instead, use `drive.files().copy()`.

## Workflow

### 1. Extract Folder ID from the Shared Link

The link looks like:
```
https://drive.google.com/drive/folders/1toJw5X7pE_PkYQs8wfZA7oQ-_8wCd_k-
```
The folder ID is the long string after `/folders/` and before any `?` parameter:
```
1toJw5X7pE_PkYQs8wfZA7oQ-_8wCd_k-
```

### 2. List Contents (including subfolders)

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

shared_folder_id = '1toJw5X7pE_PkYQs8wfZA7oQ-_8wCd_k-'

# List top-level files/folders
res = drive.files().list(
    q=f"'{shared_folder_id}' in parents and trashed = false",
    fields='files(id,name,mimeType,webViewLink,size)',
    pageSize=100,
    orderBy='name'
).execute()

files = res.get('files', [])
for f in files:
    print(f"{f['name']} ({f['mimeType']}) [{f['id']}]")
```

**Note:** You may need `supportsAllDrives=True` if the folder is in a shared drive. For user-shared folders (typical), it works without this flag.

### 3. Copy Files to Your Target Folder

Use `drive.files().copy()` with the `parents` parameter pointing to your target folder:

```python
target_folder_id = '1RQZ0UXmShpa0TtSa0aBa9f9-JUAPxeZZ'

for f in files:
    if f['mimeType'] == 'application/vnd.google-apps.folder':
        continue  # Handle subfolders separately if needed
    
    copy = drive.files().copy(
        fileId=f['id'],
        body={'name': f['name'], 'parents': [target_folder_id]},
        fields='id,name,webViewLink'
    ).execute()
    print(f"Copied: {copy['name']} -> {copy['webViewLink']}")
```

### 4. Handle Subfolders Recursively

If the shared folder has nested subfolders (e.g., `DWG/`, `PDF/`, `SITE IMAGES/`), flatten them into your target or recreate the structure:

**Flat copy (all files into one folder):**
```python
def copy_all_files(folder_id, target_id):
    items = drive.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        fields='files(id,name,mimeType)',
        pageSize=100
    ).execute()
    
    for item in items.get('files', []):
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            copy_all_files(item['id'], target_id)  # recurse
        else:
            drive.files().copy(
                fileId=item['id'],
                body={'name': item['name'], 'parents': [target_id]}
            ).execute()
```

### 5. Batch Copying Many Files

For large batches (50+ files), copy sequentially — the Drive API rate limit handles individual copies fine. Example from session: **93 files** (1 DWG, 2 PDFs, 90 site images) copied in ~30 seconds.

## Example (from session)

| Source | Target |
|---|---|
| Shared folder owned by "Melchi zedek" containing `DWG/`, `PDF/`, `SITE IMAGES/` | User's `Embassy Habitat / 1503 / Plans` folder |
| 93 files total: 1 `.dwg`, 2 PDFs, 90 `.jpg` site photos | All flattened into target folder (no subfolder recreation needed) |

```python
# Session pattern — copy all files from shared folder
shared_id = '1toJw5X7pE_PkYQs8wfZA7oQ-_8wCd_k-'
target_id = '1RQZ0UXmShpa0TtSa0aBa9f9-JUAPxeZZ'

res = drive.files().list(
    q=f"'{shared_id}' in parents and trashed = false",
    fields='files(id,name,mimeType)',
    pageSize=200
).execute()

for f in res.get('files', []):
    if f['mimeType'] == 'application/vnd.google-apps.folder':
        # List and copy contents of subfolder
        sub = drive.files().list(
            q=f"'{f['id']}' in parents and trashed = false",
            fields='files(id,name,mimeType)'
        ).execute()
        for sf in sub.get('files', []):
            drive.files().copy(
                fileId=sf['id'],
                body={'name': sf['name'], 'parents': [target_id]}
            ).execute()
    else:
        drive.files().copy(
            fileId=f['id'],
            body={'name': f['name'], 'parents': [target_id]}
        ).execute()
```

## Complete Workflow — With First-Time Auth

When the user hasn't authorized their Google account yet, pair the copy workflow with OAuth setup:

### 1. Verify auth and resolve the account

```python
from tools.gws_skill_bridge import call as gws

# Check if user's account is authorized
result = gws("gws_resolve_account", account="sales1.blr@draas.com")
# If has_token: false → send OAuth URL
```

### 2. Send the OAuth authorization link

Use `send_oauth_url` tool (never construct manually):

```
send_oauth_url(login_hint="user@email.com", label="Authorize Google Drive")
```

**⚠️ UX note:** The OAuth button is sent to the current Telegram chat but users often don't see it, especially on mobile. **Always explicitly tell the user: "Scroll up in this chat — there's an **Authorize** button I sent earlier. Tap it and sign in."** If the button can't be re-sent due to flood control, describe where to find the original one.

### 3. Verify the token landed

After the user confirms they authorized:

```python
result = gws("gws_resolve_account", account="sales1.blr@draas.com")
# Should show has_token: true
```

### 4. Proceed with the copy workflow

## Using gws_skill_bridge for Listing & Folder Creation (preferred)

The `gws_skill_bridge` handles credential management automatically. Use it for discovery and folder setup:

```python
from tools.gws_skill_bridge import call as gws

shared_folder_id = "1fXCdyRZzXeGUg8OrkLEs4l8vufJBggk-"

# List contents — pass raw_query=True for Drive API query syntax
result = gws("drive_search", service_name="google-draas",
             query=f"'{shared_folder_id}' in parents",
             raw_query=True, max=100)

# Create a root-level folder (pass parent="" — omitting it raises AttributeError)
folder = gws("drive_create_folder", service_name="google-draas",
             name="Vendor Files - Project Name", parent="")

# Create a subfolder inside it
sub = gws("drive_create_folder", service_name="google-draas",
          name="Drone", parent=folder_id)
```

**Pitfall — `parent=""` is required for root-level folders.** The underlying `drive_create_folder` function checks `if args.parent:` — if the attribute doesn't exist on the SimpleNamespace, it raises `AttributeError`. Pass `parent=""` explicitly to create at the Drive root.

### For the actual copy, use the Drive API directly

The bridge has no `drive_copy` operation, so fall back to `build_service` for `drive.files().copy()`:

```python
from tools.gws_auth import build_service
drive = build_service("drive", "v3", service_name="google-draas")

for f in files:
    drive.files().copy(
        fileId=f["id"],
        body={"name": f["name"], "parents": [target_folder_id]}
    ).execute()
```

## Large File Sets — Timeout Handling

**Problem:** A batch of 100 files (57 MP4 videos + 22 DNG raws + 21 JPGs, ~3+ GB total) can take well over 5 minutes to copy sequentially in `execute_code()`, hitting the 300-second timeout with only partial completion.

**Pattern — check progress and resume:**

```python
# Step 1: Copy as many as possible (may timeout)
for f in src_files:
    drive.files().copy(
        fileId=f["id"],
        body={"name": f["name"], "parents": [target_id]}
    ).execute()

# Step 2: Check what made it
dest = gws("drive_search", service_name=service_name,
           query=f"'{target_id}' in parents", raw_query=True, max=500)
dest_names = {f["name"] for f in json.loads(dest)}

# Step 3: Copy only the missing ones
for f in src_files:
    if f["name"] not in dest_names:
        drive.files().copy(fileId=f["id"], ...).execute()
```

- **Always verify final counts match** (source vs destination) before telling the user it's done
- For very large sets (500+ files), batch in smaller chunks (50-100 at a time) with verification between each batch
- The timeout is in `execute_code()` (5 min), not in the Drive API itself — sequential copies of large video files are simply slow

## Pitfalls

- **Cannot move — only copy.** You don't own the shared files, so `addParents`/`removeParents` will fail with a 403. Always use `copy()`.
- **Duplicate detection.** If you run the copy twice on the same folder, you'll get duplicate files. Check `name` in the target folder first, or use a unique naming convention.
- **Large files cause timeouts.** Video files (MP4), DNG raws, and other large media copy much slower than JPGs. Sequential copy of 60+ media files can exceed the 300-second `execute_code()` timeout. Use the progress-check-and-resume pattern above.
- **Subfolder structure is lost.** The flat copy approach puts everything in one folder. If structure matters, recreate the subfolder hierarchy in your target first, then copy into the correct subfolder.
- **Copy inherits your permissions.** The copied files are owned by you, with your default sharing settings. Originals remain untouched.
- **No automatic rename.** The copy retains the original filename. Rename afterwards using the naming convention workflow.
