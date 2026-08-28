# BBMP NOC Requirements Research & Management Report

**Skill:** `real-estate-legal-compliance`
**Category:** Building Plan Approval Compliance

## Trigger

User asks: "What NOCs are required for building plan approval?" or "Generate a report on NOCs needed for [project details]" — providing project parameters (land area, building height, location, proposed use).

## Workflow

### Step 1: Map Project Parameters to Regulatory Triggers

Extract from the user's query (or ask if missing):

| Parameter | Regulatory Significance |
|-----------|----------------------|
| Building height | >=15 m → Height-based NOCs (aviation, fire, BESCOM, BSNL) |
| Built-up area | >2,000 sq.m → Area-based NOCs (KSPCB, BWSSB) |
| Dwelling units | >=20 units → Unit-based NOCs (KSPCB, BWSSB) |
| Land area | >20,000 sq.m residential → BDA Dev. Plan approval |
| Location (village/hobli) | Determines aerodrome proximity (AFS/HAL/Jakkur) |
| Land use / zoning | Zoning compliance per RMP 2015 |

### Step 2: Source Official BBMP NOC Matrix

**Primary reference:** `https://site.bbmp.gov.in/PDF/buildingplanapproval/NOC%20Details.pdf`

This PDF is the authoritative BBMP document listing every NOC by building parameter. Extract the relevant rows based on project triggers.

### Step 3: Research Legal Basis Per NOC

For each triggered NOC, find the specific Act/GO/Notification:

| NOC | Key Source Documents |
|-----|---------------------|
| Aviation Height Clearance | Aircraft Act 1934 (S.9A), Aircraft Rules 1937 (R.89), IAF Yelahanka zoning map, HAL NOC procedure, AAI NOCAS portal |
| Fire Safety NOC | Karnataka Fire Force Act 1964 (S.13) + Amendment 2023 (Act 24 of 2023), GO HD 33 SFB 2011, BBMP Building Bye-Laws 2023 Part 4 |
| BESCOM NOC | BBMP Building Bye-Laws 2023 NOC Schedule, BESCOM Terms & Conditions of Supply |
| BSNL NOC | BBMP Building Bye-Laws 2023 NOC Schedule, Indian Telegraph Act 1885 |
| KSPCB CFE | Water Act 1974 (S.25/26), Air Act 1981 (S.21), KSPCB 2018 circular on construction projects |
| BWSSB NOC | BWSSB Act 1964, Circular No. BWSSB/C/EIC/CE(W)/CE(E)/1160/2022-23 |
| Lab Dept | Karnataka Building & Other Construction Workers Welfare Board, labouronline.karnataka.gov.in |

### Step 3b: Gather Official Processing Timelines

For each triggered NOC, find the official timeline from the authority's website or published circulars:

| NOC | Official Timeline | Source |
|-----|-----------------|--------|
| Aviation (HAL/IAF) | 30-90 days (civil) / 60-180 days (defence) | HAL NOC Procedure 2023, IAF Guidelines, CREDAI reference |
| Fire NOC | 15-30 days (provisional in 7 working days) | Karnataka Fire Force Amendment Act 2023, BBMP Notification 2011 |
| BESCOM NOC | 15-30 days | BESCOM FAQ, Charges Schedule |
| BSNL NOC | 15-30 days (longer if IBS design needed) | BSNL NOC samples (KRERA registered projects) |
| KSPCB CFE | 60-90 days (Orange); 30-45 days (Green); 100 days (Red Non-EIA); 120 days (Red EIA) | KSPCB Official Timelines page |
| BWSSB NOC | 30-45 days (3-4 weeks if near existing mains; 8-12 weeks if main extension needed) | BWSSB Portal, Circular 1160/2022-23 |
| Labour Dept | 7-15 days | Karnataka e-Labour Portal |

**Recommended phasing:**
- Phase 1 (start immediately): Aviation Height Clearance + KSPCB CFE + BWSSB NOC
- Phase 2 (after drawing finalisation): Fire NOC + BSNL NOC + BESCOM NOC
- Phase 3 (pre-construction): Labour Dept Registration
- Total: 12-20 weeks with parallel processing

### Step 3c: Compile Document Checklists Per NOC

For each NOC, compile the specific documents required by that authority:

