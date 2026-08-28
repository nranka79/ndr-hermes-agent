---
name: real-estate-company-valuation-ipo
description: "IPO readiness, valuation analysis, and comparable-company benchmarking for private real estate companies — SEBI criteria, peer multiples, and listing valuation ranges."
version: 1.0.0
author: Hermes (DRAAS)
---

# Real Estate Company Valuation & IPO Analysis

Analyze a private real estate developer for potential IPO / listing — financial extraction, comparable peer multiples, SEBI eligibility, and valuation synthesis.

## Trigger

Use when Nishant asks about:
- "what can this company list at?"
- "IPO valuation / listing analysis / what multiple"
- "comparable companies / peer analysis / market cap"
- "SEBI criteria / IPO eligibility / listing requirements"
- "what's this stake worth if listed"
- Any request to value a private real estate company against listed peers

## Workflow

### 1. Extract Financial Data from Source Documents

Pull financials from available PDFs using `pdftotext`:

```bash
pdftotext "/path/to/financial.pdf" -
```

Key data points to extract:
- **5-year revenue trajectory** (look for CAGR)
- **PAT / PAT margin** (trailing and trend)
- **Net Worth** (share capital + reserves)
- **Total Borrowings & D/E ratio**
- **Total Assets**
- **Shareholding pattern** (promoter vs minority)
- **Future projections** (revenue, EBITDA, cash flow by year)

For scanned documents, use `pdftoppm` + `vision_analyze` on first page to identify document type.

### 2. Identify Comparable Listed Companies

Target companies by geography and size tier:

**Large-cap (₹50K Cr+):** DLF, Macrotech (Lodha), Prestige Estates, Oberoi Realty, Godrej Properties
**Mid-cap (₹5K-50K Cr):** Brigade, Sobha, Phoenix Mills, Anant Raj, Signature Global, Puravankara
**Small-cap (under ₹5K Cr):** Keystone Realtors, Shriram Properties, Kolte-Patil

**Key Chennai comparator:** Casagrand Premier Builder (SEBI approval June 2026 for ₹1,220 Cr IPO)

Sources for multiples data:
- **screener.in** (P/E, market cap, quarterly sales/profit for Nifty Realty constituents)
- **multiples.vc** (EV/Revenue, EV/EBITDA benchmarks — median Indian real estate: 6.7x EV/Revenue, 16.2x EV/EBITDA)
- **stockanalysis.com** / **simplywall.st** (individual company statistics)
- **ipoplatform.com** (recent IPO PE ratios by sector)

### 3. Gather Key Multiples Per Company

For each comparable, collect:
- Market Cap (₹ Cr)
- P/E ratio (trailing)
- EV/EBITDA (where available)
- EV/Revenue (where available)
- Revenue scale and PAT margin
- Geographic focus and segment (luxury vs affordable vs mid-income)

### 4. Assess SEBI Main Board IPO Eligibility (ICDR Reg 6.1)

Checklist:

| Requirement | Threshold |
|---|---|
| Net Tangible Assets | ≥ ₹3 Cr each of preceding 3 years |
| Avg Pre-tax Operating Profit | ≥ ₹15 Cr (3 of last 5 years) |
| Net Worth | ≥ ₹1 Cr each of preceding 3 years |
| Track Record | ≥ 3 years existence |
| Min Issue Size | ₹10 Cr |
| Min Allottees | 1,000 |
| Promoter Contribution | Min 20% post-issue capital |

**Real estate-specific disclosure norms** (SEBI 2007 circular):
- Land bank at CURRENT market value only (no projected valuations)
- Ownership status of every land parcel with purchase agreements
- RERA compliance for all projects >500 sqm or >8 units
- 70% buyer collections in dedicated escrow accounts
- Credit rating from SEBI-registered agency

### 5. Apply Multiple Valuation Approaches

Use ALL of these and present a range:

**A. P/E Multiple**
- Conservative: 15x (small-cap peer like Shriram Properties)
- Moderate: 20-25x (mid-cap like Brigade/Oberoi)
- Optimistic: 28-35x (growth premium if strong pipeline story)
- Apply to latest full-year PAT

**B. EV/EBITDA**
- Conservative: 10x
- Moderate: 14x (near median of 16.2x, adjusted for size)
- Optimistic: 18x
- Formula: EV - Total Debt + Cash/Investments = Equity Value

**C. EV/Revenue**
- Conservative: 1.0x
- Moderate: 2.0x
- Optimistic: 3.0x
- Note: Leverage heavily affects this approach

**D. DCF (if available from valuation report)**
- Enterprise Value from DCF
- Add: Investments, tax assets, cash
- Less: Total debt
- = Equity value (controlling basis)

### 6. Synthesize and Present

Structure the final report:

1. **Company Snapshot** — revenue, PAT, net worth, D/E, growth rate
2. **Future Projections** — if available from management/valuer
3. **Comparable Multiples Table** — peer companies with P/E, EV/EBITDA, EV/Revenue
4. **Valuation Range** — across all approaches, with clear conservative/moderate/optimistic columns
5. **IPO Feasibility** — SEBI eligibility checklist with ✅/⚠️/❌ per item
6. **Key Risks** — size, leverage, geographic concentration, audit status, RERA compliance
7. **Recommended Timeline** — short/medium/long-term actions before filing DRHP
8. **Value Unlock Commentary** — private vs listed valuation gap (DLOC/DLOM removal)

### 7. Reference Data

See `references/comparable-company-multiples.md` for an expandable database of listed real estate peer multiples to reuse across analyses.

## Pitfalls

- **Provisional vs audited financials**: SEBI requires audited statements. Label any provisional data clearly.
- **Share count consistency**: Verify if share count changed during the year before calculating per-share metrics.
- **EBITDA estimation**: For real estate companies, EBITDA = PAT + Tax + Interest + Depreciation. Don't confuse with operating cash flow.
- **Single-city concentration**: Chennai-only developers must address geographic risk explicitly (see Casagrand DRHP — 60%+ in one city flagged as risk).
- **Multiple DRHP attempts are normal**: Casagrand filed 3 DRHPs (Jul'22, Sep'24, Dec'25) before SEBI approval in Jun'26. Don't over-interpret a returned DRHP as rejection.
- **Rs. 10 face value shares**: Most real estate company IPOs have ₹10 face value — use this for per-share comparisons.
- **D/E ratio matters to SEBI**: High leverage is not disqualifying (most developers carry 3-4x debt), but the IPO use-of-proceeds should address debt reduction clearly.
