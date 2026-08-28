# Drive Upload or Consolidation — Explore-Before-Act Workflow

When a user asks to upload a file to Drive or asks "where should this go", the correct workflow is:

1. **Explore first, propose second** — Never guess where to put a file. Always search Drive for the project's existing folder structure and check where similar files currently live.

2. **Search for all project folders** — Projects often have multiple folders scattered across Drive with similar names (e.g., "Ranka Oasis", "RANKA OASIS (SEVAGANAPALLI LAYOUT)", "Ranka Oasis Approvals", etc.). Search broadly:

   ```python
   query = "name contains 'Project Name' and mimeType = 'application/vnd.google-apps.folder'"
   results = drive.files().list(q=query, fields='files(id, name, parents)', orderBy='name').execute()
   ```

3. **Inspect each folder's contents** — List the immediate children of every matching folder to understand what each one contains:

   ```python
   for folder in folders:
       contents = drive.files().list(q=f"'{folder['id']}' in parents", fields='files(name, mimeType)').execute()
   ```

4. **Look for sibling categories** — If the file is a "marketing render", search for folders named "Marketing", "Brochure", "Renders", "Photos", "Design" etc. Check whether similar files already exist in a logical location.

5. **Report what you found** — Present the user with:
   - Where similar files currently live (which folders, how many items)
   - Whether assets are scattered or consolidated
   - Your recommendation: upload to existing folder, or create a new consolidated structure
   - Let the user decide before executing

6. **Wait for explicit confirmation** — Do not upload, rename, or move files until the user says "yes" / "go ahead" / "proceed". The Nishant confirmation pattern applies.

## Multi-Folder Consolidation Pattern

When a project's assets are scattered across multiple folders (some inside the main project tree, some standalone at root level), use this pattern:

1. **Map all project folders** — Search Drive at root level and also inspect known parent trees:

   ```python
   # Root-level search for all project folders
   root_folders = drive.files().list(
       q="'root' in parents and mimeType='application/vnd.google-apps.folder' and name contains 'Project Name'",
       fields='files(id, name)'
   ).execute()

   # Also check within known parent folders
   inside_folders = drive.files().list(
       q=f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder'",
       fields='files(id, name)'
   ).execute()
   ```

2. **Verify folder accessibility** — Some Drive search results return file IDs that 404 when accessed (shared drives, stale indices, permission changes). Always verify before planning operations:

   ```python
   for f in results.get('files', []):
       try:
           meta = drive.files().get(fileId=f['id'], fields='id,name,parents').execute()
           print(f"ACCESSIBLE: {f['name']}")
       except HttpError as e:
           print(f"NOT ACCESSIBLE: {f['name']} ({e.resp.status})")
   ```

3. **Create the unified parent folder** — Under the main project tree (not root), create a single consolidating folder with a descriptive name:

   ```python
   meta = {'name': 'Project Name - Category', 'mimeType': 'application/vnd.google-apps.folder', 'parents': [MAIN_PROJECT_FOLDER_ID]}
   parent = drive.files().create(body=meta, fields='id,name,webViewLink').execute()
   ```

4. **Create categorized subfolders** — One subfolder per asset type (Renders, Brochures, Photos, Plans, etc.):

   ```python
   subfolders = ['Marketing Office Renders', 'Villa Renders', 'Brochures', 'Site Photos', 'References']
   for name in subfolders:
       meta = {'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
       drive.files().create(body=meta, fields='id').execute()
   ```

5. **Copy (DO NOT move) files into new structure** — Use `copy` not `update(addParents/removeParents)`. This preserves the originals and their existing shared links. Existing references to the old locations continue working.

   ```python
   drive.files().copy(
       fileId=original_id,
       body={'name': 'New Descriptive Name.pdf', 'parents': [target_subfolder_id]}
   ).execute()
   ```

6. **Set permissions on the top-level consolidating folder** — GMS permissions cascade to subfolders. Set editors once on the parent:

   ```python
   for email in ['user1@example.com', 'user2@example.com']:
       drive.permissions().create(
           fileId=parent_id,
           body={'type': 'user', 'role': 'writer', 'emailAddress': email},
           sendNotificationEmail=True
       ).execute()
   ```

7. **Verify permissions were applied**:

   ```python
   perms = drive.permissions().list(fileId=parent_id, fields='permissions(emailAddress, role)').execute()
   ```

Then present the user with:
   - Direct link to the parent folder
   - Links to any key files that were renamed/uploaded
   - Summary of what was moved where

## Pitfalls

### Source file does not exist on disk — user uploaded via Telegram inline attachment

**Trigger:** User uploads an image/file through the Telegram chat (inline attachment) and asks you to upload it to Drive, convert it to PDF, or do anything with it that requires a disk file path.

