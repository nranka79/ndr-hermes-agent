# Drive Folder → Spreadsheet Index (per-survey / per-category sheets)

When the user shares a Drive folder link and asks for a spreadsheet listing all files
grouped by category (survey number, project, etc.) — one sheet per category, columns
Sl No / Category / File name / Drive link / Date.

## Identity: which account can see the folder (CRITICAL)

The session telegram id often does NOT map to the user you think it is.

- `HERMES_SESSION_USER_ID=[REDACTED-TID]` (Prakash's chat) resolves via vault to
  `ndr-[REDACTED-TID]` — i.e. **ndr's** identity, NOT psingh's. Loading `google-draas`
  under that session authenticates as ndr@draas.com and the folder 404s.
- psingh's own token lives under canonical uid `psingh-[REDACTED-TID]` and is reachable
  with `HERMES_SESSION_USER_ID=psingh` (slug form resolves cleanly).
- Always pass `service_name='google-draas'` to `build_service()` — the default is
  `google`, which has NO token for anyone and yields a false not-authorized error.

Working header for all GWS calls in this flow:

```bash
HERMES_SESSION_USER_ID=psingh /opt/hermes/.venv/bin/python3 script.py
```

```python
from tools.gws_auth import build_service
svc = build_service('drive', 'v3', service_name='google-draas')   # NOT bare build_service()
```

Verify identity first with `about().get(fields='user(emailAddress)')`; the folder
`files().get(fileId=...)` check is a fast second probe.

If the folder still 404s under the resolved token, the folder owner is a THIRD
account (observed: bestamanahalli owned by admin2.blr@draas.com, shared to psingh).
Then `send_oauth_url(login_hint=<user's email>)` and retry after the user taps.

## Walking a large folder tree (2,000+ files, 90+ subfolders)

Serial recursion times out (300s+). Parallel BFS with ThreadPoolExecutor works:

- **NEVER share one service object across threads** — googleapiclient's HTTP
  transport is not thread-safe; concurrent `files().list()` on one service raises
  `SSL: RECORD_LAYER_FAILURE` intermittently and silently skips folders.
  Fix: thread-local services via `threading.local()` + `build_service()` per thread.
- BFS queue of `(folder_id, path)`; 6-8 workers, batches of ~20 folders.
- `pageSize=1000`, `supportsAllDrives=True`, `includeItemsFromAllDrives=True`.
- Collect `id, name, mimeType, modifiedTime, createdTime` — enough to build links
  and dates without a second pass. Save to JSON before building the sheet.

## Survey-number / category extraction from folder names

Folder names are noisy: `100-1      16.50 guntas`, `Sy No. 130-3    11.08 Guntas best`,
`Sy142-8 best`, `Besthamanahalli Sy106-3`, `142-3,84-2 best`, `120-1,B`.

Normalization rules that worked:
- strip leading `sy | s.y | survey no. | sy no. | SY NO` (case-insensitive)
- strip trailing tokens `best | bet | ats` (and area text like guntas)
- collapse whitespace, trim trailing dots/underscores
- `142-3,84-2` and `120-1,B` are legitimately multi-value survey keys — keep as-is
- when the SAME survey number appears in multiple folders with different areas
  (`100-1 16.50 guntas` vs `100-1 8.04 guntas`), keep the area suffix in the sheet
  title to disambiguate — do NOT merge the two folders
- one top-level file (e.g. `Besthamanahalli reqied Documentes list.pdf`) is a file
  at root, not a folder — it still gets its own sheet; it shows up as a top entry

## Building the spreadsheet (90 sheets)

- Create with a `Summary` sheet (Sl No / Category / File Count) at index 0.
- `batchUpdate addSheet` in chunks of ≤50 requests (API limit).
- Write all values in one `values().batchUpdate` with `valueInputOption: USER_ENTERED`
  — chunk the valueRanges list (25/call) to avoid timeouts.
- Sheet titles must be ≤100 chars and unique; sanitize category labels first.
- Drive link format: `https://drive.google.com/file/d/<FILE_ID>/view`.
- Date column: use `modifiedTime` date portion (`[:10]`) — labeled
  "Date (Drive modified)"; most scans show upload dates.

## Formatting gotcha

`addSheet` responses do NOT give you a usable sheetId mapping. After adding all
sheets, fetch `spreadsheets().get(fields='sheets.properties')` to get
`title → sheetId`, THEN build `repeatCell` / `updateSheetProperties` /
`updateDimensionProperties` requests with explicit sheetIds. (Bold header,
freeze row 1, widen link column ~340px.)

Also: `foregroundColor` (e.g. white header text) is NOT a top-level field of
`userEnteredFormat` — nest it inside `textFormat` (`{'textFormat': {'bold': True,
'foregroundColor': {...}}, 'backgroundColor': {...}}`). Top-level placement returns
HttpError 400 "Unknown name foregroundColor". Same fix applies to any sheet-build
script; see `deed-index-flat-sheet.md` for the full pattern.

## Delivery

- Spreadsheet created via the requesting user's token is owned by them — verify
  `files().get(fields='owners')` shows the right email.
- Deliver the link in a plain code block (Telegram breaks URLs); mention searching
  Drive by spreadsheet name as fallback.
- Report: sheet count, file count, spot-check one sheet, and note any data caveats
  (duplicate filenames across surveys are distinct Drive files with distinct links).
