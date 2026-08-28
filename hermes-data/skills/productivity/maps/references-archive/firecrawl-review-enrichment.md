# Firecrawl Enrichment: Reviews & Pricing for POIs

When the OSM `nearby` or raw Overpass query returns a list of places but the
user wants **ratings, reviews, and pricing** (not just location data), use
Firecrawl's search API to enrich each candidate with review-site data.

## Prerequisites

- `FIRECRAWL_API_KEY` in env (stored in `/run/s6/container_environment/` by
  the hermes container, or passed at session start)
- Internet access (Firecrawl API endpoint)

## Firecrawl Free Tier

- **1,000 credits/month** (free)
- 1 credit = 1 search or 1 scrape
- Enough for 10-20 POI enrichment cycles

## Search & Scrape Strategies

### Strategy 1: Firecrawl Search (best for quick review/pricing snippets)

```python
import os, json, urllib.request

FIRECRAWL_KEY = os.environ.get("FIRECRAWL_API_KEY", "")

def firecrawl_search(query):
    """Search the web via Firecrawl and return enriched business info."""
    data = json.dumps({"query": query, "limit": 3}).encode()
    req = urllib.request.Request(
        "https://api.firecrawl.dev/v1/search",
        data=data,
        headers={
            "Authorization": f"Bearer {FIRECRAWL_KEY}",
            "Content-Type": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        result = json.loads(resp.read())

    if not result.get("success"):
        return []

    enriched = []
    for item in result.get("data", []):
        enriched.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("description", "")[:400],
        })
    return enriched
```

Example query patterns:
```
"Naturals Lounge Cunningham Road Bangalore reviews haircut price"
"SPA ce The Spa Cunningham Road Bangalore Tripadvisor rating"
"Cloud 9 salon Bangalore Justdial rating"
```

### Strategy 2: Firecrawl Scrape (for deep-diving a specific review page)

```python
def firecrawl_scrape(url):
    """Scrape a single URL to extract full page content (markdown)."""
    data = json.dumps({"url": url}).encode()
    req = urllib.request.Request(
        "https://api.firecrawl.dev/v1/scrape",
        data=data,
        headers={
            "Authorization": f"Bearer {FIRECRAWL_KEY}",
            "Content-Type": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        result = json.loads(resp.read())
    if result.get("success") and result.get("data", {}).get("markdown"):
        return result["data"]["markdown"]
    return None
```

Good targets: TripAdvisor pages, Justdial pages, business websites, Instagram.

## Useful Review Sites (India)

| Site | Data Quality | Scrapable via Firecrawl |
|------|-------------|------------------------|
| TripAdvisor | ⭐⭐⭐⭐⭐ | ✅ Yes (markdown) |
| Justdial | ⭐⭐⭐⭐ | ✅ Yes (search snippets) |
| Google Maps | ⭐⭐⭐⭐⭐ | ⚠️ Partial (JS-heavy, use search not scrape) |
| Instagram | ⭐⭐⭐ | ✅ Public posts visible |
| wheree.com | ⭐⭐⭐ | ⚠️ Cloudflare-blocked |

## Enrichment Workflow (full pipeline)

1. **Find places** via maps CLI (`nearby`) or raw Overpass for custom tags
2. **For each named place**, run `firecrawl_search()` with:
   `"{place_name} {area} Bangalore reviews rating"`
3. **Extract** rating, review count, pricing mentions from search snippets
4. **For top candidates**, optionally `firecrawl_scrape()` TripAdvisor/Justdial
5. **Present** enriched results: name, walk time, ⭐ rating, pricing, phone

## Pitfalls

- **Firecrawl key vs Apify key**: Firecrawl keys start with `fc-`, Apify keys
  start with `apify_api_`. Don't confuse them — the API formats are different.
- **Google Maps scraping**: Firecrawl can scrape Google Maps URLs but returns
  image tiles and encoded data, not structured results. Use Firecrawl *search*
  instead to find Google Maps data indirectly via search results.
- **Justdial scrape**: Returns HTTP 500 errors consistently. Use search for
  Justdial snippets, not scrape.
- **Cloudflare-protected sites** (wheree.com, many Indian review sites): Scrape
  will fail. Fall back to search.
- **Rate limiting**: Firecrawl free tier is 1,000 credits. Each search = 1 credit.
  Batch queries when possible (one search per place, not per review site).
- **Instagram**: Public posts scrape fine. Private accounts won't work.

## Alternative: Apify Google Maps Scraper

If Firecrawl is unavailable, Apify's Google Maps Scraper actor extracts
structured data (name, rating, reviews, phone, hours, website, popular times)
directly from Google Maps. Requires Apify API key + credit (~$2.10/1,000 places).
