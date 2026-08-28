# Project File Inventory — No Seed Document

When the user gives you the project name (or name variants) directly — not a seed document — and asks you to "find everything" on Drive.

## When to Use

- User says "find all files related to [project X] on my Drive" with multiple aliases
- User gives you name variants directly (e.g. "North Star, also called Northstar, North-Star, Alal Sandra")
- User wants to locate images/renders specifically across a scattered folder structure
- Task is a comprehensive file listing, not an analysis/dossier

## Workflow

### Step 1 — Collect All Name Variants

The user often provides aliases in their first message. Extract ALL of them:

- Full name (Ranka North Star)
- Composed variant (North Star / Northstar / North-Star / NorthStar)
- Known alias (Alal Sandra / Allalsandra)
- Partial combinations (Ranka North, North Star, etc.)
- Common misspellings or phonetic variants

**Do NOT ask the user to clarify aliases they already gave.** They just told you.

### Step 2 — Search Drive with Multiple Name Queries

Use `name contains` (not `fullText contains`) — the user wants files BY NAME, not files that merely mention the project in their content:

```python
queries = [
    "name contains 'Ranka' and name contains 'North'",
    "name contains 'North Star' or name contains 'Northstar'",
    "name contains 'North' and name contains 'Star'",
    "name contains 'Alal Sandra' or name contains 'Allalsandra'",
    "name contains 'Ranka North'",
    "name contains 'RankaN'",  # catch any RankaN* combos
]

all_results = []
seen_ids = set()

for q in queries:
    page_token = None
    while page_token is not None or len(all_results) == 0:
        results = drive.files().list(
            q=q,
            spaces='drive',
            fields='files(id, name, mimeType, webViewLink, parents, modifiedTime, size)',
            pageToken=page_token,
            pageSize=100,
            orderBy='folder,modifiedTime desc'
        ).execute()

        for f in results.get('files', []):
            if f['id'] not in seen_ids:
                seen_ids.add(f['id'])
                all_results.append(f)

        page_token = results.get('nextPageToken')
```

**Key points:**
- Deduplicate by file ID — same file matches multiple queries
- Use `spaces='drive'` to include both My Drive and shared drives
- Order by `folder,modifiedTime desc` so folders appear first, then files by recency
- Paginate — each query can return 100+ results

### Step 3 — Map Folder Hierarchy

After collecting all results, identify parent folders to understand the structure:

```python
# Collect all unique parent folder IDs
parent_ids = set()
for f in all_results:
    for pid in f.get('parents', []):
        parent_ids.add(pid)

# Fetch folder names for each parent
for pid in parent_ids:
    folder = drive.files().get(fileId=pid, fields='id, name, webViewLink').execute()
    print(f"{folder['name']}: {folder['webViewLink']}")
```

This reveals:
- Which folders are standalone (at root level or under a general project parent)
- Which folders are nested inside others
- Whether the same files appear in multiple parent folders (duplication)

### Step 4 — List Contents of Every Identified Folder

For each folder found in Steps 2-3, list its contents:

```python
for folder_id, folder_name in major_folders:
    results = drive.files().list(
        q=f"'{folder_id}' in parents",
        fields='files(id, name, mimeType, webViewLink, modifiedTime, size)',
        pageSize=100,
        orderBy='folder,modifiedTime desc'
    ).execute()

    for f in results.get('files', []):
        ftype = "folder" if f['mimeType'] == 'application/vnd.google-apps.folder' else "file"
        # classify by type
        img = "IMAGE" if f['mimeType'].startswith('image/') else ""
        pdf = "PDF" if f['mimeType'] == 'application/pdf' else ""
        dwg = "DWG" if 'dwg' in f['mimeType'] or f['name'].endswith('.dwg') else ""
        pres = "PPTX" if 'presentation' in f['mimeType'] else ""
        print(f"  [{ftype}] {f['name']} {img}{pdf}{dwg}{pres}")
```

### Step 5 — Identify Images, Renders & Visual Files

This is often the user's primary interest. Classify files by these patterns:

