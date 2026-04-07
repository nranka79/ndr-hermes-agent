
import pandas as pd
import sys
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

file_path = r'c:\Users\ruhaan\AntiGravity\serenity_data.xlsx'
df = pd.read_excel(file_path, sheet_name='Plot Distribution')

# Clean up column names
df.columns = df.columns.astype(str).str.strip()

# Area column
area_col = 'Total Area' if 'Total Area' in df.columns else 'Registerable Area(Sft)'
total_land_area = df[area_col].sum()

print(f"Total Property Land Area: {total_land_area:,.2f} sq ft")

# User's Updated Proportions:
# Group A (Investors): 60%
# Group B (Investors): 40%

# Total Area Breakdown
area_group_a = total_land_area * 0.60
area_group_b = total_land_area * 0.40

print(f"\n--- Area Allocation (60/40 Split) ---")
print(f"Group A (60%): {area_group_a:,.2f} sq ft")
print(f"Group B (40%): {area_group_b:,.2f} sq ft")

# Cost Analysis for Group B
# Total Project Cost = 21 Crores (as stated by user in previous message)
# Group B holds 40% of the area.
# Proportionate Land Cost for Group B = 21 Crores * 40% = 8.4 Crores
land_cost_group_b = 21_00_00_000 * 0.40
dev_cost = 3_00_00_000
misc_cost = 1_00_00_000

total_cost_group_b = land_cost_group_b + dev_cost + misc_cost

print(f"\n--- Cost Analysis for Group B (Investors P1-P19) ---")
print(f"Allocated Land Cost (40% of 21Cr): ₹ {land_cost_group_b:,.2f} (8.4 Cr)")
print(f"Development Cost: ₹ {dev_cost:,.2f} (3.0 Cr)")
print(f"Miscellaneous Cost: ₹ {misc_cost:,.2f} (1.0 Cr)")
print(f"Total Cost for Group B: ₹ {total_cost_group_b:,.2f} (12.4 Cr)")

# Calculate Cost per sq ft for Group B
cost_per_sqft_group_b = total_cost_group_b / area_group_b

print(f"\nEffective Cost per sq ft for Group B: ₹ {cost_per_sqft_group_b:,.2f}")

# Target Rate Calculation
target_rate = 1100
current_valuation = area_group_b * target_rate
print(f"\nValuation at Target Rate (₹ {target_rate}/sqft): ₹ {current_valuation:,.2f} (~ {current_valuation/10_000_000:.2f} Crores)")
