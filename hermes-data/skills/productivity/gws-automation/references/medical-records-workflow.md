# Medical Records Workflow — Nishant / DRAAS

## Context
Nishant manages his children's (Ruhaan, Rivaan) medical records on Drive. Whenever a new doctor is consulted, a new prescription is written, or a medical invoice is received, he wants everything systematically recorded. This reference documents the standard workflow.

## Drive Folder
All medical documents go in the **Ruhaan Medical** folder:
- **Folder ID:** `0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k`
- **Link:** https://drive.google.com/drive/folders/0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k
- All files named as: `YYYYMMDD_Description_Patient_Doctor_Hospital.pdf/doc`

## File Naming Convention
Use Nishant's standard naming: `YYYYMMDD_ShortDescription_KeyDetails.pdf`
- Medical invoices: `YYYYMMDD_Hospital_Invoice_Medicines_DoctorName.pdf`
- Prescriptions: `YYYYMMDD_Patient_Doctor_Hospital_Prescription_Condition.pdf`
- Verbal consultation records: `YYYYMMDD_Patient_VerbalPrescription_DoctorName_Hospital_Condition`

## Workflow Steps

### 1. Receive a Medical Document (PDF/Scan)
- Use OCR (tesseract or ocrmypdf) to extract text content from scanned PDFs
- Identify: patient name, doctor name, hospital, medicines, amounts, dates
- The user typically shares via Adobe Scan or similar

### 2. Upload Invoice to Drive
- Upload to the Ruhaan Medical folder with proper naming
- Set permission: `{'type': 'anyone', 'role': 'reader'}` for easy sharing
- Record the Drive file ID for reference

### 3. Create Prescription Record (Google Doc)
When the user gets verbal advice from a doctor (phone consultation), create a Google Doc in the same folder:

```python
docs = build('docs', 'v1', credentials=creds)
prescription_doc = docs.documents().create(body={'title': title}).execute()
prescription_id = prescription_doc['documentId']

# Move to medical folder
drive.files().update(fileId=prescription_id, addParents=folder_id, removeParents='root').execute()
```

Document content should include:
- Patient details (name, DOB, age)
- Consulting doctor (name, hospital, specialty, phone)
- How the doctor was introduced / reached
- Clinical context (what prompted the consultation)
- Doctor's advice verbatim (medicines, doses, instructions)
- Follow-up instructions (e.g., "if not settled → chest X-ray")
- Date and time of consultation
- Note: source of information (telephonic, in-person)

### 4. Add Doctor Contact — Two Places (always both)

#### A) Google Contacts (People API)
```python
people = build('people', 'v1', credentials=creds)
contact = {
    'names': [{'givenName': 'First', 'familyName': 'Last', 'displayName': 'Dr. Full Name'}],
    'phoneNumbers': [{'value': '+91XXXXXXXXXX', 'type': 'mobile'}],
    'organizations': [{'name': 'Hospital Name', 'title': 'Specialty'}],
    'biographies': [{
        'value': 'Context about who introduced them, when consulted, what for.',
        'contentType': 'TEXT_PLAIN'
    }]
}
created = people.people().createContact(body=contact).execute()
```

**Note:** The People API does NOT accept a `labels` field — don't include it or the request fails with `Invalid JSON payload... Cannot find field`.

#### B) DRAAS Contacts Sheet
Sheet: `NDR DRAAS Google contacts.csv` in spreadsheet ID `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`

Append using the Sheets API:
```python
sheets.spreadsheets().values().append(
    spreadsheetId=sheet_id,
    range='NDR DRAAS Google contacts.csv!A:S',
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body={'values': [row_data]}
).execute()
```

Column mapping (0-indexed):
- A=0: First Name
- B=1: Middle Name
- C=2: Last Name
- G=6: Name Prefix (Dr.)
- J=9: File As
- K=10: Organization (Hospital)
- L=11: Organization Title (Specialty)
- O=14: Notes (consultation context)
- Q=16: Labels (* myContacts)
- R=17: Phone 1 Label (Mobile)
- S=18: Phone 1 Value (+91 number)

### 5. Create Medication Calendar Reminders

