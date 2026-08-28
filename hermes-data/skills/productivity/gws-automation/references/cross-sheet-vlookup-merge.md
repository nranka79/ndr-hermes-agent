# Cross-Sheet VLOOKUP / Lookup Merge (Sheets)

## When to use

The user has TWO Google Sheets and wants to pull data from sheet A into sheet B based on a shared key column (typically Plot No, Unit No, Customer ID, etc.). The user will usually describe it as "VLOOKUP" or "map this data against plot numbers."

This is a recurring pattern for Nishant's real estate projects (Serenity Hillview, Ranka Oasis, Vani Vilas, Ranka North Star, Nippon Capital, etc.) — each has a "newer area sheet" and an "older plottal/unit inventory sheet" that need to be reconciled into one consolidated inventory.

## Why NOT use IMPORTRANGE or array formulas

`IMPORTRANGE` + `VLOOKUP` works but is fragile:
- Breaks if the user renames the source sheet
- Doesn't write a static value, so the user can't see the actual data without opening the file
- Slower to debug when a single plot number has a typo
- Cross-file formula references frequently fail with `#REF` if the source column changes

The Python-dict-lookup approach is simpler, deterministic, and produces a static result the user can audit visually.

## Workflow

### Step 1 — Read both sheets' headers + first 2 rows

Always read headers from BOTH sheets before mapping columns. Users frequently misremember column letters (e.g., "facing column B" — but facing is column D). The truth comes from the data, not the user's recall.

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

sheets = build_service('sheets', 'v4', service_name='google-draas')

SS_SOURCE = 'SOURCE_SPREADSHEET_ID'  # sheet that has the data to pull
SS_TARGET = 'TARGET_SPREADSHEET_ID'  # sheet to write into

# Read source — get all data
src = sheets.spreadsheets().values().get(
    spreadsheetId=SS_SOURCE, range='Sheet1!A:H'  # widen as needed
).execute().get('values', [])

# Read target — get all data, including any pre-existing columns past M
tgt = sheets.spreadsheets().values().get(
    spreadsheetId=SS_TARGET, range='Sheet1!A:M'  # widen to include target cols
).execute().get('values', [])

# Print headers + first 2 rows of each
print("SOURCE headers + 2 sample rows:")
for i, row in enumerate(src[:3]):
    print(f"  Row {i+1}:", row)
print("TARGET headers + 2 sample rows:")
for i, row in enumerate(tgt[:3]):
    print(f"  Row {i+1}:", row)
```

### Step 2 — Confirm the column mapping with the user BEFORE writing

The user almost always gives a partial column list. Common ambiguities:
- "5 columns N, O, P, Q, R" but they listed 7 fields — clarify which to drop
- "Facing column B" but facing is actually in column D
- Source and target both have the same field name (Registerable Area) — is the user replacing the target's existing data, or adding a new versioned column from the source?

Show the user the exact mapping you intend and ask: "You mentioned 7 fields but only 5 columns N-R. Should I include all 7 in N-T, or drop Facing and Total Area?"

### Step 3 — Build the Python dict lookup, then row-by-row write

```python
# Build lookup: plot_no -> [colB, colC, colD, colE, colF, colG, colH]
lookup = {}
for row in src[1:]:  # skip header
    if not row or not row[0].strip():
        continue
    plot = row[0].strip()
    padded = (row + [''] * 8)[:8]
    lookup[plot] = padded[1:8]  # exclude the plot number itself

print(f"Lookup built: {len(lookup)} unique plots")
print(f"Sample lookup['1']: {lookup.get('1')}")

# Build rows_to_write matching target row count
# For each target row, look up the plot number in column A
new_headers = ['Registerable Area (SS1)', 'Right of Use (SS1)',
               '% of Plot area (SS1)', 'UDS sqft (SS1)', '% UDS Loading (SS1)']

rows_to_write = [new_headers]
matched, unmatched = 0, 0
for row in tgt[1:]:
    if not row or not row[0].strip():
        # blank or totals row — write blanks to preserve alignment
        rows_to_write.append([''] * 5)
        continue
    plot = row[0].strip()
    if plot in lookup:
        # Adjust column indexes to match what you actually want
        rows_to_write.append(lookup[plot][:5])  # first 5 fields
        matched += 1
    else:
        rows_to_write.append([''] * 5)
        unmatched += 1

