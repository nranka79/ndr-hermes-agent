# Drive Consolidation Pattern — Scattered Folders → Unified Tree

**Trigger:** The user's Drive has the same project's marketing/design/engineering assets scattered across multiple independent folders (main project folder, standalone folders, abandoned sub-trees). User says "bring them all under one [category] folder."

## Workflow

### Phase 1 — Discover All Scattered Locations

Search for the project name across ALL drives and folders. Common hiding spots:
- Standalone folders at root level (`drive.files().list(q="name contains 'Ranka Oasis'")`)
- Subfolders inside the main project tree (`Marketing office/Architectural/Render/`, `Entrance/Renders/`)
- Shared With Me or shared-drive items the user may not control
- Folders the user mentioned in past sessions

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

# Search both name and fullText to catch partial matches
results = drive.files().list(
    q="name contains 'Ranka Oasis' and trashed=false",
    corpora='allDrives',
    includeItemsFromAllDrives=True,
    supportsAllDrives=True,
    fields="files(id, name, parents)"
).execute()
```

### Phase 2 — Map the Structure

Recursively list each candidate folder to understand contents. Group by category:
- Marketing Renders, Villa Renders, Entrance Concepts
- Brochures, Site Photos, Master Plans & Floor Plans
- References/Competitor Data

### Phase 3 — Present Options to User

Ask: "Shall I create a unified folder and move everything into it (Option A), or just upload the new file and leave existing folders untouched (Option B)?"

**Get explicit confirmation before moving anything.** Moving files in Drive changes existing links and may break references.

### Phase 4 — Create Unified Structure

```python
FOLDER_ID = None  # Set from step above

def create_folder(parent_id, name):
    meta = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = drive.files().create(body=meta, fields='id,name').execute()
    return folder['id']

# Create parent
root = drive.files().create(body={
    'name': 'Ranka Oasis - Design & Marketing',
    'parents': ['MAIN_PROJECT_FOLDER_ID'],
    'mimeType': 'application/vnd.google-apps.folder'
}).execute()

# Create subfolders
subfolders = {
    'Marketing Office Renders': root['id'],
    'Villa Renders': root['id'],
    'Entrance Concepts': root['id'],
    'Brochures': root['id'],
    'Site Photos': root['id'],
    'Master Plans & Floor Plans': root['id'],
    'References': root['id'],
}
for name, parent in subfolders.items():
    create_folder(parent, name)
```

### Phase 5 — Move Files

For each source folder, move files into the appropriate target subfolder:

```python
# For each file:
drive.files().update(
    fileId=file_id,
    addParents=TARGET_SUBFOLDER_ID,
    removeParents=SOURCE_FOLDER_ID,
    supportsAllDrives=True
).execute()
```

**⚠️ Ownership pre-check — critical first step before any move.**

Before calling `addParents`, check whether the current user owns the source folder/file. A folder shared by another user has `canAddMyDriveParent: False` and the Drive API will reject any move attempt with `"Increasing the number of parents is not allowed"`.

```python
source_info = drive.files().get(
    fileId=source_folder_id,
    fields="id, name, ownedByMe, capabilities(canAddMyDriveParent, canCopy)"
).execute()

if not source_info.get('ownedByMe'):
    cap = source_info.get('capabilities', {})
    if not cap.get('canAddMyDriveParent'):
        # Cannot move — fall back to copy or shortcut
        if cap.get('canCopy'):
            # Copy individual files instead of moving the folder
            items = drive.files().list(q=f"'{source_folder_id}' in parents").execute()
            for item in items.get('files', []):
                drive.files().copy(
                    fileId=item['id'],
                    body={'parents': [target_folder_id], 'name': item['name']}
                ).execute()
        else:
            # Create shortcuts
            shortcut = {
                'name': f"→ {source_info['name']}",
                'mimeType': 'application/vnd.google-apps.shortcut',
                'parents': [target_folder_id],
                'shortcutDetails': {'targetId': source_folder_id}
            }
            drive.files().create(body=shortcut).execute()
```

**Pitfall — API timeout on bulk moves:** Each file move is a separate HTTP request. Moving 30+ files in one script may time out. Batch in groups of 10-15.

### Phase 6 — Set Permissions on Root Folder

Set editor/writer access for specific users on the root folder. All sub-items inherit automatically:

```python
for email in ['gsingh@draas.com', 'rnr@draas.com']:
    drive.permissions().create(
        fileId=root_id,
        body={'type': 'user', 'role': 'writer', 'emailAddress': email},
        sendNotificationEmail=False
    ).execute()
```

**Inheritance is automatic** — you do NOT need to set permissions on subfolders individually.

### Phase 7 — Verify

List the full tree recursively to confirm:
- All files are in their correct subfolders
- No orphan files remain in the old locations
- Permissions show the expected users

### File Naming Convention

Follow the user's naming convention from memory:
- `YYYYMMDD_Project_DocumentDescription_Author.pdf`
- E.g., `20260616_RankaOasis_MarketingOffice_3DRenders_Bhuvanesh.pdf`

For variations: append a descriptor suffix:
- `_Original_` for the source file
- `_GPTEnhanced` for AI-generated variations
- `_v2`, `_v3` for versioned updates

## Renaming Original Files in Place

When you find an existing file in a source folder (e.g., `np marketing office.pdf`) and want to rename it before or instead of moving:

```python
drive.files().update(
    fileId=file_id,
    body={'name': '20260616_RankaOasis_MarketingOffice_3DRenders_Original_Bhuvanesh.pdf'}
).execute()
```

## Change-Sensitive Duplicate Detection

After consolidation, check for duplicate files with different names. E.g., `np marketing office.pdf` (original name in source folder) and `20260616_RankaOasis_MarketingOffice_3DRenders_Bhuvanesh.pdf` (renamed copy already uploaded) may be the same content. When in doubt, leave both — the user will tell you if one should be removed.

## When to Use This Pattern

- **Project reorganization:** User says "bring everything under one folder"
- **Marketing asset consolidation:** Brochures, renders, photos scattered across years
- **After discovering orphan folders:** Old standalone folders that should be children of the main project
- **Before sharing a folder with new team members:** Consolidation first, permissions second

## When NOT to Use This Pattern

- **Files referenced by external systems** (Kelsa, third-party portals, published URLs) — moving changes the URL structure and breaks references
- **Active shared-drive files** (Shared Drives, not My Drive) — move requires different permissions
- **User only wants the new file uploaded** — ask before proposing full consolidation (Phase 3)
