# Drive ownership consolidation & team sharing (NDR workflow)

Use when NDR says "consolidate all <entity> documents into one folder",
"make sure they're available in the folder shared with <team>", "change
ownership of all of these to me", after a doc search spread files across
colleague drives (sales1.blr@draas.com, bhavesh@draas.com, narayan@ahfl.in).

Proven on AHFL Ranka Stelo Dharwad (2026-09-22): ~200 nodes moved from
Bharat's drive + own-drive extras consolidated into one NDR-owned folder.

## Steps

1. **Inventory with the OWN token first.** Walk the full tree with
   `build_service('drive','v3', service_name='google-draas')` +
   `files().list(q=f"'{parent}' in parents and trashed=false", pageSize=300)`.
   DWD recursive listings can silently skip subfolders (see pitfall) — use
   own-token enumeration of the shared tree for the full map.
2. **Move the root folder** (`files().update(addParents=..., removeParents=...)`)
   as its current owner, then transfer ownership of EVERY node (root + all
   children) to ndr@draas.com. Sequential transfer loops are slow (~1 node
   per call); chunk them and resume from whatever did not complete.
3. **Verify by reading back** — never trust loop exit status alone. List each
   node's `owners` and confirm ndr@draas.com after the batch.
4. **Move in NDR's own core docs** (OC, RERA set, plans, no-dues samples) from
   other locations into the consolidated folder.
5. **Sweep for outliers** once consolidated (name search for unrelated files —
   e.g. stray Japan Airways tickets rode along inside AHFL FILES 4). Delete
   permanently with `files().delete()` and confirm 404 when NDR approves.
6. **Rebuild the index spreadsheet** in the MAIN folder root (not subfolder):
   one row per doc — name, folder path, short description, HYPERLINK to file
   ID. Derive descriptions from filenames: normalize underscores → spaces
   before matching rules; exclude the index sheet itself from its own rows.
7. **Viewer grants (360 days):** reader role + `expirationTime` on BOTH the
   folder and the index sheet for each named viewer. If a colleague previously
   had writer (granted temporarily to enable the move), explicitly reset them
   to reader afterwards — verify final permission list.
8. **Email draft** (draft only, never send): to the primary viewer, folder
   link + index link + short contents summary.

## DWD account map (draas.com, verified)

- Anbu / Anbarasan = **pm2.blr@draas.com** — anbarasan@draas.com FAILS
  invalid_grant; never use it.
- Bharat Hawaldar = sales1.blr@draas.com; Roshni Ranka = rnr@draas.com;
  Piyush = piyush@; Bhagya = crm.blr@ (NOT bhagya@); Bhavesh = bhavesh@.
- Resolve before use; own-token tools need `service_name` explicitly.

## YOU CANNOT DELETE WHAT YOU DO NOT OWN — transfer first, then delete (verified 2026-10-05)

Deleting an item owned by another account fails **even when ndr has writer rights
via the parent folder**, and it fails the same way for both delete and trash:

```
files().delete(fileId=...)                -> 403 insufficientFilePermissions
files().update(body={'trashed': True})    -> 403 insufficientFilePermissions
```

Both were tried on `Approved Doc- Plan Sanction  and building Approval`
(owned by `sales1.blr@draas.com`, sitting inside ndr-owned `Ranka Amber Approvals`).
Writer-on-the-parent confers **no** delete or trash right.

**The fix — DWD-transfer ownership, THEN delete:**

```
gws_dwd_drive_transfer_ownership(target=<current owner>,
                                 new_owner_email='ndr@draas.com',
                                 file_id=<id>)
# read back owners == ndr@draas.com, then:
gws_drive_delete(file_id=<id>)          # plain own-token delete now works
```

Do the transfer on the **folder AND every document you are keeping out of it** in
the same pass — NDR's standing instruction is that DRA project documents should
end up **owned by `ndr@draas.com`**, not merely shared. Re-verify with
`files().get(fields='id,name,owners,permissions')`: the previous owner stays on as
`writer`, which is usually correct; offer to trim it rather than trimming silently.

