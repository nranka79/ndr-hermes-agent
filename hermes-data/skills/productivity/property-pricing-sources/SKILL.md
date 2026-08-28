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
- **NoBroker** (nobroker.in) — plot/land listings with price + sqft; publishes locality avg price/sq-yard. **Project pages render a live "avg ₹X per sq ft" banner** (`https://www.nobroker.in/flats-for-sale-in-<project-slug>-prjtl`) — a priority-1 per-sqft source that worked in the 2026-08 T3 run (Sattva Park Cubix ₹9,691, Brigade Atmosphere ₹6,443, Ivory ₹11,390, all current-month).
- **NoBroker villa-listing pages pair project + price + area in one curl (validated 2026-08-20, Sarjapur run).** `curl -sL "https://www.nobroker.in/villas-for-sale-in-<locality>-bangalore"` returns a ~780KB HTML page carrying `propertyTitle` (e.g. "4 BHK Villa In Confident Atria For Sale In Sarjapur"), `price` (raw rupees, e.g. 23000000) and `carpetArea` (e.g. 2200) in embedded JSON. These three arrays are position-aligned per listing → compute psf = price/area directly, project-level prices from live listings with NO browser and NO Apify. Filter junk: skip carpetArea <300 or >8000 sqft (page also embeds non-listing `title` noise like 'Dining','Kitchen' — anchor on `propertyTitle`, not generic `title`). This is the fastest reliable project-level villa pricing path when web_search/Tavily is down and browser subagents are slow. Follow redirects with `-L` and send a desktop UA (needs `python re.findall` — inline bash regex with `₹`/`Cr` breaks shell quoting; write a .py file instead).
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
reserve per paid actor; below it every launch fails with `not-enough-usage-to-run-paid-actor`.
When the MONTHLY limit is exhausted (not just the reserve), launches fail with
HTTP 403 `platform-feature-disabled` / `"Monthly usage hard limit exceeded"` — hit
2026-08-12. Check before launching:
`curl -s "https://api.apify.com/v2/users/me?token=$APIFY_API_KEY"` — plan=FREE means credits are
metered. When the wall hits, pivot geocoding to the Playwright headless batch (`maps` skill,
`geocode_batch_subproc.py`) — zero Apify credits needed, worked 114/115 in the same run — and
pivot listing/pricing mining to the Tavily direct-API fallback above.

## NoBroker plot / villa / flat detail + list pages — plain-requests JSON (verified 2026-08-26, Sterlitee Regal Park belt)

**Big refinement to the "NoBroker needs tunnel + Playwright" rule:** for the
*list* pages (villas/flats) AND every *individual detail* page, plain
`requests` from the datacenter IP works — no tunnel, no Playwright — and the
detail pages carry **clean embedded JSON** (`propertyTitle`, `price`,
`propertySize`, `plotArea`, `creationDate`, `lastUpdateDate`, `uploadedBy`
= OWNER|AGENT, `active`). This is the fastest path to verified, dated,
owner-vs-broker-labelled listing data. WHAT still 410s / needs JS:
- `plots-for-sale-in-<locality>_bangalore` list pages → **410 Gone** (blocked).
- Project pages (`<project>-prjt-...`) load resale listings via XHR — no
  embedded JSON on the SSR.

Working URL shapes (all confirmed HTTP 200 with plain requests):
- Villa/flat list (has prices): `/villas-for-sale-in-<loc>_bangalore`,
  `/flats-for-sale-in-<loc>_bangalore` → embedded `propertyTitle`, `price`,
  `carpetArea` arrays (position-aligned; carpet can be 0 = skip that row).
- **Individual plot detail** (the workhorse for plotted-land comps):
  `/property/plot/buy/plot-for-sale-in-<project>-bangalore/<32-hex-id>/detail`
  → full JSON with `plotArea`, `creationDate`, `lastUpdateDate`,
  `uploadedBy` (OWNER or AGENT), `active`, `propertyTitle`.
- Individual villa/apartment detail:
  `/property/buy/<n>-bhk-...-for-sale-in-<loc>-bangalore/<32-hex>/detail`.

Recipe for plotted-development pricing (plotted devs have active in-project
plot resales on NoBroker project pages but the list page 410s):
1. DDG-via-Jina discovery: `curl https://r.jina.ai/https://html.duckduckgo.com/html/?q=<project>+plot+for+sale+nobroker`
   → grep `uddg=` URLs, unquote → collect `.../property/plot/buy/.../detail` URLs.
2. `requests.get()` each detail URL, `requests.Session()` with a desktop UA.
3. Regex the JSON: `"price":\s*(\d+)`, `"plotArea":\s*(\d+)`,
   `"uploadedBy":\s*"(\w+)"`, `"creationDate":\s*(\d+)`,
   `"lastUpdateDate":\s*(\d+)` (millisecond ts → datetime.utcfromtimestamp/1000).
4. psf = price/plotArea. Verify `active: true` + `lastUpdateDate` within 3 months
   before reporting — filters expired listings automatically.

## MagicBricks plot listing URL encoding (verified 2026-08-26)

