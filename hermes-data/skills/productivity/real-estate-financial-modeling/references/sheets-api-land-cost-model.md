# Google Sheets API — Editable Land-Cost Realisation Model (Palya 2A6G worked example)

Trigger: user shares a Google Sheets link and asks to "redo this financial model… arrive at the actual land cost after considering all project cost… as a land owner what is the Land cost realisation we can arrive, after profit of 30%. Make an editable model."

Deliverable pattern: NEW editable Google Sheet (V2), original preserved, shared with the requesting user (psingh@draas.com in this case) as writer. Verified live-formula model — user tweaks yellow cells, everything recalculates.

## Workflow

1. **Dump the existing sheet with formulas, not values** — `values().get(valueRenderOption='FORMULA')` on every sheet. Note discrepancies between note-text and values (see pitfalls).
2. **Search Drive for sibling models** (`name contains 'Palya'` etc.) — the original IRR calculator holds the intended assumptions and JDA structure (LO share 0.4, dev cost 3750/4750, sale 10000/12000). Cross-check which input set the user's current sheet uses.
3. **Replicate the math in Python FIRST** (skill Section 2). These are the numbers you report.
4. **Create new spreadsheet** via `spreadsheets().create()`, then `values().update(..., valueInputOption='USER_ENTERED')`.
5. **Format in a separate batchUpdate pass** with the REAL sheetId (see pitfalls).
6. **Share** via `drive.permissions().create(type=user, role=writer, emailAddress=<requester>)`.
7. **Verify**: `values().get(valueRenderOption='FORMATTED_VALUE')` read-back of key rows must match Python replication exactly. Deliver link in a code block (Prakash's Telegram breaks URLs) + tell him to search Drive by filename as fallback.

## Row layout (section map)

- A. INPUTS (yellow, editable): Land Area acres (2.15 = 2A6G → 93,654 sqft), FAR (1.05), LO BUA Share (0 = cash land-cost model; 0.40 = 60:40 JDA), Sale Price psft (10,000), GST pass-thru psft (=5%×sale), Dev Cost psft (4,250), Marketing % of Dev Revenue (5%), JD/Reg/Legal fixed (₹1.5 Cr), Sanction psft (150), CLU psft (100), Refundable Deposit (₹1.0 Cr), Non-Refundable/Goodwill (₹1.0 Cr), Deposits Recoverable from LO psft (500), GST Rate from LO (18%), Mkt Fee % from LO (5%), **TARGET PROFIT % on Cost (0.30)**.
- B. DERIVED: Total SBUA = land_sqft×FAR; Dev SBUA = total×(1−LO share); LO SBUA = total − dev.
- C. DEV REVENUE: Sales (dev_sbua×sale), −GST pass-thru, +LO mkt commission recovery (lo_mkt×sale×lo_sbua), +LO deposit recovery (lo_dep×lo_sbua), +Refundable deposit recovery, +GST recoverable from LO (lo_gst×lo_sbua×(devcost+sanction)).
- Costs: JD Agreement (jd_fixed + sanction×total + clu×total + refundable + nonrefundable), Construction (devcost×total), Marketing (mkt×sales), **LAND COST = MAX(bs_land,0)** (auto-link), total.
- PROFIT: revenue − cost; % on cost; % on revenue.
- D. BACK-SOLVE: Max Allowable Total Cost = revenue/(1+target); Fixed Costs (excl land); **MAX ALLOWABLE LAND COST = MAX(maxcost−fixed, 0)**; per acre (÷ acres); psft of land.
- E. LO REALISATION: land cost + non-refundable goodwill + refundable deposit = total; per acre; psft.
- F. SCENARIOS 25/30/35%: max land cost Cr, per acre Cr/ac, LO realisation/ac.
- G. SENSITIVITY: land cost 0–25 Cr in 1 Cr steps → land psft, total cost, profit, % on cost, % on rev; final row = max-allowable row with `MAX(bs_land,0)`.

## Worked numbers (Palya 2A6G, current inputs)

- Land 93,654 sqft (2.15 ac), FAR 1.05 → SBUA 98,337 sqft (~45 units @2,200)
- Dev revenue ₹98.34 Cr; −GST ₹4.92 Cr → net ₹94.42 Cr
- Fixed costs: JD ₹5.96 + Constr ₹41.79 + Mkt ₹4.92 = ₹52.67 Cr
- Max total cost @30% = ₹94.42/1.30 = ₹72.63 Cr → **MAX LAND = ₹19.96 Cr = ₹9.28 Cr/acre = ₹2,132 psft**
- LO total realisation incl ₹1+₹1 Cr deposits = ₹21.96 Cr (₹10.22 Cr/ac)
- Scenarios: 25% → ₹22.87 Cr (₹10.64/ac); 30% → ₹19.96 (₹9.28); 35% → ₹17.27 (₹8.03)
- With deposits at 2.5+2.5 Cr (per the original note): max land drops to ₹16.96 Cr (₹7.89/ac)

## Pitfalls (all hit on this build)

1. **Hardcoded row numbers → #REF! everywhere.** The planned layout (row 31 = sales, etc.) shifts when a blank spacer row is inserted/omitted. Fix: build `rows[]` with `KEY["label"] = len(rows)` after each append and interpolate `B{KEY[...]}` into every formula. Then formulas always point at actual cells.
2. **`sheetId: 0` in batchUpdate → `Invalid requests[0].repeatCell: No grid with id: 0`.** Must fetch `spreadsheets().get()` and use the real `sheets[0].properties.sheetId` (e.g. 1088711304).
3. **Label starting with `+` is parsed as a formula → #ERROR!** in that cell (e.g. "+ Non-Refundable Goodwill"). Rename to "Non-Refundable Goodwill (add)".
4. **Note-vs-value drift**: original sheet notes said deposits "= 2.50 Cr" but cells held ₹1.0 Cr. Keep current values, flag to user, show sensitivity impact. Never silently "fix" (confirm-before-actions).
5. **Reading FORMATTED_VALUE shows rounded/percent-formatted strings** — for exact cross-check read with `valueRenderOption='FORMULA'` to confirm formula strings and `'UNFORMATTED_VALUE'` for raw numbers.

## Deliverable summary format (to user)

Lead with the answer: max land cost @ target profit (Cr, Cr/acre, psft), total LO realisation incl deposits, then fixed-cost breakdown, scenario table (25/30/35%), editable-list, flags (deposit discrepancy, LO share 0 vs 0.40), and the link in a code block.
