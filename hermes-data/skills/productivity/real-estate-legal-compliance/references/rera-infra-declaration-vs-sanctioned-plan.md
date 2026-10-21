# RERA Registration Infrastructure Declaration vs Approved Building Plan

Verification workflow for K-RERA REGISTRATION-RECORD corrections: when a DRAAS project
wants to correct the Internal/External Infrastructure Yes/No declarations made at
registration (RERA registration application form), the correction letter's claims must be
checked against the **approved building plan** before filing. K-RERA cross-checks
registration forms against the sanction; a blanket "not applicable / not provided" claim
that contradicts the sanctioned plan is a pushback risk.

Verified on **Ranka Amber** (RERA PRM/KA/RERA/1251/446/PR/050826/008859, DRA Realty,
correction letter Oct 2026). Use for: "verify whether the given details are available in
the approved building plan", RERA correction letters, registration-audit questions about
infrastructure.

## Document Set (Ranka Amber)

| Doc | Drive id | Role |
|---|---|---|
| AutoDCR sanctioned output `Amber Plan Sanction GBA_BECC_0540_25-26 (2).pdf` | `1v-aLlu9LVH3aILRiTvu3fnFJw4vIExLT` (+ variant `1fT5XUa8pWsxUoCQYmaBEr9yTc6mEOYTQ`) | AUTHORITATIVE approved plan: site plan + stilt plan + RWH details + solar diagram + all 50 sanction conditions |
| Architect drawing set `AMBER SANCTION 07.05.2026.pdf` | `1aaNKuSd01zDgfiAGzELC2IQP75rghht2` | Same submission, full text layer — good for labels (TRANSFORMER, DRIVEWAY) the AutoDCR page may not OCR |
| RERA file: project 14,000 sft, 20 units (3BHK), stilt+G+3, HT 14.99 m, plot 1300.58 sqm, FAR 2.00 (2559.82 sqm), coverage 45.84% | — | context for thresholds below |

Download both via `tools.gws_auth.build_service('drive','v3',service_name='google-draas').files().get_media(fileId=...)`.

## Reading the correction letter (docx)

- Plain text extraction: `unzip -p file.docx word/document.xml` + strip tags — fine for body.
- **The Infra table is often an EMBEDDED IMAGE, not a table** (w:tbl count = 0). The letter
  says "as detailed below:" then the items live in `word/media/image1.png`. Extract with
  `unzip -o -j file.docx word/media/image1.png -d /tmp/` and OCR with `vision_analyze`.
- Amber correction table = Internal 1–7 (Water Supply MANDATORY stays Yes; Sewage/Drainage,
  RWH, Energy mgmt, Fire safety, Solid waste, Emergency evacuation marked Yes→No) and
  External 1–12 (all Yes→No incl. transformer, STP, parks).

## Reading the approved plan (two layers)

1. **Architect drawing set** (eg `AMBER SANCTION …pdf`): HAS a clean vector text layer →
   `pdftotext -layout` is authoritative. Site plan labels: DRIVEWAY, TRANSFORMER, Electrical
   Room, Security Room, parking bay nos, 9.14 m road, setback lines, ORIENTATION/NORTH.
2. **AutoDCR sanctioned output** (site plan + condition sheets): text layer is partial/garbled
   → render with `pdftoppm -png -r 150..300` then `vision_analyze`. Drawing labels are tiny:
   crop with PIL first (`im.crop(...)` from the 300-dpi render) and zoom before OCR.
   - Site-plan labels that matter: **R.W.H** (rain-water harvesting recharge points, often
     multiple around the building), DRIVEWAY, adjacent plot names, road width (9.14 MT WIDE
     ROAD), building title ("PROPOSED RESIDENTIAL BUILDING AT ST+GF+FF+SF", "H.T. OF BUILDING = 14.99M").
   - The sheet itself carries **RWH cross-section details** (percolation well ∅0.15 m bore,
     percolation pit/ trench with sand/aggregate layers) and a **Solar Unit diagram**
     ("1000 lts capacity solar water heater — will be installed").
   - Terrace plan: **O.H.T (overhead tanks)** x2; floor plans: lift, staircase, common toilet,
     PH ramp condition.
   - Do NOT expect an STP label — sewage runs to BWSSB mains (cond 4).
   - The word TRANSFORMER may appear on the architect set but not OCR from the AutoDCR site
     plan crop — rely on Condition 10 which mandates transformer space within the premises.

