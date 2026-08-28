# Editing Existing Google Slides via PPTX Round-Trip

Use when the Google Slides API is **disabled** for the GCP project (returns `HttpError 403: Google Slides API has not been used in project...`), or when you need a bulk find-and-replace across many slides and the Slides API batchUpdate is overkill.

## Workflow

1. Export the Google Slides presentation as PPTX via Drive API
2. Modify with python-pptx (text find/replace, shape edits)
3. Upload the modified PPTX back to Drive, updating the existing file

Drive auto-converts the PPTX back to native Google Slides format on upload.

**You can also add new slides** (with images, text boxes, and shapes) via python-pptx and insert them at correct position — see [Adding a New Content Slide](#adding-a-new-content-slide-to-an-existing-deck). This works for survey sketches, photos, maps, or any visual asset the user sends after the deck was built.

## Step 1: Export as PPTX

```python
from tools.gws_auth import build_service
import io

drive = build_service('drive', 'v3', service_name='google-draas')

# Export as PPTX
file_id = "1NQn4Qmm0O7Jg87nzVUlk2t9Qe-K-D5KEzylFAVy05po"
request = drive.files().export_media(
    fileId=file_id,
    mimeType="application/vnd.openxmlformats-officedocument.presentationml.presentation"
)

pptx_bytes = io.BytesIO(request.execute())

# Save locally
with open("/tmp/slides_edit.pptx", "wb") as f:
    f.write(pptx_bytes.getvalue())
```

## Step 2: Modify with python-pptx

```python
from pptx import Presentation

prs = Presentation("/tmp/slides_edit.pptx")

for slide in prs.slides:
    for shape in slide.shapes:
        # Text frames
        if shape.has_text_frame:
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    if "Old Text" in run.text:
                        run.text = run.text.replace("Old Text", "New Text")
        
        # Tables (shapes.has_table)
        if shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    if "Old Text" in cell.text:
                        for paragraph in cell.text_frame.paragraphs:
                            for run in paragraph.runs:
                                if "Old Text" in run.text:
                                    run.text = run.text.replace("Old Text", "New Text")

prs.save("/tmp/slides_updated.pptx")
```

### Important: Run-level vs paragraph-level text

python-pptx stores text in **runs** within paragraphs. Always iterate `paragraph.runs` for replacements — checking only `paragraph.text` (which concatenates all runs) tells you something is there but doesn't let you change it. Run-level replacement preserves formatting (font size, color, bold).

## Step 3: Upload — Delete old + Create new (⚠️ files.update() doesn't work)

**Do NOT use `drive.files().update()`** to replace a native Google Slides file with PPTX content. It returns HTTP 200 and shows a modified timestamp, but the slide content does **not** change — the PPTX conversion doesn't happen on update. You must **delete the old file and create a new one** with the Slides MIME type:

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', service_name='google-draas')

# 1. Delete old file
drive.files().delete(fileId=file_id).execute()
print(f"✓ Deleted old file {file_id}")

# 2. Upload PPTX with conversion to Google Slides
media = MediaFileUpload(
    "/tmp/slides_updated.pptx",
    mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    resumable=True
)

body = {
    'name': 'Presentation Name',
    'mimeType': 'application/vnd.google-apps.presentation'  # ← triggers conversion
}

result = drive.files().create(
    body=body,
    media_body=media,
    fields='id, name, mimeType, webViewLink'
).execute()

new_file_id = result['id']
print(f"✓ Created new file: {new_file_id}")
print(f"  Link: {result.get('webViewLink')}")

# 3. Share with the requesting user (new file = new ID, old permissions gone)
drive.permissions().create(
    fileId=new_file_id,
    body={'type': 'user', 'role': 'writer', 'emailAddress': 'user@example.com'},
    sendNotificationEmail=True
).execute()
print("✓ Shared with user")
```

**Key differences from the old `files.update()` approach:**
| Aspect | `files.update()` ❌ | Delete+Create ✅ |
|--------|-------------------|------------------|
| PPTX→Slides conversion | Does NOT happen | Works correctly |
| File ID | Stays same | Changes (new ID) |
| Permissions | Preserved | Lost — must re-share |
| Link | Stable | Changes — deliver new link |

## Verify: Download and re-check

Re-download the file (repeat Step 1) and run a verification scan to confirm no occurrences of the old text remain:

```python
prs = Presentation(pptx_bytes)
remaining = 0
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                if "Old Text" in p.text:
                    remaining += 1

print(f"'Old Text' remaining: {remaining}")
assert remaining == 0, "Some instances were not replaced"
```

## Exporting a Google Slides Deck to PDF for Delivery

**A native Google Slides deck can be exported straight to PDF via the Drive API — no re-upload, no LibreOffice, and NO Slides API required.** This is the primary delivery path when the user asks for "a PDF of this presentation" (the Slides API may be disabled for the GCP project; Drive export still works):

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseDownload
import io

drive = build_service("drive", "v3", service_name="google-draas")
req = drive.files().export(fileId=PRESENTATION_ID, mimeType="application/pdf")
fh = io.FileIO("/tmp/deck.pdf", "wb")
dl = MediaIoBaseDownload(fh, req)
done = False
while not done:
    status, done = dl.next_chunk()
fh.close()
```

- Verify the page count after export (37-slide deck → 37 PDF pages) by scanning for `/Type /Page` in the PDF bytes or rendering with pymupdf.
- Deliver via `MEDIA:/path/to/deck.pdf` so the file arrives as a native attachment, not a link (Telegram link previews mangle Google URLs — see `google-slides-access-troubleshooting.md`).

**Verify contrast on the PDF before delivery:** white-on-white is a classic failure mode — a table with light cell fills and white-ish text looks fine in the editor but is invisible in the exported PDF. Render pages to PNG with pymupdf and check with `vision_analyze`:

```python
import fitz
doc = fitz.open("/tmp/deck.pdf")
for pno in [0, 33]:  # spot-check title + comparison table
    pix = doc[pno].get_pixmap(dpi=90)
    pix.save(f"/tmp/page_{pno+1}.png")
```

Then `vision_analyze(image_url="/tmp/page_34.png", question="Is all table text readable? Any white-on-white cells?")`. Ask explicitly about white-on-white; OCR alone won't tell you the color contrast.

## Advanced: Bulk Restyle — Flip Every Slide to White Background + Black Text

When the user reports "the color combination is not visible" on a slide (e.g. white-ish text on light table cells) and asks to make the whole deck white background / black text, do a full color flip via the PPTX round-trip. **Crucially: whitening the slide background is NOT enough — you must also whiten every solid shape fill (dark navy cards turn black-on-navy if left alone) and every table cell, or black text lands on dark fills.**

```python
from pptx import Presentation
from pptx.dml.color import RGBColor

SRC, OUT = "/tmp/deck_raw.pptx", "/tmp/deck_white.pptx"
WHITE, BLACK = RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0x00, 0x00, 0x00)
prs = Presentation(SRC)

def set_text_black(tf):
    for para in tf.paragraphs:
        for run in para.runs:
            try:
                run.font.color.rgb = BLACK
            except Exception:
                pass

def set_fill_white(shape):
    try:
        f = shape.fill
        if f.type is not None and str(f.type) != "MSO_FILL_TYPE.BACKGROUND (5)":
            f.solid(); f.fore_color.rgb = WHITE
    except Exception:
        pass

def walk(shape):
    if shape.shape_type == 6:              # GROUP — recurse into it
        for sub in shape.shapes:
            walk(sub)
        return
    if shape.has_text_frame:
        set_text_black(shape.text_frame)
    set_fill_white(shape)
    if shape.has_table:
        for row in shape.table.rows:
            for cell in row.cells:
                try:
                    cell.fill.solid(); cell.fill.fore_color.rgb = WHITE
                except Exception:
                    pass
                if cell.text_frame is not None:
                    set_text_black(cell.text_frame)

for slide in prs.slides:
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = WHITE
    for shape in slide.shapes:
        walk(shape)

prs.save(OUT)
```

**Pitfalls:**
- **Groups must be recursed** (`shape.shape_type == 6`) — a top-level pass alone misses grouped text/fills.
- Whitening shape fills kills the navy card aesthetic — that's exactly what the user asked for in a white/black flip. If they wanted to KEEP brand colors, restrict the flip to slide backgrounds + table text only.
- Flipping text to black while leaving navy fills is the worst outcome (invisible). Always whiten fills that hold text.
- After upload, re-export PDF and verify contrast (see previous section) before delivering.

## Pros & Cons

| Pros | Cons |
|------|------|
| Works even when Slides API is disabled | Loses some Google-native formatting on round-trip (embedded charts, Google fonts → system fonts) |
| Bulk find-replace across 30+ slides in seconds | Don't use if slides contain complex Google-native elements (linked charts, Apps Script) |
| One code path for all modifications | File gets a new ID on each upload — must re-deliver link and re-share |
| **Can add new slides** with images, text, and shapes (see [Adding a New Content Slide](#adding-a-new-content-slide-to-an-existing-deck)) | Can't change slide layouts or masters — content-only |
| **Can delete slides** safely (see [Advanced: Deleting Slides](#advanced-deleting-slides-from-an-existing-pptx)) | |
| **Can bulk-restyle colors** (white/black flip incl. tables and groups) | |
| **Can export to PDF directly** for delivery without Slides API | |

## Advanced: Adding Hyperlinks (Clickable URLs)

For more than just text replacement — when you need to add **clickable links** (Google Maps, listing portals, source URLs) to each slide, you need to work with the underlying PPTX XML to create `a:hlinkClick` elements.

### ⚠️ Hyperlink performance: batch relationships in groups

When adding links to 30+ slides in a single `prs.save()`, the `slide.part.relate_to()` call creates O(n) relationship entries per slide. This works fine for moderate decks (under 100 links total). For very large decks or if you see `ValueError: Relationship already exists`, wrap the `relate_to` call in a try/except — duplicate relationships for the same URL on the same slide are benign to suppress.

### Hyperlink helper pattern

```python
from pptx.oxml.ns import qn
from lxml import etree

def make_hyperlink(run_obj, url, slide_obj):
    """Attach a clickable hyperlink to a text run."""
    rPr = run_obj._r.find(qn('a:rPr'))
    if rPr is None:
        rPr = etree.SubElement(run_obj._r, qn('a:rPr'))
    
    # Create the relationship and get its ID
    rId = slide_obj.part.relate_to(
        url,
        'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',
        is_external=True
    )
    
    hlinkClick = etree.SubElement(rPr, qn('a:hlinkClick'))
    hlinkClick.set(
        '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id',
        rId
    )

# Usage: create a text box, add runs with different styles, then attach links
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor

txBox = slide.shapes.add_textbox(left=Emu(300000), top=Emu(4000000),
                                 width=Emu(8000000), height=Emu(300000))
tf = txBox.text_frame
p = tf.paragraphs[0]

# Google Maps link (green)
r1 = p.add_run()
r1.text = "📍 Maps"
r1.font.size = Pt(8)
r1.font.color.rgb = RGBColor(0x34, 0xA8, 0x53)
r1.font.underline = True
make_hyperlink(r1, "https://www.google.com/maps?q=12.853,77.783", slide)

# Separator
r_sep = p.add_run()
r_sep.text = "  │  "
r_sep.font.size = Pt(8)
r_sep.font.color.rgb = RGBColor(0xBB, 0xBB, 0xBB)

# MagicBricks link (orange)
r2 = p.add_run()
r2.text = "🏠 MagicBricks"
r2.font.size = Pt(8)
r2.font.color.rgb = RGBColor(0xE3, 0x74, 0x00)
r2.font.underline = True
make_hyperlink(r2, "https://www.magicbricks.com/...", slide)
```

### Adding text boxes to existing slides

Use `slide.shapes.add_textbox()` to insert new content. Position relative to the slide dimensions:

```python
slide_width = prs.slide_width   # Emu
slide_height = prs.slide_height  # Emu

# Find the bottom-most element for positioning
max_bottom = 0
for shape in slide.shapes:
    if hasattr(shape, 'top') and hasattr(shape, 'height'):
        bottom = shape.top + shape.height
        if bottom > max_bottom:
            max_bottom = bottom

# Place new text box just below the lowest element
top = min(max_bottom + Emu(30000), slide_height - Emu(350000))
txBox = slide.shapes.add_textbox(
    left=Emu(250000), top=top,
    width=slide_width - Emu(500000), height=Emu(280000)
)
tf = txBox.text_frame
tf.word_wrap = True
```

### Matching project names to slides

When you need to add different data to each slide based on which project it refers to, match by scanning slide text against a project name list:

```python
projects = {
    "Assetz 18 & Oak": {"lat": "12.8361198", "lon": "77.8012745"},
    # ... 30+ more
}

skip_slides = {0, 1, 2, 3}  # title, overview, section headers, summary

for i, slide in enumerate(prs.slides):
    if i in skip_slides:
        continue
    
    full_text = ""
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                full_text += para.text + " "
    
    for pname, pdata in projects.items():
        if pname.lower() in full_text.lower():
            # Add links to this slide
            maps_url = f"https://www.google.com/maps?q={pdata['lat']},{pdata['lon']}"
            # ... add text box with hyperlinks
            break
```

## Advanced: Adding Two-Line Metadata Footer Bars to Multiple Slides

When enriching real estate slides with per-project data (Google Maps links, listing sources, land area, RERA, developer name), the pattern below adds a two-line footer bar to each project slide:

**Line 1:** Clickable hyperlinks — Google Maps (green) | Source listings (orange)
**Line 2:** Metadata — Land area | RERA number | Developer name

### Implementation pattern

```python
from pptx.oxml.ns import qn
from lxml import etree
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor

def make_hyperlink(run_obj, url, slide_obj):
    """Attach clickable hyperlink to a text run."""
    rPr = run_obj._r.find(qn('a:rPr'))
    if rPr is None:
        rPr = etree.SubElement(run_obj._r, qn('a:rPr'))
    try:
        rId = slide_obj.part.relate_to(
            url,
            'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',
            is_external=True
        )
        hlinkClick = etree.SubElement(rPr, qn('a:hlinkClick'))
        hlinkClick.set(
            '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id',
            rId
        )
    except Exception:
        pass  # Suppress duplicate relationship errors

def add_footer_bar(slide, data, SLIDE_W, SLIDE_H):
    """Add a two-line metadata footer. 'data' dict: maps_url, sources[], land_area, rera, developer."""
    # Find bottom-most element to position the footer below it
    max_bottom = 0
    for shape in slide.shapes:
        if hasattr(shape, 'top') and hasattr(shape, 'height'):
            if shape.top is not None and shape.height is not None:
                bottom = shape.top + shape.height
                if bottom > max_bottom:
                    max_bottom = bottom

    footer_top = max_bottom + Emu(50000)
    # Clamp to stay on-slide
    footer_top = min(max(footer_top, Emu(500000)), SLIDE_H - Emu(450000))

    txBox = slide.shapes.add_textbox(
        left=Emu(180000), top=footer_top,
        width=SLIDE_W - Emu(360000), height=Emu(400000)
    )
    tf = txBox.text_frame
    tf.word_wrap = True

    # Line 1: clickable links
    p1 = tf.paragraphs[0]
    p1.space_after = Pt(2)

    if data.get('maps_url'):
        r = p1.add_run()
        r.text = "📍 Location"
        r.font.size = Pt(7)
        r.font.color.rgb = RGBColor(0x34, 0xA8, 0x53)
        r.font.underline = True
        make_hyperlink(r, data['maps_url'], slide)
        _sep(p1)

    for idx, src in enumerate(data.get('sources', [])[:2]):
        r = p1.add_run()
        r.text = src.get('label', f'Source {idx+1}')
        r.font.size = Pt(7)
        r.font.color.rgb = RGBColor(0xE3, 0x74, 0x00)
        r.font.underline = True
        if src.get('url'):
            make_hyperlink(r, src['url'], slide)
        if idx < len(data['sources'][:2]) - 1:
            _sep(p1)

    # Line 2: metadata text
    details = []
    if data.get('land_area'):        details.append(f"📐 Land: {data['land_area']}")
    if data.get('rera'):             details.append(f"📋 RERA: {data['rera']}")
    if data.get('developer'):        details.append(f"🏗️ {data['developer']}")

    if details:
        p2 = tf.add_paragraph()
        p2.space_before = Pt(1)
        r = p2.add_run()
        r.text = "  •  ".join(details)
        r.font.size = Pt(6.5)
        r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

def _sep(para):
    """Add a small gray separator run."""
    r = para.add_run()
    r.text = "  |  "
    r.font.size = Pt(7)
    r.font.color.rgb = RGBColor(0xBB, 0xBB, 0xBB)
```

### Usage: enrich 30+ project slides

Define a `data` dict per slide index, then loop:

```python
projects_data = {
    3: {  # Nexon Travenza — keyed by slide index
        'maps_url': 'https://www.google.com/maps?q=13.0337,77.7889',
        'sources': [
            {'label': '🏠 MagicBricks', 'url': 'https://www.magicbricks.com/project-page'},
            {'label': '🏠 Housiey', 'url': 'https://housiey.com/projects/nexon-travenza'},
        ],
        'land_area': '8.06 Acres',
        'rera': 'PRM/KA/RERA/.../008109',
        'developer': 'Nexon Builders And Developers',
    },
    # ... one entry per slide
}

SLIDE_W = prs.slide_width
SLIDE_H = prs.slide_height

for slide_num, data in projects_data.items():
    slide = prs.slides[slide_num]
    add_footer_bar(slide, data, SLIDE_W, SLIDE_H)
```

### Verify that every slide received its content

After adding footers, don't trust in-memory state — re-read from disk and check:

```python
prs = Presentation("/tmp/output.pptx")
expected_fields = ['maps_url', 'land_area', 'rera', 'developer']

for slide_num, expected in projects_data.items():
    slide = prs.slides[slide_num]
    full_text = " ".join(
        para.text for shape in slide.shapes if shape.has_text_frame
        for para in shape.text_frame.paragraphs
    )
    # Check each expected field is present in the slide text
    for field in expected_fields:
        val = expected.get(field, "")
        if val and val not in full_text and val not in str(val):
            print(f"⚠️ Slide {slide_num}: missing '{field}'")

# Also check hyperlink count per slide
from pptx.oxml.ns import qn
for slide_num in projects_data:
    slide = prs.slides[slide_num]
    links = slide._element.findall('.//' + qn('a:hlinkClick'))
    expected_links = 1 + len(projects_data[slide_num].get('sources', []))
    if len(links) < expected_links:
        print(f"⚠️ Slide {slide_num}: expected {expected_links} links, found {len(links)}")
```

### ⚠️ Pitfalls with footer bars

- **Text overflow:** If the slide already has content near the bottom, clamp `footer_top` to leave room. Never go below `SLIDE_H - Emu(400000)`.
- **Empty fields:** Use `—` or skip the line entirely rather than showing "None" or empty string.
- **`relate_to` duplicate errors:** The `try/except` in `make_hyperlink` suppresses the benign `ValueError: Relationship already exists` — this can fire when two runs link to the same URL on the same slide.
- **Verification must re-read from disk:** in-memory `prs.slides[n].shapes` shows the added boxes even without save(), but the file on disk may not have them. Always `prs.save()` then `Presentation("/path/")` to verify.

## Advanced: Data from Google My Maps (KML Export)

When slides are based on a Google My Maps layer, export the KML to get exact coordinates and marker data for each project:

```bash
curl -sL "https://www.google.com/maps/d/kml?mid=MID_VALUE&forcekml=1" -o projects.kml
```

Then parse the KML with Python's `xml.etree.ElementTree`:

```python
import xml.etree.ElementTree as ET

tree = ET.parse('/tmp/projects.kml')
root = tree.getroot()
ns = {'kml': 'http://www.opengis.net/kml/2.2'}

for folder in root.findall('.//kml:Folder', ns):
    layer_name = folder.find('kml:name', ns)
    layer_name = layer_name.text if layer_name is not None else "Unknown"
    
    for placemark in folder.findall('kml:Placemark', ns):
        name = placemark.find('kml:name', ns)
        name = name.text.strip() if name is not None and name.text else "Unnamed"
        
        coords = placemark.find('.//kml:coordinates', ns)
        coords_text = coords.text.strip() if coords is not None else ""
        
        # Extract first coordinate pair (for point markers)
        first_pt = coords_text.split('\n')[0].strip().split(',')
        lon, lat = first_pt[0], first_pt[1] if len(first_pt) >= 2 else ("", "")
        
        print(f"{name}: {lat}, {lon}")
```

This gives you precise coordinates for generating Google Maps links (`https://www.google.com/maps?q=lat,lon`).

## Advanced: Updating Summary / Price Comparison Slides

When a Google Slides deck has a summary slide (e.g., "Price Comparison — All Projects") that lists many items with prices — each row as 3 individual text boxes (number, project name, price) rather than a table — use this pattern:

### 1. Dump the full shape structure

```python
from pptx import Presentation

prs = Presentation("/tmp/slides_edit.pptx")
summary_slide = prs.slides[34]  # find the right slide index

for idx, shape in enumerate(summary_slide.shapes):
    if shape.has_text_frame:
        text = ''.join(p.text for p in shape.text_frame.paragraphs)
        left, top = shape.left, shape.top
        print(f"Shape {idx}: pos=({left},{top}) text='{text[:80]}'")
```

### 2. Identify the pattern

In a structured summary slide, each row typically has 3 text boxes in sequence:
- Shape N: number (e.g., "1")
- Shape N+1: project name (e.g., "NVT Arcot Vaksana")
- Shape N+2: price (e.g., "₹10,600 — 12,300/sq.ft")

The shapes alternate with rectangle auto-shapes (row backgrounds). Scan the output to confirm which shape indices map to price fields.

### 3. Build a price update map

```python
# Map: shape_index -> new_price_text
price_updates = {
    7: "₹12,132-15,011/sq.ft",    # NVT Arcot Vaksana
    11: "₹10,900-12,000/sq.ft",   # Assetz 18 & Oak
}

# Update each price shape in-place
for idx, shape in enumerate(summary_slide.shapes):
    if idx in price_updates and shape.has_text_frame:
        para = shape.text_frame.paragraphs[0]
        run = para.runs[0] if para.runs else para.add_run()
        run.text = price_updates[idx]
```

### 4. Cross-reference with project slides

When the deck also has individual project slides with their own current prices, extract those values to populate the comparison slide:

```python
project_data = {}
for i, slide in enumerate(prs.slides):
    texts = []
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                t = para.text.strip()
                if t:
                    texts.append(t)
    if not texts:
        continue

    # Find "💰 CURRENT PRICE" label and read the value below it
    for j, t in enumerate(texts):
        if t == '💰 CURRENT PRICE' and j + 1 < len(texts):
            current_price = texts[j + 1]
            project_data[texts[0]] = current_price
```

### Key differences from find-replace

Find-replace works when the same string appears everywhere. For summary slides, each item has a **different value**, so you need an explicit mapping of shape-index → new-value. Use the shape indices from the dump — they are stable within a single execution because python-pptx reads them in document order.

### When NOT to use this pattern

- If the summary slide uses a **table** (shape.has_table is true), use cell iteration instead
- If the summary slide uses **group shapes** (shape.shape_type == GROUP), recursively ungroup first
- For adding NEW items to the summary (not updating existing), create the presentation from scratch — existing text box positioning is fragile

## Adding a New Content Slide to an Existing Deck

When the user sends a document (survey sketch, photo, PDF) to add to an already-built presentation, you can insert a new slide through the same PPTX round-trip:

### Workflow

1. Export Slides → PPTX (see Step 1 above)
2. Insert a new slide using python-pptx
3. Upload back via Option C (Delete + Create)

### Insert pattern (full example)

```python
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation("/tmp/slides_edit.pptx")
BLANK = prs.slide_layouts[6]

# Create new slide at the end
new_slide = prs.slides.add_slide(BLANK)

# Set dark background
new_slide.background.fill.solid()
new_slide.background.fill.fore_color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

# Gold header bar
bar = new_slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Emu(40000))
bar.fill.solid(); bar.fill.fore_color.rgb = RGBColor(0xD4, 0xA5, 0x37); bar.line.fill.background()

# Title textbox
tb = new_slide.shapes.add_textbox(Emu(300000), Emu(150000), Emu(10000000), Emu(350000))
tb.text_frame.word_wrap = True
p = tb.text_frame.paragraphs[0]
p.text = "SLIDE TITLE — Subtitle"
p.font.size = Pt(22); p.font.bold = True; p.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

# Add image (resize large images first to avoid bloating the PPTX)
new_slide.shapes.add_picture("/tmp/sketch.jpg",
    Emu(300000), Emu(800000),
    Emu(11400000), Emu(4200000))

# Add annotation card at bottom
card = new_slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
    Emu(300000), Emu(5200000), Emu(11400000), Emu(1400000))
card.fill.solid(); card.fill.fore_color.rgb = RGBColor(0x1E, 0x2A, 0x45); card.line.fill.background()

# ... add text boxes with details inside the card ...

# Reorder: move new slide to desired position (0-indexed)
# Position 2 = after slide 1 (Subject Land Overview), before slide 2 (Location)
new_idx = 2
sldIdLst = prs.slides._sldIdLst
new_slide_elem = sldIdLst[-1]  # freshly added slide is last
sldIdLst.remove(new_slide_elem)
sldIdLst.insert(new_idx, new_slide_elem)

prs.save("/tmp/slides_updated.pptx")
```

### Expected placement conventions

| Deck type | Insert after | New index |
|-----------|-------------|-----------|
| Villa/Plotted market research | Slide 1 (Subject Land Overview) | 2 |
| Land Proposal Evaluation | Slide 2 (Location & Connectivity) | 3 |

### → Follow up with Step 3 upload (Delete + Create)

After saving, upload back to Drive using the [Delete + Create](#option-c-delete--create-replacing-an-existing-google-slides-file) pattern. Re-share with the user (new file = new ID).

> See also `references/land-survey-sketch-integration.md` for the full survey sketch workflow (vision analysis → image prep → slide insertion → upload). The Pattandur Agrahara companion script at `/opt/data/add_survey_sketch.py` is a working example.

## Advanced: Deleting Slides from an Existing PPTX

Despite the common warning, you CAN delete slides from a python-pptx presentation and successfully round-trip it through Google Drive. The technique works reliably when you use the low-level XML manipulation to remove both the slide relationship and the slide list entry.

**⚠️ Only delete slides that contain user content (text boxes, shapes, images).** Do NOT try to delete layout masters or slide layouts — those are referenced by the schema and will break the round-trip. Content slides (the kind you create or see in the thumbnail panel) are safe to delete.

### Delete pattern

```python
from pptx import Presentation

prs = Presentation("/tmp/slides_edit.pptx")

# Slides to remove (0-indexed). DELETE IN REVERSE ORDER so indices stay valid.
remove_indices = [35, 34, 33, 4]  # highest index first!

sldIdLst = prs.slides._sldIdLst
for idx in remove_indices:
    rId = sldIdLst[idx].rId
    prs.part.drop_rel(rId)        # Remove the relationship
    del sldIdLst[idx]              # Remove from slide list

prs.save("/tmp/slides_updated.pptx")
print(f"Removed {len(remove_indices)} slides. New count: {len(prs.slides)}")
```

### Key rules

1. **Delete in reverse index order.** The highest index first, working down. This prevents index shifting because removing a later slide doesn't change the position of earlier slides.
2. **`_sldIdLst`** is the internal list of slide references. It is indexable and mutable. Deleting from it removes the slide from the presentation.
3. **`part.drop_rel(rId)`** removes the relationship to the deleted slide's XML file, preventing orphan references.
4. **Call `prs.save()` immediately after deletions** — the in-memory object is transient, and without save(), no changes persist.

### When to delete slides

- Removing duplicate or obsolete slides from a deck
- Removing a section whose all projects were removed (e.g., entire "Older Boutique" section)
- Removing a pricing justification or bonus slide the user no longer wants
- After filtering a price comparison table, remove the corresponding project slides

**Tested:** 14 slides removed from a 39-slide deck in a single pass (v4 → v5 of RANKA Amber market research report). The resulting 25-slide deck uploaded and converted to Google Slides without issues.

### Verify deletions on disk

```python
prs = Presentation("/tmp/slides_updated.pptx")
# Check slide titles to confirm the right ones were removed
for i, slide in enumerate(prs.slides):
    first_text = ''
    for shape in slide.shapes:
        if hasattr(shape, 'text') and shape.text.strip():
            first_text = shape.text.strip()[:90]
            break
    print(f"  Slide {i+1}: {first_text}")
```

## Advanced: Editing Text Boxes by Position (Y/X Coordinate Matching)

When a slide contains many text boxes positioned as a structured layout (e.g., a price comparison table where each "row" is 7 individual text boxes at the same Y coordinate), shape index is fragile — inserting or removing shapes shifts indices. Instead, match by **position coordinates**:

### Pattern: group shapes by Y coordinate

```python
# Group all text shapes by their Y position
rows = {}  # y → {x: text}
for shape in slide.shapes:
    if not hasattr(shape, 'text') or not shape.text.strip():
        continue
    y = shape.top
    x = shape.left
    if y not in rows:
        rows[y] = {}
    rows[y][x] = shape  # Store the shape object

# Iterate rows from top to bottom
for y in sorted(rows.keys()):
    row = rows[y]
    # Now identify columns by X ranges
    for x in sorted(row.keys()):
        shape = row[x]
        # ... modify shape text
```

### Determine column ranges from the actual layout

Print all shapes to find the X ranges per column:

```python
for shape in slide.shapes:
    if hasattr(shape, 'text') and shape.text.strip():
        print(f"  y={shape.top} x={shape.left}: {shape.text.strip()[:60]}")
```

Then define column matchers by X position:

```python
def column_at(x):
    if 300000 <= x <= 400000:    return 'number'
    if 500000 <= x <= 600000:    return 'name'
    if 3300000 <= x <= 3400000:  return 'launch_price'
    if 5100000 <= x <= 5200000:  return 'current_price'
    if 6900000 <= x <= 7000000:  return 'units'
    if 7600000 <= x <= 7700000:  return 'launch_year'
    if 8200000 <= x <= 8300000:  return 'completed'
    return 'other'
```

### Advantages over shape index matching

- **Survives modifications:** Adding or removing text boxes elsewhere on the slide won't break your logic.
- **Self-documenting:** The Y/X values encode the table structure explicitly.
- **Row-level operations:** You can delete entire rows (all shapes at a given Y), renumber, or compact spacing.

### Removing rows and renumbering

```python
# Y values of rows to remove
remove_ys = {2742000, 2907000, 3237000}

# Collect shapes to remove
shapes_to_remove = []
remaining_rows = {}

for shape in slide.shapes:
    if not hasattr(shape, 'text') or not shape.text.strip():
        continue
    y = shape.top
    if y in remove_ys:
        shapes_to_remove.append(shape)
    else:
        col = column_at(shape.left)
        if y not in remaining_rows:
            remaining_rows[y] = {}
        remaining_rows[y][col] = shape

# Remove shapes
for shape in shapes_to_remove:
    sp = shape._element
    sp.getparent().remove(sp)

# Renumber and compact upward
new_y = 1092000  # Starting Y for first data row
for row_num, old_y in enumerate(sorted(remaining_rows.keys()), 1):
    for col, shape in remaining_rows[old_y].items():
        shape.top = new_y          # Move to new position
        if col == 'number':
            # Update the row number text
            for run in shape.text_frame.paragraphs[0].runs:
                run.text = str(row_num)
    new_y += 165000  # Row height in EMU

# Move note/footer text below the new last row
for shape in slide.shapes:
    if hasattr(shape, 'text') and shape.text.strip().startswith('Note:'):
        shape.top = new_y + 100000
```

### Row height reference

| Use case | Vertical spacing (EMU) | Notes |
|----------|----------------------|-------|
| Tight table rows | 165,000 | ~0.165 inches — leaves room for 25+ rows on a single slide |
| Spacious summary rows | 200,000-250,000 | ~0.2-0.25 inches — easier to read |
| Section headers above table | 50,000 gap | Small gap before a new section |

## ⚠️ Known Pitfalls

- **python-pptx has_table check:** `shape.has_table` is the attribute, NOT `shape.has_table()`. No parentheses.
- **CRITICAL: `prs.save()` is required.** python-pptx stores all edits in memory. Until you call `prs.save("/path/to/file.pptx")`, nothing is written to disk. Do NOT trust the in-memory object's `.text` values after editing — they reflect the edited state, but the file on disk is still the original. After every edit, call `save()` and verify by re-opening from disk:
  ```python
  prs.save("/tmp/slides_updated.pptx")

  # VERIFY: re-open from disk and check
  prs_check = Presentation("/tmp/slides_updated.pptx")
  slide_check = prs_check.slides[target_slide]
  actual_text = slide_check.shapes[target_shape].text_frame.paragraphs[0].text
  assert actual_text == expected_value, f"Save failed! Expected '{expected_value}', got '{actual_text}'"
  ```
  This caught me in production: I edited shapes in memory, printed confirmations that showed the new values, but never called `save()`. The user saw zero changes.
- **Hyperlink relationships:** Each `slide.part.relate_to()` call creates a new relationship entry. For 33 slides × 3 links = 99 relationships, this is fine. For thousands of links, consider deduplication.
- **Font substitution:** Google fonts (e.g., Calibri, Roboto) that aren't in the LibreOffice font set may render differently after round-trip. For text-only find/replace this is usually fine.
- **File size limit:** Google Drive export of presentations over ~100MB may fail. For typical market research decks (2-3MB) this is not an issue.
- **Slide deletion is safe for content slides** but do NOT delete layout masters or slide layouts — those are referenced in the schema and will break the round-trip. Content slides (the kind that appear in the thumbnail panel) are fine to delete. See the [Advanced: Deleting Slides](#advanced-deleting-slides-from-an-existing-pptx) section for the correct technique.
- **Verify after upload, not before** — download the file from Drive after uploading and re-check key values. A successful HTTP 200 from the upload doesn't guarantee the server-side conversion was correct. The `drive.files().update()` trap (documented above) is a real example: it returns 200 but content doesn't change.
- **`execute_code` sandbox isolation:** Each call to `execute_code()` runs in a fresh sandbox process. All variables (`prs`, `drive_service`, etc.) are lost between calls. Combine download → modify → verify-on-disk → upload in a SINGLE `execute_code()` script.
- **Run-level vs paragraph-level text** (repeated for emphasis): Always iterate `paragraph.runs` for replacements — checking only `paragraph.text` tells you something is there but doesn't let you change it. Run-level replacement preserves formatting.
