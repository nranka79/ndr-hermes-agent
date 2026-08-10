---
name: property-title-due-diligence
description: >
  Karnataka (and Bangalore/Chennai BBMP) property legal title due diligence:
  read land/registration documents (RTC, mutation register / MR, sale deed,
  encumbrance certificate EC/CC, khata, survey records) and establish the
  legal chain of title for a property — khatedar names, survey numbers, MR
  references, encumbrances, BBMP PID/ePID formats, khata status incl.
  amalgamation, MCA entity verification, property tax receipts, and
  survey-wise land document inventory/organization with master sheets and
  gap analysis. Kannada OCR is unreliable — use vision_analyze with
  also_describe_visually=true. NEVER fabricate mutation numbers or document
  references; always cite the source document.
metadata:
  hermes:
    tags: [real-estate, title, due-diligence, rtc, land-records, bbmp, mca, khata, kannada, ec, karnataka]
    category: domain
    related_skills: [karnataka-rera-collector, legal-document-drafting, rera-compliance, maps, ocr-and-documents, property-rd]
---

# Property Title Due Diligence

End-to-end title due diligence for DRAAS real estate operations (Karnataka
revenue records + BBMP Bangalore / Chennai civic records): read the documents,
establish the legal chain of title, verify ownership/encumbrances/khata,
verify the entity behind a transaction, and organize survey-wise land document
sets into master sheets with gap analysis. Every fact must trace to a source
document — never invent mutation numbers, registration numbers, or document
references.

## When to Use

- User asks to verify property ownership, title, or tax status
- User asks to establish the chain of title for a property (RTC, MR, sale deed, EC chain)
- User asks about BBMP PID/ePID formats for a property
- User asks to check who owns a property or developer company (MCA verification)
- User asks to verify property tax receipts, EC/CC, or khata
- User asks for company director verification of a real estate entity
- User shares a Drive folder with 50+ land documents across survey numbers and asks to organize / build a master data sheet with gap analysis
- User asks to file a property document on Drive and notify on WhatsApp (Vinod workflow)
- User uploads a BBMP memorandum template (PID/khata bifurcation) and asks for a draft

## Key Principles (chain-of-title quality rules)

- **NEVER fabricate mutation numbers or document references.** If you cannot
  find a reference in the documents, say so clearly. Filling gaps with
  invented facts is worse than having a gap.
- **MR = Mutation Register** in Karnataka land records (revenue document,
  NOT a court order). MR numbers track changes in ownership/possession —
  inheritance, sale, gift, partition, court decree, or land acquisition.
- **Always cite the source document** for every fact. The user needs
  chain-of-title with document links.
- **Kannada OCR is unreliable** — always use `vision_analyze` with
  `also_describe_visually=true` to trigger full vision analysis; tesseract
  OCR alone misses key fields.
- **When the user (domain expert) corrects you, embed that learning in the
  skill** — e.g., the ePID correction from Vinod Das below.

## Workflow

### 1. RTC Reading & Karnataka Chain of Title

The core Karnataka title flow: revenue documents (RTC/Pahani) are the
starting point, then mutation history, then registered deeds and ECs.

1. Download all RTC PDFs from Drive using the GWS drive service
2. Convert to PNG images using `pdftoppm -png -r 150`
3. Use `vision_analyze` with `also_describe_visually=true` for Kannada text
   (OCR alone is unreliable)
4. Ask specific questions: survey number, khatedar names, MR numbers, LA
   (land acquisition) references
5. Cross-reference MR numbers across RTCs, Sale Deed, EC, and Confirmation Deed
6. Assemble the chain of title as a sequence of events with registered
   document numbers — original grant/allotment → transfers → current khatedar

**RTC pitfalls:**
- RTC PDFs may have 4 pages each; always check all pages
- Never assume "MR" in an RTC column refers to a court case — it's a revenue
  mutation number
- RTC year ranges vs mutation entries: an RTC shows the current record; the
  MR entries give the history — both are needed for chain of title

### 2. BBMP Property ID Formats

**Know the two systems — they are NOT interchangeable:**

**Old PID Format** (e.g., `72-1-B1-740`)
- Legacy manual system — Ward_Block_Building_Unit
- 72 = Old BBMP Ward Number
- 1 = Block/zone within the ward
- B1 = Building identifier
- 740 = Individual unit/shop number
- These properties have NOT been through improvement charge payment or plan sanction

**New ePID Format** (e.g., `4372453357` or `7611897160`)
- 10-digit electronic Property ID
- Assigned when:
  - Improvement charges are paid to BBMP, OR
  - Plan sanction is applied/approved for the property
- Not assigned by blanket migration — triggered by specific BBMP transactions

**Pitfall:** Do NOT tell the user that ePID was assigned through a general
system migration or digitisation drive. The ePID is directly tied to
improvement charge payment or plan sanction events. Properties in the same
area (e.g., Domlur 2nd Stage) can have different formats depending on which
ones have undergone these processes.
- This correction came from Vinod Das (DRAAS Property Title Due Diligence) —
  the user is the domain expert on BBMP processes. When they correct you,
  embed that learning in the skill.

**Verification sources:**
- BBMP property tax portal: https://paytax.bbmp.gov.in
- BBMP e-Aasthi portal (for khata/e-khata)
- Physical property tax receipts from BBMP ward office

See `references/bbmp-pid-formats.md` for the detailed reference.

### 3. Property Tax Receipt Verification

- Cross-check owner name, PID, property address, and financial year
- Tax paid receipt vs. demand notice: look for Receipt No, Date, Amount, PID
- Owners are often listed as "M/s Company Name (rep by Director Mr Name)"

### 4. Encumbrance Certificate (EC/CC) Analysis

When reviewing EC/CC documents:
- Verify property schedule matches the target property
- Identify all registered encumbrances (mortgages, liens, agreements)
- Look for discharge deeds that clear prior loans
- Cross-check period: ensure the search period is continuous
- Use YYYYMMDD_PropertyName_EC_FromDate-ToDate.pdf naming convention

See `references/ec-compilation-merging.md` for the workflow to download,
organize, and merge multiple EC PDFs into a single printable document.

### 5. Khata Status, e-Khata & Amalgamation

- A-Khata: Properties with approved plan sanction — bankable, transferable
- B-Khata: Properties without full approvals — restricted
- e-Khata: Digitised version available on BBMP e-Aasthi portal
- Verify through: BBMP ward office or e-Aasthi portal

#### 5a. Amalgamation & Composite Khata

A common DRAAS scenario: DRA purchases **multiple adjacent BDA sites** from
different original allottees, then applies to BBMP to amalgamate them into
one composite property. When a user asks about "amalgamation khata":

**What amalgamation means:**
- BBMP merges adjacent sites (e.g., Sites 37, 37A, 38) into a single composite property
- The composite gets a new khata number (e.g., 37-37A-38) and PID (e.g., 72-30-37-37A-38)
- All subsequent documents (building permit, OC, tax receipts) use the composite khata

