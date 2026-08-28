# DPR Financial Tables — worked per-project numbers (24-Aug-2026)

Canonical financing/cash-flow/balance-sheet tables inserted into DPR sections 6.2 / 7.2 / 7.4 across all four Ranka DPRs. Referenced from `real-estate-financial-modeling` §4 (DRA capital policy).

## User-mandated financing rule (applies to every DPR 6.2 table)

Where project land is OWNED by the developer → land value = developer equity; add **25% of total development cost as capital equity**; the **balance (75%) as debt** from investors/institutions. JDA projects (land NOT owned) have NO land equity — just 25% capital equity / 75% debt.

## User-confirmed model parameters (Prakash's answers, 24-Aug-2026)

| Parameter | Value |
|---|---|
| Debt interest | 11% p.a. |
| Debt tenor | 72 months |
| Sales velocity (booking targets) | 30% + 10% + 10% + 10% + 15% + 15% over 24 months + 6 months; 10% retention at handover |
| Project start date | Assumed Q2 (user: "Assumed Q2") |
| Amber goodwill/IFRSD | ALREADY PAID by developer → treat as EQUITY (₹1 Cr goodwill + ₹1 Cr IFRSD) |
| Amb NDR internal funding | ~₹2 Cr for Amber (NOT ₹18.19 Cr — earlier ledger figure was wrong) |
| Udaya rate | 38 plots @ ₹4,000/sq.ft (→ ₹18.58 Cr sales = 46,451 × 4,000) |

## Worked financing structure per project (₹ Cr)

| Project | Land eq | Cap eq (25%) | Debt (75%) | Total |
|---|---|---|---|---|
| **Amber** (JDA 50:50, land not owned) | 0.00 | 4.00 (paid-in: goodwill 1 + IFRSD 1 + NDR ~2) | 6.70 | 10.70 |
| **Udaya** (owned, Sale Deed 20527/2024-25) | 6.10 (land value) | 0.85 | 2.55 | 9.50 |
| **Oasis Phase 1** (6.58 ac owned + 0.95 JDA) | 37.51 (6.58 ac @ ₹5.70 Cr/ac) | 46.45 | 139.35 | 223.31 |
| **NorthStar** (JDA 67:33, land not owned) | 0.00 | 8.85 | 26.55 | 35.40 |

Bases: Amber dev cost 10.7 (sales 18.42); Udaya dev cost 3.4 (sales 18.58); Oasis Phase 1 dev cost excl land 185.80 (sales 345.26); NorthStar dev cost 35.4 (sales 65.0). All from the Investor Portfolio spreadsheet `1wDKS0SxtY0EF_-JUe2BfXzLSSwh4J5fo4y0sI_brFfw` tabs.

## Oasis MUST use Phase 1 (approved) basis

**User correction (24-Aug-2026): "One Change in Oasis — Currently Phase 1 (approved) is about 7.53 Acres, so the project cost, balance sheet projections and cashflow and other financials should be calculated based on this. Check the investor spreadsheet for details and saleable area details."**

- Phase 1 approved layout = **7.53 ac** = DRA-owned 6.58 ac + JDA 0.95 ac (Ramesh Reddy). Do NOT model on the full 8.86 ac owned or 10.31 ac total (Phase I + II).
- Investor sheet Phase I rows (authoritative): owned lands saleable BUA 343,090 sq.ft (113 villas); JDA dev share 40,534 sq.ft (14 villas); landowner share 9,000 sq.ft (3 villas); dev total 383,624 sq.ft.
- Phase 1 sales ₹345.26 Cr (own 308.78 + JDA dev 36.48); land value @ ₹5.70 Cr/ac; consolidated Phase 1 dev cost ₹213.88 Cr + infra ₹9.43 Cr = ₹223.31 Cr incl land; profit ₹121.96 Cr.
- The 8.86-ac figure (from the earlier 8.86-ac land-ownership summary) is NOT the modeling basis — Phase 1 is.

