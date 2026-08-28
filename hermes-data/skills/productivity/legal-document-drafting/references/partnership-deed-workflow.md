# Partnership Deed Drafting Workflow

Covers deed of partnership, deed of reconstitution, contribution deeds, and commercial arrangement documents for DRAAS real estate partnerships.

## Overview

Partnership deeds for DRAAS involve:
- **Partners**: DRA Realty Pvt Ltd (corporate entity) + individual landowner
- **Consenting party**: The landowner's existing entity (e.g. Satvik Developers) that holds title
- **Land Assets**: Multiple land parcels across villages contributed by each partner
- **Structure**: NOT a partnership at will — specific-purpose partnership with locked-in duration

## Typical Documents in the Chain

1. **Principal Partnership Deed** — initial formation of the partnership
2. **Deed of Reconstitution** — when partners change (retire/admit)
3. **Deed of Contribution** — each partner contributes specific land assets to the firm
4. **Commercial Terms / Side Letter** — underlying financial arrangement

## Workflow

### Step 1: Gather Context from Drive
```
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')
```
- Search for existing deeds, commercial terms docs, ledgers
- Use multiple queries: name contains 'partnership', name contains 'reconstitution', fullText contains partner name
- Retrieve spreadsheet-based land lists (Byadarahalli Master Sheet, Survey Lists, etc.)
- Download DOCX files for commercial terms; read Google Docs via Docs API

### Step 2: Read All Financial Documents
- Partner ledgers (NDR books) — understand ₹ flows between partners
- Payment proofs, loan docs, bank statements
- Nagendra transaction details (sale agreements, payment chain)

### Step 3: Clause-by-Clause Analysis
Use a thinking model for detailed analysis — the user's preferred routing for this is:

**Model routing (Nishant preference, June 2026):**
- Use OpenCode Go as provider
- Use thinking models (GLM family, Gemini 2.5 Flash/Pro, or similar)
- Do NOT use deepseek models for legal analysis (they may run out of reasoning tokens on long documents)
- First attempt with a full-capability thinking model; fall back to a lighter model (e.g., Gemini 2.5 Flash) if the primary model consumes all tokens on reasoning

```python
# Preferred pattern:
call_openrouter_model(
    user_trigger_phrase="use [model] via openrouter for detailed clause by clause analysis",
    model="google/gemini-2.5-flash",  # or glm-4, or other thinking model
    max_tokens=16000,  # Set high enough — reasoning models need 4000+ for the thinking block alone
    prompt="Full analysis prompt with both deed texts, transaction background, and specific instructions"
)
```

If the model returns `OpenRouter returned empty content (possibly all tokens consumed by reasoning)` with `error` in the response (not a normal model output), retry with:
- A higher max_tokens value (32000+)
- A shorter/condensed prompt that removes low-value content (e.g. combine lengthy background into a concise intro paragraph)
- A different model — switch from Gemini 2.5 Pro to Gemini 2.5 Flash (has lower reasoning overhead and succeeds where Pro exhausts tokens)
- **Or do the analysis directly**: if you've already read all documents into your context, run the clause-by-clause analysis yourself without delegating to OpenRouter. You have the full deed texts, you understand the structures — write the analysis directly. This is often faster and avoids the token-consumption problem entirely.

**Note**: The OpenRouter error returns `"error"` key (not text content), so check response structure before treating result as analysis text. The `response` field will be empty. The `usage` dict may show `completion_tokens=0` and `reasoning_tokens=0` — the entire reasoning budget was consumed without producing output.

**Alternative**: Do the analysis directly without OpenRouter if the documents have been fully read into context — the main model (deepseek-v4-flash or MiniMax) can handle the analysis directly.

```python
from hermes_tools import execute_code
# Read the deed text from Drive
# Analyze each clause: risk, adequacy, changes needed
# Format as structured report
```

