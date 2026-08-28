---
name: location-research
description: "NDR's fixed location research pipeline: given a project name, Google Maps place, or lat-long, resolve the locality, find alias names + nearby localities, enumerate real-estate/infra projects, geocode each project, pull recent (30/60/90-day) listing prices from property portals, compute median capital value ₹/sqft, store results in the local research DB, and reuse cached research when it exists. Trigger phrases: 'research <location>', 'do the location research', 'run the pipeline for', 'analyse the area around'."
version: 1.0.0
author: NDR + Hermes
license: MIT
metadata:
  hermes:
    tags: [research, real-estate, property, locality, pricing, listings, bangalore, chennai, portal-scraping]
    related_skills: [maps, bengaluru-town-planning, property-legal-analysis, research-web-tools]
---

# Location Research Pipeline (NDR)

Fixed, repeatable research workflow for any location/project. Always run the
steps in order. Every run MUST end with results stored in the local DB and a
cached entry recorded — the cache check (Step 1) is what makes repeat
requests cheap.

## Local Research DB Layout

Root: `~/.hermes/research/` — resolve `~` via `$HOME` (NDR's session home; do not hardcode a path).

- `~/.hermes/research/index.json` — master index of every researched location.
  Entry shape:
  ```json
  {
    "slug": "devanahalli",
    "query": "as given by user",
    "resolved": "Primary locality name",
    "aliases": ["alt name 1", "nearby 1", "nearby 2"],
    "created": "YYYY-MM-DD",
    "updated": "YYYY-MM-DD",
    "project_count": 12,
    "median_cap_per_sqft": 4800,
    "files": {
      "report": "reports/devanahalli.md",
      "data": "data/devanahalli.json"
    }
  }
  ```
- `~/.hermes/research/reports/<slug>.md` — human-readable markdown report.
- `~/.hermes/research/data/<slug>.json` — full structured dataset.

If `~/.hermes/research/` does not exist, create it on first run (Step 1
handles this).

## R&D Sheet Classification Convention (NDR, Aug 2026)

When building or auditing a competitor/POI R&D sheet for a project, NDR's rule
is strict — get it right the first time:

- **Competitor sheet (first tab) = everything sellable as real estate.** All
  plots, villas, villa plots, gated communities, plotted developments,
  residential plots, farm land for sale, apartments, and "new projects"
  (99acres category `new_projects_Devanahalli` etc.) belong here — even small
  one-off villas or single apartment buildings. Categories that MOVE:
  `villa_projects`, `gated_community`, `new_projects_*`, `farm_land_for_sale`,
  `plotted_development`, `apartments`, `residential_plots`.
- **POI sheet (second tab) = infrastructure and amenities only.** IT
  companies, industries, industrial areas, colleges, schools, hospitals,
  hotels, and religious/spiritual places (ashrams, foundations, satsang
  centres). Categories that STAY: `IT_companies`, `colleges`, `schools`,
  `hospital`, `hotels`, `industrial_area`, `religious`.
- **Religious places are POI, not competitors** — e.g. Sadhguru Sannidhi /
  Isha Foundation (Chikkaballapura, 13.486649, 77.706878) and Radha Soami
  Satsang Beas (Devanahalli, 13.338646, 77.719630). When NDR names one, add it
  to the POI tab with category `religious`.
- NDR has explicitly corrected this once; treat it as a standing convention,
  not a per-session preference. When in doubt, ask "sellable project or
  infrastructure?" — projects are competitors, everything else is POI.
- **GPS pins are QA-critical (NDR correction 2026-08-20).** NDR reviews
  every KML pin and will flag even one wrong pin ("all these GPS pins seem
  completely off"). Before delivering a competitor map, re-verify each pin
  resolves to the EXPECTED locality (not just "a name matched"): confirm
  each project's locality on the Maps place page, and sanity-check the two
  leading decimal digits of lon (a Sarjapur project must be ~77.7x-77.8x, not
  77.5x). Do not ship 2-decimal-place rounded pins as placeholders — they
  drift kilometres and NDR notices. Prefer ≥6-decimal exact place-page coords.

## Per-Sqft Pricing Is Mandatory, Totals Are Not Enough

NDR's standing requirement: per-sqft (₹/sqft) rates must be collected and
updated **for every project** in the Competitor sheet. Total-price ranges from
99acres deep-scrape are NOT sufficient — do not stop at `displayPrice` totals.

- The 99acres deep-scraper (`codingfrontend/99acres-projects-search-scraper`)
  returns `price.displayPrice` totals (e.g. "Rs 6.94 - 11.36 Cr") with
  `area.min/max = null` — per-sqft CANNOT be derived from it.
- Real path: **per-project web_search snippets** — search `"<project>"
  Devanahalli price per sqft`, then extract the rate from result descriptions
  (portals index their rate pages; the VPS gets 403/406 on direct fetch).
  Worked for ~33/53 moved projects in the Aug 2026 run.
- Fill the Competitor tab's "Current Price (per sq.ft)" column (col D) with
  the extracted rate; leave honest blanks for projects with no indexed rate.
- Locality-band pages (99acres/MagicBricks/Housing `price-trends` pages) are a
  fallback for overall context (Devanahalli mid-2026: apartments
  ₹6,500–11,550/sqft, plots ₹3,350–9,550/sqft) but are not per-project rates.

## Step 1 — Cache Check (always first)

1. Read `~/.hermes/research/index.json`.
2. Match the user's input (project name, place name, or lat-long) against
   `resolved`, `aliases`, and `slug`. Use fuzzy/phonetic matching — NDR often
   says names slightly differently each time (e.g. "Katenahalli" vs
   "Katnalli", "Dunnasandra" vs "Dunnasandra Cross").
3. If a match exists AND `updated` is within **90 days** of today:
   - Reply immediately with the cached report summary + point to files.
   - Do NOT run the pipeline. Report "using cached research from <date>".
4. If match is older than 90 days: flag it as stale, then re-run the full
   pipeline and overwrite.
5. If no match: proceed to Step 2.

## Step 2 — Resolve the Location

Input may be: project name, Google Maps place name, or lat-long.

- If lat-long: reverse-geocode via OSM Nominatim
  (`https://nominatim.openstreetmap.org/reverse?lat=..&lon=..&format=json`)
  to get locality + sub-locality. Use the `maps` skill for OSM helpers.
- If project name: web_search `<project> <city>` first to find the project's
  locality, then confirm on Google Maps.
- If place name: confirm on Google Maps which locality/sub-locality it maps
  to.

Output: `primary_locality`, `city`, `state`, `lat`, `long`.

## Step 3 — Alias & Vicinity Discovery

For `primary_locality`, discover:
1. **Alternate names** the locality is known by (old name, regional name,
   transliteration variants) — web_search `<locality> also known as OR called OR formerly`.
2. **Nearby/vicinity localities** — search property portals' suggestion
   endpoints and "similar localities":
   - 99acres: `https://www.99acres.com/api/property/suggest/<locality>` (or
     the search-suggest endpoint; fall back to their search page HTML).
   - MagicBricks: `https://www.magicbricks.com/search/_searchSuggest/_mapping_new/<locality>`
   - Housing.com: search page suggest API.
   - Plus web_search `<locality> nearby localities OR areas OR neighbourhoods`.
3. Keep at most **10 nearby localities** that are genuinely adjacent (check
   distance via OSM; skip anything > ~10 km unless it's the same micro-market).

Output: `aliases` (2–5 names) and `vicinity` (up to 10 locality names).

## Step 4 — Project Enumeration

For `primary_locality` AND each vicinity locality:

- web_search `<locality> residential projects`
- web_search `<locality> commercial projects`
- web_search `<locality> new launches 2026` / `<locality> upcoming projects`
- web_search `<locality> infrastructure development OR metro OR ring road OR flyover`
- Check 99acres/MagicBricks project listing pages for the locality.

Collect every distinct project/announcement. For infrastructure items (metro
stations, roads, flyovers, industrial corridors), record as
`infrastructure_events` (name, type, status if known). For property
projects: `name`, `builder`, `type` (residential/commercial/mixed),
`status` (under-construction/ready-to-move/new-launch). For METRO-specific questions (which line serves X, proposed corridors,
station lists, maps/KML), load the `research-web-tools` skill references
instead — `references/bangalore-metro-network.md` (Namma Metro: all 8 lines,
Red Line 3A, Yellow/Attibele ext, 72 km corridor) and
`references/bangalore-suburban-rail-bsrp.md` (K-RIDE suburban rail,
doubling projects, RLDA, Drive KML pack location). The combined urban rail
KML pack lives at Drive R&D > Bangalore > Metro.

## Step 5 — Geocode Each Project

For each property project:
1. Try RERA first: web_search `<project> <builder> RERA` — the RERA site
   (karnataka rera / tn rera) often lists exact location; use
   `web_extract` on the RERA page.
2. Fallback: Google Maps search `<project> <locality>` — extract lat-long
   from the maps URL. Use the Playwright headless technique in
   `references/google-maps-coordinate-resolution.md` — it is the proven path
   when `web_extract`/plain requests get bot-walled. Private gated
   communities are often MISSING from OSM/Nominatim, so Google Maps (not
   Nominatim) is the primary resolver for competitor projects.
3. Fallback: OSM Nominatim search.

Record `lat`, `long` for every project. If a project cannot be geocoded,
mark `geocoded: false` and keep going — do not block the pipeline.

**PITFALL — locality-comparison projects can pin to a DIFFERENT micro-market
(hit 2026-08-20, MJR Divine Meadows / Sarjapur run).** Projects that come from
a portal's *project-vs-locality rate-trend comparison table* (MagicBricks
shows unrelated projects beside the target locality whose prices you're
comparing) are NOT necessarily located in that locality. Google Maps
resolved two such projects — "Birla Ojasvi" (→ RR Nagar / West BLR, lon
77.505) and "Gopalan Florenza" (→ Hosur Rd / Electronic City, lon 77.593) —
to totally different corners of the city than the Sarjapur subject, no
matter how many locality-qualified query variants I tried. This is NOT a
geocoder failure: the projects genuinely live elsewhere and don't belong in
the competitor set. **Rule:** before adding a pinned project to a competitor
KML/sheet, confirm it came from *actual listings in that micro-market*, not
from a locality rate-trend comparator. When the pin is stale (an NDR keyword
for "the pin looks wrong-fat"), verify the reliability of the batch lookups.

**Shortlink resolution:** when the user shares a Google Maps shortlink
(`maps.app.goo.gl/...`), follow it with `curl -sL` to get the redirect URL,
then open that URL in the headless browser and read `@lat,lon` from the
final URL bar — the shortlink redirect often omits coordinates.

**`share.google/<code>` is often a builder MARKETING link, not a GPS pin
(hit 2026-08-20, MJR Divine Meadows run).** When the user shares a bare
`https://share.google/<code>` for a project, it frequently redirects to the
developer's official project website (a Google-Ads / digital-marketing
tracking URL with `gclid`, not a map pin) — it gives the PROJECT, not the
coordinates. Do NOT stop at the redirect. Separately resolve the real pin on
Google Maps (`browser_navigate` to
`google.com/maps/search/<project>+<locality>`, then read `@lat,lon` from the
final page URL). For a project whose RERA/address carries a locality, confirm
the Plus code and address on the Maps place page too.

**KML/MyMaps output:** when NDR asks for a KML of competitor projects, see
`references/google-maps-coordinate-resolution.md` for the verified KML icon
URLs (villa = house, plot = flag), the label convention (name + ₹/sqft), and
the ASCII-only + XML-escape delivery rules.

**Batch geocode at 100+ POI scale:** when geocoding a large POI set, see
`references/places-api-reverification-and-99acres-pricing.md` for the
systematic −0.002575° lon shift pitfall (headless-browser viewport-center
vs pin), the Google Places API re-verification recipe (Apify
`compass/crawler-google-places`, lowercase `countryCode`, title-similarity +
bounding-box hygiene), the working 99acres deep-scrape pricing path
(`codingfrontend/99acres-projects-search-scraper` with `-ffid` URLs; use
`deepScraping: true` — the `false` output is search-result junk incl.
wrong-city projects; some projects have NO price even deep-scraped; area
fields are null so labels carry total-price ranges not ₹/sqft), the
projectId-keyed merge/dedupe pattern, the explicit ALIASES name-matching
map for attaching prices to sheet rows, the terminal `&`-guard workaround
(write scripts via write_file, don't heredoc them), and the vision-verified
icon inventory.

## Step 6 — Listings & Pricing (30/60/90-day)

For each geocoded property project, pull recent listings:

1. web_search `<project> <locality> <city> price OR rate OR "per sqft" listing`.
2. Portal listing pages to check (use web_extract; where the portal blocks,
   try the browser tool):
   - MagicBricks — `<project>` project page → price trends + listings.
   - 99acres — `<project>` project page → listings.
   - Housing.com — `<project>` project page.
   - NoBroker — owner listings for `<project>` / `<locality>`.
3. For each listing found, record: `date` (approx), `price_cr` or
   `price_lakh`, `area_sqft`, `rate_per_sqft` (computed),
   `resale_or_primary` if determinable.
4. Prefer listings from the last **90 days** (best: 30 days). Record the
   `listing_age_days` per row. Drop anything older than ~1 year unless it's
   the only data point (flag it as `stale_benchmark: true`).

## Step 7 — Median Analysis

1. Collect all `rate_per_sqft` values for the locality (across all projects
   and all listings).
2. Compute: **median**, min, max, and the spread (max−min).
3. If there are ≥ 5 listings, report median as the headline number. If fewer,
   say so explicitly ("only N listings — median is indicative").
4. Also compute per-project median if a project has ≥ 3 listings.
5. Note outliers (e.g. a 2x listing price) but don't silently drop them —
   list them as outliers.

Output: `median_cap_per_sqft`, `min_cap_per_sqft`, `max_cap_per_sqft`,
`listing_count`, `sample_date`.

## Step 8 — Store & Report

1. Create/update `~/.hermes/research/data/<slug>.json` with the full
   structured dataset (all steps' outputs, ISO dates).
2. Write `~/.hermes/research/reports/<slug>.md` — a clean markdown report:
   - Location resolved + aliases + vicinity
   - Project list w/ type, status, lat-long, geocoded flag
   - Infrastructure events
   - Listing summary table (project | listings | range | median ₹/sqft)
   - Headline median + caveats + timestamp
3. Update `~/.hermes/research/index.json` (create if absent) with the entry.
4. Report to NDR: headline median ₹/sqft, number of projects, listing
   sample size, staleness caveats, and the file paths.

## Pitfalls

- **Portals block scraping.** 99acres/MagicBricks aggressively block plain
  HTTP fetches. If `web_extract` returns a bot-wall, use the browser tool;
  if that also fails, fall back to `web_search` snippets and site: queries
  and say clearly that portal pages were not directly readable.
- **Suggestion endpoints drift.** The exact suggest API paths change; always
  verify the response is JSON/HTML containing locality names before trusting
  it. A 200 with an error page is still a failure.
- **Listing age is fuzzy.** Most portals don't show exact dates on listings.
  Use search result dates and page markers (e.g. "listed X days ago") and
  record them as approximations.
- **Don't cross the road.** Nearby localities must be genuinely adjacent.
  `Varthur` and `Whitefield` are a micro-market; `Varthur` and `Devanahalli`
  are not — skip anything >10 km unless the user asked for the broader belt.
- **Cache freshness is 90 days.** Real-estate pricing moves; anything older
  is reported as stale and re-run.
- **Phonetic matching is mandatory** for cache lookups — STT voice queries
  garble place names (Katnalli/Katenahalli, Dunnasandra/Dunnasandra Cross).
- **Never fabricate listing data.** If a portal gave nothing, say so. A
  report with 2 real listings beats 20 invented ones — the median is only as
  honest as the sample.
- **KML must be ASCII-only AND XML-escaped before delivery.** Two failure
  modes hit in practice: (1) raw `&` in placemark names (R&D, "& Spa", "&
  Technology") makes Google Earth reject with "not well-formed (invalid
  token)"; (2) after fixing the `&`, the SAME error persists when names still
  contain non-ASCII — em dashes, curly quotes, or emoji appended to scraped
  labels (🦅 Prestige Golfshire, Ajmal Flora 🖼️, Brigade Atmosphere 🏞️).
  Google's importer is stricter than ElementTree. Fix: escape `&`/`<`/`>` AND
  strip/replace every non-ASCII char during generation (em dash → hyphen,
  ₹ → Rs., emoji → drop); validate with ElementTree AND minidom; verify the
  file is all-ASCII (`all(b < 128 for b in open(f,'rb').read())`) before
  upload. If a Drive copy was already shared, re-upload to the SAME file ID
  so the link keeps working. Full recipe in
  `references/google-maps-coordinate-resolution.md`.

## Related Skills

- `maps` — OSM geocoding/reverse-geocoding helpers (Nominatim, OSRM).
- `bengaluru-town-planning` — zoning/regulatory context for BLR locations.
- `property-legal-analysis` — when the user moves from market research to a
  specific plot/deed.
