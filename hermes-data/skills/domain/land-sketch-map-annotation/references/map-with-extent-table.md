# Single-page map + embedded extent table (Prakash/DRA preferred deliverable)

User requirement (Aug 2026): "PL ADD THE TABLE TO THE MAP ONLY" — the survey-map artifact and the
survey/extent table must be ONE combined page/document. A separate table file was rejected.

## Composite page build (PyMuPDF)

Key pitfall: `page.show_pdf_page(rect, doc, 0)` raises
`ValueError: source document must not equal target` if `doc` is the same document you're
building the composite page in. Fix: annotate the map in the SOURCE doc, save it to an
`io.BytesIO` buffer, reopen it as a NEW `pymupdf` doc, then stamp that into the composite:

```python
import pymupdf, io

src = pymupdf.open(SRC)          # source sketch
page0 = src[0]
# ... annotate page0 (label boxes + legend) ...
buf = io.BytesIO(); src.save(buf); src.close()
map_doc = pymupdf.open(stream=buf.getvalue(), filetype="pdf")

out = pymupdf.open()
PAGE_W = 595.28                    # A4 width
MAP_H = 842.0                      # map stamped at original A4 size
PANEL_H = 490.0                    # table panel height
page = out.new_page(width=PAGE_W, height=MAP_H + PANEL_H)
page.show_pdf_page(pymupdf.Rect(0, 0, PAGE_W, MAP_H), map_doc, 0)
# then draw the table panel starting at y = MAP_H + 18 on `page`
```

Table panel layout that worked: white background rect over the panel area, title line,
subtitle (village/hobli/taluk/district + "1 Acre = 40 Guntas"), then TWO side-by-side
tables (SALE DEEDS left at x≈40, AGREEMENTS right at x≈305, each ~250pt wide, 13.2pt row
height), each with: colored title bar, header row (# / SURVEY / EXTENT / RMK), zebra
striping on even rows, colored TOTAL row, then a shared GRAND TOTAL + net-of-kharab row.
Rows fit: 22 sale rows + 9 agree rows comfortably inside PANEL_H=490.

Render PNG at ~180 dpi for the combined page (tall image, ~1489×3330 px); also render the
map page alone at 300 dpi if a clean map-only PNG is wanted.

## PITFALL: PDF export can lose the table text (PNG is fine)

Observed 2026-08-17: the delivered `byadarahalli_map_with_table.pdf` — composite built by
`page.show_pdf_page(...)` for the map + vector-drawn table panel — rendered the TABLE area
as **empty colored boxes** in real viewers. Symptom signature:
- `pdftotext` spews `Syntax Error: Unknown font tag 'helv'` and `No font in show/space`
- `pdftoppm -r 100/300` + `vision_analyze` of the table crop: sees ONLY bare rectangles
  (title bars, zebra rows, colored TOTAL bars) with **no glyphs at all**
- The PNG render of the SAME composite is perfect — the loss is PDF-export-specific.

Cause: the table text was inserted with `fontname="helv"` on the composite page; the
stamped-map fonts resolve but the inserted helv text is dropped/flattened on PDF write.

**Verify BOTH deliverables:** PNG via pixel-sampling; PDF via `pdftoppm` render + crop +
OCR/vision on the table panel. Do not assume the PDF inherits the PNG's correctness.

**Fix options if PDF text is lost:**
1. Rasterize the table panel to a PNG (`page.get_pixmap(clip=panel_rect)`, or build the
   panel separately and stamp it with `page.insert_image`), then stamp THAT image into
   the composite instead of vector text — text arrives as pixels, cannot be dropped.
2. Or embed a real TTF via `insert_text(fontfile=..., fontname=...)` so glyphs are
   subsetted into the PDF instead of relying on base-14 helv.
3. Or deliver a PDF whose page IS the final composited PNG (wrap image in PDF page).

## Cross-checking the table total against the Documents sheet

When the user asks \"check: is the total 42 acres?\" do NOT just eyeball the GRAND TOTAL
row — recompute item-by-item (sum guntas, 1 acre = 40 guntas) and reconcile scope
differences if another source shows a different total. Known scope delta (Byadarahalli):

- Map table GRAND = 42A 27.08G = SALE 24A 14.08G (22 parcels, EXCLUDES 41/11 0-20G —
  not drawn on sketch) + AGREEMENT 18A 13G (9 parcels, INCLUDES 45/P3/P5/P7 = 10A
  pending-registration parcels).
- Documents sheet (Satvik Byadarahalli Legal Documents) GRAND = 33A 07.08G = SALE
  24A 34.08G (INCLUDES 41/11 0-20G) + AGREEMENT 8A 13G (unique land only; ATS+GPA for
  same survey counted once; EXCLUDES the 10A P-parcels).
- Difference is scope, not error: +20G (41/11) − 10A (P-parcels) in the docs sheet.
  State both totals and the scope delta when the user asks to verify.

## Extent values per survey (Byadarahalli, Satvik / DRA KAAJ)

Authoritative extents come from deeds/RTCs/partition deed; sketch's own extent tokens
(1-00, 2-00, 4-00 …) are the fallback for parcels absent from the deed list (e.g.
45/P3, 45/P5, 45/P7 — pending-registration parcels per partition deed; sketch shows
2-00 / 4-00 / 4-00).

SALE DEEDS (22):  209/1 1-00 · 209/2 1-00 · 209/3 1-00 · 209/4 0-35 · 210 4-00 ·
221/2 3-38 (incl 0-38 kharab) · 175/1 0-25 · 175/4 0-04 · 175/5 0-15 · 175/6 0-20 ·
175/9 0-27 (partition/RTC; deed said 0-25) · 176/2 1-20 · 180 2-05 ·
181 4-00 (incl 0-06 kharab) · 184/5 0-30 · 174/3 1-00 · 219/4 0-07 · 219/5 0-07 ·
219/6 0-05 · 219/7 0-05 · 41/14 0-06 · 41/17 0-05.08
TOTAL 24A 14.08G

AGREEMENTS (9): 45/6 1-00 · 45/5B 2-00 · 223 2-00 · 216/1 1-00 · 216/2 1-00 ·
45/P3 2-00 · 45/P5 4-00 · 45/P7 4-00 · 190/3 1-13
TOTAL 18A 13G

GRAND TOTAL 42A 27.08G; net of kharab (1A 04G) = 41A 23.08G.
1 acre = 40 guntas for all arithmetic.

## Marker recipe (label-only, Aug 2026)

```python
def mark_label(pg, box, color, label):      # box = (x0,y0,x1,y1) of the text word
    x0,y0,x1,y1 = box
    pad = 1.3
    pg.draw_rect(pymupdf.Rect(x0-pad, y0-pad, x1+pad, y1+pad),
                 color=color, fill=color, fill_opacity=0.62, width=1.0)
    fs = max(3.0, (y1-y0) * 1.5)
    pg.insert_text(pymupdf.Point(x0-0.2, y1+0.8), label,
                   fontsize=fs, fontname="helv", color=(0.05,0.05,0.05))
```
RED=(0.85,0,0.05) sale deeds, BLUE=(0,0.2,0.95) agreements.

## Multi-precision verification

- Map: pixel-sample each label box region on the 300-dpi render; expect RED dominance for
  sale boxes, BLUE for agreement boxes. Tight boxes around 12pt radius catch label colors;
  wide 24pt boxes can bleed the neighbor's blue — use the tight box for final call.
- Table: crop the rendered panel and OCR it (tesseract) to confirm TOTAL / GRAND TOTAL rows;
  also crop per-panel columns to verify row alignment.