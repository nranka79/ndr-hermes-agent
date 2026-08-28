# RERA Batch Date Update — Project End / Possession Date

Recurring workflow when the project end date (RERA registration) or possession date in documents needs to be revised across all RERA documents. Common triggers: registration delay, construction extension, correction of prior date.

## Documents That Contain the Project End Date

| Document | Where Date Appears | Format | Update Method |
|----------|-------------------|--------|--------------|
| **Project Details Letter** (docx) | End date line: `31-07-2029 (including time for obtaining OC...)` | `DD-MM-YYYY` | Raw XML find-replace in word/document.xml |
| **Work Order** (docx) | Completion line: `Completion: 31-07-2029 (24 months from commencement)` | `DD-MM-YYYY` | Raw XML find-replace in word/document.xml |
| **Allotment Letter** (Google Doc) | Clause 7 (Possession): `on or before 10.12.2027` | `DD.MM.YYYY` | Docs API `replaceAllText` |
| **Agreement of Sale Proforma** (docx) | Clause 7.1: `in place on 10.12.2027` | `DD.MM.YYYY` | Raw XML find-replace in word/document.xml |
| **BANK AFFIDAVIT** (docx) | Project end date field | `DD-MM-YYYY` | Raw XML find-replace in word/document.xml |
| **FORM B** (docx) | Project end date / validity | `DD-MM-YYYY` or `DD.MM.YYYY` | Raw XML find-replace in word/document.xml |
| **JDA AFFIDAVIT** (docx) | Project end date | `DD-MM-YYYY` or `DD.MM.YYYY` | Raw XML find-replace in word/document.xml |
| **SIS Spreadsheet** (Google Sheet) | `Project details` tab, Cell C12 (PROJECT END DATE) | `DD-MM-YYYY` | Sheets API `values().update()` |

## Documents Without Specific Dates (skip)

- Section 3(1) Affidavit (no date field — just fresh copy)
- No Mortgage Affidavit (no date field — just fresh copy)
- non-litigation Affidavit (no date field — just fresh copy)
- Board Resolution (board meeting date only — unrelated to project end)
- Agreement of Sale blank proforma (template with blank placeholders)
- Allotment Letter blank model form (template with blank placeholders)
- Form-1 CA, Form-2 Architect, Form-3 Engineer (certificate dates — not project end)

## Workflow

### Step 1: Scan the Folder

List all files in `RANKA AMBER - RERA DOCUMENTS` or equivalent project folder. Identify:
- .docx files (Project Details Letter, Work Order, Agreement of Sale, affidavits)
- Google Docs (Allotment Letter, any editable versions)
- Google Sheets (SIS spreadsheet)

Check each for the old date. The date may appear in multiple formats:
- `10.12.2027` (dots in Google Docs and some docx)
- `10-12-2027` (hyphens in other docx)
- `10/12/2027` (slashes in Sheets)
- `10 December 2027` (text in some letters)

### Step 2: Create Output Folder

```python
target_folder = drive.files().create(
    body={
        'name': 'Ranka Amber - Updated Documents',
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': ['PARENT_FOLDER_ID']
    },
    fields='id'
).execute()['id']
```

### Step 3: Update Each Document Type

#### Google Docs (Allotment Letter)

Use Docs API `replaceAllText`:

```python
docs = build_service('docs', 'v1')
docs.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': [{
        'replaceAllText': {
            'containsText': {'text': '10.12.2027', 'matchCase': True},
            'replaceText': '31.07.2029'
        }
    }]}
).execute()
```

**Pitfall:** `replaceAllText` counts occurrences at the text-run level. A single visible date may be split across multiple runs, so the API may report more occurrences changed than you expect. Verify afterward by re-reading the doc.

After updating, copy the doc to the output folder:

```python
drive.files().copy(
    fileId=doc_id,
    body={'name': 'Allotment Letter - Updated', 'parents': [target_folder]}
).execute()
```

#### DOCX Files (Project Details Letter, Work Order, Agreement of Sale, Affidavits)

