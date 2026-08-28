---
name: recruitment-candidate-pipeline
description: "Manage candidate recruitment tracking for DRAAS — create Drive resume folders, upload CVs with public sharing, build master tracking sheets with candidate details, resume links, and daily follow-up remarks column. Trigger when user says 'create hiring sheet', 'track candidate', 'resume for hiring', 'DRA hiring master sheet', 'add candidate to pipeline', or shares a resume PDF."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Recruitment Candidate Pipeline — DRAAS Hiring Tracker

Class-level workflow for creating and maintaining a recruitment candidate tracking system. Covers resume storage, candidate details extraction, and a master sheet with daily follow-up.

## When to load this skill

Triggers (any one):
- "create a hiring sheet" / "DRA hiring master sheet"
- "track this candidate" / "add candidate to pipeline"
- User shares a resume PDF (`.pdf`) and says it's for hiring
- "store this resume and create a tracker"
- "give some details about the candidate and keep a remark on daily basis on the follow"

## Core Workflow

### 1. Receive & parse the resume PDF

The resume lands at `/data/hermes/document_cache/` when the user uploads it. Extract candidate info with pymupdf:

```python
import fitz
doc = fitz.open(resume_path)
text = ""
for page in doc:
    text += page.get_text()
doc.close()
```

### 2. Create a Drive folder for resumes

Create one folder per hirng drive (e.g. "DRA Hiring - Resumes"), not one per candidate:

```python
folder = drive.files().create(
    body={"name": "DRA Hiring - Resumes", "mimeType": "application/vnd.google-apps.folder"},
    fields="id, name, webViewLink"
).execute()
folder_id = folder["id"]
folder_link = folder["webViewLink"]

# Set sharing to anyone-with-link
drive.permissions().create(
    fileId=folder_id,
    body={"type": "anyone", "role": "reader"}
).execute()
```

### 3. Upload resume PDF to the folder

Name the file with candidate name (e.g. `Divya_Narayan_Resume.pdf`):

```python
from googleapiclient.http import MediaFileUpload

resume = drive.files().create(
    body={"name": resume_filename, "parents": [folder_id]},
    media_body=MediaFileUpload(local_path, mimetype="application/pdf"),
    fields="id, name, webViewLink"
).execute()
resume_link = resume["webViewLink"]

# Set public sharing
drive.permissions().create(
    fileId=resume["id"],
    body={"type": "anyone", "role": "reader"}
).execute()
```

### 4. Extract candidate info (text + OCR fallback)

Resumes may be text-based PDFs or scanned images:

```python
import fitz
doc = fitz.open(resume_path)
text = ""
for page in doc:
    text += page.get_text()
    images = page.get_images()
    # Images indicate a scanned PDF — need OCR
doc.close()

# If all pages have images and no text, OCR the PDF:
if not text.strip():
    import os
    ocr_path = "/tmp/ocr_temp.pdf"
    os.system(f"ocrmypdf --force-ocr --language eng {resume_path} {ocr_path}")
    doc = fitz.open(ocr_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
```

### 4b. Parse candidate fields

| Field | Extraction method |
|-------|------------------|
| **Name** | Usually first line of the resume, before contact info |
| **Email** | Regex `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` |
| **Phone** | Regex `\d{10}` — extract last 10 digits |
| **Experience** | Date ranges in work history. Compute total (e.g. "5 yrs 6 mo"). If explicit mention exists (e.g. "5y 6m" in filename), use that. |
| **Position** | Most recent job title (after name/summary) |
| **Skills** | Look for a "Skills" or "Core Skills" section, bullet list |
| **Education** | Look for "Education" section — degrees, institutions, years |
| **Location** | Address line near the name/contact section |

### 5. Create the master tracking sheet

Build with openpyxl using the full column set Bharat requested:

**10-column structure:**

| # | Name | Position | Email | Phone | Experience | Education | Skills | Resume Link | Remarks / Daily Follow-up |
|---|------|----------|-------|-------|------------|-----------|--------|-------------|---------------------------|

**Phone number format (Bharat preference):** Prefix as `91XXXXXXXXXX` — no `+` symbol. Do NOT use `+91`. The raw digits from the resume are sufficient; just prepend `91`.

**WhatsApp hyperlink:** Add wa.me link on the phone column so taps open WhatsApp (e.g. `https://wa.me/91{digits[-10:]}`).

**Resume Link column:** Clickable hyperlink "View Resume" pointing to the Drive file. Set as column 9 (I).

**Remarks column:** Highlight with a yellow/light fill to distinguish it. Pre-populate with context from the conversation (e.g. "Contacted once — did not answer. Follow up again."). Make the text italic.

**Education column (col 7):** Degrees, institution names, and years.
**Skills column (col 8):** Bullet list of core competencies. Use a smaller font (size 9) since these are often long strings.
**Experience column (col 6):** Include total years + recent employers in parentheses.

### 5. Upload the sheet to Drive root

```python
media = MediaFileUpload(out_path, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
sheet = drive.files().create(
    body={"name": "DRA_Hiring_Master_Sheet.xlsx"},
    media_body=media,
    fields="id, name, webViewLink"
).execute()

# Set public sharing
drive.permissions().create(
    fileId=sheet["id"],
    body={"type": "anyone", "role": "reader"}
).execute()
```

