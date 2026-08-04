---
name: real-estate-area-research
description: Competitive-area discovery for Indian real estate land parcels — locality-first area search, Google Maps geocoding, dedupe, radius filter, KML/sheet outputs. Use when the ask is "find additional projects (villa/plot/apartment) in the vicinity of <land parcel>".
version: 1.1.0
author: Nishant Ranka (nranka79), Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [real-estate, apify, area-search, geocoding, kml]
    category: domain
    related_skills: [property-rd, real-estate-portal-research, property-pricing-sources, maps]
---

# Real-Estate Area Research (competitor discovery around a land parcel)

Companion to `real-estate-portal-research` (which covers listing-price
lookups) and `property-rd` (which owns the TOOLS this skill's output feeds
into). This skill covers the **discovery pipeline** used when Nishant
asks to expand competitor coverage around a specific land parcel (e.g.
"re-run the skill looking for additional projects in the vicinity,
collect pricing, add them to the KML and the competitor sheet").

## Tool-first execution (MANDATORY, v1.1.0)

Discovery is LLM-driven, but every WRITE and every artifact goes through
the `property-rd` scripts — never hand-edit the sheet from chat, never
hand-write KML/XML:

1. LLM collects candidates + pricing + coords → writes `rows_to_add.json`
   and `listings.json` (schemas in property-rd SKILL.md).
2. `python3 <property-rd>/scripts/sheet_io.py append <sheet_id> Competitors rows_to_add.json`
   (and `Listings & Sources` with listings.json rows).
3. `python3 <property-rd>/scripts/kml_generator.py --sheet <sheet_id> --subject-name ... --subject-lat ... --subject-lon ... --drive-file-id <id>`
   — KML comes FROM the sheet: labels `Name | Rs X/sqft`, icons per type,
   description carries every detail + the pricing source URL(s).
4. Gap-check with `radius_query.py` (5/10 km) — catches projects a
   name-driven run misses (Sammy's Palm Hills class of gap).

## Trigger conditions

- "find additional projects / villas / plots / apartments in the vicinity"
- "expand competitor coverage around <project/land parcel>"
- "add <project> to the KML and the competitor sheet"
- "area search" for a specific locality (Devanahalli, IVC Road, Sadahalli…)

## Pipeline

0. **Pin → address entry point (v1.1.0).** The run can start from a GPS pin
   (lat/lon or a dropped Google pin). Reverse-geocode it first (`maps` skill
   Nominatim reverse, or the Places crawler anchored at the pin) to get the
   locality/address; the locality drives every search string below, the pin
   stays the radius reference.
1. **Load the sources-of-truth registry (v1.1.0).** Read
   `property-rd/references/sources-registry.md` — the growing KB of known
   portals, Reddit groups, Facebook groups, Insta handles, forums. The
   discovery legs below start from it; any NEW source found (a portal, a
   group, a handle that yielded listings) is appended back to it.
2. **Locality-first area search (NOT project-keyed, NOT city-wide).**
   City-wide MagicBricks runs return scattered metro listings and MISS
   projects that don't rank city-wide. Use the 99acres-projects-search-scraper
   with locality search strings (`residential land in devanahalli bangalore
   north`, `villas in devanahalli`, `plots in sadahalli`) or locality URLs
   (`https://www.99acres.com/residential-land-in-devanahalli-bangalore-north-ffid`).
3. **Google-search + social/community leg (v1.1.0).** In parallel with the
   portal leg: `web_search` for the locality (identify MORE portals, direct
   listings, Insta ads, FB group posts — e.g. `site:instagram.com <locality>
   realestate`, `site:facebook.com/groups <locality> property`,
   `site:reddit.com <locality> property`), then run the community sources
   from the registry (Reddit subs, FB groups, forums, Insta handles).
   FB/Insta are login-walled: snippets for discovery, `browser_use_cloud`
   for a public group page. Record new sources in the registry.
4. **Dedupe after stripping locality suffixes.** Normalize names (lowercase,
   strip non-alphanumerics) AND strip locality tokens (`devanahalli`,
   `bangalore north`, `sadahalli`, `ivc road`) before comparing against the
   competitor sheet — naive dedupe conflates in-result duplicates with sheet
   duplicates. (`sheet_io.key_name` implements this.)
5. **Classify vicinity by URL locality tokens, not "bangalore-north".**
   - FAR tokens override: `bangalore-south`, `hosur`, `kumbalgodu`,
     `singasandra`, `banashankari`, `yadavanahalli`, `bidarahalli`,
     `handenahalli`, `ambedkar`, `hebbal`, `yelahanka`, `vijayapura`,
     `palanahalli`, `bangalore-east`.
   - A URL can say `-bangalore-north-` yet be 15-20 km away (Adarsh Savana
     Yelahanka, Vario Homes Hebbal). FAR token wins.
   - NEAR requires a Devanahalli-belt token: `devanahalli`, `sadahalli`,
     `singarahalli`, `kamenahalli`, `ivc`, `hosahudya`, `neraganahalli`,
     `thylagere`, `bidaganahalli`, `beedaganahalli`, `nandi`, `msr-city`.
6. **Expansion loop — harvest suggested projects (v1.1.0).** For EVERY
   project on the list, run one direct search (99acres project page +
   `web_search`). Portals return "similar projects" alongside — take those
   suggested names, dedupe against the sheet, append the unknown ones to the
   frontier, and continue the cycle until the frontier empties or the sheet
   crosses **~100 projects** for this point of interest. (Visited set;
   per-project direct searches also serve pricing, next step.)
7. **Geocode candidates** with the Apify Google Maps Places crawler — see
   pitfalls below (anchor is MANDATORY). Prefer extracting coords from any
   Google Maps link on the project's own page first:
   `python3 <property-rd>/scripts/coords_from_urls.py links.json` (handles
   `@lat,lon`, `q=lat,lon`, `!3d!4d`, short `maps.app.goo.gl` links).
8. **Radius filter:** Haversine ≤ 10 km from the reference pin
   (Thylagere subject land = 13.3216384, 77.6789048). Geocoded projects
   > 10 km drop; no-coords projects still go to the sheet but not the KML.
   (`radius_query.py` automates the scan + 5/10 km counts.)
9. **Pricing:** 99acres deep-scrape covers ~1/3 of records
   (`price.displayPrice`); for the rest `web_search` "<exact project name>
   price per sqft" — portal snippet pages (99acres/MagicBricks/housiey/
   proplocators) give psf bands directly. Keep the source note per figure
   (validate snippets against raw context — wrong-row locality tables are
   the biggest trap).
10. **Infrastructure pipeline (v1.1.0).** For the same pin + radius, run a
    separate infra sweep: OSM/Overpass via the `maps` skill (hospitals,
    schools, colleges, industries, warehousing, tech parks — 46 POI
    categories), SEZ from the official notified list (sezindia.gov.in PDF),
    `web_search` for malls / temples / ashrams (under-indexed in OSM).
    Write rows to the `POIs & Infrastructure` tab; the same kml_generator
    run includes them with their icons.
11. **Outputs (tool-only, v1.1.0):** append rows to the Competitors /
    Listings & Sources / POIs tabs via `sheet_io.py append`; generate +
    upload the KML with `kml_generator.py` (same Drive file id).

## Apify direct-API drive (when the `apify_run_actor` wrapper returns empty)

- Base `https://api.apify.com/v2`, header `Authorization: Bearer $APIFY_API_KEY`.
- Launch async: `POST /v2/acts/{actorId}/runs` with JSON body → `data.id`,
  `data.defaultDatasetId`.
- Poll `GET /v2/actor-runs/{runId}` until SUCCEEDED (sleep 60-90s; a 40+
  search Places run takes ~5 min).
- Fetch items: `GET /v2/datasets/{datasetId}/items?format=json&clean=true&limit=200`.
- Sync-run caveat: `run-sync-get-dataset-items?timeout=1200` gets killed at the
  terminal's 180s foreground timeout while the server keeps going — prefer
  async + poll.
- Known actor IDs: Google Places crawler `nwua9Gu5YrADL7ZDj` (username
  `compass`); 99acres projects search `hHadmAwXCpNrsHH2O` (username
  `codingfrontend`). Confirm via `GET /v2/actor-runs/{runId}` → `data.actId`.
- **Apify FREE-plan credit wall (hit live Aug 2026).** Paid actors need a
  ~$0.50 minimum launch reserve; below it every launch fails with
  `not-enough-usage-to-run-paid-actor`. The shared account drains FAST —
  one 99acres run spent ~$0.73, and a concurrent Places run then died
  with $0.347 left (0 results, all 8 follow-up launches rejected). Before
  a big run: `curl -s "https://api.apify.com/v2/users/me?token=$APIFY_API_KEY"`
  → `plan: FREE` means metered. When the wall hits, pivot geocoding to the
  Playwright headless batch (`maps` skill `geocode_batch_subproc.py`) —
  zero Apify credits, resolved 114/115 in the same run.

## Google Maps Places crawler — pitfalls (all hit live Aug 2026)

- **MANDATORY location anchor.** Without `locationQuery` (or `@lat,lon` in
  startUrls) the crawler searches the WRONG CITY — one batch wandered to
  Kolkata (22.9, 88.3). Always set
  `"locationQuery": "<town>, <state>, India"` + `"countryCode": "in"`.
- **Anchor boundary SIZE is the trap (hit live Aug 2026 on the Anekal
  belt).** Anchoring at the small town itself (`"Anekal, Karnataka, India"`)
  Nominatim-geocodes to the ~1 km town boundary (zoom 18) and the actor
  filters EVERY real project as `outOfLocation` → 0 scraped. Anchoring at
  the big city (`"Bengaluru"` + `searchMatching: all`) returns plenty but
  Google ranks central-Bangalore results first — observed 79 places ALL
  16–41 km from the target. Working combo: CITY-level anchor +
  `searchMatching: all` + post-hoc Haversine radius filter in your own
  cleanup. Town anchors are silent zero-result traps.
- **Use `searchStringsArray` + `locationQuery`, NOT plain `startUrls`
  strings** — the actor rejects plain string startUrls ("do not contain
  valid URLs").
- Working input:
  ```json
  {
    "searchStringsArray": ["Konig Pearl County Sadahalli", "The Secret Lake Devanahalli"],
    "locationQuery": "Devanahalli, Karnataka, India",
    "maxCrawledPlacesPerSearch": 1,
    "language": "en",
    "countryCode": "in",
    "searchMatching": "all",
    "scrapePlaceDetailPage": false,
    "includeWebResults": false,
    "maxReviews": 0
  }
  ```
- **Coordinates live in `location.lat` / `location.lng`**, not top-level
  `latitude`/`longitude`.
- **Result titles ≠ project names** ("Total Environment Tangled Up In The
  Green", "Riviera Sky Villas - Goyal co | Hariyana Group"). Match candidates
  with token-overlap fuzzy logic (≥2 shared tokens or substring both ways
  after normalization), never exact equality.
- Cost ~$0.004 per place; `maxCrawledPlacesPerSearch: 1` keeps it cheap.
- Some searches return 0 places (pre-launch projects with no Maps pin) —
  normal, don't rerun; project still goes in the sheet without coords.

## Headless Google-Maps geocoder (fallback when Apify Places is blocked/broke)

`maps` skill `geocode_batch_subproc.py` + `geocode_one.py` — crash-resilient
subprocess-per-name batch, works with zero Apify credits. Two hard lessons
from the Aug-2026 Anekal belt run:

- **The fallback locality is baked into `geocode_one.py` and defaults to
  Devanahalli.** Unresolved queries fall back to `"<name> Devanahalli"`
  and resolve to WRONG pins when you're researching another belt (e.g.
  "Bestamanahalli gated plots" resolved 48 km away near Devanahalli).
  Fix: pass the target locality as argv[3] to the batch:
  `geocode_batch_subproc.py names.json out.json Anekal` (scripts already
  accept it — default stays Devanahalli for the Thylagere belt).
- **Locality-qualified query beats bare name + " Bangalore".** `"<project>
  Bangalore"` frequently resolves to a SAME-NAMED project elsewhere in the
  city (Green Avenue → 27 km off, Godrej Ananda → Bagalur). Build the query
  as `"<project> <known locality>"` (Anekal / Attibele / Chandapura /
  Electronic City). Also filter far-out pins: resolve 15+ km rows with a
  locality-qualified retry before trusting them.
- Output file is keyed by the QUERY string (not the orig name) with `lon`
  (not `lng`). When merging multiple batches, later locality-qualified
  results must win over earlier "Bangalore" results — iterate the
  query→orig map in reverse so the fix batch overrides.

## Multi-agent execution (≥100-point R&D runs, proven Aug 2026)

For a full belt R&D the user asked to run as a "detailed multi-agent
exercise", delegate 3 parallel leaf agents (toolsets: terminal/file/web),
then merge centrally:

1. **Portal scrape agent** (terminal+file): drive the 99acres
   projects-search actor via direct API with locality-first searchUrls;
   save raw + deduped JSON.
2. **Places/discovery agent** (terminal+file): crawler-google-places with
   the city-level anchor + locality search strings; save cleaned JSON with
   `location.lat/lng`.
3. **Pricing agent** (web+file): per-project `web_search` snippet mining;
   writes a markdown brief (project | type | price | per-sqft | source |
   confidence).

Then the parent: merge+dedupe (strip locality suffixes — `sheet_io.key_name`),
geocode stragglers with the Playwright batch (locality-qualified queries) or
`coords_from_urls.py` (map links on project pages), radius filter with
`radius_query.py`, write rows via `sheet_io.py append`, build the sheet +
KML with `kml_generator.py` (from the sheet). Watch for: a scrape agent can
time out while its Apify run keeps going server-side — poll the run's dataset
yourself and fetch `99acres_raw.json` after the agent dies; one agent
draining shared Apify credits blocks the other's launches mid-flight.

## Deliverables convention (NDR, Aug 2026)

- Google Sheet on Drive TMP folder (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`),
  ≥100 rows: # | Project | Type | Locality | Listing Price | Per Sqft |
  Lat | Lng | Dist km | Maps link | Source URL | Confidence. Bold header +
  frozen row 1. Rows land via `sheet_io.py append` (Competitors / Listings &
  Sources / POIs & Infrastructure tabs).
- KML via `kml_generator.py` (NOT hand-built): labels `Name | Rs X/sqft`,
  icons per the approved map (apartment=blue pin, villa=realestate signpost,
  plot=green pin, subject=star, infra categories per kml-icons.md),
  descriptions carry every detail + the pricing source URL(s), ASCII-only +
  XML-escaped + minidom-validated; upload to TMP folder with
  `files().update()` on the SAME file id, share as viewer.
- Post BOTH links as a Kelsa lead note addressed to the assigned user
  (Prakash), with headline rate bands + caveats (prices are asking not
  transactions; flag 20+ km rows as verify).

## KML output (native Drive KML — via kml_generator.py)

- The KML is generated FROM the sheet by `property-rd/scripts/kml_generator.py`
  — after any sheet edit, re-run the tool, never hand-edit KML.
- Download native KML with `drive.files().get_media(fileId=...)` — the
  Docs-export path fails ("This file cannot be converted").
- Re-upload with `files().update(fileId=...)` (same file id keeps the link).
- Count placemarks from the tool's summary output; spot-check the Drive
  download greps the change.

## Verification

- New projects are genuinely absent from the sheet (post-suffix-strip dedupe).
- Geocoded placemarks fall within the 10 km radius of the reference pin.
- Every price figure has a source (deep-scrape displayPrice or a web snippet).
- Sheet and KML counts updated; KML re-uploaded to the same Drive file id.

## Reference

- `references/devanahalli-thylagere-2026-08.md` — live state of the ongoing
  Devanahalli/Thylagere competitor expansion: sheet/KML ids, reference pin,
  the 43 prepared rows (14 geocoded + 29 sheet-only) with researched pricing,
  the excluded FAR list, and the quirks hit on the Aug 2026 run. Read this
  before continuing that project.
- `references/bestamanahalli-anekal-2026-08.md` — live state of the Anekal/
  Attibele/SH-35 belt run: subject pin + deal context (Sanchaya Lands),
  deliverables links (115-row sheet + KML), what worked/broke, and the
  open Verify items. Read this before continuing that project.
- Pricing bank for this belt: `property-pricing-sources` →
  `references/anekal-attibele-belt-pricing-aug2026.md`.