When a new medication is prescribed (e.g., Augmentin × 3 days, BD), create calendar events as reminders:

```python
calendar = build_service('calendar', 'v3')

attendees = [
    {'email': 'ruhaanr.2030@gsuite.aditi.edu.in', 'displayName': 'Ruhaan Ranka'},
    {'email': 'rnr@draas.com', 'displayName': 'Roshini Ranka'}
]

reminders = {
    'useDefault': False,
    'overrides': [{'method': 'popup', 'minutes': 15}]
}

# Doses: (date, hour, label)
doses = [
    ('2026-06-21', 19, 'Night (Dose 1 of 6)'),
    ('2026-06-22', 7,  'Morning (Dose 2 of 6)'),
    # ... etc
]

for date_str, hour, label in doses:
    event = {
        'summary': f'💊 Augmentin 625 - Ruhaan {label}',
        'description': 'Ruhaan — Augmentin 625 mg (after food)\nPrescribed by Bhagwan Mahaveer Jain Hospital\n...',
        'start': {'dateTime': f'{date_str}T{hour:02d}:00:00', 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': f'{date_str}T{hour:02d}:15:00', 'timeZone': 'Asia/Kolkata'},
        'reminders': reminders,
        'attendees': attendees,
    }
    calendar.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
```

**Always add both the child (school email) and parent (rnr@draas.com) as attendees** so both get 15-min popup reminders.

### 6. Add Entry to Medical Report Index (Spreadsheet)

The **Ruhaan Medical Report Index** (spreadsheet ID: `1E14iA3xDdoBaC0Sdlim6r6MipmSzNkKqFLaV2dXvHQU`) is the master chronological log. Always append a row for new incidents:

```python
# Get next Sl No
res = sheets.spreadsheets().values().get(spreadsheetId=ss_id, range='A:A').execute()
nums = [int(r[0]) for r in res.get('values', [])[1:] if r and r[0].isdigit()]
next_no = max(nums) + 1 if nums else 1

new_row = [
    str(next_no),
    'PRESCRIPTION / OPD',           # TYPE column
    '21/06/2026',                     # DATE
    '20260621 Description - Hospital', # REPORT NAME
    'https://drive.google.com/file/d/.../view',  # LINK
    '20260621 Short Description'      # REPORT NAME (duplicate column)
]

sheets.spreadsheets().values().append(
    spreadsheetId=ss_id, range='A:F',
    valueInputOption='USER_ENTERED',
    body={'values': [new_row]}
).execute()
```

**Column structure:** Sl. No | TYPE | DATE | REPORT NAME | LINK | REPORT NAME (dup)

Common TYPE values: `PRESCRIPTION / OPD`, `REPORT`, `BILL`, `RADIOLOGY REPORT`, `ADVISE`, `PRESCRIPTION`

### 7. Add Note to Medical Notes & Corrections (Companion Sheet)

The **Medical Notes & Corrections** sheet (ID: `1wNADzWJjdjkqgu4WT0_-uKq2kHBSo3rGuTMoPjpfMKE`) captures chronological notes with links:

```python
note = [
    '21 Jun 2026',                              # Date
    'Minor Surgery / Splinter Removal',          # Category
    'Full description of what happened...',      # Description
    'Hospital Name — Patient No 12345 — Splinter Photo: LINK'  # Source / Links
]

sheets.spreadsheets().values().append(
    spreadsheetId=ss_id2, range='A:D',
    valueInputOption='USER_ENTERED',
    body={'values': [note]}
).execute()
```

### 8. Upload Document Photos/Scans to Drive Folder

When the user sends photos or scanned documents (Adobe Scan PDFs), upload them to the **Ruhaan Medical** folder with proper naming:

```python
file_metadata = {
    'name': 'YYYYMMDD_Description_Hospital.pdf',
    'parents': ['0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k'],
}
media = drive.files().create(
    body=file_metadata,
    media_body='/path/to/local/file.pdf',
    fields='id,name,webViewLink'
).execute()
```

After upload, update the Medical Report Index row's LINK column with the file's `webViewLink`.

## Multi-Phase Dossier Creation (Complex Second-Opinion Requests)

