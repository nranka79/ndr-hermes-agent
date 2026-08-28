# Integrating Land Survey Sketches into Villa Market Research Presentations

## When to Use

The user sends a government land survey sketch (photograph, scan, or PDF of a survey map) and asks you to "add this sketch to the presentation" — typically a villa/plotted development market research deck.

The sketch is usually:
- A **Karnataka survey compilation map** showing multiple survey numbers across villages
- A **Podi / Hissa / Akarband** document from the Tahsildar's office
- A **layout plan** with marked plots, access roads, and boundaries

## Workflow

### Step 1: Analyze the Sketch with Vision/OCR

```python
vision_analyze(image_url="/path/to/sketch.jpg",
               question="Analyze this survey land sketch in detail.
                         Identify: 1) Village and taluk names
                         2) Survey numbers marked
                         3) Any land measurements
                         4) Overall shape and boundaries
                         5) Developer/owner names mentioned
                         6) Roads or access paths shown",
               also_describe_visually=True)
```

**Key data to extract:**
- **Administrative info**: District, Taluk, Hobli, Village names
- **Survey numbers**: Individual Sy. No. values and their subdivisions
- **Ownership**: Names of owners, developers mentioned (e.g. "Trishul Bulltech & Infrastructures Pvt", "Satvik Developers")
- **Land markings**: Total extent, government land parcels, access roads
- **Boundary context**: Adjacent features (roads, nalas, government land, neighboring villages)

### Step 2: Capture Important Context from the Sketch

From the OCR + visual analysis, compile a structured metadata card:

```
Location: Village, Hobli, Taluk, District
Survey Numbers: [list of visible Sy. No.]
Developer/Owner: [names found]
Key Features: [roads, boundaries, govt land, access points]
Special Markings: [e.g. "To Be Procured", phase markers]
```

### Step 3: Add the Sketch as a Presentation Slide

In the python-pptx deck, create a dedicated slide for the sketch:

```python
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import os

def add_sketch_slide(prs, sketch_path, sketch_data, blank_layout, palette):
    """
    Add a slide with the survey sketch on the left and annotations on the right.
    
    sketch_data = {
        'title': 'Land Survey Sketch',
        'subtitle': 'Village, Taluk — District',
        'details': ['Detail 1', 'Detail 2', ...],
        'notes': ['Note 1', 'Note 2', ...]
    }
    palette = {'bg': DARK_BG, 'gold': GOLD, 'white': WHITE, 'light': LIGHT}
    """
    slide = prs.slides.add_slide(blank_layout)
    
    # Dark background
    bg = prs.slides[0].background
    # ... (add dark background as in base template)
    
    # Title
    T(slide, 0.5, 0.3, 12, 0.5, f"🗺️ {sketch_data['title']}", 
      28, True, palette['white'])
    T(slide, 0.5, 0.9, 12, 0.3, sketch_data['subtitle'],
      14, False, palette['gold'])
    
    # Sketch image on the left (wider portion)
    if os.path.exists(sketch_path):
        slide.shapes.add_picture(sketch_path, 
                                 Inches(0.8), Inches(1.5), 
                                 Inches(7.5), Inches(5.5))
    
    # Annotations panel on the right
    R(slide, 8.8, 1.5, 4.0, 5.5, fill=palette.get('card', RGBColor(0x25,0x25,0x3D)))
    T(slide, 8.8, 1.6, 3.8, 0.4, "🔍 Sketch Details:", 
      16, True, palette['gold'])
    
    # Details as bullet list
    y = 2.1
    for item in sketch_data['details']:
        T(slide, 8.8, y, 3.8, 0.3, f"• {item}", 
          11, False, palette['light'])
        y += 0.28
    
    # Notes section
    if sketch_data.get('notes'):
        T(slide, 8.8, y + 0.3, 3.8, 0.3, "📌 Notes:",
          14, True, palette['gold'])
        for note in sketch_data['notes']:
            y += 0.32
            T(slide, 8.8, y, 3.8, 0.3, f"• {note}",
              10, False, palette['light'])
```

