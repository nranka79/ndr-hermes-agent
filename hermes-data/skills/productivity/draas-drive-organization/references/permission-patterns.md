# DRAAS Drive Permission Patterns

## Folder Hierarchy

DRA Projects (`1wYtUJJwELLu7o1dIr38p_QthRHaMwWvH`) — owned by bk@findingform.design
  ├── Serenity Hill View (`1IE7eHHYhpODMDbh8ehVkAVguv9yVrv7Z`)
  │   ├── Architectural (subs: Revit, PDF, Renders, Sketchup, Autocad)
  │   ├── Brochure
  │   ├── Content Marketing
  │   ├── Destination Wedding Resort Proposal
  │   ├── Drone Footage
  │   ├── Investor
  │   ├── Legal
  │   └── Structural
  ├── Amber
  ├── Riverstone
  ├── Edwardian Chambers
  ├── Ranka Udaya
  ├── Ranka Oasis
  └── Northstar

## Capability Check: DRA Projects vs ndr-owned folders

### DRA Projects project folder (e.g., Serenity Hill View)
- `owners[0].emailAddress`: bk@findingform.design
- `owners[0].me`: false
- `canAddChildren`: **false** (cannot create new folders here)
- `canEdit`: **false** (cannot edit folder metadata)
- `canDelete`: **false**
- `canComment`: true

### Existing subfolder inside DRA Projects (e.g., Legal subfolder)
- `canAddChildren`: may be true (children-of-subfolders may have different perms than the root)
- `canEdit`: true (can modify file contents inside)
- **Can move files INTO existing subfolders** even though the project root blocks folder creation

## Key Permission Rules (Verified Jul 2026)

1. **`canAddChildren: false` on a folder** ≠ the contents are read-only. Files inside can still be edited, moved in/out, and deleted.
2. **Moving files across ownership boundaries** works when the destination is an existing subfolder. The receiving folder's permissions are checked per-item, not inherited from the project root.
3. **`files().delete()` permanently deletes** the item (Drive v3 API, does NOT go to trash). Use `files().update(body={'trashed': True})` if you want trashing behaviour.
4. **Creating new folders** IS blocked at the project-root level. Create in your own Drive first, then shortcut or ask the owner.

## Drive API Field Selection

To check permissions:
```python
f = svc.files().get(
    fileId=FOLDER_ID,
    fields='id,name,parents,driveId,capabilities,owners'
).execute()
```

Key `capabilities` fields:
- `canAddChildren` — can create subfolders/files inside
- `canEdit` — can modify file metadata and content
- `canAddMyDriveParent` — can move into My Drive
- `canMoveItemWithinDrive` — can reorganize

## Merging Two Parallel Folder Structures

When a project has duplicate folder trees (one at Drive root, one under DRA Projects):

1. **List contents** of both root-level and correct folders — compare subfolder names
2. **Identify what has actual content** — empty subfolders can be ignored/deleted
3. **Move files** (not folders!) from root subfolders into matching correct subfolders using `files().update(fileId, addParents=newId, removeParents=oldId)`
4. **Delete empty subfolders** after moving their contents out
5. **Delete the root-level folder** — `files().delete()` permanently removes it

**Pitfall:** `files().delete()` on a parent folder also deletes its children (moves to nowhere — they become orphan 404s). Move children out FIRST, then delete the parent.

**Pitfall:** When the root and destination are owned by different users, moving files INTO existing subfolders works, but creating new subfolders at the destination root is blocked. Plan around this limitation.