## The 50-condition infra map (GBA/BECC AutoDCR sanction, Bengaluru East)

Conditions that decide RERA infra Yes/No — cite these when verifying:

| Cond | Requirement | Maps to RERA item |
|---|---|---|
| 4 | Dev charges to BWSSB + BESCOM (water/sanitary/power mains) | water supply, sewage & drainage |
| 5 | Space for garbage dumping within premises | solid waste management |
| 10 | Space for distribution transformers per KERC (E&S D) code, 3 m from building | electricity transformer & substation |
| 21 | BWSSB drinking water not for construction | water supply |
| 22 | RWH structures provided & maintained (Bye-law 32(a) capacity) | water conservation / RWH / recharge |
| 24 | Solar water heaters per Table 17 | energy management, renewable energy |
| 25/26/27 | PH access + common toilet ground floor; **OC only after 23/24/25/26** | accessibility |
| 29 | Garbage segregation organic/inorganic + **recycling/processing unit at site — Residential units of 20 AND ABOVE** | solid waste management (Amber = 20 units → APPLIES) |
| 33–36 | Fire clearance every 2 yrs + annual inspection + 2 mock drills — **high-rise only (≥15 m)** | fire protection & safety (Amber 14.99 m → technically NOT triggered) |
| 41/42 | SWM Bye-laws 2016 + C&D waste | solid waste |
| 43 | EV charging provision | energy management |
| 44 | Tree planting: min 2 trees (>240 sqm site) + 1 per 240 sqm FAR → Amber ≈ 11 trees | parks & tree planting |

## Deliverable: item→evidence→risk matrix

For EVERY item the letter wants to flip Yes→No, say: (a) what the plan/conditions show,
(b) verdict CONSISTENT / CONTRADICTS / CODE-MANDATED-BUT-NOT-EXPLICIT, (c) the risk of
filing. Lead with the bottom line: which items are defensible, which are not.

Ranka Amber worked verdicts:
- **Defensible as No in plan:** STP (absent everywhere; sewage→BWSSB), Emergency evacuation
  (no provision at this height), Parks (no park; only tree planting).
- **Contradicts the sanctioned plan (do NOT blanket-No):** RWH (cond 22 + R.W.H points +
  drawn percolation wells), solar/renewable (cond 24 + 1000 l unit in drawing), transformer
  (cond 10 + TRANSFORMER label), solid waste (conds 5/29/41 — 20 units triggers recycling
  unit), internal roads/driveway (DRIVEWAY on site plan), sewage & drainage (unit plumbing +
  BWSSB mains cond 4), tree planting (cond 44).
- **Water Supply stays Yes** — consistent (OHT + BWSSB).

## Pitfalls

- **docx tables can be images** — check `word/media/` before concluding the list is missing.
- **Choose the text layer by probing, not habit**: architect sets pdftotext; AutoDCR scanned
  pages → render + crop + vision. Vision OCR on the raw site-plan render returns noise
  (`SS'6P'L1…`), not labels — zoom crops at 300 dpi.
- **`vision_analyze` on these sheets is OCR-contextual**; if a critical label (TRANSFORMER)
  is ambiguous, cite the condition + the drawing-set text layer rather than asserting the
  AutoDCR crop shows it.
- **Not every 50-condition reading is stable**: the same condition block may OCR differently
  at different resolutions (cond 10 read once as firefighting equipment, once as transformer
  space — the E&S D code text is authoritative).
- **RERA form semantics are "provided by the promoter"**: a BESCOM-owned transformer in an
  earmarked space still means the project "provides" transformer & substation infrastructure.
- The blanket claim "neither required under town planning norms nor proposed/provided" fails
  the moment ANY one condition or drawing element requires the facility — advise revising the
  letter to correct only the defensible items.