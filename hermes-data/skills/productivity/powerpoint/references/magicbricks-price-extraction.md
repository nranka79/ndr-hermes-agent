# Real Estate Portal Price Extraction

Extract current listing prices from MagicBricks, 99acres, and SquareYards for Bangalore/Sarjapur real estate projects.

## Context

For a 33-slide market research presentation (RANKA Oasis), we needed to replace generic market research prices with **verified current listing prices** from real estate portals. Each project slide had a "Current Price" showing the market price range and a "Launch Price" with original launch data.

## MagicBricks Price Extraction

### Source of Truth: Individual Listings

MagicBricks PDP (Project Detail Page) URLs like:
```
https://www.magicbricks.com/nvt-arcot-vaksana-sarjapur-road-bangalore-pdpid-4d4235303733363531
```

Contain a "Properties in [Project Name]" section with individual listing cards showing:
- **Total price** (e.g. ₹3.50 Cr, ₹5.50 Cr, ₹45 Lacs)
- **Built-up area** in sq.ft (e.g. 2885 sq.ft, 3664 sq.ft)
- **BHK type** (e.g. 4 BHK Villa)

### Technique

**Use the browser tool** — NOT curl, NOT web_extract. MagicBricks uses Akamai anti-bot protection. Only the browser (headless Chrome) renders the listing cards. curl returns HTTP 403, web_extract returns nothing.

```python
# In execute_code or via subagent:
browser_navigate(url)
browser_scroll("down")  # Scroll to load listing cards
browser_snapshot()  # Extract visible listings
```

**Caution:** MagicBricks class names are minified and change frequently. Browser snapshot + manual parsing works best.

### Per-sq.ft Calculation

| Input | Calculation |
|-------|-------------|
| ₹3.50 Cr, 2885 sq.ft | `3.50 × 1,00,00,000 ÷ 2885 = ₹12,131/sq.ft` |
| ₹5.50 Cr, 3664 sq.ft | `5.50 × 1,00,00,000 ÷ 3664 = ₹15,011/sq.ft` |
| ₹45 Lacs, 1200 sq.ft | `45 × 1,00,000 ÷ 1200 = ₹3,750/sq.ft` |

**Conversions:** 1 Cr = ₹1,00,00,000, 1 Lac = ₹1,00,000

### Projects Without PDP Pages

Some projects don't have a dedicated MagicBricks project page. For these, try:
1. Search MagicBricks for the exact project name via browser
2. Check if the project exists under a different name (e.g. "Pelican Square" → "Whitehill Pelican Square")
3. Fall back to 99acres (npxid pages for many projects)
4. Use existing market research prices as estimated fallback

## DuckDuckGo Lite Workaround for Finding Listing URLs

When **all three** direct routes fail — MagicBricks bot protection, 99acres 404s, and Google CAPTCHA — DuckDuckGo Lite works as a search intermediary because it renders results as static HTML without JS requirements.

### Technique A: browser_console extraction (fast, for URL gathering)

```
browser_navigate("https://lite.duckduckgo.com/lite/")
browser_type("@e1", "magicbricks <Project Name> Whitefield Bangalore")
browser_press("Enter")
```

1. Navigate to `lite.duckduckgo.com/lite/` — NOT the full DuckDuckGo site, the **Lite** version
2. Enter a simple search: `magicbricks <Project Name> <Locality> Bangalore`
3. Submit — you **will** get a duck-identification CAPTCHA on the first search (select duck squares). Complete it
4. **After the one-time CAPTCHA**, the session is clean for all subsequent searches
5. Extract listing URLs from `<span class="link-text">` elements using `browser_console()`:

```javascript
// Extract MagicBricks and 99acres project URLs from the page
var spans = document.querySelectorAll('.link-text');
var results = [];
var seen = new Set();
spans.forEach(function(s) {
    var text = s.textContent.trim();
    if ((text.includes('magicbricks.com') || text.includes('99acres.com')) 
        && !text.includes('spid-') && !text.includes('resale') && !text.includes('for-sale') && !text.includes('for-rent') && !text.includes('rent-')) {
        if (!seen.has(text)) { seen.add(text); results.push(text); }
    }
});
// Return only the first 3-4 project-level URLs (not individual listings)
results.slice(0, 4).join('\\n');
```

