# Removing external/team access from files when the grant is INHERITED

**Problem (2026-10-08, Ranka Oasis × Jiraaf term sheets):** documents inside a
shared deal folder carry team access via FOLDER inheritance (Sarthak writer,
Bharat/Anbarasan/Prakash reader, Roshini writer, presales writer…). Trying
`drive_permissions_remove` at the FILE level fails with:

```
403 cannotDeletePermission — "The authenticated user cannot delete the permission.
If the permission is inherited, limited access must be leveraged
(https://developers.google.com/workspace/drive/api/guides/limited-expansive-access)"
```

## Diagnosis: how to tell a grant is inherited
- The SAME permission id appears on every file inside a folder (e.g.
  `03023515843104297958` = Sarthak on all six term sheets). Direct file grants
  have distinct ids; folder-inherited grants share one id per user.
- `drive_permissions_remove` on that id → 403 cannotDeletePermission = inherited.
- A DIRECT grant on the file (e.g. `17594083637291823918` =
  nishantprakash@theyelloweye.com on v0.4) HAS a unique file-scoped id and CAN be
  removed at file level — do that first.

## Fix: MOVE the file to a private parent (severs inheritance)
Inherited grants cannot be deleted from the file; they disappear when the file
leaves the granting folder. Steps:
1. Remove any DIRECT grants on the file first (they survive a move).
2. Create/choose a destination folder whose own grant chain is clean (owner
   only), then `drive_move` (add_parents=private, remove_parents=old folder).
3. Re-list permissions on the moved file — should now show ONLY the owner.
4. Keep the still-shared doc(s) in the original folder untouched.

Worked IDs (Ranka Oasis term sheets, 2026-10-08):
- Shared deal folder that granted the inheritance: `1pKvhDHDFvMNJsEnveaRl-VGJ4tAuAKog` (Balaji Land).
- v1.1 KEPT shared: `1bKUUKT35wx3SRPTa35kw4AsIWPHRlVWp2vS9zKw0icY` (+ nishantprakash1@gmail.com writer).
- v0.4/v1.0/v0.3/v0.2/v0.1 MOVED to private folder
  `1urBPARda5_iMlQavQNsajU7sB0zcYM2b` ("Z_Private — Ranka Oasis Term Sheets
  v0.1-v1.0 (NDR only)"). After move + parent cleanup: owner-only each.

## Corrected drive geography (google-draas account, verified via drive_get 2026-10-08)
- `0AFOc8cSaJXPGUk9PVA` = **ndr's personal "My Drive" ROOT** (parents [], owner
  ndr@draas.com, owner-only permission). Earlier sessions mislabeled this as the
  "company shared drive" — it is not. Files/folders created here are private.
- `0B1Oc8cSaJXPGYkQtYXJDQWVBUVE` = **"Personal"** folder (inside My Drive root)
  — carries **Roshini (rnr@draas.com) writer grant**; anything placed under it
  is visible to her. Do NOT use it as a "private" destination.
- `11RQfeyD9vWgUiQNa0tMf9DopA6C5y5T6` = "Investment Opportunities" (inside
  Personal) — also has Roshini writer.
- `gws_drive_create_folder` with parent_id='root' resolves to My Drive root
  (0AFOc8cSaJXPGUk9PVA) for this account.
- Lesson: when a destination folder is expected to be private, `drive_get` the
  parent and CHECK ITS PERMISSIONS before moving sensitive files into it — the
  parent chain can leak access (Roshini) that isn't in the file's own listing
  until after the move.