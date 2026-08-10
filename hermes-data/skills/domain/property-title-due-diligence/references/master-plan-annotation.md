# Master Plan PDF — Circling Plots on Revised/Renumbered Plans

Context: DRAAS sends revised layout PDFs (e.g. Oasis Master Plan 03.08.26) where plot
LOCATIONS stay the same but NUMBERS change (old 105/107/109 + 95/93 become MERGED PAIRS
105-106, 107-108, 109-110, 95-96, 93-94; 119/118/117/92 keep numbers). Task: circle the
same physical plots as on the previous plan, at their NEW numbers.

## Workflow

1. Save the uploaded PDF (it lands in /data/hermes/document_cache/).
2. Extract text labels + coordinates:
   ```
   pdftotext -bbox plan.pdf plan_bbox.html   # word coords in DISPLAY space
   pdftotext -layout plan.pdf plan_text.txt
   ```
   Note: pdftotext -bbox already reports coordinates in the page's DISPLAY space
   (rotation applied). For a /Rotate 270 page, x/y here match what you see rendered.
3. Render for OCR ground truth:
   ```
   pdftoppm -png -r 100 plan.pdf plan_render   # 100 dpi
   tesseract plan_render-1.png out_ocr --psm 11 tsv
   ```
   Parse the TSV (csv.DictReader with tab delimiter) to get label pixel positions.
   Use these to verify/denoise pdftotext coords. Plot label rows are ~42px apart at
   100dpi (cell height ~41px) — any radius > ~18px in image space bleeds into
   neighbor labels.
4. Map old → new numbers by POSITION (same physical spots). Read merged-pair labels
   like "105-106" as single combined plots.

## CRITICAL PITFALL — PyMuPDF rotated pages

`page.draw_circle()` / `draw_*` on a rotated page (page.rotation == 270, MediaBox
1684x1191, rect 1191x1684) uses **UNROTATED page coordinates**, NOT the display space
that pdftotext -bbox reports. Drawing circles from pdftotext coords lands them
rotated ~90° off target (invisible on the intended plots).

**Fix:** get label positions from PyMuPDF itself, then draw at those exact coords:
```python
import fitz
doc = fitz.open('plan.pdf')
page = doc[0]
words = page.get_text('words')   # (x0,y0,x1,y1,word) in the space draw_* uses
# find target labels, draw circle at center:
page.draw_circle(fitz.Point(cx, cy), r, color=(0.86,0.12,0.12), width=2.5)
doc.save(out, deflate=True, garbage=3)
```
Radius: r = label height * 2 is a good visual fit (keeps clear of neighbors).

## CRITICAL PITFALL — deliverable format

A PDF made by rasterizing the marked PNG (PIL `img.save('x.pdf','PDF')`) will NOT open
on the user's phone. ALWAYS draw vector circles on the ORIGINAL PDF via PyMuPDF and
deliver that. (PIL path = single embedded raster page; phone viewers choke on it.)

## Verification (do all three)

1. **Containment check** — after drawing, re-open and confirm no OTHER label's word
   bbox falls inside a circle (compare against get_text('words')).
2. **Pixel-diff** — render marked PDF via pdftoppm, diff red pixels vs original render:
   added red should cluster ONLY in the villa block region at expected label centers
   (window ±25px, count > 30 per circle = OK).
3. **Vision spot-check** on a zoomed crop of the target block; note OCR/vision models
   misread overlapping red strokes — trust the pixel-diff as ground truth.

## Environment notes

- The skills bridge / gws_skill_bridge and skills dir may be permission-denied under
  /data/hermes; set `HERMES_HOME=/opt/hermes` when running python that imports
  `tools.gws_skill_bridge` (e.g. drive_search to verify asset links before emailing).
- `&` inside numpy expressions in inline `python3 -c` trips the terminal backgrounding
  guard — write the script to a file and run it instead.
- pymupdf is not in the base venv: `uv pip install --python /opt/hermes/.venv/bin/python pymupdf`.
