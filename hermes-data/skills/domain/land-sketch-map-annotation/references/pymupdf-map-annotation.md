# PyMuPDF map annotation — working code recipe

Extracted from the Byadarahalli land-sketch session (Aug 2026). Reproduce-with-modifications.

## 1. Text layer extraction (label coordinates)

```python
import fitz  # or pymupdf
doc = fitz.open("sketch.pdf")
page = doc[0]
wlist = page.get_text("words")  # (x0,y0,x1,y1,word,block,line,word_no)
# Build label center map for target survey numbers:
targets = {'209/1','210','221/2','45/5B','45/P3', ...}
label_pos = {}
for w in wlist:
    if w[4] in targets:
        label_pos.setdefault(w[4], ((w[0]+w[2])/2, (w[1]+w[3])/2))
```

Fallback regex from `pdftotext -layout` dump: `\b\d{1,3}\s*/\s*\d{1,3}[A-Za-z]*\b` catches slash labels; standalone parcel numbers (210, 223) need a separate pattern + position lookup.

## 2. Stroke color detection

```python
drawings = page.get_drawings()
from collections import Counter
col = Counter(str(d.get('color')) for d in drawings)
# Byadarahalli example:
#   (0.663, 0.325, 0.627) magenta/pink = Satvik-owned parcels (1594 strokes)
#   (0.478, 0.686, 0.875) blue          = other parcels          (1390 strokes)
#   (0,0,0) black                        = base boundary lines
```

The map's own colors are ground truth for which parcels belong to the developer. Reuse them.

## 3. Segment extraction — the critical pitfall

`'l'` items are LINE-TO endpoints. A drawing with ONE `('l', Point)` item is a straight
segment whose true endpoints are the RECT CORNERS. Multi-`l` drawings are polylines.

```python
def extract_segments(draw):
    its = draw.get('items', [])
    segs = []
    if len(its) == 1 and its[0][0] == 'l':
        # single-item drawing: rect corners ARE the segment
        r = draw['rect']
        segs.append(((r.x0, r.y0), (r.x1, r.y1)))
    else:
        pts = [it[1] for it in its if it[0] == 'l']
        for i in range(len(pts)-1):
            segs.append(((pts[i].x, pts[i].y), (pts[i+1].x, pts[i+1].y)))
    return segs
```

WRONG version (drops ~70% of strokes): collecting only the `l` points and drawing
consecutive pairs. Correct: 1013 sale segs + 532 agree segs from 1594 pink strokes.

## 4. Stroke→parcel assignment (nearest among TARGET labels, radius-capped)

```python
import math
R = 40
def assign(draw):
    r = draw['rect']
    cx, cy = (r.x0+r.x1)/2, (r.y0+r.y1)/2
    cands = []
    for lbl,(lx,ly) in label_pos.items():
        d = math.hypot(lx-cx, ly-cy)
        if d < R:
            cands.append((d, lbl))
    if not cands: return None, 999
    cands.sort()
    return cands[0][1], cands[0][0]
```

Radius-cap matters: a stroke near an un-targeted label (e.g. standalone "45" text)
would otherwise be dropped. Sort candidates and take nearest.

## 5. Recolor overlay + legend

```python
RED = (0.85, 0.0, 0.05); BLUE = (0.0, 0.2, 0.95)
for (p1,p2) in sale_segs:
    page.draw_line(fitz.Point(p1[0],p1[1]), fitz.Point(p2[0],p2[1]), color=RED, width=2.4)
# same for agree_segs with BLUE
# Add missing label: page.insert_text(fitz.Point(x,y), "190/3", fontsize=10, fontname="helv", color=BLUE)
# Legend: page.draw_rect(...fill=(1,1,1), fill_opacity=0.9) + draw_line samples + insert_text
# fontname MUST be "helv" — helv-bold throws "need font file or buffer" in some builds.
```

## 6. Pixel verification

```python
from PIL import Image
im = Image.open('out.png').convert('RGB')
s = im.width / 595.28  # PDF points -> px at render dpi
def check(x0,y0,x1,y1):
    crop = im.crop((int(x0*s),int(y0*s),int(x1*s),int(y1*s)))
    px = list(crop.getdata())
    red  = sum(1 for r,g,b in px if r>180 and g<90 and b<90)
    blue = sum(1 for r,g,b in px if b>170 and r<90 and g<130)
    return red, blue
```

Use parcel-SIZED regions, not tight label boxes (a 4-acre parcel's boundary can sit
15-30pt from its label; tight boxes give false negatives like "210: red=17").

## Environment notes

- pymupdf may live in a project venv: `find / -name pymupdf -maxdepth 6 -type d` → `/tmp/docenv/lib/python3.13/site-packages/pymupdf`; run with `/tmp/docenv/bin/python3`.
- tesseract with Kannada tessdata (`TESSDATA_PREFIX=/tmp/tessdata ... -l kan+eng`) is the OCR fallback; 450 dpi render + 6x8 overlapping tiles catches raster-drawn labels the text layer misses.
- VPS is RAM-constrained (3.7GB): OCR in SEQUENTIAL jobs, never `xargs -P 8` — parallel tesseract OOM-kills (exit 143/137) and leaves 0-byte outputs.
