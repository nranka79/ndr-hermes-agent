# Drive Folder Ownership & Path Tracing

**Use when:** Placing confidential documents on Drive — need to ensure the target folder is owned by the user (not a shared/shared-with-me folder), or when tracing full folder hierarchy to decide where to file something.

## Trace a folder's full path to My Drive

```python
from tools.gws_auth import build_service
drive = build_service("drive", "v3")

def get_path(file_id, path_parts=None):
    """Trace folder parents up to root. Returns string like 'My Drive → Folder → Subfolder'"""
    if path_parts is None:
        path_parts = []
    
    f = drive.files().get(fileId=file_id, fields="id, name, parents, owners").execute()
    name = f.get('name', '?')
    owner = f.get('owners', [{}])[0].get('emailAddress', '?')
    path_parts.insert(0, f"{name} [{owner}]")
    
    parents = f.get('parents', [])
    if parents:
        return get_path(parents[0], path_parts)
    else:
        return " → ".join(path_parts)

# Usage
path = get_path(folder_id)
print(path)
# Output: "My Drive [user@domain.com] → TerraGreens [user@domain.com] → Riverstone [user@domain.com]"
```

## Check who owns a folder

```python
f = drive.files().get(fileId=folder_id, fields="id, name, owners, shared").execute()
owner = f.get('owners', [{}])[0]
print(f"Owner: {owner.get('emailAddress')} ({owner.get('displayName')})")
```

## Find folders owned by a specific user

```python
results = drive.files().list(
    q="mimeType='application/vnd.google-apps.folder' and 'user@domain.com' in owners",
    fields="files(id, name)"
).execute()
```

## Move a file between different owners' folders

When the source and target folders have different owners you may need to use update() with addParents/removeParents:

```python
# Move within same owner (or when you have write access to both)
moved = drive.files().update(
    fileId=file_id,
    addParents=target_folder_id,
    removeParents=current_parent_id,
    fields="id, parents"
).execute()
```

If this fails with permissions errors, use copy + delete:
```python
# Copy to target
copied = drive.files().copy(fileId=file_id, body={"parents": [target_folder_id]}).execute()
# Delete original
drive.files().delete(fileId=file_id).execute()
```

## Pitfalls
- `'ndr@draas.com' in owners` query syntax works — no quotes around the email inside the query string
- A folder without `parents` (empty list or `['root']`) is a root-level folder in My Drive
- The `owners` field is an array — always take `owners[0]`
- When using `parents` from API response, pass `parents[0]` to trace upwards — there's usually only one parent
