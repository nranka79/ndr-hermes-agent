# Cross-Account Document Consolidation (Drive + Gmail → one indexed tree)

**Trigger:** "do a drive-wide search across my drive and also across Google / my Gmail
for all <project> documents, bring everything into one folder, and create an index with
the file name, the link, and a short summary." Often adds "and do the same on
<colleague>'s drive and email, then consolidate across the two."

**Also fires on the follow-ups** to that sweep — they arrive in later turns and belong
here too: "work through the duplicate flags and propose which copy to keep", "delete them
in the original source / change the ownership to me and file it here, keep a shortcut
there", "add a README explaining the tree", "drop a shortcut to the index in the <counsel>
correspondence folder", "give <person> viewer access to folders X/Y/Z and email them".

Verified end-to-end 2026-09-25 on **Gunjur Farm** (Sy 39/40/41, Gunjur Village, Tubagere
Hobli, Doddaballapura Taluk): NDR's Drive + Rajendra's Drive + 3 of NDR's mailboxes +
Rajendra's mailbox → 10-bucket tree, 572 files, master index sheet.

This is a five-phase pipeline. Do the phases in order; the discovery phase is where the
work actually is, and the index cannot be written until the tree is stable.

---

## Phase 0 — Resolve names before searching (cheap, prevents a wasted sweep)

Colleagues are addressed by short names; resolve to the canonical `@draas.com` login
first. Two DWD paths exist and only one is right:

- `gws_dwd_resolve(target="rajendra@draas.com")` → `in_vault: false`, `mode: dwd`.
  The **canonical** login works for DWD even with no vault identity. This is normal and
  correct for ex-employees and staff without OAuth.
- A **wrong alias** returns `invalid_grant: Invalid email or User ID`. `rajendrasv@draas.com`
  → `invalid_grant`, `rajendra.sv@draas.com` → `invalid_grant`, but `rajendra@draas.com`
  → resolved. Do not conclude "DWD is broken" — probe the canonical form.

**`gws_dwd_resolve` SUCCESS DOES NOT MEAN THE MAILBOX EXISTS — verify before acting.**
A resolve can come back clean (`mode: dwd`, `direct: true`, `in_vault: false`) for an
address that is **not a real account**, because the resolver is matching the string you
handed it, not confirming a mailbox. Observed 2026-09-25: NDR dictated
`rsrajendra@draas.com`; `gws_dwd_resolve` returned `direct: true` with no error, but the
very next `gws_dwd_drive_list` and `gws_dwd_gmail_search` both failed with
`invalid_grant: Invalid email or User ID`.

So: after resolving a **user-supplied** address (dictated, typed into chat), prove it with
one cheap read (`gws_dwd_drive_list(target=..., page_size=1)` or a 1-result
`gws_dwd_gmail_search`) **before** any destructive or ownership-changing step. Only an
actual API call proves the mailbox. When it fails, ask NDR for the correct address — do
NOT guess a variant and start taking ownership of, or deleting, files on a possibly-wrong
account. The content may well be reachable through a different identity than the one
dictated (this is what happened above: the GRC 2025 survey pack and DWG files *were*
reachable, just not under the dictated address).

Corollary: an address that resolves `direct: true` is fine to **read** with, but treat
"resolver said yes" and "mailbox is real" as two separate facts. Note also that a name
lookup (`contact_resolver` / `entity_resolver`) can return a person whose contact-sheet
email is a *personal* or *external* address (e.g. a `.com` at another firm) — never
substitute that for the `@draas.com` login without NDR confirming.

Also call `gws_resolve_account` (no args) once to list every account + live auth status,
so you know which mailboxes actually exist before you write the query loop.

**Spelling variants are not optional.** The farm is called Gunjur, Gunjuru, Gunjur Village,
Doddaballapur, Dodballapur, Doddabalapur, Doddaballapura — and the hobli is spelled
**Tubagere** (NDR says "Talopahubli"; the real name appears only in the legal brief).
Run every variant; the documents use all of them. On this session the `fullText` query
found files that the `name contains` queries missed entirely.

**False-positive trap:** "Gunjur" is also a locality off Sarjapur Road / Varthur (KRK Urban
Ville, Prestige Lakeside Habitat, Gunjur palya road). A `gunjur` query happily returns
those. Confirm the parcel identity from a source document before including anything —
the IndusLaw / Shodhan Lokhande brief wording is the ground truth: *"Gunjur Village, Thubgere
Hobli, Doddaballapura Taluk i.e., Survey Nos.39 (15 Acres 10 Guntas), 40/2 (9 Acres), and
Survey No.41 (18 Acres 37 Guntas)"*. Exclude sibling parcels that share the village but not
the survey numbers (Sy 38 / Sumuka, Sy 101, TDR-Panathur-Gunjur-Kodigehally which is really
Panathur Sy 236/6, 236/7, 284/2, 268/36) and mention the exclusions in the report.

