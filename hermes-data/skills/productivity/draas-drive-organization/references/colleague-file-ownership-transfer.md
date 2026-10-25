# STANDING RULE — colleague-owned project files: take ownership, leave a shortcut

**NDR, 2026-10-16. Applies every time, not per request.**

Whenever a document relevant to our projects or land is found in a colleague's Drive, **do not copy
it and do not ask the colleague to share it.** Three steps:

1. **Transfer ownership to `ndr@draas.com`** via DWD, impersonating the current owner. Same file,
   same file ID, same URL — nothing is copied, so any link already sent to a third party keeps
   working.
2. **Leave a shortcut** (same name, `application/vnd.google-apps.shortcut`) in the folder the file
   came out of, so the colleague's own folder structure keeps working.
3. **File it in NDR's canonical project folder.**

**Why:** while a colleague owns a document, NDR cannot share it with an outside party (contractor,
counsel, bank) without that colleague's cooperation — and cannot rely on it staying put.

---

## Mechanics — verified end-to-end 2026-10-16 (Ranka North Star, 14 objects)

Order is **move (as source owner) → transfer ownership (as source owner) → shortcut**.
Never transfer first: once NDR owns the file, DWD impersonation of the old owner can no longer
move it.

### 1. Destination grant — must be made by NDR, not the source owner

`gws_dwd_drive_permissions_add` as `sales1.blr@draas.com` on NDR's own folder returns
**404 `File not found`** — the colleague simply cannot see NDR's folder, so DWD-as-colleague 404s.
Grant the source owner `writer` on the destination with **NDR's own token**
(`ndr.permissions().create(...)`, `sendNotificationEmail=False`).

### 2. Ownership does NOT cascade

A folder + its 5 children = **6 separate** `gws_dwd_drive_transfer_ownership` calls. Then verify
every id as NDR: `owners[0].emailAddress == ndr@draas.com` **and** the destination id is in
`parents`.

The transfer ack is `{file_id, new_owner}` — that is SUCCESS, not an error shape. The misleading
`400 invalidSharingRequest "emails could not be sent"` also often means it landed. **Always verify
by re-reading `owners`.**

### 3. Shortcuts — the DWD surface cannot do it

There is no `drive_create_shortcut` op, and `gws_ops.drive_create_file` carries no
`shortcutDetails`. Create shortcuts with **NDR's own token**:

```python
ndr.files().create(
    body={"name": name,
          "mimeType": "application/vnd.google-apps.shortcut",
          "parents": [target_parent],
          "shortcutDetails": {"targetId": fid, "targetMimeType": mime}},
    fields="id,name", supportsAllDrives=True).execute()
```

This requires NDR to be a **writer on the target parent** — grant it first via DWD as that
folder's owner (`drive_permissions_add`, role `writer`, email `ndr@draas.com`).

### 4. File at the top level of a colleague's My Drive

A root id (`0ABYJX…`, `0AL2CQ…`) cannot receive a shortcut created by another account — 404.
Workaround that works:

1. Create the shortcut with NDR's token in **NDR's own folder**.
2. `gws_dwd_drive_move` it **as the colleague**: `add_parents=[their_root_id]`,
   `remove_parents=[NDR_folder_id]`.

The colleague can do this because NDR granted them `writer` on that folder in step 1 above.

---

## Pitfalls hit

- **Never transcribe a 72-character legacy folder id.** One wrong character
  (`…c1VsUjI3cnhtV3g5azQ` vs the correct `…c1VsQjI3cnhtV3g5azQ`) yields a silent
  `404 File not found` on the folder **while its children still read fine** — which makes it look
  like a permissions problem rather than a typo. Derive the parent id from a live child:
  `ndr.files().get(fileId=<child>, fields='parents').execute()['parents'][0]`.
- **`registry.dispatch` returns a JSON string, sometimes double-encoded.** Peel it in a loop
  (`json.loads` until you get a dict) before calling `.get()`. A bare
  `json.loads(out)['result']['owners']` intermittently raises
  `'str' object has no attribute 'get'`.
- **`drive_get` via the DWD bridge may not project `shortcutDetails`** — a `targetId` of `None` in
  the read-back is not evidence the shortcut is broken. Confirm by name + parent instead.
- **Deleting the now-redundant duplicate copies is permanent on the first call**
  (`gws_ops.drive_delete` → `files().delete()`, not a trash). Transfer and verify the originals
  **first**, then delete the copies, then confirm each copy 404s.
- **Re-point any links already sent out.** If a workaround copy was shared (e.g. with an outside
  contractor) and the email links at the copy, the copy's ID dies with it. Grant the third party
  viewer on the **original** (with the same `expirationTime`), then swap the links.
- **After the transfer, check the third party's grant actually exists on the original.** A copy
  and its original do not share permissions. Read the permission list back and confirm
  `emailAddress` + `role` + `expirationTime`.
- **The destination folder's existing permissions survive a transfer**, and files moved into a
  folder inherit the folder's shares only for files created there *after* the move.
