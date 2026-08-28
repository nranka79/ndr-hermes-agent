# SPV / New Entity Document Filing Workflow

**Trigger:** User creates a new partnership/SPV entity (e.g., "DRA KAAJ Development Partners") and needs to file all incorporation documents on Drive with proper folder structure, naming, and accounts narration.

## Workflow

### Step 1 — Create Folder Hierarchy

```
BusDev → [City] → [Entity Name]
```

Check if `BusDev` folder exists in My Drive. Then create city subfolder, then entity folder.

```python
busdev_id = "<BusDev folder ID>"
city_folder = drive.files().create(body={
    'name': 'Bangalore',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': [busdev_id]
}, fields='id,name,webViewLink').execute()

entity_folder = drive.files().create(body={
    'name': 'DRA KAAJ Development Partners',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': [city_folder['id']]
}, fields='id,name,webViewLink').execute()
```

### Step 2 — File Documents with Consistent Naming

Use the naming convention: `YYYYMMDD_EntityName_DocType_PartnerName[_N].pdf`

| Document | Naming Pattern | Example |
|----------|---------------|---------|
| Deed of Partnership | `YYYYMMDD_Entity_DeedOfPartnership.pdf` | `20260623_DRA_KAAJ_DeedOfPartnership.pdf` |
| Contribution Deed | `YYYYMMDD_Entity_ContributionDeed_PartnerName[_N].pdf` | `20260623_DRA_KAAJ_ContributionDeed_AshokKumar_1.pdf` |
| Payment Proof / Cheque | `YYYYMMDD_Entity_Cheque_Amount_Purpose.pdf` | `20260623_DRA_KAAJ_Cheque_1Cr_AshokKumar_CapitalWithdrawal.pdf` |
| Payment document | `YYYYMMDD_Entity_PaymentTo_PartnerName_Purpose.pdf` | `20260623_DRA_KAAJ_PaymentToAshokKumar_NewPartnership.pdf` |

Upload each with a meaningful `description` field:

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
file_meta = {
    'name': 'YYYYMMDD_Entity_DocType.pdf',
    'parents': [entity_folder_id],
    'description': 'Detailed description of what this document is'
}
uploaded = drive.files().create(body=file_meta, media_body=media, fields='id,name,webViewLink').execute()
```

### Step 3 — Create Accounts Narration Google Doc

Create a Google Doc in the same folder with the accounts narration:

```python
narration_doc = drive.files().create(body={
    'name': 'YYYYMMDD_Entity_Narration_Amount_Purpose_Partner',
    'parents': [entity_folder_id],
    'mimeType': 'application/vnd.google-apps.document',
    'description': 'Accounts narration for <transaction>'
}, fields='id,name,webViewLink').execute()

docs = build_service('docs', 'v1')
docs.documents().batchUpdate(
    documentId=narration_doc['id'],
    body={
        'requests': [{
            'insertText': {
                'location': {'index': 1},
                'text': narration_content
            }
        }]
    }
).execute()
```

**Narration content structure:**

```
ACCOUNTS NARRATION

Date: DD Month YYYY
Entity: [Entity Name] (new SPV)
Partners: [Partner A] & [Partner B]

-------------------

TRANSACTION DETAILS:
- Amount: Rs X (Amount in Words)
- Payee: [Person Name]
- Bank: [Bank Name]
- Purpose: [Description of what this payment is for]

ACCOUNTING TREATMENT:
[Brief description of the accounting logic]

Journal Entry:
  [Account] -- Dr  Rs X
      To [Account] -- Cr  Rs X

REFERENCE DOCUMENTS (filed in this folder):
1. <Document 1> — <status>
2. <Document 2> — <status>
...
```

### Step 4 — Update Narration as More Documents Arrive

When the user sends additional documents later, append them to the narration doc:

```python
docs.documents().batchUpdate(
    documentId=narration_id,
    body={
        'requests': [{
            'insertText': {
                'location': {'index': 1},
                'text': "\n\n--- DOCUMENTS FILED (DD MMM YYYY) ---\n✅ <New document>\n"
            }
        }]
    }
).execute()
```

### Step 5 — Provide Copy-Paste Summary for Accounts

When the user asks for the narration to copy into the accounts book, format as a single code block with all document links:

```
ACCOUNTS NARRATION — [ENTITY NAME]

