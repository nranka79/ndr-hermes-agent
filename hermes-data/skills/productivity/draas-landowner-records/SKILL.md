---
name: draas-landowner-records
description: "Manage landowner documentation for DRA Group projects: banking info/KYC collection, cancelled cheque archival, folder structure conventions, email/project-record cross-referencing for context on landowner negotiations and exit proposals."
tags: [real-estate, draas, landowner, documentation, banking, kyc, ranka-northstar, project-records]
metadata:
  hermes:
    tags: [real-estate, draas, landowner, documentation, banking, kyc, ranka-northstar, project-records]
    category: productivity
    related_skills: [google-workspace, draas-due-diligence-pack, kelsa-land-proposal]
---

# DRAAS Landowner Records Management

When a landowner provides banking information, a cancelled cheque, or KYC documents — or when you need context on a landowner's agreements/exit proposals — use this workflow to capture, store, and cross-reference everything.

## When to load

- User shares a cancelled cheque / bank statement / KYC document from a landowner
- User says "save this landowner's banking info", "file this in the landowner folder", "attach this to the landowner records"
- User asks for the status/context of a landowner's exit/buyout negotiations
- User needs to cross-reference a landowner's details against the project's LO (Land Owner) sheets and JDA records
- User asks to "rearrange document list by survey number", "group documents survey-wise", or "reorganise legal document register"

## Standard workflow

### Phase 1 — Extract banking info from cancelled cheque

When the user shares a cancelled cheque image:

1. The image text is usually auto-extracted by the platform OCR. If not, call `vision_analyze(image_url)` with a question like "extract all the banking details from this cheque".

2. Capture these fields from the cheque:
   - Account holder name (as printed on cheque)
   - Bank name + Branch
   - Branch address (printed on cheque)
   - Account number
   - IFSC code
   - MICR code
   - Account type (Savings/Current/etc. — often printed at bottom)

3. Also capture the landowner's email from Gmail search results and any other ID information (age, PAN, Aadhar) from project records.

### Phase 2 — Create folder structure on Google Drive

Always create under the **Entity → Project** hierarchy. The entity is the legal holder of the development rights (e.g. DRA Ranka Holdings, DRA Projects), and the project is the development name (e.g. Ranka Northstar, Ranka Oasis):

```
<Entity>/
  <Project>/
    Land Owners/
      <Full Name>/
        Banking and Financial Information/
          <Cancelled Cheque Image>
          <Banking Details Doc>
        [Other relevant folders]
```

If you don't have write permission on the entity's Drive folder (e.g. the folder is owned by ndr@drahomes.in while your token is ndr@draas.com), create at root level first and flag it to the user for restructuring.

Use the Google Docs API to create:
1. **Banking Information doc** — structured text with all fields
2. **Context & Background Notes doc** — cross-referenced history

### Phase 3 — Cross-reference email history

Search Gmail (via `tools.gws_auth.build_service('gmail', 'v1', service_name='google-draas')`) for emails from/to the landowner:

```python
# Search patterns to try in order:
queries = [
    f'from:{email} OR to:{email}',
    f'{landowner_first_name} {landowner_last_name} OR "{full_name}"',
    f'{landowner_first_name} {project_name}'
]
```

Extract relevant context:
- JDA amendments and addendums discussed
- Exit / buyout proposals mentioned
- Commercial terms (rates per sqft, security deposits, payment structures)
- Names of other landowners in the same project (for cross-reference)
- Timeline of correspondence

### Phase 3b — Cross-reference WhatsApp chat (when provided)

When the user shares a WhatsApp chat transcript with the landowner:
1. Read the full transcript — it often contains the **final agreed commercial terms** that were never put in email
2. Extract: agreed total consideration, payment milestones, token amounts paid, rate per sqft, SBUA/share area, and all date-stamped decisions
3. Note periods where the user introduced the landowner to an external buyer (e.g. Bhavesh Bafna in Jan 2026) — these explain who was originally involved
4. Capture any corrections the landowner requested (name spelling, area figures, payment terms) — these reveal the finalized terms
5. Identify when the structure changed (e.g. from SBUA-based exit to undivided-land-right purchase)
6. Check for cancelled cheque media shared in the chat — the user may have already requested and received it
7. Upload the chat transcript to the landowner's Drive folder (`Correspondence/` subfolder) as a reference document

### Phase 4 — Cross-reference project records

