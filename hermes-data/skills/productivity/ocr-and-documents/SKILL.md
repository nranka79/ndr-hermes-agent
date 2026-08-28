---
name: ocr-and-documents
description: "Extract text from PDFs/scans (pymupdf, marker-pdf)."
version: 2.3.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [powerpoint, personal-document-organization, medical-document-processing, professional-documents]
---

# PDF & Document Extraction

For DOCX: use `python-docx` (parses actual document structure, far better than OCR). If python-docx is not available, use zipfile + XML ElementTree to extract text and table data directly — .docx is a ZIP of XML files. See the DOCX Table Extraction section below.

### Legacy .doc (OLE2 binary) — detect & extract without LibreOffice

Many statutory forms and older templates (MCA MGT-11 proxy forms, old agreements) are shipped as **legacy Word 97-2003 `.doc`** (OLE2 compound binary), NOT `.docx`. python-docx and zipfile CANNOT read them, and LibreOffice/antiword/catdoc are often not installed on the VPS.

**Detection first — magic bytes, not extension:**
```python
with open('file.doc', 'rb') as f:
    head = f.read(8)
# b'PK\x03\x04' → actually a .docx (zip) — read with python-docx
# b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' → legacy OLE2 .doc
```

**Fast extraction — `strings`:** the text layer of a legacy .doc is embedded as readable UTF-16/ANSI runs. `strings -n 6 file.doc` reliably dumps all visible text including labels, field names, and values (verified Aug 2026 on an MGT-11 proxy form). Good enough to read the form's fields and legal text; not enough for precise layout.

```bash
strings -n 6 "1_Form MGT-11.doc" | head -80
```

**If a fillable PDF must be produced from the .doc template:** rebuild it with reportlab (see `professional-documents` / `legal-document-drafting` references for the MGT-11 pattern) — mirror the statutory text exactly, leave blanks for signatures. Never claim the rebuilt PDF is the official form; deliver it as a filled replica for signature, then attach to a Gmail draft via the raw API.

### DOCX Table Extraction via zipfile+XML

When `python-docx` is not installed but you need to extract structured table data from .docx files (legal requisition lists, proformas, tabular forms):

```python
import zipfile, re
from xml.etree import ElementTree

ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def get_text_from_para(para):
    texts = []
    for t in para.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
        if t.text:
            texts.append(t.text)
    return ''.join(texts).strip()

def get_table_data(filepath):
    with zipfile.ZipFile(filepath) as z:
        xml_content = z.read('word/document.xml')
        root = ElementTree.fromstring(xml_content)
    body = root.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body')
    tables = []
    for child in body:
        if child.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl':
            rows_data = []
            for row in child.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr'):
                cells = []
                for cell in row.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc'):
                    cell_text = []
                    for p in cell.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                        cell_text.append(get_text_from_para(p))
                    cells.append('\n'.join(cell_text).strip())
                rows_data.append(cells)
            tables.append(rows_data)
    return tables
```

### Column Detection by Header Text

For structured tables (requisition lists, proformas, forms), identify the right column by matching header text:

```python
def get_column_indices(header_row):
    procured_idx = doc_idx = sl_idx = comment_idx = -1
    for i, h in enumerate(header_row):
        h_lower = h.lower()
        if 'procured' in h_lower or 'procure' in h_lower or 'to be' in h_lower:
            procured_idx = i
        elif 'particulars' in h_lower or 'document' in h_lower or 'information' in h_lower:
            if doc_idx == -1:
                doc_idx = i
        elif 'sl' in h_lower or 'no' in h_lower:
            sl_idx = i
        elif 'comment' in h_lower or 'remark' in h_lower or 'note' in h_lower or 'client' in h_lower:
            comment_idx = i
    # Fallback: first long-text column after item number
    if doc_idx == -1:
        for i, h in enumerate(header_row):
            if h and len(h) > 10 and i not in (sl_idx, procured_idx):
                doc_idx = i
                break
    return doc_idx, procured_idx, comment_idx
```

Then iterate rows with `for row in table_data[1:]:` and access `row[doc_idx]`, `row[procured_idx]`. This handles varied table layouts across different legal/requisition list documents.

**Use cases:** Legal requisition lists, land acquisition document trackers, regulatory filings in DOCX format where you need to match "To be procured by" columns, extract document descriptions, and identify assignees by name (Rahul, Aamir, etc.) while excluding rows assigned to a specific party (e.g. Sangam).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support).
This skill covers **PDFs and scanned documents**.

## Step 1: Remote URL Available?

If the document has a URL, **always try `web_extract` first**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, web_extract fails, or you need batch processing.

## Step 2: Choose Local Extractor

| Feature | pymupdf (~25MB) | marker-pdf (~3-5GB) |
|---------|-----------------|---------------------|
| **Text-based PDF** | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ✅ (90+ languages) |
| **Tables** | ✅ (basic) | ✅ (high accuracy) |
| **Equations / LaTeX** | ❌ | ✅ |
| **Code blocks** | ❌ | ✅ |
| **Forms** | ❌ | ✅ |
| **Headers/footers removal** | ❌ | ✅ |
| **Reading order detection** | ❌ | ✅ |
| **Images extraction** | ✅ (embedded) | ✅ (with context) |
| **Images → text (OCR)** | ❌ | ✅ |
| **EPUB** | ✅ | ✅ |
| **Markdown output** | ✅ (via pymupdf4llm) | ✅ (native, higher quality) |
| **Install size** | ~25MB | ~3-5GB (PyTorch + models) |
| **Speed** | Instant | ~1-14s/page (CPU), ~0.2s/page (GPU) |

**Decision**: Use pymupdf unless you need OCR, equations, forms, or complex layout analysis.

### Lighter OCR Alternative: pymupdf + tesseract (when marker-pdf is unavailable)

If marker-pdf is not installed and you need OCR for a scanned PDF, use pymupdf to render pages to images + tesseract for OCR:

```python
import fitz, tempfile, os
doc = fitz.open('/tmp/scanned.pdf')
for i in range(doc.page_count):
    page = doc[i]
    # Check if text exists first
    if page.get_text().strip():
        print(f'Page {i+1}: native text available')
        print(page.get_text())
        continue
    # Render at 200 DPI and OCR
    pix = page.get_pixmap(dpi=200)
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(pix.tobytes('png'))
        img_path = f.name
    text = os.popen(f'tesseract \"{img_path}\" stdout --psm 6 -l eng 2>/dev/null').read()
    os.unlink(img_path)
    print(f'--- PAGE {i+1} (OCR) ---')
    print(text[:2000])
```

**Tesseract settings for printed documents:**
- `--psm 6` — uniform block of text (good for single-column legal docs)
- `--psm 4` — single column of text (alternative)
- `-l eng` — English
- 200 DPI is sufficient for printed text at readable font sizes
- No ~5GB PyTorch install needed — tesseract is tiny (~30MB)

**Kannada OCR (RTCs, Kannada deeds, government letters) when system tessdata is read-only:**

`apt`/`cp` into `/usr/share/tesseract-ocr/*/tessdata` often fails with *Permission denied* on the VPS. Workaround — run tesseract with a **local TESSDATA_PREFIX** (no root needed):

```bash
mkdir -p /tmp/tessdata
cp /usr/share/tesseract-ocr/5/tessdata/eng.traineddata /tmp/tessdata/   # already installed
curl -sL https://github.com/tesseract-ocr/tessdata_fast/raw/main/kan.traineddata -o /tmp/tessdata/kan.traineddata
# then prefix every tesseract call:
TESSDATA_PREFIX=/tmp/tessdata tesseract page.png out --psm 6 -l kan+eng
```

- `-l kan+eng` on a Kannada/English mixed document (Karnataka RTC Form 16, Kannada sale deeds/GPAs) returns both scripts; `-l kan` alone garbles embedded English numbers/labels.
- Kannada land-record extents OCR as `02-00 (ಎರಡು ಎಕರೆ)` = 2 Acres 00 Guntas; survey as `ಸರ್ವೆ ನಂಬರ್ ಹಳೇದು 18, ಹೊಸದು 223` = old Sy 18, new Sy 223.
- RTC extent field (A.G.G.G = acres.guntas.anekalu) lives in the header row `3. ಖೇತವಾರು ... ಒಟ್ಟು ವಿಸ್ತೀರ್ಣ` near the top of page 1. A full-page OCR often misses it — crop the top ~10–30% of the page, left ~50%, upscale 2–3×, then OCR that crop.
- **Ambiguous digit verification:** when a deed extent and an RTC extent disagree by a digit (e.g. deed 0-25G vs RTC `0.27.00.00`), re-OCR the extent box at 300 DPI with a tight crop before trusting either — Kannada numeral 5 vs 7 misreads are common. Flag the variance to the user rather than silently picking a source.

**When to use this:** Scanned legal documents, government-issue PDFs, old registrations, property deeds. Any PDF where `page.get_text()` returns empty string.

**Pitfall — `--force-ocr` and `--skip-text` are mutually exclusive:** `ocrmypdf --force-ocr --skip-text in.pdf out.pdf` fails immediately with `Choose only one of --force-ocr, --skip-text, --redo-ocr.` (verified Aug 2026 on a scanned partition deed). For a fully scanned PDF (no text layer anywhere) use `--skip-text` alone — it OCRs every page; `--force-ocr` alone is the right choice if you must re-OCR even pages that have a text layer. `--deskew` and `--jobs 4` can be added freely. If the job fails this way, the error is at CLI-arg level, NOT a document problem — do not re-download or suspect the file.

