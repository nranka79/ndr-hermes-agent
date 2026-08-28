# PDF Redaction with PyMuPDF (fitz)

**Use when:** You need to selectively black out rows/regions in a PDF bank statement or similar financial document before sharing externally.

## Workflow

### 1. Extract text to identify target rows

```python
import fitz
doc = fitz.open("/path/to/document.pdf")
for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    print(f"--- PAGE {page_num + 1} ---")
    print(text)
```

### 2. Get precise coordinates via blocks

`page.get_text("blocks")` returns `(x0, y0, x1, y1, text, block_no, block_type)` tuples. The coordinates are in PDF points (1/72 inch). Use these to identify the exact y-ranges of rows to redact.

```python
blocks = page.get_text("blocks")
for b in blocks:
    x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4]
    print(f"  ({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f}): {text.strip()[:60]}")
```

### 3. Draw redaction annotations

`page.add_redact_annot(rect)` marks a region for redaction. Multiple annotations can be added before applying. Use `fitz.Rect(x0, y0, x1, y1)` for each rectangle.

Strategy: Draw large rectangles covering contiguous blocks of rows to be redacted, leaving gaps for rows to keep visible.

```python
# Redact rows above the target (y1 to y2)
page.add_redact_annot(fitz.Rect(x_left, y_top, x_right, y_bottom_redact_end))

# Keep target row visible (don't annotate its y-range)

# Redact rows below the target
page.add_redact_annot(fitz.Rect(x_left, y_below_top, x_right, y_page_end))
```

### 4. Apply all redactions

```python
page.apply_redactions()
```

This permanently replaces the annotated regions with black rectangles and removes the underlying text content. The PDF is flattened — no hidden data remains under the black boxes.

### 5. Save and verify

```python
doc.save("/tmp/redacted_output.pdf")
doc.close()
```

Verify by re-reading the saved file's text to confirm no unintended text leaks.

## Full worked example (bank statement)

```python
import fitz

doc = fitz.open("/path/to/Kotak_Statement.pdf")

# Page 1: Keep header + row 5 (O3 Infotech salary), redact rest
page1 = doc[0]
page1.add_redact_annot(fitz.Rect(36, 393, 560, 464))  # Rows 1-4
page1.add_redact_annot(fitz.Rect(36, 485, 560, 800))  # Rows 6-20
page1.apply_redactions()

# Page 2: Keep rows 28, 42, 43 (salary rows), redact rest
page2 = doc[1]
page2.add_redact_annot(fitz.Rect(36, 128, 560, 280))  # Rows 21-27
page2.add_redact_annot(fitz.Rect(36, 300, 560, 564))  # Rows 29-41
page2.add_redact_annot(fitz.Rect(36, 604, 560, 800))  # Rows 44-51
page2.apply_redactions()

doc.save("/tmp/Redacted_Statement.pdf")
doc.close()
```

## Pitfalls

- **Coordinate units:** PDF coordinates are in points (1/72 inch), not pixels. Use the same values from `get_text("blocks")` directly.
- **Call `apply_redactions()` per page** after adding all annotations to that page. Multiple pages must each be redacted individually.
- **Password-protected PDFs:** Some bank PDFs are password-protected. The password is often the CRN (Customer Relationship Number). PyMuPDF can open password-protected PDFs: `fitz.open(path, password=password)`.
- **Image-based PDFs:** If the PDF is a scanned image (no extractable text), pymupdf redaction still works visually — the black rectangle is drawn over the image area — but coordinate identification must be done by visual inspection rather than text block extraction.
- **Verify after redaction:** Always do a post-redaction text extraction check to ensure no salary or personal data leaks through.
- **Column alignment:** Bank statement rows often span the full page width (from ~36 to ~560). Use a single wide rectangle per row group rather than multiple narrow ones.

## Related

- `gmail-attachment-to-drive-upload.md` — downloading attachments from Gmail
- `drive-file-upload.md` — uploading the result to Drive
