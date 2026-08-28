# Drive Permission Inheritance — Restricting Files in Shared Folders

## The Problem

When a file lives inside a folder that has **`anyone | reader`** ("Anyone with the link can view"), the file *inherits* that permission. You **cannot delete the inherited `anyone` permission at the file level** — the Drive API returns:

```
HttpError 403: "The authenticated user cannot delete the permission.
If the permission is inherited, limited access must be leveraged"
```

This means you cannot make individual files more restrictive than their parent folder.

## Detection: Check If Permission Is Inherited

List permissions on the file:
```python
perms = drive.permissions().list(
    fileId=FILE_ID,
    fields='permissions(id,type,role)'
).execute()
for p in perms.get('permissions', []):
    if p['type'] == 'anyone':
        print(f"Public access: {p['role']}")
```

If `permissionId` is `anyoneWithLink`, it is inherited from the parent. Direct permissions have numeric IDs (e.g., `01142957624446430543`).

## Case: USER-level grants inherited from a shared folder (not just `anyone`)

The same 403 hits when the file's **user permissions are inherited from the parent folder**, not just public-link access. Observed Jul 2026: an employment contract sat in the "Employment Contracts" folder, which was shared as `writer` with two users from the design firm (`bk@findingform.design`, `powrnika@findingform.design`). The file showed them in `permissions().list()`, but `permissions().delete()` failed with the identical message:

```
HttpError 403: "The authenticated user cannot delete the permission.
If the permission is inherited, limited access must be leveraged"
```

**Detection:** compare `permissionIds` on the file vs on its parent folder — identical IDs mean the grants are inherited, not direct. (The `inheritedFrom` field is NOT a valid `permissions.list()` field — don't request it.)

**Fix is the same move pattern, with one extra step:**
1. Move the file to a folder the outsiders can't see (e.g. the DRA HR folder, owned only by ndr@draas.com).
2. **Re-grant the intended editors directly on the file after the move** — moving drops ALL inherited grants, including the editor you want to keep. In the worked case, `rnr@draas.com` had been a writer via the old folder; after moving, the only permission left was the owner, so Roshni had to be re-granted `writer` explicitly.
3. Verify with `permissions().list()` — confirm the outsiders' emails are gone.
4. Note: moving also drops `anyoneWithLink` if the destination folder has none — usually desired for sensitive docs. The file's link (file ID) does NOT change on move, so already-shared links keep working.

**Detection: Check If Permission Is Inherited**

## Fix: Move the File to a Restricted Folder

The only reliable workaround is to **move the file out** of the publicly shared folder into one that has no `anyone` permission.

### Step 1: Find or create a restricted parent folder

```python
# Option A — Find an existing restricted folder (e.g., project root)
results = drive.files().list(
    q="name='RANKA IRIS' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    fields='files(id,name)'
).execute()
target_parent = results['files'][0]['id'] if results.get('files') else 'root'

# Option B — Create a new restricted subfolder under a non-public root
folder_meta = {
    'name': 'Sale Deeds - Restricted',
    'parents': [target_parent],
    'mimeType': 'application/vnd.google-apps.folder'
}
new_folder = drive.files().create(body=folder_meta, fields='id,name').execute()
new_folder_id = new_folder['id']

# Remove any 'anyone' permission (should be clean if parent isn't public)
perms = drive.permissions().list(fileId=new_folder_id, fields='permissions(id,type)').execute()
for p in perms.get('permissions', []):
    if p['type'] == 'anyone':
        drive.permissions().delete(fileId=new_folder_id, permissionId=p['id']).execute()
```

### Step 2: Add explicit user permissions

```python
authorized = [
    ('user@draas.com', 'writer'),
    ('other@draas.com', 'reader'),
]
for email, role in authorized:
    drive.permissions().create(
        fileId=folder_id,
        body={'type': 'user', 'role': role, 'emailAddress': email},
        sendNotificationEmail=False
    ).execute()
```

### Step 3: Move the file (update `parents`)

```python
file = drive.files().get(fileId=FILE_ID, fields='parents').execute()
old_parents = ','.join(file.get('parents', []))
drive.files().update(
    fileId=FILE_ID,
    addParents=NEW_FOLDER_ID,
    removeParents=OLD_PARENT_ID,
    fields='id,parents'
).execute()
```

### Step 4: Verify

```python
perms = drive.permissions().list(fileId=NEW_FOLDER_ID, fields='permissions(id,type)').execute()
types = [p['type'] for p in perms.get('permissions', [])]
is_restricted = 'anyone' not in types
```

## Case: Removing `anyone` from a Folder Itself

If the `anyone` permission is set **directly** on the folder (not inherited from higher up), you CAN remove it:

```python
# Works when permission is direct (permission ID is numeric, not 'anyoneWithLink')
drive.permissions().delete(fileId=FOLDER_ID, permissionId=PERM_ID).execute()
```

This succeeds for top-level folders and any folder where the public sharing was explicitly enabled rather than inherited.

## Making a File Temporarily Public for Sharing (e.g., WhatsApp)

When the user needs to share a Drive file link via WhatsApp and the file is in a restricted folder, add `anyone | reader` permission to just that file:

```python
drive.permissions().create(
    fileId=FILE_ID,
    body={'type': 'anyone', 'role': 'reader'},
    sendNotificationEmail=False
).execute()
```

The user can then share the link. Note: the user may later want to remove this — remind them to revoke the `anyone` permission after the recipient has downloaded the document.

## Verified Context

- June 2026: Ranka Iris Customer Legal Set folder had `anyone | reader` — all files inherited it
- New clean Sale Deeds uploaded there inherited the public sharing
- Fix: moved to a new restricted folder under the project root, added explicit permissions, verified no public access
- After moving Sale Deeds, the user then asked to restrict the *folder itself* — which succeeded because it was a direct permission, not inherited