### Parallel OCR for multi-page scans (fast, validated Aug 2026): Sequential per-page tesseract on a 40+ page scan takes ~20+ minutes. Render once, OCR with `xargs -P 8`, then combine in page order. 8 workers is safe on a ~3.7GB RAM VPS; tesseract is single-threaded so this is a near-linear speedup:

```bash
pdftoppm -r 200 -png input.pdf ocr_pages/page
mkdir -p ocr_out
ls ocr_pages/page-*.png | xargs -P 8 -I {} sh -c 'b=$(basename "$1" .png); tesseract "$1" "ocr_out/$b" --psm 6 -l eng 2>/dev/null' _ {}
# Combine in page order — sort -V handles page-10 before page-2
> out.txt
for f in $(ls ocr_pages/page-*.png | sort -V | sed 's/\.png$//'); do
  b=$(basename "$f"); echo "===== PAGE ${b#page-} =====" >> out.txt
  cat "ocr_out/$b.txt" >> out.txt; echo "" >> out.txt
done
```

- Monitor progress while it runs: `ls ocr_out/*.txt | wc -l` (target = page count).
- **If a background OCR job exits non-zero (SIGTERM 143, OOM-killed workers), check the outputs BEFORE re-running** (verified Aug 2026): a batch whose script starts with `rm -f out/*.txt` may have been killed only AFTER every page was written — `ls out/*.txt | wc -l` = page count and all files non-empty means the data is intact and the exit code was just the kill signal. Re-running blindly wastes 20+ minutes and risks the same thrash. The worker guard `[ -s "$out" ] && exit 0` also makes any re-run idempotent — it skips pages already OCR'd, so re-running after a partial kill only processes the missing pages.
- If it stalls, check `ps aux | grep tesseract | wc -l` — some pages take much longer than others (dense registration sheets, Kannada pages).
- Detection shortcut for image-only PDFs: `pdftotext -layout file.pdf out.txt` producing near-zero bytes (≈1 empty line per page) means there is no text layer → skip pymupdf, go straight to render+OCR.
- Eng-only tessdata is common (`tesseract --list-langs`); Kannada RTC pages OCR unreliably for names — do NOT fabricate owner names, flag them instead.

**PITFALL — `xargs $(basename {})` expands in the OUTER shell, not per-file:** `xargs -I {} sh -c '... tesseract "$1" "out/$(basename {} .png)" ...' _ {}` looks right but `$(basename {} .png)` is evaluated ONCE by the outer shell before xargs runs, producing the literal filename `out/{}.txt`. Every worker then races writing the same file → you see N pages "done" but zero useful text, or one mangled file. Fix: put the basename computation INSIDE a worker script that takes the input path as `$1` and derives its own output name:
```bash
#!/bin/bash  # ocr_worker.sh
in="$1"; base=$(basename "$in" .png); outdir="${in%_pages}_ocr"
mkdir -p "$outdir"
[ -s "$outdir/$base.txt" ] && exit 0
TESSDATA_PREFIX=/tmp/tessdata tesseract "$in" "$outdir/$base" --psm 6 -l kan+eng 2>/dev/null
# then: find pages_dir -name 'pg-*.png' | sort | xargs -P 8 -I {} bash ocr_worker.sh {}
```

**PITFALL — concurrent OCR batches thrash the VPS; pages stick at 0 bytes (verified Aug 2026):** 8 parallel tesseract workers is fine for ONE job on a ~3.7GB RAM VPS, but running TWO xargs -P 8 OCR jobs at once (16 tesseract processes) spikes load to 30+, and pages sit at 0 bytes for 10+ minutes — looks like a document problem, actually resource contention. Rules: (1) run OCR batches one at a time — don't background a second batch while the first is running; (2) add a per-page guard `timeout 180 tesseract ...` so one pathological page can't hang the batch; (3) if pages are stuck at 0 bytes, kill ALL tesseract and rerun sequentially (`ps aux | grep tesseract | grep -v grep | awk '{print $2}' | xargs -r kill -9`), or re-run the single batch alone — a page that OCRs fine solo will complete when the machine isn't thrashing.

### Kannada OCR (registered deeds, RTCs) — local tessdata install

When `tesseract --list-langs` shows only `eng`/`osd` but the documents are Kannada (registered deeds, Bhoomi RTCs), download the Kannada traineddata to a **local** dir and point `TESSDATA_PREFIX` at it — the system tessdata dir is usually not writable by the agent (`cp ... /usr/share/tesseract-ocr/5/tessdata/` → Permission denied):

```bash
mkdir -p /tmp/tessdata
cp /usr/share/tesseract-ocr/5/tessdata/eng.traineddata /tmp/tessdata/
curl -sL https://github.com/tesseract-ocr/tessdata_fast/raw/main/kan.traineddata -o /tmp/kan.traineddata
cp /tmp/kan.traineddata /tmp/tessdata/
TESSDATA_PREFIX=/tmp/tessdata tesseract img.png stdout --psm 6 -l kan+eng
```

Notes (verified Aug 2026 on Byadarahalli registered deeds + RTCs):
- `-l kan+eng` beats `-l eng` on Kannada docs — English numbers/labels inside Kannada text survive (extents like `02-00`, doc numbers, dates come through).
- Kannada OCR is reliable enough for **structured numeric fields** (extent `02-00`, survey numbers, MR numbers, dates) even when names are garbled. Extract the numbers; flag unreadable names.
- For RTC extent boxes, crop the top field-band first (roughly top 10–30% height, left 50–60% of page) and upscale 2–3× before OCR — whole-page OCR returns only the table header, missing field 3 (ಖೇತವಾರು ಒಟ್ಟು ವಿಸ್ತೀರ್ಣ). See `real-estate-legal-compliance` → `references/rtc-form16-reading.md`.

**PITFALL — `vision_analyze` rejects PDFs outright (`Only real image files are supported for vision analysis`).** Do NOT pass a PDF file path to `vision_analyze` — it only accepts image files (.png, .jpg, .webp, .gif). Convert first: `pdftoppm -png -r 150 input.pdf /tmp/page` → then `vision_analyze(image_url='/tmp/page-1.png')` (watch the zero-padded page glob pitfall below). If poppler-utils is not installed, fall back to tesseract (see Kannada OCR section) or ask the user.

**PITFALL — pdftoppm zero-pads page numbers, globs with literal `-N` silently return nothing:** When you render single pages with `pdftoppm -f 1 -l 1 -png input.pdf prefix`, the output is `prefix-01.png` (zero-padded), NOT `prefix-1.png`. A glob like `prefix-1.png` finds nothing, tesseract never runs, and every document silently comes back as `len=0` — looks like a download failure, actually a filename mismatch. Always glob with a wildcard: `glob.glob(prefix + '-*.png')`. Same class of bug: page numbers ≥10 render as `-10.png` (no padding change) but 1–9 are padded, so only single-digit pages fail with the literal-glob approach.

**PITFALL — stylized marketing brochures (CorelDRAW/design-tool PDFs) OCR empty at plain render+psm:** Branded property brochures (villa/resort/real-estate PDFs produced in CorelDRAW etc.) have NO text layer (`pdftotext -layout` → ~0 bytes) AND their decorative, low-contrast typography makes plain `tesseract page.png --psm 3` return empty even at 200 DPI — verified 2026-08-16 on a Coonoor villa brochure (16 pages, `pdfinfo` Producer shows CorelDRAW). Fix: render at 100 DPI, then **preprocess with PIL before OCR** — grayscale → autocontrast → mild contrast boost:
```python
from PIL import Image, ImageOps, ImageEnhance
img = Image.open(f'pg-{p:02d}.png')
g = ImageOps.grayscale(img)
g = ImageEnhance.Contrast(g).enhance(1.4)
g.save(f'pre-{p:02d}.png')
# tesseract pre-XX.png stdout --psm 3
```
Plain render+psm 3/11 returned empty on pages 1–4; the preprocessed pass read the project name, unit counts, amenities, and the embedded YouTube link reference. Also pull `page.get_links()` with pymupdf for any embedded URLs (brochure YouTube/video links) — OCR won't reliably catch those. When the brochure is the ONLY source for deal facts (unit count, area), cross-check against the companion P&L Excel — the brochure and model often disagree (12 villas in brochure vs 11 in the P&L) and that discrepancy is worth flagging, not silently picking one.

### Poor-contrast scanned financial statements (ITR / audited BS PDFs) — the recipe that works

Low-contrast scanned audit packs (ITR statements, P&L + Balance Sheet + Auditor Report compilations) look OCR-dead at plain `pdftoppm -r 200` + `tesseract --psm 6`: earlier pass on DRA Realty's scans returned 2 readable pages out of 73 and was abandoned as "unreliable". The fix is **stronger preprocessing + a keyword location pass**, verified 2026-08-25 on three 23–27 pp DRA Realty audit PDFs (all balance sheets + notes pages extracted, totals reconciled):

