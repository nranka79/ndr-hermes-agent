# Drive Document Pack Compile (project document dossier)

Reusable recipe: user says "look at the <doc type> for <project> and give me a copy — all <type>-related documents, I need to send them to someone." Deliverable: one compiled PDF pack (title page + index + merged docs) + links to the originals. Worked example 2-Sep-2026: Ranka Iris Occupancy Certificate pack → `20260902_DRA_RankaIris_OccupancyCertificate_DocumentPack.pdf` (17 docs, 45 pages).

## Recipe

1. **Live re-sweep first — never trust a session inventory blindly.** The June 2026 inventory (`session_search`) had the OC IDs, but files had since been renamed to the YYYYMMDD convention and new files appeared. Queries that worked:
   - `name contains 'Occupancy' and trashed=false`
   - `name contains 'OC' and trashed=false`
   - Walk the project root folder + the colleague's project subfolder (Bharat's "Documents Related to Occupancy Certificates" `1tSsS1OOtd5ep9-dbdLL0vSVidULj8DkQ` held a file NOT in the old inventory: the OC Fee DD Kotak ₹62,92,000).
2. **Verify support files by ID** (`files().get`) — stability cert + as-built DWG still live, names standardized (20260503_...FormIX..., 20260414_...AsBuiltDrawing_OCSubmission.dwg).
3. **Download**: `files().get_media` for PDFs; `files().export_media(fileId, mimeType='application/pdf')` for Google Docs. **Pitfall: raw-uploaded .docx / binary files are NOT Docs Editors files — export_media fails 403 "Export only supports Docs Editors files."** Look for a PDF twin of the same letter (the DD submission cover letter existed as both PDF and docx).
4. **Compile with pymupdf**: title page → index page created BEFORE appending docs (so page numbers are accurate) → `insert_pdf(src)` each doc recording start page → fill index text AFTER all pages exist (see stale-page pitfall).

## Pymupdf pitfalls (hit 2-Sep-2026)

- **Not installed in the Hermes venv by default**: `uv pip install --python /opt/hermes/.venv/bin/python3 pymupdf` (import as `pymupdf`; legacy `fitz` import shows a deprecation warning but works).
- **`insert_text` with `fontname="helv-b"` raises "need font file or buffer"** — only built-in names work: `helv`, `hebo` (Helvetica-Bold), `heit`, `cour`, `tiro`.
- **Page objects go STALE across `insert_pdf()`**: a Page object held while later `insert_pdf` calls rebuild the document ends up with `doc=None`, and `insert_text` dies with `AttributeError: 'NoneType' object has no attribute 'is_pdf'`. Fix: create all pages first, then fetch fresh page objects via `final[pno]` to write text.
- **Index page numbering**: insert the index page(s) BEFORE appending the docs; displayed page for doc i = `start_0based + num_index_pages + 1`.
- **Scanned certificates have no text layer** — verify a doc arrived with `len(page.get_text().strip()) == 0` and `page.get_images(full=True)` non-empty. Normal for BBMP OC scans; don't re-OCR just for verification.

## Output pattern

- Local: `/opt/data/YYYYMMDD_Entity_Description.pdf` (matches NDR naming convention — underscores only).
- Deliver: `MEDIA:</path>` for the pack + the key Drive `webViewLink`s + the full-set folder link, so he can send either the pack or individual files.
- Note any non-PDF artifacts separately (e.g. as-built `.dwg` 7 MB — cannot merge; give its link and offer to share).