# Drive File Rename & Move Between Folders

Rename a file and/or move it into a different Drive folder using `files.update()`.

## Single File Rename

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

updated = drive.files().update(
    fileId='<file_id>',
    supportsAllDrives=True,
    body={'name': '20260530_Project_Document_v3'}
).execute()
print(f"Renamed to: {updated['name']}")
```

## Move File to a Different Folder

```python
# addParents = target folder, removeParents = current folder
drive.files().update(
    fileId='<file_id>',
    addParents='<target_folder_id>',
    removeParents='<current_folder_id>',
    supportsAllDrives=True
).execute()
```

Both rename and move can be done in a single call by combining the parameters.

## Find Current Parent Folder

```python
meta = drive.files().get(
    fileId='<file_id>',
    supportsAllDrives=True,
    fields='id, name, parents'
).execute()
for pid in meta.get('parents', []):
    parent = drive.files().get(fileId=pid, fields='id, name').execute()
    print(f"Folder: {parent['name']} ({parent['id']})")
```

## Moving Files from Folders You Don't Own (Ownership Boundary)

**Problem:** A folder shared with you (owned by another user) cannot be moved into your own folder hierarchy. The API returns:

```
HttpError 403: "Increasing the number of parents is not allowed"
```

with root cause `capabilities.canAddMyDriveParent: False`. This is a Drive security restriction — you cannot add a "My Drive" parent to a file owned by someone else.

**However: individual files INSIDE that shared folder CAN be moved** into your own folders. Each file has `capabilities.canMoveItemWithinDrive: True` even when the parent folder doesn't have `canAddMyDriveParent`.

### Detection

Before attempting a move, check ownership:

```python
f = drive.files().get(
    fileId=folder_id,
    fields="id, name, ownedByMe, capabilities(canAddMyDriveParent, canMoveItemWithinDrive)"
).execute()

if not f.get('ownedByMe'):
    cap = f.get('capabilities', {})
    print(f"⚠️ Not owned. canAddMyDriveParent={cap.get('canAddMyDriveParent')}, canMoveWithinDrive={cap.get('canMoveItemWithinDrive')}")
```

### Fix — Move files out individually

Instead of trying to move the folder itself, list all contents and move each file:

```python
# List all files in the shared folder (handle pagination — max 100 per page)
all_items = []
page_token = None
while True:
    resp = drive.files().list(
        q=f"'{source_folder_id}' in parents and trashed = false",
        fields="files(id, name, mimeType)",
        pageSize=100,
        pageToken=page_token
    ).execute()
    all_items.extend(resp.get("files", []))
    page_token = resp.get("nextPageToken")
    if not page_token:
        break

# Move each file into the target folder
for item in all_items:
    try:
        f = drive.files().update(
            fileId=item['id'],
            addParents=target_folder_id,
            removeParents=source_folder_id,
            fields='id, name'
        ).execute()
        print(f"✅ {item['name']}")
    except Exception as e:
        print(f"❌ {item['name']}: {e}")
