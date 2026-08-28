# Adding WhatsApp Links to a Lead Sheet

A common recurring task at DRAAS: read phone numbers from an existing lead tracking sheet, generate `wa.me` links, and write them to a designated "Whats App Link" column — without modifying any other data.

## When to use this

- User says "add a WhatsApp link column to my sheet"
- User points to a sheet with phone numbers and wants clickable wa.me links
- User shows you a sheet that already has a "Whats app Link" header column and wants it populated

## Workflow

1. **Identify the sheet tab name** — What the user calls it may differ from the API name

   ⚠️ The sheet tab name in Google Sheets is **case-sensitive** via the API. The URL's `gid=` parameter doesn't show the exact name. Always probe with a single-cell read first if you're unsure of casing:
   ```python
   # Probe — try with the name as-is from the URL
   try:
       data = call('sheets_get', service_name='google-draas',
                   sheet_id=SHEET_ID, range="'Exact Sheet Name -Tab'!A1:A1")
   except:
       # Try lowercase variants — Google's URL encoding preserves case but the
       # actual tab might differ from what the user typed in the link
       data = call('sheets_get', service_name='google-draas',
                   sheet_id=SHEET_ID, range="'exact sheet name -tab'!A1:A1")
   ```

2. **Get all data** — Read the full range including all columns to see headers and phone numbers. Use `A1:K` or whatever range covers both phone column and target column.

3. **Build the WhatsApp link column values** — For each data row:
   - Extract the phone number (usually column E, index 4)
   - Clean it: strip spaces/dashes/parentheses, remove leading `+` or `0`, ensure it starts with `91`
   - Generate: `https://wa.me/{cleaned_phone}`
   - Preserve the header row text

4. **Write only the target column** — Use `sheets_update` with a range limited to the target column only (e.g., `'Sheet'!K1:K600`). This ensures no other columns are modified.

## Complete script pattern

Run via terminal with the Hermes venv:

```bash
cd /opt/hermes && /opt/hermes/.venv/bin/python3 -c "
import sys, json
sys.path.insert(0, '/opt/hermes')
from tools.gws_skill_bridge import call

# 1. Read the full sheet
data = call('sheets_get', service_name='google-draas',
            sheet_id='SPREADSHEET_ID',
            range=\"'Sheet Tab'!A1:K600\")
rows = json.loads(data)

# 2. Build wa.me links for column K
k_values = []
for i, row in enumerate(rows):
    if i == 1:
        # Header row — keep existing header
        k_values.append([row[10] if len(row) > 10 and row[10] else 'Whats app Link'])
    elif len(row) >= 5 and row[4] and row[4].strip():
        phone = row[4].strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if phone.startswith('+'): phone = phone[1:]
        elif phone.startswith('0'): phone = '91' + phone[1:]
        elif not phone.startswith('91') and len(phone) == 10: phone = '91' + phone
        k_values.append([f'https://wa.me/{phone}'])
    else:
        k_values.append([''])

# 3. Write only column K
result = call('sheets_update', service_name='google-draas',
              sheet_id='SPREADSHEET_ID',
              range=\"'Sheet Tab'!K1:K\" + str(len(k_values)),
              values=json.dumps(k_values))
print('Updated:', result)
"
```

## Key parameters for `sheets_update` via gws_skill_bridge

| Parameter | Value | Notes |
|-----------|-------|-------|
| `sheet_id` | Spreadsheet ID from URL | NOT `spreadsheet_id` — the bridge maps kwargs to SimpleNamespace, and the function expects `args.sheet_id` |
| `range` | `'Sheet Tab'!K1:K{n}` | Must match actual sheet tab name exactly (case-sensitive) |
| `values` | `json.dumps(k_values)` | Must be JSON-serialized! A Python list will not work |
| `service_name` | `'google-draas'` | Resolved via `gws_resolve_account` |

## Common pitfalls

### Sheet name mismatch
The URL's `gid=` parameter hides the actual tab name. The tab name in the browser URL fragment shows what the user typed, but Google normalizes it. If you see `Unable to parse range`, try:
- Different casing (the tab might be lowercase even if the URL shows uppercase)
- Trimming spaces or special characters

### Phone number edge cases
- Some entries have `+` (`+919845107169`) — strip it
- Some start with `0` (`09845107169`) — replace `0` with `91`
- Some have spaces/dashes (`919845 107169`, `91-9845-107169`) — strip all non-digits
- Empty rows between data — skip rows with no phone number

### Sheets update ≠ append
`sheets_update` **replaces** the entire range you specify. This is fine for writing to a single column — you're telling it the exact cells to overwrite. But never use it to write to a range that overlaps with data you want to preserve.

### Only modify the target column
Always limit the range to the exact column you're updating (e.g., `K1:K600`). Do NOT use a multi-column range like `A1:K600` — that would overwrite all columns.