Use raw XML manipulation via zipfile:

```python
import zipfile, io, re
from googleapiclient.http import MediaIoBaseUpload

# Download
request = drive.files().get_media(fileId=file_id)
content = request.execute()

# Read XML
z = zipfile.ZipFile(io.BytesIO(content))
doc_xml = z.read('word/document.xml').decode('utf-8')

# Replace date — check for all format variants
old_date_patterns = ['10.12.2027', '10-12-2027', '10/12/2027']
for pattern in old_date_patterns:
    doc_xml = doc_xml.replace(pattern, '31.07.2029')

# Rebuild zip with new XML
output = io.BytesIO()
with zipfile.ZipFile(io.BytesIO(content), 'r') as zin:
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == 'word/document.xml':
                data = doc_xml.encode('utf-8')
            zout.writestr(item, data)

# Upload as new file
media = MediaIoBaseUpload(
    io.BytesIO(output.getvalue()),
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True
)
drive.files().create(
    body={'name': new_name, 'parents': [target_folder]},
    media_body=media,
    fields='id, name, webViewLink'
).execute()
```

**Pitfall:** The old date format in the docx XML may differ from the visible text. Check the actual XML to confirm the exact string. Common variants:
- `10.12.2027` (with dots — used in Google Docs and some docx)
- `10-12-2027` (with hyphens — used in Project Details Letter, Work Order)
- `10/12/2027` (with slashes — rarely in docx)

Always scan ALL variants, not just one.

#### Google Sheets (SIS Spreadsheet)

```python
sheets.spreadsheets().values().update(
    spreadsheetId=sheet_id,
    range='Project details!C12',
    valueInputOption='USER_ENTERED',
    body={'values': [['31-07-2029']]}
).execute()
```

### Step 4: Subfolder for Affidavits

If affidavits exist in a subfolder, recreate that structure in the output folder:

```python
affidavit_folder = drive.files().create(
    body={'name': 'Affidavits', 'mimeType': 'application/vnd.google-apps.folder', 'parents': [target_folder]},
    fields='id'
).execute()['id']
```

Then upload updated affidavit docx files to this subfolder using the same zipfile XML replacement technique.

### Step 5: Verify

After all updates, verify the output folder contents:

```python
results = drive.files().list(
    q=f"'{target_folder}' in parents and trashed=false",
    fields='files(id, name, mimeType)'
).execute()
for f in results.get('files', []):
    print(f"{f['name']}")
```

For docx files, spot-check that the old date is gone and the new date appears:

```python
with zipfile.ZipFile(io.BytesIO(content)) as z:
    xml = z.read('word/document.xml').decode('utf-8')
print(f"Old date remaining: {'10.12.2027' in xml}")
print(f"New date present: {'31.07.2029' in xml}")
```

## Schedules Sheet — Proportional Date Spreading

When the project end date changes, the **Schedules sheet** (construction milestones in rows 7-9 Sub Structure, 17-23 Super Structure, 28-34 Finishing) also needs its dates aligned. Unlike the `Project details!C12` cell which is a single-date update, the Schedules sheet requires **proportional spreading** of all milestone start/end dates.

### Approach

1. Identify the earliest start date across all schedule rows (the anchor).
2. Identify the latest end date (the current project end).
3. Calculate the scaling ratio: `(new_end - first_start) / (old_last_end - first_start)`.
4. For each date cell, compute progress from 0.0 (first start) to 1.0 (last end), then project onto the new timeline.

```python
from datetime import datetime, timedelta

# After parsing all dates from the sheet:
first_start = min(all_start_dates)
old_last_end = max(all_end_dates)
current_span = (old_last_end - first_start).days

new_end = datetime(2028, 12, 31)
new_span = (new_end - first_start).days
ratio = new_span / current_span

for each date cell:
    elapsed = (cell_date - first_start).days
    progress = elapsed / current_span
    new_date = first_start + timedelta(days=int(progress * new_span))
```

### Updating the Sheet

