# FlowOnTitle — Linking Drive Documents per Survey + Link Verification

Workflow for the DRAAS Sevaganapalli / Ranka Oasis TSR documentation spreadsheet
(`PART_V_FlowOnTitle` sheet). When the user says "add all documents to the flow
where they belong" and "verify each drive link", this is the pattern.

## Task shape
Inputs:
- The main docs spreadsheet (PART_I_DocFurnished + per-survey `Sy_*` sheets) — optional
- An EXTERNAL drive-index spreadsheet whose Sheet1 lists rows of
  `survey | description | drive link | linked doc | remarks`
- A target sheet (`PART_V_FlowOnTitle`) that already has per-survey title-flow rows

Goal: place every document from BOTH sources onto the correct survey, and verify
every drive link actually resolves to a real, correctly-named file.

## Step 1 — Read FULL, untruncated link values
This is the single most failure-prone step. When you build any in-memory map of
links, ALWAYS pull the raw cell values with

```python
sheets.spreadsheets().values().get(..., valueRenderOption='FORMATTED_VALUE')
```

and keep the FULL 44-char file IDs. Do NOT rely on:
- terminal/print output (truncates long IDs for display) — do not re-type from it
- any intermediate JSON you built from displayed/truncated strings earlier

In this session a map built from a truncated display caused 86 of 183 links to be
handed to the Drive API as 404s, then 19, then 12 — each "fix pass" only worked
once the map was rebuilt from the raw cell values. Symptom to watch for:
a file ID that Drive 404s on but whose prefix is a valid full ID.

**Rebuild, don't patch.** If you detect truncation, re-read the authoritative
source (the spreadsheet cells themselves) and regenerate the whole map. A
`deedno_map` built once from good values and stored in `/tmp` can silently carry
bad data into later passes — rebuild it from source each time you change source data.

## Step 2 — Map docs to surveys
- Parse each doc description for a registration number `(\d{3,6})/(\d{4})` → key.
  Build `deedno_map[doc_no] = full_link` from BOTH sources (exclude FMB/patta/online).
- For revenue docs (FMB, UDR/A-Register, Adangal, EC, Patta): read the per-survey
  `Sy_*` sheets, and under the `DOCUMENT TYPE` header each row is
  `category | filename | link`. Classify by `name.lower()` keywords
  (`fmb`→FMB, `adangal`/`kist`→Adangal, `udr`/`a register`/`old settlement`→AReg,
  `encumbrance`→EC, `patta`→Patta).
- Match a doc to a survey by prefix/series: `158/1C3` or general `158/1` applies to
  all `158/1*` subdivisions; `166/3D,166/3F,...` expands to each listed survey.
- Keep a per-survey `merged` dict with dedupe by link.

## Step 3 — Place docs in the target sheet
Two placement surfaces:
1. **Survey HEADER rows** carry FMB / A-Register / Adangal / EC / Patta links in
   dedicated columns (e.g. cols N–R).
2. **Transaction rows** carry the DEED link in the deed-link column. Match the deed
   by its doc number to `deedno_map` and overwrite the truncated link.

For documents that don't fit either surface (sale agreements, DC/LHC, survey docs),
append a **📎 DOC ANNEXURE block** after each survey's last transaction row:
- header row: `['', '📎 {survey}', '┌─ DOCUMENTS ─', ... , 'DOC ANNEXURE', ...]`
- one row per doc: `['', '📎 {survey}', '│', '', 'Doc', desc, CATEGORY, ..., link]`
- trailer: `└─` row

Annexure blocks keyed to the SURVEY HEADER rows: walk the flow, and whenever a new
survey's HEADER row appears, flush the PREVIOUS survey's annexure first. This keeps
the block attached to the right survey.

## Step 4 — Verify every link via Drive API
```python
for fid in unique_ids:
    meta = drive.files().get(fileId=fid, fields='name,mimeType,trashed').execute()
    verified.append((fid, meta['name'], meta['mimeType'], meta['trashed']))
```
Collect IDs from columns that hold links (deed link col, FMB/AReg/Adangal/EC/Patta
cols, annexure link col). Compare each file's returned `name` against the expected
document to confirm the RIGHT file is attached (not just that it resolves).

