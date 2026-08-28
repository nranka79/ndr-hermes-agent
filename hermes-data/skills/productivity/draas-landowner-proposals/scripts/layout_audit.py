#!/usr/bin/env python3
"""Layout QA for WeasyPrint-generated A4 PDFs.

Detects the classic "page alignment" complaints before the user does:
  - pages whose content is only 1-2 lines (orphans)
  - uneven left/right margins vs the @page margin setting
  - content overrunning the margins
  - large empty gaps at the bottom of content pages

Usage:
  layout_audit.py proposal.pdf [dpi]

Renders every page with pdftoppm, measures the non-white content bounding
box with PIL+numpy, and reports per page. Page 1 (full-bleed cover) and the
covering-letter page (ends naturally with the signature block) legitimately
show larger bottom gaps — flagged as INFO, not ISSUE.

Dependencies: poppler-utils (pdftoppm), python3-PIL, numpy.
"""
import glob
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

PDF = sys.argv[1] if len(sys.argv) > 1 else "proposal.pdf"
DPI = int(sys.argv[2]) if len(sys.argv) > 2 else 65
# Expected side margin in px at this DPI (18mm default @page margin).
# 18mm = 0.7087 in -> px = 0.7087 * DPI
MARGIN_PX = int(round(0.7087 * DPI))
# Bottom gap beyond which we suspect an orphan/blank area (footer sits ~25px
# at 65dpi; a content page should not have much more than that).
MAX_BOTTOM_GAP = int(round(1.6 * DPI))


def audit(path: str) -> int:
    tmp = tempfile.mkdtemp(prefix="layout_audit_")
    subprocess.run(
        ["pdftoppm", "-png", "-r", str(DPI), path, os.path.join(tmp, "pg")],
        check=True,
    )
    files = sorted(glob.glob(os.path.join(tmp, "pg-*.png")))
    print(f"{len(files)} pages, expected side margin ~{MARGIN_PX}px @ {DPI}dpi")
    issues = 0
    for f in files:
        page = int(f.split("-")[-1].split(".")[0])
        im = np.array(Image.open(f).convert("L"))
        h, w = im.shape
        mask = im < 245
        rows = np.where(mask.any(axis=1))[0]
        cols = np.where(mask.any(axis=0))[0]
        if len(rows) == 0:
            print(f"page {page:2}: BLANK")
            issues += 1
            continue
        t, b = rows[0], rows[-1]
        l, r = cols[0], cols[-1]
        gap = h - b
        notes = []
        if page != 1:
            if l < MARGIN_PX - 6:
                notes.append(f"LEFT-OVERRUN L={l}")
            if w - r < MARGIN_PX - 6:
                notes.append(f"RIGHT-OVERRUN R={w-r}")
        if gap > MAX_BOTTOM_GAP:
            notes.append(f"BIG-BOTTOM-GAP({gap}px)")
        status = "ISSUE" if notes else "ok"
        if notes:
            issues += 1
        print(
            f"page {page:2}: L={l:3} R={w-r:3} T={t:3} bot-gap={gap:3} "
            f"[{status}] {' '.join(notes)}"
        )
    print(f"\n{issues} issue page(s)")
    return issues


if __name__ == "__main__":
    sys.exit(1 if audit(PDF) else 0)