print(f"Matched: {matched}, Unmatched: {unmatched}")
```

### Step 4 — Write to target sheet starting at the specified column

```python
# Update the target sheet's column N onwards (column letter = 13 in 0-indexed)
# N1 is the first header cell, so range starts at N1
# rows_to_write[0] is the header, rows_to_write[1:] are data
sheets.spreadsheets().values().update(
    spreadsheetId=SS_TARGET,
    range='Sheet1!N1',  # adjust sheet name and starting col
    valueInputOption='USER_ENTERED',
    body={'values': rows_to_write}
).execute()

print("Write complete")
```

Use `valueInputOption='USER_ENTERED'` (not `'RAW'`) so percentages and dates auto-format, but note this will also auto-convert strings like "1.0" to numbers — fine for area data.

### Step 5 — Verify the write

Re-read the written range and spot-check 3 rows: first, middle, last. Also confirm the totals row at the bottom of the target wasn't accidentally populated.

```python
verify = sheets.spreadsheets().values().get(
    spreadsheetId=SS_TARGET, range='Sheet1!N1:R5'
).execute().get('values', [])
for i, row in enumerate(verify):
    print(f"Row {i+1}: {row}")
```

## Pitfalls

### `execute_code` sandbox is stateless

Each `execute_code` block starts with a fresh Python interpreter. Variables (including the `sheets` service) do NOT persist between blocks. Always rebuild the service at the top of every block:

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4', service_name='google-draas')
# ... your code
```

The one-line "sheets is not defined" error is the symptom.

### Use `build_service`, NOT the `gapi` CLI

`/opt/hermes/skills/productivity/google-workspace/scripts/google_api.py` reports "Not authenticated" because the CLI path expects its own token file. The vault-based `tools.gws_auth.build_service` path works for Sheets too. Always go through `build_service` for any GWS work in this environment.

### Trailing totals / blank rows

Most inventory sheets have:
- Header in row 1
- Data rows for N items
- A totals row with empty plot number but populated sum values
- One or more trailing blank rows

Read the full range (don't restrict to data rows). When iterating to build `rows_to_write`, preserve the alignment by writing blanks for rows where the plot number is empty:

```python
for row in tgt[1:]:
    if not row or not row[0].strip():
        rows_to_write.append([''] * N)  # preserve blank rows
        continue
    # ... lookup
```

If you skip blank rows in the write, the entire grid shifts up and corrupts alignment.

### Sheet grid size (1000 rows)

Default Google Sheets have 1000 rows × 26 columns. If you write past column M (column 13), you may need to expand the grid. Two options:
- Just write — the API auto-grows the grid for you
- Pre-expand via `spreadsheets().batchUpdate()` with `appendDimension` requests if you need a specific size

In practice, just writing works. No pre-expansion needed.

### Column letter math

If you need to programmatically compute the target range:
- Column N = index 13 (0-indexed) = letter N
- Column letter for 0-indexed `c`: `chr(65 + c)` — `chr(65+13) = 'N'` ✓
- The WRONG pattern `chr(64 + c)` shifts left by 1: `chr(64+13) = 'M'`
- This is a real bug that has corrupted sheets before — see `sheets-batchupdate-pitfalls.md`

### Plot number type coercion

Plot numbers are usually stored as TEXT in the source sheet but as NUMBERS in the target sheet (or vice versa). When building the lookup dict, normalize to string with `.strip()`:

```python
plot = str(row[0]).strip()
```

If you skip this, `"1" != 1` and the lookup will silently miss every row.

### User may want to PRESERVE existing target data

Sheet B (the plottal inventory) often has its own version of the same columns. Don't overwrite B's existing B-L columns with A's data — the user wants A's data ADDED as new columns (N onwards) for comparison, not as a replacement.

Always confirm: "Are you adding A's data as new columns, or replacing B's existing values?"

## Worked example — Serenity Hillview, Jul 2026

**Source** (SS1, area sheet): 38 plots, columns A-H = Plot No, Registerable, RoU, Facing, %plot, UDS, %UDS, Total
**Target** (SS2, plottal inventory): 38 plots + totals row + 1 trailing blank, existing columns A-L with its own area data
**User intent:** ADD SS1's area values to SS2 starting at column N for comparison.

Mapping: N=Registerable, O=Right of Use, P=%Plot area, Q=UDS sqft, R=%UDS Loading (5 columns, dropped Facing and Total because user said "N O P Q R")

Result: 38/38 plots matched, 0 unmatched. Wrote N1:R41 = 1 header row + 38 data rows + 1 totals row (blank) + 1 trailing blank.

**Ambiguity surfaced to user:** User mentioned 7 fields in source (B, C, D, E, F, G, H) but specified only 5 target columns (N-R). Paused to confirm before writing — correct call.
