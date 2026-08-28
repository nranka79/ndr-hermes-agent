# Villa Development Market Research (python-pptx)

## When to Use

Use this workflow when building a market research report for a **proposed villa/plotted development** project — typically 5-20 acres in a growth corridor. The deck covers: subject land analysis, competitor villa projects, competitor plotted developments, infrastructure, demand drivers, product-fit analysis, price comparison, and pricing recommendation.

**Differences from Apartment Market Research** (`real-estate-market-research-slides.md`):

| Aspect | Apartment Report | Villa Report |
|--------|-----------------|--------------|
| Competitors | Only apartment projects | Villas + Plots + Mixed, separate sections |
| Product-fit | N/A | 3 options: Plots / Built-to-Suit / Mixed |
| Demand section | Implicit in pricing | Explicit buyer profile + velocity indicators |
| Recommendation | Pricing only | Product type + Pricing + Sales Strategy + Financials |
| Price comparison | Single table | Two tables (villas and plots side-by-side) |

## CRITICAL: Data Source Hierarchy — Sheet Before Web

**The user's Google Sheet is the single source of truth — not web research.** In the Thylagere session, web research (MagicBricks/99acres browser extraction) produced prices 10-30% HIGHER than the user's spreadsheet data:

[... existing content unchanged ...]

## CRITICAL: Document vs Slides Format Decision

**Data-heavy feasibility studies (cost sheets, multi-scenario P&L, competitor tables, buyer personas, risk matrices) belong in a Google Doc, NOT in slides.** Prakash explicitly stated: "slides will not be able to accommodate all the data" after receiving a 14-slide deck that couldn't fit the full cost breakdown and scenario analysis.

**Decision rule:**
- Use **Google Slides / PPTX** when: presenting to clients/investors, visual impact matters, 8-15 slides with key highlights, charts, and summary tables
- Use **Google Doc** when: the user asks for a "comprehensive development proposal," the content includes full cost sheets with line-item breakdowns, 3+ detailed scenario tables, >20 competitor entries, multi-section analysis with sub-headings, or the user explicitly says "the slides won't accommodate the data"

**If you're unsure, ask.** The doc format is always safer for data density — it can be converted to a summary deck later.

| Project | Web research (browser) | Sheet (authoritative) |
|---------|----------------------|----------------------|
| Prestige Sanctuary | ₹16,850-22,000/sq.ft | ₹15,400+ /sq.ft |
| Godrej Reserve | ₹8,000-9,500/sq.ft | ₹7,200-8,500/sq.ft |
| DNR Solace | ₹8,300-8,750/sq.ft | ₹6,220-7,500/sq.ft |
| Esteem Misty Hills | ₹6,500-7,500/sq.ft | ₹5,800-6,800/sq.ft |
| Over the Rainbow | ₹16,500-18,000/sq.ft | ₹15,000-17,500/sq.ft |

**Why portal prices differ from the sheet:**
- Portals show ASKING prices of remaining higher-end inventory (survivorship bias)
- The user's sheet reflects developer-quoted base prices or averages across all units
- Different phases / inventory mixes produce different per-sq.ft rates
- Individual resale listings on portals are not representative of the project-wide average

**🎯 The rule: when the user sends a sheet mid-session, STOP using web-researched prices immediately. Rebuild from the sheet data.**

**Mitigation when no sheet is available (pure web research):**
- Cross-verify each project across 3+ sources (MagicBricks, 99acres, official site, housing.com)
- For sold-out projects, use **resale listing prices** not builder list prices
- Always tag prices with the month/year of research
- When portal data seems low vs peers, treat it as suspect and dig deeper with browser tool
- **But understand: the user's own data (when provided) overrides everything**

## Workflow

### Step 1: Extract Location Data from My Maps

When the user shares a Google My Maps link for the proposed land:

```python
# Use browser to view the My Maps
# The URL pattern is:
# https://www.google.com/maps/d/edit?mid=XXXXXXXXXXXXX&usp=sharing

# Navigate in browser to extract:
# - Map title (often contains acreage + area name)
# - Coordinates from the "Proposed Land" layer
# - Layer names and their project markers
# - Villa project names (one layer)
# - Plotted development names (another layer)
```

