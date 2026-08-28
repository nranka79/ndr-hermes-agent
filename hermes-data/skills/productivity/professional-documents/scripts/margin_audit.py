#!/usr/bin/env python3
"""Geometric margin audit for WeasyPrint HTML->PDF output.

Detects table overflows and orphan/gap pages that text checks miss.
Usage:  python3 margin_audit.py <document.pdf> [dpi]

Rules (A4, 22mm/18mm/20mm/18mm @page margins, ~65 dpi render):
  - Content pages should show L ~= R ~= 46-47 px (18mm side margins).
  - l < 38 or r < 38          -> table/content overruns the right margin
  - bottom_gap > 110          -> large empty area (orphan-tail or over-short page)
  - line count (pdftotext) < 5 on a content page -> orphan page (1-2 lines)

Common causes & fixes:
  - Right-margin overrun on wide numeric tables: td.num/th.num in Courier New
    with white-space:nowrap is too wide -> switch to Helvetica/Arial 8pt nowrap.
  - Orphan pages: fixed-height spacer divs too tall (letter sig-space, sign-off
    spacers) or sections overflowing by 1-2 lines -> shrink spacers and tighten
    .sec-head/h3/td/li/KPI spacing (see professional-documents SKILL.md).
"""
import subprocess, sys, glob, os, tempfile

def audit(pdf: str, dpi: int = 65) -> int:
    from PIL import Image
    import numpy as np
    tmp = tempfile.mkdtemp(prefix='margin_audit_')
    subprocess.run(['pdftoppm', '-png', '-r', str(dpi), pdf, os.path.join(tmp, 'p')], check=True)
    files = sorted(glob.glob(os.path.join(tmp, 'p-*.png')))
    if not files:
        print('no pages rendered'); return 1
    issues = 0
    for f in files:
        im = np.array(Image.open(f).convert('L'))
        h, w = im.shape
        mask = im < 245
        rows = np.where(mask.any(axis=1))[0]
        cols = np.where(mask.any(axis=0))[0]
        if len(rows) == 0:
            print('BLANK PAGE'); continue
        pg = int(f.split('-')[-1].split('.')[0])
        l, r, t, b = cols[0], w - cols[-1], rows[0], h - rows[-1]
        # line count from pdftotext
        out = subprocess.run(['pdftotext', '-f', str(pg), '-l', str(pg), pdf, '-'],
                             capture_output=True, text=True).stdout
        nl = len([x for x in out.splitlines() if x.strip()])
        flag = ''
        if pg != 1 and (l < 38 or r < 38):
            flag = ' <-- MARGIN OVERRUN'; issues += 1
        if b > 110:
            flag += ' <-- BIG BOTTOM GAP'; issues += 1
        if pg != 1 and nl < 5:
            flag += ' <-- ORPHAN PAGE'; issues += 1
        print(f'P{pg:2}: L={l} R={r} T={t} B-gap={b} lines={nl}{flag}')
    print(f'\nissues: {issues}')
    return 1 if issues else 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: margin_audit.py <document.pdf> [dpi]'); sys.exit(2)
    dpi = int(sys.argv[2]) if len(sys.argv) > 2 else 65
    sys.exit(audit(sys.argv[1], dpi))
