---
name: duckduckgo-search
description: Free web search via DuckDuckGo — text, news, images, videos. No API key needed. Use the Python DDGS library or CLI to search, then web_extract for full content.
version: 1.2.0
author: gamedevCloudy
license: MIT
metadata:
  hermes:
    tags: [search, duckduckgo, web-search, free, fallback]
    related_skills: [arxiv]
    fallback_for_toolsets: [web]
prerequisites:
  commands: [ddgs]
---

# DuckDuckGo Search

Free web search using DuckDuckGo. **No API key required.**

Preferred when `web_search` tool is unavailable or unsuitable (no `FIRECRAWL_API_KEY` set). Can also be used as a standalone search tool.

## Setup

```bash
# Install the ddgs package (one-time)
pip install ddgs
```

Note: `ddgs` is not pre-installed in all environments. If `ModuleNotFoundError: No module named 'ddgs'` occurs, install it first with `pip install ddgs`.

## Python API (Primary)

Use the `DDGS` class in `execute_code` for structured results with typed fields.

**Important:** `max_results` must always be passed as a **keyword argument** — positional usage raises an error on all methods.

### Text Search

Best for: general research, companies, documentation.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.text("python async programming", max_results=5):
        print(r["title"])
        print(r["href"])
        print(r.get("body", "")[:200])
        print()
```

Returns: `title`, `href`, `body`

### News Search

Best for: current events, breaking news, latest updates.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.news("AI regulation 2026", max_results=5):
        print(r["date"], "-", r["title"])
        print(r.get("source", ""), "|", r["url"])
        print(r.get("body", "")[:200])
        print()
```

Returns: `date`, `title`, `body`, `url`, `image`, `source`

### Image Search

Best for: visual references, product images, diagrams.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.images("semiconductor chip", max_results=5):
        print(r["title"])
        print(r["image"])       # direct image URL
        print(r.get("thumbnail", ""))
        print(r.get("source", ""))
        print()
```

Returns: `title`, `image`, `thumbnail`, `url`, `height`, `width`, `source`

### Video Search

Best for: tutorials, demos, explainers.

```python
from ddgs import DDGS

with DDGS() as ddgs:
    for r in ddgs.videos("FastAPI tutorial", max_results=5):
        print(r["title"])
        print(r.get("content", ""))       # video URL
        print(r.get("duration", ""))       # e.g. "26:03"
        print(r.get("provider", ""))       # YouTube, etc.
        print(r.get("published", ""))
        print()
```

Returns: `title`, `content`, `description`, `duration`, `provider`, `published`, `statistics`, `uploader`

### Quick Reference

| Method | Use When | Key Fields |
|--------|----------|------------|
| `text()` | General research, companies | title, href, body |
| `news()` | Current events, updates | date, title, source, body, url |
| `images()` | Visuals, diagrams | title, image, thumbnail, url |
| `videos()` | Tutorials, demos | title, content, duration, provider |

## CLI (Alternative)

Use the `ddgs` command via terminal when you don't need structured field access.

```bash
# Text search
ddgs text -k "python async programming" -m 5

# News search
ddgs news -k "artificial intelligence" -m 5

# Image search
ddgs images -k "landscape photography" -m 10

# Video search
ddgs videos -k "python tutorial" -m 5

# With region filter
ddgs text -k "best restaurants" -m 5 -r us-en

# Recent results only (d=day, w=week, m=month, y=year)
ddgs text -k "latest AI news" -m 5 -t w

# JSON output for parsing
ddgs text -k "fastapi tutorial" -m 5 -o json
```

### CLI Flags

| Flag | Description | Example |
|------|-------------|---------|
| `-k` | Keywords (query) — **required** | `-k "search terms"` |
| `-m` | Max results | `-m 5` |
| `-r` | Region | `-r us-en` |
| `-t` | Time limit | `-t w` (week) |
| `-s` | Safe search | `-s off` |
| `-o` | Output format | `-o json` |

## Workflow: Search then Extract

DuckDuckGo returns titles, URLs, and snippets — not full page content. To get full content, follow up with `web_extract`:

1. **Search** with ddgs to find relevant URLs
2. **Extract** content using the `web_extract` tool (if available) or curl

```python
from ddgs import DDGS

with DDGS() as ddgs:
    results = list(ddgs.text("fastapi deployment guide", max_results=3))
    for r in results:
        print(r["title"], "->", r["href"])

