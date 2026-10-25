# Bulk Cross-Owner Ownership Migration — "move everything related to <project> from <colleague>'s Drive into mine, leave shortcuts"

Verified 2026-09-10 on the Ranka Udaya consolidation: **166 files moved + 7 vendor copies + 48 duplicates skipped + 19 excluded (findingform), 238 shortcuts left in place**, all per-file verified. Use this playbook when NDR asks to consolidate a colleague's drive contents (Bharat/Prakash/Gowri/any draas.com employee) into ndr@draas.com with shortcuts preserved so nothing breaks for the colleague.

## Preconditions / environment quirk (DWD drive-scope impersonation)

- A **DWD (domain-wide) service account** exists and is authorized for the **drive scope only**. `session_uid=<owner-email>` impersonation WORKS for drive operations (verified). A mixed scope-set (drive+gmail+docs) is rejected wholesale by Google (`unauthorized_client`) — do NOT try to extend the delegation.
- The impersonation can act AS the original owner (Bharat, Prakash, Gowri) to move + transfer THEIR files. It cannot act as an external vendor (findingform, IamHere, Propstory) — those are copy-only.
- This SUPERSEDES the older "cross-owner file: rename OK, MOVE FAILS — copy instead" pitfall for the on-domain case: with DWD drive-scope impersonation the legitimate move+transfer path exists. The copy fallback still applies ONLY to external-owner files.

## Scope decisions (ask before executing)

1. **Which owners?** Employee/colleague accounts (on the @draas.com domain) → fully migratable. External vendors → copy-only (Google Docs/Sheets export to .docx/.xlsx; binaries copy as-is). User may explicitly exclude an owner (e.g. "except findingform").
2. **Recursion is mandatory.** A name-match on the folder is NOT enough — the project's Master Folder contains the whole dossier (title deeds, ECs, PAN/Aadhaar copies, GST, sale deeds) whose filenames rarely all say the project name. Recursively walk ALL children of matched folders; only skip files already owned by the target.
3. **Dedup against the target drive BEFORE moving.** Same name + size already present in NDR's drive (e.g. the guideline-value PDF he linked) → skip, report as duplicate, don't touch. "If it's already copied over you can ignore, you can highlight it."

## Execution sequence (per file — the order is the whole game)

Correct order: **MOVE first (via original owner's impersonated token) → then TRANSFER ownership → then SHORTCUT in the original location.**

- Why move-first: NDR's own token cannot remove the colleague's My Drive root as a parent (invisible to him even on a shared file). The original owner's impersonated token CAN: one `files().update(addParents=<target>, removeParents=<old>)` moves the file while it's still theirs.
- Why transfer-after-move: once ownership flips to ndr, the colleague's token loses reliable parents access; doing the move first keeps the file in a known state for the transfer call.
- Shortcut: create a `application/vnd.google-apps.shortcut` in the ORIGINAL parent folder pointing at the moved file (now NDR-owned). The colleague's drive layout then shows shortcuts where the files were — "nothing breaks for Bharat".
- For files ALREADY NDR-owned but sitting in the colleague's drive: just move (no transfer, no shortcut needed — or shortcut per user preference).
- Give the source owners (and admin2) **editor access to the target folder** ONCE before the run — the moves depend on the source owner being able to write into the destination. Offer to revoke after.

## Resume-safety / idempotency (the script went through 3 runs)

Write the migrator so a crash mid-run never corrupts state and re-running is safe:
- Skip files already processed: check `owners[0] == target` AND `target_folder in parents` → done, skip.
- Vendor copies reuse the impersonated employee token for the COPY operation (a vendor email cannot have a DWD client built — that was the run-1 crash).
- A `400` on a transfer is often a RACE on a half-state from a previous run (file already transferred + moved by then) — verify the actual state before declaring a failure; the file is frequently fine.
- Move skip-if-already-in-target: if `target_folder in parents` already, don't attempt the move.

## Per-file verification (non-negotiable)

After the full run, walk every moved file and assert: `owners[0].emailAddress == ndr@draas.com` AND target folder is in `parents` AND a shortcut exists in the original location. Report counts as: moved / vendor-copied / dup-skipped / excluded-owner / folder-shells-left (folders remain in the colleague's drive, now containing the shortcuts).

## Runtime shape

~263 walk items → ~80 file-by-file operations with verification took several background runs (a few minutes each). Run as `terminal(background=True, notify_on_complete=True)` and poll progress via an output file, NOT stdout. Idempotent resume means an interrupted run just continues.

## Which folders stay

Folders themselves stay in the colleague's drive (recurse into them, move the FILES). Delete empty folder shells only if the user asks — they normally want the layout preserved (the Master Folder / Title Documents / Legal Reports keep existing, now full of shortcuts).