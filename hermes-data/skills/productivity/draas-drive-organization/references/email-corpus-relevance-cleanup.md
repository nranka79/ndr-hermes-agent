# Email-corpus relevance cleanup (round-2: prune the rendered email folders)

Sibling to `evidence-pack-relevance-triage.md` (which handles Documents_Collected).
Trigger phrases: "one more round of complete cleanup on the emails", "now that the
emails are rendered / you created the PDFs, delete everything not related to <name>",
"this email has nothing to do with <customer>, why is it here?".

Applies AFTER `eml-archive-to-pdf.md` produced per-email folders (PDF + email.txt +
Attachments/) and `bulk-drive-tree-mirror-upload.md` mirrored them to Drive. The
rendered pack gives you a huge advantage: **email.txt exists for every email**, so you
classify on full body text, not filenames.

## Why the round-1 flag fails (the user's actual complaint)

The INDEX's `behera` flag was metadata/filename-based, so unrelated mail slipped in:
"DRA Group — Mirabilis Latest Demand Note" and "Updated Financial Statement as of
31st August" (both about **Nishant's own unit A-1001**) landed under a Mirabilis
filename. Lesson: once email.txt exists, ANY relevance decision is body-level. Never
filename-only for an email corpus.

## Body-level classifier design (verified 2026-09-10, Behera pack)

email.txt layout: 7 header lines — `SUBJECT:`, `FROM:`, `TO:`, `CC:`, `DATE:`,
`SOURCE:`, `ATTACHMENTS:` — then a `---` separator line, then the full body (quoted
threads included). Parse headers + body separately; classify on `headers + body`
together (a name may only appear in the header or deep in a quoted thread).

Positive signals (regexes, case-insensitive):
- unit number: `b\s*1\s*[-_/\s]?\s*203\b` AND `\bb1203\b` (both spellings occur)
- subject's email address (e.g. `sabyasachi\.basis@gmail`)
- subject's first name (`sabyasachi|subya\s*sachi|subyasachi`)
- co-allottee first name (`damayant|damayanth|damayanthy`)
- case number: `(?:cmp[\s/_-]*200628|200628|0{2,}6093)` — decisive on its own
- surname alone (`behera`) — keep but tag `behera-surname-only` for review

Negative / disambiguation (override the positives):
- same-surname OTHER customer: `ipsita` (flat A-1002) — drop unless unit/case/his-name also hit
- brand homonyms: `tata\s*cliq|jewell?ery|fashion|couture|luxury\s*discover`
- other-unit trap: `\bA[\s\-_]?1002\b` (Ipsita's flat) without any real positive

Keep rule: ANY positive signal → keep, UNLESS a negative applies. Counts for Behera:
1,989 scanned → 219 keep (ndr_draas 177, sales1 42, ahfl 0, gmail 0), 1,770 drop.

**Timeline check before dropping a "different person":** the 2017 "RG/PR Mirabilis |
Cold/Hot | sabyasachi" sales-lead notifications looked like a different Sabyasachi,
but lead (Oct–Nov 2017) → "Bhavya | Booked | Damayanti Behera" (Dec 2017) → AOS
Apr 2018 = the SAME person pre-booking. Keep leads that precede the booking.

## QA before deleting anything

1. **KEEP audit**: print one match-context snippet per DISTINCT subject (not per email —
   threads collapse to one row) and eyeball them. Catches quoted-thread-noise keeps
   (group Cc threads where the name only rides along).
2. **False-negative sweep**: list DROPPED items whose full text STILL mentions the
   name. In Behera's case all 12 were legitimate: 11 × Ipsita Behera on-boarding +
   1 × Tata CLiQ jewellery ad. If any are real, fix the rule and re-run.

## Drive-side execution

1. **Inventory → plan JSON**: per account folder, list `.eml` files and
   `Readable_Emails/` children; for each, keep vs trash vs missing vs present.
   Save `/tmp/eml_drive_plan.json` (`trash[]`, `present{}`, `missing[]` KEEP dirs not
   on Drive, `eml_missing[]` KEEP .eml not on Drive). This is a point-in-time
   snapshot — see stray-uploader pitfall below.
2. **Trash in process shards** (8), each shard process builds its OWN
   `build_service()`: `files().update(fileId=..., body={'trashed': True})`,
   retry 429/403/500/503. Expect `ok=N fail=0` per shard. (threads segfault with
   googleapiclient — see `bulk-drive-tree-mirror-upload.md`.)
3. **Upload missing KEEP items**: dirs from the local tree; .eml from the source dump
   `/tmp/<dump>/<acct>/<folder>.eml` (the rendered pack does NOT contain the .eml).
4. **Final per-account verify**: for EACH account, `eml_count == len(KEEP)` AND
   `readable_dir_count == len(KEEP)`, no extras unless the local tree was sanitized
   (see double-dot pitfall). Iterate trash/upload until `ALL CLEAN`.

## Pitfalls

- **⚠️ Stray uploader resurrects trashed folders (hit 2026-09-10).** A background
  mirror job from the PREVIOUS turn was still alive and kept creating non-KEEP
  Readable_Emails folders AFTER the inventory was taken. Sales1 readable dirs:
  321 at inventory → 751 mid-cleanup → 462 after trash pass 1 (target 42) → needed a
  SECOND inventory + trash pass (420 more). Before ANY bulk cleanup run
  `ps aux | grep -E '[e]ml|[a]rchive'` and kill/await stray processes; ALWAYS
  re-verify counts after each pass and budget for a second pass. The plan JSON is
  stale the moment another process writes to the same folders.
- **Double-dot .eml stem mismatch.** Source file `…_units..eml` vs sanitized folder
  `…_units` → the `eml_missing` check reports it missing even though it exists.
  Locate by distinctive token (`name contains 'Possession_Letter_-_DRA'`), then
  `files().update(fileId, body={'name': '<folder>.eml'})` to canonicalise.
- **Misleading verify scripts**: account-folder names on Drive are
  `Emails_NDR_<email>` but KEEP tuples use short account keys (`ndr_draas`) — map
  explicitly or every child looks "extra".
- **Ghost-cleanup counts**: a folder-trash also hides children, so a mid-run
  re-count can float; only trust counts taken after a shard pass completes.

## Finish

- Regenerate the pack `INDEX.csv` as KEEP-only rows (account, folder, date, from, to,
  subject, relevance tags) and refresh `README.md` (kept counts per account, what was
  removed, "trash-recoverable" note).
- Save the FULL N-row audit log locally (`/opt/data/<matter>_email_cleanup_log.csv`:
  acct, folder, keep, reason, date, subject) and offer to add the removal list to the
  pack — the user may want it as an audit artifact for counsel.
- Mention the 30-day Drive-trash window; the full corpus stays on server disk.