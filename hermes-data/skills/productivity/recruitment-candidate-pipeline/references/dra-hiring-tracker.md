# DRA Hiring Tracker — Absorbed Workflow Details

This skill (`dra-hiring-tracker`) has been absorbed into `recruitment-candidate-pipeline` as its content was nearly identical (both cover resume intake → Drive → master sheet for DRAAS).

## Key Specifics from dra-hiring-tracker

### Drive Folder
- **Folder:** `DRA Hiring - Resumes` — folder ID: `18nyMns_2KYbJhhLMsyQ3fR3G5lWxzlyv`
- Data owner: Bharat Hawaldar (sales1.blr@draas.com, TG: sales1.blr)

### Master Sheet
- **File:** `DRA_Hiring_Master_Sheet.xlsx`
- Columns: `# | Name | Position | Email | Phone | Experience | Education | Skills | Resume Link | Remarks / Daily Follow-up`

### Phone Format (Bharat Preference)
- `91XXXXXXXXXX` — NO `+` symbol
- WhatsApp hyperlink: `https://wa.me/91{digits[-10:]}`
- Colour: green (`#075E54`), underlined

### Public Sharing
- ALWAYS set "Anyone with the link" reader permission on both the folder and every uploaded file:
```python
drive.permissions().create(
    fileId=f["id"],
    body={"type": "anyone", "role": "reader"},
    fields="id"
).execute()
```

### Resume Text Extraction
- **PDF:** `fitz.open(path).get_text()` — if empty, `ocrmypdf --force-ocr --language eng`
- **DOCX:** `zipfile` + XML extraction from `word/document.xml`
- Phone extraction: `re.sub(r'\D', '', phone_raw)` → last 10 digits

### Sheet Update Pattern
- Download existing `DRA_Hiring_Master_Sheet.xlsx` from Drive
- Append new row with `openpyxl`
- Delete old sheet via Drive API, upload new version
- Set public sharing on uploaded sheet too
