# Multi-Source Document Compilation Workflow

Use this when drafting a legal document (Agreement for Sale, Construction Agreement, or Combined) from an existing source deed AND multiple supporting reference materials.

## Workflow

### 1. Source Document = READ-ONLY
- Identify the source / template document (e.g. existing Sale Deed for a similar plot).
- **Never modify the source.** It is reference-only.
- If the user shares a link saying "I'm sharing you the link, do not make any changes" — honour that literally.

### 2. Reference Resource Audit
Before drafting, gather ALL supporting materials from Drive:
- **Plans & Layouts** — villa/building plans (PDF from architect), master layout plans
- **Data Sheets** — inventory spreadsheets with plot dimensions, boundaries, survey numbers
- **Specifications** — investment letters / construction specs (finishes, brands)
- **Legal Documents** — JDA, reconstitution deeds, partnership registration, PAN/CIN records
- **Regulatory** — RERA registration, building permits (if available, mark as pending if not)

Cross-check every party field across all sources:
- Name spelling consistency
- Address
- PAN / CIN
- Firm registration number
- Director / partner names and designations

### 3. Red Flag Logging
Maintain a running list of discrepancies found during cross-checking:
- Dual representation (same entity represented by different people in different sections)
- Missing registration numbers that are referenced but not obtained
- Scope ambiguity (e.g. ₹/sqft — does it cover plot only or plot + construction?)
- Present these clearly to the user for resolution

### 4. Incremental Drafting
- Fill one section at a time. Present to user for approval before moving to next.
- Leave these fields blank until user provides:
  - Allottee name & contact
  - Pricing & instalment schedule
  - TNRERA Registration Number
  - Building permit number
  - Completion timeline
- Use the source document's clause structure but adapt for the specific plot/project.

### 5. Formatting Standards
- **Use tables** for all schedules, annexures, specifications, and payment plans.
- Tables should have proper columns, headers, and alternating rows where applicable.
- Avoid long blocks of unstructured text for financial/commercial data.
- Create Docs via HTML-to-Doc import or Docs API batchUpdate with table elements.
- If generating .docx first, format tables in Word before uploading to Drive.

### 6. Document Organization
After all documents are drafted:
1. Create a dedicated Drive folder: `{ProjectName}_Plot{XX}_Legal_Set`
2. Move all final documents into this folder
3. Remove any older/duplicate versions
4. Create a **Resources Reference** document inside the same folder:

```
Resources Reference — {Project} Plot {XX} Legal Set
├── A. Source Sale Deed (link)
├── B. Villa Layout Plan (link)
├── C. Template Agreement (link)
├── D. Plot Data Sheet (link)
├── E. Construction Specs (link)
├── F. Partnership/Reconstitution Deed (link)
└── G. Joint Development Agreement (link)
```

5. Step-wise order inside folder:
   - Agreement for Sale (primary)
   - Construction Agreement (secondary)
   - Combined Agreement (if applicable)
   - Resources Reference (last)

### 7. Final Deliverable
- Share the folder link with the user
- Provide a summary of what was done, what's pending, and any red flags found
- Keep the original source document untouched

## Example: Ranka Oasis Plot 119
- Source: `Ranka_Oasis_Plot65_Sale_Deed_NishantPrakash` (Google Doc, read-only)
- Villa plan: `OASIS- EAST (9-14X15M) - 2 (1).pdf` (Ar. Anest Raj)
- Template: `Inara Phase 1 Villa 10 AOS.pdf`
- Plot data: `Oasis Master Inventory Sheet` (Google Sheets)
- Specs: `Letter-Investment-Details.docx`
- Legal: SLP Reconstitution Deed, JDA
- Folder: `Plot 119 Legal Set`
- Red flags flagged: DRA Realty dual representation, TNRERA not received, scope ambiguity
