# Google Sheets API: Reading and Writing

## Reading — values endpoint

**Single cell:**
```
GET /v4/spreadsheets/{sheetId}/values/{sheetName}!{col}{row}?valueRenderOption=FORMATTED_VALUE
```

**Range:**
```
GET /v4/spreadsheets/{sheetId}/values/{sheetName}!{startCol}{startRow}:{endCol}{endRow}?valueRenderOption=FORMATTED_VALUE
```

- `sheetName` must be URL-encoded (`urllib.parse.quote("Sheet Name")`)
- Sheet title with `.csv` extension requires the full name, e.g. `"NDR DRAAS Google contacts.csv"`

---

## Writing — batchUpdate (NOT values.update)

**The `values.update` PUT endpoint returns 404** when targeting a single cell or small range on this spreadsheet. Use `spreadsheets/:batchUpdate` instead.

```python
url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}:batchUpdate"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

body = {
    "requests": [
        {
            "updateCells": {
                "rows": [{"values": [[{"userEnteredValue": {"stringValue": "Wife"}}]]}],
                "fields": "userEnteredValue",
                "start": {
                    "sheetId": 1196451362,          # numeric, from spreadsheet metadata
                    "rowIndex": 2986,               # 0-indexed (row 2987 = index 2986)
                    "columnIndex": 75                # 0-indexed (column BX = index 75)
                }
            }
        }
    ]
}
req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
```

**Getting `sheetId`** (required, not optional):
```python
url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}?fields=properties.title,sheets.properties"
# response["sheets"][i]["properties"]["sheetId"]  — numeric integer
# response["sheets"][i]["properties"]["title"]    — string sheet name
```

**Key differences from values.update:**
- Uses `sheetId` (numeric), not `sheetName` (string)
- `rowIndex` and `columnIndex` are 0-indexed
- `rows[].values[][]` is a 2D array of cell objects, not raw values
- `fields` uses `userEnteredValue` to write values (other field types available for formatting)

---

## Finding a sheet by name

```python
sheet_name = "NDR DRAAS Google contacts.csv"
matched = [s for s in sheets if s["properties"]["title"] == sheet_name]
sheet_id_num = matched[0]["properties"]["sheetId"]
```

---

### Google Drive file naming convention (NDR user)

**Pattern:** `YYYYMMDD Entity Name Land Proposal Name [Few Words describing doc and Parties Involved, if applicable]`

**Examples:**
- `20260107 TerraGreens Alipur 300 [FW Agreement – Syed Zamin Raza].pdf`
- `20260107 TerraGreens Alipur 300 [MOU – Syed Zamin Raza].pdf`
- `20250502 Degree Realty Koramangala [Sale Agreement – Buyer Name].pdf`

**Key points:**
- Date comes first, YYYYMMDD format
- Entity name first (e.g. TerraGreens, Degree Realty)
- Land proposal / location next (e.g. Alipur 300, Koramangala)
- Description + parties in brackets last
- Hyphen/dash separators between major sections; em-dash inside brackets for sub-clauses

## A1 Notation vs Python Array Indexing — Column Offset Pitfall

**Confirmed trap (June 2026):** When using A1 notation to write to specific columns, the column letter-to-index mapping is 1-based (A=1, B=2, ..., Z=26, AA=27). But Python array indices from a Sheets `values().get()` are 0-based (index 0 = A, index 25 = Z, index 26 = AA).

**Wrong calculation that caused data to shift by 1 column:**
```python
# ❌ BROKEN: treating array index 39 as "AM" (A1 for 39th column)
# Index 39 = 40th column = AN, NOT AM
```

**Correct mapping — array index → A1 column:**

| Data | Array Index | A1 Column |
|------|-------------|-----------|
| Address 1 - Label | 39 (0-based) | **AN** |
| Address 1 - Formatted | 40 | **AO** |
| Address 1 - Street | 41 | **AP** |
| Address 1 - City | 42 | **AQ** |
| Address 1 - PO Box | 43 | **AR** |
| Address 1 - Region | 44 | **AS** |
| Address 1 - Postal Code | 45 | **AT** |
| Address 1 - Country | 46 | **AU** |

**Helper to convert Python index to A1 letter:**
```python
def col_letter(py_index):
    """0-based Python index -> A1 column letter (A=0, B=1, ..., Z=25, AA=26)"""
    result = ""
    n = py_index
    while True:
        result = chr(n % 26 + 65) + result
        n = n // 26 - 1
        if n < 0:
            break
    return result
```

**To verify before writing:** always dump the header row first and check what the sheet actually has at the target index. If the data lands in the wrong column, the most likely cause is off-by-1 in A1 calculation. Re-read the current state and write again with the corrected range.
