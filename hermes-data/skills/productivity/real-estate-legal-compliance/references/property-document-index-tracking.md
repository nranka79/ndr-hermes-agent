# Property Document Index Tracking — Google Sheet Workflow

**Trigger:** DRAAS team member (Bharat, Nishant, etc.) shares an image/PDF of a handwritten or printed document index for a property project and asks to create or update a tracking sheet.

**Recurring pattern — Dharwad (Ranka Stello) File No. 1, 2, 3, IV** — multiple sessions over consecutive weeks. This is not a one-off.

## Pipeline

### Phase 1 — Read the Index Image

The user uploads a photo/scan of a document index. Extract document names via:

1. **vision_analyze** on the raw image (best for handwritten or mixed-layout indexes)
2. **tesseract CLI** fallback (`tesseract image.jpg stdout -l eng --psm 6`) if vision fails
3. Up-scale with PIL (`Image.resize(width*3, height*3), Image.LANCZOS`) before OCR for small images

### Phase 2 — Check for Existing Sheet

Search Drive for an existing document index spreadsheet for the same property:

```python
drive = build_service("drive", "v3")
results = drive.files().list(
    q="name contains 'Document Index' and trashed=false",
    fields="files(id, name, owners)"
).execute()
```

Check ownership — if the sheet was created by another user (e.g., `ndr@draas.com`), the current user (`sales1.blr@draas.com`) may not have write access. In that case:

- Option A: Share the sheet with the current user via Drive API (requires owner-level permission — often blocked)
- Option B: **Create a new combined sheet** under the current user's account: read all data from the read-only source, then write to a new sheet

### Phase 3 — Google Sheet Structure

**Columns (standard for DRAAS property document indexes):**

| Col | Header |
|-----|--------|
| A | SI No. |
| B | Particulars (document description) |
| C | Document No. (e.g., registration number like `2940/2013-14`) |
| D | Date |
| E | Original / Photocopy |
| F | Handed Over (Yes/No) |
| G | Remarks |

**Section headers** use a merged row across A:G (e.g., "FILE NO. 1", "FILE NO. 2", "FILE NO. 3 — RANKA STELLO (DHARWAD)", "FILE NO. IV"). Blank rows between sections for readability.

### Phase 4 — Handle Multi-File-Number Indexes

Property document indexes are often organized by file number (File No. 1, 2, 3, IV, etc.). Each file number represents a category of documents:

- **FILE NO. 1** — Title chain (Sale Deeds, Trust Deeds, MOUs)
- **FILE NO. 2** — Agreements (JDA, GPA, Sharing Agreements, Addendums)
- **FILE NO. 3** — Regulatory/Statutory (Fire NOC, Plan Sanction, Water Supply NOC, HDMC correspondence)
- **FILE NO. IV** — Revenue records (Mutation, RTC, EC, Extract)

When a user provides a new file number, **append it to the existing sheet** rather than creating a new one.

### Phase 5 — Write Data

Use the Sheets API `update()` pattern with explicit row range (NEVER `append()`):

```python
from tools.gws_auth import build_service

sheets = build_service("sheets", "v4")

# Read current rows to find the next empty row
result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range="'SheetName'!A1:G200"
).execute()
existing = result.get("values", [])
next_row = len(existing) + 2  # +1 for blank separator, +1 for data start

# Write using update (NOT append)
sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range=f"'SheetName'!A{next_row}:G{end_row}",
    valueInputOption="USER_ENTERED",
    body={"values": data_rows}
).execute()
```

### Sheet Create (with Drive Link)

```python
# Create spreadsheet
created = sheets.spreadsheets().create(
    body={"properties": {"title": title}, "sheets": [{"properties": {"title": tab_name}}]},
    fields="spreadsheetId"
).execute()
spreadsheet_id = created["spreadsheetId"]

# Get Drive link
drive = build_service("drive", "v3")
meta = drive.files().get(fileId=spreadsheet_id, fields="webViewLink").execute()
link = meta["webViewLink"]
```

### Phase 6 — Notify User

Share the Google Sheet link and a summary table of what was added:
- Which file number(s) are in the sheet
- How many documents per section
- Which columns are still blank (waiting for user to fill Original/Photocopy, Handed Over, Remarks)

## Pitfalls

- **Sheet owned by another user** — Writing to Nishant's sheet from Bharat's account gives 403. Must create a new sheet under the current user's account and copy data over.
- **Inline string cells** — XLSX files may store text as `inlineStr` (not shared strings). The raw XML parser must handle both. Prefer Google Sheets API over openpyxl when possible.
- **The index image often has partially legible text** — cross-reference dates and document numbers from context (e.g., a 1948 sale deed makes sense for File No. 1; a 2015 MOU for File No. 2).
- **Section headers need merged cells** — Use `mergeCells` in the Sheets create request or manual merging after write (not critical — the header text in col A alone is readable).
- **Empty rows between sections** — Insert blank `[]` lists between sections for readability.

## Dharwad Ranka Stello — Verified Structure

| Section | Docs | Theme |
|---------|------|-------|
| FILE NO. 2 | 14 | Agreements (Girija Devi / AHFIL) — MOU, JDA, GPA, Sharing, Addendums |
| FILE NO. 1 | 10 | Title chain — Sale Deeds (1948–2013), Trust Deed (1945), MOUs |
| FILE NO. 3 — RANKA STELLO (DHARWAD) | 16 | Regulatory — Fire NOC, Plan Sanction, Water Supply, HDMC correspondence |
| FILE NO. IV | 6 | Revenue — Mutation, RTC (1967–2013), EC (1948–2013), Extract, Plan Sanction receipts, HDDA correspondence |
