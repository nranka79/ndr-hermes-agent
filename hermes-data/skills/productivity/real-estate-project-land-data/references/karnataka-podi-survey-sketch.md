# Karnataka Podi Survey Sketch (Podi ನಕ್ಷೆ)

**Status:** Interpreted from actual documents found on Drive, Jul 2026.
**Land:** Hurulagurki Village, Vijayapura Hobli, Devanahalli Taluk, Bengaluru Rural District.

## What is a Podi Sketch?

A **Podi** (Podi/ಪೋಡಿ) document is a Karnataka government survey record issued by the **Tahsildar's Office** that records the sub-division of a survey number (Sy No.) into smaller parcels. It includes a boundary sketch/map of the land parcel with measurements, adjacent parcels, and corner markers.

Also known in documents as: "Sketch", "Podi Sketch", "Print SketchImage", or "Survey Sketch". The Transaction Type field in the document shows "Podi".

## Key Information Found on a Podi Sketch

The document is a formal government record from the Karnataka Revenue Department. Here's what to look for:

### Header Section
- **Government Emblem** — Government of Karnataka at the top center
- **Issuing Authority** — Tahsildar's Office (ತಹಶೀಲ್ದಾರ್ ರವರ ಕಛೇರಿ), [Taluk Name]
- **Page Number** — typically Page No: 1
- **F Number** (ಎಫ್ ಸಂಖ್ಯೆ) — unique application number (e.g. 21030524796252)

### Land Identification Fields
| Field (Kannada) | Meaning | Example |
|---|---|---|
| ಸರ್ವೆ ನಂ | Survey Number | 93/2 (or 91/*/2) |
| Document Type | — | Sketch |
| ಜಿಲ್ಲೆ | District | ಬೆಂಗಳೂರು ಗ್ರಾಮಾಂತರ (Bengaluru Rural) |
| ತಾಲ್ಲೂಕು | Taluk | ದೇವನಹಳ್ಳಿ (Devanahalli) |
| ಹೋಬಳಿ | Hobli | ವಿಜಯಪುರ (Vijayapura) |
| ಗ್ರಾಮ | Village | ಹುರುಳಗುರ್ಕಿ (Hurulagurki) |
| ವಹಿವಾಟು | Transaction Type | Podi (sub-division) |
| ಅರ್ಜಿದಾರರ ಹೆಸರು | Applicant Name | — |
| ವಿಳಾಸ | Address | — |

### The Sketch Drawing (Central Visual Element)

The core of the document is a **geometric drawing** of the land parcel:

**Boundaries:**
- The parcel is drawn as an irregular polygon (often 4-6 sides)
- Thick black lines represent the property boundaries
- Each boundary is labeled with adjacent survey numbers or features:
  - ರಾ.ಭಂ. [No.] / ರಾ.ಸಂ. [No.] = Adjacent survey number
  - Examples: ರಾ.ಭಂ.92 (top boundary), ರಾ.ಸಂ.94 (left), ರಾ.ಸಂ.98 (bottom)

**Internal Features:**
- **Corner/Khuna Numbers** (ಖುಣ ನಂಬರ್): Small numbers (1, 2, 3, 4, 5...) at vertices — these are physical boundary markers placed on site
- **Internal division lines**: May show sub-divisions within the parcel
- **Labels like ರಾ.ಸಂ.3**: May indicate internal survey points or features
- **Nala/canal indicators**: Right-side boundary markings may indicate a Nala (drainage channel/stream) or pathway

**Orientation & Scale:**
- **North Arrow**: Standard arrow pointing up, usually to the right of the drawing
- **Scale Bar**: Text like "1cm:39.60mtrs" — 1cm on sketch = 39.60m on ground

### Bottom Section (Notes, Dates, Stamps)

Numbered notes in Kannada typically state:
1. "Boundary measurement work completed per Land Survey Department Order No. [F Number]"
2. "Boundary of Re. Survey No. [X] has been demarcated according to measurements in the original Tipni (field book) and Hissa Tipni (sub-division field book). Khuna numbers 1,2,3... determined by measurement. Present at site."
3. "There is no excess/shortage in this survey number." (measurements match records)

**Dates:**
- **ದಿನಾಂಕ** (Date of preparation): e.g. 15-05-2024
- **Valid Till**: Validity of the certified copy (e.g. 17-07-2025)

**Signatures:**
- **ತಯಾರಿಸಿದವರು** (Prepared by) — surveyor/official signature + stamp
- **ಸಹಿಪಡಿಸಿದವರು** (Signed by) — reviewing official
- **ಮೋಜಿಣಿ ನಿರ್ವಾಹಕರು** (Mojini Nirvahakaru — Survey Administrator/Manager)

## Related Document Types (also found on Drive)

| Term | Meaning | Search hint |
|---|---|---|
| **Akarband** / Aakarbandi | Land measurement/valuation sketch showing dimensions | Search "akarband" or "aakarbandi" |
| **Hissa** / Hissa Atlas | Sub-division atlas — shows how a survey number is split into sub-plots | Search "hissa atlas" or "hissa sketch" |
| **Tipni** / Tippani | Field book / survey notes — written records of measurements | Search "tipni" or "tippani" |
| **Podi** | Sub-division record (this document) | Search "podi" |
| **RTC** | Record of Rights, Tenancy and Crops (land ownership record) | Search "RTC" with survey number |

## How to Find These Documents on Drive

Use **multiple name variants** for the same piece of land — real estate land in India is often known by several names:

```python
searches = [
    # Trust/owner name
    ("Godwad", "Godwad Bhavan Jain Trust", "GBJT", "Godwad Bhawan"),
    # Project name
    ("Serenity Hillview", "Serenity Hill View"),
    # Village + survey number
    ("Hurulagurki", "Hurulugurki", "Hulgurki", "Hurlugurki"),
    ("93/2", "93(2)", "Sy No 93", "Sy No_93"),
    # Document type + survey
    ("sketch", "podi", "hissa", "akarband"),
]
```

**Technique:** Execute multiple `drive_search` calls with one keyword at a time. Cross-reference results. Documents matching the survey number under multiple name variants are likely the same land parcel.

## Pitfalls

- **Mixed Kannada/English OCR**: Vision analysis produces garbled OCR when Kannada script is present. Use the *visual description* mode of `vision_analyze` (set `also_describe_visually=True`) to get both OCR text AND visual descriptions of the sketch.
- **PDF must be converted to PNG** before `vision_analyze` can process it. Use: `pdftoppm -png -r 300 input.pdf /tmp/output_prefix`
- **Garbled OCR with "Page No: 1" header**: If vision_analyze returns mostly garbled text but mentions "Document Type: Sketch" and "Podi", the document IS a valid survey sketch — the OCR just struggles with the Kannada font. Trust the visual description.
- **Valid Till date may be in the past**: The sketch document itself is still a valid historical survey record. The "Valid Till" refers to the certified copy's validity, not the survey data.
- **Multiple PDF pages may be blank**: Government scans often include blank separator pages. Check all pages — the sketch is usually on the largest page.
- **"Print SketchImage" variations**: Files named "Print SketchImage Report.93-2" vs "Print SketchImage 93-2 new" may be different versions or copies of the same survey. Both are worth checking.
