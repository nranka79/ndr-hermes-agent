# RERA Registration Document Workflow — DRAAS

Generated from: Ranka Amber project (June 2026), Prakash + Nishant sessions.

## 12-Document RERA Registration Set

When the user needs to prepare RERA registration documents, the following standard set is required (per Section 4 of RERA Act and Karnataka RERA Rules, 2017):

| # | Document | Format | Certified By |
|---|----------|--------|-------------|
| 1 | Work Order | Letterhead | Promoter |
| 2 | Project Photos with GPS | Photos (app) | On-site |
| 3 | Project Details (name, start/end dates) | Letterhead | Promoter |
| 4 | Project Specifications | Letterhead | Promoter |
| 5 | Source of Water Supply + Borewell details | Letterhead | Promoter |
| 6 | Cash Flow Statement (3 FYs) | Letterhead | Promoter |
| 7 | Director's Report (3 FYs, per Companies Act S134) | Letterhead | Board |
| 8 | Means of Finance / Source of Funds | Letterhead | Promoter |
| 9 | Total Cost of Project Land | Letterhead | Promoter (attested) |
| 10 | Construction Cost Abstract (BOQ summary) | Letterhead | Engineer |
| 11 | Common Areas & Amenities Measurement | Letterhead | Architect |
| 12 | Area Statement (Carpet, Common, UDS per unit) | Excel + Letterhead | Architect |

Also required separately:
- Board Resolution (S179 Companies Act)
- Organization Structure with T&C
- SIS 5.2 Spreadsheet
- Form-1 CA (Reg)
- Form-2 Architect (Reg)
- Form-3 Engineer (Reg)
- Allotment Letter (model KRERA form)
- Agreement of Sale Proforma (model KRERA form)

## Data Sources & Extraction Order

When gathering data for RERA forms, consult in this priority:

1. **Plan Sanction / Building Licence** — Authority, sanction no, date, land area, built-up, FAR, coverage, height, floors, units, parking, conditions
2. **JDA / GPA / EC** — Landowner names, JDA date/doc no, GPA date/doc no, correct boundaries (North/East/West/South), survey details
3. **Area Statement (Architect's XLSX)** — Unit-wise carpet area, balcony, built-up, common area breakup, UDS calculation
4. **Specifications Sheet** — Construction specs, amenities, brands, finishes
5. **Company Documents (MOA/AOA/Incorporation/GST/PAN)** — CIN, registered office, directors, capitalization, GST, PAN
6. **ITR / Audited Financials** — Cash flow, P&L, balance sheet for 3 preceding FYs
7. **BOQ / Cost Estimate** — Construction cost breakdown by component

## Critical Distinctions

### Project-Level vs Per-Allottee Data

**FILL with project data:**
- Project name, address, description
- Promoter name, CIN, registered office, directors
- JDA/GPA references, landowner names
- Sanction details, approval numbers
- Total units, building count, floor count
- Total land area, built-up, carpet, FAR
- Parking count, common area breakdown
- Amenities list, specifications
- Estimated cost (total project)
- Boundaries (as per EC, not arbitrary)

**LEAVE BLANK (per-allottee/negotiated/execution only):**
- Allottee name, PAN, Aadhar, address
- Specific unit number
- Carpet area of specific unit
- Total consideration / price
- Booking amount
- Payment schedule dates
- Default periods (negotiable)
- Possession date (needs OC timeline)
- Engineer/Architect license numbers if not provided

### Promoter Legal Status
- If the Developer holds a GPA from the Landowners, the Promoter should be described as:
  `"[Company Name], acting as the GPA Holder of [Landowners] vide GPA No. [___] dated [___], and as Developer under Joint Development Agreement dated [___] registered as Doc No. [___]"`
- The GPA Holder status must be consistently applied across ALL documents

## DOCX Letterhead Generation

Use `python-docx` with the following structure:

```python
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

def letterhead(doc):
    # Top border
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pPr.append(parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="24" w:space="1" w:color="1F3864"/></w:pBdr>'))
    
    # Company name - 16pt bold, navy blue #1F3864
    # Tagline - 8.5pt italic, grey
    # CIN/GST/PAN - 7.5pt, navy
    # Address - 7.5pt, navy
    # Bottom border
    
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
```

Standard elements: Company name, tagline, CIN/GST/PAN, registered address, double border lines, signature block with Director name + DIN + Company Seal placeholder, footer note.

## Color Highlighting Convention

Use `WD_COLOR_INDEX` for change tracking:

| Color | Meaning |
|-------|---------|
| **YELLOW** | Initial data fill (project-level data) |
| **TURQUOISE** | Second-pass / JDA-correction updates |
| **BRIGHT_GREEN** | User-requested changes after review |

```python
from docx.enum.text import WD_COLOR_INDEX
run.font.highlight_color = WD_COLOR_INDEX.YELLOW
```

## SIS 5.2 Spreadsheet Mapping

The SIS 5.2 Excel template has 5 sheets. Key field mapping from plan sanction:

### Project Details
- R4C: Project Name ← Plan Sanction
- R5C: Description ← Plan Sanction
- R8C: Type ← "Residential"
- R9C: Sub Type ← "Apartment"
- R10C: Status ← "New"
- R11C: Start Date ← From Schedules sheet
- R12C: End Date ← From Schedules sheet
- R13C: Address ← Full plot address from plan
- R17-R20C: Boundaries ← From EC, NOT from generic description
- R22-R23C: LAT/LONG ← Geocode address, verify against known location

### Plan Details
- R6C: Authority ← BECC / BBMP
- R7C: Plan No ← GBA/BECC/XXXX/YY-ZZ
- R8C: Date ← from plan
- R9C: Total units ← from plan
- R15C: Land area ← from plan
- R18C: Built-up ← from plan
- R19C: Carpet ← from plan
- R33C: Type of Inventory ← "Apartment"
- R35C: Total Inventories ← matches R9C

### FAR Details
Watch the row mapping carefully — the template has a specific layout where:
- R2: Total Towers (B col)
- R3: FAR Sanctioned (B col)
- R5: Tower 1 Name (B col)
- R6: Type (B col)
- R7: No. of Floors (B col)
- R8: Total Units (B col)
- R9: No. of Basement (B col)
- R10: No. of Stilts (B col)
- R11: No. of slabs (B col)
- R12: Parking (B col)
- R13: Height (B col)

Floor-wise distribution starts at R19 (B=floor, C=units).

## Document Numbering Convention

```
YYYYMMDD_ProjectName_DocumentType.docx
```

Example: `20260608_Ranka_Amber_Form-2_Architect.docx`

## Upload Pattern

1. For DOCX files → Upload as `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
2. For XLSX files → Upload with mimeType `application/vnd.google-apps.spreadsheet` to auto-convert to Google Sheet
3. Delete existing version before uploading updated version to avoid duplicates
4. Maintain consistent naming with date prefix for version tracking

## Key Company Data Points (DRA REALTY PRIVATE LIMITED)

- CIN: U70100KA2011PTC058105
- PAN: AAPCS9730H
- GST: 29AAPCS9730H1ZO
- Registered Office: 201A/202BA, Queens Corner, No.3, Queens Road, Bangalore - 560001
- Directors: Nishant Ranka, Kishan Murjani Nair
- Original incorporation: 11 April 2011 (as Southcity Retail Plus Pvt Ltd, name changed 8 Dec 2020)
- DIN numbers are NOT in MOA/AOA — must be obtained from MCA portal
