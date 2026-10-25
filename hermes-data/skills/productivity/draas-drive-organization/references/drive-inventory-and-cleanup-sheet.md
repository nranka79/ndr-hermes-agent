# Master Drive Inventory / Cleanup Sheet — build, update, walk

Canonical artifact (NDR's own, ndr@draas.com / vault `google-draas`):

- Sheet ID `17bKPoC5XdlRZ_iUPOQzCjRZW96ablJgYN9DmXZID-M8`
- Title `20260901_Drive_Inventory_Recent_500_Files_Cleanup_Sheet`
- Tabs: `Sheet1` (the frozen original 500-item baseline), `Summary` (regenerated each update),
  `Delta Since Sep-01` (the one-by-one walk list), `Full Delta 6863` (every new item drive-wide).
- Baseline semantics: 500 items, **most recent by created date, drive-wide** — NOT root-only,
  and it did not include folders. Say so plainly; NDR remembers it as "everything on my root drive".

Companion sheet from June 2026: `Drive Root — Duplicate File Analysis` (exact MD5 dupes, zero-byte,
same-name-different-content, near-duplicates). Cross-check against it before re-reporting dupes.

## When to run this

NDR asks to "update the cleanup spreadsheet", inventory the Drive, go through the root/TMP backlog,
or reorganise the root. Re-runnable generator: `scripts/drive_delta_inventory.py`.

## The delta recipe

1. **Read the baseline from the sheet**, not from memory — get the header, the row count, and the
   `Generated` / `Baseline cutoff` cells on `Summary`. The cutoff is the only honest starting point.
2. **Pull the delta** with `files.list(q="createdTime > '<cutoff>T00:00:00' and trashed=false")`,
   paginating on `nextPageToken`, `fields` naming `id,name,mimeType,createdTime,modifiedTime,size,parents,owners,webViewLink`.
   Default `corpora` is `user`, so the result **includes shared-with-you items and items outside
   My Drive** — bucket them separately, do not lump them into My Drive.
3. **Reconstruct paths** from a full folder map (`id -> (name, parent)`) by walking parents up to the
   My Drive root id. Cache the map to disk; the walk is run once.
4. **Bucket by top-level ancestor**, then decide what is actually actionable.

## Numbers as of the 2026-10-16 update (use as a sanity check)

- Drive-wide new since 2026-09-01: **6,863** (1,049 of them folders)
- 5,955 in My Drive; 843 outside My Drive whose parent the API does not expose; 65 shared-with-you with no parent
- 1,739 items sit directly at My Drive root (1,639 files / 100 folders) — this is the standing backlog
- Walk list = **187**: A 30 loose files at root, B 11 new root folders, C 85 loose files in TMP,
  D 28 new folders in TMP, E 33 new items dropped directly into an existing root-level folder
- Two self-contained dumps, never expanded into per-file rows: `20260909 Mirabilis RERA Case…` (2,329)
  and the TMP tree (2,167)

## Section design — this is the part that makes it walkable

Ordered by decision type, not by date:

- **A. LOOSE AT MY DRIVE ROOT (files)** — the highest-value section; smallest and unblocks the most. Offer it first.
- **B. NEW FOLDERS AT MY DRIVE ROOT** — a folder at root is itself the mistake.
- **C. LOOSE IN TMP (files)** — the chat-session backlog (per the TMP hard rule).
- **D. NEW FOLDERS IN TMP**
- **E. NEW ITEMS DIRECTLY INSIDE A ROOT-LEVEL FOLDER** — mostly already correctly filed; default these to
  `OK` (see pitfalls) so the REVIEW signal survives.

Columns: `Sl No | Section | File Name | Kind | Location (Folder Path) | Created | Modified | Size | Link | Proposed Action | Target Folder | Notes`.
Actions used: `MOVE`, `MOVE + RENAME`, `RENAME + MOVE`, `GROUP`, `GROUP + DEDUPE`, `RENAME + GROUP`,
`MOVE + SUPERSEDE`, `SUPERSEDE`, `DELETE ONE COPY`, `KEEP`, `KEEP in TMP`, `KEEP at root`, `KEEP (restricted)`, `OK`, `REVIEW`.

**Collapse bulk dumps.** A 2,329-file case folder is ONE row on the walk list with its count in Notes.
A delta tab with 6,863 rows is not a walk-through and NDR will not use it — that is what the
`Full Delta` tab is for. Never let volume crowd out the decision surface.

## Pitfalls (all hit for real)

- **Never label a bucket with a guessed drive name.** 843 items came back with `parents` and `driveId`
  both empty even under `supportsAllDrives=True`, and `'<driveId>' in parents` on the one shared drive
  returned 0 children. Label it honestly — "outside My Drive (parent not exposed)" — rather than
  asserting which drive they are in. Fabricating the label was caught on read-back.
- **Hand-typed suggestion keys must match on a prefix, not exact equality.** Keys written from a
  truncated console printout (`…CONDENSED (11 page`, `…ScopeReview_and_ContentOS`) will silently miss.
  Normalise (lowercase + collapse whitespace) and match on a 45-char then 25-char prefix.
- **Default matched-but-not-important rows to `OK`, never `REVIEW`.** Section E rows are usually already
  correctly filed; leaving them as REVIEW buries the genuine flags. Target is **zero REVIEW** — every row
  should carry a real answer before delivery.
- **Lambda-scoping bug:** `cnt = lambda p: sum(1 for r in md if p(r))` where `md` is the My-Drive-only
  subset silently returns 0 for every other bucket. Scope summary counters over the full `rows` list, and
  **read the Summary back** to verify each line is non-zero before reporting.
- `values().update` past the sheet's `gridProperties.rowCount` auto-expands the grid (the 6,863-row tab
  came back as 6,864 rows). No need to pre-size.
