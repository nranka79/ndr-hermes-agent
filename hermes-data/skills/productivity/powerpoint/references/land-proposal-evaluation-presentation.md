# Land Proposal Evaluation Presentations (Ranka Amber Template Pattern)

## When to Use

Build a land proposal evaluation presentation when the user provides a **My Maps link for a raw land parcel** (not an existing project) and asks for a project proposal "in the lines of Ranka Amber" or similar reference project. The pattern evaluates a site for acquisition/development, modeled after DRAAS's standard project presentation format.

## Template Structure (22 slides)

| # | Slide | Content |
|---|-------|---------|
| 1 | **Title** | Project code, land area, "Land Proposal Evaluation Report", location, CONFIDENTIAL |
| 2 | **Land Proposal Overview** | Key stats cards (area, sq.ft land, est. FSI, est. cost/sq.ft), Land at a Glance table (property name, location, area, dev type, zoning), Proposed Use table (est. FSI, built-up, units, asking price) |
| 3 | **Location & Connectivity** | Key highlights (metro, roads, IT hubs, malls, hospitals, schools) + Market context (avg property rates by source, land rates, annual appreciation) |
| 4 | **Development Potential Analysis** | Two scenarios side-by-side (Scenario A: Mid-Rise Apartments — RECOMMENDED, Scenario B: Boutique Villas — ALTERNATIVE), each with land area, FSI, built-up, unit count, est. sell price, revenue, cost, margin. Market comparability box with ✅ references to similar projects and final recommendation. |
| 5 | **Vicinity Projects Overview** | Summary stats (project count, min/max/avg price, year range), project categories by type (New Premium Launches, Established RTM, Mature Communities), source attribution footer |
| 6-18 | **Individual Project Slides** | Each with: verified current price (22pt, highlighted), launch price, quick facts (type, status, units, floors, sizes, developer), project details table (11 fields), source links (📍 Maps · 🏠 MagicBricks · 🏘️ 99acres) |
| 19 | **Key Developments** | 5 categories × 4 items each (IT Hubs, Shopping, Healthcare, Education, Transport) + Market highlights box |
| 20 | **Price Comparison Table** | All projects sorted newest→oldest with rank, name (clickable → Maps), location, price range, note about recommended strategy |
| 21 | **Acquisition Summary** | Land acquisition details table (title, zoning, asking price, est. cost at various rates), Project financials (cost, revenue, construction, soft costs, financing, net profit, margin, payback), Risk factors section (title, volatility, competition, approvals, absorption) |
| 22 | **Closing** | Same style as title — project code, land area, CONFIDENTIAL |

## Two-Scenario Analysis Pattern

Always present TWO development scenarios on the same slide:

```
┌─ SCENARIO A: MID-RISE APARTMENTS ────┐  ┌─ SCENARIO B: BOUTIQUE VILLAS ──────┐
│ ✅ Recommended                       │  │ 🔶 Alternative — Higher ticket       │
│ Land Area: 2.32 Ac (1,01,059 sqft)  │  │ Land Area: 2.32 Ac (1,01,059 sqft)   │
│ FSI: 2.0                             │  │ Plot Coverage: ~35%                   │
│ Built-up: ~2,02,118 sq.ft           │  │ Built-up: ~3,000-4,000 sq.ft/villa   │
│ Units: ~72 (2/3 BHK)                │  │ Units: ~30-40 villas/row houses      │
│ Sell Price: ₹11,000-13,000/sq.ft    │  │ Sell Price: ₹14,000-16,000/sq.ft     │
│ Revenue: ~₹178-210 Cr               │  │ Revenue: ~₹150-180 Cr                │
│ Margin: 20-25%                       │  │ Margin: 18-22%                       │
└──────────────────────────────────────┘  └──────────────────────────────────────┘
```

### Financial Projection Formula

```
Total Built-up = Land Area × FSI
Saleable Area = Total Built-up × 0.80 (80% efficiency)
Units = Saleable Area / avg. unit size
Gross Revenue = Saleable Area × avg. sell price/sq.ft
Construction Cost = Total Built-up × ₹4,000-5,500/sq.ft
Soft Costs = 8-10% of construction
Financing = 12% p.a. × 18 months × (Land + Construction)
Net Profit = Revenue - (Land + Construction + Soft + Financing)
Margin = Net Profit / Total Cost
```

