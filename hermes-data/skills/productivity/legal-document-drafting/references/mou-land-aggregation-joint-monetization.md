# MOU Drafting — Land Aggregation & Joint Monetisation

Covers MOUs between an aggregator/developer (First Party) and a land-owning entity (Second Party) for joint land aggregation and monetisation. Distinct from partnership deeds — this is a contractual arrangement, not a partnership formation.

## Formatting Rules (Nishant preference, Jun 2026)

### RED Markup — ALL changes in RED
Every modification to any legal document must be applied in **RED** text color:
- Party name changes (deletions → replacements)
- New clause insertions
- Clause rewrites or amendments
- Alignment/formatting corrections

Use Docs API `updateTextStyle` with `foregroundColor.rgbColor: {red: 1.0, green: 0.0, blue: 0.0}`.

Do NOT use strikethrough or comments — replace text directly and color it RED.

### Alignment — WHEREAS clauses must be JUSTIFIED
Recital paragraphs (WHEREAS A, B, C...) should use **JUSTIFIED** alignment, not CENTER.
```python
{'paragraphStyle': {'alignment': 'JUSTIFIED'}, 'fields': 'alignment'}
```

### Index Drift Trap with deleteContentRange
When using `deleteContentRange` + `insertText` in the same batchUpdate, subsequent operations' indices shift. The insert happens at the deletion point, so the new text's range starts at the same index. For RED coloring, compute `startIndex: DELETE_START, endIndex: DELETE_START + len(new_text)`.

If text gets mangled after an index operation, use `replaceAllText` with `containsText` + `replaceText` as a safety net to fix garbled fragments.

---

## Party Descriptions

### Aggregator/Developer (First Party)
```
M/s [FIRM NAME],
Represented by its Partners [NAME(S)],
Registered Office at [ADDRESS].
PAN No. [PAN].
```

### Partnership Firm as Second Party
When the second party is a partnership firm (e.g. DRA KAAJ Development Partners), use this expanded form:
```
M/s. DRA KAAJ DEVELOPMENT PARTNERS,
A Partnership Firm registered under the Indian Partnership Act, 1932,
Having its Registered Office at [FULL ADDRESS],
Represented by its Partners.

The Partners of [Firm Name] are:

(i) [PARTNER 1 NAME], a company incorporated under the Companies Act, 2013, bearing CIN [CIN], having its registered office at [ADDRESS], represented by its Director, [NAME] (Aadhaar No. [AADHAAR]) [and/or PAN [PAN]]; and

(ii) [PARTNER 2 NAME], Son of [FATHER'S NAME], aged about [AGE] years, residing at [ADDRESS], bearing Aadhaar No. [AADHAAR] and/or PAN [PAN].
```

Keep the "Hereinafter referred to as the 'SECOND PARTY'" clause unchanged.

---

## Schedule Property Formats

### Survey Table Format
```
Sl.No. | Sy.No. | Owner Name | Total Extent (A-G) | Kharab (A-G) | Extent in Guntas
1 | [Sy.No] | [Owner Name] | [A-G] | [A-G] | [Guntas]
```

Village headers separate each geography:
```
[SCHEDULE A PROPERTY]

Byadarahalli Village
[survey table]

Gundlahalli Village
[survey table]
```