```python
sheets.spreadsheets().values().batchUpdate(
    spreadsheetId=sheet_id,
    body={
        'valueInputOption': 'USER_ENTERED',
        'data': [{
            'range': f'Schedules!E{row}',  # start date column
            'values': [[new_start_value]]
        }, {
            'range': f'Schedules!F{row}',  # end date column  
            'values': [[new_end_value]]
        }]
    }
).execute()
```

**⚠️ Important cell reference — column offset pitfall:**  
- 0-indexed column 4 = Excel column **E** = `chr(65+4)` = `chr(69)` = `'E'`  
- 0-indexed column 5 = Excel column **F** = `chr(65+5)` = `chr(70)` = `'F'`

**Wrong:** `chr(64+4)` = `'D'` (off by one — updates wrong column silently)  
**Right:** `chr(65+col)` where col is 0-indexed (A=0, B=1, ..., Z=25)

For 1-indexed (A=1): `chr(64+col_1indexed)` → `chr(64+5)` = `'E'` ✓

### Row Reference

| Rows | Section | Columns with dates |
|------|---------|-------------------|
| 7, 8, 9 | Sub-structure | E (start), F (end) |
| 17, 18, 19, 20, 21, 22, 23 | Super-structure | E (start), F (end) |
| 28, 29, 31, 33, 34 | Finishing | E (start), F (end) |

## Common Format Variants

| Old (example) | New (example) | Appears In |
|---------------|---------------|------------|
| `10.12.2027` | `31.07.2029` | Allotment Letter Google Doc, Agreement of Sale docx |
| `10-12-2027` | `31-07-2029` | Project Details Letter docx, Work Order docx, affidavits |
| `10/12/2027` | `31/07/2029` | SIS Spreadsheet Project details cell |
| `7/10/2026` | (scaled) | Schedules sheet — uses **mixed formats** (see pitfall) |

Always check ALL formats across ALL documents. Run a multi-format replace for safety.

## Area Details Sheet — Unit Conversion (sqft → sqm)

When a user asks to convert area columns from sq.ft to sq.mtr in the Area details sheet (the unit inventory tab of the SIS spreadsheet):

### Columns to convert

| Column | Header | Content |
|--------|--------|---------|
| G | RERA Carpet Area | Per-unit carpet area — convert from sqft to sqm |
| H | Exclusive Common Area | Per-unit balcony/exclusive area |
| I | Common Area to Association | Per-unit share of common areas |
| J | Undivided Share of Land | Per-unit land share (in sqft → sqm) |
| L | RERA CARPET | Original RERA carpet in sqft → sqm (may become redundant) |

**Don't convert:** Column K (parking count — integer count, not area).

### Conversion rate

```
1 sq.ft = 0.092903 sq.mtr
```

### Workflow

```python
SQFT_TO_SQM = 0.092903

# 1. Update headers to show "(Sq.mtr)" suffix
header_map = {
    7: 'RERA Carpet Area (Sq.mtr)',
    8: 'Exclusive Common Area (Sq.mtr)',
    9: 'Common Area Alloted To Association (Sq.mtr)',
    11: 'RERA Carpet (Sq.mtr)'
}

for col_idx, header in header_map.items():
    col_letter = chr(65 + col_idx)  # 0-indexed → A=65
    batch_data.append({
        'range': f'Area details!{col_letter}4',
        'values': [[header]]
    })

# 2. Convert data rows (rows 5-24, 20 units)
for i in range(20):  # 20 units
    row_num = i + 5
    for col_idx in [7, 8, 9, 11]:
        sqft = read_cell_value(row_num, col_idx)
        sqm = round(sqft * SQFT_TO_SQM, 2)
        col_letter = chr(65 + col_idx)
        batch_data.append({
            'range': f'Area details!{col_letter}{row_num}',
            'values': [[sqm]]
        })

# 3. Add totals row (Row 25)
sheets.spreadsheets().values().batchUpdate(
    spreadsheetId=sheet_id,
    body={
        'valueInputOption': 'USER_ENTERED',
        'data': [{
            'range': 'Area details!A25:K25',
            'values': [['', '', 'Total', '', '', '',
                round(total_rera_sqm, 2),
                total_exclusive_common_sqm,
                total_common_area_sqm,
                round(total_land_share_sqm, 2),
                total_parking
            ]]
        }]
    }
).execute()
```