When the user needs a comprehensive medical dossier for a second opinion, use this phased approach:

### Phase 1 — Ingest & Index
- List all files in the Drive folder recursively (skip non-medical folders like "Invoices and Bills")
- Spawn parallel subagents to parse: summary docs, report index sheets, PFT PDFs, prescription PDFs, lab reports
- Extract structured data: FEV1, FVC, FEF25-75, FeNO, eosinophils, IgE, medication names/doses
- Build a MASTER INDEX (chronological, tagged by relevance)

### Phase 2 — Gap Analysis & User Q&A
- Compare MASTER INDEX against clinical completeness checklist
- Ask targeted questions in small batches; accept "skip/N/A/proceed"
- Confirm: patient identity, cough timing (especially sleep resolution), habit cough history, medication timeline accuracy, test status (IOS/HRCT done or not)

### Phase 3 — Ideation (external models)
- Send the ideation brief to external models (GPT-5.5, Opus 4.8) via OpenRouter for presentation strategy
- Reconcile the two blueprints, keeping the best of each

### Phase 4 — Drafting
- Generate the full dossier content (markdown or HTML)
- Build a professional PDF using WeasyPrint (see `references/weasyprint-pdf-generation.md`)
- A4 page size, dashboard-style tables, color-coded competing views, highlighted key facts

### Phase 5 — QA & Delivery
- Verify ALL Drive links resolve
- Set source file permissions to "Anyone with link (Reader)"
- Delete old document versions
- Upload PDF to Drive
- Deliver via Telegram (MEDIA: prefix) and/or Gmail draft

## "Medical Facts & Corrections" Companion Sheet Pattern

When creating a second-opinion dossier, always create a companion Google Sheet titled "Medical Notes & Corrections" that captures:

- **Absolute facts** that may overrule conflicting prescription/doctor-note details
- **Timeline corrections** (e.g., Duolin was TID scheduled, not SOS)
- **Medication change history** with exact dates and reasoning
- **Doctor identification** (some may be unnamed/unknown)
- **Pre-asthma context** for prior episodes

The sheet should open with an explicit disclaimer:
> "ABSOLUTE FACTS — These notes contain verified facts that overrule any conflicting information that may appear in individual prescriptions or doctor notes."

Column headers: `Date/Period | Category | Fact (absolute) | Source/Rationale`

Link this sheet in the dossier's footer and in the report index section. See `references/sheets-create-and-populate.md` for API pattern.

## Medical Report Compilation from Drive — Existing Reports Dossier

When Nishant asks to compile all reports for a specific specialty (e.g., ear/ENT) across family members from their existing Drive folders, use this pattern.

### Drive Folder Hierarchy (Nishant's Personal)

The medical folders live under **Personal** on Nishant's Drive (ndr@draas.com):

```
My Drive / Personal /
  ├── NDR Medical           (Nishant's own medical records) ID: 0B1Oc8cSaJXPGT1JPMVlfajFnTmc
  ├── KDR Docs / KDR Medical (Mom - Kanta Ranka)           ID: 0B1Oc8cSaJXPGUUtVbTJHb0Y3V2s
  ├── DR Medical            (Dad - Dinesh Ranka)
  ├── SDR Medical           (SDR)
  ├── SMR Medical           (SMR)
  └── Mamta Rathod / MRR /    (Sister — Mamta Ranjeeth Rathod)
       └── Medical            (Her medical records, reports, blood work)
```

