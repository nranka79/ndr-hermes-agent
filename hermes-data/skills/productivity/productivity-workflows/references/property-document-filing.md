# Property Document Filing Workflow

## Overview

When a property document (tax receipt, Khata certificate, sale deed, etc.) is uploaded, identify the property, find the correct Drive folder, rename per convention, upload, and share the link.

## Universal Property Document Naming Convention

```
YYYYMMDD [Project/Property Name] [Document Type] FY YYYY-YY – [Party Names].pdf
```

Examples:
- `20260520 Golfshire Villa 123 Property Tax Receipt FY 2026-27 – DRA Projects.pdf`
- `20250407 Golfshire Panchayat Tax Receipt DRA-Ranka Sy104-123.pdf`

## Workflow

1. **Verify flat/unit number FIRST** — user may misstate the flat number (e.g., says "911" but Drive has "914" for Embassy Habitat). Always confirm the exact flat/unit number before searching Drive. If the stated number doesn't yield results, search for the nearest number(s) and present alternatives to the user.
2. **Extract text** from PDF using `pdftotext -layout` (preserves table structure)
3. **Identify property** from text: PID/Property ID, Owner name, Property No/Villa No
4. **Identify document type**: Tax Receipt, Khata, Sale Deed, NOC, etc.
5. **Find Drive folder** using project-specific folder IDs (see Embassy Habitat below, or `references/golfshire-folder-ids.md` for Golfshire)
6. **Rename file** per convention above
7. **Upload** via `googleapiclient.http.MediaFileUpload` to correct folder
8. **Verify** file appears in Drive at correct path
9. **Return share link** to user

## Property Types with Known Folder IDs

### Golfshire (Villas 123, 124, 125)
- **Legal Docs folder**: `1wdxC2qn8A9DQ9tCRSL3JIv7A-36lkmYs`
  - Panchayat tax receipts, title documents
- **DRA Asset Sale folder**: `1FGgS5b8yCOybTm2VaG0MFPeMUmVxYTwP`
  - Sale deeds, payment undertakings

### Embassy Habitat (Embassy Property Developments — Outer Ring Road, Bangalore)
Known units: **914** (sold to Ravikumar Naik; also in NDR ownership context), **911** (verify with user — no Drive files found matching "911" as of June 2026)
- **Main folder**: `1-N8vU98O3sVnrkarb08qsqiC2Q7BAvww`
- **Legal Documents folder**: `1Rz1_I6pcdnzJvzBUZZDfzPoRB_CwLrnR`
- **914 Title Documents folder**: `1rvnnl3168-YrvGQcUsD71aSYoVpmcChH` — contains historic sale deeds (2001 series) from previous owners (LK Trust era)
- **914 EH Sale Agreements folder**: `1usmf8DrYX-1cH9Pv-7wBlLF3ihudu-FU` — NDR's signed/draft sale agreements
- **Sale deed for 914 (Ravi Kumar → NDR/RNR)**: Google Doc `1yHiL4vSGjhyEPOfX3g_Q_LiUsRZWlG61_BROKCUkIL8` (Draft Sale Deed 914 EH Ravi 2 RNR, March 2026)

**Search tip:** `name contains '914' and 'sale deed'` will find the NDR sale deed. No files with "911" in name exist in NDR's Drive as of June 2026.

### Ranka Oasis / Sevaganapalli
- See `google-workspace:references/ranka-oasis-file-organization.md`

### Ranka Amber (Whitefield)
- See `google-workspace:references/ranka-amber-drive-folders.md`

### Allalsandra Sites
- See `google-workspace:references/allalsandra-ranka-northstar-docs.md`

## Upload Script Template

```python
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load token
with open('/data/hermes/google_token.json') as f:
    token_info = json.load(f)
creds = Credentials(**token_info)
if creds.expired:
    creds.refresh(Request())

drive = build('drive', 'v3', credentials=creds)

# Upload
file_path = '/path/to/document.pdf'
file_name = 'YYYYMMDD Property Document Type.pdf'
folder_id = 'DRIVE_FOLDER_ID'

media = MediaFileUpload(file_path, mimetype='application/pdf')
file = drive.files().create(
    body={'name': file_name, 'parents': [folder_id]},
    media_body=media,
    fields='id, webViewLink'
).execute()

print(f"Uploaded: {file['webViewLink']}")
```