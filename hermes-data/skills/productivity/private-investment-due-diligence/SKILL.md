---
name: private-investment-due-diligence
description: "Evaluate an investment ask for NDR as HNI — BOTH variants: private-company (venture debt / NCD / equity: extract pitch deck + financial model, verify registries and founders, devil's-advocate both-sides analysis) AND public-market (Indian IPO: Form 2A/DRHP/RHP, valuation vs listed peers, GMP/subscription sentiment). Deliver a self-contained HTML report in NDR's preferred section flow (briefing, methodology, founders, good, bad, argument for, argument against, structure & enforceability, verdict, checklist). Absorbed indian-ipo-evaluation (2026-08-16)."
version: 1.1.0
author: Hermes Agent
---

# Private Investment Due Diligence (Venture Debt / NCD / Equity / IPO)

UMBRELLA for evaluating an investment ask for NDR (or a client) as HNI — both the private-company variant (venture debt / NCD / equity with a pitch deck + financial model) AND the public-market variant (Indian IPO offer documents: Form 2A / DRHP / RHP). Produces an advisor-grade devil's-advocate analysis, not a summary. This skill absorbed the former `indian-ipo-evaluation` skill (merged 2026-08-16) — the IPO workflow below is that skill's content, kept as a labeled section; its worked example lives at `references/shankesh-jewellers-ipo-2026.md`.

## When to Use

- User shares a pitch deck + financial model and asks "should I give them ₹X Cr", "devil's advocate analysis", "would you invest as my financial advisor"
- Any private company debt/equity evaluation for an HNI (venture debt, NCD, seed/Series equity)
- User shares a Form 2A / DRHP / RHP / IPO note and asks whether to apply (public-market variant — see "Indian IPO Evaluation" section below)
- GMP / subscription / analyst-sentiment questions on a specific IPO
- The deliverables: pros AND cons, argument FOR the deal, argument AGAINST the deal, structure & enforceability options (Indian law), kill criteria

## Workflow

### Phase 1: Ingest both artifacts

**Excel model** (openpyxl — install into Hermes venv if missing):
```bash
uv pip install --python /opt/hermes/.venv/bin/python3 openpyxl pymupdf
```
Load with `data_only=True` (computed values). Iterate ALL sheets, print every non-None cell with coordinate. Look for: `#REF!`/`#ERROR!` cells (model quality signal), month headers stored as datetimes, and the **equity/funds utilisation table** — this is where arrears admissions live (statutory dues, vendor dues lines).

**Pitch deck PDF** (pymupdf first):
- Canva decks (metadata `creator: Canva`) often have a **jumbled/duplicated text layer** — `page.get_text()` returns scrambled chart labels. Render page to PNG at 300 DPI, then `vision_analyze` with "extract ALL numbers and labels exactly".
- Small stat tiles (MRR, fleet count) may NOT OCR even when cropped + 2-3× upscaled — flag them as "not machine-readable; verify with company" instead of guessing.

### Phase 2: Registry & corporate verification

Search: `<legal name> CIN zauba OR vakilsearch OR falconebiz OR instafinancials OR tracxn`. Extract:
- CIN, incorporation date, RoC, authorised vs **paid-up capital** (thin paid-up vs large debt = leverage red flag)
- Director list (DINs, appointment dates) — compare against deck's "Founders" block
- **Charges**: free aggregators often show "No charges" — this is a VERIFICATION FLAG, not proof. Unregistered charge is void against a liquidator (Companies Act 2013 s.77). Tell the user to check the MCA portal charge registry.
- GST state, registered email (personal Gmail on MCA = minor governance flag)

### Phase 3: Funding & cap-table history

- Tracxn/Crunchbase/F6S: total raised, round dates, investors, stage, cap table split (founder % vs others)
- Note: **Tracxn financial values are obfuscated/scrambled** — only use their revenue brackets and qualitative rows, never the raw digits
- Cross-check press announcements (₹ Cr claims) vs database totals — discrepancies are normal; report both

### Phase 4: Founder/team deep-dive

- LinkedIn each named founder; capture actual role dates. Reconcile vs deck claims:
  - "Ex-X" claims: check tenure length at the named employer (1 month vs 5 years both produce "Ex-X")
  - "Founder" labels: later-stage hires are often labelled founders on decks — cross-check company anniversary posts / welcome posts for join dates
  - **Hidden directors**: MCA director list often includes co-founders NOT on the deck — flag prominently
- Check for a CFO/finance lead in the narrative; absence of one for a debt-burdened company is a red flag

### Phase 5: Financial & unit-economics reconstruction

