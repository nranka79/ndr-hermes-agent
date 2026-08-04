---
name: property-pricing-sources
description: "Collect per-sqft / per-unit property pricing for Indian real estate (Bangalore, Chennai, Devanahalli, Nandi Hills corridors). Documents which property portals are reachable from the Hermes VPS, which need Apify/browser fallbacks, and the Google-search-snippet technique for rate bands. Use for R&D competitor pricing, land/project valuation, and investment research."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Property Pricing Sources (India)

Use when the user needs **per-sqft or per-unit price data** for Indian real estate — competitor projects, plots, villas, apartments, farmland, gated communities. Especially for the Devanahalli / Nandi Hills / Doddaballapur corridor around Thylagere.

## Source Inventory (tested Aug 2026 from Hermes VPS)

### Directly accessible from VPS (HTTP 200 via curl)
- **NoBroker** (nobroker.in) — plot/land listings with price + sqft; publishes locality avg price/sq-yard. Works directly.
- **99sqft** (99sqft.com) — works directly.
- **Propzilla** (propzilla.in) — works directly.
- **QuikrHomes** (quikrhomes.com) — works directly.
- **CrazyAssets** (crazyassets.com) — investment guides with per-sqft bands (e.g. Devanahalli villas ₹5,250–7,500/sqft).
- **Bulwark / builder sites** (e.g. bulwarkthewoodlandforest.in) — often publish locality rate tables (Devanahalli apartments 6500–11000, plots 3500–6900, 30x40 total 50–85 L).
- **Homznspace** (homznspace.com) — per-project price tables (unit type / plot area / built-up / agreement price), e.g. TE Over the Rainbow 3000 sqft @ ₹7.14 Cr; Prestige Golfshire 4BHK from ₹9 Cr.
- **PropertyCrow** (propertycrow.com) — per-project floor-plan price tables (e.g. Brigade Orchards 1BHK ₹46L → 4BHK villa ₹3.13 Cr).
- **Proplocators** (proplocators.com) — per-project per-sqft rates (e.g. TE Over the Rainbow ₹23,800/sqft).
- **HousingMan** (housingman.com) — per-project base price (e.g. Esteem Misty Hills plots ₹2,100/sqft).
- **Official builder sites / PDFs** — plot pricing sheets (Canterbury Orchards II ₹2,000/sqft; AMT Kadamba 6000 sqft @ ₹1.79 Cr; Godrej price-sheet).
- **360Realtors, Regrob, RespaceInfra, LavishLiving, UrbanFlatsHub** — project microsites with price tables and Devanahalli market guides (2026 plot range ₹5,300–13,000/sqft).

### Blocked from VPS (403/406 — need Apify actor or Google snippet)
- **99acres** (99acres.com) — 403. Use Apify actor `codingfrontend/99acres-projects-search-scraper` (project detail pages = per-project totals; **does NOT return per-sqft or area** — area fields are null). Price-rate page `property-rates-and-price-trends-in-<loc>-prffid` gives locality bands via Google snippet.
- **MagicBricks** (magicbricks.com) — 403. Rate pages `Property-Rates-Trends/...-<loc>-in-Bangalore` give locality bands via Google snippet.
- **Housing.com** — 406. Price-trends pages (`housing.com/price-trends/property-rates-for-buy-in-<loc>`) indexed by Google.
- **CommonFloor** — 403 (owned by Quikr; portal still live).
- **SquareYards** — 403.
- **Makaan** — 406.
- **Sulekha Properties** — 403.
- **PropTiger** — 404 on /buy/projects paths; effectively unavailable.
- **Google Maps / Places** — for POI coords, not prices.

## Best-Effort Per-Sqft Workflow

