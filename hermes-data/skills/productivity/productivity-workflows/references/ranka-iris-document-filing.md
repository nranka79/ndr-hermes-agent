# Ranka Iris — Document Naming & Folder Reference

## Project
**Ranka Iris** — DRA Developers & Projects Pvt. Ltd.
Site 37-37A-38, Sy 17/1 & 17/2, Domlur 2nd Stage, Ward 72, Bengaluru

## Document Naming Convention
```
YYYYMMDD [Project] [Owner] [Authority] [Document Type] [Details].pdf
```
- Date format: no spaces, no dashes within the name itself (dashes only in date as YYYYMMDD)
- Example: `20190405 Ranka Iris DRA Developers BBMP Commencement Certificate Kannada.pdf`
- Example: `20260430 Ranka Iris BBMP OC Demand English Translation Detailed Fee Calculation.pdf`
- Example: `20260430 Ranka Iris BBMP OC Demand Original Kannada.pdf`
- Example: `20130902 Ranka Iris DRADevelopers BBMPBuildingPermit Sanction26822 3BF GF 13Floors.pdf`

## Document Types & Naming Patterns

| Document | Naming Pattern |
|----------|---------------|
| Commencement Certificate | `BBMP Commencement Certificate [Kannada/English]` |
| Building Permit | `BBMPBuildingPermit Sanction[SanctionNo] [floors]` |
| OC Demand | `BBMP OC Demand [Original Kannada/English Translation]` |
| BBMP Fee Receipt | `BBMPLicenseFee_CommencementCert` |
| BBMP Demand Draft | `BBMPDemandDraft [Amount] DD[DDNo]` |

## Drive Folder IDs

| Folder | ID |
|--------|---|
| **Ranka Iris Sanction Plans** (all BBMP docs) | `1WIKsg4-2JHdCyjodBj9v2LGMd1HQ6j5` |
| OC Demand + FLIT applications + travel docs | `1mZbVBUC42HX5HzrBpLw5y1_nmkypbaDC` |

All BBMP sanction/permit/OC documents go in `1WIKsg4-2JHdCyjUodBj9v2LGMd1HQ6j5`.

## Documents Filed (as of May 2026)

| Date | Document | File ID |
|------|----------|---------|
| 20190404 | BBMP License Fee Receipt (JPG→PDF) | `1Ed6pHIftEAjYI8PBK0AovxACx2PNYRRH` |
| 20190405 | Commencement Certificate Kannada | `1KCeIoPLWn98G90QFXfjM5M1uqwd6IErB` |
| 20130902 | Building Permit Sanction 26822 | `1steV8pSkIC-KQAqx1qKBD9buV_NM6tTA` |
| 20190801 | BBMP Demand Draft DD150078 ₹10.10L | `1EDzPHOiGQH78OJ45rgUiaiOApaZ05Afk` |
| 20260430 | OC Demand English Translation | `1CV3WNjgNmiiQrURlcYCFhdLwT9N8v-xU` |
| 20260430 | OC Demand Original Kannada | `1FMcDppu7KL_YBnkVphG7mSmOlbY7JcnD` |

## BBMP OC Demand — Key Reference

- **Document Number:** BBMP/Addl.Dir/JD North/LP/0037/2013-14
- **Date:** 30/04/2026
- **Total Fee Demanded:** ₹1,28,57,000
- **Payee:** Commissioner, Bangalore Central City Corporation A/C
- **Mode:** Demand Draft
- **Authority:** Joint Director City Planning (North), BBMP Bengaluru Central City Corporation, Annex-3 Building 4th Floor, N.R. Circle, Bengaluru – 560002
- **Approval:** Hon'ble Additional Commissioner (Revenue) dated 29/04/2026
- **Applicant:** M/s DRA Developers & Properties, No.4, Ranka Chambers, 31 Cunningham Road, Bangalore – 560052

## Google Drive Authentication Pattern

For Drive operations in this environment, use `google_token.json`:
```python
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_info(json.load(open('/data/hermes/google_token.json')))
creds.refresh(Request())
drive = build("drive", "v3", credentials=creds)
```

**Token file path:** `/data/hermes/google_token.json`
**Note:** `gws_sa.build_service()` requires `GOOGLE_SA_KEY` env var — not available in this environment. `oauth-draas.json` etc. do not exist at expected paths.

## Move File Between Folders (Single API Call)

```python
# Move to a new folder in ONE call (don't remove first, then add — causes 404)
updated = drive.files().update(
    fileId=file_id,
    addParents=destination_folder_id,
    removeParents=current_parent_id,
    body={},
    fields="id, name, parents"
).execute()
```

## JPG to PDF Conversion

```python
from PIL import Image
img = Image.open('/path/to/file.jpg')
img_rgb = img.convert('RGB')
img_rgb.save('/path/to/output.pdf', 'PDF', resolution=150)
```

Use when: a file was uploaded with wrong MIME type (e.g., JPG stored as PDF) — download, convert, re-upload, delete original.