**Sibling folders** follow the pattern `Personal / [Name or Initials] / Medical`. Mamta's folder may be named `Mamta Rathod`, `MRR`, or `Mamta Rathode` — search all variants. This hierarchy covers not just parents but also extended family members whose documents Nishant manages.
```

### Vault Authentication

Nishant's vault user_id is `ndr-<telegram-id>` (draas_user_id + "-" + telegram_id). The vault stores tokens for:
- `google-draas` — ndr@draas.com (has Drive scope — use for all Drive operations)
- `google-ahfl` — ndr@ahfl.in
- `google-gmail` — nishantranka@gmail.com

**Never use the default `build_service()` without explicit service_name.** Always use:
```python
drive = build_service('drive', 'v3', telegram_id='ndr', service_name='google-draas')
```

### Discovery & Inventory Pattern

1. **Find the Personal folder** — search for name='Personal' with mimeType='application/vnd.google-apps.folder' on the Drive root
2. **List subfolders** — query for 'Medical' under Personal to find all family member folders
3. **Full inventory** — list ALL files in each target folder sorted by name (typically YYYYMMDD prefix)
4. **Specialty search** — search across each folder for medical specialty terms relevant to the request:
   - Ear/ENT: 'audi', 'ENT', 'Haldipur', 'otosc', 'tympan', 'ear', 'hearing'
   - For unrelated audio files ('Audio' matches 'audiology' search), filter manually
   - Audit-related business documents ('Auditor', 'Audited') also match 'audi' — filter these out

### Compilation Method

1. **Present findings first** — show the user the full list with dates, file names, and Drive links in chronological order per person. Let them confirm before downloading anything. Get explicit confirmation of which files to include.

2. **Examine and rename mislabeled files** — Files in a patient's folder that reference a different name (e.g., "Mr Dhananjay - Tympanogram" in KDR Medical) may still belong to that patient. Open the file to verify, then rename it appropriately on Drive with the correct patient prefix. Confirm the rename with the user.

3. **Download all confirmed PDFs** from Drive to local temp directory using `drive.files().get_media(fileId=...).execute()`.

4. **Extract content** — use parallel sub-agents for:
   - Text-based PDFs: extract with pdftotext or pymupdf
   - Scanned/image-only PDFs: convert to PNG via pdftoppm then use vision_analyze
   - Build structured JSON per file: date, type, hospital, doctor, summary text

5. **CRITICAL: Build ONE separate PDF per patient, NOT one combined PDF** — Nishant explicitly prefers separate PDFs per person, each with its own title page, summary, timeline, and index. Use fpdf2 + pypdf (see "PDF Construction with fpdf2 and pypdf" section below for the complete technique).

6. **Each patient PDF should have:**
   - **Page 1:** Title page — patient name, date range, total report count
   - **Page 2:** Executive summary — chronological sequence of events, key diagnoses, surgeries, follow-ups in narrative form
   - **Page 3:** Chronological timeline table — every report as a table row with Date, Type, Hospital/Doctor, and Key Finding
   - **Page 4+:** Index with page numbers — sequential list of all reports mapping to their start page
   - **Remaining pages:** All original PDFs merged in chronological order via pypdf

7. **Upload to Drive** — upload each patient's PDF into their respective medical folder:
   ```python
   drive.files().create(
       body={'name': 'YYYYMMDD_Patient_Medical_Records_Compilation.pdf', 'parents': [FOLDER_ID]},
       media_body='/path/to/local/pdf'
   ).execute()
   ```

8. **Delete old compilation from both folders** — if a previous combined PDF exists in any folder, remove it to avoid confusion:
   ```python
   svc.files().delete(fileId=old_file_id).execute()
   ```

### PDF Construction with fpdf2 and pypdf

Use fpdf2 for the summary/index pages and pypdf to merge the original report PDFs. This avoids format loss from copying content out of PDFs — the original reports stay verbatim.

**Setup:**
```python
from fpdf import FPDF
from pypdf import PdfWriter, PdfReader
```

**IMPORTANT: Unicode font registration (Helvetica does NOT support Unicode):**
The default fpdf2 font (Helvetica) only supports latin-1. Characters like em-dash (—), bullet (•), accented letters, or any non-latin-1 character will raise `FPDFUnicodeEncodingException`. Always register a Unicode TTF font:

```python
FONT_REGULAR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

class SummaryPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('DejaVu', '', FONT_REGULAR, uni=True)
        self.add_font('DejaVu', 'B', FONT_BOLD, uni=True)
        self.add_font('DejaVu', 'I', FONT_REGULAR, uni=True)

    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', 'I', 7)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')
```

Replace ALL `set_font('Helvetica', ...)` calls with `set_font('DejaVu', ...)` everywhere.

**Building summary pages:**
```python
pdf = SummaryPDF()
pdf.set_auto_page_break(auto=True, margin=20)

