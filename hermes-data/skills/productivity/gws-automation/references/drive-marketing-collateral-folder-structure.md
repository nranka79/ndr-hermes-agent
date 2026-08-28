# Drive Marketing Collateral Folder Structure

Creating and organizing marketing collateral on Drive for real estate projects.

## Entity → Project → 6-Subfolder Pattern

When a user has marketing collateral from an agency (Form and Flow, Krackerz, etc.) for a real estate entity that owns multiple projects:

```
TerraGreens LLP (Entity)
├── Project Name (e.g. Riverstone)
│   ├── 01_Marketing_Videos_and_Film
│   ├── 02_Brochures_and_Presentations
│   ├── 03_Renders_and_Designs
│   ├── 04_Content_and_Copy
│   ├── 05_Social_Media_and_Digital
│   └── 06_Print_Signage_and_Displays
└── Another Project (e.g. Soul & Solace, Alipur)
    ├── 01_Marketing_Videos_and_Film [same 6 folders]
    └── ...
```

This mirrors the Ranka Udaya 6-bucket scheme adapted for marketing-specific assets.

## When to Copy vs Move

If the same marketing asset (video, PDF brochure, render) is relevant to **multiple projects**, COPY it to each project's folder rather than moving the original. Use `drive.files().copy()` not `drive.files().update()`:

```python
drive = build_service("drive", "v3", service_name="google-draas")

# Upload original once
uploaded = drive.files().create(
    body={"name": "asset.pdf", "parents": [project_a_folder]},
    media_body=media,
    fields="id"
).execute()

# Copy to other projects
for folder_id in [project_b_folder, project_c_folder]:
    drive.files().copy(
        fileId=uploaded["id"],
        body={"name": "asset.pdf", "parents": [folder_id]},
        fields="id"
    ).execute()
```

## Assets from Shared (External) Drive Folders

When the agency shares a folder with you (not owned by your account):
1. List contents with `drive.files().list(q=f"'{shared_folder_id}' in parents")`
2. Download via `drive.files().get_media(fileId=...)` with `MediaIoBaseDownload`
3. Upload to your own Drive via `drive.files().create(media_body=MediaFileUpload(...), resumable=True)`
4. For large files (>100 MB), use `resumable=True` and 10 MB chunks

The shared folder is owned by the agency; you cannot move files from it directly. Copy (download → upload) is the only path.

## Pitfalls

- **Folders exist but have old names**: Check before creating — rename existing folders (e.g. "Alipur 300" → "Sol and Solis (Alipur)") rather than creating duplicates.
- **Marketing agencies often name videos differently from project names**: E.g. "Soul & Solace" is the brand name for project "Sol and Solis, Alipur". Keep both names in metadata.
- **6-folder naming**: Use zero-padded numbers (01_, 02_, etc.) so Google Drive sorts them consistently.
- **Copy across projects**: Duplicate files don't consume additional Drive quota (same file, same MD5, Drive dedupes internally). But copies are independent for permission purposes.
