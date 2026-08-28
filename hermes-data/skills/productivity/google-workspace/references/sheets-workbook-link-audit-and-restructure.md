# Sheets Workbook-Wide Drive-Link Audit & Project-Wise Restructure

Pattern validated Aug 2026 on the DRA "Firm Dossiers Master (PS)" workbook — user asked to "check each Drive link — some are not properly linked" and rearrange a checklist sheet project-wise.

## Phase 1 — Workbook-wide link audit

Read EVERY sheet with `valueRenderOption='FORMULA'` (links live inside `=HYPERLINK("url","label")`), extract IDs with:

```python
id_pat = re.compile(r'(?:/d/|/folders/|open\?id=|spreadsheets/d/)([a-zA-Z0-9_-]{15,})')
```

Then `drive.files().get(fileId=id, fields='id,name,mimeType,trashed')` each unique ID. Classify:
- `File not found` (404) → broken/deleted link.
- `trashed:True` → link to trash.
- OK + real filename → compare against the cell's LABEL. **Mismatch detection is the gold:** labels like "View GST" pointing at a "Reconstitution Deed…pdf" are objectively wrong links (found: Seveganapalli GST → recon deed; Srinivas Krishnappa Aadhaar → Kishan's PAN+Aadhaar doc).

Other defects found in the same pass:
- **Dangling shortcuts**: a Drive shortcut's targets can be deleted. `files().get(shortcut id, fields='shortcutDetails')` → `targetId` may 404. The shortcut ID itself is clickable but the target is gone — the source PDF must be re-uploaded.
- **Plain text where a link should be**: "Oasis Master Plan" / "Ranka Amber RERA filings (multiple docs)" as raw text after a `|`. Fix by locating the real file (name search in Drive/project folder) and hyperlinking.
- **Filename-only references** ("Ranka Udaya Brochure.pdf.pdf") that are NOT links — check the project folder for the actual PDF (it usually exists; get its ID).
- **Non-canonical URL shapes**: `/open?id=…`, missing `/view`, `?usp=drivesdk` — canonicalize to `/file/d/<id>/view` or `/drive/folders/<id>`.

## Phase 2 — Project-wise rebuild (checklist → per-project tables)

- Keep the same tab/gid. Build a `rows` list: title row, legend row, then per-section: section header row, header row (`# | Required Document | What lenders verify | Status | Drive Link | Remarks`), data rows.
- Multi-link cells: `=HYPERLINK("a","A") & CHAR(10) & HYPERLINK("b","B")` — write with `valueInputOption='USER_ENTERED'`.
- Write flow: `values().clear` the tab → `values().update` in chunks of ≤50 rows → verify by read-back with FORMULA render.
- Formatting via `batchUpdate`: section header bars (dark bg + white bold text), table header rows (light bg), `repeatCell` borders per table block, WRAP on data columns, column widths (`updateDimensionProperties`), `frozenRowCount` 2.
- **Derive positions by reading the written sheet back** — scanning for section markers/headers — instead of hardcoding row indices (indices drift and silently break formatting).
- Preserve original status text and remarks; never invent statuses. Update the summary block counts honestly (✅/◐/✗ tallies from the new tables).

## Verification after rebuild

- Re-run the audit on the new sheet: every HYPERLINK resolves, no TRASHED, no 404.
- Count hyperlink instances vs unique IDs; report both.
- Export the sheet/PDF render if visual check needed (not required).

## Pitfall: wrong identity during audit

Files under another vault user (e.g. ndr-owned Amber decks) return 403/`File not found` for psingh — that's an access/permission fact, NOT a broken link. Report as "export/download restricted", not "missing".