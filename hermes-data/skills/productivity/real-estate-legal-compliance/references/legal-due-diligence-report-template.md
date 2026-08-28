# Legal Due Diligence Report — Template & Workflow

## When to Use

When the user provides registered Indian property documents (Sale Deed, Confirmation Deed, Gift Deed, GPA, etc.) and asks for a comprehensive Legal Due Diligence Report covering chain of title, encumbrances, statutory compliance, red flags, and title opinion.

## Critical Constraint — Report Scope

**State clearly that the report is based solely on documents provided.** Do NOT fabricate dates, document numbers, case laws, or EC status. Where a document is missing (EC, khata, RTC), flag it as a pending requirement — do not assume it exists and is clean.

## The Six-Section Structure

### 1. Executive Summary
- Table of documents reviewed (Document type, registration No., date, SRO)
- Property details (sy no, extent, village, hobli, taluk, district)
- Purchaser name, vendors/confirming parties
- Total consideration and mode of payment
- **Bottom-line title opinion** (prima facie marketable / qualified / adverse)

### 2. Chain of Title
- Chronological table: each title event (ancestral ownership → inheritance → sale → confirmation)
- For each event: date, nature of transfer (inheritance/sale/gift), registration details if applicable, parties
- Show the current title holder explicitly

### 3. Property Schedule
- Survey number(s), extent, village, hobli, taluk, district
- Boundaries: North / South / East / West
- Current land use (agricultural, residential, industrial, etc.)

### 4. Sale Consideration & Payment
- Table of payments: amount, mode (cheque/DD/RTGS), instrument number, date, bank, payee
- Total consideration
- Stamp duty and registration fees paid

### 5. Encumbrances & Liabilities
**From documents:** List vendor covenants about encumbrances (mortgages, litigation, attachments, tenancy, ceiling limit, SC/ST grant land)
**Pending verification:** Standard list of missing documents that need independent verification:
- Encumbrance Certificate (EC) — last 13 to 30 years
- Khata Certificate / Extract
- RTC / Mutation Register extracts
- Property tax paid receipts
- Land use conversion order (if developing)

### 6. Statutory Compliance & Approvals
- Registration compliance: book, SRO, stamp duty adequacy
- Land use compliance: agricultural ceiling, tenancy, SC/ST restrictions
- Building approvals: only if property has construction (OC/CC/Plan sanction)
- Conversion order: if property is to be developed for non-agric use

### 7. Red Flags & Risks
Rate each:
- 🔴 Critical (missing EC, no khata, undisclosed LRs)
- 🟡 Moderate (joint title complexity, elderly parties, multiple vendors)
- ⚠️ Addressed (defect that a confirmation deed cured)

Patterns particularly common in Indian registered deeds:
- **Non-joinder of LRs:** Original sale misses some legal heirs → cured by subsequent Confirmation Deed. Flag the residual risk that more LRs may exist.
- **Multiple co-vendors (15+):** High complexity. Need family tree to confirm all traced.
- **Elderly vendors:** Capacity concern; check proper execution (thumb impressions, witnesses).
- **No antecedent agreement:** No prior Agreement to Sell on record.

### 8. Key Covenants & Representations
Summarize the material covenants from the deed: title warranty, possession, no encumbrances, indemnity, taxes paid, title deeds delivered.

### 9. Conclusion
- Opinion on title (prima facie marketable / qualified / adverse)
- Pending documents checklist (numbered table) required for unqualified clearance
- Standard disclaimer

## Registered Indian Deed Extraction Pipeline

Registered Indian legal documents (Sale Deeds, Confirmation Deeds, Gift Deeds, Settlement Deeds) **consistently fail with pymupdf/pdftotext text extraction** — returning only the repeating header/footer text ("This Document... Page X of Y"). The actual deed content is embedded as images on stamp paper pages.

**Workflow:**

1. **Try pdftotext first** as a fast check — it will usually return only the certified copy certification page (Kannada text at the end) and blank stamp paper sheets.

2. **Render to images** with pdftoppm:
   ```bash
   pdftoppm -jpeg -r 200 -f 1 -l 2 input.pdf /tmp/output_prefix
   ```
   - First 2 pages usually contain: deed title + first party recitals (page 1), Kaveri stamp duty endorsement (page 2)
   - Middle pages (check every 5-10 pages): property schedule, consideration, terms, covenants
   - Last pages: witness/signature page, notary attestation, certified copy certification

3. **Batch render strategically** — don't render all 53 pages. Render first 2, middle 5-10 (adjust based on total page count), last 3-5. If key info still missing, render additional ranges.

