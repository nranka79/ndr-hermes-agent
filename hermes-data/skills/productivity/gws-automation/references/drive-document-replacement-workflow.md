# Drive Document Replacement Workflow

When the user provides a **cleaner version** of a document already on Drive and wants to **replace** the existing file(s) — upload the new version, delete the old ones, rename appropriately, and share with a specific team.

## When to Use

**Trigger:** User says "this is a cleaner version of [document X], delete the old one and keep only this" or sends a clean scan saying "replace the existing file."

## Workflow

### Step 1 — Identify the Old Files

The old document may exist in **multiple copies** across different folders. Search Drive by name pattern:

```python
results = drive.files().list(
    q="name contains 'occupancy' and name contains 'Iris' and trashed=false",
    fields="files(id, name, parents, webViewLink)",
    pageSize=20
).execute()
```

**Key insight:** Old files might be in different parent folders (e.g., project folder + legal set folder). Check each one's parent to understand the duplication.

### Step 2 — Confirm the Deletion Plan with User

Before deleting anything, list what will be removed and where the new file will go.

### Step 3 — Upload the New File

Use the same naming convention as the old file(s):

```python
from googleapiclient.http import MediaFileUpload

file_meta = {
    'name': '20260604_Domlur_RankaIris_OccupancyCertificate.pdf',
    'parents': [target_folder_id]
}
media = MediaFileUpload(local_path, mimetype='application/pdf')
uploaded = drive.files().create(body=file_meta, media_body=media, fields='id, name, webViewLink').execute()
new_file_id = uploaded['id']
```

### Step 4 — Share with Specific Viewers

When the user names specific people to share with, look up their emails from the NDR DRAAS contacts sheet or from known employee records:

```python
viewers = [
    ('vkdas@draas.com', 'Vinod'),
    ('bhavik.92@gmail.com', 'Bhavik'),
    ('piyush.92@gmail.com', 'Piyush'),    # ⚠️ Piyush no longer uses drahomes.in — use Gmail
    ('sales1.blr@draas.com', 'Bharat'),
]

for email, name in viewers:
    drive.permissions().create(
        fileId=new_file_id,
        body={'type': 'user', 'role': 'reader', 'emailAddress': email},
        fields='id'
    ).execute()
```

Also set `anyone` with link access so non-Google users can view.

### Step 5 — Delete Old Files

```python
for fid in old_file_ids:
    drive.files().delete(fileId=fid).execute()
```

**⚠️ Permission failure:** If a file is owned by another user (e.g., owned by vkdas@draas.com) and you only have writer access, `delete()` raises `HttpError 403: insufficientFilePermissions`. Inform the user which files couldn't be deleted and why. The owner needs to delete them.

### Step 6 — Verify

Confirm deletion by trying `drive.files().get(fileId=old_id)` — it should raise 404.

## Edge Cases

| Issue | Resolution |
|-------|-----------|
| Old file owned by someone else | Cannot delete. Ask owner to remove. |
| Old files in different folders | Upload new file to the primary project folder (where the original was). |
| Same filename used for all versions | The new upload with same name in same folder cleanly replaces it. |
| User specifies a viewer with outdated email | Check contacts sheet for alternative email (e.g., Piyush's drahomes.in was replaced by piyush.92@gmail.com). |

## Naming Convention

Follow the existing naming pattern from the old files: `YYYYMMDD_Project_DocumentType.pdf`
- Date = document content date, not upload date
- Project = project name (Ranka Iris, Ranka Amber, etc.)
- DocumentType = OccupancyCertificate, SaleDeed, etc.
