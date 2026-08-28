# DuckDuckGo Lite — Browser-Based Search (CAPTCHA-Workaround)

DuckDuckGo Lite (`https://lite.duckduckgo.com/lite/`) is a minimal HTML version of DuckDuckGo that works WITHOUT JavaScript. It reliably returns search results when:

- Firecrawl/`web_search` tool is down (unconfigured API key)
- Google/Bing block automated requests with CAPTCHAs
- `curl`/HTTP requests to DDG get rate-limited or challenged

## How it works

DDG Lite serves search results as a plain HTML `<table>` with rows of:
- Cell 1: Result number
- Cell 2: Title as `<a>` link (wrapped in DDG redirect)
- Cell 3: Description text
- Cell 4: URL + date as plain text

All links go through DDG's redirect: `https://duckduckgo.com/l/?uddg=ENCODED_URL&rut=...`

## Two Approaches

### Approach A: Browser + `browser_console` (preferred — works every time)

Navigate to DDG Lite, then extract links via JavaScript.

```python
# In execute_code or via browser_console tool:
# 1. Navigate
# browser_navigate(url="https://lite.duckduckgo.com/lite/?q=%22Project+Name%22+MagicBricks")

# 2. Extract all portal links
# browser_console(expression="
const links = document.querySelectorAll('a');
const results = Array.from(links).map(l => l.href).filter(h => 
  h.includes('magicbricks') || h.includes('99acres') || h.includes('squareyards')
);
results;
")
```

The actual URLs are encoded in the `uddg` query parameter of DDG redirect links. Extract them:

```javascript
// From the raw href like:
// https://duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.magicbricks.com%2Fproject-slug-pdpid-XXXXXX&rut=...
// Just click or extract the actual URL
const actualUrl = decodeURIComponent(href.match(/uddg=([^&]+)/)[1]);
```

### Approach B: Jina Reader via curl (when browser is slow or unavailable)

```bash
curl -s "https://r.jina.ai/https://lite.duckduckgo.com/lite/?q=%22Project+Name%22+Sarjapur+MagicBricks"
```

Jina Reader converts the DDG Lite HTML to clean Markdown with working links (stripped of DDG redirect). See `references/jina-reader.md` for full details.

## Query Construction

DDG Lite handles these search operators reliably:

| Operator | Example | Effect |
|----------|---------|--------|
| `"exact phrase"` | `"Assetz 18 & Oak"` | Exact match (recommended for multi-word project names) |
| `site:domain` | `site:magicbricks.com` | Restrict to domain (use with caution — may trigger CAPTCHA) |
| Simple keywords | `Project Name + Sarjapur + MagicBricks` | Basic AND search |

**Avoid:** Boolean operators (`OR`, `AND`), advanced syntax like `intitle:`, `filetype:` — these often trigger DDG's CAPTCHA on Lite.

**Safer query pattern (no CAPTCHA):**
`"Project Name Here" + SiteName + Location`

Example: `"NVT Arcot Vaksana" + MagicBricks + Sarjapur`

## URL Extraction Pattern

When searching for specific listing pages (MagicBricks, 99acres, SquareYards), the first result is usually the project page. Extract actual URLs from the DDG redirect:

```javascript
// browser_console approach
const links = document.querySelectorAll('a');
const portalUrls = [];

for (const link of links) {
  const href = link.href;
  if (href.includes('uddg=')) {
    const match = href.match(/uddg=([^&]+)/);
    if (match) {
      const decoded = decodeURIComponent(match[1]);
      if (decoded.includes('magicbricks') || decoded.includes('99acres') || decoded.includes('squareyards')) {
        portalUrls.push(decoded);
      }
    }
  }
}

// Sort: prefer project pages (pdpid, npffid, ffid) over listing pages
const projectPages = portalUrls.filter(u => 
  u.includes('pdpid') || u.includes('npffid') || u.includes('ffid') || u.includes('/project')
);
```

## Real Estate Portal URL Patterns

When found, MagicBricks and 99acres project page URLs follow these patterns:

**MagicBricks project page:**
`www.magicbricks.com/project-slug-locality-bangalore-pdpid-4d42XXXXXXXXXXXX`

**99acres project page:**
`www.99acres.com/project-slug-locality-bangalore-east-npxid-rXXXXXX`

**SquareYards project page:**
`www.squareyards.com/location/project-slug/XXXXX/project`

## Pitfalls

- **Rapid searches trigger CAPTCHA:** After 5-8 searches in quick succession, DDG Lite may start showing a challenge page. Wait 10-15 seconds between searches or use the `browser_vision` tool to solve if needed.
- **Site-specific queries (`site:domain`) are more likely to trigger CAPTCHA:** Use `"Project Name" + SiteName` pattern instead when possible.
- **The `browser_navigate` URL must be URL-encoded:** Spaces in query should be `+` or `%20`, quotes should be `%22`.
- **DDG Lite shows max ~7 results per page:** Click "Next Page >" button (ref=e167 usually) or scroll down for more results.
- **Project names may differ on portals** — e.g. "Genurise Divine Meadows" → "MJR Divine Meadows", "Royal Tulip Villas" → "Whitehill Royal Tulip", "Ridgewood Villas" → "Frontier Ridgewood Villas", "Seven Sarjapur" → "Fortune Seven Sarjapur". Try alternative names if initial search fails.
- **Some projects have no dedicated portal page** (new/unlisted projects). For these, use a search URL as fallback: `https://www.magicbricks.com/property-for-sale/residential-real-estate?cityName=Bangalore&propertyName=project-slug`
