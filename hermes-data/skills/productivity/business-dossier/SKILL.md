---
name: business-dossier
description: "Multi-source intelligence gathering for any business, legal, or transaction matter — search Drive across name variants, mine Gmail for related threads, extract key documents, cross-reference findings, compile into a structured briefing note, and prepare respectful third-party outreach."
version: 1.3.0
author: Hermes Agent
---

# Business Dossier — Intelligence Gathering & Briefing Note

Class-level skill for quickly assembling a comprehensive dossier on any business/legal/transaction matter by searching Google Drive + Gmail, synthesizing findings, and creating a structured briefing note. Also covers preparing a respectful WhatsApp/communication draft for third-party outreach (community elders, MLAs, mediators).

## When to Use

- User asks to "find everything on Drive related to [company/entity/project]" (often with multiple aliases — e.g., Nippon Capital = Veracious = Vani Vilas = Amit Nippon)
- User needs a briefing note on a legal dispute, transaction, or investment opportunity
- User wants to approach a senior community member / intermediary (MLA, elder, mediator) about a matter
- Cross-referencing Drive documents + Gmail threads to build a complete picture
- User shares a **WhatsApp chat export zip** (chat txt + media) as source material — see `references/whatsapp-export-intake.md` for the intake workflow: unzip, read the .txt entirely, extract corrected numbers/commitments/exit asks, mine the chat for email addresses to use as Gmail search terms, and classify media (PDFs = file, IMG = screenshots, STK = skip).

## Workflow

### Phase 1: Identify All Name Variants / Aliases

Before searching, establish the full set of names the target goes by. The user often provides these: "it's also called X, Y, Z, A interchangeably."

Build a search list including:
- Legal entity name (from contracts, MCA records)
- Project/development name
- Builder/developer name
- Landowner surname / family name
- Short forms and phonetic variants
- Key people associated (promoters, directors, lawyers, brokers)

### Phase 2: Parallel Drive Search — Multiple Queries

Search Drive with each variant using BOTH `name contains` and `fullText contains`:

```python
drive = build_service("drive", "v3")
all_files = []
for q in queries:
    page_token = None
    while True:
        results = drive.files().list(
            q=q,
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType, parents, size, createdTime, modifiedTime, owners)',
            pageSize=100,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        # Deduplicate by file ID
        for f in results.get('files', []):
            entry = (f['id'], f['name'], ...)
            if entry not in all_files:
                all_files.append(entry)
```

Key: Deduplicate by file ID — the same file may match multiple search terms.

Identify the **primary folder** for the matter, if one exists. Check sub-folder structure:
- Transaction Documents (mortgage deeds, debenture trust deeds)
- Legal Data (court orders, IA applications, complaints)
- Property Documents (sale deeds, JDAs, GPAs, encumbrance certs)
- Sanction Plans and NOCs (BBMP, BESCOM, BWSSB, Airport, etc.)
- JDA / Supplementary Agreements
- Notes (analysis, briefs, facts compilations, legal opinions)

### Phase 2.5: Seed Document → Identifier Extraction (Optional)

When the user provides a **single document** (legal opinion, title report, facts compilation) as the starting point for discovery — use it as a seed. Extract every identifier from it and use them as search terms.

**Trigger:** User shares a link to a document (especially a legal opinion or due diligence report) and asks you to "find all related documents."

**Workflow:**

1. **Download the seed document:**
   ```python
   file_id = extract_file_id_from_url(user_shared_link)
   request = drive.files().get_media(fileId=file_id)
   with open(local_path, 'wb') as f:
       downloader = MediaIoBaseDownload(f, request)
       # ... complete download
   ```

2. **Extract text from the seed document:**
   - First check if PDF is text-based: `pdftotext input.pdf output.txt` — if output > 0 bytes, you have text
   - If scanned (0 bytes): **convert to PNG first** using PyMuPDF (fitz), THEN call `vision_analyze` on each page image — `vision_analyze` does NOT accept PDFs directly, only image files (PNG/JPG):
     ```bash
     /opt/hermes/.venv/bin/python3 -c "
     import fitz
     doc = fitz.open('input.pdf')
     for i, page in enumerate(doc):
         pix = page.get_pixmap(dpi=300)
         pix.save(f'/tmp/pages/page_{i+1}.png')
     "
     ```
   - For Google Docs: `drive.files().export(fileId, mimeType='text/plain')`
   - For .docx: `python-docx` or zipfile+XML fallback

3. **Extract ALL identifiers from the text:**

   Build a comprehensive list of:
   - **Property identifiers:** Survey numbers (Sy. 151, 152, 153), village names (Binnamangala, Birmangala), municipal numbers (No. 1), locality names (Indiranagar I Stage, Rangappa Garden, Narayanappa Garden), extents (12,240 sq.ft.)
   - **Party names (ALL):** Landowners (Chinnaraje Ammal, M. Ramaswamy Reddy, R. Mahalingam Reddy, R. Lalitha, R. Vijaya Kumar Reddy), developers (Arya Developers, Dinesh Ranka, Kanta D. Ranka), purchasers/intermediaries (P. Dayananda Pai, M. Devraj), advocates/law firms (Prashanth Acharya, Muniyappa Advocate, CrestLaw Partners, Pingal Khan, Ashlar Law)
   - **Document references:** JDA dated 07.09.1995, GPA dated 25.03.1995 and 09.02.1996, Supplemental Agreement dated 07.02.1996, Khatha Certificate 11.01.1996, BBMP License 94/96-97
   - **Legal case references:** OS 6889/1998, OS 2095/2002, AC 10017/1984, Misc 240/2012, RFA 347/1993, OS 7005/2000
   - **Authority references:** BDA Resolution 485/18.12.1982, BBMP Notice 09.01.1996
   - **Date ranges:** All dates mentioned (e.g., 28.08.1952, 01.11.1973, 07.09.1995)
   - **Name variants and misspellings** (Binnamangala, Binmangala, Birmangala, Binnamagala)

   **DO NOT SKIP any identifier** — every name, number, and reference is a potential search term. Documents that the user's team has filed may use slightly different names, spellings, or abbreviations than the legal opinion does.

