---
name: property-legal-analysis
description: |-
  Analyse property legal documents — sale deeds (apartment & plotted development),
  declarations, allotment letters, title documents — using dual-model legal reasoning
  (Claude Opus + DeepSeek) and document cross-referencing. Covers both Karnataka
  and Tamil Nadu property law. Trigger:
  "find the sale deed", "analyse the [deed/declaration/letter]",
  "read the car parking clause", "get both models to opine",
  "compare these legal documents",
  "review this plot sale deed", "check this template".
metadata:
  hermes:
    tags: [bangalore, property, legal, sale-deed, deed-of-declaration, legal-opinion, multi-model]
    related_skills: [karnataka-land-title-due-diligence, property-title-due-diligence, bengaluru-town-planning, google-workspace, ocr-and-documents]
category: research
version: 1.0.0
author: Hermes (from session analysis)
---

# Property Legal Document Analysis — Bangalore & Tamil Nadu

Workflow for finding, extracting, analysing, and compiling legal opinions on property documents from Karnataka and Tamil Nadu, using dual-model reasoning.

This skill is for a SINGLE-DOCUMENT clause question (UDS/area figures, parking clause, lease terms, GPA/TDR authority) with dual-model opinion. When the ask spans a full title/possession/encumbrance/survey investigation across a document set, use `karnataka-land-title-due-diligence` instead.

## 1. Trigger Conditions

Activate when the user asks to:
- "Find the [sale deed / deed of declaration / allotment letter] for [property]"
- "What is the UDS / super built-up area / scheduled property area in this sale deed?" /
  "what are the three figures mentioned?" — the three-figure area extraction; load
  `references/deed-area-figures-extraction.md`
- "Analyse whether [specific issue] is covered in this document"
- "Read this document and tell me if [specific clause exists]"
- "Get [model A] and [model B] to opine on this"
- "Compare these two legal documents" / "compare this deed against a template"
- "Check this plot sale deed / sale deed template"
- "Review this [deed/agreement/contract] for [plot/flat/villa]"
- "What's missing from this sale deed?"
- "Issue a detailed note / legal opinion on [topic]"
- "Check the mortgage/investor situation"
- Any request involving property legal documents in Bangalore or Tamil Nadu
- "Check this construction agreement" / "review this construction agreement"
- "Is <person> a signatory to the original JDA / the addendum / the GPA?" /
  "what's the full list of landowners?" / "which index and which row?" /
  "who has to attend the registration?" — party & signatory verification from
  executed deeds. Load `references/jda-addendum-party-signatory-verification.md`
- "When does the lease terminate for [property]?" / "how many years left on the lease" / "check the lease end date" (see `references/lease-deed-term-extraction.md`)
- "Pull me the details of the lease agreement we have executed" / "what are the lease terms" / "give me the rent, deposit and notice period" / "is this lease registered?" — full executed-lease **term sheet** + stamping/registration compliance check (see `references/lease-term-sheet-and-stamping-compliance.md`)
- "Can the tenant extend / stay after the lease expires?" / "does this lease let them renew against the owner's will?" / "tenant vacate risk before we take the building" — lease renewal/extension risk (see `references/lease-renewal-extension-risk.md`)
- "Does this construction agreement cover everything?"
- "Draft a construction agreement for [plot/villa]"
- "Does the GPA / Power of Attorney cover applying for TDR?" / "Can the GPA holder sign the TDR affidavit and Form IV?" / "Authority analysis: GPA vs KTCP Act / TDR" — see references/gpa-authority-tdr-analysis.md

## 2. Document Discovery & Retrieval

### 2.0 Document Discovery Strategy

When the user asks to find a property document, start with a **broad multi-source discovery pass**:

1. **Gmail first** — search with multiple keyword variants (project name, unit number, developer, abbreviated names). Gmail often has transaction history even when Drive doesn't have the scanned deed.
2. **Google Drive** — search by name and fullText with multiple query variations.
3. **WILL / Asset Schedule documents** — check the DR WILL and Schedule A & B Assets List.
6. **Parent folder browsing** — once any related file is found, check its parent folder for grouped documents. This is critical for filing: the parent folder is likely where the current document should also go.
7. **Pre-filing folder search** — before saving the output, search Drive for the correct project-specific folder using sibling document names. See P4 for the full workflow. Do NOT default to TMP.
8. **NDR DRAAS Contact Sheet** — for broker/agent contacts.

**Gmail search queries pattern:**
```python
from tools.gws_skill_bridge import call as gws
queries = [
    f"'{project_name}' sale deed",
    f"'{project_name}' unit {unit_number}",
    f"'{developer_name}' '{project_name}'",
]
for q in queries:
    r = gws("gmail_search", query=q, max=5)
```

### 2.1 Search Google Drive

Use `build_service('drive', 'v3', service_name='google-draas')` for NDR's primary account.

```python
from tools.gws_auth import build_service
s = build_service('drive', 'v3', service_name='google-draas')

# Search by document name
for q in [
    "name contains 'Sale Deed' and fullText contains 'Embassy'",
    "name contains 'Deed of Declaration' and fullText contains 'Embassy Habitat'",
    "fullText contains '1503' and fullText contains 'Embassy'",
]:
    r = s.files().list(q=q, spaces='drive', pageSize=10, fields='files(id,name,mimeType,size)').execute()
```

**Key patterns for search queries:**
- `name contains` + `fullText contains` — double filter for property-specific docs
- `name contains 'Sale Deed'` — exact document type
- Try multiple query variations — the right document often matches different keywords
- Look for date prefixes in filenames (`20100802_EmbassyHabitat1503_SaleDeed_NDR.pdf`)

### 2.2 Download PDF

```python
import requests
token = s._http.credentials.token
r = requests.get(f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media',
                 headers={'Authorization': f'Bearer {token}'})
with open('/tmp/local_copy.pdf', 'wb') as f:
    f.write(r.content)
```

Do NOT use `web_extract` for Drive PDFs — it returns text only. Use the Drive API for binary download.

**Simpler path — the skill bridge (verified 2026-09-26):**

```python
import sys; sys.path.insert(0, "/opt/hermes")
from tools.gws_skill_bridge import call
print(call("drive_download", file_id=FILE_ID, service_name="google-draas"))
```

The bridge is importable from **system `python3`** — `/opt/hermes/.venv/bin/python3`
is only needed when you import `googleapiclient` directly, not for the bridge.
Never hand-build Google credentials and never look for a token file; resolve the
account with `gws_resolve_account` and pass its `service_name` explicitly.

**PITFALL — the bridge IGNORES `output_path`.** It writes into the **current
working directory** using the Drive file's own name. If the CWD is not writable
(e.g. running from `/opt/hermes`) it raises
`PermissionError [Errno 13] ... /opt/hermes/<filename>`. Always `cd` to a
writable scratch dir first:

```bash
cd /tmp && python3 /tmp/dl.py
```

**PITFALL — `pdftotext` before OCR.** Adobe Scan PDFs carry an OCR text layer,
so `pdftotext -layout <file> -` extracts the English clauses cleanly even
though the document looks like a pure scan. Kannada runs come out as garbage
characters — that is expected, not a failure. Only fall back to
pymupdf/tesseract rendering when `pdftotext` returns nothing. `pdfinfo` gives
the page count in one shot.

## 3. Text Extraction

### 3.1 Text-based PDFs (pymupdf)

```python
import fitz
doc = fitz.open('/tmp/document.pdf')
for page in doc:
    text = page.get_text()
    if text.strip():
        print(f'--- PAGE {page.number+1} ---')
        print(text)
```

### 3.2 Import name note

In newer versions of pymupdf (>1.24), the import is `import pymupdf`; in older versions it's `import fitz`. The package name is `pymupdf` either way. If one import fails, try the other.

### 3.3 Scanned/Image PDFs (pymupdf + tesseract)

When `page.get_text()` returns empty strings, the PDF is a scanned image. Use tesseract OCR:

```python
import fitz, tempfile, os
doc = fitz.open(path)
for i in range(doc.page_count):
    page = doc[i]
    pix = page.get_pixmap(dpi=200)  # 200 DPI is adequate for printed legal documents
    img_bytes = pix.tobytes('png')
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(img_bytes)
        img_path = f.name
    text = os.popen(f'tesseract \"{img_path}\" stdout --psm 6 -l eng 2>/dev/null').read()
    os.unlink(img_path)
    print(f'--- PAGE {i+1} ---')
    print(text)
```

**Tesseract settings for legal documents:**
- `--psm 6` — treat as uniform block of text (good for single-column)
- `--psm 4` — treat as single column of text (alternative)
- `-l eng` — English language
- DPI 200 is sufficient for printed legal documents at readable font sizes
- (Optional) Use `--psm 3` for fully automatic page segmentation for mixed layouts

### 3.3 OCR for large documents (Deed of Declaration pattern)

For 70+ page scanned documents:
- Process in batches of ~10 pages
- Print page number header between each page for reference
- Use preview of first 10 pages to identify the document structure (definitions, schedules, signatures)
- Focus OCR on sections with parking/car/transfer/clause keywords

```python
import fitz, tempfile, os
doc = fitz.open(path)
for i in range(min(15, doc.page_count)):  # First pass: preview structure
    page = doc[i]
    pix = page.get_pixmap(dpi=200)
    # ... OCR as above
```

## 3.5 Plotted Development Sale Deed Analysis

### 3.5.1 Plot-Only vs Apartment Sale Deed — Key Differences

When analysing a **plotted development** (bare land / residential plot) sale deed, the structure differs fundamentally from an apartment/flat sale deed:

| Aspect | Apartment Sale Deed | Plot Sale Deed |
|--------|-------------------|----------------|
| **Subject** | Undivided share of land + specific apartment + parking | Specific plot of land only |
| **Common areas** | Defined in Deed of Declaration, shared ownership | Roads/parks gifted to government via Gift Deed |
| **Construction** | Covered within the sale deed value | Covered by separate **Construction Agreement** |
| **Consideration split** | Single price covering land + building | Land value in sale deed; construction value in separate agreement |
| **Ownership form** | Undivided share in land + superstructure | Absolute ownership of specific plot (separate patta possible) |
| **Association** | Usually governed by Deed of Declaration / Bye-laws | Covered by separate **Association Agreement** (clubhouse, amenities, maintenance) |
| **RERA** | Single RERA registration for project | Plot layout registered under RERA; construction registered separately |
| **Defect liability** | 5 years per Section 14(3) RERA (structure) | Limited to civil infrastructure (roads, drains) unless construction is included |

### 3.5.2 The Tripartite Structure (DRA Group convention for villa projects)

For DRA Group's plotted villa developments (Ranka Oasis, Ranka Udaya, etc.), the transaction is structured as **three separate agreements**:

```
┌─────────────────────────────────────────────────┐
│  1. SALE DEED (Absolute Sale)                   │
│     → Transfers plot ownership to purchaser      │
│     → Consideration = plot land value only       │
│     → Registered at Sub-Registrar                │
│     → TNRERA-registered project                  │
└─────────────────────────────────────────────────┘
                        +
┌─────────────────────────────────────────────────┐
│  2. CONSTRUCTION AGREEMENT                      │
│     → Builder constructs villa on the plot       │
│     → Consideration = ₹X/sq ft of built-up area  │
│     → Must capture ≥₹1,100/sq ft (user's floor)  │
│     → Separate RERA registration (if applicable) │
│     → Separate payment schedule                  │
└─────────────────────────────────────────────────┘
                        +
┌─────────────────────────────────────────────────┐
│  3. ASSOCIATION AGREEMENT                       │
│     → Covers clubhouse, common amenities         │
│     → Maintenance, upkeep, rules                 │
│     → Transfer of clubhouse land to association  │
│     → Monthly/quarterly maintenance charges      │
└─────────────────────────────────────────────────┘
```

**Critical drafting implication for the Sale Deed:**
- The consideration must reflect only the **land value** — construction and amenity values are captured separately
- No clause should inadvertently bundle construction obligations into the sale deed
- If mortgage existed against the project land, the discharge must be **completed before** or **simultaneous with** the sale deed registration
- **User preference (Nishant Ranka):** Do NOT add an explicit "plot-only" recital — the sale deed is a total consideration for the plot. Construction value stays strictly in the Construction Agreement. Keep it simple.

**Recital note for plot-only sale deed (user preference — DRA Group):**
> Inclusion of an explicit "plot-only" recital is optional. The user (Nishant Ranka) prefers to keep the sale deed simple — the total consideration covers the plot, and construction is purely a separate agreement matter. Do NOT add a plot-only recital unless the user explicitly asks for it.

### 3.5.3 Mortgage / Investor Due Diligence for Plot Sales

When the project land had prior investor mortgages (common pattern — investors lend via Simple/Joint Mortgage, plots are sold after mortgage discharge):

**Checklist:**
1. Identify all mortgages on the project land (joint/simple mortgages, investor agreements)
2. Verify existence of registered **Discharge Receipt** / Deed of Cancellation of Mortgage
3. **TIMING CRITICAL**: Discharge must predate (or be simultaneous with) plot sale deed execution
4. If sale deed date is BEFORE discharge date: the "no subsisting mortgage" representation in the deed is technically false at execution time
5. If the mortgage was on specific undivided shares (UDS) only, verify whether the specific plot falls within the mortgaged UDS
6. Recommend: include a specific recital about the mortgage and its discharge for transparency

**Documents to check:**
| Document | What it proves |
|----------|---------------|
| Joint Simple Mortgage Deed | Loan amount, mortgaged land description, UDS extent |
| Individual Investment Agreements | Terms of investor's loan/return |
| Discharge Receipt / Release Deed | Mortgage fully satisfied, investors paid |
| Encumbrance Certificate (EC) | Official record confirming no subsisting encumbrances |

### 3.5.4 Plot Sale Deed — Checklist of Essential Clauses

Compare any plot sale deed against this checklist:

| # | Clause | Purpose | Status |
|---|--------|---------|--------|
| 1 | Parties with full IDs (Aadhaar, PAN) | Identify parties | ✅ Mandatory |
| 2 | Recitals — title chain | Prove vendor's ownership | ✅ Mandatory |
| 3 | Recitals — layout approvals | Show statutory compliance | ✅ Mandatory |
| 4 | Recitals — RERA registration | RERA Act compliance | ✅ Mandatory |
| 5 | Sale consideration | Price agreed | ✅ Mandatory |
| 6 | Payment acknowledgment | Receipt confirmed | ✅ Mandatory |
| 7 | Conveyance clause | Title transfer | ✅ Mandatory |
| 8 | Delivery of possession | Physical handover | ✅ Mandatory |
| 9 | Vendor's title warranty | Seller guarantees clear title | ✅ Mandatory |
| 10 | Covenant against encumbrances | No mortgages/liens | ✅ Mandatory |
| 11 | Indemnity clause | Seller compensates buyer for title defects | ✅ Mandatory |
| 12 | Further assurance | Seller signs future docs if needed | ✅ Recommended |
| 13 | Vendee's acknowledgments | Buyer confirms due diligence, legal advice | ⚠️ Important |
| 14 | Governing law / jurisdiction | Which courts hear disputes | ⚠️ Important |
| 15 | Litigation disclosure | Any pending cases affecting title | ⚠️ Important |
| 16 | TDS compliance | Section 194-IA for >₹50L | ⚠️ Important |
| 17 | Patta mutation consent | Revenue records transfer | ✅ Mandatory |
| 18 | Plot-only declaration | Excludes construction/amenities from deed | ❌ Optional — user prefers not to add unless asked |
| 19 | Schedule of documentary evidence | Full chain with doc numbers | ⚠️ Important |
| 20 | General provisions | Entirety, severability, no waiver, amendments | ⚠️ Recommended |
| 21 | Gift Deed for roads/parks | Govt. conveyance of common areas | ✅ Mandatory |
| 22 | Witnesses (2) | Attestation | ✅ Mandatory |

### 3.5.5 Construction Agreement — Essential Clauses for Villa Projects (DRA Group Pattern)

