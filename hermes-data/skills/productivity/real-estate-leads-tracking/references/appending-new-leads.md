# Appending New Leads to an Existing Tracking Sheet

After the initial lead sheet is created and uploaded, new leads come in regularly (daily/weekly). The workflow is **fetch → dedupe → append**, not create-from-scratch each time.

## Step 1: Check for new leads in Gmail

```python
gmail = build_service("gmail", "v1", telegram_id="sales1.blr")
result = gmail.users().messages().list(
    userId="me",
    q="(from:magicbricks.com) newer_than:2d",
    maxResults=50
).execute()
msgs = result.get("messages", [])
```

Use `newer_than:Nd` where N = days since last check. For daily checks, `newer_than:2d` gives a safety margin.

## Step 2: Parse + extract contact details

Same regex patterns as the initial extraction (see `magicbricks-parsing-notes.md`). Extract name, phone, email, property ID, property type, date.

## Step 3: Get existing leads from the Sheet

```python
sheets = build_service("sheets", "v4", telegram_id="sales1.blr")
result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range="A:I"  # all columns
).execute()
rows = result.get("values", [])

# Build set of already-tracked phones
existing_phones = set()
for row in rows[4:]:  # skip header rows
    if len(row) >= 6:
        existing_phones.add(row[5].strip())  # phone is column F
```

## Step 4: Dedupe new leads against existing

```python
new_entries = []
for lead in parsed_leads:
    is_new = lead["phone"] not in existing_phones
    # Always append (user said "capture all"), but flag duplicates
    new_entries.append({**lead, "is_new": is_new})
```

## ⚠️ PITFALL: `len(rows) + 1` is NOT the append row when the sheet has trailing whitespace

Sheets frequently have leftover blank/whitespace rows below the real data (e.g. a row `['', ' ']` from a previous edit or manual cleanup). `len(rows)` counts those, so `start_row = len(rows) + 1` can append hundreds of rows below the actual last entry, leaving a huge empty gap (verified Aug 2026: existing data ended at row 32 but `len(rows)+1` computed 683).

**Fix — scan for the last NON-EMPTY row, then append at last_non_empty + 1:**

```python
res = sheets.spreadsheets().values().get(spreadsheetId=SID, range="'Clients'!A1:B5000").execute()
values = res.get('values', [])
last_non_empty = 0
for i, row in enumerate(values, 1):
    if ''.join(row).strip():
        last_non_empty = i
start_row = last_non_empty + 1
```

Also clear any stray whitespace-only row (`'Clients'!A682:B682`) if it sits in the gap. If you DO append in the wrong place, clear the misplaced block with `values().clear(range="'Clients'!A683:B900")` then re-append — do not leave the gap.

## Verified destination: Bharat's WhatsApp campaign list sheet (Aug 2026)

When Bharat says "add the MagicBricks leads into the sheet I shared", the destination is the **WhatsApp client list** used for MB lead outreach:

- Sheet ID: `1eaOfED6TDNb3RnBkoj4ya4tH7gvLzrY_wiXa1KAXJaM` ("Camp_Magic_Client_WhatsApp_List_updated")
- Single tab: `Clients`
- Format: **2 columns only** — A = Lead name, B = Contact phone as `91XXXXXXXXXX` (no `+`, 12 digits)
- Append directly below the last existing entry; keep the same 2-column format; no headers, no # column
- Phone cleanup: strip `+`/spaces, prefix `91` if missing (same as PITFALL #4 in SKILL.md)

## Step 5: Calculate next row and sequence number

```python
last_no = 0
for row in rows[4:]:
    if row and row[0].isdigit():
        last_no = max(last_no, int(row[0]))
max_row = len(rows) + 1  # next available row

append_data = []
for i, lead in enumerate(new_entries):
    last_no += 1
    append_data.append([
        last_no, lead["date"], lead["name"], lead["type"],
        lead["email"], lead["phone"], lead["prop"], lead["prop_id"],
        f"📱 Chat with {lead['name']}"
    ])
```

## Step 6: Append to Sheet

```python
start_row = max_row
range_str = f"A{start_row}:I{start_row + len(append_data) - 1}"

sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range=range_str,
    valueInputOption="USER_ENTERED",
    body={"values": append_data}
).execute()
```

## ⚠️ PITFALL: Sheet ID is NOT always 0

When you create a new Sheet via Drive upload (xlsx → Google Sheets conversion), the default sheet's ID is **not 0**. It's a randomly assigned integer. Verified example:

```python
# Get actual sheet ID
ss = sheets.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
for s in ss.get('sheets', []):
    props = s.get('properties', {})
    print(f"Sheet: {props.get('title')} | ID: {props.get('sheetId')}")
# Output: Sheet: Site Visits | ID: 216711979
```

If you try `{"sheetId": 0}` on a converted sheet, you'll get:
```
HttpError 400: Invalid requests[0].insertDimension: No grid with id: 0
```

**Fix:** Always fetch the actual sheet ID first via `spreadsheets().get()`, then use that ID in batch requests.

For simple value appends (no batch formatting), the A1 range notation (`A65:I69`) works fine — no sheet ID needed.

## Step 7: Verify

```python
result = sheets.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=f"A{start_row}:I{max_row+len(append_data)-1}").execute()
```

## User preference: capture all, flag duplicates

Bharat's instruction (Jun 2026): *"capture all these leads in Excel sheet"* — meaning append every new lead email to the sheet, even if the phone/email already exists in it. The `is_new` flag is informational only; always add the row. This keeps a chronological record of repeat inquiries.

## User preference: upload to Drive root

When creating a *new* sheet (first time), upload to Drive root — not to a project-specific folder. Bharat explicitly said to keep it in *his* Drive and share the link. For subsequent appends, just update the existing sheet (its ID is already known).