## Amber saleable area — Customer Area Statement is authoritative

User: "AMBER - TOTAL SALEABLE AREA - AS PER CUSTOMER AREA STATEMENT ADD THAT DETAILS". CAS (Annexure-A, 17-Aug-2026, Drive `1yZEj1HhGOujhdflwtgtVGYn_TLjycldQ`, image-only PDF — render PNG → vision_analyze OCR):
- **Total Saleable (SSA/sanctioned) = 27,543.25 sq.ft**; SBUA 31,853; Carpet 23,439; Built-up (walls) 25,563; loading 4,152; plot 14,000 sq.ft; UDS 0.4395; 20 units = 10 LO + 10 DEV (LO 101–105, 401–405; DEV 201–205, 301–305).
- Note it differs from the portfolio sheet's 28,900 FAR / 30,700 built-up — use the CAS number when the user asks for "saleable area as per customer area statement".

## Docs API table-insert mechanics (worked through many failed runs)

- **Insert text at `cell['startIndex'] + 1`** — the cell's paragraph starts after the cell marker, not at `startIndex`.
- **Batch index staleness**: recompute shifted positions explicitly after each insert; never reuse stale indices across a batch.
- **Row styling**: text-background (highlight) styling is more reliable than cell-background for matching the doc's branded table style (charcoal headers, 9.5 pt).
- Column properties need `fields` set; drop explicit column widths (API needs `widthType`; auto-size matches existing tables) or set `widthType`.
- Skip empty-string cells; guard style ranges.
- **Idempotent inserts**: check for existing heading signature before re-inserting; retries created triplicated financing tables.
- **Surplus plug** on the balance sheet is REQUIRED for the BS to balance (cumulative income − spend − interest).
- **Cash-flow rows quarterly, NOT cumulative** (user's first version was cumulative; corrected to quarterly).
- **Purge discipline critical**: cleanup predicates must ONLY match Fin/Quarter/Year-end header signatures — NEVER a generic 'Particulars' table start. 'Particulars' is the signature of the pre-existing Section 1.3 ITR tables; a broad purge deleted them from all 4 docs (had to restore from dumps).
- Heading glue: when inserting a heading before an existing section header, append a trailing newline or the new heading fuses with the next header; splitting afterwards risks consuming the following heading (7.3 Profitability headings got eaten in Udaya/Oasis — restore with proper heading style).

## DPR → editable slide decks (when user asks "convert DPRs to slides")

Google Slides API is DISABLED on the GCP project (403 SERVICE_DISABLED) — do NOT start from `slides.presentations().create()`.
Pivot that works: build branded .pptx with python-pptx (10-slide pattern: cover / 1 Exec Summary table / 2 Overview / 2.1A Land-JDA / 6.2 Means of Finance / 7.2 Quarterly Cash Flow / 7.4 Balance Sheet / 7.3 Profitability / 8 Project Images / 9 Development Status as-on-date), then upload with `files().create({mimeType: 'application/vnd.google-apps.presentation'})` + MediaFileUpload — Drive auto-converts to native Google Slides (editable in-browser). Verify by Drive `files().export` to PDF → pymupdf page count + text spot-check.
Install python-pptx into the Hermes venv (no pip module): `uv pip install --python /opt/hermes/.venv/bin/python python-pptx`.

## As-on-date development status images

- 24-Aug-2026 site photos live in Drive folder `Actual Site Photos` (11 WhatsApp images) — Udaya's plotted layout (roads, boundary wall, plot markers). Posters folder (6 PNGs) also all Udaya (HNTDA approved, 38 plots, ₹48L onwards).
- **Verify image ownership before embedding into per-project decks** — folder context ≠ project mapping. Amber site photos from `/tmp/amber_photos` (Site photos 3–7) belong to Amber; Oasis/NorthStar had no as-on-date photos → placeholder note on the deck slide is correct, ask user for photos.