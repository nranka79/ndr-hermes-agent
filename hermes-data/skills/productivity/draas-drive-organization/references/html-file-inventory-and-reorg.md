# HTML File Inventory (with folder chains) + File-by-File Reorganization Workflow (10-Sep-2026)

NDR asked: "list every file in this folder tree related to <project>, with the link, exact folder, and the ENTIRE folder chain from My Drive down, as an HTML table" — then: "reorganize: move these files here, flatten that folder, merge this subfolder into that one, trash the empties, dedupe, then give me the updated HTML." Worked example: Ranka Northstar Sy 14/1 inventory (earlier), DR Villa/R99/SouthCity inventory v1 → v2.

## Trigger phrases
- "give me a list of everything with links" / "list every file with the link and the exact folder and the entire chain"
- "as an HTML table, then I can identify which file we need to give access to"
- "move the files to <folder>, flatten <folder>, merge <sub> into <target>, eliminating duplicates, trash the empty folder, regenerate the HTML"

## Step 1 — Inventory (live walk, never trust cached counts)
- Use `drive.files().list(q=f"'{fid}' in parents and trashed=false", pageSize=1000, fields='files(id,name,mimeType,parents,createdTime)')`, recurse into subfolders, dedupe by file id into a dict.
- **Scope surgically**: walk only the target cluster's root folder(s). Broad name queries catch unrelated projects (same villa/survey words appear in other villages). After the walk, list EVERY subfolder with file+dir counts (`List`) to find deep marketing/asset branches (fonts/JPGs/links/`PUSH Deliverables`) that balloon the count — ask or exclude them, don't dump them.
- Ignore/`SKIP` folder-ids set: pass into the walker to skip excluded branches (e.g. DR Villa Drawings, Elevation & Visuals, Floor Plans PDF, BusDev, PUSH Deliverables).

## Step 2 — Folder chain for each file
- Walk UP from the file's parent: `drive.files().get(fileId=cur, fields='id,name,parents')`, take `parents[0]`, repeat until My Drive root `0AFOc8cSaJXPGUk9PVA`, prepend "My Drive".
- Cache folder names while walking up (many files share parents — one get() per folder, ~200 gets for 270 files).

## Step 3 — Emit the HTML
- Group files by chain (`" > ".join(chain)`), rows: `# | File (icon) | Created date | open link | folder chain`.
- Highlight project-relevant rows with a pale-yellow class (`re.search(project|alias, name, re.I)`).
- Include a "What changed in v2" block when regenerating after a reorg — NDR wants to see the diff at a glance.
- Save locally, upload to Drive root with convention name `YYYYMMDD_Entity_Description.html`, and ALSO copy to `.html.txt` because the Telegram gateway DROPS `.html` attachments (known pitfall — always deliver the `.txt` twin as MEDIA).
- Delete the previous version's Drive file when replacing it (NDR expects one current file, not v1+v2).

## Step 4 — Reorganization (file moves with dedupe)
- Before ANY move, build a **name-normalized + md5 dedupe audit** against each target folder:
  `files(id,name,md5Checksum,size,parents)` for target; normalize names (`re.sub(r'[\s_\-\(\)\.]+','',n).lower()`).
- Classify each source file: MOVE (no dup) / EXACT-DUP (name AND md5 match → skip move, trash source) / NAME-DUP-content-diff (same name, different md5 → keep both, rename incoming `_v2`).
- Move = `files().update(fileId, addParents=TARGET, removeParents=SRC, fields='id,parents')`. **verify parents after** (interrupted runs can leave partial state — always re-read live state, not the cached pickle).
- Trash = `files().update(fileId, body={'trashed': True})`; folder trash cascades to remaining children — only trash a folder AFTER moving its contents out and verifying 0 live children.
- **Un-trash when needed**: `files().update(fileId, body={'trashed': False})` then move — an interrupted run trashed a file that should have moved (`SouthCityDoc.pdf`); recovery = untrash + move to target.
- **Multiparent files**: a file can have parents = [root+legal]. `parents[0]` may be misleading in pickles; use the live `get()` during the move and bin any root-orphan after.
- Report per-step: moved N, skipped+trashed N dups, folder trashed, verified counts of target folders.

## Pitfalls
- Vision OCR unavailable (503 no provider) → scanned records (RTCs, Tippani, Akarbandh) can't be text-verified; classify by folder context + name and say so — offer OCR later.
- Root-level `name contains 'DR' and 'Villa'` queries catch other projects (Sevaganapalli 240/3A, Kengeri, Lakkur) — do a root-scope-only query with a REAL regex exclusion list (`Sevaganapalli|Kengeri|Lakkur|Thindlu|Oasis Village|Golfshire|SPL|FM Draft`).
- The 7th root "DR Villa" file was actually `Preliminary Title Opinion-Sevanganapalli` (typo variant of Sevaganapalli) — check the real content, route to the correct project's Legal Opinions folder (`Sevaganapalli Land Partners > 01_Legal_and_Title_Docs > Legal Opinions`, id `1JVVcYPZDuPR9GyAVIwmiZpWiJzWw0FnX`), NOT the DR Villa cluster.

## Worked example IDs (DR Villa / R99 cluster)
- Root: `Parked Properties` (1_J-gi0ZsaitGCZVbDAUWyboW5Ak12qiX) > `R99` (0B1Oc8cSaJXPGM1ZwaENYN2Z1YkE) > `Ranka99 Legal` (0B1Oc8cSaJXPGeXdNWWc4dXVhdVU) is the legal home; `Ranka99 > SouthCity Legal` (1wF0d_ebM2ZpaOmKFgxcSS9dWuCsYWFYV).
- From HardDrive (1hO92TtODBT0gQWmXoebEapBtWm7JFLb4) flattened into Ranka99 Legal (34 moved, 1 dup); its `SouthCity Legal` subfolder merged into Ranka99>SouthCityLegal (1 new `SouthCityDoc.pdf` moved, 8 dups trashed); both empty folders trashed.
- v2 inventory (209 files, 12 chains): https://drive.google.com/file/d/1ynq1ekFYZu6LrrtI7v3MxN_p5JSiql7v/view (v1 `1_tTej1eqQBNUMNxxHNiATJ0uS2bRDo2E` deleted).