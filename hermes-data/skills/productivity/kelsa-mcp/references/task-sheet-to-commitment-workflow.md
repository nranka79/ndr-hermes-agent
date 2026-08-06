# Task Sheet → Kelsa Commitment Pipeline Workflow

**Class:** Task tracking setup for outsourced/vendor team members (Rahul/Vinod, Anbu, etc.)
**Source:** Nishant's workflow (Jul 2026)
**Endpoint:** Kelsa Pipeline 2002 (DRA Commitments)

## Overview

When a team member has a long task list across multiple projects, the workflow is:

1. **Compile** all tracked tasks into a master list
2. **Find or create** a Google Sheet for review (prefer adding tab to existing sheet)
3. **User reviews** each item and gives update/feedback
4. **Update/modify** sheet based on review
5. **Convert** committed tasks into deadlines → create records in Kelsa Pipeline 2002
6. **Share Kelsa links** with the assignee so they can post progress updates

## Step 1: Inventory Existing Sheets

Before creating anything new, search Drive for existing task tracking sheets:

```python
# Search for relevant sheets
from tools.gws_skill_bridge import call
result = call('drive_search', service_name='google-draas',
              raw_query=True,
              query="name contains 'task' or name contains 'Task' or name contains 'tracker' or name contains 'Tracker'",
              max=50)
```

**Key sheets to look for** (DRAAS context):
- `"Rahul Tasks"` — old per-person task sheet (stale data from months ago)
- `"Legal- Vinod Task Tracker"` — old legal task tracker
- `"Anbu Critical Tasks"` — old per-person sheet
- `"DRA Jobs and Tasks Inventory List"` — high-level job responsibilities
- `"DRA Projects Delivery Tracker"` — project-level delivery tracking

**Decision rule:**
| Condition | Action |
|-----------|--------|
| A sheet for this person already exists (`"Rahul Tasks"`, `"Vinod Task Tracker"`) | **Add a new tab** named `YYYYMMDD` or `Current` to the existing sheet |
| No sheet exists for this person | **Create a new spreadsheet** titled `"{Name} Tasks - YYYYMM"` |
| A general task tracker exists with no per-person tabs | **Add a tab** named after the person |

### Checking existing sheets for relevance

Read contents of candidate sheets to see if they're current or stale:

```python
# Check if a sheet has current data
result = call('sheets_get', service_name='google-draas',
              sheet_id='SPREADSHEET_ID',
              range='Sheet1!A1:Z10')
# If dates are months old, it's stale — add a new tab
# If dates are recent, update in-place
```

**⚠️ `sheets_get` uses `sheet_id` as the parameter name** (NOT `spreadsheet_id` or `spreadsheetId`). See `references/gws-skill-bridge-sheets-operations.md` for the full parameter reference.

**⚠️ `drive_search` with raw query needs `raw_query=True`** — Without it, the bridge's `call()` doesn't create the attribute on the `SimpleNamespace`, and the skill function raises `AttributeError: 'SimpleNamespace' object has no attribute 'raw_query'`. Always pass `raw_query=True` when building your own query string.

## Step 2: Create/Populate the Sheet

### Adding a new tab to an existing spreadsheet

```python
# Use the raw Sheets API since the bridge doesn't expose addSheet
import sys; sys.path.insert(0, '/opt/hermes')
import json, os; os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
from tools.gws_auth import build_service

sheets = build_service('sheets', 'v4', service_name='google-draas')

# Add a new sheet tab
requests = [{
    'addSheet': {
        'properties': {'title': 'Jul 2026', 'index': 1}
    }
}]
sheets.spreadsheets().batchUpdate(
    spreadsheetId='SPREADSHEET_ID',
    body={'requests': requests}
).execute()
```

### Creating a brand new spreadsheet

```python
from tools.gws_skill_bridge import call
result = call('sheets_create', service_name='google-draas',
              title='Rahul Tasks - Jul 2026',
              sheet_name='Task List')
# Returns spreadsheetId and spreadsheetUrl
```

### Recommended column structure (review-ready)

| # | Project | Task | Source | Status | Your Feedback | Deadline/Commitment | Kelsa Link |
|---|---------|------|--------|--------|---------------|---------------------|------------|
| 1 | Serenity Hillview | Legal DD checklist | Email 17 Jul | PENDING | | | |
| 2 | Ranka North Star | Visit BBMP Town Planning | Email 30 Jun | URGENT | | | |

- **Source** — where the task originated (email date, meeting, etc.)
- **Status** — PENDING / URGENT / ✅ Done / 🟡 Overdue / Ongoing
- **Your Feedback** — Nishant's review input (updated after his review pass)
- **Deadline/Commitment** — date or marker once task is committed
- **Kelsa Link** — URL to the Kelsa Pipeline 2002 record (filled after commitment)

