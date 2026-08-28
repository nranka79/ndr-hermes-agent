# Personal Research Folder Convention (Nishant's Drive)

**Pattern:** Research documents on a specific company/topic are organized under `Personal > Research > [Topic Name]` in Nishant's Google Drive. Source PDFs, extracted text, and synthesized reports all live in the same topic folder.

## Folder Hierarchy

```
Personal/ (existing top-level folder, ID: 0B1Oc8cSaJXPGYkQtYXJDQWVBUVE)
  Research/ (created as needed)
    [Company/Topic Name]/ (e.g., "Blue Hat Solutions")
      Source Documents/ (optional subfolder, or inline)
      YYYYMMDD_Topic_Research_Report.html (synthesized output)
```

## When to Use

- User says "create a research folder for [topic] under Personal > Research"
- User uploads multiple PDFs/docs about a company and wants them filed for future reference
- A research report is being generated and needs a permanent home

## Workflow

### Step 1 — Check for existing Personal folder

```python
drive = build_service('drive', 'v3')
response = drive.files().list(
    q="mimeType='application/vnd.google-apps.folder' and name='Personal' and trashed=false",
    spaces='drive',
    fields='files(id, name, parents)'
).execute()
personal_folders = response.get('files', [])
```

### Step 2 — Create Research folder under Personal (if not exists)

```python
# Check if Research folder already exists under Personal
research_in_personal = drive.files().list(
    q=f"mimeType='application/vnd.google-apps.folder' and name='Research' and '{personal_id}' in parents and trashed=false",
    fields='files(id, name)'
).execute()
```

### Step 3 — Create topic subfolder

```python
topic_folder = drive.files().create(body={
    'name': 'Blue Hat Solutions',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': [research_folder_id]
}, fields='id, name, webViewLink').execute()
```

### Step 4 — Move existing research document into topic folder

If a previously-created research document exists elsewhere (e.g., Drive root, TMP folder):

```python
# Get current parents
file_meta = drive.files().get(fileId=doc_id, fields='parents').execute()
prev_parents = ','.join(file_meta.get('parents', []))

# Move to new location
drive.files().update(
    fileId=doc_id,
    addParents=topic_folder_id,
    removeParents=prev_parents,
    fields='id, name, parents'
).execute()
```

### Step 5 — Upload all new source PDFs

```python
from googleapiclient.http import MediaFileUpload
for name, path in pdf_files:
    media = MediaFileUpload(path, mimetype='application/pdf', resumable=True)
    drive.files().create(body={
        'name': name,
        'parents': [topic_folder_id]
    }, media_body=media, fields='id, name, webViewLink').execute()
```

### Step 6 — Deliver links to user

Provide:
- The topic folder link
- Direct links to each file
- Brief summary of what was filed

## Naming Conventions

| File Type | Pattern | Example |
|-----------|---------|---------|
| Source PDF (as uploaded) | `OriginalName.pdf` | `BHS_Financials_June2026.pdf` |
| Extracted text (for agent reference) | Keep in `/tmp/` only, not Drive | — |
| Synthesized report | `YYYYMMDD_Topic_Type.html` | `20260624_BlueHatSolutions_Investment_Research_Report.html` |
| Earlier research doc | `YYYYMMDD_Topic_Type.md` (or .html) | `20260624_BlueHatSolutions_PvtLtd_DeepDive_Research.md` |

## Pitfalls

- **Check if the Research folder already exists elsewhere first.** Nishant's Drive may have multiple `Research` folders under different parents (e.g., under `Hurestic/hardware/`). Always create the Research folder specifically under `Personal/` — verify the parent ID.
- **Extracted text files are transitory.** Save them to `/tmp/` for agent consumption. Do NOT upload `.txt` extracts to Drive unless the user explicitly asks for them — the PDFs are the canonical source.
- **Report naming must be date-prefixed.** Use `YYYYMMDD_DescriptiveName` format to match Nishant's overall Drive convention. Do NOT use version suffixes (v1, v2) — the date serves as versioning.
