# Project photos tree & expiry-grant patterns

Validated 2026-09-21 while filing the Prestige Hermitage 2201 after-cleanup
photo set (32 IMG-20260920-WA00XX.jpg WhatsApp exports) and sharing it with
follow-up email recipients.

## Finding the CANONICAL project-photos tree — Prestige Hermitage example

Drive contains TWO folders named "Prestige Hermitage" — do not file into the
first one you find:

1. **`Project Photos` master (1reTYRi5JBz27zEvsLEBLLRxofsShqHzs, root-level) →
   `Prestige Hermitage` (11AuYAeKx6kHhym6DR_GBONQX4tp5XAGb)** — the canonical
   photo repository. Contains real photo subfolders:
   - `bareshell` (numbered raw JPGs of units pre-fitout)
   - `Amenities and others`
   - `Project Photos (demo)` (numbered 1–81 photos)
   - unit subfolders as created (e.g. `2201 After Cleanup (Sep 2026)`)
   The Hermitage docs folder (`Hermitage` 1-69U7spKpaQG8YgYEel0h4eBjMApls6Y)
   holds a shortcut "Project Photos" pointing at this master — a strong signal
   it is the intended destination.
2. **`DRA Projects Photos and other details` (1lbJ1h9eKEhsHiWbFoJTVP2az4ssr7j_d)
   → `Prestige Hermitage` (1wJby6mhNgU3qK7N9MePhBrx1oUs347Pd)** — only 2
   brochure-style JPGs (Hermitage.jpg, Hermitage 2.jpg). Marketing shots, not
   the working photo archive.

Search pattern that separated them: `name contains 'Hermitage'` returns every
file/folder matching; then inspect which parent is reachable from the project's
docs folder (the shortcut target) and which has the deep photo subfolder
structure.

## Filing a unit/event photo set

- Keep the shared/uploaded folder's id; move it with `files().update(
  addParents=<project photos folder>, removeParents=<TMP>,
  body={'name': '<Unit> <State> (<Mon YYYY>)'} )` — e.g.
  `2201 After Cleanup (Sep 2026)`.
- TMP → project move was explicitly requested here, so the move was correct
  (normal rule: files stay in TMP until NDR says move).

## Expiry grants — reader + expirationTime

Pattern that worked for external recipients:
```python
exp = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
svc.permissions().create(fileId=fid, body={
    'type': 'user', 'role': 'reader', 'emailAddress': email,
    'expirationTime': exp}, fields='id,role,type,emailAddress,expirationTime')
```
- 90-day viewer was NDR's default in this request ("90-day … or 180-day").
- **Always list existing permissions first** (`permissions().list`): uploads
  frequently arrive with pre-existing writer grants to internal staff
  (observed: sales1.blr@draas.com, piyush.r@draas.com, admin2.blr@draas.com
  were writers from the upload chain) and a domain reader grant for @draas.com.
- **You cannot downgrade an inherited/upload-chain grant.** Trying
  `permissions().update(role='reader', expirationTime=...)` on the existing
  writer permission failed with
  `403 Cannot modify a permission on an item to be less than the inherited
  access from a direct or indirect parent. Leverage limited access`. If the
  permission already exists at writer, either leave it (internal staff) or tell
  NDR — do not treat the grant as failed if the user list shows the right
  person with any role.
- The 403 arrives even when the folder is owned by ndr@draas.com; the writer
  grant was created by whoever uploaded via the shared folder.