Key focus areas:
- Gap analysis between old deed (reconstitution) and new deed
- Structural conflicts (retiring partner vs continuing partner)
- Capital contribution wording
- Payment milestone conditions
- Title indemnity and capital adjustment mechanisms
- Document custody provisions
- Profit sharing ratio verification
- Continuity clauses (death, insolvency, withdrawal)

### Step 4: Identify Protection Clauses Needed

Always include for DRA Realty's protection:

1. **Non-Contestation Clause**: Partner acknowledges DRA's total contribution (cash + land + brand fee waiver) constitutes full and fair consideration for their profit share. Prevents challenges under Section 6(b) Partnership Act.

2. **Title Indemnity with Capital Adjustment**: All rectification costs for title defects are adjusted against the contributing partner's capital account. If negative, personal liability.

3. **Document Custody**: All original title documents held by DRA Realty in safe custody. Partner has inspection rights on notice.

4. **Objective Conditions Precedent for Payments**: Define exact conditions (written title opinion, 30-year ECs, updated RTCs, no litigation, physical doc delivery) rather than subjective "satisfaction."

5. **Revenue Waterfall**: Priority order: costs → project finance → DRA Brand Fee (top-line %) → partner capital takeout → profit share.

6. **Lock-In with Non-Compete**: Minimum 7-year lock-in. Personal liability for breach. Non-compete within 10km radius.

7. **Continuity**: No dissolution on death or insolvency of any partner. Successor bound by deed of adherence.

### Step 5: Create Google Doc as Deliverable

Use Google Docs API for formatted output:

```python
from tools.gws_auth import build_service

# Create via Drive (not Docs) to set parent folder
drive = build_service('drive', 'v3')
doc_file = drive.files().create(body={
    'name': 'YYYYMMDD_Partnership_Name_Deed',
    'mimeType': 'application/vnd.google-apps.document',
    'parents': [TARGET_FOLDER_ID]
}, fields='id, name, webViewLink').execute()

doc_id = doc_file['id']

# Populate content
docs = build_service('docs', 'v1')
docs.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': [{
        'insertText': {
            'location': {'index': 1},
            'text': FULL_DEED_TEXT
        }
    }]}
).execute()

# Apply formatting
requests = []
# TITLE style for doc title
requests.append({
    'updateParagraphStyle': {
        'range': {'startIndex': TITLE_START, 'endIndex': TITLE_END},
        'paragraphStyle': {
            'namedStyleType': 'TITLE',
            'alignment': 'CENTER'
        },
        'fields': 'namedStyleType,alignment'
    }
})
# HEADING_1 for articles
requests.append({
    'updateParagraphStyle': {
        'range': {'startIndex': H1_START, 'endIndex': H1_END},
        'paragraphStyle': {
            'namedStyleType': 'HEADING_1',
            'spaceAbove': {'magnitude': 18, 'unit': 'PT'}
        },
        'fields': 'namedStyleType,spaceAbove'
    }
})
# Send in batches of 10
for i in range(0, len(requests), 10):
    docs.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests[i:i+10]}
    ).execute()
```

To find heading positions, iterate document content:
```
doc = docs.documents().get(documentId=doc_id).execute()
for elem in doc['body']['content']:
    if 'paragraph' in elem:
        for run in elem['paragraph'].get('elements', []):
            if 'textRun' in run:
                text = run['textRun'].get('content', '')
                start = run.get('startIndex', 0)
                # Check for heading text
```

### Step 6: Create Drive Folder Structure

Create a top-level project folder and subfolders:
```
📁 Project Name (e.g. "DRA Satvik Development Partners")
  ├── 📁 Partnership Documents    ← deed goes here
  ├── 📁 Partner Name - Land Contributions
  │   ├── 📁 Byadarahalli Lands
  │   └── 📁 Palya Land
  ├── 📁 Nagendra Transaction
  ├── 📁 Legal Due Diligence
  ├── 📁 Project Financials
  └── 📁 Commercial & Financial
```

### Step 7: Move Existing Documents into Structure

