# Incoming consolidated / "combined legal set" — intake & reconciliation

Trigger: NDR drops a large consolidated legal PDF (e.g. *"KP Combined Legal Set
30NOV16_compressed.pdf"*) into TMP and says something like:

> "File it in the appropriate Mirabilis folder, legal folder. Then examine each
> of the documents in there — it's a combined legal set, so there's an index.
> See if this is already existing in our legal folder. If all the documents are
> already there, then we ignore this — bring it to my notice and I will look at
> those individual documents and see which scan quality is better, then we
> decide which one to keep."

The order of operations NDR asks for is **file first, then reconcile** — don't
analyse before the file is in its folder.

## Step 1 — File into the project legal folder first

Locate the project's legal root by Drive search, not by memory. Verified ids
(Kolte Patil / Mirabilis, 2026-09):

| Role | Id | Name |
|---|---|---|
| Mirabilis legal root | `0Bw-tZQ5aDnc3M2ZvRTZjZGh4ZDA` | **"Mirabilies Legal Set"** (note the typo — search `Mirabilis`, don't string-match exactly) |
| Prior consolidated set | `0B1Oc8cSaJXPGYjduWk1RUnNfaGc` | "Mirabilis Updated Set 19/05/2018" (subfolder of the root) |
| Nested per-document folder used for listings | `0Bw-tZQ5aDnc3dEdoa3hsdjFDclE` | (documents folder under the legal root) |

Move with `gws_drive_move`, `add_parents=[<legal folder>]`,
`remove_parents=['18p74II2uL32sNDzDDwXzmlOUdJJOTmE-']` (TMP).

Legal folders are widely shared — expect many writers/readers (Prashanth,
Piyush, CRM, Bharat, E. Chamundeshwari…). **Report odd access, never change an
ACL unilaterally.**

## Step 2 — Extract the index (two sources, in this order)

1. **Look for an authoritative index as a Google Doc** in/next to the same
   folder (this case: *"INDEX (Updated Set 19/05/2018)"*). Export it — the Doc
   beats OCR of the scan:
   ```python
   svc.files().export_media(fileId=DOC_ID, mimeType='text/plain').execute()
   ```
2. **Text layer of the combined PDF, index pages only.** Big consolidated sets
   are scans: this one had text on pages 1–8 only; pages 9+ returned nothing but
   form feeds and raised `TypeError: bool(hits)` in PyMuPDF page searches — i.e.
   don't fight it, the rest is images.
   ```bash
   pdftotext -layout -f 1 -l 8 kp_combined.pdf kp_index.txt
   pdftoppm -jpeg -r 60 -f 1 -l 1 kp_combined.pdf page   # render to read visually
   ```

## Step 3 — Recursive listing of what we already hold

Tool payloads for these folders are huge (30k+ chars). Use a small paginated
script that prints `name<TAB>size<TAB>id` per line into a TSV, run it against
**both** the prior consolidated folder and the legal root.

## Step 4 — Reconcile by serial base key

Match `index serial → existing filename`, keyed on the serial base (`00001`,
`00002`, …) and cross-checked by date/description.

**Tail items diverge.** The 2018 consolidated set re-numbered the tail relative
to the older 2016-era listing, so pure key matching fails there. Keep a
hand-built semantic map for those, e.g.:

- combined `00101 / 00102 / 00103` (ECs 2012→2016) → existing `00117
  "EC from 01.04.18 to 12.12.18.pdf"` (the later EC supersedes them)
- combined `00104…00115` → existing `00101…00110` (tax receipts, BBMP licence
  letter, commencement certificate, rectification deed, confirmation deeds)

Report per row as **duplicate** vs **new**, and give counts (`114 index rows /
114 matched`) rather than a wall of filenames.

## Step 5 — The decision rule (NDR's, not yours)

- **Every document already present** → do NOT keep the new set, do NOT delete
  it silently either. It stays filed where he asked; you **bring it to his
  notice**, state plainly that nothing in it is new, and note that the new copy
  is CamScanner-sourced with mixed scan quality. He then compares scan quality
  document-by-document and decides which copy survives.
- **Some documents new** → list only the genuinely new ones with their index
  description + date, and ask whether to file them separately.
- Offer a page-by-page scan-quality comparison only if he wants it — don't
  produce it unprompted (a 395 MB, 500-page scan).

## Pitfalls

1. **Never conclude "duplicate" from the index alone** — confirm against the
   actual folder listing (name + size + id).
2. **Index serials skip.** The folder held `00045`/`00116` files not present in
   the index; match on name+date, never on position.
3. **Don't re-derive what a prior session already did.** Check for existing
   `recon.json` / `existing_*.tsv` work products in the working dir first.
4. **Don't shove the whole combined PDF's text into context.** Pages 9+ are
   blank; a few index pages + a rendered thumbnail is enough to verify identity.
