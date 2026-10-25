#!/usr/bin/env python3
"""OCR keyword sweep of an image-based PDF.

Render every page, tesseract it, and report per-page keyword hits.
Use to verify which projects/sections an image-heavy (marketing/scan) PDF
actually covers — e.g. "does DRA Portfolio Updated.pdf contain Ranka Oasis
and the Chennai projects?" when pdftotext returns near-zero text.

Usage:
  /opt/hermes/.venv/bin/python3 ocr-keyword-sweep.py <file.pdf> <outdir> [kw1 kw2 ...]

Default keywords cover the DRA corporate-profile check. ~2-4 min for 65 pages at 90 dpi.
"""
import subprocess, os, sys, glob

pdf = sys.argv[1]
outdir = sys.argv[2]
if len(sys.argv) > 3:
    keywords = sys.argv[3:]
else:
    keywords = ['chennai', 'bangalore', 'bengaluru', 'north star', 'northstar', 'oasis', 'udaya', 'amber',
                'inara', 'skylantis', 'harmony', 'tuxedo', 'pristine', 'navallur', 'omr', 'vellachery',
                'velachery', 'tamil nadu', 'truliv', 'riverstone', 'serenity', 'eden park', 'silver springs']

os.makedirs(outdir, exist_ok=True)
info = subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout
n = None
for l in info.split('\n'):
    if l.lower().startswith('pages'):
        n = int(l.split(':')[1].strip())
        break
print(f"pages={n}", flush=True)

# Render the WHOLE doc in one call, then GLOB the output. Per-page -f/-l output
# names are unreliable across pdftoppm versions — never guess exact filenames.
subprocess.run(['pdftoppm', '-r', '90', '-png', pdf, f"{outdir}/pg"], capture_output=True, timeout=300)
pngs = sorted(glob.glob(f"{outdir}/pg-*.png"))
print(f"rendered {len(pngs)}", flush=True)

hits = []
for i, png in enumerate(pngs, 1):
    txt = subprocess.run(['tesseract', png, 'stdout'], capture_output=True, text=True, timeout=90).stdout
    low = txt.lower()
    found = [k for k in keywords if k in low]
    if found:
        hits.append((i, found))
        print(f"page {i}: {found}", flush=True)
    os.remove(png)

print("\n=== SUMMARY ===")
for i, found in hits:
    print(f"  p{i}: {found}")