```python
# For files owned by the user: update parents
drive.files().update(
    fileId=FILE_ID,
    addParents=TARGET_FOLDER_ID,
    removeParents=CURRENT_PARENT_ID,
    fields='id, parents'
).execute()

# For files not owned by user (shared): make a copy in the folder
copy_meta = {'name': FILE_NAME, 'parents': [TARGET_FOLDER_ID]}
drive.files().copy(fileId=FILE_ID, body=copy_meta).execute()
```

## Standard Clauses for Partnership Deeds

See also `templates/partnership-deed-boilerplate.md` if available.

### Capital Contribution Clause Pattern
```
The [Partner Name]'s total capital contribution comprises:
(a) Land Contribution: [Schedule ref] valued at Rs. [value]
(b) Cash Contribution: Rs. [value] structured as:
   (i) Rs. [x] payable immediately on execution;
   (ii) Rs. [y] payable within [z] days of satisfaction of conditions
Conditions precedent for payment: [list objective conditions]
```

### Profit Sharing Clause Pattern
```
Revenue Waterfall (priority order):
1. Project costs and statutory dues
2. Project Finance repayment
3. [Partner Name] Brand Fee ([x]% of gross revenues)
4. Priority capital takeout for contributing partners
5. Return of remaining capital
6. Balance: [ratio]% / [ratio]%
```

## Pitfalls

