# Entity → Property Folder Consolidation on Drive

**Pattern: Consolidate multiple related properties under the same partnership/entity folder.**

When a single entity (partnership firm, company) owns interests in **multiple separate properties** — for example, ARYA Developers has both Binnamangala (via JDA with Chinnaraje Ammal) and Elegant Springdale (via compensation units from Muneer MKH/Elegant Developers) — the Drive folder structure should reflect Entity→Property hierarchy, not flat/scattered folders.

## The Pattern

```
Entity Name (e.g., "Arya Developers")
├── Property Name 1 (e.g., "Binnamangala")
│   ├── Legal/              ← Legal opinions, court documents
│   ├── Power of Attorney
│   ├── Supplementary Agreements
│   └── Timeline documents
├── Property Name 2 (e.g., "Elegant Springdale Agreements" or "Springdale")
│   ├── Sale Deeds
│   ├── JDAs
│   ├── Legal Docs/
│   └── Correspondence
└── Entity-level documents (Pan Card, Partnership Deeds, Reconstitution, etc.)
```

## When to Use

- A single partnership firm (Arya Developers) entered into JDAs for **multiple distinct properties** — each property gets its own subfolder under the entity
- The entity has entity-level documents (partnership deed, PAN, reconstitution, bank signatory) that are NOT specific to any one property
- Both entity and property documents currently exist but are **scattered** across different parent folders (Parked Properties, Current Properties, Legal, root) and owned by different users

## Workflow

### Step 1: Identify the Entity and All Related Properties

From the user's description or from a seed document (legal opinion), identify:
- The **entity name** (e.g., "Arya Developers" — may exist as a Drive folder)
- All **property names** the entity is involved with (e.g., "Binnamangala", "Elegant Springdale")
- The **relationship** between them (JDA, compensation units, GPA, etc.)

### Step 2: Check Existing Folder Structure

```python
# Find entity folder
entity_folder = drive.files().list(
    q="mimeType='application/vnd.google-apps.folder' and name='Entity Name'",
    pageSize=10, fields='files(id, name, parents, owners)'
).execute()

# Find property folders
property_folders = drive.files().list(
    q="mimeType='application/vnd.google-apps.folder' and (name contains 'Property1' or name contains 'Property2')",
    pageSize=50, fields='files(id, name, parents, owners)'
).execute()

# Find scattered entity-level files (partnership deeds, PAN, etc.)
entity_docs = drive.files().list(
    q="name contains 'EntityName' and mimeType!='application/vnd.google-apps.folder' and trashed=false",
    pageSize=100, fields='files(id, name, owners, parents)'
).execute()
```

### Step 3: Check Ownership Boundaries

Folders owned by other users (`ownedByMe: False`) **cannot be moved** into your Drive structure. The API returns:
```
HttpError 403: "Increasing the number of parents is not allowed"
```
with `capabilities.canAddMyDriveParent: False`.

**Detection:**
```python
f = drive.files().get(fileId=folder_id, fields="id, name, ownedByMe, capabilities(canAddMyDriveParent)").execute()
```

**Fix for cross-owner folders:** Create a **shortcut** inside the entity folder that points to the owned-by-another-user folder:
```python
shortcut = drive.files().create(body={
    'name': '⬅ Original Name (in OwnerName\'s Drive)',
    'mimeType': 'application/vnd.google-apps.shortcut',
    'parents': [entity_folder_id],
    'shortcutDetails': {'targetId': owned_folder_id}
}, fields='id,name,webViewLink').execute()
```

**Note:** The shortcut arrow prefix (➡ / ⬅) signals it's a pointer, not the real folder. Only the file owner can move the actual folder.

### Step 4: Move Movable Folders Under Entity

For folders you DO own (`ownedByMe: True`), move them into the entity folder:

```python
drive.files().update(
    fileId=property_folder_id,
    addParents=entity_folder_id,
    removeParents=current_parent_id,
    fields='id,parents'
).execute()
```

