# PDF Dossier Compilation with PyMuPDF (pymupdf) — Verified Pitfalls

Used 2026-09-02 for the Ranka Iris Occupancy Certificate pack (compile 17 Drive PDFs +
Google-Doc exports into one 45-page dossier with title page + index). These pitfalls
cost real debugging time; bake them in.

## Import

```python
import pymupdf   # NOT `import fitz` — fitz is deprecated (warns) and may disappear
# `fitz.open(...)` still works on pymupdf 1.28 but raises a deprecation warning
```

Install if missing: `uv pip install --python /opt/hermes/.venv/bin/python3 pymupdf`

## Built-in fonts

`page.insert_text((x, y), text, fontname="helv-b")` **FAILS** with
`Exception: need font file or buffer`. PyMuPDF builtin names are 4-letter:
- `helv` (regular), `hebo` (Helvetica-Bold), `heit` (italic), `cour`, `tiro`.
Use `fontname="hebo"` for bold headers. Never "helv-b" / "times-roman" style names.

## Stale page objects after insert_pdf — the #1 trap

**Page objects obtained BEFORE `final.insert_pdf(...)` become invalid** (their internal
doc pointer turns None) once the doc is re-parented, so `page.insert_text` on them raises
`AttributeError: 'NoneType' object has no attribute 'is_pdf'`.

Pattern that works:
1. Create title page + append all source PDFs FIRST (`final.insert_pdf(src)`, record
   `start = final.page_count` before each insert).
2. Create/fetch index pages AFTER all inserts (`final.new_page(pno=1)` for the index slot,
   or fetch `final[pno]` fresh).
3. Fill ALL text (title header, index lines) LAST by fetching page objects fresh:
   `page = final[pno]` — never hold a page reference across an insert_pdf.

## Index page numbering

Compute displayed page numbers AFTER knowing how many pages precede the docs:
- If the index page is inserted at pno=1 (after title), every doc shifts by +1.
- Displayed first page = `start + offset + 1` (offset = number of inserted index pages),
  last = `start + pages + offset`. Write the index text AFTER all pages exist so the
  numbers are final.

## Downloading the source set

- Drive PDF download: `service.files().get_media(fileId=...)` + `MediaIoBaseDownload`.
- Google Docs → PDF: `files().export_media(fileId=..., mimeType='application/pdf')`.
- **`.docx` files in Drive are NOT Docs-Editor files for export** — export_media 403s with
  "Export only supports Docs Editors files." If a .docx is a duplicate of a PDF in the set
  (cover-letter docx vs PDF version), just include the PDF and note the docx is the
  editable twin — do not block on it.
- Verify each download: open with pymupdf, print `page_count` + size.

## Subset extraction ("only pages N–M of the generated pack")

```python
out = pymupdf.open()
out.insert_pdf(src, from_page=2, to_page=5)   # 0-based: pages 3–6 inclusive
out.save('/path/standalone.pdf', deflate=True, garbage=3)
```

User-friendly: when the user says "give me only the first document (pages 3-6 of the
pack)", extract exactly those pages into a standalone file named
`YYYYMMDD_Entity_Document.pdf` and also give the original Drive link. Verify page count
after extraction (4 pages for a 4-page OC).

## Verification

- `pymupdf.open(final_path)` → assert page_count, then read `chk[1].get_text()` for the
  index preview and check the first doc page renders (`len(page.get_images(full=True))` —
  scanned BBMP certificates have zero text layer + 1 image; that is expected, not a bug).

## Out-of-scope note

Compiling SCANNED multi-page OC/cert PDFs is fine; page 1 of the merged doc often shows
`text len 0` + `images: 1` — normal for scan-only artifacts. Deliver as one PDF + Drive
links for the individual originals.