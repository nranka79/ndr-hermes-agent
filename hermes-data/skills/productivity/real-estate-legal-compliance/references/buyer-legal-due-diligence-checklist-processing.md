# Buyer Legal Due Diligence — Advocate Requisition Checklist Processing

**Status:** Working pattern, confirmed Jul 2026 (Assudani → Serenity Hillview Sy.93/2).

## When to use

A buyer/assignee engages a lawyer to conduct legal due diligence on a target property. The lawyer produces a numbered checklist/requisition list (typically 15-50 items) asking for title deeds, revenue records, conversion orders, trust documents, etc. The task is to:

1. Check every item against the Drive inventory
2. Create a tracking spreadsheet with hyperlinks to available documents
3. Report what's missing and follow up with relevant parties

## Workflow

### Phase 1: Ingest the checklist

The checklist typically arrives as a scanned PDF or email attachment. Extract all items:

```bash
pdftotext checklist.pdf /tmp/checklist.txt
# Then read the text, parse into numbered items
```

Each item has a description, document reference number, dates, and parties. Parse accurately — the lawyer's numbering is the master key.

### Phase 2: Multi-phase Drive search

**Scanned title deed → legal opinion fallback pattern**

Many registered sale deeds (especially pre-2010) are scanned PDFs with **no selectable text layer** — pymupdf extracts 0 chars. When pymupdf reports zero text on all pages:

```python
import fitz
doc = fitz.open('/tmp/deed.pdf')
for i, page in enumerate(doc):
    print(f'Page {i+1}: {len(page.get_text())} chars')
# → Page 1: 0 chars, Page 2: 0 chars, ... (image-only PDF)
```

**Fallback — use the Legal Opinion Google Doc.** The legal opinion (prepared by the advocate who reviewed the originals) almost always quotes the property schedule **verbatim** from the sale deed, including:

- Survey number, village, taluk
- **Total extent** as per the deed
- **Kharaab breakdown** (regularized A Kharab, B Kharab/canal)
- **Regular/non-kharaab extent**
- Boundaries (N/E/S/W)
- Conversion order reference

The legal opinion is typically a **native Google Doc** (text-searchable, readable via `docs_get` bridge). Use the bridge to extract the data:

```python
from tools.gws_skill_bridge import call

opinion = call("docs_get", service_name="google-draas",
               doc_id="DOCUMENT_ID")  # NOT document_id — uses doc_id
# Returns: {"title": "...", "documentId": "...", "body": "full text..."}
```

The property description is usually in a clear paragraph in the "Property Description" or "Schedule Property" section. Parse the body text for extent, kharaab, and boundary clauses.

This was verified on Serenity Hillview Sy.93/2 (Jul 2026): the sale deed PDF from Muddasar Pasha to GBJT was image-only (9 pages, 0 chars each). The legal opinion Google Doc (`20250520 Serenity Hill View - Legal Opinion`) contained the exact property schedule with total extent (6A 28G including 02G regularized A Kharab = 6A 26G net).

**2a — Identify all relevant folders first**

Search for ALL name variants the project/land is known by — these typically include the trust name, the project name, the survey number, village name, and any partnership entity:

```python
from tools.gws_skill_bridge import call as gws
import json

terms = [
    "Godwad Bhawan Jain Trust", "GBJT", "Serenity Hillview", 
    "Hurulugurki", "Hurulagurki", "Huralagurki",
    "Redsol", "Red Sol", "Red Soul Farmers",
    "Sy.93/2", "Sy 93", "Survey 93"
]

for term in terms:
    # Search folders
    r = gws("drive_search", service_name="google-draas", raw_query=True,
            query=f"name contains '{term}'", max=50)
    data = json.loads(r)
    for f in data:
        print(f"{f.get('mimeType','')} | {f.get('name','')} | {f.get('id','')}")
```

**2b — Search by title document numbers**

The lawyer's checklist often references specific registered document numbers. Search for those:

| Pattern | Query |
|---------|-------|
| Exact doc number | `name contains '686'` |
| Doc with year | `name contains '1043' and name contains '1975'` |
| Sale deed search | `name contains 'Muddasar'` |
| Legal opinion | `name contains 'Legal' and name contains 'Opinion'` |

**2c — Check for existing file index**

The project may already have a file index spreadsheet (e.g., Godwad Bhavan file index with 1,064 rows). Read it fully and search for each checklist item across the index:

```python
r = gws("sheets_get", service_name="google-draas",
        sheet_id="FILE_INDEX_SPREADSHEET_ID", range="A:F")
data = json.loads(r)

# For each checklist item, search the index rows
for row in data:
    full_text = " ".join(str(c) for c in row).lower()
    if search_term.lower() in full_text:
        # Found a match — extract the Drive link from column F
        link = row[5] if len(row) > 5 else ""
```

**2d — Cross-account search**

For multi-account users (Nishant has google-draas, google-ahfl, google-gmail), check ALL accounts with the same searches.

**2e — Client-shared legal folder (CRITICAL)**

When the buyer/vendor or their team shares a Google Drive folder link (e.g., `https://drive.google.com/drive/folders/1t335m5vJcYJmCMwmc3D38t1_qrTwCCGX`), **browse it explicitly**. Do NOT rely on full-text Drive search to find documents in shared folders — they often don't index properly:

```python
# List ALL files in the shared folder by parent folder ID
folder_id = extract_folder_id(url)  # e.g., "1t335m5vJcYJmCMwmc3D38t1_qrTwCCGX"

# Search by parent — raw_query=True is essential
r = gws("drive_search", service_name="google-draas", raw_query=True,
        query=f"'{folder_id}' in parents", max=100)
data = json.loads(r)

for f in data:
    print(f['name'], f['webViewLink'], f['mimeType'])
```

This folder often contains every scanned document the client has — and many items that were "Not Found" in your own Drive search may be sitting here. In the Jul 2026 Assudani session, the shared legal folder revealed:
- **Original JDA** (06.04.2021, 26 pages) — not found by any `fullText contains` search
- **EC from 1948 to 1980** — hidden in a shared folder, not in user's Drive tree
- **Nil Tenancy Certificate** (labeled "NIL PTC.pdf") — not found by descriptive term search

Always ask: *"Do you have a Drive folder or link where the scanned documents are shared?"*

**2f — Full re-verification on every new source**

When a new source arrives (shared folder, file index, Bharat's scanned set, Vinod's set), re-verify ALL 35 checklist items — not just the ones previously marked "Not Found." Reasons:

- The spreadsheet status may be **stale** — docs found earlier may still show "Not Found" (the cancellation of GPA had a Drive link in the sheet but was marked "Not Found" — the status was never updated after the link was added)
- Items marked "Available" may only have a **cancellation deed** while the **original document** is still missing (e.g., original JDA was missing but cancellation of JDA was found — the difference matters for the title chain)
- The new source may have **higher quality copies** or **certified versions** of documents already marked as found

Method: read the full spreadsheet, walk through every row, and for each item check:
- Is the status correct given everything we now know?
- If a link exists, does it point to the correct document type?
- If a cancellation deed exists, does the original also exist separately?

### Phase 3: Build the tracking spreadsheet

Create a spreadsheet with these columns:

| Sl.No | Checklist Item Description | Status | Document Available | Drive Link | Notes |
|-------|---------------------------|--------|-------------------|------------|-------|
| 1 | Sale deed 21.05.1974 (686/74-75) | Available | ✅ | https://... | Found in file index |
| 4 | JDA 06.04.2021 (DNH-1-00527) | Not Found | ❌ | | Need to obtain |

**Working recipe:**

```python
result = gws("sheets_create", service_name="google-draas",
            title="Buyer Name - Legal Due Diligence - Project Name - Checklist Tracker",
            sheet_name="Checklist")

# Populate
header = ["Sl.No", "Description", "Status", "Document Available", "Drive Link", "Notes"]
rows = [header] + checklist_data
result = gws("sheets_update", service_name="google-draas",
            sheet_id=spreadsheet_id, range="A:F",
            values=json.dumps(rows))  # values MUST be JSON string
```

The spreadsheet is created at Drive root — move to TMP per Nishant's convention:

```python
from tools.gws_auth import build_service
service = build_service("drive", "v3", service_name="google-draas")
file = service.files().get(fileId=spreadsheet_id, fields="parents").execute()
service.files().update(
    fileId=spreadsheet_id,
    addParents="TMP_FOLDER_ID",
    removeParents=",".join(file.get("parents", [])),
    fields="id,parents"
).execute()
```

### Phase 3.5: Expand composite items into sub-rows

Some checklist items bundle multiple documents under one line item (e.g., "MR 1/1975-76, MR 81/2004-05, MR 42/2006-07, MR H.29/2018-19"). **Always expand these into individual rows** — one per distinct document. Do not leave the item as a vague "Partial."