Date: DD Month YYY6
Entity: [Entity Name]
Partners: [Partner A] & [Partner B]

TRANSACTION:
[Description of transaction]

ACCOUNTING TREATMENT:
  [Account] -- Dr   Rs X
      To [Account] -- Cr   Rs X

REFERENCE DOCUMENTS:
1. Deed of Partnership
   [Drive link]

2. Contribution Deed — [Partner] (1 of 2)
   [Drive link]

3. Contribution Deed — [Partner] (2 of 2)
   [Drive link]

4. [Other document]
   [Drive link]
```

## Checklist

- [ ] Check for existing BusDev folder
- [ ] Create city subfolder if not exists
- [ ] Create entity folder
- [ ] Upload Deed of Partnership (proper naming + description)
- [ ] Upload all Contribution Deeds (with copy numbers)
- [ ] Upload Payment Proof / Cheque
- [ ] Create Accounts Narration Google Doc
- [ ] Update narration as additional docs arrive
- [ ] Provide copy-paste summary for accounts
- [ ] Save entity name + folder ID to memory

### Step 6A — Process Existing/Uploaded Documents from Drive Folder

When the user uploads new documents to an existing SPV folder, process them systematically:

1. **Scan for new files** — List files in the folder ordered by `modifiedTime desc`. Cross-reference with already-processed files.
2. **Download each file** — Use `drive.files().get_media(fileId=...).execute()` and save to `/tmp/`.
3. **Identify document type** — Check text layer first (`pdftotext` or `pymupdf`), then render with `pdftoppm -jpeg -r 200` for scanned docs and use `vision_analyze`.
4. **Extract key data** — PAN, names, addresses, dates, registration numbers, income/tax figures from ITRs.
5. **Rename per convention** — `YYYYMMDD_Entity_DocType_KeyParties_Details.pdf`
6. **Upload with new name** to the appropriate subfolder (or create one like "Documents for [Entity]").
7. **Move/remove originals** from root into the subfolder.

**Document type identification guide:**

| Content Signals | Document Type |
|---|---|
| "Dissolution", "winding up", "cease to exist" | **Dissolution Deed** — terminates partnership entity |
| "Partition", "division", "allotted", "Schedule A/B" | **Partition Deed** — divides assets among ex-partners |
| "Section 281", "prior approval", "Assessing Officer" | **Section 281 Application** — IT approval for asset contribution |
| "ITR", "Acknowledgement", "Form ITR-3" | **ITR-V Acknowledgement** — income tax return filing proof |
| "Certificate of Registration", "Registrar of Firms", "Section 58" | **Firm Registration Certificate** — Registrar of Firms |
| "PAN", "Permanent Account Number" | **PAN Card** — individual or firm PAN |
| "Aadhaar", "UIDAI", "VID" | **Aadhaar Card** — identity document |

**Key distinction — Dissolution vs Partition:**
- **Dissolution Deed**: Terminates the partnership entity (firm ceases to exist)
- **Partition Deed**: Divides specific assets/properties among ex-partners (who gets which land)

### Step 6B — Section 281 Application Pipeline

When Section 281 (Income Tax Act) applications are needed for an SPV:

1. **Identify how many apps needed** — Each applicant + property source combo = separate app
2. **Extract partner details** from dissolution/partition deeds (PAN, address, father's name, phone)
3. **Fill ITR data** — AY, filing date, total income from ITR-V PDFs via `pdftotext`
4. **Note: AO Circle/Ward is NOT on ITR-V acknowledgements** — must be obtained from IT portal
5. **Update the application doc** via Docs API `batchUpdate` with `replaceAllText`

### Step 6C — Dual-Store Contact Updates

When user provides new contact details for a partner:

1. **Update Google Contacts** via People API (`people.people().updateContact`)
2. **Update NDR DRAAS Google contacts sheet** — Find row by name+org, update email (col S=18), phone (col AC=28), address (col AP=41, AQ=42, AT=45, AU=46)

### Step 6D — Replace a Document When a Complete Version Arrives

When the user sends an updated/corrected version of a previously filed document (e.g., deed without stamp paper → complete deed with stamp paper):

1. **Delete the old file** from Drive
2. **Upload the new version** with a slightly updated name to distinguish it (e.g., add `_Complete` suffix)
3. **Re-grant permissions** to the same users who had access to the old one (use `sendNotificationEmail=False` to avoid spam)
4. **Update the narration doc** with a note about the replacement and the new link
5. **Provide the user with updated accounts summary** containing all new links

```python
# Delete old
drive.files().delete(fileId=old_file_id).execute()

