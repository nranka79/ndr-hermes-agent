# RERA Document Preparation Pipeline

When the user asks to "prepare documents for RERA approval" or "fill the RERA forms for project X", this is the standard sequence:

## Pipeline Overview

```
Plan Sanction PDF (GBA/BECC/XXXX/XX-XX)
    → Building Licence PDF (BBMP/CC/XXXX/XX-XX)
    → Area Statement (XLSX or PDF from architect)
    → BOQ/Estimate PDF
    ↓
SIS Spreadsheet (unit inventory + FAR + plan details)
Form-3 Engineer Certificate (estimated cost)
Allotment Letter (proforma per allottee)
Agreement of Sale (proforma with schedules)
```

## Step 1 — Extract Source Data

### Plan Sanction (the primary source)
Extract from the PDF with `pdftotext` or pymupdf. Key fields to capture:

| Field | Where in plan sanction |
|---|---|
| Project No | `GBA/BECC/XXXX/XX-XX` format — in AREA STATEMENT section |
| Authority | Bengaluru East City Corporation / BECC / BBMP |
| Approving Officer | Deputy Director Town Planning (DDTP), digitally signed |
| Approval Date | From digital signature date |
| Applicant/Promoter | `M/S DRA REALTY PRIVATE LIMITED represented by its Director Mr. Nishant Ranka` |
| Owner/GPA Holder | Listed near bottom of first text page |
| Property Address | Plot No, Katha No, PID, Village, Hobli, Taluk — in footer area |
| Block Details | Block name, Wing, Stilt+GF+nUF, tenements count |
| Plot Area | In sq.mt. under AREA DETAILS |
| Built-up Area | Total BUA (sq.mt.) under FAR & Tenement Details |
| Carpet Area | Total carpet area (sq.mt.) |
| Coverage % | Permissible vs proposed |
| FAR | Permissible vs achieved |
| Parking | Car, two-wheeler counts |
| Height | In metres |
| Boundaries | In EC document (not typically in plan sanction text) |
| Building Licence | LP No (BBMP/CC format) and File No (GBA/MDP/DDTP format) |

### Area Statement (XLSX from architect)
Contains per-unit execution areas. Key columns (standard layout):

| Column | Content |
|---|---|
| Unit # | 101, 102...(first digit = floor, last 2 = unit index within floor) |
| Share | LO (Land Owner) / DEV (Developer) |
| Configuration | e.g. "3 BHK Double Balcony" |
| Floor | First/Second/Third/Fourth |
| Entrance Facing | North/East/West |
| Unit Built-up Area | In sq.ft. |
| Execution Balcony Area | In sq.ft. |
| RERA Carpet Area | In sq.ft. (this goes into the SIS Arera details) |
| Super Built Up Area | = Built-up + balcony + common share |

**Floor naming convention:** The Area Statement typically uses First/Second/Third/Fourth Floor, while the plan sanction uses GF/FF/SF/TF (Ground through Third). Map them: First=GF, Second=FF, Third=SF, Fourth=TF.

### BOQ / Estimate PDF
Contains the total estimated project cost needed for Form-3. Extract with `pdftotext` and grep for "TOTAL COST OF PROJECT". Value is typically in Rs. Crores.

### Building Licence PDF
Contains the LP No (`BBMP/CC/XXXX/XX-XX`) and file reference (`GBA/MDP/DDTP/XXXX/XX-XX`). Both refer to the same sanction — do NOT flag as discrepancy.

### Encumbrance Certificate (EC)
Contains verified boundaries, ownership history, and encumbrances. Key for Schedule F in Agreement of Sale.

### JDA / GPA / Addendum
Registered documents between landowners and developer. Key for WHEREAS clauses in Agreement of Sale.

## Critical Data Source Rules (Corrected June 2026)

**⚠️ Property boundaries come from EC/JDA, NOT from plan sanction conditions.**
The plan sanction's conditions section sometimes lists generic road/property references that are NOT the actual plot boundaries. Always extract true boundaries from the Encumbrance Certificate (EC):

| Source | When to use |
|--------|-------------|
| **EC / JDA** | ✅ Boundary schedule for Schedule F and all property descriptions |
| **Plan Sanction Conditions** | ❌ These describe neighbouring context, not the plot's legal boundaries |
| **E-Khata** | ✅ Cross-reference — boundry details here match EC |

