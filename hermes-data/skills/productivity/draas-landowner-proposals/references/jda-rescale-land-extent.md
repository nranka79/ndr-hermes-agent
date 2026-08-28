# JDA land-extent rescale — worked recipe (10 → 7 acres, Bidadi, Jul 2026)

When the user says "update this proposal to land EXTENT of about X acres, so all the
numbers, calculations, offer, costing, everything changed accordingly", scale every
extent-dependent figure by ×(new/old). Per-sqft rates and per-sqft invariants do NOT
change. This file records the complete 10→7 ac recompute (×0.70) as a worked example —
repeat the same shape for any other extent.

## Step 1 — recompute the model

| Item | Formula | 10-ac (old) | 7-ac (new) |
|---|---|---|---|
| Gross land area | acres × 43,560 | 4,35,600 sqft | 3,04,920 sqft |
| Net developable | gross × ~53% | 2,30,868 sqft | 1,61,608 sqft |
| Villa yield | 15 villas/ac × acres | 150 | 105 |
| Split 33:67 | total/3 : 2·total/3, integers summing to total | 50 / 100 | **35 / 70** (exact 1/3 : 2/3 on 105) |
| Built-up | villas × 2,500 sqft | 3,75,000 | 2,62,500 (LO 87,500 / Dev 1,75,000) |
| Construction | 3,500/sqft × total built-up | 131.25 Cr | 91.88 Cr |
| Infrastructure | 600/sqft × total built-up | 22.50 Cr | 15.75 Cr |
| Approvals | 200/sqft × total built-up | 7.50 Cr | 5.25 Cr |
| Deposit | **10% of illustrative land value** (₹5 Cr/ac × acres × 10%) | 5.00 Cr | **3.50 Cr** (= 10% × ₹35 Cr) — user-confirmed JDA convention, NOT a scaled assumption to flag |
| Financing & overheads | balancing figure ≈ 14% of total (70% debt × 10% × 24 mo = 0.14×total); total = (other costs)/0.86 | 27.04 Cr | 18.94 Cr |
| **Total cost** | | 193.29 Cr | **135.32 Cr** |
| Gross revenue/scenario | price/sqft × developer sqft (1,75,000) | | 9,500→166.25; 10,500→183.75; 11,500→201.25 |
| Marketing 5% | 5% of gross | | 8.31 / 9.19 / 10.06 |
| Net revenue | gross − marketing | | 157.94 / 174.56 / 191.19 |
| Profit | net − 135.32 | | **22.62 / 39.24 / 55.87 Cr** |
| Margin | profit/net | | **14.3 / 22.5 / 29.2% — identical to 10-ac (sanity check)** |
| Landowner value | 35 × 2,500 × ₹10,500 | 131.25 Cr | **91.88 Cr** |
| Land-value reference | ₹5 Cr/ac × acres | ₹50 Cr | **₹35 Cr** |
| Breakeven | per-sqft — **scale-invariant, KEEP ₹8,207** | ₹8,207 | ₹8,207 |
| Villas to breakeven | ~74% of developer share | ~74 of 100 | **~52 of 70** |
| Equity | 30% × (dev cost excl. financing+deposit) + deposit = 0.3×112.875 + 3.5 | ~₹53 Cr | **~₹37 Cr** |
| Sales velocity | per-phase counts sum to developer share; ~60% by month 18 | 20–25/35–40/25/15 | **15 / 25 / 18 / 12 = 70** |

Key invariant: **pure linear scaling leaves margins unchanged** (14.3/22.5/29.2% in both).
If your recomputed margins differ, a formula is wrong.

## Step 2 — edit the HTML source (`/opt/data/bidadi_jda_proposal.html`)

Every section carries extent-dependent numbers. Complete sweep list:
cover subtitle + cover-meta Property + version bump (BID-LO-JDA-V1.0 → V1.1, and the
letter "Encl:" line) · letter subject ("your approx. 7-acre land parcel") · letter offer
para (35 fully-built villas + ₹3.5 Crore) · S1 Land Overview (area, villas) · S1 JDA
Transaction (33% = 35 villas 87,500 sqft; 67% = 70 villas 1,75,000 sqft; deposit ₹3.5 Cr;
reference value ₹35 Cr → ₹92+ Cr) · S1 scenario table + footnote + breakeven line ·
S2 exec summary para + both KPI card rows · S2.1 land consideration + returns ·
S2.2 bullets · S3.1 key terms · S3.2 yield table · S3.3 split table · S3 protection box
("Landowner's 35 villas") · S4.1 area + proposed use · S6.2 scarcity bullet (70 developer
villas) · S7.3 sales velocity counts · S8 box + 8.1 cost table + 8.2 multiplier box
(effective cost = total/dev sqft = 7,733/sqft) · S9.2/9.3/9.4 tables + 9.5 bullets + 9.6
equity & repayment · S10 benefits table + what-landowner-keeps box · S11.1 · S12 step 3
(deposit) + step 6 (all 105 villas).

Leave per-acre references alone: "₹5.0 Cr per acre" and the disclaimer's "land value
₹5 Cr/acre reference" are correct regardless of extent.

## Step 3 — stale-number sweep

After edits, grep the HTML for the FULL old-number set. Every hit except the intended
per-acre references must be fixed:

```
4,35,600|3,75,000|2,50,000|1,25,000|193\.29|131\.25|262\.50|393\.75|56\.09|79\.84|32\.34|225\.62|249\.38|273\.12|237\.50|287\.50|131\+|27\.04|74 of 100|10-acre|10 acres|~150|150 villas|100 villas|50 villas|&#8377;5 |5\.0 Cr|50 fully|100 fully
```

## Step 4 — rebuild + verify

- PDF: WeasyPrint → NEW filename (`Bidadi_7Acres_JDA_Proposal_2026-07-31.pdf`); keep old
  files on disk.
- DOCX: parametrize the brand script's `out =` path (copy of `brand_docx.py` →
  `brand_bidadi_docx.py`), run pandoc static binary + navy/gold post-processing
  (see `references/html-to-docx-branded.md`).
- Verify with pdftotext:
  - `pdfinfo` page count (stayed 17 — same structure, numbers only)
  - grep for key NEW numbers: `105 villas|~105|35 fully|70 villas|135\.32|91\.88|39\.24|3,04,920|2,62,500|87,500|1,75,000`
  - stale grep (step 3) must return 0 hits
  - per-page `pdftotext -f N -l N` non-empty line counts — no page < 16 lines (orphan check)
- Deliver BOTH PDF + DOCX via MEDIA: lines.
- **Deposit labeling (user-confirmed):** after rescale, state in the doc that the deposit = 10% of the ILLUSTRATIVE land value — S1.2 deposit row ("refundable, 10% of illustrative land value (recoverable against the landowner's share realisation)"), S1.2 reference-value row ("₹5.0 Cr per acre (₹35 Cr total) — illustrative, used only to derive the 10% deposit; replaced by the 33% share, expected to realise ₹92+ Cr"), S3.1/S11.1 deposit rows (10% of illustrative land value), and the disclaimer ("land value ₹5 Cr/acre reference — illustrative, for the 10% refundable deposit"). Never present land value as a valuation opinion.
- **Pagination pitfall after wording additions:** the extra deposit/reference wording lengthened rows and pushed the doc 17→19 pages with orphan pages (P4 held only the breakeven line; P19 only the brand footer). Compact the added wording, then shrink the S12.2 signature spacers 10mm→8mm and brand-line margin 6pt→3pt; re-run the per-page line-count orphan check (min 16 lines/page).