4. **Search Drive with EVERY identifier as a `fullText contains` query:**
   ```python
   for term in all_identifiers:
       results = drive.files().list(
           q=f"fullText contains '{term}' and trashed=false",
           pageSize=50,
           fields='files(id, name, mimeType, owners, webViewLink, modifiedTime)'
       ).execute()
   ```
   Deduplicate results by file ID — the same file may match multiple terms.

5. **Search Gmail with the same identifiers:**
   ```python
   gmail = build_service('gmail', 'v1')
   for term in identifiers[:20]:  # most distinctive terms
       results = gmail.users().messages().list(
           userId='me', q=term, maxResults=50
       ).execute()
   ```
   Focus on emails that reveal the deal/property history, document exchanges, and payment records.

6. **Cross-reference: found vs referenced-but-missing**

   Compare the documents the seed document references against what you actually found on Drive. Create a **gap analysis**:
   - ✅ Found on Drive: File name + link
   - ⚠️ Referenced but NOT on Drive: Document name + date + "may need to locate physically"

   This is one of the most valuable outputs — the user may not know key referenced documents are missing from their digital repository.

6.5 **Cross-reference Gmail Attachments Against Drive Inventory**

   After searching Drive, check Gmail for documents that exist as email attachments but are **NOT on Drive**. This catches documents referenced in email threads that were never filed into the Drive folder structure.

   **Trigger:** When the seed document references other documents that the Drive search didn't find, OR when the user asks for a complete picture of all documents the team has exchanged.

   **Workflow:**

   1. **Search Gmail with `has:attachment` for the matter's key identifiers:**
      ```python
      gmail = build_service('gmail', 'v1')
      search_terms = [
          'PropertyName has:attachment',
          'EntityName has:attachment',
          'SurveyNo has:attachment',
          'CaseNumber has:attachment',
      ]
      for term in search_terms:
          results = gmail.users().messages().list(userId='me', q=term, maxResults=30).execute()
      ```

   2. **For each matching email, extract and check attachments:**
      ```python
      for m in results.get('messages', []):
          msg = gmail.users().messages().get(userId='me', id=m['id'], format='full').execute()
          parts = [msg['payload']]
          while parts:
              part = parts.pop(0)
              if 'parts' in part: parts.extend(part['parts'])
              if part.get('filename') and part['body'].get('attachmentId'):
                  fn = part['filename']
                  # Check if this filename already exists on Drive
                  existing = drive.files().list(q=f"name = '{fn}' and trashed=false", pageSize=3, fields='files(id)').execute()
                  if not existing.get('files'):
                      # Download it — it's a new document not on Drive
                      att = gmail.users().messages().attachments().get(userId='me', messageId=m['id'], id=part['body']['attachmentId']).execute()
                      data = base64.urlsafe_b64decode(att['data'])
                      with open(f'/tmp/gmail_docs/{fn}', 'wb') as f:
                          f.write(data)
                      print(f'⚠️ NOT on Drive: {fn} — saved from email')
      ```

   3. **Upload missing documents to Drive:**
      For each new attachment found, determine the correct folder (property subfolder, Legal subfolder), apply naming convention (YYYYMMDD), and upload with a description noting the source email:
      ```python
      media = MediaFileUpload(local_path, mimetype=mime, resumable=True)
      uploaded = drive.files().create(body={
          'name': new_name,
          'description': f'Extracted from email: {email_subject} ({email_date})',
          'parents': [target_folder_id]
      }, media_body=media, fields='id,name,webViewLink').execute()
      ```

   4. **Report:**
      - ✅ New documents uploaded from email: list with links
      - ✅ Already on Drive (no action needed)
      - ❌ Irrelevant attachments (different property, same entity)

   **Pitfalls:**
   - Same attachment sent by multiple people — deduplicate by filename+size before uploading
   - Password-protected or image-only PDFs — note and move on
   - Some email attachments may relate to DIFFERENT properties under the same entity (e.g., Elegant Springdale docs under Arya Developers entity but NOT Binnamangala property) — cross-check before filing
   - Save source email metadata (subject, date, from) in Drive file description for audit trail

7. **Produce a structured inventory report:**

   Create an HTML document (`PropertyName_Complete_Document_Inventory.html`) with:
   - **Property Summary Card** — all key details from the seed document (survey numbers, extent, parties, legal cases)
   - **Section A: Core Property Documents Found** — tables grouped by type (Legal Opinions, JDAs, GPAs, Court Documents, Revenue Docs) with name, date, owner, description, and link for each
   - **Section B: Key Emails** — chronological list of relevant emails with subject, from/to, and snippet
   - **Section C: Entity/Firm Documents** — entity-level docs (partnership deeds, reconstitutions) that relate to the firm but not specifically to the property
   - **Section D: Separate-Property Documents** — documents that share the same entity but belong to a DIFFERENT property (e.g., Elegant Springdale docs under Arya Developers are NOT Binnamangala docs)
   - **Section E: Referenced-but-Missing** — the gap analysis table with all docs the seed document mentions that are NOT on Drive
   - **Section F: Current Drive Organization** — how files are currently organized in folders

   Upload to `temp.tmp` folder on Drive and provide the link to the user.

