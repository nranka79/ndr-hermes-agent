# Editing a .docx on Drive in place (spacing, placeholder fill, dates)

Scenario: the user points at an "online version" of a document on Drive
(`docs.google.com/document/d/<id>/edit`) that is actually an Office file
(.docx), not a native Google Doc. They want formatting cleaned up, blanks
filled, dates changed — while keeping the SAME link.

## Detect Office file

- Docs API `documents().get()` fails with:
  `HttpError 400 ... "This operation is not supported for this document. The document must not be an Office file."`
- Confirm with Drive: `files().get(fields='id,name,mimeType,size')` — mimeType is
  `application/vnd.openxmlformats-officedocument.wordprocessingml.document`.
- Docs API `batchUpdate` / `replaceAllText` also refuse Office files. Edit the .docx directly.

## Workflow (proven 2026-08-17, Dinesh Ranka Giving Effect Order letter)

1. **Download**: `drive.files().get_media(fileId)` → BytesIO → save .docx locally.
2. **Find source values before filling blanks**: search Drive for a sibling
   "FILLED" version (`q="name contains '<doc>' and name contains 'FILLED'"`).
   NDR's team keeps filled-in copies holding the exact values (death date, PAN).
   The FILLED doc is the fastest source when the user says "you have all the details".
3. **Edit with lxml, NOT python-docx, for spacing**:
   - `paragraph_format.line_spacing = 1.0` / `space_after = Pt(0)` writes did NOT
     persist (read-back showed `None`; XML had zero `<w:spacing>` elements even
     though the setter printed success). Do not debug this — go straight to XML.
   - Robust path: parse `word/document.xml` with lxml; for each paragraph create
     (or fill) `pPr` + `<w:spacing w:line="240" w:lineRule="auto" w:before="0" w:after="0"/>`
     for tight single spacing; omit `before`/`after` where paragraph separation
     is wanted. The docDefaults line (`w:spacing w:after="160" w:line="259"`) is
     what makes every paragraph inherit gaps — explicit per-paragraph spacing
     overrides it.
   - Re-zip: read all zip entries, replace only `word/document.xml`, write a new
     zip (ZIP_DEFLATED), preserve every other entry byte-for-byte.
4. **Fill placeholder dots ("……") — DANGER: split across multiple runs**:
   - The placeholder can span 2+ `<w:r>` runs (e.g. "Ranks passed away on ………"
     + a separate "….." run). Naive per-run `replace('………', value)` duplicates
     content (real bug this session: the body sentence got duplicated twice).
   - Fix: identify runs by an anchor substring (`'Ranks passed away on'`,
     `'my Pan number is'`), rewrite that run's text wholesale to the full correct
     sentence, and DELETE leftover dot-only runs (`p.remove(r)`).
5. **Re-upload in place**: `drive.files().update(fileId=FILE_ID,
   media_body=MediaFileUpload('clean.docx', mimetype=...))` — same ID, same link,
   sharing preserved. Also pass `body={'name': ...}` in the same call to rename
   (e.g. date changed 7 Jul → 17 Aug).
6. **Visual verification pipeline (no LibreOffice)**:
   - Create a temp Google Doc copy: `drive.files().create(body={'mimeType':
     'application/vnd.google-apps.document'}, media_body=...)` — Drive converts the .docx.
   - Export PDF: `drive.files().export_media(fileId=temp_id, mimeType='application/pdf')`.
   - `pdftoppm -png -r 200 out.pdf page` → `vision_analyze(page-1.png, ...)` asking
     specifically about line-gap consistency within each section (tight vs loose).
   - Delete the temp doc after export.

## Extracting the source data from a large scanned sale-deed PDF

A common DRAAS redline task: the user shares a big scanned sale-deed PDF (e.g. a
148-page "Adobe Scan" 7.53-acre deed) and wants its parties + survey schedule
pasted into a NEW deed's recital. Source data must come from the deed itself:

- **Detect no text layer**: `pdftotext deed.pdf - | wc -c` returns near-zero for a
  scanned image deed (148 bytes across 148 pages). Creator = "Adobe Scan" confirms.
- **OCR page 1–5 first** for the header + parties (first vendor + vendee/purchaser).
  The deed lists 100+ co-vendors — you only need the FIRST name + "and others" for
  the recital. The purchaser appears as "VENDEE" or by firm name.
- **Locate the Schedule of Properties** (the survey numbers/extents being conveyed)
  by keyword-grep over per-page OCR, NOT by reading all pages:
  ```bash
  for i in $(seq 1 148); do
    pdftoppm -png -r 150 -f $i -l $i deed.pdf /tmp/pg
    tesseract /tmp/pg-$(printf '%03d' $i).png /tmp/txt$i
  done
  grep -lciE "schedule|extent|acres|survey" /tmp/txt*.txt
  ```
  The schedule appeared on pages ~58–60 ("SCHEDULE OF PROPERTIES"), with a duplicate
  copy inside a GPA-authorisation recital on page 51 — cross-check both. Items read
  `Survey No.158/1A1A, Dry Ext Hec.0.14.50 (or) Ac.0.36 cents` (record BOTH hectares
  and acres); the schedule ends with the total (`...making a total extent of Ac.7.53
  cents`). Users read the acres column.
- Drive-link input: raw `export=download` curl returns a Google sign-in page when the
  file isn't public; use `build_service('drive','v3')` + `files().get()`/`get_media()`
  instead.

## Yellow-highlight "mark changes" redline edits (DRAAS legal doc convention)

DRAAS legal-doc users (Bharat/Nishant) frequently ask to ADD recitals/parties/
clauses to an existing deed and **highlight the changes in yellow** so they can
spot the edit at a glance. The convention: newly added text is highlighted
yellow, the original text stays uncoloured.

