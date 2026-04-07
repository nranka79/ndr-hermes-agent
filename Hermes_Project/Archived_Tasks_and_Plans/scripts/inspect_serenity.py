
import pandas as pd

# Load the Excel file
file_path = r'c:\Users\ruhaan\AntiGravity\serenity_data.xlsx'
xls = pd.ExcelFile(file_path)

print(f"Sheet names: {xls.sheet_names}")

# Based on user description, there's an 'Analysis' sheet.
# Let's try to find it.
analysis_sheet = None
for sheet in xls.sheet_names:
    if 'analysis' in sheet.lower():
        analysis_sheet = sheet
        break

if not analysis_sheet:
    print("Analysis sheet not found specifically by name. Listing all sheets data for inspection.")
    for sheet in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet)
        print(f"\n--- Sheet: {sheet} ---")
        print(df.head())
else:
    df = pd.read_excel(file_path, sheet_name=analysis_sheet)
    print(f"\n--- Analysis Sheet Content ---")
    print(df.to_string())

# Also inspect the first sheet which seemed to have the plot-wise data in the previous view_file
df_main = pd.read_excel(file_path, sheet_name=0)
print(f"\n--- Main Sheet (Sheet 0) Content ---")
print(df_main.to_string())