When survey data is scanned/image-only (OCR can't extract tabular data), insert a placeholder:
```
SCHEDULE [X] PROPERTY
[Village Name] — [Party Name]

(Refer to scanned PDF for complete Schedule [X] survey details — including Sy.No. [list] — owned by [Party Name])
```

---

## Standard Clauses for Aggregator-Developer MOU

### 1. JOINT MONETISATION
Both parties bound to jointly and exclusively monetise all Project Lands together once:
- MOU is executed AND either party pays consideration, OR
- Either party registers any land

Neither party may independently deal with Project Lands without mutual written consent.

### 2. LAND AGGREGATION AND PURCHASE PRIORITY
Target: ~30 acres. Purchased on 50:50 basis (or mutual %). Priority order:
(a) Fill critical gaps / remove bottlenecks for contiguity
(b) Purchase minimum parcels to extend contiguity (bridging detached parcels)
(c) Additional parcels as jointly identified

### 3. CONSIDERATION STRUCTURE
Indicative: Rs. X Cr/acre, ALL-INCLUSIVE of:
- Revenue clearance and matters
- Legally clear, marketable title (no pending issues/claims/parties)
- Full survey of physical extent
- All legal docs, revenue records, village/family trees, grant documents
- Statutory processes (Podi, RTC corrections, mutation corrections)
- Encroachment resolution

**EXCLUDED** (borne separately): Stamp duty, Registration, CLU fees, Land Conversion costs.

### 4. REGISTRATION BY SECOND PARTY
- Second Party registers each parcel in **one shot**
- Condition: parcel must have clear, marketable title — free of all encumbrances, claims, revenue dues
- Payment concurrent with registration only
- First Party ensures each parcel is registrable before Second Party is called

### 5. FIRST PARTY'S LEAD ROLE
- First Party drives identification, negotiation, aggregation, procurement
- Title verification, legal due diligence, execution of agreements
- At every stage: **joint monetisation** by both parties

### 6. DEVELOPMENT OPTIONS
- DM for Plotted Development via Grade A Bangalore developers is one option
- Any more lucrative proposal may be jointly considered and approved
- All terms mutually finalised and approved in writing

### 7. SHARING OF PROCEEDS
- Strictly proportional to respective land holding
- No additional consideration, premium, management fee beyond proportionate entitlement

### 8. BINDING MEDIATION (NOT ARBITRATION)
- Amicable resolution: 30 days
- Failing that: **binding mediation** at Bengaluru
- Sole mediator mutually appointed within 15 days
- If no agreement: each party nominates one mediator → the two nominate a third (presiding)
- Decision of sole mediator or panel = **final and binding**
- Conducted under Mediation Act, 2023
- **Do NOT use** Arbitration & Conciliation Act, 1996 — user specifically replaced arbitration with binding mediation

### 9. CONTINUING OBLIGATIONS / GOOD FAITH
- Obligations continue until monetisation complete OR mutual written termination
- Utmost good faith, prompt disclosure of material info
- No adverse actions affecting project or other party's rights

---

## Party Description Replacement Pattern (via Docs API)

When replacing a party name throughout a document (e.g., Satvik Developers → DRA KAAJ Development Partners):

1. **Replace exact party name strings** using `replaceAllText`:
```python
requests = [
    {'replaceAllText': {
        'containsText': {'text': 'SATVIK DEVELOPERS', 'matchCase': True},
        'replaceText': 'DRA KAAJ DEVELOPMENT PARTNERS'
    }},
    {'replaceAllText': {
        'containsText': {'text': 'Satvik Developers', 'matchCase': True},
        'replaceText': 'DRA KAAJ Development Partners'
    }}
]
```

2. **Replace the full party description block** (indices depend on document structure):
   - Delete `deleteContentRange` from start to end of old description
   - Insert new text at the same index
   - Color the insertion RED with `updateTextStyle`
   - All three in one batchUpdate call (indices adapt sequentially)

3. **Verify** — re-read the document and check for any remaining old party name strings.

---

## Reference Session
- Session: 20260629 — MOU between Nine Triangle Infrastructure (First Party) and DRA KAAJ Development Partners (Second Party) for Byadarahalli & Gundlahalli land aggregation
- Source scanned PDF: `doc_ff061640b314_Byadarahalli - MOU draft btw Nine triangle and DRA(scan).pdf`
- Google Doc ID: `1uT_mEHDpYGrb5i-O2n65PxGAoAw9NLwZexp4rVXKJFQ`
- Changes: Party name swap (Satvik → DRA KAAJ), expanded party description with partner details, 8 new clauses (17-24), binding mediation replacing arbitration, alignment fixes, all in RED
