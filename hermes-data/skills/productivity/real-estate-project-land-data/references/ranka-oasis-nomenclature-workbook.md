# Ranka Oasis Unit Nomenclature workbook — structure & plan-file map

Session 2026-09-10/11 (Prakash). The workbook is the living reference for Oasis Phase I plot /
unit data; keep the numbering conventions straight across its tabs.

## Workbook

- **`20260910 Ranka Oasis Unit Nomenclature – Phase I`** — id `1rLNLCs9aJafH6gkBWs5VH1Mw9GvS9zzD1olsQ2Pk_x0` (owner psingh@draas.com)
- Tabs (as of 2026-09-11):
  - `Nomenclature` — unit nos in `001..305` style (block A/B split per Ranka Amber convention)
  - `DTCP Approved Plan (13.01.2026)` — **sanctioned basis, the reference tab**: Plot # | Shape |
    E/W/N/S dims (m) | Area sqm | Area sqft | SBUA sqft @ FSI 1.80 | Facing | Corner, plots **1–130
    individual** (row 132 TOTAL; row 133 source note; rows 134–136 facing-verification notes added
    11-Sep-2026)
  - `M vs DTCP` — per-plot comparison Master vs DTCP (dims strings diverge in 46 plots while areas
    are identical for 1–130; plots 131–138 Master-only = 1,653.20 sqm)
  - `Master Plan Areas (03.08.26)` — added 11-Sep-2026, per-plan-print areas (see
    `references/layout-plan-plot-area-extraction.md`)
- Master Inventory Sheet (source of Master tab): `1jHjOIUQSMVwVQewFES2d77D9SaHK2DcUbbTBvwwRH8o`
  (tabs `Master Sheet `, `As per sanction layout` [dims only, NO facing], `Plan Tracker`).

## Numbering: sanctioned (DTCP) vs master-plan (combined)

- **DTCP tab = sanctioned individual plots 1–130.** 130 house sites = 17,802.49 sqm per sanction
  letter; per-plot transcription sums to 17,372.66 sqm (2.4% gap, reconcile — flag, never fix).
- **Master plan combines** sanctioned plots into bigger saleable plots:
  `79-80`, `82-83-84`, `85-86`, `93-94`, `95-96`, `97-98`, `99-102` (labels `99-100`/`101-102`,
  one area 2219.55 sqft), `103-104`, `105-106`, `107-108`, `109-110`, `111-112`, `113-114-115`,
  `121-122`, `123-124`, `125-126`, `127-128-129-130`.
- **Plots 131–138** exist only in the master plan (not in the sanctioned 1–130 set); the
  03.08.26 Sheet-1 print shows their labels but prints NO areas.

## Plan file IDs (Drive)

- DTCP approval letter print `2026-01-13, Sevaganapalli, DTCP Layout Plan Approval — Krishnagiri, —.pdf`
  (1,158,151 B, letter, vector-outlined, no text layer): `1YxNtZNkWDuQXWysx9huGFDhN_Rt0Ul9l`
  (also copies `1N71dju5aQPLONUPec34wUqchDQ2W8awl`, `1k0ANDRMmknBGXZOH3-KZHGSiQfHioEBy`)
- Master plan `Oasis Master Plan 03.08.26-Sheet 1.pdf` (A2 AutoCAD, text layer): `1rvO-KxOVsJyIjwhACoXety_4AWOpnQDO`;
  same-session upload was `doc_32a319656ea6_Oasis Master Plan 03.08.26-Sheet 1 (1).pdf`.
  Other versions: `Oasis Master Plan 10.09.26-Sheet 1.pdf` (`1IElexHr5bmLEhfLkI7t4W8C0p7TETsVD`),
  24.08.26 Sheets 1–4, 03.08.26 "- Marked.png" (`1r6MuyMGbVeiS-pKnFlUPELxohExNoe3t`), "- Circled.pdf" (`141bigMEehBvt5KI3EyU0VGu9OV-TsiDq`).
- Panchayat + DTCP sanction letter (3-page English OCR-able): `20260330 ... Layout Planning
  Sanction` = `1QZ2UvZs8mL96-GfzLLLbAanG6gUTlKZ1` (2,413,146 B) — carries SWP LAYOUT NO. 03/2026 &
  02/2026 dated 13.01.2026.
