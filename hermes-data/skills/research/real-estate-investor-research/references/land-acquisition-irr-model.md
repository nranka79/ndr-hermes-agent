# Land Acquisition IRR Model — Methodology Reference

## Overview

Three-scenario framework for evaluating a land parcel acquisition from a developer's perspective. Used by DRAAS for Bangalore real estate. All scenarios share the same base assumptions (land area, FAR, construction cost, finance rate, tax rates) but differ in execution strategy.

## Base Inputs (always confirm with user)

| Parameter | Example | Notes |
|-----------|---------|-------|
| Land Area | 3.0 Ac (1,30,680 sqft) | Verify from survey/sketch |
| Construction Cost | ₹4,000/sqft BUA | **Always confirm — do NOT assume.** User may correct you. |
| Achievable FAR | 3.00 (depends on road width) | **Critical variable — verify road width first.** See BBMP FAR-by-road-width table. |
| Sale Price | ₹11,000/sqft | Justify from competitive benchmarking |
| Saleable Efficiency | 85% | After deducting common areas, walls |
| Finance Rate | 12% p.a. | Construction finance from banks/NBFCs |
| Weighted Drawdown | 1.5 years | Phased drawdown over construction |
| Corporate Tax | 25% | New regime |
| LTCG (land banking) | 10% | Indexed, for raw land resale only |

### Land Overheads
- Stamp Duty: 5%
- Registration: 1%
- Brokerage: 1%
- Legal & DD: Flat ₹50,00,000
- Conversion/NOCs: Flat ₹25,00,000
- All-in rate ≈ base rate × 1.07 + ₹5.73/sqft (flat costs spread)

### Soft Cost Breakdown
| Item | Rate | Basis |
|------|------|-------|
| Architects & Design | 3% | Base construction cost |
| Structural Consultant | 1% | Base construction cost |
| Project Management | 2% | Base construction cost |
| Bank Processing | 0.5% | Base construction cost |
| RERA Registration | ₹30,00,000 | Flat |
| Marketing (pre-launch) | ₹50,00,000 | Flat |
| **Total** | **~6.5% + ₹80L flat** | |

### GST
- Output: 5% of GDV (on under-construction premium residential)
- Input: 18% on construction inputs (cement, steel, contractor bills)
- Credit availability: 70% assumed for residential
- Net GST = max(0, Output - Input × 70%)

## Scenario A: Land Banking (Buy → Hold → Sell Raw)

Used when the user wants a passive investment thesis rather than active development.

### Cash Flow
```
Year 0: -(Land all-in)
Year 1: -(Holding costs = property tax ~0.2% + security ~₹6L/yr)
Year N: +(Sale value - brokerage - LTCG tax)
```
IRR = solve NPV=0 with single outflow, single inflow at exit.

### Inputs
| Parameter | Example |
|-----------|---------|
| CAGR (appreciation) | 8-15% |
| Hold period | 2-4 years |
| Exit brokerage | 1% |
| LTCG tax | 10% (indexed) |

### Outputs
Exit land rate, gross exit value, net proceeds, net profit, IRR, MOIC.

## Scenario B: Development (Apartment Project)

Full build-and-sell scenario. Most detailed cash flow model.

### Phased Cash Flow
```
Year 0.0: -(Land all-in)
Year 0.5: -(Construction 30% + Soft 30% + GST 15%)
Year 1.0: -(Construction 40% + Soft 40% + GST 40% + Finance 40%)
Year 1.5: -(Construction 30% + Soft 30% + GST 45% + Finance 60%)
Year 2.0: +(GDV × 25% - Sales × 25%)
Year 2.5: +(GDV × 40% - Sales × 40%)
Year 3.0: +(GDV × 25% - Sales × 25%)
Year 3.5: +(GDV × 10% - Sales × 10% - Corp tax)
```

### Sensitivity
Build a matrix: Sale Price (₹8,500-14,000) vs XIRR. Green-highlight the base case row.

## Scenario C: JDA (Joint Development Agreement)

### Landowner's View
| Metric | Formula |
|--------|---------|
| Gross Revenue | GDV × JDA_Share_% |
| Taxable Gain | Revenue - (All-in_Land_Cost × Share_%) |
| LTCG Tax | Gain × 10% |
| Net to Landowner | Revenue - Tax |
| Eqv. Land Rate | Net / Total sqft |
| IRR | Single outflow (land value) at t=0, single inflow at t=project_end |