```

**Important:** Some files inside shared folders may have `canCopy: False` at the file level. If a file fails to move AND fails to copy, create a shortcut instead:

```python
shortcut = drive.files().create(
    body={
        "name": f"→ {item['name']}",
        "mimeType": "application/vnd.google-apps.shortcut",
        "parents": [target_folder_id],
        "shortcutDetails": {"targetId": item['id']}
    },
    fields='id, name'
).execute()
```

### Edge case — Root-level files (parents=None)

When a file or folder returns `parents: None` (it's at Drive root), omit `removeParents` entirely — use only `addParents`:

```python
drive.files().update(
    fileId=file_id,
    addParents=target_folder_id
    # No removeParents — file is at root, has no parent to remove
).execute()
```

If this still returns `"Increasing the number of parents is not allowed"`, the file is at root AND owned by another user → fall back to copy or shortcut.

### Batch move pitfall — Pagination

Drive API returns max **100 results per page**. When listing files for a batch move, always use pagination (see loop above). If you skip pagination and only get one page, you'll silently miss files beyond 100.

## User Confirmation Pattern (Nishant)

Nishant requires **confirmation before executing** rename or move operations:

1. Query current file name and parent folder → share both
2. Propose new name and target folder
3. Ask "Shall I proceed?" → wait for explicit approval
4. Execute rename + move in a single `files.update()` call
5. Confirm completion with before/after state

## Nishant Naming Convention (Documented Patterns)

Two main naming patterns are used depending on the document type:

### Pattern 1: Dated Property/Business Documents

**Format:** `YYYYMMDD Description - Detail[ - Entity].ext`

- **Date prefix**: YYYYMMDD of the document content (not upload date). For date-range docs (e.g., tax receipts covering a financial year), use the start year as the date prefix.
- **Description**: Short description of document type (Legal Opinion, Sale Deed, Payment Receipts, Power of Attorney)
- **Detail**: Specific document identifier, party name, or case reference
- **Entity/Property**: Optional — who or what the document relates to

Examples from this session:
```
20161222 Legal Opinion - Binnamangala Property - Prashanth Acharya.pdf
20170526 Binnamangala Property Legal Opinion on OS 7005-2000 by Pingal Khan.docx
20161217 Binnamangala Property Payment Receipts Scanned.pdf
201409 Springdale Area Statement.pdf
Power of Attorney_Ranka_Binnamangala Property.docx
Supplementary Agreement_Ranka_Binnamangala Property.docx
```

### Pattern 2: CAD / Technical Drawings

**Format:** `UnitCode ContentType.dwg` or `UnitCode ContentType.pdf`

For architectural/engineering drawings where the unit code is the primary identifier:
```
C-202 Unit Floor Plan.dwg
C-202 Unit Model.pdf
D-210 Unit Floor Plan.dwg
D-010 GF Springdale Floor Plan.dwg
D101 GF Springdale Model.pdf
```

### Pattern 3: Undated / Entity Documents

**Format:** `DocumentType_Entity_Detail.ext`

For documents where the date is unknown or irrelevant:
```
Power of Attorney_Ranka_Binnamangala Property.docx
Supplementary Agreement_Ranka_Binnamangala Property.docx
Maintenance Due Chart - Elegant Springdale until Dec 2019
```

### Pattern 4: Inventoried Legal Sets (Pre-numbered)

For legal due diligence document bundles that already have a numbering system (00001, 00002, etc.), preserve the original numbering and naming:
```
0000 JDA between Muneer MKH & Arya Developers dtd 09APR2012.pdf
00011 Khatha Extract issued by BBMP dated 23.06.2012...
00012 Cancellation Deed Dated 09.05.2012 between Muneer KMH...
```

These already follow a consistent scheme — don't renumber them.

### Renaming Decision Tree

When analyzing an unnamed or poorly-named file:

1. **Is the date known?** → Use YYYYMMDD prefix (from filename, content date, email timestamp, or **Drive `createdTime`**)
2. **Is it a CAD file?** → Use Pattern 2 (Unit Code + Content Type), with date from `createdTime` prepended
3. **Is it part of a numbered legal set?** → Keep the numbering (Pattern 4)
4. **No date, no unit code?** → Use Pattern 3 (document type + entity)
5. **Generic names** (Legal Opinion.docx, Document.pdf) → Read the content to determine what it is, then apply the appropriate pattern above
6. **TEST_** or unnamed render files → Use `createdTime` from Drive metadata as the date prefix; the filename after the date should describe what the render shows (e.g. `20260626_NorthStar_Elevation_Render_Evening.jpg`)

## Batch File Analysis & Rename Workflow

When the user says "analyze all files and rename them using our naming convention":

### Step 1: Inventory the folder
```python
results = drive.files().list(
    q=f"'{folder_id}' in parents and trashed=false",
    pageSize=50,
    fields='files(id, name, mimeType, createdTime, modifiedTime)'
).execute()
```

### Step 2: For each file, determine the appropriate name

- **Filenames with obvious dates** (e.g., `20240810 Sale Deed...`) → Standardize the format
- **Generic names** (e.g., `C-202.dwg`, `Legal Opinion.docx`) → Read content or infer from context to assign a proper name
- **Misspelled names** (e.g., `Sprindale`, `Binmangala`, `Springdate`) → Correct spelling consistently
- **Inconsistent capitalization** (e.g., `sprindale area statemenT-Sept 2014.pdf`) → Normalize

### Step 3: Rename in batch
```python
def safe_rename(drive, file_id, new_name):
    try:
        old_name = drive.files().get(fileId=file_id, fields='name').execute()['name']
        if old_name != new_name:
            drive.files().update(fileId=file_id, body={'name': new_name}).execute()
            print(f'🔤 \"{old_name}\" → \"{new_name}\"')
    except Exception as e:
        print(f'❌ Failed: {e}')
```

### Step 4: Verify
Re-list the folder to confirm all renames took effect. Note: Drive search may have stale index — use direct `files().list()` on the parent folder, not a `name contains` query.

## Pitfalls

- **Drive search may be stale**: After a file is created or modified, searching by `name contains 'X'` with `corpora='allDrives'` may return empty for several minutes. This is a Drive search indexing delay — not a permanent state. If search returns 0 results but you know the file exists, try:
  - Searching without `corpora` (defaults to `user`)
  - Using `fullText contains 'X'` instead of `name contains 'X'`
  - Direct ID lookup via `files().get(fileId=...)`
  - Retrying the search after accessing the file via a shared link (which refreshes the index)
- **Google Docs vs. native files**: Google Docs don't have file extensions. The naming convention `YYYYMMDD Description - Detail` works for both.
- **Multiple parents**: Drive files can have multiple parents. `removeParents` removes only the specified parent, not all parents.
- **DWG and other binary CAD files**: The agent cannot analyze DWG file content. When renaming DWG files, look for unit codes in the filename (C-202, D-210, D-010) and use them as the primary identifier with `Unit Floor Plan.dwg` as the type. Always prepend the `createdTime` date as YYYYMMDD prefix.
- **File already has a date in the name**: If the filename already carries a date pattern (e.g. `FINAL_MM_07-05-2026.dwg` or `R1_2026-04-17`), leave it alone — the file follows a convention even if not in YYYYMMDD format. The embedded date serves as a version/revision identifier that may differ from Drive's `createdTime` (the file was last modified on a later date).
- **No exact filename match → similar file**: When the user asks for a specific filename (e.g. TEST_17) that doesn't exist, search for similar names in the same folder (TEST_7, TEST_15). The user likely remembers the approximate name. Report gracefully rather than saying "not found" — offer the closest match.
- **Don't renumber legal due diligence sets**: Folder like `Elegant Springdale Legal Docs` with 45+ pre-numbered files (00001 through 00045) already follows a consistent naming scheme for indexed document sets. Renaming them individually would destroy the index reference. Only rename files that DON'T belong to a pre-numbered set.
