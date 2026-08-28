# Building Formula-Rich Google Sheets from Extracted PDF Data

## When to Use This

A document (PDF, scan) contains tabular data — fee schedules, rate tables, calculations, cost estimates — and the user wants it in a Google Sheet with the **exact row-by-row layout** and **interlinked formulas** instead of hardcoded values.

## Full Workflow (Bangalore Approvals Session — Reference Implementation)

### Phase 1: Extract Data from PDFs

**For text-based PDFs** (data extracts cleanly with `pdftotext`):

```bash
pdftotext -layout input.pdf /tmp/output.txt
```

Then read the text file. The `-layout` flag preserves column alignment.

**For image-based / scanned PDFs** (WhatsApp scans, photos):

The PDF is an image wrapped in a container. Two approaches:

**A) Ghostscript + vision_analyze (this session's approach):**
```bash
# Convert single page at 150 DPI
gs -dNOPAUSE -dBATCH -sDEVICE=png16m -r150 \
  -sOutputFile=/tmp/page.png input.pdf 2>&1

# Then analyze via vision_analyze with a specific extraction prompt
vision_analyze(image_url="/tmp/page.png",
  question="Extract EVERY row, every cell value, every label...")
```

The 150 DPI produces ~20MB for a large-format page (2492×3538 pts). Use 72 DPI for smaller files if needed. Ghostscript handles iOS Quartz-generated PDFs that `pdftoppm` times out on.

**B) Poppler (when it works — faster, smaller):**
```bash
pdfinfo input.pdf                     # Check page count, dimensions, rotation
pdftoppm -png -r 200 input.pdf /tmp/page
```

**Why ghostscript over pdftoppm for large-format iOS scans:** Some iPhone-scanned PDFs have huge page dimensions (e.g. 2492×3538 pts ≈ 34.6"×49.1"). At 150 DPI that's ~3463×4914 pixels. `pdftoppm` with poppler 25.x can time out (>30s on a 2.4MB PDF) while `gs` processes the same file in ~2s.

### Phase 2: Organize the Data

Build a Python list-of-lists preserving:

1. **Every row exactly as it appears** — including blank separator rows that group sections
2. **Labels match source verbatim** — "S.No.", "Particulars", "Amount (Rs)" stay as-is
3. **Numbers as Python numbers** (not strings) where they'll later be formula inputs

```python
row_data = []
def r(*cells):
    row_data.append(list(cells))

# Blank separator row
r()
# Title row
r("BBMP FEE SCHEDULE — GREATER BANGALORE AUTHORITY")
r()
# Parameter section
r("PROJECT PARAMETERS")
r("Site Area (sqm)", 7232.44, "sqm")
# ... etc
```

### Phase 3: Create the Sheet via Terminal (Not Sandbox)

`build_service()` and `gws_skill_bridge.call()` fail in the `execute_code` sandbox (`ImportError: cannot import name 'gws_fetch_token'`). For complex sheet operations, use the terminal:

```python
# /tmp/build_sheet.py
import os, sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import _load_credentials_direct
from googleapiclient.discovery import build

creds = _load_credentials_direct(
    os.environ.get('HERMES_SESSION_USER_ID', '[REDACTED-TID]'),
    'google-draas'
)
sheets = build('sheets', 'v4', credentials=creds)
drive = build('drive', 'v3', credentials=creds)
```

Run from the Hermes venv with the session user ID:
```bash
cd /opt/hermes && HERMES_SESSION_USER_ID=[REDACTED-TID] python3 /tmp/build_sheet.py
```

### Phase 4: Write Values, Then Formulas (Two-Pass Pattern)

**Pass 1 — RAW values** (all structural data, labels, numbers):
```python
sheets.spreadsheets().values().update(
    spreadsheetId=SID, range="'Sheet1'!A1:D40",
    valueInputOption='RAW',  # <-- treats "=SUM(...)" as text, not formula
    body={"values": row_data}
).execute()
```

**Pass 2 — Formulas** one per `update()` call, using `USER_ENTERED`:
```python
# Parameter cell reference: B5 = Site Area, B7 = GV, B11 = Basic FAR
formulas = [
    {"range": "'Sheet1'!B12", "values": [["=B11*0.4"]]},     # PFAR
    {"range": "'Sheet1'!B13", "values": [["=B11*0.2"]]},     # TDR
    {"range": "'Sheet1'!B15", "values": [["=SUM(B11:B14)"]]}, # Total FAR
    {"range": "'Sheet1'!B20", "values": [["=B18*$B$19*$B$7"]]}, # PFAR charges
]
for f in formulas:
    sheets.spreadsheets().values().update(
        spreadsheetId=SID, range=f["range"],
        valueInputOption='USER_ENTERED',  # <-- evaluates as formulas
        body={"values": f["values"]}
    ).execute()
```

### Phase 5: Apply Formatting

