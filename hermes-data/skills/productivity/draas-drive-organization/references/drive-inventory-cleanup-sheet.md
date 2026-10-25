# Drive Inventory → Cleanup Spreadsheet

Trigger: "give me a list of my last N files on Drive / create a spreadsheet of my files / I want to clean up my drive". NDR starts a drive-cleanup process: inventory recent files (owned + shared), then decide rename / refile / merge / version.

## Workflow

1. Resolve account: `gws_resolve_account()` — NDR's main drive is `google-draas` (ndr@draas.com). Do NOT guess.
2. Fetch the N most recent files by **createdTime desc** (not modifiedTime — NDR said "files created on my drive"). Query:
   ```
   ( 'me' in owners or sharedWithMe = true ) and trashed = false and mimeType != 'application/vnd.google-apps.folder'
   ```
   With `orderBy='createdTime desc'`, `pageSize=1000` (max), paginate until N (default 500). Exclude folders — they are noise in a file inventory; folder names appear in the Location column anyway.
3. Build folder path per file by walking `parents` up with a folder-name cache (cache `files().get(fileId=fid, fields='id,name,parents')` — most files share folders, so unique folder fetches are far fewer than files).
4. Compute cleanup heuristics (see below), sort newest-first, write to a fresh Google Sheet on the same account.
5. Spreadsheet layout (validated 2026-09-01):
   - Sheet1 columns: `Sl No | File Name | Kind | Location (Folder Path) | Created | Modified | Owner | Size | Link | Cleanup Suggestion`
   - Link column = `=HYPERLINK("url","open")` with `valueInputOption=USER_ENTERED` → clickable "open" links.
   - Formatting: bold header + grey background, freeze row 1, `autoResizeDimensions` on name/path column ranges (endIndex exclusive — use 0-4 and 8-9 for 10 columns).
   - Second tab "Summary" with stats (total, at root, flagged rename, flagged duplicate, OK + tips).
   - File name: `YYYYMMDD_Drive_Inventory_Recent_500_Files_Cleanup_Sheet` (follows NDR's naming convention).
6. Re-runnable script: `scripts/drive-inventory-sheet.py` (`cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 <path>`). First run sheet: `17bKPoC5XdlRZ_iUPOQzCjRZW96ablJgYN9DmXZID-M8`. Re-running creates a NEW sheet (idempotent, safe).

## Cleanup Heuristics (column J)

- `Review name` — generic/auto names: `^untitled|new document|copy|document|doc|sheet|slide|drawing|export`, trailing `(N)`, words `copy|final|finalN|draft|new`, trailing `_vN`, `-N|final` suffix.
- `File into folder` — location == `My Drive (root)` (30 of 500 on first run).
- `Possible duplicate/merge` — normalized-name (strip non-alphanumeric, lowercase) count > 1; or `Copy of X` where base name X also exists in the list. Example caught first run: `RankaNorthStar_Allalasandra_Sy14-1_GuidanceValue_Attested.pdf` twice in the same folder, same 15.1 MB size → genuine duplicate.
- else `OK` (456/500 first run).

"Description" column: Drive `description` field is almost always empty; the `Kind` column (mimeType→short code: PDF/Doc/Sheet/Slides/PNG/DOCX/…) supplies the "what is this" context instead.

## Three-pass cleanup approach (NDR's agreed method)

1. **Duplicates/merges first** — biggest storage + confusion win. Keep newest/canonical version, rename it `_vX`, move superseded copies into an `_Archive` subfolder (or bin if truly obsolete). NEVER delete blindly — NDR reviews the merge list, agent executes.
2. **Root-level filing next** — move loose files at My Drive root into the right TMP/project folders (see Root-File Cleanup Pattern, `tmp-to-project.md`).
3. **Renames last** — low urgency because renaming preserves file IDs/links (`files().update(body={'name': ...})` never breaks links).

Long-term: enforce `YYYYMMDD_Entity_Description` naming at creation/upload time so the backlog stops regenerating (offer this as part of any file-creation routine).

## Pitfalls

- **`drive.about().get(fields='rootFolderId')` → HttpError 400 "Invalid field selection rootFolderId"** (hit 2026-09-01). The about resource rejects that field mask. Detect root by walking parents: a folder whose `parents` array is empty/missing IS My Drive root. Shared-with-me files not added to My Drive have no `parents` → label `Shared with me (direct)`.
- Run GWS scripts from `terminal()` with the Hermes venv python (`/opt/hermes/.venv/bin/python3`) + `HERMES_SESSION_USER_ID=ndr` — execute_code lacks the vault socket; system python3 lacks googleapiclient. Print `svc.about().get(fields='user')` first and verify AUTHED AS is the intended account.
- `supportsAllDrives=True` on files().list so shared files surface reliably.
- Sheets `autoResizeDimensions` endIndex is EXCLUSIVE — pass one past the last column you want resized.