1. **Render grayscale at 250 DPI**: `pdftoppm -r 250 -gray file.pdf pages/prefix` (`.pgm` files).
2. **Preprocess every page with PIL before tesseract** (stronger than the brochure recipe):
   ```python
   from PIL import Image, ImageOps, ImageEnhance
   img = Image.open(p)          # .pgm
   img = ImageOps.autocontrast(img, cutoff=1)
   img = ImageEnhance.Contrast(img).enhance(1.6)
   img = ImageEnhance.Sharpness(img).enhance(1.5)
   img.save(enh_path)           # .png
   ```
3. **OCR everything once** (`tesseract enh.png ocr/base --psm 6`), then **locate the target pages by keyword** instead of guessing which page is the balance sheet:
   ```python
   kw = ['BALANCE SHEET', 'EQUITY AND LIABILITIES', 'ASSETS', 'Reserves', 'Non-current']
   # scan ocr/*.txt; pages hitting 3+ of these = the real BS page + its notes pages
   ```
   Typical hit pattern in a 23–27 pp audit pack: 1–2 pages with **BALANCE SHEET + EQUITY AND LIABILITIES + ASSETS + Reserves** (the main BS), plus nearby pages with only `Reserves`/`Non-current` (the notes). The notes pages carry the breakdown (borrowings by lender, reserves movement, investment composition) — read them, not just the top sheet.
4. **Verify by arithmetic before trusting numbers**: sum the extracted line items against the printed TOTAL and against the other side (`Total Assets` must equal `Total Liabilities`; individual schedules must sum to their subtotal). A ₹1K rounding drift on a ₹30 Cr balance sheet is normal — a real mismatch is not. See also the "Validating OCR'd financial totals" section for quotient-style checks, and remember **"Rupees in Thousands"** header — multiply by 1000 before quoting ₹ figures.
5. Only if this enhanced pass still fails, fall back to `vision_analyze` on the enhanced PNGs (the KYC pattern: `pdftoppm -r 300` → `vision_analyze`).

Do NOT abandon a scan set as "unreadable" after only trying plain render+psm — the autocontrast/contrast/sharpness chain above is cheap and routinely rescues these.

**Batch OCR of many documents (100+ PDFs) — download + probe + OCR + parse in one background job:** For a whole folder of scanned deeds (e.g. 190 sale-deed/ATS/GPA PDFs):
1. Pull the file list from Drive/Sheets with IDs, download each to `/tmp/out/NNN.pdf`.
2. Probe `pdftotext` first — most scans return <80 chars → skip to OCR.
3. OCR only the first 2–3 pages per doc (title + parties + schedule usually live there) — `pdftoppm` per page + `tesseract --psm 6`.
4. Save each doc's text to `/tmp/out/text/NNN.txt` so parsing is a separate, restartable pass.
5. Run as `terminal(background=True, notify_on_complete=True)`; poll progress via filesystem counts (`ls text/*.txt | wc -l`), not stdout (often buffered/stale).
6. Runtime reality check: ~190 docs × 3 pages @200dpi ≈ 25–30 min on a 3.7GB VPS. Don't block the turn waiting — background + notify, then continue when it exits.
7. `int()` sheet row numbers before `f'{sl:03d}'` formatting — Sheets API returns them as strings, and `:03d` raises `ValueError: Unknown format code 'd' for object of type 'str'`.

**PITFALL — pre-printed form header stamps are NOT transaction dates:** Scanned Karnataka registration PDFs carry a printed "Document Sheet" header with a fixed date field like `09-05-2003` (OCR often reads `09-05-2030`). This template artifact appears on every page and must be EXCLUDED when extracting the real transaction date. Reliable sources instead: (a) the deed's own "made and executed on this the X day of <Month> <Year>" clause (b) the registration footer "Print Date & Time : DD-MM-YYYY" (c) the stamp-office receipt line. Filter by plausibility: real dates for this class of doc are 2010–2027, and explicitly reject `09/05/2003` / `09/05/2030`.

**Pitfall:** `tesseract` must be installed (`which tesseract`). It usually is on Linux systems; if not, `apt install tesseract-ocr`.

### PDF Analysis Workflow (User Preference)
When the user asks to "examine", "check", "read", or "analyze" a PDF:
1. First attempt OCR using the `ocr-and-documents` skill (marker-pdf for scanned documents, pymupdf for text-based).
2. If OCR fails, returns unusable/poor text, or key information cannot be extracted → fall back to **vision analysis** using OpenRouter + **Gemini 2.5 Flash** (multimodal model).

This workflow is mandatory for medical reports, invoices, and scanned documents unless the user explicitly directs otherwise.

**Tool limitation — `call_openrouter_model` is text-only:** The `call_openrouter_model` tool cannot accept image or PDF attachments even when the underlying model is multimodal. This is a Hermes tool limitation, not a model limitation. If vision analysis is required and OCR is not available, do NOT try to push the PDF through `call_openrouter_model` with different model slugs (Gemini 2.5 Flash, GPT-4o, GPT-5.5 — all fail the same way). Instead, tell the user upfront: the model is multimodal but the tool is text-only, and ask them to either install the OCR tools, convert the PDF to images first, or paste a vision-capable model URL into `vision_analyze`/`browser_use_cloud`.

If the user needs marker capabilities but the system lacks ~5GB free disk:
> "This document needs OCR/advanced extraction (marker-pdf), which requires ~5GB for PyTorch and models. Your system has [X]GB free. Options: free up space, provide a URL so I can use web_extract, or I can try pymupdf which works for text-based PDFs but not scanned documents or equations."

---

## pymupdf (lightweight)

```bash
pip install pymupdf pymupdf4llm
```

**PEP 668 hosts (no system pip, e.g. this VPS) — install into the Hermes venv via uv:**
```bash
uv pip install --python /opt/hermes/.venv/bin/python3 pymupdf
```
Verified Aug 2026: pymupdf disappeared from `/opt/hermes/.venv` mid-session (venv recreated/changed); the uv command restored it in <1s. If `import pymupdf` fails, reinstall with this command rather than assuming the skill docs are stale — also note `import fitz` is the legacy module name (deprecated warning, still works) while `import pymupdf` is current.

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Arxiv Papers

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Creating Highlighted / Annotated PDFs from Source Documents

When you need to produce a visually marked-up PDF highlighting specific sections of an original document (e.g. licence conditions, regulatory clauses, NOC requirements for a bank):

### Workflow

1. **Download the PDF** from Drive via `build_service` using the `drive.files().get_media()` method — NOT via `web_extract` (which returns text, not the binary).

2. **Inspect page structure** with `pdfinfo` (page count, dimensions, rotation) and `pdftotext -layout` to understand where relevant text lives.

3. **Check for embedded conditions in separate files**: Licences often reference "Licence Conditions" or "Sanctioned Plans" as separate documents — the conditions table may NOT be in the licence PDF itself. Use `drive.files().list()` to find the sanctioned plan / conditions document in the same Drive folder.

4. **Convert to images** for visual marking:
   ```bash
   pdftoppm -r 200 -png input.pdf /tmp/pages/page
   ```
   - A4/letter pages: 200 DPI is fine (~2200px wide)
   - **A0/A1 technical drawings** (architectural plans, sanctioned plans): render at **300 DPI minimum** or the text will be unreadable. At 150 DPI an A0 page is ~7000×5000px, at 300 DPI it's ~14000×10000px (watch for PIL DecompressionBombWarning — set threshold or work with smaller crops)

5. **For A0/A1 drawings with small text** (sanctioned plans, zoning maps):
   - The conditions table is typically in a column on one side of the drawing
   - Use `pdftotext -layout -f N -l N` to locate the text area first
   - Crop the relevant section: `sp_img.crop((x1, y1, x2, y2))` where coordinates are percentage-based from the full-size image
   - Scale up the crop: `crop.resize((int(cw*scale), int(ch*scale)), Image.LANCZOS)` with scale ~1.5–2.0× for readability
   - Verify text readability with `vision_analyze` before finalizing

6. **Add highlight overlays with PIL**:
   ```python
   from PIL import Image, ImageDraw, ImageFont

   # Convert to RGBA for overlay compositing
   img = img.convert('RGBA')
   overlay = Image.new('RGBA', img.size, (0,0,0,0))
   d = ImageDraw.Draw(overlay)

   # Semi-transparent yellow highlight
   d.rectangle([x1, y1, x2, y2], fill=(255, 255, 0, 120), outline=(255, 200, 0, 220), width=4)

   # Annotation label with black background
   d.rectangle([x, y, x+tw, y+th], fill=(0,0,0,200))
   d.text((x+5, y+3), annotation_text, font=font, fill=(255,255,255,255))

   # Composite and convert back to RGB
   result = Image.alpha_composite(img, overlay).convert('RGB')
   ```

**Pitfall — pdftoppm timeout on iOS Quartz-generated PDFs with oversized pages:** Some scanned/image PDFs (especially from iPhones/iOS) have massive page dimensions (e.g. `pdfinfo` shows `2492 x 3538 pts` ≈ 34.6×49.1 inches) despite being only a single A4/letter-sized scan. On these, `pdftoppm` and `pdf2image` can time out (>30s) even at low DPI. **Use ghostscript instead:**

```bash
# Fast, handles oversized iOS Quartz PDFs
gs -dNOPAUSE -dBATCH -sDEVICE=png16m -r72 \
  -sOutputFile=/tmp/page.png input.pdf 2>&1
```