## Python Build Script Pattern (python-pptx)

Use the same build script pattern as the Ranka Amber template. Key components:

### Color Palette
```python
GOLD = RGBColor(0xD4, 0xA5, 0x37)
BLUE = RGBColor(0x00, 0x7B, 0xFF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LGRAY = RGBColor(0xCC, 0xCC, 0xCC)
SUB = RGBColor(0xAA, 0xAA, 0xAA)
BG = RGBColor(0x1A, 0x1A, 0x2E)       # dark navy background
CARD = RGBColor(0x1E, 0x2A, 0x45)      # card background
ORANGE = RGBColor(0xFF, 0x95, 0x00)
GREEN = RGBColor(0x00, 0xC8, 0x53)
```

### Helper Functions
```python
def bg(slide, c=BG):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = c

def rect(slide, l, t, w, h, c):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = c
    s.line.fill.background()
    return s

def tb(slide, l, t, w, h, txt, sz=14, bold=False, c=WHITE, al=PP_ALIGN.LEFT):
    bx = slide.shapes.add_textbox(l, t, w, h)
    bx.text_frame.word_wrap = True
    p = bx.text_frame.paragraphs[0]
    p.text = txt
    p.font.size = Pt(sz)
    p.font.bold = bold
    p.font.color.rgb = c
    p.font.name = 'Calibri'
    p.alignment = al
    return bx

def hlink(slide, l, t, w, h, display, url, sz=11, c=BLUE):
    bx = slide.shapes.add_textbox(l, t, w, h)
    bx.text_frame.word_wrap = True
    p = bx.text_frame.paragraphs[0]
    p.font.size = Pt(sz)
    p.font.name = 'Calibri'
    run = p.add_run()
    run.text = display
    run.font.size = Pt(sz)
    run.font.color.rgb = c
    run.font.name = 'Calibri'
    run.hyperlink.address = url
    return bx
```

### Competitor Project Data Schema

Each project in the vicinity gets this data structure:

```python
{'name':'Prestige Evergreen','year':'2025','type':'Premium High-rise','dev':'Prestige Group',
 'units':'~2,000','floors':'B+G+24','bhk':'1, 1.5, 2, 3, 3.5, 4 BHK',
 'sizes':'660 — 2,400 sq.ft','land':'~45 Acres',
 'launch_price':'₹9,500/sq.ft','current_price':'₹9,500 — ₹13,500/sq.ft',
 'status':'Under Construction','rera':'PRM/KA/RERA/1251/446/PR/240109/007616',
 'mb_url':'https://www.magicbricks.com/...','ac_url':'https://www.99acres.com/...',
 'gmaps':'https://maps.google.com/?q=...','location':'Varthur-Sarjapur Road, Whitefield'}
```

### Price Research Sources (Priority Order)
1. **MagicBricks** project page — most reliable for per-sq.ft rates
2. **99acres** listings — good for resale prices
3. **Housing.com** — supplemental price ranges
4. **Google Search AI Overview** — when portals block: query `{project} {location} Bangalore price units launch`
5. **HomzNSpace / SquareYards** — supplementary

### Drive Upload (via terminal)
```python
# Must run in terminal() context, not nested in execute_code
from tools import gws_skill_bridge

result = gws_skill_bridge.call(
    'drive_upload',
    service_name='google-draas',       # or resolved account
    path='/opt/data/file.pptx',
    mime_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
    name='Project Name — Land Proposal Jul2026',
    parent=None                         # REQUIRED — bridge uses SimpleNamespace
)

# Share with user
result = gws_skill_bridge.call(
    'drive_share',
    service_name='google-draas',
    file_id='...',
    type='user',
    role='writer',
    email='user@example.com',
    notify=False
)
```

**⚠️ Bridge param quirk:** `drive_upload` requires ALL params, including `parent=None`. Missing optional params cause `AttributeError: 'SimpleNamespace' object has no attribute 'X'`.

### Account Resolution
For Prakash Singh (psingh@draas.com): maps to `google-draas` service. Verify with:
```python
from tools.gws_skill_bridge import gws_auth
print(gws_auth.EMAIL_TO_SERVICE)  # {'psingh@draas.com': 'google-draas', ...}
```

