# Agreement of Sale Proforma — RERA Bank Details Insertion

## When to Use

When the user asks you to update the **Agreement of Sale Proforma** (RERA Annexure template) with the **project-specific RERA bank account details** — filling in Clause 2 (Mode of Payment) and/or Schedule C (Payment Plan) with the collection/designated/operative account details from the "RERA Separate Bank Accounts" document.

## ⚠️ Scope Rule (Critical)

**When the user says "collection account details" or "collection account" — insert ONLY the 100% RERA Collection Account. Do NOT add the 70% Designated or 30% Operative accounts unless explicitly named.**

**When the user says "update Clause 2" — update ONLY Clause 2. Do NOT touch Schedule C or any other section unless explicitly directed.**

**Default assumption: minimum scope.** The user will ask for more if they want it. Adding extra accounts or extra sections "to be helpful" will be reverted. When in doubt, ask: "Clause 2 only, or Schedule C too? All three accounts or just the Collection Account?"

## Workflow

### 1. Extract Bank Details from Source Document

The source is typically a Google Doc named **"RANKA AMBER RERA Separate Bank Accounts"** (or similar `[Project Name] RERA Separate Bank Accounts`) in the project's Drive folder.

```python
from tools.gws_auth import build_service

drive = build_service("drive", "v3")
# Export Google Doc as plain text
doc_id = "FILE_ID"
content = drive.files().export_media(fileId=doc_id, mimeType="text/plain").execute().decode("utf-8")
print(content)
```

Expected output — three accounts:

| Account | Type | Purpose |
|---------|------|---------|
| **i** | 100% RERA Collection Account | Allottee payments (100% collection) |
| **ii** | 70% RERA Designated Account | 70% construction cost allocation |
| **iii** | 30% RERA Operative Account | 30% promoter/operative expenses |

Each entry contains: Account Holder, Account Number, Bank Name, IFSC Code, Branch Name.

### 2. Read the Agreement of Sale Proforma

The proforma is typically a PDF (printed/exported from Google Docs). Download it and convert to images for reading:

```python
# Download PDF
request = drive.files().get_media(fileId=proforma_pdf_id)
with open("/tmp/proforma.pdf", "wb") as f:
    f.write(request.execute())

# Convert to images
import subprocess
subprocess.run([
    "pdftoppm", "-jpeg", "-r", "200",
    "/tmp/proforma.pdf",
    "/tmp/pages/page"
], check=True)
```

Then use `vision_analyze` (parallel calls) to read all pages. Key sections to find:

| Section | Page(s) | What to Look For |
|---------|---------|------------------|
| **Clause 2 — Mode of Payment** | ~Page 11 | Blank `______________` where bank details go |
| **Schedule C — Payment Plan** | ~Page 24 | Milestone table, usually with no bank details |

### 3. Update Clause 2 — Mode of Payment

Replace the blank with the full bank details in this format:

> Subject to the terms of the Agreement and the Promoter abiding by the construction milestones, the Allottee shall make all payments, on written demand by the Promoter, within the stipulated time as mentioned in the Payment Plan [Schedule C] through A/c Payee cheque / demand draft / bankers cheque or online payment (as applicable) in favour of **"[Company Name]"**, payable to the RERA Bank Account of the Project as detailed below:

Then list the three accounts:

```
i. 100% RERA COLLECTION ACCOUNT – "[Project Name]"
   Account Holder  : [Company Name]
   Account No.     : [Number]
   Bank & Branch   : [Bank Name], [Branch Address]
   IFSC Code       : [IFSC]

ii. 70% RERA DESIGNATED ACCOUNT – "[Project Name]"
   Account Holder  : [Company Name]
   Account No.     : [Number]
   Bank & Branch   : [Bank Name], [Branch Address]
   IFSC Code       : [IFSC]

iii. 30% RERA OPERATIVE ACCOUNT – "[Project Name]"
   Account Holder  : [Company Name]
   Account No.     : [Number]
   Bank & Branch   : [Bank Name], [Branch Address]
   IFSC Code       : [IFSC]
```

### 4. Update Schedule C — Payment Plan

Add a note **after the milestone table**:

> All payments under the above Payment Plan shall be made to the following RERA bank accounts maintained with [Bank Name], [Branch Address]:
>
> - **100% RERA Collection A/c** ([Number]) — IFSC: [IFSC]
> - **70% RERA Designated A/c** ([Number]) — IFSC: [IFSC]
> - **30% RERA Operative A/c** ([Number]) — IFSC: [IFSC]