Search Google Drive for:
1. **LO Internal sheet** — landowner site details (area, share percentage, site number)
2. **LO Share Details sheet** — FAR calculations, total landowner share, allocation
3. **JDA documents** — in `North star Documents/` or `Legal/` folder
4. **Area Statement sheets** — unit-wise allocation (Developer vs Land Owner vs Dev)

⚠️ **Sheet names often have trailing spaces** (e.g. `'LO Share Details '` not `'LO Share Details'`). Always retrieve exact names first:
```python
meta = sheets.spreadsheets().get(spreadsheetId=ID).execute()
titles = [s['properties']['title'] for s in meta['sheets']]  # exact names with spaces
```

Key fields to extract from LO Internal sheet:
- Site Number assigned to the landowner
- Site area (excluding/including private access road)
- Share percentage (% As Per LO and % As Per Us)
- Remarks (e.g. "Matching" / "Not Matching")

### Phase 5 — Create structured summary

Create a context document with:
- **Project context**: JDA parties, project name, location
- **Original exit structure** (if applicable): proposed terms, rate, payment structure
- **Current structure** (if applicable): what's changed, the new approach
- **Gaps**: what you couldn't find (missing documents, unconfirmed entity names, discussions outside email)
- **Key documents found**: links to relevant JDA, spreadsheet, legal opinion files

## Folder structure conventions

Drive folders must follow the **Entity → Project → Category → Individual** hierarchy. The entity is the legal owner of the JDA/project rights (e.g. DRA Ranka Holdings), the project is the development name (e.g. Ranka Northstar).

```
<Entity (e.g. DRA Ranka Holdings)>/
  <Project (e.g. Ranka Northstar)>/
    Land Owners/
      <Full Name>/
        Banking and Financial Information/        # Cancelled cheques, bank details docs
        KYC/                                      # Aadhar, PAN, passport, photos
        Agreements/                               # Signed JDAs, addendums, GPAs
        Correspondence/                           # Key emails, WhatsApp chat transcripts
        Exit Proposal/                            # Buyout offers, commercial analysis
```

⚠️ Do NOT create at root level. Always nest under Entity → Project. If you don't have write permissions on the entity's Drive folder, create at root level as a temporary measure BUT flag it to the user and be prepared to move files once the correct parent location is confirmed.

### How to find the right parent folder

1. Search Drive for the entity name folder (e.g. `name contains 'DRA Ranka Holdings' and mimeType='application/vnd.google-apps.folder'`)
2. Check write permissions by creating a test folder inside — if it fails with `insufficientParentPermissions`, you need a different parent or a different Google account
3. Common entity folder names: "DRA Ranka Holdings docs", "DRA Projects", "DRA Realty", "Ranka Holdings"

### How to restructure when the user corrects the placement

If the user says the folder is in the wrong place:
1. Create the correct hierarchy: Entity → Project → Land Owners → Person
2. Use `drive.files().update()` with `addParents` + `removeParents` to move each file to the new location
3. Delete the old orphaned folders
4. Report the final link to the user

The Banking doc content format:

```
<FULL NAME> - BANKING INFORMATION

Project: <Project Name>
Role: <Land Owner / Partner / etc.>

=== BANK ACCOUNT DETAILS ===

Bank: <Bank Name>
Branch: <Branch Name>
Address: <Branch Address>
Account Type: <Savings/Current>
Account Number: <A/c No>
IFSC Code: <IFSC>
MICR Code: <MICR>

=== SOURCE ===
<How obtained, date shared>
Cheque image uploaded to same folder.

=== CONTACT ===
Email: <email>
Phone: <phone if known>

=== PROPERTY DETAILS ===
Site No.: <site number>
Site Area: <area in sqft>
Share: <percentage>
```

## Known GOIs (Go-to Information sources)

- **Project LO Sheets**: Usually found as Google Sheets named with the project name + "Area statement" or "LO Internal". Search Drive for `name contains '<project>' and mimeType contains 'spreadsheet'`.
- **North star Documents** folder: Contains signed JDAs, GPAs, addendums, legal opinions at `1r5gdS1ydu73oK1RRlBCETjkwnazenFat` (for Ranka Northstar).
- **Email search across accounts**: Use `gws_resolve_account` first to find the right vault service name. Most DRA work lives under `google-draas` (ndr@draas.com).
- **WhatsApp chat history**: When provided, this is often the most up-to-date record of commercial negotiations. Emails may have stopped months before the final deal was struck.