MagicBricks plot listing URLs from the search/hub pages
(`https://www.magicbricks.com/propertyDetails-<area>-FOR-Sale-<loc>-in-Bangalore&id=<base64>...`)
work **through the SOCKS tunnel** (`requests.Session().proxies=...`). Two gotchas:
- The `&id=` base64 contains `+` and `=` which MUST be URL-encoded (`%2B`, `%3D`)
  or the request 404s. Both the `propertyDetails-<area>-FOR-Sale-...&id=...` and
  the slash form `propertyDetails/<area>-...&id=...` work when encoded.
- **Always liveness-verify the listing URL before reporting it** — the user
  clicks every link. Batch-check with a tunnel session: some rows in a locality
  sweep 404 even when siblings 200 (broker pull-downs); drop the 404s, keep 200s.
- Plot list pages carry `Resale` (broker) vs `New Property` (dev/direct) in the
  title — that's the broker-vs-developer signal for plots.

## Tavily Direct-API Fallback (when `web_search` tool is unavailable)

Hit 2026-08-12 (Hosur belt run): the session had no `web_search` tool and
the env var was suffixed (`TAVILY_API_KEY_2`), so the built-in tool failed
but the Tavily REST API worked fine via curl. This is the documented
fallback for snippet mining when the tool wrapper is missing/empty:

```bash
KEY=$(env | grep '^TAVILY_API_KEY_2=' | cut -d= -f2-)
curl -s --max-time 30 "https://api.tavily.com/search" \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$KEY\", \"query\": \"villas in Hosur for sale price\", \"max_results\": 5, \"search_depth\": \"basic\"}"
```

- Response shape: `{"results": [{"title", "content", "url"}]}` — same
  snippet-mining material as `web_search`.
- Key discovery: grep `env` for `TAVILY_API_KEY*` — the env var may carry
  a numeric suffix (`_2`, `_3`). Don't assume the plain name is set.
- Works from the VPS without proxies (Tavily is a hosted API).
- Validated on the Ranka Oasis/Hosur run: queries like "villas in Hosur
  for sale price" returned 99acres/MagicBricks/Housing.com snippets with
  per-sqft bands (₹7,083/sqft 2BHK villas, ₹5.79-6.97K/sqft ranges).
- When Apify is ALSO dead (monthly FREE limit — HTTP 403
  `platform-feature-disabled` / "Monthly usage hard limit exceeded"),
  this + direct-reachable portals (NoBroker/99sqft/QuikrHomes) + Playwright
  geocoding is the full pivot.
- **Tavily `/extract` beats search snippets for Akamai-blocked 99acres
  project pages (validated 2026-08-15, Inspira Winds of Life).** The
  npxid project page returns `raw_content` with the full price range
  (₹1.47–2.14 Cr), super built-up area range, the "Floor Plans and Price
  List" table, facilities count, open-area %, possession date — zero
  Apify spend. Call `https://api.tavily.com/extract` with
  `{"urls": ["<99acres project URL>"], "extract_depth": "advanced"}` and
  grep raw_content for `PRICE RANGE` / `Floor Plans and Price List` /
  `Completion in`. Use this BEFORE the Apify 99acres actor when credits
  are tight or the project is single-target.
