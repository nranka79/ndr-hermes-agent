# Clone & Adapt a Presentation for a Different Project

When the user says "make a presentation like [Project X] but for [Project Y]" — cloning the structure/theme of an existing deck and adapting it for a new land/project.

## When to use

- User provides an existing presentation (Drive link or file ID) and wants the same format/pattern for a different project
- Same corridor/market — competitive landscape slides can be largely reused
- Only title slides, land details, location advantages, and project-specific analysis change

## Workflow

### 1. Download the source presentation

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseDownload
import io

drive = build_service('drive', 'v3', service_name='google-draas')
request = drive.files().get_media(fileId='SOURCE_PPTX_ID')
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()

with open('/tmp/template.pptx', 'wb') as f:
    f.write(fh.getvalue())
```

### 2. Analyze the template structure first

```python
from pptx import Presentation

prs = Presentation('/tmp/template.pptx')
for idx, slide in enumerate(prs.slides):
    for shape in slide.shapes:
        if shape.has_text_frame:
            print(f"S{idx+1}: {shape.text_frame.text[:80]}")
```

Identify which slides are:
- **Project-specific** (title, flagship/land details, price comparison) → modify
- **Reusable** (competitive landscape, section dividers) → keep as-is
- **New slides needed** (location advantages, development scenarios) → add

### 3. Modify existing slides (text replacement)

Work slide-by-slide using `slide.shapes` iteration. Replace text at the **run level** (preserves formatting):

```python
slide = prs.slides[0]  # Title slide
for shape in slide.shapes:
    if shape.has_text_frame:
        for para in shape.text_frame.paragraphs:
            for run in para.runs:
                if 'ORIGINAL PROJECT NAME' in run.text:
                    run.text = run.text.replace('ORIGINAL PROJECT NAME', 'NEW PROJECT NAME')
                elif 'ORIGINAL DETAILS' in run.text:
                    run.text = run.text.replace('ORIGINAL DETAILS', 'NEW DETAILS')
```

**Pitfall:** This only works if the runs contain identifiable text fragments. If the text is split across runs unpredictably, examine the XML structure first.

### 4. Add new slides with matching styling

Use the **Blank layout** (`prs.slide_layouts[6]`) and manually apply the template's styling:

```python
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

layout = prs.slide_layouts[6]  # Blank
slide = prs.slides.add_slide(layout)

# Dark navy background (matching Ranka Oasis theme)
bg = slide.background.fill
bg.solid()
bg.fore_color.rgb = RGBColor(0x0D, 0x2B, 0x3E)

# Gold accent line at top
accent = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, Emu(0), Emu(0), prs.slide_width, Emu(50000)
)
accent.fill.solid()
accent.fill.fore_color.rgb = RGBColor(0xE8, 0x9C, 0x31)
accent.line.fill.background()

# Title text box
tb = slide.shapes.add_textbox(Emu(685800), Emu(400000), Emu(10500000), Emu(800000))
p = tb.text_frame.paragraphs[0]
p.text = "Slide Title"
p.font.size = Pt(32)
p.font.bold = True
p.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

# Bullet items
y = 1350000
for item in ["• Item 1", "• Item 2", "• Item 3"]:
    tb = slide.shapes.add_textbox(Emu(685800), Emu(y), Emu(10500000), Emu(500000))
    p = tb.text_frame.paragraphs[0]
    p.text = item
    p.font.size = Pt(16)
    p.font.color.rgb = RGBColor(0xDD, 0xDD, 0xDD)
    y += 420000
```

### 5. Reorder slides via XML manipulation

python-pptx's `Slide.reorder()` doesn't exist directly. Use the low-level XML:

```python
sldIdLst = prs.slides._sldIdLst
elements = list(sldIdLst)

# New slides are at the end; rest are existing
new_elements = elements[-N:]  # N = number of new slides
rest = elements[:-N]

# Insert new slides at desired positions (0-indexed)
result = []
for i, elem in enumerate(rest):
    result.append(elem)
    if i == target_after_index:  # after this existing slide
        for new_elem in new_elements:
            result.append(new_elem)

