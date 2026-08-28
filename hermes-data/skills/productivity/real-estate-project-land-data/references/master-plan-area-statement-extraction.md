# Master Plan → Area Statement Extraction

Extract ALL plot numbers and their details from a master plan / layout plan PDF into a structured Google Sheet area statement.

## Trigger

User shares a layout master plan PDF and asks for an "Area Statement" — a table with:
- Plot No, Dimensions, Plot Size (Sq.ft), Plot Size (Sq.Mtr), Facing/Orientation, Survey No

## Workflow

### Phase 1: PDF → Image

`vision_analyze` does NOT accept PDFs directly (`Only real image files are supported`). Convert first:

```bash
pdftoppm -png -r 300 "/path/to/plan.pdf" /tmp/plan_page
```

- 300 DPI is sufficient for most master plans with readable plot labels
- Check page count: `ls -la /tmp/plan_page*.png`
- For A0/A1 large plans, 200 DPI may be sufficient and avoids PIL DecompressionBombWarning

### Phase 2: Extract Data via vision_analyze

Use `vision_analyze` on the rendered PNG with a comprehensive prompt:

```
This is a master plan for a layout. I need to extract ALL plot details.
For each plot, tell me:
1. Plot Number
2. Dimensions (if shown along edges)
3. Plot Area in Sq.ft (shown inside each plot)
4. Facing — which road does the plot front onto
5. Survey No (if marked)

Also read the title block: project name, architect, client, date, drawing number, scale.
Read the legend/color key.
Read all road names/labels.
```

**Strategy for large complex plans with many plots:**
- For plans with 50+ plots, crop the image into a grid (e.g. 3×3 sections) and run vision_analyze per section
- Prompt each section: "Read every plot number and its area in sq.ft visible in this section. List them in order."

### Phase 3: Reconcile Vision Output

- vision_analyze may miss some plot numbers or misread areas
- Cross-check: many plots in a row often share the same standard area (e.g. 1,517.71 Sq.ft appears repeatedly)
- Flag combined plots (79-80, 103-104, etc.) as single entries in the table
- Plots at the edge of the plan (131-138) may have illegible areas — mark as "—"

### Phase 4: Create Google Sheet

Create the sheet via Google Sheets API:

```python
from tools.gws_auth import build_service

sheets = build_service('sheets', 'v4', service_name='google-draas')
drive = build_service('drive', 'v3', service_name='google-draas')

# 1. Create sheet
spreadsheet = {
    'properties': {'title': 'YYYYMMDD_PROJECT_Area_Statement_MasterPlan'},
    'sheets': [{'properties': {'title': 'Area Statement'}}]
}
sheet = sheets.spreadsheets().create(
    body=spreadsheet, fields='spreadsheetId,spreadsheetUrl'
).execute()
sheet_id = sheet['spreadsheetId']

# 2. Write headers + data in one call
values = [
    ["#", "Plot No.", "Dimensions (ft)", "Plot Size (Sq.ft)", "Plot Size (Sq.Mtr)", "Facing / Orientation", "Survey No."],
    [1, "1", "—", 2858.15, 265.53, "Corner — Road A", "—"],
    # ... all plot rows
]

result = sheets.spreadsheets().values().update(
    spreadsheetId=sheet_id,
    range=f"'Area Statement'!A1:G{len(values)}",
    valueInputOption='USER_ENTERED',
    body={'values': values}
).execute()

# 3. Share with user
drive.permissions().create(
    fileId=sheet_id,
    body={'type': 'user', 'role': 'writer', 'emailAddress': 'USER_EMAIL'},
    sendNotificationEmail=False
).execute()
```

### Phase 5: Format the Sheet

Use `batchUpdate` with `repeatCell` for formatting:

```python
requests = [{
    'repeatCell': {
        'range': {'sheetId': 0, 'startRowIndex': 0, 'endRowIndex': 1},
        'cell': {
            'userEnteredFormat': {
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}},
                'backgroundColor': {'red': 0.1, 'green': 0.23, 'blue': 0.36},
                'horizontalAlignment': 'CENTER'
            }
        },
        'fields': 'userEnteredFormat(textFormat,backgroundColor,horizontalAlignment)'
    }
}]
# Auto-resize columns
for col in range(7):
    requests.append({
        'autoResizeDimensions': {
            'dimensions': {'sheetId': 0, 'dimension': 'COLUMNS', 'startIndex': col, 'endIndex': col + 1}
        }
    })
# Freeze header row
requests.append({
    'updateSheetProperties': {
        'properties': {'sheetId': 0, 'gridProperties': {'frozenRowCount': 1}},
        'fields': 'gridProperties.frozenRowCount'
    }
})
```

## Pitfalls

