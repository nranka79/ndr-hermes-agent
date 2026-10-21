#!/usr/bin/env python3
"""
pdf_drawing_dimension_extract.py — authoritative data extraction from architectural /
CAD-derived PDF drawings (floor plans, sanction drawings, layout sheets).

WHY THIS EXISTS
---------------
Vision/OCR on architectural sheets hallucinates dimensions, mislabels which boundary a
dimension attaches to, and gets dimension-line orientation wrong. Verified on a
TruBuild G+1 residential plan (Sep 2026) where three separate vision passes produced
three partly-wrong readings of the same sheet. pdftotext on the same file scrambles
dimension strings into unreadable columns.

pymupdf's text layer + vector geometry gives the EXACT text, the EXACT bbox (which
reveals dimension-line orientation), and the EXACT plotted geometry (which lets you
prove whether a labelled dimension matches what was drawn).

WHAT IT PRINTS
--------------
  1. TEXT SPANS      every string with bbox + aspect -> dimension strings, notes,
                     title block, area statements. Rotated (vertical) dimension labels
                     come out tall & narrow: h > w.
  2. FILLED SHAPES   wall poche and surface fills, classified by colour:
                       (0,0,0)      wall / solid mass
                       (1,1,1)      white core of a wall assembly
                       ~0.92        floor-finish grid (parking pavers, tiled floors)
                       ~0.88-0.96   other finishes (kitchen, shaft, balcony)
  3. LONG SEGMENTS   horizontal & vertical runs > --min-len: walls, boundary lines,
                     compound walls. Cluster identical coordinates to collapse
                     multi-line wall assemblies into one axis position.
  4. SCALE CALIBRATION  derive pt-per-foot from a dimension you trust, then convert
                     every other plotted clearance to feet so labels can be checked
                     against geometry.
  5. CROP COMMANDS   ready-to-paste pdftoppm lines for targeted high-DPI crops,
                     so vision is used only on a small region as corroboration.

USAGE
-----
  uv venv /tmp/venv && uv pip install --python /tmp/venv/bin/python pymupdf
  /tmp/venv/bin/python pdf_drawing_dimension_extract.py <file.pdf> [--pages 1,2]
      [--min-len 20] [--dpi 600]

  # calibrate scale from a dimension you trust (label, x0, y0, x1, y1 of its dim line):
  /tmp/venv/bin/python pdf_drawing_dimension_extract.py plan.pdf --calibrate "25'-0\" 161.8 320.0 559.6 320.0"

Then, and only then, use vision_analyze on a targeted crop for a second opinion.
Text layer and vector geometry are authoritative; vision is corroboration.
"""

import argparse
import sys
from collections import defaultdict

try:
    import pymupdf  # modern import; `fitz` is the deprecated alias
except ImportError:  # pragma: no cover
    print("pymupdf missing. Run:\n  uv venv /tmp/venv && uv pip install --python /tmp/venv/bin/python pymupdf")
    sys.exit(2)

PT_PER_IN = 72.0
PT_PER_FT = 12.0 * PT_PER_IN  # 864


def parse_pages(spec, npages):
    if not spec:
        return list(range(npages))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a) - 1, int(b)))
        else:
            out.append(int(part) - 1)
    return [p for p in out if 0 <= p < npages]


def spans(page):
    """Every non-empty text span with bbox and orientation hint."""
    rows = []
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for s in line["spans"]:
                t = s["text"].strip()
                if not t:
                    continue
                x0, y0, x1, y1 = s["bbox"]
                w, h = x1 - x0, y1 - y0
                # CAD dimension labels are rotated 90deg -> tall & narrow bbox
                orient = "vertical-label" if h > w * 1.5 else ("horizontal-label" if w > h * 1.5 else "block")
                rows.append((y0, x0, y0, w, h, orient, t))
    return sorted(rows)


