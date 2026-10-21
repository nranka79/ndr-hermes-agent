# Kannada Government Letter Processing → English PDF Replica

For **formal Kannada government letters** from BMTF, BIAAPA, DC office, Tahsildar, BBMP Police, etc. — NOT land records (RTC/MR/EC). These are structured correspondence documents with letterhead, reference number, addressee, subject, body, and signature.

## Document Classes

| Class | Source | Typical Subject |
|---|---|---|
| **BMTF Police Notice** | Bengaluru Metropolitan Task Force (BBMP HQ, N.R. Circle) | Encroachment complaint, bylaw violation, buffer zone, hearing summons |
| **BIAAPA Letter** | Bengaluru International Airport Area Planning Authority | Land conversion, layout approval, NOC, zoning |
| **DC Letter** | Deputy Commissioner, Bengaluru Rural District | Conversion cancellation, land acquisition |
| **Tahsildar Letter** | Tahsildar Office | Revenue entries, mutation orders |
| **BMRDA Letter** | Bangalore Metropolitan Region Development Authority | Planning permission, master plan |

## Workflow

### Step 1: Convert PDF to Image (for scanned documents)

```bash
# Check if PDF has embedded images (scanned = image-only PDF)
pdfimages -list input.pdf

# Check if PDF has text layer
pdftotext input.pdf - | head -20

# Convert to PNG for OCR — use high DPI (300) for small Kannada text
pdftoppm -png -r 300 input.pdf /tmp/output_page
```

### Step 2: OCR + Translation — PRIMARY: vision_analyze (recommended)

**vision_analyze** via `vision_analyze(image_url=..., question=...)` gives the BEST results for Kannada government letters. It returns complete Kannada text AND English translation in a single call, with excellent accuracy on clean scanned PDFs (300 DPI). No separate Tesseract setup needed.

```python
# Works for scanned PDFs converted to PNG
vision_analyze(
    image_url="/tmp/output_page-1.png",
    question="Extract ALL text from this Kannada government letter. Read every word: header, reference number, date, addressee, subject, body paragraphs, numbered items, signature, stamps, contact numbers. Then provide full English translation."
)
```

**When vision_analyze returns image-not-found (PDF direct):** Convert to PNG first with pdftoppm, then pass the PNG path.

### Step 2b: OCR + Translation — FALLBACK: Tesseract

Use this only when vision_analyze is unavailable:"

| Kannada | English |
|---|---|
| ಬೆಂಗಳೂರು ಅಂತರಾಷ್ಟ್ರೀಯ ವಿಮಾನ ನಿಲ್ದಾಣ ಪ್ರದೇಶ ಯೋಜನಾ ಪ್ರಾಧಿಕಾರ | Bengaluru International Airport Area Planning Authority (BIAAPA) |
| ವಿಮಾನ ನಿಲ್ದಾಣ ಪ್ರದೇಶ ಯೋಜನಾ ಪ್ರಾಧಿಕಾರ | Airport Area Planning Authority |
| ಜಿಲ್ಲಾಧಿಕಾರಿಗಳು | Deputy Commissioner |
| ಗ್ರಾಮಾಂತರ ಜಿಲ್ಲೆ | Rural District |
| ತಾಲ್ಲೂಕು | Taluk |
| ಹೋಬಳಿ | Hobli |
| ಗ್ರಾಮ | Village |
| ಸ.ನಂ. (ಸರ್ವೇ ನಂಬರ್) | Survey No. |
| ಜಮೀನು | Land |
| ಭೂಪರಿವರ್ತನೆ | Land Conversion (Land Use Change) |
| ಭೂಪರಿವರ್ತನಾ ಆದೇಶ | Land Conversion Order |
| ರದ್ದುಪಡಿಸುವ | Cancellation / Revoke |
| ವಿನ್ಯಾಸ ನಕ್ಷೆ | Layout Plan / Development Plan |
| ಅನುಮೋದನೆ | Approval / Sanction |
| ಅಭಿವೃದ್ಧಿ ಕಾಮಗಾರಿಗಳು | Development Works |
| ಕೃಷಿ ಚಟುವಟಿಕೆ | Agricultural Activity |
| ವಸತಿ ವಲಯ | Residential Zone |
| ವ್ಯವಸಾಯ ವಲಯ | Agricultural Zone |
| ಭೂಉಪಯೋಗ ಬದಲಾವಣೆ | Land Use Change |
| ಜಂಟಿ ನಿರ್ದೇಶಕರು | Joint Director |
| ಸದಸ್ಯ ಕಾರ್ಯದರ್ಶಿಗಳು | Member Secretary |
| ವರದಿ | Report |
| ಪರಿಶೀಲಿಸಿ | Inspect / Examine |
| ಅಭಿಪ್ರಾಯ | Opinion |

