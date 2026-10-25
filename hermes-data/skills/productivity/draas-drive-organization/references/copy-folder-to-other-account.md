# Copy a DRAAS project folder into a colleague's own Drive

Trigger: a DRAAS colleague (e.g. psingh@draas.com) says "add the folder as
new in my drive" / "give me my own copy" / "add this folder to my drive".

## Why this exists

DRAAS project trees (Ranka Udaya, Ranka Amber, Sobha, etc.) live under
`ndr@draas.com`'s Drive. Colleagues accessing them via their own sessions
see the folders shared to them, but the folders are NOT in their My Drive.
When they ask for the folder "as new in my drive", they want a copy they
OWN at their own Drive root — not a move, not a share, not a shortcut.

## Recipe (verified 2026-09-21, psingh@draas.com + Ranka Udaya)

1. **Confirm whose Drive the session acts as.** `build_service("drive","v3",
   service_name="google-draas")` in a colleague session authenticates as
   THAT colleague (not NDR), even though the folder tree is owned by NDR.
   Verify: `svc.about().get(fields="user(emailAddress)").execute()`.

2. **Resolve the target account's service_name.** `psingh@draas.com` maps
   to `google-draas` via `tools.gws_auth.EMAIL_TO_SERVICE`. In general:
   any `@draas.com` → `google-draas`, `@ahfl.in` → `google-ahfl`,
   `@gmail.com` → `google-gmail` (domain-derived; explicit override map
   wins). Do NOT pass a raw email as service_name.

3. **Get the target user's Drive root.** Use
   `svc.files().get(fileId="root", fields="id,name").execute()`.
   PITFALL: `about().get(fields="rootFolderId")` returns HTTP 400
   "Invalid field selection rootFolderId" — the root id is NOT exposed
   that way. `fileId="root"` is the correct call.

4. **Create the new folder** at root, same name as source:
   ```python
   svc.files().create(body={
       "name": "Ranka Udaya Marketing and Content",
       "mimeType": "application/vnd.google-apps.folder",
       "parents": [root_id]}, fields="id,name,owners(emailAddress)").execute()
   ```

5. **Server-side copy each file** — no byte download/re-upload:
   ```python
   svc.files().copy(fileId=src_id,
                    body={"name": name, "parents": [new_folder_id]},
                    fields="id,name,owners(emailAddress),size,md5Checksum").execute()
   ```
   Each copy is owned by the target user. ~1s per file.

6. **FILTER the source folder's contents.** DRAAS marketing folders
   accumulate unrelated material (the Ranka Udaya "Marketing and Content"
   folder had 148 children — mostly Serenity Estate site photos mixed in
   with the 12 Ranka Udaya assets). Copy only the files that belong to
   the project being requested. Filter by name pattern, then show the user
   what was excluded and offer to mirror everything if they want.

7. **Verify** — list children of the new folder, cross-check `size` against
   source sizes (md5 may not be returned for all copies; size 12/12 match
   is the acceptance check), confirm every `owners[0].emailAddress` is the
   target user, return the folder link.

## Notes

- The original folder stays in place — this is a copy, not a move.
- Server-side copy means no local temp files, no media upload quota burn,
  and the md5 is preserved for binary files.
- The same `files.copy` pattern works for one-off "copy this file to my
  drive" requests: create folder if needed, then copy.