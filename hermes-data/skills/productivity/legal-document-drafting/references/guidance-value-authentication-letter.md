# Guidance Value Authentication Letter — Sub-Registrar

Letter template for requesting current guidance value from the Sub-Registrar's office, required before property registration and stamp duty computation.

## Standard Letter Structure

**From:** [Company Name] with Registered Address
**To:** The Sub-Registrar, [Office Jurisdiction — e.g., Shivajinagar, Bangalore]
**Subject:** Request for Authentication of Current Guidance Value — [Property Identifier]

### Required Property Description Table

| Particulars | Details |
|---|---|
| Plot/Old No. | [e.g., Plot No. 1‑B / House List No. 156] |
| Khata No. | [Current + previous khata numbers if changed] |
| BBMP PID | [13‑digit PID number] |
| Locality | [Layout, Village, Hobli, Taluk, District] |
| Dimensions | [E‑W × N‑S in metres or feet] |
| Approach Passage | [Width × Length, direction, road access] |
| Total Approx. Area | [sq.ft / sq.mtr] |

### Boundaries Table

| Direction | Abutting Property |
|---|---|
| East | [property details] |
| West | [property details] |
| North | [property details] |
| South | [property details] |

### Known Missing Info Pattern

Company Registered Address is NOT available from generic letter drafts — must be sourced separately:
- From ITR documents found on Drive (naming pattern: "DRA Realty ITR Statement of Income P&L Balance Sheet Auditor Report FY 20XX 20XX.pdf" under sales1.blr@draas.com)
- From MCA records
- From the user directly

### Drive ITR Search Pattern

```python
service = build_service('drive', 'v3')
# Primary query:
results = service.files().list(
    q="name contains 'ITR' and fullText contains 'DRA Realty'",
    pageSize=20
).execute()
# Or by exact file naming convention:
results = service.files().list(
    q="name contains 'DRA Realty ITR Statement of Income'",
    pageSize=20
).execute()
```

ITR PDFs are typically scanned (image-based), 23-27 pages. OCR needed for company address extraction.

## Key Property Doc Conventions

- Plot No. → House List No. → Khata No. history → BBMP PID convey the chain of municipal identification
- Dimensions: East‑West first, then North‑South (standard Indian convention)
- Approach passage described separately with its own dimensions
- Boundaries use cardinal directions with abutting property names
