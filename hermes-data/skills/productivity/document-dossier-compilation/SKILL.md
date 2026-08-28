---
name: document-dossier-compilation
description: "Compile documents from Drive into organized PDF dossiers per person/category — download, classify, extract, compile with summary/timeline/index, upload back to Drive."
version: 1.1.0
author: Hermes Agent
tags: [PDF, Drive, Compilation, Dossier, Medical, Document-Management]
related_skills: [ocr-and-documents, clinical-dossier, google-workspace]
---

# Document Dossier Compilation

Class-level skill for compiling collections of documents from Google Drive into organized, indexed PDF deliverables — one per person or per category. The output is a bound PDF with:

- Title page
- Executive summary (concise narrative from all documents)
- Chronological timeline table (date, document type, hospital/department, key findings)
- Index with page numbers referencing each source document
- All original reports/documents appended in chronological order

This is distinct from `clinical-dossier` (which produces a clinical second-opinion referral letter with linked evidence). This skill produces the source-document compilation itself — the raw organized packet.

## When to use

- User asks to compile medical / legal / project records from a Drive folder into "one PDF" or "combined file"
- User asks for a dossier of all documents related to a person or topic with summary + index
- User asks to separate documents belonging to different people into separate PDFs
- User needs a doctor-ready packet of all original reports in chronological order
- **Customer-facing real-estate legal pack** — user wants to share a project's title/legal documents with a buyer WITHOUT giving them access to the internal Drive folder. Compile ONE indexed PDF (title page, index with page ranges, docs chronological by date, undated at end). Keep internal/non-legal files out. See `references/real-estate-customer-legal-pack.md` for the DRAAS Ranka Udaya worked example.
- **Email evidence** — user has `.eml` files that need batch conversion to PDF → see `references/eml-to-pdf-conversion.md`
- **WhatsApp evidence** — user has a WhatsApp chat export that needs an interactive HTML transcript with Drive-linked media → see `references/whatsapp-evidence-html.md`
- **IRDAI complaint filing** — user needs a Bima Bharosa complaint drafted for an insurance grievance, with regulatory citations and portal constraints → see `references/bima-bharosa-complaint-drafting.md`
- **Filename standardization / inventory audit** — user needs to analyze a folder of files, standardize names, fix spelling errors, correct dates, handle duplicates, and produce a rename manifest → see `references/filename-standardization.md`
- **Firm dossier compilation** — user needs structured Word dossiers about legal entities (partnership firms, companies) compiled from scanned legal documents (partnership deeds, registration certificates, reconstitution deeds, ITRs) scattered across multiple project Drive folders → see `references/firm-dossier-compilation.md`
- **Document decompilation / splitting** — user shares a single combined multi-page PDF (e.g. 58 scanned medical pages) and needs to split it into separate documents by hospital/doc-type and organise into folders → see `references/document-decompilation-splitting.md`
- **Project material audit** — user wants to find ALL available materials (brochures, images, floor plans, renders, photos) for a project across their email and Drive, before deciding what to compile/share. Multi-account Gmail search + Drive inventory → see `references/project-material-audit.md`

## Workflow

### Phase 1: Discovery & Folder Verification

1. **Resolve Google account** — use `gws_resolve_account` to identify which Google account to use (never hardcode).
2. **Find the source folders** — search Drive for the folder structure the user described. List contents to verify.
3. **Confirm with the user** — show the folder paths, file counts, and any ambiguous filenames BEFORE downloading.

### Phase 2: Classification & Ambiguity Resolution

