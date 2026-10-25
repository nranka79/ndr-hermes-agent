# RERA Registration Correction — verify Internal/External Infrastructure claims against the approved plan

Session-verified method (2026-10, Ranka Amber correction letter vs sanction GBA/BECC/0540/25-26).

## When to use
The promoter wants to "correct" the K-RERA project registration record — Internal/External
Infrastructure entries marked Yes at registration, proposed to flip to No via a correction letter.
**Before drafting the letter, verify every line item against the sanctioned building plan.**
RERA cross-checks registration forms against the sanction; a blanket "not applicable / not
provided" claim contradicted by the approved plan invites pushback and poisons the genuine items.

## Method
1. **Get the correction docx's item table.** It is often an embedded IMAGE, not a `<w:tbl>`
   (`unzip -p …/word/document.xml` shows 0 tables). Extract `word/media/image1.png` and OCR with
   `vision_analyze` to recover the exact RERA-form item labels (they differ between Internal and
   External lists — preserve them verbatim in the memo).
2. **Pull both plan documents from Drive**: (a) the AutoDCR sanction PDF (`GBA/BECC/0540/25-26`
   style — has the numbered conditions + site plan + cross-sections), (b) the stamped drawing set
   (`AMBER SANCTION 07.05.2026.pdf` style — site plan, stilt/GF/floor/terrace plans, section).
   Search: `name contains '<project>' and (name contains 'Sanction' or name contains 'Approved')`
   plus the sanction folder's `pdf/` subfolder.
3. **Read the plans**: `pdftotext` for vector labels (TRANSFORMER, DRIVEWAY, R.W.H, DUCT, O.H.T,
   Solar Unit) and the full conditions block; `pdftoppm -png -r 300` + PIL crop of the site plan
   for `vision_analyze` to read small plan labels verbatim ("Read EVERY small label/symbol … be
   exhaustive and verbatim").
4. **Map each form item to sanction conditions + sheet refs.** Keep one row per item.
5. **Classify verdicts**:
   - `CONTRADICTS` (red) — the plan/conditions require it → keep "Yes".
   - `DEFENSIBLE "No"` (green) — genuinely absent (STP; emergency evacuation below 15 m; storm
     drains when runoff is handled by RWH percolation, worded with that clarification).
   - `PARTIAL` (amber) — split the item (e.g. Parks "No" but Tree planting "No" is wrong).
6. **Deliver an item-by-item verification memo** (.docx via python-docx — see
   `professional-documents`) with a one-line summary verdict table (counts per verdict), per-item
   tables (Sl | Item | What plan/conditions show | Sheet/condition ref | Verdict), a key-risks
   section, and a recommendation (surgical correction vs withdraw).

## Karnataka (BBMP AutoDCR) sanction condition cheat-sheet
Condition numbers below are from the standard 50-condition BBMP sanction (GBA/BECC series);
re-verify per actual sanction but expect the same pattern.

- **Cond 4** — dev charges to BWSSB/BESCOM for water-supply/sanitary/power mains → external water
  supply & sewage connection = Yes.
- **Cond 5** — garbage dump space within premises → solid waste = Yes.
- **Cond 10** — space for distribution transformers per K.E.R.C (E&S D) code, 3.00 m from
  building, within premises → transformer/substation = Yes. Also marked "TRANSFORMER" on site plan.
- **Cond 22** — RWH structures mandatory (min capacity per Bye-law 32(a)) → RWH/recharge = Yes.
- **Cond 23** — NBC compliance → fire protection = Yes (even when high-rise fire conditions don't bite).
- **Cond 24** — solar water heaters per Table 17 of Bye-law 29 → energy management / renewable = Yes.
- **Cond 27** — OC considered only after conditions 23/24/25/26 → the OC chain; filing
  "renewable energy = No" contradicts the OC dependency.
- **Cond 29** — waste segregation + recycling/processing unit at site, applicable to
  **"Residential units of 20 and above"** → know the project's exact unit count before arguing
  "not required". Amber has exactly 20 units → trigger applies.
- **Cond 33–36** — high-rise fire mock-drills/certificates: bite only at **≥15 m** HT. At
  14.99 m they don't bite (and emergency-evacuation services can defensibly be marked No).
- **Cond 41/42** — SWM Bye-laws 2016 + C&D waste.
- **Cond 44** — tree planting: sites >240 sqm → min 2 + 1 per 240 sqm of FAR (≈11 trees on Amber).
  "Parks" (as a layout/DP item) is not in a single-plot building sanction → split the verdict.

## Pitfalls
- The letter's opening blanket claim should be dropped even if a few items are defensible — it is
  contradicted on most items and weakens the whole filing.
- Map RERA form item names exactly (Internal: Water Supply [MANDATORY], Sewage & Drainage, RWH,
  Energy management, Fire protection, Solid waste, Emergency evacuation; External adds roads &
  footpaths, transformer/substation, storm drains, renewable energy, STP, Parks & Tree planting).
- OHT tanks on terrace plan + BWSSB connection keep **Water Supply = Yes** on both lists.
- STP is the cleanest defensive item: absent from plan and drawing set, sewage → BWSSB mains (Cond 4).

## Worked example (Ranka Amber)
- RERA PRM/KA/RERA/1251/446/PR/050826/008859; sanction GBA/BECC/0540/25-26 (AutoDCR, 13.05.2026,
  Zone Mahadevapura, Ward 083); drawing set AMBER SANCTION 07.05.2026 (DRA Realty / Ar. Bhuvanesh).
- 20 units, HT 14.99 m, 22 car parks, 9.14 m road, Plot 1-B D'Silva Layout, Whitefield.
- Outcome: 9 of 18 items CONTRADICTS (RWH, solar, transformer, solid waste, sewage, driveway,
  fire); 4 DEFENSIBLE No (emergency evacuation ×2, storm drains w/ caveat, STP); 1 PARTIAL
  (Parks & Tree planting → split); Water Supply stays Yes ×2.