# Editing a Drive file that is stored as an Office document (.xlsx / .docx)

Verified 2026-10-14 on `Yerthiganahalli_Airport_Rd_Villa_CF_Model_M1M4.xlsx`
(id `1evITy9FbL9S6plN7VgfoSG2qWwqsB_7S`, owned by Sarthak).

## The constraint

- The **Sheets API refuses Office files**: `spreadsheets().get()` / `values()` →
  *"This operation is not supported for this document. The document must not be an Office file."*
  Same for the Docs API on `.docx`.
- `drive.files().update(fileId=…, body={"mimeType": "application/vnd.google-apps.spreadsheet"})`
  **does NOT convert in place** — the call succeeds and returns the file, but `mimeType` is unchanged.
- `files().update(..., media_body=…, body={"mimeType": google-sheets})` fails with
  `HttpError 400 … "Invalid MIME type provided for the uploaded content." (location: media.mimeType)`.
- Conversion on upload works only on **create / copy**:
  `files().create(body={"mimeType": google-sheets}, media_body=<xlsx>)` and
  `files().copy(fileId=…, body={"mimeType": google-sheets})`.

So: you cannot turn the user's file into a native Sheet without changing its id. Do not try.

## Recipe — edit in place, keep the file id, URL and format

1. **Back up first.** `files().get_media(fileId=…)` → save the bytes as `*_ORIGINAL_BACKUP.xlsx`.
   Never edit without this.
2. Edit the bytes with **openpyxl** (`load_workbook(data_only=False)`). It preserves formulas,
   styles, number formats, merged cells and **data validations** (verified: the three route
   dropdowns at `C86`/`C87`/`G86` survived the round-trip).
3. `files().update(fileId=<SAME id>, media_body=MediaFileUpload(path, mimetype=<office mime>))`.
   File id, share link and version history survive; Drive just bumps `version`.

Never hand back a NEW file — the user's shared link must stay valid.

## Verifying COMPUTED values (the reason this matters)

openpyxl output cannot be recalculated locally (no LibreOffice in the container, `formulas`
not installed), so verification goes through a throwaway Google-side conversion:

1. `files().copy(fileId=<live id>, body={"name": "__TMP_verify", "mimeType": "application/vnd.google-apps.spreadsheet"}, fields="id")`
2. Read `values().get(..., valueRenderOption="UNFORMATTED_VALUE" | "FORMATTED_VALUE")` for the cells that matter.
3. `files().delete(fileId=<temp id>)`, then confirm `files().list(q="name contains '__TMP_'")` is empty.

**Conversion fidelity (measured):** xlsx → Google Sheet preserved every formula; the only diffs
were Google stripping quotes around single-word sheet names (`='Dashboard'!B19` → `=Dashboard!B19`).
Harmless — and it means a converted copy is a trustworthy oracle for the real file.

## Pitfalls

- **Read quota**: Sheets API is **60 read requests/min/user**. Sweeping a 21-sheet workbook one
  range at a time trips `429 RATE_LIMIT_EXCEEDED`. Use `values().batchGet(ranges=[…])` (~7 ranges
  per call) and/or `time.sleep(60)` then retry. Batch first; sleep only if still throttled.
- **MergedCell**: writing a merged range's non-anchor cell raises
  `AttributeError: 'MergedCell' object attribute 'value' is read-only`. List merges with
  `[str(r) for r in ws.merged_cells.ranges]`, and wrap bulk writes in `try/except AttributeError`
  so you collect the failures instead of dying mid-apply — then fold those labels into the
  range's top-left anchor.
- `files().get_media(fileId=…)` needs no `alt=media` when called through the client library.
- A file can be an Office document *and* still open as a Sheet via the Drive link
  (`…/edit?rtpof=true`). That is normal and does not make it API-editable.