# Rebuild the XML
for elem in elements:
    sldIdLst.remove(elem)
for elem in result:
    sldIdLst.append(elem)
```

**Pitfall:** Inserting multiple new slides at once requires planning insertion order. Insert in reverse position order (last insertion first) to avoid position shifting.

### 6. Update section dividers (if keeping them)

If the template had section divider slides for categories (Villas / Apartments / Plotted), update their subtitles to reference the new project location:

```python
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame and 'Sarjapur Corridor' in shape.text_frame.text:
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    if 'Sarjapur Corridor' in run.text:
                        run.text = run.text.replace('Sarjapur Corridor', 'New Location')
```

### 7. Upload and convert to Google Slides

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload(
    '/tmp/new_deck.pptx',
    mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
    resumable=True
)

file_meta = {
    'name': 'PROJECT — Market Analysis — Jul 2026',
    'mimeType': 'application/vnd.google-apps.presentation'
}

uploaded = drive.files().create(
    body=file_meta, media_body=media, fields='id,name,webViewLink'
).execute()

print(f"Link: {uploaded['webViewLink']}")
```

### 8. Verify slide structure

After uploading, re-verify by checking the saved file:

```python
prs2 = Presentation('/tmp/new_deck.pptx')
for idx, slide in enumerate(prs2.slides):
    texts = [s.text_frame.text[:60] for s in slide.shapes if s.has_text_frame and s.text_frame.text.strip()]
    print(f"S{idx+1}: {texts[0] if texts else '(empty)'}")
```

## Common pitfalls

- **Run-level text replacement fails** if the source text is split across multiple runs (common with templated slides). Check `len(para.runs)` — if >1, the string might be fragmented. Alternative: replace at the paragraph level with `para.clear()` + `para.add_run()`.
- **New slides don't match the visual style** if you don't apply the same background color + accent elements. Always check the template's dominant colors first.
- **Slide insertion shifts indices** when inserting multiple slides sequentially. Insert in reverse order (last position first) or use the bulk reorder pattern above.
- **Drive upload creates size=0 file** if the upload silently fails — always verify `uploaded.get('size')` before delivering the link.
- **Conversion to Google Slides drops some formatting** — complex tables, specific fonts, or overlapping elements may render differently. Test with `browser_navigate` before declaring success.

## Rebinding a clone to a new parcel: the global-replace trap

Cloning an existing deck and doing a global run-level text replace (`OLD PROJECT` → `NEW PROJECT`) is fast but creates semantic errors you must sweep for. From the Nandi Hills ← Thylagere clone (Aug 2026):

1. **Fix place names after global replace.** `"Thylagere Village"` → `"Nandi Hills Village"` is wrong (the parcel is not a village). Replace title lines to `"NANDI HILLS (Subject Land)"`. Also sweep for **hobli/taluk strings inherited from the old parcel** — `"Kundana Hobaly, Devanahalli Taluk"` is the old parcel's hobli and does NOT apply to the new one; replace with the new parcel's own administrative string.
2. **Sweep every distance/proximity claim.** The old deck's distances (e.g. `"Nandi Hills — 15 km"` on the Subject Land Overview, `"15 km | Premium villa belt"` on the Location USP) describe the OLD parcel. If the new parcel IS on that corridor, rewrite to `"Subject land on corridor | Premium villa belt"` — never leave the inherited km figure. Search the whole deck for `km` and `corridor` after rebinding.
3. **Survey numbers list must be replaced, not carried.** The old deck lists the old parcel's survey numbers (`129, 132/1-26, ...`). The new sketch's numbers are usually NOT readable from a hand photo — **do not fabricate survey numbers**. Write what's verifiable: `"Survey Numbers: As per joint sketch — Plots 1–7 (scale 1" = 100')"`.
4. **Verify the original project name is gone** — grep the final PPTX for the old name (incl. uppercase variant) before upload.

## Replacing an embedded picture in place (fit-box math)

