---
name: property-rd
description: "Tool-first competitor R&D for Indian real estate — from a GPS pin, discover competing projects + infrastructure within 10 km, price them, and produce the R&D sheet + KML via scripts. The LLM extracts data; sheet_io/radius_query/kml_generator/pricing_refresh do the writes and the KML. Comp discovery is now K-RERA-primary (karnataka-rera-collector). Companion: real-estate-area-research (discovery), real-estate-portal-research (pricing listings), property-pricing-sources (rate bands)."
version: 1.1.0
author: Nishant Ranka (nranka79), Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [real-estate, rd, kml, sheets, pricing, competitors, infrastructure]
    category: productivity
    related_skills: [karnataka-rera-collector, real-estate-area-research, real-estate-portal-research, property-pricing-sources, maps]
---

# Property R&D Skill (tool-first)

End-to-end competitive R&D for a land parcel / project / locality: given a
GPS pin (or dropped map pin), discover the competing projects in the area,
harvest suggested projects until the list crosses ~100, price each from the
latest listings, gather infrastructure, and produce (1) the R&D Google
Sheet and (2) a KML map where the label carries the per-sqft rate, the icon
reflects the project type, and every placemark description carries all
project details plus the source link(s) the rate was computed from.

## Architecture — MANDATORY: the tools do the real work

The LLM **orchestrates and extracts** (web_search, apify actors, browser,
firecrawl). Every *write* and every *derived artifact* goes through the
scripts under `scripts/`. Never hand-write KML or XML; never hand-edit the
sheet via chat.

| Step | Tool (script) | What it does |
|---|---|---|
| Sheet reads | `python3 scripts/sheet_io.py read <id> --tab <t>` | tab -> JSON records |
| Sheet writes | `python3 scripts/sheet_io.py append <id> <tab> rows.json` | append rows (competitors / listings / POIs) |
| Radius scan | `python3 scripts/radius_query.py --sheet <id> --lat .. --lon ..` | T1: everything within 5/10 km, by coords |
| KML | `python3 scripts/kml_generator.py --sheet <id> --subject-name .. --subject-lat .. --subject-lon ..` | T2: sheet -> KML (labels, icons, descriptions w/ source links) |
| Pricing refresh | `python3 scripts/pricing_refresh.py --sheet <id> --listings listings.json` | T3: outlier rules, sheet+audit updates |
| Map-link coords | `python3 scripts/coords_from_urls.py links.json` | extract lat/lon from Google Maps links on project sites |

Auth: scripts default to `service_name=google-draas` via the gws-vault; if a
session 403s, re-run with `--email ndr@draas.com` (vault-client fallback).
Identity always comes from the session — never pass a user id.

## When to Use

- "R&D on <GPS pin / Google pin / land parcel> — competing projects, pricing, KML"
- "Find villas/plots/apartments near <locality> and build the competitor sheet + map"
- "Infrastructure near <pin>: hospitals, schools, colleges, industries, warehousing, tech parks, SEZ, malls, temples"
- "Refresh pricing for the <belt> competitor sheet"
- "Add <new project> to the R&D sheet + KML"

## Pipeline

### 0. Pin -> address (GPS entry point)

Given a GPS pin (lat/lon or a dropped Google pin):
1. Reverse-geocode to a locality/address — `maps` skill geocode tool
   (Nominatim reverse), or the Places crawler with the pin as anchor.
2. The locality name drives every search string below. Keep the exact pin
   as the radius reference.

### 1. Load the sources-of-truth registry

Read `references/sources-registry.md` — the growing KB of known portals,
Reddit groups, Facebook groups, Instagram handles, forums, gov sources.
The discovery phase starts from here.

### 2. Discovery — recursive portal + Google crawl (PRIMARY), K-RERA supplement

The locality name from Step 0 drives everything. Discovery is a recursive crawl, not a one-shot search:

- **Registry bootstrap (first leg):** load `references/sources-registry.md` — the list of known property portals + community sources. This is the seed set.
- **Google + portal sweep:** run `web_search("<locality> property plots villas projects")` AND search EVERY known portal in the registry for that locality:
  - Portals reachable from the VPS (NoBroker, 99sqft, Propzilla, QuikrHomes, Homznspace, PropertyCrow, Proplocators, HousingMan, builder PDFs) — direct extraction/search.
  - Blocked portals (99acres, MagicBricks, Housing.com) — Apify actor (`magicbricks-99acres`) with the locality.
- **Registry growth:** any NEW property portal surfaced by Google or portal results is appended to the sources-registry — it becomes a known portal for all future runs.
- **K-RERA leg (statutory supplement, NOT the discovery engine):** `karnataka-rera-collector` query by taluk for the belt — authoritative registration/promoter/type/units/land/status as a cross-check and completeness layer.

### 3. Expansion loop — recursive per-project search until 100 unique competitors