## Phase 6 — Reorganise a legal document register by survey number

When the user asks you to restructure a flat document list from a legal docs spreadsheet into a **survey-number-wise grouped format** — documents grouped under each survey number, ordered oldest to newest within each group — follow this workflow.

Trigger phrases: "rearrange by survey number", "survey-no-wise table", "group documents by survey", "reorganise document list".

### When to do this

The user has a legal document register (typically a spreadsheet with one row per deed/agreement, columns: Survey Number, Extent, Document Name, Reg No, Date, Parties) and wants to see it grouped by land parcel. Common scenarios:

- A flat "Sale Deeds — Registered" + "Agreements/GPA" list needs regrouping by survey number
- User wants all documents impacting a specific survey number listed together chronologically
- User needs to verify which survey numbers have full documentation (sale deed + ATS + GPA) vs gaps

### Workflow

1. **Read the full spreadsheet** — Fetch ALL rows, not just the first N. Use `values().get()` with a wide range (e.g. `A1:H1007`). The sheet has section headers mixed with data rows (e.g. "SALE DEEDS — REGISTERED", "AGREEMENTS / GPA", totals rows) — preserve the distinction.

2. **Parse the section structure** — Identify the document blocks:
   - Sale Deeds (registered, numbered docs with reg numbers)
   - Agreements / GPA (ATS + GPA pairs, P-series parcels)
   - Totals / summary rows (do not include in per-survey tables, but retain for final summary)

3. **Map each document to its survey number(s)** — The source sheet's Survey Number column may have:
   - Single survey: `181` → maps to `181`
   - Compound: `180 & 184/5` → maps to `180 & 184/5` as one group
   - Multi-survey deed: `175/4,6,176/2` → treat as one group covering all sub-surveys
   - ATS+GPA pairs: `190/3` has 2 docs (ATS + GPA) — keep them together under the same survey

4. **Sort survey numbers ascending** — Indian survey numbering convention: whole numbers (41, 174, 175, 180, 181, 190, 209, 210, 216, 219, 221, 223) then sub-divisions sorted numerically by the numerator of the fraction. P-series (45/P3, 45/P5, 45/P7) comes after regular 45-series.

5. **Sort documents within each survey by date, oldest first** — Use the Date column from the sheet. Format consistently as DD-MM-YYYY.

6. **For each survey, output**:
   - Survey number + total extent (Acres-Guntas) as the group header
   - Numbered list of documents, each showing: Document Type, Date, Reg No, Parties
   - If ATS and GPA share the same date, list them as separate items in date order

7. **Separate legal from non-legal** -- Legal documents (sale deeds, agreements, GPAs) go into the survey-number-wise grouping. Non-legal reference tables (Extents_By_Survey, RTC_CrossCheck, Extent_Totals, etc.) have their own structure — list them as separate sections with the tab/folder name as the header.

8. **Append a totals summary** — Re-state the aggregate numbers from the spreadsheet's total rows so the full picture is available in one place.

### Telegram formatting rules

**NO tables** — Telegram has no table syntax. Use these instead:
- `**Survey Number** — Extent` as a bold section header on its own line
- Numbered items `1. **Document Type** — Date — *Reg No*` for each doc
- Doc/Reg number in italics `*italic*`
- Parties line as an indented bullet below the doc line
- `—` (em dash) separator between sections
- Summary totals as a simple bullet list at the end

Example format:
```
**41/11** — 0-20 Guntas

1. **Absolute Sale Deed** — 03-02-2023 — *13853/22-23*
   Krishnamurthy et al. → Satvik Developers
```

### Pitfalls

- **Mixed date formats in source**: The sheet may have `03.02.2023` (dots) and `22-08-2022` (dashes) in the same column. Normalise to DD-MM-YYYY when presenting. For actual date sorting, parse both formats.
- **Section header rows**: Rows like "SALE DEEDS — REGISTERED" have no survey number and should be skipped as data but their documents captured into the per-survey groups.
- **Multi-survey deeds**: A single deed covering `175/4,6,176/2` appears only once. Group it under the primary survey or keep it as a multi-survey group — prefer keeping it as one group under the first survey listed, with a note showing the full range.
- **P-series parcels**: `45/P3`, `45/P5`, `45/P7` have no registered document numbers or dates — mark as "(unreg)" or "(pending)" and note they're P-series parcels under agreement per the map.
- **Old deeds**: Very old documents (e.g. Title Deed 15-02-1962 for 45/P3) may have no Reg No. Use "—" as placeholder.
- **ATS+GPA pairs on same date**: The Agreement to Sell and GPA for the same survey can be registered on the same day. List them as separate items (ATS first, then GPA) under the same survey group.

