# Google Docs tracked edits — "new version with highlighted changes"

DRAAS workflow for legal deeds (e.g., R3N KAAJ partnership deed, v2 → v3 → v4_NoSchedule, Aug 2026).
Used whenever the user says: *"make changes in this draft as new version"*, *"PL generate a new version"*,
*"HIGHLIGHT THE CHANGES"*, *"NO OTHER REFERENCES TO X"*, or attaches a reference doc with *"AS PER THIS"*.

## Workflow (do all steps — the user expects a working link, verified)

1. **Always copy first, never edit the original.** `drive.files().copy(fileId, body={'name': ...})`.
   `files.copy` keeps the SOURCE name — set the name explicitly, following the DRAAS convention:
   `YYYYMMDD_DEED_OF_PARTNERSHIP_<FIRM>_<SUBJECT>_v<N>[_NoSchedule]`. Rename if you forgot.
2. **If a reference doc is provided**, export it first (`drive.files().export(mimeType='text/plain')`)
   and mirror its structure. WARNING: a reference may reintroduce things the user banned elsewhere —
   apply the user's explicit change rules ON TOP of the reference structure (session example: the
   NoSchedule reference still carried Satvik / C.R. Nagendra / Partition Deed references; final deliverable
   combined no-schedule structure + zero Satvik/CRN/Partition mentions).
3. **Read target paragraphs precisely** via Docs API `documents().get(documentId=...)`. Paragraph text
   lives at `element['textRun']['content']` — NOT `element.get('text')` (that returns nothing).
   Content may sit inside tables — recurse `table → tableRows → tableCells → content`.
4. **Build edit specs**: `marker` (unique substring identifying the paragraph), `region_old` (exact text
   to delete; `''` = whole paragraph), `insert` (replacement; `''` = deletion only), `hl` (substring of
   the FINAL paragraph text to highlight yellow; `'__WHOLE__'` = whole paragraph).
5. **One atomic `batchUpdate`** with ops per edit, ordered DESCENDING by paragraph startIndex:
   - `deleteContentRange [r_start, r_end)`
   - `insertText` at `r_start` — **SKIP entirely when insert is empty**: an empty insertText request
     rejects the WHOLE batch (atomic), nothing gets applied.
   - `updateTextStyle` on the inserted range re-applying the ORIGINAL run's textStyle (captured before
     the edit) plus a fields mask — otherwise inserted text inherits unreliable formatting; instead
     bold definition/heading runs would lose bold.
   - `updateTextStyle` highlight with `textStyle: {backgroundColor: {color: {rgbColor: {red:1, green:1, blue:0}}}}`,
     `fields: 'backgroundColor'` (classic yellow).
6. **Deleting a whole paragraph** (obsolete definition, dead clause): delete `[start, end-1)` KEEPING the
   trailing `\n`, or the next paragraph merges into the previous one. A leftover blank line is acceptable.
7. **Post-edit verification (mandatory):**
   - Export `text/plain`, run `difflib.unified_diff` vs the original — each intended change visible.
   - Assert **0 occurrences** of every banned term (case-insensitive) across the whole doc.
   - Count highlighted runs (scan for `textStyle.backgroundColor`) — should be > 0.
   - Print the `webViewLink` and a change summary. Verify changed paragraphs read coherently
     (deletions mid-sentence can leave double spaces or missing periods — patch those).

## Pitfalls
- Docs API text extraction: `r['textRun'].get('content','')` is the only reliable key.
- `batchUpdate` is atomic — one invalid request (e.g., empty insertText) rolls back all edits silently.
- Region strings must match EXACTLY incl. spaces/tabs/periods; after delete+insert check the junction
  for double spaces or missing periods (session fix: inserted `.` where a removed period left "Lands The").
- Highlights: whole-paragraph replacements → highlight entire new paragraph; substring edits → highlight
  just the insert; pure deletions cannot be highlighted — flag them in the reply and highlight the
  surrounding sentence instead.
- Style preservation: always capture the style of the run at `r_start` and re-apply; do not rely on
  insert-inheritance.

## Reusable implementation
`scripts/google_docs_tracked_edit.py` — working delete+insert+highlight batch editor with EDIT_SPECS
structure, style capture, descending order, and verification helpers. Copy a doc, fill EDIT_SPECS, run.