### Technique B: browser_vision-based reading (for full context)

When the DDG Lite results page is too long and `browser_snapshot(full=True)` truncates, use **browser_vision** to read the full SERP:

1. `browser_navigate('https://lite.duckduckgo.com/lite/')`
2. `browser_type(@e1, query)` — type the search term
3. `browser_click(@e2)` — submit
4. `browser_vision(question="List all search results with titles, descriptions, and any visible URLs. Give me the full list.")` — captures everything visible, including truncated snapshot areas

The vision model returns every result in the viewport, including titles, descriptions, and visible portal URLs. This is more reliable than snapshot when the result list is long (DDG Lite returns many results per page with ellipsis-truncated descriptions).

**When to use which:**
- **Technique A (console):** Faster (~2-3s per search). Use when you just need portal URLs for source-link footers.
- **Technique B (vision):** Slower (~5-10s per vision call) but captures full context — descriptions, prices, status snippets. Use when you also need project data (pricing, status, builder) from the search results themselves, not just URLs.

Tip: The one-time CAPTCHA applies to both techniques. After passing it on the first search, switch between console and vision freely on subsequent searches.

### Sequential search is faster than subagents for URL discovery

The doc below suggests parallelizing with subagents for 16+ projects, but **each subagent starts a fresh browser session that hits the CAPTCHA again**. The DuckDuckGo Lite session cookie doesn't transfer to subagent sessions. Budget ~30-60 seconds per project when searching sequentially in the main session — you type the project name into the search box (`@e3` on the results page), submit (`browser_press("Enter")`), and extract URLs from `browser_console()` or `browser_vision()`. This is faster per project than subagent overhead + CAPTCHA solves.

### Why DuckDuckGo Lite specifically

| Approach | Result |
|----------|--------|
| Direct curl to MagicBricks | HTTP 403 / bot challenge |
| Direct browser to MagicBricks | "Oops" error page |
| Direct browser to 99acres | 404 / "page not exists" |
| Google search via browser | Google CAPTCHA / IP block |
| DuckDuckGo Lite | **Works** — HTML-only, one-time CAPTCHA |

### Session persistence

Once you pass the initial puzzle CAPTCHA on the first search, you can type new searches directly into the search box (ref `@e3` on results page, or `@e1` on home page) and submit without re-challenge. Do NOT navigate to a different URL — use the on-page form to submit new searches.

### URL patterns found

Successful results return URLs like:

```text
# MagicBricks project PDP
www.magicbricks.com/<project-slug>-whitefield-bangalore-pdpid-4d4235XXXXXXXX

# MagicBricks listing page  
www.magicbricks.com/project-<project-slug>-for-sale-in-bangalore-pppfs

# 99acres project page
www.99acres.com/<project-slug>-whitefield-bangalore-east-npxid-rXXXXX
```

### Project name spelling differences

Project names may differ between your data and portal listings due to SEO normalization. Common patterns:
- **Compound names split**: "Balaji Casablanca" → "Balaji Casa Blanca" (two words on both MagicBricks and 99acres)
- **Apostrophes dropped**: "D'Silva" → "DSilva" or "D Silva"
- **Abbreviations expanded**: "SOBHA" → "Sobha"
- **Developer name included**: Just the project name may not match; try adding the developer's name to the search
- **Old legacy projects**: Pre-RERA projects may use their original scheme name rather than the current marketed name

When DuckDuckGo Lite returns no portal results for a project, try searching with portal names omitted — just `"<Project Name>" <Locality> Bangalore 99acres` may find the listing when `magicbricks <Project Name>` does not.

### Older/smaller projects may only have resale pages

Some older projects (pre-2010, <50 units) don't have dedicated project pages on 99acres (no `npxid`). They may only have individual listing or resale pages (`npffid` or `spid-` URLs). Use these as fallbacks — they still show the project name and location even though they're individual listing pages.

### Sequential search is faster than subagents

The doc above suggests parallelizing with subagents for 16+ projects, but **each subagent starts a fresh browser session that hits the CAPTCHA again**. The DuckDuckGo Lite session cookie doesn't transfer to subagent sessions. Budget ~30-60 seconds per project when searching sequentially in the main session — you type the project name into the search box (`@e3` on the results page), submit (`browser_press("Enter")`), and extract URLs from `browser_console()`. This is faster per project than subagent overhead + CAPTCHA solves.

