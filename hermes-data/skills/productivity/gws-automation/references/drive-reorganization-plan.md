# Drive Folder Reorganization Workflow

**When the user asks to reorganize scattered Drive folders** (multiple folders across different parents with overlapping/duplicate content).

## Discovery Phase — Find all related folders

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

# 1. Find the main folder
results = drive.files().list(
    q="mimeType='application/vnd.google-apps.folder' and name contains 'ProjectName'",
    orderBy='name', pageSize=20,
    fields='files(id,name,parents)'
).execute()

# 2. Find ALL scattered folders that should be under the umbrella
results = drive.files().list(
    q="mimeType='application/vnd.google-apps.folder' and (name contains 'Keyword1' or name contains 'Keyword2')",
    orderBy='name', pageSize=50,
    fields='files(id,name,parents)'
).execute()
```

## Inventory Phase — Map the full tree

```python
def list_folder(folder_id, indent=0):
    results = drive.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        orderBy='name', pageSize=100,
        fields='files(id,name,mimeType)'
    ).execute()
    for item in results.get('files', []):
        prefix = '  ' * indent + ('[+] ' if item['mimeType'] == 'application/vnd.google-apps.folder' else '    ')
        print(f'{prefix}{item["name"]}')
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            list_folder(item['id'], indent + 1)
```

## Analysis — Identify issues

- **Scattered folders** — same project name appearing under different parent folders (DRA Projects, DRA Realty, standalone)
- **Duplicate files** — same filename appearing in 3+ locations (sale deeds, legal opinions)
- **Wrong categorization** — engineering drawings mixed with legal docs, investor agreements outside finance folder

## Deliverable — Create a Reorganization Plan

Generate a `.md` file (as a Google Doc on Drive root):

```python
# Create the plan as a Google Doc
content = """# Project Name — Drive Reorganization Plan

## Current State
Found N scattered folders across M locations.
Duplicate files in X locations.

## Proposed Structure
Project_Name/
├── 01_Legal_and_Title_Docs
├── 02_Partnership_and_Firm_Docs
├── 03_Approvals_and_Regulatory
├── 04_Engineering_and_Design
├── 05_Investors_and_Finance
├── 06_Marketing_and_Brochures
├── 07_Communication_and_Correspondence
├── 08_Acquisitions
├── 09_Project_Management
├── 10_Reference_Docs
└── _Archive

## Proposed Actions (by phase)
Phase 1 — Rename & Create Umbrella
Phase 2 — Consolidate Scattered Folders (numbered steps)
Phase 3 — Deduplication
Phase 4 — Cleanup

## Files Already Correct
...

## Files Added Recently
...
"""

docs_service = build_service('docs', 'v1')
doc = docs_service.documents().create(body={'title': 'Project_Drive_Reorganization_Plan.md'}).execute()
docs_service.documents().batchUpdate(
    documentId=doc['documentId'],
    body={'requests': [{'insertText': {'location': {'index': 1}, 'text': content}}]}
).execute()
```

## Execution Pattern

1. **Never move without confirmation** — present the plan, let user review
2. **Use `drive.files().update(fileId, addParents=new_folder, removeParents=old_parent)` to move folders**
3. **Moves are non-destructive** — file IDs and share links are preserved
4. **Move sub-folders inside the umbrella first**, then the umbrella folder itself if renaming

```python
# Move a file/folder into the new structure
drive.files().update(
    fileId=FILE_ID,
    addParents=TARGET_FOLDER_ID,
    removeParents=CURRENT_PARENT_ID,
    fields='id,parents'
).execute()
```

### Handling Folder Name Queries with Special Characters

Single quotes (`'`) in folder names break Drive API query strings. Use `name contains` with the non-quoted portion instead:

```python
# WRONG — single quote in name breaks the query
q=f"name='Doc's Related to Road'"

# RIGHT — use contains with partial name
q=f"name contains 'Doc' and name contains 'Related to Road'"
# OR: list ALL items and filter in Python
items = drive.files().list(q=f"'{parent}' in parents", ...).execute()
for item in items.get('files', []):
    if "Doc's Related" in item['name']:
        # move this item
```

## Structured Audit Report — Pre-Reorganization Discovery

**When the user asks "where all are the files related to X?"** before deciding on reorganization. This is the discovery phase — produce a comprehensive owner-by-owner, folder-by-folder breakdown that the user can review before approving any moves.

### Step 1 — Find ALL Related Folders Across All Owners

Ranka Amber files were scattered across **12+ folders owned by 4 different accounts** (ndr@draas.com, sales1.blr@draas.com, psingh@draas.com, findingform.design@gmail.com). Search for each owner using a prepared query list:

```python
from tools.gws_auth import build_service

drive = build_service("drive", "v3")

# Verify which account you're searching
about = drive.about().get(fields='user').execute()
print(f"Searching as: {about['user']['emailAddress']}")

# Use multiple keyword combinations — Drive search is exact substring
queries = [
    "name contains 'Ranka Amber'",
    "name contains 'Raghu' and name contains 'Amber'",
    "name contains 'Whitefield' and name contains '14K'",
    "name contains 'SSA' and name contains 'Amber'",
]

for q in queries:
    results = drive.files().list(
        q=q + " and trashed=false",
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        corpora='allDrives',
        fields='files(id, name, mimeType, owners, parents)',
        pageSize=50
    ).execute()
```

