# Lead Intake & Team Forwarding Workflow

When a property/land lead comes in via message (WhatsApp, Telegram, email) from a broker/agent/owner, the end-to-end workflow involves three steps: capture → store → forward to team.

## Trigger
- User receives a message about a land/property for sale, JV, or development
- "Add this to my contacts"
- "Forward to Prakash"
- Any property solicitation from an external broker/agent

## Step 1 — Check the NDR DRAAS Contacts Sheet First

**Always check for existing entries before adding.** The user may have already received a message from this person under a different name or project.

```python
from tools.gws_auth import build_service
sheets = build_service("sheets", "v4", telegram_id="ndr")
SHEET_ID = "1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g"
RANGE = "'NDR DRAAS Google contacts.csv'"

result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID, range=f"{RANGE}!A:AI"
).execute()
rows = result.get('values', [])

# Search by name and company
target_name = "manohar"
target_company = "vishal enterprises"
for i, row in enumerate(rows):
    name = (row[0] + ' ' + row[1] + ' ' + row[2]).lower() if len(row) > 0 else ''
    org = row[10].lower() if len(row) > 10 else ''
    if target_name in name or target_company in org:
        print(f"FOUND at row {i+1}: {row[:5]}")
```

## Step 2 — Add to NDR DRAAS Contacts Sheet

Use the **append** method (auto-extends sheet). Never write to a row beyond grid limits — use `insertDataOption='INSERT_ROWS'`.

**Column map (critical — off-by-one is the most common bug):**

| Col | Index | Field | Value |
|-----|-------|-------|-------|
| A   | 0     | First Name | Person's first name |
| B   | 1     | Middle Name | Initial (G) |
| K   | 10    | Organization Name | Company name |
| L   | 11    | Organization Title | Designation |
| O   | 14    | Notes | Full message + timestamp |
| Q   | 16    | Labels | `"* myContacts"` |
| R   | 17    | E-mail 1 - Label | `"* Work"` |
| S   | 18    | E-mail 1 - Value | Email address |
| AH  | 33    | Phone 1 - Label | `"Mobile"` |
| AI  | 34    | Phone 1 - Value | Phone number |

**⚠️ Pitfall:** Col K (index 10) is Organization Name, NOT Col J (index 9). Col J is "File As". Writing company name to index 9 is the most common bug.

**⚠️ Pitfall:** Phone numbers starting with `+` cause `#ERROR!` in sheets with `valueInputOption='USER_ENTERED'`. Use `valueInputOption='RAW'` when writing phone numbers.

```python
new_row = [""] * 93  # 93 columns A-CO
new_row[0] = "Manohar"           # A - First Name
new_row[1] = "G"                 # B - Middle Name
new_row[10] = "Vishal Enterprises"  # K - Organization Name
new_row[11] = "Complete Real Estate Solutions"  # L - Title
new_row[14] = "Full message including the property details, contact info, and --- Received: [Date] via [Channel]."
new_row[16] = "* myContacts"
new_row[17] = "* Work"
new_row[18] = "manohar@vishalestates.in"
new_row[33] = "Mobile"
new_row[34] = "9513215555"

sheets.spreadsheets().values().append(
    spreadsheetId=SHEET_ID,
    range=f"{RANGE}!A:CO",
    valueInputOption='USER_ENTERED',  # Use RAW for phone numbers with +
    insertDataOption='INSERT_ROWS',
    body={'values': [new_row]}
).execute()
```

**Important:** The contacts sheet is NOT Google Contacts (People API). They are separate stores that do NOT sync. If the user asks "was this added to my Google contacts?", the answer is: "No — it was added to the NDR DRAAS contacts spreadsheet only. To add to Google Contacts as well, I'd need to use the People API."

## Step 3 — Add to Land Proposals Sheet

If the lead involves a specific land/property (not just a service provider), also add it to the `land_proposals` sheet in the same spreadsheet.

