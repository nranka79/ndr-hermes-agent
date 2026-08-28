# Drive Search — Property Survey & Architectural Drawings

## When to Use

Searching for property survey drawings, FMB (Field Measurement Book) sketches, site plans, road network surveys, and architectural DWG files — typically on projects where the user needs to verify road widths, property boundaries, or existing survey data.

## Search Strategy

### Step 1: Query with Project Name + Drawing Type Keywords

Use `drive_search` via `gws_skill_bridge.call()` with multiple query patterns in parallel:

```python
queries = [
    f'{project_name} survey',
    f'{project_name} site plan',
    f'{project_name} DWG',
    f'{project_name} sketch',
    f'{project_name} road',
]

for q in queries:
    data = call('drive_search', service_name='google-draas', query=q, max=20, raw_query=False)
    # filter by mimeType in results
```

### Step 2: Filter by MIME Type

Survey/sketch files appear in these formats:
- `application/pdf` — PDF drawings (most common, viewable in-browser)
- `application/acad` — AutoCAD DWG files (need viewer)
- `image/vnd.dwg` — DWG variant
- `image/jpeg` — Scanned sketches or FMB images
- `image/vnd.google-earth.kml+xml` — KML spatial data (viewable in Google Earth)

### Step 3: Refine with Additional Keywords

If too many results, refine with `raw_query=True`:
```python
raw_q = f"fullText contains '{project_name}' and (fullText contains 'survey' or fullText contains 'DWG' or fullText contains 'sketch' or fullText contains 'site plan')"
data = call('drive_search', service_name='google-draas', max=20, raw_query=raw_q)
```

### Step 4: Cross-reference Folders

Many projects have a dedicated folder containing the key drawings. Get the folder ID and list its contents:
```python
data = call('drive_search', service_name='google-draas', query=f'{project_name} final', max=5, raw_query=False)
# Then list its contents
raw_q = f"'{folder_id}' in parents"
contents = call('drive_search', service_name='google-draas', max=50, raw_query=raw_q)
```

## gws_skill_bridge Quirk

The `drive_search` operation requires explicit `raw_query` parameter to avoid AttributeError:

| Pattern | Call Signature | When to Use |
|---------|---------------|-------------|
| Full-text search | `call('drive_search', query='search term', max=N, raw_query=False)` | Project name + keyword search |
| Raw Drive query | `call('drive_search', query='raw query string', max=N, raw_query=True)` | Folder contents, combined queries, mimeType filters |

## File Name Patterns to Recognize

Files likely to contain road networks, property boundaries, or survey data:

| Name Pattern | Likely Content |
|-------------|----------------|
| `*Site Digital Survey Drawing*` | Full digital survey showing boundaries, roads, contours |
| `*FMB Sketch*` | Field Measurement Book sketch — property boundaries |
| `*PreDCRDrawings*` | Pre-DCR building approval drawings with road layout |
| `*SitePlan*` | Site plan showing property + adjacent roads |
| `*Site and Abutting Roads Survey*` | Survey focused on road network bordering property |
| `*.dwg` (AutoCAD) | Full CAD drawing, may show road widths and dimensions |
| `*.kml` | Spatial data, viewable in Google Earth |

## Real Session Example (Jul 2026 — Ranka Northstar)

The user needed road survey drawings showing the road network next to Ranka Northstar (Allalasandra) property, with road widths. Search queries used:
- "Ranka Northstar survey" → found `NorthStar Allalasandra Site Digital Survey Drawing.pdf` and `Ranka_Northstar_SHEET1_SitePlan.pdf`
- "Ranka Northstar DWG" → found `NorthStar Allalasandra Site Digital Survey Drawing.dwg` and `20260525_NorthStar_DraDevelopers_PreDCRDrawings.dwg`
- "road survey" → found `BUX RANKA Site and Abutting Roads Survey.pdf` (a different project but relevant pattern)
- "FMB sketch" → found `20260320_RankaNorthstar_Allalasandra_FMB_Sketch.jpg`
