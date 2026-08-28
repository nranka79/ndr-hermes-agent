# SBI/ICICI Bank Pre-Approval Documentation — 3-Document Set Fill

Recurring DRAAS task: Fill the 3-document SBI pre-approval set (CA Certificate, Request Letter, Builder Profile) for a project using enterprise data and financial documents.

## The 3 Documents

| Doc | Purpose | Key Fields |
|-----|---------|------------|
| **CA Certificate** | Chartered Accountant certifies total investment = 100% of budgeted cost | Builder name, project name, total investment amount, registered address |
| **Request Letter** | Developer requests tie-up arrangement with SBI HLST | Entity details, project description, unit counts, pricing, approvals, RERA number, 5 standard undertakings |
| **Builder Profile** | Company background + financial standing | PAN, registered/correspondence address, constitution, director/partner profiles, prior projects, present proposal with full financials, bank disbursement fields |

## Data Sources (Priority Order)

1. **Enterprise Data Spreadsheet** — `DRA Realty Pvt Ltd - Enterprise Data-PF.xlsx` or similar. Contains project specs (land area, FAR, unit count, cost, sales value), entity details, approvals, profitability
2. **Project Document Tracking** — `Project_Document_Tracking_Ranka_v2.xlsx` or similar. Contains RERA doc status, bank pre-approval checklist per project
3. **RERA Documents** — Filed RERA forms, plan sanction, affidavits (contain project/entity legal details)
4. **PAN Card PDFs** — On Drive: search `name contains 'PAN'` + entity name. Download → `pdftotext` (text PDFs) or `pdftoppm` + `vision_analyze` (scanned images)
5. **RERA Bank Confirmation Letters** — Contain RERA account details (account number, IFSC, branch)

## Workflow

### Phase 1: Read Template Documents
- The blank letter formats are in the shared folder
- Read via web_extract export (`/export?format=txt`) or Docs API
- Identify all `[To be filled]` fields per document

### Phase 2: Collect Data from Sources
Use terminal() with direct vault access to search Drive:

```python
import sys, os, json
sys.path.insert(0, '/opt/hermes')
from tools import gws_vault_client as vault
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

uid = vault.resolve('email', 'psingh@draas.com')
token_json = vault.get_token(uid, 'google-draas', session_uid=uid)
creds = Credentials.from_authorized_user_info(json.loads(token_json))
drive = build('drive', 'v3', credentials=creds)
sheets = build('sheets', 'v4', credentials=creds)
docs = build('docs', 'v1', credentials=creds)
```

For each project:
- Read Enterprise Data sheet for project specs
- Search for PAN card PDFs
- Search for RERA bank confirmation letters
- Search for project financials (cost sheets, profitability)

### Phase 3: Extract PAN Numbers
- **Text PDFs** — Use `pdftotext` command (stdlib available on Linux)
- **Scanned/image PDFs** — Use `pdftoppm` to convert to PNG, then `vision_analyze` for OCR

### Phase 4: Update Google Docs
Use `replaceAllText` via Docs API batchUpdate:

```python
requests = [{
    'replaceAllText': {
        'containsText': {'text': old_text, 'matchCase': True},
        'replaceText': new_text
    }
}]
docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

For bank details (when `[To be filled]` appears multiple times with different meanings):
```python
replace_text(doc_id, "Bank: [To be filled]", "Bank: Kotak Mahindra Bank Ltd")
replace_text(doc_id, "Account No: [To be filled]", "Account No: 8551119387")
replace_text(doc_id, "IFSC: [To be filled]", "IFSC: KKBK0000431")
replace_text(doc_id, "Branch: [To be filled]", "Branch: 100 ft Road, HAL 2nd Stage, ...")
```

This works because each label prefix makes the search string unique.

### Phase 5: Verify All 9 Documents
After updates, scan every doc for remaining `[To be filled]` markers.

## Known Entity Data (DRAAS, Jul 2026)

| Entity | PAN | RERA Bank (Kotak) |
|--------|-----|-------------------|
| DRA Realty Pvt Ltd | AAPCS9730H | 8551119387 / KKBK0000431 |
| Sevaganapalli Land Partners | AFCFS4430H | No bank details found on Drive |
| DRA Thindlu Land Partners | AAXFD2296G | No bank details found on Drive |

## Pitfalls

- **PAN in XLSX enterprise data** may show placeholder values ("AAACD1234E") — always verify against actual PAN card PDF
- **Bank accounts may not exist for all entities** — Sevaganapalli Land Partners and DRA Thindlu Land Partners had no bank documents on Drive (Jul 2026). These need user input.
- **XLSX files cannot be read as Google Sheets** — `openpyxl` must be installed or use `drive.files().get_media()` to download, then parse
- **`pdftotext` fails on scanned PDFs** — The PAN card image PDF returns empty text. Use `pdftoppm` + `vision_analyze` instead
- **`replaceAllText` replaces ALL occurrences** — For repeated `[To be filled]`, use context-specific search strings (e.g. `"Bank: [To be filled]"` not just `"[To be filled]"`)
- **Always check project entity name** — Each project uses a different legal entity (DRA Realty Pvt Ltd for Amber, Sevaganapalli Land Partners for Oasis, DRA Thindlu Land Partners for Udaya). Do not cross-populate data.