**Browser extraction tips:**
- Toggle layers on/off by clicking checkboxes
- Click layer names to expand marker details
- Vision/screenshot can capture the listed project names
- Coordinates appear in the layer details when expanded
- The URL parameter `ll=lat,lng` in the viewer URL gives center coordinates

### Step 2: Research Competitor Pricing

For each project identified in My Maps, research current pricing:

```python
# Search pattern for villa projects
web_search(f"<Project Name> <Area> Bangalore villa price per sqft 2026")

# For plotted developments
web_search(f"<Project Name> <Area> plotted development price")
```

**Key data points to collect per project:**
- Developer name
- Project size (acres)
- Total units/plots
- Configuration (bedrooms, built-up area)
- **Current price rate (₹/sq.ft range) — VERIFIED against actual Jul 2026 listings**
- **Total price range (e.g. ₹5.5 Cr — ₹8.7 Cr)**
- **🚀 LAUNCH PRICE — per sq.ft and total. Research from official microsites, older listings, RERA docs**
- **🚀 LAUNCH DATE — month and year. Available from RERA registration date, news articles, project blog posts**
- **📈 APPRECIATION — calculate percentage increase from launch to current for the slide**
- Status (Ready to Move / Under Construction / Pre-Launch)
- RERA number — VERIFY from official RERA website or multiple consistent sources
- Location / distance to key landmarks
- Google Maps link — construct as `https://maps.google.com/?q=<Project+Name+Area+City>`
- MagicBricks listing URL — actual working project page URL
- 99acres listing URL — actual working project page URL
- Notes on unique selling points

**Pricing range sources:**
- Search results descriptions often quote ranges
- MagicBricks and 99acres listing pages (high confidence)
- Project brochure sites
- Portal search pages (use when direct listing page is blocked)
- Note the source date — real estate prices change quarterly

### Step 3: Categorize Competitors

Group projects identified from My Maps into:

```
VILLA DEVELOPMENTS (built villas, not plots)
  - Luxury tier: ₹10,000+/sq.ft (e.g., Prestige Sanctuary, Total Environment)
  - Mid-premium: ₹5,000-9,999/sq.ft (e.g., Signature One, Triton)
  - Entry-level: < ₹5,000/sq.ft (e.g., 99D, Canterbury Orchards)

PLOTTED DEVELOPMENTS (villa plots)
  - Premium: ₹5,000+/sq.ft (e.g., Montira, Chartered Fireflies)
  - Mid: ₹3,000-5,000/sq.ft (e.g., DNR Solace, Godrej Reserve)
  - Value: < ₹3,000/sq.ft (e.g., Song of the Winds)
```

### Step 4: Build the Presentation (python-pptx)

Use the DRAAS dark theme palette defined below. The deck structure:

```
1.  Title Slide — project name, acreage, location corridor
2.  Subject Land Details — coordinates, area, distances to key landmarks
3.  Location USP & Connectivity — connectivity highlights + location advantages + market insight callout
4.  Villa Developments Overview — intro slide with summary metrics
5-11. Individual Villa Project Slides (one per competitor) — pricing + specs + location + key takeaways
12. Plotted Developments Overview — intro slide with summary metrics
13-14. Plotted Project Slides — project cards + combined slides
15. Key Developments & Infrastructure — transport, employment, social, upcoming projects
16. Demand Drivers & Sales Velocity — 6 primary demand drivers + velocity indicators
17. Product-Fit Analysis — 3 options side by side
18. Price Comparison — two-column table (villas left, plots right)
19. Pricing Recommendation — product strategy, positioning, sales strategy, financial projection
| 20. Closing Slide

### Review Slides — Market Sentiment Section (added in v3)

After EVERY competitor project slide, insert a review/sentiment slide with this 4-section dark-theme layout:

```
┌─────────────────────────────────────────────┐
│  ★ Project Name — Market Review          ← navy bar, gold text
├─────────────────────────────────────────────┤
│  CUSTOMER & MARKET REVIEW                ← gold label badge
│                                             │
│  ✅ HIGHLIGHTS                             │
│  Buyers praise brand trust, on-time        │
│  delivery, airport proximity...            │
│                                             │
│  ⚠️ CONCERNS                               │
│  Premium pricing, limited social infra...  │
│                                             │
│  📊 MARKET REPUTATION                      │
│  Strongly Positive ⭐ 4.2-4.5/5...          │
│                                             │
│  💡 WHY BUY / INVEST                       │
│  Brand trust, airport proximity, ready     │
│  possession, rental potential...           │
│                                             │
│  📍 Google Maps: ... | 🏠 MB: ... | 🏘️ 99A: ...  (source URLs)
└─────────────────────────────────────────────┘
```

**Key layout rules:**
- Very dark navy background (`#0A1628` — same family as slide backgrounds)
- Gold title bar (`#16213A` bg, `#D4A53C` text) with ★ prefix
- "CUSTOMER & MARKET REVIEW" gold badge below title
- Four sections in vertical stack with colored headers:
  - ✅ HIGHLIGHTS (gold)
  - ⚠️ CONCERNS (red `#E74C3C`)
  - 📊 MARKET REPUTATION (gold)
  - 💡 WHY BUY / INVEST (gold)
