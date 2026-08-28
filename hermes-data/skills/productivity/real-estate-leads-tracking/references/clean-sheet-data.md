# Cleaning Lead Data in Sheets

Two common cleaning operations when normalizing Indian real estate lead sheets before Kelsa import or outreach.

## 1. Phone Format: Standardize to `91XXXXXXXXXX`

Bharat's preferred format: **12 digits, no `+`**, no brackets/dashes/spaces.

**Source formats you'll encounter:**
- `(+91)-9488813596` — most common
- `+919488813596`
- `9488813596` (no country code)
- `91 9488 1359 6` (spaces)
- `(+91)-9488813596(Verified)`
- `+91 94888-13596`

**Regex normalization:**
```python
import re

def clean_phone(raw: str) -> str:
    """Strip all non-digits, ensure 91 prefix."""
    digits = re.sub(r'\D', '', raw.strip())
    if len(digits) >= 12:
        # Already has country code — take last 12 digits (91 + 10-digit number)
        formatted = '91' + digits[-10:]
    elif len(digits) >= 10:
        # 10 digits — prepend 91
        formatted = '91' + digits[-10:]
    elif len(digits) == 0:
        formatted = ''
    else:
        # Partial number — prepend 91 anyway
        formatted = '91' + digits
    return formatted

# Examples:
# clean_phone('(+91)-9488813596') → '919488813596'
# clean_phone('+919488813596')    → '919488813596'
# clean_phone('9488813596')       → '919488813596'
# clean_phone('')                 → ''
```

**Sheet update (single shot):**
```python
# Read all rows, convert col B, write back
result = sheets.spreadsheets().values().get(
    spreadsheetId=sid, range='Sheet1!A1:B140'
).execute()
rows = result.get('values', [])

converted = []
for r in rows:
    name = r[0].strip() if len(r) > 0 else ''
    phone_raw = r[1].strip() if len(r) > 1 else ''
    digits = re.sub(r'\D', '', phone_raw)
    formatted = '91' + digits[-10:] if len(digits) >= 10 else '91' + digits
    converted.append([name, formatted])

# Fix header row manually (the formula above turns 'Contact' into '91')
if converted[0][1] == '91':
    converted[0][1] = 'Contact'

body = {'values': converted}
sheets.spreadsheets().values().update(
    spreadsheetId=sid, range='Sheet1!A1:B140',
    valueInputOption='USER_ENTERED', body=body
).execute()
```

## 2. Name Cleaning: Remove Bracket Annotations

Indian real estate leads often have role labels appended to the name:
- `Harsh (Owner)`
- `C (Broker)`
- `John peter (Broker)`
- `appu (Owner)`
- `Thanuja (Owner)`
- `P Narender (Owner)`
- `Pramod Mahajan g (Owner)`

**Regex removal:**
```python
import re

def clean_name(name: str) -> str:
    """Strip any (parenthetical annotations) from a name."""
    return re.sub(r'\s*\(.*?\)\s*', '', name).strip()

# clean_name('Harsh (Owner)')           → 'Harsh'
# clean_name('John peter (Broker)')     → 'John peter'
# clean_name('P Narender (Owner)')      → 'P Narender'
# clean_name('Raju Hiremath (Owner)')   → 'Raju Hiremath'
# clean_name('Ramamurthy')              → 'Ramamurthy'  (no change)
```

The pattern `\s*\(.*?\)\s*`:
- `\s*` — optional whitespace before/after brackets
- `\(.*?\)` — non-greedy match inside brackets (handles nested-like text but not actual nesting)
- Works on any annotation: `(Owner)`, `(Broker)`, `(Co-owner)`, `(Builder)`, etc.

**Sheet update (single shot, column A only):**
```python
result = sheets.spreadsheets().values().get(
    spreadsheetId=sid, range='Sheet1!A1:A140'
).execute()
rows = result.get('values', [])

cleaned = []
for r in rows:
    name = r[0].strip() if r else ''
    cleaned_name = re.sub(r'\s*\(.*?\)\s*', '', name).strip()
    cleaned.append([cleaned_name])

body = {'values': cleaned}
sheets.spreadsheets().values().update(
    spreadsheetId=sid, range='Sheet1!A1:A140',
    valueInputOption='USER_ENTERED', body=body
).execute()
```

## 3. Kelsa-Export Format → Clean (TailorTalk / WhatsApp upload)

Kelsa lead exports (or sheets whose rows were copied from Kelsa) come in a composite format:
- Lead column: `Name-["phone"]-date` e.g. `RaviKantGupta-["919580269381"]-2026-08-22` (sometimes `["+91…"]`)
- Contact column: `["phone"]` or `["+phone"]` e.g. `["919130411705"]`

The clean upload format (TailorTalk / Meta-rules WhatsApp lists, what Sheet1 of Bharat's Camp Magic list used) is **Lead = name only**, **Contact = plain `91XXXXXXXXXX`** — no brackets, quotes, dashes, `+`, or date suffix.

**Verified parser (Aug 2026, 249/249 rows):**
```python
import re

LEAD_RE = re.compile(r'^(.*?)-\["(\+?\d+)"\]-\d{4}-\d{2}-\d{2}$')

def clean_kelsa_row(lead: str, contact: str):
    m = LEAD_RE.match(lead.strip())
    if not m:
        return None  # flag unparsed rows, don't guess
    name = re.sub(r'\s+', ' ', m.group(1)).strip()   # collapse double spaces in names
    phone = m.group(2).lstrip('+')                   # 91XXXXXXXXXX, no +
    # cross-check: contact column must match phone parsed from the lead column
    cont_m = re.match(r'^\["(\+?\d+)"\]$', contact.strip())
    if cont_m and cont_m.group(1).lstrip('+') != phone:
        return ('MISMATCH', name, phone, contact)
    return (name, phone)
```

**Pitfalls:**
- **Names legitimately contain spaces AND double spaces** (`Ali N/A`, `mouni  N/A`, `Kumar  A`) — collapse `\s+` → single space but KEEP the name as-is otherwise; don't drop `N/A`.
- **Validate 12-digit length after strip** (`^91\d{10}$`). An 11-digit number like `Sumaiya -> 91552302879` (source `["+91552302879"]`) is a source typo — flag it to the user, don't silently rewrite.
- Always **cross-check the contact column against the phone parsed from the lead column** (both should carry the same number).

**Sheet update (single shot):** read `Sheet2!A1:B1000` → transform rows → `values().update` back to `A1:B{len}` with `valueInputOption="RAW"`. Do NOT write to Sheet1 — it's already the clean reference format.

## When to use

Apply these operations BEFORE:
- Importing leads into Kelsa Pipeline 10 (clean data prevents dedup failures)
- Generating WhatsApp links (clean names look professional in the message)
- Appending to a master lead sheet (consistent format across sources)
- Running the batch import script (`batch_import_leads.py`)

## Order of operations

1. Clean names first (no brackets)
2. Normalize phones second (standardize `91XXXXXXXXXX`)
3. Then dedupe (phone is the primary key)
4. Then Kelsa import or WhatsApp outreach