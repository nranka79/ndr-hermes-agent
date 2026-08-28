# Reconstitution Deed & Section 281 Application Pattern

## Overview
This reference covers the pattern for:
1. Drafting a **Deed of Reconstitution** (changing an existing partnership firm's name, ratio, and terms)
2. Drafting **Section 281 applications** (income tax approval for land contribution to a firm)
3. Creating **step-by-step change instruction docs** for colleague delegation
4. **RED color markup** convention for Google Doc updates

---

## 1. Reconstitution Deed Pattern

### When to use
When the user wants to change key terms of an existing registered partnership firm (name, profit ratio, capital structure) rather than creating a new partnership deed from scratch.

### Source documents needed
- **Original partnership deed** — find the date, registration details (Firm No.), parties
- **New/desired partnership deed** — the Google Doc version with the target terms
- **Any Partition Deed** or dissolution deed that explains how properties came to current partners

### Structure of a Reconstitution Deed
```
DEED OF RECONSTITUTION OF PARTNERSHIP
Date: [current date], at Bangalore

BY AND BETWEEN:
[Original continuing partners only — no consenting parties unless required]

RECITALS:
A. Original partnership deed dated [original date], registered as Firm No. [xxx]
B. Background facts (dissolution of prior entity, property allocations, etc.)
C. Partners now wish to reconstitute the Firm

NOW THIS DEED WITNESSETH:

ARTICLE 1 — RECONSTITUTION
1.1 Name Change: From [Old Name] to [New Name]
1.2 Profit Ratio Change: From [old ratio] to [new ratio]
1.3 Supersession: All terms replaced by this Deed

ARTICLES 2-N — (Copied from the target partnership deed, renumbered)
[Import all clauses: definitions, pooling/conveyance, capital contribution,
revenue waterfall, management, reps/warranties, restrictive covenants,
succession, compliance, arbitration]

SCHEDULES — (Copied from target deed)
Schedule A: [First land parcel]
Schedule B: [Second land parcel with Part A/B if needed]
Schedule C: [Additional parcels]
Schedule D: (Optional — documents checklist)

EXECUTION
Parties + 2 witnesses
```

### Key drafting rules
- **Only 2 parties** if the target deed has only 2 — no consenting/confirming parties unless explicitly needed
- **Recitals must tell the full chain**: Original deed → Dissolution of prior entity → Partition → Current ownership → Reconstitution need
- **Capital contribution must be updated** to show what's ALREADY contributed vs what's BALANCE
- **Section 281 is a condition precedent** for balance payment — NOT a separate article, NOT a suspension clause
- **PTCL/general land clearance clause**: generalize to 24 months, cover any land not legally clear
- **Contribution Deeds** should be referenced as separate documents dated same day

---

## 2. Section 281 Application Pattern

### When to use
When a partner needs income tax department approval to contribute land/assets to a partnership firm, to ensure the transfer isn't challenged as void under Section 281 of the Income Tax Act.

### Who applies
- **Individual partners** apply separately for their own lands
- **Dissolved firms** may also apply separately for lands they formerly held (by way of abundant precaution)

### Structure of Section 281 Application
```
[Date]

From,
[APPLICANT NAME]
PAN: [PAN]
[Address]
[Phone] | [Email]

To,
THE ASSESSING OFFICER
Circle ___(___)
[Address]

Dear Sir / Madam,

Sub: [Name], PAN: [PAN] — Application for prior approval under
Section 281 of the Income-tax Act, 1961

Ref: Proposed contribution of land assets to [Partnership Firm Name]

SECTION 1 — DETAILS OF THE APPLICANT
[Name, PAN, address, residency status]

SECTION 2 — DETAILS OF THE PROPOSED TRANSACTION
[Name of the firm, date of partnership deed, partners, nature of contribution]

SECTION 3 — DESCRIPTION OF THE LAND ASSETS
[Full schedule: survey numbers, extent, village, taluk, district,
document references (sale deed/GPA/Agreement of Sale numbers and dates)]

SECTION 4 — TAX COMPLIANCE HISTORY
[Table: AY, date of filing, returned income]

SECTION 5 — DECLARATION
[No outstanding tax demand — attach screenshot]

SECTION 6 — PRAYER
[Request approval under Section 281]

Yours faithfully,

_________________________
(Applicant Name)
PAN: [PAN]

Enclosures:
Annexure 1: ITR acknowledgements (last 3 years)
Annexure 2: Tax demand status screenshot
Annexure 3: Partnership Deed / Reconstitution Deed
Annexure 4: Land schedules
Annexure 5: Title documents
```

### Content sources
- Applicant's PAN, Aadhaar, address → from existing deeds or Google Contacts
- Land schedules → from the partnership deed schedules
- AO details → ask user if unknown (use placeholder)

---

## 3. Step-by-Step Change Instruction Document

### When to create
When the user wants to delegate document editing to a colleague (e.g., Prakash) and needs to explain exactly what changes to make.

### Structure
```
STEP-BY-STEP CHANGES: [Base Doc] → [Target Doc]

Reference Documents:
1. NEW DEED (final reference) — [link]
2. BASE DOCUMENT (starting point) — [link]

INSTRUCTIONS:

SECTION A: [Area of change]
Step A1: [What to do]
- DELETE FROM: [exact text to remove]
- REPLACE WITH: [exact text to add]

SECTION B: [Next area]
...
```

### Key principles
- Give the colleague TWO options: (A) apply changes to base doc preserving formatting, or (B) take the new doc and re-apply formatting
- Use code blocks for exact text to copy-paste
- Number every step sequentially
- Include a quick-reference summary table at the end

---

## 4. RED Color Markup Convention

### When updating Google Docs for Nishant's review
1. All changes must be in **RED** text (RGB: 1.0, 0.0, 0.0)
2. Use **bold + red** for emphasis
3. Edit the **existing document in-place** — never create a new version
4. After changes, provide a summary table showing Before → After

### Implementation (Docs API)
```python
requests = [
    {
        'insertText': {
            'location': {'index': position},
            'text': 'new text here'
        }
    },
    {
        'updateTextStyle': {
            'range': {
                'startIndex': position,
                'endIndex': position + len('new text here')
            },
            'textStyle': {
                'foregroundColor': {
                    'color': {
                        'rgbColor': {'red': 1.0, 'green': 0.0, 'blue': 0.0}
                    }
                },
                'bold': True
            },
            'fields': 'foregroundColor,bold'
        }
    }
]
```

---

## 5. Delegating Complex Legal Drafting to Subagents

For complex legal documents (reconstitution deeds, Section 281 applications), use `delegate_task` with:

- **One subagent per source document** to extract content
- **Write source files to `/tmp/`** (e.g., `/tmp/kaaj_v2_deed.txt`) for cross-agent sharing  
- **Final drafting subagent** that reads all source files and creates the Google Doc
- Use the file-based handoff pattern: write content to a `.txt` file first, then use a Python script to create the Google Doc via Drive + Docs APIs
