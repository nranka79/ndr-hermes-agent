# Legal Document Pack — Customer Handoff Build Recipe

Verified 2026-08-25 on the **Ranka Udaya Legal Document Pack** (23 docs, 225 pages, from the
`Ranka Udaya - Legal Documents` Drive folder id `1zvvtbBtedFiJ4XdcY-9LO4AzJ7V46N9t`).

Use case: Bharat shares an internal Drive folder of title-diligence PDFs, wants one clean
customer-facing PDF for WhatsApp/email. Never expose the internal folder link.

## Workflow

1. **Download all PDFs** from the Drive folder (skip .docx — e.g. allotment letter draft).
   Watch out: long filenames truncated to 80 chars by `safe()` can COLLIDE and silently
   overwrite one another — when two files differ only in the tail (e.g. `...(Amaresha)& others`
   vs `...& others`), the second overwrites the first. Keep `safe()` output unique, or
   detect collisions before writing.

2. **Classify by date.** Source of truth = document execution/issue date, read from content
   (text regex for `dd/mm/yyyy`, `DDth Day of MONTH YYYY`, or OCR), NOT filename alone
   (though filenames like `20241024_...` are usually reliable). Undated docs → end of pack.

3. **Dedupe copies.** Same deed appearing 2–3× in the folder (colour copy / original /
   re-scan / "Copy of Copy of") → keep ONE, normally the largest original. If two legal
   reports are the same date/content (e.g. two K. Velayudham reports 21.09.2024), keep the
   DRA-facing one.

4. **Exclude internal-only files** and say so in the reply:
   - ICICI/unit-nomenclature sheets (internal financing format, not legal)
   - Allotment letter drafts (product of the same session, not source docs)

5. **Build with exact page numbers FIRST** (title=1, index=2, then per doc: separator + N pages).
   Compute ranges before writing so separator pages and the index agree:

```python
ranges = []  # (name, date, start_page, end_page, sep_page)
cursor = 3   # page 1 title, page 2 index; next separator is page 3
for (name, date, fn), n in zip(DOCS, page_counts):
    sep = cursor
    ranges.append((name, date, cursor + 1, cursor + n, sep))
    cursor = cursor + n + 1  # next separator
```

6. **Separator page** per document: dark band + "DOCUMENT {i}" + display name + date +
   `Pages {start} - {end}`. Then `final.insert_pdf(src)`.

7. **Compress** (see below) — scanned title packs land 90–150 MB raw; Telegram/WhatsApp
   delivery cap is ~50 MB.

## 💾 Compression CRITICALITY (the 2× gotcha)

`page.get_pixmap(...)` + `newpage.insert_image(rect, pixmap=pix)` **made the file BIGGER**
(96.4 MB → 145.5 MB) — pymupdf stored the inserted pixmap as uncompressed/unoptimized bytes.

**Working pattern — embed real JPEG streams via PIL:**

```python
pix = page.get_pixmap(dpi=120, colorspace=pymupdf.csRGB)
img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
buf = io.BytesIO()
img.save(buf, format="JPEG", quality=55, optimize=True, progressive=True)
newpage.insert_image(newpage.rect, stream=buf.getvalue())
```

Rasterize only scanned pages (little text + images present); keep text/vector pages as-is
via `insert_pdf(from_page=i, to_page=i)`. 96.4 MB → 36.4 MB (−62%) with this pattern.
Use DPI 120 / quality 55 as a starting point; the pack stays legible.

`scripts/compress_dossier.py` in this skill is the re-runnable version (accepts
input/output/dpi/quality args).

## Vision on scanned PDFs

`vision_analyze` accepts PNG, not PDF. Convert the first page first:

```python
pix = doc[0].get_pixmap(dpi=150); pix.save('/tmp/page.png')
```