### Reference example

See `references/byadarahalli-document-register.md` for a complete worked example: the Byadarahalli legal docs spreadsheet (Satvik Developers(PS)) with 15 sale deeds + 12 agreements/GPAs across 23 survey groups, plus 3 non-legal tabs.

## Phase 7 — Draft the commercial term sheet / contract email

When the research (Phases 1–5) is complete and the user asks for an email that records the agreed terms — functioning as a contract until definitive agreements are executed — follow this workflow.

### When to do this

The user says things like: "I want an email which is almost like a contract", "draft a term sheet", "record the agreed terms", "this is what we agreed, put it in an email to him."

### What the email must cover

A term-sheet email should contain these sections (adapt as needed):

| Section | Content |
|---------|---------|
| **1. Parties** | Purchaser (DRA Ranka Holdings / entity), Vendor (landowner name) |
| **2. Property Details** | Project name, site number, land area, share %, FAR, SBUA share in sqft |
| **3. Total Consideration** | Lump sum in INR (words + figures) |
| **4. Payment Terms** | Token already paid, ad-hoc advance being sent now, total advance, balance due on registration |
| **5. RTGS Details** | Bank name, branch, account number, IFSC (from the cancelled cheque) |
| **6. Vendor's Acknowledgment** | Confirmation of receipt + agreement to sell |
| **7. Structure & Documentation** | Tax-efficient — definitive agreements (Sale Deed, Release Deed) to follow post-diligence |
| **8. Representations** | Clear title indemnity, "As Is Where Is" basis |
| **9. Governing Law** | Courts of Bengaluru |
| **10. Definitive Agreements** | This email records the commercial understanding; formal docs to follow |

### Drafting rules

1. **Always use Gmail draft_create** — never send directly. The user must review and send.
2. **Set To**: the landowner's email (from email records or user-provided)
3. **Subject**: `Record of Agreed Commercial Terms & Acknowledgment of Advance — [Landowner] / [Entity] ([Project])`
4. **Format**: Plain text is fine for this genre (legal-ish contract language). Do NOT use HTML — the recipient may print/save as-is.
5. **Include payment acknowledgment block**: a clear section saying "Kindly reply confirming receipt of INR X" with a signature block.
6. **Reference the cancelled cheque**: mention that the RTGS is being made to the account per the cancelled cheque provided.
7. **Upload supporting documents**: After creating the draft, upload the WhatsApp chat transcript and any commercial note PDFs to the landowner's Drive folder for a complete record.

### After drafting

Report to the user:
- Draft created in Gmail (Drafts folder)
- Subject line
- To address
- Key numbers (total consideration, advance amount, balance)
- Any supporting files uploaded to Drive

### GWS environment for Drive/Gmail operations

Since system python has PEP 668 and no system `google-api-python-client`:

