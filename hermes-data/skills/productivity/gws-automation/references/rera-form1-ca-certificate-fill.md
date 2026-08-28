# RERA Form-1 CA Registration Certificate — Fill from Source Documents

Pattern for filling a KRERA Form-1 (Chartered Accountant's Certificate for Registration) template from data extracted across multiple project documents on Drive.

## When to use

The user provides a link to a .docx template (Form-1 CA) and asks to fill it with data from other documents on their Drive — typically during RERA registration for a Bangalore/Karnataka real estate project.

## Source documents to look for

| Data needed | Where to find it |
|---|---|
| Project Name, Address, Type | Project Details Letter/PDF — "Project Details of 'X'" letter to KRERA |
| Promoter Name, CIN, PAN, GST | Org Structure doc, PAN card PDF, GST certificate PDF, Board Resolution |
| Date of Incorporation | PAN card or Certificate of Incorporation PDF |
| Directors / Partners | Org Structure table, Board Resolution, GST Annexure B |
| Total Land Area / Built-up / Carpet | Project Details letter, Area Statement |
| Land Cost | Land Cost Letter — "Total Cost of Project Land" |
| Construction Cost break-up | Cost Abstract (Engineer Form-3), Construction Cost Abstract docx |
| Means of Finance | Means of Finance / Source of Funds letter |
| Project Start/End Dates | Project Details letter |
| JDA / GPA details (registration numbers, dates) | Land Cost Letter or Board Resolution |

## Promoter entity types and their Table 1 data

**Private Limited Company (most common for DRAAS projects):**
- Row 1: CIN + PAN
- Row 2: Date of Incorporation (from PAN card or COI)
- Row 3: GSTIN — check if GST cert is for same entity name
- Row 4: "Not Applicable (Private Limited Company - not an LLP)"
- Row 5: List of Directors from Org Structure or Board Resolution
- Row 6-7: Assets & Net Worth — "Rs. [Refer latest audited Balance Sheet]" if not available

**Partnership Firm** (e.g., DRA Ranka Holdings, DRA KAAJ):
- Row 1: Partnership Registration Number + PAN
- Row 2: Date of Deed / Date of Registration
- Row 3: GST Registration Number
- Row 4: List of Partners
- Row 5: N/A (Directors don't apply to partnerships)
- Row 6-7: Same — use latest Balance Sheet

## Table 2 — Estimated Cost mapping

Four rows:
1. **Land of the Project** — from Land Cost Letter. Amount + remark citing JDA registration number.
2. **Approvals & NOCs** — estimate Rs. 10-15 L for plan approvals + BWSSB + BESCOM + Fire + Pollution Control. Remark: "Promoter to calculate based on sanctioned plan."
3. **Construction Cost** — from Engineer's Cost Abstract / Form-3. Amount + remark citing Form-3 date and basis (sanctioned plan, BOQ, current market rates).
4. **TOTAL** — sum of 1+2+3. Write in words.

## Bank account details

Sections for 100% (Collection), 70% (Designated), and 30% (Current) accounts are often blank in the template. Check:
- Bank statement PDFs in the scanned docs folder
- Means of Finance / Source of Funds PDF
- If not found: leave blank and flag to user

## Paragraph-level text fixes to check

Templates often have placeholder dashes split across multiple runs:
- `'-------------` (13 dashes) → should become promoter name
- `'-------'` (7 dashes) → should become project name
- `"plotted development / group housing / villa project / commercial"` → should become the actual project type (e.g., "Residential Apartment Project (Group Housing)")

These dashes are separate runs in the XML, so run-based detection (`if run.text == '-------------': run.text = '...'`) is more reliable than paragraph-level string replacement.

## Upload strategy

Since the form is a .docx (not a native Google Doc), you must:
1. Download via Drive API `files().get_media()`
2. Modify with python-docx
3. Upload as a **new file** with updated name prefix (e.g., `20260624_ProjectName_Form1_CA_Filled.docx`) — do NOT overwrite the original template
4. Use `files().create()` with the same folder as parent

## Pitfalls

1. **Scanned PDFs yield no text** — Cost Abstract, Project Details, and Source of Funds PDFs are often scanned images. Use the docx versions instead (e.g., `20260608 Ranka Amber Construction Cost Abstract.docx` not the scanned PDF).
2. **GST may be under a different entity** — The project may be developed by a company (DRA Realty Pvt Ltd) but the GST certificate may belong to a partnership (DRA Ranka Holdings). Verify the entity name matches before filling.
3. **Land cost vs total project cost** — The Means of Finance letter may state the total project cost *excluding* land (if the land is under JDA). The Form-1 Table 2 expects land cost separately. Sum land + approvals + construction for the total.
4. **Table column alignment** — `python-docx` table cell indices are 0-based. Map carefully: Col 0 = Sl No, Col 1 = Estimated Cost of, Col 2 = Amount in INR, Col 3 = Remarks. Writing to the wrong column overwrites the column header text.
5. **Venv needed** — Use `/opt/data/gdrive-env/bin/python3` or `/opt/hermes/.venv/bin/python` for both `googleapiclient` and `python-docx`. System python has neither.
6. **CA details stay blank** — Unless the user explicitly provides CA name/membership/UDIN, leave those fields blank. The user may forward the partially-filled form to their CA.