- Body text in light grey (`#CCCCCC`), 10pt
- Source URL footer at bottom in small grey text (7pt, `#888888`) listing Google Maps, MagicBricks, 99acres URLs
- Each review slide follows immediately after its corresponding project slide

**python-pptx construction:**
```python
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from lxml import etree
from pptx.oxml.ns import qn

def add_review_slide(prs, proj_name, review_data, sources, after_index):
    """
    Adds a review slide and reorders it after the project slide.
    review_data = {'highlights': str, 'concerns': str, 'reputation': str, 'why_buy': str}
    sources = {'maps': url, 'mb': url_or_None, 'acres': url_or_None}
    """
    sw = prs.slide_width
    blank = [l for l in prs.slide_layouts if l.name == 'BLANK'][0]
    new_slide = prs.slides.add_slide(blank)
    
    # Dark background
    bg = etree.SubElement(new_slide._element.find(qn('p:cSld')), qn('p:bg'))
    bgFill = etree.SubElement(bg, qn('a:solidFill'))
    etree.SubElement(bgFill, qn('a:srgbClr')).set('val', '0A1628')
    
    y = Emu(1300000)
    line_h = Emu(260000)
    
    def add_section(slide, y_pos, header, content, header_color='D4A53C'):
        add_textbox(slide, Emu(300000), y_pos, Emu(11000000), line_h,
                    header, fs=13, bold=True, color=header_color)
        y_pos += line_h + Emu(20000)
        add_textbox(slide, Emu(400000), y_pos, Emu(10900000), Emu(1350000),
                    content, fs=10, color='CCCCCC')
        return y_pos + Emu(1400000)
    
    # Add each section
    y = add_section(new_slide, y, f"✅ HIGHLIGHTS", review_data['highlights'])
    y = add_section(new_slide, y, f"⚠️ CONCERNS", review_data['concerns'], 'E74C3C')
    y = add_section(new_slide, y, f"📊 MARKET REPUTATION", review_data['reputation'])
    y = add_section(new_slide, y, f"💡 WHY BUY / INVEST", review_data['why_buy'])
    
    # Source footer
    parts = [f'📍 Google Maps: maps.google.com/?q={proj_name.replace(" ", "+")}+Devanahalli+Bangalore']
    if sources.get('mb'): parts.append(f'🏠 MagicBricks: {sources["mb"]}')
    if sources.get('acres'): parts.append(f'🏘️ 99acres: {sources["acres"]}')
    ft = add_textbox(new_slide, Emu(300000), y + Emu(500000), Emu(11000000), Emu(400000),
                     ' | '.join(parts), fs=7, color='888888')
    
    # Reorder: insert right after the project slide using sldIdLst manipulation
    sldIdLst = prs._element.find(qn('p:sldIdLst'))
    all_ids = list(sldIdLst.findall(qn('p:sldId')))
    new_id = all_ids[-1]  # Last added slide
    
    # Move from last position to after the project slide
    sldIdLst.remove(new_id)
    ref_child = all_ids[after_index] if after_index < len(all_ids)-1 else None
    if ref_child is not None:
        # Find ref_child in current list (indices shifted after remove)
        for idx, child in enumerate(sldIdLst):
            if child.get(qn('r:id')) == ref_child.get(qn('r:id')):
                sldIdLst.insert(idx + 1, new_id)
                break
    else:
        sldIdLst.append(new_id)

def add_textbox(slide, left, top, width, height, text, fs=12, bold=False, color='FFFFFF', align=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    run = p.add_run(); run.text = text
    run.font.size = Pt(fs); run.font.bold = bold
    run.font.color.rgb = RGBColor(*bytes.fromhex(color))
    return txBox
```

