# Drive Project Asset Consolidation — Scattered to Unified Folder

**Trigger:** User wants to reorganize scattered project files/folders across Drive into a single unified "Design & Marketing" or similar parent folder. Common when design assets (renders, brochures, photos, plans) have accumulated in multiple isolated folders.

## Workflow

### Phase 1 — Full Discovery

Before proposing any structure, map ALL locations where the project's assets currently live:

1. **Main project folder** — Check the primary Drive project folder first. List all subfolders and note which ones contain design/marketing assets vs. engineering/legal/approval docs.
2. **Standalone folders (root or other trees)** — Search Drive for folders not under the main project tree but clearly related (e.g., "Ranka Oasis Villa Designs", "Oasis Int/").
3. **Search by project keyword** — `q="name contains 'Ranka Oasis' and mimeType='application/vnd.google-apps.folder'"`
4. **Categorize each folder** by content type: renders, photos, floor plans, master plans, brochures, references, competitor data.

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

# List main project folder
main = drive.files().list(
    q="'<main_folder_id>' in parents and trashed=false",
    fields="files(id, name, mimeType)"
).execute()

# Search for related standalone folders
standalone = drive.files().list(
    q="name contains '<project_keyword>' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    corpora="allDrives",
    fields="files(id, name)"
).execute()
```

### Phase 2 — Map the Content

Create a structured map showing:
- **Within main tree**: what exists and where
- **Standalone folders**: what exists outside
- **Empty or near-empty folders**: note them (may be organizational remnants)

Present to user as a clear tree/list so they can see the full picture before deciding.

### Phase 3 — Propose Unified Structure

Suggest a category-based structure:

```
Project Name — Category/
  |-- Asset Type A/
  |-- Asset Type B/
  |-- Asset Type C/
  |-- References/
```

Name the parent folder descriptively: "Ranka Oasis — Design & Marketing" (project name + purpose category).

**Categories to consider:**
- Marketing Office Renders (or just Renders)
- Villa Renders / Villa Designs
- Entrance Concepts
- Brochures
- Site Photos / Progress Photos
- Master Plans & Floor Plans
- References (competitor data, design references, inspiration)

### Phase 4 — User Approval

Present both options:
- **Option A (Move/Consolidate):** Create the unified parent folder, MOVE all scattered folders/files into it. Breaks existing links — warn the user.
- **Option B (Copy/Preserve):** Create the unified parent folder, upload new files there, but leave existing folders untouched. No broken links.

Wait for explicit confirmation before any write operations.

### Phase 5 — Execute Consolidation

```python
# Create unified parent
folder_meta = {
    'name': 'Ranka Oasis — Design & Marketing',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': ['<project_root_folder_id>']
}
parent = drive.files().create(body=folder_meta, fields='id').execute()

# Create subfolders
subfolders = ['Marketing Office Renders', 'Villa Renders', 'Entrance Concepts', 
              'Brochures', 'Site Photos', 'Master Plans & Floor Plans', 'References']
sub_ids = {}
for name in subfolders:
    sf = drive.files().create(body={
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent['id']]
    }, fields='id').execute()
    sub_ids[name] = sf['id']

# Move files: for each file, find current parents, then update
for file_id, target_folder in files_to_move:
    meta = drive.files().get(fileId=file_id, fields='parents').execute()
    current_parents = ','.join(meta.get('parents', []))
    drive.files().update(
        fileId=file_id,
        addParents=target_folder,
        removeParents=current_parents,
        fields='id, parents'
    ).execute()
```

**Important:** When moving folders (not files), sub-folders' contents DON'T automatically get the new parent's permissions. Set permissions on the parent folder after all moves are done.

### Phase 6 — Set Permissions

```python
for email in editor_emails:
    drive.permissions().create(
        fileId=parent_folder_id,
        body={'type': 'user', 'role': 'writer', 'emailAddress': email},
        sendNotificationEmail=False
    ).execute()
```

Set on the PARENT folder — all descendants inherit the permission automatically.

### Phase 7 — Return Links

Return:
1. **Parent folder link** — for browsing
2. **Key file links** — for the specific files the user needs right now
3. **Permission confirmation** — list who has access

## Pitfalls

- **Broken existing links:** Moving files/folders breaks any previously shared links. Always warn the user before Option A.
- **Drive search staleness:** After moving files, Drive search may not reflect the new location for several minutes. Verify by direct `files().get()` not by search.
- **Duplicate files:** The same file may appear in multiple locations (Drive allows multiple parents). When moving from multiple locations to one, the file might already be in the target.
- **Empty subfolders:** Some existing folders may be empty (organizational stubs). Decide whether to keep or delete them — ask the user.
- **Folders outside main tree:** Standalone folders at Drive root or under different parents won't appear in the main project folder listing. You must discover them separately.
- **File ID context corruption:** After context compaction between turns, file IDs may have subtle character errors. Always re-list target folders via `files().list()` before write operations — do not reuse compacted IDs.

## When to Use This Pattern

- Marketing/design asset consolidation for a project
- Moving from scattered folder structure to organized hierarchy
- Onboarding new team members who need access to all project assets in one place

## When NOT to Use

- Single file upload (use simpler workflow)
- Reorganizing personal files not related to a project
- Legal/approval document filing (use `drive-notice-folder-workflow.md`)
