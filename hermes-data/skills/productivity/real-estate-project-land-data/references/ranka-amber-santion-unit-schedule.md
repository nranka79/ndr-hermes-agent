# Ranka Amber — Sanctioned-Plan Unit Schedule & SSA Numbering (verified 2026-09-22)

Context: cross-checking the Supplementary Sharing Agreement (SSA) unit numbers/areas against
the BBMP sanctioned plan instead of trusting the signed PDF. All file IDs under Drive
`Ranka Amber Approvals` / `Ranka Amber Title` via service_name=google-draas.

## Building licence (clean text layer, authoritative)
- `Ranka Amber Building Sanction Planpdf` (1LuwlNxmPAzvYmbxnK9l6lWTsPWkKc3KL) — 6-page licence, grayscale, `pdftotext -layout` works.
- **BBMP/CC/4247/26-27**, LP GBA/MDP/DDTP/0007/26-27, Project GBA/BECC/0540/25-26
- Date 27 Apr 2026, accepted 7 May 2026 (EoDB JC Mahadevapura Zone 1, BECC)
- Site area **1,300.58 sq.m**; Block A (Residential); **Stilt + Ground + 3**; **20 tenements**; height 12 m; total BUA **3383.17 sq.m**
- FAR area **2559.82** sq.m (per drawing schedule); **Total Car 22** (302.50 sq.m) — matches SSA parking 22
- PID 7057785976, Khata 4/124, Plot 1-B, D'Silva Layout, Pattandur Agrahara Village, Ward 083

## Sanctioned drawing (A0, REAL text layer — pdftotext -layout pulls the full unit table)
- `Ranka Amber Approved Plan _0540_25-26.pdf` (1vgwreceF9ar83saqUaNYLibL4CIp_N8O) and
  `20260518_Ranka_Amber_Sanctioned_Plan_GBA_BECC_0540_25-26.pdf` (1fT5XUa8pWsxUoCQYmaBEr9yTc6mEOYTQ)
  — 2 pp, 2384x3370 pts, producer pdfplot16.hdi (same family as layout-plan extraction
  `references/layout-plan-plot-area-extraction.md`). `pdftotext -layout` yields the
  per-floor unit schedule lines like `GROUND FLOOR PLAN  GF1  FLAT  121.73  121.73  8`.
- Approvals folder also holds `20260416 Ranka Amber Sanction Approval Drawing GPA Pre-DCR.pdf`
  (19OaMXtcnBeRSL9LjI2lstqpNy50S5ViG) — pre-DCR, not the final sanction.

## Unit schedule (carpet sq.m, identical on all 4 floors)
| Plan unit | Carpet sq.m | Tenements |
|---|---|---|
| GF1/FF1/SF1/TF1 | 121.73 | 8 |
| GF2/FF2/SF2/TF2 | 124.68 | 8 |
| GF3/FF3/SF3/TF3 | 108.21 | 8 |
| GF4/FF4/SF4/TF4 | 90.94 | 7 |
| GF5/FF5/SF5/TF5 | 110.71 | 8 |

## SSA numbering (executed 24-06-2026 vs re-issue)
- Signed SSA marketing numbers: Ground **101–105**, First **201–205**, Second **301–305**, Third **401–405**
- Re-issued (2026-09) marketing numbers: Ground **001–005**, First **101–105**, Second **201–205**, Third **301–305**
- Allotment: LANDOWNERS = Ground + Third; DEVELOPER = First + Second (50:50, 10 units each)
- SBA per unit: Ground/Second 1486/1518/1288/1058/1313; First/Third 1570/1605/1380/1141/1413 (sq.ft)
- UDS 755.24–815.59 sq.ft; saleable total 27,544 sq.ft (2558.9 sq.m); per-side 11,976 sq.ft BUA / 11,652 sq.ft RERA carpet
- Signed PDFs: For_Raghu 1IkNoLeNVCtOtgxFDbWW0MNRVmqGG1eUE, For_DRA 1Ygo5p4JUUYswnwJffLS6Z9IpAnQyCkIU

## ⚠ Conflict flag — Customer Area Statement is NOT authoritative for current numbering
- `Ranka Amber - Customer Area Statement.pdf` (1yZEj1HhGOujhdflwtgtVGYn_TLjycldQ) is a
  **1-page image-only** PDF (needs vision OCR / pdftoppm, no text layer) carrying the OLD
  4-floor design numbering: 101–105 **First**, 201–205 **Second**, 301–305 **Third**,
  401–405 **Fourth**; per-unit SBA 1687/1712/1468/1219/1504 etc.; total SBA 31,853 sq.ft,
  UDS loading 0.4395, plot 14,000 sq.ft.
- Its unit numbers conflict with BOTH the signed SSA numbering and the sanctioned plan
  (Stilt+G+3, not 4 upper floors). Predates the final sanction — do not use it to verify
  the current unit numbers or SBA.

## JDA / Addendum T&C anchors (2025-08-16)
- JDA word/registered: `20250810 JDA Raghu Iyer Whitefielf 14K sqft` (1i8rOWUVsJNlNC6zSLqn6_i-se1gf1POJ_vMIt4tVIuY);
  registered `20250816 JDA Reg N0 2227(2025-26).pdf` (1eceImiIY2T6ObI-5j5lxRZ07PLJuNx2i);
  Addendum (1O8NJAa4Jt2LpgFCMsAnwom9tiymx5CVq); irrevocable GPA 277/2025-26 (1Fl9eeomOG8k4379CibgiA4Z9kAVQltRx)
- JDA: 50:50 SBUA sharing (cl 5.4), IFRSD ₹1 Cr, completion 24 months + 6 grace from execution (cl 7.3/7.8)
- Addendum: amended SBUA definition, inserted cl 9 Marketing & Sales (4% fee, 2% NRI-referral)
- SSA vs JDA conflicts to flag: SSA cl 17 "no irrevocable POA" vs JDA 3.12 + registered GPA 277/2025-26;
  SSA possession 30 months from RERA registration vs JDA 24+6 from execution.