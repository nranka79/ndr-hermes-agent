---
name: real-estate-area-research
description: Competitive-area discovery for Indian real estate land parcels — locality-first area search, Google Maps geocoding, dedupe, radius filter, KML/sheet outputs. Use when the ask is "find additional projects (villa/plot/apartment) in the vicinity of <land parcel>". For EACH competing project found, hand off to the individual-project-research skill (pricing + RERA deep-dive per project). Use headless browsing, not curl.
version: 1.3.0
author: Nishant Ranka (nranka79), Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [real-estate, apify, area-search, geocoding, kml]
    category: domain
    related_skills: [property-rd, real-estate-portal-research, individual-project-research, property-pricing-sources, maps]
---

# Real-Estate Area Research (competitor discovery around a land parcel)

Companion to `real-estate-portal-research` (which covers listing-price
lookups) and `property-rd` (which owns the TOOLS this skill's output feeds
into). This skill covers the **discovery pipeline** used when Nishant
asks to expand competitor coverage around a specific land parcel (e.g.
"re-run the skill looking for additional projects in the vicinity,
collect pricing, add them to the KML and the competitor sheet").

## Two-stage flow (MANDATORY, v1.3.0)

This skill is **stage 1 — area/competitor discovery**. Given a location
(pin, locality, land parcel), it finds every competing project + point of
interest around that location and produces the KML + competitor sheet.
Then, for EACH competing project found, run the **`individual-project-research`**
skill as **stage 2** — the per-project deep-dive that extracts pricing and
RERA details for that specific project. Do NOT stop after the area sweep:
every shortlisted competitor on the sheet must go through
`individual-project-research` for its pricing + RERA deliverables.

- If the user says "research this location / area / vicinity and find the
  competing projects" → run THIS skill (stage 1), then `individual-project-research`
  per competitor (stage 2).
- If the user gives ONE specific project (name/URL) → run
  `individual-project-research` directly.
- Both stages MUST use headless browsing (`browser_navigate` / `smart_browser`,
  real Chromium) or curl-with-full-browser-headers through the residential
  tunnel — NOT bare curl (curl-minimal fingerprints get Akamai/WAF 403s
  from every IP; see real-estate-portal-research pitfalls).

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
9. **Pricing:** Use headless browsing first — `browser_navigate`/`smart_browser`
   (real Chromium, pre-wired to the residential tunnel) on the portal's
   project/listing page, or curl with a FULL browser header set through
   `socks5h://hermes-utilities:1000` (bare `-A` curl 403s — fingerprint, not IP).
   99acres deep-scrape covers ~1/3 of records (`price.displayPrice`); for the
   rest `web_search` "<exact project name> price per sqft" — portal snippet
   pages (99acres/MagicBricks/housiey/proplocators) give psf bands directly.
   Keep the source note per figure (validate snippets against raw context —
   wrong-row locality tables are the biggest trap).
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
12. **Per-project deep-dive handoff (v1.3.0):** for EACH shortlisted
    competitor project on the sheet, run the `individual-project-research`
    skill — extract RERA details + plans and per-project pricing listings,
    and produce that project's info doc + pricing spreadsheet. The area KML
    gives the map; `individual-project-research` gives the per-project
    depth. Use headless browsing there too.

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

## TN RERA registry leg (Tamil Nadu parcels) — v1.2.0

When the user asks for a TN property's full R&D ("go to Tamil Nadu RERA
website, get their details… about 10 projects at least"), pull the official
registry — NOT just portal listings:

1. **Access via the residential tunnel only** — `rera.tn.gov.in` network-blocks
   the VPS datacenter IP (bare curl → HTTP 000). Use `browser_navigate`/
   `smart_browser` (real Chromium, pre-wired to the tunnel), or curl with a
   FULL browser header set through `socks5h://hermes-utilities:1000` (same
   pattern as K-RERA; bare `-A` curl is not enough). The `registered-layout/tn`
   page is ~8.8 MB; `registered-building/tn` ~0.9 MB; default shows current
   year only — add `?_token=x&year=2025` (any token value works) to sweep
   prior years.
2. **Filter by district code = the number after `TN/` in the reg no.**
   Nilgiris = 12, Coimbatore = 11, Chennai = 29, Krishnagiri = 30,
   Chengalpattu = 35. Registration formats vary by vintage (`TN/12/Layout/1858/2025`
   old vs `TNRERA/12/LO/0230/2026` new) — match both. Parse with regex over
   the `<tr>` rows + `html.unescape`; don't need pandas.
3. **Use mirrors for clean detail pages** — `verified.realestate/rera/registered-layouts/<slug>`,
   `aurumproptech.in/pulse/rera/tamil-nadu/<district>/<project>/<id>`,
   `proquiro.com/tools/rera-tamil-nadu/...` carry extent, plot breakdown,
   approvals, project cost, escrow bank, status.
4. **A THIN registry is itself the finding** — Nilgiris has only ~4-5
   district-12 registrations across 2024-2026 (most hill-station projects run
   pre-RERA or on municipality/DTCP approval). State it: a new RERA
   registration is a clean compliance differentiator; verify the existing
   JDA/promoter's RERA status before claiming first-mover.
5. Full recipe + worked Coonoor/Nilgiris result:
   `references/tn-rera-nilgiris-collector.md`.

## Hospitality / OTA leg (hill-station & second-home parcels) — v1.2.0

For Coonoor-class parcels the "social infrastructure" ask means HOTELS and
HOMESTAYS, not just schools/hospitals. When NDR says "categorize the hotels
5-star / 4-star / 3-star, get rates from MakeMyTrip/Airbnb/Booking.com and
Google reviews, restaurants within a 10 km radius":

- **No officially rated 5-star in most hill stations** — name the de-facto
  anchor (Coonoor: Taj's Gateway ~₹17,850/night, 4.5★/1,282 TA reviews) and
  build tiers off OTA positioning: 5★/luxury (₹15k+), 4★/upscale (₹5-15k),
  3★/mid (₹3-6k), homestay/budget (<₹3k). Deliver a category-count table +
  typical rate range + examples.
- **Rates come from OTA snippets, not hotel sites** — KAYAK/HotelsCombined/
  MMT/Expedia/Trip.com search snippets give current nightly rates; official
  sites for whole-villa products (Lohono, amã Stays & Trails, Isprava).
  ALWAYS attach the source URL; mark unconfirmed rates explicitly; note
  point-in-time (OTAs fluctuate daily).
- **Direct villa competitors are the real comp set** for a villa project
  (Lohono/amã/Isprava whole-villa rentals ₹20-50k/night), and "no luxury
  product on/near the subject parcel" is a location-led differentiator.
- **Seasonality matters for feasibility** — KAYAK city pages show the
  peak/low spread (Coonoor Aug ~$35 vs May ~$192 → model 2.5-3×).
- **Restaurants**: Tripadvisor city page (top-N with ratings + review counts)
  + OSM POI belt for the full radius; a project's in-house F&B (five-star
  chefs) is a differentiator vs mostly mid-market standalone restaurants.
- Delegation works: 3 parallel leaf agents (hospitality/OTA, TN RERA,
  for-sale projects) with `['web','search']` toolsets — but the RERA agent
  timed out and the PARENT re-ran that leg directly via tunnel curl (see
  tn-rera-nilgiris-collector.md). Check child tool_traces before trusting.

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

**Child agents may return planning text with an EMPTY tool_trace** (hit
2026-08-12 Hosur run: delegated `['web','search']` children claimed "I'll
research..." but never executed a search — the session's Tavily key was
suffixed `TAVILY_API_KEY_2` so the built-in tool wrapper had nothing to
call). Verify children actually produced results before trusting them; the
robust fallback is for the PARENT to mine snippets itself via the Tavily
direct-API curl recipe (see property-pricing-sources "Tavily Direct-API
Fallback").

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
- **Carve-out: POI/infrastructure KML with NO sheet behind it** (hospitality +
  restaurants for a hill-station/second-home land proposal) IS hand-built. Recipe:
  OSM Overpass `tourism=*` + `amenity=restaurant` bbox query (NOT Nominatim — it
  under-maps hill-station hotels, 1/25 resolved for Coonoor), Haversine ≤10 km,
  merge OTA rates/reviews onto OSM names via a mapping dict (OSM name ≠ marketed
  name: "Taj Garden Retreat" = Gateway Coonoor), researched-but-unpinned props go
  into a "Reference-only" folder — NEVER fake coordinates. **XML escaping kills
  hand-built KMLs**: html.escape() on fields misses raw `&` in the `<description>`
  element ("R&D", "& Dining"); fix with
  `re.sub(r'&(?!(amp|lt|gt|quot|apos|#\d+);)', '&amp;', content)` and always
  validate with `xml.dom.minidom.parse()` before upload. Full worked recipe:
  `references/coonoor-shaanthavana-2026-08.md`.
- Download native KML with `drive.files().get_media(fileId=...)` — the
  Docs-export path fails ("This file cannot be converted").
- Re-upload with `files().update(fileId=...)` (same file id keeps the link).
- Count placemarks from the tool's summary output; spot-check the Drive
  download greps the change.

## Verification

- **Marketing/developer names ≠ portal/RERA names.** "The Roots by SVAM
  Realty" is listed on 99acres/MagicBricks and in the sheet as **"SRK The
  Roots"** (promoter SRK Infra Projects / Svam Realty) — same project.
  When the user asks "did <marketing-name project> come up", search the
  sheet by partial tokens (roots) AND the developer name, and confirm
  against the source URL before concluding it's absent. Offer to add an
  alias note to the sheet row so future dedupe doesn't re-add it.
- New projects are genuinely absent from the sheet (post-suffix-strip dedupe).
- Geocoded placemarks fall within the 10 km radius of the reference pin.
- Every price figure has a source (deep-scrape displayPrice or a web snippet).
- Sheet and KML counts updated; KML re-uploaded to the same Drive file id.
- **Every shortlisted competitor got its `individual-project-research` run**
  (per-project pricing + RERA deliverables), not just an area row on the sheet.
- Data was gathered with headless browsing (browser_navigate/smart_browser or
  full-browser-header curl through the tunnel) — not bare curl (fingerprint 403s).
- **Tunnel-health check uses the RIGHT endpoint.** Verify with a residential-listed
  echo endpoint (`ifconfig.me` → node IP) or the actual portal domain. `httpbin.org/ip`
  and `api.ipify.org` are NOT residential-listed, so they show the VPS IP by design —
  that is expected, not a tunnel failure. Never conclude "routing broken" from a
  non-listed echo endpoint or from a bare-curl 403 (curl fingerprint is blocked from
  every IP).

## Reference

- `references/uganavadi-kannamangala-2026-08.md` — live state of the
  Uganavadi/Kannamangala Palya (Devanahalli taluk, airport corridor) run:
  subject pin 13.220644,77.675830 (KIA ~4.2 km), 70-row sheet
  (1UF4s9UXKM0LFcqJM6EQHn5xlY0EqSArVWpK636IdIew) + KML
  (1mb8txNDtBlc1lZ3lR3-gpfOYPO8UnRdR), rate bands, infra highlights,
  POR project list, and the K-RERA timeout gap. Read before continuing that
  belt.
- References section (existing): `references/devanahalli-thylagere-2026-08.md` — live state of the ongoing
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
- `references/tn-rera-nilgiris-collector.md` — TN RERA registry scraping
  (tunnel access, year filter, district codes, thin-registry finding) + the
  worked Coonoor/Nilgiris registrations. Read before any Tamil Nadu land
  proposal R&D.
- `references/coonoor-shaanthavana-2026-08.md` — live state of the Coonoor
  ("Kunur") Shaanthavana parcel: 30% LO JV (≠ Bangalore 25%), Kelsa lead
  #54688453 + Drive links, hospitality/restaurant/TNRERA findings, and the
  hand-built POI KML recipe (OSM Overpass → OTA merge → XML-escape → validate).