- Idempotency: `values().clear(range='<tab>!A1:Z20000')` then `update` — safe to re-run the whole build.

## What the walk eventually executes

Per the umbrella's hard rule: nothing moves without NDR's explicit approval, file by file. The sheet is
the proposal; approval is conversational. Sensitive finds go first regardless of section order —
sensitive personal/identity material sitting loose in TMP should be lifted out before anything else.

## Sensitive-material flags found in the first walk

Loose in TMP: `PassportReissue_KantaRanka_Case_2026`, `KYC & Identity Records - Kanta Ranka & Late Dinesh Ranka`.
Loose in Personal: `20201008_NDR_Aadhaar_Front/Back.jpg`. All need moving out of generic locations plus
restricted sharing.

## Duplicate families this exercise surfaced

- `R3N KAAJ Byadarahalli Investor Pack v14b (9 slides)` — twice at root, identical name
- `20260922_SC_ROP_SLP32316_2026_PremiumFAR.pdf` — twice in TMP under two dates
- `20260915_Ranka_Oasis_Master_Inventory_All_Drives` — twice in TMP
- `COMPLETE_SESSION_TRANSCRIPT.md` — twice in TMP (one stored with the wrong MIME)
- One deliverable split across files with no folder: `20260917_DRAAS_Devanahalli_SH96_*` (PDF + HTML + KML + JSON),
  `DNR_*_Ranka_Northstar_JDA_Addendum` (PDF + HTML), `20260915_RankaOasis_SurveyExtent_Extract` (PDF + HTML)
- Filename quality: 34 Nenumal Murjani medical PDFs with `recpit` for `Receipt`, `BMJH pdf.pdf`, and one
  dated only `202610`; a `Ranka North Start 1.75FAR` typo for NorthStar

## GWS invocation

`env -u PYTHONPATH /opt/hermes/.venv/bin/python3` with
`from tools.gws_auth import build_service; build_service('sheets','v4',service_name='google-draas')`.
Never hand-build credentials. Never send mail. Writes are verified by reading back.
