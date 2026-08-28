# Partnership Deed Analysis — DRA Realty Perspective

## Workflow for Clause-by-Clause Analysis

### Phase 1: Document Discovery

Search Drive for ALL related documents — not just the deed itself but:
- **Commercial terms / term sheets** — to cross-reference agreed commercials
- **Earlier deed versions** (reconstitution/amendment drafts) — to identify structural changes
- **Accounting ledgers** (PDF/Sheets) — to trace money flow between parties
- **Land lists / survey sheets** — to verify survey numbers, extents, ownership
- **KYC docs** of counterparties
- **Payment records / bank statements**

Drive search patterns:
```python
# Multiple targeted queries
queries = [
    ("name contains 'Satvik' and name contains 'Partnership'", "Partnership docs"),
    ("name contains 'Muthanallur' or name contains 'Ashok'", "Related entity docs"),
    ("fullText contains 'commercial' and fullText contains 'terms'", "Commercial terms"),
    ("name contains 'Nagendra' and name contains 'sale'", "Underlying transaction"),
    ("fullText contains 'Beyadar' or fullText contains 'Bedar'", "Land parcels"),
]
for q, label in queries:
    results = drive.files().list(q=q, fields='files(id,name,mimeType,parents)',
                                  orderBy='modifiedTime desc', pageSize=10).execute()
```

### Phase 2: Document Reading

**Google Docs** → Docs API:
```python
docs = build_service('docs', 'v1')
doc = docs.documents().get(documentId='ID').execute()
text = ''.join(run['textRun']['content']
    for elem in doc['body']['content']
    if 'paragraph' in elem
    for run in elem['paragraph'].get('elements', [])
    if 'textRun' in run)
```

**DOCX** → download + zip parse:
```python
fh = io.BytesIO(drive.files().get_media(fileId='ID').execute())
archive = zipfile.ZipFile(fh)
xml_content = archive.read('word/document.xml')
# Parse XML with namespace {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
```

**Google Sheets** → Sheets API:
```python
sheets = build_service('sheets', 'v4')
result = sheets.spreadsheets().values().get(spreadsheetId='ID', range="'Sheet1'").execute()
rows = result.get('values', [])
```

**PDF ledgers** → pdftotext:
```bash
pdftotext "path.pdf" -
```

### Phase 3: Structural Mapping

Map documents into a **current vs target structure** comparison:

| Element | Old Draft Structure | New Draft Structure | Impact |
|---------|-------------------|-------------------|--------|
| Party roles | Who retires/joins | Who stays/changes | If roles reversed, old draft unusable |
| Capital structure | How much, when | How much, when | Payment triggers, sequencing |
| Profit ratio | X:Y | X:Y | Flag discrepancies |
| Management | Who controls | Who controls | DRA should be managing partner |
| Exit/lock-in | 0/3/5/7 years | Required term | Protections needed |

### Phase 4: Risk Identification (DRA Perspective)

**High-risk areas to flag:**
1. **Contribution imbalance** — If DRA contributes less land value, counterparty could challenge partnership under Section 6(b) Partnership Act
2. **Title defects** — PTCL/GPA lands, litigation-stayed parcels → need tiered contribution
3. **Document custody** — Originals must be in DRA's custody before significant payments
4. **Payment conditions** — Must be objective, not subjective ("satisfactory to DRA")
5. **Profit ratio discrepancy** — Cross-reference recitals vs operative clauses vs waterfall
6. **Capital adjustment mechanism** — Define formula for deducting title rectification costs from counterparty's capital account
7. **Continuity** — Death/insolvency of individual partner should not dissolve firm

### Phase 5: Protection Clause Drafting

**Standard clauses to draft from DRA's perspective:**

1. **Non-contestation clause**: Counterparty acknowledges DRA's aggregate contribution (cash + land + brand + management) = full and fair consideration. No challenge to adequacy.

2. **Tiered contribution with capital adjustment**: Each land parcel valued provisionally until: (a) legally transferred to firm, (b) legal DD completed, (c) originals in DRA custody. Rectification costs deducted from counterparty's capital account.

3. **Document custody**: ALL originals in DRA's physical custody. Counterparty has inspection rights. Warranty of no duplicate originals.

4. **Objective payment conditions**: Written legal opinion, 30-year ECs, updated RTCs/mutation, no pending litigation, physical document delivery checklist.

5. **Capital account adjustment formula**: Cost of rectification → first adjusted against counterparty's capital account → if insufficient, personal liability of counterparty.

6. **Lock-in + personal guarantee**: Counterparty personally guarantees lock-in compliance. Any attempted transfer void.

7. **Expansion of expulsion grounds**: Include failure to contribute minimum land within 12 months, failure to cure title defects within notice period.

### Phase 6: Deliverable Structure

Save analysis as a single markdown file with sections:
- A. Gap Analysis (old vs new structure)
- B. Risk Identification (per key area)
- C. Protection Clauses Drafted (with full clause language)
- D. Specific Recommendations (new deed vs amendment)
- E. Consolidated Change List (clause-by-clause table)

## Key Triggers for This Workflow
- "analyze partnership deed"
- "clause by clause analysis" + "partnership"
- "review reconstitution deed"
- "compare commercial terms with deed"
- "protection clauses for DRA Realty"