**Pitfalls:**
- Scanned PDFs (registered deeds, legal opinions) have NO text layer — pdftotext returns 0 bytes. Always check with `pdftotext` first, then fall back to `pdftoppm` + `vision_analyze`.
- The seed document may contain typographical errors in names/case numbers — search for variants too (e.g., "Binnamangala" + "Binmangala" + "Birmangala")
- 335+ files may match broad searches — filter for relevance by checking name/path against the seed document's context
- Dayananda Pai documents may relate to the property's sale history even if they don't mention the survey numbers explicitly — cross-reference by party name
- The same property might be documented under the FIRM name (Arya Developers) AND the property name (Binnamangala) in different folders — both searches are needed
- Documents referenced in a legal opinion may never have been digitized (especially pre-2000 documents) — flag these honestly as "not on Drive, may exist only as physical copies"

### Phase 3: Multi-Account Parallel Gmail AND Drive Search

Search Gmail **and Drive** across ALL configured accounts (not just the default). Key correspondence and documents may live on a secondary account (e.g., Nippon Capital emails absent from the primary account).

```python
# Search all configured accounts — never skip this
import os
for svc_name in ["google-draas", "google-ahfl", "google-gmail"]:
    try:
        gmail = build_service("gmail", "v1", service_name=svc_name)
        profile = gmail.users().getProfile(userId="me").execute()
        authed_as = profile.get("emailAddress")
        for term in variants:
            # Gmail search
            results = gmail.users().messages().list(userId='me', q=term, maxResults=10).execute()
            # Drive search
            drive = build_service("drive", "v3", service_name=svc_name)
            drive_results = drive.files().list(q=f"fullText contains '{term}' and trashed=false", pageSize=20).execute()
    except Exception:
        continue  # Account may not have token — skip silently
```

Extract from each relevant email:
- **Subject** (often reveals the deal stage — MOU, term sheet, exclusivity)
- **From/To/Cc** (key contacts — project lead at the bank/PE firm, their legal, the counterparty)
- **Body** (key terms, baseline numbers, timelines, conditions)
- **Attachments** (documents shared but not filed on Drive)

**Focus on recent emails first** — they reflect the current state of the matter.

### Phase 4: Read Key Documents

From the Drive results, read the most informative documents first:

1. **Facts Compilation / Brief Note** — usually the best single-source overview
2. **Comprehensive Legal Analysis** — detailed positions of all parties
3. **Court Order Summaries** — current legal status
4. **MOU / Term Sheet drafts** — from Gmail — deal structure and key contacts
5. **Enforcement Suit / Complaint** — if litigation is involved

For `.md` files: use `drive.files().get_media(fileId=...).execute()` (text/plain mimeType).
For Google Docs: use `drive.files().export(fileId, mimeType='text/plain')`.
For `.docx`: download via `get_media()` and extract via zipfile + XML (stdlib-only fallback without python-docx).

**Extract these key data points:**
- Identity of all parties (plaintiffs, defendants, co-obligors)
- Financial details (loan amount, debentures, outstanding, interest rate)
- Chronology (when each event occurred)
- Current legal status (pending, settled, NCLT, appeal)
- Dispute nature (fraud, non-payment, occupancy dispute)
- Key contacts (phone, email, firm)

### Phase 5: Cross-Reference & Correlate

Cross-check information across documents:
- Landowner names in the mortgage deed vs the court orders vs the email thread
- Loan amounts and outstanding across sources (often differ slightly due to interest accrual)
- What each party claims vs the documentary evidence

Note any discrepancies for the briefing note.

### Phase 6: Decision — Google Doc Briefing Note vs HTML Timeline vs WhatsApp-Only

**Before creating any document, determine the user's intent:**

- **Internal reference / team use** → Create a briefing note (Google Doc by default, or HTML timeline document if the user asks for a formatted sequence of events)
- **Third-party outreach to a senior/elder contact** → Skip the document, go straight to WhatsApp message
- **"Sequence of events" / "chronology" / "timeline" request** → Use the HTML Timeline Document option (Phase 6b) instead of a Google Doc

**Signal mapping (Jul 2026):**
| User says | Document type |
|-----------|--------------|
| "briefing note", "brief me", "summary of the matter" | Google Doc briefing note (Phase 6a) |
| "timeline", "sequence of events", "chronology", "detailed narration based on sequence" | HTML timeline document (Phase 6b) |
| "WhatsApp message for [elder/contact]" | WhatsApp-only (Phase 7) |
| ambiguous — "create a document", "prepare a report" | Ask: "Do you want a briefing note (Google Doc) or a visual timeline (HTML document)?" |

For third-party outreach to a senior/elder contact (MLA, community elder, mediator), ask: "Do you want a formal document, or just a WhatsApp message?" If they just need WhatsApp, skip the document and go straight to Phase 7.

⚠ **Session signal (Jun 2026):** User asked to create a formal briefing note for Nippon Capital/Veracious matter, then immediately said to delete it — they only needed the WhatsApp message for Uncle Ji (senior community member). The formal document was unnecessary overhead. Default to WhatsApp-only for elder/community-leader outreach unless the user explicitly asks for a document.

### Phase 6a: Create Briefing Note (Google Doc)

Create a structured briefing note as a Google Doc (only if Phase 6 decision was to create a document):

```
Title: YYYYMMDD [Entity Name] — [Matter Name] — Briefing Note

1. THE PROJECT / TRANSACTION
   - Project name, location, developer/builder
   - Current status (operational, NCLT, settled, in dispute)

2. THE PARTIES
   - Lender / Debenture holder — contact names, emails
   - Builder / Developer — directors, promoters
   - Landowners / Co-obligors — family group, relationship to the property
   - Other stakeholders (tenants, allottees, legal counsel)

3. THE FINANCIAL STRUCTURE
   - Loan amount, debentures issued, interest rate
   - Outstanding dues claimed
   - Security / collateral pledged

4. THE DISPUTE (if applicable)
   - Nature of the dispute (fraud, occupancy, non-payment)
   - Each party's position
   - Legal proceedings: court, case number, current stage
   - Key court orders / findings

5. CURRENT STATUS
   - What Nippon / the lender wants
   - What the landowners want
   - What the builder (if in liquidation) is doing
   - What settlement framework is being discussed

6. THE ASK — [RECIPIENT NAME]
   - What is needed from the third party (introduction, mediation, legal opinion)
   - Why they are the right person (knows the family, respected intermediary)
   - Expected outcome if they help

7. **KEY CONTACTS**
   - Names, emails, **phone numbers** of all relevant people (extract from documents — court orders, mortgage deeds, email signatures often contain phone numbers)
   - Source (email thread, mortgage deed, court order, contact sheet)

8. DRIVE FOLDER & DOCUMENTS
   - Link to primary Drive folder
   - Brief index of key documents available
```

