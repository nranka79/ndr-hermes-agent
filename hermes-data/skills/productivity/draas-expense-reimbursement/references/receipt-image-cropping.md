# Receipt image cropping — pure-PIL recipe

When a user sends a photo of a receipt (thermal slip, invoice, card payment
voucher) and asks to "crop it" before filing, the naive approach fails and this
recipe works. Verified 2026-08-11 on a Maverick & Farmer Coffee card voucher.

## Why naive cropping fails

```python
gray.point(lambda p: 0 if p < 245 else 255).getbbox()  # → None
```

On a photo of a receipt lying on a dark table/surface, the whole frame has
mid-gray values (extrema ~(1, 221), mean ~140) — there is no clean white
background, so simple content-vs-white thresholding finds "everything" (bbox =
full frame) or "nothing" (None). You must profile darkness row-by-row and
column-by-column to locate the receipt zone.

## The recipe

### 1. Row + column darkness profiles (pure PIL, no numpy)

```python
from PIL import Image, ImageOps, ImageStat

im = Image.open(SRC).convert("RGB")
w, h = im.size
gray = ImageOps.grayscale(im)
dark = gray.point(lambda p: 255 - p)  # darkness image (0=white, 255=black)

step = 20
for y in range(0, h, step):                       # row profile
    row = dark.crop((0, y, w, min(y + step, h)))
    print(y, ImageStat.Stat(row).mean[0])

step = 16
for x in range(0, w, step):                       # column profile
    col = dark.crop((x, 0, min(x + step, w), h))
    print(x, ImageStat.Stat(col).mean[0])
```

Read the two profiles: the receipt zone is the vertical span where row darkness
drops from the background level, and the horizontal span where column darkness
drops. In the verified case: content was x≈40–595, y≈100–1180 on a 721×1280
frame; the surrounding bands (dark table) sat at ~140–186 darkness.

### 2. Crop + fix lighting + export PDF

```python
im = im.crop((38, 98, 598, 1182))                 # content zone + small margin
im = ImageOps.autocontrast(im, cutoff=1)          # fixes gray cast
im = ImageEnhance.Contrast(im).enhance(1.15)
im = ImageEnhance.Brightness(im).enhance(1.05)
im = im.filter(ImageFilter.SHARPEN)               # text legibility
im.save(OUT_JPG, "JPEG", quality=95)
im.convert("RGB").save(OUT_PDF, "PDF", resolution=200)
```

### 3. Verify before filing (non-negotiable)

Re-run `vision_analyze(image_url=cropped_jpg)` and confirm amount, vendor,
date, and invoice no. all survived the crop. Only then upload the PDF to
Kelsa/Drive. A crop that cuts the ₹ amount is worse than no crop.

## Pitfalls

- `ImageStat.Stat` on a row crop is cheap; no need to downscale first.
- If the receipt is a clean scan (white background), the simple
  `getbbox()`-on-inverted-image DOES work — try it first, fall back to
  profiling only when it returns None or the full frame.
- Keep a margin (~10–15px) around the detected zone so descenders and receipt
  edges don't get clipped.
- The `vision_analyze` OCR path works without any vision model configured —
  the tool returns `"method": "ocr"` for text extraction. The visual-description
  fallback (needs a configured vision provider) may fail; that does NOT mean
  OCR extraction is broken.