**Researching review content:**
Each review needs 4 condensed paragraphs covering:
- **Highlights** — What buyers praise (brand trust, design, location, amenities, pricing)
- **Concerns** — Common complaints (delays, location remoteness, limited amenities, builder reputation)
- **Reputation** — Portal ratings (e.g., 4.2/5), analyst/YouTube descriptions, brand standing
- **Why Buy** — Decision drivers (investment, lifestyle, affordability, brand value)

Use `delegate_task` with `toolsets=["web","search"]` to research all projects in parallel, requesting results as JSON. When web tools are unconfigured (no Firecrawl API key), fall back to training knowledge — which can provide detailed, accurate coverage of Indian real estate projects.

### Clickable Source Links

After the review slides and colour pattern are applied, use the technique in [references/python-pptx-hyperlinks.md](references/python-pptx-hyperlinks.md) to make the source labels (`📍 Maps`, `🏠 MagicBricks`, `🏘️ 99acres`) on each **project slide** clickable. Each label must be a separate run with its own hyperlink relationship on `slide.part`. Do NOT attempt this during the initial slide build — add hyperlinks as a separate pass after all review slides are inserted and reordered, because slide reordering doesn't affect shape-level content but ensures you're targeting the correct slides.
```

### Step 5: DRAAS Dark Theme python-pptx Helpers

The DRAAS dark theme uses navy/dark backgrounds with gold accents. These helpers should be defined at the top of every villa market research script:

```python
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Emu(12191675)   # 13.33" widescreen
prs.slide_height = Emu(6858000)   # 7.5"
BLANK = prs.slide_layouts[6]

# Palette
GOLD = RGBColor(0xD4, 0xA5, 0x3C)
DARK_BG = RGBColor(0x0D, 0x0D, 0x1A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0x95, 0xA5, 0xA6)
CARD = RGBColor(0x1E, 0x1E, 0x32)
SUBD = RGBColor(0x16, 0x16, 0x28)   # header bar background
GREEN = RGBColor(0x27, 0xAE, 0x60)  # positive
REDc = RGBColor(0xE7, 0x4C, 0x3C)   # negative/highlight
TEAL = RGBColor(0x29, 0x80, 0xB9)   # secondary accent
PURPLE = RGBColor(0x8E, 0x44, 0xAD) # tertiary accent

# Helpers — use SHORT names to keep layout code readable
def bg(s):
    f = s.background.fill; f.solid(); f.fore_color.rgb = DARK_BG

def T(s, l, t, w, h, txt, fs=14, b=False, c=WHITE, a=PP_ALIGN.LEFT):
    """Add textbox. Parameters: slide, left, top, width, height, text,
       font_size, bold, color, alignment."""
    bx = s.shapes.add_textbox(Emu(l), Emu(t), Emu(w), Emu(h))
    tf = bx.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = txt
    p.font.size = Pt(fs); p.font.bold = b
    p.font.color.rgb = c; p.font.name = 'Calibri'; p.alignment = a

def R(s, l, t, w, h, fill=None):
    """Add rectangle. Parameters: slide, left, top, width, height, fill_color."""
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(l), Emu(t), Emu(w), Emu(h))
    sh.line.fill.background()
    if fill: sh.fill.solid(); sh.fill.fore_color.rgb = fill
    return sh