Use the `google-doc-formatting-template` skill for proper formatting (HTML import preferred).

### Phase 6b: Create HTML Timeline Document (Chronological Sequence)

When the user asks for a **timeline**, **sequence of events**, **chronicle**, or **detailed narration based on date order** — create a self-contained HTML+CSS document instead of a Google Doc.

**Structure:**

```
1. HEADER — Project/Property name, subtitle with location, entity
2. SUMMARY CARDS — Key facts as grid cards (property, entity, landowner, developer, time period, source count)
3. KEY INFO BOX — Structured grid: location, legal status, partnership entities, case numbers
4. TIMELINE — Chronological sections grouped by phases:
   - Each phase has a labelled divider (Phase 1 — Origin, etc.)
   - Each event: date, event title, description with key people/entities bolded, source citation
5. DRIVE FILES TABLE — Tabular listing of all related documents with dates, filenames, owners
6. KEY PEOPLE TABLE — Names, emails, roles
7. FOOTER — Generation date, data source summary
```

**Formatting rules:**
- Self-contained HTML with inline `<style>` (no external dependencies)
- Use timeline visual: left vertical line, circle markers, border-left accent per event
- Summary cards at top: grid layout, each card = label + value
- Tables for file listings: `th` with uppercase labels, alternating row hover
- Responsive: `@media` query for mobile
- Colors: dark navy header (#16213e, #0f3460), light grey background (#f5f7fa), white cards
- Font: system sans-serif stack ('Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif)
- Source citations at bottom of each event in smaller grey text
- No JavaScript needed — pure CSS

**Generation approach:**
```python
html = \"\"\"<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>Descriptive Title</title>
<style>
  /* All inline styles */
</style>
</head>
<body>
<div class=\"container\">
  <!-- All content -->
</div>
</body>
</html>\"\"\"

with open('/tmp/timeline.html', 'w') as f:
    f.write(html)
```

Generate the HTML via `execute_code()` (not terminal heredoc — avoids shell escaping issues with HTML special characters).

Then proceed to Phase 6c for Drive upload, sharing, and email notification.

### Phase 6c: Upload to Drive, Share & Email Notification

After creating the HTML document in `/tmp/`, deliver it via Drive:

**Step 1 — Find the target folder:**
```python
drive = build_service('drive', 'v3')
results = drive.files().list(
    q=\"name='temp.tmp' or name='TMP'\",
    pageSize=10,
    fields=\"files(id,name,mimeType)\"
).execute()
# Use temp.tmp (preferred) or TMP folder
folder_id = '1QMCQPOoSiCJ9ubibnaLQSQou5GXc4FO2'  # temp.tmp
```

**Step 2 — Upload the HTML file:**
```python
from googleapiclient.http import MediaFileUpload
media = MediaFileUpload('/tmp/timeline.html', mimetype='text/html', resumable=True)
uploaded = drive.files().create(
    media_body=media,
    body={'name': 'Descriptive_Filename.html', 'parents': [folder_id], 'mimeType': 'text/html'},
    fields='id,name,webViewLink'
).execute()
file_id = uploaded['id']
doc_link = uploaded.get('webViewLink')
```

**Step 3 — Set viewer permissions for recipients:**
```python
for email in [recipient_email, owner_email]:
    perm = drive.permissions().create(
        fileId=file_id,
        body={'type': 'user', 'role': 'reader', 'emailAddress': email},
        sendNotificationEmail=False
    ).execute()
```

**Step 4 — Send email notification:**
```python
from email.message import EmailMessage
import base64

msg = EmailMessage()
msg['From'] = 'Nishant Ranka <ndr@draas.com>'
msg['To'] = ', '.join([recipient_email, owner_email])
msg['Subject'] = f'[Project Name] — Timeline Document Ready'

body = f\"\"\"Hi [Names],

The comprehensive timeline document for [Project/Entity] is now ready.

📄 Document: [Filename]
🔗 Link: {doc_link}

What's covered:
- [Summary of key phases covered]
- [Source statistics: X emails + Y Drive files referenced]

Please access the link above and review.

Regards,
Nishant\"\"\"

msg.set_content(body)
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8').replace('+', '-').replace('/', '_').replace('=', '')
gmail.users().messages().send(userId='me', body={'raw': raw}).execute()
```

**Naming conventions:**
- HTML filename: `Entity_Property_Descriptive_Timeline.html` (underscores, no spaces)
- Email subject: `[Entity/Property] — Complete Timeline Document Ready`
- File goes to `temp.tmp` folder on Drive (never create new tmp folders)

**Recipient identification:** When the user says "share with Rahul and me", check if "Rahul" is a nickname. From the verified alias list (Jul 2026): Rahul → Vinod Kumar Das (vkdas@draas.com). Always resolve nicknames before setting permissions or sending email.

### Phase 6.5: Save to Memory

Save a compact factual summary to memory after the dossier is created:

```python
memory(action='add', target='memory', content='[Entity Name/Matter summary: key names, amounts, current status, contacts, relationships.]')
```

### Phase 7: Prepare Third-Party Outreach (WhatsApp / Message)

When the dossier is for an intermediary (senior community member, MLA, family elder), draft a simple, respectful message.

**⚠ Delivery format (Nishant, Jun 2026):** Present the WhatsApp message as a **markdown code block** (triple backticks, no language tag) so the user can tap to select and copy the entire block. Use WhatsApp *bold* formatting for emphasis. Do NOT create a deep link or clickable URL — the user will paste the text into their own WhatsApp conversation.

**Tone rules (for senior Marwadi community members / elders):**
- Open with a respectful greeting: `[Name] Ji, pranam.`
- Ask about their well-being briefly
- State the purpose simply in 1-2 sentences
- Give the key facts (who, what, where, why now) — NO legal jargon, NO court case numbers, NO technical financial terms
- Make a specific ask (e.g., "could you kindly connect us with / arrange a meeting with")
- Explain why they are the right person (they know the family, respected by both sides)
- Close with gratitude and deference

**Keep it simple — WhatsApp-length, not email-length:**
- No court case numbers, no section numbers, no legal citations
- No financial jargon (debentures, NCLT, co-obligors)
- Use plain terms: "loan", "builder went bankrupt", "landowner family", "settle amicably"
- The recipient is a community elder, not a lawyer or banker

**WhatsApp markdown to use:**
- `*bold*` for project names, key numbers, key people, and the ask
- `~strikethrough~` where appropriate
- Line breaks between sections for readability
- No URLs — the user copies the text into WhatsApp

**Example structure (to present as code block):**
```
*[Name] Ji, pranam.* Hope you and family are well.

I wanted to seek your guidance on a matter regarding *[project name]* in [location].

Briefly: [25-word summary]

We understand *[MLA / person's name] Ji* knows the family personally. We believe if he steps in as a respected intermediary, a settlement can be reached.

*Request:* If you could kindly connect us or arrange a brief meeting, it would go a long way.

*Thank you, [Name] Ji.* Looking forward to your guidance.
```

### Phase 7b: VIP / MLA Post-Meeting Follow-Up — WhatsApp with Structured Data

When the user has already **met in person** with a VIP (MLA, elected representative, senior government officer) and needs a follow-up message thanking them and sharing structured data about a matter they discussed.

**Trigger:** User says "create a WhatsApp message for [MLA name] — thanking him for his time and hospitality today" and wants to share landowner/party details.

**This is DIFFERENT from Phase 7 (elder outreach asking for an introduction):**
- Phase 7: Cold outreach — asking the elder to connect/arrange a meeting
- Phase 7b: Post-meeting follow-up — already met, thank them, share data discussed

**Tone rules for MLAs / elected representatives:**
- Open with "Respected Sir," — NOT "Ji, pranam" (that's for community elders)
- Thank them specifically for their time AND hospitality
- Share structured data in a clean, readable format — numbered list with owner name, age, units, sq ft, address
- Use plain language: "units" not "mortgaged inventory," "sq ft" not "built-up area super built," "loan" not "NCD"
- No court case numbers or legal citations
- End with gratitude and offer to share supporting documents if needed
- Keep it one message, not a chain — WhatsApp-length is fine for structured lists

**Data preparation for share:**
1. Calculate per-owner built-up area proportionally from total:
   ```python
   total_units = 45
   total_sqft = 81165
   per_unit_sqft = total_sqft / total_units  # ~1804 sq ft avg
   owner_data = {
       'Sunanda Vani': {'units': 12, 'pct': 26.7, 'sqft': 21672},
       'Malathi':      {'units': 10, 'pct': 22.2, 'sqft': 18037},
       ...
   }
   ```
2. Include address (from court filing documents) for each owner
3. Note how many of the total are local (within the VIP's jurisdiction)

**Format (present as code block for easy copy):**

```
Respected Sir,

Thank you very much for your time and hospitality today.

As discussed, here are the details of the [X] landowner families whose units are part of the [project] matter:

1. *[Name]* — [Age] yrs — [X] units ([X]%) — [X] sq ft — [Address]
2. *[Name]* — [Age] yrs — [X] units ([X]%) — [X] sq ft — [Address]
...

Total: [X] units, [X] sq ft built-up area.

[X] of the [X] reside at [location] itself — within your jurisdiction.

Happy to share the supporting documents if needed.

Thank you again for your guidance.
```

**Delivery format:** Present as markdown code block (triple backticks, no language tag) for easy selection and copy. No clickable links or deep URLs — the user pastes into their own WhatsApp.

### Phase 7c: Internal Team Document Delivery — WhatsApp with Links

When the deliverable is a structured list of Drive documents for a **team member** (Vinod, Prakash, Anbu, Bhavik, etc.) — not an elder/third-party outreach — use a different WhatsApp format.

**Trigger:** User says "create a WhatsApp message for [team member] with all these documents," "share these docs with [name]," or similar.

**Format — structured document listing with clickable Drive links:**

```
*[Name],*

*As discussed, here are all the [project] [category] documents you asked for. Links below — [access duration]:*

### 🏗️ [Category Group]
1. **[Document Name]** — [Short description]
   → [Link]
2. **[Document Name]** — [Short description]
   → [Link]

### 📄 [Next Category]
3. **[Document Name]**
   → [Link]
...
```

**Delivery format (Nishant preference, Jun 2026):** Present the WhatsApp message as a **markdown code block** (triple backticks, no language tag) so the user can tap to select and copy the entire block. The user pastes it into their own WhatsApp conversation with the recipient.

**Document listing rules:**
- Group documents by category (Plan Sanction, CC, OC, NOCs, Khata, EC, Tax)
- Number each item sequentially (1, 2, 3…) across all categories
- Use WhatsApp markdown: `*bold*` for headings and document names
- Every document needs a clickable Drive link after it
- Add a brief description for each doc (date, purpose)
- Specify access duration at the top: "viewer access valid for 1 week only"
- No sender sign-off needed (the user sends it from their own WhatsApp)
- No URLs to external sites — only Drive links

**Before the WhatsApp message, handle access:**
1. Check current sharing permissions on each document
2. Grant `reader` access to the recipient with `expirationTime` set to 7 days
3. Remove any `anyone` (public) or `domain` access where the current user has permission to delete
4. If the current user cannot delete inherited permissions, note it for the user
5. If the recipient already has `writer` access via folder inheritance, the expiry cannot be set — note this limitation
6. Report access status after the message

**Permission management code pattern:**

```python
from datetime import datetime, timezone, timedelta
expiry = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

# Check and grant
for label, fid in docs:
    perms = drive.permissions().list(fileId=fid, fields='permissions(id, emailAddress, role, type)').execute()
    existing = [p for p in perms.get('permissions', []) if p.get('emailAddress','').lower() == recipient_email.lower()]
    
    if existing:
        # Already has access — note limitation for inherited perms
        if 'inherited' in str(existing[0]):
            print(f"⚠️ {label}: inherited permission — cannot set expiry")
    else:
        # Grant new access with expiry
        drive.permissions().create(fileId=fid, body={
            'type': 'user', 'role': 'reader',
            'emailAddress': recipient_email,
            'expirationTime': expiry
        }, sendNotificationEmail=False).execute()

# Remove public/domain access
for pid in perm_list:
    if ptype in ('anyone', 'domain'):
        drive.permissions().delete(fileId=fid, permissionId=pid).execute()
```

**Access report format (present after the message):**
```
**Access status:**
✅ New access granted (7-day expiry): [doc count]
✅ Already had access (inherited, no expiry set): [doc count]
🚫 Public/domain access removed: [doc count]
⚠️ Could not remove inherited public access (needs file owner): [docs]
```

### Phase 8: Financial Valuation & IPO Readiness Analysis

When the user asks about company valuation, IPO potential, shareholder exit pricing, or comparable company analysis for a private entity — use this phase to extend the dossier with a financial valuation lens.

**Trigger:** User says "what is this company worth," "compare with listed peers," "could this company list," "what multiples apply," "what price for a shareholder exit."

**Workflow:**

1. **Extract Financial Data from Company Documents**

   From balance sheets, P&L statements, valuation reports, and auditor reports available on Drive:

   ```python
   # Key metrics to extract (Rs. Cr)
   historical = {
       'Revenue': {'FY22': 54.4, 'FY23': 114.2, 'FY24': 165.3, 'FY25': 195.0, 'FY26': 284.4},
       'PAT':      {'FY22': 5.4,  'FY23': 6.0,   'FY24': 9.4,   'FY25': 13.8,  'FY26': 25.3},
       'Net Worth':{'FY22': 18.3, 'FY23': 24.4,  'FY24': 46.3,  'FY25': 95.8,  'FY26': 122.4},
       'Total Debt':{'FY22': 86.8,'FY23': 113.7, 'FY24': 153.6, 'FY25': 253.4, 'FY26': 373.6},
       'D/E Ratio': {'FY22': 4.73,'FY23': 4.65,  'FY24': 3.32,  'FY25': 2.64,  'FY26': 3.05},
       'PAT Margin':{'FY22':10.0%, 'FY23':5.3%,  'FY24':5.7%,   'FY25':5.5%,   'FY26':8.9%},
   }
   ```

   For **scanned valuation reports** (no embedded text):
   - Use `pdftoppm` to convert key pages to PNG (table of contents, project-wise tables, value conclusion)
   - Use `vision_analyze` (OCR) on each relevant page
   - Navigate using the report's table of contents → find sections on:
     - Project-wise revenue/gross profit (typically in appendices)
     - DCF methodology and assumptions
     - Market approach / comparable company analysis (if included)
     - Value conclusion and per-share price

2. **Research Comparable Public Companies**

   Search across multiple sources for current trading multiples:

   ```python
   # Sources to check
   sources = [
       'screener.in'    → P/E, P/B, market cap, quarterly results
       'multiples.vc'   → EV/Revenue, EV/EBITDA for sector
       'simplywall.st'  → Forward P/E, analyst estimates
       'ticker.finology.in' → P/E, P/B, market cap
       'stockanalysis.com'  → EV/EBITDA, EV/FCF, trailing & forward P/E
       'tijorifinance.com'  → Quarterly revenue, EBITDA, margin
       'indexpe.in'         → Nifty Realty / sector PE
   ]
   ```

   **Minimum data points per comparable company:**
   - Market Capitalization (₹ Cr)
   - Revenue (latest fiscal year, ₹ Cr)
   - P/E Ratio (trailing)
   - EV/EBITDA (if available)
   - EV/Revenue (if available)
   - P/B Ratio
   - EBITDA Margin
   - Geographic focus / niche

   **Key sector PE benchmarks (Jul 2026):**
   - Nifty Realty Index P/E: **38.4x**, P/B: **4.0x**
   - Indian real estate median EV/EBITDA: **16.2x** (multiples.vc)
   - Indian real estate median EV/Revenue: **6.7x** (multiples.vc)
   - Mainboard IPO median P/E: **22x** (all sectors, IPOPLatform data)

3. **Research IPO / Listing Eligibility Criteria**

   For Indian companies considering a mainboard IPO via SEBI ICDR Regulations:

   | Requirement | Threshold | How to Verify |
   |---|---|---|
   | Net Tangible Assets | ≥ ₹3 Cr in each of 3 preceding years | Balance sheet |
   | Avg Pre-tax Op Profit | ≥ ₹15 Cr (3 of last 5 yrs) | P&L statements |
   | Net Worth | ≥ ₹1 Cr each of 3 preceding years | Balance sheet |
   | Track Record | ≥ 3 years operations | Incorporation date |
   | Min Issue Size | ₹10 Cr (mainboard) | — |
   | Min Public Shareholding | 25% post-IPO (or 10% if mkt cap > ₹4,000 Cr) | — |
   | Sector-specific | RERA compliance, land bank at current (not projected) value, credit rating | Management reps, RERA portal |

   **Alternative route:** If profitability criteria not met, QIB route requires 75% of offer to QIBs.

4. **Apply Valuation Methodologies**

   Use **at least 3 approaches** for triangulation:

   **a) P/E Multiple Method:**
   ```
   Equity Value = PAT × P/E
   Scenarios: Conservative (15-18x), Moderate (20-25x), Optimistic (28-35x)
   ```

   **b) EV/EBITDA Method:**
   ```
   EBITDA = PAT + Tax + Interest + Depreciation
   Enterprise Value = EBITDA × EV/EBITDA multiple
   Equity Value = EV − Total Debt + Cash & Investments
   Scenarios: Conservative (10-12x), Moderate (14-16x), Optimistic (18-22x)
   ```

   **c) EV/Revenue Method** (for high-growth / pre-profit companies):
   ```
   EV = Revenue × EV/Revenue multiple
   Equity Value = EV − Total Debt + Cash & Investments
   Scenarios: Conservative (1-2x), Moderate (2-4x), Optimistic (4-6x)
   ```

   **d) Market Approach (Existing Valuation Report):**
   - If an IBBI-registered valuer's DCF report exists, use it as the anchor
   - The DCF gives the **private, controlling-basis value**
   - IPO listing would add a **liquidity premium** (typically 2-4x private value)