- **MagicBricks project hub page via tunnel curl exposes the whole
  pricing picture in JSON-LD (validated same run).** For
  `/project-<slug>-<locality>-...-pdpid-<hex>` fetched with
  `curl -x socks5h://hermes-utilities:1000`, parse the
  `application/ld+json` blocks: AggregateOffer gives
  lowPrice/highPrice/offerCount, additionalProperty carries the RERA
  number, description carries launch + possession dates and towers/units,
  and one listing JSON carries `sqFtPrD` (per-sqft). The visible text
  also carries the Project-vs-Locality quarterly per-sqft trend table.
  One curl + one JSON parse replaces three portal visits.

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
- **99acres deep-scrape gives totals only** — `price.displayPrice` (e.g. "₹6.94 - 11.36 Cr") with `area.min/max = null` on **npxid project-brochure pages**. Per-sqft CANNOT be derived from those. BUT the same actor's **npspid listing-level records** (from locality `-ffid` searchUrls with `enableDeepScraping: true`) DO carry price.min/max + area.min/max — psf = price/area is computable (verified 2026-08-11: Sumadhura ₹8,000, Assetz City of Palms ₹9,008, Prestige Crystal Lawns ₹8,494, Secret Lake ₹7,000-7,250, Arvind Orchards ₹12,851). Two data shapes, same actor; check `idType` ("npspid" = listing, "npxid" = brochure). The actor also validates `maxItems ≤ 200` and yields only ~31 records/run (captcha wall) — run multiple targeted searches, don't expect belt-wide coverage in one shot.
- **NDR pricing mandate (2026-08-11): bank figures are FALLBACK ONLY.** The rate-bank reference file is a sanity cross-check, never the primary psf source. Every competitor psf must triangulate from the project's 3-4 most recent individual listings (99acres/MagicBricks/Housing), each with area + total + computed psf + URL + date. See property-rd `references/live-listing-pricing-recipe.md` for the full verify-then-scale recipe.- **Apify preset `magicbricks-99acres` mapper is broken** (`apify_run_actor` fails). Use raw API calls to `api.apify.com/v2/acts/<owner~actor>/runs` with `APIFY_API_KEY` env var.
- **MagicBricks `fascinating_lentil/magicbricks-99acres-property-scraper` is stale** — MagicBricks parser returns 0, 99acres blocked even via residential proxy. Don't rely on it.
- **MagicBricks listing URLs: old format is dead (Aug 2026).** `propertyDetails/property-for-Sale-in-Bangalore&id=<decimal>` and `propertyDetails&id=<decimal>` now 404. Use `propertyDetails/property-for-Sale-in-Bangalore&id=<hex('MB'+decimal)>` — e.g. 84700953 → `https://www.magicbricks.com/propertyDetails/property-for-Sale-in-Bangalore&id=4d423834373030393533`. Convert with `bytes('MB'+str(id),'utf-8').hex()`. Validate listing URLs via web_extract (Tavily) before trusting them in a sheet/KML.
- **Rate pages are JS-heavy but Google-indexed** — the snippet descriptions carry the numbers even when the page itself is 403/406 to us.
- Never fabricate per-sqft. If only totals are available, report totals and say per-sqft is unavailable from that source.
- **Google-native research decks / maps can be download-restricted (403 on export)**: a Drive file whose sharing setting has "Viewer and commenter can see the option to download, print, and copy" OFF returns `403 ... "Export on..."` from `files().export`, and Google-native files (Slides, My Maps) also reject `get_media` ("Only files with binary content can be downloaded. Use Export..."). This is the file owner's sharing setting, NOT an API problem and NOT a broken permission on the VPS. Don't burn time retrying: pivot to `session_search` for the deck's pricing data, or mine live listings straight from the portal (NoBroker `propertyTitle`/`price`/`carpetArea` JSON → psf). Flag to the user that re-enabling download on the deck would unlock its data for reuse.
- Always cross-check at least 2 sources for rate bands; portal averages vary by quarter and by micro-locality.

## References

- `references/devanahalli-per-sqft-curated-aug2026.md` — verified mid-2026 per-sqft rates for ~35 Devanahalli/Nandi Hills projects (new projects, plotted devs, villas, gated, farms, apartments), locality rate bands, and Places-verified coords for the religious POIs (Isha/Sadhguru Sannidhi, Radha Soami Satsang Beas). **Also holds the 03-Aug-2026 area-search additions** (~30 more projects found via the locality-first `-ffid` run — Assetz City of Palms, TE Tangled Up in Green, Prestige Crystal Lawns/Gardenia, Sobha Oakshire, Konig Pearl/North County, Embassy Greenshore/Verde/Edge, Bhartiya Garden Estate, etc., with Places coords). Reuse before re-searching; re-verify for formal documents.
- `references/karnataka-land-price-govt-sources.md` — **per-acre land benchmarks + government sources** (Kaveri 2.0 guidance values, IGR, KIADB acquisition compensation ₹2.70 Cr/acre Jun 2026, findcirclerate.com extraction, market per-acre bands for Nandi Hills/Devanahalli corridor). Use when the user asks for "current land prices from Kaveri/government sources" — complements the per-sqft reference above.
- `references/anekal-attibele-belt-pricing-aug2026.md` — verified Aug-2026 per-sqft rates for the Anekal/Attibele/Bestamanahalli belt (Bangalore South / SH-35 + Hosur Rd corridor): ~40 project prices, locality rate bands, per-acre benchmarks (agri ₹1–2 Cr/acre vs converted ₹13–26 Cr/acre), and the out-of-belt name-collision list (Adarsh Tropica, Birla Tisya, Godrej Ananda Ph2 Bagalur, etc.). Reuse before re-searching this belt.
- `references/sterlitee-regal-park-plotted-pricing-2026-08.md` — 2026-08-26 plotted-development benchmark on the Hosur Rd/Jigani belt: the no-in-project-plots fallback (use own-village + adjacent-locality comps), the NoBroker plot-detail-page plain-requests recipe (plotArea/uploadedBy/dates JSON), MagicBricks plot-id URL encoding + liveness check, and per-project averages (Sterlitee zone ₹5,974, PKC ₹10,998, Guru Ernika ₹3,675, Sobha SBA ₹13,267).
- `references/ranka-project-pricing-rnd-index.md` — **DRA/Ranka first-stop index**: where each Ranka project's curated pricing R&D lives on Drive (Amber map/decks, Oasis Market Research deck + Comp sheet, NorthStar v4 + Jan-2026 sheet, Udaya brochure ID), the video-recorded Whitefield / Yelahanka / Sarjapur–Hosur villa-corridor bands, and the pivot ladder when a deck is export-blocked (403): alternate copies → session_search → NoBroker live-listing JSON psf mining. Reuse before re-searching these projects.
- `references/` under the `location-research` skill — Places API re-verification, 99acres deep-scrape pricing recipe, KML icon inventory, terminal `&`-guard workaround.
