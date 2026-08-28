# PDF Highlighting and Annotation with PyMuPDF

When you need to extract specific sections of a PDF, add highlight annotations,
and compile a new PDF for an email attachment (e.g. highlighting clauses in a
building licence, annotating regulatory conditions, marking up contract terms).

## Use case

The user asks: "Take this PDF, highlight the relevant sections, and attach it
to a draft email." The source PDF is often:
- A **scanned or digitally-signed licence** (A4, readable)
- An **engineering drawing** (A0 size with tiny text)
- A **multi-page report** with conditions on later pages

## Toolchain

```python
import fitz  # PyMuPDF — available in the Hermes .venv
```

## Technique 1: Simple highlight annotations on readable PDFs

For standard A4/letter PDFs where text is already readable:

```python
import fitz

doc = fitz.open("input.pdf")
page = doc[0]

# Search for text bounding boxes
text_instances = page.search_for("BESCOM")
for inst in text_instances:
    annot = page.add_highlight_annot(start=inst[:2], stop=inst[2:])
    annot.set_colors(stroke=[1, 1, 0])   # Yellow
    annot.set_opacity(0.4)
    annot.update()

doc.save("highlighted.pdf")
```

## Technique 2: Extracting a zoomed section from a large-format drawing (A0)

Engineering drawings (sanctioned plans) are typically A0 size (841 x 1189 mm)
with very small text. Direct text search rarely works because the text blocks
are positioned in an entirely different coordinate space from what you'd
expect. Instead, render the relevant region at high resolution and insert it
into a new A4 page:

```python
import fitz

# Open the A0 drawing
src = fitz.open("sanctioned_plan.pdf")
page = src[0]  # A0 page

# Clip the region containing the conditions list
# Coordinates were found by inspecting page.get_text("blocks")
# and locating the block with the target text
clip = fitz.Rect(1450, 1750, 2400, 2700)
pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=clip)

# Create new A4 document
doc = fitz.open()
out = doc.new_page(width=595, height=842)
image_bytes = pix.tobytes("png")
out.insert_image(out.rect, stream=image_bytes)

# Add highlight over the relevant text region
# (approximate pixel coords on the rendered A4 page)
hl = fitz.Rect(30, 250, 565, 320)
annot = out.add_highlight_annot(start=hl.tl, stop=hl.br)
annot.set_colors(stroke=[1, 1, 0])
annot.set_opacity(0.4)
annot.update()

# Add a text annotation/note beside the highlight
note = out.add_text_annot(
    (300, 340),
    "Condition #4: Development charges to BESCOM/BWSSB 'if any' — not an NOC."
)
note.set_colors(stroke=[1, 0.6, 0])
note.update()

doc.save("highlighted.pdf")
```

## Technique 3: Combining pages from multiple PDFs

When the evidence spans multiple documents (licence cover page from one PDF,
conditions from another):

```python
doc_out = fitz.open()
doc_a = fitz.open("licence.pdf")
doc_b = fitz.open("sanctioned_plan.pdf")

# Copy specific pages
doc_out.insert_pdf(doc_a, from_page=0, to_page=0)  # licence page 1
doc_out.insert_pdf(doc_b, from_page=1, to_page=1)  # conditions page

# Insert a rendered clip from an A0 page as an image page
page_b0 = doc_b[0]
clip = fitz.Rect(1450, 1750, 2400, 2700)
pix = page_b0.get_pixmap(matrix=fitz.Matrix(3, 3), clip=clip)
img_page = doc_out.new_page(width=595, height=842)
img_page.insert_image(img_page.rect, stream=pix.tobytes("png"))

doc_out.save("combined_highlighted.pdf")
doc_out.close()
```

## Pitfalls

1. **A0 coordinate detection**: `page.get_text("blocks")` returns absolute
   coordinates on the A0 canvas. Text you see in the top-right of the drawing
   may have y=1800+, not y=100. Always print all blocks and look for a text
   snippet to locate the right region.

2. **search_for() on A0 drawings**: `page.search_for("BESCOM")` will find the
   text but return coords in A0-units, not A4-units. If you add a highlight
   annotation using those coords on a zoomed-in rendered page, the highlight
   won't align. Safer to use the clip-and-render approach (Technique 2) and
   add highlights at approximate pixel positions on the output A4 page.

3. **Annotation opacity**: `set_opacity(0.4)` keeps the highlight visible
   without obscuring the underlying text. Higher opacity may make text
   unreadable when printed.

4. **Text annotations vs highlight annotations**: `add_text_annot()` creates
   a clickable speech-bubble icon that expands on hover. `add_highlight_annot()`
   is a transparent color overlay. Use both — highlights for the key text,
   text annotations for explanatory notes about *why* it's highlighted.

5. **Base64 encoding for MIME attachment**: After creating the PDF, attach it
   to an email via the MIMEMultipart pattern:
   ```python
   with open("highlighted.pdf", "rb") as f:
       part = MIMEBase("application", "pdf")
       part.set_payload(f.read())
       encoders.encode_base64(part)
       part.add_header("Content-Disposition", "attachment",
                       filename="Highlighted_Document.pdf")
   ```
