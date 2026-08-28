# EC Compilation & Merging for Printing

## When to Use
- User says "download all EC" for a property
- User says "make it folder so I can take print out" after you've downloaded multiple ECs
- User needs a single printable document containing all ECs for submission

## Workflow

### Step 1: Find All EC Files on Drive

Search the user's Drive for all Encumbrance Certificate files related to the property:

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

drive = build_service("drive", "v3")

# Search for EC files by property name
results = drive.files().list(
    q="(name contains 'EC' or name contains 'Encumbrance') and (name contains 'ProjectName' or name contains 'SyNo')",
    spaces='drive',
    fields='files(id, name, size, createdTime)',
    pageSize=100,
    orderBy='createdTime desc'
).execute()
```

Also check dedicated legal set folders — ECs are often stored alongside sale deeds, NOCs, and tax receipts in a single project folder.

### Step 2: Download All EC Files

Download each EC file to a local directory:

```python
import os
ec_dir = '/data/hermes/document_cache/ProjectName_ECs'
os.makedirs(ec_dir, exist_ok=True)

for fname, fid in ec_files:
    content = drive.files().get_media(fileId=fid).execute()
    path = os.path.join(ec_dir, fname)
    with open(path, 'wb') as f:
        f.write(content)
```

**Pitfall — API timeouts on bulk downloads:** Each `get_media()` call is a separate HTTP request. Downloading 28+ files in one invocation may timeout. The pattern works because individual ECs are small (100KB–1MB each), totalling ~15MB for 28 files.

### Step 3: Organize Chronologically

Sort the files by their date range (extracted from the filename):

- Files with explicit date ranges (e.g., `1920-2004`, `01APR04-17FEB16`) go in date-order
- Undated files (e.g., `Ranka Iris EC1.pdf`) go last within their group
- Standard naming convention: `EC_PropertyName_FromDate-ToDate.pdf`

Common filename patterns for Karnataka ECs:
| Pattern | Example | Date Range |
|---------|---------|------------|
| `EC SyNo37_1 1920-2004.pdf` | 1920 – 2004 | Oldest |
| `EC SyNo37_1 01Apr04-22Aug21.pdf` | 01 Apr 2004 – 22 Aug 2021 | Middle |
| `EC latest for 37A 1Nov2023-20May2024.pdf` | Nov 2023 – May 2024 | Most recent |

### Step 4: Merge into Single PDF with pdfunite

Use `pdfunite` (from poppler-utils, available at `/usr/bin/pdfunite`) to merge all ECs into one chronological PDF:

```bash
cd /path/to/ec_folder

pdfunite \
  "01_oldest_ec.pdf" \
  "02_middle_ec.pdf" \
  "03_latest_ec.pdf" \
  "/output/path/PROJECT_ALL_ECs_MERGED.pdf"
```

**Example** (28 files merged):
```bash
pdfunite \
  "EC SyNo37_1 1920-2004 v2.pdf" \
  "EC SyNo37_1 1920-2004.pdf" \
  ... (all chronologically ordered) ...
  "EC latest for 38 1Nov2023-20May2024.pdf" \
  "/data/hermes/document_cache/PROJECT_ALL_ECs_MERGED.pdf"
```

**Verify the result:**
```bash
pdfinfo /path/to/PROJECT_ALL_ECs_MERGED.pdf | grep -E "Pages|File size"
```

### Step 5: Deliver to User

Send the merged PDF to the user via Telegram using the `MEDIA:` directive:

```
MEDIA:/data/hermes/document_cache/PROJECT_ALL_ECs_MERGED.pdf
```

Include a summary in the message:
- Total pages
- Total file size
- Date range coverage (e.g., 1920 to 2024)
- Number of ECs merged
- Where the individual originals are saved

**Example delivery:**

> All 28 EC files downloaded and merged ✅
> 
> **File:** `PROJECT_ALL_ECs_MERGED.pdf`
> - **56 pages** | **14 MB**
> - Chronological order: 1920 → 2024
> 
> MEDIA:/path/to/file.pdf
> 
> The individual originals are also saved at `/data/hermes/document_cache/Project_ECs/`

## Pitfalls

1. **xref errors in merged PDFs:** `pdfunite` sometimes produces minor xref table errors. The PDF is still viewable and printable — these are cosmetic issues from merging scanned PDFs with different internal structures.

2. **File size:** Merging 28 scanned PDFs can produce a 14MB+ file. This is acceptable for Telegram delivery (files up to ~50MB are supported).

3. **Chronological ordering is manual:** `pdfunite` concatenates files in the order you list them on the command line. You must explicitly list them in date order — it does NOT auto-sort.

4. **Original ECs still on Drive:** The merged PDF is a local file. The originals remain on the user's Drive. The user may need both — the merged version for printing, and the originals for individual reference.

5. **Duplicates:** Some EC folders contain multiple copies of the same EC (scanned at different times, with different names). Deduplicate by checking file size and date range before merging. If two ECs cover the same period for the same property, keep only the latest/most complete copy.

## Tools Reference

| Tool | Path | Purpose |
|------|------|---------|
| `pdfunite` | `/usr/bin/pdfunite` | Merge multiple PDFs into one (poppler-utils) |
| `pdfinfo` | `/usr/bin/pdfinfo` | Check page count and metadata of merged PDF |
| `pdftoppm` | `/usr/bin/pdftoppm` | Convert PDF pages to PNG images (for OCR) |
