# Color-Marking Survey Parcels on a Cadastral / Land-Sketch Map

Worked example: Byadarahalli land sketch, Aug 2026 (Satvik Developers → DRA KAAJ).
User sent a survey map PDF and asked: "mark the survey numbers that are sale deeds
vs agreements — different colour or pattern."

## Step 0 — Verify the map is the RIGHT VILLAGE (critical, user-corrected)

The user first sent a "Besthamanahalli Joint Map-Model.pdf". Its title block read
`ಗ್ರಾಮ:-ಬಿಸ್ತಮಾನಹಳ್ಳಿ, ಹೋಬಳಿ:-ಕಸಬಾ, ತಾಲ್ಲೂಕು:-ಆನೇಕಲ್` — Besthamanahalli, Kasaba Hobli,
Anekal Taluk. The survey numbers on it (131/3, 136/1B, 137, 138, 143/3, 145, 146/1,
152/1, 153/2, 158, 160, 162…) did NOT match the Byadarahalli target list (175/1–9,
176/2, 209/1–4, 221/2, 41/14, 45/5B, 45/6, 216, 219/4–7, 180, 181, 184/5, 174/3…).
The user then sent the correct "byadarahalli land sketch" PDF.

**Always OCR/read the map's title block FIRST** (village/hobli/taluk) and grep the
extracted survey tokens against the target list before marking anything. If zero
tokens match, the map is the wrong village — tell the user, don't mark.

## Step 1 — Check for a vector text layer BEFORE OCR

AutoCAD-generated land sketches (`Producer: AutoCAD ... pdfplot16`) have a FULL
vector text layer — every survey number and extent is real text, not pixels.
`pdftotext -layout` returns it cleanly (121 KB of text from one A4 page). OCR
(tesseract) on such maps is nearly useless (tile OCR returned only garbage
fragments like "ರಾಶ ತ / ಹಾ ಬ"). Rule: **pdftotext first; OCR only if it returns
near-zero bytes.**

## Step 2 — Extract survey-number labels WITH coordinates

`pdftotext -layout` gives you the text but not positions. For positions use
PyMuPDF word extraction:

```python
import pymupdf, re
doc = pymupdf.open("map.pdf")
page = doc[0]
words = page.get_text("words")   # (x0, y0, x1, y1, word, block, line, word_no)
pat = re.compile(r'^\d{1,3}/\d{1,3}[A-Za-z]?$')   # 209/1, 45/5B, 41/17, 175/10
labels = []
for w in words:
    if pat.match(w[4]):
        labels.append({'word': w[4], 'x0': w[0], 'y0': w[1], 'x1': w[2], 'y1': w[3]})
```

Also capture STANDALONE parcel numbers the slash-regex misses (210, 223, 180, 181,
45, 218 appear as bare integers on the map). Search for them separately with
`re.fullmatch(r'\d{1,4}[A-Za-z]*', word)` and pick ones whose y-range sits in the
parcel grid.

## Step 3 — Draw color-coded markers directly on the PDF (vector, not raster)

Marking the PDF itself keeps the result crisp at any zoom and lets you re-render
to PNG. Use PyMuPDF `draw_rect` with translucent fill + re-drawn label on top:

```python
def draw_marker(page, box, color, label):
    x0, y0, x1, y1 = box
    pad = 2.0
    rect = pymupdf.Rect(x0-pad, y0-pad, x1+pad, y1+pad)
    page.draw_rect(rect, color=color, fill=color, fill_opacity=0.55, width=0.6)
    page.draw_rect(rect, color=color, width=1.2)                 # border
    fontsize = max(2.5, (y1-y0) * 1.4)
    page.insert_text(pymupdf.Point(x0, y1+0.5), label,           # re-draw label dark
                     fontsize=fontsize, fontname="helv", color=(0.05, 0.05, 0.05))

RED  = (0.85, 0.12, 0.12)   # sale deeds (registered)
BLUE = (0.10, 0.35, 0.90)   # agreements / GPA / ATS
```

Add a legend box (white fill rect + color swatch rects + captions) at a corner
that's clear of the parcel grid (e.g. top-right). Save PDF, then render:

```python
doc.save("map_MARKED.pdf")
pix = page.get_pixmap(dpi=300); pix.save("map_MARKED.png")
```

Deliver BOTH via MEDIA tags (PNG shows inline as photo, PDF for download).

## Step 4 — Verify marker placement by pixel analysis (not OCR)

OCR of tiny marker crops returns nothing (labels are 2.5 pt). Instead, count
colored pixels inside each label's rendered box:

```python
from PIL import Image
im = Image.open('map_MARKED.png').convert('RGB')
s = 2480 / 595.28   # scale = rendered_px_width / page_width_pts (300 DPI A4 → 2480/595.28)
def check(label, x0, y0, x1, y1):
    box = (int(x0*s), int(y0*s), int(x1*s), int(y1*s))
    px = list(im.crop(box).getdata())
    red  = sum(1 for r,g,b in px if r>150 and g<100 and b<100)
    blue = sum(1 for r,g,b in px if b>170 and b>r+30 and b>g+20)
    ...
```

**Pitfall — 55% opacity lightens colors; strict thresholds fail.** The blue marker
at fill_opacity=0.55 composites to ~(128,164,241), so `b>150 and r<100 and g<150`
misses it. Use relational thresholds: `b>170 and b>r+30 and b>g+20`. A marker is
"landed" when its color count exceeds ~20–25% of the box pixels. This caught a
real placement issue: 9/9 sale-deed boxes verified RED, 5/5 agreement boxes BLUE.

## Step 5 — Report parcels NOT on the map

Compare the target survey list against the labels actually found. In the worked
example, 190/3 (agreement) and 41/11 (sale deed) were in the deeds/RTCs but absent
from the sketch's parcel grid — report them explicitly ("not drawn on this sketch;
41/11 sits between 41/10 and 41/12, likely a labeling omission").

## Reference data (Byadarahalli sketch, Aug 2026)

- Sale-deed parcels marked RED: 209/1–4, 210, 221/2, 175/1, 175/4, 175/5, 175/6,
  175/9, 176/2, 180, 181, 184/5, 174/3, 219/4, 219/5, 219/6, 219/7, 41/14, 41/17
- Agreement parcels marked BLUE: 45/6, 45/5B, 223, 216/1, 216/2
- The same sketch also carries extents as labels ("4-00", "1-00", "0-35", "2-0.5")
  and owner names (SATVIK DEVELOPERS, PRAVEEN KUMAR, Hanumanthappa, NINE TRIANGLE
  INFRASTRUCTURE) — useful for spot-checks against deed extents.
