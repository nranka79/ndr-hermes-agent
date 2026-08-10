# Drive filing — ownership & move pitfalls (learned 2026-08-05, Gunjur Sy40 PTCL filing)

## Confirm-before-file rule (user preference)
Nishant wants folder + filename PROPOSED and CONFIRMED before anything is uploaded.
- Propose folder path AND file name together, following the folder's existing naming convention (e.g. `YYYYMMDD_Gunjur_Sy40_<DocType>.pdf`).
- If the voice message / instruction mentions a survey number that differs from the document text, flag the discrepancy explicitly before filing — the document content wins unless the user overrides.
- If the user does not respond to a clarify prompt within ~10 min, send a Telegram nudge via send_message and WAIT. Do not file unconfirmed.

## Audit the WHOLE landscape before proposing a destination
Do not assume the first matching folder is canonical. The user explicitly asked: "check for other Gunjur-Dodballapur folders" before confirming.
- List every similarly-named folder/file across the drive (search "Gunjur", "Doddaballapur", "Dodballapur", "Tubagere", village/hobli names).
- Resolve the parent chain of each candidate (walk up to My Drive root) — a folder that reports `parents=None` is an ORPHAN at root, not organized.
- Check for SHORTCUTS that point at the real folder (a shortcut inside the intended tree = the real folder was never moved there).
- Show the user the full tree of the target folder + where every related item actually lives, then propose the reorg.

## Ownership checks BEFORE attempting folder moves
The `Gunjur Farm Dodballapur legal docs` folder (id 1dmEK1ZPPylA-ZfVNSHKVeKxvcWqn36x-) is OWNED by `admin2.blr@draas.com`, has `parents=None` (hidden parent), and ndr@draas.com only has domain-reader.
- Before any `files().update(addParents=..., removeParents=...)` on a folder, call `files().get(fields="id,name,parents,ownedByMe,driveId")` and `permissions().list(...)`.
- If `ownedByMe=False` and the owner is another account (admin2.blr@draas.com, legal.blr@draas.com etc.), the move will FAIL with:
  `403 "Increasing the number of parents is not allowed"` (reason `cannotAddParent`) — because the real parent is hidden/None from our view and Drive refuses to add a second parent.
- This error is NOT permission on the destination; it is ownership/parent-visibility on the file being moved. Diagnose before retrying — retrying the same call wastes turns.

## Probe before assuming write access
- Create+delete a tiny probe file inside a target folder to test whether uploads will work:
  `files().create(body={"name":"__probe__.txt","parents":[folder_id]})` then delete it.
- In this session: probe create inside `Sy No: 40 documents` and inside `Gunjur Farm` both SUCCEEDED (so the PTCL PDF could be filed) even though the parent folder itself could not be moved.

## What DOES work vs what is blocked (observed pattern)
- ✅ Creating NEW files inside a folder we don't own (when we have create access).
- ✅ Moving loose FILES between subfolders of the legal docs tree (sale deeds, MRs -> Sy40; sheets/docx/letter from My Drive root -> legal docs folder).
- ❌ Moving the FOLDER ITSELF between parents (ownership + hidden parent).
- ❌ Deleting/trashing a folder owned by another account (Copy Gunjur-Doddaballapur, owned by admin2.blr@draas.com).
- 🔶 Shortcut owned by ndr@draas.com CAN be deleted, but DON'T delete it while the real folder is unmovable — the shortcut is the only organized entry point. Keep it until the real folder is relocated (or ownership is transferred / editor granted).

## Escalation path for blocked folder moves
Tell the user precisely what to do from the owning account (`admin2.blr@draas.com` or whoever controls it):
1. Move the folder into the intended tree themselves, OR
2. Grant EDITOR access to ndr@draas.com on the folder — then Hermes can move it and clean up the shortcut.
Do not attempt ownership transfer from the LLM side; it requires owner-account consent flows.
