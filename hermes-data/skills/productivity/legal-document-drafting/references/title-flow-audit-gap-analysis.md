# Title-Flow Audit & Gap Analysis for Sale Deed Drafts

## When to use this

The user shares an existing sale deed draft and asks you to **verify the title flow** — trace each survey number in Schedule A back through every recital, identify whether the VENDOR actually holds registered title to each, spot gaps where the VENDOR's claimed ownership is unsubstantiated, and deliver a marked-up document with findings highlighted in yellow.

Differs from `title-flow-recitals.md` (which covers *writing* new recitals) — this reference covers *auditing* recitals already drafted.

## Audit methodology (step by step)

### Step 1: Build the survey-to-receipt map

Read the draft and extract every registered document the recitals claim as a source of the VENDOR's title. For each document, note:
- Document number, date, SRO
- Parties (buyer = the entity receiving title)
- Survey numbers conveyed
- Whether the buyer is the **VENDOR** (e.g. "Sevaganapalli Land Partners") or a **different entity** (e.g. "DRA Realty Pvt. Ltd.")

Construct a table in your analysis like:

```
Document         Buyer              Survey Nos                  VENDOR?   Status
──────────────────────────────────────────────────────────────────────────────
21201/2023       Sevaganapalli     158/1A1A, 158/1C1, …        ✓ YES    VENDOR
4292/2024        DRA Realty        176/2B, 177/1A, 176/1B2      ✗ NO     Need chain
21785/2024       DRA Realty        158/1C9A, 158/1C4, …        ✗ NO     Need chain
7963/2025 (JDA)  DRA Realty        166/1, 167/1G, 168/1B       ✗ JDA    Rights not in VENDOR
6157/2025 (JDA)  DRA Realty        177/1B, 177/2A1              ✗ JDA    Rights not in VENDOR
```

### Step 2: Match Schedule A survey numbers to the map

Take every survey number listed in Schedule A (the project land). For each one, ask:
1. Is this survey number mentioned in any recital? Which one?
2. Does the recital show that the VENDOR — specifically — acquired title?
3. If the recital shows a different entity (DRA Realty, JDA owner), what document bridges that entity's rights to the VENDOR?

### Step 3: Classify each survey number

```
Status codes:
  ✓ VENDOR       — VENDOR directly owns via registered sale deed
  ✗ DRA Realty   — DRA Realty owns it, no chain to VENDOR shown
  ✗ DRA (JDA)    — DRA Realty has only JDA rights, not full title
  ✗ UNKNOWN      — Survey number not traced to any recital
  ✓ EXCHANGED    — Was VENDOR's but exchanged away (removed from holding)
  ✓ SOLD         — Was VENDOR's but sold to DRA Realty
```

### Step 4: Identify critical gaps

**Type A — No registered chain:** A survey number in Schedule A was acquired by DRA Realty (or another entity) but the draft contains NO document showing how it reached the VENDOR. Typical locations:
- Properties from Exchange Deeds where the counterparty (Venkatamma) conveyed to DRA Realty, not the VENDOR.
- Properties from JDAs where the owner contracted with DRA Realty as developer, and the VENDOR has no assignment/novation.

**Type B — Mismatched survey sub-numbers:** Schedule A lists a different sub-division than what the recitals describe (e.g. `166/2B2` in Schedule A but `166/2B` in Recital (iii)). Needs clarification — are they the same with further sub-division, or a different parcel?

**Type C — Missing consolidation recital:** The draft recitals list each source deed individually, then jump straight to "Project and Plotted Development" without a consolidation paragraph stating "Through the above documents, the VENDOR became absolute owner of all Schedule A properties aggregating Ac.X.XX." This consolidation recital is the bridge between individual title flows and the VENDOR's claim of absolute ownership.

**Type D — No JDA/contribution recital between VENDOR and CONFIRMING PARTY:** When the CONFIRMING PARTY (DRA Realty) owns land that appears in Schedule A (project land sold by the VENDOR), there must be a recital showing the mechanism (JDA, Contribution Agreement, Development Agreement) under which the CONFIRMING PARTY contributed its land into the project, authorizing the VENDOR to sell plots from the consolidated layout.

**Type E — Truncated title flows:** Some recitals (especially Exchange Deeds) only name the survey numbers without providing the detailed chain from original owners to the transferor. These need the same level of granularity as the main Sale Deed recital's title flows.

**Type F — Date discrepancies:** A document referenced in one recital with one date and in another recital with a different date (e.g. "exchange deed dated 14.11.2024" in Recital (iv) vs "dated 03.07.2025" in Recital (viii)). These must be reconciled.

### Step 5: Produce the delivery

**Survey-by-survey table:** List every Schedule A survey number with its status, owning entity, source document, and specific issue.

**Yellow-highlighted DOCX:** Insert annotation paragraphs at the exact positions in the draft where each gap is found. Each annotation should:
- Be highlighted yellow (w:shd w:fill="yellow")
- Be bold (w:b)
- Start with `[HIGHLIGHT — TITLE FLOW GAP #N]`
- State the issue clearly and prescribe the fix
- Immediately follow the paragraph describing the gap's source

**Summary of priority order:**
1. 158/1C9A (or whichever survey feeds the sold plot) — VENDOR must hold title to the plot being sold
2. Exchange Deed properties in Schedule A but held by DRA Realty
3. JDA lands in Schedule A but held by DRA Realty
4. Missing consolidation recital
5. Missing JDA/contribution recital between VENDOR and CONFIRMING PARTY
6. Survey sub-number mismatches
7. Date discrepancies
8. Truncated title flows

## DOCX markup technique

When inserting yellow-highlighted annotation paragraphs into an existing .docx:

```python
from docx import Document
from docx.oxml.ns import qn
from lxml import etree

doc = Document('input.docx')

# For each annotation, find the paragraph to follow
after_para = doc.paragraphs[idx]
parent = after_para._element.getparent()
pos = list(parent).index(after_para._element)

# Build new paragraph element
p_elem = etree.SubElement(parent, qn('w:p'), {})
parent.remove(p_elem)
parent.insert(pos + 1, p_elem)

# Add yellow-highlighted run
run_elem = etree.SubElement(p_elem, qn('w:r'))
rpr = etree.SubElement(run_elem, qn('w:rPr'))
hl = etree.SubElement(rpr, qn('w:shd'))
hl.set(qn('w:val'), 'clear')
hl.set(qn('w:fill'), 'yellow')
b = etree.SubElement(rpr, qn('w:b'))  # bold

t_elem = etree.SubElement(run_elem, qn('w:t'))
t_elem.text = annotation_text
t_elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

doc.save('output.docx')
```

**Important:** Insert annotations in **reverse paragraph-index order** so that earlier insertions don't shift the indices of later ones.

## Pitfalls

- **Recitals may use inconsistent survey number references** (e.g. "166/2B" vs "166/2B2" in Schedule A). When in doubt, flag it — don't assume they're the same.
- **DRA Realty as CONFIRMING PARTY** holding land in the project creates a structural gap: the VENDOR (typically the partnership firm) sells plots, but DRA Realty (a company) owns several source properties. A recital showing a Contribution Agreement / Development Agreement / Assignment of Rights between them is essential for clean title passing.
- **JDAs generate only contractual rights**, not full ownership. The VENDOR cannot convey absolute title to JDA land unless the JDA rights have been assigned to it and the owner is a confirming party to the sale deed.
- **Title flows for Exchange Deeds** are often truncated in drafts — attorneys only name the survey numbers without tracing the chain to the transferor. These need to be expanded with the same level of detail as the main Sale Deed recital.