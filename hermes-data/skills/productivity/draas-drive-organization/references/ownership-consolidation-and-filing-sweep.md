# Ownership consolidation + filing sweep (Ranka Amber, 2026-10-05)

Proven procedure for "take ownership of everything shared with me, file it, rename it,
share it back". Ran across **363 files / 15 source folders** in one pass.

## 1. Scope it read-only first

- Walk every folder whose name matches the project (`name contains 'Amber'`) recursively,
  recording `id, name, mimeType, owners[0].emailAddress, parents, createdTime, webViewLink`.
- Merge in a global `name contains '<project>'` search (catches loose/orphan files).
- Report **counts by owner and by source folder** before touching anything. NDR named
  "Bharat/Prakash/Anbarasan/Kantesh/Sinchana" as likely owners; the measured answer was
  Prakash 129, Finding Form 74, Sinchana 69, Bharat 64, Anbu 7 — **Kantesh owned none**.
  Report the delta; it is the most useful line in the plan message.

## 2. The DWD guard governs the whole design

`tools.gws_dwd_tools` (and any grep of it) is **hard-blocked** from `terminal` /
`execute_code` by a DWD guard that cannot be bypassed. Consequences:

- **Ownership transfer is NOT scriptable.** Each file needs one native
  `gws_dwd_drive_transfer_ownership(target=<current owner>, file_id=..., new_owner_email=ndr@draas.com)`
  call. 255 files = 255 tool calls. Batch **~60 per assistant turn**; a 64-file batch runs fine.
- **Everything else IS scriptable** once ownership is yours: rename, move, copy, re-share —
  all via `tools.gws_auth.build_service('drive','v3', service_name='google-draas')`.
- Order: **transfer first, then rename/move/re-share.** A file you only have writer on can be
  renamed/moved, but you avoid permission edge cases by owning it first.

### Transfer failure modes (expected, ~2%)
- `400 invalidSharingRequest` — *"cannot be performed on an item of mime-type:
  application/vnd.google-apps.shortcut"*. **Shortcuts cannot change ownership.** Skip them.
- `403 insufficientFilePermissions` — usually a shortcut in disguise, or the person in
  `target` is no longer the owner.
- `404 notFound` — the file was deleted between the scan and the run.
Do not treat these as blockers; collect and report them.

## 3. Filing map — prefer the SOURCE FOLDER over the filename

A filename-keyword classifier put 192 of 363 files in `Misc`; the source folder is the
stronger signal. Rules that worked:

| Source folder | Destination |
|---|---|
| `Ranka Amber Approvals` | Approvals |
| `Ranka Amber Architectural and Engineering` | Architectural and Engineering |
| `Ranka Amber Title` / `Customer` / `Marketing and Content` | same bucket |
| `RANKA Amber - Scanned Documents for RERA Approval` | Approvals |
| `Amber` (architect working set) | Arch & Eng; **images/brochure/model → Marketing** |
| `Amber Sanction` | Approvals; renders/brochure → Marketing |
| `Amber Execution`, `Amber Basement` | Architectural and Engineering |
| `Ranka Amber_Enhanced` (studio renders) | Marketing and Content |

**Only move when there is no canonical-bucket ancestor.** Walk the parent chain; if the file
already sits anywhere under one of the 9 buckets (e.g. in `Demand Notes` under Approvals),
leave it where it is and just take ownership. This preserves sub-structures NDR has not asked
to flatten and cut the move count by ~15%.

## 4. Renaming convention

`YYYYMMDD_RankaAmber_<Cleaned_Description>.<ext>`

- Date source: a **valid** date in the filename → else Drive `createdTime`.
  **Validate month 1–12 and day 1–31** — an unvalidated `20\d{2}[-_. ]?\d{2}[-_. ]?\d{2}`
  pattern turned `ECC-04072026-3051415` into `20263051`. Iterate all matches, not just the first.
- Clean: strip leading 8-digit date, drop `Ranka`/`Amber`/`DRA` tokens, `(n)` → `_vn`,
  non-alphanumerics → `_`, collapse, truncate 70, strip trailing stop-words
  (`for|of|the|and|to|in|on|with`).
