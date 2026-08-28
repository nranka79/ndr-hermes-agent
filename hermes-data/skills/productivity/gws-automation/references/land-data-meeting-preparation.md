# Land Data Analysis & Client Meeting Preparation

Cross-reference multiple sheets in a Google Sheets project database to find land parcels matching specific criteria, compile supporting assets, and produce a presentation-ready summary.

## When to Use

A client meeting requires identifying land parcels by criteria (approximate size, ownership share, registration status, entity name) using a project's Google Sheets database. The pattern also covers assembling Drive links to supporting documents (masterplan, renders, brochures).

## Data Sources Typically Involved

| Sheet | Purpose | Example Sheets from Riverstone |
|-------|---------|-------------------------------|
| Survey Details | Per-survey extents, share, status | `Surevy NO's Details` |
| Plot Inventory | Individual plot-level data (size, status) | `Plot Inventory Summary` |
| Land Summary | Aggregate land data by survey | `60 Acres land sy No details` |
| Share Distribution | Landowner vs Developer split | `LO and Dev share` |
| Allocations | Who plots are allotted to | `Allocations` |
| RTC Records | Revenue records | `BHVESH RTC CAL` |

## Step 1 — Get Exact Sheet Names

Sheet names in DRAAS spreadsheets commonly have trailing spaces that break A1 notation queries. Always verify exact names first:

```python
meta = sheets.spreadsheets().get(spreadsheetId=ID).execute()
for s in meta.get('sheets', []):
    title = s.get('properties', {}).get('title', '')
    print(f'Sheet: [{repr(title)}]')  # repr() reveals trailing whitespace
```

Then use the exact name including trailing space:
```python
range_str = "'Plot Inventory Summary '!A1:Z200"  # note trailing space
```

## Step 2 — Parse Land Extents

Indian land extents come in multiple formats. Parse to decimal acres for comparison:

### Format: Acres:Guntas (e.g. "1:04" = 1 acre 4 guntas)
```python
def parse_acres_guntas(meas):
    """Parse '1:04' or '01:14.08' to decimal acres. 1 acre = 40 guntas."""
    parts = str(meas).replace(' ', '').split(':')
    acres = float(parts[0])
    guntas_str = parts[1] if len(parts) > 1 else '0'
    guntas = float(guntas_str.split('.')[0]) if '.' in guntas_str else float(guntas_str)
    return acres + guntas / 40
```

### Format: Decimal acres (e.g. "1.04")
Use `float()` directly.

### Format: Guntas only
```python
acres = guntas / 40
```

### Verification
- 1 Acre = 40 Guntas = 43,560 sqft
- 1 Gunta = 1,089 sqft
- 1 sqmt = 10.764 sqft

## Step 3 — Cross-Reference Across Sheets

### Finding ~1 acre parcels with specific share and status

```python
# From survey details sheet
survey_sheet = "'Surevy NO\\'s Details '!A1:I48"
# Columns: Schedule, SL NO, Survey Number, Measuring (A/G), Karab (A/G), Share, RTC/Title Status, DOC Link

# Filter criteria:
# - ~1 acre (0.65 to 1.35 acres)
# - Share = "Landowner" (for client registration)
# - Status = "reg" (registered title)
```

### Combining adjacent plots
When individual plots are smaller than 1 acre, group by survey number from the Plot Inventory sheet and sum:

```python
from collections import defaultdict
groups = defaultdict(list)
for row in plot_data:
    sy_no = row[2] 
    share = row[5]
    if 'Land Owner' in share and 'SOLD' not in status:
        acres = float(row[4])
        groups[sy_no].append((row[0], acres, row[1]))

for sy, plots in sorted(groups.items()):
    total = sum(p[1] for p in plots)
    print(f'Sy No {sy}: {total:.2f} acres in {len(plots)} unsold LO plots')
```

## Step 4 — Filter by Entity Name

Client names and entity names may appear across multiple sheets (Plot Inventory, Allocations, bank details sheet). Search all sheets:

```python
for sheet_name in all_sheet_names:
    result = sheets.spreadsheets().values().get(
        spreadsheetId=ID,
        range=f"{sheet_name}!A1:Z200"
    ).execute()
    for row in result.get('values', []):
        row_str = ' '.join(str(c) for c in row).lower()
        if 'clientname' in row_str:
            print(f'{sheet_name}: {row}')
```

## Step 5 — Compile Supporting Assets from Drive

Search for project-related files systematically:

```python
# Search patterns for common document types
queries = {
    'Masterplan': "name contains 'Masterplan' and name contains 'ProjectName'",
    'Brochure': "name contains 'Brochure' and name contains 'ProjectName'",
    'Renders': "name contains 'Render' and name contains 'ProjectName'",
    'Villa Plans': "name contains 'Villa' and name contains 'ProjectName'",
}
```

Check ownership — files from different users (Bhavesh/bk@findingform.design, Finding Form team) may have different access levels. List folder contents to verify viewer access.

## Step 6 — Compile Presentation Summary

Present findings as a structured brief with:

1. **Meeting header** — Client names, time, objective
2. **Options table** — Survey No, Extent (A:G & decimal), Share, Status, Notes
3. **Excluded options** — Why they were excluded (lamination, too large, pending title)
4. **Discussion items** — Points needing client clarification (RTC segregation, etc.)
5. **Drive Links** — 10-12 key document links with descriptions

## Common Pitfalls

- **Sheet name trailing spaces** — Always use `repr()` to verify. Query fails silently with `HttpError 400: Unable to parse range` if trailing space is missing.
- **Apostrophe in sheet name** — Sheets with apostrophes (e.g. "Surevy NO's Details") need careful quoting in A1 notation. Use Python string with proper escaping: `"'Surevy NO\\'s Details '"`.
- **Inconsistent extent columns** — Some sheets store as "Acres:Guntas" string, others as separate Acres and Guntas columns. Always check the header row.
- **Plot vs Survey granularity** — One survey number may be subdivided into multiple plots. The total landowner share from the LO/Dev share sheet may differ from the sum of unsold plots in the inventory (some parcels may already be allocated/sold or under lamination).
- **"NA" share** — Plots with "NA" share are unassigned. They may need clarification from the project team before being offered to clients.
- **Lamination** — A survey number under "lamination" means the title/registration is in process and not yet ready for transfer. Exclude from client options.
- **Existing client bookings** — Check if the client already has plots allotted (even if SOLD with NOT DONE sign status). This may affect the discussion.

## Verified Example: Riverstone Client Meeting (Jun 2026)

- Client: Sumaya Anwar & Anwar Sir
- Criteria: ~1 acre, landowner share, registered
- Cross-referenced: `Surevy NO's Details`, `60 Acres land sy No details`, `Plot Inventory Summary`, `LO and Dev share`, `BHVESH RTC CAL`, `Allocations`
- Best match: 114/7 (1.04 acres, Landowner, Registered, Mahakasi Enterprises)
- Excluded: 114/4A (lamination), 114/9 (Developer share), 115/2 (2.30 acres, too large)
- Discussion item: 113/10 — segregated into 10A/10B but no RTC records
- Assets compiled: 11 Drive links (masterplan, brochure, villa options, renders, entrance portal, gazebo options, landscape views)
