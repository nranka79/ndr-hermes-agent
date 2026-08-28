# TMP → Project Folder Workflow

Complete recipe for moving a file from the TMP folder into a project's Customer Documents folder.

## Step 1: Find the file in TMP

```python
svc.files().list(
    q="'<TMP_FOLDER_ID>' in parents and trashed=false and "
      "name contains '<keyword>'",
    spaces='drive',
    fields='files(id,name,mimeType,webViewLink,modifiedTime)'
).execute()
```

**TMP folder ID:** `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`

## Step 2: Find the project folder (writable copy)

Search for the project name. You'll likely find two copies:
1. Under DRA Projects — owned by bk@findingform.design, read-only
2. Under shared drive root (same parent as TMP) — owned by ndr, writable

```python
f = svc.files().get(fileId=FOLDER_ID, fields='id,name,owners,capabilities').execute()
if not f['capabilities'].get('canAddChildren', False):
    # This is the read-only copy — find the ndr-owned one
```

## Step 3: Create folder structure

```python
# Create Customer Documents if needed
cust = svc.files().create(body={
    'name': 'Customer Documents',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': [PROJECT_ID]
}, fields='id,name').execute()

# Create customer subfolder
cust_folder = svc.files().create(body={
    'name': 'CustomerName',  # Use spelling from file name
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': [cust['id']]
}, fields='id,name').execute()
```

## Step 4: Move the file

```python
updated = svc.files().update(
    fileId=FILE_ID,
    addParents=NEW_PARENT_ID,
    removeParents=OLD_PARENT_ID,  # TMP folder ID
    fields='id,name,parents,webViewLink'
).execute()
```

## Error Handling

| Symptom | Cause | Fix |
|---|---|---|
| `InsufficientParentPermissions` 403 | Destination folder is read-only (DRA Projects copy) | Use the shared drive copy instead |
| `File not found` 404 | Wrong file ID | Search TMP again with broader query |
| `Invalid field selection` 400 | Wrong field name in `fields` param | Use only valid Drive API v3 field names |
