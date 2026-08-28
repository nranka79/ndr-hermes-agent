# Real Estate Market Research / Competitive Analysis Report (python-pptx)

## When to use this pattern

User wants a slide-by-slide project comparison report for a real estate market analysis — competitor projects, pricing, developer data, sorted and tabulated. The data typically comes from:
- Google My Maps (layers: villas, apartments, plotted, key developments)
- Brochure PDFs (extract via pymupdf)
- Property portals (MagicBricks, SquareYards, 99acres, Housing.com)
- Existing Drive documents (comprehensive reports, spreadsheets)
- Google Search AI Overview (see [magicbricks-price-extraction.md](magicbricks-price-extraction.md) for the technique)

## Proven Corridors

This pattern has been executed for four Bangalore corridors, confirming reusability:

| Corridor | Projects | Slides | My Maps KML Layers |
|----------|----------|--------|-------------------|
| **Sarjapur-Attibele Road** (Ranka Oasis) | 33 villa/apt/plotted | 36 | Villas, Plotted, Apartments, Key Dev |
| **Hoskote-Whitefield** (18 Acres) | 36 villa/plot/apt/mixed | 45 | Villas, Plotted, Apartments, Mixed, Key Dev |
| **Whitefield** (Ranka Amber) | 20 unit apt + 27 competitors | 38 | Project Location, Apartments (27), Key Dev |
| **Yelahanka** (Ranka NorthStar) | 11 apt projects + 2 discovered | 18 (v3) → removed review slides per user | Project Location, Projects (8) + 3 discovered via search + 2 more |

**v3 update (Jul 2026, Yelahanka session):** User explicitly rejected the Market Review / Customer Sentiment slides. Final structure was:
- Slide 1: Title
- Slide 2: Subject Project Overview (12-field format)
- Slide 3: Key Developments
- Slides 4-16: 13 Nearby Project slides (single-slide, all data, source hyperlinks)
- Slide 17: Price Comparison (launch-date sorted, amber highlight for subject)
- Slide 18: Thank You

This is now the preferred deck structure for all future research reports (no review slides, single-slide format).

All followed the same workflow: My Maps → extract project names → research prices → build python-pptx slides → upload as Google Slides → share with user.

### Ranka NorthStar — 4th Corridor Detail (Jul 2026)

The Yelahanka/North Bangalore session differed from earlier corridors because the My Maps had only 8 projects listed, not 27+. Three additional projects (Godrej Aveline, Sobha Althea, Prestige Gardenia Estates) were discovered via Google Search while researching the area. The final deck had 27 slides:

| # | Content |
|---|---------|
| 1 | **Title** — Ranka NorthStar, Yelahanka |
| 2 | **Project Overview** — 72 units, 1 acre, ₹54.5 L-₹1.60 Cr, Ready to Move |
| 3 | **Section** — Nearby Projects |
| 4-14 | **11 project slides** (data + highlights + concerns + source links) |
| 15-25 | **11 Market Review slides** (reputation, customer sentiment, why buy, source URLs) |
| 26 | **Price Comparison** — All projects sorted by ₹/sq.ft ascending |
| 27 | **Closing** |

**Key difference vs villa/plotted corridors:** This was an apartment-focused analysis (all 11 projects were apartments, from budget ₹6,500/sq.ft to ultra-luxury ₹23,000/sq.ft). Each project had TWO slides — a project data card slide + a market review/sentiment slide.

**My Maps format observation:** Prakash's My Maps pins were named with embedded pricing data: `"Fortuna Acacia - 9500 - Ready"`, `"Brigade Eternia - 16000 - Dec 2029"`. The number after the dash was the approximate ₹/sq.ft. This is a useful lookup key when researching — the map price acts as a sanity check against portal data.

**Browser-based research note:** For this corridor, all project data was obtained via Google Search AI Overview (direct search on google.com). Property portals (MagicBricks, 99acres) mostly blocked automated access. Google's AI Overview consistently returned structured data with price ranges, unit counts, configurations, launch dates, and developer names — sufficient for the deck.

### What's New in v2 (Jul 2026 Whitefield session)

The Ranka Amber session introduced several user-driven corrections that are now mandatory for Prakash (DRA Group):

1. **ALL projects from My Maps must be included** — do NOT skip projects even if pricing data is hard to find. Every entry in every KML layer gets a slide. For projects without portal listings, use location-based estimates from comparable nearby projects.
2. **Sort order: by launch date (newest→oldest)** — NOT by price. Within each launch-age tier, separate projects into two groups: <100 units first, then 100+ units. Use section dividers between groups.
3. **Source links on every project slide** — each competitor slide MUST include Google Maps coordinate link, MagicBricks URL, and 99acres URL at the bottom (hardcoded project page URLs even if data-limited).
4. **Bigger fonts** — headings 24-48pt, content text 11-20pt. Fonts should fill the slide. Avoid single-digit font sizes for main content.
5. **Unit table on project's own data slide** — keep only RERA Carpet Area + Built-up Area columns. Remove Super Built-up Area and any share/ownership columns (Developer/Landowner Share, LO/DED indicator).
6. **Verify pricing via browser research** — search MagicBricks + 99acres + Housing.com for EACH project. Log the verification date. Do not carry forward prices from older presentations.

### What's New in v3 (same session, later corrections)

Further user corrections from the same Whitefield session added these requirements:

7. **Clickable project names** — every project name on competitor slides must be a hyperlink to its Google Maps location. Use `add_run()` with `r.hyperlink.address = gmap_url` in python-pptx.
8. **Inline source links format** — instead of a separate source links bar at the bottom only, add compact inline links directly below the project name: `📍 Maps · 🏠 MagicBricks · 🏘️ 99acres` — all clickable in the same text line.
9. **12-field detail layout per competitor slide** — every competitor project slide must show:
    - Project Name (→ clickable Maps), Location, Land Area, Type of Development, No. of Units, Unit Types, RERA Number, No. of Floors, Launch Date, Launch Price, Current Price per sq.ft, Developer Name
    - Group these as: Left panel (prices + launch data) + Right panel (Project Snapshot with 7 fields) + Full Details section below.
10. **Price Comparison Summary slide** — a standalone table sorted newest→oldest with columns:
    `# | Project · Location | Launch Price | Current Price | Units | Launch Year | Completed Year`
    - Every project from every market segment gets a row. This is separate from the individual project slides.
11. **Pricing Justification slide** — after the project overview slides (title, overview, brief, unit table) and before the competitor sections, add a dedicated slide that justifies the project's ₹/sq.ft launch price:
    - Top: market range highlight bar (e.g., "Whitefield Range: ₹5,000-17,500/sq.ft | Your Project: ₹12,000/sq.ft")
    - Left column: Location advantages with distances to key landmarks (metro, tech park, mall, hospitals, schools)
    - Right column: Project highlights (limited inventory, premium specs, amenities, approvals, developer)
    - Bottom: pricing context bar comparing to comparable new launches with appreciation potential
12. **Sub-sort within launch tiers** — projects < 100 units come before 100+ units within the same launch-era section. Use separate section dividers for each group.

### What's New in v4 (Jul 2026, Ranka NorthStar cleanup session)

The following corrections were applied during user review of the Ranka NorthStar v2 deck:

13. **NO Market Review slides. Ever.** — The Market Review / Customer Sentiment slides were explicitly rejected by Prakash as "very confusing" and "doesn't give the right required information." All 13 review slides were deleted and never re-added. **The single-slide project detail format is now the only acceptable format for all projects regardless of type or price tier.**

14. **Price Comparison table: amber highlight for subject project** — The subject project (RANKA NORTHSTAR ⭐) gets an amber/gold tint row (`FFF3E0`) at top of table, separate from the launch-date sort. All other projects are sorted newest→oldest below it.

15. **Location name in Price Comparison** — Add a dedicated Location column showing the first locality segment (e.g., "Yelahanka", "Vidyaranyapura", "Devanahalli") for every project.

16. **Clickable source links only — no inline URLs** — Source URLs should be hyperlinked text labels (blue, underlined) like `📍 Google Maps`, `🏠 MagicBricks`, `🏘️ 99acres`, not raw URLs in the text.

17. **"Key Developments" slide is mandatory** — Always include infrastructure/amenity context between the subject project overview and the competitor project list. This was retained in the v3 cleanup and is essential context.

18. **Developer name truncated** — In the Price Comparison table, developer names longer than 18 chars should be truncated. Use `proj["developer"].split("(")[0].strip()[:18]`.

---

## Extracting Placemarks from Google My Maps (KMZ/KML)

When the user provides a Google My Maps link (e.g., `https://www.google.com/maps/d/edit?mid=...`), the marker data must be extracted programmatically. The My Maps page is JavaScript-rendered and not directly scrapable, but Google provides a **KMZ export** endpoint.

### KML Extraction Workflow

