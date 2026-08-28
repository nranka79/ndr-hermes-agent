---
name: pdf-redaction
description: "Selective redaction of PDF content by keeping specific zones (header, target rows) and blacking out everything else. Produces a flattened image-based PDF where redacted areas are unrecoverable."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [PDF, redaction, privacy, bank-statements, image-redaction]
    related_skills: [ocr-and-documents]
---

# PDF Selective Redaction

Redact a PDF by keeping specific rows (e.g., salary credits in a bank statement) and blacking out everything else. Two approaches available:

| Approach | Speed | Precision | Output | When to Use |
|----------|-------|-----------|--------|-------------|
| **pymupdf native** (primary) | Fast | Exact (text block coordinates) | True PDF with annotations | Most cases — bank statements, invoices, structured docs |
| **Image-based** (fallback) | Slow | Approximate (pixel coords) | Flattened image PDF | Scanned PDFs, complex layouts, text-extraction failures |

---

## Primary Approach: pymupdf Native Annotations

Uses `fitz` (pymupdf) to add redaction annotations and apply them directly — text is physically removed, not just overlaid.

### 1. Parse text blocks with coordinates

```python
import fitz
doc = fitz.open("/path/to/input.pdf")
for page_num in range(len(doc)):
    page = doc[page_num]
    blocks = page.get_text("blocks")
    for b in blocks:
        x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4]
        print(f"  ({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f}): {text.strip()[:80]}")
```

### 2. Add redaction annotations + apply

```python
page = doc[page_num]
page.add_redact_annot(fitz.Rect(x0, y0, x1, y1))  # zone to remove
page.apply_redactions()                              # physically remove text
doc.save("/tmp/redacted.pdf")
```

**Key insight:** Draw ONE large rectangle covering multiple consecutive rows rather than one per row — fewer annotations, cleaner output. Use page-width margins (e.g. `36` to `560`) for full-width redaction.

### 3. Worked example: Bank statement with only salary rows visible

```python
import fitz

doc = fitz.open("/path/to/statement.pdf")

# Page 1: keep header (0-390), keep O3 salary row (466-485), black out rest
doc[0].add_redact_annot(fitz.Rect(36, 393, 560, 464))   # rows 1-4
doc[0].add_redact_annot(fitz.Rect(36, 485, 560, 800))   # rows 6-20
doc[0].apply_redactions()

# Page 2: keep header + O3 salary (282-300) + Southcity/DRA salary (566-604)
doc[1].add_redact_annot(fitz.Rect(36, 128, 560, 280))   # rows 21-27
doc[1].add_redact_annot(fitz.Rect(36, 300, 560, 315))   # row 29
doc[1].add_redact_annot(fitz.Rect(36, 315, 560, 564))   # rows 30-41
doc[1].add_redact_annot(fitz.Rect(36, 604, 560, 800))   # rows 44-51
doc[1].apply_redactions()

doc.save("/tmp/redacted.pdf")
```

---

## Pattern: Identifying salary rows in bank statements

1. Extract all text via `page.get_text()` — look for employer names in descriptions
2. Identify salary patterns: NEFT/RTGS/IMPS deposits from known employers (O3 Infotech, DRA Projects, Southcity Properties, etc.)
3. Record row coordinates from text blocks
4. Always keep: page header, column headers, opening balance, salary rows, closing summary
5. **Ask user to confirm** which rows are salary before redacting — don't assume

---

## Fallback: Image-Based Redaction

Use when the PDF is scanned/image-only. See `references/kotak-bajaj-redaction-may2026.md` for the full image-based workflow.

## Step 1: Render PDF pages to images

```python
from pdf2image import convert_from_path

pages = convert_from_path("/path/to/input.pdf", dpi=150)
for i, page in enumerate(pages):
    out_path = f"/tmp/redaction_work/page_{i+1}.jpg"
    page.save(out_path, "JPEG", quality=85)
    print(f"Page {i+1}: {page.size}")
```

**⚠️ Use pdf2image, NOT pdftoppm** — pdftoppm is not available in the sandbox (no `/usr/bin` in PATH).

## Step 2: Identify target pages and keep zones

Use `vision_analyze` with `google/gemini-2.5-flash-image` to identify:
- The page(s) containing entries to keep
- The exact y-range of each keep zone (header + target rows)

```python
# After rendering, call vision_analyze on each page
# Ask: "Is there a BAJAJ ALLIANZ entry on this page? What is the y-coordinate of that row?"
```

**Common keep zones in bank statements:**
- Header (account name, bank, statement period): y≈0 to y≈100
- Transaction rows: y≈100 to y≈1600 (depends on statement length)
- Footer: y≈1600+

