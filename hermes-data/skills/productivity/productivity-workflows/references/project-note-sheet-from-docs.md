# Project Note Sheet from Uploaded Plans & Reports

Extract structured real-estate project data from multiple uploaded document types and compile a Project Note Sheet (Google Doc). Verified on DRA Downtown, Egmore, Chennai (Jun 2026).

## Inputs

User typically uploads a batch of files:
- **Weekly Progress Report** (PDF) — budget, milestones, timeline, delays
- **Approved Site Plan** (PDF) — site dimensions, plot area
- **Architectural Plans** (multiple pages/sheets) — floor plans, parking, FSI, unit areas
- **Business Suite / Tenant Option Plans** (PDFs) — office space breakdowns
- **Renders / photos** (JPEG) — building visualisations (may have no readable text)
- **Approval docs** (PDFs) — sanction numbers, dates

## Extraction Steps

### 1. Weekly Progress Report — `pdftotext -layout`
```bash
pdftotext -layout "input.pdf" /tmp/output.txt
```
Key data to pull:
- **Project Data**: name, site area, BUA, saleable area, floors, type (Commercial/Residential)
- **Budget**: Initial budget, committed/awarded, cost certified, net paid, outstanding
- **Milestones**: % completion per stage (foundation → slab → blockwork → plastering → finishes → handover)
- **Timeline**: Start date, planned finish, actual/anticipated finish
- **Delay Register**: Each delayed activity with days + total delay
- **Catch-up plan**: strategies for recovering delays

### 2. Architectural Plans — rendered image path
For image-based PDFs (pdftotext returns 0 lines):
```bash
pdftoppm -jpeg -r 200 "input.pdf" /tmp/output/page.jpg
```
Then analyze each page with `vision_analyze`. Key data to extract:
- **Plot Area** — typically in sq.ft
- **FSI** — allowable vs achievable
- **Stilt floor area** — for parking
- **Typical floor area** — total across all floors
- **Parking** — Cars required vs achieved, Bikes required vs achieved
- **Per-unit breakdown**: Office #, Carpet Area, Plinth Area, Saleable Area (each in sq.ft)
- **Triple height / atrium dimensions**
- **STP ducts** — Fresh Air Duct, Exhaust Duct presence
- **Nearby landmarks** — site context

### 3. Approved Site Plan — `pdftotext -layout`
May extract dimension lines and site boundaries. Note: output may be heavily OCR-fragmented (dimensions scattered). Vision_analyze on rendered pages is often better for site plans.

### 4. Renders / Photos
Check file properties (dimensions, color count) to classify:
- If unique_colors > 10,000 → photo/render, text unlikely
- Upload to Drive folder as-is with proper naming
- Note: cannot extract structured data from renders

## Note Sheet Structure (Google Doc)

### INCLUDED
- Project name, location, developer, architect
- Site Area, BUA, Saleable Area
- Floors (Stilt + N), Building height
- Type (Commercial / Residential / Mixed)
- Completion date
- STP design info (capacity, type, approval date)
- **Car Parking** — count achieved (vs required)
- **Bike Parking** — count achieved (vs required)
- Power backup — if found in docs (else note as "Not found")
- Sanction details — number and date if found in docs

### EXCLUDED (per DRAAS user preference — Nishant confirmed Jun 2026)
- Lease premium
- Estimated sale value / rate
- Construction cost
- Total cost
- CF loan
- Rental potential
- Approval status (just state "Fully Approved")

## Tools Used

| Tool | For |
|------|-----|
| `pdftotext -layout` | Text-based PDFs (progress reports, some approval docs) |
| `pdftoppm -jpeg -r 200` | Render image-based PDF pages for vision analysis |
| `vision_analyze` | Read rendered plan pages (parking, areas, annotations) |
| `build_service('drive', 'v3')` | Folder creation, file upload, dedup check |
| `build_service('docs', 'v1')` | Google Doc creation for note sheet |

## Pitfalls

- **Slight data discrepancies** between docs are normal — weekly report may say 46,233 sqft site area while the plan says 46,251.08 sqft. Note both with source links.
- **Progress reports may have 0-line text from pdftotext** for image-based scans — fall back to pdftoppm + vision.
- **Architectural plans mix text and annotations** — some values live in tables (pdftotext-readable), others as callouts on drawings (vision-only). Use both paths.
- **Not all uploaded images are project-related** — check content before filing (user may intersperse housewarming invites, personal maps, etc.).
- **User may batch-upload unrelated documents** alongside project files — separate them before filing.

## Verified Example: DRA Downtown, Egmore (Jun 2026)

| Field | Value | Source |
|-------|-------|--------|
| Site Area | 46,233 sqft (46,251.08 per plan) | Weekly Report / Stilt Plan |
| BUA | 109,353 sqft | Weekly Report |
| Floors | Stilt + 4 (18.25m) | Plan drawings |
| Type | Commercial (Office) | Plan header |
| Car Parking | 71 achieved (67 req) | Stilt Floor Plan |
| Bike Parking | 304 achieved (271 req) | Stilt Floor Plan |
| Budget | ₹42.84 Cr | Weekly Report |
| Start | Nov 2024 | Progress Report |
| Completion | July 2026 | Progress Report |
| STP | 110 KLD SBR (approved May 2024) | Earlier records |
| Architect | Kharche & Associates | Plan sheets |
| Construction | 66.58% complete | Weekly Report |
