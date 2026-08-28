# Drive Land Document Dedup & Bulk Rename Workflow

Complete workflow for cleaning up a Google Drive folder containing land/legal documents organized by Survey Number. Covers deduplication, bulk renaming, and syncing the results to a Master Sheet.

## Trigger

User shares a Drive folder link or asks to "go through this drive link, extract documents, clean up duplicates, rename all files."

## Phase 1: Audit

### 1A. Map the Folder Structure

```python
from tools.gws_auth import build_service
service = build_service("drive", "v3")

# Root folder from shared link
root_id = "FOLDER_ID_FROM_URL"  # e.g. 1UJRwQa2G8LZTnYesXa_H9Yzv0vNT3EWi

# List subfolders
folders = service.files().list(
    q=f"'{root_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
    fields="files(id, name)",
    pageSize=100
).execute().get('files', [])
```

### 1B. Check Permissions First

Always check what the token can do before attempting writes:

```python
folder = service.files().get(fileId=root_id, fields="id, name, owners, capabilities").execute()
print(f"Owner: {[o['emailAddress'] for o in folder.get('owners',[])]}")
caps = folder.get('capabilities', {})
for k, v in caps.items():
    if v: print(f"  {k}: {v}")
```

Key capabilities to look for:
- `canEdit: True` — can rename files
- `canDelete: True` — can delete files
- `canAddChildren: True` — can create files/folders

If only `canDownload` and `canListChildren` are True, the token has read-only access. Use the `telegram_id` override (see `references/build-service-telegram-id-override.md`).

### 1C. Full Content Audit

```python
print(f"{len(folders)} folders")
for folder in sorted(folders, key=lambda f: f['name']):
    items = service.files().list(
        q=f"'{folder['id']}' in parents and trashed=false",
        fields="files(id, name, size)",
        pageSize=200
    ).execute().get('files', [])
    
    # Categorize
    with_dates = [f for f in items if f['name'][0].isdigit()]
    nodate = [f for f in items if f['name'].startswith('NoDate')]
    no_type = [f for f in items if f['name'].endswith('village_only.pdf')]
    
    print(f"  {folder['name']}: {len(items)} files ({len(with_dates)} dated, {len(nodate)} NoDate, {len(no_type)} no doc type)")
```

### 1D. Find Duplicates

Group by name+size for exact duplicates, then by name alone for near-duplicates:

```python
from collections import Counter
name_size_counts = Counter()
for f in all_items:
    name_size_counts[(f['name'], f.get('size','0'))] += 1

# True duplicates
true_dups = [(n,s,c) for (n,s),c in name_size_counts.items() if c > 1]
for name, size, count in true_dups:
    print(f"  DUP: {name} ({round(int(size)/1024,1)} KB) x{count}")
```

## Phase 2: Dedup

Delete exact duplicates (same name + same size), keeping one copy:

```python
for (name, size), count in name_size_counts.items():
    if count > 1:
        matches = [f for f in all_items if f['name']==name and f.get('size')==size]
        for extra in matches[1:]:  # keep first, delete rest
            service.files().delete(fileId=extra['id']).execute()
```

**Known limitation:** Files with same name but different sizes are NOT duplicates — they are different documents that happen to share the same generic name (e.g., multiple `2026-05-28, Sy 103-7, Lakshmipura.pdf` files). These need their document types identified via OCR.

## Phase 3: Rename

### Naming Convention

**Standard format:** `NoDate/YYYY-MM-DD, Sy X, Village, DocType, RegNo.pdf`

- **Date:** `YYYY-MM-DD` from document content, or `NoDate` if unknown
- **Survey No:** `Sy 103`, `Sy 87/3`, `Sy 103-11`
- **Village:** `Lakshmipura` or `Bomvachanahalli` (derive from folder context)
- **Doc Type:** `Sale Deed`, `EC`, `RTC`, `MR`, `GPA`, `Grant Deed (Form 1)`, etc.
- **Reg No:** Optional — `RMN-1-04889-2020`, etc.

### Rename Rules (in priority order)

**Case A — "Sy X, Village, DocType.pdf" (no date):**
→ Prepend `"NoDate, "`
- `Sy 302, Lakshmipura, RTC.pdf` → `NoDate, Sy 302, Lakshmipura, RTC.pdf`

**Case B — "YYYY-MM-DD, Sy X, Village.pdf" (no doc type):**
→ Needs doc type identification via OCR (Phase 4). Leave as-is and flag.
- `2026-05-28, Sy 103-7, Lakshmipura.pdf` → needs doc type

