# TMP duplicate-file dedup — same file twice in root TMP (verified 2026-10-07)

When NDR says "TMP has two recent files, both seem exact same, one is — eliminate duplicate and file it":

## Signals
- Same filename, same byte size, creation timestamps seconds apart in root TMP = one upload created two copies (common when the same attachment lands twice in a session).
- Worked case: `20260917_Endorsement_ForestDept_Gunjur_Sy39-41.pdf` ×2 in TMP (both 3,191,649 bytes, uploaded 12:10:10 and 12:10:22).

## Procedure
1. **Prove byte-identity first — never delete on name+size alone.**
   `drive.files().get(fileId=..., fields="name,size,md5Checksum,parents,trashed")`. Identical `md5Checksum` AND `size` = same bytes. (Drive stores md5Checksum natively — no download needed.)
2. **Check whether the file is ALREADY filed before moving anything.**
   `drive.files().list(q="name = '<exact filename>' and trashed = false", fields="files(id,name,parents,modifiedTime,owners)")` across the whole drive. In the worked case a THIRD copy already sat in `Gunjur Farm → Gunjur Farm Title` (1A3_5X69WqPYsP4FfJOfF8MlLXfq6F0xH), uploaded 12:10:35 — i.e. a prior session had already filed it; only the two TMP copies were junk.
3. **Branch:**
   - Filed copy exists (verify its md5 too) → delete BOTH TMP copies. Per NDR: "if it's already put in the appropriate folder, delete it from the temp folder in full."
   - No filed copy → move ONE (drive_move add_parents to target folder, remove TMP parent), delete the other; NDR's TMP→project rule applies (explicit instruction or obvious project folder).
4. **Verify after delete:** re-list TMP for the name (expect 0) and the target folder (expect 1, same md5).

## Pitfalls
- Don't trust `trashed=false` only — the filed copy search must include `owners` so you can see whose Drive copy it is (worked case: all copies were ndr@draas.com's own).
- Root TMP folder for ndr@draas.com = `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-` (NOT the ahfl TMP `1bCEdyjMJq9t8DO_x_GjsHp-1bUqgvnlH`). Confirm account first.
- Cross-account search: Gunjur-type matter docs also live under Vinod's (vkdas) Drive in older sessions — same filename may exist there; don't delete someone else's Drive copy, only ndr@draas.com's TMP.