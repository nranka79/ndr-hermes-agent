# Drive Folder Copy, Rename & Survey-Grouped Index

Copy documents from a source Drive folder to a new banking/lending folder, rename them with a structured convention, and generate an index spreadsheet grouped by Indian land survey number.

## When to use

- A user has a large document repository (JDA, GPAs, sale deeds, legal opinions, approvals) and needs a clean subset for bank/NBFC due diligence
- Documents need to be renamed with a structured convention: `YYYY-MM-DD, Village, Description, RegNo.ext`
- The index needs to group documents by **survey number** (e.g., Sy 158/1C3, Sy 166/2B, Sy 177)
- The original folder must be left untouched

## Workflow

### Phase 1 — List and index all source files recursively

```python
from tools.gws_auth import build_service
service = build_service("drive", "v3")

SRC_FOLDER = "folder_id_here"

all_items = {}
def index_all(parent_id, prefix=""):
    results = service.files().list(
        q=f"'{parent_id}' in parents and trashed=false",
        spaces='drive',
        fields='files(id, name, mimeType, size, webViewLink)',
        pageSize=100
    ).execute()
    for f in results.get('files', []):
        key = (prefix + f['name']).strip()
        all_items[key] = f
        if f['mimeType'] == 'application/vnd.google-apps.folder':
            index_all(f['id'], key + '/')

index_all(SRC_FOLDER)
```

**Note:** Folder names in Drive can have **trailing spaces** (e.g., `"Ranka Oasis Approvals  "`). When building keys by concatenating `prefix + f['name']`, these trailing spaces carry through and cause key mismatches. Always `.strip()` the key after concatenation, and when searching for a file, use `find_partial(name_part)` to match by substring rather than exact key.

```python
def find_partial(name_part):
    for k, v in all_items.items():
        if name_part in k:
            return k, v
    return None, None
```

### Phase 2 — Define document metadata

For each document, define structured metadata:

```python
documents = [
    {
        'src_key': 'JDA and GPA/20251031 JDA NO 7963 Betwn DRA Realty & Ramesh Reddy .pdf',
        'date': '2025-10-31',
        'village': 'Sevaganapalli',
        'doc_type': 'JDA',
        'parties': 'DRA Realty & Ramesh Reddy',
        'reg_no': '7963/2025',
        'description': 'JDA No. 7963/2025 — Ramesh Reddy & DRA Realty',
        'survey_nos': ['158', '167'],
    },
    # ... per document
]
```

Key fields:
- **`date`**: Document date in `YYYY-MM-DD` format, or `"—"` if unknown
- **`village`**: Village name (e.g., Sevaganapalli, Allalsandra)
- **`description`**: Human-readable document description
- **`reg_no`**: Registered document number (e.g., `"21785/2024"`), or `"—"` if none
- **`survey_nos`**: List of survey numbers this document pertains to — used for grouping

### Phase 3 — Create new folder and copy files with renamed filenames

```python
# Create target folder
nf = service.files().create(body={
    'name': 'Ranka Oasis - Banking documents folder',
    'mimeType': 'application/vnd.google-apps.folder'
}, fields='id').execute()
NEW_FOLDER_ID = nf['id']

# Copy each file with renamed filename
for doc in documents:
    src_key = doc['src_key']
    if src_key not in all_items:
        continue
    f = all_items[src_key]

    ext = os.path.splitext(f['name'])[1] or '.pdf'
    clean_desc = re.sub(r'[\\/*?:"<>|]', '', doc['description'])[:70].strip()
    clean_village = re.sub(r'[\\/*?:"<>|]', '', doc['village'])[:20].strip()

    new_name = f"{doc['date']}, {clean_village}, {clean_desc}, {doc['reg_no']}{ext}"
    new_name = re.sub(r'\s+,', ',', new_name).strip(', . ')
    new_name = re.sub(r',\s*,', ',', new_name).strip(', ')

    copied = service.files().copy(
        fileId=f['id'],
        body={'name': new_name, 'parents': [NEW_FOLDER_ID]}
    ).execute()
```

**Naming convention:** `YYYY-MM-DD, Village, Description, RegNo.ext`
- Avoid `/` in filenames (use `-` hyphen)
- Strip trailing commas, spaces, and dots
- Keep descriptions under 70 chars for readability

### Phase 4 — Generate survey-grouped index spreadsheet

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = openpyxl.Workbook()
ws = wb.active

# Group header style
grp_fill = PatternFill(start_color='D6E4F0', end_color='D6E4F0', fill_type='solid')
grp_font = Font(bold=True, size=11, color='2F5496')

# Sort survey numbers for consistent ordering
survey_order = sorted(set(s for doc in documents for s in doc.get('survey_nos', [])))

# Organize: documents may appear under MULTIPLE survey numbers
survey_groups = {s: [] for s in survey_order + ['General']}
for doc in documents:
    for s in doc.get('survey_nos', ['General']):
        survey_groups[s].append(doc)

# Write: Survey group header then document rows
for sg in survey_order:
    # Merged header row with survey number as label
    ws.merge_cells(f'A{r}:H{r}')
    cl = ws.cell(r, 1, f'  📌 Survey No. {sg}')
    cl.font = grp_font; cl.fill = grp_fill
    for c in range(2, 9):
        ws.cell(r, c).fill = grp_fill
    r += 1

    for doc in survey_groups[sg]:
        # Add row with Sl No, Survey No., Description, Date, Parties, Aadhar, PAN, Link
        r += 1
```

**Spreadsheet columns:**
| Sl No | Survey No. | Document Description | Document Date | Parties Involved | Aadhar No | PAN No | Document Link |

### Phase 5 — Upload spreadsheet and set permissions

```python
media = MediaFileUpload(local_xlsx,
    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
uploaded = service.files().create(
    body={'name': 'Index Name.xlsx', 'parents': [NEW_FOLDER_ID]},
    media_body=media, fields='id,webViewLink').execute()

service.permissions().create(
    fileId=uploaded['id'],
    body={'type': 'anyone', 'role': 'reader'},
    sendNotificationEmail=False
).execute()
```

## Handling oversized files

Files >20 MB may fail to preview in some browsers or mobile apps. Two strategies:

1. **Copy anyway, note size** — Drive copy works regardless of size. Add a `Size (MB)` column to the index and mark oversized files with ⚠.
2. **Link to source** — for files already hosted in a separate folder (e.g., Legal Opinions folder), delete the copy from the banking folder and set the index link to point to the **source file** in the original folder. This avoids duplicating large files.

## Pitfalls

- **Trailing spaces in folder names** — Drive allows trailing spaces in folder names (e.g., `"Sevaganapalli Maps and Plans  "`). These cause key mismatch when building prefix paths. Always `.strip()` keys and use partial matching.
- **0-byte Google shortcuts** — some files may be Google Workspace shortcuts with 0 bytes and no downloadable content. Skip these during copy.
- **No `webViewLink` on copy response** — when copying a file via `files().copy()`, the response may not include `webViewLink`. Construct it manually: `f"https://drive.google.com/file/d/{copied_id}/view"`
- **Duplicate files across subfolders** — the same document (same content, different name) may exist in multiple subfolders. Deduplicate by file ID before copying.
- **Spreadsheet links may not be clickable** — after writing a URL to a cell, explicitly set `hyperlink` and font color:
  ```python
  cl.value = url
  cl.hyperlink = url
  cl.font = Font(color='0563C1', underline='single', size=10)
  ```
- **Aadhar/PAN extraction** — Aadhar and PAN numbers inside scanned PDFs cannot be extracted without OCR. Leave as `"—"` and let the user fill them in from known records.
