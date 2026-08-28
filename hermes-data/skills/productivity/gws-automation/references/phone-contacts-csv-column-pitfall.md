# Google Contacts CSV Export — Phone Column Pitfall

## The problem

The NDR DRAAS Google contacts sheet (`1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`) is a full Google Contacts CSV export with **53 columns**. If you only read columns A–Z (cols 0–25), you **will miss all phone numbers**.

## Column layout

| Col range | Header | What's there |
|-----------|--------|-------------|
| A–Z (0–25) | First Name → E-mail 5 - Label | Identity, org, notes, labels, email addresses ONLY. No phone data. |
| AA–AB (27–28) | Phone 1 - Label / Phone 1 - Value | **Primary phone number** |
| AC–AD (29–30) | Phone 2 - Label / Phone 2 - Value | Alternate phone |
| AE–AM (31–38) | Phone 3–6 Label + Value | Additional numbers |
| AN–BA (39–53) | Address 1–2 fields | Address data |

## Detection

If a row has data in the Notes column (O, col 14) or Labels column (Q, col 16) but you see no phone number — you probably didn't read far enough.

**Test:** Check `len(header)` — a full read should return 53 columns. If it returns 26 or fewer, the range was too narrow.

## Fix

```python
# WRONG — misses cols 27+
result = sheets.spreadsheets().values().get(
    spreadsheetId='1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g',
    range="'NDR DRAAS Google contacts.csv'!A1:Z500"
)

# RIGHT — reads all 53 columns
result = sheets.spreadsheets().values().get(
    spreadsheetId='1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g',
    range="'NDR DRAAS Google contacts.csv'!A1:BA500"
)
```

Then check columns 27+ for phone data:

```python
row = result.get('values', [])[n]  # nth row
phone_label = row[27] if len(row) > 27 else ''  # e.g. "Mobile"
phone_value = row[28] if len(row) > 28 else ''  # e.g. "+91 9972042131"
```

## Context

The NDR CONTACTS sheet (`1fYa-t2RY1siy2qBgAH8uu_Jd2chjJ716BbcpxilpOK0`) is a hand-maintained structured table with columns: SL.NO, NAME, COMPANY, DESIGNATION, ADDRESS, TELEPHONE, FAX, MOBILE. That one's columns are obvious (MOBILE is column H). The CSV export sheet is the one with the hidden-column trap.