5. **Assess Feasibility & Timeline**

   Build a checklist against SEBI criteria and flag:
   - ⚠️ Items that need verification (RERA compliance, land bank docs, credit rating)
   - ❌ Items that fail (revenue too small, leverage too high, litigation)
   - ✅ Items already satisfied

   **Size guidelines for mainboard IPO:**
   - Revenue: typically ₹500 Cr+ minimum for credible listing
   - Several recent IPOs at ₹300-500 Cr revenue range but face higher scrutiny
   - Suggest 2-3 year growth runway if below ₹500 Cr

6. **Present the Analysis**

   Structure the report:

   ```
   1. COMPANY SNAPSHOT — revenue, PAT, net worth, D/E, growth CAGR
   2. PROJECTIONS (if available) — revenue pipeline, EBITDA margins
   3. COMPARABLE TABLE — peer companies with their multiples
   4. VALUATION RANGES — 3 methodologies × 3 scenarios
   5. KEY PRECEDENT — most similar recent IPO (same city/segment)
   6. LISTING READINESS — SEBI criteria checklist
   7. CHANCES & TIMELINE — realistic outlook
   8. LIQUIDITY PREMIUM — private valuation vs potential IPO valuation
   ```

**Pitfalls:**
- Scanned valuation reports may have internal page numbers differing from PDF page numbers — navigate by finding the TOC first, then converting ±5 pages around each listed appendix
- The `gws_skill_bridge.drive_search()` wraps queries in `fullText contains '...'`, breaking compound queries like `'folder_id' in parents` — use `raw_query=True` when the bridge supports it, or fall back to `gws_auth.build_service('drive', 'v3')` for direct API calls
- Comparable company multiples from different sources may use different fiscal periods — note the period clearly (e.g., "trailing P/E as of Jul 2026 based on FY26 results")
- Projections in management-prepared documents (PFI) are not independently verified — the valuer's DCF report usually includes an assessment of reasonableness
- Real estate companies recognize revenue under POCM (Percentage of Completion Method) — EBITDA and cash flows can diverge significantly; prefer EV/EBITDA over P/E for real estate

