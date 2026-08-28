# Google Sheets: row reordering, permission traps, date serials

Session-proven patterns (2026-08, sorting "Satvik Developers(PS) - Byadarahalli Legal Documents").

## Sorting rows OLD→NEW while preserving hyperlinks & formatting

The wrong way: read values, sort in Python, `values().update()` the range back.
This DESTROYS cell hyperlinks (Document Link columns) and any cell formatting —
the URLs become plain text.

The right way: use `moveDimension` batchUpdate requests to physically move rows.
Formatting, hyperlinks, and data stay glued to their rows.

Algorithm (data rows only, header stays row 1):

```python
# rows: list of lists from values().get() — each tagged with its ORIGINAL sheet row index (2..N)
# sort key: parsed transaction date, None-dates sink to the end
data = [(parse_date(row[5]), sheet_row_idx, row_values) for ...]
data.sort(key=lambda x: (0 if x[0] else 1, x[0] or date.max))

order = [d[1] for d in data]              # desired sequence of original sheet indices
current = list(range(2, 2 + len(data)))   # current top-to-bottom sheet indices
moves = []
for t, target_id in enumerate(order):
    p = current.index(target_id)
    if p == t:
        continue
    moves.append({'moveDimension': {
        'source': {'sheetId': GID, 'dimension': 'ROWS', 'startIndex': p, 'endIndex': p + 1},
        'destinationIndex': t}})
    current.pop(p); current.insert(t, target_id)

sheets.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={'requests': moves}).execute()
```

- Compute moves against the LIVE sheet layout (re-read after any failed run — indices shift).
- Verify afterwards by re-reading with `FORMATTED_VALUE`.
- Check `gridProperties`/`merges`/`conditionalFormats` first — merged cells complicate row moves.

## Permission trap: read works, write returns 403

`spreadsheets().values().get()` succeeding does NOT mean you can write.
`batchUpdate` returning `<HttpError 403 "The caller does not have permission">` means the
shared account (psingh@draas.com / google-draas) has **Viewer, not Editor**.

- Drive `permissions().list()` also returns 403 "insufficient permissions" when you're not an editor.
- Don't burn time debugging the API — tell the user to change the share to **Editor**.
- If the user says "access updated" and only read works, they granted Viewer. Ask for Editor again explicitly.

## Date serials under en_US locale: 45231 ≠ 11-Jan-2023

A spreadsheet with **locale en_US** parses typed `11-01-2023` as
**November 1, 2023** and stores serial `45231` — even though Indian document
convention means **January 11, 2023** (dd-mm-yyyy).

- Read with `valueRenderOption='UNFORMATTED_VALUE'` to detect serials (int/float in the Date cell).
- Convert serials: `date(1899, 12, 30) + timedelta(days=int(serial))` → gives 2023-11-01 for 45231.
- **Cross-check against the document itself**: filename (`dtd 11-01-2023`), or Karnataka
  registration number FY segment (`/22-23` = registered by 2023-03-31, so Nov 2023 is impossible).
  The sheet's serial is then a data-entry artifact — sort by the DOCUMENT date, and fix the cell.
- Locale lives in `spreadsheets().get(fields='properties(locale,timeZone)')` — check it before trusting date cells.