# Deleting Shared Folders & Ownership-Transfer Requests (verified 2026-09-19)

Two recurring NDR instructions that both carry a silent failure mode. Load this whenever
NDR says **"delete that folder"** or **"change the ownership to me."**

---

## 1. Deleting a folder that was shared with a colleague — revoke first, and check the email

NDR periodically says *"we don't need that folder in the root directory at all — delete it."*
Before trashing anything that was shared, check two things and REPORT them:

1. **Does a live email link to it?** If an outgoing draft or an already-sent message points
   at the folder, deleting it breaks the recipient's link. Say so and offer the two options —
   **delete the folder** vs **keep-but-empty it** — rather than trashing silently.
2. **Who has access?** A folder created for a deliverable is typically also shared with the
   assignee (often as `writer`) and sometimes a second colleague. Deleting it silently removes
   their working copy.

**Practical order:** report the dependency → get NDR's pick → revoke permissions → trash.

**The case where the dependency is already resolved:** if the deliverable content was moved
into an email BODY (see `email-drafter` → `references/ndr-email-presentation-2026.md`, Rule 1b),
the folder is genuinely redundant and deletion is safe. Say that explicitly so NDR knows *why*
the link no longer matters — otherwise he reasonably assumes you ignored the risk.

---

## 2. Ownership-transfer requests — transfer only what is personally NDR's

NDR sometimes says *"wherever a collateral is owned by someone else, change the ownership to
me, put it in the appropriate folder on my drive, and always leave a shortcut back in the
current owner's drive."* **Do not action this blanket form.** Three hard constraints:

### 2a. Ownership transfer destroys the previous owner's copy

After the transfer the file leaves their Drive. The "shortcut back" NDR asks for is a
*pointer* — if the original is later moved, renamed or trashed, their shortcut breaks and they
have no copy. For title deeds, High Court matters or land records that is a
records-integrity problem, not a tidiness problem. Flag it plainly.

### 2b. You usually cannot do it anyway

`permissions().create` (and any owner change) returns **`403`** when the file is not owned by
the active account. Observed: a collateral video owned by `sales1.blr@draas.com` refused every
sharing attempt. The vault only carries `google-draas` / `google-ahfl` / `google-gmail`, so
there is **no token for a colleague's Drive** — files owned by other people are simply not
actionable. Report them as such rather than attempting a workaround.

### 2c. Corporate assets should stay with the entity

For a liquidation or deal file, moving PSCP / DRA Projects / South City holdings into NDR's
*personal* Drive blurs the corporate–personal line — exactly what you don't want on a
monetisation file where the title position may later be examined.

### Recommended split to offer instead of the blanket transfer

| Class | Assets (worked example, Sep 2026) | Action |
|---|---|---|
| **Personally NDR's** | Century Regalia units, Hermitage 601/2201/2301, Ranka Iris | → transfer ownership to NDR |
| **Entity holdings** | 80 Edifice, Gandhi Nagar, Goa (DRA Projects), Nelamangala | → leave with the entity; **share**, don't transfer |

Present this as three options — (a) transfer only the personally-owned three, (b) transfer all
and accept the shortcut dependency, (c) hold the transfers and just do the folder deletion —
then wait for his pick. This is a case where asking is materially cheaper than guessing.

---

## 3. WRITER access does NOT let you delete — only the owner can (verified 2026-10-05)

Emptying a folder is not the same as removing it. When NDR asks to "remove"/"delete" a
folder, check the owner BEFORE promising it's gone.

Observed on `Approved Doc- Plan Sanction  and building Approval `
(`1rOZeiTpA8oJEbJkh07jMOZq-i0C5Vvcq`), owned by **sales1.blr@draas.com** (Bharat H) and
sitting inside a folder ndr@draas.com *does* own:

- `files().delete` → **403 `insufficientFilePermissions`**
- `files().update(fileId=..., body={'trashed': True})` → **same 403** (trash is not a loophole)

All of this held **even though**: (a) ndr had writer on the folder, (b) ndr owns the parent
folder, and (c) `files().update` moves *of the children out of it* succeeded fine. Moving a
child only needs write on the file; deleting/trashing the container needs ownership.

**Before reporting a folder as removed, always `drive_get` it and check `owners[0]`:**

- owner is ndr's account (google-draas) → proceed, then verify with a children listing = 0.
- owner is anyone else → **you cannot remove it.** Report honestly: emptied, but the leftover
  container needs the owner to delete it. Bharat (`sales1.blr@draas.com`) is the most common
  owner of DRA project folders he created.

**Fix options to offer NDR (do NOT reach for DWD on your own):** (1) the owner deletes it
himself — cheapest, folder is already empty so nothing is lost; or (2) NDR explicitly asks you
to act on that person's account *by name* in the conversation — only then is the DWD path
sanctioned. Policy forbids using DWD just because it's the only technical route; "no other way"
is not an authorisation.

**Reporting shape:** state plainly which documents moved and where they now sit, confirm the
old folder returns zero children, then say the empty container could not be deleted and why
(owner + exact error), with the two options. Never let the reply imply the folder is gone when
it is only empty.

## 4. Flattening a level: move the children first, then deal with the container

NDR's "bring everything up one level, we don't need that folder" is three steps, in order:

1. `gws_drive_list(folder_id=<subfolder>)` — enumerate children (note per-child owner).
2. `gws_drive_move(file_id=..., add_parents=[<parent>], remove_parents=[<subfolder>])` per
   child — use the kwarg form, not body fields (see `move-file-tmp-to-project-folder.md`).
3. Re-list the subfolder to prove 0 children; **then** attempt the container deletion (§3).

Avoid name collisions before step 2 — a flattened child can clash with a sibling already at
the parent level. If it does, surface both and let NDR choose rather than silently superseding.