- **`foregroundColor` is under `textFormat`, not top-level:** `userEnteredFormat.textFormat.foregroundColor` is correct; `userEnteredFormat.foregroundColor` silently fails with "Unknown name" error.
- **`en_IN` locale is unsupported:** Sheets API rejects `locale: 'en_IN'` with `Invalid requests[0].updateSpreadsheetProperties`. Omit or use `en_US`.
- **Plots with illegible areas** (e.g. edge plots on the plan): Mark as "—" rather than guessing. Flag them in the response.
- **Combined plots** (79-80, 103-104, 127-128-129-130): List as a single row with the compound plot number. The vision model may interpret these as ranges or combined parcels.
- **Standard area patterns**: Many plots in a row share the same area. A cluster of 1,517.71 Sq.ft plots is common — don't flag these as missing data.
- **Dimensions not shown**: Master plans often show only the area (Sq.ft) inside each plot, not explicit length × width dimensions. State "—" for dimensions.
- **Survey numbers**: Master plans rarely mark survey numbers. Leave as "—" and note that survey numbers need to be obtained from revenue documents.
- **Conversion**: 1 Sq.ft = 0.092903 Sq.Mtr. Compute Sq.Mtr = round(Sq.ft × 0.092903, 2).

## Variant: Customer Area Statement (docx)

When the user asks for a **Customer Area Statement in Word format** (rather than a Google Sheet), use python-docx to create a professionally formatted .docx file with the architect's certified data:

### Workflow

#### Phase A: Read the Architect's Reference Sheet

The master plan vision analysis gives approximate plot numbers and areas, but the **architect's certified data sheet** (Google Sheet) has the authoritative orientations, dimensions, and corner status:

```
Plot # | Facing | Corner | Shape | East(ft) | West(ft) | North(ft) | South(ft) | Area(Sq.ft)
```

Read via Sheets API:
```python
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4', service_name='google-draas')
result = sheets.spreadsheets().values().get(
    spreadsheetId=REF_SHEET_ID, range='A:Z'
).execute()
rows = result.get('values', [])
```

Build a dict keyed by plot number:
```python
plot_data = {}
for row in rows[2:]:  # skip header rows
    if len(row) < 15: continue
    pno = str(row[0]).strip()
    if not pno: continue
    plot_data[pno] = {
        'facing': row[1], 'corner': row[2], 'shape': row[3],
        'dim_e_ft': row[10], 'dim_w_ft': row[11], 
        'dim_n_ft': row[12], 'dim_s_ft': row[13],
        'area_sft': row[14], 'area_sqm': row[8],
    }
```

#### Phase B: Data Merging Rules

| Condition | Action |
|-----------|--------|
| Plot exists in both sources | Use reference sheet dimensions + facing (authoritative) |
| Plot only on master plan | Use vision-extracted area, mark dimensions as "—" |
| Combined plot on plan (79-80) but individual in reference | Add individual plot rows from reference sheet data |
| Edge plots (131-138) illegible on plan | Reference sheet has the definitive data — use it |
| Standard plots (same area repeatedly) | Reference sheet confirms exact dimensions per plot |

#### Phase C: Create .docx with python-docx

Install if needed: `uv pip install python-docx`

```python
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# --- Title ---
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('PROJECT NAME')
run.bold = True; run.font.size = Pt(18)
run.font.color.rgb = RGBColor(0x1a, 0x3a, 0x5c)

# --- Subtitle ---
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub.add_run('CUSTOMER AREA STATEMENT')
run.bold = True; run.font.size = Pt(14)
run.font.color.rgb = RGBColor(0x1a, 0x3a, 0x5c)

# --- Details line ---
details = doc.add_paragraph()
details.alignment = WD_ALIGN_PARAGRAPH.CENTER
details.add_run('Project: ... | Client: ...').font.size = Pt(9)
details.add_run('\\nArchitect: ...').font.size = Pt(9)

# --- Table ---
table = doc.add_table(rows=1, cols=8)
table.style = 'Table Grid'
table.alignment = WD_TABLE_ALIGNMENT.CENTER

# Header rows with dark blue background
hdr_cells = table.rows[0].cells
headers = ['#', 'Plot No.', 'Dimensions (ft & in)', 'Plot Size', 'Facing', 'Corner', 'Shape', 'Survey No.']
for i, h in enumerate(headers):
    p = hdr_cells[i].paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(h)
    run.bold = True; run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), '1a3a5c')
    shading.set(qn('w:val'), 'clear')
    hdr_cells[i]._tc.get_or_add_tcPr().append(shading)

# Data rows with multi-line dimensions
for idx, pno in enumerate(sorted_plot_nos, 1):
    p = plot_data[pno]
    row_cells = table.add_row().cells
    
    # Dimensions as 4-line column
    p2 = row_cells[2].paragraphs[0]
    for di, d in enumerate([f"East   : {p['dim_e_ft']}", f"West  : {p['dim_w_ft']}",
                            f"North : {p['dim_n_ft']}", f"South : {p['dim_s_ft']}"]):
        if di > 0: p2.add_run('\\n')
        p2.add_run(d).font.size = Pt(7)
    
    # Area with sqm in grey
    p3 = row_cells[3].paragraphs[0]
    p3.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p3.add_run(f"{p['area_sft']} sft").font.size = Pt(8)
    p3.add_run('\\n')
    p3.add_run(f"({p['area_sqm']} sqm)").font.size = Pt(7)

    # Alternate row shading
    if idx % 2 == 0:
        for cell in row_cells:
            shading = OxmlElement('w:shd')
            shading.set(qn('w:fill'), 'f2f6fc')
            shading.set(qn('w:val'), 'clear')
            cell._tc.get_or_add_tcPr().append(shading)

# Notes section
doc.add_paragraph()
pn = doc.add_paragraph()
pn.add_run('Notes:').bold = True
for nt in ['• Note 1', '• Note 2']:
    doc.add_paragraph(nt).font.size = Pt(8)

doc.save('PROJECT_Customer_Area_Statement.docx')
```

