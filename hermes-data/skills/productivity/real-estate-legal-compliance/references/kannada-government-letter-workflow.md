# Kannada Government Letter Processing → English HTML Replica

For **formal Kannada government letters** from BIAAPA, DC office, Tahsildar, etc. — NOT land records (RTC/MR/EC). These are structured correspondence documents with letterhead, reference number, addressee, subject, body, and signature.

## Document Classes

| Class | Source | Typical Subject |
|---|---|---|
| **BIAAPA Letter** | Bengaluru International Airport Area Planning Authority | Land conversion, layout approval, NOC, zoning |
| **DC Letter** | Deputy Commissioner, Bengaluru Rural District | Conversion cancellation, land acquisition |
| **Tahsildar Letter** | Tahsildar Office | Revenue entries, mutation orders |
| **BMRDA Letter** | Bangalore Metropolitan Region Development Authority | Planning permission, master plan |

## Workflow

### Step 1: OCR with Kannada Tesseract

```bash
# Kannada traineddata must be downloaded separately (not in apt)
mkdir -p /data/hermes/tessdata
curl -sL -o /data/hermes/tessdata/kan.traineddata \
  https://github.com/tesseract-ocr/tessdata/raw/main/kan.traineddata

# Run OCR
tesseract /path/to/image.jpg /path/to/output -l kan \
  --tessdata-dir /data/hermes/tessdata
```

**Note:** The image may already be cached at `/data/hermes/image_cache/img_*.jpg` if the user uploaded it via Telegram.

### Step 2: Translate to English

**Two methods — offer both for cross-verification:**

#### Method A — Manual translation (always available)

Read the Tesseract OCR output and translate directly. Use the glossary below.

#### Method B — Gemini 3.5 Flash via OpenRouter (when credits available)

```python
# Works when OpenRouter credits are sufficient
call_openrouter_model(
    model="google/gemini-3.5-flash",
    prompt="You are a Kannada→English translator. Translate this Kannada document...",
    user_trigger_phrase='"translate via OpenRouter"'
)
```

`google/gemini-3.5-flash` gives accurate Kannada→English results with good formatting.
Create a separate HTML file marked as "Gemini 3.5 Flash Translated" so the user can compare both versions side-by-side.

**Convert original image to PDF** using ImageMagick (`convert input.jpg output.pdf`) and file it alongside the translation — the user explicitly requires the source document filed as PDF in the same folder as the translated HTML.

**Note:** OpenRouter may return HTTP 402 (insufficient credits). Offer manual translation as fallback.

Read the OCR output and translate manually. Key government letter terminology:

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

### Step 3: Create HTML Replica

Format the English translation as an HTML document that mirrors the original government letter layout.

**Layout Structure (top to bottom):**

