# Gmail Attachment — Document Checklist Extraction

**Trigger:** User says "extract the checklist from [advocate name]'s email attachment" or asks for a survey-wise summary of documents required from an advocate's email.

**Class-level pattern:** DRAAS real estate document management often involves advocates (Prasanna Swaminathan, Krishna B R) sending .docx/.pdf checklists as email attachments. The user needs these turned into survey-wise structured summaries.

## Workflow

### Phase 1 — Find the Email Thread

1. **Search Gmail** across available accounts:
   ```python
   from tools.gws_auth import build_service, list_google_accounts
   
   for label in list_google_accounts():
       svc = build_service('gmail', 'v1', label)
       results = svc.users().messages().list(userId='me', q='from:ADVOCATE subject:REQUISITION').execute()
       if results.get('resultSizeEstimate', 0) > 0:
           break  # Found the thread in this account
   ```

2. **Get the latest email with attachments:**
   ```python
   msg = svc.users().messages().get(userId='me', id=msg_id, format='full').execute()
   parts = msg['payload'].get('parts', [msg['payload']])
   attachments = []
   for part in parts:
       if part.get('filename') and part['filename'].endswith(('.docx', '.doc', '.pdf')):
           att_id = part['body'].get('attachmentId')
           att = svc.users().messages().attachments().get(userId='me', messageId=msg_id, id=att_id).execute()
           file_data = base64.urlsafe_b64decode(att['data'])
           filepath = f"/opt/data/{part['filename']}"
           with open(filepath, 'wb') as f:
               f.write(file_data)
           attachments.append(filepath)
   ```

### Phase 2 — Extract Content from .docx Files

Use `python-docx` to extract text:
```python
from docx import Document
doc = Document(filepath)
for para in doc.paragraphs:
    print(para.text)

# Also check tables in the doc
for table in doc.tables:
    for row in table.rows:
        print([cell.text for cell in row.cells])
```

**Pitfall:** Some .docx attachments have the actual content in tables, not paragraphs. Always check `doc.tables` if `doc.paragraphs` yields nothing useful.

### Phase 3 — Organize by Survey Number

When a single email contains checklists for MANY survey numbers (e.g., 23 survey files in one attachment or 23 separate .docx files):

1. For **multiple attachments**: download and extract each one
2. For **single .docx with categories**: parse by section headings
3. **Key columns to identify**: Survey Number, Document Description, Responsible Party, Status (Pending/Received)
4. **Identify flags**: Stay orders (RSA), mortgages, missing endorsements — these are critical blockers

### Phase 4 — Present as Structured Summary

**Format:**
```markdown
### Survey XXX (Project Name — Extent)
| # | Document | Responsible | Status |
|---|---|---|---|
| 1 | Required document description | Party | Pending/Received/lib-soft copy|

**⚡ Notable flags:**
- Stay order in effect
- Mortgage needs discharge confirmation
```

### Phase 5 — Offer File Delivery

The attachments are saved to disk (e.g., `/opt/data/prasanna_checklists/`). Ask the user if they want:
- The individual .docx files sent here
- A compiled summary in Drive
- The email forwarded

## Known Patterns (DRAAS Context)

| Advocate | Survey #s | Attachment Format | Key Pattern |
|---|---|---|---|
| Prasanna Swaminathan | 114/1-12, 115/2, 120/1-2, 121, 122/1-2, 123, 125/2-5, 157, 158, 159 (Katenahalli) | Multiple .docx files (one per survey) | Color-coded: black=asked earlier, blue=received, red=NEW pending. Common gaps: Nil Tenancy endorsement, sale deed soft copies |
| Krishna B R (Pattan Shetty) | Sy.40 Gunjur (Doddaballapur) | Single .doc with columnar table | Title docs for 2 portions (Thippaiah + Patel Hanumegowda). Requires: family trees, DC permission, endorsements from 5+ authorities |

## Common Document Categories

| Category | Typical Documents |
|---|---|
| Title Documents | Grant order, Saguvali Chit, Sale Deeds chain, GPA, Family Tree (Tahsildar-attested), Death Certificates |
| Revenue Records | RTCs (all years), MR extracts, Index of Lands, Inheritance Register |
| Survey Records | Phodi/LR Tippany, Hissa Tippani, RR Pakka Book, Village Map, Survey Sketch |
| Endorsements | Nil Tenancy (Tahsildar), PTCL (Asst. Commissioner), BIAAPA/KIADB/KHB no-acquisition, NH/SH no-widening |
| Encumbrance | EC 30+ years, discharge deeds for mortgages |
| Other | CLU conversion, CDP/BIAAPA zone, Property Tax, Aadhaar/PAN of owner |