def filled(page, min_area=1.0):
    """Filled vector shapes classified by fill colour = surface / wall mass."""
    out = []
    for pa in page.get_drawings():
        f = pa.get("fill")
        if f is None:
            continue
        r = pa["rect"]
        if r.width * r.height < min_area:
            continue
        fr = tuple(round(c, 2) for c in f)
        if fr == (0.0, 0.0, 0.0):
            kind = "WALL / solid mass"
        elif fr == (1.0, 1.0, 1.0):
            kind = "white core of wall assembly"
        elif abs(fr[0] - 0.92) < 0.01 and fr[0] == fr[1] == fr[2]:
            kind = "floor-finish grid (pavers / tiled floor)"
        elif 0.85 < fr[0] < 0.98 and fr[0] == fr[1] == fr[2]:
            kind = "other finish (kitchen / shaft / balcony)"
        else:
            kind = "tinted fill"
        out.append((r.y0, r.x0, fr, kind, r))
    return sorted(out)


def segments(page, min_len):
    """Long straight H/V runs = walls, boundary lines, compound walls."""
    hz, vt = [], []
    for pa in page.get_drawings():
        for it in pa["items"]:
            if it[0] == "l":
                a, b = it[1], it[2]
                if abs(a.y - b.y) < 0.6 and abs(a.x - b.x) >= min_len:
                    hz.append((round(a.y, 1), round(min(a.x, b.x), 1), round(max(a.x, b.x), 1)))
                if abs(a.x - b.x) < 0.6 and abs(a.y - b.y) >= min_len:
                    vt.append((round(a.x, 1), round(min(a.y, b.y), 1), round(max(a.y, b.y), 1)))
            elif it[0] == "re":
                r = it[1]
                if r.width >= min_len:
                    hz.append((round(r.y0, 1), round(r.x0, 1), round(r.x1, 1)))
                    hz.append((round(r.y1, 1), round(r.x0, 1), round(r.x1, 1)))
                if r.height >= min_len:
                    vt.append((round(r.x0, 1), round(r.y0, 1), round(r.y1, 1)))
                    vt.append((round(r.x1, 1), round(r.y0, 1), round(r.y1, 1)))

    def cluster(items, tol=8.0):
        items = sorted(set(items))
        groups = defaultdict(list)
        for a, s, e in items:
            key = None
            for k in groups:
                if abs(a - k) <= tol:
                    key = k
                    break
            groups[key if key is not None else a].append((a, s, e))
        merged = []
        for k, g in groups.items():
            lo = min(x[1] for x in g)
            hi = max(x[2] for x in g)
            merged.append((round(k, 1), lo, hi, round(hi - lo, 1), len(g)))
        return sorted(merged)

    return cluster(hz), cluster(vt)