When the template slide already contains a picture (e.g. the old joint sketch) and you swap in a new one:

```python
old_pic = None
for shape in slide.shapes:
    if shape.shape_type == 13:  # PICTURE
        old_pic = shape
        break
if old_pic is not None:
    sp = old_pic._element
    sp.getparent().remove(sp)          # remove old picture shape

from PIL import Image
img = Image.open(new_sketch_path)
iw, ih = img.size
target_w = int(slide_width * 0.52)     # ~52% of slide width
target_h = int(slide_height * 0.80)    # ~80% of slide height
scale = min(target_w / iw, target_h / ih)
new_w, new_h = int(iw * scale), int(ih * scale)
left = int(slide_width * 0.46)         # right column, survey card is left
top = int(slide_height * 0.14)
slide.shapes.add_picture(new_sketch_path, left, top, new_w, new_h)
```

If the new image is portrait and the old slot was landscape, do NOT reuse the old picture box dimensions — compute fit-box as above, otherwise the sketch crops or leaves a huge gap.

## Resolving a Google Maps short link to coordinates

The user often drops a `maps.app.goo.gl/...` link for the subject land. Resolve it cheaply without a browser:

```bash
curl -s -o /dev/null -w "%{url_effective}\n" "https://maps.app.goo.gl/W4AFbjrgAcxp7Q8z6"
```

The redirected URL contains the pin coordinates as `!3d<lat>!4d<lng>` (e.g. `!3d13.329655!4d77.600761`) and the `@lat,lng` viewport. Use this to confirm the parcel sits next to the old deck's parcel before claiming "same corridor" (this justified reusing the competitive-landscape slides).

## Verify the clone before delivering

Export the uploaded deck to PDF and render the changed slides to PNG for a vision check (the local host has no LibreOffice, so export via Drive is the reliable path):

```python
pdf = drive.files().export(fileId=slides_id, mimeType='application/pdf').execute()
with open('/tmp/deck.pdf', 'wb') as f:
    f.write(pdf)
# then: fitz (PyMuPDF) render slides 1, 3, 4 → vision_analyze each
```

Look for: sketch not cropped, sketch upright (see `land-survey-sketch-integration.md`), text not overlapping the image, no leftover old-project strings.

## Adding executive-summary slides at the start of a clone

When the user asks for "a summary of the land + development potential + launch price + sales velocity + current land prices" up front, build 3 summary slides and insert them right after the title (positions 2, 3, 4). Reorder trick: python-pptx appends new slides at the END, then you rebuild `_sldIdLst` so `[title] + [new1, new2, new3] + [rest]`:

```python
xml_slides = prs.slides._sldIdLst
slides = list(xml_slides)
new_ids = slides[-3:]      # the 3 appended summary slides
old_ids = slides[:-3]
desired = [old_ids[0]] + new_ids + old_ids[1:]
for sldId in slides:
    xml_slides.remove(sldId)
for sldId in desired:
    xml_slides.append(sldId)
```

Then re-upload as a new Google Slides file (delete the old one first, then create fresh — same name with (v2) suffix so the user can tell versions apart).

**Land-price summary content pattern** (proven Aug 2026, Nandi Hills deck): slide 1 = land at a glance (parcel/location/survey/corridor/connectivity) + development potential card (recommended model, price positioning, plot inventory, est. revenue, buyer pool, catalysts); slide 2 = launch price list with 3 benchmark rows + expected sales velocity card (corridor demand, monthly absorption, sell-out horizon, levers, caveat); slide 3 = government/registry data column (KIADB compensation, guidance values, guidance-vs-market gap, portal to verify) + market-transaction column (per-acre recent deals) + a footer note with the implied value range and the "verify on Kaveri before any offer" caveat.

## Adding user-provided survey numbers + extents to the title slide

Follow-up pattern (Aug 2026, Nandi Hills deck): after delivering the deck, the user drops the real survey list in **A-G bracket shorthand** — `75 (1A28G), 76 (2A02G), 76 (1A15G), 76 Hissa 8 (2A02G), 76 (1A10G), 76 (1A20G)` — and asks to add it "in the first page".