**Step 1 — Download the KMZ** (it's a ZIP archive containing `doc.kml`):
```bash
curl -s -L -o project.kmz "https://www.google.com/maps/d/kml?mid=MID_VALUE&usp=sharing"
unzip -o project.kmz
# Extracts: doc.kml (KML data), images/ (marker icons)
```

**Step 2 — Parse doc.kml for placemarks by layer (folder):**
```bash
# Quick glance at the structure
grep -E '<Folder|<name>|<Placemark|<Document' doc.kml | head -40

# Shows layers and project names without full XML parsing
```

**Step 3 — Extract all placemark names programmatically:**
```bash
# List all layer names and their placemark names
grep -E '<name>|</Folder>' doc.kml | grep -v 'CDATA' | sed 's/<[^>]*>//g' | grep -v '^$'
```

**Step 4 — Full XML parsing with Python for structured extraction:**
```python
from xml.etree import ElementTree as ET
import re

kml_ns = '{http://earth.google.com/kml/2.2}'
root = ET.fromstring(kml_data)

for folder in root.findall(f'.//{kml_ns}Folder'):
    folder_name = folder.find(f'{kml_ns}name').text
    print(f"=== {folder_name} ===")
    
    for pm in folder.findall(f'{kml_ns}Placemark'):
        name = pm.find(f'{kml_ns}name')
        desc = pm.find(f'{kml_ns}description')
        desc_text = ''
        if desc is not None and desc.text:
            desc_text = re.sub('<[^<]+?>', '', desc.text).strip()[:200]
        
        print(f"  - {name.text if name is not None else 'unnamed'}")
        if desc_text:
            print(f"    {desc_text}")
```

### KMZ URL Construction

The export URL follows this pattern:
```
https://www.google.com/maps/d/kml?mid=<MY_MAPS_MID>&usp=sharing
```

Extract the `mid` parameter from the user's My Maps URL. The URL format is:
- `https://www.google.com/maps/d/edit?mid=1-Fu2J08TlGmBLPONwY4hJjmOw_gabgw&usp=sharing`
- → `mid=1-Fu2J08TlGmBLPONwY4hJjmOw_gabgw`

### Why This Matters for Real Estate Research

The KML layers directly map to slide sections:
- **Project Location and Boundary** → project overview slides
- **Apartments** → apartment competitor slides (sorted by price descending)
- **Villas** → villa competitor slides
- **Plotted** → plotted competitor slides
- **Key Developments** → amenities/infrastructure slide

### Known Pitfalls

- **Not all projects in the KML will have readily available pricing data** — the My Maps may include projects too small/new to appear on listing portals. For those projects, estimate pricing from comparable nearby projects based on location proximity and unit type. DO NOT skip the slide — the user has explicitly corrected this.
- **The KMZ download returns binary ZIP data** — `curl` with `-L` is essential (the URL redirects). Save to file, don't pipe to stdout
- **Some KML exports use CDATA-wrapped names** — grep patterns need to account for `<name><![CDATA[Name]]></name>` format
- **Placemark descriptions may contain HTML** — always strip tags with regex before displaying names
- **XML namespace parsing can fail** — the KML namespace `{http://earth.google.com/kml/2.2}` causes `findall()` issues in some Python versions. **Fallback: use regex** — simpler and more reliable for extracting placemark names and coordinates:
  ```python
  import re
  with open('doc.kml') as f: content = f.read()
  placemarks = re.findall(r'<Placemark>(.*?)</Placemark>', content, re.DOTALL)
  for pm in placemarks:
      name = re.search(r'<name>(.*?)</name>', pm)
      coords = re.search(r'<coordinates>(.*?)</coordinates>', pm)
      desc = re.search(r'<description>(.*?)</description>', pm, re.DOTALL)
      # Extract folder by looking at surrounding context
  ```
  Regex parsing is preferred over ElementTree for this format because the KML structure is simple enough that regex handles it without namespace headaches.

### Adding Descriptions (with Highlighted Prices) to My Maps Markers

When you need to add project descriptions with **highlighted current prices** to the My Maps placemarks themselves (not just the slides), work with the KML directly.

#### Workflow

1. **Export current KML** (authenticated, using OAuth from gws-vault):
   ```python
   from tools import gws_auth
   import urllib.request

   service = gws_auth.build_service('drive', 'v3', service_name='google-draas')
   creds = service._http.credentials
   kml_url = f'https://www.google.com/maps/d/kml?mid={MAP_ID}&forcekml=1'
   req = urllib.request.Request(kml_url)
   req.add_header('Authorization', f'Bearer {creds.token}')
   with urllib.request.urlopen(req) as resp:
       kml = resp.read().decode('utf-8')
   ```

2. **Add `<description>` elements** to each `<Placemark>` with HTML that highlights the current price:
   ```xml
   <Placemark>
     <name>Prestige Sanctuary</name>
     <styleUrl>#icon-1899-0288D1-nodesc</styleUrl>
     <description><![CDATA[
       <b>📍 Nandi Hills Road, Devanahalli</b><br><br>
       🏡 Status: <b>Sold Out</b> (Resale only)<br>
       🏠 4 BHK Luxury Villas — 2,896 to 4,750 sqft<br><br>
       💰 <span style="background-color:#FFEB3B;padding:2px 6px;font-weight:bold;font-size:1.1em">
         Current Price: ₹11.70 Cr – ₹19.57 Cr</span><br>
       📊 Rate: ~₹25,455/sqft (Resale)
     ]]></description>
     <Point><coordinates>77.6969201,13.3138264,0</coordinates></Point>
   </Placemark>
   ```

3. **Update BalloonStyle** to show `$[description]` (both `-normal` and `-highlight` variants):
   ```xml
   <BalloonStyle>
     <text><![CDATA[<h2>$[name]</h2><p>$[description]</p>]]></text>
   </BalloonStyle>
   ```

4. **Upload KML to Drive** and tell the user to import it into My Maps via **Add layer → Import** in the browser editor.

#### ⚠️ Known Update Limitations (July 2026)

| Method | Result |
|--------|--------|
| Drive API `files.update()` with KMZ/KML body | Returns **200 OK** but DOES NOT change map content — only metadata updates |
| Create My Maps from KML via Drive API (`mimeType: application/vnd.google-apps.map`) | **400 Bad Request** — conversion not supported |
| OAuth token → browser sign-in | **Not possible** — OAuth token can't replace Google password for browser session |
| Browser My Maps editor → Import KML | ✅ **Only reliable path** — user must import KML in browser |

**Bottom line:** There is no programmatic write API for Google My Maps. Build the KML, save it to Drive, and have the user import it via the browser UI.

#### HTML Quick Reference for My Maps Descriptions

| Purpose | Code |
|---------|------|
| Highlighted price | `<span style="background-color:#FFEB3B;padding:2px 6px;font-weight:bold;">…</span>` |
| Bold text | `<b>text</b>` |
| Line break | `<br>` |
| CDATA wrapper (mandatory) | `<![CDATA[ … ]]>` |
| Emoji indicators | 📍🏡💰📊🚀🏠🏘️ |

## Key user preferences (from Prakash, DRA Group)

### Layout: Left Sidebar + Main Area
Every project slide follows this two-zone template:

```
┌─────────────────┬──────────────────────────────────┐
│  LEFT SIDEBAR   │         MAIN AREA               │
│  (~30% width)   │         (~70% width)            │
│                  │                                  │
│  💰 CURRENT      │  PROJECT DETAILS (rows)         │
│  PRICE card      │  • Type of Development          │
│  (dark bg, gold) │  • Project Status               │
│                  │  • Unit Sizes                   │
│  🚀 LAUNCH       │  • No. of Units                 │
│  PRICE card      │  • Launch Date                  │
│  (light bg)      │  • 🚀 Launch Price (per sq.ft)  │
│                  │  • 💰 Current Price (per sq.ft) │
│  💰 Sale Price   │  • 💰 Current Sale Price (total)│
│  (red highlight) │  • Developer / RERA             │
│                  │                                  │
│  QUICK FACTS     │                                  │
│  • Type          │                                  │
│  • Status        │                                  │
│  • Units/Sizes   │                                  │
└─────────────────┴──────────────────────────────────┘
```

### Sorting: Launch Date (Newest → Oldest), then by Unit Count

Sort all project slides within each section by launch date (newest first). Then sub-sort:
- Projects with < 100 units come BEFORE 100+ units (boutique projects first)
- Use section divider slides between these groups

Exception: if there's only one launch-age group (e.g., all are older projects), sort by current price descending instead.

### Unit Table Format (for the subject project's own data slide)

When creating the unit configuration table for the project itself (not competitors):
- Columns to INCLUDE: Unit#, Floor, Unit Type, Facing, Built-up Area (sq.ft), RERA Carpet Area (sq.ft)
- Columns to EXCLUDE: Super Built-up Area, UDS (undivided share), Developer/Landowner Share, LO/DED type column
- Keep it clean — 6 columns max. Use alternating row colors for readability.
- Font size: 10-11pt minimum for table text

### Source Links Format — Clickable Hyperlinks on Project Slides

Every project slide must have clickable source links at the bottom. There are two patterns:

**Pattern A (for single-slide format — Prakash's current preference):**
```
🔗 SOURCE LINKS:
📍 Google Maps    🏠 MagicBricks    🏘️ 99acres
```
Each link name is a separate hyperlink text box, positioned side-by-side.

**Pattern B (for inline source links below project name):**
```
Project Name (→ clickable Maps link)  
📍 Maps · 🏠 MagicBricks · 🏘️ 99acres
```

**Implementation in python-pptx (using built-in run.hyperlink.address — preferred):**

```python
def add_hyperlink_run(slide, left, top, width, height, display_text, url, size=10, color=BLUE_LINK):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = display_text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.underline = True
    run.hyperlink.address = url  # ← built-in API, handles all OOXML relationships
    return tf
```

This creates proper OOXML hyperlinks with relationship IDs that survive PPTX→Google Slides conversion. The built-in `run.hyperlink.address` setter handles relationship creation automatically. See `references/python-pptx-hyperlinks.md` for the full API reference.

**⚠️ Do NOT use manual XML construction** (`parse_xml` with `xlink:href`) for hyperlinks — it creates invalid XML that Google Slides drops during conversion. Use `run.hyperlink.address` instead. The manual approach also causes `AttributeError: module 'pptx.oxml' has no attribute 'OxmlElement'` when using `pptx.oxml.OxmlElement()` which does not exist.

**Reminder:** These hyperlinks work in PowerPoint and Google Slides after upload but are NOT clickable in telegram-rendered markdown — the user must open the file in Google Slides.

### Source Links on Every Competitor Slide (Legacy inline format)

(Previous section continues below)
```text
📍 Google Maps  |  🏠 MagicBricks  |  🏘️ 99acres
```
- Google Maps: use the coordinates from the KML placemark (construct a `https://maps.google.com/?q=LAT,LNG` URL)
- MagicBricks: construct `https://www.magicbricks.com/<ProjectName-Whitefield` (even if 404, it's the expected pattern)
- 99acres: construct `https://www.99acres.com/<project-name-whitefield` (same)
- These links go at the bottom of each slide in a small card/bar

### Font Size Guidelines (Prakash preferences)

- Title slide: 48pt project name, 26pt location
- Section headers: 34pt
- Project name on competitor slides: 26pt
- Current price display: 20pt bold
- Body text: 11-13pt
- Smallest text (captions, sources, labels): 9-10pt
- Table content: 10-11pt
- Do NOT use font sizes below 8pt — the user will request bigger

### Content Rules
- **Keep it brief** — 10-12 data rows per project, no verbose descriptions
- **Market research only** — DO NOT include construction cost, yield, profit margins, or developer-side financials. This is a competitive positioning report, not a project development memo.
- **Both launch price AND current price per sq.ft** must appear on every project slide
- **Include total sale price range** (e.g., ₹3.18 Cr - ₹4.12 Cr) alongside per-sq.ft pricing
- Prices from listing portals go in the main area; sidebars show the highlighted rate card
- **Do NOT skip projects from My Maps** — even small/obscure ones get a slide with estimated pricing

### Brochure-Based Project Brief (Slide 3)
When the user asks to add a project description from the brochure:
1. Search Drive: `name contains '<project>' and name contains 'brochure'` (raw_query=True)
2. Download the newest version (check modifiedTime)
3. Extract text via pymupdf: `import fitz; doc = fitz.open(path)`
4. Present in a two-column research slide:
   - Left: Project philosophy/positioning + full specs table
   - Right: Location advantages (with commute times) + amenities list

## Implementation (python-pptx)

Use python-pptx (pip installable) for full layout control. Key settings:

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

prs = Presentation()
prs.slide_width = Inches(13.333)  # Widescreen
prs.slide_height = Inches(7.5)
```

### Helper Functions (reuse these)

```python
def add_shape(slide, left, top, width, height, fill_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.line.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    return shape

def add_textbox(slide, left, top, width, height, text, font_size=14, 
                font_color=BLACK, bold=False, alignment=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = font_color
    p.font.bold = bold
    p.font.name = "Arial"
    p.alignment = alignment
    return txBox

def add_badge(slide, left, top, text, bg_color, text_color=WHITE, font_size=10):
    shape = add_shape(slide, left, top, Inches(1.2), Inches(0.28), fill_color=bg_color)
    shape.text_frame.paragraphs[0].text = text
    p = shape.text_frame.paragraphs[0]
    p.font.size = Pt(font_size)
    p.font.color.rgb = text_color
    p.font.bold = True
    p.font.name = "Arial"
    p.alignment = PP_ALIGN.CENTER
    return shape
```

### Project Color Palette (Section Badges)

```python
SECTION_VILLA = RGBColor(0x8E, 0x44, 0xAD)  # Purple
SECTION_APT   = RGBColor(0x29, 0x80, 0xB9)  # Blue  
SECTION_PLOT  = RGBColor(0x27, 0xAE, 0x60)  # Green
```

### Upload + Convert to Google Slides + Share

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

# Upload with conversion to native Google Slides
service = build_service("drive", "v3", service_name="google-draas")
file_metadata = {
    "name": "Project Name — Report Name",
    "mimeType": "application/vnd.google-apps.presentation"  # converts automatically
}
media = MediaFileUpload("/tmp/output.pptx", 
    mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    resumable=True)
result = service.files().create(body=file_metadata, media_body=media,
    fields="id, name, mimeType, webViewLink").execute()
file_id = result["id"]

# Share with the requesting user (NOT with yourself)
from tools.gws_skill_bridge import call
call("drive_share", service_name="google-draas",
     file_id=file_id, type="user",
     email="user@example.com", role="writer", notify=True)
```

### Data Structure for Project Slides

Each project is a tuple:
```python
(name, badge, current_rate, launch_rate, dev_type, status, 
 units, floors, sizes, sale_price, developer, rera, launch_date, section_color)
```

Sorted by price descending using high-end of current_rate range as key.

## Pitfalls

- **⚠️ Slide deletion via `del sldIdLst[idx]` corrupts the saved file** — python-pptx's `_sldIdLst` is an XML element list. Using `del` removes the child from the Python list but DOES NOT properly clean up the slide part's relationship in the OPC package. The saved file has the wrong slide count when re-opened (verified multiple times). **Correct technique only:**
  ```python
  sldIdLst = prs.slides._sldIdLst
  for idx in sorted(remove_indices, reverse=True):
      sldId = sldIdLst[idx]
      rId = sldId.rId
      sldIdLst.remove(sldId)   # removes the XML child element (NOT del!)
      prs.part.drop_rel(rId)   # drops the slide part relationship
  ```
  Always delete in reverse index order and always call `drop_rel()` after `remove()`. After removal and save, ALWAYS verify by reloading the file - do NOT trust the slide count from the in-memory object after `sldIdLst` manipulation.

- **⚠️ Slide reordering via XML element reordering** — python-pptx has no native slide reorder method. To rearrange slides, collect all `sldId` elements, build the desired index order, then clear and re-append:
  ```python
  sldIdLst = prs.slides._sldIdLst
  elements = list(sldIdLst)
  new_order = [elements[i] for i in DESIRED_INDICES]
  for el in list(sldIdLst):
      sldIdLst.remove(el)
  for el in new_order:
      sldIdLst.append(el)
  ```
  Verify after save/reload. The sldId elements themselves carry the relationship IDs, so reordering doesn't need `drop_rel`/re-relate — just XML list reordering.

- **⚠️ Cloning slides by copying shape XML to a new slide fails** — appending raw `<sp>` elements from `etree.tostring(shape._element)` to a new slide's `_spTree` creates elements that python-pptx's `SlideShapeFactory` can't parse, causing `AttributeError: 'lxml.etree._Element' object has no attribute 'has_ph_elm'`. **Don't clone slides this way.** Instead, build project slides from scratch using `add_textbox()` for each field (see "Building Project Slides Programmatically" below).

- **`gws_skill_bridge.call()` missing params cause AttributeError** — always pass `raw_query=True/False` explicitly for `drive_search` (the SimpleNamespace won't have it otherwise)
- **`drive_share` needs `type=user` and `email=`** — missing `type` param also causes AttributeError
- **`build_service()` fails with `VaultNoTokenError` even though user is authorized** — see `gws-automation` skill → "Session user ID mismatch" pitfall. Workaround: resolve the vault UID via email directly (`gws_vault_client.resolve("email", email)`) and construct credentials manually with `Credentials.from_authorized_user_info()`. This happens when the session user ID (e.g., `pm2.blr-[REDACTED-TID]`) doesn't resolve to a vault UID but the email does.
- **Pricing in summary slide** — truncate long price strings to 22 chars max to fit columns
- **Forgetting to share** — the file is created under YOUR account (ndr@draas.com). If the user is Prakash (psingh@draas.com), they get page not found unless you explicitly share
- **Font size consistency** — all body text 10pt, titles 24pt, card prices 14pt, sidebar labels 9-10pt
- **⚠️ ALWAYS verify prices from current listings** — Never accept prices from the existing presentation as accurate. Real estate listing prices change weekly. For every project, search 2+ listing portals (MagicBricks, 99acres, SquareYards, Housing.com, NoBroker) and note the verification date. Prakash has explicitly corrected stale prices in the past — this is a first-class quality gate, not cosmetic. When web tools are unavailable, fall back to DuckDuckGo lite search via curl or aggregator sites (roofandfloor, nobroker, propertywala, etc.).

- **⚠️ ALWAYS show prices in DUAL FORMAT (absolute + per-sqft)** — Prakash explicitly said "I dont understand the prices, are these current prices?" when given single-format pricing. Every price line must carry BOTH the absolute total (₹X Cr) AND the per-sqft rate. Launch price, current price, resale price — all dual-format. Template: `💰 Current Price: ₹X Cr — ₹Y Cr` on one line, `💰 Rate: ₹X,XXX — ₹Y,YYY/sqft` on the next.

- **⚠️ "Why Prices Differ" root cause report** — When user asks why presentation prices don't match fresh research, produce a structured comparison table: Project | Old Price | New Price | Difference | Root Cause. Root cause categories: Stale sheet data, Portal vs sheet mismatch, Sold Out confusion, Premium listing skew, Per-sqft calculation error. Follow with specific examples per project, source quality assessment, and a key takeaway summary.

- **⚠️ ALWAYS verify project status from three independent sources** — A project listed as "Ready to Move" may actually be stalled or awaiting plan approval. Cross-check using:

  | Source | What It Tells You |
  |--------|-------------------|
  | **MagicBricks project page** | Status field: "Ready to Move", "Ongoing", "Under Construction". Look for explicit mention of Commencement Certificate status. |
  | **Google Maps listing** | Operating status: "Open", "Closed Permanently", "Temporarily Closed". For completed projects, "Closed" is normal. For uncompleted ones, it may signal stall. |
  | **Developer's official website** | Is the project listed under Ongoing/Upcoming/Completed? Does the project-specific URL return 200 or 404? |

  **Worked example (Ranka NorthStar, Jul 2026):** MagicBricks said *"Commencement certificate has not been granted"* with status **Ongoing** (not Ready). Google Maps showed **Closed Permanently**. DRA Homes website returned **404** for the project page. Conclusion: **Plan Approval Pending** despite earlier presentation claiming "Ready to Move". This correction was material — it changed the entire analysis context.

- **⚠️ Search for additional nearby projects beyond the My Maps** — The user's My Maps may not be exhaustive. When researching the area, search "new residential projects [locality]" on DuckDuckGo or Google to find additional competitors. In the Yelahanka session, 2 new projects (Godrej Beacon, Casagrand Promenade) were discovered this way. Godrej Beacon was in the exact same micro-location (Ambedkar Colony) as Ranka NorthStar — a critical competitive data point not in the original My Maps.

## Sheet-Driven Price Verification Workflow

When the user says: *"Check [sheet] in the spreadsheet, extract, compare, verify, update both presentation and mymaps"* — this is now a recurring pattern (executed for Ranka Oasis, Ranka Northstar).

### Workflow

1. **Extract sheet data** via CSV export (`export?format=csv&gid=X`). Note: hyperlinks are LOST in CSV.
2. **Find existing assets** — presentation (via `drive_search` with `raw_query=True`) and My Maps (filter by mimeType `application/vnd.google-apps.map`).
3. **Compare prices**: Sheet vs Presentation vs Verified Market (browser research on MagicBricks, 99acres, Housing.com).
4. **Build updated presentation** — fresh PPTX with verified prices, upload as native Google Slides, share.
5. **Build updated KML** — HTML descriptions with **highlighted current prices** in yellow (`<span style="background-color:#FFEB3B">`). Upload to Drive, tell user to import manually.

### Pitfalls
- CSV export drops all hyperlinks — tell the user
- Sheet prices can be 10-30% lower than portal-verified prices — always cross-verify
- No programmatic My Maps update API — user must import KML manually
- Find My Maps by searching with `q="mimeType='application/vnd.google-apps.map' and name contains '...'"` via `raw_query=True`

### When the User Provides a Spreadsheet (Sheet as Authoritative Source)

⚠️ **If the user sends a Google Sheet with project data, USE IT as the single source of truth — DO NOT override with web-scraped prices.**

**Important nuance: sheet prices can be LOWER than what you extract from portals via browser.** In the Thylagere session, browser-verified prices were 10-30% HIGHER than the sheet data. The sheet likely reflects base/average rates, while portals show remaining premium inventory at higher asking prices. When in doubt, the sheet wins — it's the developer's own data.

#### ⚠️ Critical: CSV Export Drops Hyperlinks

When you extract sheet data via `export?format=csv&gid=X`, **all hyperlinks are permanently lost** — only the anchor/display text survives in the CSV. There is no way to recover the original URLs from the CSV output.

**Impact for real estate research:** The "Primary Source / Reference" column in project tracking sheets typically contains clickable link labels like "Prestige Sanctuary (99acres)". The CSV export gives you only the label text, not the underlying URL. You cannot programmatically visit those source links.

**Workarounds (in order of reliability):**
1. **Use the Sheets API directly** (`sheets_get`) — preserves hyperlinks in cell metadata
2. **Browser screenshot + vision** — take a screenshot and read URLs visually
3. **Reconstruct URLs from anchor text** — if label says "Project Name (99acres)", construct search URL manually
4. **Ask user for the URLs** — tell them CSV export loses links and request the actual sheet link

In the 2026-07-17 Whitefield session, the user provided a spreadsheet with current prices that differed significantly from what web research (MagicBricks, 99acres) returned. Web-scraped prices were 20-90% higher for most projects because:
- Portals often list the asking price of remaining higher-end inventory (survivorship bias)
- The user's sheet likely reflects developer-quoted base prices or averages across all units
- Different listing portals report different inventory at different listed prices

**Rule**: When a spreadsheet arrives mid-session, the user's data wins. Rebuild from the sheet.

### Property Type Classification Verification

When a spreadsheet labels project types (e.g., "Plotted Development", "Plotted / Villa Community", "Plotted / Eco Community"), **always verify against live portal data before finalizing the categorization.** Spreadsheet labels can be incorrect or ambiguous.

#### Verification Sources (3-way cross-check)

| Source | What It Tells You | |
|--------|-------------------|--|
| **MagicBricks project page** | Explicit "Project Type" field + "Configurations" section (shows Villas, Plots, Apartments) | Most authoritative for type classification |
| **99acres project page** | Property type tag + unit listing (e.g., "3 BHK Villa", "Plot" vs "Apartment") | Secondary confirmation |
| **Developer's own website** | How the project describes itself — "luxury villas", "plotted layout", "garden apartments" | Final authority |

#### Red Flags That Trigger Verification

Be suspicious when the spreadsheet labels these as "Plotted Development":
- Projects with "Villa" in their name (e.g., Bluejay Ananda **Villas**)
- Projects described as "Villa Community" or "Eco Community"
- Projects with G+1 building configuration (that's built-up, not bare plots)

#### Worked Example (Ranka Oasis, Jul 2026)

Four projects were initially classified as "Plotted Developments" in the sheet but verified as **Villas**:

| Project | Sheet Label | Web-Verified Type | Key Evidence |
|---------|------------|-------------------|--------------|
| Urban Serenity | Plotted / Villa Community | **Villa** | 152 units of 2,120-2,400 sq.ft villas (ready-to-move) |
| Urban Greens | Plotted Development | **Villa** | 178 units of 3 BHK villas (MB explicitly: "Villa Project") |
| Bluejay Ananda | Plotted Development | **Villa** | 140 G+1 independent villas (3 & 4 BHK) |
| Natura Atavi | Plotted / Eco Community | **Villa** | 296 units of 4 BHK villas in 17-acre gated community |

**Pattern:** If a "Plotted" project has >100 units with unit sizes >1,500 sq.ft and mentions bedrooms (3 BHK/4 BHK), it's almost certainly a **villa** project, not a plotted development.

#### When to Move a Project Between Categories

Only reclassify after finding **at least two independent sources** confirming the correct type. A single MagicBricks listing is enough if it explicitly states "Villa" in the configuration field. A 99acres title saying "Plotted Development" but listing individual units as "Villa" should trigger deeper inspection.

#### Implementation

```python
# Verification checklist before finalizing category assignment
verified_types = {
    "Urban Serenity":  "villa",   # MB: 4 BHK Villas
    "Urban Greens":    "villa",   # MB: "Villa Project", 3 BHK configs
    "Bluejay Ananda":  "villa",   # MB: Independent Villas, G+1
    "Natura Atavi":    "villa",   # Developer site: 4 BHK Villas
}

for project in plotted_candidates:
    if project.name in verified_types:
        project.category = verified_types[project.name]
```

### Comparison Workflow

When verifying presentation data against a user-provided sheet:

1. Read both datasets side-by-side — pull the sheet via sheets_get and compare field-by-field
2. Flag every project where current price, launch year, units, or launch price differ
3. Check removal criteria against sheet data — if you removed projects based on web prices, verify those same projects in the sheet before declaring them removed
4. Rebuild the presentation with sheet data — update each project slide's data fields AND the Price Comparison summary table

### Price Comparison Summary Table — Newest→Oldest by Launch Date (Prakash preference)

The Price Comparison table must:

1. **Highlight the subject project** in an amber/gold tint row at the top (RGB `FFF3E0`)
2. **Sort all other projects by launch date, newest→oldest**
3. **Include location name** for each project (shortened to first location segment)
4. **Use colour bands** for development type:
   - 🟢 Green tint (`E8F5E9`) = budget apartments
   - 🔵 Blue tint (`E3F2FD`) = plotted developments
   - 🔴 Pink tint (`FDE8E8`) = premium/luxury/ultra-luxury apartments
   - White = odd rows of uncoloured categories
5. **Full column set:** Project Name, Type, Launch Date, Launch Price, Current / sq.ft, Location, Status, Developer

**Build technique:** Use python-pptx `add_table()` with 8 columns. Set column widths to fit 13.333" widescreen. Apply row fills by iterating `table._tbl` cells and setting `solidFill` via XML.

**Sort key for launch date:**
```python
def sort_key(p):
    d = p["launch_date"]
    if "2026" in d or "Pre-Launch" in d: return 0
    if "2025" in d: return 1
    if "2024" in d: return 2
    if "2023" in d: return 3
    if "2022" in d: return 4
    if "2021" in d: return 5
    if "2020" in d: return 6
    if "2019" in d or "2018" in d: return 7
    if "2017" in d: return 8
    return 99
```

**Known Pitfall:** Price range strings often exceed column width. Truncate long strings to 22 chars max. The Location column should only show the first segment (before the first comma).

### Price Comparison Table Rebuild Technique (Legacy)

(Previous section preserved below — markdown structure continues)

```python
# Remove existing data-row shapes (keep title, subtitle, header, note)
shapes_to_remove = []
for shape in slide.shapes:
    if hasattr(shape, 'text') and shape.text.strip() and shape.top not in KEEP_YS:
        shapes_to_remove.append(shape)
for shape in shapes_to_remove:
    shape._element.getparent().remove(shape._element)

# Re-add text boxes for each row
start_y = FIRST_ROW_Y  # e.g. 1092000
for row_num, proj_data in enumerate(projects, 1):
    for col_idx, (col_x, text) in enumerate(zip(COL_X_POSITIONS, row_data)):
        txBox = slide.shapes.add_textbox(col_x, start_y, width, height)
        p = txBox.text_frame.paragraphs[0]
        run = p.add_run()
        run.text = text
        run.font.size = Pt(9 if col_idx != 1 else 8)
        run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        if col_idx == 3:  # current price column bold
            run.font.bold = True
    start_y += ROW_SPACING  # ~165000 EMU
```

⚠️ **Font size**: `run.font.size` takes Pt objects (`Pt(9)`), not raw ints.

### Updating Project Slides via Position Matching

When updating slide data fields to match a sheet, find shapes by position + content:

```python
def set_text(shape, new_text):
    for para in shape.text_frame.paragraphs:
        for run in para.runs:
            run.text = ""
        for run in para.runs:
            run.text = new_text; break
        break

for shape in slide.shapes:
    if not hasattr(shape, 'text') or not shape.text.strip(): continue
    t, x, y = shape.text.strip(), shape.left, shape.top
    if 700000 < y < 900000 and '₹' in t and 'sq.ft' in t:
        set_text(shape, new_current_price)
```

Key positions for a widescreen (13.333×7.5") presentation:

| Field | X range | Y range |
|-------|---------|---------|
| Left — Current Price | 400-500k | 800-900k |
| Left — Total Price | 400-500k | 950k-1.1M |
| Left — Launch Price | 400-500k | 1.25-1.45M |
| Right — Developer | 7.2-7.6M | 850k-1.05M |
| Right — Location | 7.2-7.6M | 1.05-1.2M |
| Right — Land Area | 7.2-7.6M | 1.2-1.4M |
| Right — Units | 7.2-7.6M | 1.55-1.7M |
| Detail — RERA | 2.5-3.0M | 2.0-2.15M |
| Detail — Launch Price | 2.5-3.0M | 2.52-2.68M |
| Detail — Current Price | 2.5-3.0M | 2.7-2.85M |

## Building Project Slides Programmatically (When Cloning Fails)

When you need to create large numbers of project competitor slides and python-pptx's slide manipulation proves unreliable (clone-by-XML fails, slide deletion doesn't persist), build each slide from scratch using `add_textbox()` for every field. This approach is more code but 100% reliable.

### Architecture

Each project slide consists of three zones:

```
┌──────────────────────────────────────────────────────────────┐
│  📍 Project Name                          [TAG]             │
│  📍 Maps · 🏠 MagicBricks · 🏘️ 99acres                     │
├──────────────────────┬───────────────────────────────────────┤
│  LEFT (~450k start)  │  RIGHT (~6200k start)                 │
│                      │                                       │
│  💰 CURRENT PRICE    │  PROJECT SNAPSHOT                     │
│  ₹12,500/sq.ft       │  Developer: Prestige Group           │
│  Total: ₹2.11 Cr     │  Location: ECC Road, Whitefield      │
│                      │  Land Area: ~8.34 Acres              │
│  🚀 LAUNCH PRICE     │  Type: Luxury High-rise              │
│  ₹8,500/sq.ft        │  Units: 316                          │
│  ~2022               │  Unit Types: 3 & 4 BHK               │
│                      │  Floors: B+G+16                      │
│  PROJECT DETAILS:    │                                       │
│  RERA Number: ...    │                                       │
│  No. of Floors: ...  │                                       │
│  Launch Date: ...    │                                       │
│  Launch Price: ...   │                                       │
│  Current Price: ...  │                                       │
│  Total Price: ...    │                                       │
│  Developer: ...      │                                       │
└──────────────────────┴───────────────────────────────────────┘
```

### Helper Function

```python
from pptx.util import Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

def add_tb(slide, left, top, width, height, text, size=9, bold=False, 
           color=RGBColor(0x33,0x33,0x33)):
    """Add a text box to a slide at EMU coordinates."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return txBox
```

### Creating One Project Slide

```python
def create_project_slide(prs, pdata, blank_layout):
    """pdata is a tuple: (name, loc, dev, land, dev_type, units, floors, 
       unit_types, sizes, launch, launch_p, curr_p, total, rera, status)"""
    name, loc, dev, land, dev_type, units, floors, unit_types, sizes, \
        launch, launch_p, curr_p, total, rera, status = pdata
    
    slide = prs.slides.add_slide(blank_layout)
    
    # Title bar
    add_tb(slide, 300000, 120000, 9000000, 350000, f"📍 {name}", 22, 
           True, RGBColor(0x1A,0x1A,0x2E))
    add_tb(slide, 11291675, 140000, 650000, 230000, "APARTMENT", 9, 
           True, RGBColor(0xFF,0xFF,0xFF))
    add_tb(slide, 300000, 420000, 11500000, 200000, 
           "📍 Maps · 🏠 MagicBricks · 🏘️ 99acres", 8, 
           False, RGBColor(0x66,0x66,0x66))
    
    # LEFT PANEL — Current Price
    add_tb(slide, 450000, 700000, 5000000, 120000, 
           "💰 CURRENT PRICE PER SQ.FT", 8, True, RGBColor(0x1A,0x1A,0x2E))
    add_tb(slide, 450000, 820000, 5000000, 180000, curr_p, 14, True, 
           RGBColor(0xC0,0x39,0x2B))
    add_tb(slide, 450000, 1010000, 5000000, 120000, f"Total: {total}", 9, 
           False, RGBColor(0x55,0x55,0x55))
    
    # LEFT PANEL — Launch Price
    add_tb(slide, 450000, 1250000, 5000000, 120000, "🚀 LAUNCH PRICE", 8, 
           True, RGBColor(0x1A,0x1A,0x2E))
    add_tb(slide, 450000, 1360000, 5000000, 150000, launch_p, 11, False, 
           RGBColor(0x2E,0x86,0x4B))
    add_tb(slide, 450000, 1490000, 5000000, 120000, launch, 9, False, 
           RGBColor(0x55,0x55,0x55))
    
    # LEFT PANEL — Project Details labels + values
    add_tb(slide, 450000, 1830000, 3000000, 120000, 
           "FULL PROJECT DETAILS", 8, True, RGBColor(0x1A,0x1A,0x2E))
    
    details = [
        ("RERA Number", rera, 2070000),
        ("No. of Floors", floors, 2245000),
        ("Launch Date", launch, 2420000),
        ("Launch Price", launch_p, 2595000),
        ("Current Price (per sq.ft)", curr_p, 2770000),
        ("Current Sale Price (Total)", total, 2945000),
        ("Developer", dev, 3120000),
    ]
    for label, value, y in details:
        add_tb(slide, 450000, y, 2400000, 130000, label, 8, False, 
               RGBColor(0x55,0x55,0x55))
        add_tb(slide, 3000000, y, 4000000, 130000, value, 8, True, 
               RGBColor(0x33,0x33,0x33))
    
    # RIGHT PANEL — Project Snapshot
    add_tb(slide, 6200000, 700000, 4000000, 180000, "PROJECT SNAPSHOT", 10, 
           True, RGBColor(0x1A,0x1A,0x2E))
    
    snapshot = [
        ("Developer", dev, 920000),
        ("Location", loc, 1090000),
        ("Land Area", land, 1260000),
        ("Type", dev_type, 1430000),
        ("Units", str(units), 1600000),
        ("Unit Types", unit_types, 1770000),
        ("Floors", floors, 1940000),
    ]
    for label, value, y in snapshot:
        add_tb(slide, 6200000, y, 1400000, 120000, label, 8, False, 
               RGBColor(0x55,0x55,0x55))
        add_tb(slide, 7600000, y, 3500000, 120000, value, 8, True, 
               RGBColor(0x33,0x33,0x33))
    
    return slide
```

### Creating a Section Header Slide

```python
def create_section_header(prs, title, subtitle, blank_layout):
    slide = prs.slides.add_slide(blank_layout)
    add_tb(slide, 300000, 2875985, 10000000, 400000, title, 24, True, 
           RGBColor(0x1A,0x1A,0x2E))
    add_tb(slide, 300000, 3200000, 10000000, 300000, subtitle, 14, False, 
           RGBColor(0x55,0x55,0x55))
    return slide
```

### Price Comparison Table — Font Size Note

When rebuilding the price comparison table with `add_textbox()`, use `Pt(size)` for font sizes, not raw integers:

```python
run.font.size = Pt(9)   # ✅ correct
run.font.size = 9       # ❌ ValueError: must be in range 100 to 400000
```

### Also persist these facts to memory

### Re-Applying Filter Criteria After Data Source Change

⚠️ **CRITICAL: When a user-provided sheet changes project data, RE-APPLY your filtering criteria using the new (sheet) values, not the old (web-researched) values.**

In the 2026-07-17 Whitefield session, the user provided a sheet after v5 was already delivered. The sheet showed different launch years and prices for several projects. Some projects that passed the "launched ≥ 2018 AND current price ≥ ₹8K" filter with web data FAILED the same filter with sheet data (e.g., Balaji Casablanca was 2016 in the sheet → removed). 

**Correct workflow:**
1. Apply filter to web-researched data → produce vN
2. User provides sheet → update ALL project data to match sheet
3. Re-APPLY the same filter to the sheet data → remove projects that no longer qualify
4. Rebuild section headers and Price Comparison summary with the narrower set

**Common mistake (what happened here):** Updated project data to sheet values but kept the web-filtered project set without re-checking. This left in projects whose sheet launch year was now < 2018 or whose sheet current price dipped below ₹8K.

#---

### Table Cell Coloring via XML Manipulation (Price Comparison Table)

When you need to apply category colors (e.g., green for villa rows, blue for plot rows) to an existing PowerPoint table, python-pptx's table API doesn't expose cell fills directly in all cases. Use XML manipulation via `lxml` on the table element:

### Direct Cell Value Update (Simpler Alternative)

If you only need to update **text values** in existing table cells (not colors or structure), use cell-by-cell access — far simpler than text replacement which fails on cell boundaries:

```python
def set_cell(table, row, col, value):
    \"\"\"Replace text in a specific table cell. Simpler and more reliable 
    than find-replace which fails on cell boundaries.\"\"\"
    cell = table.rows[row].cells[col]
    for para in cell.text_frame.paragraphs:
        for run in para.runs:
            run.text = value
            return
    # Fallback if no runs exist
    p = cell.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = value

# Usage
table = slide.shapes[0].table  # find the table shape first
set_cell(table, 1, 3, '₹17,000-36,352/sq.ft')  # row 1, col 3
set_cell(table, 2, 4, '+3-45%')                  # row 2, col 4
```

**When to use which:**
from pptx.oxml.ns import qn
from lxml import etree

slide = prs.slides[SLIDE_INDEX]
for shape in slide.shapes:
    if shape.has_table:
        tbl = shape.table._tbl
        for row_idx, row in enumerate(tbl.findall(qn('a:tr'))):
            cells = row.findall(qn('a:tc'))
            for cell in cells:
                tcPr = cell.find(qn('a:tcPr'))
                if tcPr is None:
                    tcPr = etree.SubElement(cell, qn('a:tcPr'))
                
                # Remove existing fills
                for fill in tcPr.findall(qn('a:solidFill')):
                    tcPr.remove(fill)
                
                # Apply new fill
                sf = etree.SubElement(tcPr, qn('a:solidFill'))
                srgb = etree.SubElement(sf, qn('a:srgbClr'))
                
                if row_idx == 0:
                    srgb.set('val', '16213A')      # Navy header
                elif 1 <= row_idx <= 6:
                    srgb.set('val', 'D5F5E3')      # Light green (villas)
                elif row_idx == 7:
                    srgb.set('val', 'F0F0F0')      # Grey separator
                elif 8 <= row_idx <= 14:
                    srgb.set('val', 'D6EAF8')      # Light blue (plots)
        break
```

### Pattern library (reusable color schemes for price comparison tables)

| Scheme | Header | Category A | Separator | Category B |
|--------|--------|-----------|-----------|-----------|
| **Green/Blue** (villa/plot) | `16213A` navy | `D5F5E3` light green | `F0F0F0` grey | `D6EAF8` light blue |
| **Purple/Teal** (premium/value) | `1B2A4A` dark navy | `E8DAEF` light purple | `F8F8F8` off-white | `D1F2EB` light teal |
| **Orange/Blue** (sold/available) | `2C3E50` dark blue | `FDEBD0` light orange | `F0F0F0` grey | `D6EAF8` light blue |
| **Single zebra** (alt rows) | `16213A` navy | `F5F5F5` light grey | — | `FFFFFF` white |

### When to use XML table coloring vs text-box rebuild

- **XML coloring**: Use when the table already exists and you just need background fills. Fast, preserves existing text formatting, column widths, and borders.
- **Text-box rebuild** (documented above under "Price Comparison Table Rebuild Technique"): Use when you need to restructure columns, change font sizes per cell, or add/remove rows. More code but full control.

---

## Project Data Card Format (Two-Slide Pattern: Card + Review)

For apartment-focused decks (vs villa/plotted), use a two-slide pattern per project:

### Slide A: Project Data Card

A horizontal layout with three zones:

```
┌──────────────────────┬──────────────────────────────────────────────┐
│ PROJECT NAME         │  ₹/sq.ft badge (gold)   Developer + Location │
│ (navy bg, white)     │  Status badge (green/amber)                  │
├──────────────────────┴──────────────────────────────────────────────┤
│ QUICK FACTS (cream)              │  ✅ HIGHLIGHTS (teal tint)        │
│ • Type: Apartment                │  • Bullet point 1                │
│ • Status: Ready                  │  • Bullet point 2                │
│ • Units: 150                     │  • Bullet point 3                │
│ • Config: 2/3 BHK                │  • Bullet point 4                │
│ • Config details                 │                                  │
│ • Developer                      │  ⚠️ CONCERNS (red-pink tint)      │
│ • Rating                         │  • Concern 1                     │
│                                  │  • Concern 2                     │
│                                  │  • Concern 3                     │
│                                  │                                  │
│                                  │  🔗 SOURCE LINKS (gray bar)      │
│                                  │  📍 Maps | 🏠 MB | 🏘️ 99A      │
└──────────────────────────────────┴──────────────────────────────────┘
```

### Slide B: Market Review / Sentiment

```
┌──────────────────────────────────────────────────────────────────┐
│ ★ PROJECT NAME — Market Review                                   │
├──────────────────────┬───────────────────────────────────────────┤
│ 📊 MARKET REPUTATION  │  ⭐ CUSTOMER & MARKET SENTIMENT           │
│ (cream bg)            │  (navy bg, gold text)                    │
│                       │                                          │
│ • Brief reputation    │  • Narrative sentiment paragraph          │
│   description         │                                          │
│                       │  • Rating: 4.4★                         │
│ 💡 WHY BUY / INVEST   │  • Developer: XYZ Group                 │
│                       │                                          │
│ • Key rationale       │                                          │
├──────────────────────┴───────────────────────────────────────────┤
│ 🔗 PROJECT SOURCE LINKS                                          │
│ 📍 Google Maps URL                                               │
│ 🏠 MagicBricks URL                                               │
│ 🏘️ 99acres URL                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Prakash's Preferred Format (as of Jul 2026) — Single Slide, No Reviews

**⚠️ IMPORTANT: Prakash explicitly rejected Market Review / Customer Sentiment slides** in the Jul 2026 Ranka NorthStar session. He said they were "very confusing" and didn't give the right information. When asked, he chose to **delete all review slides entirely** rather than reformat them. This is now the default for all DRA Group research decks — never generate separate review slides.

**Current single-slide format (preferred):**

Every project gets exactly **one** slide with these 12 fields in structured layout:

| # | Field |
|---|-------|
| 1 | Project Name (→ hyperlinked to Google Maps) |
| 2 | Project Location |
| 3 | Land Area |
| 4 | Development Type |
| 5 | Total Units / Scale |
| 6 | Unit Types (with sq.ft sizes) |
| 7 | RERA Number |
| 8 | No. of Floors |
| 9 | Launch Date |
| 10 | Launch Price |
| 11 | Current Price per sq.ft |
| 12 | Developer Name |

Plus **clickable source links** at the bottom row:
- 📍 Google Maps (hyperlinked)
- 🏠 MagicBricks (hyperlinked, where available)
- 🏘️ 99acres (hyperlinked, where available)

### When to Use Two-Slide Pattern (Legacy — Do NOT use for Prakash)

This pattern was tried for the Ranka NorthStar deck (Jul 2026) and explicitly rejected. Do NOT use it for DRA Group presentations.

| Deck Type | Slides per Project | Status |
|-----------|------------------|--------|
| Villa/Plotted projects | 1 slide | Current default |
| Apartment projects | 1 slide only (no review) | ✅ Prakash's explicit preference as of Jul 2026 |
| Ultra-luxury projects (₹15K+/sq.ft) | 1 slide | All data in single slide |
| Budget projects (₹7K-/sq.ft) | 1 slide | Consistent format |

### Implementation Notes

- **Slide A colors**: Navy header bar, cream for quick facts, teal-tinted for highlights, red-tinted for concerns, gray background for source links
- **Slide B colors**: Dark navy for sentiment section with gold text, cream for market reputation section
- **Sorting for price comparison**: Sort projects by ₹/sq.ft ascending (lowest to highest) with the subject project highlighted in gold. The Price Comparison table includes all projects + the subject.
- **Data fields captured**: Project Name, Type, Units, Configuration, Launch/Possession Status, ₹/sq.ft, Total Price Range, Developer, Location, Rating, Source URLs, Highlights, Concerns, Market Reputation, Why Buy/Invest sentiment.

When the user asks to add "reviews" or "market sentiment" for each competitor project, add dedicated review slides after each project slide with a structured dark-themed layout.

### Slide Structure

Each review slide has 4 sections in a consistent dark theme (navy background, gold accents):

```
┌──────────────────────────────────────────────────────────┐
│  ★ Project Name — Market Review           [GOLD BAR]     │
├──────────────────────────────────────────────────────────┤
│  [CUSTOMER & MARKET REVIEW] label                        │
│                                                          │
│  ✅ HIGHLIGHTS                                            │
│  • Buyer praise points (1-3 sentences)                   │
│  • What makes this project stand out                     │
│                                                          │
│  ⚠️ CONCERNS                                              │
│  • Common complaints and risks                           │
│  • Known issues from forums/reviews                      │
│                                                          │
│  📊 MARKET REPUTATION                                    │
│  • Portal ratings (e.g., 4.2/5 on 99acres)              │
│  • Analyst/agent quoted description                      │
│                                                          │
│  💡 WHY BUY / INVEST                                     │
│  • Key decision drivers for buyers                       │
│  • Investment rationale                                  │
│                                                          │
│  📍 Google Maps | 🏠 MagicBricks | 🏘️ 99acres  [small]   │
└──────────────────────────────────────────────────────────┘
```

### Research Pattern for Review Content

When web tools (Firecrawl) are unavailable:
1. **Use DuckDuckGo Lite** for quick URL discovery (see "DuckDuckGo Lite for Portal Research" below)
2. **Leverage training knowledge** about well-known Indian real estate projects (brand reputation, reported delays, common buyer feedback)
3. **Construct review content** as structured data: highlights, concerns, reputation, why-buy
4. **Add source URLs** at the bottom — real Google Maps, MagicBricks, and 99acres links found via DDG Lite

### python-pptx Implementation

```python
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from lxml import etree

def add_review_slide(prs, project_name, review_data, sources, blank_layout):
    """
    review_data: {highlights, concerns, reputation, why_buy}
    sources: {mb, acres}  # URL strings or None
    """
    sw, sh = prs.slide_width, prs.slide_height
    new_slide = prs.slides.add_slide(blank_layout)
    
    # Dark navy background
    bg = etree.SubElement(new_slide._element.find(qn('p:cSld')), qn('p:bg'))
    bgFill = etree.SubElement(bg, qn('a:solidFill'))
    bgSrgb = etree.SubElement(bgFill, qn('a:srgbClr'))
    bgSrgb.set('val', '0A1628')  # Very dark navy
    
    # Helper
    def add_tb(slide, left, top, width, height, text, size=12, bold=False, color='FFFFFF', align=PP_ALIGN.LEFT):
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = align
        run = p.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = RGBColor(*bytes.fromhex(color))
        return txBox
    
    # Title bar (gold on navy)
    title_shape = new_slide.shapes.add_shape(1, Emu(0), Emu(0), sw, Emu(700000))
    title_shape.fill.solid(); title_shape.fill.fore_color.rgb = RGBColor(0x16, 0x21, 0x3A)
    title_shape.line.fill.background()
    p = title_shape.text_frame.paragraphs[0]
    run = p.add_run(); run.text = f"  ★ {project_name} — Market Review"
    run.font.size = Pt(22); run.font.bold = True; run.font.color.rgb = RGBColor(0xD4, 0xA5, 0x3C)
    
    # Section label
    label = new_slide.shapes.add_shape(1, Emu(300000), Emu(800000), Emu(1800000), Emu(350000))
    label.fill.solid(); label.fill.fore_color.rgb = RGBColor(0xD4, 0xA5, 0x3C)
    label.line.fill.background()
    p = label.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    run = p.add_run(); run.text = "CUSTOMER & MARKET REVIEW"
    run.font.size = Pt(11); run.font.bold = True; run.font.color.rgb = RGBColor(0x16, 0x21, 0x3A)
    
    # Four content sections
    y = Emu(1300000)
    sections = [
        ("✅ HIGHLIGHTS", review_data['highlights'], 'D4A53C', 'CCCCCC'),
        ("⚠️ CONCERNS", review_data['concerns'], 'E74C3C', 'CCCCCC'),
        ("📊 MARKET REPUTATION", review_data['reputation'], 'D4A53C', 'CCCCCC'),
        ("💡 WHY BUY / INVEST", review_data['why_buy'], 'D4A53C', 'CCCCCC'),
    ]
    for title, body, title_color, body_color in sections:
        add_tb(new_slide, Emu(300000), y, Emu(11000000), Emu(260000),
               title, 13, True, title_color)
        y += Emu(280000)
        add_tb(new_slide, Emu(400000), y, Emu(10900000), Emu(1300000),
               body, 10, False, body_color)
        y += Emu(1400000)
    
    # Source links at bottom
    src_parts = []
    loc_q = project_name.replace(' ', '+') + '+Devanahalli+Bangalore'
    src_parts.append(f'📍 Google Maps: maps.google.com/?q={loc_q}')
    if sources.get('mb'): src_parts.append(f'🏠 MagicBricks: {sources["mb"]}')
    if sources.get('acres'): src_parts.append(f'🏘️ 99acres: {sources["acres"]}')
    add_tb(new_slide, Emu(300000), y, Emu(11000000), Emu(400000),
           ' | '.join(src_parts), 7, False, '888888')
    
    return new_slide
```

### Inserting Review Slides After Each Project Slide

When inserting 13+ review slides into an existing deck, process in **reverse order** so insertions don't affect earlier indices:

```python
project_slides = [(4, 'Prestige Sanctuary'), (5, 'Over the Rainbow'), ...]
for slide_idx, proj_name in reversed(project_slides):
    review_slide = add_review_slide(prs, proj_name, review_data, sources, blank_layout)
    # review_slide is appended at the end
```

Then reorder slides via XML manipulation:

```python
sldIdLst = prs._element.find(qn('p:sldIdLst'))
sldIds = list(sldIdLst.findall(qn('p:sldId')))

# Original slides: indices 0-22
# New review slides: indices 23-35 (added in reverse order = Montira first at 23)
# Build target order interleaving project + review

new_order = []
# Slides 1-4 (indices 0-3)
for i in range(4):
    new_order.append(sldIds[i])

# Villa projects (4-9) matched to review slides (35, 34, 33, 32, 31, 30)
for i in range(4, 10):
    review_idx = 35 - (i - 4)  # Last processed = Prestige Sanctuary at 35
    new_order.append(sldIds[i])       # Project
    new_order.append(sldIds[review_idx])  # Review

# Plotted header (index 10)
new_order.append(sldIds[10])

# Plot projects (11-17) matched to review slides (29→23)
for i in range(11, 18):
    review_idx = 40 - i
    new_order.append(sldIds[i])
    new_order.append(sldIds[review_idx])

# Remaining slides (18-22)
for i in range(18, 23):
    new_order.append(sldIds[i])

# Reorder XML
for idx, sldId in enumerate(new_order):
    sldId.set('id', str(256 + idx))

# Rearrange in sldIdLst (clear and re-append in order)
for sldId in list(sldIdLst):
    sldIdLst.remove(sldId)
for sldId in new_order:
    sldIdLst.append(sldId)
```

⚠️ Verify after save/reload to confirm slide ordering persisted.

---

## Google Search AI Overview for Portal-Blocked Research

When MagicBricks, 99acres, SquareYards, and Housing.com all block automated access (CAPTCHAs, JS challenges), **Google Search AI Overview** is a reliable fallback for extracting structured project data. It works even without residential proxies and consistently returns usable data for Bangalore real estate projects.

### Technique: Direct Google Search for Each Project

```python
# Navigate to Google Search for each project
browser_navigate(url=f"https://www.google.com/search?q={project_name}+{location}+price+units+launch")
```

Google's AI Overview panel typically returns:
- **Price range** (e.g., ₹1.07 Cr — ₹2.53 Cr)
- **Price per sq.ft** (e.g., ₹9,500 — ₹13,907)
- **Unit configurations** (e.g., 2 BHK 1,121 sq.ft, 3 BHK 1,667 sq.ft)
- **Launch date / possession timeline**
- **Developer name**
- **Total units and project scale** (acres, towers)
- **Portal ratings** (e.g., 4.3★ on MagicBricks, 4.4★ on Google)
- **Source links** to MagicBricks, 99acres, Housing.com pages

### Query Pattern

```
{project_name} {location} Bangalore price units launch
```

**Examples that worked:**
- `Brigade Eternia Yelahanka Bangalore price units launch date`
- `Kanisha White Palace Vidyaranyapura Yelahanka Bangalore price`
- `GR OPAL Yelahanka Bangalore price apartment project`
- `Aryan 1 Celeste Yelahanka Bangalore apartment price`

### When to Use This vs Portal Browsing

| Situation | Recommended Method |
|-----------|------------------|
| Portal pages load without CAPTCHA | Direct portal browsing (more detailed data) |
| Portals blocked by CAPTCHAs | Google Search AI Overview |
| Need structured pricing tables | Portal (MagicBricks has best tables) |
| Need developer name, units, RERA | Google Search AI Overview (covers all) |
| Need Google Maps reviews/rating | Google Search (business panel on right side) |
| Portal URLs for source links | Google Search results show portal URLs even if pages themselves are blocked |

### Why This Works

Google's AI Overview scrapes multiple real estate portals and aggregates the data into a structured summary. It bypasses individual portal bot protection because Google itself is whitelisted by these portals. The data quality is comparable to visiting each portal individually, though you may lose some fine-grained details (individual listing prices, floor-wise variation).

### Supplementing with Google Maps Business Panel

When searching on Google, most projects have a **Google Maps business panel** on the right side of the search results page. This panel includes:
- Google ratings (e.g., 4.4★, 47 reviews)
- Address with coordinates
- Phone number
- Website link
- Direction links

Scrape this by checking the right sidebar of the search results page (the snapshot will show a `heading "Project Name"` with rating info below it).

### Limitations

- **Not all projects have AI Overview coverage** — very new or very small projects may not appear. Fall back to DuckDuckGo search (see below) or location-based estimation.
- **Price ranges can vary by source** — the AI Overview may show a wider range than individual portal pages. Use the median or most common figure.
- **Possession dates may be approximate** — always cross-reference with the developer's own website if possible.
- **No floor plans or detailed amenity lists** — AI Overview only gives high-level summary data.

---

## DuckDuckGo Lite for Portal URL Research

When Firecrawl/web tools are unavailable or portals block automated access (MagicBricks, 99acres block API/bot traffic), use **DuckDuckGo Lite** (`lite.duckduckgo.com/lite/`) — it's a lightweight HTML search that works with curl or Python urllib.

### Technique: Direct HTTP Search

```python
import urllib.parse, urllib.request, re

def search_ddg(query):
    """Search DuckDuckGo Lite for real estate portal URLs."""
    url = 'https://lite.duckduckgo.com/lite/'
    data = urllib.parse.urlencode({'q': query}).encode()
    req = urllib.request.Request(url, data=data,
        headers={'User-Agent': 'Mozilla/5.0'})

    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8', errors='replace')

    # Extract portal URLs from results
    results = []
    for match in re.finditer(r'<a[^>]*href="(https?://[^"]+)"[^>]*>', html):
        url = match.group(1)
        if 'magicbricks.com' in url or '99acres.com' in url:
            if url not in results:
                results.append(url)
    return results

# Search for a project
urls = search_ddg("Prestige Sanctuary MagicBricks 99acres Bangalore villa")
# Returns: [magicbricks_URL, 99acres_URL, ...]
```

### Alternative: Browser-Based DDG Lite (when browser tool is available)

Use `browser_navigate` to `https://lite.duckduckgo.com/lite/?q={query}`. DDG Lite renders as plain HTML with no CAPTCHA for subsequent searches in the same session. Results appear in a table format with link URLs visible.

**Workflow for price verification:**
1. `browser_navigate(url="https://lite.duckduckgo.com/lite/?q=PROJECT+LOCATION+price+sqft")`
2. Read the snapshot — each result row shows: number, link title, description snippet, and URL
3. Extract portal URLs (MagicBricks: `pdpid-XXXX`, 99acres: `npxid-rXXXX`)
4. Note price data from description text (snippets often contain pricing info)
5. For more data on a specific project, click the URL to open the portal page

**When to use which:** Prefer the browser approach when the browser tool is available — it handles ephemeral CAPTCHAs and gives richer result context. Use the HTTP approach for batch searches where browser cycles are limited.

### Search Query Patterns

Use location-specific queries:

| Project Type | Query Pattern | Example |
|-------------|--------------|---------|
| Villa project | `"{project} MagicBricks 99acres Bangalore villa"` | `"Prestige Sanctuary MagicBricks 99acres Bangalore villa"` |
| Plot project | `"{project} MagicBricks Bangalore plot"` | `"Godrej Reserve Devanahalli MagicBricks Bangalore plots"` |
| Apartment | `"{project} MagicBricks {location} apartment"` | `"Prestige Lily Creek Devanahalli MagicBricks apartment"` |

### Portals supported

- `magicbricks.com` — best coverage for Bangalore projects
- `99acres.com` — good for both new projects and resale listings
- Housing.com, NoBroker, CommonFloor — can be found similarly but less reliably via DDG Lite

### Pitfalls

- **Rate limiting**: DDG Lite doesn't heavily rate-limit but be polite — add 1-2 second delays between searches
- **One-time CAPTCHA**: The lite interface may show a CAPTCHA on first use via curl. If blocked, open `lite.duckduckgo.com/lite/` in a browser once to pass the CAPTCHA (sessions persist for a while). For batch searches via script, this is rarely an issue.
- **Generic results for small projects**: Smaller/niche projects may not have dedicated portal pages — fall back to Google Maps link only and note "not found on portals" in the slide
- **URL patterns**: MagicBricks uses `/pdpid-XXXX` or `/pppfs` suffixes, 99acres uses `/npxid-rXXXXX` — these are stable project identifiers, not session tokens

## Total Price Estimation from Sheet Data

When the sheet provides per-sq.ft prices but no total price:

```python
min_size, max_size = 1170, 2215
min_psf, max_psf = 9500, 10800
total_min = round(min_size * min_psf / 10000000, 2)
total_max = round(max_size * max_psf / 10000000, 2)
total_price = f"₹{total_min:.2f}-{total_max:.2f} Cr"
```

## Enriching Existing Presentations (vs Create-From-Scratch)

When the user asks to add data (maps links, RERA, land area, source URLs, demand drivers) to an existing Google Slides deck:

1. **Export PPTX** via `build_service(drive, v3).files().export_media()` with the presentation mimeType
2. **Parse slides** — identify project slides vs section headers by scanning first text for project name matches
3. **Add metadata footer bars** using the two-line pattern in [edit-existing-google-slides-pptx.md](edit-existing-google-slides-pptx.md) — Line 1: clickable Maps + source links, Line 2: land area + RERA + developer
4. **Add demand drivers** — extend the Key Developments slide with a Why-This-Location section (STRR, industrial employment, rail, overflow demand)
5. **Verify** — re-read from disk after save, check each slide for expected content
6. **Upload** — delete old file (creates new file ID), create new with Google Slides MIME type, re-share with user
