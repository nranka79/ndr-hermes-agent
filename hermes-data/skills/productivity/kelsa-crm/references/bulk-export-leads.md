# Bulk Export: Kelsa Leads → Excel/CSV

## When to use

User asks for "export Kelsa leads to Excel/CSV" — all leads in a stage, from a source, or for a project. Typically 100+ records where manual `get_lead()` calls are impractical.

## The pattern

### Step 1: Use gateway tools for the main loop, or direct HTTP MCP for scripts

The kelsa_* gateway tools (`kelsa_call_tool`) work within the agent session loop. For long-running background exports, use **direct HTTP JSON-RPC** via terminal (see §11 in kelsa-crm SKILL.md).

### Step 2: Paginate `search_leads` to collect all lead IDs

```python
all_leads = []
page = 1
while True:
    text = call_tool("search_leads", {
        "pipeline_id": 10,
        "query": "stage:Cold",      # your filter
        "per_page": 100,
        "page": page
    })
    leads = parse_ids(text)         # extract #[id] from each line
    if not leads: break
    all_leads.extend(leads)
    page += 1
```

`parse_ids` regex: `re.search(r'\[#(\d+)\]', line)` — extract the numeric ID from search result lines.

### Step 3: Fetch details concurrently

Use `ThreadPoolExecutor(max_workers=10)` — Kelsa's MCP handles concurrent requests fine. Each worker calls `get_lead(pipeline_id, lead_id)` and parses the text response.

**The `get_lead` output format** (learned 2026-08-23):

```
# Name-["phone"]-date (ID: 12345)
Link: https://kelsa.io/10/leads?current_item_id=12345

## Status
  Stage: Cold
  Assignee: unassigned
  Created: ... by Bharat H
  Updated: ...

## Fields
  Channel: Portals
  Source: Magicbricks
  SourceDetails: MagicBricks
  Project: Ranka udaya
  Contact: Yash
  Contact Email: email@example.com
  Contact Phone: 919130411705
  ...

## Outstanding Prerequisites
## Recent Activity
```

The `## Fields` section contains `Key: Value` pairs. Parse by splitting on `## Fields`, then reading each subsequent non-empty, non-`##` line. Regex pattern per field:

```python
m = re.match(r'^\s*Channel:\s*(.+)$', line)
m = re.match(r'^\s*Source:\s*(.+)$', line)
m = re.match(r'^\s*SourceDetails:\s*(.+)$', line)
m = re.match(r'^\s*Project:\s*(.+)$', line)
m = re.match(r'^\s*Contact:\s*(.+)$', line)
m = re.match(r'^\s*Contact Email:\s*(.+)$', line)
m = re.match(r'^\s*Contact Phone:\s*(.+)$', line)
```

### Step 4: Write Excel with openpyxl

```python
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Cold Leads"

# Headers
headers = ["S No", "Client Name", "Client Phone", "Client Email",
           "Channel", "Source", "Source Detail", "Project"]

# Style
hfont = Font(bold=True, size=11, color="FFFFFF")
hfill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
bdr = Border(left=Side(style='thin'), right=Side(style='thin'),
             top=Side(style='thin'), bottom=Side(style='thin'))

for col, h in enumerate(headers, 1):
    c = ws.cell(row=1, column=col, value=h)
    c.font, c.fill, c.border = hfont, hfill, bdr

for i, r in enumerate(results, 1):
    for col, v in enumerate([i, r["name"], r["phone"], r["email"],
                             r["channel"], r["source"], r["source_detail"], r["project"]], 1):
        c = ws.cell(row=i+1, column=col, value=v)
        c.border = bdr

ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:H{len(results)+1}"
wb.save("/tmp/export.xlsx")
```

## Complete worked example

See `/tmp/export_cold_leads.py` from 2026-08-23 session — exports 1,687 Cold stage leads from DRA Sales Leads (pipeline 10) with all 8 requested columns.

Key stats from that run:
- 1,687 records fetched in ~2.5 min (10 concurrent workers)
- Source breakdown: I Am Here Software Labs (1,077), Magicbricks (380), Housing.com (220)
- Excel size: 102 KB
- `openpyxl` installed via `uv pip install openpyxl`

## Pitfalls

- **Background stdout buffering**: scripts run via `terminal(background=True)` buffer stdout. Set `PYTHONUNBUFFERED=1` or use `sys.stdout.flush()` / `print(..., flush=True)` in the script.
- **concurrent.futures rate**: 10 workers saturated the MCP server nicely. Could go higher but 10 is safe. The MCP calls are idempotent (read-only), so retry is safe on transient errors.
- **`openpyxl` not installed**: install via `uv pip install openpyxl` (Hermes root venv or user venv).
- **Phone numbers in Kelsa**: stored without country prefix (`919130411705`, not `+919130411705`). Add `+` prefix in Excel if needed.