- `—, Sevaganapalli, Oasis — East/West/North Plan.pdf` files are BUILDING floor plans (A3
  architectural, "walk-in wardrobe / duct" notes) — NOT plot-facing maps. Red herring for facing work.

## Area reconciliation (proven numbers)

- Master-plan printed sum (plots with labelled areas): **16,311.37 sqm = 175,573.97 sqft**
- + plots 6/7/8 (not printed; from DTCP tab: 778.69 / 145.27 / 137.28 sqm) → **17,372.70 sqm =
  186,997.97 sqft** ≈ DTCP tab TOTAL 17,372.66 ✓
- Units: the plan prints sqft; sqm = sqft ÷ 10.7639.

## Facing basis

The sanction print has NO north arrow / NO facing labels → facing = road frontage (north-up),
verified at block level 11-Sep-2026. Ambiguous on the tiny print: plots **81, 82, 86, 87, 90, 91**
(keep Master values, verify on full-size drawing when shared).

## The DTCP print carries TWO area statements + clubhouse detail (reads of 16-Sep-2026)

The `20260113 ... DTCP Layout Plan Approval` print (id `1pJ9upN71y3gegmZWa4WtFJSzcbpCmurI`,
Ranka Oasis Approvals folder) contains **two distinct printed tables** — a first pass reads only
one and you will think the other is an error. Both came from Gemini-2.5-pro vision with a
full-page + right-half pass and a terse digit-verification zoom pass:

1. **Main Area Statement (பரப்பளவு விபரம்), total 30,416.00 sq.m** — Total 30,416.00; plots for
   sale 17,802.49 (58.53%); roads **digit ambiguous** — model read 10,183.44 (33.48%), letter
   arithmetic gives 10,193.49 (30,416 − 10,193.49 = 20,222.51 net, then − OSR 2,065.91 − public
   utility 106.63 − TANGEDCO 247.48 = 17,802.49 EXACTLY); park/OSR provided 2,222.07 (7.31%);
   required park/OSR 2,474.06 (8.13%); deficiency 252.00 (0.82%); 130 plots.
2. **Allotment/Reservation statement, total 20,635.97 sq.m** — plots 16,153.45 (78.28%); roads
   2,109.05 (10.21%); park & playground 2,063.60 (10.00%); public purpose 247.49 (1.20%);
   **shop plots 62.38 (0.30%)**; total reservation 2,373.47 (11.50%). Fully self-consistent
   (row sum = total) — treat as a real printed block, not a misread, but flag context unverified.
3. **Plot 130 note** — print says plot 130 was **removed and merged into the park** to cover the
   OSR deficiency; separate note: 247.41 sq.m of plot 130 (excluding 11.50) allocated as
   deficiency compensation. So "130 sites" is sanctioned-numbering, but plot 130 is effectively
   park on the ground.
4. **Clubhouse/commercial land** — there is NO separate clubhouse/commercial line in the sanction.
   On the master plan (03.08.26), the Clubhouse + Infinity Pool + Social Lawn + Basketball Court +
   Koi Pond + Picnic Zone + Outdoor Gym + Senior Citizens Corner + Children's Play Area belt sits
   on the NE plot band **plots 6–13**; plot 6 (8,382 sq.ft / 778.69 sq.m — the big NE-corner
   site) is the clubhouse plot, INSIDE the sanctioned 17,802.49. Shop land only appears as the
   tiny 62.38 sq.m line in the allotment statement.
5. **Master-only plots 131–138 (~1,653.20 sq.m ≈ 17,795 sq.ft)** are NOT in the sanctioned 1–130
   set — the sales master plan adds them (plot labels present on 03.08.26 Sheet-1, no areas
   printed). Only 17,802.49 sq.m is approved; master total incl. 131–138 = 19,455.69 sq.m.
6. **Filenames lie**: `20260330 Ranka Oasis Village Panchayat Residential Layout Approval 8.52
   Acres.pdf` and the `Approved Plan Drawing` copy are byte-identical to the 30,416 sq.m sanction
   letter / DTCP print (same md5-size) — the "8.52 Acres" name is wrong; real extent is 7.52 ac.
   Check bytes/`pdfinfo` before trusting a filename.