| NOC | Documents Required |
|-----|-------------------|
| **Aviation Height Clearance** | Application form (2 sets by post for HAL), notarized affidavit on Rs.100 SP, GPS coordinates (Lat/Long DMS), elevation/height above MSL certificate from licensed surveyor, building elevation drawings (total height including OHT/lightning arrestor), site plan & location map, master plan of area, ownership/title docs, site photographs, affidavit undertaking height compliance |
| **Fire NOC** | Application form, building plan (architectural/structural/services), fire safety system drawings (hydrant, sprinkler, detection layout), site plan with fire tender access route, structural stability certificate, occupancy details, equipment test certificates, ownership proof, indemnity bond |
| **BESCOM NOC** | Application (online), ID proof (Aadhaar/Voter/Driving License/PAN), address proof, property docs (Sale Deed/Khata/Tax Receipts), building plan/site plan, load details form (connected load in KW), existing bill (if replacement) |
| **BSNL NOC** | Application letter to GM BSNL Telecom Circle, elevation drawings with total height, GPS coordinates + height MSL certificate, site plan & location plan, building composition details (basement/floors/terrace/OHT/Lift room), ownership/title docs |
| **KSPCB CFE** | Form 1 online (XGN portal), site plan, building plan, water balance diagram, STP proposal, solid waste mgmt plan, env. mgmt plan, air quality assessment, water consumption details, flow diagram, ownership docs, project cost details |
| **BWSSB NOC** | Application (BWSSB portal), building plan, Khata certificate, property tax receipts, site plan, ownership docs, floor plan with area breakup, water demand calculation, sewage generation calculation, rainwater harvesting proposal, NOCs from other depts (if available) |
| **Labour Dept** | Form I online (e-Labour portal), establishment name & location, employer details, PAN, Aadhaar/ID proof, worker count details, workmen insurance policy, Cess payment proof (1% of cost), site photographs, estimated cost statement |

**Tip:** Prepare at least 10 attested copies of building plan, site plan, ownership docs, and GPS certificate — these are the most commonly requested docs across authorities.

### Step 4: Collect Official URLs

Use web_search with targeted queries for each NOC's governing notification. Key URL patterns to collect:

- `site.bbmp.gov.in/PDF/buildingplanapproval/` — BBMP NOC matrix & related PDFs
- `dpal.karnataka.gov.in/` — Karnataka Gazette notifications
- `indianairforce.nic.in/Resources/pdf/color/YELAHANKA.pdf` — AFS zoning maps
- `hal-india.co.in/backend/wp-content/uploads/` — HAL procedures
- `bescom.karnataka.gov.in/storage/pdf-files/` — BESCOM circulars
- `kspcb.karnataka.gov.in/` — KSPCB consent guidelines
- `bwssb.karnataka.gov.in/` — BWSSB portal
- `labouronline.karnataka.gov.in/` — e-Labour portal

### Step 5: Compile Management Report (.docx)

Use **python-docx** to produce a professional report with these sections:

1. **Title Page** — Project name, date, "Prepared for Management Approval"
2. **Project Summary** — Parameter table with triggers
3. **Regulatory Framework** — Governing acts/regulations with brief descriptions
4. **Overview Matrix** — All NOCs sorted by trigger category with priority, timeline column
5. **Detailed NOC Analysis** — One subsection per NOC with:
   - Trigger condition
   - Legal basis (specific act/section/notification)
   - Application process steps
   - **Processing timeline** (with source reference) ← new
   - **Document checklist** (bulleted list per authority) ← new
6. **Consolidated Document Checklist Matrix** — Table grid showing which documents are needed by which authority ← new
7. **Process Flow** — Phase-wise application timeline (Phase 1/2/3) with parallel tracks and dependencies
8. **Cost Estimates** — Govt fees + consulting estimates per NOC (label as indicative)
9. **Annexure: Source Links** — Table with official URLs mapped to document titles and descriptions

#### python-docx Code Patterns

```python
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def add_bold_para(doc, bold_text, normal_text=""):
    p = doc.add_paragraph()
    run = p.add_run(bold_text)
    run.bold = True
    if normal_text:
        p.add_run(normal_text)
    return p

def make_header_row(table, headers):
    """Bold the first row of a table"""
    for j, h in enumerate(headers):
        table.cell(0, j).text = h
        for p in table.rows[0].cells[j].paragraphs:
            for r in p.runs:
                r.bold = True
```

Style settings: Calibri 11pt, 2.54 cm margins, 24pt navy title, 'Light Grid Accent 1' tables.

### Step 6: Add Costing Analysis (if Vendor Quotation Available)

