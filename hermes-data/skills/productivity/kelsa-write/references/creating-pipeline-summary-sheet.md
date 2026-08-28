# Creating a Pipeline Summary Google Sheet

A recurring DRAAS workflow: after bulk-updating leads in Kelsa, Bharat requests a **pipeline summary in worksheet/table format** — a multi-tab Google Sheet showing prospects by stage (SSV, Warm, Hot, PSC) with conversion potential.

## Trigger

User says: "give me a summary in worksheet/table format", "create a table format in a worksheet", "show me the prospects where are the possibilities", or after completing a bulk update asks for a summary of what was done.

## Prerequisites

- Kelsa MCP access (`get_stats`, `search_leads` by stage with date filter)
- Google Sheets API access via `tools.gws_auth.build_service('sheets', 'v4', service_name='google-draas')` — this works from `execute_code()`
- Spreadsheet ID for the newly created sheet

## Workflow

### 1. Get Pipeline Stats

```python
from tools.gws_auth import build_service
kelsa_call_tool("get_stats", {"pipeline_id": 10, "group_by": "stage"})
# Returns: SSV: 28, Warm: 88, Hot: 101, PSC: 19, Cold: 1625, etc.
```

### 2. Get Detailed Lead Lists by Stage

Filter by today's date to show what changed:

```python
# Leads updated today
kelsa_call_tool("search_leads", {
    "pipeline_id": 10,
    "query": "cf_updated_at>=2026-08-28;stage:SSV",
    "sort": "updated_at", "order": "desc", "per_page": 100
})
```

### 3. Create the Google Sheet

```python
sheets = build_service('sheets', 'v4', service_name='google-draas')

req = {
    'properties': {'title': 'Pipeline Summary - 28 Aug 2026'},
    'sheets': [
        {'properties': {'title': 'Pipeline Overview'}},
        {'properties': {'title': "Today's Updates"}},
        {'properties': {'title': 'SSV Leads (Site Visits)'}},
        {'properties': {'title': 'Warm Leads (New - 17)'}},
        {'properties': {'title': 'Hot Leads (101)'}}
    ]
}
spreadsheet = sheets.spreadsheets().create(body=req).execute()
spreadsheet_id = spreadsheet['spreadsheetId']
```

**⚠️ HTTP 503 transient error:** On first call the Sheets API may return `HttpError 503 (The service is currently unavailable)`. Retry with exponential backoff:
```python
import time
for attempt in range(3):
    try:
        spreadsheet = sheets.spreadsheets().create(body=req).execute()
        break
    except Exception as e:
        if attempt < 2: time.sleep(3)
        else: raise
```

### 4. Write Data to Each Tab

**Simple data (no special chars in sheet name):**
```python
body = {'range': 'Pipeline Overview!A1:D16', 'values': data_rows, 'majorDimension': 'ROWS'}
sheets.spreadsheets().values().update(
    spreadsheetId=sid, range='Pipeline Overview!A1:D16',
    valueInputOption='USER_ENTERED', body=body
).execute()
```

**⚠️ APOSTROPHE IN SHEET NAME PITFALL (critical):** Sheet names with apostrophes (`Today's Updates`) cannot be addressed with A1 notation via `values().update()` — the API returns `400 Unable to parse range`. Even escaping with single quotes fails (`'Today''s Updates'` is rejected). 

**Fix — use `batchUpdate` + `updateCells` with numeric sheet ID:**
```python
# Find the numeric sheet ID
sheet_meta = sheets.spreadsheets().get(spreadsheetId=sid).execute()
today_sid = None
for s in sheet_meta['sheets']:
    if "Today" in s['properties']['title']:
        today_sid = s['properties']['sheetId']
        break

# Build rows for batchUpdate
rows = []
for row_data in updates_data:
    cells = [{'userEnteredValue': {'stringValue': str(v) if v is not None else ''}} for v in row_data]
    rows.append({'values': cells})

request = {
    'requests': [{
        'updateCells': {
            'rows': rows,
            'fields': 'userEnteredValue',
            'start': {'sheetId': today_sid, 'rowIndex': 0, 'columnIndex': 0}
        }
    }]
}
sheets.spreadsheets().batchUpdate(spreadsheetId=sid, body=request).execute()
```

This approach also works for ANY sheet name with special characters, not just apostrophes.

### 5. Apply Formatting

Bold headers, section headers, and gray backgrounds via `batchUpdate` with `repeatCell`:

```python
requests = [{
    'repeatCell': {
        'range': {'sheetId': sid, 'startRowIndex': 0, 'endRowIndex': 1},
        'cell': {'userEnteredFormat': {'textFormat': {'bold': True}}},
        'fields': 'userEnteredFormat.textFormat.bold'
    }
},
{
    'repeatCell': {
        'range': {'sheetId': sid, 'startRowIndex': 10, 'endRowIndex': 11},
        'cell': {'userEnteredFormat': {'textFormat': {'bold': True, 'fontSize': 12}}},
        'fields': 'userEnteredFormat.textFormat'
    }
}]
sheets.spreadsheets().batchUpdate(spreadsheetId=sid, body={'requests': requests}).execute()
```

### 6. Verify and Share

Return the spreadsheet URL from step 3 to the user:
```python
# From the create response:
spreadsheet['spreadsheetUrl']
# e.g. "https://docs.google.com/spreadsheets/d/16LisqgwsTq5vg5AGUWHEpOOUwJBxNOXfixNwBkMMI0I/edit"
```

## Suggested Tab Layout

| Tab | Content | Data Source |
|---|---|---|
| Pipeline Overview | Stage-wise counts + today's update summary (what was done, how many moved to each stage) | `get_stats` + manual |
| Today's Updates | Date-stamped activity log: calls made, stage moves, notes added | Manual from session work |
| SSV Leads (Site Visits) | All 28 SSV leads — name, phone, SV date, assigned to, notable remarks | `search_leads(stage:SSV)` |
| Warm Leads (New - N) | The N leads moved (e.g. Cold→Warm) today — name, phone, previous stage, current stage | `search_leads(stage:Warm)` filtered by date |
| Hot Leads | All hot leads — name, phone, assigned to, last updated | `search_leads(stage:Hot)` |

## Pitfalls

- **API 503 on create** — Sheets API is eventually consistent. Retry with 3s backoff. Same retry pattern works for batchUpdate on large sheets.
- **Apostrophe in sheet name blocks `values().update()`** — always use `batchUpdate` + `updateCells` for sheets with special characters in names. Pre-plan tab names to avoid apostrophes if possible.
- **`valueInputOption='USER_ENTERED'`** — use this for text/numbers. For formula cells, use `valueInputOption='USER_ENTERED'` too (Google interprets `=HYPERLINK(...)` correctly with this mode).
- **Number of tabs limit** — Google Sheets maxes at 200 sheets/tabs per spreadsheet. For large pipelines, consolidate into fewer summary tabs (Overview, Hot/Warm/SSV combined, Cold grouped).
- **`execute_code` sandbox timeout** — writing 5 tabs of data + formatting may take 10+ seconds. The sandbox has a 5-min timeout so this is fine. Break into multiple execute_code calls if needed.