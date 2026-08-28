# python-pptx — Adding Clickable Hyperlinks to Existing Slides

## Problem

You have an existing `.pptx` slide with a text box containing labels like `📍 Maps  │  🏠 MagicBricks  │  🏘️ 99acres`.  
The text is a single run — you want each segment to be a separate clickable hyperlink.

## Quick Solution (Built-in API — Preferred)

python-pptx has a built-in hyperlink API that handles all relationship management automatically. Use this instead of the manual lxml approach:

```python
# Clear existing runs
for r in list(para.runs):
    r._r.getparent().remove(r._r)

# Add runs with clickable hyperlinks
run = para.add_run()
run.text = "📍 Maps"
run.font.size = Pt(8)
run.hyperlink.address = "https://maps.google.com/?q=..."

run = para.add_run()
run.text = "  │  "
run.font.size = Pt(8)

run = para.add_run()
run.text = "🏠 MagicBricks"
run.font.size = Pt(8)
run.hyperlink.address = "https://www.magicbricks.com/..."
```

The `run.hyperlink.address` setter **automatically creates the relationship on the correct slide part** and inserts the `<a:hlinkClick>` element into the run's `rPr`. No need to touch `lxml`, `slide.part`, or `qn()`.

### Complete example: processing both project and review slides

When a deck has TWO slide types per project — one with emoji labels (`📍 Maps`, `🏠 MagicBricks`) and one with full-text URLs (`📍 Google Maps: maps.google.com/...`) — process both:

```python
def make_links(shape, segments):
    """Replace a text box's single run with multiple clickable runs."""
    tf = shape.text_frame
    para = tf.paragraphs[0]
    
    # Clear existing runs
    for r in list(para.runs):
        r._r.getparent().remove(r._r)
    
    for idx, (label, url) in enumerate(segments):
        if idx > 0:
            sep = para.add_run()
            sep.text = "  │  "
            sep.font.size = Pt(8)
        
        run = para.add_run()
        run.text = label
        run.font.size = Pt(8)
        
        if url:
            run.hyperlink.address = url  # ← built-in API, handles relationships

# Extract URLs once from review slides using URL regex (not keyword match)
urls_by_slide = {}
for slide_num in range(len(prs.slides)):
    slide = prs.slides[slide_num]
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        t = shape.text_frame.text
        has_maps_url = bool(re.search(r'(?:https?://)?maps\.google\.com[^\s|]+', t))
        if not has_maps_url:
            continue
        # Extract each URL type
        urls = {}
        m = re.search(r'(?:https?://)?maps\.google\.com[^\s|]+', t)
        if m: urls['maps'] = 'https://' + m.group(0) if not m.group(0).startswith('http') else m.group(0)
        m = re.search(r'https?://www\.magicbricks\.com[^\s|]+', t)
        if m: urls['mb'] = m.group(0)
        m = re.search(r'https?://www\.99acres\.com[^\s|]+', t)
        if m: urls['99acres'] = m.group(0)
        urls_by_slide[slide_num] = urls
        break

# Then process project slides (emoji labels) and review slides (full URLs)
for proj_num, review_num in [(4,5), (6,7), (8,9), ...]:  # (project_idx, review_idx)
    urls = urls_by_slide.get(review_num, {})
    
    # Project slide: short labels
    proj_slide = prs.slides[proj_num]
    for shape in proj_slide.shapes:
        if not shape.has_text_frame: continue
        t = shape.text_frame.text
        if '📍' in t and 'http' not in t and len(t) < 150:
            segments = []
            if '📍' in t: segments.append(("📍 Maps", urls.get('maps')))
            if '🏠' in t: segments.append(("🏠 MagicBricks", urls.get('mb')))
            if '🏘' in t: segments.append(("🏘️ 99acres", urls.get('99acres')))
            make_links(shape, segments)
            break
    
    # Review slide: full text URLs
    review_slide = prs.slides[review_num]
    for shape in review_slide.shapes:
        if not shape.has_text_frame: continue
        t = shape.text_frame.text
        has_url = bool(re.search(r'(?:https?://)?maps\.google\.com[^\s|]+', t))
        if not has_url: continue
        segments = []
        if urls.get('maps'): segments.append(("📍 Google Maps", urls['maps']))
        if urls.get('mb'): segments.append(("🏠 MagicBricks", urls['mb']))
        if urls.get('99acres'): segments.append(("🏘️ 99acres", urls['99acres']))
        make_links(shape, segments)
        break
```

