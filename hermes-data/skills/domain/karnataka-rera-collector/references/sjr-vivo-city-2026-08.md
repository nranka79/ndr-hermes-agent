# SJR VIVO CITY PHASE 1 — single-project K-RERA pull (2026-08-13)

NDR gave only the RERA number (`PRM/KA/RERA/1250/307/PR/070326/008510`,
Nelamangala) and asked for: all details, approved plan, and — most
important — architect information. Working dir: `/opt/data/rera_008510/`
(scripts: `fetch_project.py`, `parse_detail.py`, `download_wanted.py`,
`upload_to_tmp.py`, `build_sheet.py`).

## Identity (no cross-contamination — clean single match)

- Detail page confirmed: **SJR VIVO CITY PHASE 1**, ACK
  `ACK/KA/RERA/1250/307/PR/060126/009909`, registered `070326` (07-03-2026).
- Promoter: M/s PRIMECO REALTY PRIVATE LIMITED (CIN U70100KA2015PTC079923,
  PAN ACYPR8463Q, GSTIN 29AAICP1400G1ZP), website primecorp.co.
- Approving Authority: **Nelamangala Planning Authority**; Approved Plan
  No. **LAO/41/2025-26**, dated 15-11-2025. Plotted Development, 1,115
  plots, 271,146 sq m total land (A 145,577 + B 125,569), 46 survey nos
  (landowner A. Rama Reddy 50%, Sy 69-5). Start 01-12-2025, completion
  30-11-2029. Total project cost ₹207.26 Cr.
- Bank: ICICI Cunningham Road, IFSC ICIC0001421, RERA 100%/70%/30%
  accounts 777705202612/13/16.

## Detail-page field parser — the structure that actually works

The `div.col-md-3` label/value pairs use **`<p class="text-right">` labels,
NOT `<label>` elements** — a `<label>`-based scraper returns zero fields
(hit this live). Working extraction:

- Header block (project name / ack no / registration no): `span.pull-right
  user_name` spans (`Project Name :<b>...</b>`).
- Body fields: `div.col-md-3 > p.text-right` (label, strip trailing `:`)
  followed by the NEXT sibling `div.col-md-3 > p` (value). Walk
  `find_next_sibling('div', class_=col-md-3)` then `.find('p')`.
- This page had 105 fields; parsed cleanly.

## Architect info — resolved from documents, not fields

No architect field exists anywhere on the detail page (CA = Makam
Vaibhav, Engineer on form = Sridhar M C are the only professionals in
tables). Architect identity came from:

1. **Council of Architecture CERTIFICATE.pdf** (`pdftotext -layout`):
   **Mr. Mohan Raj K, COA Registration No. CA/2022/154263**, valid
   27-12-2022 → 31-12-2026, issued 11-02-2026.
2. **Architect Letter.pdf**: states plotted development → no buildings →
   "no requirement of an Architect to plan and execute" (flag to NDR).
3. **Architect Aadhar.jpeg** (tesseract): Mohan Raj, DOB 1996-05-26, Karur
   TN. Report name only — mask Aadhaar number.
4. **Approved Plan (Demarked) title block** (OCR, see recipe below):
   "Ar.Mohan Raj.K COA REGISTERED ARCHITECT COA/2022/154263" + engineer
   **MEHBOOB BASHA** (BCC/BL-3-6/E-3150/2023-2028) — differs from the
   form's Sridhar M C; flagged to NDR.

## OOM-safe OCR of giant JP2 plan PDFs — proven recipe

Approved_Plan.pdf and Approved_Plan( Demarked)…pdf are 1 page, ~12-16 MB,
with 10 embedded JPEG2000 streams at **14850 × 21000 px** (8 bpc, ~445 MB
decoded each). Everything full-page died with exit 137:
- `pymupdf page.get_pixmap()` (even with a clip + Matrix)
- `pdfimages -j` (poppler)
- `pdftoppm -r 120 -x -y -W -H` (crop region still OOMs — decodes full page)
- `gs -sDEVICE=png16m -r120`
- `PIL Image.thumbnail` with `Image.MAX_IMAGE_PIXELS=None` (decodes full)
- `glymur jp[:]` full decode

Working path:
1. Raw stream extraction (cheap, no decode): pymupdf
   `doc.xref_stream(xref)` for each `page.get_images(full=True)` xref →
   `.bin`. Magic bytes `00 00 00 0c 6a 50 20` = JP2.
2. **Region decode with glymur**: `jp = glymur.Jp2k(bin);
   arr = jp[y0:y1, x0:x1]` — openjpeg area decode, only the region's
   memory is used. For 14850×21000 the title block (architect seal +
   approving authority + engineer) is in the **bottom strip**:
   y 16800-21000, x 8167-14850 (bottom-right); also scanned left_mid /
   right_mid / left_bot regions — architect text was in the bottom-left
   ("mid_bot": y 16800-21000, x 0-8167) in this plan.
3. PIL `thumbnail((1400-1600))` → `tesseract` → extract names/seals.
4. glymur was installed via `uv pip install --python
   /opt/hermes/.venv/bin/python glymur` (pulls numpy). NOTE: the
   `openjpeg` PyPI package does not exist; glymur is the JP2 reader.

## numpy user-site shadowing gotcha (fixed, worth knowing)

`/opt/hermes/.venv/bin/python` imported numpy from
`/data/hermes/home/.local/lib/python3.13/site-packages/numpy` (user site,
an aarch64 build with missing/broken `_multiarray_umath`) even though the
venv had a good x86_64 copy — `PYTHONNOUSERSITE=1` did NOT override it
(user site was still on sys.path). Fix: move the broken user-site dirs
aside (`mv .../numpy .../numpy.broken`, same for `numpy.libs` and the
`.dist-info`), then the venv's numpy 2.5.2 imports cleanly. Do not
uninstall user-site packages blindly — check `sys.path` order first.

## Targeted downloader pattern (vs full 504-doc sweep)

First run used the generic downloader (all docs) — killed by the 420s
foreground cap after ~108 docs. Rewrote as a WANTED-list downloader:
build name→href map from the parsed docs manifest, download only the
10 wanted files, skip existing (size > 0). Result: all 10 fetched in
under a minute (home 200 → 10 OK).

## Deliverables (TMP Drive + sheet, NDR's conventions)

- Drive folder: "SJR Vivo City Phase 1 RERA (2026-08-13)" under TMP root
  (google-draas) → 10 files (plans + architect docs).
- Sheet: "SJR Vivo City Phase 1 — RERA Details (2026-08-13)" with base
  fields, per-file-type link columns, architect block, engineer
  discrepancy note.
- Sheet links are plain text `filename\nhttps://drive.google.com/file/d/…`
  (never `=HYPERLINK()` — #ERROR!, known pitfall).