## Reference Files

- `references/comparable-real-estate-multiples-jul2026.md` — Comparable Indian real estate company trading multiples, Nifty Realty PE, and median sector EV/EBITDA as of July 2026. Refresh periodically before reuse.

## Pitfalls

- **Dual-source discovery: Drive vs Web.** When the user names a project/entity, determine whether it's an internal DRAAS project (search Drive + Gmail) or an external developer's project (search the web). Signal: if the user names a known developer (Assetz, Prestige, Sobha, etc.) or the name sounds like a branded project, default to web search first. If you start with the wrong source, the user will correct you — that's the signal to switch immediately. Rule: don't report "not found" from Drive when the source is a public project; search the web.
- **Name variants matter.** Search at least 3-5 variants of the same entity. The user says "also called X, Y, Z interchangeably" — use ALL of them.
- **Don't ask the user to clarify aliases they already gave.** They're telling you the variants. Use them — don't ask "do you mean X or Y?"
- **Recent emails > old documents.** The Gmail thread from last week tells you current status. The court order from 2023 tells you the legal baseline.
- **Drive file deduplication.** The same file appears under multiple search terms. Deduplicate by file ID.
- **Document count vs relevance.** 100+ documents found does not mean 100+ need to be read. Read the summaries/analyses first (Facts Compilation, Brief Note), court orders second, original deeds third.
- **Financial figures may differ across sources.** Loan principal vs outstanding vs claimed amount — cite the source and note if there's a discrepancy.
- **Landowner families are large.** One family member dying mid-proceeding means legal heirs get substituted (e.g., D5 → D5a+D5b). Track this in the briefing note.
- **Third-party message tone.** Do NOT use legal jargon with a community elder. Do NOT quote case numbers or sections. Keep it to plain language — "loan", "dispute", "settle".
- **Phone number for WhatsApp links.** The user may not have the intermediary's number in the contacts sheet. Ask the user directly rather than searching fruitlessly.
- **GWS session user mismatch.** Always run a pre-flight identity check before Drive/Gmail searches:
  ```python
  gmail = build_service('gmail', 'v1')
  profile = gmail.users().getProfile(userId='me').execute()
  authed_user = profile.get('emailAddress')
  # Confirm matches the user you're chatting with
  ```