**Decode before placing:**
- Notation: `SyNo (AcreGunta)` — `1A28G` = 1 acre 28 guntas; 40 guntas = 1 acre → 1 + 28/40 = **1.70 ac**. `76 Hissa 8` = Sy 76, subdivision (hissa) 8.
- Sum all extents and compare against the deck's acreage claim. This parcel: 1.70 + 2.05 + 1.375 + 2.05 + 1.25 + 1.50 = **9.925 ac ≈ 9.93** → consistent with "~10 Acres" branding. State the total on the slide (`Total Extent: 9.93 Acres (~10 Acres)`) — it validates the title.

**Positioning (pitfall — proportional fractions overlap):** the title slide has a fixed gap between the tagline line (e.g. `~10 Acres | ...` ending ≈3,850,000 EMU) and the date line (`July 2026 | ...` starting ≈4,572,000 EMU). First attempt with `int(SH*0.585)` / `int(SH*0.645)` put the Total line INTO the date line. Fix: use **absolute EMU positions** — survey line at `4000000` (H `250000`), total line at `4290000` (H `250000`). Both fit inside the 722,000 EMU gap. Verify with `pdftoppm` + `vision_analyze` that both lines render fully and nothing overlaps the date line.

## Upload interpreter (pitfall)

The python-pptx build venv (`/opt/data/pptxenv/bin/python`) has **no `googleapiclient`** — an upload script run through it dies with `ModuleNotFoundError: No module named 'googleapiclient'`. Run Drive-upload scripts with **`/usr/bin/python3`** (or `/opt/hermes/.venv/bin/python`) — both have googleapiclient. Keep the build step (python-pptx) in pptxenv and the upload step in system python; don't merge the two venvs.

## The vision-QA clipping loop (summary slides)

Summary slides are text-box-dense and the FIRST render WILL have clipping. The loop that worked:

1. Upload → export PDF via Drive → `fitz` render the 3 new slides at **110–120 dpi** (`get_pixmap(dpi=110)`).
2. `vision_analyze` with `also_describe_visually=true`, asking explicitly "is the title fully readable / any clipped or overlapping text?".
3. Fix the specific bugs (below), rebuild, re-upload (delete + create), re-render ONLY the affected slides, re-check. Never declare done after one pass.

**Clipping bugs actually hit (all real, all caught by this loop):**
- **Title box too narrow → wraps to 2 lines → second line clipped** ("Sales Velocity" became "Sales Velocit", "Potential" lost its tail). Fix: shorten the title to fit ONE line (e.g. "Launch Price & Velocity" instead of "Launch Price & Expected Sales Velocity"), widen the title box to ≤0.72×slide width so it never reaches the SUMMARY chip, and raise the box height (0.12×SH) so even a wrap isn't clipped.
- **Value column too narrow → last word clipped at the box edge** ("premium brands" rendered "premiur" — word split mid-letter). Fix: widen the value column and/or reduce the value font 12→11.5pt; when in doubt shorten the string rather than widening, since the right card boundary is fixed.
- **Footer note at bottom edge clipped on the right** — the note is long and wraps past the slide edge. Fix: shorten the note text, cap width ≤0.80×slide width, keep it one visual line.
- **OCR can misread a clean word** ("premium" → "premiur" reported even after fix). When the model still flags a word after widening, render a **zoomed crop** of just that row (`page.get_pixmap(dpi=200, clip=fitz.Rect(x0,y0,x1,y1))`) and re-check before changing anything else.
- **Long section-header chip text clips inside its navy bar** — keep chip labels short (e.g. "RECENT NANDI-CORRIDOR DEALS / LISTINGS (2026)" → "RECENT NANDI-CORRIDOR DEALS / LISTINGS (2026)" at 11.5pt, or shorten to "RECENT DEALS / LISTINGS (2026)").
- **Vertical rhythm**: rows of label+value need enough row step (≥0.09×SH) once values wrap to 2 lines; a row step sized for 1-line values clips 2-line values' second line.