### Developer's View (viability check)
| Metric | Formula |
|--------|---------|
| Revenue | GDV × (1 - Share_%) |
| Costs | Construction + Soft + Finance + GST + Sales (100%) |
| Net Profit | (Revenue - Cost) × (1 - 25%) |
| IRR | Phased costs (no land) vs phased revenue |
| **Viable if** | Developer IRR ≥ **15%** |

### Standard Structures
| L:D Ratio | Landowner Gets | Developer Gets | When |
|-----------|---------------|----------------|------|
| 70:30 | 30% of GDV | 70% of GDV | Weak landowner bargaining power |
| 65:35 | 35% of GDV ★ | 65% of GDV | Standard for good locations |
| 60:40 | 40% of GDV | 60% of GDV | Scarce land, strong landowner |
| 55:45 | 45% of GDV | 55% of GDV | Aggressive — rare, exceptional location |

### Impact of Construction Cost on JDA
Higher construction cost → developer margin compresses → landowner gets lower share. At ₹2,800/sqft construction, landowner could get ~40%. At ₹4,000/sqft, realistic max is ~35%. Always flag this when user revises construction cost.

## Hybrid Acquisition (Partial Buy + Partial JDA)

### Structure
- Buy X% of land outright
- Remaining (100-X)% on JDA with standard share terms
- Develop entire site as one integrated project

### Your Economics
```
Your Land Cost = Total_Land_sqft × Purchase_rate × Buy_% (all-in)
JDA_Portion_GDV = Total_GDV × (100-Buy_%)/100
JDA_To_Landowner = JDA_Portion_GDV × JDA_Share_%
Your_GDV_Share = Total_GDV - JDA_To_Landowner
Your_Total_Cost = Your_Land_Cost + Development_Costs (100%)
Your_Net_Profit = (Your_GDV_Share - Your_Total_Cost) × (1 - Tax)
Blended_XIRR = Solve NPV=0 with phased cash flow
```

### Comparison Table
| Metric | 100% Buy | Hybrid | Pure JDA |
|--------|----------|--------|----------|
| Upfront Equity | Highest | Reduced | Zero |
| Net Profit | Highest | Moderate | Lowest |
| XIRR | Moderate | **Best** | Moderate |
| Control | Full | Full | Shared |
| Risk | Highest | Moderate | Lowest |

## Target Profit → Max Land Cost (Backward Method)

When the user states a target profit margin (e.g. "min 24%"), work backwards:

### CRITICAL — Clarify First\nAsk: "Do you mean Gross Margin (GP/Total Cost, pre-tax) or Net Margin (NP/Total Cost, post-tax)?"\n\nAt ₹4,000/sqft construction, the gap between gross and net is ~8-10 percentage points. User says "24% profit" — one interpretation delivers the deal, the other kills it. Do not proceed until they answer.\n\n**Quoting pitfall:** Never say "at current asking (₹7,000/sqft) you only get X% net margin" without first establishing which margin they meant. If they meant gross, the deal may still work at ₹7,000. Lead with the clarification, not the conclusion.

### Formula (for Net Margin target = T)
```
NP/TC = T
0.75(GDV - TC) / TC = T
GDV / TC = 1 + T/0.75
Max_TC = GDV / (1 + T/0.75)

Max_Land_AllIn = Max_TC - (Construction + Soft + Finance + GST + Sales)
Max_Land_Rate = (Max_Land_AllIn - 75_00_000) / 1.07 / Total_sqft
```

### Worked Example
Construction ₹4,000/sqft, FAR 3.00, Sale ₹11,000/sqft, Target 24% Net Margin:
```
Saleable = 1,30,680 × 3.0 × 0.85 = 3,33,234 sqft
GDV = 3,33,234 × 11,000 = ₹366.56 Cr
Max_TC = 366.56 / 1.32 = ₹277.70 Cr
Fixed_Costs = 192.10 + 12.69 + 36.86 + 0 + 7.33 = ₹249.0 Cr
Max_Land_AllIn = 277.70 - 249.0 = ₹60.4 Cr
Max_Land_Rate = (60.4 - 0.75) / 1.07 / 130680 × 1e7 = ₹4,459/sqft
```

## BBMP R3 FAR by Road Width (Bangalore)

**Road width is the single most critical variable. Confirm physically.**

