# Real Estate Market Research — Bangalore North (Devanahalli/Doddaballapur Corridor)

Research methodology for residential plot projects in Bangalore's north corridor
(Devanahalli, Doddaballapur, STRR, NH7, Aerospace Park zone).

## The Problem

Standard research paths fail in sequence:
1. **`web_search`** tool → `"No web search provider configured"` — Firecrawl/API key not set
2. **Browser + Google** → CAPTCHA block, 404 on property portals, bot detection on 99acres/MagicBricks
3. **Property portal URLs** → `99acres.com` returns 404, `magicbricks.com` returns server error, `housing.com` returns 404

## The Working Path: DuckDuckGo via `ddgs` Python Library

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.text("project name residential plots Bangalore", max_results=5):
        print(r["title"])
        print(r["href"])
        print(r["body"][:400])
```

- **No API key required** — uses DuckDuckGo HTML scraping
- **Install:** `pip install ddgs` (one-time; not pre-installed in all environments)
- **`max_results` is keyword-only** — `ddgs.text("query", 5)` raises error, use `ddgs.text("query", max_results=5)`
- **Rate limiting:** add short delays between searches if needed

## Google My Maps — Extracting Project Names from a Shared Map

When a user shares a Google My Maps link (e.g. `maps.google.com/maps/d/viewer?mid=...`), extract all placemark names via the KML feed:

```bash
# Download KML feed
curl -s "https://www.google.com/maps/d/kml?mid=<MAP_ID>&resourcekey" -o /tmp/map.zip

# Extract
unzip -o /tmp/map.zip -d /tmp/map_extract

# Parse placenames
python3 << 'EOF'
import xml.etree.ElementTree as ET

tree = ET.parse('/tmp/map_extract/doc.kml')
root = tree.getroot()
ns = {'kml': 'http://www.opengis.net/kml/2.2'}

skip_patterns = ['Directions from', 'Dabaspet', 'Thondebavi', 'Yelahanka',
                 'Hoskote', 'GITAM', 'FOXCONN', 'Harrow', 'AMITY',
                 'Subject Land', 'Proposed Land', 'Untitled layer']

for placemark in root.findall('.//kml:Placemark', ns):
    name_el = placemark.find('kml:name', ns)
    coords_el = placemark.find('.//kml:coordinates', ns)
    if name_el is None:
        continue
    name = name_el.text or ''
    if any(p in name for p in skip_patterns):
        continue
    coords = ''
    if coords_el is not None and coords_el.text:
        lon, lat = coords_el.text.strip().split(',')[0:2]
        coords = f"{lat}, {lon}"
    print(f"{name} | {coords}")
EOF
```

**Key insight:** Project names in the KML are the authoritative list — the user's voice message had corrupted/phonetic place names ("Brbilla Poole Town", "Kauribidnu Road" → Devanahalli / Doddaballapur). Extract from the map first, then search.

## Search Query Patterns for Bangalore North Real Estate

```python
# Devanahalli/Doddaballapur/STRR area — primary search template
query = "residential plots Devanahalli Doddaballapur NH7 near foxconn 2025 launched approved"

# Named project searches (use when user mentions specific projects)
projects = [
    ("Salar Puriya Sattva / Sattva Bhumi", "Sattva Bhumi plots Devanahalli price 2025"),
    ("KNS Candrill", "KNS Candrill plots Doddaballapur price RERA"),
    ("Godrej Reserve", "Godrej Reserve Devanahalli plots price 2025"),
    ("DNR Solace", "DNR Solace Devanahalli plots price"),
    ("House of Hiranandani Calgary", "House of Hiranandani Devanahalli plots price"),
    ("Century OneWorld Seraya", "Century OneWorld Seraya plots price size"),
    ("Lagos by Bricks & Milestones", "Lagos Bricks Milestones Devanahalli plots price"),
    ("Brigade Oasis", "Brigade Oasis Plots Devanahalli price"),
    ("Tata Carnatica", "Tata Carnatica plots Bangalore Devanahalli"),
    ("Rare Earth Athena", "Rare Earth Athena Devanahalli plots price"),
    ("Elite Serenity", "Elite Serenity plots Devanahalli price"),
    ("Sunshine D Greens", "Sunshine D greens Devanahalli 30 acres plots"),
    ("Northern Lights (Taapasi)", "Northern Lights plots Devanahalli Bangalore price"),
]

for name, query in projects:
    for r in ddgs.text(query, max_results=5):
        # collect results
