# Project Note Sheet from Multi-Document Uploads

Create a consolidated project note sheet (Google Doc) by analyzing multiple uploaded real estate project documents — progress reports, approved plans/site plans, floor plans, renders, and photos.

## When to use

- User uploads a batch of real estate project files (progress report, approved plan, floor plan renders, photos)
- User says "analyze these files and create a note sheet"
- User asks for a single-page project summary with key specs extracted from supporting documents

## Workflow

### Step 1 — Identify and classify files

The user may upload files via Telegram. Check both caches:

```python
import glob, os
doc_files = glob.glob("/data/hermes/document_cache/*")
img_files = glob.glob("/data/hermes/image_cache/*")
```

Classify each file into one of:
- **Progress report** — weekly/monthly dashboard (text-based PDF, use `pdftotext -layout`)
- **Approved plan / site plan** — dimensional site layout (image-based PDF or text)
- **Floor plan** — architectural floor plan with room layout, area statements, parking counts
- **Render** — 3D visualization / concept image
- **Photo** — construction site photo
- **Approval / Sanction document** — government approval, building licence

### Step 2 — Extract data by file type

**From weekly progress reports** (`pdftotext -layout <file> -`):
- Project name, location, site area, BUA, saleable area, floor count
- Type (Commercial / Residential)
- Budget (approved, committed, paid, outstanding)
- Milestone completion percentages
- Start / finish dates, delays, catchup plan

**From approved plans / site plans** (`pdftoppm -jpeg -r 200` → `vision_analyze`):
- Plot dimensions, plot area, FSI / allowable FSI
- Parking requirements vs achieved (cars + bikes)
- Stilt floor area, typical floor area, total FSI area
- Building height, architect details, drawing date

**From floor plans** (same rendering approach):
- Per-floor plinth/carpet/saleable areas
- Office/unit breakdown
- STP features (fresh air duct, exhaust duct)
- Amenity spaces (lobby, terrace, AHU rooms)

### Step 3 — Compile the note sheet

A Google Doc in the project's Drive folder containing:

**Project Identity** — name, location, developer, architect, completion date
**Site & Building** — site area, BUA, saleable area, floors, type, FSI, STP design info
**Parking** — achieved vs required (cars + bikes)
**Power Backup** — (flag if not found)
**Sanction Details** — approval date, reference number, authority
**Budget & Progress** — budget, completion %, start/finish, delays

**Excluded** (per DRAAS convention): lease premium, estimated sale value/rate, construction cost, total cost, CF loan, rental potential, approval status detail (just "Fully Approved" + STP info)

### Step 4 — Upload to Drive

1. Confirm target folder with user
2. Create Google Doc in that folder
3. Return Drive link

## Tools

| Tool | When |
|------|------|
| `pdftotext -layout <file> -` | Text-based PDFs (progress reports, some approvals) |
| `pdftoppm -jpeg -r 200 <file> <out>` | Image-based PDFs → render for vision |
| `vision_analyze(image_url=...)` | Rendered JPEGs and uploaded images |
| `drive.files().create()` | Upload to Drive |

## Pitfalls

- **vision_analyze may fail on original uploaded images** — render via pdftoppm first, the JPEG is more likely to work
- **pdftotext on site plans** returns jumbled dimension lines but usable area/parking numbers
- **Parking data** is on the stilt floor plan, rarely in the progress report
- **Power backup** rarely in standard plans/progress reports — tell the user
- **Confirm folder with user** before uploading
- **Naming convention**: YYYYMMDD_ProjectName_DocumentType_Description.pdf (date = document content date)