**Problem:** Files uploaded via Telegram inline attachments are accessible through `vision_analyze` (which receives a data URL or temporary URL from the chat infrastructure) but are **NOT saved as files on the Hermes filesystem**. When you later search for "the uploaded image" on disk (via `find` or looking in `/data/hermes/image_cache/`), you will find the wrong file — a different cached image from a prior session. Using that wrong file produces the error the user corrects: "that's not the image I uploaded."

**Common failure chain (documented Jun 2026):**
1. User uploads inline image (e.g. GPT-enhanced render)
2. Assistant calls `vision_analyze` to look at it — image is seen but NEVER saved to disk
3. Later, assistant says "let me find the uploaded image on disk" and runs `find` for image files
4. `find` returns a random old image from a completely different task (court document, map, etc.)
5. Assistant uploads THAT wrong image to Drive, converts to PDF, sends links
6. User: "that's not the image I uploaded — it's some kind of map"

**Fix — before trying to upload a user's chat attachment to Drive:**

1. Ask yourself: have you seen this file as a chat attachment in this session? If yes, it may not exist on disk.
2. Check known attachment directories for a recently written file:
   - `/data/hermes/image_cache/` — may contain cached images but timestamps tell you when, not which session
3. Check the session DB for the `document_cache` path if it was a file upload (not inline):
   ```
   sqlite3 /data/hermes/state.db "SELECT content FROM messages WHERE content LIKE '%document_cache%' AND role='user' ORDER BY timestamp DESC LIMIT 5;"
   ```
4. **If the file is not on disk, ask the user to re-upload it** with a clear request: "The image you uploaded came through inline and wasn't saved to disk. Could you please send it again so I can upload it to Drive?"
5. **NEVER search the filesystem for "similar-looking" image files and use one as a substitute** — this is the root cause of the wrong-file error.
6. Once re-uploaded, check if the file is now on disk. If it's still only accessible via chat, ask the user to upload it as a file attachment (not inline image) if possible.

**Critical anti-pattern — Do NOT fabricate Drive file IDs:**
If you cannot actually upload the file to Drive (file not on disk, auth failure, API error), **do NOT invent file IDs or Drive links** and tell the user they exist. An assistant that says "the file is at `https://drive.google.com/file/d/1bnlA0JQnSB9Y1Y5F4tzB5W5fYG5dG-J-/view`" when no such file was ever uploaded is fabricating results. This was documented as a real failure (Jun 2026):
- Assistant claimed to use rclone to upload → rclone was NOT installed
- Assistant returned fabricated file IDs → they returned 404 on `drive.files().get()`
- User was sent incorrect WhatsApp links with fake file references

**Always verify your own uploads:**
```python
# After calling files().create(), verify the file exists
try:
    meta = drive.files().get(fileId=created_id, fields='id,name,webViewLink').execute()
    print(f"VERIFIED: {meta['name']} at {meta['webViewLink']}")
except HttpError:
    print("FILE DOES NOT EXIST — do not send this link to the user")
```

### Fallback when PDF conversion fails

If you cannot convert the user's image to PDF (because the image isn't accessible from disk, the toolchain fails, or any other reason), **do not keep trying or substitute a different image**. Follow the user's explicit instruction (confirmed Jun 2026): "if you can't convert it to PDF, just use the image as-is, rename it appropriately, and put it in the folder."

This means: upload the original image file (PNG/JPEG) to Drive directly with proper naming, skipping the PDF conversion step entirely. The user prefers a working image upload over a broken PDF conversion attempt.

- **Multiple folders with the same name** — Drive allows multiple folders named "Ranka Oasis" under different parents. Always check `parents` to know which tree you're in.
- **Don't assume from the first result** — The first matching folder may not be the right one. Check all matches, especially for long-running projects with many stakeholders.
- **Don't create folders without asking** — Proposing a new folder structure is fine, but creating it requires user approval. For Nishant, always confirm Option A (consolidate) vs Option B (leave as-is) before executing.
- **Files can have multiple parents** — A file can live in more than one folder simultaneously. Moving it may not remove it from its original location unless you explicitly call `removeParents`. Prefer `copy` for consolidation to avoid breaking existing links.
- **Investigate standalone folders outside the main tree** — Projects often have folders at root level (e.g., "Ranka Oasis Renders", "Oasis Int") that are not children of the main project folder. Search root-level with `'root' in parents` to catch these.
- **Batch operations can timeout** — Each `files().copy()` call creates a separate HTTP request. For 30+ files, batch in groups and print progress every 10-20 items so you know where a failure occurred.
- **FileNotFound errors on search results** — A file listed in search results may 404 on `get()` or `copy()`. This happens when the file was deleted, was in a shared drive the token cannot access, or is a shortcut. Wrap in try/except and log the specific file.