When the user has a vendor quotation for the NOC services, add a costing analysis subsection (8.1) to the report with:

1. **Per-NOC breakdown tables:** Each NOC as a separate table showing:
   - Professional fee vs government fee (DD) split
   - Industry benchmark range (with source)
   - Verdict (✅ Fair / ⚠ Overpriced / ❓ Needs clarification)

2. **Consolidated comparison table:** All NOCs in one row-per-item table:
   - `NOC | DSC Fee (Rs) | Est. Fair Fee (Rs) | Diff. (Rs) | Margin Analysis | Recommendation`

3. **Grand total table:**
   - Professional fees subtotal, DDs subtotal, GST, Grand total
   - DSC quote column vs Est. Fair column vs Negotiation Target column

4. **Benchmark reference data:**

   | NOC | Professional Fee (Fair Range) | Government Fee (Official) |
   |-----|------------------------------|--------------------------|
   | AAI NOC | ₹30,000 – ₹60,000 | NIL (AAI charges zero) |
   | BSNL Survey | ₹30,000 – ₹50,000 | DD ~₹75,000 – ₹95,000 |
   | HAL Survey | ₹1,00,000 – ₹1,50,000 | DD ₹2,00,000 + GST (official) |
   | MOD (IAF) NOC | ₹1,00,000 – ₹1,50,000 | NIL (IAF charges zero) |
   | Fire NOC | ₹25,000 – ₹50,000 | ₹10,000 – ₹25,000 |
   | BESCOM NOC | ₹15,000 – ₹25,000 | ₹5,000 – ₹15,000 |
   | KSPCB CFE | ₹25,000 – ₹50,000 | ₹15,000 – ₹30,000 |
   | BWSSB NOC | ₹20,000 – ₹35,000 | ₹10,000 – ₹20,000 |

5. **Negotiation strategy bullets** with target savings amount.

6. **Timeline comparison** sub-table: consultant's stated timeline vs industry standard vs assessment.

See `real-estate-legal-compliance` SKILL.md section **NOC Vendor Quotation Validation & Cost Benchmarking** for the full quotation validation workflow.

### Step 7: Deliver the Report

- Copy to `/opt/data/` for Telegram MEDIA: delivery
- Name format: `NOC_Requirements_Report_[Location]_[ProjectType].docx`

### Expanded Source Link List (19 URLs)

When building the annexure, include these sources:

1. BBMP NOC Requirements Matrix — https://site.bbmp.gov.in/PDF/buildingplanapproval/NOC%20Details.pdf
2. BBMP Building Bye-Laws 2023 — https://dpal.karnataka.gov.in/uploads/media_to_upload1750139344.pdf
3. Fire Safety Notification (2011) — https://site.bbmp.gov.in/documents/Fire%20Safety%20Notification.pdf
4. Karnataka Fire Force Amendment Act 2023 — https://dpal.karnataka.gov.in/storage/pdf-files/24of2023(E)Fireforce.pdf
5. Karnataka Fire Force Act 1964 — https://www.indiacode.nic.in/bitstream/123456789/8192/1/42_of_1964_%28e%29.pdf
6. IAF Yelahanka AFS Zoning Map — https://indianairforce.nic.in/Resources/pdf/color/YELAHANKA.pdf
7. IAF NOC Guidelines — https://indianairforce.nic.in/Resources/pdf/utilities/guidelines-for-NOC-UPDATED.pdf
8. HAL NOC Procedure — https://hal-india.co.in/backend/wp-content/uploads/2023/03/Latest-Amended-HAL-NOC-Procedure.pdf
9. AAI NOCAS Portal — https://nocas.aai.aero/nocas/
10. KSPCB Timelines — https://kspcb.karnataka.gov.in/time-taken-issuing-consent-authorization
11. KSPCB Categorisation — https://kspcb.karnataka.gov.in/consent-management/categorisation-rog
12. BWSSB Official Portal — https://bwssb.karnataka.gov.in/english
13. BESCOM Documents & Charges — https://bescom.karnataka.gov.in/storage/pdf-files/ICT%20and%20MIS/ListofDocuments&ScheduleofChargesforNewconnection.pdf
14. BESCOM FAQ — https://www.bescom.co.in/bescom/main/faq
15. BSNL NOC Sample (KRERA) — https://rera.karnataka.gov.in/download_jc?DOC_ID=QAlq5Gg5E%2F3ohWJTBKZdZA%3D%3D
16. e-Labour BOCW Registration — https://labouronline.karnataka.gov.in/karBuildingcon/Building_Registration.aspx
17. BBMP Building Plan Portal — https://site.bbmp.gov.in/buildingplan.html
18. BBMP Plan Sanction Sample (Labour condition) — https://img.staticmb.com/mbimages/reradoc/2024/03/22/53320311820509_2_20.pdf
19. CREDAI - AAI NOC Filing Guidelines — https://admin.credai.org/public/upload/e4a7cdc2bc0b73be0981a6bcb4d9a26a.pdf