**Detection:** Run `pdfinfo input.pdf`. If `Producer` contains `iOS Version ... Quartz PDFContext` AND page dimensions exceed ~2500 pts in either axis, prefer ghostscript. At 72 DPI on a 2492×3538 pt page the output is ~7.7MB (manageable for `vision_analyze`). At 150 DPI it's ~20MB. A 2.4MB PDF processed in ~2s with gs vs timing out at 30s+ with pdftoppm.

7. **Add a summary/reference page** generated with PIL using text and formatting — no scanning required:
   ```python
   ref = Image.new('RGB', (1800, 950), (240, 240, 235))
   d = ImageDraw.Draw(ref)
   d.text((40, 30), "TITLE", fill=(0,51,102), font=title_font)
   # ... render checklist items with colored indicators
   ```

8. **Compile into a single PDF**:
   ```python
   images = [Image.open(p).convert('RGB') for p in sorted_png_list]
   images[0].save("output.pdf", save_all=True, append_images=images[1:])
   ```

9. **Upload to Drive** and set shareable permissions:
   ```python
   from googleapiclient.http import MediaFileUpload
   media = MediaFileUpload(pdf_path, mimetype='application/pdf', resumable=True)
   uploaded = drive.files().create(body=file_meta, media_body=media, fields='id, webViewLink').execute()
   drive.permissions().create(fileId=uploaded['id'], body={'type': 'anyone', 'role': 'reader'}).execute()
   ```

10. **Delete old versions** if replacing: `drive.files().delete(fileId=old_id).execute()`

### A0/A1 drawings: tesseract instead of vision (floor count / building height)

When `vision_analyze` is unavailable (no vision provider configured) but
you must answer questions like "how many storeys sanctioned / total
height" from a huge scanned sanctioned-plan drawing, tesseract works —
with a few rules:

- **Do NOT render at 300 DPI for tesseract.** A0/A1 at 300 DPI is
  ~14600×10700 px: PIL raises DecompressionBombWarning and tesseract
  hangs or OOMs. Render at **100–150 DPI** (`pdftoppm -png -r 100`).
- **Use `--psm 11`** (sparse text) — drawings have scattered labels,
  not text blocks. `--psm 3/6` return near-empty output.
- **Filter OCR with a keyword grep** to answer the actual question:
  `grep -iE "lvl|level|floor|storey|height|basement|stilt|roof|terrace|GL|m$"`.
  Floor lists ("GROUND FLOOR / 1st FLOOR … 4th FLOOR / TERRACE FLOOR")
  and "BUILDING HEIGHT 54,600" (mm) survive tesseract well enough to
  count storeys and read the sanctioned height.
- Sanctioned-plan PDFs are usually image-only; `pdftotext` returns
  near-zero → skip to render+OCR directly.

Verified Aug 2026: Legacy Cataleya sanctioned layout plan (A0 scan) →
100 DPI render → `--psm 11` → extracted floor list (Basement, 1st
Basement, Ground, 1st–4th, Terrace) and building height 54.600 m.

### Detecting + fixing rotated pages in scanned PDFs (when vision_analyze unavailable)

When a scanned drawing PDF's pages appear rotated 90° (user: "the pages
are rotated counterclockwise 90 degrees — rotate them straight") and
`vision_analyze` has no vision provider configured, use
**OCR-across-rotations** to determine the correction direction, then
fix with pymupdf. Verified 2026-08-14 on Sobha Oakshire plans
(102 layout 1 pg + 103 approved plans 8 pgs, all CCW-rotated):

1. **Media orientation ≠ content orientation.** `page.rotation` and the
   native image dims (`page.get_images(full=True)` →
   `doc.extract_image(xref)`) show the *media* is portrait, but the
   drawing content inside is rotated. Scanned drawings are image-only
   (`page.get_text()` empty), so text-direction spans (`get_text("dict")`
   span `dir`) don't exist to detect rotation either. Must render + OCR.
2. **OCR each candidate rotation with `--psm 11`** (drawings have
   scattered labels; psm 3/6 return near-empty):
   ```python
   from PIL import Image
   img = Image.open(render_png)          # render at 100–150 DPI
   for name, deg in [("orig", 0), ("cw90", -90), ("ccw90", 90), ("180", 180)]:
       im2 = img.rotate(deg, expand=True) if deg else img.copy()
       im2.save(f"/tmp/rot_{name}.png")
       # tesseract /tmp/rot_{name}.png stdout --psm 11
   ```
   PIL `rotate(-90)` = clockwise 90; `rotate(90)` = counterclockwise 90.
   The rotation whose OCR shows readable English (title blocks,
   "AREA STATEMENT IN SQM…", column headers) is the correction.
3. **PITFALL — word-count heuristics lie; read the OCR text.** Counting
   ASCII words ≥4 chars to pick the "best" rotation gets fooled by
   mirrored/rotated glyph artifacts (garbage like "RUINSO OvOY" still
   yields alpha4+ tokens — the automated score said ccw90 for one page
   while the true readable orientation was cw90). Print the OCR sample
   and judge readability directly before trusting any scoring.
4. **Apply the fix with `page.set_rotation(90)`** — PDF /Rotate is
   clockwise, so a counterclockwise-rotated page is corrected by +90.
   For PIL image renders the equivalent is `rotate(-90, expand=True)`.
   Save with `doc.save(dst, garbage=3, deflate=True)`.
5. **Verify EVERY page after rotation** — re-render + re-OCR each page;
   expect high readable-word counts on all pages before delivering.
6. **Replace on Drive:** `drive.files().get_media()` → fix locally →
   `MediaFileUpload` create with same name + same parent folder →
   `drive.files().delete(old_id)` → update any Sheets cells that pointed
   at the old file IDs (mind the row-indexing pitfall in
   `google-workspace` troubleshooting).

### Deskewing slightly-rotated full-bleed scans (invoices, receipts) — sub-degree skew

When a scan is upright but subtly tilted (user: "rotate it / make it straight") — NOT the 90° case above — auto-deskew with OpenCV, then rebuild the PDF. Verified 2026-08-25 on a 3-page Mythri Pharmaceuticals invoice set:

1. **Check metadata first** (`pdfinfo -f 1 -l N`: pages all `rot: 0`, portrait, embedded image dims ≈ page ratio) → full-bleed upright content, only fine skew. Do not assume 90° rotation.
2. **Skew detection — three methods, trust agreement:** (a) `cv2.minAreaRect` on thresholded content returns ~0 for full-bleed rectangular invoice blobs — do NOT use alone; (b) projection-profile (rotate by candidate angles ±6° in 0.2° steps, maximise variance of row-sums of inverted-threshold pixels) detects mild skew but under-corrects; (c) `HoughLinesP` on long table lines (adaptive-threshold + horizontal morphology open `(90,1)`, then Canny) is most robust for invoice grids. Note OpenCV 5 returns lines as `(N,4)`, not `(N,1,4)` — handle both shapes.
3. **Do NOT trust vision-model tilt estimates at sub-degree:** the SAME page was called "1–2° clockwise" then "1–2° counter-clockwise" across two calls. When two CV methods independently report <0.5°, the document is effectively straight — ship the deskewed rebuild and move on.
4. **Rebuild for email-size output:** render at 300 dpi → deskew via `cv2.warpAffine` (INTER_CUBIC, BORDER_REPLICATE) → convert pages to JPEG q≈92 with a 12px white margin → `img2pdf.convert([jpgs])`. PNG pages at 300 dpi ≈ 10 MB; JPEG pages ≈ 3.5 MB. Install: `uv pip install --python /opt/hermes/.venv/bin/python opencv-python-headless img2pdf` (adds cv2, numpy, img2pdf, pikepdf).
5. **Always re-verify with vision** on the rebuilt PDF's render (upright/clean) before filing or attaching to a claim email.

Full working script + settings: see `references/deskew-scanned-invoices.md`.

### Pitfalls (annotated-PDF workflow)
- **pdftoppm rotation**: PDFs with `Page rot: 270` may render rotated. Check with `pdfinfo` and adjust crop coordinates accordingly.
- **Conditions may be in a separate document**: The licence certificate (BBMP/CC/xxxx) may only reference conditions — the actual conditions table is often in the **Sanctioned Plan** drawing PDF, not the licence PDF. Always search the same Drive folder for the sanctioned plan document.
- **Threading email drafts correctly**: When creating a reply draft with `MIMEMultipart`, the `In-Reply-To` and `References` headers must exactly match the target message's Message-ID and References chain for Gmail to thread it properly. Get these from the full thread metadata via `gmail.users().messages().get(format='full')`.
- **Draft thread ID**: A draft may get a temporary thread ID different from the target thread. When sent (by the user from Drafts), Gmail should re-thread it correctly based on In-Reply-To — this is normal Gmail behaviour.

### Example: Ranka Amber NOC Evidence PDF

A 4-page highlighted PDF was produced showing:
1. Licence cover with building details highlighted
2. Sanctioned Plan conditions crop with Condition #4 (BESCOM/BWSSB dev charges) highlighted in yellow
3. Labour conditions page with "Labour NOC is mandatory" highlighted (showing this is the ONLY required NOC)
4. Summary table listing which NOCs are required vs not, with colour-coded indicators

This pattern works for any regulatory/legal document where specific clauses need visual evidence for third-party submission (banks, authorities, auditors).

### Quick highlight & render-to-image (pymupdf-native)

When you need to highlight a specific text region on a PDF page and deliver the result as an **image** (PNG) — not a PDF — use pymupdf's native shape-drawing + pixmap render. This avoids pdftoppm, PIL imports, and intermediate files.

