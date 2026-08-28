# Gandhinagar Mamatha Apartments — Dark Store Location Research

**Date:** 2026-07-15
**Property:** No. 14, Mamatha Apartments, 3rd Cross, 4th Main Road, Gandhinagar, Bengaluru – 560009
**Coordinates:** 12.977716°N, 77.577864°E
**Use case:** Dark store / quick commerce leasing outreach

## Workflow

### 1. Extract property photos from email

Property outreach emails sent by Prakash Singh to BigBasket, Blinkit, Swiggy contained a "Space for Rent.pdf" attachment with photos and floor plans.

**Technique:** Use the Gmail API via `tools.gws_auth.build_service("gmail", "v1")` to get full message payload, check `payload.parts` for attachments with `mimeType=application/pdf` and an `attachmentId`, then download via `users().messages().attachments().get()`.

```python
from tools.gws_auth import build_service
import base64

service = build_service("gmail", "v1", service_name="google-draas")
msg = service.users().messages().get(userId="me", id=MSG_ID, format="full").execute()

for part in msg["payload"]["parts"]:
    if part.get("filename", "").endswith(".pdf"):
        att_id = part["body"]["attachmentId"]
        att = service.users().messages().attachments().get(
            userId="me", messageId=MSG_ID, id=att_id
        ).execute()
        data = base64.urlsafe_b64decode(att["data"])
        with open("output.pdf", "wb") as f:
            f.write(data)
```

### 2. Extract images from the PDF

```bash
pdfimages -all input.pdf /output/dir/img
```

The Gandhinagar PDF had 10 images: 3 floor plans (basement, ground floor, building plan) and 6 JPG photos (exterior, interior empty halls, showroom entrance).

### 3. Resolve Google Maps short link to coordinates

```bash
curl -sI "https://maps.app.goo.gl/SgJZ9JT75GBFWhta6" | grep -i location:
```

Returns: `https://www.google.com/maps/place/12.977716,77.577864/...`

### 4. OpenStreetMap / Overpass location research

Query within 1km radius for:
- Amenities (schools, hospitals, supermarkets, restaurants, banks)
- Land use (residential, commercial areas)
- Transit nodes (bus stops, railway stations)
- Road hierarchy (primary, secondary, trunk roads)

Results from this query for Gandhinagar:
- **Shopping:** DMart, Grand Majestic Mall, Janata Bazaar
- **Education:** Central College, UVCE, Maharani's College, Orchids International
- **Healthcare:** Mallige Medical Centre, Sreeniwasa Hospital, ESI Hospital
- **Banks:** SBI, Axis, ICICI, Bank of Baroda, CSB Bank
- **Roads:** Kempegowda Road (primary), Palace Road, Sheshadri Road, Old Mysuru Road, Tank Bund Road

### 5. HTML design for location page

Used a **dark theme** (tailwind-inspired, not the navy-gold DRAAS brand) because this was for a quick commerce outreach, not investor brochure. Design features:

- 1200px fixed width page vs A4 — allows for richer layout
- Gradient slate background with subtle radial glow accents
- Card-based grid layout (2-column, full-width for important sections)
- **Delivery coverage rings** card (10/20/30 min radius)
- **Dark store suitability scores** as gradient progress bars
- **High-density residential catchment** with density bar visualization (stacked horizontal bars)
- **Clickable Google Maps link** as a styled button

Key CSS patterns used:
```css
@page { size: 1200px; margin: 0; }  /* custom width instead of A4 */
.page { width: 1200px; min-height: 2000px; }
.suitability-track { background: rgba(148,163,184,0.1); border-radius: 4px; }
.suitability-fill { background: linear-gradient(90deg, #3b82f6, #8b5cf6); }
```

### 6. Convert to PDF with WeasyPrint

```bash
cd /opt/data && uv run python3 -c "
from weasyprint import HTML
HTML('input.html').write_pdf('output.pdf')
"
```

**Note:** Use `uv run python3` rather than the venv path — it reliably finds the installed weasyprint package.

### 7. Merge with existing PDF

```bash
uv pip install pypdf
```

```python
from pypdf import PdfReader, PdfWriter

existing = PdfReader("existing.pdf")
new_page = PdfReader("location_page.pdf")
writer = PdfWriter()
for p in existing.pages: writer.add_page(p)
for p in new_page.pages: writer.add_page(p)
writer.write("merged.pdf")
```

### 8. Drive upload & share

Uploaded to **Gandhinagar Mamta** folder (ID: `1DPZ3gw_cGY5FpuFYhZwqjFjPICG1ypQK`) — not TMP, since this is a finalized folder for this property. Shared with Prakash Singh (psingh@draas.com) as reader.

Deleted the old version before uploading the new one — Drive has no overwrite semantics.

## Dark store evaluation summary for Gandhinagar

| Factor | Score | Notes |
|--------|-------|-------|
| Location Centrality | 95% | Heart of Bangalore, near Vidhana Soudha/MG Road |
| Residential Density | 90% | 1M+ catchment in 20min radius |
| Road Connectivity | 92% | Multiple primary roads, 2km to Majestic |
| Space Config | 85% | 3,200sqft basement + 2,000sqft GF + mezzanine potential |
| **Overall** | **90%** | Prime city-centre dark store location |

## Pitfalls encountered

1. **`weasyprint` not in PATH** — `uv run python3` instead of calling the binary directly
2. **Overpass query syntax** — initial query with `~"regex"` on amenity failed silently; switched to `around:1000` with explicit categories
3. **pypdf not in base venv** — had to `uv pip install pypdf` first
4. **Drive no-overwrite semantics** — must delete old file before uploading new one with same name
5. **Google Maps short link resolution** — can't extract coordinates from the short URL without following redirects; use `curl -sI` to resolve