| Road Width | Base FAR | Max Premium | Achievable FAR |
|------------|----------|-------------|----------------|
| < 24 ft | 2.00 | +0.75 | **2.75** |
| 24-30 ft | 2.00 | +1.00 | **3.00** |
| 30-40 ft | 2.25 | +1.25 | **3.50** |
| 40+ ft | 2.50 | +1.50 | **4.00** |
| TOD corridor | 2.50 | +2.00 | 4.50 |

A 15% change in FAR (3.00 → 3.50) changes the max affordable land rate by ~₹750/sqft = ~₹10 Cr swing in land budget for 3 acres.

## XIRR Calculation

Use bisection (not Newton-Raphson) for robustness — real estate cash flows with large positive/negative swings can cause Newton to diverge.

### Algorithm
1. Define NPV(rate) = Σ CF_t / (1+rate)^t
2. Bracket: start lo=-0.90, hi=10.0 (IRR > -90% and < 1000%)
3. If NPV(lo) × NPV(hi) > 0, expand search
4. If still no bracket found, fall back to CAGR approximation
5. Bisection: 50 iterations narrowing lo/hi until NPV~0

### Cash Flow Structure
```
cf = [
    (year, amount),  # negative = outflow, positive = inflow
    (0.0, -land_cost),
    (0.5, -construction_phase_1),
    ...
    (3.5, +final_sales_tranche),
]
```
Sort by year before computing. Fractional years allowed.

## Key Ratios to Report
| Ratio | Target Range | Formula |
|-------|-------------|---------|
| Margin on Cost (Gross) | 25-40% | GP / Total Cost |
| Margin on Cost (Net) | 15-25% | NP / Total Cost |
| Margin on Revenue | 15-25% | NP / GDV |
| Return on Land Cost | 50-100% | NP / Land Cost |
| Land Cost % of GDV | 15-30% | Land Cost / GDV |
| Const. Cost % of GDV | 35-50% | Construction / GDV |

### Multi-Line Sensitivity Cells\nWhen the user asks for "percentages and value" in the same view, format each cell as a multi-line block showing all four key metrics:\n```\n₹4,458/sf    ← Max land rate\n₹63.1 Cr     ← All-in cost\n24.0%        ← Net margin\n17.2% of GDV ← Land cost % of GDV\n```\nImplementation: `ws.cell.value = multi-line string`, set `alignment(wrap_text=True)`, and adjust `row_dimensions[r].height` to ~72.\n\n### openpyxl API Pitfalls (verified June 2026)\n\nThese cost multiple iterations in a single session. Know them upfront:\n\n1. **Cell kwargs DON'T work.** These are INVALID:\n   ```python\n   # BROKEN\n   ws.cell(row=r, column=c, value=v, font=Font(...), fill=PatternFill(...), border=tb)\n   ws.cell(row=r, column=c, border=tb)        # BROKEN — 'border' not a valid arg\n   ws.cell(row=r, column=c, font=Font(...))    # BROKEN — 'font' not a valid arg\n   ```\n   Instead, set properties on the returned cell object:\n   ```python\n   c = ws.cell(row=r, column=c, value=v)\n   c.font = Font(...)\n   c.fill = PatternFill(...)\n   c.border = tb\n   c.alignment = Alignment(horizontal='right', wrap_text=True)\n   ```\n\n2. **MergedCell read-only.** After `ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)`, you can only write to cell(r, 2). Writing to cell(r, 3) raises `AttributeError: 'MergedCell' object attribute 'value' is read-only`. Either:\n   - Don't merge — just write to column 2 and let text overflow\n   - Or merge AFTER writing all values\n\n3. **Color variable naming.** Choose one convention and stick to it. `l_gold_f`, `l_gold_fill`, `gold_fill_light` will all be used inconsistently when you're in a hurry. Define at the top:\n   ```python\n   l_gold_f = PatternFill(start_color=L_GOLD, end_color=L_GOLD, fill_type=\"solid\")\n   l_navy_f = PatternFill(start_color=L_NAVY, end_color=L_NAVY, fill_type=\"solid\")\n   green_f = PatternFill(start_color=\"E8F5E9\", end_color=\"E8F5E9\", fill_type=\"solid\")\n   red_f   = PatternFill(start_color=\"FFEBEE\", end_color=\"FFEBEE\", fill_type=\"solid\")\n   ```\n\n4. **Rupee → Cr conversion.** `ai` (all-in land) is in raw rupees (e.g. 63,09,70,408). To display in Cr: `ai / 1e7`. The `/#,##0.00" Cr"` number format works on cell values but NOT on f-string display. Keep the division explicit in f-strings.\n\n5. **Hermes venv.** Always:`/opt/hermes/.venv/bin/python /path/to/script.py`. System `python3` won't have openpyxl. If it breaks mid-session, `uv pip install openpyxl`.