# Then use web_extract tool on the best URL
```

## Browser-Based Alternative: DuckDuckGo Lite

When the `ddgs` Python package is unavailable, rate-limited, or you need visual interaction with results (clicking through), use **DuckDuckGo Lite mode** via the browser tool:

```
https://lite.duckduckgo.com/lite/?q=<your-search-query>
```

**Why:** The lite version (`lite.duckduckgo.com`) has minimal JavaScript and no CAPTCHA walls — it works reliably with the browser tool when Google (captcha), Bing, and even regular DuckDuckGo are blocked. Results render as simple HTML tables that the browser snapshot can parse.

**⚠️ CAPTCHA bypass with `cc=us`:** After ~3-5 searches on DDG Lite, a "select all squares containing a duck" CAPTCHA appears. Appending `&cc=us` to the URL bypasses this by changing the region cookie. Works for another ~3-5 searches before rotating. Full URL pattern:
```
https://lite.duckduckgo.com/lite/?q=<query>&cc=us
```

**Workflow:**
1. `browser_navigate(url="https://lite.duckduckgo.com/lite/?q=your+search+terms")`
2. `browser_snapshot()` — results are in a table, each row has a numbered cell + a link cell
3. Click any result by finding its ref from the snapshot
4. If the target page is JS-heavy (e.g. Amazon, parts sites), the lite search at least gives you URLs and snippets to work with

**Best for:** Parts research, pricing lookups, technical specs — queries where the answer is in snippets and linked pages, not behind login walls.

**Limitations:**
- No API structured output — must parse the HTML table snapshot
- Clicking through to target sites may still hit their own blocks (Amazon, etc.)
- Not suitable for image/video search

## Limitations

- **Rate limiting**: DuckDuckGo may throttle after many rapid requests. Add a short delay between searches if needed.
- **No content extraction**: ddgs returns snippets, not full page content. Use `web_extract` or curl for that.
- **Results quality**: Generally good but less configurable than Firecrawl's search.
- **Field variability**: Return fields may vary between results or ddgs versions. Use `.get()` for optional fields to avoid KeyError.
- **News search skews to secondary results**: `ddgs.news()` on broad queries like "BBC News" tends to return sub-topic articles (e.g. sports) rather than the homepage lead headlines. For homepage headline extraction, prefer the BBC RSS feed instead.

## Pitfalls

- **`max_results` is keyword-only**: `ddgs.text("query", 5)` raises an error. Use `ddgs.text("query", max_results=5)`.
- **Don't confuse `-k` and `-m`** (CLI): `-k` is for keywords, `-m` is for max results count.
- **Package name**: The package is `ddgs` (was previously `duckduckgo-search`). Install with `pip install ddgs`.
- **Empty results**: If ddgs returns nothing, it may be rate-limited. Wait a few seconds and retry.

## Freelancer Marketplace Research (Upwork / Fiverr)

When researching freelancers on Upwork or Fiverr for a specific skill niche, use DuckDuckGo HTML mode combined with `site:` operators. Both platforms deploy aggressive CAPTCHA walls that block direct browser access, so search-based URL extraction is the reliable path.

### Search Patterns

```bash
# Upwork freelancer search by skill
site:upwork.com "real estate video" "drone" "map animation" freelancer

# Fiverr seller search by skill
site:fiverr.com "real estate video" drone map animation seller

# Multi-city India search (tier 2/3 non-metro)
site:upwork.com India freelancer "real estate video" drone map Jaipur Lucknow Coimbatore

# Specific city combinations
site:fiverr.com India "real estate video" map animation Freelancer Jaipur Lucknow
```

### Extraction Workflow

1. **Search** via DuckDuckGo with `site:` operator for the platform
2. **Parse** the HTML results for freelancer profile URLs — patterns like:
   - `upwork.com/freelancers/~[hex-string]` — individual profile
   - `upwork.com/services/product/` — fixed-price service listing
   - `fiverr.com/[username]/` — seller profile
   - `fiverr.com/[username]/[gig-slug]` — specific gig
3. **Extract** key info from search snippets: rating, review count, specialization keywords, location
4. **Build** a candidate list from snippet data before attempting profile access

### Handling Platform CAPTCHA

- **Upwork**: Blocks direct profile URLs with Cloudflare challenge. Search snippets carry enough info (rating, reviews, location, skills) to build a shortlist without visiting.
- **Fiverr**: Blocks profile/gig URLs with human verification challenge. Use search snippet descriptions as primary data source.
- **Fallback**: If a profile URL is blocked, the snippet data (name, rating, specialization from search results) is sufficient to include in a recommendation list.

### Key Snippet Fields to Capture

From search results for freelancer profiles:
- **Name/username** — appears as link text
- **Platform** — Upwork or Fiverr
- **Rating** — e.g., "4.9", "5.0 ⭐"
- **Review count** — e.g., "(37 reviews)", "(200+ reviews)"
- **Specialization** — visible in the snippet description
- **Location** — e.g., "Bhaktapur, Nepal", "Rawalpindi, Pakistan", "Repalle, AP"
- **Rate** — sometimes shown ("$15.00/hr", "$50–80/project")
- **Profile URL** — extracted from href patterns above

### India Non-Metro Freelancer Patterns

For India searches (tier 2/3 cities outside major metros):
- **AP/Telangana**: Repalle, Hyderabad
- **Gujarat**: Ahmedabad, Surat
- **Maharashtra**: Pune, Nagpur
- **Rajasthan**: Jaipur
- **Uttar Pradesh**: Lucknow
- **Tamil Nadu**: Coimbatore, Chennai
- **Madhya Pradesh**: Indore
- **Odisha**: Bhubaneswar
- **Karnataka**: Mysore (relevant for Bangalore adjacency)
- **Pakistan**: Rawalpindi Cantonment (tier 2)
- **Sri Lanka**: Colombo

For real estate video with satellite/drone/map animation, prioritize freelancers who specifically mention Google Earth Studio, GeoLayers, drone footage, property lines, road map animations, and location callouts.

### Verified Profile URL Patterns

```
Upwork individual:  https://www.upwork.com/freelancers/~[hex-id]
Upwork service:     https://www.upwork.com/services/product/video-audio-[slug]-[id]
Fiverr seller:      https://www.fiverr.com/[username]
Fiverr gig:         https://www.fiverr.com/[username]/[gig-slug]
```

Note: Upwork profile pages are blocked by Cloudflare; service catalog pages sometimes load. Fiverr profile and gig pages consistently trigger human verification. Use search snippet data as primary source.

## Lead Enrichment Use Case: Search People by Name + Phone

ddgs works well for enriching lead spreadsheets where you have a person's name and phone number. DuckDuckGo indexes LinkedIn, Instagram, Facebook, and Crunchbase in organic results — making it more useful for lead research than X/Twitter-only searches.

### Search Pattern

```python
from ddgs import DDGS
import time, re

