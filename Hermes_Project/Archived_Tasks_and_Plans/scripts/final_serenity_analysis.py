
import pandas as pd

file_path = r'c:\Users\ruhaan\AntiGravity\serenity_data.xlsx'
df = pd.read_excel(file_path, sheet_name='Plot Distribution')
df.columns = df.columns.astype(str).str.strip()

# Area column
area_col = 'Total Area' if 'Total Area' in df.columns else 'Registerable Area(Sft)'
total_land_area = df[area_col].sum()

# Area Breakdown
area_group_1 = total_land_area * 0.60
area_group_2_calc = total_land_area * 0.40

# Costs
land_cost = 21_00_00_000
dev_cost = 6_00_00_000
misc_cost = 1_20_00_000
total_project_cost = land_cost + dev_cost + misc_cost

# Cost to be borne by Group 2 (50% of total cost)
cost_group_2 = total_project_cost * 0.50

# Cost per sq ft for Group 2
cost_per_sqft_group_2 = cost_group_2 / area_group_2_calc

print(f"Total Land Area: {total_land_area:,.2f} sq ft")
print(f"Group 1 Area (60%): {area_group_1:,.2f} sq ft")
print(f"Group 2 Area (40%): {area_group_2_calc:,.2f} sq ft")
print("-" * 30)
print(f"Total Project Cost: ₹ {total_project_cost:,.2f} (28.2 Cr)")
print(f"Cost borne by Group 2 (50%): ₹ {cost_group_2:,.2f} (14.1 Cr)")
print("-" * 30)
print(f"Effective Cost per sq ft for Group 2: ₹ {cost_per_sqft_group_2:,.2f}")

# Revenue Comparison at different rates
rates = [1100, 1150, 1200, 1250]
print("\n--- Revenue Comparison for Group 2 ---")
for rate in rates:
    revenue = area_group_2_calc * rate
    pct_of_total_cost = (revenue / total_project_cost) * 100
    print(f"@ ₹ {rate}/sqft: Total = ₹ {revenue:,.2f} ({revenue/10_000_000:.2f} Cr) | % of Overall Cost: {pct_of_total_cost:.2f}%")