### 5. Create the Updated Document

Since the original proforma is typically a PDF (not editable), create a **new Google Doc** in the same Drive folder with the updated content.

**Method: Docs API batchUpdate** (for structured text insertion):

```python
from tools.gws_auth import build_service

docs = build_service("docs", "v1")

# Create the doc
doc = docs.documents().create(body={"title": "YYYYMMDD Project Name Agreement of Sale Proforma - UPDATED"}).execute()
doc_id = doc.get('documentId')

# Insert content at index 1 (build requests in reverse order)
requests = [
    {"insertText": {"location": {"index": 1}, "text": "Content..."}},
    # ... more inserts
]
requests.reverse()
docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

# Move to the target Drive folder
drive.files().update(fileId=doc_id, addParents=TARGET_FOLDER_ID, fields="id, parents").execute()
```

### 6. Verify

Open the document URL and verify:
- Clause 2 has all three bank accounts listed
- Schedule C has the payment reference note at the bottom
- Account numbers/IFSCs match the source document exactly

## RERA Bank Account Structure (Template)

Every KRERA-registered project must maintain three accounts:

| Account Type | Percentage of Collection | Purpose |
|-------------|------------------------|---------|
| **Collection Account** | 100% | All allottee payments deposited here first |
| **Designated Account** | 70% | Transferred from Collection — used for construction costs |
| **Operative Account** | 30% | Transferred from Collection — promoter's margin/expenses |

## Known Data (Ranka Amber, Jun 2026) — UPDATED Jul 2026

| Field | Collection (100%) | Designated (70%) | Operative (30%) |
|-------|------------------|-----------------|-----------------|
| **Account Holder** | DRA Realty Pvt Ltd | DRA Realty Pvt Ltd | DRA Realty Pvt Ltd |
| **Account No.** | 8551119387 | 8551119394 | 8551119370 |
| **Bank** | Kotak Mahindra Bank Ltd | Kotak Mahindra Bank Ltd | Kotak Mahindra Bank Ltd |
| **Branch** | Indiranagar, Bangalore | Indiranagar, Bangalore | Indiranagar, Bangalore |
| **IFSC** | KKBK0000431 | KKBK0000431 | KKBK0000431 |

> **⚠️ Correction history:** Initial entry had KKBK0008068 (100 Feet Road, HAL 2nd Stage branch) and Branch listed as "100 feet Road, HAL 2nd Stage". User verified the correct IFSC is **KKBK0000431** (Indiranagar branch). The 100% Collection Account (8551119387) uses KKBK0000431, not KKBK0008068. Always verify IFSC against the FORM B affidavit — it is the authoritative source document.

## Scope Precision

⚠️ **Critical: confirm what exactly the user wants before executing.**

This session produced two corrections that should not be repeated:

1. **Which accounts to include**: The user may only want the **100% RERA Collection Account** in Clause 2, not all three accounts. Do not add the 70% Designated or 30% Operative accounts unless the user explicitly asks for them.

2. **Which sections to update**: The user may want only **Clause 2 updated**, not Schedule C. Do not add bank details to Schedule C unless explicitly requested — ask if you are unsure.

**Pattern**: The user prefers minimum-scope changes — fix only what they identified, nothing more. Adding extra content (extra accounts, extra sections, explanatory notes) to "be helpful" will be reverted and wastes time. When the request is ambiguous ("add bank details"), ask: "Clause 2 only, or Schedule C as well? All three accounts or just the Collection Account?"

## Pitfalls

- **Don't edit the PDF** — create a new Google Doc alongside it. The PDF is a snapshot; the Google Doc is the editable working version.
- **Account numbers must be exact** — one transposed digit will cause payment rejections. Triple-check against the source.
- **"In favour of"** in Clause 2 should be the **company name** (e.g. "DRA Realty Pvt Ltd"), not a person's name.
- **The user may want the original PDF replaced** — if so, delete or archive the old PDF after creating the new Google Doc.
- **Project name** in the account descriptors (e.g. `— "RANKA AMBER"`) must match the RERA-registered project name exactly.
- **Schedule C milestone percentages** are illustrative defaults — verify against the actual project's SIS sheet payment plan.
