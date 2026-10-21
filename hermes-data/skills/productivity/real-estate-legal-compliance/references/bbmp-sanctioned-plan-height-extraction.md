# BBMP Sanctioned-Plan Analysis — Building Height & Level Extraction (worked Sep 2026)

Use when NDR asks for building height / terrace level / floor levels / "height of the building"
comparisons from sanctioned plans (e.g. Legacy Cataleya vs Ranka Iris), or any raster PDF project
plan pulled from Drive.

## Locating the plans

- Search ALL vault accounts (`google-draas`, `google-ahfl`, `google-gmail`) via
  `build_service("drive","v3", service_name=...)`; search name + fullText variants
  (`name contains 'ataleya'`, `'Legacy'`, `'Anction'`, `'Iris'`). Project folders on draas drive:
  Cataleya lives in a "Legacy" folder (files: `Approved_SectionOfBuilding_CunninghamRoad.pdf`,
  `Approved_BuildingPlan_Site30_CunninghamRoad.pdf`, `Approved_LayoutPlan_...`); Ranka Iris has
  `Ranka_Iris_Sanction_Plan.pdf`. Check Gmail for download/attachment trail if Drive comes up empty.
- Voice note: "Katalia" = **Cataleya** (C-A-T-E-L-E-Y-A, Legacy Group, Cunningham Road).
- Run GWS scripts from `terminal` (vault socket env) with `HERMES_SESSION_USER_ID=ndr`.

## Reading raster CAD PDFs (no text layer)

Sanctioned sheets are vector/raster plots — `page.get_text()` returns empty. Recipe:

1. Render at high DPI: `pix = page.get_pixmap(dpi=200-220)` → PNG (A0 sheets become ~10k px).
2. Tile-crop with PIL grid (section sheets 4x2, plans 2x2) so annotation text stays legible.
3. `vision_analyze` each tile with a targeted extraction prompt ("extract every level label +
   number exactly, RL values, terrace, parapet, plinth; quote exactly").
4. For the level column on SECTION drawings: the schedule runs top→bottom on one side
   ("LIGHTNING ARRESTER TOP LVL … LVL +54.60 m", "13TH FLOOR LVL +43.80 m", ...). Crop a tight
   strip around it (e.g. x 45-78%, y 20-95% in overlapping chunks) — full-tile OCR garbles it.

## Key tables that answer height questions

- **Section level schedule** — every floor RL above datum (often "±0.00 m ROAD LVL").
- **Summary box** on building/site plan: `HEIGHT OF THE BUILDING — PERMISSIBLE = X.XX m /
  ACHIEVED = Y.YY m`. Site plans also label the footprint: "HT.OF THE BLDG.=47.40M" or
  "G+13 FLOORS +48.4 MTS".
- Building height per BBMP/KMC = terrace level above average ground (parapet / lift machine room /
  lightning arrester are NOT counted, but worth reporting separately).

## OCR conflict resolution (important)

Vision models garble numbers: **55.00 → "15.00"**, and different tiles gave "47.40" vs "54.00"
for the same box. When readings conflict, zoom-crop the EXACT box (3x3 grid) and re-read; the
architect's summary box and the authority-conditions box can legitimately show different figures
(e.g. architect achieved-to-terrace 47.40 m vs authority box "allowed 55 m / achieved 54 m" incl.
top structure). Quote both with their labels.

## Worked example (Sep 2026, verified figures)

- **Legacy Cataleya** — Site 30 (Old 19/2), Cunningham Rd, Ward 110, Vasanthnagar; sanction 2014;
  2B + GF + 13 floors + terrace; 21-24 units. Section (Dwg 08) datum ±0.00 road: terrace +47.40,
  parapet +48.60, lift machine room +52.80, lightning-arrester top +54.60. Height box:
  PERMISSIBLE 55.00 / ACHIEVED 47.40 m.
- **Ranka Iris** — Khata 37-37A-38, Sy 17/1 & 17/2, Domlur 2nd Stage, Ward 112(72); sanction
  BBMP/Addl.dir/JDTP(N)/LP0037/2013-14; 3B + GF + 13 floors + terrace. Height box:
  PERMISSIBLE 54.00 / ACHIEVED 48.4 m ("+48.4 MTS" on footprint).
- **Answer pattern**: height-to-terrace Cataleya 47.40 vs Iris 48.4 → Iris ~1.0 m taller; both
  G+13 (Cataleya 2 basements, Iris 3); margin to permitted limit 7.6 m vs 5.6 m.