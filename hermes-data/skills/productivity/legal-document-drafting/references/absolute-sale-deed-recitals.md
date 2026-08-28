# Absolute Sale Deed — Recital Assembly from User-Shared Deeds

Recurring DRAAS workflow (Ranka Oasis & similar plotted-development absolute sale
deeds). The user (Bharat, on NDR's behalf) shares Google Drive links to the chain
of title documents one at a time; you OCR/extract each and append it as a numbered
recital in the master absolute-sale-deed `.docx`.

## Reference: the master deed
- File: `20260820_RankaOasis_Plot119_AbsoluteSaleDeed_DocByBharat.docx`
- Drive file ID: `10Y-7L2wCDLtBSQD2nOFoo8NOxf_9uaa2` (owned by ndr@draas.com, shared
  to sales1.blr@draas.com). Re-upload IN PLACE via Drive `files.update`.
- It is a native `.docx` (not a Google Doc after upload), so edits made locally and
  re-uploaded render correctly in Docs.

## Workflow (repeat for each shared deed)
1. **Download** via `tools.gws_auth.build_service('drive','v3', service_name='google-draas')`
   + `files().get_media()`. Do NOT rely on `curl` of the `uc?export=download` URL —
   it fails on large/scanned files and tunnel-errors. Use the Drive API every time.
2. **Extract**: try `pdftotext` first; if < ~50 chars it's scanned → `pdftoppm -r 300`
   to PNG + `tesseract` OCR (page-by-page). Read party names, Doc No., SRO, date,
   survey numbers, extents, consideration.
3. **Add** as a numbered roman recital with yellow highlight (see XML below).
   Re-find the current recital element by text, then `element.addnext(new_para)` / `addprevious`.
4. **Renumber** every subsequent recital up by one when you insert into the middle
   (e.g. insert as (v) → old (v)→(vi), (vi)→(vii)...). Match by paragraph text, edit
   the `(x)` token in-place on the first run only.
5. **Upload** in place via Drive `files.update` with MediaFileUpload.
6. **Verify** by re-reading paragraphs (recital markers + highlight flags) after save.

## Detail level — IMPORTANT user preference (Bharat)
Not all recital types get a full title flow. Only the conveyance instruments get it:
- **Sale Deed / Exchange Deed** → full title history/chain (who→who, partition→sale, docs).
- **JDA / GPA / SPA / Mortgage / Other's Deed** → BRIEF entry ONLY: parties, survey
  numbers, extent, doc no. NO title-flow paragraphs. User was explicit:
  *"I don't want any recitals and all, just add the JDA details — between whom and
  whom, what survey number, what extent — that's it."*
- A **twin pair** (JDA + its linked GPA) gets two sequential recitals with the SAME
  survey numbers/extents, second referencing "the same property covered under Recital (n)".

## Standard recital shape (Sale/Exchange deed example)
"(x)  Sale Deed executed on the [n] day of [Month] [Year] between [VENDORS, all named]
(the Vendors) and [VENDEES] (the Vendee/Vendee), represented by its Director,
registered as Document No.[X], of Book 1, in the Office of the Sub-Registrar, [SRO],
in respect of the undermentioned properties of Sevaganapalli Village, Hosur Taluk,
Krishnagiri District, Tamil Nadu."
Then a title-flow: "The title flow of the VENDOR ... is summarized as under:" followed
by per-survey paragraphs and a closing consideration line.

## Yellow highlight XML (must be w:highlight, NOT w:shd)
Google Docs does NOT render paragraph shading (`<w:shd>`) as a visible highlighter.
Use run-level highlight:
```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
def yell(run):
    rPr = run._r.get_or_add_rPr()
    h = OxmlElement('w:highlight'); h.set(qn('w:val'), 'yellow'); rPr.append(h)
```
When building a paragraph from scratch, add the highlight to the run's rPr.

## Recital-structure gotcha
The deed's PART II operative clauses introspections (Title & Ownership, No
Encumbrances, etc.) ALSO use roman numerals `(i)..(x)`. When renumbering recitals,
match ONLY the BACKGROUND recitals (the ones listing deeds with doc numbers +
"Sub-Registrar ..."), never touch the operative-clause or Schedule B enumerated
lists. Match on distinctive text like "(v)  Special Power of Attorney" not just "(v)".