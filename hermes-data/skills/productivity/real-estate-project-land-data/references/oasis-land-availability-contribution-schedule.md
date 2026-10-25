# Oasis Land Availability — Contribution Schedule Reconciliation (verified 2026-09-16)

Answering "land availability for our internal numbers: total held / already
relinquished-committed / balance available to contribute" for DRA Realty's land
under Ranka Oasis (Sevaganapalli), before finalising a contribution schedule
(e.g. DRA Realty → partnership-firm capital contribution).

## The three-bucket survey-wise schedule (deliverable shape)

1. **Total held** — registered owned parcels, split into *approved layout*
   (Investor Portfolio §I) vs *outside approved layout* (Investor Portfolio §J).
2. **Already relinquished / committed** — gift deeds (roads/OSR, TNEB),
   plot-level sales, JDA land (landowner's, NOT owned), agreement-only parcels,
   mortgages/charges. These CANNOT be contributed.
3. **Balance available** — registered owned minus committed; note sanctioned-plot
   rights separately (they attach to approved surveys only).

## Source order (use before re-deriving from scans)

1. `20260707_DRA_Group_Investor_Portfolio_All_Projects` (1wDKS0SxtY0EF_-JUe2BfXzLSSwh4J5fo4y0sI_brFfw)
   → Ranka Oasis tab: §H owner summary, §I approved-plan parcels (19 rows, 751.5c),
   §J not-in-approved (277c). `values().get` WORKS on this workbook (unlike the
   matrix/master-data workbooks).
2. Kagganur Master Data `Ownership details (Registered)` (export-parse; see
   seveganapalli-ownership-master-data.md) — Belongs To / Ownership Vide.
3. DRA Sevaganapalli Project Breakdown by Survey number
   (1gfAFQMnuxNmm4HrxA5uARkLriHaSju_xUmRl6xdJWa8, owner madhu.ga@gmail.com) —
   newer sub-divisions + Phase flags.
4. Deeds (scans → tesseract `--psm 3`): gift deeds, sale deeds, Plot 119 set.

## DRA Realty position worked example (16-Sep-2026)

**TOTAL HELD (registered owned) = 162.5c / 1.625 ac**
- Approved (Phase I, §I): 158/1C9A 0.25 (SD 21785/2024, Patta 2058); 176/1B2D
  0.16 + 176/2B4A 0.225 + 177/1A1A 0.025 + 177/1A1B 0.235 (Exchange 4292/2024,
  Patta 2000) = 89.5c
- NOT in approved plan (§J, Phase II): 158/1C3 0.25, 158/1C4 0.38, 158/1C6 0.10
  (SD 21785/2024) = 73c
- ⚠️ Workbook §H summary says DRA 140c vs parcel-sum 162.5c (±22-25c attribution
  shift on 158/1C9A/158/1C3) — flag, never pick a side silently.

**RELINQUISHED / COMMITTED (cannot contribute)**
- **Plot 119** — 1,492.7 sq ft (~3.4c) carved out of **158/1C9A**; restructured
  sale deed = **VENDOR DRA Realty + CONFIRMING SLP** (Sevaganapalli Land Partners
  as co-promoter), buyer Prathyusha Vuppala. Deed set: `Plot 119 Legal Set`
  (1lVlRlVKzHc4ID4H7e_ec3toSSfiYeo1w): Agreement for Sale, Absolute Sale Deed
  COMPLETE/RESTRUCTURED/DETAILED drafts (20-21 Aug 2026) + Schedule A/B/C pattern
  (A = 19-survey project land ~7.53 ac; B = 158/1C9A; C = Plot 119 measurements).
- **Gift Deed 9188/2025 → TN Govt** (1pg1wHAebnKgtqIf2vERs4X0Xf32Zag8z): internal
  layout Roads 1–17 + Local Body Areas + Parks = **12,866.03 sqm** gifted for
  roads/OSR; per-road survey mapping in recitals (e.g. Road 14 under 158/1C9A;
  Roads 2/3/16 under 177/1A1B).
- **Gift Deed 9196/2025 → TNEB** (1sBoa7Evhf779HHm7Mot1XikeYMiZE_qP): electric
  corridor ~247.48 sqm from 176/1B2D, 176/2B4A, 177/1A1A, 177/1A1B, 158/1C9A/1C9B
  + JDA parcels.
- **JDA land (landowner's — NOT owned)**: 166/1 0.35, 167/1G 0.07, 168/1B 0.53
  (Ramesh Reddy JDA 7963/2025 + GPA 915/2026); 177/1B 0.323, 177/2A1 0.177
  (K Harish JDA 6157/2025). DRA holds development rights only.
- **168/1A 0.95 ac** — Agreement to sell only, advance paid, NOT registered →
  not contributable until registered.
- **166/2B legacy 0.30** vs 166/2B2 0.10 (SLP, Patta 1941) — confirm current
  patta before treating as available.
- **Mortgage without Possession 7049/2025** — SLP → 10 individual investors
  (encumbrance, SLP-side).

**BALANCE AVAILABLE to contribute**
- Approved: 89.5c gross − Plot 119 (~3.4c) ≈ 86c; further netting = road/OSR/TNEB
  gift shares (needs plot-to-survey map for exact per-survey splits).
- Non-approved: 73c clean, no commitments found.
- Sanctioned-plot rights: DTCP **11996/2022/A4 dt 13.01.2026** — 30,416 sqm,
  130 plots / 17,802.49 sqm site; rights attach to the approved-survey parcels
  (89.5c), NOT to the non-approved 73c.
- ≈ 1.59 ac contributable today before road/OSR netting; +0.95 if 168/1A registers.

## Pitfalls & techniques

- Gift deeds are multi-page scans with NO text layer — tesseract default psm
  returned EMPTY on every page; `--psm 3` recovered the survey schedules and
  extent blocks. Always retry `--psm 3` before declaring a scan unreadable.
- Plot 119 deed drafts on Drive are native .docx (not Google Docs): `export_media`
  fails — use `files().get_media`; parse XML with ElementTree (their tags use an
  `ns0:` prefix, so `re.findall(r'<w:t…')` matches nothing).
- The gift deed schedule lists the donors' full title surveys ("Full extent" per
  survey) even when only a small corridor/road portion is gifted — read the
  boundary/measurement block, not the schedule header, for the actual gifted area.
- Board-resolution context for the contribution class: 24-06-2026 BR of DRA Realty
  (DRA KAAJ Dev Partners) approving Managing-Partner role, 51:49 (DRA:Ashok Kumar),
  contribution of Palya Sy 8/1 2A6G + Byadarahalli ~40 ac + C.R. Nagendra lands,
  ₹10 Cr capital (₹5.5 Cr deployed, ₹1 Cr cheque, ₹3.5 Cr balance). Same pattern
  applies to Oasis land → partnership contributions.