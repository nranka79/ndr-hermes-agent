# Extracting Data from Scanned DTCP Layout Plan PDFs

When a user uploads a scanned DTCP layout plan approval PDF (Tamil Nadu, typically in Tamil + English), extract plot area, survey numbers, and layout details.

## Challenge

DTCP layout plans are **scanned image PDFs** — no text layer. `pdftotext` returns empty. The document is typically single-page, A3/A2 size, with:
- Top section: Approval order in Tamil (DTCP letterhead, date, reference number, conditions)
- Middle section: Layout plan with numbered plots, road widths, survey boundaries, reserved areas
- Bottom section: Signatures, seals, date stamps

## Extraction Workflow

### Step 1: Convert PDF to High-Res PNG

```bash
python3 -c "
import pymupdf
doc = pymupdf.open('layout_plan.pdf')
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=200)
    pix.save(f'layout_p{i+1}.png')
"
```

### Step 2: Crop Into Sections

The full-page image is large (e.g., 1700×2200 px). Crop into functional zones:

```python
from PIL import Image
img = Image.open('layout_p1.png')
w, h = img.size

# Top third — approval text
img.crop((0, 0, w, h//3)).save('top.png')
# Middle third — layout plan + table
img.crop((0, h//3, w, 2*h//3)).save('mid.png')
# Bottom — signatures
img.crop((0, 2*h//3, w, h)).save('bot.png')
# Left half of middle — details area
img.crop((0, h//3, w//2, 2*h//3)).save('details.png')
# Right half — table/legend
img.crop((w//2, 0, w, 2*h//3)).save('table.png')
```

### Step 3: Analyze Each Section with vision_analyze

```python
vision_analyze(image_url='/tmp/top.png', question='...')
vision_analyze(image_url='/tmp/mid.png', question='...')
vision_analyze(image_url='/tmp/details.png', question='...')
```

### What to Look For

| Section | What to Extract |
|---------|-----------------|
| **Top (approval text)** | DTCP reference number, date, approving authority, total extent, conditions |
| **Middle (layout plan)** | Survey numbers (புல எண்), plot numbers, road widths (in meters), reserved areas (TANGEDCO, OSR park), plot dimensions |
| **Bottom (signatures)** | Approval date, signatory name, seal |
| **Table/legend** | Area breakup table (if present): total extent, plotted area, roads, OSR, amenities |

### Common Layout Features

- **Survey numbers**: Labeled `புல எண்:158/1C8` (Tamil for "Survey No")
- **Road widths**: `10.00 மீ மனைப்பிரிவு சாலை` (10.00 m layout road)
- **Plot dimensions**: In meters along plot boundaries
- **OSR**: Open Space Reservation (green hatched, labeled `பூங்கா-1` = Park-1)
- **TANGEDCO**: Area reserved for Tamil Nadu electricity board
- **Prohibited construction**: `3.00 மீ அகல கட்டுமானம் கட்ட தடைசெய்யப்பட்ட பகுதி`
- **Conditions (நிபந்தனைகள்)**: Numbered list of approval conditions

### Data Mapping

Once extracted, map to the spreadsheet:

| DTCP Plan Data | Spreadsheet Field |
|----------------|-------------------|
| Survey numbers | Survey Numbers (Phase 1) |
| Total extent | Total Land Area |
| Plot dimensions | Used to calculate plot sizes |
| Road widths | For understanding layout quality |
| Reserved areas | For calculating plottal % (deductions) |

### Limitations

- **OCR quality is poor** for Tamil text — the vision model may produce garbled text. Cross-reference with the user's stated land area and survey numbers from legal documents.
- **Area breakup table may not be present** in the uploaded image — the full A3 print may have it on a separate sheet or in a different scan.
- **User's stated plottal %** (e.g., "63%") is more reliable than trying to calculate from an incomplete OCR extraction.
- If the user says "just assume 63%", use that rather than struggling with poor OCR.

## Key Fields to Extract

```python
# From the OCR + user confirmation
survey_numbers = "Sy 158/1C3, 158/1C4, 158/1C6, 158/1C8, ..."
plot_numbers = "6 to 130 (not all consecutive)"
road_widths = "10.00m, 9.00m, 7.20m"
reserved_areas = "TANGEDCO, Park-1 (OSR), 3.00m prohibited construction zone"
```

## Pitfalls

- `pdftotext` returns **empty** for scanned image PDFs — always use pymupdf + image conversion
- The Tamil OCR is often garbled — don't trust raw OCR output for exact numbers
- The layout plan may cover MORE land than Phase 1 — check survey numbers against user's stated Phase 1 extent
- `from PIL import Image` requires Pillow (`uv pip install Pillow` if missing)