### Step 3: Create HTML Replica (Kannada + English Combined)

Create an HTML document with TWO sections — the Kannada original reproduced exactly (matching layout/emblem/fonts) on top, and the English translation below, separated by a divider. This gives the user ONE document containing both, which is cleaner than separate files.

**Format: Kannada Original → Divider → English Translation**

The HTML should reproduce the original letter's visual layout faithfully including:
- Government emblem (SVG approximation)
- Department/authority name
- Office address and contact
- Reference number and date
- "Police Notice" / subject title
- Body text with exact Kannada content (from vision_analyze OCR, NOT Tesseract garbled text)
- Numbered document lists
- Addressee block
- Signature block with name, designation, contact number

**Layout Structure (top to bottom):**

1. **Emblem** — Government of Karnataka emblem (SVG), centered
2. **Header** — "Karnataka Rajya" → department → authority name (bold, centered)
3. **Address line** — Office address, centered
4. **Contact** — Phone number
5. **Reference + Date row** — Left: Ref No. | Right: Date
6. **Sender block** — Office of the [designation], authority name
7. **Notice title** — Bold, centered, with asterisks/separators
8. **Body text** — Justified, 11px, 1.75 line-height
9. **Numbered list** — Ordered list of required items
10. **Addressee block** — "To," then name/address
11. **Signature block** — Right-aligned: name in parentheses, designation, station, contact number
12. **Divider** — 3px double line or gradient
13. **English Translation** — Same structure but in English