def caliper(page):
    """All long lines, both axes, as raw numbers for scale calibration."""
    hz, vt = segments(page, 20)
    return hz, vt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages")
    ap.add_argument("--min-len", type=float, default=25.0)
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--calibrate", help='label x0 y0 x1 y1  (of a dimension line you trust)')
    ap.add_argument("--max-spans", type=int, default=400)
    ap.add_argument("--max-shapes", type=int, default=200)
    args = ap.parse_args()

    doc = pymupdf.open(args.pdf)
    pages = parse_pages(args.pages, len(doc))

    print("=" * 78)
    print(f"FILE: {args.pdf}   pages={len(doc)}   processing={[p+1 for p in pages]}")
    try:
        meta = doc.metadata or {}
        for k in ("title", "author", "creator", "producer", "creationDate"):
            if meta.get(k):
                print(f"  {k}: {meta[k]}")
    except Exception:
        pass
    print("=" * 78)

    for pno in pages:
        page = doc[pno]
        print(f"\n{'#' * 78}\n### PAGE {pno+1}   rect={page.rect}\n{'#' * 78}")

        # ---- 1. text spans -------------------------------------------------
        sp = spans(page)
        print(f"\n--- TEXT SPANS ({len(sp)}) ---")
        print("  y0      x0      w      h    orientation        text")
        for (_, _, y0, x0, w, h, orient, t) in sp[: args.max_spans]:
            print(f"{y0:7.1f} {x0:7.1f} {w:7.1f} {h:6.1f}  {orient:<17} {t}")
        if len(sp) > args.max_spans:
            print(f"  ... {len(sp) - args.max_spans} more (raise --max-spans)")

        # ---- 2. filled shapes ---------------------------------------------
        fl = filled(page)
        print(f"\n--- FILLED SHAPES ({len(fl)}) : wall poche & surface fills ---")
        for (_, _, fr, kind, r) in fl[: args.max_shapes]:
            print(f"  {str(fr):<18} {kind:<38} ({r.x0:7.1f},{r.y0:7.1f})-({r.x1:7.1f},{r.y1:7.1f})  {r.width:6.1f} x {r.height:6.1f}")
        if len(fl) > args.max_shapes:
            print(f"  ... {len(fl) - args.max_shapes} more (raise --max-shapes)")

        # ---- 3. long segments ---------------------------------------------
        hz, vt = segments(page, args.min_len)
        print(f"\n--- LONG HORIZONTAL RUNS >={args.min_len}pt  (axis y, x0..x1, len, lines) ---")
        for (a, s, e, ln, n) in hz:
            print(f"  y={a:8.1f}  x {s:8.1f} .. {e:8.1f}   len={ln:8.1f}  ({n} line(s))")
        print(f"\n--- LONG VERTICAL RUNS >={args.min_len}pt  (axis x, y0..y1, len, lines) ---")
        for (a, s, e, ln, n) in vt:
            print(f"  x={a:8.1f}  y {s:8.1f} .. {e:8.1f}   len={ln:8.1f}  ({n} line(s))")

        # ---- 5. crop commands ---------------------------------------------
        print(f"\n--- TARGETED HIGH-DPI CROPS (pixel = point * dpi/72 at {args.dpi} dpi) ---")
        print("  # pdftoppm -x/-y/-W/-H are PIXELS at the output resolution.")
        xs = [s for (_, s, _, _, _) in hz] or [page.rect.x0]
        ys = [a for (a, _, _, _, _) in hz] or [page.rect.y0]
        print(f"  # example, full drawing area:")
        k = args.dpi / 72.0
        print(f"  pdftoppm -r {args.dpi} -f {pno+1} -l {pno+1} "
              f"-x {int(page.rect.x0*k)} -y {int(page.rect.y0*k)} "
              f"-W {int(page.rect.width*k)} -H {int(page.rect.height*k)} -png "
              f'"{args.pdf}" /tmp/pg{pno+1}')

    # ---- 4. scale calibration --------------------------------------------
    if args.calibrate:
        parts = args.calibrate.rsplit(None, 4)
        label, (x0, y0, x1, y1) = parts[0], map(float, parts[1:])
        length_pt = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        print(f"\n{'=' * 78}\n### SCALE CALIBRATION\n{'=' * 78}")
        print(f"  dimension {label!r} spans {length_pt:.1f} pt")
        try:
            import re
            m = re.search(r"(\d+)'\s*-?\s*(\d+)?", label)
            feet = int(m.group(1)) + (int(m.group(2)) / 12.0 if m.group(2) else 0.0)
        except Exception:
            print("  could not parse feet from label; pass e.g. \"25'-0\\\"\"")
            feet = None
        if feet:
            ppf = length_pt / feet
            print(f"  => {ppf:.3f} pt per foot  ({ppf * 12:.3f} pt per inch -> nominal scale ~1:{ppf * 12:.0f})")
            print("\n  Convert any plotted span to feet with:  feet = pt / %.3f" % ppf)
            print("  Cross-check EVERY other labelled dimension against this. If a label and")
            print("  the plotted geometry disagree, REPORT THE LABEL (authorities read labels)")
            print("  AND FLAG THE INCONSISTENCY -- do not silently pick one.")


if __name__ == "__main__":
    main()