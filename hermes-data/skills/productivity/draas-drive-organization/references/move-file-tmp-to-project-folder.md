# Moving a file out of TMP into its project folder (Drive API mechanics)

Worked 2026-09-22: NDR uploaded a DXF to the root TMP folder on Drive because
Telegram rejects `.dxf` ("Unsupported document type '.dxf'"). Job: rename, move
TMP → target project folder (`01_Approvals_and_Title`), verify, and append to
the project's document index spreadsheet.

## HARD PITFALL — addParents/removeParents are QUERY PARAMS, not body fields

googleapiclient Drive v3 `files().update()` silently IGNORES parents changes
passed in the body:

```python
# WRONG — returns success, parents unchanged (silent no-op, verified 2026-09-22)
drv.files().update(fileId=ID, body={'addParents': TARGET, 'removeParents': TMP}).execute()

# CORRECT — pass them as kwargs to the method (they map to URL query params)
drv.files().update(fileId=ID, addParents=TARGET, removeParents=TMP,
                   fields='id,name,parents').execute()
```

The wrong form does NOT error — it returns the file metadata with the OLD
parent list. That's exactly why "success" + no verification == future 404s /
wrong-folder finds. Always read back `parents` after the move and assert the
TARGET appears and TMP does not.

Full worked sequence:
1. Find the file in TMP by keyword (`name contains 'Allalasandra'`) — NDR may
   have named it differently from the chat filename.
2. Rename in-place first (optional, see naming below) or just move.
3. Move with the kwarg form; wait ~2s; `files().get(fields='id,name,parents,webViewLink')`
   and print parents.
4. Verify TMP no longer contains the keyword (list TMP filtered by name).
5. Append to the project's document index sheet (see next section).

## Document index append (land/survey projects)

DRAAS land projects carry an "Extracted Document Index" Google Sheet
(e.g. `Allalsandra - Extracted Document Index`, SSID `1LwzRjdaWEp06kd7Ek1cCCW5FpjYD4Tb7rR3oMjNCq6c`,
tab `Document Index`, columns: `# | Document Name | Original Pages | Description | Size (KB) | Drive Link`).

- Appending rule: read `A1:F40`, compute next `#` = max(existing numeric #) + 1
  (do NOT hardcode 28/29 — always from the live sheet), append with
  `values().append(range="Document Index!A1", valueInputOption="RAW")`, verify
  via returned `updatedRange`.
- When building the row: `Size (KB)` must be a STRING — `str(round(int(size)/1024))`.
  Dividing a googleapiclient `size` string directly crashes with
  `TypeError: unsupported operand type(s) for /: 'str' and 'int'` AFTER the
  upload already succeeded — the file exists; only the sheet row failed; retry
  the append with the string cast.
- Description column: full content identity (Sy numbers, extents, taluk),
  e.g. "Village FMB/pakka-book sheet - Allalasandra (Attalikoppa), Yelahanka Taluk:
  Sy 14/1 (1 ac 28 g), Sy 15, Sy 13 etc., boundary measurements". For a DXF note
  it is the digital equivalent of the paper sketch (e.g. "CAD drawing, rev R12").

## File naming for Allalasandra / Ranka Northstar land records

`YYYYMMDD_RankaNorthstar_Allalasandra_<Description>.pdf|.dxf`, e.g.
`20260922_RankaNorthstar_Allalasandra_VillageFMB_Sheet_Attalikoppa_Sy14-1_Sy15.pdf`
and `20260922_RankaNorthstar_Allalasandra_Sy14-1_SurveyBoundary_FIXED_R12.dxf`.
Home for land records / title docs = `Ranka Northstar > 01_Approvals_and_Title`
(folder `1lKNIIfme5Kv7vvzwmCVvXkLSsjJJMUy5`); survey/engineering drawings live in
`02_Engineering_and_Design`. The pre-existing `20260320_..._FMB_Sketch.jpg` is a
hand-drawn hissa sketch (single Sy split into 6) — the official village FMB sheet
is a DIFFERENT record; both stay on file.

## Duplicate-check before filing

When NDR sends a scan "if it's already on record keep the better copy":
- Search Drive by the doc type FIRST (`name contains 'FMB'`, `'Sketch'`, `'Tippani'`,
  `'village map'`, `'Document Index'`) — scan results for BOTH the doc and any
  existing index spreadsheet.
- Compare content on the actual page (vision) — different docs can share a name
  (FMB sketch vs village FMB sheet). Only treat as duplicate if content matches,
  not name.
- If a new doc: rename, file, AND append to the index (NDR explicitly asks for
  index updates for these land-record filings).