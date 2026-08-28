# Draft NOC Support Documents — Generation from Google Maps Data

**Skill:** `real-estate-legal-compliance`
**Category:** Pre-Construction NOC Documentation

## Trigger

User needs draft documents for NOC applications (Aviation Height Clearance, Fire NOC, BESCOM, BWSSB, etc.) and provides a Google Maps link or known coordinates of the property.

## Workflow

### Step 1: Extract Coordinates from Google Maps Link

The URL format is: `https://www.google.com/maps/place/[PlaceName]/@[LAT],[LNG],zoom/data`

Extract `@LAT,LNG` — e.g. from `@13.0898128,77.5828981,365m`:
- Latitude: 13.089813° N
- Longitude: 77.582898° E

Convert to DMS (Degrees, Minutes, Seconds):
```
Lat DMS = int(degrees)° int((degrees - int(degrees))*60)' (remaining*60)"
e.g. 13° 05' 23.33" N
```

### Step 2: Research Elevation

Search: `"[village/town] elevation height above sea level meters"`
- Yelahanka avg: ~915 m MSL
- Allalasandra Lake area: 891-949 m range, avg ~914 m

Cross-reference with topographic-map.com or Wikipedia for the locality.

### Step 3: Generate Documents (5 Drafts)

#### Document 1: GPS Coordinates Certificate
Fields:
- Project name, location, land area, survey/property ref
- GPS Coordinates table (Decimal Degrees + DMS for Lat/Long)
- Datum reference: WGS 84
- Site boundary coordinates note (to be measured by licensed surveyor)
- **Certification block:** Surveyor name, license no., council, date, signature, seal

#### Document 2: Elevation Certificate (Height Above MSL)
Fields:
- Project details
- Elevation data table (MSL value, datum, reference benchmark, min/max in vicinity)
- Proposed building height reference table (building height AGL, max top elevation, topmost point including OHT/lift)
- **Certification block:** Surveyor name, license no., date, signature, seal

#### Document 3: Building Elevation Reference (Design Reference — NOT architect-certified)
- Project building specifications table (height, configuration, footprint, setbacks, fire access)
- Elevation components from bottom to top (GL → Stilt → Upper Floors → Terrace → LMR → OHT → LA)
- **Heights from Pre-DCR drawings** when available (use vision_analyze on the drawing to extract elevation level markings like +3.374, +6.299, +9.223, etc.)
- Mandatory note: "Actual elevation drawings must be prepared, signed, and stamped by a COA-registered architect"
- **Certification block:** Architect name, COA registration no., BBMP empanelment no., date, signature, seal

#### Document 4: Site Plan & Location Map
- Site location details (address, GPS, elevation)
- Landmarks & distances table (direction + distance for: lake, main road, nearest AFS, airport, highway, town centre, tech parks)
- Text description of the site and surroundings
- Surrounding road network list
- Key NOC-specific notes per authority (aviation: nearest aerodrome distance; fire: access road width; BWSSB: nearest mains; BESCOM: nearest HT/LT lines)
- **Certification block**

#### Document 5: Area Master Plan Reference
- Area overview narrative
- Land use classification per RMP 2015 (subject site, water bodies, adjacent properties, corridors)
- Surrounding developments table (10+ entries within ~1 km: developments, landmarks, distances)
- Infrastructure availability (road, water, power, drainage, transport, fire, police, hospital)
- Applicable FAR & height restrictions notes
- **Disclaimer:** "This is a preparatory reference for NOC applications. Formal drawings must be prepared by licensed architect/town planner."

### Step 4: Professional Formatting (python-docx)

```python
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def create_basic_doc():
    d = Document()
    for s in d.sections:
        s.top_margin = Cm(2.54)
        s.bottom_margin = Cm(2.54)
        s.left_margin = Cm(3.18)
        s.right_margin = Cm(3.18)
    style = d.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    return d

def add_title_block(doc, title_text, subtitle_text=""):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(title_text)
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(0, 51, 102)
    if subtitle_text:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(subtitle_text)
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(102, 102, 102)
    doc.add_paragraph()

def add_field(doc, label, value):
    p = doc.add_paragraph()
    run = p.add_run(f"{label}: ")
    run.bold = True
    p.add_run(value)
```

### Step 5: Name & Deliver

- Naming: `01_GPS_Coordinates_Certificate_DRAFT.docx`, `02_Elevation_Certificate_MSL_DRAFT.docx`, etc.
- All five documents have **DRAFT** in the filename — they need licensed professional certification
- Copy to `/opt/data/` for Telegram MEDIA delivery
- Always explain to the user which documents need which professional to certify

## Pitfalls

- **These are drafts, not certified documents.** GPS coordinates, elevation, and building elevation drawings all require a licensed surveyor/architect to verify, sign, and seal. The certification blocks at the end are placeholders.
- **Google Maps coordinates may have minor offset** — for NOC submission, a DGPS survey is required. The Google Maps coordinate is a reasonable starting point.
- **Elevation from web sources is approximate** — topographic map data gives neighbourhood averages, not site-specific elevation. A physical survey is needed for ±1m accuracy.
- **Building elevation without actual drawings** — if the user hasn't provided Pre-DCR drawings, the elevation reference can only show generic height breakdown. Request their architect's drawings for accurate elevation component heights.
- **Multiple basements** — Pre-DCR drawings may show basement levels below ground (e.g. -2.70m, -5.75m). Include these in the elevation reference as below-ground levels.
- **Don't guess the building configuration** — if the user hasn't specified floors, derive from height. For 18m height: likely Stilt + Ground + 4 Floors. For 20m+ height: likely Stilt + Ground + 5 Floors.
- **Certification blocks without stamp images** — docx can't embed scanned stamps. Tell the user to have the professional affix their stamp physically or add a scanned image.

## Verified Example

**Ranka NorthStar, Allalasandra, Yelahanka — Jul 2026:**

Google Maps coordinates 13.089813° N, 77.582898° E used to generate 5 draft documents. Elevation data sourced from topographic-map.com (avg 914 m MSL). Building elevation components derived from Pre-DCR drawing analysis using vision_analyze — extracted actual heights: +3.374m (1st), +6.299m (2nd), +9.223m (3rd), +12.147m (4th), +15.071m (5th), +17.595m (Terrace), +20.247m (Parapet). All 5 docx files delivered via Telegram MEDIA.