**CSS Notes (from verified Ranka Amber BMTF Notice, Sep 2026):**
- Font: 'Noto Sans Kannada' + 'Noto Sans' (Google Fonts) for bilingual
- Background: #e8e8e8 with white letter card
- Box shadow: 0 4px 20px rgba(0,0,0,0.15)
- Kannada body text: 11px font, English translation: 11px
- Max-width: 800px, padding: 50-60px
- Translation section: light background (#fafaf8) with header + border
- Print-friendly @media print styles

### Step 4: Convert HTML to PDF via weasyprint

Install weasyprint and convert:

```bash
uv pip install weasyprint
```

```python
from weasyprint import HTML
HTML("/tmp/notice.html").write_pdf("/tmp/notice.pdf")
```

**Critical:** weasyprint produces a PDF that exactly mirrors the HTML layout — government emblem, Kannada text, numbered lists, and English translation all in one document. No Tesseract needed, no separate upload steps.

### Step 5: File on Google Drive

**Rename to YYYYMMDD convention** (per DRAAS global naming rule):

```
20260903_RankaAmber_BMTF_Police_Notice.pdf
20260903_RankaAmber_BMTF_Police_Notice_Original_Scan.pdf
```

**Filing location:**
- BMTF/BBMP Police notices → project folder > Legal Notices (create if absent)
- Always create a dedicated "Legal Notices" subfolder under the project folder, NOT TMP
- Upload BOTH the reproduced PDF AND the original scan side by side

Upload code (from terminal(), not execute_code — vault socket not available in sandbox):

```python
from googleapiclient.http import MediaFileUpload
media = MediaFileUpload(local_path, mimetype='application/pdf')
uploaded = svc.files().create(
    body={'name': 'YYYYMMDD_Project_BMTF_Police_Notice.pdf', 'parents': [folder_id]},
    media_body=media, fields='id,name,webViewLink'
).execute()
```

## Document-Type-Specific Keywords

### BIAAPA-Specific

| Kannada Keyword | English |
|---|---|
| ಬೆಂಗಳೂರು ಅಂತರಾಷ್ಟ್ರೀಯ ವಿಮಾನ ನಿಲ್ದಾಣ ಪ್ರದೇಶ ಯೋಜನಾ ಪ್ರಾಧಿಕಾರ | BIAAPA (header) |
| ಬಿಐಎಎಪಿಎ | BIAAPA (in reference no.) |
| ವಿನ್ಯಾಸ ನಕ್ಷೆ ಅನುಮೋದನೆ | Layout plan approval |
| ಭೂಪರಿವರ್ತನಾ ಆದೇಶ | Land conversion order |
| ದೇವನಹಳ್ಳಿ | Devanahalli (BIAAPA HQ) |

### BMTF Police Notice-Specific

| Kannada Keyword | English |
|---|---|
| ಬೆಂಗಳೂರ ಮಹಾನಗರಕಾರ್ಯಾಚರಣೆ ಪಡೆ | Bengaluru Metropolitan Task Force (BMTF) |
| ಬಿಎಂಟಿಎಫ್ | BMTF (in reference no.) |
| ಪೊಲೀಸ್ ನೊಟೀಸ್ | Police Notice |
| ಸಬ್ ಇನ್ಸ್‌ಪೆಕ್ಟರ್ | Sub Inspector |
| ಪೆಟಿಷನ್ | Petition (in ref no.) |
| ಖರಾಬು ಜಾಗ | Kharab land (government waste/gutter land) |
| ಒತ್ತುವರಿ | Encroachment |
| ಬಫರ್ ಜಾಗ | Buffer zone |
| ಬೈಲಾವನ್ನು ಉಲ್ಲಾಂಘನೆ | Bylaw violation |
| ವಿಚಾರಣೆ | Inquiry / Hearing |
| ಹಾಜರಾಗುವಂತೆ ಸೂಚಿಸಿದೆ | Instructed to appear |
| ಸ್ವತ್ತಿನ ನೊಂದಣಿಕ್ರಯ ಪತ್ರ | Property registration/sale deed |
| ಭೂ ಪರಿವರ್ತನಾ ಪ್ರಮಾಣ ಪತ್ರ | Land Conversion Certificate (CLU) |
| ಅನುಮೋದಿತ ನಕ್ಷೆ | Approved plan / Sanctioned plan |
| ಪರಿತ್ಯಾಜನಾ ಪತ್ರ | Relinquishment deed |
| ಆರ್.ಟಿ.ಸಿ | RTC (Record of Rights, Tenancy and Crops) |
| ಆಕಾರ್‌ಬಂದ್ | Akarband (land measurement sketch) |
| ಮ್ಯುಟೇಷನ್ | Mutation |
| ನಿರಕ್ಷೇಪಣಾ ಪತ್ರ | No Objection Certificate (NOC) |
| ರೇರಾ | RERA |

### 8 Documents Required for a BMTF Hearing (standard list found in 2026 notices)

1. Property registration / sale deed
2. Land conversion certificate (CLU)
3. Approved plan from planning authority
4. Relinquishment deed, survey documents
5. RTC and Akarband
6. Mutation documents and RR and ILR
7. NOCs from competent authorities
8. RERA NOC for sale

### Step 4: Find the Correct Drive Folder for Filing

**⚠️ CRITICAL — Do NOT default to temp.tmp.** Legal documents (BIAAPA letters, DC/Tahsildar correspondence) about a specific survey number MUST go in the legal documentation folder for that property, NOT a generic temp folder.

The correct folder may be named after:
- The **entity/trust** that owns the land (e.g., "Godwad Bhavan Jain Trust", "GBJT", "Godwad Bhavan Jain Trust Nandi Hills property")
- The **village name** (e.g., "Hulurugurki", "Huluro Gurki")
- A **dedicated survey-number folder** (e.g., "Bamnolim (Sy No 93-2) Legal Documents")
- The **project name** (e.g., "Serenity Hill View") — but only if it has a Legal subfolder

**Search strategy for the right folder:**
```python
from tools.gws_auth import build_service

svc = build_service("drive", "v3")

# Extract survey number and village from the letter
survey_no = "93/2"  # from document content
village = "Hurulugurki"  # from document content

# Search multiple name variants
queries = [
    f"name contains '{village}' and mimeType = 'application/vnd.google-apps.folder'",
    f"name contains 'Sy No {survey_no}' and mimeType = 'application/vnd.google-apps.folder'",
    f"name contains 'Legal' and name contains '{survey_no.split('/')[0]}' and mimeType = 'application/vnd.google-apps.folder'",
    f"name contains '{village[:5]}' and mimeType = 'application/vnd.google-apps.folder'",
]

for q in queries:
    results = svc.files().list(
        q=q, fields="files(id, name, parents, webViewLink)",
        includeItemsFromAllDrives=True, supportsAllDrives=True
    ).execute()
    # Check each result's contents — if it has legal PDFs (sale deeds, ECs, RTCs),
    # that's likely the right place
```

**Check the folder's contents before filing:** List files in candidate folders. If a folder already contains legal documents (sale deeds, ECs, RTCs, BIAAPA applications) for the same survey number, file there. If the folder is empty or has architectural drawings, it's a project folder — keep searching.

**If no legal folder exists:** Create a new folder under the project's DRA Projects entry with a descriptive name, or ask the user where they want it. Do NOT default to temp.tmp.

**Upload the files:**
```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

svc = build_service('drive', 'v3')

def upload_to_drive(local_path, target_folder_id, display_name):
    media = MediaFileUpload(local_path, mimetype='text/html' if local_path.endswith('.html') else 'application/pdf', resumable=False)
    uploaded = svc.files().create(
        body={'name': display_name, 'parents': [target_folder_id]},
        media_body=media,
        fields='id,webViewLink'
    ).execute()
    # Make publicly viewable
    svc.permissions().create(
        fileId=uploaded['id'],
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()
    return uploaded.get('webViewLink', '')
```

**Naming convention (YYYYMMDD per global DRAAS rule):**

- PDF replica: `YYYYMMDD_ProjectOrEntity_BMTF_Police_Notice.pdf`
- Original scan: `YYYYMMDD_ProjectOrEntity_BMTF_Police_Notice_Original_Scan.pdf`

Examples:
- `20260903_RankaAmber_BMTF_Police_Notice.pdf` (reproduction)
- `20260903_RankaAmber_BMTF_Police_Notice_Original_Scan.pdf` (source)
- `20260622_GodwadBhavanTrust_BIAAPA_LandConversion_Cancellation_Report.pdf` (BIAAPA)

**Always file two artifacts together:**
1. Reproduced PDF (Kannada + English in one document)
2. Original scanned PDF (renamed per convention)

## Pitfalls

- **Vision model works WELL on Kannada — do NOT default to Tesseract.** vision_analyze (Gemini-based) produces clean, complete Kannada text + English translation from a single 300 DPI PNG. The old pitfall claiming otherwise was based on earlier models. Use Tesseract `-l kan` ONLY when vision_analyze is unavailable (no vision provider configured). Tesseract accuracy is ~60-70% on Kannada and produces garbled text.
- **OpenRouter credits**: `google/gemini-3.5-flash` works well when credits are available. Without credits, vision_analyze's built-in fallback handles translation without OpenRouter.
- **Write location permissions**: Cannot write to `/mnt/uploads/` (read-only filesystem). Stage files in `/tmp/` before uploading to Drive.
- **⚠️ Do NOT default to TMP folder for legal documents**: Legal notices (BMTF, BIAAPA, DC, Tahsildar) about a specific property MUST go in the project's legal documentation folder. Create a "Legal Notices" subfolder under the project's Drive folder.
- **Always upload the original scan alongside the reproduction**: The user expects the source Kannada PDF to be filed in the same folder.
- **Search multiple name variants for the target folder**: The legal docs for a property may be under the trust/entity name, project name, or a dedicated folder.
- **BMTF Notice specific: 8 documents required for hearing.** When the notice demands documents (sale deed, CLU, approved plan, relinquishment deed, RTC/Akarband, mutation/RR/ILR, NOCs, RERA NOC), list them explicitly in the translation. These are urgent — hearing dates are typically within days.
- **weasyprint must be installed via uv** — `uv pip install weasyprint`. Not available in base Python.

## Verified Examples

### Example 1 — BMTF Police Notice for Ranka Amber (03 SEP 2026)

- **Letter:** No.BMTF/ADGP/Petition/1237/2026, dated 03/04/2026
- **Issuer:** Office of PSI Manoj Kurane, Bengaluru Metropolitan Task Force, BBMP HQ, N.R. Circle
- **Subject:** Encroachment complaint — government kharab land encroached, buffer zone not left, bylaw violation at Plot 1-B, Katha 4/124, PID 7057785976, D'Silva Layout, Pattandur Agrahara
- **Hearing:** 07/09/2026 at 11:30 AM — 8 documents required
- **Workflow used:** pdftoppm (300 DPI) → vision_analyze (full Kannada OCR + translation) → HTML/CSS reproduction (Kannada on top, English below) → weasyprint PDF → Drive upload to Ranka Amber > Legal Notices subfolder
- **Output:** Single PDF with Kannada original layout + English translation
- **Contact:** PSI Manoj Kurane, 9886876942
- **Uploaded:** https://drive.google.com/drive/folders/1jOQzLjRAhy761CUU8aobTtDdmYqLyROm

### Example 2 — BIAAPA Letter No. BIAAPA/TP/MIS/07/2025-26/26 (22 JUN 2026)

- **Subject:** Sy. 93/2, Hurulugurki Village, Vijayapura Hobli — Land conversion cancellation report
- **Key finding:** BIAAPA confirmed NO layout/development plan approval was granted for 6A-26G in Sy. 93/2
- **Method (old):** Tesseract Kannada OCR → manual translation → HTML
- **Delivery:** Godwad Bhavan Jain Trust Nandi Hills property folder