```bash
uv venv /tmp/gwsvenv
uv pip install --python /tmp/gwsvenv/bin/python google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

Then run scripts with:
```bash
PYTHONPATH=/opt/hermes:/tmp/gwsvenv/lib/python3.13/site-packages /tmp/gwsvenv/bin/python /tmp/script.py
```

For Gmail drafts, use `build_service('gmail', 'v1', service_name='google-draas')` from `tools.gws_auth` and the `users().drafts().create()` API with a MIMEText-encoded message.

## Pitfalls

- **Voice transcription mangles "Land Owner" to "Landono"**. When the user says "Landono," they mean "Land Owner." Do not search Drive for "Landono" — use "Land Owner" or the specific landowner name.
- **Email context may be split across accounts.** The user's work account (ndr@draas.com) and personal account (nishantranka@gmail.com) both receive project emails. Check both via `gws_resolve_account` if you don't find what you need in the first one.
- **"Bhavish Bhavna" / Mumbai party not in email records.** Exit-buyer discussions often happen via WhatsApp or in person. If you can't find a referenced entity in email, say so directly and note that it was discussed outside email. Do not keep searching with alternate spellings.
- **Commercial analysis docs referenced in emails may not be attached.** When an email chain references "the potential realization figures provided in previous communications" (e.g. at ₹9,000/sqft), those figures may have been communicated as separate emails or attachments not retained. Document what you found and what's missing.
- **Drive write permissions vary.** The primary project folder may be owned by ndr@drahomes.in while your OAuth token is ndr@draas.com. If folder creation fails with `Insufficient permissions for the specified parent`, create at root level and inform the user.
- **Name spelling**: The cheque is authoritative for the account holder's legal name. But in project records (LO sheets), the same person may use a slightly different spelling. Document both — e.g. cheque says "SUNDER PADMANABHAN" while emails use "Sunder Padmanabhan." The cheque name is the bank's record; the email/project name is the working name.
- **Always resolve the GWS account before any Google API work.** Never hardcode `service_name='google-draas'` — call `gws_resolve_account()` or `gws_resolve_account('ndr@draas.com')` first to get the actual vault key.
- **Google Docs export fails for native .docx/PDF files**: `drive.files().export()` returns `fileNotExportable` for non-Docs-Editors files — use `drive.files().get_media()` for native .docx/.pdf. Export only works for Google-native types (document, spreadsheet, slides).
- **Scanned letterhead PDFs return empty pdftotext**: render with `pdftoppm -png -r 150 -f 1 -l 1` and OCR with `vision_analyze` to extract company letterhead / registered-address blocks. (This is how DRA Realty's registered office — 201A/202BA Queens Corner, No. 3, Queens Road, Bengaluru 560 001 — was recovered from the Raghu Iyer covering letter in the Ranka Amber folder, id `1pr8qQDrQYPC1PK7T4ZIJJY-iYjy3noe5`.)
- **PDF commercial notes can't be read by vision_analyze.** The tool says "Only real image files are supported." Use `pdftotext` (from poppler-utils, pre-installed) as your first fallback instead:
  ```bash
  pdftotext "/path/to/document.pdf" /tmp/output.txt && cat /tmp/output.txt
  ```
  If pymupdf isn't installed (import fails), do NOT spend time installing it — pdftotext extracts text from text-based PDFs instantly. For scanned PDFs, use the ocrmypdf + pdftotext pipeline (`ocr-and-documents` skill covers this).
- **ocrmypdf flag conflict:** `--force-ocr` and `--skip-text` are MUTUALLY EXCLUSIVE — ocrmypdf aborts with "Choose only one of --force-ocr, --skip-text, --redo-ocr" and produces no output file. For a scanned deed use: `ocrmypdf --skip-text --deskew --jobs 4 in.pdf out.pdf` then `pdftotext -layout out.pdf out.txt`. (2026-08: partition deed SRJ/10373, 32p, OCR'd successfully this way in ~2 min.)
- **After OCR, vision-verify the schedule pages.** OCR mangles headings and can silently drop rows — the schedule that mattered came out as bare "SCHEDULE" (the "- C" was lost) and vision confirmed it was the Nagendra allocation. For each schedule/heading of interest, render the page(s) with `pdftoppm -png -r 100 -f N -l N in.pdf /tmp/pg && vision_analyze` and independently list the survey numbers/items — cross-check against the pdftotext lines, don't trust either alone.
- **Partition deed taxonomy for "which survey numbers did X get":** In Satvik-style partition-cum-settlement deeds the structure is: **Schedule A** = all firm-acquired parcels (recitals, items 1–22 with sale deed numbers), **Schedule B** = Partner No.1 share, **Schedule C** = Partner No.2 share. Search the OCR text for "settled and allotted" and "SCHEDULE" headings to find the per-partner schedules; the header line names the partner ("...share of the Partner No. 2 i.e. Mr. C.R. Nagendra"). Also scan any clause numbers mentioning the partner name — the operating clauses (rights in agreements-for-sale, pending registrations, litigation parcels) can allocate parcels OUTSIDE the schedules.
- **Voice transcription errors create phantom entity names.** The user saying "Landono" means "Land Owner" — never search Drive for "Landono". "Bhavish Bhavna of Bombay" was a transcription of **Bhavesh Bafna** — a real Bombay-based investor whose name was shared via vCard in WhatsApp. When the user says a name you can't find in email records, FIRST scan any WhatsApp chat provided for vCard attachments or name corrections before concluding it's not in the record.
- **Name spellings cascade across systems.** The cheque says "SUNDER", the LO sheet says "Sunder", and WhatsApp self-correction shows "Sunder Padmanabhan (Padmanabhan wrongly spelt)". Track the canonical name through corrections — the last corrected version in WhatsApp/email is the working name, the cheque is the bank record name.
