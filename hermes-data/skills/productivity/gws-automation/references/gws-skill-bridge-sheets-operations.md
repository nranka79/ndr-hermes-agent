# gws_skill_bridge Sheets Operations — kwarg/arg-name mismatch trap

**Status:** Working pattern, confirmed Jul 2026.

## What the bridge does

`tools.gws_skill_bridge.call(operation, **kwargs)` creates a `SimpleNamespace` from kwargs, then passes it to the skill function which reads attributes like `args.sheet_id`, `args.range`, `args.values`. The parameter names differ from both the Google Sheets v4 API and what you'd intuitively guess.

## Operations & the kwarg names that ACTUALLY work

| Operation | Working kwargs | Notes |
|---|---|---|
| `sheets_create` | `title=...`, `sheet_name=...` | `title` = spreadsheet title. `sheet_name` = first sheet tab name. Returns JSON with `spreadsheetId` and `spreadsheetUrl`. |
| `sheets_get` | `sheet_id=...`, `range=...` | NOT `spreadsheet_id` or `spreadsheetId`. `range` = e.g. `"Sheet1!A:F"`. Returns JSON array of row arrays. |
| `sheets_update` | `sheet_id=...`, `range=...`, `values=...` | `values` must be a **JSON string** (the bridge does `json.loads(args.values)`). Pass `json.dumps(data)` where data is a list of lists. Uses `USER_ENTERED` mode automatically — URLs become clickable links. |
| `sheets_append` | `sheet_id=...`, `range=...`, `values=...` | Same pattern as update but appends rows. |

## What bit me (silent failures → AttributeError)

- **First call used `spreadsheet_id`** → raised `AttributeError: ... has no attribute 'sheet_id'`. The skill reads `args.sheet_id`.
- **First call used `spreadsheetId`** → same error.
- **For `sheets_update`, first call passed a Python list as `values`** → crashed silently because the bridge expects a JSON string and calls `json.loads()` on it. Pass `values=json.dumps(your_data)`.

## Working recipes

### Create a new spreadsheet

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_skill_bridge import call

result = call("sheets_create", service_name="google-draas",
              title="My Spreadsheet Title",
              sheet_name="Checklist")
# Returns: {"status": "created", "spreadsheetId": "...", "title": "...", "spreadsheetUrl": "..."}
```

### Read sheet data

```python
import json
result = call("sheets_get", service_name="google-draas",
              sheet_id="SPREADSHEET_ID",
              range="Checklist!A:F")
data = json.loads(result)  # list of row lists
```

### Write/overwrite data (with URLs that become clickable links)

```python
import json

header = ["Sl.No", "Description", "Status", "Link"]
rows = [
    ["1", "Sale deed dated 21.05.1974", "Available", "https://drive.google.com/file/d/.../view"],
    ["2", "Sale deed dated 28.10.1974", "Available", "https://drive.google.com/file/d/.../view"],
]

# values must be a JSON string, not a Python list
result = call("sheets_update", service_name="google-draas",
              sheet_id="SPREADSHEET_ID",
              range="Checklist!A1:D3",
              values=json.dumps([header] + rows))
# Returns: {"updatedCells": 12, "updatedRange": "Checklist!A1:D3"}
```

### Append rows (for incremental updates)

```python
result = call("sheets_append", service_name="google-draas",
              sheet_id="SPREADSHEET_ID",
              range="Checklist!A:D",
              values=json.dispatch(new_rows))
```

## Pitfalls

- **`values` must be a JSON string**, not a Python list. The bridge calls `json.loads(args.values)` on whatever you pass. If you pass a list, `json.loads` will fail or produce unexpected results.
- **`USER_ENTERED` mode is hard-coded** in the bridge for `sheets_update`. This means Google Sheets will interpret dates, times, and formulas. For raw text, prefix with a single quote (`'`) if needed, or escape date-like strings. For URLs, USER_ENTERED is actually beneficial — it auto-converts them to clickable hyperlinks.
- **The spreadsheet is created at Drive root** by default. If you need it in a specific folder, use `drive_get` to get its current parents, then move it via the raw Drive API with `addParents`/`removeParents` (see `gws-skill-bridge-drive-operations.md` → "Moving files between folders").
- **`sheets_create` returns the spreadsheet URL** — use the `spreadsheetUrl` field to send to the user, not the `spreadsheetId`.
- **No native formatting support** via the bridge. For bold headers, column widths, or merged cells, use the raw Sheets API with `batchUpdate()`.
- **`service_name` defaults to `"google-draas"`** — pass explicitly for multi-account setups.
- **Output is always JSON on stdout** — `call()` returns a string. Parse with `json.loads()`.
