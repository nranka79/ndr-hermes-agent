# Plot-Level Legal Document Set Creation from Source Deed

**Class:** Real Estate Legal Compliance — Document Drafting  
**Trigger:** User provides a source Sale Deed (e.g., Plot 65 for Nishant Prakash) and asks you to create derivative legal documents for a new plot (e.g., Plot 119 for a new allottee), based on that source.  
**Verified:** Ranka Oasis, Plot 119 (Jul 2026) — 3 documents produced: Agreement for Sale, Construction Agreement, Combined Agreement.

---

## Workflow

### Phase 1: Source Review & Red Flag Identification

1. **Read the source Sale Deed** thoroughly — it's the template for party details, recitals, clauses, and legal structure.
2. **Identify red flags** against supporting documents:
   - Dual representation (same entity represented by two different people)
   - Missing TNRERA registration number (mentioned in deed but not yet received)
   - Scope ambiguity (₹2,000/sqft — plot only or includes construction?)
3. **DO NOT modify the source document.** Cross-check supporting docs (PAN, CIN, Reconstitution Deed, JDA) from Drive.
4. **Log all findings** — they go in the Resources Reference document later.

### Phase 2: Document Creation

Create three derivative documents per plot:

| Document | Template Source | Key Content |
|----------|----------------|-------------|
| **Agreement for Sale** | TNRERA standard format + source deed structure | Party details (from source), plot data, payment schedule blank |
| **Construction Agreement** | Investment Letter specs + villa plan | BUA/carpet breakups, room dimensions, finishing specs (Kohler/Grohe, Asian Paints, Fenesta) |
| **Combined Agreement** (optional) | Combined template (e.g., Inara AOS) | Merged Sale + Construction structure |

**For each document:**
- Replace "Apartment" with "Villa" throughout
- Keep pricing blanks until user provides
- Fill plot-specific data (dimensions, boundaries, plot no.)

### Phase 3: Formatting with Proper Tables ⚠️ CRITICAL

**User preference (Bharat):** Legal agreements must have professional tabular formatting — NOT continuous text. Schedules, payment plans, specification annexures, room breakups all go in clean tables.

**The .docx upload approach (preferred for new docs with tables):**

1. Build the document content with python-docx, creating proper table structures for:
   - Schedule C (Built-up area / Carpet area breakup) — GF/FF/TF room-wise dimensions
   - Schedule D (Payment schedule) — stage-wise milestones as rows
   - Annexure (Finishing specifications) — 2-column tables (Item | Specification)
   - Signature blocks — multi-column party signing areas

2. Upload the .docx to Drive with `mimeType='application/vnd.google-apps.document'` — the conversion preserves table formatting.

3. Apply remaining text fixups via Docs API `replaceAllText` or `batchUpdate`.

**Alternative: HTML import approach** (from `google-doc-formatting-template` skill) — use when the document has design-heavy elements (colored headers, callout boxes).

### Phase 4: Filling Allottee Details

Use Google Docs API `batchUpdate` with `deleteContentRange` + `insertText`:

```python
requests = [
    {"deleteContentRange": {"range": {"startIndex": S, "endIndex": E}}},
    {"insertText": {"location": {"index": S}, "text": new_text}}
]
docs_svc.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
```

**Critical pitfall — index shifting:** Google Docs API indices shift after every `batchUpdate` call. ALWAYS read fresh document indices between batch updates. Never reuse indices from a previous read. The pattern is:

1. Read doc → find all placeholder positions → build ONE batch update for all replacements
2. If the batch fails or needs more edits → re-read the document to get NEW indices
3. Do NOT try to "adjust" indices manually — they shift unpredictably

**Placeholders to fill across all documents:**
- Allottee party block (name, age, spouse, address, Aadhaar, PAN)
- Allottee label in notice clause (Clause 17 addresses)
- Signature block (under "Allottee:" line)
- Any "[Allottee Name]" or "[Allottee Address]" occurrences

### Phase 5: Drive Organization

1. **Create a project subfolder** under the main project folder: e.g., `Ranka Oasis / Plot 119 Legal Set`
2. **Move all derivative documents** into this folder (use `addParents` + `removeParents`)
3. **Remove duplicates** — if an older unformatted version exists, remove it from the folder
4. **Create a Resources Reference document** inside the same folder

### Phase 6: Resources Reference Document

Create a Google Doc inside the folder listing:

- **Final documents** with direct Drive links (one per document)
- **Reference resources** with URLs:
  - Source Sale Deed
  - Villa Layout Plan (with architect, drawing ref, date)
  - Combined Agreement Template (if used)
  - Master Inventory Sheet
  - Investment Letter / construction specs
  - Reconstitution Deed (vendor partnership)
  - JDA (title chain)
- **Pending items** still blank (pricing, TNRERA, building permit, timeline)
- **Red flags** identified during review

This ensures traceability — anyone opening the folder knows exactly what went into each document.

---

## Pitfalls

### Google Docs API Index Instability

The most common error across multiple session turns. Each `batchUpdate` call shifts all subsequent indices. Symptoms:

- `deleteContentRange` removes wrong content
- `insertText` appears in wrong location
- Placeholders persist despite successful-looking API replies

**Solution:** Every batch update must use indices from the SAME read call. If you need a second batch, re-read the entire document first.

### Duplicate Document Versions

When creating a formatted version via .docx upload:
- The upload creates a NEW Google Doc with a new ID
- The old version (without proper tables) remains in Drive
- Remove the old version from the target folder so only the formatted one stays

### Inara Template Not on Drive

Combined agreement templates (e.g., Inara Phase 1 Villa 10 AOS.pdf) may have been accessed via temporary shared link and cached locally at `/data/hermes/document_cache/` but NOT stored in Drive. Note this in the Resources Reference.

### Partial BatchUpdates Create Fragments

When a batch update only partially replaces text (because indices shifted), leftover fragments like `ess: [Allottee Address]\n` or `IN WIMrs. Prathyusha` can remain. Always verify by re-reading after the batch.

---

## Allottee Data Template

```text
Name:       Mrs. Prathyusha Vuppala
Age:        35 years
Spouse:     W/o Mr. Vasudev Neehar Chinnam
Address:    B 1304, Bren Champions Square Apartment, Sarjapur Road, Decathlon, Bengaluru - 560 035
Aadhaar:    7892 9165 9175
PAN:        AGEPV6817A
```

---

## Phase 7: Title Chain Reference Update (Post-Creation)

