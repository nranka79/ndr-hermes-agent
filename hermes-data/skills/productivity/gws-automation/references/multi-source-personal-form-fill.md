# Multi-Source Personal Form Filling (Sheets)

When a user shares a Google Sheet link and says "fill this with my details," use a systematic multi-source approach before asking them for missing info. This reduces back-and-forth and catches facts already available from their conversation history.

## Workflow

### Step 1: Read the Sheet Structure

Use `gws_auth.build_service("sheets", "v4")` (per-user OAuth — personal sheets require user auth, not SA DWD).

```python
from tools.gws_auth import build_service

sheets = build_service("sheets", "v4")
spreadsheet_id = extract_id_from_url(url)  # between /d/ and /edit

# Get sheet names
meta = sheets.spreadsheets().get(
    spreadsheetId=spreadsheet_id,
    fields='sheets.properties'
).execute()

# Read all data
result = sheets.spreadsheets().values().get(
    spreadsheetId=spreadsheet_id,
    range="'Sheet Name'!A1:ZZ200"
).execute()
values = result.get('values', [])
```

**Key question:** Which column is the label and which is the value? In one session, column A was the field label, column B was the fill-in value. This varies per form — always print the header structure first.

### Step 2: Map Labels to Columns

Print the full structure (all columns per row) to understand the mapping:

```python
for i, row in enumerate(values):
    parts = [f"{chr(65+j)}='{val}'" for j, val in enumerate(row)]
    print(f"Row {i+1}: {' | '.join(parts)}")
```

Look for section headers (e.g., "EMPLOYER DETAILS", "SOURCE OF FUNDS") — they're labels, not fillable fields.

### Step 3: Fill from Memory First

Memory stores stable user facts: name, email, phone, country, employer, role, family members. Fill what you know immediately on first pass — before searching anything.

### Step 4: Search Past Sessions for Personal Details

**This is the key technique.** Before asking the user for missing personal data, search past conversations:

```python
session_search(query="Roshni OR Ruhaan OR wife OR son OR family", limit=3)
session_search(query="marital OR spouse OR married", limit=3)
```

Common gaps that session_search fills:
- **Marital status** and **spouse name** — often mentioned in family/household contexts
- **Children names** — mentioned in education, immigration, or parenting conversations
- **Visa details** — immigration-related discussions mention visa type and status
- **Property details** — real estate discussions mention addresses, properties owned
- **Employer details** — job/role mentioned in business contexts

**Example:** The user didn't provide their spouse or children's names directly. `session_search(query="Roshni Ruhaan family")` returned a past session showing wife's name and son's name, filling Marital Status and Dependents fields.

### Step 5: Search Email/Drive (If User Explicitly Asks)

Only do this if the user says "search my email/drive for more info" or "use everything you can find." Delegate to subagents for parallel search:

```python
delegate_task(
    goal="Search Gmail for EB-5 related emails with personal details",
    toolsets=["terminal"]
)
delegate_task(
    goal="Search Drive for EB-5 related documents with personal info",
    toolsets=["terminal"]
)
```

**Caveat:** Background delegates may not return during the same session. Don't block on them — fill what you have from earlier steps and note the gaps.

### Step 6: Batch Update the Sheet

Use `values().batchUpdate()` (not individual `update()` calls) for efficiency:

```python
body = {
    "valueInputOption": "USER_ENTERED",
    "data": [
        {"range": "'Sheet'!B1", "values": [["Nishant Ranka"]]},
        {"range": "'Sheet'!B2", "values": [["ndr@draas.com"]]},
    ]
}
result = sheets.spreadsheets().values().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body=body
).execute()
```

### Step 7: Verify and Present Gap Analysis

Read the sheet back and produce a clear filled/empty summary. Format as a markdown table of what was filled, plus a bullet list of empty fields with specific questions.

### Step 8: Ask About Remaining Gaps

Group empty fields thematically. Don't dump all at once — lead with the most important gaps. Ask specific questions rather than "what's missing?"

### Drive Passport/Resume Scanning for Personal Details

When the user says "use everything you can find," search Drive for passport and resume PDFs — naming conventions often reveal key data:

```python
# Find visa expiry from filename
visa_files = drive.files().list(
    q="name contains 'US Visa' and name contains 'NDR' and trashed=false",
    fields="files(id, name)"
).execute()
# File "NDR Passport US Visa Exp 20280813.pdf" → visa expires Aug 2028

# Find resume for DOB
resume_files = drive.files().list(
    q="name contains 'Resume' and name contains 'Nishant' and trashed=false",
    fields="files(id, name)"
).execute()
# Export as text → DOB found in first few lines

# Find children/family members from passport files
passport_files = drive.files().list(
    q="name contains 'Passport' and trashed=false",
    fields="files(id, name)"
).execute()
# Names like "Ruhaan Passport v2.pdf" and "Rivaan Passport v2.pdf" reveal dependents
```

**Pattern:** Look for `"<Name> Passport"`, `"<Name> US Visa"`, `"<Name> Resume"` files. Filenames often contain expiry dates. Export Google Docs as `text/plain` to parse DOB from content.

**Pitfall — Don't assume file naming convention matches current status.** A file named "NDR Passport US Visa Exp 20280813.pdf" is strong evidence, but always present it to the user for confirmation — the visa may have been renewed or extended since the file was saved.

### Source of Funds Structuring for Financial/Immigration Forms

When filling financial source-of-funds sections for EB-5 applications or similar:

1. **Current asset form over historical origin.** List what the funds currently are (Stocks, Property Sale), not where they originally came from (Gift). This keeps documentation simpler.

2. **Gift from a deceased parent — DON'T list as "Gift from Parents".** If you list a category like "Gift from Parents," the reviewer (USCIS etc.) will ask for the *donor's* source documentation. If the donor is deceased, producing tax returns and bank statements from a deceased person is complex or impossible. Instead:
   - List the gift amount under its current form (e.g., "Stocks" if the gift was invested in a brokerage account)
   - Explain the gift origin in the cover letter / source-of-funds narrative, not as a line item
   
3. **Company equity as "Others" or narrative.** Large company valuations (e.g., $20-30M in family companies) are better presented as evidence of overall net worth and earning capacity, not as a direct source line item for a specific investment amount. The form asks for the source of the *investment amount*, not the entire asset base.

4. **When the user says "self-earned under Others":** Map this by putting "Self-earned" in the value column of the "Others" row. There's often no separate description column — the row label is fixed as "Others" and the value column doubles as description entry.

### Address: Company Office ≠ Residential Address

A common pitfall: memory may store the user's company address but not their home address. Always distinguish:

- Company address (e.g., "Prism Towers, Kalinga Road, Bangalore") → only use as placeholder, flag explicitly
- Residential address often found in past sessions (authorization letters, agreements, delivery addresses)

Search for `session_search(query="address OR residence OR home OR Embassy OR Habitat OR apartment", limit=3)` before asking the user.

**Example:** User's address found in a past Roma Ventures authorization letter: "#1503, Embassy Habitat, No.59 Palace Road, Bangalore - 560 001"

## Pitfalls

- **Phone number `+` prefix.** Sheets may strip `+` sign in USER_ENTERED mode. Use `"'+"` prefix apostrophe (e.g., `"'+919880055634"`) or use `STRING_VALUE` rendering mode to force text treatment.
- **Amount formatting.** Bare integers appear unformatted (`1500000` → hard to read). Use `"$1,500,000"` strings in USER_ENTERED mode for readability. But note: this makes the cell text, not a number — fine for form-filling.
- **Don't guess addresses.** Company offices ≠ residential addresses. Always flag placeholders explicitly and search for the real one.
- **Don't block on background delegates (email/Drive search).** Fill what you have from memory + sessions + confirmation, and present the gaps. Delegates may return late — merge their findings in a follow-up update.
- **Don't use SA DWD for personal sheets.** The user's personal EB-5 spreadsheet needs `gws_auth.build_service("sheets", "v4")` — OAuth, not SA. Using SA will fail or write to the wrong account.
- **Batch updates are faster than single-cell updates.** One `batchUpdate()` call with a `data` array is more efficient than N individual `update()` calls.