4. **Vision analyze each image** — ask specific questions:
   - Page 1: "Document title, registration number, date, parties (seller/s and buyer/s), recitals"
   - Schedule page: "Property schedule — survey number(s), village, boundaries (N/S/E/W), extent"
   - Consideration page: "Sale consideration amount, payment breakdown (cheque/DD details)"
   - Covenants page: "List all vendor covenants and representations"
   - Witness page: "Witness names, signatures, notary details, thumb impressions"

5. **Cross-reference** — The same property often appears in a related Confirmation Deed. Cross-check parties, property schedule, and consideration across both.

## Confirmation / Ratification Deed Pattern

A Confirmation Deed commonly appears 1-3 days after the main Sale Deed to cure non-joinder of legal heirs. Key features:

- **Registration fee is nominal** (~₹500-₹1,000) — confirms it's a ratification, not a fresh transfer
- **Recital typically states:** "At the time of execution of Sale Deed, the L.Rs of [Original Owner] were not joined since the Purchaser was not aware of their whereabouts"
- **Effect:** The confirming parties ratify/confirm the sale, curing the non-joinder defect
- **Residual risk:** Implicitly confirms title search at original sale was incomplete. Recommend verifying ALL legal heirs via a proper family tree / legal heirship certificate.

## Delivering the Report as a Word (.docx) Document

When the user requests the report in Word format (common for formal legal submissions):

### python-docx Setup

```bash
# python-docx is available in the Hermes venv
/opt/hermes/.venv/bin/python -c "from docx import Document; print('ready')"
```

### Core Patterns

**1. Styled Headings with custom color:**
```python
from docx.shared import RGBColor

def add_heading_styled(text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
    return h
```

**2. Formatted tables with colored header row:**
```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cell_shading(cell, color):
    shading_elm = OxmlElement('w:shd')
    shading_elm.set(qn('w:fill'), color)
    shading_elm.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def add_header_row(table, headers):
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                run.font.size = Pt(10)
        set_cell_shading(cell, '1A1A2E')
```

**3. Two-column property table (key-value):**
```python
t = doc.add_table(rows=1, cols=2)
t.style = 'Light Grid Accent 1'
add_header_row(t, ['Field', 'Details'])
for k, v in [('Survey No.', '8/1'), ('Extent', '2 Acres 6 Guntas')]:
    row = t.add_row()
    row.cells[0].text = k
    row.cells[1].text = v
    # bold the first column
    for p in row.cells[0].paragraphs:
        for r in p.runs:
            r.bold = True
```

**4. Multi-section document structure:**

| Section | Content |
|---------|---------|
| Title Page | Document title, subtitle, date, disclaimer |
| 1. Executive Summary | Summary table, purchaser, property, consideration, opinion |
| 2. Chain of Title | Chronological table of title events |
| 3. Property Schedule | Survey/area/boundaries table |
| 4. Consideration | Payment breakdown table |
| 5. Encumbrances | Vendor covenants + missing documents list |
| 6. Statutory Compliance | Registration, land use, conversion |
| 7. Red Flags & Risks | Rated table of risks |
| 8. Key Covenants | Summary table |
| 9. Conclusion | Opinion + pending docs table |

**5. Write the script to `/tmp/` and execute:**
```python
write_file('/tmp/create_dd_report.py', script_content)
terminal('HERMES_HOME=/data/hermes /opt/hermes/.venv/bin/python /tmp/create_dd_report.py')
```

**6. Deliver via MEDIA:**
```python
# In response, include:
# MEDIA:/tmp/Legal_Due_Diligence_Report_PropertyName.docx
```

### Table Styling Best Practices
- Use `'Light Grid Accent 1'` table style as base — it's professional and readable
- Override header shading with a dark color (`1A1A2E` for navy) for contrast
- Keep font at 10-11pt Calibri throughout
- Add page breaks between major sections (`doc.add_page_break()`)
- For yes/no/status columns, use emoji indicators: ✅, ⚠️, ❌, 🔴, 🟡

## Standard Pending Documents Checklist

Always include in every DD report conclusion:

| # | Required Document | Purpose |
|---|------------------|---------|
| 1 | Encumbrance Certificate (Form 15/16) — 30 years | Confirm no subsisting mortgages, liens, attachments |
| 2 | Khata Certificate / Extract | Verify khata standing (A/B/e-Khata) |
| 3 | RTC / Mutation Extract — current + 10 years | Verify revenue entries and mutation |
| 4 | Property Tax Paid Receipts — 5 years | Confirm taxes up-to-date |
| 5 | Legal Heirship Certificate / Family Tree | Confirm all LRs traced |
| 6 | Land Use Conversion Order (if developing) | Lawful change of use |
| 7 | Survey Sketch / Taluk Map | Verify physical boundaries |