---

## Phase 1 — Drive sweep (session user's own token)

Write a script to a file (`write_file`) and run it — do NOT inline it.

```python
from tools.gws_auth import build_service
svc = build_service('drive', 'v3', service_name='google-draas')

QUERIES = ["name contains 'Gunjur'", "name contains 'Gunjuru'",
           "name contains 'Doddaballapur'", "name contains 'Dodballapur'",
           "fullText contains 'Gunjur'"]

def list_all(q):
    out, tok = [], None
    while True:
        r = svc.files().list(q=q + " and trashed = false", pageSize=1000, pageToken=tok,
              fields="nextPageToken, files(id,name,mimeType,parents,modifiedTime,createdTime,"
                     "owners(emailAddress),size,webViewLink,md5Checksum)",
              includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
        out.extend(r.get('files', [])); tok = r.get('nextPageToken')
        if not tok: break
    return out
```

Then a **recursive walk** of the identified roots (depth cap 6-8, `seen` set for id
cycles), resolving each file's parent name so you can present a real path rather than a
bare id. Save the whole tree as JSON to `/tmp` — you will reuse it for the index and will
not want to re-query.

`supportsAllDrives=True` + `includeItemsFromAllDrives=True` on **every** call; these
folders are frequently owned by `admin2.blr@`, `legal.blr@`, `sales1.blr@`, `mdr@` and
`vkdas@` even when they sit in NDR's tree.

A bare `http 500` on a batch of `files().get()` parent lookups just needs a retry.

---

## Phase 2 — Mail sweep (two different mechanisms, on purpose)

**Session user's own accounts — per-user OAuth, `build_service('gmail','v1',service_name=...)`.**
Loop the accounts from `gws_resolve_account` (`google-draas`, `google-ahfl`, `google-gmail`)
and run several query shapes (`gunjur`, `doddaballapur OR dodballapur`, `"sy 39" OR "sy 40"`,
`has:attachment gunjur`, `subject:gunjur`). Use `format='full'` so you get attachment
metadata **and** bodies in one pass.

**Filter noise in Python, not in the query.** A `gunjur`/`doddaballapur` search on
`ndr@gmail` returns ~90 messages of which ~85 are Commonfloor/MagicBricks/IndiaProperty
blast mail. Drop by sender/subject regex (`commonfloor|magicbricks|indiaproperty|makaan|
100floors|googlealerts|olacabs`). Note the *same mailbox* produced 545 vs 191 hits
depending on the query — always de-noise and dedupe by message id before reporting counts.

**Colleague's mailbox — DWD, and ONLY because NDR named the account in this conversation.**
`gws_dwd_gmail_search` / `gws_dwd_gmail_thread_get` return **attachment metadata only** —
filenames, sizes, `attachmentId`, no bytes. That is by design, not a scope failure. Do not
"diagnose" it.

---

## Phase 3 — Extract the attachments (the hard part)

### Plain path: `gws_dwd_gmail_attachment_get`
Returns `{result: {size, dataBase64, dataBase64Length}}`. Works, but a 5 MB attachment
is ~6.8 M characters of base64 — the tool result **spills to a file** under
`/tmp/hermes-results/call_*.txt` with only a 1500-char preview inline. That is normal.

### The trap: decoding from the SPILL FILE, not the payload
The preview is a *truncated slice* of the JSON, so any regex you run over the spill file
grabs a truncated base64 string. Symptom, in order of how it looks:

1. `binascii.Error: Incorrect padding`
2. `base64.b64decode` succeeds but the byte length is ~90% of the claimed size
   (e.g. `1,010,907` vs claimed `1,038,441`)
3. `Invalid base64-encoded string: number of data characters (976025) cannot be 1 more
   than a multiple of 4`

All three are the *same* bug: truncated input. Do not code around the padding — that
silently produces corrupt files that look plausible.

**Fix — three steps, and the third is what makes it reliable:**

1. `json.loads()` the whole spill file (fall back to `json.JSONDecoder().raw_decode(raw[i:])`
   from the first `{"target"` if there is any prefix), then take `result.dataBase64`.
   Never regex the raw file for the payload.
