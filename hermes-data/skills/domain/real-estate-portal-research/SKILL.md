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

The VPS runs on a datacenter IP that the portals network-block, BUT the
residential tunnel SOCKS (`socks5h://hermes-utilities:1000`) is
**domain-policy routed**: residential-listed domains (MagicBricks,
NoBroker, rera.tn.gov.in) exit from the residential node and are directly
reachable with plain curl/Playwright through the tunnel. Verified
2026-08-12: MagicBricks 200, NoBroker 200 through the tunnel; 99acres
still 403 (Akamai browser fingerprinting, not IP-blocking — residential
IPs get denied too). The skill's core rule is therefore: **never scrape
portals with raw HTTP/curl/browser from the bare VPS IP — go through the
tunnel SOCKS first (reachable portals), then Apify/Tavily for the rest.**
Full working recipes in `references/tunnel-portal-scraping-recipes.md`.

## When to Use

- User asks for property prices / listings / projects (villa, flat, land) in an Indian city
- Market research for real-estate projects (e.g. "13 villa projects near Devanahalli")
- Google Maps coordinates for project locations
- Comparing prices across 99acres / MagicBricks / Housing.com

## Prerequisites

- API keys live in the process environment (some hosts have no
  `/opt/hermes/.env`). On the current host they appear as suffixed
  variants: `TAVILY_API_KEY_2`/`_3`, `APIFY_API_KEY`/`_2`/`_3`,
  `FIRECRAWL_API_KEY_2`/`_3`. Verify before assuming a tool is
  unconfigured: `env | grep -iE 'tavily|apify|firecrawl'`.
- If Tavily calls return HTTP 401 from `execute_code` while the terminal
  works, the sandbox venv doesn't inherit those vars — run API calls from
  terminal python (`urllib`/curl) instead of execute_code.
- `BROWSER_USE_API_KEY` set for `browser_use_cloud` (Browser Use Cloud account)
- The smart-browser sidecar container (`smart-browser`) running for `smart_browser`

## NDR preference: tunnel-direct over Apify (2026-08-12 directive)

NDR: "Don't use [Apify]. If I just use playwright and the browsers directly
and given that the socks is set up, it will tunnel it via residential client
nodes." — the VPS sidecar browsers (`browser_navigate`, `smart_browser`,
Playwright headless) are wired through the residential tunnel SOCKS, so they
egress from residential nodes and can reach portals without Apify. On
2026-08-12 NDR repeated the point mid-run: "I don't see any reason to use
apify." Same run, when the agent started manually wiring socks into raw
Playwright, NDR corrected: **"You don't need to route it through the
tunnel socks and point as the browsers are already configured to do
that."** Hermes' own browser tooling (browser_navigate, smart_browser)
is pre-wired to the residential tunnel (AGENT_BROWSER_PROXY env =
socks5://hermes-utilities:1000) — do NOT add manual proxy flags to those
tools. Only standalone curl / raw Playwright scripts launched from a
shell need the explicit `-x socks5h://hermes-utilities:1000` /
`proxy={"server": "socks5://hermes-utilities:1000"}` (the env var is not
inherited by every shell context). Preferred order for portal listing
extraction:

1. `web_search` (Tavily) snippets — free, fast, carries listing title/price/
   area/date/URL.
2. **Tunnel-direct scrape** (`curl -x socks5h://hermes-utilities:1000` or
   Playwright with `proxy={"server": "socks5://hermes-utilities:1000"}`) on
   the portal's listing/project page — WORKS for MagicBricks (server-rendered
   JSON-LD + card text; paginate `?page=N`), NoBroker (SEO pages render via
   JS; dismiss the login popup with Escape, then read body text), and
   rera.tn.gov.in. Exact URL patterns, JSON-LD block layout, card-parsing
   regexes: `references/tunnel-portal-scraping-recipes.md`.
3. `apify_run_actor` — LAST RESORT only (Apify FREE-plan credit wall also
   blocks it mid-run; all keys get rejected after ~1 run).

**Directive extended to ALL research (2026-08-15):** NDR: "dont use apify of
tavily. use direct browser search." For non-portal research (metro/infra/news,
route maps, KML) the fallback ladder — Google News RSS, Wikipedia API, OSM
Overpass/Nominatim, Jina page+search proxy, Commons/GitHub — lives in the
`research-web-tools` skill: `references/direct-browser-search-no-api.md`.

## NDR scope preference: SMALL-N comparable research (2026-08-15)