Key pattern: extract URLs once from the review slides (where they exist as full text), then apply to BOTH the project slide's emoji labels and the review slide's text labels. This keeps the data in one place.

## No URLs anywhere in the deck — research them per project

When the deck has only plain-text source bars (`📍 Google Maps │ 🏠 MagicBricks │ 🏘️ 99acres │ Sources: 99acres Map & Details`) and NO review slides with full URLs, research each project's real page from scratch (observed Aug-2026, Chikkaballapur deck: 16 project slides, zero embedded URLs):

- **Google Maps link**: take the project pin's coordinates from the source KML → `https://maps.google.com/?q=LAT,LNG`
- **MagicBricks project page**: `web_search` `"<Project Name>" magicbricks` → prefer URLs containing `pdpid-` or `project-plots-<slug>-for-sale-in-bangalore-pppfs`
- **99acres project page**: `web_search` `"<Project Name>" 99acres` → prefer URLs containing `-npxid-rXXXXX` (project ID) over `-npffid` (resale-filter page) or `-spid-` (single-plot listing)
- Query pattern that works: `"<Project Name>" 99acres OR magicbricks plots` — add locality for generic names (e.g. "Montira" → found as "Rare Earth Montira Nandi Hills"; "Belmont" → "Citrus Belmont")
- **Projects with no dedicated portal page** (older/pre-RERA layouts, e.g. Sammy's Sunrise Boulevard): fall back to the developer's official site or an aggregator page; keep the icon but link the best available source, and tell the user which links are fallbacks

**Confirmation:** After saving, verify by re-opening and checking `run.hyperlink.address`:
```python
prs2 = Presentation(output)
for i, slide in enumerate(prs2.slides):
    for shape in slide.shapes:
        if not shape.has_text_frame: continue
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                try:
                    addr = run.hyperlink.address
                    if addr:
                        print(f"  ✓ Slide {i+1} '{run.text[:25]}' -> {addr[:60]}")
                except:
                    pass
```

## ⚠️ False positive trap when finding the right text box

When searching slides for source-links text boxes that contain full URLs like `maps.google.com/?q=...`, the slide may also have **other text blocks** with the same keyword (e.g. a "CONCERNS" section: "Some Google Maps reviews mention the surrounding area..."). Checking `'Google Maps' in shape.text_frame.text` matches the wrong shape.

**Fix — use URL pattern detection, not keyword matching:**

```python
import re

for shape in slide.shapes:
    if not shape.has_text_frame:
        continue
    t = shape.text_frame.text
    
    # Only match shapes with actual URLs — not shapes that just mention the keyword
    has_url = bool(re.search(r'(?:https?://)?maps\.google\.com[^\s|]+', t))
    if not has_url:
        continue
    
    # This shape has real URLs — safe to process
    ...
```

Or when the relationship is known (source-label bars on project slides are short, URLs are on review slides), use this heuristic:

```python
if '📍' in text and 'http' not in text and len(text) < 100:
    # Short emoji labels — project slide source bar
    ...
```

## Root Cause

python-pptx manages hyperlinks through the OPC relationship system. Each clickable link requires:
1. A relationship on the **slide part** (not the shape, not the run) pointing to the external URL
2. An `<a:hl>` element inside the run's `<a:rPr>` with `r:id` pointing to that relationship

The shape itself has no relationship collection — you must go through `slide.part`.

## Technique

```python
from pptx.oxml.ns import qn
from lxml import etree

HYPERLINK_TYPE = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink'

def add_hyperlink_to_run(run, url, slide_part, tooltip=''):
    """Make a run clickable. slide_part = slide.part"""
    if not url:
        return False
    # 1. Add an external relationship → get rId back
    rId = slide_part.relate_to(url, HYPERLINK_TYPE, is_external=True)
    
    # 2. Ensure rPr exists on the run
    rPr = run._r.find(qn('a:rPr'))
    if rPr is None:
        rPr = etree.SubElement(run._r, qn('a:rPr'))
    
    # 3. Add hyperlink element
    hl = etree.SubElement(rPr, qn('a:hl'))
    hl.set('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id', rId)
    if tooltip:
        hl.set('tooltip', tooltip)
    return True
```

### Rebuilding a source-links bar (single run → multiple runs)

When the original text is one run like `📍 Maps  │  🏠 MagicBricks  │  🏘️ 99acres`:

```python
def rebuild_source_links(tx_box, links, slide_part):
    """
    Replace a text box's entire content with hyperlinked segments.
    links = [(text, url, tooltip), ...]
    """
    tf = tx_box.text_frame
    tf.clear()
    para = tf.paragraphs[0]
    
    # Remove any existing runs
    for r_elem in para._p.findall(qn('a:r')):
        para._p.remove(r_elem)
    
    for label, url, tip in links:
        r = etree.SubElement(para._p, qn('a:r'))
        
        if url:
            rPr = etree.SubElement(r, qn('a:rPr'))
            try:
                rId = slide_part.relate_to(url, HYPERLINK_TYPE, is_external=True)
                hl = etree.SubElement(rPr, qn('a:hl'))
                hl.set('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id', rId)
                if tip:
                    hl.set('tooltip', tip)
            except Exception:
                pass  # text still shows, link silently omitted
        
        t = etree.SubElement(r, qn('a:t'))
        t.text = label

# Usage:
links = [
    ('📍 Maps', maps_url, 'Open in Google Maps'),
    ('  │  🏠 MagicBricks', mb_url, 'View on MagicBricks'),
    ('  │  🏘️ 99acres', acres_url, 'View on 99acres'),
]
rebuild_source_links(textbox, links, slide.part)
```

## ⚠️ Image hyperlinks are DROPPED by Google Slides import (Aug-2026)

python-pptx lets you attach a hyperlink to a picture via raw XML:
`<p:nvPicPr><p:cNvPr ...><a:hlinkClick r:id="rId3"/></p:cNvPr>`. In PowerPoint
this works — but when the PPTX is uploaded to Drive and converted to native
Google Slides (the standard delivery path when the Slides API is disabled),
the image-attached link is SILENTLY DROPPED. The slide converts fine; the
image is just no longer clickable. User reports "the link is not working".

**Fix: put the hyperlink on a text RUN, never on the image.**
- Remove the image's `a:hlinkClick` from `p:cNvPr`
- Add (or reuse) a text box / shape whose run carries `run.hyperlink.address = URL`
  — text-run links DO survive conversion
- Standard pattern: a prominent button shape with styled text:
  ```python
  btn = slide.shapes.add_shape(1, Emu(x), Emu(y), Emu(w), Emu(h))  # 1 = RECTANGLE
  btn.fill.solid(); btn.fill.fore_color.rgb = RGBColor(0x1B,0x2A,0x4A)
  run = btn.text_frame.paragraphs[0].add_run()
  run.text = "OPEN INTERACTIVE MAP"
  run.hyperlink.address = MAP_URL
  ```
  Plus hyperlink the caption run too — two independent text links on the
  slide so one is always obvious.

**Verify after conversion:** export the CONVERTED deck back to PPTX
(`drive.files().export_media(fileId=..., mimeType='...presentationml.presentation')`),
unzip, and grep the map slide XML for `hlinkClick`. Look at ~250 chars of
context before each match: it must contain `<a:rPr` (TEXT-RUN). If the
context shows `cNvPr`, the link is on an image and will NOT work in Slides.
Also confirm the URL is present in `ppt/slides/_rels/slideN.xml.rels`.

## Slides round-trip reorders slides — locate by content, not index

After Google Slides imports/converts a PPTX, users can drag slides around.
Exporting that deck back to PPTX gives a DIFFERENT slide index than the file
you uploaded. Never address a slide by hardcoded index across a round-trip —
locate it by content (loop `prs.slides`, search each shape's text for a
unique title string like `'INTERACTIVE MAP'`), then edit. Observed Aug-2026:
map slide built at index 22 came back at index 7 of 25 after the user
reordered; editing by assumed index would have hit the wrong slide.

## Deck access diagnostics — file 404s though the user owns it

Observed Aug-2026: user pastes `docs.google.com/presentation/d/<ID>/edit`
but Drive API `files().get` returns 404 and the vault token says the file
doesn't exist. Root cause: deck is PRIVATE and owned under a DIFFERENT Google
account than the vault token. Diagnostic ladder, in order:

1. `curl -sL "https://docs.google.com/presentation/d/<ID>/export/pptx" -o x.pptx`
   → **HTTP 200 = link-shared, grab it directly** (no vault needed).
   → **HTTP 401 = private** (file exists but requires auth). Ask the user to
   set Share → General access → "Anyone with the link" (Viewer or Editor),
   then re-curl. 401→200 flip is the confirmation sharing landed.
2. If still 401 after they say "done": retry after ~15s (propagation lag),
   then ask them to share directly with the vault account (`ndr@draas.com`)
   as Editor — Google Workspace domain policies can block public link
   sharing on some org files.
3. Once exported, the standard upload-as-native-Slides path creates a NEW
   file ID owned by the vault account — share that copy back with the user's
   account (`permissions().create(type='user', role='writer',
   emailAddress=user_email)`) AND set anyone-with-link reader so the link
   opens everywhere.

## Reordering slides in python-pptx (XML sldIdLst)

`prs.presentation.sldIdLst` does NOT exist (AttributeError) — the slide ID
list lives at `prs.slides._sldIdLst`:

```python
prs = Presentation(deck)
sldIdLst = prs.slides._sldIdLst   # NOT prs.presentation.sldIdLst
ids = list(sldIdLst)              # one <p:sldId> per slide, in order
# find target slide by content index, then:
map_el = ids[target_idx]
sldIdLst.remove(map_el)
sldIdLst.insert(desired_index, map_el)  # 0-based insert position
prs.save(out)
```

Verify after save by re-opening and printing slide titles in order.

## Interpreter split on the VPS (gws vs python-pptx)

System `python3` has `googleapiclient` (gws_auth works for Drive export/
upload/permissions). The venv (`/opt/data/.venv/bin/python`) has
python-pptx but NOT googleapiclient. Pattern that works: **export with system
python3, edit/verify with the venv python** — never try to install
googleapiclient into the venv or run gws_auth from it.

## Important Details

- **`slide.part` vs `slide._element`**: The `_element` is XML; relationships live on the `part` object. Always use `slide.part.relate_to(...)`.
- **Duplicate relationships**: If you call `relate_to()` with the same URL twice on the same slide, it creates **two** relationship entries (different `rId` values). The slide still works — each link points to the same URL via different rIds. No dedup needed.
- **Relationship isolation**: Each slide has its own relationship collection. A hyperlink on Slide 5 does **not** create a relationship visible from Slide 6.
- **Hyperlinks survive re-save**: Relationships are serialized to the `slides/_rels/slideN.xml.rels` file inside the PPTX. They persist across `prs.save()`.
- **Tooltips**: The `tooltip` attribute on `<a:hl>` is the hover text shown in PowerPoint. Not all viewers display it (Google Slides ignores it), but it's harmless and useful for PowerPoint desktop users.
- **Error handling**: `relate_to()` can raise `DuplicateRelationShipError` in some versions of python-pptx if the exact URL was already related on this slide. The `try/except` in the example above handles this gracefully — the text renders, the link just won't be clickable (rare).

## Finding the Source Textbox

When processing project slides with unknown shape names, identify the source-links textbox by content:

```python
for shape in slide.shapes:
    if not shape.has_text_frame:
        continue
    text = shape.text_frame.text
    # Project source links are short labels, not full URLs.
    # Use < 150: bars carrying a trailing 'Sources: ...' note run 100-150 chars.
    if '📍' in text and 'http' not in text and len(text) < 150:
        # This is the source links textbox
        rebuild_source_links(shape, links, slide.part)
        break
```

Avoid matching review-slide footers (which contain full URLs like `maps.google.com/?q=...`) by checking `'http' not in text`.

## ⚠️ Google Slides import DROPS image-attached hyperlinks (use text runs)

**Symptom:** You add a hyperlink to a picture in python-pptx (e.g. `shape.click_action.hyperlink` or manual `a:hlinkClick` in the pic's `cNvPr`), upload the PPTX to Drive as a native Google Slides file, and the user reports "the link is not working." It worked in PowerPoint but is dead in Google Slides.

**Root cause:** Google Slides' PPTX importer silently discards `a:hlinkClick` elements that live in `<p:cNvPr>` of `<p:pic>` (image-attached links). It only preserves hyperlinks attached to **text runs** (`<a:hlinkClick>` inside `<a:rPr>` of `<a:r>`).

**Fix — put the link on text, not on the image:**
- Keep the image as a visual.
- Add a prominent button shape (rectangle) whose *text run* carries the hyperlink: `run.hyperlink.address = url` (built-in API handles the rel). Style it with brand colors so it reads as a CTA.
- Optionally also hyperlink a caption line: `run.hyperlink.address = url`, set underline + accent color so it looks clickable.
- Remove the dead image link for cleanliness:
  ```python
  from pptx.oxml.ns import qn
  for sh in slide.shapes:
      if sh.shape_type == 13:  # PICTURE
          cNvPr = sh._element.find('.//' + qn('p:cNvPr'))
          if cNvPr is not None:
              for hl in cNvPr.findall(qn('a:hlinkClick')):
                  cNvPr.remove(hl)
  ```

**Verify AFTER Google Slides conversion (not just in the source PPTX):** re-export the converted deck from Drive (`drive.files().export_media(fileId=..., mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation')`), open the slide XML from the zip, and confirm every `hlinkClick` sits inside `rPr` context (TEXT-RUN), never `cNvPr` (IMAGE). Check `slideN.xml.rels` contains the target URL. This is the only reliable proof the link survived — checking the pre-upload PPTX is insufficient.

```python
import zipfile, re
z = zipfile.ZipFile('converted_back.pptx')
for n in z.namelist():
    if n.startswith('ppt/slides/slide') and n.endswith('.xml'):
        x = z.read(n).decode('utf-8', 'ignore')
        if 'YOUR_SLIDE_MARKER' in x:          # e.g. slide title text
            print('hlinks:', len(re.findall(r'hlinkClick', x)))
            for m in re.finditer(r'hlinkClick', x):
                ctx = x[max(0,m.start()-250):m.start()+60]
                kind = 'TEXT-RUN' if 'rPr' in ctx else ('IMAGE(cNvPr)' if 'cNvPr' in ctx else 'OTHER')
                print(' ', kind)
            relf = n.replace('slides/','slides/_rels/') + '.rels'
            print(re.findall(r'Target="([^"]*)"', z.read(relf).decode('utf-8','ignore')))
```

## Full Workflow

1. Find the textbox on the project slide (content-based detection)
2. Clear it and rebuild with separate runs per link
3. Each run gets its own relationship + `a:hl` in `rPr`
4. Save the presentation — hyperlinks persist

## Downloading the project KML for coordinates — use get_media(), NOT export_media()

`drive.files().export_media(fileId=..., mimeType='application/vnd.google-earth.kml+xml')` fails with **403 "Export only supports Docs Editors files"** for KML/KMZ files stored on Drive — they're uploaded as regular binary files, not Docs Editors. Download with:

```python
kml_data = drive.files().get_media(fileId=KML_FILE_ID).execute()
```

Then parse placemark names + coordinates (folder-aware regex over `<Folder>...</Folder>` / `<Placemark>...</Placemark>` blocks) to build the `maps.google.com/?q=LAT,LNG` links. (Observed Aug-2026: KML exported from Drive worked fine as a file upload; the failure was only the export_media call.)