2. Pick the **longest** payload seen per `attachment_id` across all spill files (`if aid in
   best and len(b64) <= len(best[aid]): continue`) — repeated reads can leave a shorter
   earlier copy.
3. **Dump the base64 to a file and decode with the `base64` shell tool**, not Python:

```bash
s=$(printf '%s' "$b64" | tr -d '\n' | tr -- '-_' '+/')   # urlsafe → standard
pad=$(( (4 - ${#s} % 4) % 4 )); printf '%s' "$s"; printf '=%.0s' $(seq 1 $pad) > "out.b64"
base64 -d "out.b64" > "out.pdf"
```

Shell `base64 -d` handles the padding correctly and is the fastest thing to iterate on.
**Verify each decode against the claimed size** from the metadata and report the count
(`10 decoded / byte-exact`). A size mismatch means truncated input — go back to step 1,
do not ship the file. On this session the Python route failed 4 of 10 files and the
dump-then-`base64 -d` route got all 10 byte-exact.

### Attachments that arrive as inline `image001.jpg` (1-2 KB)
These are email signature logos. Skip them explicitly rather than uploading 40 of them.

### Ambiguous `attachmentId`
`attachmentId` is **per-message**, not per-thread. `gws_dwd_gmail_thread_get` returns
attachments nested under each message — pass that message's `id` as `message_id`, never
the `thread_id`. A wrong pairing fails with `Invalid attachment token` (not a crash).

### Session user's own-mailbox attachments
Use the Gmail API directly — `g.users().messages().attachments().get(userId='me',
messageId=mid, id=aid)` then `base64.urlsafe_b64decode(d['data'])`. Match by filename
(exact, case-insensitive) against a WANT list, and report which WANT entries were **not
found** — that list is itself a useful finding.

---

## Phase 4 — Build the tree

### The `cannotCopyFile` 403 (folder-level `files().copy()`)
`files().copy(fileId=<FOLDER>, ...)` fails with:

```
HttpError 403 ... "This file cannot be copied by the user."
domain: global, reason: cannotCopyFile
```

This fires on every folder owned by **another** account even when NDR can see and read it
(`Gunjur Farm Pics`, `Gunjur Legal Files`, `Copy Gunjur-Doddaballapur`, all
`admin2.blr`-owned). It does **not** fire on individual files, nor on folders NDR owns.
An individual `files().copy(fileId=<FILE>)` from inside those same folders succeeds.

**Fallback — recursive mirror.** Create a new folder at the destination (you own it, so
you can nest freely), then walk the source: subfolder → recurse and create; file →
`files().copy()`. One `files().copy()` in ~400 still 500s on a large slim PDF — retry
those individually at the end and report the residual.

