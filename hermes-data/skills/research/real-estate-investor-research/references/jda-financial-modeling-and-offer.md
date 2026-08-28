# JDA Financial Modeling & Landowner Offer Recommendation

Session: Chikkadunnasandra (18 Acres) & Thyalagere (10 Acres) — Jul 2026

## Overview

When a user asks "what should we offer the landowner?" for a JDA deal, the workflow is:

1. Collect inputs → 2. Compute financials → 3. Determine JDA split → 4. Sensitivity analysis → 5. Build presentation

## Input Collection Checklist

| Input | Example | Source |
|-------|---------|--------|
| Land area (acres) | 18 Acres | Kelsa / user |
| Location | Sarjapur Road | Kelsa / user |
| Development type | Villa / Apartments / Layout | User |
| Deal type | JDA or Outright | User |
| FAR / FSI | 0.85 | User / plan sanction |
| Expected sale price (/sft) | ₹12,000–15,000 | User |
| Construction cost (/sft) | ₹3,500 | User |
| Infrastructure cost (/sft) | ₹600 (if applicable) | User |
| CLU/consultants cost (/sft) | ₹500 (if applicable) | User |
| Marketing (% of revenue) | 3% | User |
| Soft costs (% of revenue) | 5% (if not itemised) | User |
| Land value reference (/acre) | ₹6–10 Cr | User |
| Upfront deposit (% of land) | 10% | User |
| Target ROC (%) | 36% | User |

## Computation Logic

```python
land_sqft = land_acres * 43560
saleable = land_sqft * far
revenue = saleable * rate_psft

# Development costs
if infrastructure specified:
    total_cost = const_cost + infra_cost + soft_cost(5% of rev)
else:
    total_cost = const_cost + clu_cost + mktg_cost(3% of rev)

# Target economics
target_profit = total_cost * target_roc
target_dev_rev = total_cost + target_profit
dev_share_pct = target_dev_rev / revenue * 100
land_share_pct = 100 - dev_share_pct

# Terms
deposit = land_acres * land_value_per_acre * 0.10  # 10%
dev_rev = revenue * dev_share_pct / 100
dev_profit = dev_rev - total_cost
roc = dev_profit / total_cost * 100
land_net = revenue * land_share_pct / 100 - deposit
```

## Recommended Split Determination

- The precise split is `dev_share_pct : land_share_pct` (what hits target exactly)
- Round to nearest whole number for practical negotiation
- Show 3-4 scenario rows in the presentation for the user to negotiate with

## Scenario Sensitivity

Test at least:
- **Price sensitivity**: ±₹1,000/sft and ±₹2,000/sft from base
- **Cost sensitivity**: ±₹300/sft and ±₹500/sft from base construction cost
- **Split sensitivity**: Target split ±1-2 points, and extreme (40:60 for walk-away)

## Presentation Structure (8 slides)

1. **Cover** — Project name, acres, type, DRA Realty
2. **Executive Summary** — Land card + metrics cards + thesis bar
3. **Development Assumptions** — Table of all inputs
4. **Revenue Projection** — Large revenue number + area/rate cards
5. **Cost Analysis** — Cost breakdown table + summary bar
6. **Profitability & JDA Split** — Revenue distribution (left) + metric cards (right) + ROC bar
7. **Recommended Offer** — Large split number + scenario comparison table
8. **Sensitivity Analysis** — Two-column: price sensitivity (left) + cost sensitivity (right) + negotiation guidelines

## Pitfalls

- ALWAYS confirm JDA vs outright with the user — Kelsa may show 'Outright' but actual deal is JDA
- FAR is the governing constraint — confirm with user before using any value, different jurisdictions (BBMP/BDA/BMRDA/KIADB) have different FAR tables
- Deposit is recoverable from landowner's share at settlement — it's not a cost, it's a recoverable advance
- When user says "target 36% profit" they mean ROC (Return on Cost = profit / cost), not margin (profit / revenue)
- Present the split recommendation with scenarios, not just one number — the user needs to negotiate
- Round split ratios to whole numbers for the presentation, note the precise figure in your calculation