def H(s, title, tag=''):
    """Add header bar to slide."""
    R(s, 0, 0, 12191695, 822960, fill=SUBD)
    T(s, 548640, 137160, 9144000, 550000, title, fs=30, b=True, c=GOLD)
    if tag:
        T(s, 9601200, 274320, 2200000, 256032, tag, fs=13, b=True, c=GOLD, a=PP_ALIGN.RIGHT)
    R(s, 0, 822960, 12191695, 100, fill=GOLD)
```

### Step 6a: Research Thoroughly Using Browser (Portals Block Bots)

**Critical insight: Real estate portals aggressively block automated scraping.** `web_search` returns snippets that may show old prices. Use this approach:

```python
# Step 1: Web search for initial leads
web_search(f"<Project Name> <Area> price per sqft 2026")

# Step 2: Visit ACTUAL listing pages with browser for current data
# MagicBricks and 99acres block many bots, but the browser tool renders JS
browser_navigate(f"https://www.magicbricks.com/<project-url>")
browser_snapshot()   # extract current listings

# Step 3: For launch pricing, search official sites
web_search(f"<Project Name> <builder> launch price brochure")
web_search(f"<Project Name> RERA number")

# Step 4: Verify RERA from multiple sources
# Cross-reference across 2-3 sites to avoid transcription errors
```

**Always use `delegate_task` for parallel research** — researching 14+ projects takes 5+ minutes per project. Spawn subagents with `toolsets=["web","browser"]` to research 3 projects at a time.

### Step 6b: Source Links — Mandatory for Every Project

Every project slide MUST include three source links at the bottom:
1. **📍 Google Maps** — `https://maps.google.com/?q=<Project+Name+Area+City>`
2. **🏠 MagicBricks** — Project page on magicbricks.com
3. **🏘️ 99acres** — Project page on 99acres.com

Add a source links bar at the bottom of each project slide:

```python
# Source links bar at bottom of every project slide
R(s, 457200, 6400000, 11247120, 400000, fill=RGBColor(0x0A, 0x0A, 0x15))
T(s, 548640, 6420000, 2000000, 150000, '🔗 Source Links:', fs=9, b=True, c=GOLD)
T(s, 548640, 6590000, 3800000, 150000, f'📍 Maps: {google_maps_url[:70]}...', fs=7, c=GREEN)
T(s, 548640, 6740000, 3800000, 150000, f'🏠 MB: {magicbricks_url[:70]}...', fs=7, c=GREEN)
T(s, 548640, 6890000, 3800000, 150000, f'🏘️ 99A: {ninty_acres_url[:70]}...', fs=7, c=GREEN)
```

Each villa/plotted competitor gets a dedicated slide:

```python
# Left card (55% width) — pricing + specs with alternating rows
R(s, 457200, 1097280, 5486400, 5303520, fill=CARD)
T(s, 731520, 1200000, 4937700, 300000, '💰 PRICING & SPECIFICATIONS', fs=20, b=True, c=GOLD)

specs = [
    ('CURRENT PRICE', '₹7,500 — ₹13,000/sq.ft'),
    ('TOTAL PRICE', '₹5.5 Cr — ₹8.7 Cr'),
    # ... more rows
]
y = 1600000
for label, value in specs:
    R(s, 731520, y, 1200000, 260000, fill=RGBColor(0x2A, 0x2A, 0x40))
    T(s, 777240, y+8000, 1100000, 240000, label, fs=11, b=True, c=GOLD)
    T(s, 2000000, y+8000, 3500000, 240000, value, fs=12, c=WHITE)
    y += 300000

# Right panel (45% width) — location + key takeaways
R(s, 6400800, 1097280, 5486400, 5303520, fill=RGBColor(0x1A, 0x1A, 0x2E))
T(s, 6674400, 1200000, 4937700, 250000, '📍 LOCATION', fs=16, b=True, c=GOLD)
T(s, 6674400, 1480000, 4937700, 1800000, location_text, fs=12, c=WHITE)
T(s, 6674400, 3400000, 4937700, 250000, '🎯 KEY TAKEAWAYS', fs=16, b=True, c=GOLD)
T(s, 6674400, 3700000, 4937700, 2500000, takeaways_text, fs=12, c=LIGHT)
```