- **`docs_create` via bridge expects `body=`, not `content=`**: When using `gws_skill_bridge.call("docs_create", service_name="google-draas", title=..., body=...)`, the skill function checks `args.body`. Passing `content=` as the text argument is silently ignored because `_SkillArgs` maps kwargs 1:1 to attribute names — the document is created but EMPTY. Always use `body=<full_text>`.
- **Alternative: Use `docs_create` with `body=` for speed**: The simple `gws_skill_bridge.call("docs_create", ...)` with `body=` is faster than raw Docs API batchUpdate for initial creation. The raw `build_service('docs', 'v1')` + batchUpdate approach (Step 5 above) is only needed for formatted/headed output. For plain text, the bridge call with `body=` is sufficient.
- **Ownership of existing deed files**: Docs created by other users (shared with Nishant) cannot be moved to Nishant's Drive structure since they're not owned by the processing user. Solution: copy into the target folder.
- **Google Docs API parent setting**: Must create the document via Drive API with the parent specified, not via Docs API (Docs doesn't accept parent folder).
- **Docs API batchUpdate limits**: Max 10 requests per call for stable behaviour. Each heading/formatting change counts as one request.
- **Permitted parents error**: "Increasing the number of parents is not allowed" — use addParents with removeParents together, or use a file with exactly one parent.

---

## Reconstitution Deed Workflow (Added June 2026)

### Key Structural Differences from New Partnership Deeds

Reconstitution deeds differ from new partnership deeds in critical ways:

1. **Parties**: Only continuing partners — NO consenting party if the predecessor firm has been dissolved. Reference dissolved entity only in recitals/narration.
2. **Recitals**: Must reference the ORIGINAL partnership deed (date, firm registration number) and the chain of events leading to reconstitution (dissolution, partition, allocation).
3. **Scope**: Changes name, ratio, and governing terms — the original firm continues under new identity.

### Before Drafting: Read ALL Source Documents

**Critical: Always read BOTH the Google Doc AND the executed PDF.**

| Source | What to Check |
|--------|--------------|
| **Google Doc** (draft) | Clause structure, article numbering, definitions, schedules |
| **Executed PDF** (final) | **Parties** — who actually signed? Consenting parties listed? |
| | **Recitals** — property sourcing chain, dissolution references |
| | **Schedules** — survey numbers, extents, boundaries (PDF may have more detail than Google Doc) |
| | **Execution block** — who signed and in what capacity |

**PDFs are scanned/image-based** — OCR via `fitz.get_text()` returns empty. Use:
```python
import fitz
doc = fitz.open("path/to.pdf")
for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(2,2))  # 2x zoom
    pix.save(f"/tmp/page_{i+1}.png")
# Then vision_analyze each page
```

### Reconstitution Deed Structure (Standard)

```
DEED OF RECONSTITUTION OF PARTNERSHIP
Date: [date], Bangalore

BY AND BETWEEN:
- Partner 1 (Continuing Partner)
- Partner 2 (Continuing Partner)

WHEREAS:
A. Original Partnership Deed dated [date], registered as Firm No. [number]
B. [Predecessor firm, if any] was dissolved via Partition Cum Settlement Deed dated [date]
C. Under the Partition Deed, Partner 1 was allocated [properties]
D. Under the Partition Deed, Partner 2/third party was allocated [properties]
E. [Financial arrangements made between partners]
F. Partners now wish to reconstitute

NOW THIS DEED WITNESSETH:

ARTICLE 1: RECONSTITUTION
1.1 Name Change: From [old name] to [new name]
1.2 Ratio Change: From [old ratio] to [new ratio]
1.3 Supersession: All terms of this Deed replace the original deed

ARTICLES 2-13: (Same governing terms as KAAJ V2 deed - 12 articles)
- Definitions
- Name, Registered Office, Registration
- Commencement, Term, Exclusion of Partnership at Will
- Pooling, Conveyance, Covenants on Land Assets
- Capital Contribution and Conditions Precedent
- Revenue Waterfall and Profit Sharing
- Firm Management and Banking Operations
- Representations, Warranties, Title Indemnity
- Restrictive Covenants and Non-Compete
- Succession, Deed of Adherence, Expulsion
- Statutory Compliance and LLP Conversion
- Governing Law and Arbitration

SCHEDULES A-D: (Land schedules + documents checklist)

EXECUTION: Partner 1 + Partner 2 + 2 Witnesses
```

### Capital Contribution: Already-In vs Balance Pattern

Always use this structure:
```
5.2 First Partner's Capital Contribution (Total: Rs. X Cr):
  (a) ALREADY CONTRIBUTED:
      (i) Land Contribution: [Schedule ref] valued at Rs. [X]
      (ii) Cash Contribution: Rs. [Y] paid to Firm's bank via Cheque No. [no] dated [date]
      Total Already In: Rs. [X+Y]
  (b) BALANCE CONTRIBUTION: Rs. [Z] payable within [N] days of satisfaction of ALL conditions precedent:
      (i) Section 281 permission obtained from IT Department for [Partner A] and [Predecessor firm]
      (ii) Original documents returned from [relevant department/authority]
      (iii) Legal due diligence completed by DRA Realty
      (iv) Clear title opinion, clean ECs, updated revenue records, no litigation certificate
```

### Section 281: Condition Precedent ONLY

- **Do NOT** create a standalone article for Section 281
- **Do NOT** include a suspension clause ("until Section 281 is obtained, the deed shall remain suspended")
- List it as one of the conditions precedent for balance payment
- Note that TWO separate applications are needed:
  1. The individual partner (e.g. Ashok Kumar)
  2. The dissolved predecessor firm (e.g. Satvik Developers — by way of abundant precaution)
- The 281 is for the contribution of lands, NOT for the partnership itself

### PTCL Clause: Generalize to 24 Months

```
CRITICAL LEGAL SAFEGUARD: Any land parcel that is not legally clear after completion of legal due diligence within twenty-four (24) months from the execution date shall stand excluded from the Firm's scope and asset book, and the contributing partner's asset contribution valuation shall be downscaled ratably without liability to the non-contributing partner and will be transferred back to the contributing partner.
```

### Contribution Deeds: Reference Explicitly

The reconstitution deed should mention:
```
The Second Partner hereby contributes the Palya Land and Byadarahalli Lands to the capital stock of the Firm vide separate Contribution Deed(s) dated 24 June 2026 executed by the Second Partner in favour of the Firm.
```

### Step-by-Step Change Document Pattern

When creating a final deed from a base template, also create a companion document:
1. **Base doc**: The starting point (e.g. V2 KAAJ Partnership Deed)
2. **Target doc**: The final reconstitution deed
3. **Step-by-step instructions**: Numbered steps with exact copy-paste text from the target

Structure the step-by-step doc as:
- **SECTION A**: Preamble / Parties / Recitals — complete rewrite
- **SECTION B**: Insert new Article 1 (Reconstitution: name change, ratio, supersession)
- **SECTION C**: Definitions — minor additions/updates
- **SECTION D**: Capital Contribution — major restructure
- **SECTION E**: PTCL clause — generalize
- **SECTION F**: Section 281 — remove standalone, keep as condition precedent only
- **SECTION G**: Schedules — update/add as needed
- **SECTION H**: Execution block — simplify
- **SECTION I**: Formatting notes

Each instruction should include "Delete from:" / "Replace with:" directives and the exact text in code blocks.

### Multi-Subagent Pattern for Complex Legal Drafting

For a task involving 3+ source documents, use parallel subagents:

```python
from hermes_tools import delegate_task

results = delegate_task(tasks=[
    {
        "goal": "Read Google Doc A and extract all clauses",
        "context": "Doc ID: ...",
        "toolsets": ["terminal"]
    },
    {
        "goal": "Read executed PDF B and verify parties/schedules",
        "context": "File ID: ...",
        "toolsets": ["terminal", "vision"]
    },
    {
        "goal": "Read reference deed C for format",
        "context": "Doc ID: ...",
        "toolsets": ["terminal"]
    }
])

# Then use the combined results to draft the final document
```

This avoids the 600s timeout issue on single-agent sequential reads of large documents.

### Verification Checklist for Reconstitution Deeds

Before presenting the final deed, verify:
- [ ] Only 2 parties (unless there's a real consenting party)
- [ ] Satvik/predecessor only in narration, not as a consenting party
- [ ] Recitals reference the original Muthanallur deed (date + firm no.)
- [ ] Recitals reference the Partition Deed (date + doc no.)
- [ ] Reconstitution Article covers: name change, ratio change, supersession
- [ ] All subsequent articles renumbered correctly
- [ ] Capital Contribution shows already-in vs balance
- [ ] Section 281 is condition precedent only (no standalone article)
- [ ] PTCL clause generalized to 24 months
- [ ] Contribution Deeds referenced explicitly by date
- [ ] Schedules match the executed PDF exactly
- [ ] Execution block matches the parties (no confirming parties unless in PDF)
- [ ] Date and place correct

---

## Covering Letter for Registration of Reconstitution (District Registrar / RoF)

### When to Draft
User asks for a covering letter to accompany the Deed when submitting to the District Registrar or Registrar of Firms.

### Key Principle: Crisp & Referential
The covering letter is a submission document — the detailed schedules belong in the attached Deed of Reconstitution. The letter should only explain:
1. **What** is being submitted (the Deed)
2. **What changed** (list changes concisely)
3. **Why** original properties are excluded (if applicable)
4. **Request** to register

### Structure
```
Date: [date]
To, The District Registrar / Registrar of Firms, [Address]
Subject: Submission of Deed of Reconstitution of Partnership — [Changes] — [Firm Name] — Firm No. [number]

Sir/Madam,
[Introduction — who we are, what we're submitting]

1. Changes under the Deed of Reconstitution
   • Change of Firm Name: [old] → [new]
   • Change of Profit-Sharing Ratio: [old] → [new]
   • Contribution of New Properties: [name schedules briefly — full particulars in attached Deed]

2. Declaration regarding Original Schedule Properties
   [State that original deed's properties are excluded + reason, e.g., title docs did not complete due diligence]

3. Request — [Bullet summary + request to register]

Yours faithfully,
For [Firm Name] | [Signatures]
```

### Rules
- **No detailed Schedule tables** in the covering letter — the Deed contains them. Just name the schedules and reference the Deed.
- **Always state the reason** for exclusion of original properties.
- **Keep to 3 sections max** (Changes, Declaration, Request).
- **Format**: .docx uploaded to Drive (filed as physical copies).

### Pitfall
- Do NOT copy-paste entire survey-number lists from the Deed into the covering letter — it becomes unreadable.

---

## Board Resolution for Corporate Partner Approving Reconstitution

### When to Draft
User asks for a Board Resolution of a company (e.g., DRA Realty Pvt Ltd) that is a partner in a partnership firm undergoing reconstitution.

### Who It's For
The COMPANY — not the partnership firm. The resolution authorises the company's participation in the reconstitution.

### Structure (Standard Format)
```
BOARD RESOLUTION
[Passed by the Board of Directors on [date]]

"RESOLVED THAT pursuant to the provisions of the Companies Act, 2013 and all other applicable laws, and in terms of the Deed of Reconstitution of Partnership dated [date], the Board of Directors hereby approves, ratifies and confirms:

1. Managing Partner: The Company shall be the Managing Partner of the reconstituted Firm, represented by its Director, [Name], who shall be entitled to operate bank accounts, execute documents, and conduct business affairs.

2. Change of Firm Name: From [old] to [new] effective [date].

3. Change of Profit-Sharing Ratio: Reconstitution to [ratio] ([Partner A]: [X]%, [Partner B]: [Y]%).

4. Contribution of New Properties: Schedule A, B, C of the Deed (briefly described).

5. Capital Contribution: Total commitment ₹[X] Cr — ₹[Y] already contributed, ₹[Z] balance subject to conditions.

6. Authorisation: Mr. [Name], Director and designated representative of the Managing Partner, authorised to execute the Deed, Contribution Deeds, Section 281 applications, and all compliance documents.

RESOLVED FURTHER THAT a certified copy be furnished to the Registrar of Firms."

Certified True Copy
[Signature of certifying Director/CS — DIFFERENT from Authorised Signatory]

CA ATTESTATION
[Separate block: Firm Name, Membership No., UDIN, FRN]
```

### Key Rules
- **Company letterhead**: Name, CIN, PAN, Registered Office at top.
- **List specific changes** — not generic template language.
- **Managing Partner**: Explicitly state the company's role.
- **Authorisation**: Name person + "designated representative of the Managing Partner."
- **Certifying signatory**: Must be different from authorised signatory.
- **CA Attestation**: Separate block — "Certified that the foregoing is a true and correct copy..."

### Pitfalls
- Do NOT use a generic template without listing specific changes — the Registrar needs to see what was approved.
- Do NOT make certifying Director same as authorised signatory.
- The resolution is for the COMPANY (corporate partner), not the partnership firm.

---

## Form 2 — Notice of Change in Constitution of a Firm

### When to Draft
User asks to prepare Form No. 2 under Section 63(1) of the Indian Partnership Act, 1932 and Rule 10 of the Karnataka Partnership (Registration of Firms) Rules.

### Structure
| Section | Content |
|---------|---------|
| **1. Firm Particulars** | Name, Address, Regn No., Registration Date, Change Date |
| **2. Nature of Change** | ☑ only changes being recorded (e.g., only Name Change) |
| **3. New Name** | Former + New name with effective date |
| **4. Partners After Change** | Table — Name, Father's Name, Address, Age, Occupation, Status |
| **5. Declaration** | Signed by all partners |
| **6. Witnesses** | 2 witnesses |
| **7. Documents Attached** | Tailored to the specific change |

### Rules
- **Only tick changes actually being recorded** — if only name change, tick ONLY that box.
- **Documents checklist** must match the change. For name change: Original Partnership Deed copy, Registration Acknowledgement, Reconstitution Deed copy, Aadhaar + PAN of individual partners, Certificate of Incorporation + PAN of corporate partner.
- **No change in partners** = no "Partners Ceased" section. State: "There is no change in the partners. Both existing partners continue."

### Pitfall
- Do NOT include property contribution details if only recording a name change.
- Document list must be specific — generic lists get rejected.
- Form 2 is attested by partners, not by a CA (unlike Board Resolutions).

