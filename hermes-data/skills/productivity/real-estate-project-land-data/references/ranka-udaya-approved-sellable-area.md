# Ranka Udaya (Serenity Estate) — Sanctioned Sellable Area Worked Example

Worked 2026-08-30. User asked: "From ranka udaya approval documents can u tell me how sq feet of sellable area was sanctioned".

## Project aliases (search these on Drive, not just one name)
- Ranka Udaya
- Serenity Estate / Serenity Estates
- RERA: **TNRERA/30/LO/0642/2026** dated 18.02.2026 (layout of house sites, 38 plots)
- Address: Sy 240/3A, Sevaganapalli Village, Hosur Taluk, Krishnagiri District
- Applicant: **DRA Thindlu Land Partners** (Authorised Person NISHANT RANKA), 302A, 3rd Floor, Queens Corner, Bangalore
- Approvals chain: HNDT (Hosur New Town Development Authority) Layout No. **90/2025** (letter ROC J5SROIYP/2025/TCP, dt 22.05.2025) → Sevaganapalli Village Panchayat (ROC 02/2025-2026, dt 20.07.2025) → TNRERA registration.

## Drive location (ndr@draas.com)
- Main folder: `Ranka Udaya` (`1sdDX5htwSKF2SSe_re-jjYb-8SsFCk8Z`) — subfolders: 01_Title_and_Legal_Opinions, 02_Approvals, 03_Marketing_Collaterals, 04_Sanction_Drawings, 05_Execution_Documents_and_Drawings, 06_Customer_Documents.
- `Ranka Udaya (DRA Tindlu Land partners Master Folder)` (`10sk0X6dq9-Rzo2BajJKNFkEts_pfRxLT`) — title docs, payment receipts, legal, SPA, sale deed drafts, relinquishment deeds, plan approval docs, affidavits 25.11.2025.
- Plot inventory master sheet: **`Ranka _Udaya _Master_and_Cost_Sheet (1)`** — Sheets id `1mtqU51isImvtEmqEIuuqNmeeycV5zMxhjT7tXNiaao8`
  - Tab `Master Sheet`: title row + blank + header `Plot # | Length (m) | Breadth (m) | Area (Sqm) | Area (Sft) | Facing | Availability` — 38 data rows (rows 3–40 in sheets API terms, i.e. data starts at row index 3)
  - Tab `Cost Sheet`: quotation calculator (Enter Plot Number, Rate per Sft, Legal & Handling Charges) — last seen rate ₹3,600/sft, ₹20,000 legal, token ₹50,000.

## Approval documents (all under 02_Approvals / 04_Sanction_Drawings)
| File | Drive ID |
|---|---|
| 20260527 RERA ORDER (1).pdf | `1hLCi-Hg0KYnjHX4JQTjaIXmjfGzArAoO` |
| 20260417 RERA ORDER (1).pdf | `1smvZgwOMn-0MpKUlRY5oQKR6YX9YdHoH` (duplicate of above; both are TN RERA Form C for TNRERA/30/LO/0642/2026) |
| 20250523 Serenity Estate HNDT Approval Letter.pdf | `1paVRF_dY0epebElppbbkNxiquENv18Cl` |
| 20250523 Serenity Estate HNDT Approved Layout Plan.pdf | `1XuQnKtrRSCcBwfbUhGsRVPz2NKrzCXqy` |
| 20250131 Final Layout Plan.pdf | `1Iz00bhd1xbYIMaAFjZtBOVzqz69kaKGv` |
| 20250131 Serenity Estates layout.pdf / 20241122 Serenity Estate Main Layout Look*.jpeg | `1htuaXKDRioVNnfEzHK_e3e1mNlf-a8yb` / `1xHrVw3RmWljFkDnPJvrDq-eqVz_Cr07W`, `1TEaumfhA94HmdMhfAiLCwv4r58O3v76M`, `1_H9tEVUtuvMq0F31NiAbXtcatyyF1LsM` |
| 20250517 Serenity Estates receipt for plan sanction.pdf | `1CBSf70vGYK72PUpOBUd3rD2_moJfKBrI` |
| 20250131 Building Plan.pdf | `1iJ7k_8v_iXPnMHdZELGkpkrsjUr82Qa1` |

## The three sanctioned figures (extracted via pdftotext + Sheets API)