```

## Project Data Points to Extract

For each project, aim to capture:
- **Project name** + developer
- **Location** (specific road/area — e.g., Doddaballapur Main Road, STRR, NH7, Aerospace Park)
- **Size** (total acres)
- **Number of plots / units**
- **Plot sizes** (sqft range — e.g., 1,200 / 1,500 / 2,400)
- **Price range** (starting price and max, per sqft if available)
- **Status** (New Launch / Pre-Launch / Under Construction / Ready)
- **Possession date** / expected completion
- **RERA registration number** (if available)
- **Source URL** (developer site, 99acres, MagicBricks listing)

## Key Developer Names in This Corridor

- **Sattva Group** (Salarpuria Sattva) — Sattva Bhumi, Serene Life, Doddaballapur Road
- **Century Real Estate** — Century Trails, Century OneWorld Seraya
- **Godrej Properties** — Godrej Reserve, Godrej MSR City (apartments + plots)
- **DNR Corp** — DNR Solace
- **KNS Infrastructure** — KNS Candrill
- **Brigade Group** — Brigade Oasis
- **House of Hiranandani** — Calgary (Devanahalli)
- **Tata Housing** — Tata Carnatica (Shettigere)
- **Bricks & Milestones** — Lagos
- **Rare Earth Projects** — Rare Earth Athena
- **Elite Estates** — Elite Serenity
- **Shree Hanuman Builders** — Sunshine D Greens
- **Futurearth Group** — Northern Lights

## Known STRR/Devanahalli Area Projects (Reference List)

Collected from research, May 2026:

| Project | Size | Plots | Price Start | Location |
|---------|------|-------|-------------|----------|
| Century OneWorld Seraya | 25 ac | 108–160 | ₹1.88 Cr | Devanahalli Toll |
| Godrej Reserve | 92.7 ac | 954 | ₹96 L | Devanahalli |
| DNR Solace | 30 ac | — | ₹1.13 Cr | Doddaballapur Rd |
| Sattva Bhumi | 20 ac | 356 | ₹37.6 L | Devanahalli SH96 |
| Brigade Oasis | 50 ac | Multi-phase | ₹1.09 Cr | Aerospace Park |
| Lagos (B&M) | 25 ac | 300 | ₹64 L | Doddaballapur Rd |
| KNS Candrill | 27.2 ac | — | ₹48 L (pre-launch) | Doddaballapur Rd |
| House of Hiranandani | — | — | ₹1.16 Cr | Devanahalli |
| Tata Carnatica | 70 ac | 150+ | — | Shettigere |
| Rare Earth Athena | 4.7 ac | 80 | ₹66 L | Devanahalli |
| Elite Serenity | 15 ac | — | ₹52.4 L | Devanahalli |
| Sunshine D Greens | 30+ ac | — | — | STRR Highway |
| Century Trails | 60 ac | 800+ | — | STRR |
| Northern Lights | — | — | ₹79 L | IVC Road |

---

## UPDATED: Property Portal Listing Methodology (Live Pricing)

The `ddgs` approach gives discovery URLs and developer pricing. For **live market pricing**
(what sellers are actually asking on portals right now), use this methodology instead:

### Step 1 — Discover Working Portal URLs via ddgs

```python
from ddgs import DDGS

projects = [
    '"Century Eden" "Doddaballapur" plots',
    '"Godrej Aravya" plots price',
    '"KNS Billore" plots price',
    '"Shriram Pristine" plots price',
    '"Lagos" "Bricks Milestones" plots price',
    '"ReWild" Doddaballapur plots price',
    '"KNS Candrill" plots price',
]

with DDGS() as ddgs:
    for q in projects:
        for r in ddgs.text(q, max_results=8):
            print(r["title"])
            print(r["href"])