### 6. Share the links back

Return both links in the Telegram response:
- Folder link
- Master sheet link

## Candidate info extraction (from resume text)

Parse these fields from the PDF text:

| Field | Regex / pattern |
|-------|----------------|
| **Name** | Usually first line of the resume |
| **Email** | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` |
| **Phone** | `\d{10}` (extract last 10 digits) |
| **Experience** | Look for date ranges. Count from earliest job start to present. Common format: "X yrs Y mo" or explicit year ranges. |
| **Position** | Most recent job title (often right after name/summary) |

## Adding more candidates later

When new resumes come in:
1. Upload PDF to the existing "DRA Hiring - Resumes" folder
2. Open the existing master sheet from Drive
3. Append a new row with all 9 data columns (#, Name, Position, Email, Phone, Experience, Education, Skills, Resume Link)
4. Pre-fill the Remarks column with "New - Awaiting contact" or context from the conversation
5. Re-upload the updated sheet (delete old, upload new)

Use the same phone format (`91XXXXXXXXXX`, no `+`).

## Pitfalls

### 1. Don't modify an existing unrelated sheet

If the user asks for a hiring sheet, create a **fresh** Excel file. Do NOT add columns to an existing leads sheet, contact numbers sheet, or insurance sheet. The user corrected this explicitly: "I hope you have done it in a wrong way. So let's not do it in this. Let's create a fresh excel sheet."

### 2. Phone number format — no plus symbol

Bharat explicitly said "Let's not add on the plus symbol in front of that." Numbers must be `91XXXXXXXXXX`, never `+91XXXXXXXXXX`.

### 3. Always set sharing to "Anyone with link"

Both the folder and individual resume files should have `type: "anyone", role: "reader"` permissions. This lets the hiring team and candidates access resumes without signing in.

### 4. Resume file naming

Use the candidate's actual name in the filename, not the original uploaded filename (which may be a generic Naukri filename like `Naukri_Divya_5y_1m_.pdf`).

### 5. The remarks column is for daily tracking

Pre-populate with the current follow-up status. The user updates it manually over time. Make this column visually distinct (yellow fill, italic text) so it's easy to spot.

## Output

After completing the workflow, deliver to the user:
- 📁 Resumes folder link
- 📊 Master sheet link
- A brief summary of the candidate(s) added

## Employee Aadhaar / ID Card Tracker (parallel intake pattern)

Similar to resume intake, but for employee identity documents (Aadhaar cards, PAN cards, DLs). The user uploads card images/PDFs one at a time, and you build a running Google Sheet tracker.

### Trigger signals
- User uploads or shares an Aadhaar card image/PDF (can detect by seeing "Aadhaar No." in OCR)
- User says "I'm uploading Aadhaar cards for employees" or "keep a tracker of these cards"
- User sends any identity document and asks you to maintain a record

### Workflow

#### 1. Process incoming document
The user sends images/PDFs one at a time (Aadhaar card, PAN, DL). For each:

```python
# Aadhaar cards: convert PDF to image -> vision_analyze
# pdftoppm if PDF, else use the image directly

# Extract via vision_analyze:
# - Name (from Aadhaar card text)
# - Address (multi-line from card)
# - DOB (from DOB: field or D.O.B.)
# - Aadhaar No (12 digits, strip OCR artifacts like $, FH)
# - Gender
# - S/O or C/O name

# Calculate age from DOB:
from datetime import date
today = date.today()
age = today.year - birth_year - ((today.month, today.day) < (birth_month, birth_day))
```

#### 2. Upload card image to Drive

Upload each card image to Drive root (or shared folder) for permanent reference:

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3')
media = MediaFileUpload(local_path, mimetype='image/jpeg')
meta = {'name': f'Aadhaar_{employee_name}.jpg', 'parents': []}
uploaded = drive.files().create(body=meta, media_body=media, fields='id, name, webViewLink').execute()
card_link = uploaded['webViewLink']
```

#### 3. Create or update the tracker sheet

Create a fresh Google Sheet (not Excel — so both you and the user can edit/add rows remotely):

```python
from tools.gws_auth import build_service

drive = build_service('drive', 'v3')
sheet_meta = {'name': 'Employee Aadhaar Tracker', 'mimeType': 'application/vnd.google-apps.spreadsheet'}
sheet = drive.files().create(body=sheet_meta, fields='id, name, webViewLink').execute()
sheet_id = sheet['id']
```

**Columns:**

| S.No | Employee Name | Address | Date of Birth | Age | Aadhaar Card Link |
|---|---|---|---|---|---|

Write headers via Sheets API batchUpdate with bold formatting, then append rows as documents arrive:

```python
sheets = build_service('sheets', 'v4')
body = {'values': [[sno, name, address, dob, age, link]]}
sheets.spreadsheets().values().update(
    spreadsheetId=sheet_id, range='A2:F2',
    valueInputOption='USER_ENTERED', body=body
).execute()
```