### Consolidated Document Checklist Matrix

When the user needs a quick-reference grid showing which documents go to which authority, build a table like this:

| Document | Aviation | Fire | BESCOM | BSNL | KSPCB | BWSSB | Labour |
|----------|:--------:|:----:|:------:|:----:|:-----:|:-----:|:------:|
| GPS Coordinates Cert | Y | - | - | Y | - | - | - |
| Height Above MSL Cert | Y | - | - | Y | - | - | - |
| Building Elevation Drawings | Y | Y | - | Y | - | - | - |
| Building Plan / Floor Plans | Y | Y | Y | Y | Y | Y | - |
| Site Plan / Location Plan | Y | Y | Y | Y | Y | Y | - |
| Ownership / Title Deed | Y | Y | Y | Y | Y | Y | - |
| Khata Certificate | - | - | Y | - | - | Y | - |
| Property Tax Receipts | - | - | Y | - | - | Y | - |
| Notarized Affidavit | Y | Y | - | - | - | - | - |
| Fire Safety System Drawings | - | Y | - | - | - | - | - |
| Structural Stability Cert | - | Y | - | - | - | - | - |
| Water Balance Diagram | - | - | - | - | Y | Y | - |
| STP Proposal | - | - | - | - | Y | Y | - |
| Solid Waste Mgmt Plan | - | - | - | - | Y | - | - |
| Environmental Mgmt Plan | - | - | - | - | Y | - | - |
| Load Details / KW Estimate | - | - | Y | - | - | - | - |
| Rainwater Harvesting Plan | - | - | - | - | - | Y | - |
| ID Proof | - | - | Y | - | - | - | Y |
| Form I / Notice of Commencement | - | - | - | - | - | - | Y |
| Workmen Insurance Policy | - | - | - | - | - | - | Y |
| Site Photographs | Y | - | - | - | - | - | Y |

Tip: Prepare at least 10 attested copies of building plan, site plan, ownership docs, and GPS certificate — these cross multiple authorities.

## Pitfalls

- **Distance from airport matters**: Always verify actual distances (web_search) before stating whether AAI NOC applies. The 10 km KIA rule is separate from the AFS/Jakkur/HAL NOC which applies based on the building's location relative to each aerodrome.
- **Built-up area vs land area**: The KSPCB/BWSSB trigger is built-up area, not land area. Compute explicitly: land_sqm = land_sqft / 10.764.
- **Labour NOC is standard condition**: Not listed in the BBMP matrix PDF but appears on every sanction letter as Condition #4. Always include it.
- **Cost estimates**: Always label as indicative. BOCW Cess is 1% of total construction cost — a large separate item.
- **URL freshness**: Government portal URLs change. Verify each resolves before including.
- **Aviation is longest lead-time**: Start aviation and KSPCB/BWSSB in parallel first; Fire requires finalised drawings.
- **Google Maps "365m" parameter**: The `@lat,lng,365m` value in a Google Maps URL is the camera altitude/zoom level (in this case ~1,197 ft AGL for satellite view), NOT a building height. Do not confuse with structure height.
- **Overlapping airfield zones**: A North Bengaluru site can fall under BOTH Jakkur GFTS (5 km Inner Horizontal Surface) and Yelahanka AFS (10 km Conical Zone) simultaneously — both NOCs are mandatory and one does not substitute for the other. File via NOCAS which routes to both AAI and IAF COO.

## Verified Example

**Allalasandra Village, Yelahanka Hobli — 53,000 sq.ft, 18m height, residential apartments (Jul 2026)**

Result: 7 NOCs identified, official timelines and document checklists sourced per authority, 19 official source links compiled, consolidated document checklist matrix created, .docx report (v2) delivered via Telegram MEDIA. Report included per-NOC processing timelines from KSPCB official page, HAL NOC procedure, BESCOM FAQ, and other departmental sources.