Summary numbers to report: total unique IDs, how many resolve OK, how many 404.
Flag 404/broken links ⚠️ in the status column AND append them to the worksheet's
MISSING_DOCUMENTS sheet (rows "S.No | Survey | ⚠️ BROKEN LINK — description |
why | source = Link verification <date> | priority | action").

## Step 5 — Append external docs to PART_I_DocFurnished (with highlight)

When the user asks to also add every external-index doc to the **PART_I_DocFurnished**
sheet itself ("add all the other documents from this spreadsheet to PART I"), and to
highlight what was added:

1. **Dedupe by NORMALIZED link, not doc number.** Build the set of PART_I links as
   `url.split('?')[0]` and keep only external rows whose normalized link is not in
   that set. Deduping by parsed `(\d+)/(\d{4})` doc numbers RE-ADDS docs already in
   PART I (same file, different description wording) — a real trap hit Aug 2026.
   Also dedupe WITHIN the external list by normalized link (the index itself had a
   duplicated row).
2. **Compose rows with the sheet's exact column order** — PART_I is
   `S.No | Date | Document Description | Drive Link | Matched File / Notes | Status`.
   Parse the date from leading `YYYYMMDD`/`DDMMYYYY` in the description
   (`19640622` → `22.06.1964`); fall back to `-`.
   Status for new rows: `✅ Added from ext index`.
3. **Append at the first empty row** — find the last non-empty row by scanning the
   sheet, then write starting there. Chunk if >400 rows.
4. **Highlight the added range** via `batchUpdate` — yellow fill + bold:
   ```python
   {"updateCells": {"range": {"sheetId": part1_sheet_id,
        "startRowIndex": start_0based, "endRowIndex": end_0based+1,
        "startColumnIndex": 0, "endColumnIndex": 6},
     "rows": [{"values": [{"userEnteredFormat": {
         "backgroundColor": {"red": 1.0, "green": 0.95, "blue": 0.55},
         "textFormat": {"bold": True}}}] * 6}] * nrows,
     "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat.bold"}}
   ```
   Get the sheet's `sheetId` from `spreadsheets().get(fields='sheets.properties')`.
   Verify the fill landed via a `spreadsheets().get(ranges=..., fields='sheets(data(rowData(values(userEnteredFormat(backgroundColor)))))')` readback.
5. **Log name-only references** — rows in the external index whose "Linked Doc"
   column has a filename but NO drive link (e.g. "Rest of the documents.pdf",
   "UDR A REGISTER 1983-86.pdf") become `[Reference name only] <name>` rows with
   status `📄 Name only` — they are tracking entries, not links.
6. **Add a legend row** below the appended block: `▲ Rows X-Y highlighted YELLOW =
   added from external Drive index (<id>) on <date>.` Keep it in a single column to
   avoid range/column-count 400 errors when the row has fewer cells than the range.
7. **Report the S.No range + count added**, and distinguish linked (has URL) from
   name-only rows in the summary. Offer to search Drive for the name-only files.

## Checking the rest of the workbook

When the user says "check other sheets in the workbook": list all sheet titles via
`spreadsheets().get(fields='sheets.properties')`, then read each candidate. Sheets
like FLOW_CHARTS / PART_III_Schedule are structural reference sheets (trees,
schedules) — no document links to add. A sheet may read as empty (0 rows) because
it is genuinely unused — confirm the exact title via the properties list before
concluding (the CMS report sheet in this workbook was titled
`Documents as per CMS report` and was empty).

## Pitfalls
- **Truncated IDs masquerading as full ones** — a truncated ID fails Drive 404 but
  its prefix matches a valid full ID. Detection: `[f for f in all_good_ids if f.startswith(trunc)]`.
- **Dedupe by doc number re-adds duplicates** — dedupe against the target sheet by
  normalized link (`url.split('?')[0]`), never by parsed registration number alone.
- **Patching forward is a trap** — each new link source can re-introduce fresh
  truncation/dedup issues. Always end with a full Drive-API verification pass and
  report actual numbers.
- **Batch writes > ~400 rows × 19 cols**: chunk the values().update calls.
- **Don't drop PART_I docs already embedded on transaction rows** — verify coverage
  is complete, don't blindly append duplicates.
- **Broken links in the SOURCE are real** — if Drive 404s on an ID that is present
  verbatim in the external index / PART_I, it is a genuinely bad link on the user's
  side. Flag it for re-upload, don't fabricate a replacement.
- **Legend/note rows with fewer cells than the write range** — write to a single
  column range (`A176:A176`) or pad cells, or Sheets raises a 400
  "tried writing to column" error.