**When to use this:** The user wants a single annotated page as a picture they can view instantly on messaging (e.g. bank statement with one transaction highlighted). The existing PIL-based workflow is for multi-page *PDF* outputs — use this for quick visual responses.

**Workflow:**

1. **Find text coordinates** with `page.get_text('blocks')` — each block returns `(x0, y0, x1, y1, text, ...)`:
   ```python
   import fitz
   doc = fitz.open('/tmp/document.pdf')
   page = doc[page_number]
   blocks = page.get_text('blocks')
   for b in blocks:
       print(f'[{b[0]:.0f},{b[1]:.0f},{b[2]:.0f},{b[3]:.0f}] {b[4][:80]}')
   ```

2. **Draw a highlight rectangle** using `page.new_shape()`:
   ```python
   rect = fitz.Rect(x0 - 4, y0 - 4, x2 + 4, y2 + 4)
   shape = page.new_shape()
   shape.draw_rect(rect)
   shape.finish(fill=(1, 1, 0), fill_opacity=0.3)  # Yellow at 30% opacity
   shape.commit()
   ```

   **For multi-column entries** (e.g. bank statement with description left and amount right): merge the left and right blocks into a single encompassing rectangle.

3. **Render to image** at 300 DPI and save as PNG:
   ```python
   mat = fitz.Matrix(300/72, 300/72)
   pix = page.get_pixmap(matrix=mat)
   pix.save('/tmp/highlighted_page.png')
   ```

4. **Share the image** via MEDIA tag in your response.

5. **Optional — Verify with vision_analyze** to confirm highlight is correctly positioned.

**Pitfalls:**
- `shape.finish(fill_opacity=...)` — 0.3 is a good balance. Lower = too faint, higher = obscures text.
- Text block coords are in points (72/inch). fitz handles the coordinate transform when you render after drawing.
- For scanned PDFs with no extractable text, fall back to the PIL + pdftoppm workflow below.

## Filling Non-AcroForm PDFs (Text Overlay)

When you need to fill in fields on a PDF that has **no AcroForm fillable fields** — a blank form that was designed to be printed and filled by hand — use PyMuPDF to overlay text at precise coordinates.

Common trigger: user uploaded/filled a PDF form with a mistake (wrong grade, date, name) and needs a corrected version. The original was a blank scanned form; the user's filled version was printed, signed, scanned, and sent as an image-based PDF — so you cannot edit the user's output. Instead, start from the **original blank** and overlay the correct text.

### Workflow

**1. Get the original blank form** — usually from the same email thread attachment list that contained the filled version, or from the user's Drive.

**2. Extract text positions from the blank form** to locate where fields go:

```python
import fitz
doc = fitz.open('blank_form.pdf')
page = doc[0]
blocks = page.get_text('dict')['blocks']
for b in blocks:
    if b.get('type') == 0:  # text
        for line in b.get('lines', []):
            for span in line.get('spans', []):
                bbox = span.get('bbox')
                print(f'"{span.get("text")}" at ({bbox[0]:.0f},{bbox[1]:.0f}) '
                      f'size={span.get("size"):.0f}')
```

Key insight: the `bbox` gives you `(x0, y0, x1, y1)` — the label text's bounding box in points (72pt = 1 inch on a 612×792 US Letter page). Insert your filled text at `x = x1 + a few pixels`, `y = y0` (matching baseline).

**3. Position your overlay text** using `page.insert_text()`:

```python
page.insert_text(
    fitz.Point(x, y),        # baseline position
    'Rivaan Ranka',          # your text
    fontname='helv',         # use 'helv' (Helvetica), 'times' (Times), or the PDF's embedded font name
    fontsize=11,             # match the original form's font size
    color=(0, 0, 0)         # RGB
)
```

- `insert_text` takes the **bottom-left** of the text baseline — use the original label's `y0` (top) + fontsize for natural alignment.
- For numbers (grade, date), match the existing font size exactly.
- For the **fontname**: Helvetica (`helv`) is the safe cross-platform fallback. If the original uses Arial, Helvetica is visually close enough. To use the PDF's own font, extract `fontname` from `span.get('font')` and pass that (e.g. `'ArialMT'` — case-sensitive).

**4. Draw a checkmark / tick in a checkbox** using `page.new_shape()`:

```python
shape = page.new_shape()
# Tick: short stroke down-right, longer stroke up-right
shape.draw_line(fitz.Point(cb_x, cb_y), fitz.Point(cb_x+4, cb_y+5))
shape.draw_line(fitz.Point(cb_x+4, cb_y+5), fitz.Point(cb_x+10, cb_y-4))
shape.finish(width=1.5, color=(0, 0, 0), fill=None)
shape.commit()
```

Determine `cb_x, cb_y` from the checkbox □ character's position in the text block output (its bbox gives the square's corners). Place the tick inside the square, offset slightly from the edges.

**5. Don't forget `page.update_contents()`** — after shape operations, call this to commit the drawing commands to the page stream. However, `shape.commit()` already calls `update_contents()` internally, so this is automatic.

**6. Verify** by extracting text again and checking positions:

```python
# After save, re-open and get all text
blocks = page.get_text('dict')['blocks']
for b in blocks:
    if b.get('type') == 0:
        for line in b.get('lines', []):
            for span in line.get('spans', []):
                print(f'  "{span.get("text")}" at ({span.get("bbox")[0]:.0f},{span.get("bbox")[1]:.0f})')
```

**7. Deliver** — save the corrected PDF and either:
- Send via MEDIA tag for the user to download on Telegram
- Upload to Drive TMP folder and share the link
- Attach to a Gmail draft (if part of an email reply)

### End-to-End Pipeline Reference

