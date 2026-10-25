# Ranka Oasis investor agreements — rates and what they exclude

Verified 2026-10-20, NDR's question: *"does the rate we have given them exclude clubhouse charges?"*

**Answer shape: identify WHICH document family governs, then answer per document. A single yes/no is wrong here — the four families disagree.**

## 1. Villa Option Track — the operative investor agreement

*"Loan cum Investment Agreement (Villa Option Track)"* — FINAL 10/12 Jun 2025, Doc `1j04-CiQhtN5nmMIg5Pv6bKk1SDpC3Lk3cmKT0HPeQbM`

- Rate: **Rs 3,300/sq ft West, Rs 3,500/sq ft East** of Target SBUA — Schedule C, "Agreed Base Rate for Principal Conversion". Sale Consideration = principal + accrued interest, valued at that rate.
- The defined term **"Exclusions"** expressly excludes (all payable additionally):
  - (a) GST, ~Rs 200/sq ft on Total Built-up Area
  - (b) advance maintenance deposit, corpus, sinking funds
  - (c) **Recurring Fees/charges for Clubhouse Usage**
  - (d) optional upgrades, incl. Clover Golf Club usage
  - (e) stamp duty, registration, legal fees
  - (f) Preferred Location Charges and corner-plot charges
- So: the rate is **net of clubhouse USAGE charges** — but **only recurring usage**. No one-time clubhouse membership / joining / capital contribution is provided for anywhere in the document, and the clubhouse building is not excluded.

## 2. Financial Return Track — do not quote for rate questions

*"Loan Agreement (Financial Return Track)"* 06 Jun 2025. Pure loan with an interest return; no villa allocation, no per-sq-ft rate. **Zero** mentions of clubhouse, amenities, corpus or maintenance.

## 3. Buyback Investor Agreement for Sale — 09 Aug 2025

Doc `1VAe9PFcZEjkFD3ETgppV0ynmClp67lTf4Uu3ppcvOBY`

- Base Sale Price **Rs 7,300 (West) / Rs 7,700 (East)** per sq ft, plus Rs 300 PLC, described as *"all inclusive including stamp duty & registration"*.
- **Silent on clubhouse entirely** — no exclusion clause, no mention. No contractual hook to bill clubhouse separately for any investor settled under this document.
- Contains the 2.5%/month early-completion rebate and the 12% p.a. delay-interest mechanism.

## 4. Current 2026 sale documents (post-conversion buyers)

e.g. Villa 119 Agreement for Sale + Construction Agreement, 31 Aug 2026.

- Construction Cost **Rs 64,64,600** + 5% composite GST (Rs 3,23,230), land consideration separate.
- Clubhouse appears only in **Schedule 'F' (Common Amenities)** — the allottee may "share and utilize" it; proportionate maintenance payable from handover. No separate clubhouse charge.

## Corroboration from the costing

- *"Saveganapalli Ranka Oasis Investor Costing Proposal"* sheet `11DLbtqJMyhdahI7VOiSsjxiduQicOc_PovZoN710nxk` (shortcut) — offer built from Land Cost Rs 3 Cr + **Infra Cost Rs 1.26 Cr** + construction Rs 2,750/sq ft + GST 495 → all-in 3,245; offered rate 3,500; buyback 7,450; IRR ~24%. **No clubhouse line anywhere.**
- \*"20250227 Ranka Oasis Investor Specs"\* deck — Clubhouse 12,000 sq ft, with **0.53 acre earmarked for clubhouse & amenities in Phase 1**.

**Conclusion:** the clubhouse capital cost sits inside the rate / infra cost. Only recurring usage is excluded. If NDR wants a one-time clubhouse membership or capital contribution, none of the four documents grants it — it needs a fresh clause.

## Method that worked (reuse for any "what does our agreement say about X" ask)

1. Enumerate the document set by Drive name **and** `fullText contains` (`STRR`, project name) — investor paper for one project is scattered across 4–5 families and dated versions.
2. Resolve `shortcut` files via `shortcutDetails.targetId` before exporting.
3. Export: Google Docs → `files().export(mimeType='text/plain')`; `.docx` → `files().get_media()` then unzip `word/document.xml`, strip tags, unescape.
4. **grep the DEFINED TERMS block first** — `"Exclusions"`, `"Sale Consideration"`, `"Final Sale Consideration"`. The answer almost always lives in the definitions, not the operative clause.
5. Cross-check the costing sheet for a line item: no line = the cost is inside the rate.
6. Report per-document, then the gap ("usage is excluded, membership is not"), then offer the draft clause. NDR acts on the gap, not the yes/no.