1. **Per-project**: try NoBroker + 99sqft directly (curl OK). For blocked portals, run the Apify 99acres actor for total price ranges; if per-sqft is needed and the user accepts locality bands, fall through to step 2.
2. **Locality bands via Google snippets** (works from VPS, no proxy needed):
   ```
   web_search("\"Devanahalli\" plots \"per sq ft\" OR \"per sqft\" rate 2026")
   web_search("Devanahalli Bangalore property price per sqft 2026 residential plots villas")
   ```
   Snippet descriptions from 99acres/MagicBricks/Housing rate pages carry the bands (e.g. "Land rates Rs 3350-9550 per sq ft").
3. **Per-sqft from total + area**: when a listing has both total price and area, compute rate = total / area. Never fabricate; if area missing, mark per-sqft as N/A and cite the source limitation.

## Area-Search Discovery — the verified fix for name-driven gaps (Aug 2026)

**Lesson restated:** the Thylagere competitor list was built name-seeded, so mid-market
projects like Sammy's Palm Hills never entered the funnel. The verified fix is
**locality-first AREA-search URLs on 99acres** via the account's
`99acres-projects-search-scraper` actor (`hHadmAwXCpNrsHH2O`), input key `searchUrls`:

```json
{"searchUrls": [
  "https://www.99acres.com/plots-in-devanahalli-bangalore-north-ffid",
  "https://www.99acres.com/villas-in-devanahalli-bangalore-north-ffid",
  "https://www.99acres.com/apartments-in-devanahalli-bangalore-north-ffid",
  "https://www.99acres.com/new-projects-in-devanahalli-bangalore-north-ffid"
], "maxItems": 120, "enableDeepScraping": false, "headless": true}
```

URL pattern: `https://www.99acres.com/{plots|villas|apartments|new-projects}-in-<locality>-<zone>-ffid`.
Verified 03-Aug-2026: **134 records** for Devanahalli, including mid-market projects the npxid
path never surfaced. NEVER feed project npxid pages (`...-npxid-r280367`) for discovery — they
return only marquee-biased "similar projects".

