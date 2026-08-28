# Adding Survey/PDF Sketches to Presentations

**Purpose:** Insert a survey sketch, joint sketch, or site map (received as PDF) into a Google Slides presentation.

## Workflow

### Step 1: Get the PDF
PDFs arrive via Telegram → `/data/hermes/document_cache/doc_*`. The user's message typically mentions the saved path.

### Step 2: Convert PDF to Image
```bash
# pdftoppm (best)
pdftoppm -png -r 300 input.pdf /tmp/sketch_hi

# Ghostscript (fallback)
gs -dNOPAUSE -dBATCH -sDEVICE=png16m -r200 -sOutputFile=/tmp/sketch.png input.pdf
```

### Step 3: Resize for Slides
```python
from PIL import Image
img = Image.open('/tmp/sketch_hi-1.png')
w, h = img.size
scale = 3600 / w
new_w, new_h = int(w * scale), int(h * scale)
img_resized = img.resize((new_w, new_h), Image.LANCZOS)
img_resized.save('/tmp/sketch_for_slides.png', quality=95)
```

### Step 4: Insert into .pptx
```python
from pptx import Presentation
from pptx.util import Emu
prs = Presentation('/tmp/deck.pptx')
BLANK = prs.slide_layouts[6]
slide = prs.slides.add_slide(BLANK)
slide.shapes.add_picture('/tmp/sketch_for_slides.png', Emu(500000), Emu(800000), Emu(11000000), Emu(4400000))
# Reorder: sldIdLst = prs.slides._sldIdLst; last = sldIdLst[-1]; sldIdLst.remove(last); sldIdLst.insert(N, last)
```

### Step 5: Upload (Slides API disabled fallback)
1. Drive export → download as .pptx
2. python-pptx modifications
3. Upload .pptx → copy with GS mime type conversion → share → delete intermediate

## Sketch Slide Layout (DRA Dark Theme)
- Gold header bar, title "SITE SURVEY — Name" (22pt), subtitle (12pt)
- Image, annotation card with area, boundaries, date, scale, features