Use `batchUpdate` for bold headers, column widths, number formats:
```python
reqs = []
# Bold title rows
reqs.append({
    'repeatCell': {
        'range': {'sheetId': sheet_id, 'startRowIndex': 1, 'endRowIndex': 2,
                  'startColumnIndex': 0, 'endColumnIndex': 4},
        'cell': {'userEnteredFormat': {'textFormat': {'bold': True}}},
        'fields': 'userEnteredFormat.textFormat.bold'
    }
})
# Number format for value columns
reqs.append({
    'repeatCell': {
        'range': {'sheetId': sheet_id, 'startRowIndex': 4, 'endRowIndex': 40,
                  'startColumnIndex': 1, 'endColumnIndex': 2},
        'cell': {'userEnteredFormat': {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.00'}}},
        'fields': 'userEnteredFormat.numberFormat'
    }
})
# Column widths
reqs.append({
    'updateDimensionProperties': {
        'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1},
        'properties': {'pixelSize': 350},
        'fields': 'pixelSize'
    }
})
sheets.spreadsheets().batchUpdate(
    spreadsheetId=SID, body={'requests': reqs}
).execute()
```

### Formula Chaining Pattern

Structure the sheet so formulas chain from parameter cells through intermediates to totals:

```
Row 5:  B5 = 7232.44     (Site Area — parameter)
Row 6:  B6 = 2.5         (Basic FAR — parameter)
Row 7:  B7 = 232560      (Guidance Value — parameter)
...
Row 11: B11 = 2.5        (Basic FAR — duped for reference)
Row 12: B12 = B11*0.4    (PFAR = 1.0)
Row 13: B13 = B11*0.2    (TDR = 0.5)
Row 15: B15 = SUM(B11:B14)  (Total FAR = 4.5)
...
Row 20: B20 = B18*$B$19*$B$7  (PFAR charges — references local + absolute)
Row 21: B21 = B20/10000000     (PFAR in Crores)
Row 23: B23 = B21*(1+$B$22)   (Total incl. adhoc %)
```

Use `$B$5` (absolute column+row) for cells that shouldn't shift. Use `B5` (relative) for cells within the same calculation block that should auto-adjust if copied.

### Pitfalls

1. **`_load_credentials_direct` needs HERMES_SESSION_USER_ID:** Must be set in the environment. Default for Nishant is `[REDACTED-TID]`. Without it, the vault lookup returns the wrong token or raises.
2. **Two-pass (RAW → USER_ENTERED) is mandatory:** Writing formulas with `valueInputOption='RAW'` turns them into literal text strings (e.g. `=B11*0.4` displays as text, not calculated). Writing values with `USER_ENTERED` that are meant to be labels fails if the label starts with `=` — it tries to interpret as formula.
3. **Separate `update()` calls per formula:** The Sheets API does not reliably handle mixed formula/value writes in a single range. Batch the value write, then iterate formula writes.
4. **Ghostscript vs pdftoppm for iOS scans:** `pdftoppm` literally timed out (30s+) on a 2.4MB iOS-generated PDF while `gs` processed it in 2s. Use `pdfinfo` to check the PDF Producer field — if it says `iOS Version ... Quartz PDFContext`, prefer ghostscript.
5. **`uv pip install` in terminal must find the right venv:** The Hermes venv is at `/opt/hermes/.venv/`. Commands run from `/opt/hermes` resolve it; other directories don't. Always `cd /opt/hermes` first.

### OCR Cross-Validation: When the Scan Lies

`vision_analyze` OCR on dense fee-schedule tables routinely mis-reads numbers — transposes digits, merges adjacent column values, drops decimal places. **Never trust OCR values at face value when they're part of a known calculation chain.** Cross-validate every figure against the surrounding formulas:

**Case from the BBMP Fee Schedule session:**

```
OCR read: Site Betterment = 7,232.44 × 232,560 = 8,409,881
But:      7,232.44 × 232,560 actually = 1,681,976,246  (200× off!)
```

The OCR placed `232,560.00` in the Rate column for the Site row — but that's the GV from the parameter header, not the rate for that line item. The actual rate was `0.5%` of GV (1,163 /sqm), yielding `8,409,881`. The OCR copied the wrong value from the header area.

**Workflow for tabular OCR:**

1. **Extract every row** from `vision_analyze` output into a structured table
2. **Check each calculated value** by running the formula manually: `value = base × rate × factor`
3. **If a row's OCR value doesn't match its formula**, look for what the OCR actually captured:
   - Did it pull a number from an adjacent column?  
   - Did it copy a parameter value from the header into the data row?
   - Is the decimal point placed wrong (e.g. 232560 vs 0.5%)?
4. **Reconstruct the correct rate** by solving: `rate = ocr_value / (base × factor)`. If the result is a round number (0.5%, 10%, 182, etc.), it's the intended value.
5. **Use the corrected value**, not the raw OCR output.

**Pattern for the BBMP case — Betterment Levy rates:**

| Row | OCR Rate Read | Correct Rate | Why |
|-----|--------------|--------------|-----|
| Site | `232,560.00` (GV) | `GV × 0.5%` = 1,163 | Rate is 0.5% of GV, not full GV |
| Building | `100.00` | `100.00` | Confirmed: BUA × 100 = 1,100,000 |
| BWSSB | `10%` | `10%` of site betterment | Confirmed: 8,409,881 × 10% = 840,988 |
| BDA Ring Road | `10%` | `10%` of site betterment | Confirmed |
| Slum Board | `5%` | `5%` of site betterment | Confirmed |
| MRT | `50%` | `50%` of site betterment | Confirmed |

**When the grand total also needs checking:**
Sum every section subtotal with a calculator (or Python `sum()`) and compare against the OCR's "TOTAL" row. If they mismatch by more than a rounding rupee, one of the OCR values is wrong — iterate.