```
competitive_list = projects found in step 2 (deduped by project key)
visited  = {}
frontier = competitive_list.copy()
while frontier and len(competitive_list) < 100:
    p = frontier.pop()
    if p in visited: continue
    visited[p] = True
    # for EACH project: search the portals again AND Google again
    run portal search for p on every known portal (direct for reachable,
        Apify for blocked) -> latest listings, pricing, AND the portal's
        "similar / recommended projects"
    run web_search('"<p>" <locality> price per sqft')
        -> pricing snippets AND more portals (add new ones to registry)
    for each recommended/suggested project in the results:
        if not in competitive_list and not in visited:
            competitive_list.append(it); frontier.append(it)
```

- Dedupe by project key (`sheet_io.key_name`). If a project is already in the list → ignore it; otherwise add it and recurse on it.
- Stop when the frontier is empty OR the competitive list reaches **100 unique competitors**.
- Every new project is immediately appended to the sheet (`rows_to_add.json` → `sheet_io.py append`).

### 4. Coordinates for every project

Priority order:
1. **Map link on the project's own page** — many builder/portal pages embed a
   Google Maps link; run `coords_from_urls.py` over the collected links
   (handles @lat,lon, q=lat,lon, !3d!4d, and short maps.app.goo.gl links).
2. **Places crawler** (Apify, ALWAYS with `locationQuery` + `countryCode` —
   unanchored runs wander to the wrong city; town anchors are silent
   zero-result traps; use city anchor + `searchMatching: all` + post-hoc
   Haversine filter).
3. **Playwright headless batch** (`maps` skill `geocode_batch_subproc.py`,
   locality-qualified queries, pass the belt locality as argv[3] — the baked
   default is Devanahalli and will wrong-resolve other belts).
4. No coords after all three -> sheet-only row (goes to the sheet, NOT the
   KML; the generator reports it).

### 5. Pricing per project — 3-month recency rule, listing-linked

- For each competitor, search the known portals for THAT project's listings (per-project portal search, not locality).
- **Recency cutoff:** only listings posted in the LAST 3 MONTHS count, whether by broker or by developer. Anything older is ignored for price discovery and flagged stale in the audit.
- **Price-discovery contract per accepted listing:** total quoted price + size (area) + computed psf (total/area; mark approx when area is a range) + **the listing URL — mandatory**. Every psf must be traceable to a saved listing link.
- Write one row per reviewed listing to the Listings & Sources tab: `[project, type, portal, price, total, date, url]` — `date` = listing date and MUST be within the last 3 months; `url` = the saved listing link that feeds the KML description's pricing-source list.
- Source order: direct portals first, Google snippets (validated against raw context) for blocked portals, Apify 99acres deep-scrape (totals only) as fallback.
- The pricing audit (`pricing_refresh.py`) flags any figure derived from a listing older than 3 months as stale; stale psf never reaches the KML label.

### 6. Sheet writes (tool-only)

- Competitors tab: `rows_to_add.json` -> `sheet_io.py append <id> Competitors`
- Listings & Sources tab: one row per listing reviewed:
  `[project, type, portal, price, total, date, url]` — this is what feeds
  the KML description's pricing-source list.
- POIs & Infrastructure tab: infra rows (below).
- R&D sheet schema (canonical): # | Project | Type | Locality | Launch
  Price | Current Price (per sq.ft) | Current Sale Price (Total) |
  Appreciation | Developer | Units | GPS Lat | GPS Lon | Google Maps Link |
  Location | Dist km | Source URL | Confidence.

### 7. KML — generated by the tool from the sheet

```bash
python3 scripts/kml_generator.py --sheet <id> \
  --subject-name "Thylagere Subject Land" \
  --subject-lat 13.3216384 --subject-lon 77.6789048 \
  --radius 10 --labels price --out <belt>_rd.kml \
  [--drive-file-id <existing drive file id>]
```

- Name label: `Project | Rs X/sqft` (psf; approx from total/area if needed).
- Icon: fixed per type (user-approved map — see references/kml-icons.md);
  `new_project`/`other` are auto-reclassified by name/price signals.
- Description: ALL details + "Pricing sources:" numbered list with the
  source URL(s) from the Listings & Sources tab.
- ASCII-only + XML-escaped + minidom-validated; upload via
  `files().update()` on the SAME file id (share link survives).
- The KML comes FROM the sheet — after any sheet edit, re-run the tool.

### 8. Infrastructure pipeline (separate incorporation)

For the same pin + radius:
- **OSM/Overpass** (`maps` skill, zero-cost, 46 POI categories): hospitals,
  schools, colleges/universities, industries/manufacturing, warehousing,
  tech parks. Category list per user: hospitals, schools, universities &
  colleges, industries/manufacturing, warehousing, tech parks, SEZ /
  industrial parks, malls, temples / spiritual centers / ashrams.
