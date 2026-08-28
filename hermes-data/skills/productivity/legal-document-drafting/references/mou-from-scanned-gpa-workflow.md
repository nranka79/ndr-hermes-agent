# MOU Drafting from Scanned GPA / Ownership Document

**Trigger:** User shares a scanned PDF (GPA, sale deed, legal opinion, ownership packet) and asks for an MOU draft "with recitals from this document" and "schedule of each property". Validated Aug 2026 on Sanchaya→Nahar irrevocable GPA (Besthamanahalli, 27 items, 8A-37G).

## User preference (learned — embed in every draft)
When Prakash/Nishant ask to "complete the terms and conditions, land acquisition history and schedule of each property", they want the FULL document, not a skeleton:
- Complete clause set (Definitions, Purpose, Title/DD, Consideration, Development/Monetisation/Sharing, Timeline/Exit/Default, Reps & Warranties, General Covenants).
- A dedicated LAND ACQUISITION HISTORY section (stage-wise chain of title).
- Item-wise schedule: **Item No. 1 … Item No. 27**, each with survey no, extent, conversion OM, acquisition deed (date, doc no, CD no, Sub-Registrar), predecessor-in-title, AND boundary descriptions (E/W/N/S).
- Commercial terms that are genuinely unknown stay as `[bracketed — to be confirmed]`; everything derivable from the source doc gets populated.

## Pipeline (validated steps)

### 1. Get the file
- Telegram rejects >20MB. User shares Drive link → fetch via Drive API `files().get_media()` + `MediaIoBaseDownload` (NOT web_extract — binary).
- Verify metadata first: `files().get(fields="name,mimeType,size,owners")`.

### 2. Detect scanned PDF
`pdftotext -layout in.pdf out.txt` → near-empty output (few bytes, N empty lines) = scanned, no text layer.

### 3. Parallel OCR (critical speedup)
Sequential tesseract ≈ 25s/page → 46 pages ≈ 19 min. Parallel is ~6× faster; kill the sequential run and restart:
```bash
pdftoppm -r 200 -png input.pdf ocr_pages/page
ls ocr_pages/page-*.png | xargs -P 8 -I {} sh -c 'b=$(basename "$1" .png); tesseract "$1" "ocr_out/$b" --psm 6 -l eng 2>/dev/null' _ {}
# combine in page order (sort -V so page-10 sorts after page-9):
for f in $(ls ocr_pages/page-*.png | sort -V | sed 's/\.png$//'); do
  echo "===== PAGE $(basename $f | sed 's/page-//') =====" >> combined.txt
  cat "ocr_out/$(basename $f).txt" >> combined.txt
done
```
- `--psm 6` for uniform text blocks; 200 DPI enough for printed legal text.
- English-only tesseract default; Kannada RTCs OCR unreliably — do NOT fabricate garbled names, keep source text or flag.

### 4. Map GPA content → MOU sections
- GPA **WHEREAS** → MOU recitals: ownership → registered agreements of sale (dates + doc nos) → advances received → defaults/refund arrangements (amounts + interest) → new purchaser consideration + payment details (UTR/cheque nos) → board resolution → irrevocable GPA (regd doc no) → no-objection witnesses.
- GPA **SCHEDULE PROPERTY** item blocks → MOU Schedule: keep per-item paragraph format (mirrors source), plus a summary TABLE (Item | Survey No | Extent | Conversion OM | Acquisition deed | Predecessor) with a bold TOTAL row.
- Total extent: sum guntas, 1 acre = 40 guntas.

### 5. Deliverable — build .docx then import to Drive as Google Doc
Docs API `insertText` loses tables/formatting. The reliable path for a formatted legal doc is docx→Drive import:
- PEP 668 box (no pip module): `uv venv /tmp/docxvenv && uv pip install --python /tmp/docxvenv/bin/python python-docx`
- python-docx: Normal style 11pt, justified body, 1.15 spacing, bold ALL-CAPS headers, "Item No. N:" lead run bold + rest normal, `Table Grid` style for the summary table (bold header row + bold TOTAL row).
- Upload with conversion:
```python
media = MediaFileUpload(docx_path, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document", resumable=True)
f = drive.files().create(body={"name": title, "mimeType": "application/vnd.google-apps.document", "description": "..."}, media_body=media, fields="id,webViewLink").execute()
drive.permissions().create(fileId=f["id"], body={"type": "user", "role": "writer", "emailAddress": "<requester email>"}).execute()
```
- Keep the old placeholder doc (don't delete without confirmation); give the new link and offer cleanup.
- Deliver Google Docs/Slides links inside a code block (Telegram breaks bare URLs).

## GWS account caveat (this deployment)
`gws_resolve_account` shows only `google-draas` (ndr@draas.com) has a vault token; the requester's own account (e.g. psingh@draas.com) often does NOT. Docs created via `build_service("docs","v1",service_name="google-draas")` are owned by ndr@draas.com — share them to the requester as writer via Drive permissions so they can edit. Verify account status with `gws_resolve_account` before assuming ownership.

## Related
- `references/mou-standard-drafting-format.md` — 6-part structure, clause-by-clause checklist.
- `references/mou-party-restructure-title-flow-recitals.md` — title-flow→recitals for legal opinions, Docs API edit pitfalls, vault socket env vars.
