# Bank Statement CSV Consolidation

Combine multiple bank statement CSV uploads (or their auto-converted Google Sheets) into a single chronological spreadsheet.

## User trigger

User uploads CSV bank statements to Drive (e.g. "Kotak account statements for 2025 and 2026") and asks to:
- Combine into one spreadsheet
- Sort latest→oldest
- Format date column as DD/MM/YYYY
- Search for a specific transaction by name/amount

## What actually happens

When a `.csv` is uploaded to Google Drive, Drive auto-converts it to a native Google Sheet. The original `.csv` filename becomes the sheet name. Searching by `name contains '.csv'` will NOT find these — search by the base name prefix instead.

## Pattern

### 1. Find the auto-converted sheets

```python
from tools.gws_skill_bridge import call
import json

# The user said "Kotak statements" — search for the account number or keyword
result = call("drive_search", service_name="google-draas",
              query="name contains '9880055634'", raw_query=True, max=50)
```

### 2. Read data from each sheet

```python
# Read all rows from each sheet
for file_id, sheet_range in [("FILE_ID_2025", "'9880055634_statement'!A1:Z1000"),
                              ("FILE_ID_2026", "'9880055634_statement (1)'!A1:Z1000")]:
    data = call("sheets_get", service_name="google-draas",
                file_id=file_id, range=sheet_range)
    print(data)  # JSON with 'values' key: list of lists
```

### 3. Create combined sheet

```python
# Create a new spreadsheet
new_sheet = call("sheets_create", service_name="google-draas",
                 title="Kotak 9880055634 Combined Statement",
                 parent_folder="TMP_FOLDER_ID")
```

### 4. Format and sort data

Parse all values, identifying the date column (usually column A). Reformat dates to DD/MM/YYYY. Sort by date descending (latest first). Write the combined rows to the new sheet:

```python
sorted_data = sorted(all_rows, key=lambda r: parse_date(r[0]), reverse=True)
header = ["Date", "Description", "Amount", "Dr/Cr", "Balance", "Bal Type"]
body = [header] + sorted_data

call("sheets_update", service_name="google-draas",
     file_id=new_sheet_id, range="A1", values=body)
```

### 5. Search for a specific transaction

The user asked for a payment to "Sharab Reddy" for ₹1,50,00,000. Search strategies:
- **By name variant:** Try "Sharab", "Sharabah", "Shara", "Reddy" — use case-insensitive substring match
- **By amount:** Search for rows where the amount column contains the exact figure OR nearby values (₹1.4Cr–₹1.6Cr)
- **By transfer type:** Look for RTGS/NEFT/CLG/IMPS in the description column if the exact name isn't found

### 6. Cleanup: delete the original auto-converted sheets

```python
for file_id in [ORIGINAL_2025_ID, ORIGINAL_2026_ID]:
    result = call("drive_delete", service_name="google-draas",
                  file_id=file_id, permanent=False)
    print(result)  # {"status": "trashed", ...}
```

## Date parsing pitfall

Sheets API returns dates as strings or serial numbers depending on how they were imported. Check the raw value type:
- If a number like `45678` → treat as Excel serial (days since 1899-12-30)
- If a string like `01/01/2025` → parse directly
- Use a try/parse approach: try `dateutil.parser.parse()`, fall back to Excel serial math

```python
from datetime import datetime, timedelta

def parse_date(val):
    if isinstance(val, str):
        parts = val.split('/')
        if len(parts) == 3:
            return datetime(int(parts[2]), int(parts[1]), int(parts[0]))  # DD/MM/YYYY
    if isinstance(val, (int, float)):
        return datetime(1899, 12, 30) + timedelta(days=int(val))
    return datetime.min
```

## When the transaction ISN'T found

If the transaction doesn't exist in any uploaded statement, it may be in:
1. A **different account** (HDFC, ICICI, another Kotak account with a different number)
2. A **different time period** not covered by the uploaded statements
3. The account belongs to a **different entity** (company account vs personal account)

Report clearly which account the statements covered, what you searched, and how many rows you checked.