- **SEZ:** official notified list at sezindia.gov.in (search the PDF —
  don't guess; e.g. Biocon/Siemens/HCL/Wipro SEZs in the Anekal belt).
- **Malls, temples, ashrams** are under-indexed in OSM — add a
  `web_search` leg ("<locality> mall / temple / ashram").
- Write rows to the POIs & Infrastructure tab (name, category, lat, lon,
  source), then the same kml_generator run includes them with their icons.
- Radius query re-runs (`radius_query.py` with `--tab Competitors
  --extra-tab "POIs & Infrastructure"`) surface everything at 5/10 km for
  gap-checking.

### 9. Deliverables

- R&D sheet on Drive (Competitors / POIs & Infrastructure / Listings &
  Sources / Pricing Audit tabs), bold header, frozen row 1, ≥100 rows.
- KML uploaded to Drive (same file id), shared viewer.
- Post both links + headline rate bands as a Kelsa lead note to the assigned
  user, with caveats (asking ≠ transaction prices; flag 20+ km rows as
  verify).

### 10. RERA — wired 2026-08-04 (was deferred)

Karnataka RERA (`rera.karnataka.gov.in` — not `kanarera.karnataka.gov.in`,
that was a wrong domain guess in the original deferred note) is now the
PRIMARY comp-discovery leg (step 2), via the new `karnataka-rera-collector`
skill (`skills/domain/karnataka-rera-collector/`). Registration no,
promoter, project type, land area, unit/tower breakdown, dates, status,
and (once Tier-2 enriched) survey numbers all come from the statutory
register instead of portal scraping. See that skill's SKILL.md for the
full enqueue/poll job interface, the `query` command, and its verified
live counts (Bengaluru Urban 4,359 rows / Bengaluru  Rural 694 rows, as of
2026-08-04). Known gap carried over: that skill's `locality` field is
always blank (no structured source on the RERA site) — query it by
`taluk`, and keep doing locality-level grouping/filtering here in
property-rd the same way as before.

## Data contracts

`rows_to_add.json` (competitors):
```json
[{"project": "Prestige Crystal Lawns", "type": "Plotted Development",
  "locality": "Devanahalli", "launch_price": "", "psf": "Rs 8,999",
  "total": "Rs 1.38-3.40 Cr", "developer": "Prestige Group", "units": "",
  "lat": 13.25, "lon": 77.45, "maps_link": "https://maps.app.goo.gl/x",
  "source_url": "https://www.99acres.com/...", "confidence": "high"}]
```

`listings.json` (pricing_refresh input):
```json
[{"project": "Prestige Crystal Lawns", "type": "Plotted Development",
  "portal": "99acres", "price": "Rs 8,999/sqft", "total": "plots Rs 1.38-3.40Cr",
  "date": "2026-08-03", "url": "https://www.99acres.com/..."}]
```

## Pitfalls (all hit live Aug-2026)

- **Apify FREE-plan credit wall**: ~$0.50 launch reserve per paid actor;
  concurrent runs drain it mid-flight. Check `v2/users/me?token=...` before
  big runs; pivot geocoding to the Playwright batch when blocked.
- **Places anchor size**: town anchor -> 0 results (all outOfLocation); city
  anchor alone -> 16-41 km away results. City anchor + searchMatching all +
  post-hoc Haversine filter.
- **Same-name pollution**: "<project> Bangalore" resolves to a same-named
  project elsewhere (Adarsh Tropica=Sarjapur, Birla Tisya=Rajajinagar).
  Locality-qualify queries; filter 15+ km rows with a retry.
- **Wrong-row snippet prices**: 99acres "Project vs Locality Price" table
  rows show OTHER projects'/locality averages (Century Seasons
  "Rs 66,875/sqft" was a locality row). Validate every snippet; > ~Rs 20,000/
  sqft for a Devanahalli-area project is suspicious.
- **Portals block the VPS IP**: never raw-curl 99acres/MagicBricks/Housing
  (403/406). Use Apify actors or Google snippets.
- **LLM-generated XML breaks escaping** — the reason KML is tool-generated.
  Same for sheet writes: append via sheet_io, never inline API calls.
- **Scrape agent timeout**: an Apify run keeps going server-side after the
  agent dies — poll the run's dataset and fetch the raw JSON yourself.
- **KML must be ASCII**: Rs not Rs; minidom-validate before write.

## Verification

- Every new project is genuinely absent from the sheet (post-locality-strip
  dedupe — `sheet_io.key_name`).
- All placemarks within the radius; no-coords rows listed, not dropped.
- Every psf figure in the KML label has a source URL in its description.
- KML parses (the tool validates), count matches the sheet rows.
- Sheet + KML re-uploaded; the Drive share link unchanged.

## References

- `domain/karnataka-rera-collector` — the K-RERA index/enrich/query skill that step 2's
  primary discovery leg now calls (registration/promoter/units/land-area/
  dates/status, statutory source).
- `references/kml-icons.md` — approved icon map + KML rules.
- `references/sources-registry.md` — the growing sources-of-truth KB
  (portals / Reddit / FB / Insta / forums / gov). READ at run start, APPEND
  on new finds.
- `property-pricing-sources/references/property-rd-tool-design.md` — the
  blueprint this skill implements (v0.2; keep in sync).
- `domain/real-estate-area-research` — discovery pipeline + belt references
  (Thylagere, Anekal live state, sheet/KML ids).
- `productivity/property-pricing-sources` — rate bands, snippet technique,
  reachability table.
- `productivity/maps` — geocoders (geocode_batch_subproc.py), Overpass POIs,
  reverse geocoding.