- Meaningless names (`2.png`, `1A (7).png`) fall back to an extension noun
  (`Render` for images, `Drawing` for `.dwg`, `Model` for `.rvt`/`.skp`).
- **Collision-check against the destination folder listing** before assigning; suffix `_v2`, `_v3`.
- Google-native files (Docs/Sheets/Slides) take **no extension**.

## 5. External-owned files (outside the domain)

DWD only reaches `draas.com`, so these **cannot** be transferred. Do not silently drop them:
`files().copy(fileId=..., body={'name': new, 'parents':[bucket]})` — you own the copy, the
original stays with its maker. Copies do **not** need a re-share (the owner keeps the original).
Report them separately from the transferred set.

## 6. Share back + cleanup

- Re-share each transferred file to its **original owner as writer, no expiry**
  (`permissions().create(body={'type':'user','role':'writer','emailAddress':owner},
  sendNotificationEmail=False)`). NDR's default: no expiry.
- **Folder cleanup is "delete only if empty".** After the moves, list each source folder;
  delete the ones with zero children. NDR-owned → plain delete. Owned by a colleague →
  `gws_dwd_drive_delete(target=<owner>, file_id=...)`. Owned outside the domain → **cannot be
  deleted**; flag it.
- Most duplicate folders will NOT be empty (they still hold NDR's own files) — say so rather
  than deleting or emptying them.

## 7. Gotcha: `parents` missing on some files

A handful of files return **no `parents` key** (and no `driveId`) even though they are readable —
they surface only through the global name search. `drv.files().get(fields='parents')['parents']`
raises `KeyError`. Handle with `addParents=<target>` **only** (no `removeParents`), then rename
in a second pass. Do not skip them.

## 7b. Gotcha: 403 on `addParents`+`removeParents` in ONE call — split into two calls

Some files fail the move with `HttpError 403` on
`files/ID?addParents=…&removeParents=…` even though they are **`ownedByMe: true`** with
`canEdit / canMoveItemWithinDrive / canMoveItemOutOfDrive: true`. The cause is the **source
parent folder**: if it belongs to a colleague (e.g. Sinchana's by-filetype folders
`Autocad/`, `pdf/`, `cad/`, `rvt/`), `files().get` on that folder shows
`capabilities.canEdit: false, canAddChildren: false` for ndr — and Drive refuses the
`removeParents` half of a combined request.

**Fix — two separate calls, not one:**
```python
drv.files().update(fileId=fid, addParents=DEST, body={'name': newname},
                   fields='id,name,parents').execute()      # 1) succeeds
drv.files().update(fileId=fid, removeParents=OLD_PARENT,
                   fields='id,parents').execute()           # 2) succeeds separately
```
Diagnose first with `files().get(fields='capabilities(canEdit,canAddChildren),ownedByMe,parents,driveId')`
on the file **and on each parent**. A parent with `canEdit: false` is the tell.

Do **NOT** conclude "cross-owner → must copy" (that rule is for when the *file* is
`ownedByMe: false`) — here only the *folder* is foreign and a two-call move works.
Also re-check the **re-share** step for these files: a file that errored out of the main
loop never reached the share-back pass, so verify the original owner still has access
(often they do, because the folder grant survives).

## 7c. Regex pitfall that bit TWICE: `\b` does NOT fire at underscore boundaries

Python `\b` treats `_` as a **word character**, so `\bDRA\b` and `\b10\b` **fail** inside
snake_case names like `WO_DRA_Amber_…` or `…Consultants_10June2026.docx`. Two real
consequences, both hit on 2026-10-05:

1. **Name cleaner left project tokens in the name** — `WO_DRA_Amber_Execution_…` kept
   `DRA` and `Amber` because `\b(Ranka|Amber|DRA)\b` never matched.
2. **Date parser silently fell back to `createdTime`** — `…_10June2026` was not matched by
   `\b(\d{1,2})\s*(?:…month…)\s*(20\d{2})`, so the file got the *upload* date (2026-08-05)
   instead of the real document date (2026-06-10).

**Fix: always use lookarounds, never `\b`, when scanning filenames:**
```python
r"(?<![A-Za-z0-9])(Ranka[\s_]*Amber|Ranka|Amber|DRA)(?![A-Za-z0-9])"
r"(?<![A-Za-z0-9])(\d{1,2})\s*(?:january|february|…|december)\s*(20\d{2})"
```
Also handle the **underscore-fused form** `Ranka_Amber` / `RankaAmber` (not just `Ranka Amber`)
before stripping the individual words.

**Always dry-run the rename plan and eyeball ~20 sample mappings before executing** — both
bugs above were caught only by reading the printed plan, and each would have mis-dated or
mis-named dozens of files.

## 7d. CAD sidecar files are junk — route them to `Misc`, don't pollute a curated bucket

AutoCAD working folders carry `.bak`, `.dwl`, `.dwl2`, `plot.log` — regenerated lock/backup
files with no document value. If you map the whole source folder to one bucket they land in,
say, Architectural and Engineering and pollute it. Route them to **`Misc`** instead, so the
source folder still empties and can be deleted, and **flag them** as deletion candidates.

## 8. Watch for same-named projects

`Estimate(R2)_Pragathi_Amber_21.05.2020` and `1386-AMBER.rar` sit in the Amber corpus but may
belong to a different "Amber". File them, and **flag the ambiguous ones** rather than
pretending the sweep was clean.

## 9. Report counts ONLY from a clean verified walk — never from a plan file or an earlier snapshot

**Real failure, 2026-10-05.** The same Amber tree was reported to NDR as **444**, then **536**,
then the true **628** — three different numbers across three consecutive messages. He noticed the
churn and it cost credibility. Root causes: the first figure came from a *plan CSV* (what we
intended to move, not what exists), the second from a pagination loop with a bug (below).

Rules:

- **Never quote a count derived from a plan, a pre-run scan, or a counter you have not re-run
  after the last write.** After a sweep, the only honest number is a fresh walk.
- Count with: a **fresh `nextPageToken` per folder**, recurse into subfolders, **dedupe by file id**
  globally (a file with two parents double-counts otherwise), and count only non-folder mime types.
- **Cross-check with a second method** before publishing — e.g. separately walk the parent folder
  that *contains* the buckets and compare total nodes. Make the arithmetic visible:
  `files + subfolders = total nodes`.
- Run `scripts/count-drive-tree.py` (ships with this skill) — it implements all of the above.

**Pagination pitfall that caused the undercount:** `tok = None` must be initialised **inside** each
folder's `while True` loop. Reusing one `nextPageToken` across sibling folders silently truncates
or duplicates results — and the bad number looks completely plausible, so you will not suspect it.
Related: when a verify script walks several roots, dedupe with a `seen` set or a file reachable from
two roots is counted twice.

## 10. Do NOT flatten sub-structures without an explicit call from NDR

NDR's standing preference, restated 2026-10-05: *"don't flatten the other third level folders under
approval. Let me review it and then we'll take a call."*

- Move files **into** the canonical bucket, but **leave existing nested folders in place** until he
  has reviewed them. Then report the subfolder list and wait for his decision.
- Taking **ownership** of a file is always safe and can be done unprompted. **Restructuring**
  (flattening, merging, renaming folders) is not — surface it and ask.
- When a sweep is done, explicitly state which sub-structures you did NOT touch, so the "untouched"
  state is a deliberate, visible choice rather than an omission.

## 11. Verify the fix, don't re-assert the earlier claim

When a background job reports errors (`err: N` in its summary), do not repeat the earlier "these
were handled in the second pass" line — **check each errored file's live state** (name, parent,
owner) and report what the re-read shows. On 2026-10-05 this caught 2 files that were genuinely
never fixed (stuck in a non-owned folder, see §7b) while the other 12 *had* been corrected — and
the two were only findable by inspecting them, not by trusting the summary.