When reviewing or drafting a **Construction Agreement** for a plotted villa project (the second document in the tripartite structure from 3.5.2), use the following clause framework. This is NOT an apartment sale deed — it is a standalone building contract between the plot owner (Allottee) and the Developer/Promoter acting as building contractor.

#### Recital Structure (A→H, in order)

| Recital | Content | Notes |
|---------|---------|-------|
| A | Promoter's ownership of project land (acreage as **Phase 1**, not "out of larger layout") | Remove all references to "larger layout" / "Larger Property" |
| B | Derivation of title for the specific survey containing the plot | Sale deed reference, document number, parties |
| C | Scheme of villa development + layout approval (HNDTA/DTCP letter no.) | Includes approval authority, date, and order number |
| D | Simultaneous Agreement for Sale for the divided share of land | Links to sister agreement |
| E | Engagement for villa construction (built-up area, configuration, floors) | Sets scope |
| F | Building permit in allottee's name + GPA to promoter for statutory filings | Regulatory mechanism |
| G | Upfront settlement of consideration | Full payment acknowledgment |
| **H** | **Approved layout plan details: ALL survey numbers from the approval order + plot number with its dimensions per the approved plan** | **Critical addition** — ties the plot to the statutory approval, not to Schedule A's land description |

**Recital H pattern:**
> "The Project has been granted layout planning approval vide [Order No.] dated [date] by [Authority] in respect of the project lands bearing Survey Nos. [full list]. As per the said approved layout plan, Plot No. [X] has been demarcated as a distinct residential plot admeasuring [Y] Sq. Ft., with boundaries as set forth in SCHEDULE 'B'."

#### Operative Clauses — Standard Framework

| # | Clause | DRA Group Standard |
|---|--------|-------------------|
| 1 | Engagement & Scope | Itemised scope (excavation → compound wall → utility piping). References Schedule D specs + Annexure drawings. |
| 2 | Construction Consideration | Fixed ₹X total. GST at 5% composite (without ITC) stated separately. |
| 3 | Payment Details & Receipt | Full itemised breakdown: Construction Cost + GST = Total Received. **Annexure for transaction details** (cheque nos., dates, bank). Express acknowledgment of receipt. |
| 4 | Completion Period | **18 months** from Sale Deed registration + **6-month Grace Period**. |
| 5 | Force Majeure | Standard events + utility-connection delays (electricity/water from govt despite timely application). 30-day written notice. |
| 6 | Site Inspection & Updates | Allottee inspection rights during working hours. Promoter sends written/email/digital progress updates. |
| 7 | Composite Transaction | Explicit interdependence with Agreement for Sale. Construction operative only upon Sale Deed registration. |
| 8 | No Third-Party Builder | Allottee cannot engage other contractor until formal possession handover. |
| 9 | Possession & Snags | Notice of Intimation → 15-day joint inspection → 30-day snag rectification → Possession Letter. Deemed possession after 30 days. |
| 10 | Defect Liability | **(a) 5 years structural** (RERA Sec 14(3) — foundation, columns, beams, slabs). **(b) 1 year non-structural** (finishes, fittings, fixtures, workmanship). |
| 11 | Architectural Restrictions | No external facade alteration. Residential use only. Interior works allowed without structural damage. |
| 12 | **Allottee Default / Cancellation** | **No refund.** Promoter authorised to sell plot+villa to third party. Appropriation order: (i) construction costs → (ii) default charges → (iii) plot cost to allottee → (iv) surplus retained by promoter. |
| 13 | **Promoter Default** | **Mutual remedy** — (a) joint third-party sale at market price; OR (b) promoter within Grace Period either completes OR exits at market price for plot+constructed area. |
| 14 | Variation Order Mechanism | Allottee requests in writing → Promoter provides cost+timeline assessment → Variation Order signed by both. |
| 15 | Indemnity | Mutual — Promoter for title/labour/third-party claims; Allottee for default/taxes/aesthetic breach. |
| 16 | Assignment | Pre-possession requires Promoter consent + transfer fee. |
| 17 | Arbitration | **Sole Arbitrator mutually appointed** by both parties (not unilateral). Fallback: Civil Court on disagreement. |
| 18 | Jurisdiction | Local courts (project district / registration sub-district). |
| 19 | Boilerplate | Entire agreement, severability, amendments in writing signed by both. |

#### Required Schedules

| Schedule | Content |
|----------|---------|
| A | Total project land (acreage as Phase 1, all survey numbers — **no "larger/extending to"** language) |
| B | Said plot (plot no., dimensions, boundaries) |
| C | Villa description (built-up area nett/gross, FAR, floors, configuration) |
| D | Part I — Layout Infrastructure (roads, lighting, power, water, drainage, security, landscaping) + Part II — Villa Specifications (35+ row table: structure, joinery, flooring, painting, bathroom fittings, electrical, plumbing) |
| E | Common Area Maintenance scope (security, STP, housekeeping, gardening, DG) |
| F | Common Amenities (clubhouse, gym, sports, parks, infrastructure) |
| Annexure I | Building Plan Drawings (drawing numbers and dates for each floor) |
| Annexure II | Statement of Payments (individual cheque/transfer details) |

#### Google Docs Editing — Yellow Highlight Convention

For Construction Agreement edits, use **YELLOW** background (`rgbColor(1.0, 1.0, 0.0)`) for ALL additions and modifications — distinct from sale deed blue/red convention.

```python
YELLOW_HL = {
    'backgroundColor': {
        'color': {'rgbColor': {'red': 1.0, 'green': 1.0, 'blue': 0.0}}
    }
}
```

#### Common Pitfalls (Construction Agreement)

- **Blank completion period** — the most frequent gap. Must be concrete months + grace.
- **1-year-only defect liability** — insufficient. Must split 5yr structural + 1yr non-structural.
- **Unilateral arbitration** — "appointed by Promoter" is standard first-draft language; must change to mutual.
- **No refund clause** — with full upfront payment, explicitly state what happens on allottee cancellation.
- **No variation mechanism** — absolute "no modifications" clause is unrealistic in practice.
- **"Or Equivalent" in specifications** — gives Promoter unfettered discretion. Require allottee's written approval.
- **Blank compound wall spec** — often omitted from specs table despite being a major cost item.
- **"Larger layout" / "Larger Property" references** — must be replaced with "Phase 1." Unapproved future phases should not appear.
- **Survey number mismatch** — recital survey list must match the approved layout plan exactly.

## 4. Template Comparison Methodology

When the user asks to "check" or "compare" a draft sale deed against a best-practice template:

### Step 1: Load the reference template
Identify the most comprehensive existing deed for the same geography (same state, similar project type). For DRA Group TN plotted developments, the **Ranka Udaya Sale Deed** is the current best-practice template.

### Step 2: Build a clause-by-clause comparison
Create a comparison table with three columns:
- **Clause** (what it covers)
- **Current Deed** (present/partial/missing)
- **Template Deed** (how the template handles it)

Group by logical sections: Parties, Recitals, Operative Clauses, Covenants, Financial, Schedules, General Provisions.

### Step 3: Classify gaps
- **Critical** — legal validity issue, blank mandatory field, misrepresentation
- **High** — standard clause missing that creates risk
- **Medium** — boilerplate/general provisions missing

### Step 4: Research external standards
For each gap, check against:
- RERA-mandated clauses (Section 13, Form B, etc.)
- Standard TN/Karnataka conveyance practice
- Industry best practice from comparable projects

### Step 5: Present in priority order
Lead with critical fixes, then high priority, then medium. Always quote specific clause numbers from the current deed.

### Step 6: Verify project-specific details
Cross-check all factual details in the deed against:
- Approved layout plan (survey numbers, plot dimensions)
- Registered JDA/GPA chain
- TNRERA registration certificate
- Gift Deeds for roads/parks
- Encumbrance Certificate (EC)
- Mortgage discharge documents

### 4.1 Identify clause schema per document type

