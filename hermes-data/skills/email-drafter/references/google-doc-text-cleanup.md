# Google Docs text cleanup — force ALL text to black (Docs API)

Use when the user says the online lease/deed doc "must be fully cleaned — all text in black" (usually
after collaborative edits by another party, e.g. Aamir/Akber editing a shared Google Doc) before the
doc is exported to .docx and attached to an email.

## Pitfall 1 — `rgbColor` with missing channels is BLACK, not white (critical)

The Docs API `rgbColor` object defaults missing channels to **0.0 (black)**, NOT 1.0. A naive check like
`rgb.get('red', 1.0)` misclassifies every run whose color is simply `{}` (i.e. default black) as "white"
— this produced a false "29 white runs" alarm in Aug 2026; the doc was already fine and the batchUpdate
that followed was a harmless no-op.

**Correct check:**
```python
fc = text_run.get('textStyle', {}).get('foregroundColor', {})
if fc:
    rgb = fc.get('color', {}).get('rgbColor', {})
    r = rgb.get('red', 0.0); g = rgb.get('green', 0.0); b = rgb.get('blue', 0.0)
    non_black = not (r == 0 and g == 0 and b == 0)
```

Also note: even after batchUpdate sets a run to black, the Docs API returns it as
`"rgbColor": {}` (empty) — the API canonicalizes black to empty. So verify with the correct defaults,
not by string-comparing the returned JSON.

## Pitfall 2 — `suggestionsMode` is NOT a valid parameter

`documents().get(documentId=..., suggestionsMode="RETURN_SUGGESTIONS")` raises
`TypeError: unexpected keyword argument`. The correct parameter is `suggestionsViewMode`, with only
these allowed values: `'DEFAULT_FOR_CURRENT_ACCESS' | 'SUGGESTIONS_INLINE' | 'PREVIEW_SUGGESTIONS_ACCEPTED' | 'PREVIEW_WITHOUT_SUGGESTIONS'`.

Use `suggestionsViewMode="SUGGESTIONS_INLINE"` to detect pending suggested insertions/deletions
(check `textRun.suggestedInsertion` / `suggestedDeletion` keys). Zero suggestion IDs = all collaborative
edits are already accepted/committed.

## Batch update to force black

1. Walk body + tables + headers/footers; collect every text run whose foreground is non-black (per
   Pitfall 1), recording start/end indices.
2. Sort & merge overlapping/adjacent ranges.
3. One `batchUpdate` with one `updateTextStyle` per merged range:
   ```python
   {'updateTextStyle': {
       'range': {'startIndex': s, 'endIndex': e},
       'textStyle': {'foregroundColor': {'color': {'rgbColor': {'red': 0, 'green': 0, 'blue': 0}}}},
       'fields': 'foregroundColor'
   }}
   ```
4. Re-fetch and re-verify with the correct default handling — expect 0 non-black runs.

## Visual verification (belt & braces)

API checks can miss style-layer colors (HEADING_1/2 named styles default to blue in GWS templates even
when runs carry black). Export the doc to PDF and rasterize the first pages:

```python
# export via Drive API
drive.files().export(fileId=DOC_ID, mimeType='application/pdf')
# then: pdftoppm -png -r 80 -f 1 -l 2 lease_deed_check.pdf lease_pg
# then vision_analyze the PNG: "Is the heading visible in black? any white-on-white?"
```

If the run-level foreground is explicitly black, it overrides the named style, so a PDF render should
show black headings — but verify anyway; it's cheap and catches the false-negative case.

## Confirm it's the right doc

Before cleaning/attaching, confirm the online doc is the one the collaborator just edited:
`drive.files().list(q="name contains 'Lease' ...")` and inspect `lastModifyingUser.emailAddress` +
`modifiedTime`. The user's "Aamir has just edited it" should match the file metadata exactly.

## Then attach

Export the cleaned doc to .docx via Drive API export (mimeType
`application/vnd.openxmlformats-officedocument.wordprocessingml.document`) and attach to the threaded
reply draft (see email-drafter `templates/draft-with-attachments.py`; bridge draft_create has no
attachment support). Name per NDR convention: `YYYYMMDD_DescName.ext`.
