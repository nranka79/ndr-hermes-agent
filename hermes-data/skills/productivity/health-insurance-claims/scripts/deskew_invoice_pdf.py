#!/usr/bin/env python3
"""Deskew a scanned invoice/medical PDF and rebuild it straight.

Usage:
    /opt/hermes/.venv/bin/python3 deskew_invoice_pdf.py input.pdf output.pdf [dpi]

Deps (hermes venv): pymupdf, opencv-python-headless, numpy, img2pdf
    uv pip install --python /opt/hermes/.venv/bin/python opencv-python-headless img2pdf

Method:
  1. Render each page at 300 dpi (default).
  2. Detect skew angle per page:
     - Primary: Hough line detection on the invoice's own long horizontal table lines.
     - Fallback: projection-profile variance maximisation (radon-style) if no lines found.
  3. Rotate with cv2.warpAffine (INTER_CUBIC, replicate border).
  4. Export pages as JPEG (quality ~92) and rebuild with img2pdf — PNG pages bloat the
     output to ~10 MB; JPEG keeps ~3-4 MB at legible 300 dpi.

Pitfalls learned:
  - cv2.minAreaRect returns 0 deg on whole-page invoice blobs (blob is rectangular).
  - Vision-model tilt estimates are unreliable below ~1 deg (they flip CW vs CCW).
    Trust two agreeing CV methods (Hough + projection); verify by re-rendering one
    page and asking vision "is it straight now".
"""
import sys, os
import cv2
import numpy as np
import pymupdf
import img2pdf


def hough_skew(img):
    """Median angle of long near-horizontal table/text lines. Shape-robust for OpenCV 5."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    cands = []
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 25, 12)
    horiz = cv2.morphologyEx(thresh, cv2.MORPH_OPEN,
                             cv2.getStructuringElement(cv2.MORPH_RECT, (90, 1)))
    cands.append(horiz)
    cands.append(cv2.Canny(gray, 40, 130))
    min_len = int(gray.shape[1] * 0.3)
    angs, total = [], 0
    for edge in cands:
        lines = cv2.HoughLinesP(edge, 1, np.pi / 720, threshold=100,
                                minLineLength=min_len, maxLineGap=15)
        if lines is None:
            continue
        lines = np.asarray(lines)
        if lines.ndim == 3:
            lines = lines[:, 0, :]
        for ln in lines:
            x1, y1, x2, y2 = map(int, ln)
            if np.hypot(x2 - x1, y2 - y1) < min_len * 0.8:
                continue
            a = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            if a > 90: a -= 180
            if a < -90: a += 180
            if abs(a) < 25:
                angs.append(a)
                total += 1
    return (float(np.median(angs)) if angs else 0.0), total


def projection_skew(img):
    """Radon-style fallback: angle maximising variance of horizontal projection."""
    gray = cv2.medianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 5)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    h, w = thresh.shape
    m = int(min(h, w) * 0.06)
    crop = thresh[m:h - m, m:w - m]
    best, score = 0.0, -1.0
    for ang in np.arange(-6.0, 6.01, 0.2):
        M = cv2.getRotationMatrix2D((crop.shape[1] / 2, crop.shape[0] / 2), ang, 1.0)
        rot = cv2.warpAffine(crop, M, (crop.shape[1], crop.shape[0]),
                             flags=cv2.INTER_LINEAR, borderValue=0)
        s = rot.sum(axis=1).var()
        if s > score:
            score, best = s, ang
    return best


def rotate_img(img, angle):
    if abs(angle) < 0.05:
        return img
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    out_dir = os.path.join(os.path.dirname(dst) or '.', '.deskew_tmp')
    os.makedirs(out_dir, exist_ok=True)

    doc = pymupdf.open(src)
    jpgs = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        ang, n = hough_skew(img)
        if n == 0:
            ang = projection_skew(img)
        fixed = rotate_img(img, ang)
        if ang < 0.05:
            print(f"page {i+1}: angle ~0 ({n} lines) — no rotation applied")
        else:
            print(f"page {i+1}: deskew {ang:.2f} deg ({n} lines)")
        fixed = cv2.copyMakeBorder(fixed, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=[255, 255, 255])
        jpg = os.path.join(out_dir, f"page-{i+1:02d}.jpg")
        cv2.imwrite(jpg, fixed, [cv2.IMWRITE_JPEG_QUALITY, 92])
        jpgs.append(jpg)
    doc.close()

    with open(dst, "wb") as f:
        f.write(img2pdf.convert(jpgs))
    print(f"PDF: {dst} ({os.path.getsize(dst):,} bytes)")


if __name__ == "__main__":
    main()