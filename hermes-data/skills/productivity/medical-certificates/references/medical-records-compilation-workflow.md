# Medical Records Compilation Workflow

Create a compiled medical records archive PDF — all reports for one patient in chronological order with summary, timeline table, and page-number index. This is NOT a clinical dossier (second-opinion request for a specialist) — it's a personal records archive.

## When to use

- User says "compile all reports for [person] into one PDF"
- User says "make a combined PDF with summary and index"
- User is preparing records for a doctor visit and wants everything in a single file
- User shares a Drive folder of medical records and asks for a structured archive

## Key user preference (Nishant — DRAAS)

**SEPARATE PDFs per person.** Never combine multiple patients into one PDF. Each patient gets their own file with their own summary, timeline, and index. User will correct if you combine them.

## Output structure (exact)

Each PDF has, in order:

1. **Page 1 — Title page:** Patient name (full), date of compilation, brief description
2. **Page 2 — Executive Summary:** 1-2 paragraph narrative summarizing the patient's condition, key diagnoses, surgeries, and notable findings
3. **Page 3 — Chronological Timeline Table:** Every report listed in date order with columns: Date | Hospital/Doctor | Report Type | Key Findings | Page #
4. **Page 3 (continued) — Index with Page Numbers:** Same data as the timeline but formatted as a navigable index — report title + page number
5. **All original full reports merged in date order** — each report starts on a new page

## Workflow

### Phase 1: Find the right Drive folders

1. Use `gws_resolve_account` to find the correct service_name (typically `google-draas`)
2. Search Drive recursively from a known parent folder (e.g., `Personal/`)
3. Find the specific patient folders:
   - `Personal / NDR Medical` — Nishant's medical folder
   - `Personal / KDR Docs / KDR Medical` — KDR's (mother's) medical folder
4. **Confirm with the user** which folders you've identified before proceeding

### Phase 2: Inventory the records

1. List all files in each patient's folder using `drive.files().list()`
2. Filter for medical reports (PDFs, images)
3. Note any misnamed files — e.g., a file that clearly belongs to the patient but has a different person's name in the filename (e.g., "Mr Dhananjay" in KDR's folder). **Use vision_analyze to read the content and confirm it's the patient's.** Then rename on Drive before including.
4. Present the inventory to the user for confirmation before proceeding

### Phase 3: Download and extract content

1. Download all PDFs to a local temp directory using `drive.files().get_media(fileId=...).execute()`
2. For each PDF, determine if it's text-based or image-based:
   - Try `pymupdf` (fitz) — `doc = fitz.open(path); text = page.get_text()` — if it returns text, use it
   - If pymupdf returns no text (scanned/image PDF), convert to images and use `vision_analyze`:
     ```python
     import fitz
     doc = fitz.open(pdf_path)
     for i, page in enumerate(doc):
         pix = page.get_pixmap(dpi=300)
         pix.save(f"/tmp/page_{i}.png")
     ```
   - Then call `vision_analyze(image_url=...)` for each page
3. Extract key metadata from each report: date, hospital/doctor, report type, key findings
4. Save all extracted text + metadata in a structured JSON file

### Phase 4: Build the compiled PDF

1. Build the front matter in Python:
   - Title page (hardcoded text)
   - Executive summary (drafted from all extracted content)
   - Chronological timeline table (sorted by date)
   - Index with page numbers

2. Merge all original PDFs in order using `pypdf`:
   ```python
   from pypdf import PdfReader, PdfWriter
   writer = PdfWriter()
   
   # Option A: ReportLab for front matter
   from reportlab.lib.pagesizes import A4
   from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
   
   doc = SimpleDocTemplate("/tmp/cover.pdf", pagesize=A4,
       topMargin=36, bottomMargin=36, leftMargin=36, rightMargin=36)
   
   elements = []
   elements.append(Paragraph("Kanta D. Ranka — Medical Records Compilation", title_style))
   elements.append(Spacer(1, 20))
   elements.append(Paragraph("Executive Summary", h2_style))
   elements.append(Paragraph(summary_text, body_style))
   elements.append(Paragraph("Chronological Timeline", h2_style))
   elements.append(Table(timeline_data, ...))
   elements.append(Paragraph("Index", h2_style))
   elements.append(Table(index_data, ...))
   
   doc.build(elements)
   
   # Merge cover with original PDFs
   cover_reader = PdfReader("/tmp/cover.pdf")
   for page in cover_reader.pages:
       writer.add_page(page)
   for pdf_path in sorted_pdf_paths:
       reader = PdfReader(pdf_path)
       for page in reader.pages:
           writer.add_page(page)
   
   with open(output_path, "wb") as f:
       writer.write(f)
   ```

3. **Important**: Include the FULL original PDFs, not just extracted text. The doctor needs to see the actual reports.

### Phase 5: Upload and deliver

1. Upload the compiled PDF to the **same Drive folder** where the source reports live
2. Delete any old combined PDF from the same folder to avoid confusion
3. Provide the Drive link to the user
4. If the PDF is large (>10MB), note the file size

### Phase 6: File cleanup (optional)

- Delete the old combined/merged PDFs if left from a prior pass
- Rename any misnamed files you found (e.g., "Mr Dhananjay" → correct patient name)

## Pitfalls

- **Combining patients is wrong.** Always create one PDF per person. The customer corrected this in a prior session — don't repeat the mistake.
- **Vision OCR for PDFs:** When using `vision_analyze` on scanned PDF pages, convert each page to a PNG at 300 DPI first. Calling `vision_analyze` directly on a PDF file path may not work — use `get_pixmap()` from pymupdf first.
- **File naming on Drive:** Before renaming a file, check there's no duplicate name already. Use `drive.files().list()` with `q=f"name='{new_name}' and '{parent_id}' in parents and trashed=false"`.
- **Report ordering:** Sort strictly by date. If multiple reports share the same date, sort by document type (lab orders first, then consultation notes, then imaging).
- **Page numbers in index:** Build the index AFTER you know the final page count. Either build the front matter first as a separate PDF, count its pages, then add offsets when referencing original report pages. Or use a two-pass approach: build the merged PDF, count pages, then rebuild the front matter with correct page numbers.
- **Drive permissions:** The compiled PDF inherits the folder's permissions. No need to set them explicitly.
- **Old combined PDF removal:** When splitting a combined PDF into separate per-person PDFs, delete the old combined version from Drive so the user doesn't have two files with similar names.