**When to expand:**
- Item says "MR 1, MR 81, MR 42, MR H.29" → 4 sub-items
- Item says "Akar Band, RR BalaBadi, Hissa Tippni, Atlas, Moola Tippni" → 5 sub-items
- Item says "Tax paid receipts till date" → each available receipt gets its own row + one "Latest (not found)" row
- Item says "Trust documents: Deed, PAN, Regn Certificate, Trustees list" → 4 sub-items

**How to expand:**

1. **Update the original row** to show the summary status and a note pointing to the expanded rows:
   ```
   Status: Available (info) / Partial / Available
   Notes: "Expanded below — see rows 36-39"
   ```

2. **Append sub-rows at the bottom of the spreadsheet** using `sheets_append`:
   ```python
   r = gws_call("sheets_append", service_name="google-draas",
                 sheet_id=spreadsheet_id, range="A37:G41",
                 values=json.dumps([
                   ["11a", "MR 1/1975-76 (Sy.93)", "Available", "✅", "https://...", "MR 1(75-76).pdf in legal folder"],
                   ["11b", "MR 81/2004-05 (Bifurcation)", "Not Found", "❌", "", "Not located on Drive"],
                   ["11c", "MR 42/2006-07 (Sy.93)", "Available", "✅", "https://...", "Mr no.42 2006.2007.pdf in legal folder"],
                   ["11d", "MR H.29/2018-19 (Sy.93)", "Available", "✅", "https://...", "MR H29 2018-2019.pdf in legal folder"],
                 ]))
   ```

3. **Prefix the Sl.No** with the parent item number + letter (e.g., 11a, 11b, 11c, 11d). This keeps the reference traceable to the original checklist numbering.

4. **For tax receipts, also expand** — list each individual receipt found (patta books, payment receipts by year) as a separate row, and mark the latest year explicitly as "Not Found" with a note that it may be unpaid. The user wants to see exactly what exists, not a vague "Partial."

### Phase 4: Gap analysis & follow-up

For items NOT found on Drive, classify by likely source:

| Category | Typical Source | Example |
|----------|---------------|---------|
| **Original scanned set** | Party who scanned the physical files (e.g., Bharat Hawaldar for DRA) | JDA, cancellation deeds, conversion orders |
| **Lawyer's own set** | The conveyancing lawyer who prepared the legal opinion | They reviewed ALL documents to form the opinion |
| **Court records** | District court / High Court | Misc. petitions, OS suits |
| **Government office** | Sub-Registrar, DC, Tahsildar | ECs, conversion orders, nil tenancy certs |

**Follow-up messages:**

