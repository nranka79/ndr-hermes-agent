
import pandas as pd
import sys
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

file_path = r'c:\Users\ruhaan\AntiGravity\serenity_data.xlsx'
df = pd.read_excel(file_path, sheet_name='Plot Distribution')

# Clean up column names just in case
df.columns = df.columns.astype(str).str.strip()

print("Columns in 'Plot Distribution':")
print(df.columns.tolist())

# "Reconstitution Distribution" is the column that has P1-P19, MS, CM, BB, SH, etc.
# Group 1: MS (Manohar Singh), CM (Charitra Moorjani), BB (Bhavesh Bhatna), SH (S.H.)
group_1_identifiers = ['MS', 'CM', 'BB', 'SH']

if 'Reconstitution Distribution' in df.columns:
    # Filter out rows where Reconstitution Distribution is null or not string
    df_valid = df[df['Reconstitution Distribution'].notna()].copy()
    
    # Identify group 1 and group 2
    # The user states "Reconstitution Distribution" has MS, CM, BB, P1-P19
    df_valid['Group'] = df_valid['Reconstitution Distribution'].str.strip().apply(
        lambda x: 'Group 1' if any(i in str(x) for i in group_1_identifiers) else 'Group 2'
    )
    
    print("\n--- Distribution of investors ---")
    print(df_valid['Reconstitution Distribution'].value_counts())
    
    # Area columns
    area_col = 'Total Area' if 'Total Area' in df_valid.columns else 'Registerable Area(Sft)'
    if 'Total Area' in df_valid.columns:
        print(f"\nUsing area column: 'Total Area'")
        area_col = 'Total Area'
    
    group_stats = df_valid.groupby('Group')[area_col].agg(['sum', 'count'])
    print("\n--- Group Stats ---")
    print(group_stats)
    
    # Now user states: 
    # "Now of the total area, if we say 50% belongs to investor group one, what is the total area belonging to investor group two?"
    # What did the user exactly want? Let's re-read:
    # "Now of the total area, if we say 50% belongs to investor group one, what is the total area belonging to investor group two?"
    total_area_all = df_valid[area_col].sum()
    print(f"\nTotal Area of all valid plots: {total_area_all}")
    
    # The logic given by the user:
    # "assuming we take a plot cost of 10.5 crores for their half."
    # "The total area belonging to investor group 2. To that 10.5 crores we are adding 3 crores as development cost and 1 crore as other miscellaneous cost. So it becomes 14.5 crores."
    # "Dividing it by the total area of the investor group. The other investor group. Not the group one but the group two. The rest P1 to P19 plus."
    # "What exactly are we getting in terms of total area and cost of the area?"
    # "And if we multiply the total area by 11 crore, 11, 12, 50 rupees or 1100, what are we getting as the total revenue to be collected from the other industries?"
    
    # Calculate exactly what user asked
    area_group_2 = group_stats.loc['Group 2', 'sum'] if 'Group 2' in group_stats.index else 0
    print(f"\nTotal Area Group 2: {area_group_2}")
    
    if area_group_2 > 0:
        total_cost_group_2 = 145000000  # 14.5 crores (10.5 + 3 + 1)
        cost_per_sqft_group_2 = total_cost_group_2 / area_group_2
        print(f"Cost per sqft for Group 2: {cost_per_sqft_group_2}")
        
        # Multiply total area by 1100, 1150, 1200, 1250 (as user said "11, 12, 50 rupees or 1100")
        for rate in [1100, 1150, 1200, 1250]:
            revenue = area_group_2 * rate
            print(f"Revenue at {rate} per sqft: {revenue} ( {revenue/10000000} Crores)")