| Type | Signal |
|------|--------|
| **High-res render photos** | Filename contains `FINAL_X - Photo.jpg`, `Photo.jpg` at 5+ MB |
| **Reference images** | Filename contains `reference`, `reference elevation render`, `reference image` |
| **Site photos** | WhatsApp images (IMG-YYYYMMDD-WA*.jpg) at 100-200 KB |
| **Sketchup files** | Filename contains `Sketchup`, `.skp` |
| **Render PDFs** | PDF filename contains `Elevation`, `Render`, `E-Brochure`, `final` at 5+ MB |
| **DWG drawings** | `.dwg` extension |
| **Presentations** | `.pptx` containing renders |
| **AI Studio prompts** | mimeType `application/vnd.google-makersuite.prompt` — may contain render inspirations |

Code pattern:
```python
IMAGE_MIME_PREFIXES = ('image/',)
RENDER_KEYWORDS = ('render', 'elevation', 'FINAL', 'Photo.jpg', 'Sketchup')
DOC_RENDER_KEYWORDS = ('Elevation Render', 'E-Brochure', 'final')

def is_render(f):
    name = f.get('name', '')
    mt = f.get('mimeType', '')
    sz = int(f.get('size', 0))

    # Direct images
    if mt.startswith('image/'):
        # 5+ MB images are usually high-res renders
        if sz > 5 * 1024 * 1024:
            return True
        if any(kw.lower() in name.lower() for kw in RENDER_KEYWORDS):
            return True

    # PDFs
    if mt == 'application/pdf' and any(kw.lower() in name.lower() for kw in DOC_RENDER_KEYWORDS):
        return True

    # Presentations
    if 'presentation' in mt and any(kw.lower() in name.lower() for kw in RENDER_KEYWORDS):
        return True

    return False
```

### Step 6 — Present Organized Summary

Structure the output clearly. The user asked "list everything" so organize by:

1. **Folders** — each with a clickable Drive link, grouped by hierarchy level
2. **Images/Renders** — the key focus, listed with file sizes
3. **Render PDFs** — separate section
4. **Presentations containing renders** — separate section
5. **DWG files** — technical drawings
6. **Other documents** — spreadsheets, legal docs, etc.

For each file, include:
- Clickable Drive link
- File size (MB/KB)
- File type indicator

The links should be the `webViewLink` from the Drive API — these are shareable links the user can click directly.

## Key Differences from Seed-Document Workflow

| Aspect | Seed Document (existing ref) | Name Variants (this ref) |
|--------|------------------------------|--------------------------|
| Starting point | User shares a document | User speaks name variants |
| Search scope | `fullText contains` for identifiers | `name contains` for name patterns |
| Output | Analysis + gap analysis + dossier | File/folder inventory with links |
| Folder mapping | Optional (gap analysis) | Central (user wants to see structure) |
| Image/render focus | No special treatment | Primary use case |

## Pitfalls

- **Duplicate renders.** The same FINAL_ renders often appear in multiple folders (main project folder + Renders sub-folder + a separate "Renders & Elevation" folder). Don't treat them as separate finds — note the duplication.
- **Empty skeleton folders.** New project structures may have empty sub-folders (Architectural > Renders, Sketchup, Revit, Autocad, PDF) that are scaffolding. List them but flag as empty.
- **Shortcut files.** Drive shortcuts (.shortcut mimeType) point to the real file elsewhere. Include them but note they are shortcuts.
- **Mixed case naming.** Drive search is case-insensitive for `name contains` but the same project may have files named in ALL CAPS, Title Case, and lowercase across different folders.
- **Old vs new naming.** Old files (pre-2025) may use different naming conventions than recent files. Search both `NorthStar` and `North Star` and `NORTH STAR`.
- **Root-level folders.** The same project may have folders at different hierarchy levels — one under "Current Properties", one at Drive root, one under "DRA Projects". Collect all parent folders to reveal this.
- **Large files.** Render images and PDFs are 5-15 MB each. Multiple renders can total 100+ MB. Mention sizes so the user knows what's large.
- **MIME type quirks.** DWG files may appear as `image/vnd.dwg` or `application/acad` depending on how they were uploaded. Check both mimeType AND filename extension.
