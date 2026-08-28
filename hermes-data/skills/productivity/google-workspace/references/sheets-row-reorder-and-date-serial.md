# Google Sheets: Row Reordering + Date-Serial Pitfalls

Two hard-won patterns from real DRAAS sheet edits (2026-08-17, sorting the Satvik Developers Byadarahalli documents tab).

## 1. Reordering rows: prefer CLEAR + REBUILD over moveDimension

**The fragile path (what NOT to do):** `moveDimension` on ROWS to permute data rows.
It preserves formatting/hyperlinks BUT the move math is easy to get wrong: each
`moveDimension` shifts 0-based row indices, source/destination indices must be
recomputed per move, and a wrong permutation silently scrambles rows with NO
error. Observed failure: computing 10 moves that "succeeded" (batchUpdate OK)
but left sale deeds and agreements interleaved instead of grouped. Recovery
took a full rebuild anyway.

**The reliable path (use this first):** compute the sorted/grouped table in
Python, then:
1. `values().clear` the whole data range (`Sheet1!A1:J50`)
2. `values().update` the entire rebuilt grid with `valueInputOption='USER_ENTERED'`
3. **Convert URL columns to `=HYPERLINK("url","url")` formulas** before writing
   so document links stay clickable (plain URL text written via API does NOT
   auto-link reliably).
4. Verify by reading back the whole range and eyeballing row identity (survey
   number, date) vs expected order.

Skips the index math entirely; deterministic and verifiable. Only loss vs
moveDimension: exotic per-cell formatting (fills, borders, merged cells) must be
re-applied via `updateCells` after the rebuild — straightforward for headers,
subtotal rows, section titles (bold + background color in one batchUpdate).

Formatting recipe (after rebuild):
```python
reqs.append({'updateCells': {
    'range': {'sheetId': GID, 'startRowIndex': idx0, 'endRowIndex': idx0+1,
              'startColumnIndex': 0, 'endColumnIndex': 8},
    'rows': [{'values': [{'userEnteredFormat': {
        'textFormat': {'bold': True}, 'backgroundColor': {'red':0.85,'green':0.87,'blue':0.90}}
        } for _ in range(8)]}],
    'fields': 'userEnteredFormat(textFormat,backgroundColor)'}})
```

## 2. Excel serial-number dates under en_US locale (DD-MM vs MM-DD trap)

Symptom: a date column in an Indian-user spreadsheet contains numbers (e.g.
`45231`) instead of text dates. `valueRenderOption='FORMATTED_VALUE'` shows
"11-01-2023"; `UNFORMATTED_VALUE` reveals the raw serial.

The trap: the sheet's locale is `en_US`, so the user's typed **11-01-2023
(DD-MM, Indian meaning 11 Jan 2023)** was parsed as **MM-DD → Nov 1, 2023**
(serial 45231). The formatted display still shows 11-01-2023 — looks right,
is wrong by 9.5 months. This corrupts any date-based sort.

Diagnosis checklist:
1. Read BOTH `FORMATTED_VALUE` and `UNFORMATTED_VALUE` for the date column.
2. If ANY value is a number/serial → locale parsing happened. Convert with
   `date(1899,12,30) + timedelta(days=int(serial))` to see the true stored date.
3. Cross-check the document itself for the intended date — filename
   (`dtd 11-01-2023`), registration FY (`12781/22-23` means FY 2022-23, so the
   date CANNOT be Nov 2023), or body text. The filename is authoritative for
   DD-MM vs MM-DD.
4. Fix the cell before sorting: write the intended date back as text
   (`11-01-2023`) so it no longer round-trips through the locale.
   Report the fix to the user — they don't know the cell is silently wrong.

## 3. Permission ladder for user-shared sheets

- Read 403 on `values().get` / `spreadsheets().get` → file not shared yet.
  Ask the user to share.
- Read works but `batchUpdate` 403 → user granted **Viewer**, not Editor.
  Row moves / value writes / format changes ALL need Editor. Ask explicitly:
  "change psingh@draas.com (or whoever) from Viewer to Editor."
- `drive.permissions().list` returns `insufficientFilePermissions` even for
  files you CAN read — don't use it to diagnose; use `values().get` as the
  access probe (try read, then try a harmless write).
- Always re-verify after permission changes: read the sheet, confirm you can
  write one cell, then do the real edit.