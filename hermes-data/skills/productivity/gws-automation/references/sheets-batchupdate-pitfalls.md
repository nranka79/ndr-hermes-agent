# Sheets batchUpdate — Column Offset & Date Parsing Pitfalls

## Pitfall: Column Letter Offset in batchUpdate

When building cell range strings for `spreadsheets().values().batchUpdate()`, the Excel column letter must be **1-indexed**:

| 0-indexed col | 1-indexed (Excel) | Correct formula |
|---|---|---|
| 4 (start date) | 5 → E | `chr(64 + 5)` = `"E"` |
| 5 (end date) | 6 → F | `chr(64 + 6)` = `"F"` |

**Wrong:** `chr(64 + 4)` → `"D"` (writes to wrong column)
**Correct:** `chr(65 + 4)` = `chr(64 + 5)` = `"E"`

Using the **0-indexed column index directly** with `chr(64 + col)` shifts all ranges left by one column — writing dates into the "IS APPLICABLE" column (D) and corrupting data.

### Safe patterns

```python
# Pattern 1: chr(64 + col_index + 1) where col_index is 0-based
col_letter = chr(64 + col_index + 1)  # col_index=4 → chr(69) = "E"

# Pattern 2: chr(65 + col_index) where col_index is 0-based  
col_letter = chr(65 + col_index)  # col_index=4 → chr(69) = "E"

# Pattern 3: explicit mapping
EXCEL_COLS = ['A','B','C','D','E','F','G','H','I','J','K','L','M']
col_letter = EXCEL_COLS[col_index]  # col_index=4 → "E"
```

## Pitfall: Mixed-Format Dates in Indian RERA Sheets

Indian RERA spreadsheets (especially SIS Schedules sheets) use a confusing mix of `mm/dd/yyyy` and `dd/mm/yyyy` formats — sometimes within the same section.

### The parsing heuristic

```python
def parse_rera_date(s):
    """
    Parse dates from RERA Schedules sheets.
    - If a > 12: dd/mm/yyyy (day first, month can't be >12)
    - If b > 12: mm/dd/yyyy (day second)
    - If both ≤ 12: use chronological context. In the Schedules
      sheet, the format switches between mm/dd and dd/mm even
      within the same 3-row section. Safest: don't parse at all —
      manually assign (row, col) → datetime in a dict.
    """
    parts = s.split('/')
    if len(parts) != 3:
        return None
    a, b, y = int(parts[0]), int(parts[1]), int(parts[2])
    if y < 100:
        y += 2000
    
    if a > 12:
        return datetime(y, b, a)  # dd/mm/yyyy
    elif b > 12:
        return datetime(y, a, b)  # mm/dd/yyyy
    # Both ≤ 12 — ambiguous, need context
    # Try both and pick the one that makes chronological sense
    return None  # Fall back to manual assignment
```

### Real examples from Ranka Amber Schedules sheet

| String | Correct Interpretation | Reason |
|--------|----------------------|--------|
| `"07/30/2026"` | Jul 30, 2026 (mm/dd) | b=30 > 12 → day is second |
| `"20/8/2026"` | Aug 20, 2026 (dd/mm) | a=20 > 12 → day is first |
| `"1/8/2026"` | Aug 1, 2026 (dd/mm) | Both ≤12. Context: Earth work ends Jul 30, Foundation starts Aug 1 |
| `"08/10/2026"` | Aug 10, 2026 (mm/dd) | Both ≤12. After Plinth ends Sep 15, RCC starts — Aug 10 fits |
| `"05/28/2027"` | May 28, 2027 (mm/dd) | b=28 > 12 → day is second |
| `"05/10/2027"` | Oct 5, 2027 (dd/mm) | Both ≤12. Context: after RCC ends May 28 |
| `"06/10/2027"` | Oct 6, 2027 (dd/mm) | Both ≤12. After Masonry ends Oct 5 |
| `"13/10/2027"` | Oct 13, 2027 (dd/mm) | a=13 > 12 → day is first |
| `"7/10/202610"` | Jul 10, 2026 (typo+mm/dd) | Typo in original — trailing "10" removed |

### Safest approach: manual dict

For the Schedules sheet, the format mix is so inconsistent that the safest approach is a hard-coded dictionary:

```python
manual_dates = {
    (7, 'E'): datetime(2026, 7, 10),   # Earth work start
    (7, 'F'): datetime(2026, 7, 30),   # Earth work end
    (8, 'E'): datetime(2026, 8, 1),    # Foundation start  
    (8, 'F'): datetime(2026, 8, 20),   # Foundation end
    (9, 'E'): datetime(2026, 8, 20),   # Plinth start
    (9, 'F'): datetime(2026, 9, 15),   # Plinth end
    # ... continue for all date rows
}
```

This avoids relying on a heuristic that will inevitably get some dates wrong.

## Recovery: Restoring Overwritten "IS APPLICABLE" Column

When the column offset pitfall fires, cell values written to column D overwrite the "IS APPLICABLE" / "Yes" column. Recovery:

1. Read the sheet's original data (from session history or fresh read if available)
2. Prepare a batch restore: `{'range': 'Schedules!D7', 'values': [['Yes']]}`
3. Write the correct date values to the proper columns (E and F)
4. Verify all cells are in the right columns

```python
restore = {7: 'Yes', 8: 'Yes', 9: 'Yes', 17: 'Yes', 18: 'Yes', ...}
for row, val in restore.items():
    sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f'Schedules!D{row}',
        valueInputOption='USER_ENTERED',
        body={'values': [[val]]}
    ).execute()
```

## Common RERA Sheet Columns

| Column | 0-index | Excel | Content |
|--------|---------|-------|---------|
| D | 3 | D | IS APPLICABLE (Yes/No) |
| E | 4 | E | ESTIMATE START DATE |
| F | 5 | F | ESTIMATE END DATE |
| G | 6 | G | Carpet Area / RERA Carpet Area |
| H | 7 | H | Exclusive Common Area |
| I | 8 | I | Common Area to Association |
| J | 9 | J | Undivided Share of Land |
| K | 10 | K | No. of parking lots |
| L | 11 | L | RERA CARPET (sqft) |