1. **To the person who scanned the original files** (vendor's team/employee):
   - "I remember the original files were scanned but I can't find [specific docs] on Drive. Can you share a Drive link to whatever scanned set you have?"

2. **To the lawyer who prepared the opinion** (they reviewed all docs):
   - Specific list of only the genuinely missing items (NOT all items — just the ones that survive exhaustive search)
   - Concrete template (verified Jul 2026 for Vinod Kumar Das, +91 99000 93813):

```
Hi Vinod, regarding the Hurulugurki Sy.93/2 (Godwad Bhavan Jain Trust / Serenity Hillview) legal opinion you prepared — I'm trying to locate a few specific documents from the scanned set that you would have reviewed. Could you check if these are available on your end?

1. Application under Section 11E
2. Misc. Petition No. 210/2026 & order sheet
3. O.S./4595/2026 pending before PRL City Civil Court CCH-1

If you have these scanned or a Drive link to the full set, please share. Thanks!
```

3. **For items that need procurement** (government/court):
   - Note as procurement action for the buyer's team

### Phase 5: Update the spreadsheet when new docs arrive

When Bharat or Vinod shares new documents, update individual cells:

```python
result = gws("sheets_update", service_name="google-draas",
            sheet_id=spreadsheet_id,
            range="E5",  # Just the cell, no sheet prefix needed
            values=json.dumps([["✅"]]))
```

Range works with or without sheet name prefix — the bridge auto-resolves to the first sheet.

## Pitfalls

- **Search all name variants** — The same property may be stored under the trust name (Godwad Bhavan Jain Trust), project name (Serenity Hillview), survey number (Sy.93/2), village name (Hurulugurki), or partnership name (RedSol Farmers Collective). Missing one alias = missing documents.
- **Existing file index may exist** — Always check for a pre-existing document index spreadsheet before doing exhaustive individual searches. The Godwad Bhavan file index had 1,064 rows covering most title and revenue documents.
- **Documents may be in multiple locations** — The same document (e.g., BIAAPA conversion order) can appear in the Nandi Hills property folder AND in root-level Drive. Check both.
- **"True copy" ≠ certified copy** — The buyer's lawyer asks for "True copy" but any copy (photocopy, scan) is sufficient for the checklist — don't block on certification. Mark as available with whatever copy exists.
- **Cancellation deeds don't need the original** — If you find the cancellation of JDA (Doc 17151/2023-24) but NOT the original JDA (DNH-1-00527-2021-22), the cancellation deed proves the original existed — but the original JDA itself is still needed for the title chain.
- **Sheets `values=` must be JSON string** — The bridge calls `json.loads(args.values)`. Pass `values=json.dumps(data)`. A Python list will silently crash.
- **Move to TMP** — All new artifacts go to TMP first (Nishant's convention). Don't leave them at Drive root.
- **User preference for message style** — When messaging third parties for docs: direct, no pleasantries, bullet list of what's needed, be specific about document references (dates, registration numbers).
- **Shared folder full-text blind spot** — Google Drive `fullText contains` does NOT index all documents in folders shared by another user. The file listing of the shared folder (by parent ID) will show documents that full-text search misses. Always enumerate the folder explicitly when a client shares it.
- **Stale spreadsheet statuses** — After each round of searching, the spreadsheet's "Status" column may be outdated. A document link may exist in the "Drive Link" column while "Status" still reads "Not Found". After every new search, re-read the entire sheet and verify every row — don't just update the rows you touched.
- **Sheet name is NOT always "Sheet1"** — The Assudani tracker's sheet was named "Checklist". Use `range="D5"` (no sheet prefix) to avoid parsing errors. The Sheets API auto-resolves to the first sheet.
- **Cancellation deed ≠ original** — Finding a cancellation of JDA (Doc 17151/2023-24) proves the original JDA existed, but the original itself is still a separate checklist item. If the original is missing, the title chain has a gap even though the cancellation deed exists. Mark as two separate items in the spreadsheet.
- **Partial ≠ Not Applicable** — Reserve "Partial" for items where the document exists but we lack a complete version or specific components (e.g., EC covering most but not all of the requested period). Use "N/A" when the requested document was never created because the underlying approval/event never occurred (e.g., BIAAPA layout sanction where the layout was never sanctioned). The labels are distinct — the user relies on them to know whether further search is needed vs the item being irrelevant.
- **Follow-up routing by document owner** — Sending one combined message to a single person is wrong when the gaps sit with different parties. The lawyer (Vinod) can only help with items from the scanned legal set he reviewed. Trust documents (amended trust deed, PAN, registration certificate, trustees list) must go to the trust representatives (Vikram Ji via Manohar Singh). Always identify the natural holder of each missing document before drafting follow-up messages.
- **Uploaded document handling** — When the user shares a missing document as a file (PDF attached to Telegram), immediately: (1) rename to `YYYYMMDD_DescriptiveName.pdf`, (2) upload to the project's shared legal folder (NOT Drive root), (3) update the spreadsheet in a single action (status→Available, emoji→✅, Drive link, notes), (4) report the new count showing the remaining gap shrinks. Do not leave the file in the cache or ask what to do with it. Example: `20260715_Misc_Petition_210_of_2026_Godwad_Bhawan_Jain_Trust_entire_file.pdf`.
- **Explain every partial with specific reasoning** — The user will ask "why is it partial?" for each one. Preempt this by including the exact reason in the Notes column (e.g., "EC is 18 days short of the requested period — we have up to 13.03.1977, lawyer asked for 31.03.1977"). Never leave partial items unexplained.
- **Partial vs N/A — user will correct you** — These are distinct classifications. "Partial" means the document exists in some form but the checklist item requires more than we have (e.g., EC covering most but not all of the requested period). "N/A" means the requested document was never created because the underlying event never happened (e.g., BIAAPA layout sanction was never issued because the JDA was cancelled and layout never pursued). The user relies on this distinction to know whether further search is needed vs the item being irrelevant. Using them interchangeably wastes his time.
- **WhatsApp number hygiene** — Always use the `whatsapp_link` tool to generate WhatsApp URLs. Manually typing phone numbers into URLs risks dropping digits (one zero in a 10-digit number changes the recipient). The tool validates the format and generates correct links. Verify the number in the contacts sheet before sending.
- **Scanned PDF has no text layer — pymupdf returns 0 chars** — Registered sale deeds, JDA copies, and trust documents submitted as scans almost always lack a text layer. Check with `fitz.open(path)` and `page.get_text()` before concluding a document is "empty." The correct response is NOT to report "no data" — search for a legal opinion Google Doc that quotes the deed's property schedule verbatim. See Phase 2 fallback pattern above.
- **Every item needs its OWN direct Drive link** — NEVER say "in the folder", "available in the Serenity Hillview folder", or any vague folder reference when presenting the tracker/spreadsheet/email. Every single item must have its own direct file link. If a composite item (e.g., "Patta Books") comprises multiple individual documents (patta book Sy.93, lod patta 801, patta & receipt 2020-21, patta book 153, receipt patta 1992-99), list EVERY one with its OWN link. The user will reject any delivery that says "in folder" — the exact correction was: *"instead of giving a link to the patta book, we have said it's in Serenity Hillview Folder. That's not what we want to do. We want to expand the patta book into all the items, patta book related items that we have and for each item provide a link."* This applies to ALL items (RTCs, ECs, pattas, MRs — anything that's a multi-file category). The only acceptable "in folder" reference is the tracker spreadsheet link itself and the parent project folder — individual checklist items NEVER get vague references.
- **Drive sharing with non-Google accounts requires `notify=True`** — When sharing a file/folder with someone whose email is not a Google account (e.g., rovinod@advocatev.in), `notify=False` returns a 400 error: *"As there is no Google Account associated with this email address, you must tick the 'Notify people' box."* Always set `notify=True` for non-Gmail addresses. For Gmail addresses, `notify=False` works fine.
- **Batch-sharing individual files** — After the spreadsheet is built and before sending the email, share EVERY file referenced in the spreadsheet individually with both recipients (the lawyer and the CC'd partner). Use a loop over all unique file IDs. Share with the Gmail recipient first (`notify=False`), then the non-Google recipient (`notify=True`).

### Phase 6: Draft the response email to the lawyer

After the spreadsheet is complete and all files shared, draft an email to the lawyer with an HTML table of all available documents. This is the primary deliverable — the lawyer uses it to access the documents.

**Key rules:**
- Exclude items NOT found. Do NOT list missing items or say "not found" — only show what exists. The user's instruction: *"what is not found, don't include it in that email. Let's not even include it to say not found."*
- For N/A items (like BIAAPA layout never sanctioned), include a separate note explaining why.
- Every listed item must have its own direct Drive link (see above).
- Use a styled HTML table with alternating row colors, proper header, and a professional layout.
- CC the internal partner (Nishant Prakash) who will coordinate with the lawyer.

**Working recipe:**

```python
html_body = \"\"\"<!DOCTYPE html>
<html><head><style>
  body { font-family: Arial, sans-serif; }
  table { width: 100%; border-collapse: collapse; }
  th { background: #283593; color: white; padding: 10px; text-align: left; }
  td { padding: 8px; border-bottom: 1px solid #e0e0e0; }
  tr:nth-child(even) { background: #f5f5f5; }
  .note { background: #fff3e0; border-left: 4px solid #ff9800; padding: 12px; margin: 16px 0; }
  a { color: #1565c0; }
</style></head><body>
[TABLE HERE]
</body></html>\"\"\"

draft = gws_call("draft_create", service_name="google-draas",
    to="lawyer@example.com",
    cc="partner@example.com",
    subject="Project Name — Legal DD Documents as per your checklist dated DD.MM.YYYY",
    body=html_body, html=True)
```

**Include these in the email footer:**
1. Viewer access note: "You have been granted viewer access for 1 month. Please download documents for your records."
2. Original verification offer: "For original document verification, coordinate with [partner name] (CC'd) to arrange a physical verification at any time."
3. Link to the tracker spreadsheet for reference.

### Phase 7: Coordinate originals collection

After the digital deliverable is sent, the lawyer may request physical originals. Coordinate through WhatsApp:

1. **WhatsApp to the internal partner** (Nishant Prakash) — asking them to coordinate with the trust representative to collect all physical originals using the checklist as the reference
2. **WhatsApp to the intermediary** (Manohar / who knows the trust representative) — same message, routed through their connection to the trust

**Key framing:** "Since substantial sum has already been paid, please request [trust representative] to hand over all property originals. Use the entire checklist to collect all originals."

Template (verified Jul 2026 for Nishant Prakash + Manohar → Vikram Ji / GBJT):

```
Chief — Now that the legal DD tracker for [Project] is ready ([N] of [M] items compiled with links), we need to collect all the original property documents from [Trust/Entity]. Since substantial sum has been paid already, please coordinate with [intermediary] to reach out to [trust representative] and request handover of all originals. Use the checklist as the reference — collect every document we have listed.
```

