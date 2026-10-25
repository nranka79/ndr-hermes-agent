# Ranka Oasis (Sevaganapalli) — DTCP layout approval: documents + sanctioned areas

Session 2026-09-16 (NDR voice: "Ranka OSS" = Ranka Oasis). Task: find the pattern/layout approval
drawing + letter and report total land area, total sellable plotted area incl. clubhouse/commercial.

## Where the approval docs live

`Sevaganapalli Land Partners` (104VWF9-XdeLX612NjHE9s2-92KTpmz77) →
`03_Approvals_and_Regulatory` (1hBnZFuZqvXCR0TeLPyk88v2JqZGoTawk) →
`DTCP_Approvals` (1Rq0C3o3paKH7yvrd3Tfv5myrzZYzr4RA) → `Ranka Oasis Approvals`
(17pqfdNEW6leLDVfPGH62oNJ0bhFl5Id1, sales1-owned — only 2 files):

- **Approved layout print = the "pattern approval drawing + approval" combo**:
  `20260113 Ranka Oasis Sevaganapalli Layout Plan – DTCP Krishnagiri – Nishant Ranka.pdf`
  id `1pJ9upN71y3gegmZWa4WtFJSzcbpCmurI` (1,158,058 B; 1 page letter; Producer `Microsoft Print
  To PDF`; **no text layer** — vector-outlined; left half = small plot drawing 1–130 + land line
  diagram, right half = Tamil approval text + area statement + conditions).
- **Sanction letter** (3 pages, English): `20260330 Ranka Oasis Sevaganapalli Layout Planning
  Sanction – Sevaganapalli Panchayat & DTCP Krishnagiri – Nishant Ranka.pdf` id
  `1hqAPCZTj829ceph0JioCKayY7uxhTQ2I` (2,413,146 B). No text layer but **tesseract eng OCRs it
  cleanly at 300 DPI**.

psingh copies: DTCP print `1YxNtZNkWDuQXWysx9huGFDhN_Rt0Ul9l` (also `1N71dju5aQPLONUPec34wUqchDQ2W8awl`,
`1k0ANDRMmknBGXZOH3-KZHGSiQfHioEBy`); sanction letter `1QZ2UvZs8mL96-GfzLLLbAanG6gUTlKZ1` (also
`1Q30L4dBaDsLYvk5I4PPDi4JFrSTwZB6D`).

## Mis-named copy trap (verified 2026-09-16)

`20260330 Ranka Oasis Village Panchayat Residential Layout Approval 8.52 Acres.pdf`
(`1Vi8kcs68hXwwVNJTm6FdjTdpES-JfYDD`) and `…Approved Plan Drawing.pdf` (`1V3WhWoBuGzCrIF5NvwQZApeNrP5JOHoO`)
are **byte-identical** to the 30,416 sq.m DTCP print (1,158,058 B) and the sanction letter
(2,413,146 B). The approved extent is **7.52 acres, NOT 8.52**. Never quote an acreage from a
Drive filename — verify by content (byte size / letter text) first.

## Sanctioned numbers (verbatim from letter + drawing area statement)

- Approval chain: road pattern issued 17.12.2025 → DTCP Roc **RJDVYJD1/2026/TCP dt 13.01.2026** →
  **SWP/DTCP/KRISHNAGIRI/LAYOUT NO. 03/2026 & 02/2026** → Panchayat Planning Permission **03/2025
  dt 30.03.2026**; roads/OSR donated to Panchayat via gift deeds 9188/2025 & 9196/2025
  (registered Hosur); layout approval fee ₹5,23,228.
- **Total sanctioned extent: 30,416.00 sq.m = 7.516 ac = 3,27,395 sq.ft** over 19 surveys:
  158/1C9A, 158/1C9B, 166/1, 166/2B2, 166/3A, 3B, 3C, 3D, 3E1, 3E2, 3F, 167/2C, 167/2D,
  167/1G, 168/1B, 176/1B2D, 176/2B4A, 177/1A1A, 177/1A1B.
- Area statement (drawing print): site 30,416.00 − roads 10,193.49 = net **20,222.51 sq.m**;
  OSR park 2,065.91 (10.21%) + public utility 106.63 (0.52%) + TANGEDCO/EB 247.48 (1.22%);
  **130 house sites (plots 1–130) = 17,802.49 sq.m** — letter verbatim "plot extent: 17802.49 Sq.m".
- **Arithmetic reconciles EXACTLY:** 30,416.00 − 10,193.49 = 20,222.51; 20,222.51 − 2,065.91 −
  106.63 − 247.48 = 17,802.49. Exact reconciliation = proof the extraction is complete.
- Conversions: 17,802.49 sq.m = 1,91,624 sq.ft = 4.399 ac. sqm × 10.7639 → sqft; sqm × 0.000247105 → ac.
- The print's area statement also flags "variable plots 36, 79, 82–86, 93–115, 124, 130 =
  2,161.27 (10.68%)".

## Clubhouse / commercial answer ("total sellable incl. clubhouse or commercial land")

- The approval has **NO separate clubhouse or commercial line** — all 130 plots are residential
  house sites. The clubhouse sits ON a sanctioned plot: master plan (03.08.26) text layer shows
  Clubhouse + Infinity Pool + Social Lawn + Basketball Court + Koi Pond + Picnic Zone + Outdoor
  Gym + Senior Citizens Corner + Children's Play Area in the NE plot band (plots 6–13); **plot 6**
  is the big 8,382 sq.ft / 778.69 sq.m NE-corner site → clubhouse land is INSIDE the 17,802.49.
- **Flag, never fix:** the master plan additionally shows plots **131–138 (~1,653.20 sq.m ≈
  17,795 sq.ft)** which are NOT in the sanctioned 1–130 set (see `ranka-oasis-nomenclature-workbook.md`
  `M vs DTCP` tab; areas not printed on 03.08.26 Sheet 1). Master-plan total incl. 131–138 =
  19,455.69 sq.m ≈ 2,09,419 sq.ft — only 17,802.49 is sanctioned.
- Deliverable shape NDR accepted: total land → sanctioned sellable plot extent (with letter
  quote) → area-statement break-up → clubhouse/commercial note → master-plan extras flag.

## Reading these prints (reusable)

- `Microsoft Print To PDF` → pdftotext empty, always. The 3-page English sanction letter OCRs
  cleanly with tesseract eng at 300 DPI; the 1-page DTCP print is Tamil/vector-outlined → needs a
  vision-capable engine (see `oasis-plot-facing-sanction-verification.md` Gemini-pool fallback)
  or rely on the English letter's numbers (they match the printed area statement).
- AutoCAD master-plan PDFs keep a real text layer: use pymupdf `get_text("words")` for amenity
  labels and plot numbers (Clubhouse ≈ unrotated (762, 664); plots 131–138 at x 602–683 y 372–500).
- **pymupdf install when the venv has no pip:** `uv pip install --python /opt/hermes/.venv/bin/python pymupdf`.
- **Rotated-page coordinate trap:** `page.rect` + `page.rotation` (e.g. 1191×1684 @ 270) are
  UNROTATED space; `get_pixmap(clip=rect)` applies the rotation internally, so clip rects must be
  in unrotated coordinates and you CANNOT simply x/y-swap `pdftotext -bbox` coords onto pymupdf
  words. With no vision engine available, trust the text layer + tesseract over coordinate guessing.