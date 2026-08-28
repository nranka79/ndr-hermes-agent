# Entity / SPV Filing Workflow

**Trigger:** User forms a new partnership/SPV (e.g. DRA Kaja Development Partners) and needs to create Drive folder structure, upload documents, and create an accounts narration.

## Pattern

When the user establishes a new entity (partnership, SPV, JV Co), they consistently want:

1. **Folder structure** under `My Drive → BusDev → City → Entity Name`
2. **Documents uploaded** — partnership deed, contribution deeds, payment proofs
3. **Narration document** — a Google Doc with accounts treatment for any financial transactions
4. **Memory saved** — entity name, folder ID, key transaction details

## Step-by-Step

### 1. Create Folder Structure

Check if `BusDev` folder exists first. Then:

```python
# Create city folder under BusDev
city_folder = drive.files().create(body={
    'name': 'Bangalore',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': [busdev_id]
}, fields='id,name').execute()

# Create entity folder under city
entity_folder = drive.files().create(body={
    'name': 'DRA EntityName Development Partners',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': [city_folder['id']]
}, fields='id,name,webViewLink').execute()
```

### 2. Upload Payment Proof / Cheque

Convert cheque screenshots to PDF using pymupdf (fitz):

```python
import fitz
img_path = "/path/to/screenshot.jpg"
pdf_path = "/tmp/EntityName_Cheque_Amount.pdf"
doc = fitz.open()
page = doc.new_page(width=1280, height=900)
page.insert_image(page.rect, filename=img_path)
doc.save(pdf_path)
doc.close()

# Then upload to entity folder
media = MediaFileUpload(pdf_path, mimetype='application/pdf', resumable=True)
uploaded = drive.files().create(body={
    'name': 'YYYYMMDD_EntityName_Cheque_Amount_Purpose.pdf',
    'parents': [entity_folder_id],
    'description': 'Payment of Rs X to [person] as [purpose]'
}, media_body=media, fields='id,name,webViewLink').execute()
```

### 3. Create Accounts Narration

Always create a Google Doc with:

```python
narration_content = """ACCOUNTS NARRATION

Date: [transaction date]
Entity: [Entity Name]
Partners: [Partners]

TRANSACTION DETAILS:
- Amount: Rs [amount]
- Payee: [person]
- Bank: [bank name]
- Purpose: [description]

ACCOUNTING TREATMENT:
Journal Entry:
  Partnership Capital Account ([Partner]) -- Dr  Rs [amount]
      To Bank Account -- Cr                       Rs [amount]

REFERENCE DOCUMENTS (in this folder):
1. Partnership Deed
2. Contribution Deed 1
3. Contribution Deed 2
4. Cheque/Payment Proof
"""

narration_doc = drive.files().create(body={
    'name': 'YYYYMMDD_EntityName_Narration_Amount_Purpose',
    'parents': [entity_folder_id],
    'mimeType': 'application/vnd.google-apps.document'
}, fields='id,name,webViewLink').execute()

# Write content using Docs API
docs = build_service('docs', 'v1')
docs.documents().batchUpdate(
    documentId=narration_doc['id'],
    body={'requests': [{'insertText': {
        'location': {'index': 1},
        'text': narration_content
    }}]}
).execute()
```

### 4. Document Naming Convention

Use `YYYYMMDD_EntityName_Description.pdf`:
- `20260623_DRA_Kaja_Cheque_1Cr_AshokKumar_CapitalWithdrawal.pdf`
- `20260623_DRA_Kaja_Narration_1Cr_CapitalWithdrawal_AshokKumar`

No version suffixes (v1, v2, draft, final) — revision history handles that.

### 5. Save to Memory

```
DRA EntityName Development Partners — SPV between DRA Realty & [Partner]. 
BusDev→City→EntityName folder: [folder_id]. 
₹[amount] [type of payment] via [bank] [date]. 
Deeds pending upload from user.
```

## Pitfalls

- **Folder ownership**: Always verify the BusDev folder is owned by ndr@draas.com before creating subfolders
- **Cheque screenshots**: OCR is often poor — use fitz (pymupdf) to convert image to PDF, don't rely on text extraction
- **Narration document**: Create as a Google Doc (not a PDF) so the user can edit it directly
- **Pending docs**: When the user says "I will share the copies later", note what's pending in the narration doc and save to memory
- **SA key not available in terminal subprocesses**: Use gws_auth.build_service (user OAuth) not gws_sa for Drive from subprocess scripts
