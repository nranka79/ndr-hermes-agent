# Safe Drive mutations — placement enforcement and irreversible deletions

Two ways an otherwise-correct Drive operation does real damage. Both bit us in
October 2026 and both are cheap to avoid.

---

## 1. Folder placement — the root-drive violation and how to recover

**The rule:** every folder and file a chat session creates goes inside the **root
`TMP` folder**. Never My Drive root, never directly in a project. See the HARD RULE
in SKILL.md.

**How it still went wrong.** Over three or four sessions we created three
top-level folders directly in My Drive root — the Switzerland visa dossier, the
KYC/Identity Records pack, and the `PassportReissue_KantaRanka_Case_2026` case
folder — and only discovered it when NDR spotted them and said *"many of these
folders you are creating in my root drive and as per rule we are not supposed to
create any folder in the root drive."*

The failure mode is subtle: each individual creation looked fine in isolation.
Nothing errors, the folder works, links get shared, and nobody notices the
parent is wrong. So the rule needs an *active* check, not just an intention.

### Enforce at creation time

Before creating any folder, resolve the parent explicitly and assert it:

```python
TMP = "18p74II2uL32sNDzDDwXzmlOUdJJOTmE-"      # root TMP folder
# ... create with parents=[TMP], never with no parent and never parents=["root"]
```

Then **read the parent back** — `files().get(fileId=..., fields="parents,name")` —
and confirm it equals `TMP`. Do not treat a successful create call as proof of
placement. Same read-back discipline as everywhere else in this skill.

### Recover a stray root folder — move, never recreate

```python
svc.files().update(
    fileId=FOLDER_ID,
    addParents=TMP,
    removeParents="root",
    fields="id,parents,name",
).execute()
```

🔑 **The folder ID does not change on a move, so every link you have already
shared stays valid.** That is why the fix is a move and not a re-create-and-copy.
When you move a stray folder, say so explicitly to the user in those terms —
"the Drive links you've been sharing are unchanged, they're just physically under
TMP now" — otherwise they reasonably assume the links broke.

### Find them

List My Drive root and look for anything that is not TMP, or is not a
long-standing DRAAS top-level folder:

```python
svc.files().list(
    q="'root' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
    fields="files(id,name,createdTime)",
).execute()
```

Judge by **creation date**, not just name — the tell-tale sign is a project-looking
folder created in the last few weeks sitting at top level.

---

## 2. Deleting a native Google Doc is PERMANENT — there is no Trash

NDR asked us to strip the "meaningless" Google Docs and Sheets out of a document
pack so it held only real PDFs and scans. Using the Drive API delete on a **native
Google Doc** (`application/vnd.google-apps.document`) **destroys it outright** —
it does not go to Trash and cannot be restored. We lost two will drafts that way.

This is different from every other file type:

| Type | API delete behaviour |
|---|---|
| Native Google Doc / Sheet / Slide | **Permanent. No Trash. Unrecoverable.** |
| Uploaded binary (PDF, DOCX, JPG) | Goes to Trash, restorable ~30 days |

### Rules

- **Never `files().delete()` a native Google Doc** unless the user has explicitly
  said the document itself may be destroyed.
- When the goal is only "remove this from the pack", the correct operation is
  **`removeParents`** — that un-files it from the pack without touching the file:

  ```python
  svc.files().update(fileId=DOC_ID, removeParents=PACK_FOLDER_ID).execute()
  ```

- Same for Google Sheets that are *inputs* to a pack — un-file them, don't delete.
- Verify before deleting: check `mimeType` starts with `application/vnd.google-apps.`
  and stop if it does.
- If a delete was already done, **do not report "moved to Trash"** — check Trash,
  confirm it genuinely is not there, and tell the user plainly that it is gone.
  Recovery is only possible from NDR's own prior copies or by regenerating.

### The "original got caught by mistake" trap

When cleaning a *copy* out of a pack, it is easy to delete the **source** document
instead. Restoring from Trash then fails, and the failure is silent-looking. If
you meant to delete the pack copy and hit the original:

1. Check Trash (`q="trashed=true"`) — for a native Doc it will be empty, which is
   the confirmation it is gone.
2. Search the whole Drive for other copies before telling the user it is
   irrecoverable.
3. Report it as a mistake with the specific document names, and offer to
   regenerate from the session record. Say it in the clear — do not soften it
   into "was archived".

---

## 3. Mixed-pack hygiene (the general rule)

When the user asks for a pack of **documents**, a folder full of Google Docs,
Sheets and working drafts reads as meaningless. Keep:

- signed / stamped PDFs
- scans of official documents
- portal receipts and acknowledgements

and keep drafts, petitions, working sheets and ledgers **out** — they live in
their own working folder. Remove them with `removeParents`, not delete, for
anything native.