- **Internal docs — inherited permissions cannot be expired.** When the recipient already has `writer` access to a file via folder inheritance (not a direct permission), the Drive API cannot set `expirationTime`. The user must either create a copy for time-limited sharing, or the file owner must change the parent folder permissions. Log this in the access report — don't silently fail.
- **Internal docs — public access may be inherited from parent folders.** Removing `anyone`/`domain` permissions fails with `cannotDeletePermission` when the current user is not the file owner and the permission is inherited. Note which files still have public access and who the owner is so the user can follow up.
- **Google Docs API — sequential `insertText` at index 1 REVERSES the document.** When building a long analysis/briefing doc section-by-section with `batchUpdate`, inserting each section at `{'location': {'index': 1}}` PREPENDS it, so the final doc reads bottom-to-top. Track a running end index (`idx = end` after each inserted section) and append sequentially. Read the doc back to verify order before delivering. (Hit Jul 2026 on the Lilac Insights deep-dive doc — rebuilt once; see `references/whatsapp-export-intake.md` Pitfalls.)
- **Legal entity name ≠ colloquial name in chat.** For investment dossiers, the chat/user name ("Lilac Capital") may not be the registered company name ("Lilac Insights Pvt Ltd"). The legal name usually appears in Gmail subject lines and contracts; search it explicitly — it typically returns the most hits and is the correct name for folder/analysis titles.
- **Ignore non-BBMP/non-approval docs in the WhatsApp message.** When listing documents for an internal team member about BBMP approvals, skip marketing materials, interior photos, contractor WO's, cost sheets, and unrelated items. Only include the approval/compliance documents the recipient asked for.
- **Named party in a voice-note query may be a transcription error.** When the user dictates a document request and a person name (e.g. "Ayaz") returns zero relevant hits in the matter's context AND the real counterparty is deceased / estate-held / a family group, the name is almost certainly mis-heard — most often "heirs" or a garbled family-bearing initial pair. Do NOT fabricate the person or the document. Confirm the undertying relationship from statutory records (incorporation certificate is the strongest anchor), state the literal doc wasn't found, and ask the user to confirm the exact wording before concluding. See `references/corporate-statutory-document-search.md`.

