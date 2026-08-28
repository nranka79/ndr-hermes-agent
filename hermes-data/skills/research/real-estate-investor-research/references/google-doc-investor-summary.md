# Google Doc Investor Summary — Creation from Transaction Research

## When to Use
After collating investor transaction data from Gmail + Drive (CCDs, shareholding, amendments), compile a structured investor summary document and upload it to the project's Google Drive folder.

## Pattern (Bargmane/Textworth Case Study — June 2026)

### Step 1 — Compile Local Markdown
Save to `/tmp/{project}_analysis/{project}_Investor_Summary.md` before uploading:

```markdown
# {Project Name} — INVESTOR TRANSACTION SUMMARY & CCD TERMS

## 1. EXECUTIVE SUMMARY
- Total Project Value: ₹XXX Crores
- Total CCDs: X,XX,XXX at ₹10 each = ₹XX.XX Crores
- Investment Structure: XX% [Group A] / XX% [Group B] split
- Key Agreement Date: [date]
- Project: [description]

## 2. PROJECT OVERVIEW
### Entity Details
- Company Name, CIN, Incorporation Date, Business Description
### Board of Directors (names)
### RLDA Lease Agreement (summary)

## 3. INVESTOR STRUCTURE & CCD TERMS
### CCD Issuance Summary
- Total CCDs: X,XX,XXX | Face Value: ₹10 | Total: ₹XX Cr
- Authorization: Board Resolution + Shareholder Special Resolution ([date])

### CCD Classes
#### Class A CCDs
- Amount: ₹XX.XX Cr
- Contributed By: [group]
- Conversion: [terms]

#### Class B CCDs
- Amount: ₹XX.XX Cr
- Contributed By: [all group members]
- Conversion: [at par / specific terms]

### Per-Investor CCD Breakdown
| Investor | Interest % | Fully Diluted % | Total Funds (₹ Cr) | Equity (₹ Cr) | CCD (₹ Cr) |
|---|---|---|---|---|---|
[rows]

## 4. SHAREHOLDING STRUCTURE
### High-Level Split
| Party | % |
|---|---|
| [Group A] | XX% |
| [Group B] | XX% |

### Capital Structure (₹ Cr)
| Component | Group A | Group B |
|---|---|---|
| Equity Shares | X.XX | X.XX |
| CCDs/OCDs Class A | X.XX | X.XX |
| CCDs/OCDs Class B | X.XX | X.XX |
| **Total** | **₹XXX** | **₹XXX** |
| **%** | **XX%** | **XX%** |

**Total Project Capital:** ₹XXX Crores

## 5. KEY CONTRACTUAL TERMS
### Conversion Terms
- Class A: [conversion to equity type]
- Class B: [conversion at par / other]

### Investment Agreement ([date])
- Framework for CCD/OCD/equity subscription
- Terms for Class A + Class B share purchase

### [First/Second] Amendment ([date])
- Parties, Tranche considerations, Long Stop Date, Break-away fee

## 6. TRANSACTION TIMELINE
| Date | Event |
|---|---|
[rows]

## 7. KEY PARTIES & ADVISORS
[Groups + individuals]

## 8. DOCUMENT REFERENCES
| Document | Source |
|---|---|
[rows]

---
*Generated: [date]*
```

### Step 2 — Create Google Doc via Drive API

```python
from googleapiclient.http import MediaIoBaseUpload
import io, json

# 1. Create the document
doc = drive.files().create(
    body={
        'name': '{Project} - CCD & Investor Terms Summary',
        'mimeType': 'application/vnd.google-apps.document',
        'parents': [folder_id]  # ROMA folder ID: 1HriUs2El8ekOdeVS7-9BAs0KET8tRodN
    },
    media_body=None,
    fields='id,name,webViewLink'
).execute()
doc_id = doc['id']

# 2. Insert content (plain text via paragraphs)
from googleapiclient.http import MediaIoBaseUpload

# Read the markdown file
with open('/tmp/{project}_analysis/{project}_Investor_Summary.md') as f:
    content = f.read()

# Split into lines and insert as paragraphs
lines = content.split('\n')
for line in lines:
    self._service.documents().batchUpdate(
        documentId=doc_id,
        body={
            'requests': [{
                'insertText': {
                    'text': line + '\n',
                    'location': {'index': 1}
                }
            }]
        }
    ).execute()
```

### Step 3 — Verify the Document
```python
# Verify it exists in the folder
results = drive.files().list(
    q=f"'{folder_id}' in parents and name contains '{project}'",
    fields='files(id, name, webViewLink)'
).execute()
# Confirm: name, ID, and webViewLink match expected output
```

### Step 4 — Return Link to User
```python
print(f"Document created: {doc['webViewLink']}")
```

## Known Issues

### Google Doc creation — text insertion is slow
For documents >100 lines, use batched requests (up to 100 operations per batch):
```python
batch = self._service.new_batch_http_request()
for i, line in enumerate(lines):
    batch.add(self._service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': [{'insertText': {'text': line + '\n', 'location': {'index': 1}}}]}
    ))
batch.execute()
```

### webViewLink may not be immediately accessible
If `webViewLink` is empty, the document may still be accessible via:
`https://docs.google.com/document/d/{doc_id}/edit`

### Folder ID lookup
If folder ID unknown, search by name:
```python
folders = drive.files().list(
    q="mimeType='application/vnd.google-apps.folder' and name contains 'ROMA'",
    fields='files(id, name)'
).execute()
```

## Delivery Note
For DRAAS context (Bharat/Nishant), always present the Google Doc link as the final output. The document is accessible in the ROMA Drive folder alongside other transaction documents.