**Consequence for the "no duplicates" instruction.** You cannot fold a foreign-owned folder
into the tree by move (`removeParents` on someone else's folder is not yours to do), so
folders from other accounts are **copied** while NDR-owned folders are moved. State
explicitly which ones are copies vs moves in the completion report. NDR said "bring
everything in and don't duplicate by deleting duplicates" — the honest reading is:
consolidate, preserve provenance, flag exact-duplicate files in the index, never delete
without confirmation.

`files().update(addParents=..., removeParents=...)` is the move primitive and works
across parents within one account.

### Cleaning the SOURCE side (NDR's explicit instruction, 2026-09-25)

NDR's standing preference when consolidating *out of a colleague's Drive and into his*
is: **do not leave duplicates behind at the source.** His words — *"whenever we are
copying it from say Rajendra's drive, I want us to change the ownership otherwise of the
content of the drive to me and then file it over here. Or make a copy and delete it over
there either way whichever works… Wherever we are deleting it, let's say in Rajendra's
folder, we should keep a shortcut back to him over there."*

Two acceptable routes, either is fine:
1. **Transfer ownership** of the file/folder to NDR, then file it in the tree. Preferred
   when the item should stop belonging to the colleague at all.
2. **Copy into the tree, then delete the source copy.**

Then leave a **shortcut breadcrumb** where the item used to be, so the colleague's folder
still points at the material:
```python
body = {'name': label, 'mimeType': 'application/vnd.google-apps.shortcut',
        'parents': [source_parent_id],
        'shortcutDetails': {'targetId': target_id}}
svc.files().create(body=body, fields='id,name', supportsAllDrives=True).execute()
```

**Safety rules that override "just get it done":**
- **Never delete or transfer ownership on a source account until the target mailbox is
  proven real** (see Phase 0) *and* the copy is verified present in the tree. Ownership
  transfer and deletion are irreversible-ish and land on someone else's Drive.
- Prefer **copy → verify → delete** over a bare move; verify by reading back the file id
  and size at the destination.
- Flag one genuine judgement call to NDR rather than silently choosing: a breadcrumb
  shortcut in a colleague's Drive is a **live pointer into NDR's tree**, so that account
  retains an ongoing link to the consolidated folder. Offer "shortcut as you asked" vs
  "leave their side clean with no pointer" and let him pick.
- If the mailbox can't be confirmed, **stop and report** — do the non-destructive work and
  say plainly which step is blocked. Do not guess the address.

### Sharing out to a third party (folder-scoped viewer access)

When NDR says "give <person> 90-day viewer access, but only on the folder titled X, Y and
Z — not the whole parent" — share **each named folder individually**, never the parent.
Then **read the permissions back** to prove it:

```python
r = svc.permissions().list(fileId=fid, fields='permissions(emailAddress,role,type)',
                           supportsAllDrives=True).execute().get('permissions', [])
assert any(p.get('emailAddress') == who for p in r)
```

Report per-folder confirmation, and state explicitly which buckets were **not** shared
(the non-legal buckets usually stay private). Share the index sheet separately — it is a
different file from the folders. The announcement email is a **draft** (never sent), with
one link per folder, and a plain description of what the index contains and how to use it.

---

## Phase 4b — The bucket taxomomy for a LAND / title project

`draas-project-folder-structure` gives the canonical 7 (`Title`, `Approvals`, `Legal
Notices`, `Architectural and Engineering`, `Marketing and Content`, `Customer`,
`Communication`) and `draas-drive-organization` notes NDR habitually says "five folder
structure" — it is 7, and answer with the real number.

For a land parcel whose whole point is title, 7 is not enough. Add:

| Extra bucket | Why | Contents |
|---|---|---|
| `<P> Survey Drawings` | NDR asked to split these out; they are drawings, not title | village/boundary maps, private survey drawings (dwg+pdf), tippani, bychart, akarband, sketches, contour, kmz |
| `<P> Banking and Finance` | term sheets / financing | JV & purchase term sheets, cashflow models |

**NDR's explicit placement rule (verbatim intent):** *"title related which is the general
title revenue all of those… then there will be some survey-related… survey drawings you can
put separately if at all and again if revenue related survey put it under title."*
So: **survey *drawings* → Survey Drawings bucket; survey/revenue *records* (RTC, MR, EC,
pahani, mutation register, tax receipts) → stay under Title.** Do not put an RTC in Survey
Drawings just because it says "survey".

Keep the per-survey-number subfolders (`Sy No: 39 documents` etc.) *inside* Title — NDR's
existing organization, and it maps onto per-survey index sheets he already keeps.

Empty buckets: create them anyway (idempotent, shows the intended shape) and report the
zero count honestly rather than hiding them.

---

## Phase 5 — Master index

Build as a **CSV → Google Sheet**, not a native sheet + API row writes. A 572-row index
is one `files().create(body={'mimeType': 'application/vnd.google-apps.spreadsheet'},
media_body=MediaFileUpload(csv))` call and it converts on upload.

Columns that earned their place:

`# | Bucket | Folder | Survey No. | Document Type | File Name | Summary | Size (bytes) |
Modified | Owner | Duplicate? | Drive Link | File ID`

- **Survey No.** — regex the filename for the parcel's numbers; label unmatched rows
  `39/40/41 (unspecified)` rather than blank, so a gap is visible.
- **Document Type** — ordered regex rules over the filename (sale deed, relinquishment,
  gift, partition, GPA, will, MR, RTC, EC, tax/katha, death certificate, family tree,
  affidavit, settlement, title report, revenue certificate, survey/revenue record, court
  document, term sheet, invoice, marketing, image, CAD). First match wins; put the
  narrower/legal patterns **before** the broad ones (`relinquishment` before `deed`).
- **Summary** — a deterministic sentence from (type, survey no, containing folder):
  `"Sale Deed — Gunjur Farm, Sy 39 (in Sy No: 39 documents)."` This is honest and
  re-derivable; it is NOT a content read. Do not imply the file was opened.
- **Duplicate?** — group on `(name.strip().lower(), size)` and mark the count (`x2`) when
  >1. On this session 12 files flagged, and that column *is* the deliverable NDR asked
  for ("so through the index we'll know that any duplicates… will start eliminating").
- **Drive Link** — `c['webViewLink']`, falling back to
  `https://drive.google.com/file/d/<id>/view`. Never hand-build with `/edit`.

**Read the sheet back and report the row count** before declaring done — same
three-counts-agree discipline as the bulk-upload flow:

```python
csv_out = svc.files().export_media(fileId=SHEET_ID, mimeType='text/csv').execute()
assert len(csv_out.decode().splitlines()) - 1 == expected_rows
```

**Do not delete the older per-survey index files** when the master index supersedes them —
move them into the tree and say in the report that the new sheet supersedes them, so NDR
can compare.

### Resolving the duplicates (the step after the index)

NDR will come back with *"work through the duplicate flags and propose which copy to
keep"*, and usually adds a ranking rule — 2026-09-25 it was *"keep the cleaner, higher
resolution, larger file size copy."*

**Check MD5 FIRST, before applying any ranking rule.** Pull `md5Checksum` (and `size`) for
each member of every duplicate group. In practice these groups are same-name copies made
by Drive's "Copy of …" or by a re-upload, and they come back **byte-identical** — on this
session all 12 flagged files were 6 pairs with matching md5, so the "larger file size"
rule had literally nothing to discriminate between and there was no quality or resolution
question at all. Say that plainly to NDR rather than pretending to have exercised
judgement between two identical files.

Then: keep one, **trash** the redundant copy (`files().update(fileId=fid,
body={'trashed': True})`), and report the list. Prefer the copy in the canonical bucket
over the one buried in a legacy subfolder. `md5Checksum` is `None` for Google-native files
(Docs/Sheets/Slides) — for those compare `size` + `modifiedTime` and, if in doubt, leave
both and flag rather than delete.

If MD5s genuinely **differ**, that is when the ranking rule applies: prefer the larger
byte size, then the higher-resolution/later-scan copy, and note which you kept and why.

---

## Reporting

Lead with the finished structure, verified. Include:

- A **bucket | files | subfolders** table with the real counts.
- The **sheet link + row count**, stated as read back.
- **Explicitly: what came in from outside the target folder** (which mailbox, which
  thread, what it was) — this is the value NDR asked for.
- **What was excluded** and why (sibling parcels, the other-Gunjur collisions, non-farm
  parcels sharing a taluk).
- **The duplicates count** and how to filter to them.
- Anything **missing that should exist** — on this session the KEB/KPTCL letters were the
  only electricity-side documents in the whole tree, so the gap was named rather than
  passed over.
- **The deletion picture, explicitly.** In Phase 4 nothing is deleted — say so ("all
  imports are copies; nothing was deleted yet"). But NDR's follow-up *does* ask for
  source-side cleanup (see "Cleaning the SOURCE side"), so once you action that, report
  the opposite: exactly what was deleted or ownership-transferred, on which account, what
  the destination file id is, and where a breadcrumb shortcut was left. Never leave the
  reader guessing which phase they are looking at — state copies vs moves vs deletions and
  the phase.

Finish with 2-3 concrete next-step offers, not a generic "let me know".

### Follow-up asks that arrive after the sweep (expect these)

The consolidation is rarely one turn. The 2026-09-25 session continued with: *"work through
the duplicate flags"*, *"add a short README at the top explaining the tree"*, *"drop a
shortcut to the index in the <counsel> correspondence folder"*, and *"give <person> 90-day
viewer access to folders X/Y/Z and email them"*. Handle each as below.

**README at the top of the project folder.** A `text/plain` file named
`README - <Project> Folder Structure.txt` in the project root, covering: what the tree is
+ the master-index link, the full folder list with what belongs in each, **source /
provenance** (which Drive, which mailbox, what each contributed), superseded indexes,
the duplicate cleanup that was performed, known gaps, and the explicit exclusions. This is
what makes the tree self-explanatory to a future reader (or to counsel) without asking.

**Index shortcut in a correspondence folder.** If NDR asks for a shortcut "in the
Pattanshetti / B.R. Krishna Correspondence folder" and no such folder exists — those are
often *document files*, not folders — create the folder (under Title is the right home for
counsel correspondence) and put the shortcut in it. Use
`mimeType='application/vnd.google-apps.shortcut'` + `shortcutDetails.targetId`.

**Reading a sheet back** to verify row count when the sheet was built by CSV upload:
```python
r = svc.spreadsheets().values().get(spreadsheetId=SID, range='A1:M600').execute()
rows = r.get('values', [])   # row 0 is the header
print(len(rows) - 1)         # data rows
```
Confirm the header row is intact and the count matches before declaring the index done.
