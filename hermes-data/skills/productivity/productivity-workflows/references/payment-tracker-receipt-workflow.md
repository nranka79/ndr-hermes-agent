# Payment Tracker & Receipt Management (Real Estate)

A recurring workflow for managing real estate plot payment tracking sheets, adding transfer entries from screenshots, generating receipts/messages for clients, and preparing client outreach WhatsApp messages with project info + location + document links.

## Project Name Aliases (Phonetic → Actual)

DRAAS real estate projects have multiple phonetic and marketing names. When user says one, map to the actual project:

| User says (phonetic) | Actual project name | Sheet/file name |
|---|---|---|
| "Rankau", "Ranka Udyya", "Rankav" | **Ranka Udyan** (also marketed as Serenity) | Serenity Hill View |
| "Sanity State" | **Serenity Estate** / Serenity State | — |
| "Chirchiganapalini" | **Chichuraganapalli, Tamil Nadu 635103** | Location for Serenity Estate |
| "Ranca" | **Ranka** (DRA Ranka / DRA Group entity) | — |

**Client name aliases:** The user may refer to clients phonetically (e.g., "Rankau" = a client named Rankau). Cross-check against Transfer Details sender names and Payment Tracker investor names before assuming it's the project name.

## Session Memory Gap — Handling "we discussed this yesterday"

The user frequently expects you to recall details from a prior conversation (yesterday or same week). If you can't find the session via `session_search`:

1. **Search broadly first** — try multiple query variations (phonetic spellings, project names, phone numbers)
2. **If not found, acknowledge honestly** — don't pretend or fabricate what you might have said
3. **Ask for the specific missing piece(s)** — frame it as "I need these 1-2 things to proceed" rather than asking them to re-explain everything
4. **Save immediately upon receiving** — once they reshare, commit to memory or a local note so the next lookup works

**Best practice to avoid this:** When the user shares a location link, document link, or project detail, note it in your response and consider saving to memory (for stable facts like location links, project aliases, client phone numbers).

## Trigger

User shares a Google Sheets link to a **Payment Tracker** spreadsheet containing:
- **Payment Tracker tab** — plot #, investor name, advance, balance, receipt status
- **Transfer Details tab** — transaction log (date, amount, sender, receiver, mode, ref no, status)
- **Plot & Client Info tab** — plot specs (area, facing, UDS), applicant names, PAN/Aadhar Drive links

## Workflow

### 1. Initial Sheet Reading

```python
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4')

# Discover exact sheet names (trailing spaces are common!)
ss = sheets.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
for s in ss.get('sheets', []):
    p = s['properties']
    print(repr(p['title']))  # ALWAYS use repr() — names may have trailing spaces
```

**⚠️ PITFALL — Sheet names with trailing spaces:** The Sheets API is strict — `'Transfer Details '` ≠ `'Transfer Details'`. If the actual name has a trailing space and your range doesn't, you get `HttpError 400 "Unable to parse range"`. Always use `repr()` to discover the exact name.

### 2. Adding Transfer Entries (from payment screenshots)

When user shares a payment screenshot:

```python
# 1. Extract details from screenshot using vision (amount, sender, date, ref no, plot #)
# 2. Determine next Sl. No from existing data
# 3. Append row
new_row = [sl_no, plot_no, date, time, amount, sender, receiver, mode, ref_no, status]
sheets.spreadsheets().values().append(
    spreadsheetId=SHEET_ID,
    range="'Transfer Details '!A:J",
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body={'values': [new_row]}
).execute()
```

**Common data to extract from Indian bank payment screenshots:**
- **UPI/NEFT/RTGS** — Date, time, amount, sender name, transaction/reference ID
- **Sender name** may appear as account holder name or UPI ID
- **Status** — usually "Successful" or "Pending"

### 3. Marking Receipt Done

After adding the transfer entry and/or generating a receipt, update the **Receipt Done** column (usually Column J) in the Payment Tracker tab:

```python
# Find the row for the plot/investor
result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range="'Payment Tracker '!A:J"
).execute()
rows = result.get('values', [])
for i, row in enumerate(rows):
    if i == 0: continue  # header
    # Match by plot number or investor name
    if str(row[0]) == plot_no:
        row_num = i + 1  # 1-indexed
        # Update Receipt Done column (col J = index 9)
        sheets.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'Payment Tracker '!J{row_num}",
            valueInputOption='USER_ENTERED',
            body={'values': [['Yes']]}
        ).execute()
        break
```

### 4. Generating Receipts

**Receipt format options (confirm with user which they prefer):**

| Format | Use Case | Delivery |
|--------|----------|----------|
| Chat message (plain text) | Quick WhatsApp share | Code block for copy-paste |
| HTML with styling | Professional-looking receipt | Drive upload or share link |
| PDF | Formal printed receipt | Drive upload |

**Typical receipt content:**
- Receipt # / Sl. No
- Date of payment
- Project name (e.g., "Serenity Hill View")
- Plot number
- Customer name
- Amount paid (in words + figures)
- Payment mode (NEFT/RTGS/UPI)
- Transaction/Reference number
- Received by (e.g., "Manohar Singh" or "DRA Ranka")
- Balance remaining (if applicable)
- Thank you note

### 5. Client WhatsApp Message Preparation

When user provides a client's WhatsApp number and asks to send project details:

```python
# Prepare a comprehensive message with:
# ✅ Project overview (from Plot & Client Info tab)
# ✅ Location link (Google Maps — search for the project)
# ✅ DG2 / brochure link (if user provides)
# ✅ Payment schedule or receipt (if applicable)
```

**User preference (Bharat H):** Provide the message in a code block for easy copy-paste. The user will send it themselves via WhatsApp.

**WhatsApp link format:** Use `https://api.whatsapp.com/send?phone=91XXXXXXXXXX&text=...` (URL-encoded message) — but confirm with user; some prefer manual copy-paste to avoid truncated links.

**Location link:** Search Google Maps / OSM for the project name + area, use short Google Maps link.

For Serenity Estate / Serenity Hill View, the known Google Maps location is:
- **Serenity Estate, Chichuraganapalli, Tamil Nadu 635103**
- Maps link: `https://www.google.com/maps/search/Serenity+Estate+Chichuraganapalli+Tamil+Nadu+635103`

### Complete Client Outreach Message Structure

When the user provides a client's phone number and asks to "prepare details" for them, build a comprehensive WhatsApp message with these sections:

1. **Project introduction** — "Serenity Hill View" (or Ranka Udyan), location overview
2. **Plot/payment details** — specific to this client (from Payment Tracker: plot no, total, balance, etc.)
3. **Location link** — Google Maps link for Serenity Estate
4. **Document links** — DG2 / brochure links (if user has shared them)
5. **Call to action** — invite them to visit or contact

**User preference (Bharat H):** Provide the final message in a code block for copy-paste to WhatsApp. The user sends it manually. If the user also shares payment screenshots during the same conversation, process those immediately and incorporate into the message.

**Bharat's copy-paste preference:** Code blocks are the preferred format — NOT clickable wa.me links that may truncate. He wants the exact message text he can paste into his WhatsApp chat with the client.

### DG2 / Ancillary Document Links

When the user mentions "I have shared DG2 link" or similar document references:
- Search current session and prior sessions via `session_search` for the link
- If not found, ask the user to reshare it — don't guess or skip it
- Once reshared, incorporate the link directly into the WhatsApp message
- Note: DG2 is a specific document/brochure link the user keeps and references

## Known Edge Cases

- **Incomplete rows in Transfer Details:** Some rows may have empty Sl. No or Plot NO (e.g., additional payments by same customer added without renumbering). Clean up by detecting empty cells and filling logically.
- **Missing receiver names:** Some entries only have account holder masked ("XXXX7377") — flag to user for confirmation.
- **Amount formatting:** Sheet may use Indian format (1,00,000) or plain numbers (100000). Be consistent when appending.
- **Sheet tab names with trailing spaces:** Extremely common with XLSX-imported sheets. Always use `repr()` to discover exact names.