For the complete Gmail→PDF Download→Correction→Verification→Drive→Delivery pipeline (finding the wrong form in the user's sent email, downloading the blank from the thread, overlaying corrections, verifying, and re-delivering), see `references/pdf-correction-from-gmail.md`. This covers the full workflow triggered when the user says "I put [wrong info] on the form — can you fix it?"

### Pitfalls

- **A0 drawing text is tiny**: At 150 DPI, an A0 (841×1189mm) renders at ~7000×5000px, but condition text may be 6-8pt. Always verify with `vision_analyze` on the crop → if unreadable, re-render at 300 DPI or higher (watch OOM — 300 DPI A0 is ~14K×10K = 140MP). For tesseract (not vision) use 100–150 DPI per the section above — 300 DPI hangs tesseract.
- **PIL DecompressionBombWarning**: Images >~89MP trigger this. Either increase the limit (`Image.MAX_IMAGE_PIXELS = None`) or work with crops not the full image.
- **Font availability**: `insert_text()` uses the built-in Base 14 fonts (`helv`, `times`, `courier`, `symbol`, `zapfdingbats`). If the original PDF uses an embedded font you can't load, Helvetica is an acceptable visual substitute at the same size — the recipient won't notice on a filled-value.
- **Coordinate confusion**: `insert_text` positions the **baseline** of the text, not the top. If you use the original label's `y0` (which is the top of the text), your text will render one line-height above the label. Add fontsize: `y = bbox[1] + fontsize`.
- **Color must be tuple**: `color=(0, 0, 0)` for black. PyMuPDF rejects hex strings or named colors in this API.
- **Scanned user-filled originals cannot be edited**: If the user printed, filled, signed, and scanned the form, the result is an image-based PDF. You can't change individual letters — you must regenerate from the original blank. Find the original blank in the same email thread or the user's Drive.
- **Re-delivery**: If the corrected PDF is replacing one already sent in an email thread, create a new Gmail draft (don't modify the old one) and delete the old draft if it still exists.

### Verify a final PDF is all-black before delivery

When the user asks for a "clean" PDF (often after you updated a
redlined Google Doc and they say "make sure all text is black, produce
the PDF"), verify BOTH the source doc and the rendered PDF before
sharing:

1. **Google Docs source** — walk `documents().get()` body text runs and
   flag any run whose `textStyle.foregroundColor` is non-black. A
   redlined working copy commonly still carries blue runs
   (rgb ≈ 0,0,1). The clean/updated doc should have zero non-black runs.
2. **Rendered PDF** — with pymupdf, collect distinct span colors:
   ```python
   import pymupdf
   doc = pymupdf.open('out.pdf')
   colors = set()
   for page in doc:
       for block in page.get_text('dict')['blocks']:
           for line in block.get('lines', []):
               for span in line.get('spans', []):
                   raw = span.get('color', 0)
                   colors.add(((raw>>16)&255, (raw>>8)&255, raw&255))
   # expect exactly {(0,0,0)}
   ```
3. Export the clean Google Doc via `drive.files().export(fileId, mimeType='application/pdf')` — that guarantees the PDF matches the (verified-black) doc, rather than shipping a stale earlier export.

Deliver via `MEDIA:/path.pdf` on Telegram.

### Validating OCR'd financial totals (quotes, BOQs, invoices) — arithmetic cross-check

When a scanned vendor quote / BOQ / invoice's totals are garbled by OCR (common on
dense bottom-line tables with ₹ signs and decimals), do NOT trust the raw OCR numbers.
Instead **cross-check the arithmetic**:

- GST @18% should equal `base × 0.18`; grand total should equal `base × 1.18`
  (or base + GST). If two of the three numbers satisfy the relation and the third
  doesn't, the third is an OCR misread (verified 2026-08-14 comparing Vardhan /
  Alpha / Marabou quotes: Alpha's GST line OCR'd as `7.26,660` but `80,74,000 × 0.18
  = 14,53,320` and `× 1.18 = 95,27,320` matched the printed grand total — the GST
  cell was simply misread; Marabou's totals needed a re-OCR pass).
- **Re-OCR the totals strip at high DPI with a tight crop.** Page-bottom totals get
  more garbled at 150 DPI full-page OCR. Crop the bottom ~10–30% of the page
  (`fitz.Rect(0, h*0.68, w, h*0.92)`), render at 400–500 DPI, optionally 2× upscale
  with LANCZOS, then `tesseract --psm 6` (psm 4 also useful for aligned columns).
  On the re-OCR pass the label pairs are visible: "Sub-Total | ₹76,69,668.75" /
  "GST @18% | ₹13,80,540.38" / "Total | ₹90,50,209.13" — and `76,69,668.75 × 1.18 =
  90,50,209.125 ≈ 90,50,209.13` confirms all three.
- **Check scope equivalence before comparing quote totals.** A quote that covers a
  narrower scope (e.g. plumbing-only vs full underground services incl. electrical
  conduit) is NOT directly comparable on price — flag the scope gap rather than
  reporting the cheaper-looking number as a win. Also verify each vendor's stated
  terms (advance %, running bills, client-supplied materials) since payment terms
  materially change the comparison.

### Photos of physical documents (receipts, cheques, slips) → clean PDF

A recurring DRAAS pattern: NDR shares a **phone photo** of a payment slip / cheque /
receipt and expects it processed before filing or attaching. Typical ask: "rotate it,
crop it, PDF it, rename it, file it".

### The pipeline (verified 2026-08-11, two receipts + one cheque)

1. **Rotate first.** PIL `Image.rotate(angle)` rotates **counter-clockwise** — so
   "rotate anti-clockwise 90°" = `im.rotate(90, expand=True)`. `expand=True` keeps all
   pixels (swap w/h). Verify orientation by OCR'ing the rotated file before cropping.
2. **Crop to content — but beware gray-cast photos.** `getbbox()` on a threshold LUT
   fails for photos with a gray cast (mean brightness ~140, extrema (1,221), no pure
   whites — the receipt fills the whole frame on a mid-gray surface). The `point()` LUT
   trick returns `None` bbox even though text exists. **Fix:** compute row/column
   darkness profiles with `ImageStat.Stat` on 16–20px bands of `255 - gray`, and read
   where the darkness drops (that's the document zone vs darker surround). Example
   result: receipt at x≈40–595, y≈100–1180 in a 721×1280 photo; cheque at x≈95–1185,
   y≈35–595 after rotation.
3. **Enhance legibility:** `ImageOps.autocontrast(cutoff=1)` + `ImageEnhance.Contrast(1.1–1.15)`
   + optional `Brightness(1.05)`. Save PDF via `im.convert("RGB").save(path, "PDF", resolution=200)`.
4. **Verify with tesseract** (installed, 5.5.0) — `tesseract file.jpg stdout --psm 3` on
   the cropped JPG; confirm amount/vendor/date survived the crop.

### Reading exact fields (dates, amounts) from a cheque/bill

- **vision_analyze free-OCR path is unreliable on upscaled crops** — it sometimes falls
  through to the paid vision provider ("No LLM provider configured for task=vision")
  on 3×-upscaled region crops, even though it OCR'd the original fine. Use **tesseract**
  for tight crops instead.
- **Locate a word precisely with tesseract TSV:** `tesseract img stdout --psm 3 tsv`
  → parse CSV rows, find the word (e.g. "2026"), get its `left,top,width,height` bbox,
  then crop that zone and re-OCR at 4–8× scale.
- **Digits-only whitelist for dates/amounts:**
  `tesseract crop.png stdout --psm 6 -c tessedit_char_whitelist=0123456789/-`
- **Multi-engine agreement rule:** when 2+ independent engines (tesseract + platform OCR)
  agree at conf ≥ 90 on a field (e.g. cheque date `24-02-2026`), **trust it and move on**
  — do NOT burn turns pixel-verifying via ASCII renders when the value just seems
  inconsistent with the narrative. Flag the discrepancy to the user in the summary
  instead (e.g. "date reads 24-02-2026 — say if it's actually 24-08-2026").

### Naming + filing

Use the user's naming convention `<YYYYMMDD>_<Vendor/Desc>_<Detail>_<Amount>.pdf`
(e.g. `20260224_BajajLife_Cheque_2PolicyPremiums_1900.pdf`, cheque-date prefixed).
Drive destination: search `name contains '<vendor>'` + `mimeType='application/vnd.google-apps.folder'`
to find the existing case folder (Bajaj Life Insurance folder, Personal, was the right
home for the cheque). Then attach the same PDF to a reply-all Gmail draft — see
`email-drafter` skill §"Reply-all" and `templates/draft-with-attachments.py`.

## Bilingual (Tamil/English) Government Certificates → English HTML/PDF

TN Reginet ECs (and similar bilingual certificates) arrive with English column
labels but Tamil VALUES (party names, boundaries, remarks). "Convert to English
in its original format" = rebuild as HTML+CSS reproducing the layout, then
render to PDF. Workflow (verified 2026-08-12, EC Survey 235 Sevaganapalli,
23 pp / 24 entries):

1. **Extract:** `pdftotext -layout` — these PDFs have a text layer, no OCR
   needed. Bilingual means the English labels are already in the file; only the
   values need translation.
2. **Generate HTML from data, don't hand-write it:** build a Python script with
   each entry as a dict (sno, doc_no, dates, nature, executants, claimants,
   cons, market, pr, remarks, schedules[]) and render: govt header, metadata
   table, 7-column transaction table, per-entry extra blocks
   (Consideration/Market/PR/Remarks/47A), schedule tables (Property Type /
   Extent / Village / Survey No. / Boundaries). A 24-entry EC is ~78KB HTML —
   impossible to maintain by hand.
3. **Orientation fidelity:** check `pdfinfo` FIRST — TN Reginet ECs are A4
   LANDSCAPE (842×595 pts). Set `@page { size: A4 landscape; margin: ... }` or
   the render defaults to letter/portrait and looks wrong vs the original.
4. **Render HTML→PDF with the Playwright chrome-headless-shell** (no weasyprint
   or system chromium on the VPS):
   ```bash
   CHROME=$(find /opt/hermes/.playwright -name chrome-headless-shell | head -1)
   "$CHROME" --headless --disable-gpu --no-sandbox \
     --print-to-pdf=out.pdf --no-pdf-header-footer \
     --virtual-time-budget=10000 "file:///abs/path.html"
   ```
5. **Verify via pdftotext on the OUTPUT PDF** (vision may be unavailable):
   - assert zero Tamil chars: `re.findall(r'[\u0B80-\u0BFF]+', text)` → `[]`
   - all document numbers present (list them; report any missing)
   - schedule-block count matches expectation (Σ schedules per entry)
   - grep values independently — pdftotext wraps long lines, so a missing hit
     like "Computer Patta No. 1917" is often just a line-wrap artifact: grep
     the numeric value alone before assuming content is lost.

Tamil→English glossary for EC values, boundary abbreviations, and party-name
notes: see `references/tn-ec-tamil-glossary.md`.

### Kannada registered deeds (GPA / sale deed) → English translation as HTML/CSS + PDF

Registered Kannada legal documents (GPAs, sale deeds, partition deeds) arrive as
multi-page scans with a thin text layer of garbled Kannada that pymupdf cannot
decode. The full pipeline that works (verified 2026-08-20 on a 13-page Kannada
GPA, Sy.223 Byadarahalli → clean English translation):

1. **Download from the Drive link with an authenticated account.** A raw
   `curl "https://drive.google.com/uc?export=download&id=<FILE_ID>"` on a
   private/shared file returns a Google **sign-in HTML page** (~928KB), not the
   PDF. Use `build_service('drive','v3', service_name='google-draas')` +
   `MediaIoBaseDownload` (see `download_gpa.py` pattern in
   `references/kannada-translation-pipeline.md`). Probe the PDF's identity with
   `open(path,'rb').read(10)` — expect `b'%PDF'`.
2. **Detect scanned vs text layer** — `page.get_text()` on every page. `len(text)
   < few hundred` chars of garbled Kannada across all pages means scanned.
3. **Render every page to PNG at 200 DPI**: `page.get_pixmap(dpi=200).save(...)`.
4. **OCR with Tesseract Kannada engine — NOT vision_analyze.** This is the key
   finding: on dense scanned Kannada legal text, `tesseract page.png stdout -l kan
   --psm 6` returns **clean, readable Kannada**, while `vision_analyze` returns
   **garbled mangled output** (the LLM OCR folds dense Kannada into mojibake). So
   reverse the skill's general "OCR failed → fall back to vision" instinct for
   Kannada: tesseract `kan` is the BETTER first choice. Whole-scan OCR into one
   file, `===== PAGE NN =====` delimiters, then read it per page.
5. **`-l kan` alone is fine for Kannada-heavy legal bodies** (English numbers —
   Aadhaar/survey/extent — survive). Use `-l kan+eng` only when the page is
   genuinely mixed (registration "Document Sheet" headers).
6. **Translate faithfully, mirroring the original structure.** For a GPA: keep the
   parties (Grantor/GPA-giver vs GPA-Holder/Donee — verify the direction from the
   OCR: "ನಿಮಗೆ" = "to you" marks the donee; "ಮಾರಾಟಗಾರರು" = sellers = usually the
   grantors), the numbered power clauses, the Schedule of Property with the 4
   boundaries (East/West/North/South), title recital, stamp-certificate, signature
   block. Cross-check against any known prior documentation of the same instrument.
7. **Build an HTML+CSS legal document** — serif, `.page` container, header
   (dept/name/Kannada gloss), meta-table (reg-no, dates, stamp duty paid),
   `ol.clauses` with `counter()` for the numbered powers, `.schedule` bordered box
   for the property, `.sig-box`. Include a translation note that the Kannada
   original prevails.
8. **Render + visually verify with WeasyPrint** (installed via
   `uv pip install --python <myvenv> weasyprint`): `weasyprint.HTML('f.html')
   .write_pdf('f.pdf')`, then `pymupdf` the PDF to page PNGs and `vision_analyze`
   them to confirm the CSS/header/counters/table rendered cleanly before delivery.
   Deliver both the `.html` (the requested artifact) and the `.pdf`.

Full numbered worker (download → render → OCR → HTML scaffold) with the GPA
parties/consideration mapping: see `references/kannada-translation-pipeline.md`.
That reference also covers the **Agreement-to-Sell (non-possession) variant**
(ಸ್ವಾಧೀನರಹಿತ ಶುದ್ಧಕ್ರಯದ ಮುಂಗಡ ಕರಾರುಪತ್ರ): translate faithfully as what the Kannada
actually says, and **never trust the requested doc type / filename** — read the
first OCR page's title line to identify the real instrument (GPA vs Agreement to
Sell vs sale/partition deed) and flag any mismatch to the user. Agreement-to-Sell
carries consideration + advance-payment table + balance-at-registration +
non-possession + consent-party paragraphs that a GPA does not.

**Variant: Kannada court orders / quasi-judicial proceedings** — see
`references/kannada-court-order-translation.md`. Court orders have a different
structure (case header, presiding officer, parties vs respondents, findings →
order) and the rendering pipeline favours **direct OpenRouter API with Gemini 2.5
Flash** over tesseract. For ≤3 page court orders, the direct vision approach
returns clean translations; the tesseract path is for dense multi-page deeds.

### Multi-EC transaction parsing → per-survey tables (5 ECs, 170 entries)

When the user uploads SEVERAL ECs (one per survey no) and asks to "verify all
transactions" / "list transactions per survey no" / build a spreadsheet with
Sl No, Sy No, Sub-number, Type, Date, From, To, Doc No, deduped across ECs —
use `references/tn-ec-transaction-parsing.md`. Core moves:

- **Parser input = `pdftotext -bbox` XML, not pdfplumber** — TN Reginet ECs
  have a text layer but a legacy Tamil font that pdfplumber garbles;
  pdftotext renders Tamil correctly and `-bbox` adds word coordinates.
- Classify columns by **x-coordinate** (exec ≈414, claimant ≈546), not
  character columns — compact vs expanded entry formats shift columns.
- Entry-start gate: Sr-line candidates kept ONLY if the following block has a
  doc number + "Consideration Value" line.
- **Boundary descriptions (எல்லை விபரங்கள்) bleed into survey lists** —
  hard-stop survey collection there; continuation lines must contain a `/`
  survey token; check the RIGHT zone only on modern lines whose left zone
  carries "Property Type"/"Village" labels.
- Verify entry count parity with EC footers (52/35/15/29/39 = 170).
- Master doc table: union survey lists across ECs (page-break truncation
  differs per EC).

## Split, Merge & Search

pymupdf handles these natively — use `execute_code` or inline Python:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

No extra dependencies needed — pymupdf covers split, merge, search, and text extraction in one package.

---

### Post-Extraction: Building Formula-Rich Google Sheets from Tabular Data

When the extracted document contains tabular data (fee schedules, calculations, rate tables, cost estimates) and the user wants a Google Sheet preserving the **exact row-by-row layout** with **interlinked formulas**:

**Workflow:**

1. **Extract data**, preserving every row, blank line, and value position. Do not summarise or collapse multi-row layout. Use `pdftotext -layout` for text-based PDFs or ghostscript + `vision_analyze` for image-based scans.

2. **Create the sheet** via the Google Sheets API using `_load_credentials_direct` from the terminal (this is the *reliable* path for complex multi-step sheet creation — `build_service` and `gws_skill_bridge.call` fail in the `execute_code` sandbox):
   ```python
   import os, sys; sys.path.insert(0, '/opt/hermes')
   from tools.gws_auth import _load_credentials_direct
   from googleapiclient.discovery import build
   creds = _load_credentials_direct(
       os.environ.get('HERMES_SESSION_USER_ID', '[REDACTED-TID]'),
       'google-draas'
   )
   sheets = build('sheets', 'v4', credentials=creds)
   ```

3. **Write raw values first** with `valueInputOption='RAW'` — labels, numbers, and all structural data including blank separator rows. Build the data as a Python list-of-lists and write in one `values().update()` call per sheet:
   ```python
   sheets.spreadsheets().values().update(
       spreadsheetId=SID, range="'Sheet1'!A1",
       valueInputOption='RAW',
       body={"values": row_data}  # list of lists, exact row count
   ).execute()
   ```

4. **Apply formulas in a separate pass** with `valueInputOption='USER_ENTERED'` — one `update()` per formula or formula batch. Use absolute references (`$B$5`) for parameter cells that must not shift when copied:
   ```python
   sheets.spreadsheets().values().update(
       spreadsheetId=SID, range="'Sheet1'!B12",
       valueInputOption='USER_ENTERED',
       body={"values": [["=B11*0.4"]]}
   ).execute()
   ```

5. **Formula chaining pattern** — parameter cells at the top (Site Area, FAR, GV), intermediate calculations reference them with `$` absolute refs, and final totals chain through intermediate cells:
   - Parameter row: `B5` = Site Area (absolute ref `$B$5` in all formulas)
   - Calculation: `B20 = B18 * $B$19 * $B$7` (refs parameter + local values)
   - Total: `B23 = B21 * (1 + $B$22)` (chains through local calc cells)

6. **Formatting after formulas** via `batchUpdate` for bold headers, column widths, and number formats.

**Key `_load_credentials_direct` pattern (terminal, not sandbox):**

```python
# Must run from /opt/hermes directory
# Must have HERMES_SESSION_USER_ID set
cd /opt/hermes && HERMES_SESSION_USER_ID=[REDACTED-TID] python3 script.py
```

This bypasses the `HERMES_RPC_SOCKET` sandbox check and reads the vault token directly. The service account is NOT used — tokens are per-user OAuth stored in the gws-vault daemon.

### Creating a Google Sheet in a Specific Drive Folder

The Sheets API `create()` call creates the sheet in the root of My Drive. To place it inside a specific folder:

```python
from tools.gws_auth import build_service

# 1. Create via Sheets API first
sheets = build_service('sheets', 'v4', service_name='google-draas')
drive = build_service('drive', 'v3', service_name='google-draas')

sheet = sheets.spreadsheets().create(body={
    'properties': {'title': 'Sheet Name'}
}, fields='spreadsheetId,spreadsheetUrl').execute()
sheet_id = sheet['spreadsheetId']

# 2. Move to target folder via Drive API
PARENT_ID = '1dKMyaM3DYYDjBgMz1t9Lp44NpXAfptlK'  # target folder ID
file = drive.files().get(fileId=sheet_id, fields='parents').execute()
for parent in file.get('parents', []):
    drive.files().update(fileId=sheet_id, removeParents=parent).execute()
drive.files().update(fileId=sheet_id, addParents=PARENT_ID, fields='id, parents').execute()
```

Do NOT use `drive.files().create()` with `mimeType='application/vnd.google-apps.spreadsheet'` and a `media_body` — this returns `400 Bad Request`. The Sheets API create + Drive move pattern above is the reliable path.

**Pitfall — `execute_code` sandbox vs terminal:** `build_service()` and `gws_skill_bridge.call()` fail in the `execute_code` sandbox with `ImportError: cannot import name 'gws_fetch_token'` because the sandbox's `hermes_tools` stub lacks the RPC bridge. For complex sheet creation (multi-pass, dozens of formula cells), always write a standalone Python script to `/tmp/` and run it via `terminal()` with `HERMES_SESSION_USER_ID` set.

**Row-by-row layout rule:** Preserve every blank separator row from the source document. Do not collapse consecutive empty rows to a single one — the spacing conveys section grouping. Column labels should match the source exactly, including "S.No.", "Particulars", "Amount (Rs)" as they appear.

### Document Organization

After extracting content from documents, the user often expects follow-up actions. Which skill to hand off to depends on the document type:

- **Medical documents** (discharge summaries, lab reports, prescriptions, scans) → see **`medical-document-processing`** skill: file on Google Drive with consistent naming, research medications, create follow-up calendar events, generate WhatsApp summaries.
- **Financial/tax documents** (Form 16s, salary slips, bank statements) → see **`personal-document-organization`** skill: rename with conventions, file locally, pair Part A↔B.
- **Property / legal / agreement documents** (sale deeds, agreements, title docs) → see workflow below (Drive TMP filing, rename convention, one-paragraph summary).

### Property / Legal / Agreement documents (Google Drive filing)

For property documents, agreements, sale deeds, and scanned legal documents that need to be filed on Google Drive (not locally):

**Two workflows — choose based on how clearly the destination is known:**

#### Workflow A: User specifies a project or hints at a folder (preferred — propose-then-confirm)
Use this when the user says things like "file in the RERA folder", "put it under Ranka Amber", or otherwise indicates they know roughly where it goes.

1. **Extract text** via OCR (pdftoppm + tesseract for scanned PDFs, or pymupdf for text-based PDFs)
2. **Summarise the document** — parties, property details (survey number, area, village), consideration amount, key terms
3. **Rename using convention**: `YYYYMMDD_{Project}_{Type}_{Parties}.pdf`
   - Example: `20050830_Devraj_Holiday_Village_Agreement_Pai_Ranka.pdf`
4. **Search Drive** for the most relevant candidate folder. Use `drive.files().list()` with `name contains` and `mimeType='application/vnd.google-apps.folder'` to find matching folders.
5. **Trace the folder tree to root**: recursively call `drive.files().get()` on each parent ID until you hit My Drive (a folder with no `parents` array). Build the tree path so the user sees exactly where the file lands.
6. **Present the proposal** to the user:
   - Suggested file name(s)
   - Full folder tree from root to the candidate folder
   - Brief summary of what the document contains
   - Explicitly say "waiting for your confirmation before filing"
7. **Do NOT file until the user approves.** Once they confirm, upload the renamed PDF(s) to the approved folder. Set the `description` field to a one-paragraph summary.

#### Workflow B: No destination known (TMP-first)
Use this when the user does not suggest any folder and the destination is genuinely unclear.

1. Extract text via OCR
2. Summarise the document
3. Rename using convention: `YYYYMMDD_{Project}_{Type}_{Parties}.pdf`
4. **Upload to Drive TMP folder first** (historically NDR's preference for incoming documents — TMP folder ID: `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`)
   - Use `drive.files().create()` with `MediaFileUpload`
   - Include a meaningful `description` field with the document summary
5. Report back — document name, Drive link, which folder it's in, and a one-paragraph summary
6. Propose a permanent folder (trace tree to root) and ask if they want it moved there

**Key pitfalls:**
- Always trace the full Drive tree to root when proposing a folder — the user needs to see the ancestry, not just the folder name.
- Never file without explicit user confirmation when they've indicated a preference for where it should go.
- When scanning multiple documents (e.g., 2 agreement copies + a covering letter), flag any mismatch between the user's description and the actual document type (e.g., "you called this an affidavit but it's actually a covering letter").

See also:
- `medical-document-processing` skill — for medical documents (Drive filing + calendar + WhatsApp)
- `personal-document-organization` skill — for local filing of financial/tax documents
- `professional-documents` skill — for creating new professional PDFs (quotations, invoices) from templates

### Medical documents

See the **`medical-document-processing`** skill for the full pipeline:
- Extract patient, diagnosis, procedure, medications, follow-up date
- Rename and upload to the person's Medical folder on Google Drive
- Research medications with purposes
- Create calendar event with family member attendees
- Generate WhatsApp summary for the patient/family

### Financial documents

See the **`personal-document-organization`** skill for the full workflow:
- Identify the issuing entity / document type
- Pair Part A ↔ Part B (Form 16s) by Certificate Number
- Rename with consistent conventions
- Create missing subfolders on demand
- File under the appropriate path

## Notes

- `web_extract` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- Both helper scripts have `--help` for full options
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- For Word docs: `pip install python-docx` (better than OCR — parses actual document structure)
- For PowerPoint: see the `powerpoint` skill

## Password-Protected PDFs (Indian Banks / Insurers)

Many Indian bank statement PDFs (Kotak, HDFC, ICICI, SBI card statements) and insurer policy documents are password-protected. Common conventions:

**Kotak Bank statements** (confirmed pattern):
- Password format: `first4letters_of_account_holder_name (lowercase) + DDMM of date of birth/incorporation`
- Example: Name "Raj Bhargava", DOB 28-08-1992 → password = `rajb2808`
- Company variant: Company "Raj & Sons", DOI 19-06-1998 → password = `rajs1906` (drop ampersand, lowercase)
- Hint text always appears in the email body — search the email for "password" or "Date and Month of Birth" to confirm

**Workflow when hitting a password-protected PDF**:
1. Search the originating email body for the password convention/hint (most banks put it in the email itself)
2. If hint says "Customer Relationship Number" (CRN), use the CRN from the user's contact sheet/bank welcome letter
3. Construct candidate passwords, attempt via `pymupdf.Document.open(path, password=...)` or `pdftotext -upw <pwd> file.pdf`
4. If password fails after 3 attempts, ask the user — do not brute-force

```python
import pymupdf
doc = pymupdf.open("statement.pdf", password="kant1503")  # example
if doc.needs_pass:
    print("Wrong password")
for page in doc:
    print(page.get_text())
```

## Natural-Language PDF Editing (nano-pdf)

Install `nano-pdf` and edit PDF text via natural language instructions:

```bash
uv pip install nano-pdf
nano-pdf edit <file.pdf> <page_number> "Change title to 'Q3 Results'"
nano-pdf edit report.pdf 3 "Update date from January to February 2026"
nano-pdf edit contract.pdf 2 "Change client name from 'Acme Corp' to 'Acme Industries'"
```

**Notes:**
- Page numbers may be 0-based or 1-based — retry with ±1 if wrong page is edited
- Works well for text changes; complex layout modifications may need a different approach
- Requires an API key for the underlying LLM (check `nano-pdf --help`)

---

## PDF → Images → Vision Analysis (when OCR tools are unavailable)

When `marker-pdf` is not installed but vision analysis is required (per the OCR→Vision workflow above):

1. **Convert PDF pages to PNGs** — two options:
   a) **With poppler-utils (pdftoppm):** `pdftoppm -png -r 200 input.pdf /tmp/page`
   b) **With pymupdf (faster, no poppler dependency):**
      ```python
      import pymupdf
      doc = pymupdf.open("input.pdf")
      for i, page in enumerate(doc):
          pix = page.get_pixmap(matrix=pymupdf.Matrix(200/72, 200/72))  # 200 DPI
          pix.save(f"/tmp/page_{i}.png")
      doc.close()
      ```
      pymupdf rendering is faster than pdftoppm for small-to-medium PDFs and avoids the poppler-utils dependency entirely. The `Matrix(200/72, 200/72)` gives 200 DPI; adjust for higher resolution (e.g. `Matrix(300/72, 300/72)` for 300 DPI). For a single-page PDF, use `page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))` to scale to 50% for faster preview, then `vision_analyze` on the output PNG.

2. **Pass each page image to `vision_analyze`** with a specific question (e.g. "Extract the transaction on or around 26 May 2026 with description containing 'Royal Sundaram'")
3. Aggregate results per page into a single structured answer

> **Visual PDF inspection (floor plans, brochures, cluster plans, diagrams):** For PDFs
> whose content is VISUAL (architectural floor plans, property brochures, cluster plans,
> layout diagrams) — where the question is "what does this show?" rather than "what does
> this text say?" — this pdftoppm + vision_analyze workflow is the **primary** method,
> not a fallback. pdftotext may return some labels and dimensions (room sizes, tower
> names, unit series), but the actual layout relationships (which units are adjacent on
> a floor, which tower a plan belongs to, whether a combined floor plan exists) require
> visual inspection of the rendered page.
>
> Workflow: `pdftoppm -jpeg -r 200 input.pdf /tmp/pages/page` → for each page,
> `vision_analyze(image_url=..., question="Describe this page. What tower does it show?
> What units? Is there a combined layout?")` → aggregate. JPEG at 200 DPI keeps each
> page ~300–500 KB — manageable for 20+ page brochures.
>
> Verified Aug 2026: Century Regalia brochure (22 pp, A3, Adobe Illustrator) where
> pdftotext extracted tower names and unit dimensions but the Crissa cluster plan
> (page 17) showing all 4 unit positions on a floor, and the individual Crissa unit
> floor plans (pages 18–19), required vision_analyze on page renders to confirm layout
> and answer "does a combined Crissa 401+404 floor plan exist?" (answer: no — the
> individual Series 01 & 02 plans are separate, only the cluster plan shows positioning).

**Direct OpenRouter vision call (when `vision_analyze` isn't in the session):** POST to
`https://openrouter.ai/api/v1/chat/completions` with model **`google/gemini-2.5-flash`**
(the configured vision model — do NOT use `google/gemini-2.0-flash`, it returns
`400 "not a valid model ID"` on this account; verified 2026-08-14) and content
`[{"type":"text",...}, {"type":"image_url","image_url":{"url":"data:image/png;base64,<b64>"}}]`.
Works for classifying scanned invoice pages (invoice vs supplier slip vs test cert) and
extracting table values. Read the API key from `/data/hermes/.env` (`OPENROUTER_API_KEY`).

This is the only current workaround for the `call_openrouter_model` text-only limitation when OCR tools are not installed locally.

Pitfall: `pdftoppm` requires `poppler-utils` to be installed. If unavailable, ask the user to install it, or fall back to asking the user to open the PDF and describe the key sections.
