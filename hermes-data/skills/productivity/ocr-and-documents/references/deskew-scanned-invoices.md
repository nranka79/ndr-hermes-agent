# Deskew scanned invoices (sub-degree skew) — working recipe

Verified 2026-08-25 on a 3-page Adobe Scan of Mythri Pharmaceuticals tax invoices (full-bleed, portrait, upright, ~0.2–0.5° skew). Goal: "rotate the pages and make them straight", rename, file, attach to a claim email.

## Environment

```bash
uv pip install --python /opt/hermes/.venv/bin/python opencv-python-headless img2pdf
# adds: opencv-python-headless, numpy, img2pdf, pikepdf
```

## Decision flow

1. `pdfinfo -f 1 -l 3 file.pdf` — check `Pages`, `Page N rot:` (0 = no /Rotate), page size vs embedded image size. Use pymupdf to confirm embedded image dims are portrait ≈ page ratio → full-bleed upright scan, only fine skew.
2. Render at 300 dpi (`page.get_pixmap(dpi=300, colorspace=pymupdf.csRGB)`), deskew each page, JPEG-compress, rebuild with img2pdf.

## Skew angle detection — the three methods in practice

```python
# (a) minAreaRect — DO NOT trust alone: full-bleed rectangular text blobs return ~0
import cv2, numpy as np
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
coords = cv2.findNonZero(thresh)
# angle from cv2.minAreaRect(coords) -> 0.00 on retail invoice layouts; useless here

# (b) projection-profile: maximise variance of rotated image's row sums
def find_skew_angle(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    h, w = thresh.shape
    m = int(min(h, w) * 0.06)
    crop = thresh[m:h-m, m:w-m]
    best_angle, best_score = 0.0, -1.0
    for ang in np.arange(-6.0, 6.01, 0.2):
        M = cv2.getRotationMatrix2D((crop.shape[1] / 2, crop.shape[0] / 2), ang, 1.0)
        rot = cv2.warpAffine(crop, M, (crop.shape[1], crop.shape[0]),
                             flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        score = rot.sum(axis=1).var()
        if score > best_score:
            best_score, best_angle = score, ang
    return best_angle   # typically -0.4..0.4 for these scans (mild, under-corrects)

# (c) Hough on long table lines — most robust for invoice grids
def hough_skew(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    cands = []
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 25, 12)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (90, 1))
    cands.append(cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel))  # horizontal lines only
    cands.append(cv2.Canny(gray, 40, 130))
    min_len = int(gray.shape[1] * 0.3)
    angs, total = [], 0
    for edge in cands:
        lines = cv2.HoughLinesP(edge, 1, np.pi / 720, threshold=100,
                                minLineLength=min_len, maxLineGap=15)
        if lines is None:
            continue
        lines = np.asarray(lines)
        if lines.ndim == 3:      # OpenCV 4 shape (N,1,4)
            lines = lines[:, 0, :]
        # OpenCV 5 returns (N,4) — the flatten above handles it; iterating gives 4-tuples
        for x1, y1, x2, y2 in lines.astype(int):
            if np.hypot(x2 - x1, y2 - y1) < min_len * 0.8:
                continue
            ang = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            if ang > 90: ang -= 180
            if ang < -90: ang += 180
            if abs(ang) < 25:
                angs.append(ang); total += 1
    return (float(np.median(angs)), total) if angs else (0.0, 0)
```

**Key judgement:** if BOTH (b) and (c) return <0.5° while the vision model "sees" 1–2° (and contradicts itself call-to-call: first clockwise, then counter-clockwise), trust the CV methods — the doc is effectively straight. Apply the detected rotation, rebuild, verify, ship.

## Rotation + rebuild

```python
def rotate_img(img, angle):
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)

# per page: fixed = rotate_img(img, angle)
# add white margin, JPEG q92 (NOT PNG — PNG at 300dpi ~10MB vs JPEG ~3.5MB):
img = cv2.copyMakeBorder(fixed, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=[255, 255, 255])
cv2.imwrite(page_jpg, img, [cv2.IMWRITE_JPEG_QUALITY, 92])

# rebuild PDF:
import img2pdf
with open(out_pdf, "wb") as f:
    f.write(img2pdf.convert([page1_jpg, page2_jpg, page3_jpg]))
```

## Verify before filing

- `pdftoppm -png -r 150 out.pdf check` then `vision_analyze` on page 1: upright, clean, no border clipping.
- OCR the rebuilt PDF pages to confirm invoice fields survived (pharmacy, invoice no., totals).
- If delivering to a claim email: rename per drive convention (`20260825_Entity_Description.pdf`, underscores only), upload to the patient's `Invoices` subfolder, add the row(s) to the invoice index sheet (insert ABOVE the TOTAL row, then extend `=sum(...)` ranges), then attach to the draft.