### Step 2 — Map Ownership

For each folder found, identify the owner. Folders owned by **other accounts CANNOT be moved** into your Drive structure:

```python
for f in folders:
    owner = f['owners'][0]['emailAddress']
    owner_map.setdefault(owner, []).append(f)
```

### Step 3 — Catalog Folder Contents + Resolve Shortcuts

List all files AND subfolders. If any file is a **shortcut** (mimeType='application/vnd.google-apps.shortcut'), resolve its target:

```python
shortcut_details = drive.files().get(
    fileId=shortcut_id,
    fields='id, name, shortcutDetails(targetId, targetMimeType)'
).execute()
target_id = shortcut_details['shortcutDetails']['targetId']
target = drive.files().get(
    fileId=target_id,
    fields='id, name, owners'
).execute()
print(f"  → points to: {target['name']} (owner: {target['owners'][0]['emailAddress']})")
```

### Step 4 — Present the Audit Report (Nishant's preferred format)

```
### 1️⃣ Folder Name [owner@email.com]
**Path:** My Drive → Subfolder (or Root-level)
**N files + M subfolders:**
- 📄 Category description (JDA, GPA, term sheets...)
- 📁 Subfolder name (contents description)
```

Format rules:
- **Numbered folders** (1️⃣ 2️⃣ 3️⃣) for easy reference
- **Owner in square brackets** after folder name
- **Path** shows where the folder sits in that user's Drive
- **File/subfolder counts** in bold
- **Bullet lists** for categories (not every filename)
- **Subfolders** shown as 📁

### Step 5 — Summary Section

```
**The problem:** Files are spread across N folders owned by M different people.
**Your `[main folder]`** is the best starting point — it has [X, Y, Z]. But it's missing [A, B, C].
```

### Step 6 — Let the User Drive the Plan

After presenting the audit, ask: *"Want me to suggest a reorganization plan?"* — do not prescribe moves until the user has seen the full landscape.

---

## Pitfalls

- **Folders owned by other users CANNOT be moved** — Drive API returns "Increasing the number of parents is not allowed" when you try to move a folder owned by another account (e.g., a contractor's Gmail). The API reports `parents=[]` for these folders. Only the owner can change the parent. Workaround: ask the owner to move it, or share the target folder so the owner can move it themselves.
- Some folders may return 404 (already deleted) — skip and note
- Renaming a folder does not break internal links; moving it does not either (Drive uses stable IDs)
- Check for external references (Google Doc links, spreadsheet formulas) before deep reorganization
- Always verify after each move batch — re-read the new parent's contents

## Property Unit Folder Pattern (Nishant's Real Estate Docs)

When reorganizing real estate property documents (apartments/flats), Nishant uses this standard folder structure:

```
Property_Name/
├── <UnitNumber>/
│   ├── Title Related/    ← All title documents, khatha, sale deeds, tax receipts, ECs, allotment letters
│   └── Plans/            ← Floor plans, DWG drawings, survey docs, site photos, rendered images
```

### Step-by-step Execution

1. **Create the umbrella folder** — top-level project folder (e.g., "Embassy Habitat")
2. **Create unit subfolders** — one per apartment/flat number (e.g., "1503", "914")
3. **Create standard subfolders** under each unit: "Title Related" and "Plans"
4. **Move existing files** from old scattered locations into the correct unit/type folder
5. **Copy shared folder content** — if survey drawings/photos were shared by a third party, copy them into `Plans`
6. **Rename all files** per `YYYYMMDD_Project_DocType_Author` convention (see `drive-file-rename-move.md`)
7. **Ask about unanalyzable files** — DWG files need user input for proper naming

### Copying from Shared Folders

```python
# Copy a file from a shared folder (third-party owned) into your Drive structure
copy = drive.files().copy(
    fileId='<shared_file_id>',
    body={'name': '<desired_filename>', 'parents': ['<target_folder_id>']},
    fields='id,name,webViewLink'
).execute()
```

- Use `drive.files().copy()` — this creates a new file in your Drive (the original stays in the sharer's Drive)
- Supports any mimeType (PDF, DWG, JPG, etc.)
- Batch-copy multiple files by iterating over the shared folder contents
- After copying, rename following the naming convention

### Identifying Documents for Triage

When moving files from a scattered folder into the standard structure, triage document type:

| Category | Documents | Target |
|---|---|---|
| **Title Related** | Sale Deeds, Khatha Certificates & Extracts, Property Tax Receipts (all years), Encumbrance Certificates (ECs), BESCOM Transfer Letters, E-Khatha, Allotment Letters (original & parking), Khatha Transfer Receipts, Loan Closure & Discharge Letters, Society NOCs, Mortgage Documents, POAs, Agreements of Sale, MOEs, Declaration Deeds, Indemnity Bonds | `Title Related/` |
| **Plans** | Floor Plans (PDF/DWG), Survey Drawings, Sanctioned Plans, Site Photos, Rendered Images, Interior Design Docs | `Plans/` |