### Pitfalls

1. **Column offset in batchUpdate** — When building cell ranges, remember `chr(65 + col_index)` (A=65 in ASCII), NOT `chr(64 + col_index)`. See `gws-automation` skill → `references/sheets-batchupdate-pitfalls.md`.

2. **Row 25 already has data** — The first empty row after the 20 unit rows may already contain stray cells. Overwrite rather than append.

3. **"Write Yes If The Required Details Are Correct" note** — This text in row 28 should be preserved. The totals row goes in row 25.

4. **Column L may become redundant** — After conversion, L has the same values as G. Consider removing L or keeping as cross-check.

## Pitfalls

1. **Incorrect date format in XML** — The docx XML may have `10.12.2027` (dots) while the Sheet has `10/12/2027` (slashes). Running only one find-replace misses the others.

2. **Partial replacement** — If the date appears in multiple paragraphs (e.g., clause 7.1 and clause footer), only one may get replaced if the text differs slightly (e.g., extra space). Run a verification scan.

3. **Google Doc replaceAllText over-counts** — The API reports occurrences at the text-run level, not visual instances. Verify by re-reading the document, not by trusting the occurrence count.

4. **Token refresh errors in stderr** — During this workflow, you may see `Google token refresh failed for X (account: google): Failed to store Google credentials in vault... Unauthorized: invalid vault secret` in stderr. Operations still succeed because the cached access token continues to work. Do not treat this as a blocker unless you get an actual HTTP 401.

5. **File naming** — Use descriptive names with `- Updated` suffix. Examples:
   - `Allotment Letter - Updated`
   - `20260608 Ranka Amber Agreement of Sale Proforma - Updated.docx`
   - `BANK AFFIDAVIT - Updated.docx`

6. **Multiple Agreement of Sale versions** — The project folder may have multiple versions:
   - `20260608 Ranka Amber Agreement of Sale Proforma` (original template)
   - `20260608 Ranka Amber Agreement of Sale Proforma - CORRECTED.docx` (previously corrected)
   - `Ranka Amber - Agreement of Sale Proforma.docx` (blank template)
   - `Agreement of Sale Proforma.docx` (blank template)
   Update the ones that have specific dates. Skip blank templates.

7. **File deduplication** — Users prefer keeping only **one version per document type** in the output folder. If multiple versions exist (e.g., `- Updated` and `- CORRECTED - Updated`), ask or remove the redundant one after confirming which to keep. Default: keep the main `- Updated` version.

8. **Mixed date formats in Schedules sheet** — The Schedules sheet uses a confusing mix of `mm/dd/yyyy` and `dd/mm/yyyy` within the same sheet. Example:
   - `"07/30/2026"` → Jul 30, 2026 (mm/dd, since day=30 > month=7)
   - `"20/8/2026"` → Aug 20, 2026 (dd/mm, since day=20 > month=8)
   - `"1/8/2026"` → ambiguous (Jan 8 or Aug 1? Context: this is Foundation footing starting after Earth work ends Jul 30, so Aug 1 = dd/mm)
   - `"08/10/2026"` → Aug 10, 2026 or Oct 8, 2026? Sequence context decides.
   
   **Parsing strategy for the Schedules sheet:**
   - If part1 > 12: `dd/mm/yyyy` (day is first, month can't be >12)
   - If part2 > 12: `mm/dd/yyyy` (day is second)
   - If both ≤ 12: use sequence context — check which interpretation makes the date fall after the previous milestone's end date. When in doubt, the sheet alternates between both formats even within the same section; use manual date assignments for reliable results rather than a generic parser.
   
   The safest approach: manually write a dict of `{(row, col_letter): datetime}` for every date cell rather than relying on a parser for the schedules sheet.