### Step 7: Competitor Project Slide Template (With Source Links)

Each villa/plotted competitor gets a dedicated slide. The layout has:
- **Left card (55%)** — Pricing (current highlighted in red, launch in green) + spec rows
- **Right panel (45%)** — Location context + key takeaways + appreciation
- **Bottom bar** — Source links (Google Maps, MagicBricks, 99acres)

```python
def project_slide(s, p):
    """p dict keys: name, tag, builder, curr (current price),
       lp (launch price), ld (launch date), specs (list of tuples),
       loc (location text), take (takeaways), ap (appreciation),
       gm (google maps url), mb (magicbricks url), n9 (99acres url)"""
    
    T(s, 8500000, 200000, 3500000, 300000, p['builder'], fs=12, c=LIGHT, a=PP_ALIGN.RIGHT)
    R(s, 457200, 1097280, 5486400, 5304000, fill=CARD)
    
    T(s, 731520, 1200000, 4937700, 300000, '💰 PRICING & SPECIFICATIONS', fs=20, b=True, c=GOLD)
    
    # CURRENT PRICE — highlighted in red
    R(s, 731520, 1550000, 4937700, 300000, fill=RGBColor(0x2A, 0x2A, 0x40))
    T(s, 777240, 1565000, 2300000, 130000, 'CURRENT PRICE (Jul 2026)', fs=10, b=True, c=REDc)
    T(s, 777240, 1700000, 4600000, 150000, p['curr'], fs=14, b=True, c=WHITE)
    
    # LAUNCH PRICE — in green
    R(s, 731520, 1880000, 4937700, 250000, fill=RGBColor(0x2A, 0x2A, 0x40))
    T(s, 777240, 1900000, 2300000, 110000, 'LAUNCH PRICE', fs=10, b=True, c=GREEN)
    T(s, 777240, 2020000, 4600000, 140000, p['lp'], fs=11, c=LIGHT)
    
    # LAUNCH DATE — tag
    R(s, 731520, 2160000, 2400000, 200000, fill=RGBColor(0x2A, 0x2A, 0x40))
    T(s, 777240, 2175000, 2200000, 180000, f"🚀 {p['ld']}", fs=11, b=True, c=GOLD)
    
    # Spec rows
    y = 2450000
    for lbl, val in p['specs'][:8]:
        R(s, 731520, y, 1300000, 250000, fill=RGBColor(0x2A, 0x2A, 0x40))
        T(s, 777240, y+8000, 1200000, 230000, lbl, fs=10, b=True, c=GOLD)
        T(s, 1400000+731520, y+8000, 3800000, 230000, val, fs=10, c=WHITE)
        y += 285000
    
    # Right panel — location + takeaways + appreciation
    R(s, 6400800, 1097280, 5486400, 5304000, fill=RGBColor(0x1A, 0x1A, 0x2E))
    T(s, 6674400, 1200000, 4937700, 250000, '📍 LOCATION', fs=16, b=True, c=GOLD)
    T(s, 6674400, 1500000, 4937700, 1200000, p['loc'], fs=11, c=WHITE)
    T(s, 6674400, 2900000, 4937700, 250000, '🎯 KEY TAKEAWAYS', fs=14, b=True, c=GOLD)
    T(s, 6674400, 3180000, 4937700, 1400000, p['take'], fs=10, c=LIGHT)
    T(s, 6674400, 5100000, 4937700, 200000, '📈 Appreciation: ' + p['ap'], fs=11, b=True, c=GOLD)
    
    # Source links bar at bottom
    R(s, 457200, 6400000, 11247120, 400000, fill=RGBColor(0x0A, 0x0A, 0x15))
    T(s, 548640, 6420000, 2000000, 150000, '🔗 Source Links:', fs=9, b=True, c=GOLD)
    T(s, 548640, 6590000, 3800000, 150000, f'📍 Maps: {p["gm"][:70]}...', fs=7, c=GREEN)
    T(s, 548640, 6740000, 3800000, 150000, f'🏠 MB: {p["mb"][:70]}...', fs=7, c=GREEN)
    T(s, 548640, 6890000, 3800000, 150000, f'🏘️ 99A: {p["n9"][:70]}...', fs=7, c=GREEN)
```

