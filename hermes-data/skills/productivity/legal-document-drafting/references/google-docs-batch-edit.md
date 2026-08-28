# Google Docs batch editing — new version with highlighted changes

## When to use
User asks to modify an existing legal document draft in Drive (deed, agreement, etc.)
and wants a **new version** with **changes highlighted**. Standard workflow for
Prakash/NDR legal-doc change requests (proven on R3N KAAJ DEED_OF_PARTNERSHIP_v2→v3, 2026-08).

## Workflow
1. **Never edit the original** — copy to a versioned file first:
   `drive.files().copy(fileId=<id>, body={'name': name.replace('_v2', '_v3')})`
   files.copy keeps the same Drive parent. Docs copy preserves formatting 100%;
   docx round-trip (export→edit→re-import) risks font/numbering drift — avoid for legal docs.
2. **Read structure** via `docs.documents().get(documentId=...)`.
   - Paragraph text extraction: `element['textRun']['content']` — BUG TRAP: `run.get('text','')`
     silently returns `''` and you get 0 paragraphs / "document is empty".
   - Google Docs legal drafts often wrap the whole body in a **1-row table** (table →
     `tableRows[] → tableCells[] → content[] → paragraphs`). Walk RECURSIVELY (top-level
     + inside every table cell) or you will miss everything past the first section break.
   - Paragraph range: `[startIndex, endIndex)` — endIndex includes the trailing `'\n'`.
3. **Build ONE batchUpdate**; per edit, in this order:
   a. `deleteContentRange` over the region
      (whole paragraph: `[start, end-1)` keeping the newline; mid-paragraph: exact substring range)
   b. `insertText` at region start — **SKIP when replacement text is empty** (deletion-only edit)
   c. `updateTextStyle` re-applying the ORIGINAL `textStyle` captured from the textRun at the
      insertion point (fields mask: `bold, italic, underline, strikethrough, smallCaps,
      fontSize, weightedFontFamily, foregroundColor, baselineOffset`). Inserted text does
      NOT reliably inherit formatting — without this, bold headings go plain and vice-versa.
   d. `updateTextStyle` yellow highlight:
      `textStyle={'backgroundColor': {'color': {'rgbColor': {'red': 1.0, 'green': 1.0, 'blue': 0.0}}}}, fields='backgroundColor'`
4. **Index ordering**: process paragraphs in DESCENDING start-index order inside the single
   batch. Deleting/inserting at higher indices never invalidates the lower (earlier) paragraphs'
   ranges; compute all ranges from the ORIGINAL doc and just sort desc.
5. **batchUpdate is ATOMIC** — one invalid request rejects the ENTIRE batch (nothing applied).
   Known killer: `insertText` with empty text → `Invalid requests[N].insertText: Insert text
   requests must specify text to insert.` Guard empty inserts (e.g. pure-deletion edits).
6. **Verify before reporting success**:
   - export `text/plain`, assert forbidden/old terms → 0 occurrences (case-insensitive)
   - re-scan runs for `backgroundColor` to confirm highlights actually landed
   - diff old vs new export → give the user the change log
   - return the new doc `webViewLink` (drive link), never a hardcoded chat destination.

## Notes
- Use `gws_resolve_account` + `tools.gws_auth.build_service('docs','v1', service_name=...)`
  (this session: `google-draas` for PS).
- Highlight range coordinates are relative to final paragraph text; compute offset by
  `final_text.find(hl_substring)` and anchor at `body_start + hl_rel`.
- After renames of a defined term (e.g. "C R Nagendra Lands" → "First Partner Lands"),
  grep the WHOLE doc for residual old-term occurrences and fix every one (recitals,
  subtitles, schedules, conditions precedent).