### DRAAS Colour Palette
```python
NAVY="1B2A4A"; GOLD="C9A84C"; WHITE="FFFFFF"
D_GRAY="333333"; GREEN="1E7A3C"; RED="C0392B"
L_GRAY="F5F5F5"; L_NAVY="E8EDF3"; L_GOLD="FFF8E7"
```

### Standard Sheet Structure
1. **All Rates & Assumptions** — Always include. Every rate, %, and value with source notes.
2. **Summary / Dashboard** — Key matrices, comparative table, 3-5 important takeaways
3. **A - Land Banking** — Acquisition costs, holding costs, exit scenarios (Conservative/Base/Optimistic/Quick Flip)
4. **B - Development** — Parameters, cost breakdown (land/constr/soft/finance/GST/sales), P&L, sensitivity (sale price vs IRR)
5. **C - JDA** — All structures with landowner AND developer perspectives
6. **Cash Flow Timeline** — Phased yearly cash flows, XIRR methodology note
7. **Competitive Benchmarking** — My Maps projects with verified prices, price segments, target price justification

### Always include an "All Rates & Assumptions" sheet
Pre-empt the user asking "what rates did you use." Every row needs: rate name, value, short source note.

## Competitive Benchmarking from Google My Maps

When user shares a Google My Maps link (`maps.google.com/maps/d/edit?mid=...`):
1. Fetch HTML with curl and extract `_pageData` JS variable
2. Parse project names with price ranges (formatted as "ProjectName - PriceRange")
3. Research each independently via web search for verified current pricing
4. Build Competitive Benchmarking sheet showing: project name, map price, verified price, segment, source
5. Use to justify target sale price for proposed development

**DRAAS worked example (June 2026):** "RT Nagar - 120000 Sq.ft - Rnd of Projects nearby" — 9 projects in 2 layers. After verification, target sale price of ₹11,000/sqft was justified as mid-premium, above Krishna Legacy (₹9,500-10,500) and below White House (₹12,500-13,500).

## Session-Specific Data: Kaval Byrasandra (June 2026)

- Location: Kaval Byrasandra, R.T. Nagar, Bangalore
- Parcel: 3 Acres (1,30,680 sqft)
- Construction Cost: ₹4,000/sqft (user-confirmed)
- Realistic FAR: 3.00 (24-30ft road — needs physical verification)
- Target Margin: 24% net (user-stated)
- Competitive Range: ₹7,000 (Sundher Manor floor) to ₹18,500 (HM Tropical Tree ceiling)
- Recommended Target: Land ₹4,000-4,500/sqft + Sale ₹11,000/sqft → Net Margin 24-25%
- Model file: `/opt/data/Kaval_Byrasandra_3Ac_IRR_Model.xlsx`

## Common Pitfalls

1. **Assuming FAR without road width check** — A ₹500/sqft difference in land rate × 3 acres = ~₹6.5 Cr swing. Always ask for road width first.
2. **Confusing construction cost with land cost** — Always confirm which ₹/sqft the user means. Prakash corrected this mid-session.
3. **Not re-running all scenarios when a core input changes** — If user revises construction cost (+43%), ALL outputs change (net profit, IRR, JDA share, breakeven land cost).
4. **Single-perspective JDA analysis** — Always check BOTH landowner return AND developer viability. A 40% share may look good to the landowner but if it gives the developer <15% IRR, it's not a real deal.
5. **Omitting the rates sheet** — Pre-empt "what rates did you use" by always including a transparent assumptions sheet as the first or second tab.
6. **Calling openpyxl scripts with system Python** — Always use `/opt/hermes/.venv/bin/python`.
7. **Conflating user-confirmed inputs with your recommendations** — When a user says "construction cost will be ₹4,000/sqft", that's a CONFIRMED input. When you later say "target land rate is ₹4,000", that's YOUR recommendation. These are different categories. In the spreadsheet, use separate sections with clear labels (CONFIRMED vs RECOMMENDED/TARGET). Use different fills (e.g., light green for confirmed, light gold for recommended). Never let a user confuse your suggestion for their own input — and never confuse them yourself. If the user says "I never said that" about a number you used, it means you've mixed up these categories.