## Adding a Survey Sketch to an Existing Deck (Post-Hoc)

When the user provides a survey sketch AFTER the deck is already built, add it by modifying the .pptx directly:

```python
from pptx import Presentation
from pptx.util import Emu

prs = Presentation('/opt/data/existing_deck.pptx')
BLANK = prs.slide_layouts[6]

# Create the new slide with image
new_slide = prs.slides.add_slide(BLANK)
# ... set background, title, subtitle ...
new_slide.shapes.add_picture('/path/to/sketch.jpg',
                              Emu(300000), Emu(800000),
                              Emu(11400000), Emu(4200000))
# ... add survey summary card at bottom ...

# Reorder to position 3 (after Location slide)
sldIdLst = prs.slides._sldIdLst
new_slide_elem = sldIdLst[-1]
sldIdLst.remove(new_slide_elem)
sldIdLst.insert(3, new_slide_elem)

prs.save('/opt/data/existing_deck.pptx')
```

See `references/land-survey-sketch-integration.md` → "Insert into an Existing .pptx" section for the full technique.

The Pattandur Agrahara companion script at `/opt/data/add_survey_sketch.py` is a working example that can be adapted for other projects.

## Existing Build Scripts

| Script | Project | Purpose |
|--------|---------|---------|
| `/opt/data/build_pptx_v2.py` | Ranka Amber (0.32 Ac, 20 units) | Apartment project market research |
| `/opt/data/build_pptx2.py` | Ranka Amber (alternative) | Same project, alternative layout |
| `/opt/data/build_pattandur_proposal.py` | Pattandur Agrahara (2.32 Ac) | **Land proposal evaluation** — use as template for new land proposals |

The Pattandur Agrahara script is the most relevant for new land proposal evaluations. Copy and modify for other sites.

## Location Data Extraction from My Maps

When user provides a My Maps link for a raw land parcel:

1. **Browser approach**: Navigate to the map, use `browser_vision()` to extract layers and placemarks. Look for:
   - "Project Location and Boundary" layer → green pin + boundary polygon
   - "Apartments" / "Key Developments" layers → blue pins with project names
2. **Layer structure**: Each checkbox represents a layer. Click on individual placemarks to read their names.
3. **Land context**: Pattandur Agrahara → Whitefield corridor (metro, ITPL, malls). Use this to determine the competitive set.

## Slide-Level Patterns

### Slide 2: Overview Cards
- 4 stat cards (large gold number, white label below) in a row
- Left panel: property details (5 rows, gold dot + label + value)
- Right panel: proposed use details (5 rows, same format)
- Bottom: location category bar in card background

### Slide 3: Location & Connectivity
- Left column: Key highlights (8-10 bulleted items with emoji prefixes)
- Right column: Market context table (key-value rows with gold accent)
- Bottom: Market context summary card (cream/emphasis background)

### Slide 4: Development Potential
- Two large cards side-by-side (CARD background)
- Scenario label with ✅ or 🔶 indicator
- 10 data rows in each card (label | value format)
- Market comparability box below cards (7-9 comparison points with ✅)
- Final recommendation line in bold gold

### Slide 21: Acquisition Summary
- Land acquisition details table (title, zoning, asking price, est. cost at 3 rate tiers)
- Project financials (land+cost, revenue, construction, soft costs, financing, net profit, margin, payback)
- Risk factors (5 items with bulleted mitigants)
- Uses ORANGE for warnings, GOLD for positive metrics

## Pitfalls

- **FSI must be verified per jurisdiction**: BBMP vs BMRDA vs KIADB have different FAR tables. Don't assume FSI 2.0 — check the specific planning authority for the land.
- **Land rates vary by frontage**: Corner plots and properties on main roads command 15-25% premium over interior plots.
- **Competitor projects must be from same micro-market**: Whitefield is large — a project 5 km away may have completely different price dynamics.
- **Sheet data beats web research**: When user provides a spreadsheet with prices, treat it as authoritative over portal scrapes.
- **drive_upload parent=None**: Always pass `parent=None` explicitly — the bridge's `SimpleNamespace` doesn't auto-init missing attrs.
- **GOLD vs BLUE accent convention**: Use GOLD for current price/live data, BLUE for launch price/historical data. GOLD also for section headers, BLUE for secondary information.