**Critical: Verify coordinates against actual page pixels**
- Vision models misidentify coordinates when the page has dense tables or similar-looking entries appear on multiple pages
- Always save a crop of the suspected keep zone and verify visually before applying redaction
- If coordinates are wrong, redaction will produce black bars with blank white strips (wrong zone kept) or visible Bajaj rows blacked out (wrong zone redacted)

## Step 3: Build redaction masks per page

```python
from PIL import Image
import os

os.makedirs("/tmp/redaction_work/output", exist_ok=True)

def redact_page(input_path, keep_zones, output_path):
    """
    keep_zones: list of (y_top, y_bottom) tuples — these remain white (visible)
    Everything else gets black.
    """
    img = Image.open(input_path)
    w, h = img.size
    
    # Create RGBA layer for redaction (black with transparent keep zones)
    redact = Image.new('RGBA', (w, h), (0, 0, 0, 255))  # full black
    
    # Punch white holes for keep zones
    for (y_top, y_bottom) in keep_zones:
        # Create white rectangle
        white = Image.new('RGBA', (w, y_bottom - y_top), (255, 255, 255, 255))
        redact.paste(white, (0, y_top))
    
    # Composite: redact on top of original
    result = Image.alpha_composite(img.convert('RGBA'), redact)
    result.convert('RGB').save(output_path, 'JPEG', quality=90)
    print(f"Saved: {output_path}")
```

**Keep zone examples from this session:**
- Page 3 Bajaj debit: y=1480 to y=1575 (with margin)
- Page 8 Bajaj credit: y=790 to y=890 (suspected — verify before use)

## Step 4: Combine into final PDF

```python
from PIL import Image
import pymupdf

output_images = sorted([
    f"/tmp/redaction_work/output/page_{i}.jpg"
    for i in range(1, total_pages + 1)
])

pdf = pymupdf.open()
for img_path in output_images:
    img = Image.open(img_path)
    w, h = img.size
    # Use RGB for PDF embedding
    pdf_page = pdf.new_page(width=w, height=h)
    pdf_page.insert_image(pymupdf.Rect(0, 0, w, h), stream=open(img_path, 'rb').read())
pdf.save("/tmp/redaction_work/final_redacted.pdf")
print("Final PDF saved")
```

## Coordinate Verification Pattern

When vision keeps misidentifying which page contains the target entry:
1. Save a crop of the suspected zone: `img.crop((0, y-30, w, y+60)).save("/tmp/crop.jpg")`
2. Call vision_analyze on the crop: "Does this show [ENTRY NAME]? What row is this?"
3. If yes, use those coordinates; if no, scan adjacent pages

**Never trust filename-based assumptions** — a PDF named with the target entity (Bajaj) may have the entry on page 3, while page 8 has a different entity with the same name. Verify every coordinate against pixel crops.

## Critical: Vision Coordinates Fail on Dense Tables — Know When to Stop

Vision models consistently misidentify y-coordinates when:
- The page has dense multi-row transaction tables
- Similar-looking entries appear on multiple pages (e.g., same entity name on different page numbers)
- Handwritten annotations mix with printed text

**Symptoms of coordinate failure:**
- Black bars with blank white strips where content should be visible (keep zone missed the text)
- Target rows incorrectly blacked out (keep zone was too high)
- Vision reports different page numbers across multiple analysis runs for the same entry
- Crop verification shows the keep zone saved but the visible content doesn't match

**Decision rule:** After 2 failed redaction attempts with wrong coordinates, STOP. Offer to extract the target pages as a clean PDF and let the user handle the visual redaction themselves. This is faster and more accurate than continuing.

**Trigger for immediate extraction:** When vision gives inconsistent page/location results across multiple calls (e.g., page 8 Bajaj credit confirmed at y=790 then later reported at different y-range), that's the signal to abandon automated redaction — not continue to a 3rd attempt.

**The "just give me the PDF" pattern:**
When the user says "I'll redact it myself" or similar — immediately extract the target pages as a new PDF and deliver. Do not keep trying to automate the redaction.

```python
# Fast page extraction with pymupdf (when user wants to self-redact)
import fitz

src = fitz.open("/path/to/input.pdf")
out = fitz.open()
for page_num in [2, 7]:  # 0-indexed
    out.insert_pdf(src, from_page=page_num, to_page=page_num)
out.save("/tmp/target_pages.pdf")
out.close()
src.close()
```

## Security Note

This produces an image-based PDF. It is NOT searchable text — all redacted areas are true blanks with no recoverable text layer. For true PDF-layer redaction (remove text objects, not just overlay), use `pymupdf`'s annotation-based redaction API or dedicated tools like `pdf-redact-tool`. Image-based redaction is sufficient for external sharing (email, WhatsApp, regulatory submissions where only the target entries matter).