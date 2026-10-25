# Document-checklist from a centralized master Drive folder (verified 2026-10-07)

When a user shares (a) a Drive folder of all project/company documents and (b) an Excel
checklist with rows like "RERA Registration", "JDA", "Title & Property Documents",
and says "check whatever is there, put it one by one in the checklist, tell me what's
missing, and don't paste original links — copy the docs into a separate folder and
share from there."

## Workflow

1. **Read the checklist.** If the link is `docs.google.com/spreadsheets` it may STILL
   be an Office file (`.xlsx` uploaded to Drive), not a native Google Sheet. The Sheets
   API refuses Office files with `HttpError 400 ... "The document must not be an Office file"`.
   Detect: `spreadsheets().get(spreadsheetId=...)` fails → download via Drive
   `files().get_media` and parse with `openpyxl` (installed in the Hermes venv).
2. **Inventory the master folder recursively** — `files().list(q="'<folder>' in parents
   and trashed=false", pageSize=300, fields='files(id,name,mimeType,size,shortcutDetails)')`
   per folder; record the folder path so items can be grouped by project. Dump to JSON
   for analysis.
3. **Resolve shortcuts.** Many master folder items are Drive shortcuts
   (`mimeType=application/vnd.google-apps.shortcut`). The real file id lives in
   `shortcutDetails.targetId` — use THAT id for copying, never the shortcut id.
4. **Match checklist rows to files** by case-insensitive keyword on filename within
   the project's path prefix (e.g. row "RERA" → files containing `rera`). For rows
   with many candidates (title docs), pick the representative set (sale deed, ECs,
   partition deeds) — don't copy all 100+ FMB/patta scans.
5. **Create a NEW root folder** `'<Topic> <date> (Copies)'` under the user's Drive
   root (`parents: ['root']`) plus one subfolder per checklist row named
   `<row> <Title>` (e.g. `4.4 Amber - JDA`). `files().copy(fileId=target, body={'name': ..., 'parents': [...]})`
   each matched file into its row's subfolder.
6. **Fill the checklist** (openpyxl): status column (D) = Yes/No/Yes*, link column
   (E) = the COPY subfolder link (`https://drive.google.com/drive/folders/<id>`),
   remarks (F) = what was copied, last-updated (G). Green fill for Yes, orange for
   No/blocked. Watch for **merged banner rows** (A:G) — only edit the item rows.
7. **Re-upload the filled xlsx** to the SAME Drive file id via
   `files().update(fileId, media_body=MediaFileUpload(...))` so the user's original
   link keeps working. Verify permissions survived (`permissions().list`).
8. **Report status table**: 16 Yes (with links), 9 Missing (named individually),
   and any blocked items with the reason.

## Pitfalls

- **Shortcut visible but target 404** — `files().copy` on the resolved `target_id`
  fails `HttpError 404 File not found` even though the shortcut lists fine. This means
  the target lives outside the session user's permission scope (the user can see the
  shortcut but not the real file). It is NOT a dead link to be reported as "missing" —
  it's an access problem. Identify the file's creator (ask the user; e.g. Ranka Udaya
  master files were created by Bharat Hawaldar) and draft an access-request message.
- **Ask the owner via WhatsApp deep link** (`whatsapp_link` tool — never hand-build).
  The user's pattern: draft one message per owner with the exact diagnosis (folder,
  shortcut behaviour, target 404, what the docs are needed for) and deliver as a
  tap-to-send link the user posts himself.
- **Don't paste original master-folder links into the checklist** — the user's
  explicit preference is that shared checklists carry links to the COPIES in the new
  folder only.
- **Duplicate files across projects** (e.g. the same DRA Realty ITR appears under
  Amber, Udaya, Oasis subfolders) — pick the real file copy, don't create dupes.
- **`owners()` also 404s for the inaccessible target** — you can't read the owner via
  the API for a file you can't see; ask the user who created the folder/files.
- **Checklist complex rows (balance sheet, shareholding, bank statements) are often
  genuinely absent** from the master folder — mark them `No` with remark "Not found in
  Master data folder", and note the closest available substitute in remarks (e.g.
  latest ITR FY 2024-25 as the available balance sheet).