#### 4. Handle batch uploads

When multiple Aadhaar images arrive in a batch (several files in one message), process each one and append all rows at once. Validate each extraction independently — don't assume one extraction error means all failed.

#### 5. Handle partial/cropped images

Some Aadhaar images may be cropped (showing only the bottom portion with DOB and name, but missing the Aadhaar number). For partial images:

- Extract whatever is visible (name, DOB, gender)
- Mark the missing fields with "—" in the sheet
- Add a note column or mention in summary that the document was cropped
- The user may send a complete version later — update the row when they do

### Pitfalls

- **Aadhaar OCR artifacts**: Strip non-digit characters from Aadhaar numbers. A valid Aadhaar is exactly 12 digits. OCR commonly adds `$`, `B`, `F`, `H` as artifacts — `"$B012184575FH"` → strip to `"012184575"` → if not 12 digits, re-check the image (the actual card usually shows `XXXX XXXX XXXX` clearly).
- **DOB format**: Indian Aadhaar cards show DOB as `DD/MM/YYYY`. Calculate age as `today.year - birth_year - ((today.month, today.day) < (birth_month, birth_day))`.
- **Vision model fallback failures**: If `vision_analyze` returns 404, fall back to tesseract CLI. Do NOT retry more than twice — tesseract handles scanned Aadhaar cards reliably.
- **Duplicate detection**: Before adding a new entry, check if the Aadhaar number (last 4 digits) already exists in the sheet to avoid duplicates when the user re-sends a card.
- **Address formatting**: Aadhaar addresses are multi-line (building, street, locality, district, state, PIN). Join with commas for the sheet; truncate if too long.
- **Batch gaps**: When the user sends a batch of documents, each one may need different tooling (PDF → pdftoppm, JPEG → direct vision, cropped → tesseract). Handle each document independently and report a per-document summary.

### Sheet sharing

Share the sheet link back to the user after each update so they can view progress:

```python
print(f'Tracker: https://docs.google.com/spreadsheets/d/{sheet_id}/edit')
```

### Example output format

```
Added 3 more to the tracker:

| # | Name | DOB | Age |
|---|---|---|---|
| 4 | Ravi Kumar V | 17/07/1978 | 47 |
| 5 | Bharat Hawaldar | — | — |
| 6 | Anbarasan M | 15/10/1987 | 38 |
```

For a full worked example (6 documents processed, tool selection matrix, all extracted fields), see `references/employee-aadhaar-tracker-workflow.md`.

## Related skills

- `real-estate-leads-tracking` — Similar pattern of source-data → tracking sheet, but for sales leads not hiring candidates
- `dra-employment-documents` — Drafting offer letters and employment contracts (downstream from hiring)
- `gws-automation` — GWS auth patterns, shared by all Drive/Gmail workflows
- `ocr-and-documents` — Document extraction patterns (pdftoppm, tesseract, vision_analyze) shared by the Aadhaar intake workflow

## Absorbed Skills

### employee-onboarding → recruitment-candidate-pipeline

**Absorbed:** `employee-onboarding` (2026-08-09) — the post-offer, pre-joining phase of the same hiring lifecycle.

**Content:** Full SKILL.md stored as `references/employee-onboarding-full.md`; worked example at `references/sai-neha-onboarding-workflow.md`. Key preserved detail:
- **Onboarding triggers:** "create an account for [name]", "set up email for [name]", "add [name] to my contacts" (new-hire context), "onboard [name]"
- **Data sources in order:** Gmail offer letter (often a **.docx** attachment — zipfile+XML extraction, not python-docx) → Drive resume PDF (may be a Google Doc — export as text/plain) → correspondence thread (negotiation history, official-email-ID request)
- **Contacts:** People API `createContact` (work + personal email, org DRA Realty, biography with manager + group email) + NDR DRAAS contacts sheet (`1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`) — **two tabs**: `employees` (simple append) and `NDR DRAAS Google contacts.csv` (93-column row, **must use `insertDataOption='INSERT_ROWS'`** — the fixed grid 400s on `update`)
- **Welcome WhatsApp:** wa.me link with greeting → company email `<username>@draas.com` → temp password → login steps → group email info; **always get the temp password from Nishant** (agent has no admin access) and cross-verify the phone from ≥2 sources
- **Email convention:** first-initial + last-name `@draas.com` (e.g. `nVaddadi@draas.com`) — confirm with Nishant before assuming

**Archived.**

### dra-hiring-tracker → recruitment-candidate-pipeline

**Absorbed:** `dra-hiring-tracker` (2026-06-12)

**Content:** Copy of the full SKILL.md stored as `references/dra-hiring-tracker.md`. The `dra-hiring-tracker` skill covered the same resume-intake-to-master-sheet workflow but was a subset of this skill. Key preserved details:
- DRA Hiring folder ID: `18nyMns_2KYbJhhLMsyQ3fR3G5lWxzlyv`
- Master sheet name: `DRA_Hiring_Master_Sheet.xlsx`
- Phone format: `91XXXXXXXXXX` (Bharat preference)
- Sheet update pattern via openpyxl + Drive API delete-then-upload

**Archived.**