1. **Classify files by person/category** — which records belong to whom. If a file sits in a person's named folder, it belongs to that person.
2. **Handle misnamed files** — If a file has a wrong/unrelated-looking name (e.g., "Mr. Dhananjay" in a mother's medical folder), examine it first (vision_analyze or pdftotext) to confirm ownership. If it's clearly the right person's report, rename the original Drive file to reflect the correct person and date before including it.
3. **Scan for non-obvious files** — blood work, health packages, X-ray/ECG reports that relate to the same condition should be included even if they don't have the condition name in the filename.
4. **Confirm with the user** — present the complete file list per person/category before downloading anything.

### Phase 3: Download

Download ALL identified PDFs from Drive to local storage:

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseDownload
import io

service = build_service('drive', 'v3', service_name='google-draas')
request = service.files().get_media(fileId=file_id)
content = io.BytesIO()
downloader = MediaIoBaseDownload(content, request)
done = False
while not done:
    _, done = downloader.next_chunk()

with open(f'/tmp/{filename}', 'wb') as f:
    f.write(content.getvalue())
```

### Phase 4: Extract Content

For each PDF, determine if it's text-based or image-based:

```bash
pdftotext /tmp/document.pdf - | wc -c
# If > 20 chars → text-based
# If <= 20 chars → image/scanned PDF
```

**Text-based PDFs** — extract with PyMuPDF:
```python
import fitz
doc = fitz.open('/tmp/document.pdf')
text = ''
for page in doc:
    text += page.get_text()
doc.close()
```

**Image-based (scanned) PDFs** — convert to PNG + vision_analyze:
```bash
pdftoppm -png -f 1 -l 1 -r 300 /tmp/document.pdf /tmp/page
```
Then call `vision_analyze(image_url='/tmp/page-1.png', question='Read all text from this page')`.

For multi-page scanned PDFs, process pages in sequence, assembling the text.

**CRITICAL — Vision race conditions**: vision_analyze calls run asynchronously. When processing multiple pages of the same document through vision_analyze, run them sequentially (one at a time) by waiting for each response before sending the next page. For multiple documents in parallel, use `delegate_task` sub-agents, each handling one document entirely within its own context.

### Phase 5: Compilation — SEPARATE PDFs per Person

**CRITICAL RULE (user preference):** When records belong to multiple people, create SEPARATE PDFs — one per person. NEVER mix reports from different people into a single file unless explicitly instructed.

For each person/category, build a single PDF with:

#### Page 1: Title Page
- Title: `[Person Name] - Medical Records Compilation`
- Subtitle: `Compiled on DD MMM YYYY`
- Total documents included, date range

#### Page 2: Executive Summary
- ~200-400 word narrative summarizing the key clinical story
- For each person: condition, diagnostic trajectory, key interventions, current status
- Written from the reports — do not hallucinate clinical details

#### Page 3: Chronological Timeline Table (Index)
Table format: `Page | Date | Report Type | Hospital/Doctor | Key Findings`
- One row per document
- "Page" column = starting page number of each document in the compiled PDF
- Sorted chronologically

#### Page 4+: All Original Reports
- Each report appended in chronological order
- Between reports, insert a separator page showing the report's date and title
- Use PyMuPDF (fitz) to merge pages from the original source PDFs

**Ordering rule (Bharat preference, legal packs):** When a user says "segregate by year/date" or "documents without dates at the end":
1. Sort dated documents by their date (oldest → newest). Use the document's own date from its content/filename, not the folder listing order.
2. Group documents sharing a date together (e.g. two relinquishment deeds on 2025-02-24 stay adjacent).
3. Undated documents (maps, sketches, registers, title-clearance letters with no date) go at the END, after all dated docs.
4. The index table lists page ranges ("pages X–Y") per document so the user can cite a range per doc.

```python
import fitz

# Create output
output = fitz.open()

# Add summary pages (built from scratch using fitz)
summary_page = output.new_page()
# ... insert text, table ...

# Append original reports
for pdf_path in sorted_reports:
    src = fitz.open(pdf_path)
    output.insert_pdf(src)
    src.close()

output.save('/tmp/output.pdf')
output.close()
```

### Phase 6: Upload to Drive

#### ⚠️ Pre-upload: Verify Account Identity

Before uploading, check which Google account you're actually authenticated as — it may differ from the folder owner or the user you're chatting with:

```python
from googleapiclient.discovery import build

# Check current authenticated identity
profile = service.about().get(fields='user').execute()
authed_email = profile['user']['emailAddress']
print(f"Authenticated as: {authed_email}")

# Check folder owner
folder_info = service.files().get(
    fileId=SOURCE_FOLDER_ID, fields='owners'
).execute()
folder_owner = folder_info['owners'][0]['emailAddress']
print(f"Folder owner: {folder_owner}")

if authed_email != folder_owner:
    print(f"⚠️ MISMATCH! Uploading as {authed_email} but folder is owned by {folder_owner}")
    print(f"   Files will be owned by {authed_email}, causing 400 errors for the folder owner.")
```

**CRITICAL: Files uploaded as a different account than the folder owner will cause 400 errors** for the user who owns the folder. The files are visible in the folder listing but return access-denied when clicked.

**If there's a mismatch**, use the email-resolution bypass to authenticate as the correct user:

```python
from tools import gws_vault_client as vault
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Resolve the correct vault UID from the user's email
uid = vault.resolve("email", "sales1.blr@draas.com")  # ← use the correct email
token_str = vault.get_token(uid, "google-draas", session_uid=uid)
creds = Credentials.from_authorized_user_info(json.loads(token_str))
service = build('drive', 'v3', credentials=creds)

# Now verify
profile = service.about().get(fields='user').execute()
print(f"Now authenticated as: {profile['user']['emailAddress']}")
```

This bypasses `gws_auth.build_service()` entirely — use `gws_vault_client` for token access and `googleapiclient` directly. Only proceed with upload once `authed_email` matches the folder owner.

#### Upload

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload('/tmp/output.pdf', mimetype='application/pdf')
uploaded = service.files().create(
    body={
        'name': 'YYYYMMDD_PersonName_Records_Compilation.pdf',
        'parents': [SOURCE_FOLDER_ID]
    },
    media_body=media,
    fields='id,name,owners,webViewLink'
).execute()

# Verify ownership after upload
owners = [o['emailAddress'] for o in uploaded.get('owners', [])]
print(f"Uploaded by: {owners}")
```

Date format: use the compilation date in YYYYMMDD format.

### Phase 7: Cleanup

- **Delete old combined PDF** — if this task replaces a prior compilation (e.g., a mixed-person PDF), delete that from the Drive folders so there's no confusion
- **Rename misnamed source files** — if you renamed a file on Drive (Phase 2), confirm the rename was applied correctly by checking the Drive listing
- **Remove local temp files** — clean up downloaded PDFs, extracted text, and intermediate build files (`rm -rf /tmp/compilation_workdir`)

## User Preferences (Nishant)

These are conventions specific to Nishant (DRAAS CEO, Bangalore) that MUST be followed:

### Multi-person handling
When compiling records for multiple individuals, ALWAYS produce separate PDFs per person. Never mix. Confirm the separation structure before starting.

### Misnamed files
When a file in a person's folder has a name that suggests it belongs to someone else (e.g., "Mr. X" in a folder for "Mrs. Y"), examine the file content first. If it's clearly the folder-owner's report with a data-entry error in the filename, rename the source file on Drive to correct it, then include it in the compilation.

### Chronological ordering
Always order reports chronologically within each person's PDF. The timeline table on page 3 must also be in chronological order.

### All reports policy
Include ALL documents in the folder that relate to the medical condition or period of interest, plus the latest full-body health checkup for each person. When in doubt, include — the user will tell you to exclude something they don't want.

### PDF naming
Use this format: `YYYYMMDD_PersonName_Records_Compilation.pdf`
Example: `20260709_KDR_Medical_Records_Compilation.pdf`

### Document rename on Drive
When renaming a misnamed source document, use:
`YYYYMMDD_PersonName_Description_Hospital.pdf`
Example: `20230411_KDR_Tympanogram_Cavaller_Hospital.pdf`

## Pitfalls

- **Vision model race condition**: vision_analyze calls are independent. If you send multiple pages of the same document simultaneously, the model has no memory of previous pages. Process pages within one document sequentially. Use sub-agents for parallelizing ACROSS documents, not within one.
- **pdftotext empty is normal for scanned PDFs**: don't report it as an error. Fall through to pdftoppm + vision_analyze.
- **PyMuPDF (fitz) not in venv**: If `import fitz` fails, use `pdf2image` (PIL-based) or `pdftoppm` for conversion options, or switch to the Hermes venv at `/opt/hermes/.venv/bin/python3` which has fitz pre-installed.
- **File naming confusion**: source PDFs may have names that don't reflect their content (old names, sequential numbers, wrong participants). Always examine before drawing conclusions.
- **Large folders**: If a folder has 50+ files, batch the download in groups. The download can be slow for high-resolution files.
- **Page number index shifts**: When building the index, calculate page offsets carefully. Each original PDF adds its page count plus separator pages. Track cumulatively.
- **Clean up old versions**: If this replaces a prior compilation (mixed PDF that's now superseded by separate per-person PDFs), delete the old one from Drive. Verify after deletion.
- **Google Drive shared links behind auth**: When Drive file links redirect to Google Sign-in, all download methods (curl, browser, web_extract) fail. Work with the filename metadata alone — filenames, descriptions, and known patterns often contain enough info for an audit. Do NOT fabricate file content. Log the issue and proceed with what's visible in the names.
- **Document count mismatch**: The user said 14 reports for KDR but the folder may have 17 (including imaging, blood work, follow-up visits that don't have "ear" in the name). Include all condition-related files, not just obvious ones.
- **Upload-ownership mismatch causing 400 errors**: Files uploaded to a Drive folder are owned by the authenticated Google account (the uploader), NOT the folder owner. If you authenticate as `psingh@draas.com` but the folder is owned by `sales1.blr@draas.com`, the files will be visible in the folder listing but show 400/Access Denied when the folder owner clicks them. **Always verify `authed_email` matches the folder owner before uploading.** Use the email-resolution bypass in Phase 6 when they don't match.
- **`drive_upload` parameter bug**: `gws_skill_bridge.call("drive_upload", ...)` silently drops the `mime_type` and `name` defaults from partial args (they're stored as `None` instead of falling through). Workaround: always pass BOTH `name` and `mime_type` explicitly:
  ```python
  call("drive_upload", service_name="google-draas",
       path=local_path, parent=folder_id,
       name="My_Document.pdf",              # ← always required
       mime_type="application/pdf")         # ← always required
  ```
- **fpdf2 multi_cell layout bug**: After calling `pdf.multi_cell(0, 5, text)`, always reset `pdf.set_x(pdf.l_margin)` before the next multi_cell to avoid "Not enough horizontal space" errors.
- **vision_analyze rejects PDF inputs directly**: `vision_analyze(image_url=<file.pdf>)` fails with "Only real image files are supported". Convert the first page to PNG first with PyMuPDF (`page.get_pixmap(dpi=150).save('out.png')` — note `import pymupdf`, the `fitz` name is deprecated) and pass the PNG.
- **Sanitized Drive filenames can collide after truncation**: If you build local filenames by slugifying Drive names to a fixed length (e.g. 80 chars), two long names that differ only in a parenthetical like `...Nanjamma and Prakash Reddy & others...` vs `...Nanjamma and Prakash Reddy (Amaresha)& others...` can truncate to THE SAME filename — the second download silently overwrites the first. Verify after download: compare the local file count/list against the Drive listing, or use a uniqueness suffix (index) on collision.
- **Customer-facing legal pack vs internal diligence set**: The shared Drive folder is the internal working set — it has "Copy of Copy of ..." prefixes, duplicate copies (colour copy + original), internal docs (ICICI unit nomenclature sheet), and the agent's own draft artifacts (allotment letter draft). Ask the user before compiling into a customer dossier: exclude internal-only docs and self-created drafts, and dedupe copies (keep the original colour copy, drop the duplicate). Always name the decision explicitly in the confirmation list so the user can veto.

## Legal / Title Document Packs (customer handoff)

A recurring DRAAS variant: the user shares an **internal Drive folder of land-title legal documents** (EC, sale deeds, gift/partition/rectification deeds, GPA, RERA order, approved layout, Thasildar NOC, adangal, village map, family tree, legal scrutiny reports) and wants a **customer-facing compiled PDF** — NOT the Drive folder link. The internal folder contains "Copy of" names, internal reports, and docs the customer shouldn't see.

**When user says "I don't want to share this in drive / what's a better way" → the answer is a single compiled dossier PDF** (send via WhatsApp/email attachment), not a shared folder.

Ordering / content rules (Bharat preferences, verified 2026-08-25):
- **Dated documents first, oldest → newest** (by document execution/issue date, not filename).
- **Undated documents at the END** (village map, registers, topo sketches, family trees).
- **Dedupe duplicate copies** — same deed appearing as colour copy + original + re-scan → keep ONE (the original colour copy). Ask or decide; flag the decision to the user.
- **Exclude internal-only docs** — unit-nomenclature sheets, allotment letter drafts, ICICI sheets. Not legal, customer shouldn't see them. Flag exclusion.
- **Clean names** — drop "Copy of", use display names (e.g. `Absolute Sale Deed to DRA Thindlu Land Partners (Doc 20527/24-25)`).

Structure per document: **separator page** (DOCUMENT N / display name / date / "Pages X - Y") then the original pages — so the customer's lawyer can jump straight to any document.

See `references/legal-document-pack-customer-handoff.md` for the build recipe (exact page-number arithmetic, separator pages) and `scripts/compress_dossier.py` for the size fix.

## Related Skills

- `ocr-and-documents` — Text extraction from individual PDFs (both text and scanned/image-based)
- `clinical-dossier` — Creating a clinical second-opinion referral letter with analysis (builds on top of this skill's output)
- `google-workspace` / `gws-automation` — Drive API operations (find, download, upload, rename)

---

## Decompilation (Reverse Flow)

This skill primarily covers **compilation** (many PDFs → one organized dossier). The **reverse flow** — one large multi-document PDF → split into separate files by document/hospital — is covered in `references/document-decompilation-splitting.md`. Key differences:

| Aspect | Compilation | Decompilation |
|--------|-------------|---------------|
| Input | Many separate PDFs from Drive | One combined multi-page PDF |
| Output | One bound dossier per person | Many separate PDFs organized by hospital |
| Key tool | PyMuPDF (fitz) merge | qpdf page-range split |
| Analysis | Read each PDF separately | Vision-scan each page to find boundaries |
| Naming | YYYYMMDD_Person_Description | HospitalName_DocumentType_Month |