**The document trail (in order):**
1. **Amalgamation Order** — BBMP's formal order merging the sites (Legal Set Doc #015)
2. **Khata Certificate** — Issued post-amalgamation in DRA's name (Doc #016)
3. **Khata Extract** — Detailed extract showing the composite property (Doc #017)

**Typical DRAAS timeline:**
- Purchase sites from original owners (sale deeds)
- BBMP amalgamation order (often 2-3 months after purchase)
- Khata certificate issued in DRA's name (typically 2+ years later, once building plan is sanctioned)
- Khata extract issued alongside the certificate

**When presenting to the user, use a Pre/Post format:**

*Pre-Amalgamation (Separate Sites)*

| Site | Area | Original Owner | BDA Allotment |
|------|------|---------------|--------------|
| Site X | XX sq.m | Owner A | DD-Mon-YYYY |
| Site Y | XX sq.m | Owner B | DD-Mon-YYYY |

*Amalgamation: DD-Mon-YYYY* → **Composite Khata No. XXX-XXX-XXX** (PID XX-XX-XX-XX-XX)

*Post-Amalgamation*
- **Khata Certificate:** DD-Mon-YYYY in name of M/s DRA Developers & Projects Pvt. Ltd.
- **Khata Extract:** DD-Mon-YYYY

**Pitfall — Pre vs post terminology:** Users may refer to "khata" in the
abstract. Always clarify whether they mean the pre-amalgamation khata (in the
original allottee's name) or the post-amalgamation composite khata (in DRA's
name). These are different documents with different dates and numbers.

**Pitfall — Amalgamation Order date vs Khata date:** The Amalgamation Order
typically precedes the Khata Certificate by 1-3 years (order = 2012,
certificate = 2014 for Ranka Iris). Don't present them as the same event.

**Pitfall — Standalone Amalgamation Order PDF:** The Amalgamation Order is
Doc #015 inside the legal set but may ALSO exist as a standalone Google Drive
file (e.g., `Amalgamation Order` PDF) in the Customer Legal Set folder. Look
for both when the user asks for a direct link.

See `references/ranka-iris-document-set.md` for a complete worked example.

### 6. Company/Entity Verification (MCA)

When you need to verify who the directors and owners of a real estate entity are:

**Sources:**
- MCA portal (https://www.mca.gov.in) — official company records. Behind Cloudflare; blocked from automated environments.
- QuickCompany.in — Most reliable third-party mirror. Serves raw HTML parsable via curl+grep.
- ZaubaCorp / Tofler — Behind Cloudflare; usually blocked.
- Drive/Email search — DRAAS entities often have copies of Certificate of Incorporation, Form DIR-12, MOA/AOA, board resolutions.
- Transactional documents — JDAs, sale deeds, leases often name the signing director.
- Property Tax Receipts — Often list "M/s Company Name (rep by Director Mr Name)".

**Pitfall — MOA/AOA not always in project Drive folders:** Company formation
documents (Certificate of Incorporation, MOA, AOA) are often stored separately
from property-specific document folders. A search across all of a user's Drive
for "DRA Developers" or project names may return zero results for MOA/AOA even
when the project's title deeds, NOCs, and tax receipts are fully digitized.
These docs may be:
- In a separate "Company Documents" or "Statutory" folder not shared with the project
- Held physically in the company's statutory register
- Only available from MCA portal download
If Drive search comes up empty, suggest MCA portal or physical records —
don't assume they're missing entirely.

**QuickCompany extraction workflow:**

1. Save the company page to a file (avoids pipe-to-Python timeouts):
   ```
   timeout 15 curl -s -H "User-Agent: Mozilla/5.0" \
     "https://www.quickcompany.in/company/<company-slug>" \
     > /tmp/company_page.html
   ```
2. Extract director names + DINs:
   ```
   grep -oP 'directors/\d+[^"]+' /tmp/company_page.html
   ```
3. Extract company status:
   ```
   grep -oP 'Active|Strike Off|Dissolved|Amalgamated' /tmp/company_page.html
   ```
4. Check for past directors (resignations):
   ```
   grep -A5 'id="past_directors"' /tmp/company_page.html
   ```
   Empty row = no resignations recorded.
5. For appointment dates, fetch the director's detail page:
   ```
   timeout 15 curl -s -H "User-Agent: Mozilla/5.0" \
     "https://www.quickcompany.in/directors/<DIN>-<name-slug>" \
     > /tmp/director_page.html
   grep -A1 "First Appointment Date" /tmp/director_page.html
   grep -A1 "DIN Surrendered" /tmp/director_page.html
   ```

**Pitfall:** Do NOT pipe curl output directly into Python3 for HTML parsing —
the user-approval gate for piped Python commands times out frequently. Save to
file first, then grep.

##### Known DRA Group Data (MCA-verified)

| Entity | Directors (DIN) | Status |
|---|---|---|
| DRA Projects Pvt Ltd | Dinesh Devraj Ranka (00298727), Nishant Dinesh Ranka (00298854), Dharmesh Dinesh Ranka (00298826), Manish Dinesh Ranka (00396239) | Active, ROC Bangalore |
| DRA Realty Pvt Ltd | Nishant Ranka (Managing Director & CEO) | — |
| DRA Aadithya Pvt Ltd | Nishant Ranka | — |
| Southcity Projects Pvt Ltd | Nishant Ranka | — |

**Pitfall:** Director lists change (appointments, resignations). Always ask
the user to verify with the MCA portal or a recent company search report
before relying on director information for legal documents. If the user says
"this data seems old" or "some directors are no longer around", acknowledge
the limitation and suggest MCA portal verification or a recent Form DIR-12
check.

See `references/company-verification-workflow.md` for the full workflow.

### 7. Document Discovery & Legal Set Organization

When the user asks for specific revenue documents (OC, CC, mother deed/sale
deed, tax receipts, EC), systematically locate them:

#### 7a. Filesystem Search

Start with `search_files` or `find` to locate all documents matching the property name:

```
find /opt/data -iname "*<property_name>*" -o -iname "*<shortcode>*" 2>/dev/null | sort
```

Common filename patterns for DRAAS property documents:
- `*DomlurDocuments_0001.pdf` / `*DomlurDocuments_0002.pdf` — scanned legal document bundles (13+ pages each, HP Scanjet)
- `*_OccupancyCertificate.pdf` or `*_OC*.pdf` — OC certificate
- `BBMP_CommencementCertificate.pdf` — CC certificate
- `BBMP_BuildingPermit_*.pdf` — sanctioned plan
- `StructuralStabilityCertificate.pdf` — Form IX
- `*_site_plan.pdf`, `*_section_and_elevation.pdf`, `*_ground_and_first.pdf` — architectural drawings
- `*_tax_paid_receipt*.pdf` or `Tax Paid Receipt*.pdf` — BBMP tax receipts
- `*_EC*.pdf` — encumbrance certificates

Also check subdirectories: `downloaded_docs/`, `fire_docs/`, `ranka_*_search/`
often hold supplementary documents.

#### 7b. Google Drive Document Search

When you need to find property documents beyond local files — the user
explicitly asks for "links", "folders", "Drive" or you find the local file
set is incomplete:

**Prerequisite:** The user must have a GWS token at
`/data/hermes/users/<telegram_id>/gws_token.json` with the `drive` scope.
If missing, run `tools.gws_auth.get_auth_url(telegram_id)` and send the link.

**The Hermes venv path (critical):** The `tools.gws_auth` module lives at
`/opt/hermes/tools/gws_auth.py` but its dependencies (`googleapiclient`, etc.)
are only installed in the Hermes venv at `/opt/hermes/.venv/`. System Python
cannot import it.

```python
# Correct invocation from terminal:
/opt/hermes/.venv/bin/python3 -c "
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')
# ... your Drive API calls ...
"
```

**Search workflow:**

1. **Find project folders** by name:
   ```python
   results = drive.files().list(
       q="mimeType='application/vnd.google-apps.folder' and (name contains 'ProjectName' or name contains 'ShortCode')",
       spaces='drive',
       fields='files(id, name, webViewLink)'
   ).execute()
   ```
   DRAAS often has multiple folders for the same project (old/new, different
   owners' drives). Collect all of them.

2. **List folder contents** to see what documents exist:
   ```python
   results = drive.files().list(
       q=f"'{folder_id}' in parents",
       fields='files(id, name, mimeType, webViewLink, size)',
       pageSize=50
   ).execute()
   ```

3. **Distinguish bundle vs standalone:** Google-native files (Docs, Sheets)
   open directly. PDFs and scanned documents have direct download links.
   Large scanned bundles (e.g., `*Documents_0001.pdf`) typically contain the
   legal set.

4. **Share links, not paths:** When the user asks for document access,
   provide Google Drive `webViewLink` URLs — they can open these directly.
   For local-only files, offer to upload to Drive or send via Telegram.

**Pitfall:** Multiple Google accounts can own folders for the same property.
The current user's Drive (accessed via their GWS token) may only show their
accessible folders. If another DRAAS team member has the documents in their
Drive, you'll need their token or a shared drive.

**Pitfall:** Google-native file formats (Docs, Sheets) don't have a `size`
field in the API response — they return empty string for `size`. Don't treat
`size=''` as an error.

**Pitfall:** When running repeated Drive API calls in a single python3
invocation, you may hit quota limits on large result sets. Keep `pageSize`
reasonable (30–50) and use `nextPageToken` for pagination if needed.

**Delivering downloaded files to the user via Telegram:** After downloading a
document from Drive, use `send_message` with `target="telegram"` (NOT
`target="origin"` — that raises "Unknown platform: origin"). Include
`MEDIA:/absolute/path/to/file` in the message text. Example:
```
send_message(
    target="telegram",
    message="Document Name\n\nMEDIA:/opt/data/filename.pdf"
)
```
The file path must be absolute. Image files (.png, .jpg, .webp) render
inline; PDFs and other documents send as downloadable attachments.

#### 7c. Legal Set Document Index

DRAAS properties often have a Legal Set Document Index that numbers all title
documents sequentially (e.g., 001–025). This index maps each numbered slot to
a document type:

| # | Document Type | Relevance |
|---|---------------|-----------|
| 003–013 | **Sale Deeds (Mother Deeds)** | Original BDA allotments, sale deeds from original owners to DRA — these ARE the mother deeds / sale deeds the user asks for |
| 015–017 | **Amalgamation / Khata** | Shows consolidation of multiple sites into one property |
| 018–021 | **NOCs** | AAI, Fire, BESCOM, BWSSB — regulatory approvals |
| 022 | **BBMP Sanction / Building Permit** | Plan sanction |
| 023 | **Tax Paid Receipt** | BBMP property tax paid |
| 024–025 | **EC (Encumbrance Certificate)** | Covers specific periods by site number |

**Where to find the index:**
- Look for a file named `*Legal Set Document Index*` or `*Document Index*` in the search results
- Legal diligence reports (e.g., `*Legal Diligence Report by *` or `*Legal Opinion by *`) often reproduce the full document chain in narrative form
- The scanned PDF bundles (`*Documents_0001.pdf`) typically contain the actual document scans in index order

**Pitfall:** The scanned bundles are often large (3.5 MB each), in scan-date
order not filing order. The Legal Set Index is the authoritative map — always
find it first rather than scrolling through every scanned page.

#### 7d. Mapping User Requests to Index Numbers

When user asks for "mother deed" / "sales deed":
→ Look at Sale Deed entries in the index (e.g., #009, #013 for DRA purchases from original allottees; #004, #007, #011 for BDA-to-original-owner)

When user asks for "OC certificate":
→ Look for standalone `*OccupancyCertificate*.pdf` files (recently issued — typically 2025-2026)

When user asks for "CC certificate":
→ Look for `BBMP_CommencementCertificate*.pdf` or Work Commencement Certificate entries

When user asks for "BBMP tax paid receipt":
→ Look for Tax Paid Receipt entries in the index (e.g., #023) plus standalone files in `downloaded_docs/`

When user asks for "EC" (Encumbrance Certificate):
→ Look for EC entries in the index (typically two — one per original site, covering from BDA allotment date to the search date)

When user asks for "all revenue documents":
→ Systematically cover: OC, CC, Mother Deed/Sale Deed, Tax Paid Receipt, EC plus Building Permit, NOCs, Khata

#### 7e. Extracting Document Chains from Legal Diligence Reports

The legal diligence report (e.g., "Ranka Iris Legal Diligence Report by Kusuma
Muniraj") often provides a narrative chain of title covering:
- Original BDA allotment (date, allottee name)
- BDA sale deed details (doc number, registration details)
- Subsequent transfers (original owner → DRA)
- Amalgamation of khata
- Current khata status

Extract the chain as a sequence of events with registered document numbers —
this helps the user verify they have the complete set.

#### 7f. Registration Number Extraction from Original Filenames (MR, EC, Sale Deed)

Before renaming files in bulk, extract **registration/document numbers** from
the ORIGINAL filenames — these get lost once renamed. Two critical patterns:

**MR (Mutation Register) Numbers**: Original filenames have patterns like
`MR no 17`, `M.R.No. 14`, `MR H34`, `MR 28/2000-01`. Extract with:

```python
# Run on original filenames before rename
m = re.search(r'(?:MR|M\.?R\.?)\s*(?:No\.?|no\.?)?\s*[:.]?\s*(\w[\w/-]*)', orig_name, re.IGNORECASE)
if m:
    mr_val = m.group(1).strip().rstrip('.').replace(' ', '')
    mr_num = f"MR-{mr_val}"  # e.g. "MR-17", "MR-H34", "MR-T31"
```

**EC (Encumbrance Certificate) Date Ranges**: Original filenames have date
ranges in DDMMYYYY format:
- `01042004 To 10032026 EC SyNo 274.pdf` → EC covers 2004-04-01 to 2026-03-10
- `01042004 To 11082023 EC SyNo 302.pdf` → EC covers 2004-04-01 to 2023-08-11

Parse with:
```python
def parse_ddmmyyyy(d):
    """Convert DDMMYYYY to YYYY-MM-DD. Handles DD/MM/YYYY too."""
    if len(d) == 8 and d.isdigit():
        return f"{d[4:8]}-{d[2:4]}-{d[0:2]}"
    return ''

m = re.search(r'(\d{8})\s*[Tt][Oo]\s*(\d{8})', orig_name)
if m:
    d1 = parse_ddmmyyyy(m.group(1))
    d2 = parse_ddmmyyyy(m.group(2))
    if d1 and d2 and d1.startswith('20') and d2.startswith('20'):
        date_range = f"{d1} to {d2}"
        # Use as the date portion of the new filename
```

**Pitfall — EC date range regex is destructive on already-renamed files:**
The `DDMMYYYY to DDMMYYYY` regex (`(\d{8}) to (\d{8})`) will ALSO match date
strings in already-renamed filenames like `2004-04-01 to 2023-08-11.pdf` by
extracting `20040401` and `20230811`, then re-parsing them through
`parse_ddmmyyyy()` which produces corrupted dates like `0104-20-04`. **Always
run EC date range extraction on the ORIGINAL filename before the rename pass,
never on the current filename.** If you must fix an already-renamed EC file,
extract the date range from the original filename stored in the inventory, not
from the current Drive name.

**PITFALL — MR number extraction regex casts too wide a net:** The pattern
`(\d{4})[-\s](\d{2})` also matches RMN numbers like `RMN-1-02883-2011` where
`02883-20` triggers a false positive. Always check that the matched number is
a plausible year range (e.g., start year 1990–2030, end year = start+1)
before using it. Better approach: limit MR extraction to filenames that
explicitly contain `MR` or `M.R.` (not just any digit sequence).

See `references/ec-mr-date-extraction-patterns.md` for the full reference.

### 8. Survey-wise Land Document Inventory & Organization

When the user has a Google Drive folder containing hundreds of land revenue
documents (RTCs, ECs, MRs, Form 1s, Form 7s, GPAs, sale deeds) spread across
multiple survey numbers — typically for a land aggregation project — use this
workflow to create a clean, organized structure with a master sheet and gap
analysis.

#### When to Use
- User shares a Drive folder with 50+ land documents across multiple Sy Nos
- User says "go through the drive link and extract each document" or "make a master data of all documents"
- User wants to know which documents are available per Sy No and which need to be procured
- User asks to rename files or reorganize the Drive folder structure

#### Phase 1: Inventory Audit

Recursively list ALL files/folders in the shared Drive folder using the
drive-recursive-listing pattern. Capture:
- File name, ID, size, modified time, current parent folder
- Separate by folders/buckets — note which files are already in Sy No folders vs unsorted

**Pitfall:** Google Drive API returns max 100 files per page. Always paginate
with `nextPageToken`. Use explicit `fields` to minimize quota.

**Pitfall:** Run with `/opt/hermes/.venv/bin/python3` — the Google API client
libs are installed there, not in system Python.

#### Phase 2: Sy No Classification from Filenames

Build a Sy No extraction function. Indian land document filenames follow
these patterns (use regex in priority order):

```python
import re

def classify_sy_no(filename):
    """Extract Survey Number from a land document filename."""
    n = name.rsplit('.', 1)[0] if '.' in name else name

    # Pattern 1: Explicit 'Sy No XXX', 'Survey No XXX' or variations
    # e.g. 'Sy No 87 Form 1.pdf', 'Survey No 103 Form 7.pdf', 'sy no 103_11.pdf', 'SyNo 302 EC.pdf'
    m = re.search(r'(?:Sy|SY|sy|Survey)\s*(?:No|no|NO|nos)?\s*[.:]?\s*(\d+(?:[/-]\d+)?)', n)
    if m:
        raw = m.group(1).replace('-', '/')
        base = raw.split('/')[0]
        return raw if raw in known_subdivisions else base

    # Pattern 2: Leading number + sub-division separator
    # e.g. '103_5.pdf', '87_1.pdf', '34_1.pdf'
    m = re.match(r'(\d{2,3})(?:[_-](\d+))?', n)
    if m:
        base, sub = m.group(1), m.group(2)
        valid_sy_nos = {'34','87','102','103','104','105','106','107','108','109',
                        '110','111','112','130','274','291','302'}
        if base in valid_sy_nos:
            if sub and sub.isdigit():
                full = f"{base}/{sub}"
                if full in known_subdivisions:
                    return full
            return base

    # Pattern 3: Number with parenthetical suffix
    # e.g. '87 (1).pdf', '103.pdf'
    m = re.match(r'(\d{2,3})(?:\s*\(\d+\))?$', n)
    if m and m.group(1) in valid_sy_nos:
        return m.group(1)

    return None  # Unclassifiable — flag for manual review
```

**Known valid Sy Nos** should be assembled from the user's project scope. For
the Ramanagar/Magadi Road project, the known set includes: 34, 87, 87/3,
87/12, 103, 103/7, 103/11, 103/12, 104–112, 130, 274, 291, 302.

**Pitfall:** Sub-division numbering in filenames (e.g., `103_11.pdf`) can mean
`103/11` or just an index. Cross-check with known sub-division folders before
classifying.

**Pitfall — Timestamp filenames need folder context:** Files named
`202605281234.pdf` (YYMMDDHHMM timestamp) contain NO Sy No in the filename.
Their parent folder is the only clue. When scanning recursively, track each
file's `parent_name` so timestamp-prefixed files inherit their folder's Sy No.
Since these are scan-date timestamps, NOT document dates, flag them for
OCR/vision review to determine the actual document date.

#### Phase 3: Folder Structure Creation

Create one folder per Sy No at the root of the project Drive folder. Use a
**consistent prefix**:

```
Sy No 34
Sy No 87
Sy No 87/3
Sy No 87/12
Sy No 103
Sy No 103/7
Sy No 103/11
Sy No 103/12
Sy No 104  ... Sy No 112
Sy No 130
Sy No 274
Sy No 291
Sy No 302
```

Google Drive API to create a folder:
```python
meta = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [ROOT_FOLDER_ID]}
f = drive.files().create(body=meta, fields='id,name').execute()
```

To rename an existing folder:
```python
drive.files().update(fileId=folder_id, body={'name': new_name}).execute()
```

#### Phase 4: Move Files to Correct Folders

For each classified file, move it to its Sy No folder:
```python
drive.files().update(
    fileId=file_id,
    addParents=target_folder_id,
    removeParents=source_folder_id,
    fields='id'
).execute()
```

**Pitfall — API timeouts:** Each `files().update()` call is a separate HTTP
request. Moving 200+ files this way takes a long time and may timeout in a
single terminal session. Strategies to handle this:
- **Batch in small groups** (10-20 files per invocation)
- **Present the mapping first** — generate a mapping table showing "File X →
  Folder Y" and let the user approve or move manually
- **Skip moves and focus on the Master Sheet** — Drive links work regardless
  of folder location; the sheet is the more valuable deliverable

**Pitfall:** Files can have multiple parents in Google Drive. Moving via
`addParents` + `removeParents` is safe — it doesn't create duplicates or
break existing links.

**Alternative — "Cleaned Folder" approach (Prakash preference):** Some users
(especially Prakash) explicitly ask to NOT modify the original folder
structure at all. In that case:

1. Create a **separate root folder** named e.g. "Ramanagar Land — Cleaned"
2. Create Sy No sub-folders inside it
3. Use `drive.files().copy()` to create renamed copies in the cleaned folder
4. The original files stay untouched in their original locations with original names

```python
# Copy a file to the cleaned folder with a new name
drive.files().copy(
    fileId=original_file_id,
    body={
        'name': 'YYYY/MM/DD, Sy No, Village, Document Name, Reg No.pdf',
        'parents': [cleaned_folder_id]
    }
).execute()
```

**Why copy instead of rename in Drive:** Google Drive file names are
**file-level, not folder-level**. Renaming a file changes it everywhere —
including in the original folder. To have different names in different
folders, you must create copies. The original location serves as the "master"
with original names; the cleaned folder is a derived, organized view.

**Pitfall — API timeouts on bulk copies:** Same as moves — each
`files().copy()` is an individual HTTP request. Copying 500+ files in one
invocation will timeout. Batch 10–20 per invocation, or focus on the Master
Sheet first (links work regardless of folder location).

#### Phase 5: File Renaming Convention

Rename each file to the standard format (for title due diligence readability):

```
YYYY-MM-DD, Sy No, Village, Document Name, Registered Number.ext
```

**Note:** Prakash's preferred format uses `YYYY/MM/DD` with forward slashes,
but Google Drive filenames CANNOT contain `/` (it's a path separator). Use
`YYYY-MM-DD` (hyphens) or `YYYY.MM.DD` (periods) as the practical equivalent.
This applies identically to all file naming in Drive.

| Component | Source | Example |
|---|---|---|
| **Date** | From the document content (not file timestamp) | `2008/11/12` |
| **Sy No** | From classification | `Sy 103/11` |
| **Village** | Village name from project mapping | `Lakshmipura` |
| **Document Name** | Doc type (Sale Deed, GPA, EC, RTC, MR, Form 1, etc.) | `General Power of Attorney` |
| **Reg No** | Registration number from the document | `RMN-4-00216-2008-09` |

Example renames:
| Before | After |
|---|---|
| `202605281825.pdf` | `2026/05/28, Sy 87, Bomvachanahalli, EC 2004-2026.pdf` |
| `Sy No 87 Form 1 dated 9.8.1938.pdf` | `1938/08/09, Sy 87, Bomvachanahalli, Grant Title Deed Form 1.pdf` |
| `20081112 GPA No RMN-4-00216-2008-09 Sy No 103-11.pdf` | `2008/11/12, Sy 103/11, Lakshmipura, GPA, RMN-4-00216-2008-09.pdf` |

**Pitfall:** The date in the filename must come from the document's actual
content (grant date, deed execution date, EC period end date, RTC year
range), NOT the file's upload/modified timestamp. For timestamp-named files
(e.g., `202605281825.pdf`), the date prefix is the upload scan date, NOT the
document date — you must open and read the PDF to determine the real date.

**Pitfall:** Documents covering a range (e.g., "EC 2004-04-01 to 2026-04-05")
should use the end date or the range in the document name field.

#### Phase 6: Master Sheet with Category-Grouped Structure & Gap Analysis

Populate (or create) a Google Sheet with one tab per Sy No. **Prakash prefers
the per-tab format** to be organized by the 8 document categories from the
Required Docs Reference, with both available AND missing documents listed
under each category sub-heading.

**Per-Sy No tab format (row-by-row):**

```
Row 1: Survey No: 87 — Village: Bomvachanahalli — Total Files: 111
Row 2: #, Document Name, Date, Category Match, Reg No, Drive Link, Size, Remarks
Row 3: A. Title Documents           ← main section header (single cell)
Row 4:   >> Grants / Title Deeds / Deeds (Form 1 to 7)  ← sub-heading (single cell)
Row 5:   1, Sy No 87 Form 1 dated 9.8.1938.pdf, ...      ← available doc
Row 6:   2, ❌ Form 7A — NOT AVAILABLE                    ← missing required doc
Row 7:   3, ❌ Sale Deed — NOT AVAILABLE
Row 8:   >> GPA & Authorizations    ← next sub-heading
Row 9:   4, ❌ GPA — NOT AVAILABLE
Row 10:  >> Legal Heir / Succession
Row 11:  5, ❌ Legal Heir — NOT AVAILABLE
Row 12:  >> Other Documents (this category)  ← unclassified but category-related
Row 13:  6, Sy No 87 LND-SR-2-64-65 Form 4.pdf, ...
Row 14: B. Revenue Records          ← next main section header
Row 15:  >> Mutation Register (MR)
Row 16:  7, 2019-2020 MR no T18 sy no 87.pdf, ...
⋮
⋮
Row Z: Other / Unclassified Documents   ← global unclassified
```

**Sub-heading structure** — Each main category (A–H) can have multiple
sub-headings that group related document types. Prakash specified that
"Form 1 to 7 are under Grants/Title Deeds/Deeds". The sub-heading layout for
Title Documents is:

```
A. Title Documents
   >> Grants / Title Deeds / Deeds (Form 1 to 7)  → items 3 (Form 1/Grant), 2 (Form 7A), 4 (PTCL), 1 (RTC), 5 (Sale Deed)
   >> GPA & Authorizations                         → item 6
   >> Legal Heir / Succession                      → item 7
   >> Other Documents (this category)              → title-related files that don't match specific items
```

**Sub-heading format rules:**
- Sub-heading rows use `>> Sub-heading Name` in column A
- Sub-heading rows have EXACTLY ONE element (only column A populated). This
  keeps the structure clean.
- Each item number within a sub-heading is checked for matching files; if
  none found, a `MISSING: [doc name]` row is inserted.
- For categories A–D, after all sub-headings and items, an additional
  `>> Other Documents (this category)` section collects remaining files that
  match the category theme (e.g., Tehsildar letters under C) but don't map to
  a specific item number.

**Key structural rules:**
- **Category headers** (A. Title Documents, B. Revenue Records, etc.) each
  occupy their own row with a single cell in column A
- **Within each category**, documents are in ascending date order (oldest first)
- **Missing required docs** are shown as `❌ [Doc Name] — NOT AVAILABLE` with
  a remark "REQUIRED — Procure this document"
- **Unclassified documents** (no match to any of the 34 types) go in a final
  "Unclassified / Other Documents" section
- Timestamp-named files (e.g., `202605281234.pdf`) that can't be classified
  get flagged as "Timestamp — needs OCR" in Remarks

**Summary tab** with columns:
| Survey No | Village | Files Count | Total Size | Available Doc Types | Status |

Followed by a **Gap Analysis matrix** showing all 34 required doc types as
rows and each Sy No as a column, with "YES" in cells where a matching file
was found.

**Required Docs Reference** — the canonical 34-type list organized by 8
categories with procurement sources (from Prakash's PDF):

| # | Category | Items | Obtain From |
|---|---|---|---|
| A. Title Documents | 1–7 | RTC, Form 7A, Saguvali Chit/Grant/Form 1, PTCL Permission, Mother Deed Chain/Sale Deed, GPA, Legal Heir | VA/Bhoomi, Tahsildar Office, Sub-Registrar, ADLR |
| B. Revenue Records | 8–11 | MR, EC, Index of Land/Pakka Book, Land Classification | Tahsildar/VA, Sub-Registrar/Kaveri, ADLR |
| C. Tahsildar Endorsements | 12–17 | Hiduvali, Caste, PTCL (SC/ST), Tenancy, Non-Alienation, No-Dues | Tahsildar, AC Office, Land Tribunal |
| D. Survey & Boundary | 18–24 | Hissa Atlas, Tippani, Hissa Tippani, Kharab, Village Map, Karda, 11E Sketch | ADLR Office, Forest Dept, Revenue Dept |
| E. Govt Acquisition | 25–26 | Acquisition Search, Road Widening Clearance | DC Office, KIADB, PWD, NHAI, BDA |
| F. Court Cases | 27–28 | Civil Court Search, Revenue Tribunal | Civil Court Ramanagar, Advocate, Tahsildar |
| G. Panchayat & Tax | 29–30 | Kist Receipt, Panchayat NOC | Village Accountant, Gram Panchayat |
| H. KYC | 31–34 | Family Tree, PAN, Aadhaar, Bank Passbook | Tahsildar/VA, Income Tax Dept, UIDAI, Bank |

See `references/required-docs-procurement-sources.md` for the full per-item
breakdown.

**Doc-type matching function** — Map each filename to one of the 34 item
numbers. Use regex in this priority:

```python
def match_doc_type(name):
    """Match a filename to one of the 34 required document types. Returns req# or None."""
    n = name.lower()

    # A. TITLE DOCUMENTS
    if re.search(r'\brtc\b|pahani|record of rights', n): return 1     # RTC
    if re.search(r'form\s*7', n): return 2                             # Form 7A
    if re.search(r'form\s*1\b|saguvali|grant.*(?:order|title|deed)|grantee', n): return 3  # Grant / Form 1
    if re.search(r'ptcl|granted\s*lands|section\s*4\b', n): return 4  # PTCL Endorsement
    if re.search(r'sale\s*deed|agreement\s*of\s*sale|release\s*deed|mother\s*deed|title\s*trace', n): return 5  # Sale Deed Chain
    if re.search(r'gpa|power\s*of\s*attorney', n): return 6           # GPA
    if re.search(r'legal\s*heir|succession|heir\s*ship', n): return 7 # Legal Heir

    # B. REVENUE RECORDS
    if re.search(r'\bmr\b|mutation|register.*entry', n): return 8     # MR
    if re.search(r'\bec\b|encumbrance', n): return 9                  # EC
    if re.search(r'index\s*of\s*land|\bil\b|register.*rights|pakka\s*book|prathi\s*book|moola|mulla|mula\s*survey', n): return 10  # Index of Land
    if re.search(r'classif|reclassif|second\s*replication', n): return 11  # Land Classification

    # C. TAHSILDAR ENDORSEMENTS
    if re.search(r'hiduvali|occupancy|possession\s*certificate', n): return 12
    if re.search(r'caste', n): return 13
    # Items 14-17: rare in filenames, usually caught manually
    if re.search(r'ptcl', n): return 14
    if re.search(r'tenancy|occupancy\s*rights', n): return 15
    if re.search(r'non[-\s]alienation|restriction|15.year', n): return 16
    if re.search(r'no[-\s]dues|kist|tax.*(?:due|paid|receipt)|land\s*revenue', n): return 17

    # D. SURVEY & BOUNDARY
    if re.search(r'hissa\s*atlas|survey\s*atlas|hissa\s*book|hissa\s*sketch', n): return 18  # Hissa Atlas
    if re.search(r'tippani|tippni', n) and not re.search(r'hissa\s*tippani', n): return 19   # Tippani
    if re.search(r'hissa\s*tippani', n): return 20                                           # Hissa Tippani
    if re.search(r'kharab', n): return 21                                                     # Kharab
    if re.search(r'village\s*map|cadastral', n): return 22                                    # Village Map
    if re.search(r'karda|kharda|kayam\s*dara|field.*measure', n): return 23                   # Karda
    if re.search(r'11e|pre[-\s]mutation|sketch', n): return 24                                # 11E Sketch

    # E-G: Usually not found as files
    if re.search(r'acquisition|notification|kiadb|nhai|road.*widen|buffer|setback', n): return 25
    if re.search(r'court\s*case|liti|injunction|civil\s*court|revenue\s*court|tribunal', n): return 27
    if re.search(r'panchayat|local\s*authority|noc\b', n): return 30

    # H. KYC
    if re.search(r'family\s*tree', n): return 31
    if re.search(r'pan\s*card', n): return 32
    if re.search(r'aadhaar', n): return 33
    if re.search(r'bank|passbook|cancelled\s*cheque', n): return 34

    return None  # Unclassified — will go to the "Other" section
```

**Sorting rule:** Within each category group, sort ascending by date (oldest
first). Undated files use a high sort key `9999-99-99` so they appear last
within their category, not first.

**Pitfall — Sort order direction:** Prakash explicitly corrected "newest
first" to "oldest first". Always sort documents ascending by date within each
category. Presenting newest-first will require rework of all tabs.

**Pitfall — File rename name normalization pattern:** After two rename passes
(e.g., first pass using `Sy302` no-space format, second pass using `Sy 302`
with-space format), the same file may end up with two names in different
folders. Run a normalization regex after bulk renames:
`re.sub(r'\bSy(\d+)', r'Sy \1', old)` to fix the `SyXXX` → `Sy XXX` pattern.
Also clean double-registration-number artifacts:
`re.sub(r', (RMN[^,]+)\. (RMN\1)', r', \1', new)` to fix
`RMN-1-12345, RMN-1-12345-20` → `RMN-1-12345`.

**Pitfall — Section and sub-heading headers must be single-cell rows:** When
writing a section header like `A. Title Documents` or a sub-heading like
`>> Grants / Title Deeds / Deeds (Form 1 to 7)`, the row must have exactly
ONE element in its values list (`['A. Title Documents']` or
`['  >> Sub-heading Name']`). The next row then begins the data for that
section. Google Sheets API handles variable-length rows correctly —
single-element rows occupy only column A. Sub-headings use the prefix `>> `
to visually distinguish them from main category headers. **Sub-heading rows
must NOT have 8 elements** — they only need column A.

**Pitfall — Special characters in Sheets API values:** The em-dash (—) and
other non-ASCII Unicode characters in cell values cause a 400 "Invalid
values" error from the Google Sheets API. Always use simple ASCII
equivalents: hyphen (-) instead of em-dash (—), straight quotes instead of
curly quotes. When writing Python string literals that will go into Sheets,
verify no em-dashes or other special typographic characters are present.

**Pitfall — Sheets API USER_ENTERED vs RAW:** `USER_ENTERED` parses values
as if typed by a user (converts numbers, dates, formulas). `RAW` writes
values exactly as given. For document names containing things like `1-2-93`,
use `USER_ENTERED` to avoid Sheets interpreting them as dates.

**Pitfall — Batch writes vs row-by-row:** Writing each Sy No tab with
`values().update()` (full replacement) is simpler and more reliable than
per-row `append()`. For 20+ tabs, this works fine as long as each invocation
stays under the API timeout (~120s for large datasets).

**Pitfall — Clear-before-write for sheet tabs:** Google Sheets API's
`values().update()` does NOT clear rows beyond the range being written. If
the previous write had 200 rows and the new write has 150, rows 151–200
still contain stale data from the previous version. This manifests as phantom
"NOT AVAILABLE" rows or orphaned documents that appear to exist but are
actually from a previous write. **Always call `values().clear()` on the full
data range BEFORE calling `values().update()`:**

```python
sheets.spreadsheets().values().clear(
    spreadsheetId=SHEET_ID,
    range=f"'{sheet_title}'!A1:H999",
    body={}
).execute()
time.sleep(0.5)  # Brief pause for propagation
sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID, range=f"'{sheet_title}'!A1",
    valueInputOption='USER_ENTERED',
    body={'values': rows}
).execute()
```

This is especially important when iterating through multiple sheet tabs in a
loop — a bug in one tab's data generation can leave stale artifacts that look
like correct data.

##### Village Mapping Reference (Ramanagar / Magadi Road)

| Village | Survey Numbers |
|---|---|
| **Lakshmipura** | 34, 103, 103/7, 103/11, 103/12, 104, 105, 106, 107, 108, 109, 110, 111, 112, 130, 302 |
| **Bomvachanahalli** | 87, 87/3, 87/12, 274, 291 |

#### Phase 7: Duplicate Detection & Dedup

Land document collections often have duplicates — same file uploaded to
multiple folders with different names. Detect these before building the sheet:

```python
from collections import defaultdict

# Group by file size
by_size = defaultdict(list)
for f in all_files:
    sz = f.get('size', '0')
    by_size[sz].append(f)

# Flag groups where same size + similar normalized name
for sz, files in by_size.items():
    if len(files) > 1:
        names = [f['name'] for f in files]
        # Normalize: remove parenthetical suffixes like (1), (2)
        base_names = set()
        for n in names:
            base = re.sub(r'\s*\(\d+\)', '', n).strip().lower()
            if base in base_names:
                # Duplicate found!
                pass
            base_names.add(base)
```

**What constitutes a duplicate for land documents:**
- Same file size AND same normalized name (after stripping `(1)`, `(2)` suffixes)
- Same file size AND same content hash (for different descriptive names)
- Files named `XXX (1).pdf` alongside `XXX.pdf` — these are almost always identical copies
- **Same Registration Number (RMN) across files** — This is the most reliable
  dedup signal. Extract RMN patterns from filenames and group by RMN value.
  Even if names differ completely, the same RMN means the same registered
  document.
- **Same Reg No in different Sy No folders** — An agreement of sale or GPA
  bearing the same RMN found in two different Sy No folders is the SAME
  document, not a different one. Flag in the Master Sheet Remarks column:
  `DUPLICATE - also filed in Sy No X`.

**Handling:**
- Keep one copy (prefer the version with the best descriptive name or the one in the most-specific folder)
- In the Master Sheet, list the document once. Note the alternative location in Remarks
- When copying to the cleaned folder, only copy one instance of each duplicate group

**Common duplicate patterns encountered:**
| Pattern | Example | Action |
|---|---|---|
| Same name + parenthetical suffix | `202605221553.pdf` + `202605221553 (1).pdf` | Keep first, skip (1) |
| Same file across two unsorted folders | `111_1.pdf` in "Survey Nos wise" + `111_1 (1).pdf` in "Scanned for Index" | Keep descriptive name version |
| Same file at root + in folder | `Sy No 87 Form 1 dated 9.8.1938.pdf` in root + same in folder | Keep folder version |
| Same content, different descriptive names | `Lakshmipura 103.pdf` vs `Lakshmipura 103 (1).pdf` vs `Lakshmipura 103 (2).pdf` | Check size — if same, keep one |

#### Kannada OCR for Timestamp-Named Land Documents

Many scanned land documents have timestamp-only filenames (e.g.,
`202605261825.pdf`). Without OCR, these can't be classified by document type.
OCR them to identify if they're MR (Mutation Register), EC, RTC, or other
documents.

**Setup:**

```bash
# 1. Download Kannada traineddata for tesseract
python3 -c "import urllib.request; urllib.request.urlretrieve('https://github.com/tesseract-ocr/tessdata/raw/main/kan.traineddata', '/opt/data/kan.traineddata')"

# 2. Copy English + Hindi from system
cp /usr/share/tesseract-ocr/5/tessdata/eng.traineddata /opt/data/
cp /usr/share/tesseract-ocr/5/tessdata/hin.traineddata /opt/data/

# 3. Set TESSDATA_PREFIX before running OCR
export TESSDATA_PREFIX=/opt/data
```

**OCR + classification function (Kannada keyword-based):**

```python
import pytesseract, fitz
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def ocr_classify(fid, name):
    request = drive.files().get_media(fileId=fid)
    content = request.execute()

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(content); tmp_path = tmp.name

    text = ""
    doc = fitz.open(tmp_path)
    # Try text layer first
    for page in doc:
        text += page.get_text()
    # Fall back to OCR if no text layer
    if not text.strip():
        for page_num in range(min(len(doc), 2)):
            pix = doc[page_num].get_pixmap(dpi=250)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text += pytesseract.image_to_string(img, lang='eng+kan+hin')
    doc.close()
    os.unlink(tmp_path)

    t = text
    # Kannada keywords (from actual OCR on Ramanagar land records)
    if re.search(r'ಮ್ಯುಟೇಶನ್|ಮ್ಯೂಟೇಶನ್|MUTATION', t):     return 'Mutation Register (MR)', 8
    if re.search(r'ಎನ್‌ಕಂಬರ್|ENCUMBRANCE', t):                return 'Encumbrance Certificate (EC)', 9
    if re.search(r'ಪಹಿವಾಟು|PAHIVAT|RTC', t) and \
       not re.search(r'MUTATION|ಮ್ಯುಟೇಶನ್', t):               return 'RTC', 1
    if re.search(r'ಖರೀದಿ|SALE\s*DEED|ಮಾರಾಟ', t) and \
       re.search(r'ರಿಜಿಸ್ಟ್ರಾರ್|ಸಬ್', t):                      return 'Sale Deed', 5
    if re.search(r'GRANT|SAGUVALI|ಅನುದಾನ|ಗ್ರಾಂಟ್', t):        return 'Grant / Title Deed', 3
    if re.search(r'ತಿಪ್ಪಣಿ|TIPPANI', t):                       return 'Tippani', 19
    if re.search(r'ಹಿಸ್ಸಾ|HISSA', t):                           return 'Hissa Atlas', 18
    if re.search(r'ನಕ್ಷೆ|MAP', t):                               return 'Village Map', 22
    if re.search(r'ಕಾರ್ಡಾ|KARDA|KARAD', t):                     return 'Karda', 23
    if re.search(r'ವರ್ಗೀಕರಣ|CLASSIFICATION', t):                return 'Land Classification', 11
    if re.search(r'ತಹಶೀಲ್ದಾರ್|TEHSILDAR', t):                    return 'Tehsildar Endorsement', 12
    if re.search(r'ಕಂದಾಯ|REVENUE', t):                           return 'Revenue Document', 8
    return 'Unidentified', None
```

**Pitfall — OCR throughput:** OCR at 250 DPI takes ~10–30 seconds per file
depending on page count. Processing 180+ files sequentially in one terminal
session will timeout (180s limit). Strategies:
- Process only small files (<2 MB) which are typically 1-page MR/EC/RTC docs
- Batch 5–10 files per invocation
- Prioritize the Sy No folders the user cares about most
- **Mark large timestamp files as `Needs OCR review` in the sheet** rather
  than blocking on them

**Pitfall — Kannada tesseract setup requires non-root tessdata install:** The
system `/usr/share/tesseract-ocr/5/tessdata/` is not writable. Download
kan.traineddata to `/opt/data/` and set `TESSDATA_PREFIX=/opt/data`. Copy
eng.traineddata and hin.traineddata there too — tesseract loads ALL languages
from the same directory.

See `references/kannada-land-doc-ocr-patterns.md` for the complete keyword
mapping table.

#### Name Normalization After Multiple Rename Passes

When you run the rename script more than once (e.g., first pass with `Sy302`
no-space format, second pass with `Sy 302` with-space format), some files may
retain the old format because they were in different folders at rename time.

After ALL bulk renames complete, run a normalization sweep:

```python
# Fix SyXXX -> Sy XXX (missing space pattern)
new = re.sub(r'\bSy(\d+)', r'Sy \1', old)

# Fix double RMN artifacts (reg number appearing twice)
# e.g. "RMN-1-04889-2020. RMN-1-04889-2020-21" -> "RMN-1-04889-2020-21"
new = re.sub(r', (RMN[^,]+)\. (RMN\1)', r', \1', new)

# Fix trailing dot before extension
new = re.sub(r'\s+\.pdf', '.pdf', new)
```

Also fix hyphens that should be slashes in Sy No sub-divisions
(`Sy 87-3` → `Sy 87/3`):
```python
new = f['name'].replace('Sy 87-3', 'Sy 87/3')
```

#### RMN-Based Cross-Folder Duplicate Detection

Registration numbers (RMN) are the most reliable dedup signal. Two files with
the same RMN number are ALWAYS the same registered document, even if they
appear in different Sy No folders or have different filenames.

```python
from collections import defaultdict

# Build RMN -> files map across ALL folders
rmn_map = defaultdict(list)
for f in all_files_on_drive:
    for m in re.findall(r'RMN[-\s]?\d+(?:[/-]\d+)?', f['name'], re.IGNORECASE):
        rmn_map[m.upper().replace(' ', '')].append(f)

# Report cross-folder duplicates
for rmn, files in rmn_map.items():
    if len(files) > 1:
        sy_nos = set()
        for f in files:
            m = re.search(r'Sy\s*(\d+(?:/\d+)?)', f['name'])
            if m: sy_nos.add(m.group(1))
        if len(sy_nos) > 1:
            print(f"RMN {rmn} spans Sy Nos: {', '.join(sorted(sy_nos))}")
```

**Handling cross-Sy-No RMN duplicates:**
- **The same RMN in different Sy No folders** — This is the SAME registered
  document, NOT two separate documents. A Sale Deed or Agreement of Sale with
  a single RMN covers the properties specified in its schedule, which may
  span multiple survey numbers.
- **In the Master Sheet**, list the document in BOTH Sy No tabs (since it's
  relevant to both), but flag the Status column: `DUPLICATE - same doc as
  Sy No X` or `DUPLICATE - also filed in Sy No Y`
- **Do NOT deduplicate across Sy Nos** — only deduplicate within the same Sy
  No folder. Cross-Sy-No RMN matches are legitimate references.
- **Within the same folder**, if two files share the same RMN, keep one as
  primary and rename the other with `(DUPLICATE COPY)` suffix.

**Pitfall — Same RMN + same file size in the same folder equals same file:**
If two files in the same Sy No folder have the same RMN AND the exact same
file size (within 1%), they are the identical document uploaded twice. Rename
one as `(DUPLICATE COPY)`.

See `references/survey-wise-land-doc-organization.md` for the full worked
example from the Ramanagar project.

### 9. Document Filing & Notification Workflow (Vinod)

When Vinod uploads an individual property document (e-Khata, sale deed, EC,
NOC, tax receipt) and asks you to file it on Drive with a WhatsApp
notification to Nishant:

1. **Extract metadata** from the document (date, owner, property code, doc type, reg number)
2. **Name it** following DRAAS convention: `YYYYMMDD_PropertyCode_Owner_Description.pdf`
3. **Find the correct Drive folder** based on the document type and lifecycle stage
4. **Present filename + folder for Vinod's approval** — never upload without confirmation
5. **Upload once approved**, generating the public Drive link
6. **Generate WhatsApp draft** via `whatsapp_link` tool for Nishant with document details + Drive link

See `references/e-khata-filing-workflow.md` for the full workflow with folder
hierarchy map, naming examples, WhatsApp link construction rules, and Kannada
e-Khata extraction notes.

### 10. BBMP Memorandum — Parent PID/Khata Bifurcation Draft

When a user uploads a BBMP Memorandum template (requesting bifurcation of
parent PID/Khata into individual e-PIDs/e-Khatas) and asks you to "review all
related documents and make a draft in column/row wise format":

1. **Extract the template** — read the `.docx` paragraphs and tables to identify all blank fields
2. **Search Drive** — find project-specific documents (Area Statement, Khata Certificate, Plan Sanction, Tax Receipt, CoI) via `gws_auth.build_service("drive", "v3")`
3. **Identify which project** the template relates to (Ranka Iris, Ranka Amber, BuxRanka) from context or user input
4. **Present as a draft table** with columns: `# | Section | Field | Template Content | Draft / Proposed Content | Source / Remarks`
5. **Mark missing data** clearly — distinguish confirmed data from gaps that need user input
6. **Wait for user confirmation** before generating the final filled document

See `references/bbmp-memorandum-bifurcation-draft.md` for the full workflow
including template structure, search strategy, table format template,
pitfalls, and examples. This technique generalizes to any legal template
where the user wants a structured analysis alongside proposed content.

#### Prakash Working Preferences (for this task type)

- **Show sample first:** Before committing to bulk operations (moving 100s of files, renaming in Drive, populating sheets), present a concrete sample of the output format and a clear step-by-step process. Let him approve before execution.
- **Detail-driven:** Every component must be traceable — filename, date source, classification logic. Do NOT introduce assumed values.
- **Correction precision:** When he corrects data (village name, Sy No mapping), both the old and new values matter — record the mapping accurately. He corrects sharply; accept and update.
- **Master Sheet is the deliverable:** The sheet with document links and gap analysis is more important than Drive folder restructuring. Links work regardless of folder location.
- **Naming convention uses document date, not file timestamp:** Date must come from the document content.
- **Cleaned folder, not modified originals:** He explicitly requests that original Drive data is NOT touched. Create a SEPARATE "Cleaned" folder with renamed copies, leaving the original structure intact.
- **Confirm village names with domain expert:** Village names are critical for accuracy. Present your mapping for confirmation before committing to file naming. He will correct errors sharply — accept the correction and update all documentation.
- **Oldest-first sort:** Documents within each category MUST be sorted ascending by date (oldest first). Undated files go last within their category.
- **Sub-heading grouping:** Within each main category (A–H), documents must be grouped under logical sub-headings. For Title Documents: "Grants / Title Deeds / Deeds (Form 1 to 7)" covers Forms 1–7, Grant Orders, Title Deeds. Sub-heading rows use `>> Sub-heading Name` format.
- **Available AND missing:** Both available files AND missing required documents must be listed under each sub-heading. Missing items get `MISSING: [doc name]` rows so the user can see the complete picture at a glance.
- **Clear-before-write when iterating:** When rewriting multiple sheet tabs in a loop, always `clear()` before `update()` to prevent stale data artifacts from previous iterations.
- **Dedup is multi-pass, not single-pass:** Prakash will find duplicates you missed even after you think you've checked. Do NOT rely on RMN-only matching. Run dedup checks in this order: (1) RMN cross-folder, (2) file-size cross-folder (same size in different folders = likely same doc), (3) EC date-range duplicate (same date range in same Sy No = duplicate EC), (4) same-folder same-size + normalized-name match. Present dedup results explicitly — if he says "I can see many same document is repeated", go back and run checks (2) and (3) which you likely skipped.

## Related Skills

- `karnataka-rera-collector` — statutory RERA registration/promoter/units data for Karnataka projects (complementary: title DD for ownership, RERA for project registration)
- `legal-document-drafting` — if due diligence findings lead to drafting agreements
- `rera-compliance` — if project-level RERA compliance is also needed
- `maps` — for property location geocoding and area assessment
- `ocr-and-documents` — for extracting text from scanned legal document PDFs

## References

**Title due diligence (primary):**
- `references/bbmp-pid-formats.md` — Detailed explanation of old PID vs new ePID formats (with Vinod's correction documented)
- `references/company-verification-workflow.md` — Full QuickCompany extraction workflow with save-to-file pattern, appointment date extraction, and director detail pages
- `references/ec-compilation-merging.md` — Workflow to download, organize, and merge multiple EC PDFs into a single printable document
- `references/ec-mr-date-extraction-patterns.md` — EC date range extraction from DDMMYYYY filenames, MR number + year range extraction from original filenames, RMN-based cross-folder duplicate detection, and name normalization patterns after multiple rename passes. Includes critical pitfalls for regex-on-already-renamed-files.
- `references/e-khata-filing-workflow.md` — Document filing & WhatsApp notification workflow (Vinod), folder hierarchy map, naming examples
- `references/kannada-land-doc-ocr-patterns.md` — Complete Kannada OCR keyword mapping table for Karnataka land documents (MR, EC, RTC, Sale Deed, GPA, Tippani, etc.) with classification priority, performance notes, file size heuristics, and setup commands for kan.traineddata
- `references/ranka-iris-document-set.md` — Worked example: complete Ranka Iris 25-document legal set with file paths, index mapping, and revenue document chain
- `references/required-docs-procurement-sources.md` — The "Obtain From" column from Prakash's PDF: where each of the 34 required document types is procured (Tahsildar Office, Sub-Registrar Office, ADLR Office, Gram Panchayat, etc.)
- `references/survey-wise-land-doc-organization.md` — Full worked example from the Ramanagar project: Sy No extraction regex, Drive inventory structure, folder creation, file move patterns, naming convention examples, master sheet format, and rename execution details
- `references/bbmp-memorandum-bifurcation-draft.md` — BBMP Memorandum template analysis with draft column workflow: extract template blanks, search Drive for project data (Area Statement, Khata, Plan Sanction), present as row/column table with proposed content, wait for user confirmation before generating final document
- `references/rtc-mutation-columns-explained.md` — Karnataka RTC/mutation columns explained
- `references/rtc-extraction.md` — RTC extraction patterns
- `references/rtc-phase-totals-sheets.md` — RTC phase totals sheets
- `references/kaveri-ec-parsing.md` — Kaveri EC parsing
- `references/karnataka-land-statutes.md` — Karnataka land statutes
- `references/tn-title-document-matrix.md` — TN title document matrix
- `references/tn-title-flow-chart-diagram` — TN title flow chart diagram
- `references/tn-title-part-v-flow-on-title` — TN title Part V flow on title
- `references/land-doc-read-and-file.md` — Reading and filing land documents (Kannada)
- `references/plot-allotment-verification.md` — Plot allotment verification
- `references/lawyer-requisition-checklist-tracking.md` — Lawyer requisition checklist tracking
- `references/requisition-checklist-reconciliation.md` — Requisition checklist reconciliation
- `references/scan-orientation-verification.md` — Scan orientation verification
- `references/scanned-pdf-ocr-and-signed-doc-verification.md` — Scanned PDF OCR and signed doc verification
- `references/drive-filing-owner-move-workflow.md` — Drive filing: owner move workflow
- `references/drive-filing-ownership-pitfalls.md` — Drive filing: ownership pitfalls
- `references/drive-filing.md` — Drive filing
- `references/google-drive-search.md` — Google Drive search

**Other DRAAS references (kept from the old umbrella index):**
- GWS Identity: `references/gws-account-identity.md`, `references/gws-account-identity-investigation.md`, `references/gws-api-quirks.md`
- Drive: `references/drive-permission-expiry-pitfalls.md`, `references/drive-photo-categorization.md`
- GWS Automation: `references/gws-automation.md`, `references/gws-drafts-and-drive-expiry.md`, `references/gws-docs-html-import.md`, `references/gws-doc-comments-review.md`, `references/gws-comments-calendar-drafts.md`, `references/docs-api-editing.md`, `references/docusaurus-docs-extraction.md`
- Gmail: `references/gmail-api-pitfalls.md`, `references/gmail-bounce-cleanup.md`, `references/gmail-dsn-cron-cleanup.md` (+ `scripts/gmail_trash_query.py`)
- Contacts: `references/contacts-management.md`, `references/contacts-registry.md`
- Kelsa: `references/kelsa-land-proposal-lookup.md`, `references/kelsa-misc-budget-analysis.md`, `references/kelsa-misc-budget-engineering.md`, `references/kelsa-misc-budget-engineering-focus.md`
- JDA: `references/jda-offer-letter-workflow.md`, `references/jda-offer-letter-plain-proposal.md`, `references/jda-offer-letter-production-notes.md`, `references/jda-addendum-refund-analysis.md`
- MOU: `references/mou-drafting-workflow.md`, `references/mou-aggregator-deal.md`
- Market Research: `references/market-research-deck.md`, `references/market-research-deck-workflow.md`, `references/grok-image-generation.md`, `references/pptx-deck-building.md`
- Master Plan: `references/master-plan-annotation.md`, `references/phone-safe-plan-delivery.md`
- Not-Spam: `references/not-spam-whitelist.md`, `references/not-spam-whitelist-daily-run.md` (+ `scripts/not_spam_check.py`)
- E-Commerce: `references/indian-ecommerce-availability.md`
- Other: `references/inventory-sheet-extraction.md`, `references/geocoding-methodology.md`, `references/mymaps-kml-roundtrip.md`, `references/whatsapp-link-pitfalls.md`, `references/portal-listing-capture.md`, `references/pricing-triangulation-recipe.md`, `references/medical-report-analysis.md`, `references/medical-readouts-and-openrouter-vision.md`, `references/employee-offer-payment-whatsapp.md`, `references/magicbricks-leads-camp-format.md`, `references/tailor-talk-format.md`