1. **Header** — Authority name (bold, centered, royal blue #1a237e, uppercase), subtitle "(Constituted under...)"
2. **Address line** — Office address in smaller font, centered
3. **Contact bar** — Phone, Email, Website in a single row
4. **Reference + Date row** — Left: Ref No. (bold) | Right: Date (bold, right-aligned)
5. **Addressee block** — "To," then name/title, address lines, then salutation "Sir / Madam,"
6. **Subject block** — "Subject:" label, then underlined subject text
7. **Reference line** — "Reference:" with letter number and date
8. **Separator line** — Dashed line
9. **Body text** — Justified, 12px, 1.9 line-height, bold for key figures (acres, survey numbers, amounts)
10. **Signature** — Right-aligned, designation with "Joint Director & Member Secretary" etc.
11. **Footer disclaimer** — "This is a computer-generated English translation..."

**CSS Notes:**
- Font: 'Noto Sans' (Google Fonts) for clean government-document look
- Background: light gray (#e8e8e8) with white letter card
- Box shadow: subtle (0 4px 20px rgba(0,0,0,0.15))
- Max-width: 800px
- Print-friendly with @media print styles

## BIAAPA-Specific Document Keywords

When OCR output contains these Kannada keywords, identify as BIAAPA document:

| Kannada Keyword | English |
|---|---|
| ಬೆಂಗಳೂರು ಅಂತರಾಷ್ಟ್ರೀಯ ವಿಮಾನ ನಿಲ್ದಾಣ ಪ್ರದೇಶ ಯೋಜನಾ ಪ್ರಾಧಿಕಾರ | BIAAPA (header) |
| ಬಿಐಎಎಪಿಎ | BIAAPA (in reference no.) |
| ವಿನ್ಯಾಸ ನಕ್ಷೆ ಅನುಮೋದನೆ | Layout plan approval |
| ಭೂಪರಿವರ್ತನಾ ಆದೇಶ | Land conversion order |
| ದೇವನಹಳ್ಳಿ | Devanahalli (BIAAPA HQ) |

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

**Naming convention:**
- Manual translation: `BIAAPA_Letter_English_Manual_Translation.html`
- Gemini AI translation: `BIAAPA_Letter_English_Gemini35Flash_Translated.html`
- Original Kannada image as PDF: `BIAAPA_Letter_Kannada_Original_<Date>.pdf`

**Always file three artifacts together:**
1. Manual translation HTML
2. Gemini translation HTML (if created)
3. Original Kannada letter as PDF (converted from the source image)

## Pitfalls

- **OpenRouter credits**: `google/gemini-3.5-flash` works well when credits are available. Without credits, fall back to manual translation from Tesseract OCR. Do NOT keep retrying failed OpenRouter calls — check available models first via API.
- **Tesseract quality on Kannada**: ~60-70% accuracy on clean 250+ DPI scans. Cross-reference dates/amounts visually from the original image. Some Kannada characters render as garbled Latin.
- **Vision model fails on Kannada**: Both built-in vision and OpenRouter Gemini may produce garbled OCR on Kannada. Tesseract with `-l kan` gives better results.
- **Write location permissions**: Cannot write to `/tmp/` or `/data/hermes/users/ndr/` paths. Use `/opt/data/` or `/data/hermes/cron/output/ndr/` for local staging before Drive upload.
- **⚠️ Do NOT default to temp.tmp for legal documents**: Legal correspondence (BIAAPA, DC, Tahsildar) about a specific survey number must go in the legal documentation folder for that property. Search for entity names (trusts), legal-docs folders with the survey number, and the project's legal subfolder before falling back to temp.tmp. The user will correct you if you file legal docs in a generic folder.
- **Convert the original image to PDF and file alongside the translations**: The user expects the source Kannada document to be filed as PDF in the same folder as the translated HTMLs.
- **Search multiple name variants for the target folder**: The legal docs for a property may be under the trust/entity name (Godwad Bhavan Jain Trust), the village name (Hulurugurki), a dedicated survey-number folder (Bamnolim Sy No 93-2 Legal Documents), or the project name (Serenity Hill View). Search all of these — the project name alone is not enough.

## Verified Examples

### Example 1 — BIAAPA Letter No. BIAAPA/TP/MIS/07/2025-26/26 (22 JUN 2026)

- **Subject:** Sy. 93/2, Hurulugurki Village, Vijayapura Hobli — Land conversion cancellation report
- **Key finding:** BIAAPA confirmed NO layout/development plan approval was granted for 6A-26G in Sy. 93/2
- **Manual output:** `BIAAPA_Letter_English_Manual_Translation.html` (Tesseract OCR → manual translate)
- **Gemini output:** `BIAAPA_Letter_English_Gemini35Flash_Translated.html` (Tesseract OCR → `google/gemini-3.5-flash`)
- **Delivery:** Initially filed in standalone `Serenity Hill View` folder; corrected to `Godwad Bhavan Jain Trust Nandi Hills property` (where all related Sy No 93/2 legal PDFs reside)