# Title page
pdf.add_page()
pdf.set_font('DejaVu', 'B', 18)
pdf.cell(0, 15, 'Medical Records Compilation', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# Executive summary
pdf.set_font('DejaVu', '', 10)
pdf.multi_cell(0, 5, summary_text)

# Chronological timeline table — use alternating row fills and a dark blue header
col_w = [18, 30, 50, 92]
pdf.set_fill_color(41, 65, 122)
pdf.set_text_color(255, 255, 255)
# ... cell fills ...

# Index table listing each report with page numbers
```

**Merging original PDFs:**
```python
writer = PdfWriter()

# Add summary pages first
summary_reader = PdfReader(summary_pdf_path)
for page in summary_reader.pages:
    writer.add_page(page)

# Add each original PDF
for f in sorted_files:
    reader = PdfReader(f['local_path'])
    for page in reader.pages:
        writer.add_page(page)

with open(output_path, 'wb') as f:
    writer.write(f)
```

**Running the script:**
- fpdf2 and pypdf are installed in `/opt/hermes/.venv`
- Always run with `/opt/hermes/.venv/bin/python3 script.py` — system `python3` won't find these packages
- Write the script as a `.py` file via `write_file()`, then run via `terminal()`

### NDR Medical — Ear-Specific Files Reference (discovered Jul 2026)
- 20221003 NDR R Audiological Evaluation & Impedence Test DrVijendraENT
- 20230203 NDR R Audiometry Evaluation ManipalHospital (Dr. Veena Yagna)
- 20230411 Manipal hospital - ENT Audiology

### KDR Medical — Ear-Specific Files Reference (discovered Jul 2026)
- 20170718 KDR R AUDIOMETRY BhagwanMahaveerJainHospital (first baseline)
- 20221003 KDR R Audiological Evaluation DrVijendraENT
- 20221003 Vijaya E.N.T Care Centre - Advance
- 20230411 Manipal Hospital Advise - Dr Veena Yagna(ENT)
- 20230411 Manipal hospital - ENT Audiology
- 20230606 Trustwell Hospital - Audiological Evaluation Report Dr Deepak Haldipur
- 20230606 Trustwell Hospital - Advanced otosclerosis Dr Deepak V Haldipur (diagnosis)
- 20230612 KDR R Biochem & Others TrustwellHospital (pre-surgery blood work)
- 20230612 KDR Chest PA XRay Report (pre-surgery chest X-ray)
- 2023613 KDR Discharge Summary Trustwell Hospital - Dr.Deepak Haldipur (surgery)
- 20250604 KDR A Dr Haldipur Trustwell Hospital (follow-up consult)
- 20250604 KDR R Audiological Evaluation Trustwell Hospital (follow-up audiology)
- 20250604 KDR Chest X-ray Trustwell Hospital (follow-up chest X-ray)
- 20250604 KDR R ECG Trustwell Hospital (follow-up cardiac)
- 20250604 KDR R Multiple Blood Tests Trustwell Hospital (follow-up labs)

### Pitfalls
- **User wants SEPARATE PDFs per person, not one combined file** — Nishant explicitly rejected mixing reports from two patients into a single PDF. Always build one PDF per patient with its own title, summary, timeline, and index. Confirming this upfront saves a full rebuild cycle.
- **File named after the wrong person may still belong to the correct patient** — e.g., "Mr Dhananjay - 226 Hz Tympanogram.pdf" in KDR Medical was actually Kanta's test with a data-entry error. Always open and verify before excluding. After confirming, rename the file on Drive.
- **fpdf2 default font (Helvetica) does not support Unicode** — em-dashes, bullets, accented characters, and non-latin chars trigger `FPDFUnicodeEncodingException`. Register DejaVu Sans TTF as a custom font and replace ALL Helvetica references in your script. Available at `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf` and `DejaVuSans-Bold.ttf`.
- **Null doctor values cause AttributeError** — `f.get('doctor')` returns None for explicitly null fields. Use `(f.get('doctor') or '')` instead of `f.get('doctor', '')`.
- **Old combined PDF lives in multiple folders after upload** — when replacing a combined PDF with separate per-patient PDFs, delete the old file from ALL folders it was uploaded to. Check each patient's folder individually.
- **ENT text search matches "Entrance" documents** — the substring "ent" appears in design/architecture files. Always search for 'ENT' (uppercase) or filter results.
- **'audi' matches 'audit' (business docs) and 'audio' (media files)** — manually separate medical audiology from auditor reports and audio recordings.
- **Vault may return empty services** if the user hasn't authorized. Fall back to vault socket discovery with the correct user_id format (`ndr-<telegram-id>`, not just `ndr` or `ndr`).
- **File output truncated** for large folders (>50 items) — use paginated listing with page_token for complete inventory.
- **KDR Medical folder is under KDR Docs, not directly under Personal** — searching 'Medical' directly under Personal may miss it if it's nested deeper.

## Invoice Subfolder Pattern (NDR/KDR Medical)
Each person's medical folder should have an **Invoices/** subfolder. All invoice, bill, and receipt files are moved there — never left mixed with reports and prescriptions.

### Creating the Invoices subfolder
```python
def create_folder(name, parent_id):
    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    created = drive.files().create(body=metadata, fields='id,name').execute()
    return created['id']

invoices_id = create_folder('Invoices', medical_folder_id)
```

### Moving existing invoice files into it
```python
def move_to_folder(drive, file_id, target_folder_id, source_folder_id):
    drive.files().update(
        fileId=file_id,
        addParents=target_folder_id,
        removeParents=source_folder_id
    ).execute()
```

### Identifying invoices by filename
Scan the folder listing for files containing: `Bill`, `Receipt`, `Invoice` in their name. These are financial documents and belong in Invoices/.

Invoice files typically include: consultation fees, lab test charges, procedure fees (wax removal, PTA), pharmacy bills.

## Granting Invoice Access to Team Members
When medical invoices need to be shared for accounting/records, grant reader access:
```python
for email in ['echamundeshwari@draas.com', 'rnr@draas.com']:
    perm = {'type': 'user', 'role': 'reader', 'emailAddress': email}
    drive.permissions().create(
        fileId=invoice_file_id,
        body=perm,
        sendNotificationEmail=False
    ).execute()
```

Nishant's standard: share with **Eshwari** (echamundeshwari@draas.com) and **Roshni** (rnr@draas.com) for any medical invoices that need to go to accounts.

## WhatsApp Message for Accounts
After filing invoices, generate a WhatsApp message with invoice details for the accounts group:
```python
whatsapp_link(
    text=f"KDR Medical Expenses — Date\n\n"
         f"Invoice 1: Description — Rs X,XXX\n"
         f"  🔗 Drive Link\n\n"
         f"Invoice 2: Description — Rs X,XXX\n"
         f"  🔗 Drive Link\n\n"
         f"Total: Rs XX,XXX\n\n"
         f"Please: Debit KDR's account & credit Nishant Ranka's account • "
         f"Record in expenses • Invoices shared with Eshwari & Roshni\n\n"
         f"Do the needful. Thanks."
)
```

Message structure:
1. Patient name and date
2. Each invoice with description, amount, and Drive link
3. Total amount
4. Instructions: debit patient account, credit Nishant, record in expenses
5. Note that invoices shared with Eshwari & Roshni

## Creating Google Contacts for Medical Professionals
When you extract contact info from medical documents (prescriptions, invoices, reports), create Google Contacts with full details:

### For doctors
```python
contact = {
    'names': [{'givenName': 'First', 'familyName': 'Last',
               'honorificPrefix': 'Dr.', 'displayName': 'Dr. Full Name'}],
    'organizations': [{'name': 'Hospital', 'title': 'Consultant ENT Specialist',
                       'department': 'ENT Department'}],
    'phoneNumbers': [{'value': '+91 80 XXXXXXXX', 'type': 'work'}],
    'emailAddresses': [{'value': 'hospital@email.com', 'type': 'work'}],
    'addresses': [{'streetAddress': 'No.5, J.C. Road', 'city': 'Bengaluru',
                   'region': 'Karnataka', 'postalCode': '560002', 'country': 'India',
                   'type': 'work'}],
    'urls': [{'value': 'https://www.hospital.com', 'type': 'work'}],
    'biographies': [{'value': 'Context / specialty notes', 'contentType': 'TEXT_PLAIN'}]
}
created = people.people().createContact(body=contact).execute()
```

### For non-doctor coordinators (e.g., surgery coordinators)
```python
contact = {
    'names': [{'givenName': 'Name', 'displayName': 'Name, Title - Doctor'}],
    'organizations': [{'name': 'Hospital', 'title': 'Operations Coordinator - Dr. X (Specialty)'}],
    'phoneNumbers': [{'value': '+91 XXXXXXXXXX', 'type': 'mobile'}],
    'relations': [{'person': 'Dr. Consulting Doctor', 'type': 'assistant'}],
    'biographies': [{'value': 'Context notes', 'contentType': 'TEXT_PLAIN'}]
}
```

Always extract:
- Full name as written on the document/prescription
- Phone numbers (landline and mobile)
- Hospital name, address, website
- Role/title
- Relationship to the consulting doctor
- Context about why they were contacted (surgery scheduling, pre-auth, etc.)

## Document Classification from Adobe Scans
When Nishant uploads Adobe Scan PDFs, classify each one by examining the content before renaming:

Common classifications for ENT consultations:
- **Audiological Evaluation Report**: PTA (Pure Tone Audiometry) results — audiogram chart
- **Consultation Advice / Prescription**: List of tests ordered by the doctor with hand-marked checkboxes
- **Lab Test Prescription**: Standing orders from the doctor for blood/urine/imaging tests
- **Invoice / Bill of Supply**: Financial document with bill number, patient name, items, amounts
- **Test Report**: ECG, 2D Echo, X-Ray, blood test results with actual values
- **Referral / Admission Note**: Doctor's instructions for next steps (surgery scheduling)

For each, determine:
1. Which patient (NDR/KDR/Ruhaan/Rivaan/DR/DDR)
2. Document type (from above)
3. Hospital/clinic
4. Doctor name
5. Date
6. Whether it's an invoice (belongs in Invoices subfolder)

## NDR/KDR Medical Folder IDs
```
NDR Medical: 0B1Oc8cSaJXPGT1JPMVlfajFnTmc
KDR Medical: 0B1Oc8cSaJXPGUUtVbTJHb0Y3V2s
```

KDR Medical lives under "KDR Docs" (parent: 1uzkxqMfHqBKu4GvEgaN8rHP8WJSRWbna)
NDR Medical lives under "Personal" (parent: 0B1Oc8cSaJXPGYkQtYXJDQWVBUVE)

## Vault Authentication for Nishant
- User ID: `ndr-<telegram-id>` (draas_user_id + "-" + telegram_id)
- Services: `google-draas` (ndr@draas.com — Drive + Gmail), `google-ahfl`, `google-gmail`
- Always use explicit `service_name` and `telegram_id` in `build_service()`
- When building from terminal(): set `os.environ['HERMES_SESSION_USER_ID'] = 'ndr'`

## Key Rules
- **Always add to BOTH** Google Contacts AND the DRAAS sheet — never just one
- Use the user's OAuth token for all operations (People API, Drive, Docs, Sheets) — the SA DWD does not have People API scope
- Refresh the token before building services: `creds.refresh(Request())`
- Prescription docs should be factual records of what was advised, not interpretations
- **Invoice subfolder**: Every medical folder needs an Invoices/ subfolder. Move all bills/receipts/invoices there immediately after renaming.
- **Share invoices**: With Eshwari (echamundeshwari@draas.com) and Roshni (rnr@draas.com) — reader access, no email notification
- **WhatsApp for accounts**: After filing, generate a wa.me link with invoice details, amounts, and Drive links for the accounts group
- **Contacts for medical staff**: Create Google Contacts for both doctors AND coordinators with hospital details, phone numbers, and role context
- **Per-person filing**: NDR's documents go in NDR Medical, KDR's in KDR Medical — never mix across folders
