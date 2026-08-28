# Merging Two Absolute Sale Deed Drafts with Change Highlighting

**When to use this:** User sends a second version of a sale deed (from a different drafter — Bharat, advocate, counterparty) and asks to merge it with your existing draft, preserving the best of both. This is NOT diffing — it's a structural merge that adopts one draft as the base and supplements it with the other.

## Workflow

### Step 1: Download both .docx from Google Drive

Use the Drive API to download as raw binary:

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseDownload
import io

drive = build_service("drive", "v3", service_name="google-draas")

def download_docx(file_id, output_path):
    request = drive.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    with open(output_path, "wb") as f:
        f.write(fh.getvalue())
    print(f"{output_path}: {fh.tell()} bytes")
```

Note: `export_media() with text/plain` does NOT work for .docx files (fileNotExportable error). Always use `get_media()` for binary download, then extract text locally.

### Step 2: Extract text from both

```python
from docx import Document

def extract_text(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)
```

### Step 3: Analyze structural differences

Key dimensions to compare:

| Dimension | What to check |
|-----------|---------------|
| Party roles | Who is VENDOR vs CONFIRMING PARTY? Different drafters may swap them (see below) |
| Recital structure | Roman numeral recitals vs per-survey-number header sections |
| Operative provisions | "NOW THIS INDENTURE WITNESSETH" (Prakash style) vs "Clauses 1-6" (Bharat style) |
| Covenants | 13 vendor covenants vs 4 summary covenants |
| Schedules | Section list vs structured table |
| Dates | Specific date (20 Aug 2026) vs placeholder [●] |
| Signatories | Order of parties, witness format |
| Preparer credit | "Document prepared by: Bharat Hawaldar" |

### Step 4: Decide base draft

Rules of thumb:
- **Bharat's draft** is usually more polished for end-client use — better recital detail, operative clauses, DTCP/RERA references, consideration clauses, and complete dates
- **Your draft** may have better per-survey-number title flows, consolidation summary, and deeper legal/title detail
- **Merge strategy**: Use Bharat's as the base structure, ADD your per-survey detail where it improves completeness, and flag all additions with yellow highlighting

### Step 5: Build merged version with python-docx

Use python-docx (not lxml) when you're BUILDING A NEW DOCX PROGRAMMATICALLY from text, rather than editing an existing one. For editing existing .docx files, use lxml/xml manipulation.

**Yellow highlighting helper:**

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_run(para, text, bold=False, size=None, highlight=False):
    """Add a run with optional yellow highlight."""
    run = para.add_run(text)
    if bold:
        run.bold = True
    if size:
        run.font.size = Pt(size)
    if highlight:
        rPr = run._element.get_or_add_rPr()
        hl = OxmlElement('w:highlight')
        hl.set(qn('w:val'), 'yellow')
        rPr.append(hl)
    return run

def add_mixed_para(doc, parts, align=None):
    """Add paragraph with mixed formatting.
    parts = [(text, {bold: True, highlight: True}), ...]
    """
    para = doc.add_paragraph()
    if align:
        para.alignment = align
    for text, fmt in parts:
        add_run(para, text, **fmt)
    return para
```

### Step 6: Upload as new Google Doc

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload(
    file_path,
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True
)

file = drive_service.files().create(
    body={
        'name': 'RankaOasis_Plot119_AbsoluteSaleDeed_MERGED',
        'mimeType': 'application/vnd.google-apps.document'
    },
    media_body=media,
    fields='id, webViewLink'
).execute()

# Make writable by anyone with link
permission = {
    'type': 'anyone',
    'role': 'writer',
    'allowFileDiscovery': False
}
drive_service.permissions().create(
    fileId=file.get('id'),
    body=permission,
    fields='id'
).execute()

print(f"Edit link: https://docs.google.com/document/d/{file.get('id')}/edit")
```

## Clean-Redraft Authoritative Structure Pattern

**Different from "merge two drafts":** Sometimes the user provides a **clean redraft document** (a structural template — party roles preassigned, groups predefined, schedule structure fixed) and asks you to merge your previously-built draft content INTO it. The clean redraft is **authoritative on structure** — you do NOT decide which draft is the structural base. The user already decided.

### How to recognize a clean-redraft request

The user says: "Update this draft based on this [clean redraft doc] and highlight changes in yellow" or "NOW MERGE AND MODIFY ABOVE DRAFT WITH THE CONTENTS OF THE DRAFT WE PREPARED. KEEPING ALL THE HEADERS OF SECTIONS AND ADD THE CONTENT AS PREPARED IN THIS DRAFT."

### Workflow

1. **Download the clean redraft** — this defines the authoritative structure (party roles, group ordering, schedule definitions)
2. **Download your previous draft** — this provides the content to fill in
3. **Extract both as text** (python-docx)
4. **Build from the clean redraft's structure**, adding content from your draft:
   - Party roles: use what the clean redraft says (even if it swaps VENDOR/CONFIRMING PARTY)
   - Recital grouping: use the clean redraft's grouping (e.g. 8 Groups instead of Roman numerals)
   - Schedule layout: use the clean redraft's format and ownership assignments
   - Operative clauses: prefer whichever draft has more detail (usually the newer/third-party draft)
5. **Yellow-highlight everything that was added or changed** from the clean redraft's original
6. **Upload to Drive** as a new document

### Two-pass workflow

**Pass 1 — Restructure:** Match the clean redraft's structure. Merge content, fix duplication. Deliver yellow-highlighted version.

**Pass 2 — Enrich:** User asks for more detail (e.g. "add source of title flow for each survey no, as mentioned in the registered respective deeds"). Go back to the legal opinion/Jeevanandam/TSR and:
- Add every deed in each chain with: deed type, date, doc number, SRO, parties (vendor→buyer)
- Add special events: death dates, GPA creation/specific deed numbers, specific cancellation deed numbers, partition deed references, names of legal heirs
- Rebuild the docx, re-upload with the same yellow-highlight pattern

**When re-uploading after enrichment:** Google Docs API does NOT support updating the content of an existing .docx→Google Doc conversion. You must DELETE the old file and CREATE a new one. This changes the URL. Warn the user.

```python
# Delete old
drive_service.files().delete(fileId=old_file_id).execute()
# Create new
file = drive_service.files().create(
    body={'name': 'Same Name', 'mimeType': 'application/vnd.google-apps.document'},
    media_body=media, fields='id, webViewLink').execute()