#### Phase D: Sort Plot Numbers Correctly

Handle combined plot numbers with quotes (`"93"-94`, `127-128-129- "130"`):

```python
def clean_sort_key(x):
    clean = x.replace('"', '').replace(' ', '')
    return int(clean.split('-')[0])

plot_nos_sorted = sorted(plot_data.keys(), key=clean_sort_key)
```

#### Phase E: Upload to Drive

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', service_name='google-draas')
media = MediaFileUpload('/path/to/doc.docx',
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
uploaded = drive.files().create(body={'name': 'name.docx'}, media_body=media,
    fields='id, name, webViewLink').execute()

# Share with the user
drive.permissions().create(
    fileId=uploaded['id'],
    body={'type': 'user', 'role': 'writer', 'emailAddress': 'USER_EMAIL'},
    sendNotificationEmail=False
).execute()
```

### Pitfalls (docx variant)

- **`foregroundColor` must go under `textFormat`** in Sheets API formatting requests. In python-docx, font color is set directly via `run.font.color.rgb = RGBColor(r,g,b)`.
- **Combined plots on master plan ≠ combined in reference sheet**: Plots shown as 79-80, 95-96, 103-104, 121-122 on the plan may be INDIVIDUAL plots in the reference sheet with their own dimensions and areas. Always use the reference sheet's individual entries.
- **Sort key must strip quotes first**: Plot numbers like `"93"-94` or `127-128-129- "130"` need `replace('"', '')` before sorting by numeric prefix.
- **Standard plots share identical dimensions**: A cluster of 1,517.71 Sq.ft plots (30'10" × 49'3") is normal — don't flag as duplicate data.
- **Edge plot data (131-138)**: These may have zero/empty areas on the master plan, but the reference sheet has complete data for them. Always cross-reference.
- **.docx files from Drive API look like Google Docs in the link**: The API returns a `docs.google.com/document/d/...` link even for .docx uploads. The user can download as Word from that page.

## Worked Examples

### Example 1: Ranka Oasis Master Plan — Google Sheet Area Statement (Aug 2026)

- **Project:** Ranka Oasis | **Client:** Sevaganapalli Land Partners
- **Architect:** Ar. Bhuvanesh Krishnan (Finding Form Design Studio)
- **Dwg No:** 04-MP/01 R1 | **Date:** 03-08-26
- **Sheet:** 1 of 1
- **Plots extracted:** 1–138 (118 entries including OSR + Amenity)
- **Standard plot size:** 1,517.71 Sq.ft (~141 Sq.Mtr) — 35+ plots
- **Large plots on Road F:** 2,300–2,870 Sq.ft
- **Combined plots:** 79-80, 82-84, 85-86, 93-94, 95-96, 97-98, 99-100, 101-102, 103-104, 105-106, 107-108, 109-110, 111-112, 113-114-115, 121-122, 123-124, 125-126, 127-128-129-130
- **Edge plots (131-138):** Areas illegible on the plan; reference sheet had complete data
- **OSR:** Open Space Reserve near plots 68-71, 74, 87, 95-102
- **Amenity:** Clubhouse/Pool/Courts area near plots 6-9

### Example 2: Ranka Oasis Master Plan — Customer Area Statement docx (Aug 2026)

When the user asked for a **"Customer Area Statement in word format"** with orientations and dimensions from an architect's reference sheet:

**Reference sheet used:** Sevaganapalli architect's data sheet (155 plot entries with facing, corner, shape, E/W/N/S dimensions in ft & in, areas in sqft)

**Results:**
- 155 individual plot entries (plan showed 118 — combined plots like 79-80 became Plot 79 + Plot 80 from reference)
- Standard plots: 30'10" × 49'3" = 1,517.71 Sq.ft, facing East on Road D or West on Road E
- Corner plots: 2 (SE), 6 (NE), 10 (SW), 21 (NW), 22 (NE), 56 (NE), 63 (SE), 64 (SE), 132 (NE), 133 (NW)
- OSR + Amenity area entries
- Facing directions mapped to road names (East on Road D, West on Road E, North on Road F, etc.)