With python-docx, set per-run highlighting:
```python
from docx.enum.text import WD_COLOR_INDEX
r = p.add_run("new text here")
r.font.highlight_color = WD_COLOR_INDEX.YELLOW   # or None for no highlight
```

Workflow to rewrite one recital paragraph while highlighting only the additions:
1. Build `runs_new = [(text, highlight_bool), ...]` — the pre-existing stub
   (e.g. `"(i)  "`) unhighlighted, everything you ADD highlighted.
2. Copy the original run's `<w:rPr>` (deepcopy) so formatting/font carries over,
   remove all pre-existing runs, re-add in order applying highlight per run.
3. Preserve the file ID/link via `files().update()` (same ID).

**Verify the highlighting actually rendered** (python-docx highlight is only the
XML `w:highlight`; Google's .docx→Doc conversion may or may not keep it):
upload to a temp Google Doc → export PDF → render the page → `vision_analyze`
asking *"is there yellow text background in this recital listing survey numbers?"*.
Plain OCR (`method:"ocr"`) will NOT tell you about colour — you must force the
visual path. In this session the vision model confirmed the yellow highlight was
present behind the survey-number recital.

## PITFALL — tuple-unpacking order when rebuilding paragraph runs

When you store runs as `(label, text)` tuples and iterate `for txt, hl in runs:`,
you get `txt=<label>"plain"` and `hl=<actual text>` — reversed. The result: the
paragraph text silently becomes `"plainhlhlhl..."`, ALL runs get wrongly
highlighted, and the real text is lost. Symptom after save: reading back shows
`plainhlhlhl...` instead of the intended sentence.

Fix: keep a consistent `(text, highlight_bool)` order, OR unpack explicitly
(`for label, text in runs:` and map `highlight = label=="hl"`). If you saved the
corrupted file, **re-download the original from Drive** (`files().get_media`) and
redo — do not try to repair in place (the corrupted doc no longer has the source
text). Always read the paragraph back after editing to confirm it holds the real
sentence, not label tokens.

## Inserting new paragraphs between existing content

When you need to INJECT entire new paragraphs between existing ones (e.g. adding a multi-paragraph title history after a recital, between items (i) and (ii)), python-docx's `add_paragraph_after()` is fragile. Use lxml `OxmlElement` to create new `<w:p>` elements and insert them into the parent body at the right position.

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_COLOR_INDEX
import copy

doc = Document(path)
anchor_p = doc.paragraphs[21]        # paragraph to insert AFTER
parent = anchor_p._p.getparent()     # <w:body>
anchor_index = list(parent).index(anchor_p._p)

# Get formatting from a neighbour paragraph
p_sample = doc.paragraphs[20]
rPr_sample = None
for r in p_sample.runs:
    rPr = r._r.find(qn('w:rPr'))
    if rPr is not None: rPr_sample = copy.deepcopy(rPr); break
pPr_sample = p_sample._p.find(qn('w:pPr'))
if pPr_sample is not None: pPr_sample = copy.deepcopy(pPr_sample)

# Build and insert each new paragraph
chunks = ["First paragraph text", "Second paragraph..."]
prev_elem = anchor_p._p
for chunk in chunks:
    new_p = OxmlElement('w:p')
    if pPr_sample is not None:
        new_p.append(copy.deepcopy(pPr_sample))
    r_elem = OxmlElement('w:r')
    if rPr_sample is not None:
        r_elem.append(copy.deepcopy(rPr_sample))
    t_elem = OxmlElement('w:t')
    t_elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    t_elem.text = chunk
    r_elem.append(t_elem)
    new_p.append(r_elem)
    parent.insert(list(parent).index(prev_elem) + 1, new_p)
    prev_elem = new_p

# Apply yellow highlighting post-insertion
for i in range(anchor_index + 1, anchor_index + 1 + len(chunks)):
    p = doc.paragraphs[i]
    for r in p.runs:
        r.font.highlight_color = WD_COLOR_INDEX.YELLOW

doc.save(path)
```

**DRAAS use case — per-survey title history after a recital:** After expanding "(i) Sale Deed dated 16.10.2023...", the user may ask to "attach the title history for each survey number" — the full chain from the source deed's "And whereas" recitals, summarised per survey. This inserts 20+ paragraphs between (i) and (ii). Build your chunk list from the extracted chain, insert all after the recital, highlight in yellow.

**Pitfall — paragraph indices shift after insertion:** After inserting new `<w:p>` elements, `doc.paragraphs[i]` indices shift. The new paragraphs start at `anchor_index + 1` and span `len(chunks)`. Read back and verify — the pre-insertion index for any paragraph after the insertion point is no longer valid.

**Pitfall — inserting before a specific paragraph:** To insert before a target paragraph (e.g. before the next recital), use `list(parent).index(target._p)` as the insertion point. The `prev_elem` pattern inserts AFTER `prev_elem` each iteration.

## Pitfalls

- Google's .docx→Doc conversion can normalize spacing — the PDF render is a visual
  guide, not proof. Verify the `<w:spacing>` elements in the XML too.
- OCR reads "17th" as "17h" — never trust OCR for the date; verify via the doc text.
- Empty paragraphs (P6/P14/P17 in this letter) are intentional section breaks —
  they carry the "rest can have spacing" the user wants. Only tighten within blocks.
- The user's phrasing "two section, spacing between lines not correct, those lines
  should be spaced close, rest can have spacing" = body/address blocks single-spaced,
  section breaks keep their gaps. That is the DRAAS letter-formatting convention.