```python
# Populate via sheets_update
import json
header = ["#", "Project", "Task", "Source", "Status", "Your Feedback", "Deadline/Commitment", "Kelsa Link"]
rows = [
    ["1", "Serenity Hillview", "Legal DD checklist", "Email 17 Jul", "PENDING", "", "", ""],
    # ... more rows
]
call('sheets_update', service_name='google-draas',
     sheet_id='SPREADSHEET_ID',
     range='Task List!A1:H50',
     values=json.dumps([header] + rows))
```

**⚠️ `values` must be a JSON string** (the bridge does `json.loads(args.values)`). Pass `json.dumps(your_data)`.

## Step 3: User Review

The user reviews each task and provides:
- **Update/feedback** on current status
- **Which tasks to keep/modify/drop**
- **Which tasks become committed deadlines**

Present the sheet for review after populating. The user works through the list and gives feedback item by item.

**After each item's feedback:** update the "Your Feedback" and "Status" columns in the sheet via `sheets_update`.

## Step 4: Move Committed Tasks to Kelsa Pipeline 2002

After review, tasks the user marks as **committed deadlines** get created as records in **Kelsa Pipeline 2002 (DRA Commitments)**.

### Pipeline 2002 structure

| Info | Value |
|------|-------|
| Pipeline ID | 2002 |
| Name | DRA Commitments |
| Stages | Commitment Reported → Commitment Accepted → Commitment Delivered |
| Key fields | `cf_enter_the_commitment`, `cf_deliverables`, `cf_due_date`, `cf_in_relationship_to`, `cf_is_completed` |

### Creating a commitment record

```python
# Requires MCP tools or direct Kelsa API access
# See kelsa-mcp skill for write tool details

# Stage "Commitment Reported" = st_prospect (first active stage)
commitment_data = {
    "name": f"{project_short} — {task_summary}",
    "stage_id": ST_COMMITMENT_REPORTED,  # resolve via get_pipeline(2002)
    "assignee_id": ASSIGNEE_VINOD,       # numeric user ID
    "field_values": {
        "cf_enter_the_commitment": task_description,
        "cf_deliverables": deliverable_description,
        "cf_due_date": due_date_iso,     # YYYY-MM-DD
        "cf_in_relationship_to": project_name,
        "cf_is_completed": False
    }
}
# create_lead(pipeline_id=2002, ...)
```

### After creation

1. Get the record URL: `https://app.kelsa.io/5/leads/{lead_id}`
2. **Fill the Kelsa Link column** in the Google Sheet for that row
3. **Share the Kelsa link** with Rahul so he can post updates directly on the record

## Step 5: Sharing Kelsa Links

Once committed tasks have Kelsa records, share the links with the assignee (Rahul):

**Draft an email or message** containing:
```
Committed deadlines with Kelsa tracking links:

1. [Task Name] — [Kelsa URL]
2. [Task Name] — [Kelsa URL]
...

Please post progress updates on each link directly.
```

Send as a **Gmail draft** (not sent) for the user to review and send, or as a WhatsApp/Telegram message.

## Pitfalls

- **Sheet names with spaces need single-quoted ranges** — When a sheet tab has spaces (e.g. `"Jul 2026"`), the range in `sheets_update`/`sheets_get` must use single quotes: `'Jul 2026'!A1:G40`. Without quotes the API returns `HttpError 400: Unable to parse range`.
- **`drive_search` requires `raw_query=True` for custom queries** — Passing a formatted query string without `raw_query=True` raises `AttributeError: 'SimpleNamespace' object has no attribute 'raw_query'`. Always set `raw_query=True` when building your own query.
- **Existing sheets are often stale** — The "Rahul Tasks" and "Vinod Task Tracker" sheets found in Drive (Jul 2026) had data from 6+ months ago. Always add a new tab rather than updating old data in-place, unless the user confirms the old data is still relevant.
- **`sheets_get` needs `sheet_id` not `spreadsheet_id`** — The gws_skill_bridge's `sheets_get` reads `args.sheet_id`. Passing `spreadsheet_id` raises AttributeError.
- **`sheets_update` `values` must be a JSON string** — The bridge does `json.loads(args.values)`. Pass a JSON string (via `json.dumps()`), not a Python list.
- **Kelsa Pipeline 2002 has 3 stages** — Commitment Reported (st_prospect) → Commitment Accepted → Commitment Delivered. New commitments go into "Commitment Reported" stage.
- **Assignee ID must be numeric** — Kelsa `assignee_id` requires a numeric user ID (e.g., 41 for Nishant). Name strings silently clear the assignee to unassigned.
- **Cross-pipeline task discovery** — Record-level assignee ≠ task-level assignee in Kelsa. After creating a commitment, verify assignment with `list_lead_tasks()`.
- **The addressable pipeline is DRA Commitments (2002), not DRA Invoice Processing (516)** — Nishant distinguishes general commitments from invoice-specific tasks.
