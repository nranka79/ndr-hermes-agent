# Ranka Oasis — Project Data Spreadsheet Extraction
**Session:** June 2026 | **User:** Bharat (Nishant Ranka's phone) | **Spreadsheet:** `1uXcAoO1IsJ5dJsvn8949ViKBSowOC65802aO_U4pTTU`

## Sheet: "Ranka Oasis" — Pre-Populated Fields

| Row | Field | Value | Source |
|-----|-------|-------|--------|
| A3 | Group Name | DRA Group | Already filled |
| A4 | Project Executing Entity | Sevaganapalli Land Partners | Already filled |
| A5 | Date of Incorporation | Its Firm | Correct — partnership firm, no specific incorporation date |
| A6 | Registered Office | No. 201 A202BA, Queens Corner Apts, No.3 Queens Road, Bengaluru – 560001 | From GST Certificate REG-06 |
| A7 | Project Name | Ranka Oasis | Already filled |
| A8 | Location | Ranka Oasis, Sevaganapalli – Tamil Nadu 635103 | Already filled |
| A9 | CIN | NA | Correct — partnership firm has no CIN |

## Key Document IDs (Drive)

- Master Plan PDF: `1yLBO1NbMiH2qmB8wkdkkt9SNIIlOOZW6`
- Master Document Reference Summary: `1peJlNfmEcImBhB3M_7DBg1REk-tGHh1C`
- GST Certificate: `1Oc9GbjPAnIz49a6D2M_Xg2BudK6UAdG7`
- PAN Card: `1moC5JHz1xzzOjVbi_Tu2UmvF0_lap0HC`
- TAN: `150dFAqZercVYOHoMwVS4qqJLa-WTT6uk`
- Firm Registration Acknowledgement: `1MqLQNcgKJ2p15R_x_Gqxgq0fPX9RlzvU`
- DTCP Layout Plan (Shivaji): `1pJ9upN71y3gegmZWa4WtFJSzcbpCmurI`
- DTCP Layout Sanction: `1hqAPCZTj829ceph0JioCKayY7uxhTQ2I`
- RERA Sale Deed Draft: `11rMhq6MwriO54jhlveyD132_FXhXeahXNiViLzmvbhQ`
- Geotechnical Report: `1GXCFT24Bu3aN4GXFICOHtHv5FsjVsa0f`
- Plot Sale Deed (Nishant Prakash): `1d2w32L3C0qIJXvKxnjkEoehfzoiVnMaJ`

## Spreadsheet Structure (82 rows, Sections A–H)

- **Section A:** Entity details (rows 3–9)
- **Section B:** Land Details — Land Area (sq ft), Type (Freehold), JD Share, FSI, TDR
- **Section C:** Structure Specs — BUA, FAR, No. of Buildings
- **Section D:** Sharing Ratio — Dev 100%, LO – (JV: N/A for Ranka Oasis — Dev owns 100%)
- **Section E:** Unit breakdown — start date, completion, floors, villas, area, units, saleable area
- **Section F:** Approvals — Plan Sanction, RERA, Commencement Certificate, Electricity, Water, Telecom, Height, HAL, Fire, Environment, Pollution
- **Section G:** Profitability — Total Sales Value, Total Project Cost, Profit, Profit%
- **Section H:** Sales Details (Developer share) — Sold/Unsold breakdown

## Master Plan Vision Extraction (June 2026)

**Source:** `/tmp/ranka_oasis_master_plan.pdf` → `pdftoppm` → `/tmp/master_plan_page-1.png` → vision_analyze

Extracted details:
- **Total plots:** 138
- **Land area from drawing:** ~186,352 sq ft (~4.28 acres)
- **Note:** Master Reference Summary says ~12.74 acres across Survey Nos. 158, 166, 167, 168, 176, 177 — master plan may show only Phase 1 portion
- **Roads:** 7M wide (internal), 10M wide (main arteries)
- **Amenities:** Park areas (3), Clubhouse (1), Transformer yard (1), Entrance portal (1)
- **Plot count by section:**
  - Plots 1–5 (bottom-left)
  - Plots 7–32 (bottom-right)
  - Plots 33–55 (central-bottom)
  - Plots 56–62 (central-left)
  - Plots 63–74 (top-left, near PARK)
  - Plots 75–81 (central-top)
  - Plots 84–97 (central-right)
  - Plots 101, 104–111, 115–120 (top-right)
  - Plots 122, 124, 125, 130 (far top-right, near transformer)
  - Plots 131–138 (bottom-central)

## What Can Be Filled From Drive Docs

### Already Available (no user input needed)
- Date of Incorporation: 03/08/2023 (from PAN card)
- Firm PAN: AFCFS4430H (Sevaganapalli Land Partners)
- GST: 29AFCFS4430H1ZY
- Registered Office Address (exact from GST certificate)

### Needs Extraction From Drive Docs
- **Land area (sq ft):** From Layout Plan PDF (DTCP sanction) — extract survey-wise areas
- **FSI:** From DTCP layout sanction
- **Total BUA / FAR:** From sanctioned plan
- **No. of Buildings:** From layout plan (number of blocks/phases)
- **Construction start date:** From RERA registration or first BBMP permit
- **Expected completion:** From RERA target
- **No. of floors:** From plan sanction
- **Villas:** Ranka Oasis is plotted development + villas — confirm count
- **Saleable area:** From RERA registration or cost sheet
- **Approvals:** LP number, date, issuing authority from DTCP sanction doc

### Key Drive Search Commands

```python
# Find all Ranka Oasis PDFs in Engineering folder
results = drive_service.files().list(
    q="'1wrwSgW8IYzNMP085knPUhFkkVzctqaiv' in parents and trashed=false",
    fields="files(id, name, mimeType)"
).execute()

# Find layout plan
results = drive_service.files().list(
    q="name contains 'Layout Plan' and name contains 'Ranka Oasis'",
    fields="files(id, name)"
).execute()

# Find DTCP sanction
results = drive_service.files().list(
    q="name contains 'DTCP' and name contains 'Sevaganapalli'",
    fields="files(id, name)"
).execute()
```

## Workflow for Filling This Spreadsheet

1. Read the spreadsheet via `values.get(range='Ranka Oasis!A1:Z5')` to confirm headers
2. Identify which rows already have values vs. which need filling
3. For each unfilled row, search Drive for the relevant document
4. Download → pdf2image → vision_analyze → extract figures
5. Batch fill via `values.update()` — confirm each field before writing

## User Preferences (June 2026)

- Bharat says "Let's go out" when frustrated — means he wants to skip the current task
- He said "By this I understand that you will not be able to work on this task" when Drive extraction seemed blocked — he prefers direct data entry ("one by one is fine")
- When he says "no browser search when documents on Drive suffice" — he means use Drive only, no external web
- He confirms PAN/GST field is NOT in the spreadsheet template — no need to add it