**DWD has a hard domain ceiling.** The service account can only impersonate
accounts inside the delegated domain (`draas.com`). It **cannot** act as
`bk@findingform.design`, `BK@fnw.homes`, `ndr@findingform.design`,
`esotericarts.ani@gmail.com`, `structure.pune@gmail.com` — so ownership of
externally-owned files **cannot be taken at all**. Say so plainly and offer the
workaround: copy the file into NDR's tree (the copy is ndr-owned) and leave the
original untouched. Do not promise a transfer you cannot perform.

## Bulk sweep — "take ownership of every <project> file owned by anyone else"

Trigger (2026-10-05, Ranka Amber): *"all <project> related documents owned by
anyone else, shared with me but owned by anyone else — take the ownership, move
them to the appropriate <project> folder, rename them if they don't follow the
convention, and share them back with the current owner."*

**1. Measure before mutating — never quote NDR's own estimate back as the scope.**
He said "most likely owned by Bharat or Prakash or Anbarasan or Kantesh or
Sinchana". Measured reality on 363 files: Prakash 128, Finding Form 74, Sinchana
69, Bharat 67, Anbu 5, **and Kantesh zero**. Report the real owner histogram; the
named people are a hint, not the population.

**2. Two-part enumeration** (`scripts/scan_project_corpus.py` does both):

- **Whole-account view:** `files().list(q="sharedWithMe and trashed=false")`,
  then drop anything where `ndr@draas.com in owners`. On this drive that is
  **~3,050 items** — too many to reason about, so it is the *context*, not the
  work list.
- **Project view (the actual work list):** seed on folders whose name matches the
  project (`name contains 'Amber'` → 31 seeds), then BFS every descendant. Add
  loose files matching the name anywhere. Result: 663 items, **363 not owned by
  ndr**, across 15 source folders.

**3. Stamp the source folder name, not the folder ID, onto every row.** A naive
walker that seeds `queue = [(id, name, root=id)]` labels every top-level child
with the seed's **ID**, and the plan prints a wall of `1fKJi6v1uoUPs-…` instead of
`Ranka Amber Approvals`. Keep a `seed_id -> seed_name` map and resolve at report
time.

**4. Classify by SOURCE FOLDER first, filename second.** Filename regexes are far
weaker than they look — on this corpus a name-only classifier dumped 32 files from
`RANKA Amber - Scanned Documents for RERA Approval` and all 10 render PNGs
(`Lobby 1.png`, `Terrace 2.png`) into `Misc`. The source folder is the stronger
signal: a folder already named as a bucket (`Ranka Amber Approvals`) routes its
contents there; an architect working set (`Amber`, `Amber Execution`,
`Amber Basement`) routes to Architectural and Engineering; a render set routes to
Marketing and Content.

**5. Split the work list into the part he specified and the part he didn't.**
Internal-owner files (`@draas.com`) = the class he named → the specified work.
Externally-owned files = the slice he did not anticipate → **flag with counts,
recommend copy-not-transfer, and let him decide.** That split is also the
execute-vs-stage line for this class (see `confirm-before-actions`).

**6. Report the rename/cleanup consequences with numbers before acting.** On this
sweep: **354 of 363 filenames** violated `YYYYMMDD_RankaAmber_Description`, most
carrying no date at all — so a rename pass means sourcing a date per file (from
the document where visible, else Drive `createdTime`, flagged). Also name what
happens to the **emptied source folders** afterwards (delete vs leave). These two
plus the external-owner question are the real decisions; ask them together, once.

## Notes / pitfalls carried from earlier sweeps

- **Recursion bug:** nodes returned with children pre-attached fool naive
  walkers into skipping descent — re-walk from each folder id explicitly.
- **`{file_id, new_owner}` transfer response is the SUCCESS ACK**, not an
  error — confirm via owners read-back, not response shape.
- Batch loops time out on 150–200 sequential transfers; resume + verify.
- Index description matching fails on underscore-separated filenames until
  you normalize `_` → space.
- The shared folder landing in My Drive ROOT is not the final location —
  propose the entity chain (e.g. My Drive / Current Properties / <Entity> /
  <Folder>) and WAIT for NDR's confirmation before moving.