**Schema (`land_proposals` tab):**

| Col | Field |
|-----|-------|
| A   | canonical_name |
| B   | aliases |
| C   | voice_misspellings |
| D   | location |
| E   | entity |
| F   | associated_contacts |
| G   | associated_projects |
| H   | status |
| I   | notes |
| J   | conversation_history |

Set status to `"New Lead"` for unreviewed leads.

```python
values = [[
    "Magadi Road - 30 Acres (Vishal Enterprises)",  # canonical_name
    "Magadi Road NICE Road|Vishal Enterprises 30 Acres",  # aliases
    "",              # voice_misspellings
    "Magadi Road, near NICE Road Junction, Bangalore",  # location
    "",              # entity
    "Manohar G|Prakash Singh",  # associated_contacts
    "",              # associated_projects
    "New Lead",      # status
    "Detailed notes about the property and contact",  # notes
    "Received [Date]. [Person] ([Company]) reached out about [property]. [Assignee] for follow-up."  # conversation_history
]]

sheets.spreadsheets().values().append(
    spreadsheetId=SHEET_ID,
    range="land_proposals!A:J",
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body={'values': values}
).execute()
```

## Step 4 — Generate WhatsApp Link for Team Member

After storing the lead, create a pre-filled WhatsApp message for the assigned team member (typically Prakash Singh for land leads).

**Team member phone numbers (from users.json):**

| Person | Phone | WhatsApp Link Base |
|--------|-------|-------------------|
| Prakash Singh | +919900093816 | `https://wa.me/919900093816?text=` |
| Nishant Ranka | +919880055634 | `https://wa.me/919880055634?text=` |
| Bharat Hawaldar | +919900029200 | `https://wa.me/919900029200?text=` |

**Message template for Prakash (land lead follow-up):**

```
Hi Prakash,

A lead came in today from [Contact Name] at [Company] ([email] / [phone]). [He/She]'s representing [details about the property].

Please connect with [Contact Name], collect all relevant information:
• Exact survey numbers and location
• Title documents and encumbrance
• Owner details and pricing expectations
• Any existing approvals or layout plans
• Site photos/videos

Share what you gather with me once done.
```

**Generating the link:**

```python
import urllib.parse

msg = """Lead message text with instructions for the team member"""
encoded = urllib.parse.quote(msg)
wa_link = f"https://wa.me/919900093816?text={encoded}"
```

**Delivery:** Present the link and the message preview in your response. The user clicks the link or copies the message.

## Step 5 — Confirm with User

After completing all steps, present a clear summary:

```
✅ Added [Name] to NDR DRAAS contacts sheet (row X)
✅ Added to land_proposals as "New Lead"
🔗 WhatsApp link for Prakash: [link]
```

If the user asks about Google Contacts specifically, explain: "This was added to the contacts **spreadsheet** only. Google Contacts (People API) is a separate system — they don't sync automatically. I can add to Google Contacts too if you'd like, or you can continue using the spreadsheet as your master list."

## Common Pitfalls

- **Contacts sheet vs Google Contacts:** The NDR DRAAS contacts sheet is a CSV-format spreadsheet. It is NOT linked to the native Google Contacts app (contacts.google.com). When the user asks "my contacts," they may mean either — ask or clarify.
- **Land proposals sheet doesn't auto-expand:** If append fails with "exceeds grid limits," it means the sheet has hit max rows. Use `append()` with `insertDataOption='INSERT_ROWS'` which auto-extends.
- **Phone with `+` in USER_ENTERED:** Sheets interprets `+` as a formula prefix. Use `RAW` mode or strip the `+`.
- **Organization Name column confusion:** Col K (idx 10) is Org Name. Col J (idx 9) is File As. Very easy to write to the wrong column.
- **WhatsApp link too long:** If the message is very long, provide the link AND a separate markdown code block of the message text so the user can copy-paste.
