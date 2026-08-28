# Document Decompilation / Splitting

Reverse of compilation: a single combined PDF containing multiple distinct documents needs to be **split apart** into separate PDFs, named, and organized into folders.

## When to use

- User shares a single large PDF that contains many different reports/records mixed together (e.g., a 58-page scan of all medical records for a year)
- User asks to "separate each document," "split by hospital," or "organize individually"
- A combined PDF where page boundaries don't align with document boundaries

## Workflow

### Phase 0: Handle Unknown File Extensions

Drive files may have misleading extensions (e.g., `.bin` instead of `.pdf`). Before inspecting:

```bash
# Detect actual file type
file combined.bin
# → combined.bin: PDF document, version 1.7

# Or check with pdfinfo (fails on non-PDF)
pdfinfo combined.bin 2>/dev/null && echo "Is a PDF" || echo "Not a PDF"
```

If the `file` command shows "PDF document" but the extension is `.bin` / `.dat` / `.unknown`, simply rename to `.pdf` and proceed:

```bash
mv combined.bin combined.pdf
```

**Do NOT** trust the extension alone — Drive sometimes exports jobs with `.bin` extensions for PDF exports. The `file` command's magic-byte check is the authority.

### Phase 1: Inspect the Combined PDF

```bash
# Check page count, size, if it's scanned or text
pdfinfo combined.pdf
# → Pages: 58, Page size: 579.6 x 817.2 pts

# Check if text exists (scanned = form feeds only)
pdftotext combined.pdf - | wc -c
# → 58 (form feeds = 58 scanned pages, no text)
```

If text-based, use pdftotext/PyMuPDF to extract content per page.
If scanned (image-based, no text), proceed with vision_analyze per page.

### Phase 2: Convert Pages to Images

```bash
# Convert all pages to PNG at 150-200 DPI
mkdir pages
pdftoppm -png -r 150 combined.pdf pages/page
# → pages/page-01.png, page-02.png, etc.
```

Use 150 DPI for quick scanning (balances image size vs legibility). Use 200-300 DPI for OCR-intensive pages.

### Phase 3: Identify Document Boundaries (Vision Scan)

For each page, call `vision_analyze` to extract hospital name, document type, date, and patient name.

**Batch strategy:** Process pages in groups of 5-10 sequentially (vision has no cross-page memory, so send each page independently). Look for these signals:

- **Header change**: different hospital letterhead = new document group
- **Date change**: different date with same hospital = separate visit
- **Document type**: "Audiological Evaluation Report" vs "Consultation" vs "Bill" vs "Lab Report"
- **Page numbering**: some documents say "Page 1 of 2" — group accordingly

Identity patterns to extract per page:
```
Hospital name (letterhead or footer)
Date (often in DD/MM/YYYY or Mon DD YYYY format)
Document type (consultation, lab report, bill, ECG, X-ray, etc.)
Patient name (usually on form)
```

### Phase 4: Group Pages by Document/Hospital

Create a page-to-document mapping:

```python
# Example mapping (58-page PDF)
page_groups = {
    "Vijaya_ENT_Care_Centre_Oct2022": (1, 7),        # 7 pages
    "Trustwell_Lab_Reports_Jun2023": (8, 11),         # 4 pages
    "Trustwell_Preop_Consultation_Jul2026": (12, 18), # 7 pages
    "Manipal_Hospital_ENT_Apr2023": (19, 20),         # 2 pages
    # ... etc
}
```

Rules for grouping:
- Same hospital + close date → same document group
- Same hospital + different dates → separate groups (one per visit)
- Different hospitals → always separate groups
- Bills/Insurance → group with most recent hospital visit
- Duplicate/repeat pages → include as part of the document they follow
- Diagnostics (ECG, X-ray, Echo) → group with the pre-op visit they belong to

### Phase 5: Split by Page Range

```bash
qpdf --empty --pages combined.pdf START-END -- output_filename.pdf
```

**qpdf** (pre-installed at `/usr/bin/qpdf`) is the simplest tool. Syntax:
```
qpdf --empty --pages input.pdf 1-7 -- output_group1.pdf
qpdf --empty --pages input.pdf 8-11 -- output_group2.pdf
```

Alternative: `pdfseparate` (poppler-utils) for one-page-per-file splitting.

### Phase 6: Name Files

Naming convention: `HospitalName_DocumentType_MonthYear.pdf`

- Use hospital short name (no spaces → underscores)
- Include document category (Consultation, LabReport, Bill, ECG, etc.)
- Include month/year for chronological sorting

### Phase 7: Organize into Folders

Create one folder per hospital, move files in:

```
sorted/
├── Trustwell/
│   ├── Trustwell_Lab_Reports_Jun2023.pdf
│   ├── Trustwell_Preop_Consultation_Jul2026.pdf
│   └── Trustwell_Bill_Insurance_Jul2026.pdf
├── Manipal/
│   ├── Manipal_Hospital_ENT_Apr2023.pdf
│   └── Manipal_PFT_Respiratory_Jul2026.pdf
└── Vijaya_ENT/
    └── Vijaya_ENT_Care_Centre_Oct2022.pdf
```

## Pitfalls

- **Textless PDF is normal for scans**: 58 form feeds = 58 scanned pages. Don't treat it as an error. Use vision directly.
- **OCR quality varies**: Handwriting (prescriptions, doctor notes) produces poor OCR. Use `vision_analyze` with full context (hospital name, known patient name) to help the model decode.
- **Duplicate content**: Sometimes the same page appears twice (front/back of a form, or a second copy). Dedupe by content, not page count.
- **Reversed/mirrored text**: Some older scans appear reversed. OCR may fail entirely — use vision with a prompt asking to read even difficult handwriting.
- **Mixed date formats**: Same document may have "03/10/22" (could be March 10 or October 3). Use context from other documents in same group to disambiguate.
- **Name variations**: Same patient may appear as "Kanta Ranka", "Kavita Ranka", "Kantha Ranka", "Kanta D Ranka", "Kanta Rauka" — all refer to the same person. Don't create separate groups for each name variant.
- **Large page counts**: Convert in batches (no more than 15 pages at a time to avoid disk space issues). 58 pages at 150 DPI ≈ 200-300 MB.
- **vision_analyze cost**: Each page call consumes tokens. Group similar pages and ask concise questions to minimize cost. Use OCR mode (default — it auto-detects readable text) rather than full vision when possible.
