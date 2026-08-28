# Inventory Sheet Extraction — Circled Plots → Excel / Google Sheets

Context: Bharat asks "pull out only details for the plots we circled and create an excel sheet"
(after master-plan circling). Source file is the user-uploaded `Oasis Master Inventory Sheet (3).xlsx`
(live Drive copy: `Oasis Master Inventory Sheet` 1jHjOIUQSMVwVQewFES2d77D9SaHK2DcUbbTBvwwRH8o).

## Sheet anatomy (verified Aug 2026)
- Two sheets: `Master Sheet ` (A1:Z1017, the one to use) and `As per sanction layout` (sparse — skip).
- Row 1 = group headers ("Dimensions in M", "Dimensions in Feets & Inches", "Peripherals", "Villa FSI", "Villa SBUA"); Row 2 = real column headers; data starts Row 3.
- Columns: 1 Plot#, 2 Facing, 3 Corner, 4 Shape, 5-8 E/W/N/S (M), 9 Area sqm, 11-14 E/W/N/S (ft), 15 Area sft, 16-19 Peripherals (East/West/North/South by), 20-22 Villa FSI (Grove 1.75 / Vista 1.8 / Reserve 1.85), 23-25 Villa SBUA (same trio).

## Critical: individual rows AND merged-pair rows coexist
The revised plan (03.08.26) merges adjacent small plots into full-size plots with pair labels
(93-94, 95-96, 105-106, 107-108, 109-110). The inventory sheet contains BOTH:
- individual rows (93, 94, 95, 96, ... with FSI/SBUA values), AND
- merged rows with the plan-style label as a string, e.g. `"93"-94`, `"95"-96`, `"105"-106`, `"107"-108`, `"109"-110`.

RULE: for a circled merged plot, extract the **merged row** (label matches the plan label).
Individual rows are the OLD pre-merge plots. Merged rows have FSI/SBUA blank (None) — that is
expected from the source, not an extraction bug. Offer Bharat the individual FSI values as an option,
don't silently invent them.

## Extraction recipe (openpyxl)
1. `openpyxl.load_workbook(path, data_only=True)` — data_only or formulas come back as formulas.
2. Find target rows by scanning col A; targets may be float (92.0) or string (`"93"-94`).
3. Build output workbook with clean headers (see column map above); write Plot# as the clean label
   (strip the embedded quotes from source strings — `"93"-94` → `93-94`).
4. Format: bold header fill, thin borders, right-align numerics, freeze panes below header,
   title row merged across. Column widths ~9-14.
5. Verify by re-reading the saved file and printing key cols (Plot#, Facing, area) before delivering.

## Delivery
- Send the .xlsx via MEDIA: path so Bharat gets the file in chat.
- ALSO upload to Drive (see phone-safe-plan-delivery.md) — he saves these in the project folder.
  Upload target for Oasis plans: `Plot 119 Legal Set` folder 1lVlRlVKzHc4ID4H7e_ec3toSSfiYeo1w
  (contains the old `Oasis Master Plan 18.07.26.pdf`; found via `name contains 'Oasis'`).
- Set permission role=reader type=anyone so the Sheets link opens without an auth prompt.
- Note: uploaded xlsx opens in Google Sheets directly (webViewLink); mention that in chat.

## Known plot mapping (Aug 1 circled set → new plan)
Old (18.07.26) → New (03.08.26): 119→119, 118→118, 117→117, 95→95-96, 93→93-94, 92→92,
105→105-106, 107→107-108, 109→109-110. When the user names old numbers, translate to the new
label BEFORE looking up rows.