**Case C — Old/non-standard names (number-only, "SyNo" format):**
→ Parse components and rebuild
- `108_1.pdf` → `NoDate, Sy 108, Lakshmipura, Document_1.pdf`
- `Second classification book SyNo 34.pdf` → `NoDate, Sy 34, Lakshmipura, Classification Book.pdf`
- `IL & RR Sy No 302.pdf` → `NoDate, Sy 302, Lakshmipura, IL & RR.pdf`

**Case D — Files with dates but no doc type AND Renamed already (date+Syr+Village):**
→ Flag for Phase 4 OCR

### Python Implementation

```python
import re
for item in items:
    old_name = item['name']
    new_name = old_name
    
    # Case A: "Sy X, Village, DocType.pdf" → prepend "NoDate, "
    if old_name.startswith('Sy') and re.match(r'^Sy\s*\d+', old_name):
        new_name = f"NoDate, {old_name}"
    
    # Case C: Number-only files
    elif re.match(r'^\d+(_\d+)?\.pdf$', old_name):
        num = re.match(r'^(\d+)', old_name).group(1)
        new_name = f"NoDate, Sy {num}, {village}, Document.pdf"
    
    # Apply
    service.files().update(fileId=item['id'], body={'name': new_name}).execute()
```

## Phase 4: OCR for Identifying Document Types (when needed)

For files with dates but no doc type (Case B/D), use pdftoppm + tesseract on the first page to identify:

```python
import subprocess, tempfile

# Download
resp = drive.files().get_media(fileId=fid).execute()
tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
tmp.write(resp); tmp.close()

# Render first page
subprocess.run(['pdftoppm', '-png', '-r', '150', '-f', '1', '-l', '1', tmp.name, '/tmp/page'])

# OCR
result = subprocess.run(['tesseract', '/tmp/page-1.png', '-', '-l', 'eng+kan'], capture_output=True, text=True)
text = result.stdout

# Match document type from keywords
doc_types = {
    'Sale Deed': ['sale deed', 'sale agreement'],
    'EC': ['encumbrance certificate', 'ec '],
    'RTC': ['rtc', 'record of rights', 'cultivation'],
    'MR': ['mutation', 'mutation register'],
    'GPA': ['power of attorney', 'general power of attorney'],
    'Grant Deed': ['grant', 'saguvali'],
}
```

## Phase 5: Sync to Master Sheet

After rename and dedup, update the Master Sheet (one tab per Sy No folder):

```python
sheets = build_service("sheets", "v4", telegram_id="psingh")

for folder in folders:
    items = drive.files().list(
        q=f"'{folder['id']}' in parents and trashed=false",
        fields="files(id, name, size, webViewLink)",
        pageSize=200
    ).execute().get('files', [])
    
    data = [["#", "File Name", "Size (KB)", "Drive Link", "Has Date", "Has Doc Type"]]
    for i, f in enumerate(sorted(items, key=lambda x: x['name']), 1):
        data.append([i, f['name'], round(int(f.get('size',0))/1024,1),
                     f.get('webViewLink',''), 
                     "✅" if f['name'][0].isdigit() else "⚠️ NoDate",
                     "✅" if len(f['name'].split(', ')) >= 3 else "⚠️"])
    
    sheets.spreadsheets().values().update(
        spreadsheetId=MASTER_SHEET_ID,
        range=f"'{folder['name']}'!A1:F{len(data)}",
        valueInputOption="USER_ENTERED",
        body={"values": data}
    ).execute()
```

## Session Context: Ramanagar Land (Jun 2026)

| Metric | Value |
|---|---|
| Total files | 494 (across 22 Sy No folders) |
| Files renamed | 260 |
| True duplicates removed | 6 |
| With proper dates | 233 |
| NoDate prefix added | 258 |
| Missing doc types | 171 (flagged for OCR pass) |
| Permission blocker | Bharat's token (read-only); fixed via `telegram_id="psingh"` (Prakash) |

## Pitfalls

- **Always check token permissions first** — the `get()` `capabilities` field tells you what you can do. A 403 on write with the correct token usually means the file was moved from another owner's folder and permission inheritance is broken.
- **True duplicates are rare** — most "same name" files are actually different documents with the same generic name (e.g. multiple `RTC.pdf` files for different years). Always verify by size AND consider content variance.
- **Master Sheet tab names have a 100-char limit** — truncate if needed (e.g. "Village Surveys & Maps" fits but very long Sy No strings should be shortened).
- **Rate limits** — Google Drive has per-user rate limits (∼10 req/s). Add `time.sleep(0.25)` between mutation calls.