Three options with recommendation badge:

```python
options = [
    ('OPTION A: Premium Villa Plots', '🏆 RECOMMENDED', description_text),
    ('OPTION B: Built-to-Suit Villas', 'HIGHER MARGIN', description_text),
    ('OPTION C: Mixed (Plots + Model Villas)', 'BALANCED APPROACH', description_text),
]

y = 1600000
for opt_name, tag, desc in options:
    R(s, 731520, y, 10700000, 1500000, fill=RGBColor(0x2A, 0x2A, 0x40))
    T(s, 777240, y+15000, 4000000, 250000, opt_name, fs=16, b=True, c=GOLD)
    R(s, 5000000, y+15000, 1800000, 250000, fill=GOLD)
    T(s, 5100000, y+25000, 1600000, 230000, tag, fs=11, b=True, c=DARK_BG, a=PP_ALIGN.CENTER)
    T(s, 777240, y+320000, 10300000, 1100000, desc, fs=11, c=WHITE)
    y += 1600000
```

### Step 8: Price Comparison — Two-Column Layout

Slide 18 should have two tables side by side. Use this pattern:

```python
# Villa projects — left column (starting at x=731520)
# Header row
R(s, 731520, 1500000, 5000000, 350000, fill=RGBColor(0x3A, 0x3A, 0x50))
T(s, 777240, 1520000, 5000000, 300000, '🏡 VILLA DEVELOPMENTS', fs=16, b=True, c=GOLD)

y = 1900000
for proj, rate, price in villas_data:
    R(s, 731520, y, 5000000, 260000, fill=RGBColor(0x2A, 0x2A, 0x40))
    T(s, 777240, y+15000, 2200000, 230000, proj, fs=10, c=WHITE)
    T(s, 3100000, y+15000, 1800000, 230000, rate, fs=10, c=WHITE)
    T(s, 5000000, y+15000, 1500000, 230000, price, fs=10, c=WHITE)
    y += 275000

# Highlight proposed row with gold background
R(s, 731520, y, 5000000, 260000, fill=RGBColor(0x3A, 0x2A, 0x10))
T(s, 777240, y+15000, 2200000, 230000, 'PROPOSED Development', fs=10, b=True, c=GOLD)
T(s, 3100000, y+15000, 1800000, 230000, '₹7,000-9,500/sq.ft', fs=10, b=True, c=GOLD)
T(s, 5000000, y+15000, 1800000, 230000, '₹2.5-4.5 Cr', fs=10, b=True, c=GOLD)

# Repeat for Plotted Developments — right column (x=6400800)
```

### Step 9: Pricing Recommendation — 4 Cards

```python
recs = [
    ('PRODUCT STRATEGY', GREEN, 'Option A (Recommended): Premium Villa Plots...'),
    ('POSITIONING', TEAL, 'Target Segment: ...'),
    ('SALES STRATEGY', PURPLE, 'Pre-launch: ...'),
    ('FINANCIAL PROJECTION', GOLD, 'Land: ~10 Acres...'),
]

y = 1600000
for title, color, desc in recs:
    R(s, 731520, y, 10700000, 1100000, fill=RGBColor(0x2A, 0x2A, 0x40))
    R(s, 731520, y, 10700000, 60000, fill=color)  # colored top accent bar
    T(s, 777240, y+80000, 5000000, 250000, title, fs=16, b=True, c=color)
    T(s, 777240, y+330000, 10200000, 800000, desc, fs=10, c=WHITE)
    y += 1150000
```

### Step 10: Upload and Share

```python
from tools import gws_skill_bridge

# Upload as PPTX (not auto-converted to Slides)
result = gws_skill_bridge.call('drive_upload', service_name='google-draas',
    path="/tmp/file.pptx",
    mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    name="Thylagere ~10 Acres — Villa Development Market Research.pptx",
    parent=None)   # MUST pass parent=None to avoid AttributeError

upload = json.loads(result)
file_id = upload['id']

# Share with the requesting user (CRITICAL — file is in authenticated account's Drive)
gws_skill_bridge.call('drive_share', service_name='google-draas',
    file_id=file_id, role='writer', type='user',
    email='psingh@draas.com', notify=True)
```

