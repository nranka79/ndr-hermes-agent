# Project sales / cost-incurred data sources + the Sales MIS deliverable (DRAAS)

Verified 2026-10-14 for the V Gro FinServ (Sudheer Desu) due-diligence request on
Ranka Udaya / Ranka Amber / Ranka Oasis.

## Where the per-project sales + cost-incurred figures live

**Canonical source — `DRA_Group_CashFlow_CostBreakup`** (id `1vhYoDI3un5tiabWQxHrYekt90lFmO0fbyQP3Gp80z4I`).
13 tabs; the layout repeats per project (`RankaUda_*`, `RankaAmb_*`, `RankaOas_*`, `RankaNor_*`):

- `Portfolio Summary` — one column per project: total units, developer-share units,
  **units sold to date**, units unsold, developer saleable area, target rate, total development
  cost, gross sales value, projected profit, margin, current status.
- `<Proj>_Asmp` — units, sold/unsold, avg area per unit, **achieved price (sold units)** vs
  **target rate (unsold)**, sales velocity, collection split (booking / construction / possession).
- `<Proj>_Cost` — cost heads with **both `Amount (₹ Cr.)` and `Amount Incurred to Date (₹ Cr.)`**
  → this is the "cost incurred as on date" answer. Also carries a SALES SUMMARY block
  (revenue from sold / unsold / total GSV / projected profit) and a means-of-finance block.
- `<Proj>_CF` — quarterly sales collections (modelled) + a KEY PROJECT METRICS footer
  (total revenue, total collections, cost, profit, margin).

Caveat: `<Proj>_CF`'s "projected profit" uses only forward sales, so it differs from
`<Proj>_Cost`'s profit (total GSV − cost). Both are internally consistent — quote the
**Cost-sheet** basis for GSV/profit, and say which basis you used.

**Newer single-project actuals — `Ranka Oasis — Integrated Cash Flow v4.0 (Project Cost and Revenue)`**
(id `1SubaopapjqfAVGbEoIYzaG-kftb50jkbga-XsDWuYU4`). Tabs `Assumptions` / `Dated_Cash_Flow` /
`12Qtr_Cash_Flow` / `Jiraaf P&L`. Carries **historical actuals** (dated vouchers, "spent to date")
and a **different basis** from the portfolio model: Oasis 6.20 ac / 108 villas / 2,94,784 sqft SBUA
/ ₹8,000–9,500 per sqft including the Jiraaf transaction, versus the portfolio model's
Phase I 127 developer villas / 3,81,000 sqft @ ₹8,050.

**ALWAYS surface the two bases instead of silently picking one.** Also flag stale statuses —
the portfolio model still says "Ranka Oasis — RERA pending" and "Ranka Amber — building plan
sanctioned" while both RERA registrations are now issued.

Other useful cross-checks: `DRA Realty Projects — Project Costing & IRR Model (Aug-2026)`
(`1beHSL-VPz20qQpeQwMToq4LvJWazo5y-Rq_Tykhgvfo`) for project identity/transaction details,
and `Ranka_Udaya_Payment_Tracker` — note this one is a **blank receipt template**
("Full Name as on Aadhaar", "ABCDE1234F"), not real sales data. Do not mistake it for a register.

## Sales MIS deliverable shape (what a lender expects)

One Google Sheet, three tabs — this shape went out cleanly:

1. **Sales MIS** — (A) portfolio snapshot with a Total column: entity, location, type, total units,
   developer-share units, units sold/pre-committed, units available, developer saleable area,
   achieved price, target price, revenue booked from sold units, value of unsold inventory,
   total GSV, % sold by units, total development cost, cost incurred to date, projected profit,
   margin, current status. (B) unit & value break-up per project (sold vs unsold vs pre-committed).
   (C) collections — **modelled** on the collection split, explicitly labelled, pointing at the
   collection-account bank statements for actuals.
2. **Cost Incurred to Date** — per project: cost head × (total cost, incurred to date), then a
   combined total across projects.
3. **Basis & Notes** — every source with its link and as-on date, then numbered flags: dual Oasis
   bases, modelled-vs-actual collections, updated statuses, pre-audit disclaimer.

Place the sheet in the **"Checklist" folder** (`1u8TwIv2vwSHg_oKjEm6wu1AEzniw1uZC`) beside
`DRA_Realty_Document_Checklist.xlsx`, so it can be shared with the counterparty the same way.
**Do not share externally without the user's explicit go-ahead.**

## Follow-up-request pattern (same counterparty, later list)

Sudheer D. sent a **second, different list** weeks after the first — MRTG deed by document number,
sales MIS, cost incurred — on top of the original 5 categories. So:

- Re-read the **whole thread** (`users().threads().get(userId="me", id=…, format="full")`), not just
  the newest message, and diff the new asks against the existing checklist.
- Drive-search each ask by **document number** as well as by name: `name contains '7049'` **and**
  `fullText contains '7049'`. Registered instruments are usually named
  `<yyyymmdd> <Doctype> <docno>-<year> …`, so the number is searchable even though nobody files
  a file called "MRTG".
- Report per item: **FOUND** (with link + which folder it sits in) / **NOT FOUND** /
  *partial — here is what exists instead*. Example of the third case: "Provisional Balance Sheet
  as of March 2026" was absent, but an FY2024-25 ITR statement of income / P&L / balance sheet +
  auditor report existed under a folder literally named "1.1 Latest Provisional Balance Sheet".
  Say that explicitly rather than answering a flat "no".