**⚠️ LAT/LONG must be geocoded from actual project address.**
Do NOT copy lat/long from template data or previous projects. Geocode the project's full address using Nominatim:
```bash
curl -s "https://nominatim.openstreetmap.org/search?q=FULL+ADDRESS&format=json&limit=1"
```
Then convert decimal degrees to DMS format (degrees°minutes'seconds").
*Pre-verified June 2026: Pattandur Agrahara, Whitefield → 12°59'15.5"N, 77°44'16.0"E*

**⚠️ Project dates come from the construction schedule (Schedules sheet), not guessed.**
The Schedules sheet has a row-by-row construction timeline with earliest start and latest end dates. Extract:
```python
from datetime import datetime
for r in range(7, max_row):
    e = ws.cell(row=r, column=5).value  # Start
    f = ws.cell(row=r, column=6).value  # End
    if isinstance(e, datetime) and (not earliest or e < earliest): earliest = e
    if isinstance(f, datetime) and (not latest or f > latest): latest = f
```

**⚠️ Only fill PROJECT-SPECIFIC data, never per-allottee placeholders.**
Per-allottee fields (name, PAN, unit no, price, booking amount, payment terms) must be left BLANK — not filled with "[to be filled per allottee]" or any other placeholder. Template alternative options (Partnership/Individual/HUF promoter sections) should also be left as-is, not marked "[N/A]".

✅ Fill these project-level fields only:
- Project name, address, description
- Promoter name, CIN, registered office, director
- Landowner details and JDA/GPA references
- Approval numbers (plan sanction, building licence)
- Building specifications (units, floors, parking, height, FAR)
- Boundaries, lat/long
- Project dates (start/end)
- Estimated cost (Form-2/3 only)

❌ Leave these BLANK (per-allottee):
- Allottee name, PAN, Aadhar, contact
- Unit number, carpet area per allottee
- Total consideration, booking amount
- Possession date (exact)
- Payment plan, default periods

## Step 2 — Fill SIS Spreadsheet

The SIS (`SIS_5.2_Company-Apartment details.xlsx`) has 5 sheets:

| Sheet | What to fill |
|---|---|
| **Project details** | Name, description, type (Residential/Apartment), status (New), address with PIN |
| **Plan details** | Authority, plan no, approval date, total units, parking counts, all area values (land, built-up, carpet, coverage) in sq.mt. |
| **Arera details** | One row per unit — unit no (from Area Statement), type (2BHK/3BHK), share+facing notes, RERA carpet area (sq.ft.) |
| **Schedules** | Pre-filled construction timeline — leave as-is unless user provides updated dates |
| **FAR Details** | Tower count, FAR value, tower name, type, floor count, units, basements/stilts, parking, height, floor-wise unit distribution |

**Row mapping trap:** The Project details sheet has empty rows (2-3 are blank). Verify exact row numbers with `ws.cell(row=r, column=2).value` before writing.

**Merged cell trap:** Some sheets merge C5:C7 or B5:B7. Unmerge before writing individual values:
```python
ws.unmerge_cells('C5:C7')
```

**Area unit trap:** Plan sanction is in sq.mt., Area Statement is in sq.ft. Keep both — the SIS Plan details expects sq.mt., Arera details expects sq.ft.

## Step 3 — Fill Form-3 Engineer Certificate

This is KRERA Form-3 under Section 4(2)(l)(D) of RERA Act. Template is a DOCX with placeholder underscores.

Key paragraphs to fill:
- P6: Date (today's date)
- P8: Project Name
- P9: Promoter Name
- P12: Name & Address of Promoter
- P14: Subject line — rebuild entirely with project data
- P19: Sanctioned Drawing No.
- P21: I/We paragraph — rebuild with same project data
- P23: Total Estimated Cost — from BOQ PDF

**Run splitting trap:** The Form-3 DOCX splits text across many runs. Replace carefully:
```python
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

**Cost paragraph trap (P23):** "Rs." is split across 3 runs. Concatenate all runs into the first, clear the rest.

## Step 4 — Fill Allotment Letter

KRERA Model Form of Allotment Letter (Annexure-1). Common fields from project data:
- Project name, address, RERA registration no (blank if not yet assigned)
- Unit type (BHK), floor, block/tower, wing
- Land survey/plot details
- Boundaries (from EC)
- Stage-wise completion schedule (Annexure A)

**Per-unit fields left blank:** Allottee name, PAN/Aadhar, specific unit number, carpet area, total consideration, booking amount, engineer details.

## Step 5 — Fill Agreement of Sale Proforma

KRERA Model Agreement of Sale. Focus on project-level fields:

- **Promoter section:** Fill company section (CIN, registered office, PAN, director) — clear individual promoter template data
- **WHEREAS clauses:** Land details from EC, JDA registration details, GPA details
- **P123:** Building count, project name, type
- **P140:** Competent authority, sanction date, sanction number
- **P144:** Sanctioned plan authority name
- **Schedule F:** Property description with boundaries from EC
- **Schedule G:** Common area details from architect

## Step 8 — Comprehensive 12-Document RERA Compliance Set

Beyond the core 5 documents (SIS, Form-2, Form-3, Allotment Letter, Agreement of Sale), KRERA applications require additional supporting documents. Generate all 12 as a single batch when the user says "prepare all RERA documents" or sends a RERA checklist.

### 1. Work Order

Standard format on company letterhead:

| Field | Content |
|-------|---------|
| **Title** | WORK ORDER |
| **To** | Name of vendor/contractor |
| **Project** | Ranka Amber, Plot 1-B, Pattandur Agrahara, K.R. Puram |
| **Scope** | Construction of Block A — Stilt+GF+3UF (20 units) |
| **Contract Value** | ₹5,69,75,601 |
| **Completion Period** | 18 months from date of possession of site |
| **Terms** | 8 standard clauses: scope, time, payment, quality, safety, variations, termination, governing law |
| **Signatures** | For DRA Realty (Authorized Signatory) + Contractor acceptance |

File: `YYYYMMDD Ranka Amber Work Order.docx`

### 2. Project Photos with GPS Location

**Not a document — an on-site requirement.** Provide instructions:
> Please take geo-tagged photos of the project using the **GPS Map Camera** app. Include:
> - Site overview from all 4 directions
> - Foundation / current construction stage
> - Nearby landmarks (road, junction)
> - Borewell location (if applicable)
> Photos should show: date, time, latitude, longitude embedded in the image.

Share soft copies via Telegram or Drive.

### 3. Project Details Letter (with Dates)

Company letterhead format with:

| Field | Content |
|-------|---------|
| **Project Name** | Ranka Amber (as per sanctioned plan) |
| **Project Address** | Plot 1-B, Katha 4/124, D'Silva Layout, Pattandur Agrahara, K.R. Puram, Bengaluru - 560036 |
| **Sanction No.** | GBA/BECC/0540/25-26 dated 18-05-2026 |
| **Start Date** | 10-06-2026 (from schedule) |
| **End Date** | Accounts for: construction + OC procurement + 100% development works. Typically start date + 24-30 months. |
| **Blocks** | 1 building (Block A, Wing A-1) |
| **Total Units** | 20 (Stilt+GF+3UF) |
| **Total Parking** | 22 |

File: `YYYYMMDD Ranka Amber Project Details Letter.docx`

### 4. Project Specifications Letter

List 16+ specification items on company letterhead, attested with seal and signature:

| # | Specification | Typical Brand/Type |
|---|--------------|-------------------|
| 1 | Structure | RCC framed structure — IS 456:2000 |
| 2 | Walls | Solid concrete blocks / red bricks |
| 3 | Flooring | Vitrified tiles 600x600 (living/bed) + anti-skid (balcony/bath) |
| 4 | Kitchen | Granite platform + SS sink + tile dado |
| 5 | Bathrooms | Anti-skid flooring, tile dado up to 7ft, CP fittings (Jaguar/ESS ESS) |
| 6 | Windows | UPVC / Powder-coated aluminum with MS grills |
| 7 | Doors | Flush doors with laminate finish + SS hardware |
| 8 | Painting | Interior: plastic emulsion. Exterior: weather-proof acrylic |
| 9 | Electrical | ISI modular switches (Anchor/Roma), copper wiring |
| 10 | Plumbing | CPVC / UPVC pipes (Astral/Finolex/Prince) |
| 11 | Lift | 6-passenger OTIS/KONE/Schindler |
| 12 | DG Set | Standby generator for common areas |
| 13 | Solar | Solar water heater for each unit |
| 14 | Rainwater Harvesting | Per BBMP norms |
| 15 | STP | Sewage Treatment Plant — as per KSPCB norms |
| 16 | Security | CCTV cameras at entry/lobby/lift, intercom |

File: `YYYYMMDD Ranka Amber Project Specifications.docx`

### 5. Source of Water Supply Letter

Company letterhead describing:

- **Primary source:** BWSSB / Bangalore Water Supply (specify line connection details)
- **Secondary source:** Borewell (depth, yield, location)
- **Tank capacity:** Overhead + underground tank sizes (Litres)
- **Treatment:** If STP or water treatment plant installed
- **⚠️ GPS photos required:** Photo of borewell with GPS coordinates embedded (use GPS Map Camera app)

If borewell is a water source, attach the **yield test report** from a licensed hydrogeologist.

File: `YYYYMMDD Ranka Amber Water Supply Letter.docx`

### 6. Cash Flow Statement (3-Year)

Company letterhead showing actual/estimated cash flows:

| Item | FY 2023-24 | FY 2024-25 | FY 2025-26 |
|------|-----------|-----------|-----------|
| **Opening Balance** | [₹___] | [₹___] | [₹___] |
| **Receipts** | | | |
| Share Capital / Loans | [₹___] | [₹___] | [₹___] |
| Customer Advances | [₹___] | [₹___] | [₹___] |
| Other Income | [₹___] | [₹___] | [₹___] |
| **Total Receipts** | [₹___] | [₹___] | [₹___] |
| **Payments** | | | |
| Land & Development | [₹___] | [₹___] | [₹___] |
| Construction | [₹___] | [₹___] | [₹___] |
| Administrative | [₹___] | [₹___] | [₹___] |
| Finance Costs | [₹___] | [₹___] | [₹___] |
| **Total Payments** | [₹___] | [₹___] | [₹___] |
| **Closing Balance** | [₹___] | [₹___] | [₹___] |

File: `YYYYMMDD Ranka Amber Cash Flow Statement.docx`

### Populating Cash Flow Statement from Audited Financials

**⚠️ Do NOT leave as `[___]` when audited financials ARE available on Drive.** The pipeline below extracts actual figures from CA-signed financial PDFs.

**Where to find financial documents on DRAAS Drive:**

1. **ZIP files** are the most common container. Search Drive with:
   `fullText contains 'DRA Realty Pvt Ltd' and (name contains 'zip' or name contains 'signed' or name contains 'financial') and trashed = false`
2. **Specific folders to check:** Look for "Audited Financials" folders, `Financials/` subdirectories
3. **Inside ZIPs:** Expect nested ZIP structures — extract recursively. Look for files named:
   - `DRA REALTY Private Limited_Financials_[FY]_signed.pdf`
   - `DRA Realty Financials F.Yr.[FY] A.Yr.[AY].pdf`
   - `DRA Realty Audit Report F.Yr.[FY].pdf`
   - `signedfinancialsfordrarealty[FY].zip` (nested ZIP)

**Text extraction: Indian CA financial PDFs have mixed text layers:**

| Type | Text Layer | Method | Example |
|------|-----------|--------|---------|
| CA-signed financials (older) | Usually yes | `fitz.open(path).get_text()` first | FY 22-23 worked instantly |
| CA-scanned financials (recent) | Often no text | `pdftoppm -png -r 200` + `tesseract` | FY 23-24 needed OCR |
| Audit reports only | Yes | `fitz` — always has text layer | Both FYs worked |

**Rule:** Always try `fitz` first (fast path). If empty, use `pdftoppm` + `tesseract`. The CA's PDF may use embedded fonts that fitz can't read.

**Extracting key figures from Balance Sheet (₹ in Thousands) & P&L:**

Parse these from the OCR'd / extracted text. Standard Indian CA financials layout:

- **Balance Sheet columns:** `Note No. | 31.03.[Year] | 31.03.[Prev Year]`
- **P&L columns:** Same format
- **Notes section:** Detailed breakdown per note number referenced in BS/P&L

Key fields to extract:
```python
# From P&L: Revenue, Other Income, Employee Expenses, Other Expenses, PBT, Tax, PAT
# From BS: Share Capital, Reserves, Borrowings, Provisions, Investments, Cash, Loans/Advances
# From Notes: Depreciation (check DTL schedule), Director loan details (Note 3)
```

**Cash Flow Statement compilation (indirect method):**

```python
# All figures in ₹ thousands. Convert to Indian format (lakhs/crores) for display.

# Step 1: Operating profit before WC changes
op_before_wc = pbt + depreciation

# Step 2: Working capital changes
# Increase in CA (excl cash) = OUTFLOW (negative)
# Increase in CL (excl borrowings) = INFLOW (positive)
ca_current = loans_adv_current + other_ca_current
ca_previous = loans_adv_previous + other_ca_previous
cl_current = provisions_current
cl_previous = provisions_previous

wc_change = -(ca_current - ca_previous) + (cl_current - cl_previous)
net_op_cf = op_before_wc + wc_change

# Step 3: Investing
# FA purchase (new fixed assets) + net investment change
# If P&L has "Profit on Sale of Shares" in Other Income:
#   That profit was booked in P&L -> reverse it from op CF
#   Actual sale proceeds = cost of shares sold + profit -> add to investing CF
inv_cf = -(fa_purchase) - (investments_current - investments_previous)

# Step 4: Financing
fin_cf = -(borrowings_current - borrowings_previous)  # negative = repayment

# Verify: Net CF should equal cash balance change
cash_change = cash_current - cash_previous
net_cf = net_op_cf + inv_cf + fin_cf
```

**Indian number formatting for display:**

```python
def fmt_indian(v):
    """Format thousands to Indian number string (in rupees).
    E.g. 106977 -> '10,69,77,000'"""
    if v == 0: return "-"
    sign = ""
    if v < 0: sign = "("; v = -v
    s = str(v * 1000)
    if len(s) <= 3: result = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while rest:
            groups.append(rest[-2:])
            rest = rest[:-2]
        groups.reverse()
        result = ",".join(groups) + "," + last3
    return sign + result + (")" if sign else "")
```

**Verification check:** Net Cash Flow MUST reconcile with cash balance movement:
```python
diff = abs(net_cf - cash_change)
# If diff > 0, add "Rounding / Net Effect" line to balance
```

**FY 2024-25 gap handling:** If audited financials for FY ended March 2025 are unavailable:
1. Check for: `DRA Realty Kotak Bank FY24-25 Transactions` (bank statement sheet on Drive)
2. If no financials found, mark column as `[___]` with note: *"FY 2024-25 figures to be updated upon completion of audit"*
3. Do NOT fabricate or estimate financial figures

### 7. Director's Report (3-Year)

Follows Section 134 of Companies Act, 2013. 10 standard sections on company letterhead:

1. **Company Overview** — CIN, incorporation date, registered office
2. **Financial Performance** — Revenue, profit/loss summary per FY
3. **Operations & Business** — Real estate development activities
4. **Directors & KMP** — Current Board composition
5. **Meetings** — Board meeting frequency, attendance
6. **Declaration** — No disqualification of directors
7. **Auditors** — Current auditor details
8. **Compliance** — ROC, GST, Income Tax status
9. **Internal Controls** — Adequacy statement
10. **Acknowledgments** — Thanks to stakeholders

Signed by Managing Director with Board's approval.

File: `YYYYMMDD Ranka Amber Directors Report.docx`

### 8. Means of Finance / Source of Funds Letter

Company letterhead detailing how the project will be funded:

| Source | Amount (₹) |
|--------|-----------|
| **Equity / Own Funds** | [₹___] |
| **Customer Advances** | [₹___] (estimated from booking) |
| **Project Finance / Loan** | [₹___] (if applicable) |
| **Total** | [₹___] |

> **If project finance has been obtained:** Attach the sanction letter / term sheet from the lending institution (Bank / NBFC / HFC).
> 
> **If self-funded:** Provide a declaration that the company has sufficient internal accruals to complete the project.

File: `YYYYMMDD Ranka Amber Means of Finance Letter.docx`

### 9. Total Cost of Project Land Letter

Attested by Promoter (authorized signatory). On company letterhead:

| Particulars | Amount (₹) |
|------------|-----------|
| **Land Value (as per JDA)** | Refer to JDA consideration clause |
| **Stamp Duty & Registration** | As per registration documents |
| **Legal & Other Charges** | Approximate |
| **Total Land Cost** | [₹___] |

**Source:** The land value derives from the Joint Development Agreement (JDA) — the agreed consideration per sq.ft. of built-up area or the lump sum payable to the landowner(s). This may be paid in kind (built-up area) or in cash.

File: `YYYYMMDD Ranka Amber Land Cost Letter.docx`

### 10. Construction Cost Abstract (Engineer-Certified)

Certified by a licensed Engineer (with registration/license number). On company letterhead:

| # | Component | Amount (₹) |
|---|-----------|-----------|
| 1 | Civil Works (structure, brickwork, plastering) | [₹___] |
| 2 | Finishing (flooring, painting, tiles, doors, windows) | [₹___] |
| 3 | MEP (electrical, plumbing, fire-fighting, lifts) | [₹___] |
| 4 | External Development (road, drainage, landscaping) | [₹___] |
| 5 | Amenities (clubhouse, gym, DG, STP, solar) | [₹___] |
| 6 | Contingencies & Supervision | [₹___] |
| | **Total Estimated Cost of Construction** | **₹5,69,75,601** |

Certification line:
> "I/We hereby certify that the above estimated cost of construction is true and correct to the best of my/our knowledge and belief."
>
> **Engineer's Name:** [Name, License No.]
> **Signature:** __________ **Date:** __________

File: `YYYYMMDD Ranka Amber Construction Cost Abstract.docx`

### 11. Common Areas & Amenities (Architect-Certified)

Certified by a licensed Architect (with COA registration). On company letterhead:

**Common Areas:**

| Area | Description | Area (sq.ft.) |
|------|-------------|--------------|
| Staircase | Common staircase with MS handrails | As per plan |
| Lift Lobby | Lift waiting area each floor | As per plan |
| Corridors | Passageways | As per plan |
| Service Area | Utility/common service spaces | As per plan |
| Terrace | Rooftop access | As per plan |

**Amenities:**

| Amenity | Status | Specification |
|---------|--------|-------------|
| Lift | ✓ | 6-passenger |
| DG Backup | ✓ | Common area |
| Rainwater Harvesting | ✓ | As per BBMP |
| STP | ✓ | As per KSPCB |
| Solar Water Heater | ✓ | Per unit |
| CCTV | ✓ | Common area |
| Intercom | ✓ | Security lobby |
| Visitor Parking | ✓ | Designated |

Certification line:
> "I/We hereby certify that the Common Areas and Amenities as above have been measured from the sanctioned plan and are true and correct."
>
> **Architect's Name:** [Name, COA Reg. No.]
> **Signature:** __________ **Date:** __________

File: `YYYYMMDD Ranka Amber Common Areas Certified.docx`

### 12. Area Statement (Architect-Certified)

Certified by Architect. Lists every unit with:

| Unit | Floor | Configuration | Carpet Area (sq.ft.) | Balcony | Exclusive Common | Total | UDS (sq.ft.) |
|------|-------|--------------|---------------------|---------|-----------------|-------|-------------|
| 101 | GF | 3BHK | [from architect] | [from architect] | [from architect] | [carpet+balcony+excl] | [carpet/total_carpet × land_area] |
| 102 | GF | 2BHK | ... | ... | ... | ... | ... |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Data source:** Architect's Area Statement XLSX. RERA Carpet column provides the carpet area values.

**UDS calculation:** `UDS = (Carpet Area of Unit ÷ Total Carpet Area) × Total Land Area`

Certification by Architect (COA Reg. No.) with signature and date.

File: `YYYYMMDD Ranka Amber Area Statement Certified.docx`

### Letterhead Requirement

Documents marked "on company letterhead" (all except #2 and #12 which is certified) must include:

| Element | Content |
|---------|---------|
| Logo | DRA Realty logo (top-left) |
| Company Name | DRA REALTY PRIVATE LIMITED |
| Address | Corporate Office with phone, email |
| GST/CIN | GST: 29AALCD9962L1ZW | CIN: U45209KA2014PTC074068 |
| Separator | Navy blue horizontal line |
| Footer | Company name | RERA status | Disclaimer |

See `references/docx-letterhead-logo-embedding.md` for embedding the logo into DOCX headers using python-docx.

### Batch Generation Order

Generate documents in this dependency order:

1. Work Order (#1) — no dependencies
2. Project Details Letter (#3) — needs start/end dates
3. Project Specifications (#4) — needs amenity/spec list
4. Water Supply Letter (#5) — needs borewell details
5. Cash Flow Statement (#6) — needs financial data from user
6. Director's Report (#7) — needs director details
7. Means of Finance (#8) — needs funding sources
8. Land Cost (#9) — needs JDA consideration value
9. Construction Cost Abstract (#10) — needs estimate + engineer details
10. Common Areas Certified (#11) — needs architect details
11. Area Statement Certified (#12) — needs unit area data + architect
12. GPS Photos (#2) — on-site only

## Common Pitfalls

1. **Floor level naming mismatch:** Area Statement = First/Second/Third/Fourth. Plan sanit = GF/FF/SF/TF. SIS expects GF/FF/SF/TF.
2. **Row gaps in SIS Project details:** Rows 2-3 empty. First data row = 4.
3. **Merged cells in templates:** SIS C5:C7 merged. Unmerge before writing.
4. **DOCX & in heredoc:** Python strings with `&` cause shell backgrounding errors. Write scripts to `/tmp` and execute via `terminal(command='python3 /tmp/script.py')`.
5. **Area units:** Plan sanction in sq.mt., Area Statement in sq.ft. Don't convert unnecessarily.
6. **Form-3 cost insertion:** "Rs. _____" split across 6+ runs. Collapse all into one.
7. **SIS Formula rows:** Column B has `=+B5+1` auto-increment formulas. Don't overwrite.
8. **Sheet names with trailing spaces:** openpyxl raises `KeyError` if the sheet name has a trailing space. Use `wb.sheetnames` with `repr()` to detect:
   ```python
   print([repr(s) for s in wb.sheetnames])  # reveals 'Specifications ' vs 'Specifications'
   ```
9. **openpyxl merged cell writes:** Writing to a cell that's part of a merged range (but not the top-left) raises `AttributeError: 'MergedCell' object attribute 'value' is read-only`. Always check `ws.merged_cells.ranges` and write only to the top-left cell of each merge:
   ```python
   merged_set = set()
   for mc in ws.merged_cells.ranges:
       for r in range(mc.min_row, mc.max_row+1):
           for c in range(mc.min_col, mc.max_col+1):
               merged_set.add((r, c))
   
   def safe_write(ws, row, col, value):
       if (row, col) in merged_set:
           for mc in ws.merged_cells.ranges:
               if mc.min_row <= row <= mc.max_row and mc.min_col <= col <= mc.max_col:
                   if row == mc.min_col and col == mc.min_col:
                       ws.cell(row=row, column=col, value=value)
                   return
       else:
           ws.cell(row=row, column=col, value=value)
   ```

## Step 6 — Highlight All Changes in Yellow

DRAAS users (Prakash specifically) expect all changed/filled fields to be highlighted in **yellow** so they can quickly identify what was updated. Apply this to both DOCX and XLSX files:

### KRERA Template Duplication Fix

KRERA model templates (Agreement of Sale, Allotment Letter) frequently have text duplicated 2–4 times in the same paragraph — a copy-paste artifact from the original Word source.

**Common patterns seen:**

| Document | Duplicated field | Example |
|----------|-----------------|---------|
| Allotment Letter | Date | `Date: 08-06-2026Date: 08-06-2026` |
| Allotment Letter | Land area | `1,300.58 sq.mt. (14,000 sqft)1,300.58 sq.mt. (14,000 sqft)1,300.58 sq.mt. (14,000 sqft)` |
| Allotment Letter | "at" preposition | `atat Plot No:` / `RERA Registration NoK-RERA Registration No.:` |
| Allotment Letter | Promoter name | `Name: M/S DRA...Name: M/S DRA...` |
| Allotment Letter | URL | `https:/https://rera.karnataka.gov.in/` |
| Agreement of Sale | Possession clause | `on or before [24 months...]on or before [24 months...]` |

**Fix:** Replace the full duplicated string in one shot. For severe cases (4+), use regex to collapse:
```python
import re
cleaned = re.sub(r'^(Rs\. _______________________ \[Booking Amount[^\]]+\])(?:Booking Amount[^\]]+\])*', r'\1', para.text)
```

**Always run a verification pass** after all replacements to catch any missed duplications:
```python
import re
for i, para in enumerate(d.paragraphs):
    t = para.text.strip()
    if re.search(r'(\w{3,})\1', t):
        print(f"WARNING: Possible duplication at P{i}: {t[:80]}")
```

### Schedule of Unit Prices (for Agreement of Sale)

When the user provides pricing parameters (base rate, floor rise, car park value), add a **Schedule of Unit Prices** table to the Agreement of Sale. Insert it between clause 1.2 (Total Price) and clause 1.3.

**Typical pricing structure:**
- Base rate: ₹10,000/sqft (per sqft of Super BUA)
- Floor rise: ₹500 for 1st floor, ₹200 additional for 2nd floor (or as specified)
- Car park: ₹5,00,000/unit (1 per unit)

**Table columns:** S.No. | Unit No. | Floor | Facing | Super BUA (sqft) | Rate (₹/sqft) | Base Sale Value (₹) | Car Park (₹) | Total (₹)

**Rate calculation:**
```python
base_rate = 10000
floor_rise_1 = 500   # 1st floor
floor_rise_2 = 200   # 2nd floor (additional)

if floor == "1st":
    rate = base_rate + floor_rise_1       # 10,500
elif floor == "2nd":
    rate = base_rate + floor_rise_1 + floor_rise_2  # 10,700
```

**Insertion position:** The table should go right before clause 1.3, after all sub-paragraphs of clause 1.2. See `references/docx-modify-reupload-drive.md` for the XML positioning technique.

### DOCX highlighting

```python
from docx.enum.text import WD_COLOR_INDEX

def highlight_run(run):
    run.font.highlight_color = WD_COLOR_INDEX.YELLOW
    run.font.bold = True

# After filling a run with text:
for run in paragraph.runs:
    if 'my filled value' in run.text:
        run.font.highlight_color = WD_COLOR_INDEX.YELLOW
```

### XLSX highlighting

```python
from openpyxl.styles import PatternFill

yellow_fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')

cell = ws.cell(row=r, column=c, value='my value')
cell.fill = yellow_fill
cell.font = Font(bold=True, color='CC0000')
```

## Joint Development & GPA Holder Pattern

When the project is a Joint Development between Landowner(s) and Developer, the developer acts as **GPA Holder** of the landowners via an Irrevocable GPA Coupled with Interest. This must be reflected consistently in ALL documents:

| Document | How to reference |
|----------|-----------------|
| **Promoter field** | "M/S DRA REALTY PRIVATE LIMITED, acting as GPA Holder of the Landowners (names) vide GPA No. X dated Y, and as Developer under JDA dated Z" |
| **Form-2 / Form-3** | Promoter = GPA Holder & Developer |
| **Allotment Letter** | Reference JDA + GPA in subject/whereas clauses |
| **Agreement of Sale** | P11/P48: Full GPA+JDA context in promoter definition. P96-112: Landowners → JDA → GPA chain |
| **SIS Project details** | Promoter = GPA Holder status |

### Standard wording (June 2026, verified):
```
M/S DRA REALTY PRIVATE LIMITED, acting as the GPA Holder of the Landowners
(Mrs. Farida R Iyer and Mr. Raghu Iyer) vide Irrevocable GPA No.
DRO/SJN/GPA/1088/2025-2026 dated 16 August 2025, and as Developer under
Joint Development Agreement dated 16 August 2025 registered as
Doc No. SHV-1-02227-2025-26
```

## Single Building, No Phases Rule

If the project has ONE building/tower, ALL documents must say "1 building(s)" and "No Phases" (NOT "Phase 1" or blank). Search for these patterns in every file:

- `_____ Phase` → `No Phases` or `Single Building Project`
- `Phase 1` → `Single Building (No Phases)`
- `__ multistoried apartment buildings` → `1 multistoried apartment building`

## Company Letterhead Format for Board Resolutions

Board Resolutions must be formatted as company letterhead with:

1. **Top section** (professional layout):
   - Company name prominently (navy blue, 16-18pt)
   - Tagline (optional, italic, small)
   - CIN | GST | PAN on one line
   - Registered office address
   - Double border line separator

2. **Document title** centered below letterhead

3. **Attendee table** with Sl No, Name, Designation, DIN columns

4. **Resolutions** — serially numbered, each starting with "RESOLVED THAT" / "RESOLVED FURTHER THAT"

5. **Signature block** — Two-column layout for joint signatures (Director 1 | Director 2)

6. **Company Seal** indicated on right side

7. **Note about unavailable data** — If DIN numbers are not in MOA/AOA, add red footnote: "DIN numbers could not be extracted from the available documents. Please verify from MCA portal."

### DIN extraction sources
- **MOA / AOA**: Generally do NOT contain DIN numbers (they show subscriber names only)
- **GST Certificate Annexure B**: Lists directors but NOT their DINs
- **MCA Portal**: The authoritative source (but government domains blocked by Browser Use Cloud)
- **ITR / Financial statements**: May contain director PANs (which can be used to look up DIN via MCA)
- **Fallback**: Leave as placeholder `[DIN: _______]` with note for user to fill

## Board Resolution & Organization Structure

### Board Resolution
Standard document needed for RERA application. Extract from company documents (MOA, AOA, Incorporation Certificate, PAN, GST):

| Data | Source |
|------|--------|
| CIN | Incorporation Certificate |
| Company Name | MOA |
| Registered Office | MOA / GST Certificate |
| Directors | GST Certificate Annexure B |
| Authorized Signatory | Board minutes or JDA signing party |

The resolution should authorize:
1. Project development and RERA registration
2. Specific director(s) to sign all documents
3. Bank account operations for the project
4. Cost confirmation (from Form-2/3)
5. Common Seal affixture

### Organization Structure
Three-level hierarchy:
- **Level 1**: Board of Directors (from GST Annexure B)
- **Level 2**: Key Managerial Personnel (Managing Director / CEO)
- **Level 3**: Project Team (Architect, Structural Engineer, Contractor, Legal, Accounts, Sales — fill names where available, leave `[Name]` placeholders for user)

Include company history note (original name, incorporation date, name change date) in the hierarchy summary.

## Step 7 — Common Areas & Amenities Spreadsheet

RERA applications often need a separate spreadsheet detailing common areas and amenities. Create this from:

1. **Common Area Breakup** (from the architect's Area Statement xlsx — typically has a "Common Area" sheet with staircase, lift, lobby areas)
2. **Amenities List** (from the Specifications sheet — gym, sauna, lounge, rooftop garden, elevator, CCTV, DG, solar, RWH)
3. **Common Area Specifications** (flooring, finishes, railings — also from Specifications sheet)
4. **Plan Sanction Conditions** (BBMP conditions related to common areas — extracted from the plan sanction PDF)

The spreadsheet should have 4 sheets:
- Common Area Breakup (Execution vs Sanction figures)
- Amenities (20+ items with categories, specifications, brands)
- Common Area Specs (materials and finishes for staircases, lobbies, parking, etc.)
- Plan Conditions (relevant BBMP sanction conditions with compliance status)

## DRAAS User Style Preferences

### Prakash (psingh@draas.com)
- **Extremely direct** — no clarifying questions, no options, just do the most reasonable action
- **Action-first**: send message = just send, extract = just extract. Don't ask "what should I do with it?"
- **Wants comprehensive filling**: fill every field that has data available, not just the obvious ones
- **Yellow highlighting**: all changed/updated fields must be highlighted in yellow
- **File naming**: `YYYYMMDD_DescriptiveName` pattern
- **WhatsApp links**: `wa.me` links must be clickable — no code blocks
- **Voice messages**: acceptable input method

### Nishant (ndr@draas.com)
- **Action-first during uploads**: OCR/process immediately to identify the document, don't ask "what should I do with it?"
- **WhatsApp links**: `api.whatsapp.com/send` (NOT `wa.me`). Bold caption + clickable link.
- **Calendar**: detail+attendees+Google Meet, re-fetch for correct event ID
- **Drive auto-fill before asking**: check Drive first for data before asking user
- **Parallel agents**: use delegate_task for multi-category data extraction