For root-level folders with no parents, use only `addParents`:
```python
drive.files().update(
    fileId=property_folder_id,
    addParents=entity_folder_id
    # No removeParents
).execute()
```

### Step 5: Rename Misspelled Names Consistently

After identifying the correct spelling from authoritative sources (legal opinion, registered deeds), find and rename ALL files/folders with misspellings:

| Common Misspelling | Correct |
|---|---|
| Binmangala, Bin Mangala, Birmangala, Binnamagala | **Binnamangala** |
| Sprindale, Springdate | **Springdale** |

```python
# Find all files with misspellings
query = "(name contains 'Binmangala' or name contains 'Bin_Mangala' or name contains 'Birmangala' or name contains 'Sprindale' or name contains 'Springdate') and trashed=false"
results = drive.files().list(q=query, pageSize=100, fields='files(id, name)').execute()

# Rename each with the correct spelling
for f in results.get('files', []):
    new_name = f['name'].replace('Binmangala', 'Binnamangala').replace('Bin_Mangala', 'Binnamangala').replace('Birmangala', 'Binnamangala').replace('Sprindale', 'Springdale').replace('Springdate', 'Springdale')
    drive.files().update(fileId=f['id'], body={'name': new_name}).execute()
```

**Pitfall:** Renaming a folder does NOT break existing shortcuts or shared links — Drive uses stable file IDs.

### Step 6: Move Scattered Entity-Level Files

Entity-level docs (Pan Card, Partnership Deed, Reconstitution, Release Deed, Bank Signatory Authority) that are sitting at Drive root need to be moved into the entity folder:

```python
entity_docs = [
    ('file_id_1', 'Desciption 1'),
    ('file_id_2', 'Desciption 2'),
]
for fid, desc in entity_docs:
    info = drive.files().get(fileId=fid, fields='parents').execute()
    old_par = info.get('parents', [])
    if old_par:
        drive.files().update(
            fileId=fid,
            addParents=entity_folder_id,
            removeParents=old_par[0],
            fields='id,parents'
        ).execute()
```

### Step 7: Move Timeline/Summary Docs Into Property Folders

If you created summary docs (timeline HTML, document inventory) that relate to a specific property, move them into that property's subfolder:

```python
for fid, desc in timeline_docs:
    info = drive.files().get(fileId=fid, fields='parents').execute()
    old_par = info.get('parents', [])
    if old_par:
        drive.files().update(
            fileId=fid,
            addParents=property_folder_id,
            removeParents=old_par[0],
            fields='id,parents'
        ).execute()
```

### Step 8: Verify Final Structure

```python
# List all items under entity folder
results = drive.files().list(
    q=f"'{entity_folder_id}' in parents and trashed=false",
    pageSize=50,
    fields='files(id, name, mimeType, owners)'
).execute()
for f in results.get('files', []):
    icon = '📁' if f['mimeType'] == 'application/vnd.google-apps.folder' else ('🔗' if f['mimeType'] == 'application/vnd.google-apps.shortcut' else '📄')
    owner = f.get('owners', [{}])[0].get('emailAddress','?')
    print(f'{icon} {f["name"]} (owner: {owner})')
```

## Known Pitfalls

- **Root-level shared folders can't be moved.** A folder owned by another user with `parents: None` (Drive root of that user) triggers "Increasing the number of parents is not allowed" even with `addParents` only. Create a shortcut instead.
- **Entity folder may be owned by a different user.** The Arya Developers folder is owned by admin2.blr@draas.com. You can still move YOUR files into it if you have `writer` access, but you can't move files owned by admin2 into it — they're already there.
- **The entity folder's existing contents** (Pan Card, Partnership Deed) may already be inside. Don't duplicate them.
- **File name searches may be stale** — after renaming, the old name may still appear in search results for a few minutes. Use direct ID lookup to verify.
- **Legal opinion seed documents** often contain 1990s-era spellings (Binnamangala, Birmangala) — the correct village name may differ from the legal opinion's spelling. When in doubt, use the spelling from the registered deeds or BBMP records.
