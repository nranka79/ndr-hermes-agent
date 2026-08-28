# DRAAS Contacts Sheet — Query Pattern

The NDR DRAAS Google Contacts sheet (`1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`) stores 90+ columns of contact data exported from Google Contacts. Use it to look up phone numbers, email addresses, organizations, and relationship notes for people who may not appear in Gmail search.

## Sheet Structure

The sheet has 93 columns (0-indexed). Key columns:

| Index | Header | Purpose |
|-------|--------|---------|
| 0 | First Name | Person's name |
| 2 | Last Name | Surname |
| 10 | Organization Name | Company/org |
| 11 | Organization Title | Role/title |
| 14 | Notes | Free-text notes about the contact |
| 16 | Labels | myContacts, RelA, SocialB, etc. |
| 17 | E-mail 1 - Label | Label for first email |
| 18 | E-mail 1 - Value | Primary email address |
| 19 | E-mail 2 - Label | Label for second email |
| 20 | E-mail 2 - Value | Secondary email |
| 27 | Phone 1 - Label | "Mobile", "Work", etc. |
| 28 | Phone 1 - Value | Primary phone number |
| 29 | Phone 2 - Label | Label for second phone |
| 30 | Phone 2 - Value | Secondary phone |
| 39 | Address 1 - Label | Address type |
| 40 | Address 1 - Formatted | Full address |

## Query Pattern

```python
from tools.gws_auth import build_service
svc = build_service('sheets', 'v4')

SHEET_ID = '1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g'
TAB = "NDR DRAAS Google contacts.csv"

result = svc.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range=f"'{TAB}'!A:IR",  # Read all columns
    majorDimension='ROWS'
).execute()

for row in result.get('values', []):
    if len(row) > 0 and 'search term' in row[0].lower():
        name = row[0] if len(row) > 0 else ''
        phone = row[28] if len(row) > 28 else ''  # Phone 1 - Value
        email = row[18] if len(row) > 18 else ''  # E-mail 1 - Value
        org = row[10] if len(row) > 10 else ''     # Organization Name
        notes = row[14] if len(row) > 14 else ''   # Notes
```

## Common Lookups

- **Ashok Kumar** — row[0]="Ashok Kumar", org="DRA Muthanallur Land Partners", phones at [28] and [30]
- **Mamta Rathod** — row[0]="Mamta Rathod", email at [18]="mamatadr@gmail.com", also at [20]="maadi32@gmail.com"
- **Ranjeeth Rathod** — row[0]="Ranjeeth Rathod", multiple emails across columns 18-26

## Appending a New Contact

Use `spreadsheets().values().append()` with `USER_ENTERED` value input option and `INSERT_ROWS` insert option:

```python
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4')

SHEET_ID = '1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g'
TAB = "NDR DRAAS Google contacts.csv"

# Build a 93-column row (pad with empty strings)
row = [''] * 93

row[0]  = 'Balaji'          # First Name
row[2]  = 'Babu'            # Last Name
row[6]  = 'Mr.'             # Name Prefix
row[9]  = 'Balaji Babu J'   # File As
row[10] = 'VALBY'           # Organization Name
row[11] = 'Managing Partner / Director'  # Title
row[14] = 'Notes about contact'          # Notes
row[18] = 'email@example.com'            # E-mail 1 - Value
row[28] = '+91 99451 81771'              # Phone 1 - Value
row[40] = 'Full address string'          # Address 1 - Formatted
row[41] = 'Street address'               # Address 1 - Street
row[42] = 'Bengaluru'                    # Address 1 - City
row[44] = 'Karnataka'                    # Address 1 - Region
row[45] = '560095'                       # Address 1 - Postal Code
row[46] = 'India'                        # Address 1 - Country

result = sheets.spreadsheets().values().append(
    spreadsheetId=SHEET_ID,
    range=f"'{TAB}'!A:A",
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body={'values': [row]}
).execute()

print(f"Added to {result['updates']['updatedRange']}")
```

**⚠️ Always pad to 93 columns** — Google Contacts export format requires all columns to maintain alignment. Missing columns shift subsequent data.

## Pitfalls

- Case-insensitive matching on row[0] is safest (the sheet has mixed casing)
- Some entries have the full name in row[0] (e.g. "Ashok Kumar"), others split across First/Middle/Last (row[0]/row[1]/row[2])
- The sheet is a static export — not real-time synced with Google Contacts
- Row indices are 0-based; always guard with `len(row) > INDEX` before accessing
- When appending, always build a full 93-element list — short lists cause column misalignment
