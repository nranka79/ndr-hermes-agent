#!/usr/bin/env python3
"""Per-page OCR keyword sweep for image-based PDFs (brochures, portfolios, scans).

Why: design/scan PDFs often have NO searchable text layer — pdftotext returns
~0 chars and Drive fullText search cannot index them. Render every page, OCR it,
and report which pages contain which keywords.

Usage:
  python3 ocr-sweep-keywords.py <pdf> <outdir> [keyword...]

Default keywords cover DRA projects/cities; pass your own list to override.
Prints `page N: [keywords]` per hit, then a summary. Renders at 90 DPI.
Run long sweeps with terminal(background=true, notify_on_complete=true).

Pitfall handled: pdftoppm produces <root>-<page>.png files (even with -f/-l),
never a single <root>.png — this script renders all pages in one call and
globs `pg-*.png` instead of guessing filenames.
"""
import subprocess, os, sys, glob

DEFAULT_KEYWORDS = ['chennai', 'bangalore', 'bengaluru', 'north star', 'northstar',
                    'oasis', 'udaya', 'amber', 'inara', 'skylantis', 'harmony',
                    'tuxedo', 'pristine', 'navallur', 'omr', 'velachery',
                    'tamil nadu', 'truliv', 'riverstone', 'serenity']

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(1)

pdf, outdir = sys.argv[1], sys.argv[2]
keywords = sys.argv[3:] or DEFAULT_KEYWORDS

os.makedirs(outdir, exist_ok=True)
info = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout
n = None
for l in info.split('\n'):
    if l.lower().startswith('pages'):
        n = int(l.split(':')[1].strip())
        break
print(f"pages={n}", flush=True)

# One render call for all pages; pdftoppm produces <root>-<page>.png files.
subprocess.run(['pdftoppm', '-r', '90', '-png', pdf, f"{outdir}/pg"],
               capture_output=True, timeout=300)
pngs = sorted(glob.glob(f"{outdir}/pg-*.png"))
print(f"rendered {len(pngs)}", flush=True)

hits = []
for i, png in enumerate(pngs, 1):
    txt = subprocess.run(['tesseract', png, 'stdout'], capture_output=True,
                         text=True, timeout=90).stdout
    low = txt.lower()
    found = [k for k in keywords if k in low]
    if found:
        hits.append((i, found))
        print(f"page {i}: {found}", flush=True)
    os.remove(png)

print("\n=== SUMMARY ===")
for i, found in hits:
    print(f"  p{i}: {found}")