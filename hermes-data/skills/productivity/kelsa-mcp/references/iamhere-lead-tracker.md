# I Am Here — Lead Tracker Sheet (Bulk Lead Creation)

Source for batch lead creation into Pipeline 10 (DRA Sales Leads). Maintained by Nikhil at I Am Here and shared with Bharat H at DRAAS.

## Sheet Location

- **File ID:** `1yaUwSos6DO56Oni2iiVJ0L26K-rRn7wzYsHKweNxUB0`
- **Name:** "Ranka x IamHere - Lead tracker"
- **Owner:** nikhil@iamhere.app

## Sheet Tabs

| Tab Name | Purpose | Rows | Columns |
|----------|---------|------|---------|
| Dashboard | Statistics summary (lead counts by stage) | ~37 rows | A-L |
| **Ranka Udaya \| July** | **Actual lead data** | 1101 rows, frozen header | A-Z (26 cols) |
| Ranka Udaya - Meta | Meta/additional data | 1659 rows | A-Z |

## Column Mapping ("Ranka Udaya | July" tab)

| Col | Header | Notes |
|-----|--------|-------|
| A | Lead ID | Kelsa lead ID (e.g. `6a42847e13ad1ddb97aef11e`) |
| B | Lead Date | Timestamp |
| C | When would you like to schedule a site visit? | Text (e.g. "Next Weekend", "I need more details first") |
| D | What investment amount are you comfortable with? | Text (e.g. "₹ 50 L+") |
| E | **Full name** | Customer name |
| F | **Email** | Customer email |
| G | **Phone number** | Phone — **without `+` prefix** (e.g. `917502108480`, `919900571093`) |
| H | City | City name |
| I | Status | Lead status in tracker (e.g. "Fresh", "Qualified") |
| J | Next Followup | Follow-up date |
| K | Notes | Notes field |
| L | Last Synced | Sync timestamp |
| M | Sync Status | "synced" or empty |

## Lead Data Row Count

- **Header is row 1** (frozen)
- Data starts at row 2
- Leads are numbered by their row in the tab, NOT by Lead ID
- When Bharat says "lead number 660", data row 660 = sheet row 661

## Bulk Lead Creation Workflow (Confirmed Jul 2026)

For each lead:

1. **Read the row** using Sheets API:
   ```python
   from tools.gws_auth import build_service
   service = build_service('sheets', 'v4', service_name='google-draas')
   result = service.spreadsheets().values().get(
       spreadsheetId='1yaUwSos6DO56Oni2iiVJ0L26K-rRn7wzYsHKweNxUB0',
       range="'Ranka Udaya | July'!A{row}:M{row}"
   ).execute()
   ```

2. **Extract fields:**
   - Name = col E
   - Email = col F  
   - Phone = col G **as-is** (sheet has `917502108480` format — already has `91` prefix, DO NOT add `+`)
   - Source = `"I Am Here Software Labs"` (constant)
   - SourceDetails = `"Meta"` (constant)
   - Channel = `"DigitalAds"` (constant)
   - Project = `"Ranka udaya"` (constant)

3. **Create contact** in pipeline **3429** WITH phone (use phone as-is from sheet, no `+` prefix):
   ```python
   create_lead(pipeline_id=3429, field_values={
       "cf_contact": {"name": name, "phone": phone, "email": email}
   })
   ```
   ⚠️ **Critical:** Phone from the sheet naturally has no `+` prefix. This works perfectly. DO NOT add `+` — that causes ghosting. DO NOT omit phone — contacts created without phone ghost immediately.

4. **Create lead** in pipeline **10** referencing contact by ID:
   ```python
   create_lead(pipeline_id=10, field_values={
       "cf_contact1": {"id": contact_id},
       "cf_source": "I Am Here Software Labs",
       "cf_sourcedetails": "Meta",
       "cf_campaign": "DigitalAds",
       "cf_project": "Ranka udaya"
   }, name=name)
   ```

5. **Verify** with `get_draft_status(draft_id)` then `get_lead(lead_id)`.

## Known Issues

- **Phone WITHOUT `+` prefix works:** Creating contacts in 3429 with phone like `"919036520138"` (no `+`) keeps the contact accessible and readable. The pipeline 10 lead shows Contact Phone populated and Masking auto-populated with `91`.
- **Phone WITH `+` prefix causes ghosting:** Contacts created with `"+919036520138"` ghost immediately. The contact ID still resolves in pipeline 10 but the phone field stays empty.
- **Compound object on pipeline 10 fails consistently:** Attempting `cf_contact1: {"name", "email", "phone"}` directly at pipeline 10 creation returns "Invalid master value for Contact" every time. Always use the two-step workflow above.
- **`create without phone, update later` does not work:** Even contacts created WITHOUT phone can ghost, making the phone field unsettable after creation. Always include phone (no `+` prefix) at creation time.
- **Ghost contacts block values:** If a contact was created with a phone (+ prefix), then ghosted, that phone number is permanently locked in Kelsa and cannot be reused.
