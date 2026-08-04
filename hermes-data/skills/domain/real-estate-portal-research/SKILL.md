---
name: real-estate-portal-research
description: Indian property listings via Apify, Tavily, cloud browsers.
version: 1.0.0
author: Nishant Ranka (nranka79), Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [real-estate, portals, apify, scraping, india]
    category: domain
---

# Real-Estate Portal Research Skill

Handles Indian property market research: listing prices from portals
(99acres, MagicBricks, Housing.com), Google Maps coordinates, and general
market context. It does NOT scrape personal contact data (owner/broker
phones, emails) — listing data only, for market research.

The VPS runs on a datacenter IP that the portals network-block, so the
skill's core rule is: **never scrape portals with raw HTTP/curl/browser
from the VPS IP** — use the tools below, which exit from clean IPs.

## When to Use

- User asks for property prices / listings / projects (villa, flat, land) in an Indian city
- Market research for real-estate projects (e.g. "13 villa projects near Devanahalli")
- Google Maps coordinates for project locations
- Comparing prices across 99acres / MagicBricks / Housing.com

## Prerequisites

- `APIFY_API_KEY` set in `/opt/hermes/.env` (Apify account at console.apify.com)
- `TAVILY_API_KEY` set for `web_search` (Tavily account)
- `BROWSER_USE_API_KEY` set for `browser_use_cloud` (Browser Use Cloud account)
- The smart-browser sidecar container (`smart-browser`) running for `smart_browser`

## How to Run

Pick the tool for the task type:

| Task | Tool | Notes |
|---|---|---|
| General web search | `web_search` | Tavily backend; works from the datacenter IP |
| Portal listings (99acres/MagicBricks) | `apify_run_actor` | preset `magicbricks-99acres`; Apify residential-IN proxies |
| 99acres-only listings | `apify_run_actor` | preset `99acres` |
| Google Maps / Places results | `apify_run_actor` | preset `google-places` |
| Live browsing / forms / logins | `browser_use_cloud` | cloud IPs; always share `live_url` |
| Non-blocked site browsing | `smart_browser` | VPS sidecar (browser-use + Playwright) |
| Google Maps coordinates | `execute_code` + Playwright `headless_shell` | needs CONSENT/SOCS cookies; small batches |
| Page content extraction | `web_extract` | Tavily backend; portal pages are usually bot-protected — use Apify for those |

## Quick Reference

Portal listing call (verified working input):

```
apify_run_actor(
  actor="magicbricks-99acres",
  input={
    "source": "magicbricks",         # magicbricks | 99acres | both
    "transactionType": "sale",       # sale | rent
    "cities": ["Bangalore"],         # MAGICBRICKS city name — "Bangalore", NOT "Bengaluru" (0 results)
    "maxResults": 20,                # keep small — cost control
    "proxyConfiguration": {
      "useApifyProxy": true,
      "apifyProxyGroups": ["RESIDENTIAL"],
      "apifyProxyCountry": "IN"
    }
  },
  max_items=50
)
```

Returns: title, source, price + priceDisplay, BHK, area/areaUnit/areaType,
locality, projectName, latitude/longitude (when published), propertyUrl,
imageUrl.

## Procedure

1. **Understand the request.** Listings with prices → Apify. Live site
   interaction → `browser_use_cloud`. Coordinates → Maps path. General
   context → `web_search`.
2. **Portal listings:** call `apify_run_actor` with the preset. Keep
   `maxResults` ≤ 20 per run unless the user explicitly wants volume —
   warn about cost (~$3 per 1,000 records) before large runs.
3. **Google Maps coordinates:** run Playwright via `execute_code` in the
   container with `chromium_headless_shell`; set `CONSENT`/`SOCS` cookies
   first (Google refuses first-run consent without them). Keep batches
   small — the VPS has ~3.7 GB RAM; the browser can be OOM-killed on long
   runs (EPIPE = browser died; retry in smaller batches).
4. **Live browser work:** `browser_use_cloud` with `pause_on_failure=True`
   (default). Always echo the `live_url` to the user.
5. **Synthesize:** return a structured summary — project, locality,
   price (INR + display), BHK, area, source URL. Cross-check 2+ sources
   when possible.

## Pitfalls

- **Portals block the VPS IP at network level** (Akamai on 99acres etc.).
  Raw `curl`/Playwright/`web_extract` from the VPS will fail or return
  bot pages. Use `apify_run_actor` — Apify's residential proxies (India)
  handle this.
- **Apify city names are MagicBricks names.** "Bangalore" returns listings;
  "Bengaluru" returns an empty dataset with SUCCEEDED status. Use portal
  city names and verify item count > 0 before reporting.
- **Apify actors need `proxyConfiguration`** with `RESIDENTIAL` group +
  `apifyProxyCountry: "IN"` for portal access — without it the actor
  succeeds with 0 results.
- **Apify bills per result.** Failed/blocked pages don't charge, but the
  run itself costs platform usage. Keep `maxResults` small.
- **`browser_use_cloud` costs session credits.** Prefer `max_steps`
  ≤ 20 for simple lookups.
- **Don't retry blocked sites more than twice.** After 2 failed attempts,
  switch strategy (Apify instead of browser, Tavily instead of Firecrawl)
  and tell the user what changed.
- **Never generate portal/API URLs by hand.** Use the returned
  `propertyUrl`/`live_url` verbatim.

## Verification

- Listing records contain price, BHK, area, locality/project, and a
  source URL.
- Google Maps coordinates land inside the expected district bounds.
- At least 2 sources agree on price range before reporting a figure.
- Tell the user the cost implication when a run exceeds ~1,000 records.
