# Google Sheets: HYPERLINK Formula Construction & Drive Link Verification

When building structured firm/project dossiers in Google Sheets — scanning Drive folders for documents, mapping them to entities, and producing a comprehensive master sheet with clickable links.

## HYPERLINK Formula Patterns

### Single Link
```python
formula = f'=HYPERLINK("{url}","{label}")'
```

### Multiple Links in One Cell (CHAR(10) separated)
When a cell should contain multiple HYPERLINK formulas (e.g. "PAN", "GST", "COI" for one entity):

```python
formulas = []
for label, url in items:
    if url and label:
        escaped_url = url.replace('"', '""')
        escaped_label = label.replace('"', '""')
        formulas.append(f'HYPERLINK("{escaped_url}","{escaped_label}")')

if not formulas:
    cell_value = ''
elif len(formulas) == 1:
    cell_value = f'={formulas[0]}'
else:
    joined = ' & CHAR(10) & '.join(formulas)
    cell_value = f'={joined}'
```

Write with `valueInputOption='USER_ENTERED'` — this tells Sheets to evaluate the formula, not treat it as a string.

### URL Escaping

**Parentheses in HYPERLINK URLs break Google Sheets.** A URL like:
`https://drive.google.com/.../view?usp=drivesdk&ouid=1070117018...`
contains no parentheses. But if a file name or query has `(` or `)`, escape them:

```python
url = url.replace('(', '%28').replace(')', '%29')
```

Drive's `webViewLink` usually doesn't have parentheses, but when building URLs manually from file IDs, always add this escape.

## Drive Link Verification Pattern

When a sheet has HYPERLINK formulas referencing Drive files, verify every link:

```python
import re
from googleapiclient.errors import HttpError

def verify_hyperlinks(sheets, drive, spreadsheet_id, sheet_title):
    """Check every HYPERLINK formula in a sheet against Drive API."""
    result = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_title}'!A1:Z300",
        valueRenderOption='FORMULA'
    ).execute()
    
    for i, row in enumerate(result.get('values', [])):
        for j, cell in enumerate(row):
            for m in re.finditer(r'HYPERLINK\("([^"]+)"', str(cell)):
                url = m.group(1)
                file_id = None
                for pat in [r'/d/([a-zA-Z0-9_-]+)', r'/folders/([a-zA-Z0-9_-]+)']:
                    match = re.search(pat, url)
                    if match:
                        file_id = match.group(1)
                        break
                
                if file_id and len(file_id) > 20:
                    try:
                        meta = drive.files().get(fileId=file_id, fields='id,trashed').execute()
                        if meta.get('trashed', False):
                            # Report: file is trashed
                            pass
                    except HttpError as e:
                        if 'File not found' in str(e):
                            # Report: file ID doesn't exist
                            pass
```

### Fixing a Broken Link
```python
correct_url = drive.files().get(fileId=correct_file_id, fields='webViewLink').execute()['webViewLink']
formula = f'=HYPERLINK("{correct_url}","View")'
sheets.spreadsheets().values().update(
    spreadsheetId=SS_ID,
    range="'Sheet Name'!B44:B44",
    valueInputOption='USER_ENTERED',
    body={'values': [[formula]]}
).execute()
```

## Building a Structured Dossier Sheet from Drive Folder Scan

### Phase 1: Project Folder Discovery
```python
def find_folders(drive, query_name):
    """Find Drive folders by name (broad search)."""
    response = drive.files().list(
        q=f"name contains '{query_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields='files(id, name, parents)'
    ).execute()
    return response.get('files', [])
```

### Phase 2: Document Inventory
```python
def list_folder_contents(drive, folder_id, max_depth=2):
    """Recursively list files in a folder. Returns file metadata."""
    results = []
    page_token = None
    while True:
        response = drive.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields='nextPageToken, files(id, name, mimeType)',
            pageToken=page_token,
            orderBy='name'
        ).execute()
        for f in response.get('files', []):
            results.append(f)
            if f['mimeType'] == 'application/vnd.google-apps.folder' and max_depth > 0:
                results.extend(list_folder_contents(drive, f['id'], max_depth - 1))
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    return results
```