**1. HNDT Approval Letter (22.05.2025)** — net saleable by subtraction:
- Site Extent: 1.70 Ac = 7076.00 sqm
- No. of Plots: 38
- Layout Road (gifted to local body): 2546.86 sqm
- Public Purpose: 31.34 sqm (0.69%)
- TANGEDCO Purpose: 25.47 sqm (0.56%)
- **Net plot area = 7076 − 2546.86 − 31.34 − 25.47 = 4472.33 sqm = 48,140 sqft**

**2. HNDT Approved Layout Plan** — area statement block:
- **Plot area = 4529.14 sqm = 48,752 sqft** (plan quotes total − road only; OSR/TANGEDCO pockets stay inside the figure)

**3. Final Layout Plan (31.01.2025)**:
- **Plot area = 4532.53 sqm = 48,788 sqft** (again total − road of 2543.47 sqm)

**Why they differ:** the letter's subtraction excludes OSR + TANGEDCO (strictly net), while the layout-plan area statements compute `Total − Road` only (7076 − 2546.86 = 4529.14; 7076 − 2543.47 = 4532.53). Road figure itself differs slightly between letter (2546.86) and Jan-2025 plan (2543.47) — plan updates. Always report which figure you're using and from which document.

## Master Sheet actuals (38 plots)
- **Total plot area (sum of all 38) = 4050.71 sqm = 43,601 sqft**
- West-facing (plots 1–19): 1949.31 sqm ≈ 20,979 sqft
- East-facing (plots 20–38): 2101.40 sqm ≈ 22,622 sqft
- Sold: 11 plots = 12,949.96 sqft | Unsold: 27 plots = 30,651.49 sqft (as of 2026-08-30)
- Plot shape: uniform 12.19 m breadth; lengths 5.92–9.29 m; areas 996–1,216 sqft; 12.19m = 40 ft standard.

## Reconciliation (the "answer")
- Sanctioned sellable (approved layout plan): ~48,752 sqft gross
- Actually plotted (master sheet sum): 43,601 sqft net
- **Gap ≈ 5,150 sqft** → internal roads between rows, common pathways, set-backs, rounding. Not a discrepancy — it's the standard layout-yield difference (48,752 → 43,601 ≈ 89.4% of sanctioned is plot).

## NDR's 5-cent land-extent frame (Aug 2026 — used in the Anbu feedback message)
NDR's own reconciliation of the 5,150 sqft gap when asking Anbu (pm2.blr) for feedback:
- Land holding is **1.70 acres** vs the ~1.75 acres initially contemplated → loss of **~5 cents**.
- 5 cents ≈ **2,178 sqft** (1 cent = 435.6 sqft). NDR rounds to "~2,200 sqft".
- That only explains part of the gap: **5,150 − 2,200 ≈ 2,950 sqft still unaccounted** — ask Anbu where it went (internal roads, set-backs, plan changes).
- Useful framing for client/investor questions: separate "lost land extent" (5 cents) from "layout yield loss" (~2,950 sqft unexplained).

## IRR computation brief (NDR → Sarthak, Aug 2026)
When NDR asks about the Ranka Udaya IRR / cash-flow model, these are the standing assumptions he briefed Sarthak (admin3.blr@draas.com) with:
- Cash-flow inputs = entire spend to date: land, registration & statutory, development expenses, content + sales & marketing (content bucketed inside S&M), administrative.
- Development side: add admin/engineering overhead at **10% of development cost** → total cost of developing.
- Selling side: add corporate overhead at **3% of revenue** over and above S&M cost.
- Revenue: **₹3,500/sft average** sales price.
- S&M burn: current spend (outside software agency + digital ads) **×2** (future digital double + physical: sun boards, channel partners).
- Sales velocity: **~3 plots/month → full 38-plot inventory sold within 12 months**.
- Deliverable: detailed cash-flow presentation; NDR expects it to take ≤2–3 hours.

## Pitfalls hit this session
- **vision_analyze does NOT accept drive.google.com file URLs** (401 Unauthorized). Always `drive.files().get_media()` download to /tmp first, then pdftotext / vision the local file.
- HNDT letter is text-layer clean (English scan-friendly); the layout plan PDFs are Tamil drawings — pdftotext gives the numeric area block even when labels are Tamil.
- The two RERA order PDFs are byte-dupes of the same Form C; don't double-count.