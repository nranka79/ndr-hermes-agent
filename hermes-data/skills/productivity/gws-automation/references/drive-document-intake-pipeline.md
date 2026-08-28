# Drive Document Intake Pipeline

**Trigger:** User uploads documents to a Drive folder and says "scan the folder, OCR/vision analyze each, rename, file, and extract info."

## Workflow

### Phase 1 — Scan the Folder

List ALL files in the target folder and subfolders, filtering by modification time to spot new uploads:

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')

def scan_folder(folder_id):
    results = drive.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        spaces='drive',
        fields='files(id, name, mimeType, modifiedTime, size, webViewLink)',
        orderBy='modifiedTime desc'
    ).execute()
    return results.get('files', [])
```

**Always note the `modifiedTime`** — newly uploaded files will have the most recent timestamps. Cross-reference against what's already been processed.

### Phase 2 — Download Files to Local Temp

```python
for item in new_files:
    file_id = item['id']
    name = item['name']
    # Download binary files directly
    request = drive.files().get_media(fileId=file_id)
    with open(f"/tmp/intake_{name}", 'wb') as f:
        f.write(request.execute())
    
    # Google Docs must be exported as PDF
    # request = drive.files().export_media(fileId=file_id, mimeType="application/pdf")
```

### Phase 3 — Classify & Extract (Text vs Scanned)

**Step 1:** Check for text layer with `pdftotext` (instant):
```bash
pdftotext /tmp/intake_doc.pdf - | head -5
```

**Step 2A — Text PDF found:** Extract full text directly:
```bash
pdftotext -layout /tmp/intake_doc.pdf /tmp/extracted_text.txt
```

**Step 2B — Scanned PDF (zero text):** Render pages to JPEG then use `vision_analyze`:
```bash
mkdir -p /tmp/doc_pages
pdftoppm -jpeg -r 200 /tmp/intake_doc.pdf /tmp/doc_pages/page
# Now vision_analyze each key page
```

### Phase 4 — Identify Document Type

From OCR/vision output, determine:
- **What document is this?** (Partition Deed, Dissolution Deed, ITR, Sale Deed, etc.)
- **Who are the parties?** Look for names, PANs, addresses
- **When was it executed?** Look for dates
- **What properties/assets are involved?** Survey numbers, extents, boundaries
- **Registration details** — Document number, date, registrar office

### Phase 5 — Rename Per Convention

Format: `YYYYMMDD_Entity_DocumentType_Details.pdf`

| Document Type | Pattern | Example |
|---|---|---|
| ITR | `YYYYMMDD_PANName_ITR_AYxxxx-xx_Ack[AckNo].pdf` | `20240221_AshokKumar_ITR_AY2023-24_Ack118891800210224.pdf` |
| Partition Deed | `YYYYMMDD_Entity_PartitionDeed_DocNo.pdf` | `20240116_Satvik_PartitionCumSettlementDeed_SRJ10373.pdf` |
| Dissolution Deed | `YYYYMMDD_Entity_DissolutionDeed_Partners.pdf` | `20240208_Satvik_DissolutionDeed_AshokKumar_CRNagendra.pdf` |

### Phase 6 — Upload & File

Upload the renamed file to the target subfolder. **Also keep the original file** (move it to the same folder so nothing is lost):

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload(f"/tmp/{new_name}", mimetype='application/pdf', resumable=True)
uploaded = drive.files().create(body={
    'name': new_name,
    'parents': [target_subfolder_id]
}, media_body=media, fields='id, name').execute()

# Move original into same folder (don't delete — user may need it)
drive.files().update(fileId=original_id,
    addParents=target_subfolder_id,
    removeParents=root_folder_id
).execute()
```

### Phase 7 — Extract Structured Data

Once documents are identified, extract fields needed for legal forms:

| Document | Data to Extract |
|---|---|
| **Partition Deed** | Parties, document number, date, property schedules (survey #, extent, village), allocation per partner |
| **Dissolution Deed** | Firm name, partners, profit ratio, dissolution date, original partnership date |
| **ITR (ITR-V / Acknowledgement)** | PAN, name, AY, filing date, acknowledgement number, gross total income, total income, tax paid, AO details |
| **Partnership Deed** | Partners, profit ratio, capital contribution, firm name, date |

### Phase 8 — Populate Legal Forms

For each Section 281 (or other) application needed:

1. **Duplicate** the existing template doc
2. **Fill known fields** via `docs.documents().batchUpdate` with `replaceAllText`
3. **Flag missing fields** — change placeholders to `[NOTE: needs X]` so user knows what's pending

```python
docs = build_service('docs', 'v1')
requests = [
    {'replaceAllText': {
        'containsText': {'text': '[PAN: ___________]', 'matchCase': True},
        'replaceText': 'PAN: ANBPK6960D'
    }}
]
docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

### Phase 9 — Update Contacts (When User Provides Contact Info)

When the user gives contact details (phone, email, address) for a person:

1. **Google Contacts** via People API:
   ```python
   people = build_service('people', 'v1')
   results = people.people().searchContacts(query='Ashok Kumar',
       readMask='names,phoneNumbers,emailAddresses,addresses').execute()
   resource = results['results'][0]['person']['resourceName']
   full = people.people().get(resourceName=resource, personFields='names,phoneNumbers,emailAddresses,addresses').execute()
   full.setdefault('emailAddresses', []).append({'value': 'email@example.com', 'type': 'work'})
   updated = people.people().updateContact(resourceName=resource,
       updatePersonFields='emailAddresses,addresses', body=full).execute()
   ```

2. **NDR DRAAS Google contacts sheet** (Sheet ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`):
   ```python
   sheets = build_service('sheets', 'v4')
   sheets.spreadsheets().values().update(
       spreadsheetId=ss_id,
       range='NDR DRAAS Google contacts.csv!S451',  # Column S = Email 1 - Value
       valueInputOption='USER_ENTERED',
       body={'values': [['email@example.com']]}
   ).execute()
   ```

   **Column mapping for DRAAS contacts sheet:**
   | Column | Letter | Name |
   |--------|--------|------|
   | 0 | A | First Name |
   | 10 | K | Organization Name |
   | 18 | S | E-mail 1 - Value |
   | 28 | AC | Phone 1 - Value |
   | 41 | AP | Address - Street |
   | 42 | AQ | Address - City |
   | 45 | AT | Address - Postal Code |
   | 46 | AU | Address - Country |

## Common Pitfalls

- **File upload location varies.** Telegram file uploads land at `/data/hermes/document_cache/` not `/tmp/`. Always check document_cache first when a user says "I've uploaded a file."
- **ITR-V acknowledgements do NOT print AO Circle/Ward.** You must ask the user to look it up on the Income Tax Portal or from their CA. Flag this as [SEE NOTE] in the form.
- **Indian registered documents (sale deeds, partition deeds, mortgage deeds) are often scanned images with zero text layer.** `pdftotext` returns empty. Always try it first (instant), but have `pdftoppm` + `vision_analyze` ready.
- **Multiple AY ITRs uploaded together** — check the assessment year on each and name accordingly. The AY in the filename must match the ITR form header.
- **Renaming isn't enough — move the original too.** The original raw-named file should also be moved to the subfolder so nothing is orphaned in the root.
- **People API searchContacts `readMask` must NOT include `resourceName`** — it's always returned. Including it causes HTTP 400.
- **Contacts sheet phone numbers must be plain digits** (e.g. `9731166998` not `+91 97311 66998`) or the sheet raises `#ERROR!`.