### Phase 3: Build the Sheet
Write all rows at once with `values().update()`, not row-by-row — Sheets batch writes are limited.

```python
body = {'values': rows, 'majorDimension': 'ROWS'}
sheets.spreadsheets().values().update(
    spreadsheetId=SS_ID,
    range=f"'{sheet_title}'!A1:Z{len(rows)}",
    valueInputOption='USER_ENTERED',  # ← CRITICAL for HYPERLINK formulas
    body=body
).execute()
```

### Phase 4: Apply Formatting
```python
requests = []
# Bold section headers
requests.append({
    'repeatCell': {
        'range': {'sheetId': sheet_id, 'startRowIndex': 0, 'endRowIndex': 1},
        'cell': {'userEnteredFormat': {'textFormat': {'bold': True, 'fontSize': 14}}},
        'fields': 'userEnteredFormat.textFormat'
    }
})
# Wrap text for entire sheet
requests.append({
    'repeatCell': {
        'range': {'sheetId': sheet_id},
        'cell': {'userEnteredFormat': {'wrapStrategy': 'WRAP'}},
        'fields': 'userEnteredFormat.wrapStrategy'
    }
})
sheets.spreadsheets().batchUpdate(spreadsheetId=SS_ID, body={'requests': requests}).execute()
```

## Workbook-Wide Link Audit & Project-Wise Restructure

Pattern for "check each drive link — some are not properly linked" + "rearrange project-wise / separate tables per project" on a multi-tab dossier workbook (used on 'DRA Group - Firm Dossiers Master (PS)', Aug 2026):

1. **Audit first, restructure second.** Pull EVERY tab with `valueRenderOption='FORMULA'`, regex-extract IDs (`/d/`, `/folders/`, `open?id=`, `spreadsheets/d/`), then `drive.files().get(fileId=..., fields='id,name,mimeType,trashed,size')` each unique ID. A 404 marks a dead link. Also grab `name` — real filenames expose **mislabeled links** (e.g. a cell labeled "View GST" whose ID actually resolves to a Reconstitution Deed) and give honest labels for the rebuild.
2. **Plain-text pseudo-links.** After extracting HYPERLINK IDs, re-scan raw cell text: `"Ranka Udaya Brochure.pdf.pdf"` or `"Oasis Master Plan"` sitting after a `|` in a "Drive Link" cell LOOKS linked but is plain text. Either link the real file if it exists (search Drive by name) or flag it in Remarks as needing upload.
3. **Dangling shortcuts.** A Drive shortcut (`mimeType=application/vnd.google-apps.shortcut`) resolves via `shortcutDetails.targetId`. If the target 404s, the link is dead even though the shortcut file itself exists — and MULTIPLE shortcuts can dangle at the same deleted ID (real case: two 'BESCOM Sanction Letter' shortcuts both pointed at one deleted PDF). Search Drive for the doc (`name contains 'BESCOM'`); if only dangling shortcuts remain, mark status ◐ and ask the user to re-upload rather than inventing a replacement link.
4. **Normalize URL forms.** Convert `drive.google.com/open?id=X` → `drive.google.com/drive/folders/X` (folders) or `file/d/X/view` (files); append `/view` to bare `file/d/X` URLs; keep `docs.google.com/spreadsheets/d/<id>/edit` for sheets. Join multi-link cells with `& CHAR(10) &`.
5. **Rebuild-then-format: derive positions, don't hardcode.** When restructuring a tab (values().clear → values().update with USER_ENTERED), DO NOT hardcode section/header row indices in the formatting pass. Read the sheet back and locate section headers by scanning values. Hardcoded indices drift with row counts (actual 0-based section starts were 3,23,41,59,72 vs a first guess of 3,21,39,57,71) and silently format the wrong rows.
6. **Scope discipline.** The user's link targets ONE tab (gid). Audit the whole workbook, but rebuild only the linked tab; report mislinks found on OTHER tabs and offer to fix them rather than editing without approval.
7. **Verify by read-back.** After rebuilding, re-extract every HYPERLINK from the rebuilt tab, re-check all IDs resolve via Drive API, and print status-count tallies (✅/◐/✗) as completion proof.

