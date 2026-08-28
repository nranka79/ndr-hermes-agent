# Google Sheets: structural rebuild (extent cols, section splits, totals)

Session-proven pattern (2026-08, "Satvik Developers(PS) - Byadarahalli Legal Documents").
Use when a sheet needs MULTIPLE structural edits at once: reorder rows, add a column
(extent), split rows into sections, insert subtotal/total rows.

## Rule: single reorder → moveDimension (see sheets-row-sorting.md); multi-edit → REBUILD

Incremental `moveDimension` breaks when the target order requires many overlapping
moves — the naive index-tracking algorithm reorders wrongly and scrambles rows
("move row 6 -> dest 5, row 7 -> dest 6, ..." then rows land in wrong places).
Do NOT debug the move math for several edits. Rebuild the tab instead:

1. Read the full current values (`FORMATTED_VALUE`) — you have every row.
2. `values().clear` the whole used range (e.g. `A1:H50`).
3. Build the target grid in Python: header row, section titles, data rows in desired
   order, subtotal rows, grand-total row.
4. Convert Document Link cells to clickable formulas BEFORE writing:
   `=HYPERLINK("https://...","https://...")` — write with `valueInputOption='USER_ENTERED'`.
   Plain URL text written via the API loses clickability.
5. `values().update` the whole grid at `A1`.
6. Style with `updateCells` batchUpdate: bold + background for header, section titles,
   subtotal (yellow), grand total (green). Extent column centered for data rows.

## Inserting section/total rows (if you need to insert, not rebuild)

- `insertDimension` (ROWS) with 0-based startIndex, then every row BELOW shifts —
  recompute anchors against the post-reorder layout before inserting the next row.
- After insertion, re-read with `FORMATTED_VALUE` and verify positions.

## Indian land extent columns (Acres-Guntas)

- Notation `A-G`: e.g. 2A 35G, 0-12, 4-00. 40 guntas = 1 acre.
- Flag kharab extents: `221/2 3-38 (K)` / `181 4-00 (K)`; net of kharab is a separate
  figure. 221/2 kharab 0-38 + 181 kharab 0-06 = 1A 04G combined.
- Split by document type: SALE DEEDS (registered) vs AGREEMENTS/GPA. When ATS + GPA
  cover the SAME survey number, the land total counts the parcel ONCE (unique-land
  total) — note this in the subtotal row; count documents in the section header.

## Reconciling a sheet to a map/table total ("add missing to total 42 acres")

- Compute section sums in guntas (`acres*40 + guntas`) and compare to the reference
  total. The delta identifies the missing survey numbers.
- Example: map 42A 27.08G vs sheet 33A 07.08G → delta = P-parcels 45/P3 (2-00),
  45/P5 (4-00), 45/P7 (4-00) = 10A. After adding them the sheet grand total was
  43A 07.08G, still +0-20 over the map because the sheet includes 41/11 (0-20G,
  registered but not drawn on the sketch). Explain the scope difference explicitly
  instead of forcing numbers to match.
- Missing-doc gap: if a survey has no folder/file ANYWHERE on Drive (45/P7 had no
  Legal-Files-Index section, no folder, no file under several search variants),
  add the row with "(Link PENDING)" and flag it to the user — do not fabricate a link.

## Verify

- Re-read the final grid and print survey/extent/date columns — assert the subtotal
  and grand-total cells contain the expected literals, and spot-check arithmetic
  (sum the per-row guntas independently).