```

### Step 2 — Target These Portals (in order of success rate)

| Portal | Status | URL Pattern |
|--------|--------|-------------|
| **MagicBricks** | ✅ Works | `magicbricks.com/<project-name>-<locality>-bangalore-pdpid-<ID>` |
| **NoBroker** | ✅ Works | `nobroker.in/<project-name>-<locality>_bangalore-prjt-<ID>` |
| **360realtors** | ✅ Works | `360realtors.com/<project-name>-<city>-uid-<ID>` |
| **99acres** | ❌ Broken — all URL patterns return 404 | Deprecated |
| **Housing.com** | ⚠️ Partial — some project pages 404 | Try direct URLs from ddgs results |
| **SquareYards** | ❌ Broken — returns 404 on area search | Use direct project URLs only |

### Step 3 — Extract Listings with This Filtering Logic

For each project page on MagicBricks/NoBroker:
1. Scroll to "Properties in [Project Name]" section
2. Look at **Posted date** — filter to listings within **last 30 days**
3. Check **seller type** — agent listings are acceptable; prioritize developer listings if available
4. For each qualifying listing, extract: **size (sqft)**, **price (₹)**, **posted date**, **seller type**
5. **Normalize to per-sqft rate**: `rate = price ÷ sqft`

### Step 4 — Average and Report

```
avg_rate = mean(all qualifying listing rates)
range = min rate to max rate
source = portal URL + portal name + latest listing date
```

**Output format per project:**
```
| Size | Price | Rate/sqft | Posted | Seller |
|---|---|---|---|---|
| 1,200 sqft | ₹84 Lac | ₹7,000 | May 04, '26 | Agent |
```

### Pitfalls

- **99acres returns 404 on every URL pattern** — do not waste time constructing URLs; use MagicBricks/NoBroker/360realtors instead
- **Developer listings on portals are rare** — most listings are agents/owners; use them as the market-clearing rate
- **sqyd vs sqft confusion** — some listings show "sq.yrd" (square yards); 1 sqyd = 9 sqft — convert before normalizing
- **ReWild is a different product type** — estate plots 5,000–16,000 sqft, not comparable to standard 1,200–3,000 sqft plots
- **Sattva Doddaballapur has RERA awaited** — pricing not publicly listed; "View Price" requires form submission
- **web_extract returns "No web extract provider configured"** — firecrawl/tavily/exa not set up; use browser_snapshot or ddgs snippets instead

### Known Live Listing URLs (Doddaballapur/Devanahalli corridor — May 2026)

| Project | URL |
|---------|-----|
| Century Eden (MagicBricks) | https://www.magicbricks.com/century-eden-yelahanka-bangalore-pdpid-4d4235303233303633 |
| KNS Billore (MagicBricks) | https://www.magicbricks.com/kns-billore-yelahanka-bangalore-pdpid-4d4235343233363837 |
| Shriram Pristine (MagicBricks) | https://www.magicbricks.com/shriram-pristine-estates-doddaballapur-main-road-bangalore-pdpid-4d4235343135313537 |
| Godrej Aravya (NoBroker) | https://www.nobroker.in/godrej-aravya-estate-doddaballapura_bangalore-prjt-8a9fb88499989390019998e500e80ec5 |
| Shriram Pristine (NoBroker) | https://www.nobroker.in/shriram-pristine-estates-doddaballapura_bangalore-prjt-8a9f8c83953b0fb901953b5c6d3310b1 |
| Lagos (360realtors) | https://www.360realtors.com/bricks-milestones-lagos-by-milestone-doddaballapur-road-bangalore-uid-6905 |
| ReWild (360realtors) | https://www.360realtors.com/rewild-plots-doddaballapura-bangalore-uid-7016 |
| KNS Candrill (official) | https://www.knscandrill.net.in/price.html |
| Godrej Aravya (official) | https://www.godrejaravyaestate.live/price.html |
| Sattva Doddaballapur (official) | https://sattvabuilders.com/projects/sattva-doddaballapur/ |
| The Estates Nandi Hills | https://theestates.in/villa-plots-nandi-hills/ |

### Typical Live Pricing — Doddaballapur/Devanahalli Corridor (May 2026)

| Project | Rate/sqft (live avg) | Portal |
|---------|----------------------|--------|
| Century Eden | ₹7,500–7,870 | MagicBricks |
| KNS Billore | ₹5,867–5,917 | MagicBricks |
| Shriram Pristine | ₹5,256–5,992 | MagicBricks + NoBroker |
| Godrej Aravya | ₹4,986–5,000 | Official price page |
| KNS Candrill | ₹4,000–5,000 | 360realtors + official |
| Lagos B&M | ₹6,156–6,287 | 360realtors |
| ReWild | ₹3,000 | 360realtors |
| The Estates Nandi Hills | ₹2,800–3,500 | Official + Homes247 |

## Limitations

- **Snippet-only**: ddgs returns titles, URLs, and 2-3 line snippets — not full page content
- **Rate limiting**: DuckDuckGo may throttle after rapid requests; add delays if needed
- **No structured data**: results are raw text; extract structured fields manually from snippets
- **99acres broken**: site structure changed; all URL patterns return 404

## Fallback for Full Content

If a specific URL from ddgs results is critical:
1. Try `browser_navigate` to the URL — developer sites and listing pages load without CAPTCHA
2. Try `web_extract` with a Firecrawl-backed provider (if configured — currently returns "No web extract provider configured")
3. Use `browser_snapshot` to manually extract listing data from portal pages
4. Use `curl` via `terminal` as last resort for simple HTML pages