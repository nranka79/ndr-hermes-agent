# Statutory / Regulatory Notices Against DRA Projects — Response Playbook

Class of task: government department notices (BMTF/police, Labour Dept,
BBMP) against DRA projects (e.g. Ranka Amber). Pattern established
Sep-2026. NDR wants: zero-cost closure, full delegation to Rahul (Vinod
Kumar Das) via task tracker, report only on completion. Minor chai-pani
acceptable; no formal payments.

## First-pass triage (always, in order)
1. Translate the notice (Kannada→English); file original scan + English
   reproduction PDF into `<Project> > Legal Notices` Drive folder with
   `YYYYMMDD_Project_Issuer_Notice_...` naming.
2. Check what is ALREADY PAID / already done before responding — most
   demands are answered by existing proof (e.g. labour cess collected at
   plan sanction by BBMP/GBAE — see below).
3. Check statutory applicability thresholds — most "fishing expedition"
   record demands die at the threshold table (below).
4. Push record/register demands to the turnkey contractor (pull from
   Kelsa PO/WO records); make labour-record submission a standing
   invoice-clearing prerequisite for the contractor.
5. NDR: 5-6 workers typical at site → most labour statutes don't apply.

## Labour statutes — applicability thresholds (Karnataka)
| Act | Threshold | Notes |
|---|---|---|
| BOCW (RECS) Act 1996 | 10+ building workers employed on any day in preceding 12 months (S.1(4)) | Below → no S.7 registration, no Form-I/IV/X/XXXV |
| BOCW Welfare Cess Act 1996 | No headcount threshold — 1% of cost of construction (S.3; Karnataka 1%) | Collected via local authority AT APPROVAL (S.3(2)) — usually already paid with plan sanction fees |
| Contract Labour (R&A) Act 1970 | 20+ contract workmen on any day in preceding 12 months (S.1(4)(a)) | Below → no licence (Forms 16-24), no principal-employer registration |
| Minimum Wages Act 1948 | Building operations = scheduled employment in Karnataka; applies regardless of headcount | Form-I attendance/wages register + Form-VI wage slips; cheap admin compliance |
| Karnataka Industrial Establishments (N&F Holidays) Act 1963 | Industrial establishments; every employee | Holiday list display in Kannada + English; holiday wages |
| Inter-State Migrant Workmen Act 1979 | 5+ inter-state migrant workmen (S.1(4)(a)) | At 5-6 total workers bites ONLY if workers came from other states — get factual answer from contractor |

Net at ≤5-6 local workers: only Cess (already paid), Minimum Wages,
holidays display apply. The rest of the notice is a fishing expedition —
respond on paper, don't ignore.

## Labour cess — already paid at plan sanction (proof)
Ranka Amber: ₹6,25,000 paid 27-Apr-2026 — Receipt BBMP/EoDB/RC/5754/26-27
(Transaction ID 114493156453) against Demand Note BBMP/EoDB/CH/5255/26-27
(File GBA/BECC/0540/25-26). Proofs in Drive: DRA Realty > Ranka Amber >
Approvals > Demand Notes. This is the single strongest answer to any
LOB-3/CESS notice; submit demand note + receipt and request assessment be
stayed.

## BMTF / police notices — legal position
- Formed under GO UDD 247 MNU 95 dated 15.04.1996 (Karnataka Urban
  Development Dept). Investigates under ~12 Acts (KMC Act, KLR Act incl.
  S.192-A, BMRDA Act 1985, Inam Abolition, SC/ST PTC) — NOT IPC offences.
- No jurisdiction over private property with a sanctioned building plan
  (Karnataka HC 2013, quashing BMTF FIRs re: unauthorized construction).
- Notice defects that defeat the notice (Karnataka HC, 30-Jul-2024, re
  BNSS S.35): no crime/FIR number, no penal sections cited, no copy of
  FIR appended → noticee NOT obliged to appear and no coercive action for
  non-appearance.
- KLR Act has no application within BBMP/GBA limits even for land still
  agriculturally classified (Karnataka HC Division Bench, May 2026).
- Prosecution under KLR S.192-A requires a prior, valid show-cause notice
  (Brigade Gateway line of cases).
- Playbook for a defective notice: DO NOT appear on the given date;
  reply formally through counsel citing the defects + jurisdiction; obtain
  a BBMP/BECC compliance letter (sanctioned plan, no govt-land
  encroachment); if an FIR is filed → quash petition (HC consistently
  quashes BMTF cases for lack of jurisdiction); delay within law (formal
  per-notice replies, anticipatory bail if needed, discharge).

## Translation via Gemini (Kannada→English)
- `call_openrouter_model` may reject translation prompts it classifies as
  vision tasks. Fix: call the OpenRouter API directly via
  terminal/execute_code (key in /opt/hermes/.env, model
  google/gemini-3.5) with the already-extracted text — text-only, no
  images. Preserve layout: request HTML/CSS replica, render to PDF (A4
  @page), verify page-by-page with vision against the original scan.

## Known contacts
- Jayram (Jayaram Gowda) / "Jeram" — proprietor, Vardhan Ventures (a.k.a.
  Vardhan Constructions). Ranka Amber turnkey contractor (PO-739, ₹4.03 Cr,
  WO 09-Jun-2026). info@vardhanventures.in / mejayaramgowda@yahoo.co.in /
  +91 99802 99080. Office: No.79 5th Floor Sharada Market, C.T. Street,
  Bengaluru 560002. GSTINs: 29BAVPP6247E1Z1 (Vardhan Ventures) /
  29ANSPJ9078NIZQ (Vardhan Constructions).
- Rahul = Vinod Kumar Das (vkdas@draas.com, +91 99000 93813) — SPOC for
  statutory notice closure.