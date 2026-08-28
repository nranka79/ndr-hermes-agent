# KDR Monthly Payment & Expense Tracker

Bharat's sheet for tracking Kanta Ranka (KDR) medical expenses and miscellaneous bills.

## Sheet Location

- **Name:** KDR Monthly Payment & Expense Tracker
- **Sheet ID:** `1lIMvlVR8w-_LgsbRg3FfthveVr5EX0j-0-mDLmR33JQ`
- **Link:** https://docs.google.com/spreadsheets/d/1lIMvlVR8w-_LgsbRg3FfthveVr5EX0j-0-mDLmR33JQ/edit

## Column Structure

| Col | Header | Notes |
|-----|--------|-------|
| A | Sl No | Restarts at 1 per section. Empty for recent entries. |
| B | Item / Description | Free text — hospital, bill type, or payee name |
| C | Payment Date | DD.MM.YYYY format |
| D | Mode of Payment | Credit card, Cash, Gpay, RNR Gpay, DRA Rtgs, Office Expenses |
| E | Amount (₹) | Numeric string, no commas. Used in total. |
| F | Remb Status | DONE / Not Done (or blank) |

## Append Pattern (critical)

The sheet has a **Total row at the bottom** that must be handled before appending:

```
1. Remove the old Total row       → clear rows in that range
2. Append new expense rows        → rows added where total was
3. Recalculate the total          → old_total + sum(new_items)
4. Write the new Total row        → after all new data rows
```

### Full implementation (via `build_service` — bridge has known bugs)

```python
from tools.gws_auth import build_service

service = build_service("sheets", "v4", service_name="google-draas")
sheet_id = "1lIMvlVR8w-_LgsbRg3FfthveVr5EX0j-0-mDLmR33JQ"

# 1. Read current data
result = service.spreadsheets().values().get(
    spreadsheetId=sheet_id, range="Sheet1"
).execute()
values = result.get('values', [])
last_row = len(values)  # 0-indexed

# 2. Extract old total (last row, column E)
old_total = int(values[-1][-1]) if values[-1][-1] else 0

# 3. Clear old total row (row is 1-indexed for API)
service.spreadsheets().values().clear(
    spreadsheetId=sheet_id,
    range=f"Sheet1!A{last_row}:F{last_row}"
).execute()

# 4. Prepare new entries matching column structure
new_entries = [
    ['', 'KDR Medical - CT Pulmonary Angiogram (Manipal Hospital)', '18.07.2026', 'Credit card', '16000', ''],
    ['', 'KDR Medical - Blood Tests (Manipal Hospital)', '18.07.2026', 'Credit card', '9840', ''],
    # ... more rows
]

# 5. Append new data in place of old total
service.spreadsheets().values().update(
    spreadsheetId=sheet_id,
    range=f"Sheet1!A{last_row}:F{last_row + len(new_entries) - 1}",
    valueInputOption="USER_ENTERED",
    body={"values": new_entries}
).execute()

# 6. Write new total row
new_total = old_total + sum(int(e[4]) for e in new_entries)
service.spreadsheets().values().update(
    spreadsheetId=sheet_id,
    range=f"Sheet1!A{last_row + len(new_entries)}:F{last_row + len(new_entries)}",
    valueInputOption="USER_ENTERED",
    body={"values": [['', '', '', 'Total', str(new_total), '']]}
).execute()
```

## Common Expense Categories

### KDR Medical
Forwarded messages typically arrive in one of two formats:

**Format A — Nishant's message to Eshwari (structured):**
```
<procedure> — Rs <amount>
<procedure> — Rs <amount>
Total today: Rs <total>
Dr. KDR   Rs <total>
Cr. NDR   Rs <total>
```

**Format B — Invoice list (simpler):**
```
<item> — Rs <amount>
<item> — Rs <amount>
Total: Rs <total>
```

### Regular Bills
Simple single-line items passed as text between forwarded blocks:
- `Act Bill : <amount>`
- `Bescom Bill for <month> <amount>`
- `Paid to <name> :<amount>`

## Entry Standards

| Field | Convention |
|-------|-----------|
| Item | `KDR Medical - <procedure> (<hospital>)` for medical; plain name for bills |
| Payment Date | Use today's date (DD.MM.YYYY) unless user specifies otherwise |
| Mode | `Credit card` if uncertain (default for medical); `Cash` for small payments to individuals |
| Remb Status | Leave blank for new entries |

## Pitfalls

### Add ALL items the user lists — never silently omit

When the user provides a multi-item list (mix of forwarded message blocks + inline text items), every single item is meant to be added. **Do not skip items because they look like duplicates** of existing sheet rows.

**Real case (Jul 2026):** User sent:
```
Act Bill : 1414
Bescom Bill for June 7281
Paid to Maggi :2200
```
An existing row already had `Act Bill | 1414 | 08.06.2026`. The assistant skipped the new Act Bill entry assuming it was the same — the user followed up with "where act bill". **Rule:** if the user lists it as a new item, add it. They may be submitting a bill for a different month, or confirming it needs to be entered. Add a note in the description if the date is uncertain (e.g. `Act Bill for July 2026`), but never drop it.

**Explicit listing over pattern matching:** When the user forwards multiple message blocks and then lists items inline, the inline list takes priority. If there's overlap between a forwarded block's total and the inline items, add every inline item individually — the user is curating what goes in.
