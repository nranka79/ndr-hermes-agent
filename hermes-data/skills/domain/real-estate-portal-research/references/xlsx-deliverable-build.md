# Building xlsx deliverables (openpyxl, verified 2026-08-15)

When NDR asks for a spreadsheet from portal/RERA research, the standard
deliverable is a two-sheet workbook:

- Sheet 1 "Project Averages": project, developer, locality, distance,
  RERA reg no, RERA start/end, listing count, avg/median/min/max rate
  (Rs/sqft), avg price, avg area.
- Sheet 2 "All Listings": every listing (project, BHK, area, price,
  rate/sqft, status, seller) with a CLICKABLE link column to the portal
  page.

## Environment quirk

The host has no system pip (PEP 668) and openpyxl is NOT installed.
Install-on-the-fly with uv (verified working):

```bash
uv run --with openpyxl python3 build_xlsx.py
```

## PITFALL: silent first-row loss when using ws.append() (hit 2026-08-15)

First attempt built both sheets with `ws.append([...])` in a loop. The
saved file was missing the FIRST data row of each sheet (5 projects
became 4, 25 listings became 24 + a trailing empty row). openpyxl's
`append` on a fresh worksheet can drop the initial row silently — no
error, no warning. Do NOT trust `append`-built workbooks.

## Verified pattern: explicit cell writes + self-verification

1. Write every cell explicitly with `ws.cell(row=ri, column=ci, value=val)`
   (no `append` for data rows).
2. Style headers/columns with a `fill_sheet(ws, headers, widths, data)`
   helper that also freezes panes and applies borders/alt-row fills.
3. Hyperlinks: set `cell.hyperlink = cell.value` + font
   `Font(color="0563C1", underline="single")` on the URL column.
4. SAVE, then RE-OPEN the file in the same script and assert:
   - `n_projects == expected` (count non-empty project cells in sheet 1)
   - `n_listings == expected` (sheet 2)
   - `n_hyperlinks == expected` (URL cell has both value AND hyperlink)
   Print each count; fail loudly on mismatch.

This self-verification is what caught the append bug before delivery.

## Formatting notes

- Indian rupee figures: keep raw numbers with thousands separators
  (`#,##0`); don't convert to lakh/crore notation in cells.
- Number formats applied per-column after writing (rate/sqft integers,
  price 2-decimal).
- Freeze header row (`ws.freeze_panes = "A2"`), bold the rate column.
