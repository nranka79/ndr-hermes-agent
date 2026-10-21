#!/usr/bin/env python3
"""A4 page + band-collision checker for page-exact HTML->PDF replicas.

Built for the K-RERA QU form replicas (see
`references/krera-qu-forms-html-replica.md`), but generic to any build where a
letterhead/footer band is an absolutely-positioned image on a fixed-size sheet.

WHAT IT CATCHES
  * a page that is not A4            -> prints as an extra/odd sheet
  * the `min-height` footer trap     -> the footer band printing THROUGH body text

That second one is the reason this script exists. `min-height: 297mm` does not
give an absolutely-positioned child a 297mm containing block in WeasyPrint, so
`bottom: 18.35mm` resolves against CONTENT height and the footer lands mid-page,
on top of the text. Page count, page size and any PNG-headroom check all pass.
Only rect-level geometry finds it. (Verified 2026-10-05, Ranka Amber Form-4:
footer at y564.7-586.7 while text ran to y637.6, on all 8 pages.)

Note: do NOT try to eyeball this with a vision model. Asked directly whether the
footer overlapped the text, vision_analyze answered "cleanly separated, no
overlap" on the broken build.

USAGE
    /opt/hermes/.venv/bin/python3 a4_page_band_check.py preview.pdf
    /opt/hermes/.venv/bin/python3 a4_page_band_check.py preview.pdf --expect-pages 8
    /opt/hermes/.venv/bin/python3 a4_page_band_check.py preview.pdf --headroom-warn 20

Exit code 0 = clean, 1 = at least one failure. Prints one line per page.

Interpreter: /opt/hermes/.venv/bin/python3 (has pymupdf). The system python is
PEP-668 managed and has no pymupdf.
"""
from __future__ import annotations

import argparse
import sys

try:
    import pymupdf
except ImportError:  # older wheels
    import fitz as pymupdf  # type: ignore

# A4 portrait in PostScript points.
A4_W, A4_H = 595.276, 841.890


def text_blocks(page):
    """Non-empty text blocks as (x0, y0, x1, y1, text)."""
    return [b for b in page.get_text("blocks") if b[4].strip()]


def image_bands(page):
    """Image rects on the page, sorted top-to-bottom."""
    rects = []
    for img in page.get_images(full=True):
        rects.extend(page.get_image_rects(img[0]))
    rects.sort(key=lambda r: r.y0)
    return rects


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--expect-pages", type=int, default=None,
                    help="fail if the page count differs (the printing proof)")
    ap.add_argument("--tol", type=float, default=1.0,
                    help="A4 page-size tolerance in points (default 1.0)")
    ap.add_argument("--headroom-warn", type=float, default=20.0,
                    help="warn when body ink ends within N pt of the footer band top "
                         "(default 20; treat <20pt as a defect)")
    args = ap.parse_args()

    doc = pymupdf.open(args.pdf)
    failures: list[str] = []
    warnings: list[str] = []

    if args.expect_pages is not None and doc.page_count != args.expect_pages:
        failures.append(f"page count {doc.page_count} != expected {args.expect_pages}")

    for page in doc:
        n = page.number + 1
        w, h = page.rect.width, page.rect.height

        # --- 1. sheet size -------------------------------------------------
        sized = abs(w - A4_W) <= args.tol and abs(h - A4_H) <= args.tol
        if not sized:
            failures.append(f"pg{n}: not A4 (got {w:.1f}x{h:.1f}, want {A4_W:.1f}x{A4_H:.1f})")

        bands = image_bands(page)
        blocks = text_blocks(page)

        if not bands or not blocks:
            print(f"pg{n}: {w:.0f}x{h:.0f} A4={'Y' if sized else 'N'} "
                  f"(no band/text pair to check)")
            continue

        header, footer = bands[0], bands[-1]
        text_top = min(b[1] for b in blocks)
        text_bot = max(b[3] for b in blocks)

        # --- 2. collision: any text block intersecting a band --------------
        collisions = []
        for b in blocks:
            for label, band in (("header", header), ("footer", footer)):
                if not (b[3] <= band.y0 or b[1] >= band.y1):
                    collisions.append((label, band, b))
        for label, band, b in collisions[:3]:
            failures.append(
                f"pg{n}: text intersects the {label} band -> {b[4].strip()[:52]!r} "
                f"(text y{b[1]:.0f}-{b[3]:.0f} vs {label} y{band.y0:.0f}-{band.y1:.0f})"
            )
        if len(collisions) > 3:
            failures.append(f"pg{n}: ...and {len(collisions) - 3} more collision(s)")

        # --- 3. headroom between last body ink and the footer band ---------
        headroom = footer.y0 - text_bot
        if headroom < args.headroom_warn:
            warnings.append(
                f"pg{n}: only {headroom:.0f}pt headroom above the footer band "
                f"(< {args.headroom_warn:.0f}pt — one font-metric drift from a 9th sheet)")

        print(f"pg{n}: {w:.0f}x{h:.0f} A4={'Y' if sized else 'N'} | "
              f"header y{header.y0:.0f}-{header.y1:.0f} footer y{footer.y0:.0f}-{footer.y1:.0f} | "
              f"text y{text_top:.0f}-{text_bot:.0f} | headroom {headroom:.0f}pt | "
              f"collisions {len(collisions)}")

    print("-" * 72)
    for msg in warnings:
        print(f"WARN {msg}")
    for msg in failures:
        print(f"FAIL {msg}")

    if failures:
        print(f"\n{len(failures)} FAILURE(S) — do NOT publish this build.")
        return 1
    print(f"\nCLEAN: {doc.page_count} page(s), A4, no band collisions."
          + (f" ({len(warnings)} warning(s).)" if warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