```

## Party Role Convention (Bharat vs Prakash style)

This is the most common conflict in a merge:

| Role | Bharat's convention | Prakash convention |
|------|-------------------|-------------------|
| VENDOR | **Sevaganapalli Land Partners** (the developer/promoter who sells to the end buyer) | **DRA Realty** (the landowner who holds title to the plot survey number) |
| CONFIRMING PARTY | **DRA Realty** (landowner confirming title and no-objection) | **Sevaganapalli Land Partners** (co-promoter confirming consent) |
| Rationale | SLP manages end-customer sales; DRA holds the land as investor | DRA owns the parcel; SLP is the development partner |

**When merging:** Follow whichever draft is newer/more polished. Flag the swap with yellow highlight if instructed.

## What Each Draft Typically Does Better

| Feature | Bharat | Ours |
|---------|--------|------|
| Date / Place | ✓ Complete date, place | ✗ Placeholders [●] |
| Party descriptions | ✓ Full Aadhaar, PAN, authorization | ✓ Same quality |
| Recital detail | ✓ 10 recitals (i-x), per-survey flows | ✓ Per-survey headers |
| Project/B section | ✓ DTCP No, TNRERA registration, Planning Permission | ✗ Brief mention |
| Consideration section | ✓ Rs.29,85,400 with TDS analysis | ✗ Absent |
| Operative clauses | ✓ Clauses 1-6 with full wording | ✗ Brief 2-clause |
| Representations | ✓ 10 items (title, encumbrances, litigation, RERA, TDS, layout, etc.) | ✗ 2-3 items |
| Schedules | ✓ Table format for Schedule A | ✓ Section list |
| Signatures | ✓ Name, Aadhaar, PAN per party | ✓ Similar |
| Signature location | Specified: Bagalur | Specified: Bagalur |
| Preparer | "Document prepared by: Bharat Hawaldar" | Absent |

## Typical Merge Result

The merged document should have:
1. **Opening date/place** → from Bharat (20 Aug 2026, Bagalur)
2. **Party definitions** → from Bharat (SLP as VENDOR, DRA as CP)
3. **Recitals** → from Bharat (10 recitals i-x with per-survey flows), add our Consolidation of Ownership section
4. **Project/B section** → from Bharat (DTCP approval, TNRERA registration)
5. **Consideration** → from Bharat (detailed payment clause, TDS analysis)
6. **Operative clauses** → from Bharat (Clauses 1-6 with all warranties)
7. **Schedules** → Bharat's table format for Schedule A, our per-survey extent/owner/source details in each row
8. **Signatures** → from Bharat (4 parties: VENDOR, CP, VENDEE, witnesses)
9. **Preparer credit** → "Document prepared by: Bharat Hawaldar"

## Pitfalls

- **python-docx add_run format tuples must be (text, dict)** — not (heading, body, dict). Each item in the parts list must be exactly (str, dict). Use separate runs for bold labels and body text.
- **Drive file type detection**: Always check mimeType. Google Docs return `application/vnd.google-apps.document` and must be exported. Native .docx files return `application/vnd.openxmlformats-officedocument.wordprocessingml.document` and must be downloaded via `get_media()`.
- **Google Docs API (v1) doesn't work for .docx**: It returns "This operation is not supported for this document. The document must not be an Office file." Always use `drive.files().get_media()` for binary .docx.
- **Export to text/plain not supported for .docx**: "Export only supports Docs Editors files." Download binary and extract locally with python-docx.
- **`ET.tostring` with standalone kwarg**: Python 3.13's lxml does NOT support `standalone=True`. Build the XML declaration string manually.
- **Yellow highlight in Google Docs**: Always use `w:highlight w:val='yellow'` on runs (works in Google Docs). `w:shd w:fill='yellow'` on paragraphs is invisible in Google Docs (only shows in MS Word). The python-docx `WD_COLOR_INDEX.YELLOW` maps to `w:shd`, not `w:highlight` — so manual OxmlElement is required.