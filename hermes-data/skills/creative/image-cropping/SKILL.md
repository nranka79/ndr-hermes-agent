---
name: image-cropping
description: Crop or extract a region from a user-uploaded image (screenshot, photo of two screens, document scan, panel) using pure-PIL pixel analysis. Use when the user sends an image and asks to "crop out X", "extract the screen/panel/region", "split the two screens", or "give me just the left/right/top part". Deterministic — no vision model, no numpy required.
---

# Image Cropping / Region Extraction (pure PIL)

Recurring DRAAS pattern: Nishant uploads a screenshot/photo containing multiple visual regions (e.g. a photo of two monitors, one big + one small) and wants just one region extracted as a new image.

## Core principle
Find region boundaries by **brightness profiling** with pure PIL (`Image.convert("L")` + `getpixel`). Works when `vision_analyze` is unconfigured ("No LLM provider configured for task=vision") and when numpy is broken in the venv. Pure PIL is enough — do not block on either dependency.

## Where the uploaded image lives
Telegram uploads land in `/data/hermes/image_cache/img_*.jpg`. Check there first when the user says they sent an image (don't just search /opt/data — that's the workdir, uploads go to image_cache).

## Workflow (numbered, exact code patterns)

1. **Load + inspect**
```python
from PIL import Image
img = Image.open("/data/hermes/image_cache/img_xxx.jpg")
print(img.size, img.mode)   # e.g. (1280, 593) RGB
g = img.convert("L")
w, h = img.size
```

2. **Column brightness profile** → finds VERTICAL boundaries (where one screen ends, gap begins, next screen starts)
```python
col_sums = [0]*w
for y in range(0, h, 4):
    for x, v in enumerate(g.crop((0, y, w, y+1)).getdata()):
        col_sums[x] += v
col_mean = [s/(len(range(0,h,4))) for s in col_sums]
```
Print `col_mean` at coarse steps (w//100) to see the structure. Look for: sustained low (screen content), near-white spikes (~250, bezel edge), near-black troughs (gap between screens), brightness level shifts.

3. **Row brightness profile** → finds HORIZONTAL boundaries (environment band above screens, black bars, content top/bottom)
```python
row_mean = []
for y in range(h):
    row_mean.append(sum(g.getpixel((x, y)) for x in range(0, w, 4)) / (w//4))
```
Print every ~20 rows. A bright band (250) at the top that drops sharply (~113 → ~90) = environment (ceiling/wall), NOT screen — exclude it from the crop.

4. **ASCII brightness map** — instant layout sanity check without vision
```python
for y in range(0, h, h//24):
    line = ""
    for x in range(0, w, 10):
        v = g.getpixel((x, y))
        line += " " if v < 40 else ("." if v < 90 else ("o" if v < 140 else "#"))
    print(f"{y:3d} {line}")
```
One glance shows: left screen content vs right screen content vs gaps vs top band.

5. **Fine-scan the transition zone** — per row-band, NOT one scan line (a single y can mislead)
```python
def col_profile(y0, y1):
    return [(x, sum(g.getpixel((x,y)) for y in range(y0,y1,2)) / len(range(y0,y1,2)))
            for x in range(760, 920)]
```
Run for top/mid/bottom bands separately. Each band's last brightness jump marks the boundary. Transitions of Δ>20 identify edges.

6. **RGB disambiguation at the boundary** — bezel vs gap vs screen content
At the boundary columns, sample actual RGB: `img.getpixel((x, y))`.
- Near-white (245-255, all channels) = bezel / bright screen edge
- Near-black (5-40) = gap between screens / bezel shadow
- Content tones = still inside the screen
This distinguishes "bright strip at x=830-834 is the left screen's edge" from "dark gap x=835-855 separates the screens".

7. **Crop + save + deliver**
```python
crop = img.crop((x0, y0, x1, y1))   # (left, top, right, bottom)
crop.save(out_png, "PNG")
crop.save(out_jpg, "JPEG", quality=95)
```
Deliver with `MEDIA:/abs/path.png` in the response. State the crop box explicitly in the reply so the user can ask for adjustments.

## Verification
- Print crop size and sample edge pixels: `crop.getpixel((crop.width-1, y))` should be screen content, not gap/next-screen bleed.
- Sample the crop's top row to confirm the environment band was excluded.

## Pitfalls
- **Don't assume which side is brighter/bigger** — "bigger screen" does not mean "higher brightness". Use the profiles; the right screen in a photo may be bright white while the left shows dark content.
- **Two transitions at each boundary**: screen content → bright bezel strip → dark gap → next screen. The dark gap is the reliable separator; the bright strip belongs to the screen being cropped.
- **Environment bands** (bright ceiling above a desk of monitors) span the full width at the top. Exclude them via the row profile; screen content starts where the mean drops below ~120.
- **numpy import may fail** (`ModuleNotFoundError: numpy._core._multiarray_umath` on aarch64 venv). The pure-PIL approach never needs it.
- **vision_analyze may error** if no vision provider is configured. Do not retry in a loop — pixel analysis is deterministic and usually enough for crop tasks. If the user actually needs content understanding (OCR/description), then escalate to vision config.
- **Uploaded file location**: always check `/data/hermes/image_cache/` before assuming the image didn't arrive.

## References
- `references/two-screen-crop-example.md` — worked example: photo of big-left + small-right monitors, exact boundary numbers.