## Pitfalls

- **Drive upload `parent` parameter**: When using `gws_skill_bridge.call('drive_upload', ...)`, you MUST pass `parent=None` (or `parent=''`) even if you don't want to put the file in a specific folder. The underlying function checks `if args.parent:` and crashes with AttributeError if the key is absent from kwargs.
- **Drive upload parameter name**: The parameter is `path=`, not `file_path=` or `file=`. Error: `'no attribute path'`.
- **Drive delete parameter**: Pass `permanent=False` explicitly to avoid `AttributeError` on the `permanent` attribute.
- **DRAAS account sharing**: When uploading under `google-draas` (Nishant's account), ALWAYS share with `psingh@draas.com` after upload. The file is owned by Nishant's Drive, not Prakash's.
- **My Maps data extraction**: The My Maps page loads markers dynamically. Use the browser tool to navigate, click layers to expand, and take screenshots. The coordinates may need JavaScript extraction from the page URL's `ll` parameter.
- **Data source priority**: When the user provides a sheet, IT is authoritative — web/browser prices are secondary. Sheet prices can be 10-30% LOWER than browser-extracted portal prices (portals show highest remaining inventory). Always rebuild from the sheet, don't just update individual fields.
- **Memory limit with python-pptx**: Each slide with shapes and textboxes consumes memory. For 20+ slides, building in a single script is fine, but for 40+ slides, consider saving intermediates or using subagents.
- **Competitor count balance**: Don't put 12 villa projects but only 3 plotted projects — the user's My Maps may have them in different layers. Include ALL projects marked on the map, even if some have sparse data.
- **Helper function naming collision**: When defining `T(s, l, t, w, h, txt, fs=14, b=False, ...)` where `b` is the bold parameter, the variable name `b` for the textbox shape inside the function overrides the parameter. Use a different variable name (e.g., `bx`) for the textbox shape:
  ```python
  def T(s, l, t, w, h, txt, fs=14, b=False, ...):
      bx = s.shapes.add_textbox(...)
      p.font.bold = b    # b is the parameter, not the shape
  ```
- **`parent=None` for drive_share**: Not needed — `drive_share` doesn't reference `args.parent`, only `args` attributes set by kwargs. Only `drive_upload` needs it.
- **Launch price research**: Not all projects have publicly archived launch prices. For older projects (10+ years), launch price may only appear in archived blog posts or RERA docs. Note it as "N/A" rather than guessing.
- **Dual pricing format is MANDATORY**: Prakash explicitly said "I dont understand the prices" when given single-format pricing. Every project's current price AND launch price must show BOTH:
  - Absolute total: `₹X Cr — ₹Y Cr`
  - Per-sqft rate: `₹X,XXX — ₹Y,YYY/sqft`
  - This applies to all pricing fields on every project slide and in the price comparison summary.
- **99acres CAPTCHA**: 99acres aggressively blocks automated access with CAPTCHAs. The URL is still correct and works when opened in a real browser — note this to the user if they report broken links.

## Example: Thylagere ~10 Acres Deck (v2, 2026-07-17 — Sheet-Corrected)

The deck built using this workflow had:
- **23 slides** covering 6 villa + 7 plotted projects (data sourced from user's "Projects near Golfshire" sheet)
- Subject land: Thylagere, Devanahalli, North Bangalore (13°19'17.9″N 77°40′44.1″E)
- Villa price range: **₹4,800-17,500/sq.ft** across 6 projects
- Plot price range: **₹4,200-8,500/sq.ft** across 7 projects
- All projects have: launch price, launch date, appreciation %, RERA, Google Maps, MagicBricks, 99acres links
- Recommended positioning: Premium Villa Plots at ₹4,500-6,500/sq.ft
- Drive ID (v2, sheet-corrected): `19a0S6UE8K-X_8qCCodCGtklocaEQ2UG1`
- Key lesson: The user's "Projects near Golfshire" sheet had more accurate pricing than browser-extracted portal data. Always use the sheet when the user provides one.