## Pitfalls

- **HTML-encoded ampersands in HYPERLINK URLs**: When a Drive URL contains `&ouid=...` in a HYPERLINK formula, the `&` is interpreted as a concatenation operator. Google Sheets handles this inside HYPERLINK by treating the whole URL as one string, but if you concatenate formulas with `& CHAR(10) &`, ensure each `HYPERLINK(...)` is self-contained with proper quoting.
- **Single HYPERLINK in a cell with surrounding text**: If you put `=HYPERLINK(...) & " extra"` the extra part must come through concatenation. Prefer the formula to be the sole content of the cell.
- **Link wrapping in Telegram/WhatsApp**: Never send bare `wa.me` or `api.whatsapp.com` URLs in Telegram — use the `whatsapp_link` tool. For Drive links, the display is fine.
- **File ID truncation**: Drive file IDs can be 33+ characters including `_-`. Verify the full ID is captured in the regex, not truncated.
- **`values().get().get('values', [])` skips empty rows**: Empty rows between data blocks in the returned array are implicit. When you read back the sheet to verify, rows with no content at all may be missing from the array — the `'values'` key only includes rows that have at least one non-empty cell.

## Workbook-Scale Link Audits — Dossier Master Sheet Pitfalls (2026-08)

When a master sheet holds many Drive hyperlinks ("check each Drive link"), audit at workbook scale and check label-vs-file correctness, not just resolvability:

- **Dangling-shortcut diagnosis for a 404**: when a file ID inside a HYPERLINK returns "File not found", search Drive for similarly-named entries (`name contains 'BESCOM' and trashed=false`). If the hits are shortcuts whose `shortcutDetails.targetId` equals the dead ID, the real file was *deleted* — the shortcuts dangle and the sheet link is genuinely broken; no relink will fix it. Fix = re-upload the missing PDF (or swap to the closest surviving doc) and note the action in the sheet. Do NOT "fix" by linking the shortcut while its target is missing.
- **Resolve shortcut targets before trusting them**: `drive.files().get(fileId=shortcut_id, fields='shortcutDetails')` returns `targetId`/`targetMimeType` — catches shortcuts pointing at deleted files (observed: two BESCOM sanction-letter shortcuts both targeting the same deleted 404 ID).
- **Valid-but-WRONG links**: a resolving link is not necessarily the right document. Fetch each file's real `name` via the Drive API and compare with (a) the HYPERLINK label and (b) the entity/person in that row. Real catches: Sevaganapalli 'View GST' → Reconstitution Deed (actual GST cert is a different ID); Srinivas Krishnappa 'Aadhaar' row → Kishan's PAN+Aadhaar PDF. Fix within scope; report cross-tab mislinks to the user rather than silently editing other tabs.
- **Plain-text tokens that should be links**: cells like `Oasis Master Plan` or `Ranka Udaya Brochure.pdf.pdf` reference a document with NO file ID. Search the project folder (`f"'{folder_id}' in parents and name contains 'Brochure'"`) and link the found file; if nothing exists, flag "referenced but no Drive ID — upload needed".
- **Canonical URL forms**: normalize to `https://drive.google.com/file/d/{id}/view` and `https://drive.google.com/drive/folders/{id}`. Legacy `/open?id=` works but is non-canonical; a bare `.../file/d/{id}` without `/view` opens but looks broken in a dossier.
- **Workbook-wide audit loop**: read every sheet with `valueRenderOption='FORMULA'`, regex `(?:/d/|/folders/|open\?id=)([a-zA-Z0-9_-]{15,})`, dedupe IDs, one `files().get` pass per ID (`fields='id,name,mimeType,trashed,size'`), count occurrences to spot reused IDs, then rebuild the target tab project-wise with `values().clear` + chunked `USER_ENTERED` writes and section formatting (header bars, borders, wrap, frozen rows) — same clear+rebuild rationale as `sheets-row-reorder-and-date-serial.md`.