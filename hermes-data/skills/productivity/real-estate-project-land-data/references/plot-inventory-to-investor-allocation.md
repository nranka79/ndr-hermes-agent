# Plot Inventory → Investor Unit Allocation

Linking a master plan's numbered plots to an inventory spreadsheet, then matching plots to investor requirements.

## Discovery: Finding the Inventory Sheet

Master plan PDFs show numbered plots (e.g. 1–142 with skips). The corresponding plot inventory is usually a **Google Sheet** with every plot's dimensions and area. Search strategies in order:

```python
from tools.gws_skill_bridge import call as bridge_call

terms = [
    "Oasis Master Inventory Sheet",
    "Copy of Oasis Master Inventory Sheet", 
    "Ranka Oasis Area Working",
    "<Project> plot inventory",
    "<Project> plot area",
    "<Project> plot list",
    "<Project> Area Working",
]
for term in terms:
    r = bridge_call("drive_search", service_name="google-draas",
                    query=term, raw_query=False, max=10)
```

The inventory sheet name convention across DRAAS projects: `[Project Name] Master Inventory Sheet` or `[Project Name] Area Working`.

## Reading the Inventory Sheet

Use `sheets_get` (note: arg is `sheet_id=` not `file_id=`):

```python
r = bridge_call("sheets_get", service_name="google-draas",
    sheet_id="<ID>", range="A1:Y500")
data = json.loads(r)  # list of rows
```

**Typical columns** (based on Ranka Oasis Master Inventory Sheet):

| Col | Header | Content |
|-----|--------|---------|
| A | Plot # | Number (1, 2, 3… with skips) |
| B | Facing | East / West / South / North |
| C | Corner | Corner designation or blank |
| D | Shape | Std (standard) / NS (non-standard) |
| E–H | Dims in M | East, West, North, South (meters) |
| I | Area in sqm | Square meters |
| J | (blank) | — |
| K–N | Dims in Feet | East, West, North, South (feet & inches) |
| O | Area in Sft | **Plot area in square feet** |
| P–S | Peripherals | Adjacent plot/rds (East by, West by…) |
| T–V | Villa FSI | Grove (1.75×), Vista (1.8×), Reserve (1.85×) |
| W–Y | Villa SBUA | Grove, Vista, Reserve SBUA in sqft |

**Data starts at row 3** (row 1 = merged headers, row 2 = column labels).

## Matching Investor Requirements

Given investor requirements structured as:

- East-facing **1,500 sft plot** → **~2,700 sft SBUA** (Vista/Grove)
- East-facing **1,800 sft plot** → **~3,150 sft SBUA** (Vista/Grove)
- West-facing versions of same

**Filter inventory in code:**

```python
east_1500 = []  # Plot #, Area, SBUA
east_1800 = []
west_1500 = []
west_1800 = []

for row in data[2:]:  # skip headers
    if len(row) < 15: continue
    plot_no = row[0]
    facing = row[1]
    try:
        area = float(row[14]) if row[14] else 0
    except ValueError:
        continue
    sbua_vista = float(row[24]) if len(row) > 24 and row[24] and row[24] != '#VALUE!' else 0
    sbua_grove = float(row[23]) if len(row) > 23 and row[23] and row[23] != '#VALUE!' else 0
    sbua = sbua_vista or sbua_grove
    
    if 'East' in facing:
        if 1475 < area < 1550: east_1500.append((plot_no, area, sbua))
        elif 1775 < area < 1850: east_1800.append((plot_no, area, sbua))
    elif 'West' in facing:
        if 1475 < area < 1550: west_1500.append((plot_no, area, sbua))
        elif 1775 < area < 1850: west_1800.append((plot_no, area, sbua))
```

**Standard 1,500 sft plot dimensions:** ~30'10" × 49'3" = ~1,518 sft.
**Standard 1,800 sft plot dimensions:** varies — look for plots with SBUA ~3,150–3,350.

## Presenting to the User

Present the available candidates in a facing-grouped table and highlight which plots are contiguous (good for zone-marking) vs odd-shaped (suitable for Sashimadu-style allocations).

Key details from the user preferences in this session:
- **1,500 sft plots**: mark as one contiguous section, no odd plots
- **1,800 sft plots**: near the partner-allocation area, odd shape OK
- User will then mark zones on the master plan PDF manually

## Reconciling Numbering Mismatches

When the plot numbers in the inventory sheet don't match the master plan PDF, the most common cause is that the two documents were created from **different layout drafts**. This is a version-dating problem, solvable by checking Drive file metadata.

### Drive API call for file metadata

```python
from tools.gws_auth import build_service

service = build_service('drive', 'v3', service_name='google-draas')

# Inventory sheet
sheet = service.files().get(
    fileId='<SHEET_FILE_ID>',
    fields='id,name,createdTime,modifiedTime,owners,size'
).execute()

# Master plan PDF  
plan = service.files().get(
    fileId='<PLAN_FILE_ID>',
    fields='id,name,createdTime,modifiedTime,owners,size'
).execute()

print(f"Sheet: created={sheet['createdTime']}, modified={sheet['modifiedTime']}")
print(f"Plan:  created={plan['createdTime']}, modified={plan['modifiedTime']}")
```

### Interpretation rules

| Scenario | Inference |
|----------|-----------|
| Inventory created **before** plan | Inventory was made from an earlier draft; plan is the **authoritative** numbering |
| Inventory created **after** plan | Inventory may reflect post-plan revisions; ask user which to trust |
| Both created same day | Same layout iteration — numbers should match; look for data-entry errors |
| Inventory modified after plan | Someone updated the inventory. Could be corrections to match the plan — check modifiedTime against createdTime |
| Plan created before sanction letter | Plan may still be a draft even if it's the more recent file |

### Timeline example (Ranka Oasis, Jul 2026)

| Document | Created | Owner |
|----------|---------|-------|
| Oasis Master Inventory Sheet | 24 May 2026 | bk@findingform.design |
| Approved Panchayat Plan | 30 Mar 2026 | ndr@draas.com |
| Oasis Master Plan 1040726.pdf | 04 Jul 2026 | bk@findingform.design |
| Inventory Sheet last modified | 13 Jul 2026 | bk@findingform.design |

The inventory (24 May) was created **6 weeks before** the final master plan (4 Jul). Numbering changed between those drafts. Conclusion: the **master plan PDF is authoritative** for final plot numbers.

## Pitfalls

- The inventory sheet may have **gap numbers** (plot 1, then 6, then 21…) matching the master plan's skipped numbers — this is normal, don't treat it as corruption
- SBUA column may show `#VALUE!` for non-standard plots or plots where the FSI ratio doesn't apply — fall back to the alternative villa tier
- Plot area in sqft (col O) is the authoritative plot size; the meter-based area in col I is for cross-reference
- The `#VALUE!` cells in SBUA columns are Excel formula errors — read them as `None`/`0`, don't crash on float conversion
- Some plots have EAST/WEST dual facing (both) — handle as separate category
