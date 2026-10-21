#!/usr/bin/env python3
"""Content-overflow probe for page-exact HTML -> PDF documents.

COMPANION to `a4_page_band_check.py`, not a replacement.

  * `a4_page_band_check.py` works on the EXPORTED PDF and needs a letterhead/footer
    **image band** to measure against. It is the right tool for the K-RERA QU form
    replicas (Forms 4/5/6), which carry full-width cropped scan bands.
  * THIS script is for documents with **no image bands** — e.g. the K-RERA
    "Checklist for Post Registration" (see
    `references/krera-post-registration-checklist.md`), a plain ruled-table
    document with a text footer. Run band_check on it and every page prints
    "(no band/text pair to check)", i.e. it silently checks nothing.

WHAT IT DOES
  `overflow: hidden` on a fixed-height `.page` CLIPS silently. Page count stays right,
  page size stays right, and the page still looks plausible — the content is just
  gone. So do not measure the clipped build. Instead free the page box and measure
  the real content height.

  1. Textually strip `height: 297mm;` -> `height: auto;` and
     `overflow: hidden;` -> `overflow: visible;` from the stylesheet. Keep the
     per-page `page-break-after: always`, so there is still exactly one output
     sheet per `.page` block.
  2. Render with WeasyPrint.
  3. For each sheet, take the lowest non-empty text bbox and report it in mm.
     Anything past the usable area (default 286 mm — the A4 sheet minus a normal
     footer margin) is an overflow.
  4. Cross-check the sheet count against the `.page` block count.

Proved on Ranka Amber, 2026-10-05: it found page 16 of the checklist at 295.46 mm
(footer sits at 291.5 mm) which the clipped build hid completely. After splitting
that page the worst page fell to 242.09 mm.

INTERPRETER
    /opt/hermes/.venv/bin/python3 a4_content_overflow_probe.py build/index.html
    /opt/hermes/.venv/bin/python3 a4_content_overflow_probe.py build/index.html --limit-mm 286
    /opt/hermes/.venv/bin/python3 a4_content_overflow_probe.py build/index.html --expect-pages 21

Needs weasyprint (render) and pymupdf (measure). Exit 0 = clean, 1 = overflow.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

try:
    import pymupdf
except ImportError:  # older wheels
    import fitz as pymupdf  # type: ignore

from weasyprint import HTML

MM_PER_PT = 25.4 / 72.0

DEFAULT_LIMIT_MM = 286.0   # A4 is 297 mm; leave room for a footer strip
BOTTOM_DEFAULT = 12.0      # mm of .page bottom padding assumed for the footer


def free_the_page_box(css: str) -> str:
    """Neutralise the fixed sheet so real content height becomes visible."""
    css = re.sub(r"height:\s*297mm\s*;", "height: auto;", css)
    css = re.sub(r"overflow:\s*hidden\s*;", "overflow: visible;", css)
    # keep the breaks; they are what gives us one sheet per .page block
    return css


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", help="the built index.html")
    ap.add_argument("--css", default=None,
                    help="stylesheet path (default: styles.css beside the html)")
    ap.add_argument("--limit-mm", type=float, default=DEFAULT_LIMIT_MM,
                    help=f"content lower bound in mm (default {DEFAULT_LIMIT_MM})")
    ap.add_argument("--expect-pages", type=int, default=None,
                    help="fail if the sheet count differs (default: match .page blocks)")
    ap.add_argument("--keep", action="store_true",
                    help="keep the probe html/css/pdf instead of cleaning up")
    args = ap.parse_args()

    html_path = os.path.abspath(args.html)
    base = os.path.dirname(html_path)
    css_path = args.css or os.path.join(base, "styles.css")
    if not os.path.exists(css_path):
        print(f"FAIL: stylesheet not found: {css_path}")
        return 1

    html_src = open(html_path, encoding="utf-8").read()
    css_src = free_the_page_box(open(css_path, encoding="utf-8").read())

    n_blocks = len(re.findall(r'class="[^"]*\bpage\b[^"]*"', html_src))
    expect = args.expect_pages if args.expect_pages is not None else n_blocks

    probe_css = "_probe.css"
    probe_html = html_src.replace(os.path.basename(css_path), probe_css)
    probe_pdf = os.path.join(base, "_probe.pdf")
    open(os.path.join(base, probe_css), "w", encoding="utf-8").write(css_src)
    probe_path = os.path.join(base, "_probe.html")
    open(probe_path, "w", encoding="utf-8").write(probe_html)

    HTML(filename=probe_path, base_url=base).write_pdf(probe_pdf)

    doc = pymupdf.open(probe_pdf)
    failures, worst = [], 0.0

    for i, page in enumerate(doc, 1):
        bottom = 0.0
        for b in page.get_text("blocks"):
            if b[4].strip():
                bottom = max(bottom, b[3])
        mm = bottom * MM_PER_PT
        worst = max(worst, mm)
        state = "OK" if mm <= args.limit_mm else "OVERFLOW"
        if mm > args.limit_mm:
            failures.append(
                f"pg{i}: content reaches {mm:.2f} mm (limit {args.limit_mm:.1f} mm) "
                f"— split this page or tighten it")
        print(f"  page {i:>2}: lowest content {mm:7.2f} mm   {state}")

    print("-" * 64)
    if doc.page_count != expect:
        failures.append(
            f"sheet count {doc.page_count} != expected {expect} "
            f"({n_blocks} .page blocks in the source)")

    if not args.keep:
        for f in (probe_pdf, probe_path, os.path.join(base, probe_css)):
            try:
                os.remove(f)
            except OSError:
                pass

    for msg in failures:
        print(f"FAIL {msg}")
    if failures:
        print(f"\n{len(failures)} FAILURE(S) — do NOT publish this build.")
        return 1

    print(f"CLEAN: {doc.page_count} sheet(s); worst page {worst:.2f} mm "
          f"of {args.limit_mm:.1f} mm usable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
