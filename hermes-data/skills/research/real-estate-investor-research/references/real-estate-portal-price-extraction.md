# Real Estate Portal Price Extraction — Indian Context

Extract current listing prices from Indian real estate portals (MagicBricks, 99acres, SquareYards) for competitor project pricing analysis. Used during investor research to produce verified "Current Sale Price" data.

## Portals & Anti-Bot Protections

| Portal | Anti-bot | Works via | Notes |
|--------|----------|-----------|-------|
| **MagicBricks** | Akamai CDN | Browser (Playwright/Puppeteer) | Blocks curl, web_extract, all HTTP libraries |
| **99acres** | JS-heavy rendering | Browser | Project pages load static, listings are JS-dynamic |
| **SquareYards** | Blocks curl (403) | Browser | Same page works fine in regular browser |
| **Housing.com** | Similar protections | Browser | Falls into same pattern |

**Key insight:** All portals detect non-browser HTTP clients. Always use browser tools (`browser_navigate`, `browser_scroll`, `browser_snapshot`, `browser_console`) for data extraction. The `web_extract` tool (Firecrawl/Jina) also fails because these pages require JS rendering.

## MagicBricks Price Extraction Pattern

### Page Structure

Each project has a PDP (Project Detail Page) URL pattern:
- `https://www.magicbricks.com/<project-slug>-<location>-pdpid-<id>`

The page has a section **"Properties in [Project Name]"** containing individual listing cards. Each card shows:
- **Total price**: `₹3.50 Cr`, `₹5.50 Cr`, `₹45 Lacs`, etc.
- **Built-up area**: `2885 sq.ft`, `3664 sq.ft`, etc.
- **Configuration**: `4 BHK Villa`, `3 BHK Apartment`
- **Status**: Ready to Move / Under Construction
- **Posted date**: "Today", "Yesterday", "Jun 06, '26"

### Per-sqft Price Calculation

```python
def parse_price(text):
    """Convert Indian price text to rupees."""
    text = text.replace(',', '').replace(' ', '')
    if 'Cr' in text:
        return float(text.replace('Cr', '')) * 10000000
    elif 'Lac' in text or 'L' in text:
        return float(text.replace('Lac', '').replace('L', '')) * 100000
    else:
        return float(text.replace('₹', ''))

def calc_per_sqft(total_price_text, area_text):
    """Calculate ₹/sq.ft from listing data."""
    price_rs = parse_price(total_price_text)
    area = float(area_text.replace('sq.ft', '').replace(',', '').strip())
    return round(price_rs / area)
```

### Data Extraction via Browser

```python
# Via browser_console with JS evaluation:
# Listings are in DOM elements. Extract via:
results = browser_console(expression="""
JSON.stringify(
  Array.from(document.querySelectorAll('[class*="listing"]')).map(el => ({
    price: el.querySelector('[class*="price"]')?.textContent?.trim(),
    area: el.querySelector('[class*="area"], [class*="sqft"]')?.textContent?.trim(),
    config: el.querySelector('[class*="type"], [class*="bhk"]')?.textContent?.trim()
  })).filter(x => x.price)
)
""")
```

Or via browser_snapshot text parsing:
```python
# Navigate to page, scroll down to load listings
browser_navigate(url)
browser_scroll(direction='down')
snap = browser_snapshot()
# Parse snapshot text for ₹ amounts adjacent to sq.ft values
```

### Pitfalls

1. **Not all projects have PDP pages.** Some smaller/newer projects only appear in search results, not as dedicated project pages. On MagicBricks, check if the URL pattern is `pdpid-` (PDP) vs `propertyName=` (search). Search-based URLs won't have listing cards.

2. **Listings are JS-rendered.** `browser_snapshot()` may not show them if `full=False` (compact mode). Use `full=True` or extract via `browser_console` JS evaluation.

3. **Duplicate listings.** Same listing may appear in both the "Properties" section and the "Floor Plans" section. Deduplicate by price + area combination.

4. **Under-construction projects** show "floor plan base pricing" not individual resale listings. These are builder-listed base prices, not current market rates.

5. **Plotted developments** on MagicBricks show per-plot total prices, not per-sqft rates. Calculate per-sqft by dividing by plot area if available.

6. **Outliers.** Some listings have anomalous prices (e.g. ₹37 Lac for 994 sq.ft = ₹3,722/sq.ft in a project where other listings show ₹7,000+). The anomalous one may be a different type (budget floor vs premium villa). Flag and offer to exclude.

7. **Name mismatches.** Portals list projects under slightly different names than your source data:
   - "Genurise Divine Meadows" → "MJR Divine Meadows" on MagicBricks
   - "Pelican Square Villas" → "Whitehill Pelican Square"
   - "Seven Sarjapur" → "Fortune Seven Sarjapur"
   - "Ridgewood Villas" → "Frontier Ridgewood"
   
   Search the alternate name when the known name doesn't find a PDP page.

## 99acres Price Extraction

99acres project pages show the **project price range** (e.g. "₹1.7 Cr" or "₹69 L - ₹1.2 Cr") in the hero section, not individual listing cards immediately.

### Finding Individual Listings

Scroll down to find **"Resale Properties in this project"** section (if available). This section is JS-dynamic and may need `browser_scroll` to trigger loading.

The project PDP URL pattern is:
- `https://www.99acres.com/<project-slug>-<location>-npxid-<id>`

Projects without a npxid URL are search-result pages and won't have individual listings.

### Project-Level Data (fallback)

When individual listings aren't available, extract from the hero section:
- **Price range**: "₹1.7 Cr" or "₹69 L - ₹1.2 Cr"
- **Configuration**: "4 BHK Villa" or "Land"
- **Status**: "Ready To Move" or "Under Construction"
- **Built-up area**: "2110 sq.ft" (sometimes shown)

Mark these as "estimated" since they're project-level, not listing-level data.

## SquareYards

SquareYards links work in browser but return HTTP 403 from all non-browser tools (curl, web_extract, Python requests). The page loads fine in a real browser with JS enabled.

PDP URL pattern:
- `https://www.squareyards.com/<city>-residential-property/<project-slug>/<id>/project`

The page shows:
- **Price range**: "₹1.96 Cr - 2.49 Cr"
- **Unit sizes**: "2885 to 3664 Sq. Ft"
- **Configuration**: "4 BHK Villa"
- **Project status**: "Ready to Move"

## Price Verification Workflow

1. **Start with MagicBricks PDP pages** — they have the most individual listing data
2. **For projects without MagicBricks PDP pages**, try 99acres (project-level price range)
3. **Mark data tiers clearly:**
   - **Verified** (✅): Average from 2+ individual listings on MagicBricks
   - **Partial** (⚠️): Single listing or floor-plan base price
   - **Estimated** (~): Project-level price range or from earlier research
4. **Always report the number of listings** that the average is based on
5. **Note the source** — "From X MB listings" or "Estimated"
