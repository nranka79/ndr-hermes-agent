# RERA Sale Deed — Clause-by-Clause Analysis Workflow

Use when NDR asks to analyze/review a proforma Absolute Sale Deed for a DRAAS Bangalore project, especially post-OC receipt.

## Workflow

### 1. Gather Reference Documents from Drive

Search Drive for these classes of documents:

| Type | Search Pattern | Purpose |
|------|---------------|---------|
| **RERA Notified Format** | `fullText contains "Notified RERA Agreement for Sale"` | The authoritative RERA-mandated format |
| **RERA Approved Revised 2018** | `name contains "RERA Approved Revised"` | 2018 revision with additional clauses |
| **Executed Ranka sale deed** | `name contains "Ranka" and name contains "Sale Deed"` | Previously executed DRAAS deeds for consistency check |
| **Bangalore executed deed** | Search for Embassy Habitat / 914EH sale deeds | Recently executed Bangalore deed as reference |
| **Occupancy Certificate** | `name contains "Ranka Iris" and name contains "Occupancy Certificate"` | Compare promised vs delivered areas/amenities |
| **Commencement Certificate** | Same project search | Verify timeline from CC to OC |

### 2. Download & Extract Text

```python
# For Google Docs: export as text/plain
content = drive.files().export(fileId=fid, mimeType='text/plain').execute()

# For binary PDFs: get_media then fitz
content = drive.files().get_media(fileId=fid).execute()
doc = fitz.open(stream=content)
text = ""
for page in doc:
    text += page.get_text()

# For scanned PDFs: pdftoppm + tesseract
pdftoppm -png -r 200 input.pdf /tmp/page
tesseract /tmp/page-1.png stdout

# For .docx: python-docx
from docx import Document
doc = Document(path)
text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
```

### 3. Launch Parallel Analysis via `delegate_task`

Use `delegate_task` with a single leaf agent that reads ALL documents and produces the clause-by-clause comparison. Pass:
- The proforma text (full doc)
- All reference document texts
- A structured output format (executive summary → clause-by-clause → OC issues → missing clauses → association analysis)

The agent should be given ALL the reference text paths upfront — don't make separate agents for each reference since the comparative analysis needs all references simultaneously.

### 4. Present Findings

Structure the output for Telegram:
- **🚫 BLOCKERS** — clauses that contradict RERA and must be deleted (blanket discharge, defect liability dilution, super built-up area pricing)
- **🔴 HIGH** — material non-disclosures (OC deviations, compounding fees, missing Apartment Ownership Act reference)
- **🟡 MEDIUM** — problematic but negotiable (association governance, terrace rights, parking discretion)
- **OC-SPECIFIC** — table showing what OC says vs what proforma says/omits

## Key RERA Clauses Checklist

These mandatory clauses from the Notified RERA Agreement for Sale format are frequently MISSING from DRAAS proforma sale deeds:

| # | Clause | RERA Reference | Why Critical |
|---|--------|---------------|--------------|
| 1 | Carpet area as pricing basis (not super built-up area) | Section 4(2)(l)(D) | RERA mandate — price must be carpet-area-based |
| 2 | Escalation-free total price (except statutory charges) | Para 1.3 | Purchaser protection against arbitrary hikes |
| 3 | Carpet area ±3% recalculation mechanism | Para 1.7 | Mandatory refund/adjustment provision |
| 4 | Conveyance deed within 3 months of OC | Para 10 / Section 17 | RERA statutory timeline |
| 5 | Promoter representations (title, approvals, no litigation) | Para 8 | Standard warranties |
| 6 | Promoter default consequences (refund + interest) | Para 9.2 / Section 18 | Purchaser remedy |
| 7 | No further mortgage after agreement | Para 18 | Title protection |
| 8 | State Apartment Ownership Act compliance | Para 19 | For Bangalore: Karnataka Apartment Ownership Act, 1972 |
| 9 | 70% separate account statement | Section 4(2)(l)(D) | Fund protection |
| 10 | Dispute resolution via RERA adjudication | Para 33 | Statutory remedy |
| 11 | OC copy handover at conveyance | Para 7.2 | Purchaser right |
| 12 | Binding on subsequent allottees | Para 23 | Continuity |
| 13 | Proportionate share calculation (carpet area ratio) | Para 26 | Transparency |
| 14 | Governing law under RERA | Para 32 | Legal framework |
| 15 | Parking as single indivisible unit with apartment | Para 1.9 | Prevents separate parking sale |

## Common Red Flags in DRAAS Proforma Sale Deeds

### Clause 5.3 — Blanket Discharge of Promoter
**The Problem:** Purchaser discharges promoter from ALL obligations AT execution, before the 5-year defect liability starts.
**Why it's wrong:** Contradicts RERA Sections 14(3) and 18. Purchaser waives claims for area shortfall, delayed possession, construction defects.
**Fix:** Delete entirely.

### Clause 11 — Defect Liability Exclusions
**The Problem:** Extensive exclusions that defeat RERA Section 14(3):
- Lifts/generators/STP/gym equipment → excluded (illegal — they are construction work)
- Basement water seepage → "not a defect" (illegal — this IS a structural defect)
- Minor cracks, paint peeling, tile shade differences, air pockets, glass/ceramic/vitrified materials after possession → excluded
**The Rule:** RERA allows ONLY "normal wear and tear" exclusion. Everything else is the promoter's responsibility for 5 years.
**Fix:** Strip all exclusions beyond "normal wear and tear."

### Super Built-Up Area as Primary Metric
**The Problem:** Proforma lists super built-up area first and carpet area second, or uses the oxymoron "exclusive common area."
**Fix:** Carpet area must be the primary/only pricing metric per RERA.

### OC Non-Disclosure
**The Problem:** Proforma says "completed in all respects" without disclosing:
- Deviations from sanctioned plan (with compounding fees paid)
- Forfeited security deposit
- Specific OC conditions (EV charging, rainwater harvesting, fire clearance)
**Fix:** Full disclosure in recitals.

### Association / Deed of Adherence
**The Problem:** 
- "Without right to question the same" clause is legally void
- No Deed of Adherence mentioned (purchaser's binding document)
- No timeline for association formation (RERA Section 11(3))
- Karnataka Apartment Ownership Act not referenced
**Fix:** Add Deed of Adherence requirement, delete "without right to question," add state Act reference.

## Pitfalls

- **Scanned PDFs are common for OCs** — always check with fitz first, fall back to pdftoppm + tesseract
- **docx files from Drive may actually be Google Docs** — check mimeType before choosing export vs get_media
- **"Shared with me" files can't be moved** between folders — note to user rather than silently failing
- **The Ranka Iris Ran_ka vs Ran_ka Iris vs RankaIris variation** — the folder name appears as both "Ranka Iris", "Ranka Iris ", "RankaIris" in Drive — search with partial/alternative matches
- **OC conditions differ per project** — always read the full OC, don't reuse checklists from other projects
- **Karnataka Apartment Ownership Act vs other states** — Ranka Udaya (Hosur, Tamil Nadu) follows Tamil Nadu rules. Only Bangalore projects need Karnataka Act compliance.