## Related Skills
## Related Skills

- `gws-automation` — Drive, Gmail, Docs API access
- `messaging-drafts` — WhatsApp and email drafting
- `clinical-dossier` — Medical-specific dossier creation (this skill is the business/general counterpart)
- `legal-document-drafting` — Drafting legal documents from gathered intelligence
- `google-doc-formatting-template` — Creating well-formatted Google Docs via HTML import
- `private-investment-due-diligence` — HNI venture-debt/private-credit DD on startup investment pitches (devil's-advocate HTML report, structure & enforceability); use when the user is evaluating a company's investment ask rather than a legal/land matter

## Reference Files

- `references/gmail-archival-property-search.md` — Gmail search strategies for property/entity archival research
- `references/project-file-inventory-non-seed.md` — Drive file/folder inventory from project name variants
- `references/seed-document-discovery-workflow.md` — Starting from a seed document to find all related files
- `references/marketing-collateral-gap-analysis.md` — Evaluating investor marketing video + deck against a strategic brief; transcribe, visually analyze, read companion deck, research brand, produce gap analysis with deep reasoning model
- `references/legal-document-intake-research-update.md` — Full intake-to-research-note pipeline for legal documents received via Telegram: duplicate checking against Drive, renaming, filing in proper subfolder hierarchy (TMP → Enforcement Suit / Transaction Documents / etc.), multi-agent parallel analysis via delegate_task, and compiling all findings into an updated briefing note. Includes folder ID references for the Veracious/Vani Vilas case structure.
- `references/vip-post-meeting-whatsapp.md` — WhatsApp message composition for a VIP/MLA after an in-person meeting: thanking for hospitality, sharing structured landowner data (names, addresses, units, sq ft), tone rules for elected representatives vs community elders.
- `references/insurance-dispute-evidence-compilation.md` — Insurance/policy dispute investigation: Gmail thread analysis → evidence cataloguing with message IDs → parallel legal research via OpenRouter → structured HTML legal brief with violation mapping and 30-day action plan
- `references/investor-agreement-allocation-discovery.md` — Finding unit allocation details from executed investor agreements for real estate projects: Drive search strategy, referral sheet tab structure, executed vs pending distinction, data model for villa size/facing/rate, scraped-pdf limitations.
- `references/person-centric-task-compilation.md` — Compile ALL emails with a specific person, extract every task/assignment, organize by project, cross-reference with Kelsa. Follow when user says "find all my messages with [person] and list everything I've asked them to do."
- `references/whatsapp-export-intake.md` — WhatsApp chat export zip intake: unzip pattern, .txt format parsing, extraction priorities (corrected numbers > raw claims), media classification, Gmail cross-referencing via in-chat email addresses, `Personal / <Investment> / 01-04` folder convention for personal financial investments, Gmail sweep filtering (dedupe by ID → filter by entity name), attachment dedupe by byte size, email-only updates → .txt, and post-upload consolidation of pre-existing Drive files. Verified end-to-end on Lilac Insights / Rajiv Dadlani (Jul 2026) — legal entity name differs from chat name; search the legal name.
- `references/corporate-statutory-document-search.md` — Finding a specific legally-scoped corporate document (e.g. an NOC / registered-office consent issued by named parties to a company for using a premises as its registered office). Confirm the premise from the company's own Certificate of Incorporation (CIN + ROC registered-office address, "pursuant to change of name" history), read the ROC/CS compliance-thread bodies (registered-office/reconstitution/director-change consents live there), match the premises unit no. to the property deed, and apply the voice-transcription-error disambiguation rule before concluding "not found".