### Step 4: Structure the Metadata for the Annotation Panel

Extract from the vision analysis and present as clean bullet points:

```python
sketch_data = {
    "title": "LAND SURVEY SKETCH",
    "subtitle": "Byadarahalli & Gundlahalli Villages — Devanahalli Taluk",
    "details": [
        "District: Bengaluru Rural",
        "Taluk: Devanahalli",
        "Hobli: Kundana / Kasaba",
        "Villages: Byadarahalli + Gundlahalli",
        "",
        "Notable Markings:",
        "• Multiple survey numbers marked",
        "• Ownership boundaries shown",
        "• Adjacent to Govt land parcels",
        "• Road access paths visible",
    ],
    "notes": [
        "Developer Mentioned:",
        "• Trishul Bulltech & Infrastructures Pvt",
        "• Satvik Developers (To Be Procured)",
    ]
}
```

### Step 5: Insert into an Existing .pptx (Post-Hoc Modification)

When the presentation was already built and saved as .pptx, and the user sends the sketch afterwards, you must insert the image into the existing file — you don't rebuild from scratch.

**Technique — add slide at end, then reorder via XML:**

```python
from pptx import Presentation
from pptx.util import Emu

PPTX_PATH = '/path/to/existing_deck.pptx'
IMAGE_PATH = '/path/to/sketch.jpg'

prs = Presentation(PPTX_PATH)
BLANK = prs.slide_layouts[6]

# Step 1: Create the new slide at the end
new_slide = prs.slides.add_slide(BLANK)
# ... add background, title, image, annotations ...

img = new_slide.shapes.add_picture(IMAGE_PATH,
                                    Emu(300000), Emu(800000),
                                    Emu(11400000), Emu(4200000))

# Step 2: Reorder — move the new slide to desired position
new_idx = 3  # target position (0-indexed), e.g. after Location slide at index 2
sldIdLst = prs.slides._sldIdLst
new_slide_elem = sldIdLst[-1]  # newly added slide is last in the list
sldIdLst.remove(new_slide_elem)
sldIdLst.insert(new_idx, new_slide_elem)

# Step 3: Save
prs.save(PPTX_PATH)
```

**Key points:**
- `sldIdLst[-1]` reliably identifies the freshly added slide
- Remove then re-insert at target position — the XML `<sldIdLst>` element order determines slide order
- Target index is 0-based: index 2 = after Location slide
- Always save to the same path or a new file
- The slide layout is already part of the presentation, so `BLANK = prs.slide_layouts[6]` works

### Step 6: Position the Sketch Slide in the Deck

The sketch belongs after the Subject Land Overview slide and before the Location USP slide — it provides the legal/administrative foundation for the land:

For a standard **Land Proposal Evaluation** deck (22-slide pattern), insert at position 3 (after Location slide):
- 1: Title
- 2: Land Proposal Overview
- 3: Location & Connectivity
- **4: Survey Sketch** ← INSERTED HERE
- 5: Development Potential Analysis
  
For a **Villa Market Research** deck, insert at position 2 (after Subject Land Overview):
- 1: Title
- 2: Subject Land Overview
- **3: Survey Sketch** ← INSERTED HERE
- 4: Location USP

```python
# Slide order after adding:
# 1. Title
# 2. Subject Land Overview     ← inserted index 1
# 3. Survey Land Sketch         ← THIS SLIDE (index 2)
# 4. Location USP                ← index 3
# 5+ Villa / Plotted slides
```

## Worked Example (from Thylagere session, Jul 2026)

**Input:** A photograph/scan of a government survey compilation map.

**Vision analysis extracted:**
- District: Bengaluru Rural
- Taluk: Devanahalli
- Villages: Byadarahalli (Hobli: Kundana) + Gundlahalli (Hobli: Kasaba)
- Developer: Trishul Bulltech & Infrastructures Pvt
- Status: "To Be Procured" — Satvik Developers
- Multiple survey numbers spanning two village boundaries
- Access roads and government land parcels visible

