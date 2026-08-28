# Kaval Byrasandra IRR Case Study — June 2026

## Context
Land acquisition analysis for 3-acre parcel in Kaval Byrasandra, R.T. Nagar, Bangalore. Commissioned by Prakash Singh (DRAAS). Initial model built with ₹2,800/sqft construction, later revised to ₹4,000/sqft. Target profit margin: 24% net (post-tax) on cost.

## Key Corrections Made During Session

1. **User never stated a land rate** — I assumed ₹7,000/sqft as "current asking price" but user corrected: "I never mentioned that target land cost is 4000, I mentioned our construction cost is 4000." Lesson: Never present your own assumption as the user's confirmed input. Use two distinct visual categories: CONFIRMED (user-provided) vs RECOMMENDED (your suggestion).

2. **User wanted simple, not complex** — After multiple iterations with matrix tables and 4-line cells, user said "all the calculations are wrong, I just need simple IRR calculations." Lesson: Start simple. Add complexity only when asked.

3. **Rate + Value for every component** — After building a streamlined model, user asked "always add rate and value of each component." Every line item needs the rate/basis AND the computed value.

4. **Excel formulas, not hard-coded values** — When the spreadsheet wasn't updating after cell edits, user pointed out "values are changing" (meaning they weren't). Lesson: Use `=FORMULA` references, not computed constants, when building editable models.

5. **Construction cost revision (₹2,800 → ₹4,000)** — This single change added ~₹63 Cr to project cost and dropped IRR by ~5 percentage points. The JDA landowner's viable share dropped from ~40% to ~35%. Lesson: When a core assumption changes mid-session, re-run ALL scenarios and explicitly flag the impact.

6. **FAR depends on road width** — I assumed FAR 3.50 initially. User later specified 40ft road = base FAR 2.25 + premium. The max affordable land rate dropped from ₹5,222/sqft (FAR 3.50) to ₹4,459/sqft (FAR 3.00). Lesson: Verify road width and achievable FAR BEFORE building any model — it's the single most important variable.

## Final Model Structure

### Inputs (editable yellow cells)
| # | Input | Final Value |
|---|-------|-------------|
| A1 | Land Rate (₹/sqft) | 4,500 |
| A2 | Sale Price (₹/sqft) | 11,000 |
| A3 | Achievable FAR | 3.25 (2.25 base + 1.00 premium) |
| A4 | Construction Cost (₹/sqft) | 4,000 |
| A5 | Land Area (sqft) | 130,680 (3 Ac) |
| A6 | Finance Rate (% p.a.) | 12.0 |
| A7 | Target Net Margin (%) | 24.0 |

### Key Outputs (@ ₹4,500 land, ₹11,000 sale, FAR 3.25)
- **Total Cost:** ₹296.07 Cr
- **GDV:** ₹397.10 Cr
- **Net Profit:** ₹75.77 Cr
- **Net Margin:** 25.6% ✓ (exceeds 24%)
- **BUA:** 424,710 sqft
- **Saleable:** 361,004 sqft

### Component Rate & Value Breakdown
| Component | Rate | Value |
|-----------|------|-------|
| Land (Base) | ₹4,500/sqft × 130,680 | ₹58.81 Cr |
| Stamp Duty | 5% of base | ₹2.94 Cr |
| Registration | 1% of base | ₹0.59 Cr |
| Brokerage | 1% of base | ₹0.59 Cr |
| Legal & DD | Flat | ₹0.50 Cr |
| Conversion / NOCs | Flat | ₹0.25 Cr |
| **Land (All-in)** | | **₹63.67 Cr** |
| Construction (Base) | ₹4,000/sqft × 424,710 BUA | ₹169.88 Cr |
| Contingency | 5% of base | ₹8.49 Cr |
| **Construction (Total)** | | **₹178.37 Cr** |
| Soft Costs | 6.5% of base + ₹80L | ₹11.85 Cr |
| Finance | 12% × 1.5yr | ₹34.25 Cr |
| GST (Net) | max(0, output − input) | ₹0 |
| Sales & Marketing | 2% of GDV | ₹7.94 Cr |
| **TOTAL COST** | | **₹296.07 Cr** |
| **GDV** | 361,004 saft × ₹11,000 | **₹397.10 Cr** |
| **Net Profit** | (GDV − TC) × 75% | **₹75.77 Cr** |
| **Net Margin** | NP / TC | **25.6%** |

### Land Rate Sensitivity (at ₹11,000 sale, FAR 3.25)
| Land Rate | All-in Cost | Net Margin |
|-----------|-------------|------------|
| ₹2,500/sqft | ₹36 Cr | 36.6% |
| ₹3,000/sqft | ₹43 Cr | 33.8% |
| ₹3,500/sqft | ₹50 Cr | 31.1% |
| ₹4,000/sqft | ₹57 Cr | 28.3% |
| ₹4,500/sqft | ₹64 Cr | 25.6% |
| **₹4,840/sqft** | **₹68 Cr** | **24.0% ← max for target** |
| ₹5,000/sqft | ₹71 Cr | 23.0% |
| ₹5,500/sqft | ₹78 Cr | 20.5% |

### Right Land Price Conclusion
At FAR 3.25 and ₹11,000/sqft sale:
- **Target:** ₹4,500/sqft (₹64 Cr all-in) → 25.6% margin ✓
- **Max for 24%:** ₹4,840/sqft (₹68 Cr all-in)
- **Walk away above:** ₹5,500/sqft → margin drops to 20.5%

## Formulas Used (for copy-paste into Excel)

Key formula relationships:
- `BUA = Land_Area × FAR`
- `Saleable = BUA × 0.85`
- `Land_Base = Land_Rate × Land_Area`
- `Land_AllIn = Land_Base × 1.07 + 75_00_000`
- `Construction_Base = BUA × Const_Rate`
- `Construction_Total = Construction_Base × 1.05`
- `Soft_Costs = BUA × Const_Rate × 0.065 + 80_00_000`
- `Finance_Cost = (Construction_Total + Soft_Costs) × 0.12 × 1.5`
- `GDV = Saleable × Sale_Price`
- `GST_Net = MAX(0, GDV × 0.05 − Construction_Base × 0.18 × 0.70)`
- `Sales = GDV × 0.02`
- `Total_Cost = Land_AllIn + Construction_Total + Soft_Costs + Finance + GST_Net + Sales`
- `Gross_Profit = GDV − Total_Cost`
- `Net_Profit = Gross_Profit × 0.75`
- `Net_Margin = Net_Profit / Total_Cost`

## Backward Formula (for quick land rate calc)
```
Max_TC = GDV / 1.32
Max_Land_AllIn = Max_TC − (Construction + Soft + Finance + GST + Sales)
Max_Land_Rate = (Max_Land_AllIn − 75_00_000) / (1.07 × Land_Area)
```
Derivation: NP/TC = 0.24 → 0.75(GDV−TC)/TC = 0.24 → GDV/TC = 1.32
