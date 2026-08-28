---
name: google-doc-formatting-template
description: "Create visually appealing Google Docs via HTML-to-Doc import (Drive API). Use proper HTML structure with inline CSS — tables, colored headers, alternating rows, callout boxes — instead of Docs API batchUpdate for new documents."
version: 3.0
author: Hermes Agent
---

**Hard Staging Rule (Nishant Preference — Non-Negotiable)**  
Any new document, spreadsheet, presentation, uploaded file, or artifact created for Nishant **must ALWAYS first be placed in his "TMP" (or "Temp") folder** on Google Drive. Never create anything directly in Drive root. TMP is his explicit staging/cleanup area. He will move items from there. This rule applies to *all* productivity artifacts (Docs, Sheets, Slides, exported reports, etc.).

When creating a new structured Google Doc (partnership notes, risk analysis, governance docs, etc.), **use the HTML import approach** (Drive API upload with `mimeType='text/html'` → conversion to `application/vnd.google-apps.document`). The HTML import preserves inline CSS formatting far more reliably than the Docs API, and produces a print-ready document in one operation.

**Implementation note**: Always set the `parents` field to the TMP folder ID (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`) or use `addParents` + `removeParents="root"` in the Drive API call.

## HTML → Google Doc Import — The Correct Workflow

### When to use which approach

| Approach | Use for | Why it works |
|----------|---------|-------------|
| **HTML import** (this method) | New documents with tables, colored headings, backgrounds, complex layout | HTML → Drive conversion preserves inline CSS. One call, full formatting. |
| **Docs API batchUpdate** | Minor tweaks on an existing doc (font size, bold, margins on clean content) | Surgical updates without recreating the doc. But unreliable for backgrounds/tables. |
| **Hybrid: Drive API create + Docs API insert+format** | Creating a Google Doc from **OCR'd scanned content** (not HTML) — text-heavy legal documents, MOU drafts, agreements | Create blank doc in target folder via Drive API, then use Docs API `batchUpdate` with `insertText` + `updateTextStyle` + `updateParagraphStyle`. Good for text-dominant documents where OCR output has no HTML formatting to preserve. Less suited for documents with complex tables. |
| **DOCX-from-scratch** (`python-docx` → Drive upload) | Structured data displayed in proper tables (references, summaries, comparisons) with clickable links | Building a new doc from data where tables are the primary structure. Docx upload preserves table formatting reliably. Then add URL hyperlinks via Docs API post-conversion. See `references/docx-from-scratch-table-creation.md`. |

### CRITICAL: What causes the HTML import to FAIL

**The HTML import previously produced garbage numbering** (e.g., "1| 2| 3| 29| 30| 31|" with pipes and sequence numbers everywhere) because:

- **DO NOT use `<ol>` tags** — Google Docs import converts `<ol>` into numbered paragraphs with pipes
- **DO NOT use `<li>` tags** — causes the same numbered garbage
- Instead, use `<ul style="list-style-type: disc">` for bullet lists
- For numbered lists, use manual text numbering like "1. " in front of `<p>` or `<ul>` items

**THE FIX THAT WORKS (proven in V5):**
```html
<!-- BAD: This causes garbage numbering -->
<ol>
  <li>Item one</li>
  <li>Item two</li>
</ol>

<!-- GOOD: Use bullet lists with manual numbering -->
<ul style="list-style-type: disc; margin: 6pt 0 6pt 20pt; padding: 0;">
  <li>Starting any new business line outside the approved business plan</li>
  <li>Induction of a new partner, shareholder, or strategic investor</li>
</ul>

<!-- For numbered lists, use manual text numbering -->
<p style="margin: 4pt 0"><strong>1.</strong> Clarity upfront — description here</p>
<p style="margin: 4pt 0"><strong>2.</strong> Prevent misunderstandings — description here</p>
```

### HTML Structure Template

Use the following boilerplate structure. Note: **NO `<head>` or `<html>` tags needed** — just start with `<body>`:

```html
<body style="font-family:Calibri,Arial,sans-serif;font-size:12pt;margin:3cm 2.54cm 2.54cm 2.54cm;color:#222;line-height:1.4">
<!-- TITLE -->
<h1 style="font-size:22pt;font-weight:bold;text-align:center;color:#2b5797;margin-bottom:4px">Document Title</h1>
<h2 style="font-size:16pt;font-weight:normal;text-align:center;color:#555;margin-top:0;margin-bottom:30pt">Subtitle</h2>
```

### Design System

All values confirmed working in V5 (20260628_TeraGreens_Partnership_Discussion_Note):

| Element | Style | CSS |
|---------|-------|-----|
| **Document title** | 22pt Bold, Calibri, color #2b5797, center | `font-size:22pt;font-weight:bold;text-align:center;color:#2b5797` |
| **Subtitle** | 16pt Normal, #555, center | `font-size:16pt;font-weight:normal;text-align:center;color:#555` |
| **H1 (Part I/II/III headings)** | 18pt Bold, white on #2b5797, full-width bar | `font-size:18pt;font-weight:bold;color:white;background:#2b5797;padding:8pt 14pt;margin:30pt 0 18pt 0` |
| **H2 (Section headings)** | 14pt Bold, white on #5b9bd5, full-width bar | `font-size:14pt;font-weight:bold;color:white;background:#5b9bd5;padding:6pt 12pt` |
| **H3 (Sub-section headings)** | 13pt Bold, color #4472c4, no background | `font-size:13pt;font-weight:bold;color:#4472c4;margin:16pt 0 6pt 0` |
| **Normal body** | 12pt, Calibri, color #222 | `font-size:12pt;color:#222;line-height:1.4` |
| **Risk Briefing label** | 12pt Bold | `<strong>Risk Briefing:</strong>` wrapped in `<p>` |
| **Section intro text** | 11pt, #555 | `font-size:11pt;color:#555` |

### Table Design

Tables are formatted with **dark blue header row**, **alternating white/gray rows**:

```html
<table style="border-collapse:collapse;width:100%;margin:10pt 0">
<tr style="background:#2b5797">
  <th style="padding:8pt 10pt;text-align:left;color:white;font-weight:bold;border:1px solid #2b5797">Header 1</th>
  <th style="padding:8pt 10pt;text-align:left;color:white;font-weight:bold;border:1px solid #2b5797">Header 2</th>
</tr>
<tr style="background:white">
  <td style="padding:8pt 10pt;border:1px solid #ccc;vertical-align:top">Data 1</td>
  <td style="padding:8pt 10pt;border:1px solid #ccc;vertical-align:top">Data 2</td>
</tr>
<tr style="background:#f2f2f2">
  <td style="padding:8pt 10pt;border:1px solid #ccc;vertical-align:top">Data 1</td>
  <td style="padding:8pt 10pt;border:1px solid #ccc;vertical-align:top">Data 2</td>
</tr>
</table>
```

Cell properties proven to work:
- Padding: `8pt 10pt` (not 8px — pt converts correctly)
- Borders: `1px solid #ccc` for data cells, `1px solid #2b5797` for header cells
- Dark blue header: `#2b5797` → converts to Docs RGB `0.169, 0.341, 0.592`
- Alternating rows: `#ffffff` (white) and `#f2f2f2` (light gray) → Docs RGB `0.949, 0.949, 0.949`
- First column bold for label columns

### Callout Boxes

For highlighted notes (like "Why 51% for DRA" or "Guiding Principles"):

```html
<!-- Side-bordered callout -->
<div style="background:#e8f0fe;border-left:6px solid #2b5797;padding:14pt 18pt;margin:24pt 0">
  ...content...
</div>

<!-- Full callout box -->
<div style="background:#f0f4ff;border:1px solid #2b5797;border-radius:4px;padding:12pt 16pt;margin:16pt 0">
  <p><strong style="color:#2b5797">Callout title:</strong></p>
  <p>Callout text...</p>
</div>

<!-- Simple gray status box (use single-cell table) -->
<table style="border-collapse:collapse;margin:20pt auto 30pt auto;width:100%;max-width:500px">
<tr><td style="background:#f5f5f5;border:1px solid #ccc;padding:8pt 14pt;text-align:center;font-size:10pt;color:#666">Content</td></tr>
</table>
```

Colors that convert correctly:
- Callout background `#e8f0fe` → Docs RGB 0.910, 0.941, 0.996 (light blue)
- Draft box `#f5f5f5` → Docs RGB 0.961, 0.961, 0.961 (light gray)

### Lists (CRITICAL — avoid `<ol>/<li>`)

```html
<!-- Bullet lists - OK -->
<ul style="list-style-type:disc;margin:6pt 0 6pt 20pt;padding:0">
  <li>Item one</li>
  <li>Item two</li>
</ul>

<!-- Numbered lists - use manual text numbering in <p> or table -->
<p><strong>1.</strong> First item description</p>
<p><strong>2.</strong> Second item description</p>

<!-- Or inside callout boxes using table -->
<table style="border-collapse:collapse;width:100%">
<tr><td style="vertical-align:top;width:30%;padding:6pt 0"><strong style="color:#2b5797">1. Clarity upfront</strong></td>
<td style="vertical-align:top;padding:6pt 0">Description text...</td></tr>
</table>
```

## Upload Script Template

Save as a `.py` file and run with the Hermes venv:

```python
import sys, os
sys.path.insert(0, '/opt/hermes')
os.environ['HERMES_SESSION_USER_ID'] = 'ndr'  # Nishant's Telegram ID

from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3')

# Delete old version if exists
try:
    old_meta = drive.files().get(fileId=OLD_DOC_ID, fields='id,name').execute()
    drive.files().delete(fileId=OLD_DOC_ID).execute()
except:
    pass  # No old doc to delete

# Upload HTML as Google Doc
media = MediaFileUpload('/path/to/file.html', mimetype='text/html', resumable=True)
body = {
    'name': 'YYYYMMDD_DocumentName',
    'mimeType': 'application/vnd.google-apps.document'
}
doc = drive.files().create(body=body, media_body=media, fields='id,name,webViewLink').execute()
print(f"Created: {doc['webViewLink']}")
```

Run with: `/opt/hermes/.venv/bin/python3 upload_script.py`

## Verification

After creating the doc, use Docs API to verify:

```python
docs = build_service('docs', 'v1')
doc = docs.documents().get(documentId=DOC_ID).execute()
body = doc.get('body').get('content', [])

# Check that proper heading styles are present
styles = set()
for elem in body:
    para = elem.get('paragraph')
    if para:
        style = para.get('paragraphStyle', {}).get('namedStyleType', 'NORMAL_TEXT')
        styles.add(style)
print("Styles:", sorted(styles))
# Should show: ['HEADING_1', 'HEADING_2', 'HEADING_3', 'NORMAL_TEXT']

# Count tables
tables = sum(1 for elem in body if elem.get('table'))
print("Tables:", tables)
```

## Version Management
- Delete old document before creating new one (prevents version creep)
- **MANDATORY naming (NDR hard rule, Aug 2026): every document/artifact created or uploaded for Nishant on Google Drive MUST follow `YYYYMMDD_Entity_Description`** — date first (YYYYMMDD), then entity/project name, then document type/description, all separated by UNDERSCORES. No spaces, no "—" em-dash, no "(DD-MM-YYYY)" suffix. Versions allowed as `_v1.0`, `_v0.4` etc. Applies to Docs, Sheets, Slides, HTML/MD/PDF uploads, in ANY folder (including TMP). Examples:
  - ✅ `20260825_Ranka_Oasis_Jiraaf_Term_Sheet_Key_Terms_v1.0`
  - ✅ `20260824_Ranka_Amber_DPR_Slide_Deck.pptx`
  - ❌ `Ranka Oasis × Jiraaf — Term Sheet Draft v0.4 (25-08-2026)`
  - ❌ `RANKA_AMBER_DPR.docx` (no date prefix)
- When renaming a file, use `files().update(fileId, body={'name': new_name})` — the doc ID/link is preserved
- Verify before deleting old: check file exists, check new doc created successfully

## Dual-Purpose: Same HTML → Doc + Email

When the same HTML document needs to serve as BOTH a Google Doc AND an email body (common for offer letters, appointment letters, formal notices):

1. **Write the HTML once** with full document styling (letterhead, tables, signature block)
2. **Upload to Drive** as a Google Doc (HTML import workflow above)
3. **Adapt the same HTML** for email (strip letterhead, add document links, use email-safe CSS)
4. **Create a Gmail draft** with the adapted HTML body

See `references/same-html-to-doc-and-email.md` for the full workflow, including the email adaptation pattern, Gmail API draft creation code, and pitfalls.

## Letterhead Embedding (No HTML Import)

When you need a branded letterhead but don't have a PDF version — build it programmatically and embed via Docs API `insertInlineImage`:

1. **Generate a high-res letterhead image** — two approaches:
   - **Preferred: SVG + cairosvg** — produces professional gradients, curved bars, and CSS-driven layout. No font-path fiddling.
   - **Fallback: Pillow** — for simple monochrome letterheads with system fonts.
2. **Upload the image to Drive** with `anyone` reader permission
3. **Create the Google Doc** with full letter content (via `docs_create` or HTML import)
4. **Embed the image at index 1** via Docs API `batchUpdate` (`insertInlineImage`)

**Key workflow**: Generate image → upload to Drive → create doc with content → embed image at start of body. The doc and content are created BEFORE embedding so the image sits at the top of the letter content.

See `references/letterhead-image-embedding.md` for complete code: SVG templates, font handling, Drive upload with public access, embedding via the Docs API, and the proxy download URL that works for server-side image fetch.

## Hard Staging Rule & Pitfalls

See `references/staging-rule.md` for the full hard constraint on artifact creation (Nishant requires **all** new documents, spreadsheets, presentations, and files to be staged in the TMP folder first — never in Drive root).

## .docx Template → Google Doc Import (When HTML Import Won't Work)

For documents with **complex table structures matching an existing .docx template** (bank forms, SBI builder profiles, legal formats with 6+ tables), use the python-docx → Drive upload approach:

1. Download the .docx template from Drive
2. Fill table cells programmatically with python-docx
3. Upload as Google Doc via Drive API (`mimeType: application/vnd.google-apps.document`)
4. Apply remaining text fixups via Docs API `replaceAllText`

See `references/dotx-template-to-google-doc.md` for full workflow and critical pitfalls (short-number replacement dangers, table cell edit restrictions, quota limits).

## Editing an EXISTING .docx on Drive (spacing + text blanks)

When the user asks to clean up formatting (line spacing, paragraph gaps) or fill in blanks (dates, PAN numbers) on a .docx already on Drive — e.g. a legal letter draft — do NOT try the Docs API (it refuses Office files: "must not be an Office file") and do NOT rely on python-docx `paragraph_format` (spacing settings silently don't persist to XML). Use direct lxml XML manipulation of `document.xml` (create `<w:pPr><w:spacing>` elements), fill text blanks per-run (ellipsis dots are split across multiple runs), re-upload in place with `files().update()` to preserve the link, and verify visually via temp Google Doc → PDF → pdftoppm PNG → vision_analyze. Full recipe with code in `references/edit-existing-docx-on-drive.md`.

## .docx from scratch → Google Doc (when no template exists)

**.docx from scratch → Google Doc (when no template exists)**: For creating a new structured document with proper tables (resources reference, summary docs, comparison tables) where no .docx template exists, build the document with python-docx directly — tables, headers, bullet lists, styling — then upload as Google Doc via Drive API. Key addition: after upload, use `updateTextStyle` with `link` to make URLs clickable (see `references/docx-from-scratch-table-creation.md` for complete code and the URL-split-across-text-runs pitfall).

**Direct Hyperlink Rule (Nishant Preference — Non-Negotiable)**  
All learning, tutorial, or reference documents created for Nishant **must contain direct clickable hyperlinks** to original X threads, official documentation, GitHub pages, and specific YouTube videos. Never use summaries like "search for X on YouTube" or "see @Teknium thread" without an actual `https://` link. Every mentioned resource must be a working hyperlink. See `references/direct-hyperlink-rule.md` for examples and template phrases.

## Editing Existing .docx Files on Drive (In-Place Updates)

When you need to fix formatting or fill blanks in a .docx that's already on Drive (not a Google Doc), the Docs API won't work on it because it's an Office file. Use this workflow:

1. **Download the .docx** from Drive via `drive.files().get_media()`
2. **Inspect with python-docx** for paragraph structure, runs, and spacing
3. **Fix spaces between paragraphs**: The `w:docDefaults` setting may apply `w:after="160"` (8pt) after every paragraph, creating gaps between address lines or body paragraphs. python-docx's `pf.space_after = Pt(0)` and `pf.line_spacing = 1.0` do NOT reliably write to XML — always verify with XML inspection.
4. **Use lxml for reliable spacing changes**: When python-docx doesn't write pPr, manipulate the XML directly — create `<w:pPr><w:spacing w:line="240" w:lineRule="auto" w:after="0" w:before="0"/></w:pPr>` on each target paragraph
5. **Fill text across multiple runs**: Dots/blanks (e.g. `…………`) are often split across separate `<w:r>` runs. Replace by iterating runs, not by string-replacing the full paragraph text. Remove empty runs after replacement.
6. **Use a "FILLED" reference copy** when one exists on Drive — download the filled version to extract exact values (death dates, PAN numbers, addresses)
7. **Upload in-place** with `drive.files().update(fileId=FILE_ID, media_body=media)` — same file ID, same link preserved
8. **Visual verification**: Convert the updated .docx to a temp Google Doc, export to PDF, render to PNG with pdftoppm, verify with vision_analyze

See `references/docx-edit-in-place-workflow.md` for the complete pattern: XML spacing fix, multi-run text replacement, filled-ref extraction, visual verification pipeline.

## Inserting a New Section into an EXISTING Google Doc (Docs API)

For adding a subsection into a live DRA doc (e.g. "2.1A Land Ownership Status & JDA Structure" into each DPR), `insertText` + style batch is right — but ONLY with these rules (each one cost a debug cycle on the Aug-2026 four-DPR ownership update):

1. **Include the heading in the insertText payload.** Insert the FULL text `heading\nline1\nline2\n...` in ONE request. If you insert only body lines and then try to style the "first line" as HEADING_2, the first BODY paragraph gets the heading style and the real heading never exists.
2. **Anchor deletions on markers unique to your inserted block.** Deleting a bad insert via `deleteContentRange [find(marker), find("2.2 ..."))` will silently match the ORIGINAL section-2.1 paragraph when it shares wording with your inserted "Location: ..." line — wiping the user's original content. Compute the deletion range as `[insert_start, insert_start + len(text))` from the index you actually inserted at, or search for a phrase that ONLY exists in your block (e.g. the new heading). Never re-search a phrase that exists pre-insertion.
3. **Newline semantics at a paragraph end.** `insertText` at a paragraph element's `endIndex` appends to that heading's line (`2.1 Land & Location DetailsLocation: ...` — one merged line). To start a new paragraph AFTER a heading, insert `\n` at `startIndex + len(heading_text)`, not at `endIndex`.
4. **Fix paragraph styles per-paragraph, not one range for the block.** A single `updateParagraphStyle` with range `[insert_start, first_end)` inflates to the WHOLE inserted block when indices shift (every inserted line becomes HEADING_2 — verified symptom: all 23 paras show HEADING_2). Re-read the doc, then apply per paragraph: first = HEADING_2, every other = NORMAL_TEXT, and re-apply bold labels (regex `^\s*•\s*([^:]{2,60}):`) + link `textStyle` for the URL substring in each run AFTER the paragraph-style pass.
5. **Chunk style requests ≤50 per batchUpdate** and re-fetch the doc for fresh indices between passes (standard Docs API index-shift rule).
6. **Verify programmatically**: count paras in block, assert exactly one HEADING_2 (the new heading), zero stray HEADING_2 elsewhere in the block, and the expected number of `link` runs (each URL must have a `textStyle.link`).

See `references/insert-section-into-existing-doc.md` for the working two-pass script (insert → restyle) and the delete/re-insert recovery flow used when the first attempt lands badly.

## Pitfalls
- **Rupee symbol pitfall (Aug 2026, Jiraaf term sheet):** HTML `&num;` is `#`, NOT ₹ — Google Docs HTML-import keeps it as a literal `#` (doc silently showed "#5.7 Crore per acre"). Use the actual ₹ character (U+20B9) directly in the HTML source for all money amounts. `&times;`/`&ndash;` are safe; `&num;` for currency is not. Verify post-import by scanning doc text for '#'. Fix later via Docs API `replaceAllText` (matchCase False).
- **`replaceAllText` case pitfalls (Aug 2026):** `matchCase: True` only hits exact-case runs — mixed-case source text ("#5.7 Crore" vs "#5.7 crore") survives the batch. For symbol/number sanitizing use `matchCase: False` and short unique tokens ('#5.7', '#35.34') over full sentences. Also: text verification MUST walk table cell content recursively — a top-level paragraph-only scan misses all table text, and in term sheets the tables carry the whole payload (false negatives looked like a broken build).
- **User edits live Google Docs between sessions (Aug 2026):** NDR updates drive docs in-place outside the session (filled the "?" uplift item to 20% after the last term-sheet session). ALWAYS re-dump the live doc (full walk incl. tables) and diff against your expected content BEFORE rebuilding or editing — never trust a prior session's snapshot as source of truth.
- **Docs API `documents().get` returns EMPTY text if you read the wrong key (Aug 2026).** A paragraph's text lives in `element['paragraph']['elements'][i]['textRun']['content']`. Reading `run.get('text','')` at the *element* level (or `el.get('textRun',{}).get('text','')` incorrectly) silently yields `''` even for long paragraphs — the doc looks blank though content exists (verified: P[231:962] with 731 chars showed `''`). Correct extraction: iterate `p['elements']`, and for each `r` with `'textRun' in r`, append `r['textRun']['content']`. For tables, recurse `tableRows[].tableCells[].content[].paragraph[].elements[]`. Also note top-level `sectionBreak` elements have no `startIndex` — guard with `el.get('startIndex')`.
- **OpenRouter content-generation → HTML-import build pattern (NDR, Aug 2026).** When the user asks to use a specific high-end model (e.g. "GPT 5.5 and above via OpenRouter") to generate a document's content, then build the Google Doc yourself: (1) call `call_openrouter_model` with the full term-sheet/draft spec + settled values to get the content (markdown with pipe tables), (2) convert that into the HTML-import template here (section headings + Term|Value tables + callout boxes), (3) upload via Drive HTML import, (4) verify tables/headings count. The user's intent: the capable model thinks through the content; the standard model does the Docs construction. Trigger phrases: "use a GPT ... via OpenRouter ... then generate the Google Doc".
- **python-docx spacing writes silently fail:** `paragraph_format.space_after = Pt(0)` or `line_spacing = 1.0` may not create `<w:pPr>` in the XML. The paragraph format properties read back as `None`, and the docDefaults continue to apply. Always verify by extracting the raw XML and checking for `<w:spacing>` elements in `<w:pPr>`. The fix is lxml direct manipulation.
- **Dots/blanks split across runs:** A single placeholder like `…………..` can span 2+ adjacent runs. Simple string `replace()` on the full paragraph text will only hit the first run that contains dots. Iterate each run individually and replace dot runs in order.
- **After removing a run from an lxml element tree, the iteration over remaining runs may skip items.** Collect runs into a list first, then iterate.
- **Docs API batchUpdate index shifting:** Every `batchUpdate` call (especially delete+insert) shifts all subsequent document indices. If you read the doc, build requests, and find some replacements didn't work, you MUST re-read the document for fresh indices before the next batch. Never "adjust" indices manually — they shift unpredictably across runs. Leftover fragments (e.g., `ess: [Allottee Address]` after a partial replacement) are a telltale symptom.
- **NEVER use `<ol>` or `<li>` tags** — they produce numbered garbage paragraphs
- **Font sizes**: Use `pt` units (not `px`) for font-size and padding — pt converts directly to Docs points
- **System fonts only**: Calibri, Arial, sans-serif convert reliably. Custom fonts may not appear.
- **No nested divs beyond 2 levels**: Flat table/div structures convert cleanly
- **No flexbox/grid/position/float**: Table-based layout only
- **Auth**: Use `/opt/hermes/.venv/bin/python3` which has all dependencies
- **Session user ID**: Must match the Telegram ID stored in the vault (ndr for Nishant)
- **Rupee symbol in HTML import — `&num;` renders as `#` (2026-08-25).** Using the HTML entity `&num;` for rupee amounts produces a literal `#` in the converted Doc (`#35.34 Crore` instead of `₹35.34 Crore`). Write the literal ₹ character (U+20B9) directly in the HTML file, or use `&#8377;` / `&#x20B9;`. Always verify symbols after import with a full table-cell walk (next bullet).
- **`replaceAllText` is case-sensitive — pass `matchCase: False` for value strings (2026-08-25).** A replacement map keyed on lowercase `'#5.7 crore'` silently misses `'#5.7 Crore'` (capital "Crore") and leaves the bug in the doc. For currency/unit fixups on imported docs, use `containsText: {'text': ..., 'matchCase': False}` and target the invariant fragment (`'#5.7'`, `'#35.34'`) rather than the full phrase, so casing variance can't bite.
- **Verifying table-heavy docs — paragraph-only scans miss all table content (2026-08-25).** After HTML import, a `documents().get()` walk that only reads top-level `el.get('paragraph')` returns EMPTY for table cells — a term sheet can look like the new rows are missing when they're fine. Verification must recurse `tableRows[].tableCells[].content[]` (the same recursive walker used for extraction). Check BOTH negative assertions (removed terms absent) AND positive assertions (new terms present).
- **Removing a financial clause ⇒ recompute headline figures + grep the whole doc (2026-08-25).** Deleting ₹2 Cr goodwill from the Jiraaf term sheet changed net consideration (₹33.34 Cr → ₹35.34 Cr) and left dangling references in other sections. After dropping a money term, search the entire doc for the removed concept (goodwill / % / name), fix net/gross/payment rows, then explicitly flag the headline-number change to the user — silent edits can ship the wrong number.
- **Docs API cannot delete table rows — do versioned rebuilds via HTML import (2026-08-25).** For multi-edit term sheets (remove clause + tweak a schedule), rebuilding as vX.Y through HTML import is cleaner than deleting whole tables / recreating cells batch-by-batch. Keep the old version as reference; verify the new one programmatically.
- **Old doc deletion**: Only after new doc is verified
