# Incoming consolidated legal sets — file, reconcile, and the duplicate rule

**Trigger:** NDR drops a *combined legal set* into the TMP/drop folder and dictates
something like: *"file it in the appropriate Mirabilis legal folder first. Then examine
each of the documents — there's an index. See if this is already existing in our legal
folder. If all the documents are already there, then ignore this, bring it to my notice.
I will look at the individual documents and see which scan quality is better and then we
decide which one to keep."*

Validated 2026-09-28 (KP Combined Legal Set 30NOV16 → Mirabilis). This is a recurring
class: lenders, Kolte Patil / JDA partners and counsel periodically re-issue the whole
title set as one PDF.

## 1. Stable file-first, reconcile-second

Always **move the PDF into the project's legal folder first** (as NDR asks) — the
reconciliation happens against the folder it now lives in, and the move is cheap to
reverse. Drop folder → destination with explicit parents:

```
gws_drive_move(file_id=..., add_parents=["<legal folder id>"],
               remove_parents=["18p74II2uL32sNDzDDwXzmlOUdJJOTmE-"])
```

## 2. The index is usually a Google Doc, and the PDF's own first pages

A combined set normally has TWO index sources — use both, they cross-check each other:

1. **A separate "INDEX (Updated Set …)" Google Doc** in the same legal area — export it
   with `files().export_media(mimeType='text/plain')`. This is the authoritative list.
2. **The PDF's own opening pages** — `pdftotext -layout -f 1 -l 8`.

**Pitfall — these sets are scanned after the index.** In this case `pdftotext` returned
real text for pages 1–8 (index + notes) and **only form feeds** for pages 9+ (the deeds
themselves are images). Don't conclude the file is corrupt or "has no text" — extract the
index, and OCR individual pages only when a specific document's content matters:

```bash
pdftoppm -jpeg -r 90 -f 12 -l 12 set.pdf page && vision_analyze page-12.jpg
```

## 3. Recursive listing of the target folder

`gws_drive_list` payloads are far too verbose for a 100+ document folder: write a small
paginated recursive lister instead (`files().list(q="'<folder>' in parents and
trashed=false", pageSize=1000, fields=...)`), emit one TSV line per file
(`name  size  id`), and keep it on disk. You will re-run it after the move.

## 4. Reconcile serial-by-serial, then hand the tail to a manual map

Parse the index into `serial | description | date`, then match each row against the
listing by **serial-number base** in the filename (our legal docs are named
`000NN <description>.pdf`).

**The tail will not key-match.** When a set is re-issued, the newer numbering diverges:
2018 serial `00101` = the EC that supersedes the older set's `00117`, and the tax
receipts / licence-plan letters shift by a fixed offset. Do **not** force fuzzy matching
across the whole tail — build an explicit `manual_tail` dict for those rows with the
reason inline (`'00101': ('00117', 'EC 01.01.10-29.06.17 (supersedes ...)')`). A hand-map
of ~15 rows is auditable; a fuzzy matcher that silently mis-pairs a deed is not.

## 5. The decision rule (NDR's, verbatim in effect)

- **Every index document already present in the legal folder → do NOT keep the combined
  set.** Bring it to NDR's notice with the count, name the folder it duplicates (here:
  `Mirabilis Updated Set 19/05/2018`, a subfolder of `Mirabilies Legal Set`), and state
  that the new copy is a CamScanner-sourced scan of mixed quality.
- **He then compares scan quality doc-by-doc and decides which copy to keep.** Offer the
  per-document quality comparison; do not pre-empt the decision.
- **Action he gives next is usually "delete the uploaded PDF"** — do it with
  `gws_drive_delete` (goes to Drive Trash, ~30 days recoverable) and say so, so he knows
  it is not gone forever. Verify by re-listing the destination folder.

## 6. Reporting shape

Numbers first, then the rule, then the ask: *"114 index documents (00001–00115); all 114
already exist in the legal folder; the set mirrors <folder> doc-for-doc; bringing it to
your notice rather than keeping it — tell me if you want a page-by-page scan-quality
comparison."* NDR reads this structure as the audit trail.

## Pitfalls

- **Don't equate "filed" with "kept."** He asks for the move *before* knowing whether the
  set is a duplicate; a later "delete it" is expected, not a contradiction.
- **Don't report "all duplicates" off filename similarity alone** — confirm the mapped
  counterpart exists in the recursive listing, not just that a similar name appeared.
- **Filenames carry the serial as a zero-padded prefix** (`00007 Sale Deed Dt …`); strip
  leading zeros consistently on both sides or every comparison misses.
- **A 395 MB scan** is normal for these sets — start the download in the background with
  `notify_on_complete`, don't block the turn on it.