When NDR asks for "N projects around X" (e.g. "five residential apartments
around Brigade Meadows"), he means EXACTLY that number — "five only. I don't
need a hundred data points." Do not expand the sample or pad with extras:
- Deliver exactly N projects × ~5 listings each (his standard cell), with
  per-listing URL tracked and per-project average rate/sqft.
- RERA start/end dates per project are part of the standard deliverable.
- When asked for a spreadsheet: two sheets — (1) project averages (avg,
  median, min, max rate/sqft + avg price + RERA start/end), (2) every
  listing with its own rate/sqft and a clickable listing link. See
  `references/xlsx-deliverable-build.md` for the verified build recipe
  (openpyxl via `uv run --with openpyxl`, explicit cell writes, and the
  self-verification that catches silent row-loss on save).

## How to Run

Pick the tool for the task type:

| Task | Tool | Notes |
|---|---|---|
| General web search | `web_search` | Tavily backend; works from the datacenter IP |
| MagicBricks listings | tunnel curl/Playwright | `-x socks5h://hermes-utilities:1000`; JSON-LD + card text; see `references/tunnel-portal-scraping-recipes.md` |
| MagicBricks project rate | tunnel curl, project hub page | `/project-<slug>-for-sale-in-<city>-pppfs` SSR HTML carries `₹X Cr/Lac` + `₹Y per sqft` per listing — psf direct, no Apify; recipe in `references/tunnel-portal-scraping-recipes.md` |
| NoBroker listings | tunnel Playwright | SEO pages, Escape popup, body-text cards; see recipes reference |
| 99acres-only listings | `browser_navigate`/`smart_browser`, or tunnel curl with FULL browser headers | real Chromium fingerprint returns 200 (curl-minimal 403s are fingerprint, not IP); see recipes reference |
| Google Maps / Places results | `apify_run_actor` | preset `google-places` |
| Live browsing / forms / logins | `browser_use_cloud` | cloud IPs; always share `live_url` |
| Non-blocked site browsing | `smart_browser` | VPS sidecar (browser-use + Playwright) |
| Google Maps coordinates | `execute_code` + Playwright `headless_shell` | needs CONSENT/SOCS cookies; small batches |
| Page content extraction | `web_extract` | Tavily backend; portal pages are usually bot-protected — use tunnel/Apify for those |

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

## Finding per-project portal PAGE URLs for deck source links (web_search, no Apify spend)

When building source-link bars on project slides (`📍 Google Maps │ 🏠 MagicBricks │ 🏘️ 99acres`), you need a REAL project page URL per portal — not a constructed guess. This is a web_search job, not an Apify run (no listing payload needed, free):

- Query pattern that works: `"<Project Name>" 99acres OR magicbricks` — add a locality qualifier for generic names (`"Montira" Devanahalli` → found as "Rare Earth Montira Nandi Hills"; `"Belmont"` → "Citrus Belmont").
- **MagicBricks URL shapes to prefer:** `/project-plots-<slug>-for-sale-in-bangalore-pppfs` (project listings hub) or `/pdpid-<hex>` (specific listing page). Avoid generic search-result pages.
- **99acres URL shapes to prefer:** `/<slug>-<locality>-bangalore-north-npxid-r<digits>` (project page) or `-npffid` (resale listings for the project). A `-spid-` URL is a single-plot listing — fine but only one unit.
- **Official developer site / aggregator as fallback:** projects with no portal page (old/pre-RERA layouts) still get a link — developer site or a real-estate aggregator page. Tell the user which links are fallbacks.
- Do NOT spend an Apify run just to get page URLs — `web_search` returns them from the portal SERP without paying per-result.

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

- **Portals block the BARE VPS IP at network level** (Akamai on 99acres
  etc.). Raw `curl`/Playwright from the datacenter IP fails. BUT the
  tunnel SOCKS (`socks5h://hermes-utilities:1000`) routes
  residential-listed domains via the residential node — MagicBricks,
  NoBroker and rera.tn.gov.in return 200 through it. Try the tunnel FIRST;
  only fall to Apify for what the tunnel still can't reach (99acres).
- **Stale cached listing files poison a new belt (hit 2026-08-12).** A
  `/tmp/listings_final.json` from a previous run can be a DIFFERENT belt
  (Devanahalli/Nandi Hills rows) and look plausible at a glance. Before
  merging any cached listings JSON into a new run, check the locality
  slugs / URLs inside (`Devanahalli` vs `Hosur`) — scrape fresh for the
  current pin. Never reuse a cached haul across belts.
- **Never present locality-level listings as project-specific data (2026-08-26, Sterlitee Regal Park).** When major portals return 0 plot listings inside the project name, locality-level fallback plots belong to OTHER projects in the same area — NOT the requested one. The user will call this out. Follow the protocol in `references/secondary-portal-project-pricing.md`: state the absence clearly, check secondary aggregator sites for developer pricing, and label locality data explicitly.
- **99acres 403s only for curl-fingerprint requests (verified 2026-08-28).** Akamai blocks curl/minimal-header requests from ANY IP (VPS or residential), but a **real browser fingerprint returns 200 from the same IP** — including the VPS IP. Use `browser_navigate`/`smart_browser` (real Chromium) or curl with a FULL browser header set (User-Agent + Accept + Accept-Language + sec-ch-ua + Sec-Fetch-*) through the tunnel. A bare `-A "Mozilla/5.0 ..."` curl still 403s — that's fingerprint, not an IP block. Don't conclude "site blocked" from a curl result alone.
- **Housing.com 406s even through the residential tunnel (verified
  2026-08-12).** WAF `Security Alert` on every path (listing pages, APIs,
  even `/sitemap.xml`). The error page's `Real Client IP` field showed the
  Bengaluru residential node IP (119.82.120.164) — so the tunnel WAS
  egressing residential and the WAF still blocked: fingerprint-based, same
  class as 99acres. playwright-stealth didn't help either. Cover via
  Tavily snippets. Use the WAF error page's `Real Client IP` field to
  confirm which node a site sees before blaming the tunnel.
- **NoBroker SEO URLs need the city suffix (hit 2026-08-12).**
  `/villas-for-sale-in-hosur` (no suffix) returns 410 Gone + redirects to
  homepage; the working form is `/villas-for-sale-in-hosur_bangalore`
  (Hosur is TN but its slug is `_bangalore`). Also: when merging a
  re-sweep into an existing capture file, only overwrite a locality when
  the new result is non-empty — a transient 0-card run will clobber good
  rows otherwise.
- **Don't judge tunnel health with IP-echo services.** `api.ipify.org`
  through the tunnel shows the VPS IP (Hetzner) because the router's
  domain policy sends non-residential-listed domains out the VPS IP — that
  does NOT mean the tunnel is broken. Test with the actual portal domain.
- **Apify city names are MagicBricks names.** "Bangalore" returns listings;
  "Bengaluru" returns an empty dataset with SUCCEEDED status. Use portal
  city names and verify item count > 0 before reporting.
- **`magicbricks-99acres` preset is whole-CITY, not locality-targeted (hit
  2026-08-11).** With `cities: ["Bangalore"]` it returns listings from all
  over the metro (Sarjapur, Whitefield, Hebbal...) and 0 matches for a
  Devanahalli belt query — the actor has no locality/project filter. For
  per-project pricing use `browser_use_cloud` on the project's own portal
  page (extract the "Listings in <Project>" section) or the
  `codingfrontend/99acres-projects-search-scraper` with locality-first
  `-ffid` searchUrls. Don't burn a run expecting the preset to target a
  suburb.
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

## References

- `references/secondary-portal-project-pricing.md` — project-specific developer
  pricing from secondary aggregator sites (RathiGlobalRealty, PropNewz,
  PropertySuggest, NewRealtyProject) when major portals return zero plot listings.
  Covers: tunnel SOCKS access, what data each site carries, how to extract
  pricing grids from MagicBricks ad_text JSON-LD, and the hard rule to NEVER
  present locality-fallback listings as project-specific data (2026-08-26
  Sterlitee Regal Park correction).
- `references/brigade-meadows-belt-2026-08.md` — session R&D (2026-08-15):
  nearest-5-apartment-projects workflow around Brigade Meadows (anchor pin →
  MB locality hubs → K-RERA coords → haversine rank), Bannerghatta-corridor
  MB slugs that work, per-project listing averages + RERA dates for 5
  projects (Provident Park Square, Oceanus White Meadows, Prestige Park
  Square, Casagrand Hazen, Prestige Elysian).
- `references/tunnel-portal-scraping-recipes.md` — verified 2026-08-12
  tunnel-direct recipes: SOCKS endpoint + router domain policy, MagicBricks
  URL patterns / JSON-LD block layout / card parsing, NoBroker SEO-page
  flow (Escape popup, body-text cards), and the 99acres Akamai-fingerprint
  block. Read before any tunnel scrape.
- `references/xlsx-deliverable-build.md` — verified 2026-08-15 spreadsheet
  build recipe: two-sheet deliverable shape, `uv run --with openpyxl`,
  explicit-cell-writes (NOT ws.append — silent first-row loss), and the
  reopen-and-assert self-verification (project/listing/hyperlink counts).
