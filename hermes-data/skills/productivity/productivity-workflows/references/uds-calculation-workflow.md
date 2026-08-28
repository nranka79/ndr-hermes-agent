# UDS (Undivided Share of Land) Calculation for Apartment Projects

**When to use this:** A real estate project (apartment building, villa development) needs UDS (Undivided Share of Land) values per unit for Agreements of Sale, sale deeds, allotment letters, and Kelsa inventory tracking.

## Context

UDS is the proportionate land ownership each apartment owner holds. Every unit **must** have UDS clearly defined before any Agreement of Sale is executed.

## The Formula

```
UDS per unit = (Total plot area / Total super built-up area of all units) * Unit's super built-up area
```

### Step-by-step

1. **Determine total plot area** — use the area shown in the **sanctioned plan**
   - If actual surveyed site area is **larger** than sanctioned plan area -> use sanctioned plan area
   - If actual surveyed site area is **smaller** than sanctioned plan area -> use the **lesser** (surveyed) area
   - This protects against over-selling land that doesn't exist on title

2. **Get sum of all Super Built-up Area (SBUA)** from the area statement sheet
   - Add up the SBUA column for all units

3. **Calculate UDS per sqft of SBUA**
   - UDS_factor = Total plot area / Total SBUA
   - Example: 14,000 sqft / 31,853 sqft = 0.4395

4. **Calculate per-unit UDS**
   - Unit UDS = Unit SBUA * UDS_factor

## Sanctioned vs Execution Area Statements

Projects typically have TWO area statements:

| Version | Source | Use |
|---------|--------|-----|
| Sanctioned plan-based | BBMP/BCC approved plan | Agreements of Sale, sharing agreements, legal docs |
| Execution drawing-based | Architect's construction drawings | Actual delivery, permissible deviations |

**Critical rule:** UDS per unit **must stay the same** in both versions.

- UDS is allocated between landowner and developer (e.g. 50:50 sharing) in the Joint Development Agreement / Sharing Agreement
- Once allocated, it does **not** change even if execution areas differ slightly due to permissible deviations
- Agreements of Sale reference the sanctioned plan area + note permissible deviation -> deliver execution area
- UDS remains identical — it represents the fixed land share, not the floating built-up area

## Implementation

1. **Add a UDS (sqft) column** to the area statement spreadsheet
2. Calculate per-unit UDS using the formula above
3. Cross-verify with team (project manager, architect)
4. Architect to confirm UDS allocation is consistent with plan
5. Update Sharing Agreement to reference UDS values
6. Populate UDS in:
   - Agreements of Sale
   - Allotment letters
   - Sale deeds
   - Kelsa inventory / cost sheets

## Common Pitfalls

- **Using wrong land area:** Always use sanctioned plan area (or lesser of sanctioned vs surveyed). Never use a larger area the developer wishes they had — only the legally recorded area counts.
- **Changing UDS between versions:** UDS must stay fixed. Even if execution SBUA increases, UDS does not change.
- **Forgetting UDS in sale agreements:** Every Agreement of Sale must explicitly state the unit's UDS. Buyers need it for property tax, resale, and loan approval.

## Tooling

UDS values can be computed directly in Google Sheets:
```
= <total_plot_area> / SUM(<SBUA_range>) * <cell_reference>
```

Grant Viewer/Editor access on the sheet to relevant stakeholders:
- Project manager -> Viewer
- Architect -> Editor (to confirm/validate)
- Legal/Compliance -> Viewer
- Sales team -> Viewer (needs UDS for sale agreements)