# Clean the name (remove emojis, standardize spaces)
name = "CA Santosh Mitra Sharma"
phone = "917488361751"
clean = re.sub(r'[^\w\s\.\,\-]', '', name).strip()
clean = re.sub(r'\s+', ' ', clean).strip()

# The phone number anchors the search — prevents unrelated same-name hits
query = f'"{clean}" {phone[-10:]}'

with DDGS() as ddgs:
    results = list(ddgs.text(query, max_results=3))
    for r in results:
        print(r['title'], r['href'], r.get('body', '')[:200])
    time.sleep(0.3)  # Rate limit
```

### Relevance Filtering

Not all results are about the same person. Filter by:

1. **Profile URLs** — `linkedin.com/in/`, `instagram.com/`, `facebook.com/`, `crunchbase.com/` — always relevant
2. **Phone match** — if the last 10 digits of the phone appear in the result body, it's the same person
3. **Name word match** — if most significant words from the name appear in the title

### Performance at Scale

Tested on 171 leads (165 searchable, 135 with relevant findings, ~50 LinkedIn profiles discovered):

| Setting | Value |
|---------|-------|
| Delay between queries | 0.3s |
| Results per query | 3 |
| Total time for 165 searches | ~3 minutes |
| Hit rate | 82% |

### Integration with Google Sheets

Read leads from a sheet, search each, write findings back as a new column:

```python
from tools.gws_skill_bridge import call
import json

# Step 1: Read leads
data = json.loads(call("sheets_get", service_name="google-draas",
    sheet_id="SHEET_ID", range="SheetName!A2:M200"))  # ⚠️ sheet_id= not spreadsheet_id=

# Step 2: Search each lead
# ... (loop with ddgs)

# Step 3: Write findings back
findings = [["Research Findings"]] + [[findings_text] for findings_text in all_findings]
call("sheets_update", service_name="google-draas",
    sheet_id="SHEET_ID", range="SheetName!N1:N172",
    values=json.dumps(findings))
```

⚠️ **Important:** The gws_skill_bridge's `sheets_get` and `sheets_update` expect `sheet_id=` and `range=` (SimpleNamespace attribute names), NOT `spreadsheetId` or `ranges`. Always use `sheet_id=` and `range=` with the bridge.

### What to Skip

- First names only (Raj, Amit, Renu, etc.) — too generic
- Anonymous user IDs (rcqjxdtg, cjmizdqj) — no real identity
- Phone-as-name rows
- Your own test data

### Full Workflow Reference

See `b2b-lead-research/references/lead-enrichment-chat-audit.md` for the complete worked example (171 leads, 135 findings, confidence adjudication, formatting patterns).

## Related

- `references/bbc-rss-feeds.md` — BBC RSS feed endpoints for headline extraction
- `references/public-data-sources.md` — Wikipedia API, wttr.in weather, HIBP API
- `../b2b-lead-research/references/lead-enrichment-chat-audit.md` — Complete worked example: enriching 171 leads via ddgs

## Validated With

Smoke-tested with `ddgs==9.11.2` on Python 3.13. All four methods (text, news, images, videos) confirmed working with keyword `max_results`.

Lead enrichment pattern validated with `ddgs==9.14.4` on Python 3.13 across 165 searches.
