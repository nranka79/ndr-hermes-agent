# Multi-Lender Document Tracking — Per-Process Isolation

## When to use
User asks you to build a document tracker for bank pre-approvals, project funding, or RERA filing — especially when the same project must submit documents to **multiple lenders/authorities** (ICICI, HDFC, Motilal Oswal, RERA, etc.).

## Core Principle: Each Process Stands Alone

**Critical rule: Documents shared with Party A do NOT count as shared with Party B.**

A building plan you sent to ICICI was sent to ICICI. It has NOT been sent to Motilal Oswal unless you verified that separately. Each lender/authority has its own checklist, its own email thread, its own Drive folder.

## Workflow

### 1. Identify each process independently

List every distinct authority/lender and the exact email thread where documents were exchanged:

| Process | Party | Key Email Thread | 
|---------|-------|-----------------|
| RERA Registration | RERA Consultants LLP | shwetha@reraconsultants.in |
| Bank Pre-approval | ICICI Bank | kshitij.saurabh@icici.bank.in |
| Project Funding | Motilal Oswal HF | prakash.n@motilaloswal.com |
| Pre-approval | HDFC | (separate thread) |

### 2. For each process, search Gmail independently

```python
# Search for emails FROM that specific party about this project
results = service.users().messages().list(
    userId='me',
    q=f'from:{party_email} {project_keyword}'
).execute()
```

Do NOT reuse results from another party's search — they may reference different checklists.

### 3. Extract that party's EXACT document request list

Each lender sends their OWN checklist. A document that appears in ICICI's query list may be completely absent from Motilal Oswal's list, or vice versa.

**Key sources:**
- **RERA Consultants**: Send PDF "Document list -Company Apartment - JDA DD-MM-YYYY.pdf" as attachments
- **ICICI**: Send email with numbered query list
- **Motilal Oswal**: Send checklist emails with bullet-point lists, follow-ups with pending items only

### 4. Track three states per document per process

| State | Meaning |
|-------|---------|
| **Sent ✓** | Attached in email TO this party, or shared via Drive link that THIS party can access |
| **Pending 🔴** | On this party's checklist; not yet sent to them specifically |
| **N/A** | Party confirmed this document is not required for their process |

Do NOT carry over "Sent" status from one process to another.

### 5. Build the tracker

- One sheet per process in the spreadsheet
- Each sheet has columns: #, Document, Req by Party?, Shared to Party?, Date, Notes
- Add a Summary Dashboard sheet with per-process counts
- Use color coding: green fill for Sent, red for Pending, yellow for Unclear/Assigned

### 6. Delivery

- Upload spreadsheet to Drive (new folder per project)
- Each row's Document Link column must be a **clickable hyperlink** (`ws.cell(r, c).hyperlink = url`)
- Document links point to the copied file in the new folder, not the original source

## Common Pitfalls

| Trap | Example | Fix |
|------|---------|-----|
| **Cross-process contamination** | Marking COPMOF as "sent" for MOHFL because the template was RECEIVED from MOHFL | Receiving a template ≠ sending the filled form. Track separately. |
| **Drive links without permissions** | Sharing a Drive folder with one party and assuming another party can access it | Each party's Drive access must be verified independently |
| **Blind copy of status** | Building plan was sent to ICICI, so marking it "sent" for MOHFL | MOHFL may have received it separately (Bharat's email) — check that specific thread |
| **Missing hyperlinks** | Spreadsheet has URL text but no clickable link | Use `openpyxl` hyperlink property, not just cell value |

## File naming for copied documents

When creating a banking folder with copies:

```
YYYY-MM-DD, Village, Description, RegNo.ext
```

Example: `2014-02-07, Allalsandra, Joint Development Agreement - NorthStar, —.pdf`

## Tools

- **Gmail**: `tools.gws_auth.build_service("gmail", "v1")` — search emails, fetch attachments
- **Drive**: `tools.gws_auth.build_service("drive", "v3")` — list folders, copy files, upload spreadsheets
- **openpyxl**: create formatted spreadsheets with color-coded status, hyperlinks, merge cells
- **python-docx**: alternative for DOCX output when user prefers Word format
