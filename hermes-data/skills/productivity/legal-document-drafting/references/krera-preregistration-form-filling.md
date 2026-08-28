# KRERA Pre-Registration Form Filling (Ranka Amber workflow, June 2026)

Class of work: filling KRERA Form-2 (Architect's Certificate), Form-3 (Engineer's Certificate), Allotment Letter, and Agreement of Sale Proforma for project registration, using data from multiple source documents.

## Typical Data Sources

| Source | What it provides |
|--------|-----------------|
| Plan Sanction PDF (GBA/BECC/0540/25-26) | Project no, authority, approval date, building description (Block/Wing), units, FAR, built-up/carpet areas, height, parking, land area |
| Building Licence (BBMP/CC/4247/26-27) | Licence sl no, LP no, file no, fee details, labour cess, validity period |
| Area Statement XLSX | Per-unit built-up, RERA carpet, balcony, super BUA, share type (LO/DEV), entrance facing, toilets |
| Architect Area Statement PDF | Architect-certified per-unit areas (may need OCR) |
| DRA Amber Estimate / BOQ PDF | Total estimated cost with section-wise breakdown (substructure, superstructure, finishes, doors/windows, plumbing, electrical) |
| JDA / GPA (Drive) | Landowner names, promoter details (CIN, registered office, directors), JDA reg no/date, GPA ref |
| EC (Encumbrance Certificate) | Boundary descriptions, ownership chain, JDA registration entry |
| E-Khata | BBMP PID, khata no, property dimensions, classification, address |

## Form-3 (Engineer's Certificate) — Filling Pattern

Key fields from plan sanction:
- **Project Name**: from plan sanction title
- **Promoter Name**: from plan sanction (applicant section)
- **Sanctioned Drawing No.**: GBA/BECC/0540/25-26
- **Competent Authority**: Bengaluru East City Corporation
- **Building(s)/Wing(s)**: from plan sanction building description (e.g. "Block-A (RESIDENTIAL) Wing A-1")
- **Plot/Land Details**: Plot No, Katha No, PID from plan sanction
- **Village/Taluk/District/PIN**: from plan sanction address
- **Land Area**: from plan sanction area statement
- **Boundaries**: from EC document (North/South/East/West)
- **Estimated Cost**: from BOQ/Estimate PDF total

## Form-2 (Architect's Certificate) — Filling Pattern

Similar to Form-3 but:
- **Architect details** come from the architect separately (name, COA reg no, address, phone, email)
- **Estimated Cost** goes in the certification paragraph
- **Site Inspection Date** is a post-inspection field — leave as placeholder

## Allotment Letter — Filling Pattern

The KRERA model Form of Allotment Letter has placeholders for:
- **Allottee details** (name, address, PAN, Aadhar, email, phone) — per-unit, leave as placeholder
- **Project details** — fill from plan sanction
- **Unit details** — per-unit (BHK type, unit no, carpet area, floor, tower/block/wing)
- **Land/survey details** — from plan sanction + EC
- **Total consideration** — per-unit, leave as placeholder
- **Booking amount** — per-unit, ≤10% of consideration
- **Boundaries** — from EC
- **Stage-wise completion schedule (Annexure A)** — from project schedule

## Agreement of Sale Proforma — Filling Pattern

- **Promoter section** (company): CIN, registered office, PAN, director name — from JDA / company docs
- **Land section**: Owner names, survey/plot details, JDA/GPA refs — from JDA, GPA, EC docs
- **Project description**: Building count, unit count, project name — from plan sanction
- **Approvals**: Competent authority, sanction no, date — from plan sanction
- **RERA registration**: Number assigned by authority — leave as placeholder
- **Schedule A (Apartment description)**: Unit inventory table — from area statement
- **Schedule D & E (Specifications)**: From architect/area statement specifications sheet
- **Schedule F (Boundaries)**: From EC document
- **Schedule G (Common Areas)**: From area statement common area sheet
- **Schedules with per-unit data**: Leave placeholders for allottee-specific values

## Pitfalls & Techniques

### 1. DOCX multi-run underscore replacement

KRERA forms store placeholder text across multiple runs. Naively replacing `___` in every run causes text duplication. Use `fill_single_run()` pattern:

```python
def fill_single_run(para, fill_text):
    """Replace underscores in first run that has them, clear remaining runs."""
    found = False
    for run in para.runs:
        if not found and '_' in run.text:
            t = run.text
            for n in range(30, 1, -1):
                t = t.replace('_' * n, fill_text)
            run.text = t
            found = True
        elif found:
            run.text = ''
```

### 2. Inspect run structure BEFORE editing

Some paragraphs split "Rs." across runs: Run1="Rs", Run2=".", Run3=" " , Run4="_", Run5="______", Run6="." — replacing just the underscore leaves the surrounding fragments. Always print `[repr(r.text) for r in para.runs]` before coding replacements.

### 3. Build subject lines as full text, not run-by-run

For long paragraphs (P14 in Form-3, P13 in Form-2, the subject/whereas clauses in Allotment Letter), clear all runs and set the first run to the complete assembled text. Preserve formatting on the first run.

### 4. SIS spreadsheet: row numbering gap

The SIS 5.2 template has empty rows between label rows. `iter_rows()` yields ALL rows including blanks. The display numbering (Row 1, Row 2…) when printed with `if any(v[0] is not None)` skips empty rows, causing misalignment. Always verify actual row numbers with:
```python
for r in range(1, 50):
    a = ws.cell(row=r, column=1).value
    b = ws.cell(row=r, column=2).value
    if any(x is not None for x in [a, b]):
        print(f"Row {r}: A={a} B={b}")
```

### 5. Merged cells in SIS xlsx

B5:B7 and C5:C7 are merged in the SIS template. Writing to C6 or C7 raises `AttributeError: 'MergedCell' object attribute 'value' is read-only`. Unmerge before writing individual values:
```python
ws.unmerge_cells('C5:C7')
```
Always check `ws.merged_cells.ranges` before writing.

### 6. Global Drive token for non-authorized users

When the current user (e.g. Prakash, TG psingh) has no GWS OAuth token, use the global Drive-only token:
```python
from google.oauth2.credentials import Credentials
creds = Credentials.from_authorized_user_file("/data/hermes/google_token.json")
drive = build("drive", "v3", credentials=creds)
```
This token has **Drive scope only** — no Gmail, Calendar, Sheets access.

### 7. Drive query single-quote escaping

When building Drive `q=` parameters from Python, single quotes inside the query string must be constructed with `chr(39)` to survive shell heredoc quoting:
```python
q = "'" + folder_id + "' in parents and trashed=false"
```

### 8. pdfminer / pdftotext vs fitz for BOQ/Estimate PDFs

BOQ/estimate PDFs often have tabular layouts that `fitz` (pymupdf) can't extract well — text columns are jumbled. Prefer `pdftotext` (terminal tool) for these layout-heavy documents.

---

## Documents Created in This Session

| Document | Source data |
|----------|-------------|
| SIS_5.2_Company-Apartment_details_Ranka_Amber.xlsx | Plan sanction (areas, FAR) + Area Statement (per-unit carpet, built-up, share type) |
| Form-3_Engineer_Ranka_Amber.docx | Plan sanction + BOQ estimate (₹5,69,75,601) |
| Form-2_Architect_Ranka_Amber.docx | Same data + pre-filled architect details (Ar. Bhuvanesh Krishnan) |
| AllotmentLetter_Ranka_Amber.docx | Plan sanction + JDA/GPA/EC (boundaries, land details) |
| Agreement_Sale_Ranka_Amber.docx | All above sources |