# Upload new
media = MediaFileUpload(new_path, mimetype='application/pdf', resumable=True)
uploaded = drive.files().create(body={
    'name': 'YYYYMMDD_Entity_DocType_Complete.pdf',
    'parents': [entity_folder_id],
    'description': 'COMPLETE version with stamp paper'
}, media_body=media, fields='id,name,webViewLink').execute()

# Re-grant permissions
for email in ['rnr@draas.com', 'echamundeshwari@draas.com']:
    drive.permissions().create(fileId=uploaded['id'], body={
        'type': 'user', 'role': 'reader', 'emailAddress': email
    }, sendNotificationEmail=False).execute()

# Update narration
docs.documents().batchUpdate(documentId=narration_id, body={
    'requests': [{'insertText': {
        'location': {'index': 1},
        'text': f"\n\n=== UPDATE DD MMM YYYY ===\n[Document] replaced with complete version (with stamp paper).\nNew link: {uploaded['webViewLink']}\n"
    }}]
}).execute()
```

### Step 7 — Verify and Maintain Viewer Access

After all documents are filed, verify the correct internal stakeholders have folder-level viewer access. Grant at the **folder** level (not file level) so all current and future documents inherit permissions automatically:

```python
# Verify existing permissions
perms = drive.permissions().list(fileId=entity_folder_id,
    fields='permissions(id,type,role,emailAddress)').execute()

# Grant folder-level if not already set
for email in ['rnr@draas.com', 'echamundeshwari@draas.com']:
    drive.permissions().create(fileId=entity_folder_id, body={
        'type': 'user', 'role': 'reader', 'emailAddress': email
    }, sendNotificationEmail=False).execute()
```

## Pitfalls

- **📁 Scan the FULL document cache before filing** — The user may upload multiple documents in rapid succession (partnership deed, contribution deeds, payment proof, payment document). Before filing ANYTHING, run `ls -la /data/hermes/document_cache/ | grep -i "entity\\|partner\\|kaaj\\|kaa\\|contribution"` to catch ALL pending files. In one session (Jun 2026), only 2 of 4 files were filed because the cache had 4 matching files but only the first 2 were checked. Always do a comprehensive grep before telling the user "done."
- **Entity name may differ from what user said** — If documents say "KAAJ" but user said "Kaja", use the spelling from the documents (the signed deed is authoritative).
- **SA key not available in terminal subprocesses** — All Drive/Calendar operations need `tools.gws_auth.build_service` (user OAuth), not SA. Use the hermes venv path: `/opt/hermes/.venv/bin/python3`.
- **Emoji in heredoc python scripts** — Unicode characters (especially emoji) cause `SyntaxError` in python `<< 'EOF'` heredocs. Write the script to a file first instead.
- **WhatsApp links break with & (ampersand) in text** — URL encoding of `&` to `%26` causes WhatsApp links to fail. Keep messages short without & or other special characters.
- **Calendar event times: use IST directly** — Use `'dateTime': '2026-06-24T16:00:00'` with `'timeZone': 'Asia/Kolkata'`. Do NOT convert to UTC manually — the API handles it.
- **PAN card OCR is unreliable** — Low-res PAN card PDFs (93-111 KB) often fail all extraction methods (pymupdf, pdftotext, tesseract, vision). Request clear photos or direct PAN numbers.
- **ITR-V PDFs lack AO Circle/Ward** — ITR acknowledgement PDFs do NOT print the Assessing Officer's jurisdiction. Must be looked up on the IT portal separately.
