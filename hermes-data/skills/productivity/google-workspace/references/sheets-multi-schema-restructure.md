# Multi-Sheet Workbook: Schema Detection & Category Restructuring

When a Google Sheets workbook has multiple sheets organized by **geography** (location clusters), each with **different column schemas**, and you need to restructure by **property type category** (Rowhouse, Villa, Apartment, Plotted).

## The Problem

Real estate competitive research workbooks often start organized by geography:

| Sheet | Area | Column Schema |
|---|---|---|
| Sindhu Bairavi Apartment... | Whitefield | 14-col detail format |
| Ranka Oasis | Sarjapur/South-East | 7-col summary format |
| Projects near Golfshire | Nandi Hills | 14-col detail format |

Each sheet may have a different header row structure. Sheet 1 has columns: Project Name, Location, Developer, Land Area, Type of Development, Total Units, Total Floors, Unit Types, Unit Sizes, Launch Date, Launch Price, Current Price, RERA, Sources. Sheet 5 has: Project Name, Property Type, Location, Size Range, Price/SqFt, Overall Price Range, Source.

## Detection Phase

```python
from tools.gws_auth import build_service

sheets_service = build_service('sheets', 'v4', service_name='google-draas')

# Get all sheet names
spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
sheet_names = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]

# For each sheet, read ALL data to detect schema
for name in sheet_names:
    data = sheets_service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f"'{name}'"  # No A1 notation — reads all used cells
    ).execute()
    values = data.get('values', [])
    if values:
        header = values[0]  # First row tells you the column structure
        print(f"Sheet '{name}': {len(header)} cols, header={header}")
```

## Schema Mapping

Build a mapping function that normalizes different schemas to a common data model:

| Common Field | Schema A (Col Index) | Schema B (Col Index) |
|---|---|---|
| Project Name | 0 | 0 |
| Location | 1 | 2 |
| Type/Property Type | 4 (Type of Development) | 1 (Property Type) |
| Unit Types | 7 | — (not present) |
| Price/SqFt | 11 (Current Sale Price) | 4 (Estimated Price / Sq. Ft.) |

**Key pattern — `chr(65 + col_index)` for Excel column letters in batchUpdate:** When writing results back, use `chr(65 + column_index)` not `chr(64 + column_index)`. `A = chr(65)`, not `chr(64)`.

## Category Classification

Map the "Type of Development" or "Property Type" text to a category:

```python
def classify_type(dev_type):
    t = dev_type.lower()
    if any(kw in t for kw in ['row villa', 'row house', 'rowhouse']):
        return 'Rowhouse'
    elif any(kw in t for kw in ['villa', 'villas', 'bungalow']):
        return 'Villa'
    elif any(kw in t for kw in ['apartment', 'high-rise', 'mid-rise', 'block', 'residency',
                                  'building', 'tower', 'complex', 'highrise']):
        return 'Apartment'
    elif any(kw in t for kw in ['plotted', 'plot', 'layout']):
        return 'Plotted'
    else:
        return 'Other'
```

## Creating Category Sheets

```python
# Create new sheet
body = {'requests': [{'addSheet': {'properties': {'title': 'Villa Projects'}}}]}
sheets_service.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body=body).execute()

# Write header row
sheets_service.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range="'Villa Projects'!A1:N1",
    valueInputOption='USER_ENTERED',
    body={'values': [header_row]}
).execute()

# Append categorized rows
sheets_service.spreadsheets().values().append(
    spreadsheetId=SHEET_ID,
    range="'Villa Projects'!A:N",
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body={'values': categorized_rows}
).execute()
```

## Pitfalls

1. **Mixed column formats block merge.** If Sheet A has 14 columns and Sheet B has 7, you can't simply copy-paste. Either pad the 7-col rows with empty cells to match the 14-col schema, or prompt the user to choose a target format.

2. **Property type keywords aren't clean.** "Sky Villas" (Prestige White Meadows) is an apartment product, not actual villas. "Villa-Plots" (Esteem Misty Hills) is a mixed product. Always check the full context (number of floors, unit types, total units) before classifying.

3. **Order of rows matters to the user** — they've been looking at these sheets sorted geographically for weeks. The new category sheets should preserve the original row ordering within each category group.

4. **Plotted / Villa / Rowhouse ambiguity.** "Urban Serenity" is "Plotted / Villa Community". "Skylite Vesta Villas" is "3 & 4 BHK Row Villas". These edge cases need manual classification or user confirmation.

5. **Off-by-one header detection.** A sheet often starts with a title row (e.g. "Master Real Estate Directory: ..."), then a header row, then data. Always print and verify `values[0]`, `values[1]`, and `values[2]` before assuming which is the header. Common mistake: setting `header = values[1]` when the actual header is `values[2]` or vice versa. Print the first 3 rows explicitly to confirm.

6. **"Eco" as a classification trap.** Properties like "Arvind Forest Trails — 4 & 5 BHK Eco Villas" contain "eco" in their type description but are still genuine villas. A naive filter of `if 'villa' in type and 'eco' not in type` will silently exclude them. Classification should check for exclusion keywords (row, plotted) rather than inclusion keywords (eco, garden, golf, premium) — the latter are modifiers, not category changers.

7. **Duplicate rows after rewrite.** When clearing and rewriting a sheet (`.values().clear()` + `.values().update()`), prior stale writes that ran without clearing can leave duplicates. Always run a verification pass after writing:

    ```python
    names = [r[0] for r in verify.get('values', []) if r]
    unique = list(dict.fromkeys(names))
    if len(names) != len(unique):
        print(f"⚠️ {len(names) - len(unique)} duplicates found — fix before reporting done")
    ```

8. **Script-file approach for multi-step ops.** For sheet restructuring that requires 3+ API calls (read → classify → create sheets → write → verify), write a Python script to `/data/hermes/scripts/` and run it with the Hermes venv. This gives you file-backed reproducibility and lets you fix bugs without replaying the entire conversation.

## Clarifying Questions to Ask

Before writing any new sheets, confirm with the user:

- **Scope:** Restructure the entire workbook or just one sheet?
- **Categories:** Which categories? (User might want Apartment/Villa/Rowhouse but not Plotted, or vice versa)
- **Format:** Use the 14-col detail format or 7-col summary? Or a hybrid?
- **Existing sheets:** Keep the geography sheets alongside new category sheets, or replace them?

## When This Pattern Applies

This isn't just for real estate. Use it any time you find:
- A workbook organized by one dimension (geography, team, quarter) 
- Project/entity data that has a "type" attribute
- Two or more different column schemas across sheets
- A need to re-slice the data along the type dimension

The same detection → mapping → classification → write workflow applies to CRM data (org by region → restructure by deal stage), inventory (org by warehouse → restructure by product category), etc.
