# Project-wide Drive audit → security fix → reorganization proposal → HTML email

Recurring NDR request shape:

> "There is a <project> folder on my drive… files are all over. Find all the folders relevant
> to it. Most important, find the folder where the collaterals are (renders/images/videos).
> Create a detailed email of all the folders, where they are, and a suggestion of how to
> reorganize it — the ideal folder structure and which files must move where. Also identify
> all the people it is shared with, viewer/editor access, particularly everyone OUTSIDE my
> domain — we may need to put expiry or take away rights. Send that email to <colleague>,
> give her editor access on all folders. Render it as HTML so it's readable — tables, charts."

Two deliverables, both required: **an access/security audit** and **a reorganization plan**,
delivered as an **HTML email** to the colleague (usually `rnr@draas.com` — Roshni, RNR).

## Phase 1 — enumerate every folder/file for the project

1. Name sweep in the session's own account first, then each colleague account that owns
   project material — the project's files are normally spread across `ndr@draas.com`,
   `psingh@draas.com`, `sales1.blr@draas.com`, `sgowda@draas.com`, `admin2.blr@draas.com`.
   ```python
   svc.files().list(
       q="name contains 'Ranka Amber' and trashed = false",
       fields="files(id,name,mimeType,size,modifiedTime,owners(emailAddress),parents,webViewLink)",
       supportsAllDrives=True, includeItemsFromAllDrives=True, corpora="allDrives").execute()
   ```
   Run several name variants (`Ranka Amber`, `RANKA AMBER`, `Amber`) — capitalization and
   spacing are inconsistent on Drive.
2. Expect **same-name folders under different owners**. Never merge them by name; report
   each with its owner and ID, and flag which is canonical.
3. Expect **one or more folders you cannot see at all** (owned by a colleague who never
   shared with ndr). Report it as an explicit gap with the owner's name — do not silently
   omit it.
4. Cross-check the email side (threads referencing the project) in Phase 3.

## Phase 2 — locate the collaterals

Collaterals = renders (PNG/JPG), brochures, flex/hoarding/sunpack, and any video.
- Renders are frequently filed under the **architect's own account**, not the project name —
  search by owner email, and look for a folder literally named "Renders" /
  "Tentative Renders" / "Collaterals".
- Expect a **second, informal render drop** ("Tentative Renders" early concepts) that NDR
  has forgotten about — surfacing it is usually the single most valuable part of the audit.
- Brochure + renders sometimes coexist inside a "Project Related Docs" subfolder with
  per-room subfolders (Lobby, Gym, Exterior). Report that as the canonical collateral home.
- Site photos land inside "Scanned Documents" — flag as misfiled.

## Phase 3 — external-access inventory (the security core)

For each folder and each key file:

```python
svc.permissions().list(fileId=FID,
    fields="permissions(id,type,role,emailAddress,displayName,expirationTime,deleted)"
).execute()
```

Build a table of every identity whose email domain is NOT `draas.com`, with role
(reader/writer), the item it is on, and its expiry (or "permanent"). Then classify:

| Class | Action to recommend |
|---|---|
| Legit professional counterparty (RERA consultant, counsel, bank, architect) | Keep; add an expiry if not needed indefinitely |
| Named individual you can identify (see `contact_resolver`) | Keep or expire — confirm with NDR |
| Unknown third party email (gmail/yahoo/agency) | Flag for review / remove — do NOT silently revoke |
| `anyone` / `anyoneWithLink` | Highest priority — report immediately |

**Escalate the `type: 'anyone'` findings in the email.** They are the real risk:
- `role: 'writer'` on an anyone-link = anyone on the internet can modify/delete the files.
  This is the headline finding.
- `role: 'reader'` on an anyone-link = sensitive documents (title chain, Aadhaar, bank
  statements) are internet-readable.
- Removing the anyone-link can cut off **the owner's own access** if that was the only path
  in. Fixing it means the user can no longer see the folder — say so explicitly, don't
  quietly do it and let them discover a missing folder later.
- Files owned by an external party (architect's firm) may be **copy-protected**
  (`capabilities.canCopy: false`) — copying them out as a rescue is not possible; the only
  fix is asking the external owner to transfer ownership. Report that.

## Phase 4 — grant the colleague editor access

The user's ask: "make sure <colleague> has editorial access on all folders if she doesn't
have it." For each folder:

1. `permissions().list` to see whether she already has `writer` — check FIRST, and report
   "already had editor on N of M" rather than implying fresh grants everywhere.
2. If only `reader`, promote: `permissions().update(fileId, permissionId=<her perm id>,
   body={'role': 'writer'}, supportsAllDrives=True)`.
3. If absent: `permissions().create(fileId=FID, body={'type': 'user', 'role': 'writer',
   'emailAddress': 'rnr@draas.com'}, sendNotificationEmail=False, supportsAllDrives=True)`.
4. **Folders you cannot see cannot be shared** — list them as an open action for the owner.
5. Verify by re-listing after each change. Never report a grant you did not confirm.

## Phase 5 — the reorganization proposal

Propose ONE canonical taxonomy and a file-by-file move list. A six-bucket scheme works for
DRA apartment projects:

```
<Project>/
├── 01_RERA_Compliance/     registrations, QPR/Form 4/5/6, filings
├── 02_Legal_Property/      title chain, JDA/SSA/sharing agreements, khata, EC, notices
├── 03_Design_Plans/        sanctioned plan, GFC drawings, structural, MEP
├── 04_Collaterals/         renders/, brochure/, video/, flex-hoarding/
├── 05_Financial/           cost sheets, escrow/bank, investor docs
└── 06_Correspondence/      approvals correspondence, notices, misc
```

In the email give a **moves table**: current location → owner → proposed destination →
why. Explicitly call out files that are: at My Drive root, duplicated across accounts,
misfiled (photos in Scanned Documents), or stranded in a colleague's drive.

## Phase 6 — render as HTML

- Send as an HTML email (`MIMEText(body, "html", "utf-8")`) with inline styles (email clients
  strip `<style>` blocks inconsistently — put styling on the elements).
- Tables for: folder inventory, external-access list, proposed moves. Keep to 3 tables max.
- Lead the email with the **security finding**, not the folder list.
- Build it as a **draft**, never a send — see
  `productivity/gws-automation/references/gmail-threaded-draft-reply.md`.

## Pitfalls

- **Never quote a legal document from its filename.** Before putting a document on an email
  to a bank, counsel, or counterparty, open it and confirm the parties. Scanned Indian
  agreements have **no text layer** — `pdftotext` returns only form feeds. Render and OCR:
  `pdftoppm -r 110 -png -f N -l N file.pdf /tmp/p<N>` then `vision_analyze` on the PNG.
  Worked example (2026-09-17): the Ranka Amber SSA file is named
  "...Signed_Copy_For_Raghu.pdf" but the deed names BOTH **Mr. Raghu Iyer** and
  **Mrs. Farida R Iyer** as Landowners (Raghu signs for himself and as SPA holder for Farida
  under Doc No. DRO/SIN/GPA/1088/2025-2026), with DRA Realty represented by Director Nishant
  Ranka. Voice "Frida" = **Farida**.
- **Report gaps rather than papering over them.** If a folder is inaccessible or a file
  cannot be copied, the email says so and names the person who must act.
- **Do not perform destructive access changes the user only asked you to *identify*.** The
  default instruction is "identify and recommend" — highlight who to expire/remove, don't
  revoke and then explain.
- **HTML draft body, not a Markdown dump** — NDR explicitly asks for "rendered as HTML…
  tables, charts, whatever you need such that in an email it renders okay".
