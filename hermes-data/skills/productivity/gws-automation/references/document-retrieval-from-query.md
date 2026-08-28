# Document Retrieval from User Query

Retrieve a specific document (file, invoice, drawing, report) from a user's Google Workspace when they ask via a conversational query — including code-switched queries (English + Kannada/Hindi/Tamil, common for Bangalore/Chennai teams).

## Class of task

User says "Get me the X from Y project" or "find the invoice for Z" — and you need to search their Gmail + Drive to locate it and return the link.

## Workflow

```
User query (may contain code-switched terms)
  └─ Parse clue: project name, document type, party/architect/vendor name
  └─ Search Gmail (most recent emails often have the file reference or attachment)
  └─ Search Drive (name contains + broader queries)
  └─ If file found → return link directly
  └─ If multiple matches → return list, let user pick
```

## Step 1 — Parse the query

Extract three signal categories from the user's words:

| Signal | Examples | Notes |
|--------|----------|-------|
| **Project** | Ranka Amber, Ranka Udaya, River Stone, Benson Town | Often the second/third word in the query |
| **Document type** | invoice, bill, drawing, plan, GFC, report, agreement, work order | The main noun describing what kind of file |
| **Party/architect/vendor** | AJ Architect, Vardhan Ventures, Bhuvanesh, Finding Form | Who produced the document |

**Code-switched Kannada-English terms (common with DRAAS team):**
- *kelsa / kaelsa* (ಕೆಲಸ) = work
- *pipe kelsa* = plumbing work, piping work
- *billu* = bill
- *invoice* = invoice (same in both languages)
- *estimate* = quotation / BOQ
- *kattu kaelsa* = construction work
- *plan* / *drawing* = architectural drawing

Treat these as synonyms for the English terms when searching.

## Step 2 — Search Gmail first

Gmail often contains the email thread where the document was shared. Search the user's inbox:

```python
from tools.gws_auth import build_service
gmail = build_service("gmail", "v1")
results = gmail.users().messages().list(
    userId="me",
    q="project-name OR party-name OR file-reference",
    maxResults=20
).execute()
```

For each result, check the subject line and sender to identify the relevant thread.

## Step 3 — Search Drive

File names in Drive often follow naming conventions:

```
YYYYMMDD_ProjectName_Party_DocumentType[_Rev#].pdf
```

Search patterns:
- `name contains 'ProjectName'` — broadest, catches all project files
- `name contains 'invoice'` — narrow to document type
- Combine: `name contains 'ProjectName' and name contains 'invoice'`

```python
drive = build_service("drive", "v3")
results = drive.files().list(
    q="name contains 'ProjectName'",
    fields="files(id, name, mimeType, webViewLink)",
    pageSize=50
).execute()
```

When the project name is a **single common word** like "Amber" or "Udaya", it may return many results. Filter by document type in the same query or present the most relevant matches.

## Step 4 — Link delivery

Return the Drive link directly:
```
📄 FileName.pdf
🔗 https://drive.google.com/file/d/FILE_ID/view?usp=drivesdk
```

If the document was attached to an email but not in Drive, get the attachment link from Gmail or download and upload to Drive first, then share the link.

## File naming conventions at DRAAS

Files are typically named following the pattern agreed with Nishant:
```
YYYYMMDD_ProjectName_VendorOrParty_DocumentType[_details].pdf
```

Examples seen in the wild:
- `20260502_RankaAmber_AJArchitects_RevisedInvoice_AJA-26-27-001.pdf`
- `20260314_RankaAmber_AJArchitects_OPT1and2_Stilt+G+3Typical+4th+Terrace.pdf`
- `Amber-Vardhan Ventures-Work Order-R0-09-June 2026.pdf`

Not all files follow this strictly — some use descriptive names. Search both patterns.

## Pitfalls

1. **Code-switched language:** "pipe kelsa" does NOT mean the file name contains "pipe" — it means the user is describing the work type (plumbing). Search for the project + vendor/invoice, not the kananda term literally.
2. **execute_code may be blocked:** In cron mode or certain profiles, execute_code is denied. Fall back to `terminal` + Python scripts via the Hermes venv.
3. **Multiple Drive accounts:** The user's personal Drive (via gws_auth) may have different files than the shared DRAAS Drive. Ask which one if unclear.
4. **Email attachments vs Drive files:** The document may exist as an email attachment not uploaded to Drive. Check Gmail attachments if Drive search yields nothing.
