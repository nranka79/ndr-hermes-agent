#!/usr/bin/env python3
"""Compress a scanned PDF dossier so it fits Telegram/WhatsApp delivery (<50 MB).

Usage:
  python3 compress_dossier.py <input.pdf> [output.pdf] [dpi] [quality]

Defaults: dpi=120, quality=55. Rasterizes only pages that look like scans
(little text + images present); keeps text/vector pages as-is.

IMPORTANT: use PIL JPEG streams — pymupdf `insert_image(rect, pixmap=pix)`
stores inserted pixmaps uncompressed and can make the file BIGGER.
"""
import pymupdf, os, sys, io
from PIL import Image


def main():
    if len(sys.argv) < 2:
        print("Usage: compress_dossier.py <input.pdf> [output.pdf] [dpi] [quality]")
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src.replace(".pdf", "_compressed.pdf")
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    quality = int(sys.argv[4]) if len(sys.argv) > 4 else 55

    doc = pymupdf.open(src)
    out = pymupdf.open()
    total = len(doc)

    for i, page in enumerate(doc):
        text = page.get_text().strip()
        images = page.get_images(full=True)
        is_scan = (len(text) < 80 and len(images) > 0) or (len(images) > 0 and len(text) < 300)
        if is_scan:
            pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
            newpage = out.new_page(width=page.rect.width, height=page.rect.height)
            newpage.insert_image(newpage.rect, stream=buf.getvalue())
        else:
            out.insert_pdf(doc, from_page=i, to_page=i)
        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{total}")

    out.save(dst, deflate=True, garbage=3)
    orig, new = os.path.getsize(src), os.path.getsize(dst)
    print(f"\nOriginal: {orig/1e6:.1f} MB -> Compressed: {new/1e6:.1f} MB  ({(1-new/orig)*100:.0f}% smaller)")
    out.close()
    doc.close()


if __name__ == "__main__":
    main()