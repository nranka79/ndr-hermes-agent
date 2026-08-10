# Drive filing — moving a folder the account does NOT own (owner-delete workflow)

Situation: a project folder sits at My Drive root (or anywhere wrong) but is OWNED by
another account (e.g. `admin2.blr@draas.com`), and the session account (ndr@draas.com)
only has domain-reader on it. Symptom: `files().update(addParents=..., removeParents=...)`
fails with **"Increasing the number of parents is not allowed" (cannotAddParent)**, and the
folder's `parents` field reads `None` (orphan in the owner's drive — its real parent is
hidden from you). You CANNOT move the folder itself. Do NOT keep retrying the move.

## The pattern that works
1. **Create your own (NDR-owned) target structure** at the correct home (e.g.
   `Current Properties > <Project> > <docs>`). You own what you create.
2. **Move the CONTENT, not the folder**: `files().update(fileId=<subfolder/file>,
   addParents=<your new folder>, removeParents=<their folder>)` succeeds on individual
   items even inside a tree you can't move as a whole — as long as you have edit on the
   item. Verified working for subfolders AND loose files owned by the other account.
   Verify the target folder afterwards (list children; count = expected).
3. **PITFALL — duplicate empty subfolders**: do NOT pre-create the same subfolder names
   in your new tree before moving the old ones in. You will end up with two siblings of
   the same name (old populated + new empty) and must hunt the empties down and delete
   them. Create only the parent, then move the existing subfolders wholesale.
4. **Grant the owner 30-day viewer access** on your new folder so they can verify before
   deleting theirs: `permissions().create(fileId=<new>, body={type:user, role:reader,
   emailAddress:<owner>, expirationTime: <now+30d ISO>})`. Grant on both the project
   folder and the innermost docs folder (permission propagation via drive links is not
   guaranteed for shared links).
5. **Draft an email to the owner** (DRAFT ONLY — never send; see email hard rule):
   state every file/subfolder has moved to your folder (with link), they have viewer
   access for 30 days (expiry date), and ask them to delete their own now-empty folder
   (with link to it). Include BOTH links.
6. Confirm the old folder is empty (list children == 0) before the email goes out, so
   the claim is true.
7. Delete any stale shortcuts pointing at the old folder (shortcuts owned by you are
   deletable even when the target isn't).

## Direct Gmail draft fallback (skill bridge blocked)
`tools.gws_skill_bridge.call("draft_create", ...)` can raise
`PermissionError: [Errno 13] ... '/data/hermes/skills/productivity/google-workspace/
scripts/google_api.py'` when `/data/hermes/skills` is root-owned (700, owned by root
since a permissions change; sessions run as hermes uid 10000). The sanctioned fallback:
build the draft DIRECTLY via Gmail API — still draft-only, never send:

```python
from email.mime.text import MIMEText
import base64
from tools import gws_auth
svc = gws_auth.build_service('gmail', 'v1', service_name='google-draas')
msg = MIMEText(body); msg["To"]=...; msg["From"]="ndr@draas.com"; msg["Subject"]=...
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = svc.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
```

This creates a real Gmail draft (draft id returned); the user reviews/sends it.
NEVER use `.users().messages().send(...)` — that is a real send and is forbidden.

## Ownership probes (quick checks before any move)
- `files().get(fileId, fields="id,name,parents,ownedByMe,owners(emailAddress),driveId",
  supportsAllDrives=True)` — `ownedByMe:False` + foreign owner = expect move to fail.
- `permissions().list(...)` — see who has writer/owner.
- Probe write access: create+delete a tiny `__hermes_move_probe__.txt` in the target
  folder; if create succeeds, file-level moves into it will too.
- A top-level folder showing `parents: None` (not the My Drive root id) is an orphan in
  someone else's drive — move its content, not the folder.
