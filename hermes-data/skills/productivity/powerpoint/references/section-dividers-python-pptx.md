# Section Divider Slides in python-pptx

Create styled category section divider slides and insert them at the correct position in an existing presentation.

## Use Case

You have an existing .pptx deck with 40 project slides grouped by category (Villas, Apartments, Plotted Developments). You want to add visual separator/divider slides between each category section — with custom background, category badge, title, and project count.

## Technique: Blank Layout + Full Custom Shapes

Since section dividers have a unique layout (not matching any existing slide layout), use the **Blank layout** (index 6) and add all elements programmatically.

### Step 1: Create the Section Divider Slide

```python
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation('deck.pptx')
slide_layout = prs.slide_layouts[6]  # Blank
slide = prs.slides.add_slide(slide_layout)

# 1. Background fill
bg = slide.background.fill
bg.solid()
bg.fore_color.rgb = RGBColor(0x0D, 0x2B, 0x3E)  # Dark navy

# 2. Top accent line (gold bar across full width)
accent = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE,
    Emu(0), Emu(0), prs.slide_width, Emu(50000)  # 5pt high
)
accent.fill.solid()
accent.fill.fore_color.rgb = RGBColor(0xE8, 0x9C, 0x31)  # Gold
accent.line.fill.background()

# 3. Category badge (rounded rectangle, gold fill)
badge = slide.shapes.add_shape(
    MSO_SHAPE.ROUNDED_RECTANGLE,
    Emu(685800), Emu(1600000), Emu(2000000), Emu(450000)
)
badge.fill.solid()
badge.fill.fore_color.rgb = RGBColor(0xE8, 0x9C, 0x31)
badge.line.fill.background()
tf = badge.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "VILLAS"  # or "APARTMENTS", "PLOTTED DEVELOPMENTS"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = RGBColor(0x0D, 0x2B, 0x3E)
p.alignment = PP_ALIGN.CENTER

# 4. Main title
tb = slide.shapes.add_textbox(Emu(685800), Emu(2200000), Emu(8800000), Emu(900000))
tf = tb.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Villas — Sarjapur Corridor"
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

# 5. Subtitle
tb = slide.shapes.add_textbox(Emu(685800), Emu(3100000), Emu(8800000), Emu(600000))
tf = tb.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Independent & Luxury Villa Developments — Sarjapur Corridor"
p.font.size = Pt(18)
p.font.color.rgb = RGBColor(0xBB, 0xBB, 0xBB)

# 6. Project count
tb = slide.shapes.add_textbox(Emu(685800), Emu(3800000), Emu(2800000), Emu(500000))
tf = tb.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "📊 16 Projects"
p.font.size = Pt(14)
p.font.color.rgb = RGBColor(0xE8, 0x9C, 0x31)
```

### Step 2: Reorder Slides via XML Manipulation

python-pptx's `add_slide()` always appends to the end. To insert a slide at a specific position, manipulate the `_sldIdLst` XML element directly:

```python
from lxml import etree
from copy import deepcopy

# After creating all new slides (they're at the end of the list)
sldIdLst = prs.slides._sldIdLst
sldId_elements = list(sldIdLst)

# Identify new vs existing slides.
# If you created N new slides, they're the last N elements:
new_count = 3
new_elements = sldId_elements[-new_count:]
rest_elements = sldId_elements[:-new_count]

# Target insertion positions (0-based in the original rest list):
# After element at index 1 (slide 2) → Villas divider
# After element at index 17 (slide 18) → Apartments divider
# After element at index 29 (slide 30) → Plotted divider
insert_after = [1, 17, 29]

# Build new order. Insert in REVERSE to preserve indices:
result = list(rest_elements)
for pos, elem in reversed(list(zip(insert_after, new_elements))):
    result.insert(pos + 1, elem)  # +1 because we insert AFTER, not AT

# Replace the entire sldIdLst content
for elem in sldId_elements:
    sldIdLst.remove(elem)
for elem in result:
    sldIdLst.append(elem)

# Save
prs.save('deck_with_sections.pptx')
```

### Pitfalls

| Pitfall | Solution |
|---------|----------|
| **Slides appended at end, not in correct position** | python-pptx has no `insert_slide()` method. Must use XML reordering via `_sldIdLst` as shown above. |
| **Index shift when inserting multiple slides** | After the first insertion, all subsequent indices shift. Insert in **reverse order** (last target position first). |
| **Section divider after first project instead of before** | Your `insert_after` index was off by 1. If the first category project is at slide index 2, insert_after should be 1 (after slide 2, which is at index 1). |
| **`Truth-testing of elements` FutureWarning** | Use `len(elem)` or `elem is not None` instead of bare `if elem:` when checking lxml elements. |
| **Slide background reverts to theme default** | Set background fill on the slide object immediately after creating it, before adding shapes. If it persists, check if the Blank layout has a theme background override. |
| **Shapes positions in EMU** | 1 inch = 914400 EMU. Use `Emu()` for readability. `Emu(685800)` = 0.75", `Emu(1600000)` ≈ 1.75". |

### When to Use vs Alternatives

- **Section divider slides** → Use this technique when you're working with an existing PPTX and can't enable the Slides API.
- **Section dividers via Google Slides API** → If the API is enabled, use `batchUpdate` with `createSlide` requests and insert at specific indices. Simpler, no XML manipulation needed.
- **Section dividers in pptxgenjs** → If creating from scratch, just order slides in the correct sequence during generation — no reordering needed.

## Complete Workflow: Modify PPTX + Convert to Google Slides

When the Slides API is disabled but you need to update a Google Slides presentation:

```
1. Download existing PPTX from Drive → 2. Modify with python-pptx 
→ 3. Upload back to Drive (update existing PPTX) 
→ 4. Drive API import: create new Google Slides file from PPTX

Step 4 uses the Drive files().create() endpoint with 
mimeType='application/vnd.google-apps.presentation' 
and the PPTX as the media body. This converts it to native 
Google Slides without needing the Slides API.
```

See `references/drive-upload-conversion.md` for the upload/import details.
See `references/edit-existing-google-slides-pptx.md` for the overall download-edit-upload workflow.