| Document Type | Key Sections to Check |
|---|---|
| **Apartment Sale Deed** | Schedule C (apartment description), Operative Clause, Rights & Obligations, Covenants, Schedules |
| **Plot Sale Deed** | Recitals (title chain + layout approvals), Schedule of Property (plot dimensions + boundaries), Consideration Clause, Vendor's Covenants (title warranty, encumbrance), Possession Clause, Patta Mutation Consent |
| **Deed of Declaration** | Para 4.x (floor plans), Para 5 (apartment definitions), Para 7 (common areas), Para 8-24 (restrictions and rights), Bye-laws (definitions) |
| **Allotment Letter** | Usually short — check consideration, reference to specific apartment, registration status |
| **Construction Agreement** | Recitals A-H (title → layout approval → plot → engagement → building permit → payment → approved plan with survey nos), Scope of Work, Consideration + GST breakdown + receipt acknowledgment, Completion Period (18mo + 6mo grace), Defect Liability (5yr structural + 1yr non-structural), Allottee Default (no refund + third-party sale mechanism), Promoter Default (mutual remedy), Variation Order Mechanism, Arbitration (mutual appointment), Schedules A-F + Annexures
| **Lease Deed / Lease-Cum-Construction** | Deed date (page 1 — may differ from filename's registration date), parties (lessor/lessees incl. firm name), operative term clause ("period … fixed for N years" — mid-document ~page 4), rent clause + from-date, extension clause, constructions-vest-with-lessor clause, schedule of property. See `references/lease-deed-term-extraction.md` for the scanned-deed workflow |
| **Association Agreement** | Clubhouse/common amenity rights, maintenance charges, usage rules, transfer mechanism |

### 4.2 Track cross-references

The Deed of Declaration is the **foundational document** — Sale Deeds and Allotment Letters must be read in light of it:
- Check Sale Deed recitals — they often reference the Declaration by registered document number
- Check if the Declaration defines "common areas" — then check if parking is in or out of that definition
- Check if the Declaration has onerous provisions (e.g., "undivided interest shall not be separated") and whether they apply to parking

## 5. Multi-Model Legal Analysis

### 5.1 When to use

Route to Claude Opus 4.8 or GPT-5.6 when the user explicitly asks for multi-model analysis, or when the legal question requires nuanced reasoning about:
- Distinguishing between competing interpretations of the same clause
- Applying Supreme Court precedent (e.g., *Nahalchand*)
- Explaining practical legal implications
- Issuing a formal legal opinion note

### 5.2 Prompt structure for legal analysis prompts

A good legal analysis prompt to a model should include:

1. **DOCUMENT 1**: Full clause text from the Sale Deed (with schedule/paragraph numbers)
2. **DOCUMENT 2**: Full clause text from relevant supplementary docs (allotment letters, etc.)
3. **DOCUMENT 3**: Full clause text from the Deed of Declaration
4. **Specific questions**: Numbered, with the exact legal issue stated
5. **Format requirements**: "Clause references required", "Categorical conclusion", "Practical implications"

### 5.3 Handling token limits

When `call_openrouter_model` hits the `max_tokens` limit (as Claude Opus 4.8 does easily on long legal opinions):
- Use a **continuation call**: call the same model again with the incomplete text as context, asking it to continue
- Split the analysis across multiple calls: Question 1 in one call, Question 2 in a second
- For very long analyses, use 3+ calls chained together with the last paragraph as context

### 5.4 Synthesis pattern

After getting model output, compile into a single structured note:
- Save as Markdown file locally
- Upload to Drive TMP folder
- Send the user a link and a concise summary at the beginning of the response

### 1.5 Survey-Number-Based Land Aggregation Document Discovery

When the user asks about a land aggregation project (MOU with aggregators, Schedule A of survey numbers), the document ecosystem is organised differently from individual sale deeds. A land aggregation project typically has 2-3 distinct online spreadsheets, plus per-survey-number document folders.

**Key spreadsheet types:**

| Type | Purpose | Typical columns |
|------|---------|----------------|
| **Legal Index** | All legal docs (RTCs, ECs, surveys) per survey number | Sl No, Sy No, Extent, Document Name & Link, Recipient |
| **LO Agreement Tracker** | Individual agreements between aggregator & each landowner | LO Name, Sy No, Extent, Amount, Agreement Link, RTC Link, Road Adjoining |
| **Cash Flow** | Financial model — phase-wise investment, sale proceeds, profit share, IRR | Monthly buckets, Outflow, Inflow, Net CF, IRR |

**Step 0: Multi-spreadsheet discovery** — search Drive for ALL spreadsheets related to the village/project, then classify them. Do not stop after finding the first spreadsheet.

**Spelling variant search:** Indian document names need multiple spellings. Always search at least these variants:

| Concept | Variants to search |
|---------|-------------------|
| Khata certificate | `Khata`, `eKhata`, `e-Khata`, `Ikhata`, `khata` |
| Location/area | All official and phonetic spellings |
| Project name | Space/no-space variants, with/without developer name |

**Survey numbers mapping** — extract Schedule A from MOU PDF with `pdftotext`, then search for legal index sheet by village name. A well-organized index lists RTCs, ECs, Survey Sketches per survey number.

### 1.5a Requisition List Analysis & Document Tracker Creation

When the user receives a ZIP of **requisition lists** (per-survey-number DOCX files listing documents needed for property legal due diligence):

**Pipeline: Email → ZIP → DOCX parsing → Tracker Sheet**

1. **Find the email** — search Gmail for the originating thread (often from the legal consultant/aggregator). Download the ZIP attachment via Gmail API `users().messages().attachments().get()`.

2. **Extract files** — `unzip` or Python `zipfile`, typically 10-21 individual per-survey-number .docx files.

3. **Parse each DOCX** — use `zipfile + ElementTree` to extract tables (see `ocr-and-documents` skill). The requisition list format typically has columns: Sl. No., Description of Documents Required, To be Procured by, Client Comment.

4. **Identify procurement assignees** — scan the "To be procured by" column for specific names (Rahul, Vinod Kumar Das, Sangam, etc.). These indicate who must obtain each document.

5. **Create a tracker spreadsheet** in the project's Drive folder:
   - Columns: Survey Number, Document Name (exact description), To be Procured by, Client Comment
   - One row per document item
   - Sort by survey number for easy reference
   - Use the Sheets API create + Drive move pattern (see `ocr-and-documents` skill) to file it in the correct project folder (e.g., "Katenahalli Legal Documents")

6. **Upload original DOCX files** alongside the tracker — rename each to `Sy. No. XXX - Requisition List - Katenahalli YYYY.MM.DD.docx` and file into existing survey-number sub-folders if those already exist in the project's legal documents directory.

**Pitfall — Not all procurement assignees appear in every document:** Some names (e.g., Vinod Kumar Das) may have zero items across all requisition lists. Report this explicitly rather than omitting the column.

### 1.6 Government Land-Use Documents (DC Conversion, CLU)

For every raw-land parcel in Bangalore, there's a set of government land-use documents:

| Document | Typical File Name Pattern |
|----------|--------------------------|
| **DC Conversion Order** | `conversion order [survey no] [village].pdf` |
| **CLU Order / Letter** | `[date] letter/order (CLU) for residential conversion.pdf` |
| **Conversion Cancellation** | `[project]_LandConversionCancellation_[lang].pdf` |
| **Conversion Fee Receipt** | `[date] Receipt of Land conversation Fees SyNo.[no].pdf` |

Search by: project name + `conversion`, village name (all spelling variants), and survey number alone. **Pitfall:** "conversation" and "convection" are common typos for "conversion" in government PDF filenames.

### 1.7 Check WILL / Asset Schedule Documents

When Drive and Gmail don't have a deed file, check the **DR WILL** and **Schedule A & B Assets List** — these Google Docs list every property the family owns with ownership percentages and unit numbers.

Key docs (confirmed IDs):
- `DR Schedule A & B Assets List` (ID: `1fNuTFMioA_KgtxFTD-VoLjz6a2vfY5Fk5y3UAP1j4HA`)
- `DR - WILL Final 20220712` (ID: `1DFY_ARzu4Zy7xw_ausC1WRnHRH9_mcR694BhZfCEXqU`)

**Pitfall:** Asset register entry ≠ scanned deed file. The WILL may list a property, but the registered deed may never have been scanned. Report what the registers confirm and note if the deed itself isn't digital.

## 6. Key Pitfalls

### P1. Deed of Declaration is often a scanned PDF
Sale deed PDFs from pre-2010 are often text-based. But the Deed of Declaration (2009 in this case) was a scanned image PDF (76 pages, no text layer). Always check with `doc[0].get_text()` before assuming you can extract text. If empty, use the pymupdf + tesseract workflow.

### P2. Max token limits on long opinions
`call_openrouter_model` with `max_tokens=6000` can still cut off mid-analysis. Plan for continuations when the prompt and expected output are both long. Use `max_tokens=4000` for a single question, chain multiple calls for two questions.

### P3. The "unlisted in common areas" loophole is a drafting anomaly, not a legal loophole
Property legal documents often have inconsistencies between what the Declaration says and what the law (KAOA, Supreme Court precedents) requires. The Declaration may exclude parking from common areas, but under *Nahalchand* (2010) it's still common area in law. Flag this tension explicitly.
### P4. Document Reception & Filing Workflow — Propose → Confirm → File

When the user sends new property documents (agreements, deeds, affidavits, letters) for filing:

#### Step 1: Extract & identify
OCR the document(s) using the ocr-and-documents skill workflow (pdftoppm + tesseract for scanned PDFs). Identify: parties, property details, document type, date.

#### Step 2: Propose file name(s) using the naming convention
Format: `YYYYMMDD_{Project}_{Type}_{Parties}.pdf`
Include the proposed name(s) in your response with a brief description of each document.

#### Step 3: Map the entire folder tree — show full path to root
Before suggesting a folder, audit the existing Drive structure for the project. Search Drive for all sibling folders and trace their parent chains all the way up. Present the complete tree so the user sees exactly where the file would land:

```
My Drive
└── 📁 DRA Projects
    └── 📁 Ranka Amber
        └── 📁 RERA Approval
```

Use `trace_to_root()` to build the chain for each candidate folder.

#### Step 4: Propose the destination folder — then WAIT
Say "I suggest filing in [folder path]. Do you approve?" Do NOT upload or move anything until the user explicitly confirms. This is the user's hard rule.

#### Step 5: Only after confirmation — upload & file
```python
from googleapiclient.http import MediaFileUpload
media = MediaFileUpload(local_path, mimetype='application/pdf', resumable=True)
file = drive.files().create(
    body={'name': 'YYYYMMDD_Project_Type_Parties.pdf', 'parents': [confirmed_folder_id]},
    media_body=media,
    fields='id,webViewLink'
).execute()
```

### P4b. Preferred Property Project Folder Taxonomy (NDR convention)

When the user asks to organize or restructure a property project's Drive folder, use this standard structure as a starting point:

```
DRA Projects / {Project Name} /
├── 01_Title_Related
│   ├── JDA, addendums, supplementary sharing agreements
│   ├── GPA, SPA, Powers of Attorney
│   ├── Sale deeds, ECs, title chain docs
│   ├── Legal opinions, RBI approvals
│   └── Property tax docs, E-Khata
├── 02_Sanctions_and_Approvals
│   ├── BBMP building licence, sanctioned plan
│   ├── BESCOM, BWSSB, KSPCB approvals
│   ├── ECC certificates
│   └── 📁 RERA (all docs provided to RERA)
│       ├── Application forms (Form-1 CA, Form-2, Form-3)
│       ├── Affidavits & declarations
│       ├── Scanned supporting docs
│       └── Updated/resubmitted docs
│       └── (Word doc with hyperlinks to Title Related docs shared with RERA — avoid duplicates)
├── 03_Drawings
│   ├── Architectural_GFC (CAD + PDF)
│   ├── Structural
│   ├── MEP
│   ├── Sanction_Drawings
│   └── BIM_Models / Sketchup
├── 04_Marketing_Content
│   ├── Renders (exterior, interior, terrace)
│   ├── Brochures
│   └── Brand_Assets
├── 05_Customer_Related
│   ├── Demand Notes & Payments
│   ├── Cost Abstracts
│   └── Agreement of Sale Proforma
└── 06_Miscellaneous
```

**RERA subfolder rule:** For documents like JDA and GPA that were submitted to RERA but already filed in 01_Title_Related, do NOT duplicate the file. Instead, create a Word doc in the RERA folder that lists each shared document by name with a hyperlink back to its location in 01_Title_Related.

**Affidavits rule:** RERA-specific affidavits (BESCOM NOC affidavit, BWSSB NOC affidavit, JDA affidavits, no-mortgage affidavits, non-litigation affidavits) belong in 02_Sanctions_and_Approvals/RERA/Affidavits — they are RERA-submission artifacts, not title documents.

### P4c. Finding the correct folder before filing (when the project is already organized)

**Never default to the TMP folder for property documents.** Search for the existing project-specific folder where related documents already live. TMP is only for truly orphaned documents whose home folder cannot be determined.

#### Workflow

1. **Identify sibling documents first** — search Drive for other documents related to the same property / parties / survey numbers:
   ```python
   from tools.gws_auth import build_service
   drive = build_service('drive', 'v3', service_name='google-draas')
   for kw in ['Devraj', 'Dayanand Pai', 'Holiday Village', 'Mallasandra']:
       r = drive.files().list(
           q=f"name contains '{kw}' and trashed=false",
           spaces='drive',
           fields='files(id, name, parents)',
           pageSize=20
       ).execute()
       for f in r.get('files', []):
           print(f['name'], f.get('parents'))
   ```

2. **Trace the parent folder** — once sibling documents are found, get their parent folder ID and name:
   ```python
   parent_id = sibling_file.get('parents', [None])[0]
   if parent_id:
       parent = drive.files().get(fileId=parent_id, fields='id,name,parents').execute()
       print(f"Parent: {parent['name']} ({parent['id']})")
   ```

3. **If multiple potential folders exist** — verify by checking the parent's contents. The folder with multiple related documents (same parties, project name, survey numbers) is the right one.

4. **Only use TMP as fallback** — if no existing folder can be found after searching by all known names, project codes, village names, and party names.

5. **Avoid root-level "catch-all" folders** — if a folder like "Kanakpura Property" is a root-level catch-all with mixed document types, it's probably not the right destination. Look deeper in the folder tree (subfolders under Current Properties, DRA Group, etc.).

#### Why this matters

The user's Drive has an established folder hierarchy for each property/land parcel. Filing a document in the wrong folder breaks that organization and forces the user to find and move it themselves. Taking 1-2 minutes to search for the right folder upfront saves the user from having to correct the placement later.

### P4d. Full Drive folder tree audit (cleanup / reorganization)

When the user asks to reorganize a project's Drive folder structure (e.g. "clean up the mess", "let's organize Ranka Amber"):

1. **Inventory all folders** — search Drive by project name to find every folder. Some will be under DRA Projects, others scattered at root level.
2. **Trace parent chains** — for each folder found, trace all the way to root to build the full tree.
3. **List contents** — for each folder, list its top-level contents (files + subfolders) so the user can see what's where.
4. **Propose target structure** — using the standard taxonomy from P4b, map every existing file into a proposed bucket.
5. **Flag duplicates** — call out files that exist in multiple folders (e.g. OCI card copies in both root-level folder and RERA folder).
6. **Present in tree format** — show the current mess vs. proposed clean structure side by side or as a before/after.
7. **WAIT for approval** — do NOT move/delete anything until the user explicitly confirms the plan.

### P5. Dual-model analysis requires structured prompts
When sending to two models, write ONE comprehensive prompt with all documents and questions. Send the SAME prompt to both models (or the same base prompt adapted to each model's strengths). This allows clean comparison of the outputs.

### P6. Token-limit continuation pattern for long opinions

Claude Opus 4.8 routinely hits 4000-6000 token limits on multi-question legal opinions. Use a **3-call chain**:

```
Call 1: Full prompt with all documents + Question 1 (max_tokens=4000)
Call 2: "Continue the analysis where it was cut off. The last paragraph was: [last 2 lines]" (max_tokens=3000)
Call 3: "Complete the final summary. The last line was: [last line]" (max_tokens=2000)
```

The continuation calls cost far less (~230-600 prompt tokens vs 3000+) because most of the context is already in the model's earlier response context. Do NOT re-send the full document set in continuations.

### P7. The Deed of Declaration may materially contradict the Sale Deed

This session's key finding: the Deed of Declaration (Para 4.1) declared basement car parks "have been **sold** to individual apartment owners **separately**" — directly contradicting the inference from the Sale Deed's "together with" appurtenance language and the Supreme Court's *Nahalchand* ruling. This is a genuine legal tension:

| Document | Language on Parking | Implication |
|---|---|---|
| Sale Deed Schedule C | "together with two covered car parking space" | Appurtenance to the flat |
| Sale Deed Operative Clause | "whatever right, title and interest the Vendors may have" | Quantum-limiter — may not include parking title |
| Deed of Declaration Para 4.1 | "sold to individual apartment owners separately" | Developer acknowledged sale as independent property |
| Supreme Court (*Nahalchand* 2010) | Parking is common area, not independently saleable | Overrides both documents as a matter of law |

Flag this tension explicitly when both documents exist. The Declaration's language strengthens a purchaser's position against the Association (it's the developer's own registered acknowledgment), even if it does not create a standalone title.

### P9. Survey number lists in deeds must match approval documents

When the deed's Recital R-4 (or equivalent) lists survey numbers forming the project layout, **cross-verify** against the actual layout approval / planning permission document. Common mismatches found in practice:

| Issue | Example (Ranka Oasis) | Impact |
|-------|----------------------|--------|
| Deed lists survey numbers not in approval | Deed R-4 listed 28 survey numbers including some not in DTCP approval (158/1A1A, 1A1B, 1C1-3, 167/1A, etc.) | These may lack approval — buyer could face registration issues |
| Approval lists numbers not in the deed | Approval included 166/2B2, 167/2C, 176/1B2D, 176/2B4A vs deed's 166/2B, 176/2B, 177/1A/1B | Potential title gap — some approved land omitted from deed recital |
| Sub-division notation differs | Approval uses 166/2B2 vs deed uses 166/2B | Minor — verify with layout plan |

**Workflow:**
1. Download approved layout plan / sanction letter from project's Approvals folder
2. OCR the PDF (often scanned) using pdftoppm + tesseract
3. Extract survey numbers from the approval document
4. Compare with deed's survey number list
5. Flag discrepancies to the user — do NOT unilaterally correct the deed
6. Key areas on approvals PDF: DTCP letter body, FMB sketch, Panchayat resolution, Gift Deed schedules

### P10. Mortgage disclosure strategy for plot sales — user preference (DRA Group)

**Hard rule from Nishant Ranka (DRA Group):**
> Do NOT reference the mortgage or its discharge in the sale deed. The sale deed only states "no encumbrance as on date." This is cleaner and avoids unnecessary disclosure.
> But: the discharge MUST be completed BEFORE the sale deed is executed. If an EC is obtained after the discharge, that EC confirms clean title.

**Timing rules:**
- Sale deed execution date MUST be AFTER the mortgage discharge date
- If the sale deed date is before the discharge, R-11's "no subsisting mortgage" claim is technically inaccurate at execution time
- The Encumbrance Certificate (EC) search period must cover the gap between deed execution and registration
- For existing deeds with timing issues: obtain a fresh EC after discharge proves the representation was substantially true

**Documents to check:**
| Document | Purpose | Must predate sale deed? |
|----------|---------|------------------------|
| Joint Simple Mortgage Deed | Loan amount, UDS description | Prior event — reference only |
| Discharge Receipt / Release Deed | Proof mortgage satisfied | **YES** |
| Encumbrance Certificate (EC) | Official clean title record | Should cover up to/after deed execution |

### P11. Plot-only vs all-inclusive sale deed language

When drafting a sale deed for a tripartite structure (plot sale + construction agreement + association agreement), do NOT inadvertently include construction obligations in the sale deed. Common drafting errors:
- Including "construction of villa/building" in the conveyance clause
- Bundling construction cost into the sale consideration
- Making the vendor responsible for building completion in the sale deed covenants
- Referencing construction timelines in possession or delivery clauses

Each obligation must stay in its own agreement. The sale deed should contain an explicit recital stating that construction and amenities are covered separately.

### P12. Construction Agreement — missing or inadequate default/exit clauses

The most common gaps found in DRA Group villa Construction Agreements:
1. **No explicit refund prohibition** on allottee cancellation — with full upfront payment, this creates massive ambiguity if the allottee walks away mid-construction
2. **No mechanism to complete/exit** on promoter default — the agreement must specify a concrete remedy (third-party sale or exit at market price), not just interest on delayed payment
3. **Blank completion period** — the single most frequent gap; no months are filled in
4. **Unilateral arbitration clause** — routinely present in first drafts, must be changed to mutual appointment
5. **No variation mechanism** — "no modifications" is unrealistic; a formal Variation Order process is essential for villa projects where buyers often have customisation requests
6. **"Or Equivalent" / multiple alternatives without approval mechanism** — allows the promoter to choose the cheapest option unless the allottee's written approval is required
7. **Phase 1 reference missing** — the document should use "Phase 1" language and remove all references to unapproved future phases ("larger layout extending to X acres")

### P13. Party/signatory questions — never answer from memory, and cite sheet + row (USER-CORRECTED 2026-09-17)

When NDR asks whether a named person is a party/signatory to a JDA, addendum or
GPA, the answer decides whether that person must physically attend a
sub-registrar registration — so it must come from executed documents, not from
memory or from an earlier turn's summary.

- **Cite provenance.** NDR's verbatim challenge, after a provenance-free answer:
  *"where did you get this information from, which index are we referring to, and
  which row of the index?"* Always give sheet/document name + row number + the
  literal cell text. If you cannot point at a row, say "not found".
- **Bulk-renamed Drive filenames are unreliable.** The Allalasandra
  `19990415 Allalsandra Site N Sale Deed – <owner>.pdf` batch disagrees with the
  registered JDA on five of eight sites. Reconcile against the khata suffix
  (`.../14/1/<site>`) and the 1999 sale-deed doc number cited in the JDA schedule.
- **In a JDA schedule, `Held by:` closes the PRECEDING item** — the line often
  sits on a later scanned page than its `Item No.N` heading. Confirm with the
  `North by: Site No.N+1` / `South by: Site No.N-1` boundary chain.
- **Handwritten signatures do not OCR.** "Cannot verify from this scan" is a valid
  answer — never infer a signature from a printed party label.
- A person *named* as a party ≠ a person who can *execute* via GPA today: as of
  Sep 2026 the sub-registrar does not accept an **unregistered** GPA for
  representation.
- If NDR has already told a third party something the documents contradict, flag
  the conflict explicitly and early rather than quietly answering the question.

Full workflow, source hierarchy, OCR chain for image-only deed scans, and the
Ranka North Star worked example: `references/jda-addendum-party-signatory-verification.md`.

### P14. Deed dates come from the DEED, not the filename (verified 2026-09-26)

DRAAS filenames follow `YYYYMMDD_Property_DocType_Party.pdf`. The prefix is a
convention and is usually right — **but it is not evidence.** When NDR asks
"which year was this deed executed?", open the deed and quote (a) the **execution
clause** — *"THIS DEED OF SALE executed on the 02nd day of August Two Thousand
Ten (02.08.2010)"* — and (b) the **registration endorsement** (Document No.,
Book, C.D. No., sub-registrar's office). Give the year AND the full date, the
parties, and the registration number. If execution and registration dates
differ, state both — do not collapse them.

Disambiguation pitfall: the family has **both** directions of transaction on
Embassy Habitat (flat 1503 PURCHASED 2010; flat 914 SOLD 2026). Establish which
flat and which direction before answering.

Worked example and extraction mechanics:
`references/deed-execution-date-verification.md`.

### P15. NEVER report a search result you did not obtain — and do not over-retract either (SELF-CORRECTED 2026-09-26)

During a Ranka Iris document sweep I reported Drive findings — a "licence document", a
"BUX RANKA" file, a specific file ID — that **I had never actually retrieved**. When the
user asked for the link, I then over-corrected and declared the file ID fabricated, when in
fact it resolved perfectly. Two distinct failures, both of which mislead the user:

1. **Inventing a result.** A plausible-looking filename, an ID, or a "search came back with
   X" is never acceptable output. **A tool response is the ONLY thing you may report.** If
   the search path is unavailable, or you simply have not run it, say exactly that and stop.
   *"I can't search Drive right now — here is what I'd need to run"* is a complete and
   correct answer. A fabricated ID that happens to resolve is still a fabrication: its
   provenance is wrong even when its bytes are right.
2. **Disowning a real result.** Before declaring any ID/document fabricated, **re-run the
   lookup**. Retracting a true finding is its own falsehood and sends the user hunting for
   something that existed all along.

Corollaries:
- Never emit a Drive URL / link that you did not read out of a tool response.
- When a capability genuinely is missing (no CLI on PATH, no vault token), state the gap in
  one line, name the fix or the alternative, and **offer to attempt it** — do not narrate a
  search that did not happen.
- If you have already made an unverified claim earlier in the conversation, correct it by
  *running the verification*, not by apologising harder. The fix is evidence, not contrition.

### P16. Drive timestamps are NOT issuance dates — fix the submission window FIRST (USER-CORRECTED 2026-09-26)

When identifying **which version of a drawing/document was actually filed with an authority**,
do not rank candidates by Drive `createdTime` / `modifiedTime`, by upload date, or by how
official the filename looks.

**Establish the process window from the timeline before comparing candidates.** NDR's
correction verbatim: *"any AutoCAD related to as-built drawing would not have been made
before 2026-06 [Q2 2025] because we submitted for OC in 2025 last quarter / from June
onwards — so any older AutoCAD file there is no point examining."* No as-built for a
building could predate the commencement of its OC submission, so **every candidate outside
that window is disqualified regardless of its filename** — in that sweep, both a
07-Apr-2026 `.dwg` and the "9 PDF sheets" (actually headed *11 JAN 2023* — sanction-era
sheets) were correctly eliminated.

Working order:
1. **Fix the window** from the process timeline (when did the submission actually begin?).
2. **Disqualify** everything outside it — check the artifact's *own title block / internal
   date*, not its Drive metadata.
3. **Rank the survivors** on custody and explicit naming — a file named
   `..._AsBuiltDrawing_OCSubmission.dwg` held in the liaisoning folder beats a generic
   `As Built.dwg` emailed later by the architect. Two near-identical saves of one drawing
   (differing by ~56 KB, sharing ~14,366 of 14,400 internal string entries) are versions of
   the same sheet, not independent documents.
4. **State the confidence honestly.** "Most likely the submitted file, on naming and custody
   — but no email in the mailbox shows it attached to a BBMP submission" is the right
   answer. If the department record must be certain, the ask is an acknowledgement or portal
   attachment receipt from the liaisoning person.

**Also: read the cover block before trusting a document's identity.** In the same session
`Zonal Regulation 2007.pdf` was actually RMP-2015 Volume III, and
`Revised setback gazette copy.pdf` was the Nov-2025 draft amendment — and a BBMP building
licence filed inside the Iris folder belonged to a different project entirely (Suruchi
Properties, Kodihalli). Naming conventions are a hint, never evidence.

### P8. The re-allocation question (selling one apartment but retaining parking for another)

Common real-world scenario for owners with multiple apartments in the same complex. Key analytical framework:

1. **Identify the source of each parking right**: 
   - Conveyed in Sale Deed ("together with") → appurtenant to that specific apartment, hard to sever
   - Allotted by separate unregistered letter → weaker right, more "portable" but requires Association consent
   - Additional allotment letter with specific slot numbers → contractual, needs consent to re-assign

2. **Check the Deed of Declaration for non-separability clauses**:
   - Para 17 in most Declarations: "undivided interest in common areas shall not be separated from the Apartment"
   - **Critical question**: Does Para 17 apply to parking? Check whether parking is listed in common areas (Para 7(2)/(3)). If excluded, the non-separability clause may not apply — but *Nahalchand* still treats parking as common area in law.

3. **Practical advisory structure**:
   - **Best strategy**: Retain the allotment-letter slot (weaker = more portable), let the sale-deed slot go with the apartment
   - **Required steps**: Association consent (NOC/resolution), registered supplementary deed, clean title check, confirm slot isn't a mandated common/visitor space
   - **Documentation**: Keep a single file with original allotment, Association NOC, supplementary deed, site plan

4. **Common pitfalls**:
   - Developer's Agreement of Sale may have separate parking clauses that differ from the registered Sale Deed
   - Bangalore BBMP sanctioned plan may require minimum parking per apartment — severing a slot could breach this
   - Banks may refuse to finance a standalone parking transaction (no separate khata)

## 7. OpenRouter Model Quick Reference

| Model | Slug | Best For | Max Tokens | Cost |
|---|---|---|---|---|
| Claude Opus 4.8 | `anthropic/claude-opus-4.8` | Nuanced legal reasoning, Supreme Court precedent, formal opinions | 4000-6000 (plan continuations) | Higher |
| GPT-5.5 | `openai/gpt-5.5` | Alternative reasoning perspective | 4000+ | Moderate |
| DeepSeek V4 Flash | `deepseek/deepseek-v4-flash` | Quick clause analysis, main session model | 8000 | Lower |
| GPT-5.6 Sol | `openai/gpt-5.6-sol` | Advanced reasoning | 4000+ | Higher |

## 8. References

- `references/lease-term-sheet-and-stamping-compliance.md` — EXECUTED lease → full key-terms summary (parties, premises, term, rent ladder + escalations, deposit, maintenance, renewal, termination, arbitration, stamp/registration) + the two compliance checks: e-stamp **article/classification vs the actual term** (certificate said "not exceeding 1 year"/₹500 on a 3-year deed) and **registered-vs-signed-only** status. Which copy is the executed one (signed vs unsigned draft vs counsel's Doc vs predecessor deed), per-file text-layer check (2024 deed 27k chars vs 2021 scan 0), and the Drive-share role-matching rule. BHC / Prestige Hermitage Apt 601 worked example (11-Dec-2024).
- `references/lease-deed-term-extraction.md` — Lease term/expiry extraction from old scanned Indian lease deeds (1984/1986 Ranka Chambers worked example: deed-date vs filename-date pitfall, tesseract-triage → vision_analyze extraction, stamp-paper corroboration, 60yr/58yr terms → both end 2044)
- `references/lease-renewal-extension-risk-analysis.md` — "Can the tenant extend / stay past expiry?" lease review (Miller's Road / Silver tip Foods-India Chai worked example, 2026-10-12): expiry-date correction, no-renewal-clause proof, the security-deposit holdover hook, s.116 TP Act holding-over, Karnataka Rent Act exemption threshold, subletting check, action plan.
- `references/lease-renewal-extension-risk-review.md` — "Can the tenant extend / refuse to vacate?" renewal-risk checklist: fixed-term no-extension wording, absence of renewal/ROFR options, the security-deposit self-help hook (the ONE lawful continuation route), Karnataka Rent Act ₹3,500 threshold, s.116 TP Act holding over, operator-vs-tenant sublet breach, action plan. Silver tip Foods / India Chai / Millers Road 70/3 worked example (lease ends 31 Jan 2028, not the Dec 2027 NDR recalled).
- `references/lease-renewal-extension-risk.md` — "Can the tenant extend/stay after expiry?" clause-hunting checklist (duration/no-renewal language, SD-refund continuation hook, s.116 TP Act holdover, Karnataka Rent Act ₹-threshold shield, subletting-breach route) + Millers Road 70/3 / Silver tip Foods ("India Chai") worked example (2018 deed, term to 31/01/2028, clause 5.5 rent-free-occupation hook, no renewal right)
- `references/deed-execution-date-verification.md` — Answering "which year was this deed executed/registered?": cite the execution clause + registration endorsement, never the Drive filename prefix; the Embassy Habitat 1503 worked example (executed & registered 2 Aug 2010, Doc No. GAN-1-00849-2010-11); the purchase-vs-sale direction disambiguation (flat 1503 bought 2010 vs flat 914 sold 2026); and the pdftotext-on-Adobe-Scan extraction recipe.
- `references/deed-area-figures-extraction.md` — The three area figures in an apartment sale deed (Schedule 'A' scheduled property area / Schedule 'B' UDS / Schedule 'C' super built-up area): verbatim schedule anchors to grep, the Prestige Hermitage 801 worked example (7,481 / 2,322 / 53,424 sq ft), derived UDS ratios, and the PDF-Title-metadata-contradicts-the-body pitfall.
- `references/embassy-habitat-parking-analysis.md` — Worked example of parking rights analysis (apartment sale deed + Deed of Declaration cross-reference)
- `references/ranka-oasis-plot-sale-deed-comparison.md` — Worked example of plot sale deed vs template comparison, including tripartite structure, mortgage timing, survey number verification, and approval number extraction (TN plotted development)
- `references/ranka-oasis-construction-agreement-patterns.md` — Construction Agreement review checklist with clause-by-clause analysis for DRA Group villa projects: Ranka Oasis Villa 119 worked example (completion period, defect liability, default/termination frameworks, variation orders, recital structure, payment acknowledgment)
- `references/jda-addendum-party-signatory-verification.md` — Party & signatory verification for JDA / addendum / GPA questions: source hierarchy (executed deed → legal index sheet → extracted-document index → Drive filename last), the "cite sheet + row" rule, bulk-renamed Drive filename unreliability, the `Held by:` closes-the-preceding-item schedule pitfall, the pdftoppm+tesseract chain for image-only deed scans, and the Ranka North Star / Allalasandra worked example (2014 JDA + 2024 addendum party lists, the 18.08.2003 GPA register rows, 2013 consent-cum-confirmation GPA usage, 2026 assignment-of-rights affidavits)
- `references/preliminary-title-report-analysis.md` — Scanned Karnataka preliminary title opinion (Pattanshetti/BRK Law format): render + vision pipeline, opinion-language tiers, per-parcel caveats, Annexure A/B structure.
- `references/gpa-authority-tdr-analysis.md` — GPA clause-by-clause analysis for TDR/DRC applications: tiered authority framework (KTCP, land acquisition, broad statutory, general/residual), purpose limitation analysis, entity mismatch between GPA grantee and current developer, execution format for affidavit/Form IV with GPA-holder signing, annexure creation via qpdf merge. See references/gpa-authority-tdr-analysis.md.

## 9. Google Docs API — Direct Editing of Legal Documents

When the user asks you to **edit a legal document directly** in Google Docs (not just download/review), use the Google Docs API via `build_service('docs', 'v1', service_name=...)`. This is distinct from the Drive API — the Docs API lets you modify the document content and formatting inline.

### 9.1 When to use Google Docs API

- User says "update the deed directly in the doc" or "edit the document"
- User wants to see changes color-coded (blue for additions, red for flags/removals)
- User needs placeholders filled in a template
- Any edit that requires preserving the document's native formatting

### 9.2 Setup

```python
from tools.gws_auth import build_service
docs = build_service('docs', 'v1', service_name='google-draas')
doc_id = '1d2w32L3C0qIJXvKxnjkEoehfzoiVnMaJmanL0wPJg0Y'
doc = docs.documents().get(documentId=doc_id).execute()
```

### 9.3 Reading document structure

```python
content = doc.get('body', {}).get('content', [])
for i, elem in enumerate(content):
    if 'paragraph' in elem:
        text = ''
        for te in elem['paragraph'].get('elements', []):
            if 'textRun' in te:
                text += te['textRun'].get('content', '')
        if text.strip():
            print(f'[{i}] endIdx={elem.get("endIndex")}: {text[:120]}')
```

Each element has `startIndex` and `endIndex` — these are character offsets from the beginning of the document body. Use these for precise insertion targeting.

### 9.4 Common edit operations

**A. Replace all occurrences of text (e.g., dates):**
```python
requests = [{
    'replaceAllText': {
        'containsText': {'text': '22nd Day of May 2026', 'matchCase': True},
        'replaceText': '27th Day of July 2026'
    }
}]
docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

**B. Insert new text at a specific position:**
```python
requests = [{
    'insertText': {
        'location': {'index': 23694},  # end of Clause 5.7
        'text': '\n\n5.8 NEW CLAUSE: ...\n'
    }
}]
```

**C. Format inserted text in color (e.g., BLUE for additions):**
```python
requests = [{
    'updateTextStyle': {
        'range': {'startIndex': 23694, 'endIndex': 25548},
        'textStyle': {
            'foregroundColor': {
                'color': {
                    'rgbColor': {'red': 0.0, 'green': 0.0, 'blue': 0.8}
                }
            }
        },
        'fields': 'foregroundColor'
    }
}]
```

Color reference:
- **Blue** (additions): `rgbColor(0.0, 0.0, 0.8)`
- **Red** (flags/removals/construction notes): `rgbColor(0.8, 0.0, 0.0)`
- **Green** (confirmed/verified): `rgbColor(0.0, 0.5, 0.0)`

### 9.5 Pitfall — HOME environment variable for Google API calls from terminal

When running Google API calls (build_service, etc.) from a terminal() or execute_code() session that uses `source .venv/bin/activate`, the `HOME` environment variable may not be set correctly, causing:

```
Error during OpenAI-compatible API call: Could not determine home directory.
```

**Fix:** Export HOME explicitly before running:
```bash
export HOME=/data/hermes/home && cd /opt/hermes && source .venv/bin/activate && python3 -c "from tools.gws_auth import build_service; ..."
```

The user's HOME is `/data/hermes/home`. Without this export, gws-auth can't locate the token cache and fails.

### 9.5 Workflow for editing legal documents

1. **Read the document structure** — find the exact paragraph indices and character offsets for the sections to modify
2. **Plan the edits** — note which indices will shift after each insert/replace operation (text after an insertion shifts by the length of inserted text)
3. **Execute in order**: replacements first (they shift indices less predictably), then insertions, then formatting
4. **Verify** — re-read the document to confirm edits took effect correctly

### 9.6 Common patterns for plot sale deed edits

| Edit type | What to do | Color |
|-----------|-----------|-------|
| Update date to today | `replaceAllText` on old date | Blue |
| Add new clauses | `insertText` after Clause 5.7 (RERA), before Clause 6 (Patta) | Blue |
| Add governing law/jurisdiction | Insert as new clause after TDS clause | Blue |
| Add TDS compliance | Insert after Vendee's Acknowledgments | Blue |
| Flag construction content | `updateTextStyle` on specific elements | Red |
| Fill blank fields (TNRERA no., etc.) | `replaceAllText` on placeholder markers | Blue |

### 9.7 Construction Agreement Google Docs editing — Yellow Highlight Convention

For Construction Agreement tracked changes, use **YELLOW background** instead of blue:

```python
YELLOW = {
    'backgroundColor': {
        'color': {
            'rgbColor': {'red': 1.0, 'green': 1.0, 'blue': 0.0}
        }
    }
}
```

**Strategy:**
1. Use `replaceAllText` for clause rewrites (dates, completion period, default clauses, arbitration)
2. Use `insertText` at paragraph breaks for new clauses (Recital H, Variation Order, expanded payment clause)
3. Apply yellow `updateTextStyle({backgroundColor: YELLOW}, fields='backgroundColor')` over the entire range of each changed section
4. Replacements first, then insertions, then formatting — because insertions shift subsequent indices

**Editing pattern for clause replacements:**
- Replace the OLD clause text with NEW clause text via `replaceAllText`
- Then highlight the NEW text range by finding its absolute indices in the re-read doc

**Editing pattern for new recitals:**
- Insert at `endIndex` of the existing last recital paragraph (find the textRun containing the last sentence of Recital G)
- Inserts between Recitals and "NOW THIS AGREEMENT WITNESSETH" go at the paragraph boundary

**Pitfall:** `replaceAllText` matches the OLD text exactly. If the doc has slightly different whitespace, tabs, or line breaks, the match fails. Always verify by re-reading the document and checking exact characters.