- Rebuild P&L from model totals: revenue, EBITDA, PAT, margins per year
- Debt stack: list lenders + O/S (from Borrowings sheet), compute blended interest (monthly interest / O/S ≈ p.a. rate)
- Equity utilisation table → % going to arrears vs growth. **If ≥20% of the raise clears existing dues, the ask is bridge money, not growth capital** — headline this
- Model vs actual vs deck reconciliation:
  - Model monthly ramp vs actuals-to-date (deck or news) — if actuals trail, H2 hockey-stick math is exposed: required monthly run-rate = (annual target − actual YTD) / months left
  - Internal consistency: two sheets showing different vehicle counts / revenue totals
  - Capex payback: margin per vehicle/month × fleet vs capex — thin margins = 3-5 yr payback, a capital treadmill
- Unit economics: revenue per vehicle/month, payout ratio to riders/workers, margin % kept — this is the business's structural truth regardless of deck branding

### Phase 6: Devil's advocate framing

Structure: **The Good** (real revenue, clients, tailwinds, skin in game, small ticket) → **The Bad** (arrears, thin margin, leverage, unregistered charges, model quality, deck hygiene, regulatory) → **Argument FOR** (bounded downside if secured, price for risk, cross-default leverage from institutional lenders, small time-boxed ask) → **Argument AGAINST** (worst point in capital cycle, asymmetric risk/capped return, statutory dues as disqualifier, enforcement reality, round may not close). Every point must cite a number or source — no vibes.

### Phase 7: Structure & enforceability (Indian debt) — if user proceeds

- Instrument: secured NCD (single-holder) or secured loan agreement; creates "financial debt" under IBC (CIRP trigger for ₹1 Cr+ claim)
- Security: first charge on specific unencumbered assets (vehicle VIN list + RC hypothecation at RTO) or second charge with inter-creditor agreement; avoid generic "all assets"
- **Form CHG-1 filed within 30 days of disbursement** — insist on acknowledgement
- Personal guarantees from ALL directors (notarized, with PAN/asset schedule); corporate guarantee if holding entity exists
- Coupon 18-24% (match their existing blended cost), quarterly interest (early default visibility), 24-36 mo tenor
- Escrow: 15-20% of collections auto-swept to lender
- Conditions precedent: equity round closed, statutory dues current, charge clean-up, audited AFS, no existing defaults
- Covenants: no further debt, quarterly MIS, cross-default
- Tax: TDS u/s 194A on interest by the company
- End with a clear **conditional verdict** ("lean NO as offered; YES in principle only if...") + DD checklist + kill criteria (any one = walk)

### Phase 8: HTML report (NDR's format) & delivery

NDR's specified flow, in this exact order:
1. Executive Briefing (verdict-at-a-glance box + company cards + the single most important sentence callout)
2. Methodology & Sources
3. Business model & unit economics
4. Financial analysis (P&L table, debt stack, equity utilisation, model-quality flags)
5. Founder & team profiles
6. The Good
7. The Bad
8. Argument FOR
9. Argument AGAINST
10. Structure & Enforceability
11. Conditional verdict + DD checklist + kill criteria