After the document set is created and allottee details filled, the user may provide a **source title document** (a registered Sale Deed from the vendor's chain of title) and ask you to reference it across Schedule A/B in all agreements. This is a separate workflow from Phase 1 (source review) — here the document is NOT a template source but a **title provenance reference**.

**Trigger:** User says "Plot X falls under Survey Y — we have a registered Sale Deed with [Vendor Name], add those details in the agreements."

### Workflow

#### Step 1: Find the Title Document on Drive

Search by multiple name patterns — original filenames are often inconsistent:

```python
# Use raw_query to bypass bridge's fullText wrapper
result = gws_call("drive_search", service_name="google-draas",
                  query="name contains 'Suresh' and name contains 'Reddy'",
                  raw_query=True)
files = json.loads(result)
```

**Pattern:** `raw_query=True` is REQUIRED when using Drive query language operators (`and`, `contains`, `mimeType`, etc.). Without it, the bridge wraps your query in `fullText contains '...'` which breaks compound queries.

Also search by:
- Survey number (`name contains '158/1C9A'`)
- Document type + survey (`name contains 'Sale Deed' and name contains '158'`)
- Google Doc versions (easier to extract text from) alongside scanned PDFs

#### Step 2: Extract Title Details

From the Sale Deed, extract these fields:

| Field | Example |
|-------|---------|
| Document Number | 21785/2024 |
| Date | 14.11.2024 |
| Registering Authority | SRO Hosur |
| Vendors | Y. Suresh Reddy, Deepak S, Pavan Reddy S, Y. Manjunath Reddy, Minor Adith Kiran Reddy N, Minor Janith M Reddy (through natural guardian) |
| Vendee | M/s DRA Realty Private Limited |
| Survey Number | 158/1C9A |
| Extent in Survey | Ac. 0.25 cents |
| Boundaries (N/E/S/W) | East: 158/1C9B, West: 167, North: 158/1C8, South: 158/1C9B |
| Total Consideration | Rs. 98,00,000/- (for combined 0.98 cents across 4 surveys) |

For Google Doc versions of the deed, use `docs_get`. For scanned PDFs, use `pdftotext` first, then `vision_analyze` on rendered pages if text extraction fails.

#### Step 3: Plan Which Sections to Update

All 3 documents need updates in consistent locations:

| Document | Schedule A (Project Land) | Schedule B/C (Plot/Villa) | Recitals |
|----------|--------------------------|---------------------------|----------|
| **Agreement for Sale** | Add Sale Deed ref + title source | Add Survey No. to plot description | Add survey number where blank |
| **Construction Agreement** | Add Sale Deed ref after survey list | Add Survey No. to villa description | Add survey number in Recital G |
| **Combined Agreement** | Add Sale Deed ref under Schedule of Project Land | Add Survey No. in Schedule A (plot) + Schedule B (villa) | Update Recital I with survey number |

**Key rule:** Add the survey number (e.g. "158/1C9A") everywhere a placeholder `[ ]` existed, AND add the full Sale Deed reference as a separate paragraph in Schedule A / Schedule of Project Land.

#### Step 4: Update All Documents via Docs API batchUpdate

Use Google Docs `replaceAllText` — one `batchUpdate` per document with multiple `replaceAllText` requests:

```python
from tools.gws_auth import build_service

service = build_service("docs", "v1", service_name="google-draas")

requests = [
    {
        "replaceAllText": {
            "containsText": {
                "text": "EXACT_TEXT_TO_FIND",
                "matchCase": False
            },
            "replaceText": "REPLACEMENT_TEXT"
        }
    },
    # ... more requests
]

result = service.documents().batchUpdate(
    documentId=doc_id,
    body={"requests": requests}
).execute()
```

**Target text for replacements in Schedule A / project land description:**
- Add: `"Schedule B property (Plot No. 119) is carved out of Survey No. 158/1C9A. The Promoter derives title to Survey No. 158/1C9A through a registered Sale Deed No. 21785/2024 dated 14.11.2024 registered at SRO Hosur, executed by [VENDOR NAMES] in favour of [VENDEE NAME], conveying an extent of Ac. 0.25 cents in Survey No. 158/1C9A (bounded East by Sy. [X], West by Sy. [Y], North by Sy. [Z], South by Sy. [W])."`

**Target text for Schedule B/C (plot/villa description):**
- Search for `"Plot No. 119"` or `"Villa constructed on Plot No. 119"` — insert `"in Survey No. 158/1C9A"` after the plot number

**Target text for Recitals:**
- Wherever the plot/villa is introduced (Recital F/G/I), add `"in Survey No. 158/1C9A"` or update placeholder survey brackets

### Pitfalls

- **Dry-run each replaceAllText:** Ensure each `containsText.text` matches EXACTLY one unique occurrence in the doc. If the text appears in multiple places (e.g. "Plot No. 119" in both Schedule A and Schedule B), add enough context to make it unique, or use a broader approach (update both with the same replacement).
- **Scanned PDF vs Google Doc:** The scanned PDF (printed + scanned) may be the registered version, while the Google Doc/Word version is the draft. Use the Google Doc for text extraction; reference the registered document number for legal citation.
- **Boundary format:** Use consistent direction order (East/West/North/South) matching the source deed.
- **Extent units:** TN deeds use Hectares-Ares-Centiares (e.g. Hec. 0.10.0) AND Acres-Cents (Ac. 0.25 Cents). Include both in the reference to avoid conversion ambiguity.
- **Multiple vendors / guardians:** If minors are involved, list them with "represented by their natural guardian father [NAME]" — exactly as the deed states. Do NOT simplify to just the guardian.

---

## Phase 8: Resource Sourcing from Email Attachments (Post-Creation)

After the document set is created and all title references filled, the user may ask you to find additional source documents (master plan, area statement, layout plan) from email and add them to the folder as supporting evidence for the plot data.

**Trigger:** User says "There's an email from [Name] today with the area statement and layout plan — download it, add to the folder, and note that Plot 119 extraction was taken from this layout."

### Workflow

#### Step 1: Find the Email

**Use multiple search queries** — the sender's name in Gmail may differ from what the user said:

```python
# Try name variations + subject keyword searches
queries = ["Sinchana Gowda", "Gouda", "area statement", "master plan", "layout plan"]
```

**Common mismatch patterns:**
- Spoken name ≠ Gmail display name: "Senchana Gouda" → **Sinchana Gowda** (sgowda@draas.com)
- The email may be forwarded — check the message body for the forwarded-from header
- The attachment may be in a FORWARDED email, not the original thread opener

**To get full message + attachment list**, use `format="full"` and inspect `payload.parts` recursively:

```python
from tools.gws_auth import build_service
gmail = build_service("gmail", "v1", service_name="google-draas")
msg = gmail.users().messages().get(userId="me", id="...", format="full").execute()

def extract_parts(part, depth=0):
    mime = part.get('mimeType', '')
    filename = part.get('filename', '')
    body = part.get('body', {})
    attachment_id = body.get('attachmentId', '')
    if filename:
        print(f"📎 {filename} ({mime}, size={body.get('size', 0)})")
    if 'parts' in part:
        for p in part['parts']:
            extract_parts(p, depth + 1)
    if not filename and mime == 'text/plain' and body.get('data'):
        decoded = base64.urlsafe_b64decode(body['data'].encode('ASCII')).decode('utf-8', errors='replace')
        print(f"📝 {decoded[:300]}")
```

#### Step 2: Download the Attachment from Gmail

```python
attachment = gmail.users().messages().attachments().get(
    userId="me",
    messageId="MESSAGE_ID",
    id="ATTACHMENT_ID"
).execute()

file_data = base64.urlsafe_b64decode(attachment['data'].encode('ASCII'))

local_path = "/data/hermes/document_cache/descriptive_filename.pdf"
with open(local_path, 'wb') as f:
    f.write(file_data)
```

**Naming convention:** Use a descriptive filename (e.g., `Oasis_Master_Plan_18.07.26.pdf`) rather than the raw sender filename.

#### Step 3: Upload to the Project Folder

```python
from tools.gws_skill_bridge import call as gws_call

result = gws_call("drive_upload", service_name="google-draas",
                  path="/data/hermes/document_cache/Oasis_Master_Plan_18.07.26.pdf",
                  name="Oasis Master Plan 18.07.26.pdf",
                  mime_type="application/pdf",
                  parent="FOLDER_ID")
```

**⚠️ Parameter names matter:** The underlying skill function expects `args.path`, `args.name`, `args.parent` — NOT `file_path`, `file_name`, or `parent_id`. The bridge wraps kwargs into a namespace that maps directly to function parameter names.

#### Step 4: Add Entry in Resources Reference Document

**Option A — Add a row to an existing table (if the Resources doc has a table):**

Use Google Docs API `insertTableRow` + `insertText`:

```python
from tools.gws_auth import build_service

service = build_service("docs", "v1", service_name="google-draas")

# Step 4a: Find table location and insert row
doc = service.documents().get(documentId=DOC_ID).execute()
content = doc.get('body', {}).get('content', [])
# Locate the target table by index in content list
table_elem = content[TABLE_INDEX]
table_start = table_elem.get('startIndex')
last_row_idx = len(table_elem['table']['tableRows']) - 1  # last data row

# Insert new row below
requests = [{
    "insertTableRow": {
        "tableCellLocation": {
            "tableStartLocation": {"index": table_start},
            "rowIndex": last_row_idx,
            "columnIndex": 0
        },
        "insertBelow": True
    }
}]
service.documents().batchUpdate(documentId=DOC_ID, body={"requests": requests}).execute()

# Step 4b: Read the new row's paragraph start indices (they shift after insertion)
doc = service.documents().get(documentId=DOC_ID).execute()
new_cells = doc['body']['content'][TABLE_INDEX]['table']['tableRows'][-1]['tableCells']

cell_indices = []
for cell in new_cells:
    for ce in cell.get('content', []):
        if 'paragraph' in ce:
            for pe in ce['paragraph'].get('elements', []):
                if 'textRun' in pe:
                    cell_indices.append(pe.get('startIndex'))
                    break

# Step 4c: Insert text sequentially (indices shift after each insert)
service.documents().batchUpdate(documentId=DOC_ID, body={
    "requests": [
        {"insertText": {"location": {"index": cell_indices[0]}, "text": "H"}},
    ]
}).execute()

# Re-read for shifted indices before next insert
# ... repeat for cells[1], cells[2] ...
```

**⚠️ Index shifting:** After each `insertText`, indices shift by the length of inserted text. You MUST re-read the document between cell inserts, not batch them.

**⚠️ Paragraph startIndex ≠ cell startIndex:** The cell's `startIndex` is the structural boundary. The paragraph element's `startIndex` is inside the paragraph. Always use the **paragraph textRun startIndex**, not the cell's startIndex, for `insertText`.

**Note content requirement (Bharat preference):** The user wants the note to explicitly say **"Plot 119 extracted from this layout plan"** (or similar) so anyone opening the folder knows the source of the plot data.

**Option B — Append text after the table (if the Resources doc has no table):**
Use `insertText` at the document end with a bullet-point format.
