# Drive Search — Financial Model / IRR Spreadsheet Discovery

Pattern for finding project finance modelling spreadsheets across Google Drive
(apartment projects with cash flows, IRRs, cost assumptions).

## Working Approach

`gws_skill_bridge.call('drive_search', ...)` and `gws_auth.build_service()`
**cannot** be called from `execute_code` (see `gws-bridge-pitfalls.md#2`).
Use `terminal()` with the Hermes venv instead:

```python
cd /opt && /opt/hermes/.venv/bin/python -c "
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

svc = build_service('drive', 'v3', service_name='google-draas')

results = svc.files().list(
    q=\"mimeType='application/vnd.google-apps.spreadsheet' and (fullText contains 'IRR' or fullText contains 'cash flow')\",
    pageSize=100,
    fields='files(id, name, mimeType, modifiedTime, webViewLink)',
    orderBy='modifiedTime desc'
).execute()

for f in results.get('files', []):
    print(f['name'], '|', f['modifiedTime'][:10], '|', f['webViewLink'])
"
```

## Drive Query Keywords for Financial Models

| Concept | Drive Query Term |
|---------|-----------------|
| IRR models | `fullText contains 'IRR'` |
| Cash flow projections | `fullText contains 'cash flow'` |
| GD ratios | `fullText contains 'GD ratio'` |
| Built-up area | `fullText contains 'built up'` |
| FAR/TDR | `fullText contains 'FAR'` |
| Construction cost | `fullText contains 'construction cost'` |
| Approvals | `fullText contains 'approvals'` |
| Landowner/investor/developer IRR | `fullText contains 'landowner IRR'` or `fullText contains 'investor IRR'` or `fullText contains 'developer IRR'` |
| XIRR | `fullText contains 'XIRR'` |
| CFS / projection | `fullText contains 'CFS'` or `fullText contains 'Projection'` |
| Financial model (explicit) | `fullText contains 'Financial Model'` or `name contains 'Financial Model'` |
| Quarter-by-quarter | `fullText contains 'quarter'` |

## Combined Query (Broader Net)

```python
q = (
    "mimeType='application/vnd.google-apps.spreadsheet' and "
    "(fullText contains 'IRR' "
    "or fullText contains 'cash flow' "
    "or fullText contains 'GD ratio' "
    "or fullText contains 'built up' "
    "or fullText contains 'FAR' "
    "or fullText contains 'construction cost' "
    "or fullText contains 'landowner' "
    "or fullText contains 'investor IRR' "
    "or fullText contains 'developer IRR' "
    "or fullText contains 'XIRR' "
    "or fullText contains 'CFS' "
    "or fullText contains 'Projection' "
    "or fullText contains 'Financial Model'"
    ")"
)
```

## Naming Convention Clues

DRAAS project financial models tend to follow two conventions:
1. **Date-prefixed**: `YYYYMMDD <Project> <Description>` (e.g. `20260607 SLP Ranka Oasis Balaji Land Jiraffe JD Deal IRR`)
2. **Template-based**: `<Area> Projects IRR Calculator` or `<Project> IRR Calculator V<ver>` (e.g. `BUA Projects IRR Calculator`, `JP Nagar 1.5 Acres Project IRR Calculator V2`)

The "BUA Projects IRR Calculator" family tends to be the most comprehensive —
these typically include GD ratios, FAR, built-up area, construction cost
assumptions per sqft, approvals costs, and all four IRRs (project, developer,
landowner, investor). Look for V2/V3 versions.

## Recent Files Query (Last N Days)

```python
from datetime import datetime, timezone, timedelta
cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
q = f\"mimeType='application/vnd.google-apps.spreadsheet' and modifiedTime > '{cutoff}'\"
```

## Checking Files in a Specific Folder

```python
# Find TMP folder
folders = svc.files().list(
    q="name='TMP' and mimeType='application/vnd.google-apps.folder'",
    fields='files(id, name)'
).execute()

tmp_id = folders['files'][0]['id']

# List sheets inside it
sheets = svc.files().list(
    q=f"'{tmp_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet'",
    fields='files(id, name, modifiedTime, webViewLink)',
    orderBy='modifiedTime desc'
).execute()
```