Style: self-contained HTML with inline CSS (no external deps), dark navy header (#16213e/#0f3460), verdict box with colour chips, summary cards grid, tables with navy headers, green-left-border "good" boxes / red-left-border "bad" boxes, callout boxes for key insights, responsive via @media. Numbers in ₹ Cr with tabular alignment.

Verify render: chrome-headless-shell screenshot → vision_analyze (confirms no broken layout before delivery).

**Drive organization (NDR convention, Aug 2026):** for investment pitches, create/use `Personal → Investment Opportunities → <Company Name> (<ask>)` under google-draas (EV91 folder: `1uAd1YZDA3l6KBHFgK5bmUCHJCFUdhIMx`). Upload ALL source documents (pitch decks, models, actuals, MIS) with descriptive names PLUS the versioned analysis HTML (`YYYYMMDD_<Company>_<ask>_DD_NDR_vN.html`). TMP (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`) is for un-filed incoming docs, not the final deal file.

**Versioning:** new documents almost always arrive after the first report (actuals, MIS, full deck) — produce a NEW version each wave (v1 deck-only → v2 actuals → v3 full deck). The verdict frequently flips or hardens (EV91: model +₹0.88 Cr PAT → actuals showed −₹7.06 Cr loss → deck showed ₹200 Cr valuation claim). Re-upload each version to the same folder; send latest link + MEDIA.

Then deliver via MEDIA:<local path> + Drive link + concise chat summary (verdict first, key numbers, structure offer).

## Indian IPO Evaluation (public-market variant — absorbed from indian-ipo-evaluation, 2026-08-16)

Class-level workflow when NDR (or a client) uploads an IPO offer document — Form 2A (abridged prospectus / memorandum of salient features of RHP), DRHP, or RHP PDF — and asks "should I invest?", "research everything", "pros/cons", "investment thesis / don't-invest thesis", or "what valuation is it aiming for". Worked example: `references/shankesh-jewellers-ipo-2026.md` (full Form 2A → research → thesis, including the aggregator URLs that returned data and the ones that blocked).

### Phase 1: Ingest the offer document

Extract from Form 2A (or RHP summary): CIN, incorporation year, registered office, activity code (NIC 36910 = jewellery manufacture, etc.); promoters and MD; compliance officer; website; offer structure (fresh issue share count, OFS share count, face value, BRLMs). **Share-count trap:** the Form 2A share figure is often the FRESH-ISSUE component only. Total offer = fresh shares + OFS shares. Sanity-check: total issue ₹ at upper band = (fresh + OFS) × upper price.

### Phase 2: Research ladder (keyless, works from VPS datacenter IP)

Order matters; escalate only on failure:
1. **Google News RSS** (discovery): `https://news.google.com/rss/search?q=<Company>+IPO&hl=en-IN&gl=IN&ceid=IN:en` — headlines + source + pubDate for timeline reconstruction (DRHP filing, price band, open/close, GMP coverage). **Do NOT fetch the `news.google.com/rss/articles/...` redirect links — they return HTTP 400.**
2. **IPO aggregator sites — direct fetch works** (urllib/curl with a desktop UA): `ipowatch.in/<slug>-ipo/` (issue details, financial table, valuations EPS/PE/RoNW/NAV/ROCE/EBITDA%/D/E, peer comparison, lot sizes, dates), `ipowatch.in/<slug>-ipo-gmp/` (daily GMP table — authoritative keyless GMP source), `ipocentral.in/<slug>-ipo/` (financials + margins, use of proceeds, pre/post-issue EPS and PE, peer table, GMP trend, anchor dates), `thefinancialworld.com` (MD quotes, customer counts, revenue + growth %, BRLMs), company website (business model, client testimonials — B2B vs retail is the big tell).
3. **x_search (X/Twitter)** — "<Company> IPO" with a date range: GMP chatter, analyst subscribe/avoid calls, deep-dive threads, comparisons to concurrent peer IPOs.
4. **Mainstream articles** — ET topic pages (`economictimes.indiatimes.com/topic/<Company>`) can be fetched; BusinessLine/Moneycontrol/BusinessToday/IndianRetailer are typically JS-walled or 404 from the VPS. Max 2 attempts per path.

### Phase 3: Financial extraction

Pull FY-3 / FY-2 / FY-1 (and any stub): revenue, EBITDA margin, PAT, PAT margin, EPS, NAV, RoNW, ROCE, D/E, current ratio, borrowings. Cross-checks: profit jump via margin expansion + deleveraging may not be durable; negative operating cash flow with inventory/receivables build-up = working-capital-intensive; elevated product returns (~7% of revenue) = pipeline friction; customer + supplier + geographic concentration.

### Phase 4: Valuation being aimed for

- Post-issue market cap at upper band = (pre-issue shares + fresh shares) × upper price. **OFS adds no new shares** — promoter selling; post-issue share count excludes OFS.
- P/E post-issue = mcap / FY-latest PAT. Compare with the RHP's own listed-peer table. "Cheap vs peers" must be read with peer-quality context.
- Management growth targets: implied CAGR = (target/base)^(1/years) − 1. Flag if aggressive (e.g. 45% CAGR).

### Phase 5: Sentiment

GMP from IPO Watch / IPO Central daily tables — single-digit GMP (≈3–9%) = modest listing-pop expectation, NOT a pop trade. Report as sentiment, never as valuation. Anchor book date and names, subscription day-wise once open, retail/QIB/NII quota split, concurrent IPO calendar.

### Phase 6: Devil's-advocate framing (mirror the private variant)

1. What the company IS (one crisp paragraph, incl. B2B vs retail — the single biggest business-model tell)
2. IPO mechanics (price band, fresh/OFS split, lots, dates, quotas, BRLMs, anchor)
3. Use of proceeds (debt repayment ₹X, working capital ₹Y, GCP — a big deleveraging ask is an earnings catalyst)
4. Financials table (numbers + margin trajectory)
5. Valuation aimed for (post-issue mcap, P/E vs peer table, implied CAGR of any target)
6. Grey market / sentiment
7. The case FOR (every point cites a number or source)
8. The case AGAINST (every point cites a number or source)
9. Bottom line — a clear conditional verdict plus what would flip it.

### IPO pitfalls

- Google News RSS redirect links 400 when fetched — never resolve them; go straight to aggregators.
- Form 2A share count = fresh issue only — total = fresh + OFS; recompute ₹ total at both band ends.
- OFS = promoter selling — check promoter acquisition cost in the RHP (cost < ₹1/share vs ₹90 band is a signal to weigh).
- Mainboard vs SME matters — SME IPOs have lighter scrutiny; state which board.
- GMP is unofficial and volatile — date-stamp it and label as sentiment.
- Delegated subagents with `web` toolset can return empty results — the ladder is keyless and parent-side; run it directly if delegation fails.
- Blocked paths from the VPS (max 2 retries): Bing/DDG/Mojeek HTML search, Google web search (302), Moneycontrol (login/404 walls), BSE/NSE API endpoints, SEBI filing pages.
- Aggregator numbers = "as reported" — tell the user to verify final financials/risk factors in the RHP at BSE/NSE/SEBI (full RHP PDF is often not fetchable from the VPS; give exact portal locations).
- Peer context: name-matched "jeweller" peers may be different business models (B2B manufacturer vs branded retail vs exporter) — flag model mismatch.

## Pitfalls

- **Deck claims ≠ registry reality**: revenue, fleet size, founder status — each must be traced to an independent source. Inconsistent fleet numbers across their own materials (website vs deck vs model) is a diligence tell; call it out explicitly
- **The equity utilisation table is the most informative page of any fundraise model**: statutory dues, vendor arrears, adhoc obligations are admissions. Quote them verbatim in the report
- **Free MCA aggregators lag** — "no charges" can mean stale data; frame as "verify on MCA portal" not "no charges exist"
- **Canva deck OCR**: chart value labels often unrecoverable even with crops — mark unverifiable rather than guessing
- **Don't compute fake precision**: Tracxn obfuscated digits, deck-only numbers, unaudited model figures — label every figure (deck claim / model / audited / third-party)
- **Hockey-stick detection**: always compare model monthly ramp against actuals-to-date; compute the implied H2 monthly rate and state it in plain terms (e.g. "H2 must run at 2× today's rate")
- **Recovery math for the investor**: interest at 20% on ₹2 Cr = ₹40 L/yr — always compare debt service against the company's projected PAT; if it exceeds ~30% of PAT, the cushion is gone
- **Three revenue versions, one year**: the pitch model, the management MIS, and the deck often disagree on the SAME period (EV91 FY26-27: ₹144.6 Cr model / ₹123.1 Cr MIS / ₹180 Cr deck). Put the discrepancy table in the report; the internal MIS is the most truthful document — "investor-facing docs overstate, internal docs understate"
- **Contradictory operational claims**: deck "96% utilization" vs model "85% uptime" is mutually exclusive — call it out instead of picking one
- **Valuation claims need evidence**: "raising ₹20 Cr at ₹200 Cr" with no signed term sheet / named lead investor is a marketing number (8× in 20 months for a loss-making company). Add "valuation not evidenced" to the kill criteria
- **Revenue real ≠ profitable**: a company can have fully verified revenue AND be deeply loss-making (EV91: ₹65.13 Cr actual revenue, −₹7.06 Cr PAT). Always verify both separately — the deck's top line can be true while its implied profitability is fiction
- **Hand-loan book = clearest distress signal**: many small lenders at 24–33%+ with twice-monthly EMIs means banks won't lend to them; blended hand-loan cost is the benchmark your coupon must undercut
- **If the ask ≈ outstanding statutory dues** (GST+TDS), the debt is refinancing the taxman — quote the ₹X Cr ask vs the ₹Y Cr statutory line side by side
- **Debt growth between two company documents** (₹13.36 Cr Feb → ₹24.14 Cr Aug = +₹10.8 Cr in 6 months) with new lenders appearing = borrowing faster than growing

## References

- `references/ev91-voice-case.md` — Worked example: EV91 Technologies (VOICE), ₹2 Cr debt ask, Aug 2026. Shows the full data trail (registry, funding, founders, model red flags) and the exact red-flag pattern that drives the verdict.
- `references/shankesh-jewellers-ipo-2026.md` — Worked example (public-market variant): full Form 2A → research → thesis for the Shankesh Jewellers IPO, including the exact aggregator URLs that returned data and the ones that blocked.

## Related Skills

- `business-dossier` — intelligence gathering / briefing notes for legal & property matters (overlaps in multi-source discovery; that skill is Drive/Gmail-centric, this one is investment-analysis-centric)
- `ocr-and-documents` — PDF/Excel extraction mechanics