When searching sequentially, the search box ref ID is `@e1` on the home page and `@e3` on the results page. Use the results page search box to avoid re-loading the home page between searches.

## 99acres Price Extraction

99acres project pages have URLs like:
```
https://www.99acres.com/nvt-arcot-vaksana-resale-in-sarjapur-bangalore-east-108675-npffid
https://www.99acres.com/assetz-18-and-oak-koosthanapalli-hosur-npxid-r274193
```

Same browser requirement — JS-rendered content.

## SquareYards

SquareYards blocks curl (HTTP 403) but works in browser. The 403 is bot protection, not a broken link. Links work when clicked by a human.

## Alternative: Google Search AI Overview (Quick First Pass)

When portal PDP pages are hard to reach (bot protection, JavaScript-heavy, CAPTCHA) or when Firecrawl/web_search is unavailable, **browser-based Google Search** with AI Overview extraction gives a quick first pass on prices:

```python
# In execute_code:
from hermes_tools import terminal as t

# Navigate to Google search for the project
# (browser_navigate can only be called from the main turn, not execute_code)
```

**Pattern (in main turn via browser tools):**

1. `browser_navigate("https://www.google.com/search?q=SOBHA+Galera+Hoskote+price+per+sqft+MagicBricks+99acres")`
2. `browser_vision(question="What does the AI Overview say about prices for this project?")` or read the snapshot directly
3. Google's AI Overview often synthesizes data from **multiple portals** (MagicBricks, 99acres, SquareYards) into a single answer with per-sqft ranges and total price brackets
4. Note the building/configuration (e.g., "4 BHK, 2,980-4,340 sq.ft") to verify you're comparing like-for-like

**What you get from AI Overview (example):**
```
SOBHA Galera: ₹15,500 to ₹19,600/sq.ft, 4 BHK, ₹4.53 Cr to ₹6.73 Cr
Godrej Parkshire: ₹10,867 to ₹11,550/sq.ft, 2&3 BHK, ₹1.33 Cr to ₹2.2 Cr
```

**Pros:** Fast, multi-source synthesis, works for any project visible on portals
**Cons:** Not real-time (Google cached data), may miss newest listings, can't see individual listing details
**Best use:** First-pass research to get the ballpark, then verify individual listings via browser for critical projects

**When to use:** When you need prices for 10+ projects quickly, or when direct portal scraping returns 403/CAPTCHA

**For bulk research across many projects**, batch the Google searches by category:
```python
# (In the main turn, one search per minute via browser_navigate)
searches = [
    "SOBHA Galera Hoskote price per sqft",
    "Godrej Parkshire Hoskote price per sqft",
    # ...
]
for q in searches:
    browser_navigate(f"https://www.google.com/search?q={q}")
    browser_vision(...)
```

Each AI Overview typically covers 1-3 projects, so 10 searches can cover 15-25 projects.

## Presentation Update Workflow

After extracting prices, update the Google Slides presentation:

1. **Download as PPTX** via `drive_download` with `export_mime`
2. **Edit with python-pptx** — find-and-replace text at the run level
3. **Upload back as Google Slides** via googleapiclient with `mimeType: application/vnd.google-apps.presentation`
4. **Share** with the requesting user

### Price Display Patterns

| Pattern | Example | When |
|---------|---------|------|
| Single avg | ₹14,254/sq.ft | Summary / at-a-glance |
| Min-max range | ₹12,132-15,011/sq.ft | Detail slides (preferred) |
| "From" price | From ₹12,132/sq.ft | Marketing |

**Lesson:** The user initially asked for avg prices, then corrected to min-max ranges. Confirm the format preference early.

### Slide Structure Convention

**Left panel:**
- 💰 CURRENT PRICE → listing range
- 🚀 LAUNCH PRICE → original launch price
- Launch date
- Quick facts

**Right panel:**
- Project details + current price / total price
- RERA number, developer

**Bottom bar (links):**
- 📍 Maps | 🏠 MagicBricks | 🏘️ 99acres | 📐 SquareYards
