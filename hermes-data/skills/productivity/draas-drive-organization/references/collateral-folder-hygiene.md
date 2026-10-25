# Marketing folder hygiene: purge stale versions + consolidate collateral

Trigger: user says "remove all previous versions from the folder, keep only
this version" and/or "add all the marketing collateral files to this
<RANKA Amber> folder".

Verified 2026-09-30 (Prakash Singh, RANKA Amber (PS) - Marketing Collaterals).

## Rule the user wants enforced
- ONE current version of a deliverable in a marketing folder. Old v1/v2/v3/
  v4/v4.1 PDF+HTML pairs are clutter — trash them.
- The marketing folder is the single home for ALL customer-facing collateral
  for the project: investment guide, cost sheet, renders, floor plans,
  brochures, specs, area statement, location/site maps.

## Recipe

1. **List the target folder** (`drive_list folder_id=`) and identify the
   keep-set (files matching the current version, e.g. `v4.2`) vs the
   trash-set (all older). Confirm before deleting — count explicitly.

2. **Trash the old versions** with native `gws_drive_delete` (moves to
   trash, recoverable). Do NOT delete the originals of collateral that live
   in OTHER folders — those stay in place.

3. **Discover collateral across Drive** — search by project name
   (`name contains 'Amber'`), then chase folders: renders live in the
   render-studio folder (`Ranka Amber_Enhanced`, owned by
   esotericarts.ani@gmail.com), GFC floor plans in the architect's folder
   (findingform.design), specs/area statement/location maps in the sales
   folder, brochure pptx + cost sheet loose in My Drive root. The
   "Ranka Amber - Whitefield" sales folder (owner sales1.blr@draas.com) is
   a common origin for specs/area-statement/location maps.

4. **Create subfolders** in the target: `Renders/`, `Floor Plans/`,
   `Brochures & Specs/` — keeps ~20+ files navigable. Cost sheet + guide
   stay at root.

5. **Copy, don't move, cross-owner files.** Use server-side `files.copy`
   with an explicit `parents` target (same technique as
   `copy-folder-to-other-account.md`):
   ```python
   os.environ["HERMES_SESSION_USER_ID"] = "psingh"
   from tools.gws_auth import build_service   # NOTE: no getProfile import — see below
   svc = build_service("drive", "v3", service_name="google-draas")
   svc.files().copy(fileId=src_id, body={"name": new_name,
                    "parents": [dest_folder_id]}).execute()
   ```
   - Copies are owned by the session user (psingh), so he gets full control
     in HIS marketing folder without touching the render studio's originals.
   - Rename while copying when source names are ambiguous (e.g. prefix
     "GFC " to floor plans, "Ranka Amber - " to location maps).

6. **Rename Google-Sheets copies deliberately** — `files.copy` of a native
   Sheets file produces "Copy of <name>"; pass an explicit `name` in the
   copy body to avoid the "Copy of" prefix.

7. **Verify** — re-list the folder: root shows only keep-set + subfolders;
   count children per subfolder and confirm each copy's size matches the
   source (renders ~2–2.6 MB each, GFCs ~0.3–2.2 MB).

## Environment pitfall (2026-09-30)
`tools.gws_auth` does NOT export `getProfile` — importing it raises
`ImportError: cannot import name 'getProfile'`. Set
`HERMES_SESSION_USER_ID` and import `build_service` directly; that is
sufficient (the session user is read from the env var inside the module).
Older memory notes saying "assert getProfile()" are stale.