**Resulting slide:** 7.5" wide sketch image on the left, 4" annotation panel on the right with structured details.

## Pitfalls

- **PDF source**: If the user sends a PDF instead of an image, convert first. Tools available:
  - `pdftoppm -png -r 300 input.pdf /tmp/sketch_page` (fastest, best quality — from `poppler-utils`)
  - `gs -dNOPAUSE -dBATCH -sDEVICE=png16m -r200 -sOutputFile=/tmp/sketch.png input.pdf` (ghostscript fallback when poppler unavailable)
  - `mutool draw -o /tmp/sketch.png -r 200 input.pdf` (mupdf, alternative)
- **Low resolution**: Phone photos of survey maps can be blurry. Ask for a higher-res scan if the OCR returns gibberish.
- **Kannada/Tamil text**: Government sketches often use Kannada for headings and English for measurements. Use `also_describe_visually=True` to get both text extraction AND visual descriptions of spatial layout.
- **Large images**: Survey maps can be very large (14,000+ px). The vision tool handles this, but the PPTX image embedding may need compression. Stick to the original JPG unless it exceeds slide boundaries — then resize before adding.
- **Multiple pages**: The sketch may span multiple images. Process each page separately and add the most informative one to the deck.
- **"To Be Procured" annotations**: These indicate land under negotiation/acquisition — important context for the development timeline. Highlight this in the notes section.
- **Coordinate accuracy**: The survey sketch shows relative positions, not precise GPS coordinates. Use the My Maps center coordinate for the slide's location reference, not positions measured from the sketch.

## Hand-drawn joint sketch photos (user-photographed notebook sketches)

Different from government survey maps: the user often sends a phone photo of a hand-drawn joint sketch on a notebook page (Nandi Hills ← Thylagere clone, Aug 2026). These need special handling:

### 1. The drawing is usually rotated ~90° inside the photo

The photo is often portrait but the sketch was drawn landscape (or vice-versa) — the vision tool will report "the drawing is rotated ~90° clockwise, the top of the drawing points right/left". **Do not embed the raw photo** — it looks cramped and cut off on a landscape slide.

Detect orientation with vision first (ask: "is the drawing upright? which way does the north arrow / plot numbers point?"), then rotate with PIL:

```python
from PIL import Image
im = Image.open('sketch.jpg')
# If vision says the drawing's TOP points RIGHT in the photo → rotate CCW (rotate(-90))
# If vision says the drawing's TOP points LEFT → rotate CW (rotate(90))
rot = im.rotate(-90, expand=True)   # direction depends on the vision finding
rot.save('sketch_upright.jpg', quality=92)
```

**Verify the rotation with vision_analyze before embedding** — the first rotation guess can be backwards (180° off). The upright check: plot numbers read normally, north arrow points up, and you can count the plots consistently (a rotated sketch made plots look like 1–6; upright they were clearly 1–7).

### 2. Survey details must not be fabricated

Hand sketches show **plot numbers (1, 2, 3...)** and dimensions, NOT official survey numbers. When building the SURVEY DETAILS card:
- `"Survey Numbers: As per joint sketch — Plots 1–7 (scale 1\" = 100')"` — verifiable from the sketch.
- **Never invent survey numbers** just because the template slide had a survey-number line. If the numbers aren't legible, say so.
- Do NOT carry over the old parcel's survey numbers when cloning a deck for an adjacent parcel — each land has its own.

### 3. Sketch image placement on the slide

Fit the upright image inside a target box (not the old picture's box — that may be a different aspect ratio):

```python
from PIL import Image
img = Image.open('sketch_upright.jpg')
iw, ih = img.size
target_w = int(slide_width * 0.52)
target_h = int(slide_height * 0.80)
scale = min(target_w / iw, target_h / ih)
new_w, new_h = int(iw * scale), int(ih * scale)
slide.shapes.add_picture('sketch_upright.jpg', left, top, new_w, new_h)
```

After upload, export the deck to PDF and vision-check the sketch slide: upright, not cropped at edges, no text overlap.