Post-processing (both observed live):
- **Dedupe/canonicalize:** same project recurs with/without locality suffix ("Assetz City Of
  Palms Ivc" vs "...IVC Road, Bangalore North"). Strip suffixes before matching.
- **Filter out-of-area records:** results include other-city projects (Casagrand Moondance =
  Mysore Road, Sobha Royal Crest = Banashankari, Sobha Manhattan Towers = Yadavanahalli, TVS
  Emerald Jardin = Singasandra). Verify each project's actual locality before adding.

## Places Geocoding — ALWAYS anchor location (Aug 2026)

`crawler-google-places` (`nwua9Gu5YrADL7ZDj`) with bare `searchStringsArray` wanders to random
coordinates (observed Kolkata 22.9,88.3 for Devanahalli queries). Always pass:

```json
{"searchStringsArray": ["Prestige Gardenia Estate Devanahalli", "..."],
 "locationQuery": "Devanahalli, Karnataka, India",
 "maxCrawledPlacesPerSearch": 1, "language": "en", "countryCode": "in", "searchMatching": "all"}
```

Lat/lon nest at `item["location"]["lat"]` / `item["location"]["lng"]` (not top-level).
Nominatim (OSM) resolves towns (Devanahalli ✓) but NOT villages (Beedaganahalli ✗) or project
names — not a substitute for Places.

**Anchor boundary size matters (Aug 2026, Anekal belt).** `locationQuery` must be a LARGE
boundary, not the town itself. Anchoring at `"Anekal, Karnataka, India"` Nominatim-geocodes to the
tiny town box (~1 km, zoom 18) and the actor filters EVERY real project as `outOfLocation` →
0 scraped. Anchoring at the city (`"Bengaluru"` + `searchMatching: all`) returns plenty but Google
ranks central-Bangalore results first — observed 79 places, ALL 16–41 km from the target. Working
combo: city-level anchor + `searchMatching: all` + post-hoc haversine radius filter (15 km) in
your own cleanup. A town anchor is a silent zero-result trap.

**Apify FREE-plan credit wall (Aug 2026).** The shared account has a ~$0.50 minimum launch
reserve per paid actor; below it every launch fails with `not-enough-usage-to-run-paid-actor`. A
concurrent team-member run can drain the balance mid-task, silently blocking all further launches
(mid-run: 99acres succeeded with ~$0.73 spent, then the Places actor's next 8 launches were
rejected with $0.347 left). Check before launching:
`curl -s "https://api.apify.com/v2/users/me?token=$APIFY_API_KEY"` — plan=FREE means credits are
metered. When the wall hits, pivot geocoding to the Playwright headless batch (`maps` skill,
`geocode_batch_subproc.py`) — zero Apify credits needed, worked 114/115 in the same run.

## Per-Sqft Extraction from Search Snippets (validated technique)

Worked for ~33/53 projects in the Aug 2026 Devanahalli run:

1. Per project: `web_search('"<project>" Devanahalli price per sqft', limit=4)`.
2. Extract from snippet descriptions with loose patterns
   (`(?:₹|Rs\.?|INR)\s*[\d,]+...\s*(?:per\s*sq|/sq|per\s*sft|/sft)`), allowing
   ranges ("Rs 9,200 - 9,500/sqft") and single values.
3. **Validate every hit against the raw snippet** — the biggest trap is
   *wrong-row locality tables*: 99acres "Project vs Locality Price" tables
   embed in search results, and the row shown may be the LOCALITY average for
   a DIFFERENT project or a ₹/sq-YARD figure, not the project's own rate.
   Observed wrong values: Century Seasons "₹66,875/sqft" (actually a
   locality-comparison row; the project's real resale is ₹6,681–9,200/sqft),
   Canterbury Castles "₹27,942–31,670/sqft" (locality trend row; real resale
   ₹5,466/sqft), and Bulwark Northern Boulevard "₹60,220/sqft" (same artifact;
   real ₹5,257–6,022/sqft). Any value > ~₹20,000/sqft for a Devanahalli-area
   project is suspicious — re-check the snippet context.
4. Cross-check each rate against the locality band (below) — a project rate
   wildly outside its type band is usually a misparse.
5. Prefer official builder-page quotes and 99acres listing snippets over
   estimate sites; mark "(approx)" where derived from total÷area.
6. **Marquee-project rates worth memorizing (Aug 2026, cross-checked):**
   Prestige Sanctuary ₹17,000/sqft (4085 sqft @ ₹6.94 Cr); Prestige Golfshire
   ₹32,837/sqft (MagicBricks avg; 99acres resale ₹32,727/sqft); Montira
   ₹10,800/sqft; Triton Humming Valley ₹9,200–10,200/sqft; Over the Rainbow
   (TE) ₹23,800/sqft (3000 sqft @ ₹7.14 Cr); Godrej Reserve ₹8,477–10,416/sqft
   (resale plots); DNR Solace ₹7,709–11,140/sqft; Chartered Fireflies
   ₹11,350/sqft; Birla Trimaya ₹10,124/sqft; Brigade Orchards ₹12,396/sqft avg.

## Known Devanahalli Rate Bands (mid-2026, cross-checked)
- Apartments: ₹6,500–11,550/sqft (99acres 8800–11550; Bulwark 6500–11000)
- Plots / land: ₹3,350–9,550/sqft (99acres); ₹3,600–6,900/sqft (MagicBricks); NoBroker avg ₹58,572/sq-yard (~₹6,508/sqft); gated-community 1000 sqft plot ~₹65L
- Villa plots: ₹5,250–7,500/sqft (CrazyAssets; Scribd case study ₹7,500 avg)
- Plotted developments: from ₹4,800–5,400/sqft
- 30x40 plot total: ₹50 L–85 L; villa projects total ₹1.5 Cr+

## Pitfalls
- **KML label format (NDR preference, stated Aug 2026):** competitor labels must carry the **per-sqft rate alongside the name** — `Prestige Sanctuary | Rs 17,000/sqft`. NOT ticket/total prices. If only totals exist, compute rate = total ÷ area and mark `(approx)`; if neither, no label. The user checks the KML for per-sqft — a marquee project with no rate in the label is a visible miss (happened with Prestige Sanctuary, Prestige Golfshire, Montira).
- **Name-driven discovery misses projects.** The Aug-2026 Thylagere competitor list was built by searching *known project names*; it missed **Sammy's Palm Hills** (Sammy's Dreamland Co., Beedaganahalli 13.356528, 77.725266; 447 plots/32 ac; base Rs 2,300/sqft; plots Rs 24.5L–92L) which sits **6.3 km** from the subject land — inside any 10 km scan. Lesson: for completeness, scan by **radius** (Haversine over sheet coords at 5/10 km) and cross-check Places "near" results, never rely on names alone. Blueprint for the radius tool: `references/property-rd-tool-design.md`.
- **99acres deep-scrape gives totals only** — `price.displayPrice` (e.g. "₹6.94 - 11.36 Cr") with `area.min/max = null`. Per-sqft CANNOT be derived from it. Don't invent sqft rates from it.- **Apify preset `magicbricks-99acres` mapper is broken** (`apify_run_actor` fails). Use raw API calls to `api.apify.com/v2/acts/<owner~actor>/runs` with `APIFY_API_KEY` env var.
- **MagicBricks `fascinating_lentil/magicbricks-99acres-property-scraper` is stale** — MagicBricks parser returns 0, 99acres blocked even via residential proxy. Don't rely on it.
- **Rate pages are JS-heavy but Google-indexed** — the snippet descriptions carry the numbers even when the page itself is 403/406 to us.
- Never fabricate per-sqft. If only totals are available, report totals and say per-sqft is unavailable from that source.
- Always cross-check at least 2 sources for rate bands; portal averages vary by quarter and by micro-locality.

## References

- `references/devanahalli-per-sqft-curated-aug2026.md` — verified mid-2026 per-sqft rates for ~35 Devanahalli/Nandi Hills projects (new projects, plotted devs, villas, gated, farms, apartments), locality rate bands, and Places-verified coords for the religious POIs (Isha/Sadhguru Sannidhi, Radha Soami Satsang Beas). **Also holds the 03-Aug-2026 area-search additions** (~30 more projects found via the locality-first `-ffid` run — Assetz City of Palms, TE Tangled Up in Green, Prestige Crystal Lawns/Gardenia, Sobha Oakshire, Konig Pearl/North County, Embassy Greenshore/Verde/Edge, Bhartiya Garden Estate, etc., with Places coords). Reuse before re-searching; re-verify for formal documents.
- `references/karnataka-land-price-govt-sources.md` — **per-acre land benchmarks + government sources** (Kaveri 2.0 guidance values, IGR, KIADB acquisition compensation ₹2.70 Cr/acre Jun 2026, findcirclerate.com extraction, market per-acre bands for Nandi Hills/Devanahalli corridor). Use when the user asks for "current land prices from Kaveri/government sources" — complements the per-sqft reference above.
- `references/anekal-attibele-belt-pricing-aug2026.md` — verified Aug-2026 per-sqft rates for the Anekal/Attibele/Bestamanahalli belt (Bangalore South / SH-35 + Hosur Rd corridor): ~40 project prices, locality rate bands, per-acre benchmarks (agri ₹1–2 Cr/acre vs converted ₹13–26 Cr/acre), and the out-of-belt name-collision list (Adarsh Tropica, Birla Tisya, Godrej Ananda Ph2 Bagalur, etc.). Reuse before re-searching this belt.
- `references/` under the `location-research` skill — Places API re-verification, 99acres deep-scrape pricing recipe, KML icon inventory, terminal `&`-guard workaround.
