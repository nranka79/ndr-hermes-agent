---
name: property-rd
description: "Tool-first competitor R&D for Indian real estate — from a GPS pin, discover competing projects + infrastructure within 10 km, price them, and produce the R&D sheet + KML via scripts. The LLM extracts data; sheet_io/radius_query/kml_generator/pricing_refresh do the writes and the KML. Comp discovery is RERA-primary and state-aware: Karnataka RERA via karnataka-rera-collector, Tamil Nadu RERA via rera.tn.gov.in registers (buildings/layout/regularization list-projects + Excel export). RERA detail info is also the source for a project's latitude/longitude when it carries coordinates. Companion: real-estate-area-research (discovery), real-estate-portal-research (pricing listings), property-pricing-sources (rate bands)."
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
  - **Tunnel-direct (preferred — NDR 2026-08-12 directive, no Apify):** Hermes' own browser tools (`browser_navigate`, `smart_browser`) are PRE-WIRED to the residential tunnel (`AGENT_BROWSER_PROXY=socks5://hermes-utilities:1000`) — do NOT add manual proxy flags to them (NDR: "the browsers are already configured to do that"). Standalone `curl -x socks5h://hermes-utilities:1000` and raw Playwright launched from a shell DO need the explicit `proxy={"server": "socks5://hermes-utilities:1000"}` — the env var is not inherited by every shell context, and without it raw Playwright goes out the bare VPS IP and 403s (hit 2026-08-12). Verified reachable through the tunnel: MagicBricks (`/property-for-sale-in-<loc>-pppfs`, `/villa-for-sale-in-<loc>-pppfs`, paginate `?page=N`), NoBroker (SEO villa pages, Escape the login popup), rera.tn.gov.in. Recipes: `real-estate-portal-research/references/tunnel-portal-scraping-recipes.md`.
  - Apify (`magicbricks-99acres`) ONLY for what the tunnel can't reach (99acres is Akamai-fingerprint-blocked even through the tunnel).
- **Registry growth:** any NEW property portal surfaced by Google or portal results is appended to the sources-registry — it becomes a known portal for all future runs.
- **State RERA leg (statutory supplement, NOT the discovery engine):**
  - **Karnataka** belt → `karnataka-rera-collector` query by taluk
    (authoritative registration/promoter/type/units/land/status).
  - **Tamil Nadu** belt → TN RERA register via section 10b below:
    `rera.tn.gov.in` → Registrations → Projects → Registered Projects in
    Tamil Nadu → Building / Layout / Regularization of Layout
    (`/buildings-list-projects`, `/layout-list-projects`,
    `/regularization-list-projects`), including the OFFLINE year-by-year
    folders and the Excel download for bulk sweeps.

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
1. **RERA registration info — statutory, preferred (NDR mandate 2026-08-12).**
   When the project's RERA detail page / register entry carries coordinates
   (TN RERA detail pages and some K-RERA pages embed a map or expose
   lat/lon), take THOSE as the project's lat/lon and store them in the
   sheet's GPS Lat / GPS Lon columns. RERA coordinates are authoritative
   for the registered site; only fall through to the map-link / crawler
   legs below when the RERA entry has none.
2. **Map link on the project's own page** — many builder/portal pages embed a
   Google Maps link; run `coords_from_urls.py` over the collected links
   (handles @lat,lon, q=lat,lon, !3d!4d, and short maps.app.goo.gl links).
3. **Places crawler** (Apify, ALWAYS with `locationQuery` + `countryCode` —
   unanchored runs wander to the wrong city; town anchors are silent
   zero-result traps; use city anchor + `searchMatching: all` + post-hoc
   Haversine filter).
4. **Playwright headless batch** (`maps` skill `geocode_batch_subproc.py`,
   locality-qualified queries, pass the belt locality as argv[3] — the baked
   default is Devanahalli and will wrong-resolve other belts).
5. No coords after all four -> sheet-only row (goes to the sheet, NOT the
   KML; the generator reports it).

### 5. Pricing per project — MOST-RECENT-LISTINGS triangulation (NDR mandate 2026-08-11)

**The rate-bank reference file is a FALLBACK/ sanity check ONLY — never the primary
source for a project's psf.** The Aug-2026 Uganavadi run stored Prestige Park Drive
as "Rs 6,630-11,040/sqft" from the curated bank while its live 99acres page showed
~20 resale listings at ₹9,166-12,500/sqft (most recent 4: ₹11,253 / ₹12,500 / ₹11,000
/ ₹10,750). NDR caught it and mandated the following method:

1. For each competitor, pull that project's **individual listings** from the
   popular portals — 99acres, MagicBricks, Housing.com (in that order; Apify
   locality-first `-ffid` searchUrls for 99acres, `magicbricks-99acres` preset for
   MB, browser_use_cloud for Housing). Filter the haul to the project's own rows
   (match on projectName / listing title).
2. Take the **3-4 MOST RECENT listings** (by posted/updated date — ignore anything
   older than ~3 months unless the project has <3 listings total).
3. Per listing: total price + area + **computed psf = total/area** (mark approx if
   area is a range) + the **listing URL — mandatory**.
4. **Triangulate**: the project psf = the range/median of those 3-4 recent psf
   values (report e.g. "Rs 11,000-12,500/sqft"; if the 4 cluster tightly, report
   the median with one decimal). Never take a single listing; never take a
   rate-bank number.
5. Write one row per reviewed listing to the Listings & Sources tab — **the schema is
   `[Project, Type, Portal, Price (psf), Total, Area, Date, Posted By, URL]`** and the
   **URL column MUST be the individual listing's own URL** (the listing card link —
   99acres property-details URL, MagicBricks propertyDetails URL, etc.), NOT the project
   page. NDR mandate 2026-08-11: "save the link to each of the listings... anybody can
   verify each listing's pricing." Also record: **Date** = listing's posted/updated age
   ("3 weeks ago" → date), **Posted By** = who listed it (Broker/Dealer name, Owner, or
   Developer/builder). Prefer 3-5 listings per project and **span multiple portals**
   (99acres + MagicBricks + Housing.com) rather than all from one — that is the
   triangulation base.
6. If a project has NO live listings on any portal (pre-launch / fully sold /
   builder-site-only): fall back to builder official price + mark `(official)`,
   then rate-bank `(bank)` — and flag it in the Pricing Audit as low-confidence.
   Never present a bank figure as if it were listing-derived.

### 5b. Listings → competitor rate: AVERAGE, not range (NDR mandate 2026-08-11)

The Competitors tab "Current Price (per sq.ft)" and the KML label for a project
MUST be the **arithmetic mean of its individual listing psf values** in the
Listings & Sources tab (same project name, exact match). NDR caught Godrej
Royale Woods showing "Rs 5,789-5,913/sqft" in Competitors + "Rs 5,789/sqft" in
the KML while its own Listings & Sources rows were 11,921 / 13,291 / 8,421
(avg 11,211) — a rate-bank figure had leaked into the pipeline.

- After populating the Listings & Sources tab, recompute EVERY project's psf
  as `round(mean(listing psf values))` and write
  `Rs <avg>/sqft (avg of N listings)` into the Competitors cell. Exact-match
  on the normalized project name only — never fuzzy-match (Birla Trimaya Phase
  2/4 and Brigade Orchards variants got clobbered by substring matching).
- Update the KML by RE-RUNNING `kml_generator.py` (never hand-edit), then
  verify the label in the generated file.
- Cross-check: if a Competitor's psf differs from its listing average by a
  wide margin, it's usually stale bank data — the listings win.
- **User-stated averages may be misattributed — verify against the sheet
  before accepting.** In the Aug-2026 Uganavadi fix, NDR quoted Godrej
  Royale Woods's average as "10,870 + 11,921 + 13,291 = 12,027", but 10,870
  was actually Embassy Greenshore's listing sitting in the row above the
  three Godrej rows (11,921 / 13,291 / 8,421 → true avg 11,211). When a
  user gives you listing values that don't match the tab, say so explicitly
  (which project each value belongs to), compute the sheet-true average, and
  offer the alternate (e.g. excluding an outlier) — don't silently write
  either number.

### 5c. Price (psf) column is NUMERIC (NDR mandate 2026-08-11)

In the Listings & Sources tab, the psf column holds **plain integers**
(10600), NOT text like "Rs 10,600/sqft" or "Rs 10,600/sqft". The column
header carries the unit — use `Price (₹/sqft)` (or `INR/sqft`). This keeps
the column sortable/averagable and lets sheet formulas average it directly.
If you inherit a tab with text psf values, convert them
(`re.search(r'([\\d,]+)', v)` → int) before doing the average pass.

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
- **Quick KML from consolidated JSON (hit 2026-08-12, Ranka Oasis run):**
  when the user asks for "the KML link" as a deliverable alongside the
  sheet, build a color-coded KML directly from the run's consolidated
  JSON (not via kml_generator, which reads the sheet) — pin + competitors
  + POIs as `<Placemark>`s with a shared `<Style>` per class (pin,
  comp_pri / comp_rera for priced vs RERA-only, poi_h / poi_s / poi_w /
  poi_sez for infra categories), label with rank + distance, description
  with category/locality/developer/RERA/price lines, then upload to Drive
  via `gws_auth.build_service('drive','v3')` +
  `files().create(media_body=MediaFileUpload(..., mimetype='application/vnd.google-earth.kml+xml'), fields='id,webViewLink')`
  and hand back the webViewLink. This is a legit deliverable shortcut —
  the sheet-driven kml_generator remains the canonical artifact for
  pricing labels, but the quick KML covers the "give me the map" ask.
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

### 10b. TN RERA — Tamil Nadu projects (wired 2026-08-12)

**When the R&D target is in Tamil Nadu** (Chennai belt, OMR/ECR, Coimbatore,
etc.), the RERA leg switches from Karnataka RERA to **Tamil Nadu RERA**
(`rera.tn.gov.in`). TN RERA is structured DIFFERENTLY from K-RERA — there is
no district/taluk index POST; the registered-project register is a web app
with per-category lists. NDR's flow (codified 2026-08-12):

**Navigation path:** top menu **Registrations → Projects → Registered Projects
in Tamil Nadu** — gives THREE category options (landing pages — VERIFIED
2026-08-12; the `-list-projects` slugs in older notes 404 on the live site):
1. **Building** → `https://rera.tn.gov.in/building/list-project`
2. **Layout** → `https://rera.tn.gov.in/layout/list-project`
3. **Regularisation of Layout** → `https://rera.tn.gov.in/regularisation/list-project`

Landing pages are JS folder-cards (Online + per-year folders). The ONLINE
registers themselves are server-rendered `<table>` pages — curl them
directly (no browser needed):
- Building online: `https://rera.tn.gov.in/registered-building/tn`
- Layout online: `https://rera.tn.gov.in/registered-layout/tn`
- Regularisation online: `https://rera.tn.gov.in/registered_reglayout`

**Inside each category:**
- **Online registered projects** — live register, server-side table.
  Verified 2026-08-12 row counts: building 279, layout 3,150,
  regularisation 4,369.
- **Offline registered projects** — year folders `/{cat}/offline/{year}`
  (2017–2025), ALSO server-rendered tables (layout 2022/2023 pages are
  4,000+ rows / 5MB). SEARCH ACROSS EVERY YEAR FOLDER, not just the
  latest — older comps live there. (Pre-2024 Wayback structure:
  `/cms/reg_projects_tamilnadu/{Building,Normal_Layout,Regularisation_Layout}/<year>.php`.)
- The landing page has a **search box (top right)** that filters live;
  for bulk sweeps prefer parsing the register tables directly — each row
  already carries reg no, promoter, project details, approval, completion,
  status.
- **District filter:** reg numbers embed a district code —
  `TN/(\d+)/(building|layout|regularisation)` (online: `TNRERA/30/BLG/...`).
  **TN/30 = Hosur/Krishnagiri.** Filter by code first, belt keywords
  second, dedupe by normalized reg no. Verified 2026-08-12: 682 unique
  Hosur-belt projects (24 building / 467 layout / 191 regularisation) from
  online + offline 2017–2025.
- Full URL table, row counts, parse + district-filter recipe:
  `references/tn-rera-registers.md`. Re-runnable fetcher:
  `scripts/tn_rera_fetch.py` (tunnel fetch + parse + district filter +
  dedupe in one shot; `--district 30` = Hosur/Krishnagiri).

**Project detail pages:** TN RERA detail pages carry the statutory
info AND — relevant for step 4 — **coordinates** (lat/lon / embedded map)
on the registered-site info when present. Pull those into the sheet's GPS
Lat / GPS Lon as the project pin (step 4, priority 1). If the detail page
has no coordinates, fall through to the map-link / Places / Playwright
legs as normal. NOTE (verified 2026-08-12): the register LIST tables
themselves do NOT carry lat/lon — the address text names the locality only.
For belt-level R&D (100+ projects) it is not practical to open every
detail page; assign locality-centroid coordinates instead (see
`references/tn-belt-rera-backbone-recipe.md` step 4) and reserve
detail-page coords for shortlists.

**Networking (verified 2026-08-12, CORRECTED):** `rera.tn.gov.in` is
unreachable from the VPS datacenter IP directly (curl 000) AND from fetch
proxies (r.jina.ai timeout, allorigins timeout, codetabs 522), BUT the
residential tunnel DOES work: `curl --socks5-hostname hermes-utilities:1000
https://rera.tn.gov.in/...` returns HTTP 200 for BOTH http and https
(verified live 2026-08-12 — full register pages downloaded through it).
The earlier "tunnel blocked" note was WRONG (tested against 127.0.0.1:1000
instead of the hermes-utilities hostname). Do NOT conclude the site is
globally down — tunnel first. Wayback is a fallback for the list pages
(CDX confirmed: `rera.tn.gov.in/cms/reg_projects_tamilnadu/...` snapshots
exist through 2025). TN RERA uploaded-document PDFs follow
`/cms/Other_Details/Building/{Form_A,Approval_Details,Carpet_Area}/<yr>/<seq>-<yr>.pdf`
(see memory: Wayback fallback for these).

**Reuse the K-RERA discipline:** identity cross-check (RERA no → intended
project; TN has its own "TN RERA" registration numbers — don't alias a
Karnataka number), dedupe phases, and keep statutory fields as flags when
the register contradicts marketing.

### 10c. TN belt consolidation — RERA register is the COMPETITOR BACKBONE (verified 2026-08-12, Ranka Oasis run)

In a TN belt run, portal listing titles are locality noise, NOT project
names ("1 BHK Villa for Sale in Nallur, Hosur"). Grouping portal rows by
title produces fake "projects" (zuzuwadi, ambedkar colony, thally...). The
TN RERA register carries the real branded names (Falcon City, Jay Pee
Royale Enclave, Jasmine Valley...). Pattern: **mine RERA first → that is
the competitor-name backbone → attach portal pricing to it → locality
pricing bands when per-project attach fails.** Drop individual
registrations (Tvl./Thiru./Tmt./1) prefixes — land registrations, not
branded competitors. Full recipe, sanity windows (price 10–500L, psf
1,500–15,000), locality-centroid distance fallback, and per-locality bands
from the Hosur run: `references/tn-belt-rera-backbone-recipe.md`.

### 11. Social media presence benchmarking (follower audit)

When NDR asks "check YouTube/LinkedIn/Twitter/Instagram followers of <builders> vs DRA
Homes" — brand benchmarking, separate from project R&D. Full per-platform recipe +
verified Aug-2026 baseline for 10 Indian developers: `references/social-follower-audit.md`.

Quick method:
- **Search sweep first**: `web_search("<Co> YouTube channel subscribers")` /
  `"<Co> Instagram followers"` / `"<Co> LinkedIn followers"` / `"<Co> Twitter followers"`
  — Google-indexed snippets carry exact counts ("143K followers", "401,919 followers •
  1,001-5,000 employees", "4737Posts. 170Following. 3304Followers.").
- **X**: web_extract renders bio but NOT counts — use `browser_navigate` logged-out
  (public profile snapshot shows "X,XXX Followers"; 404 = no account). Social Blade 404s
  on most Indian handles — skip.
- **LinkedIn**: `web_extract` on `in.linkedin.com/company/<slug>` returns a rendered
  Company Profile Summary with Followers — authoritative over stale post snippets.
- **YouTube / Instagram**: about pages and direct extracts fail — use search snippets.
- **Disambiguate lookalikes** (Prestige UK/Inc, Brigade NY, Samudra LLC Austin) and
  multi-account builders (DLF: Limited/Homes/Mall/Emporio). Voice transcription:
  "Samudra" = Sumadhura Group (Bengaluru) — flag the assumption.
- Deliver per-platform ranking vs benchmark + total reach; mark the audit date.

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

- **KML with raw `&` / non-ASCII renders NOTHING (hit 2026-08-12 Ranka Oasis).** A quick-KML built by string concatenation (not the kml_generator tool) wrote `R&D` unescaped into `<name>` plus 112 non-ASCII chars (₹, curly quotes) — Google Earth / My Maps silently refuse the whole file; user sees zero pins. Diagnosis: `xml.dom.minidom.parse(kml)` fails "not well-formed: invalid token" at the raw `&`. Fix: build the KML with minidom `createTextNode` (it escapes automatically) and run every string through an ASCII-only filter (`₹`→`Rs`, curly quotes→straight) BEFORE the text node; verify `minidom.parseString` round-trips and `re.findall(r'&(?!amp;|lt;|gt;|quot;|apos;|#)')` finds zero. Also check icon hrefs resolve (all maps.google.com/mapfiles/* return 200). Re-upload to the SAME Drive file id (`files().update` + MediaIoBaseUpload) and md5/byte-verify the download round-trips.
- **Fuzzy name dedupe is DANGEROUS on TN register names (hit 2026-08-12).** Char-set dice ≥0.78 merged "A S Nagar" with "Sri Sai Nagar", "Aadithya Platinum City" with "Sandiep Sun City" — 2,113 wrong pairs, silently collapsing the competitor list. Dedupe ONLY by exact RERA registration number (normalized reg no). Never fuzzy-dedupe project names.
- **Canonical R&D sheet schema (NorthStar 2026-08-04, confirmed Ranka Oasis 2026-08-12):** Competitors tab = `Sl No | Project Name | Developer | Product Type | Price (Rs/sqft) | BHK | Possession | Land Area | Locality | Latitude | Longitude | Distance km | Pricing Basis`. Listings tab = `Sl No | Project Name | Source / Portal | Posted By | Posted Date | Price (Rs) | Area (sqft) | Rate (Rs/sqft) | Source URL | Data Source`. NDR requires: every competitor has developer + project name + location + type (villa/apartment/row villa/plot/farm plot) + pricing that traces back to the Listings tab; EVERY listing row carries its individual listing URL; and URL validation is a deliverable step (batch HEAD/GET through the tunnel — all 465 Ranka Oasis URLs returned 200; keep the verify JSON as the audit trail).
- **Locality-noise locality strings sneak past the NOISE_LOCS filter via space/hyphen variants (hit 2026-08-12).** `electronic city` (space) passed a NOISE_LOCS set containing `electronic-city` (hyphen) and became a fake competitor "electronic-city" with 109 listings attached. Normalize `loc_clean.replace(' ','-')` and re-check NOISE_LOCS BOTH before and after suffix-stripping.
- **Sheets tab names with parens/spaces break A1 ranges (hit 2026-08-12,
  Ranka Oasis deliverable).** Creating tabs like `Competitors (100)` and
  `Infrastructure (287 POIs)` via `sheets_create`, then populating with
  `sheets_update(range='Competitors (100)!A1')` fails:
  `HttpError 400 "Unable to parse range"` — and even single-quoting
  (`'Competitors (100)'!A1`) fails through the bridge. Use PLAIN tab
  names (`Competitors`, `Infrastructure`, `Pricing`, `Methodology`) at
  creation time; put counts in the sheet title, not the tab name. The
  bridge ops are `sheets_create(title=..., sheets=[{title:...}])` and
  `sheets_update(sheet_id=..., range=..., values=<json-string>)` — note
  `sheet_id`/`values`, NOT `spreadsheet_id`/`range=...`-as-arg-name and
  NOT `sheets_update_values` (unknown operation error).

- **Portal listing titles in TN belts are locality noise, not project names
  (hit 2026-08-12 Ranka Oasis).** MagicBricks titles like "1 BHK Villa for
  Sale in Nallur, Hosur" do NOT carry the project name. Do NOT group portal
  rows by listing title to build the competitor list — you'll get
  "zuzuwadi"/"ambedkar colony"/"thally" as fake projects. Build the list
  from the RERA register (real names), then attach portal pricing by
  normalized-name match; when attach fails, report locality pricing bands.
  See `references/tn-belt-rera-backbone-recipe.md`.
- **Individual RERA registrations (Tvl./Thiru./Tmt./1)/2) prefixes) are
  land registrations, not branded competitors (hit 2026-08-12).** ~72 of
  325 in-belt TN rows were individuals. Keep them in a separate bucket
  (land-supply context), never in the villa/plot competitor ranking.
- **Price/psf sanity windows are mandatory on portal hauls (hit
  2026-08-12).** Raw rows contain ₹350/sqft and ₹57,083/sqft garbage from
  mis-parsed areas. Filter price to 10–500 lakh and psf to 1,500–15,000
  before computing any band or median.
- **maps.app.goo.gl short links can resolve to place URLs with NO raw
  coords** (hit 2026-08-12 Ranka Oasis pin): `coords_from_urls.py` returns
  null because the final URL is
  `/maps/place/<PlusCode>+<Name>/data=!4m2!3m1!1s<hex>:<hex>!18m1!1e1` —
  no `@lat,lon`, no `!3d!4d`. Also do NOT try to decode the short Plus Code
  by brute-forcing leading pairs — it resolves to the wrong state (Kerala/
  Rajasthan vs Tamil Nadu). Working recipe: headless chromium with the
  SOCS+CONSENT consent cookies pre-set (Google's consent wall redirects to
  consent.google.com otherwise), load the place URL, wait ~9s, then read
  `@lat,lon` from the FINAL page URL (`/maps/place/DRA+Oasis+Villa.../@12.8393648,77.8121072,17z`).
  Script pattern in the 2026-08-12 run: `resolve_pin.py`-style Playwright
  with `ctx.add_cookies` for SOCS/CONSENT before `page.goto`.
- **Playwright on the VPS needs the venv that has playwright installed** —
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
- **NDR preference: tunnel/browser-first, Apify as fallback (Aug-2026).** NDR asked
  to run the portal leg "via browser" instead of Apify, and repeated it on
  2026-08-12: "I don't see any reason to use apify." Same run, when the agent
  started manually wiring socks into raw Playwright, NDR corrected: **"You don't
  need to route it through the tunnel socks and point as the browsers are already
  configured to do that."** Hermes browser tooling (`browser_navigate`,
  `smart_browser`) is pre-wired to the residential tunnel
  (`AGENT_BROWSER_PROXY=socks5://hermes-utilities:1000`) — never add manual proxy
  flags to those tools; only raw curl / standalone Playwright scripts from a shell
  need the explicit `-x socks5h://hermes-utilities:1000` /
  `proxy={"server": "socks5://hermes-utilities:1000"}`. Reality on the VPS:
  Playwright/curl THROUGH THE TUNNEL reaches MagicBricks (JSON-LD + card text, `?page=N`), NoBroker (SEO
  pages, Escape the login popup) and rera.tn.gov.in — verified 1,138 MB
  rows + 25 NoBroker rows on the 2026-08-12 Hosur run. Recipes:
  `real-estate-portal-research/references/tunnel-portal-scraping-recipes.md`.
  Still blocked even through the tunnel: 99acres (Akamai fingerprint —
  residential IPs get 403 too), Housing.com (406 even from the residential
  node — WAF fingerprint, verified via the error page's `Real Client IP`
  field showing the Bengaluru Spectranet node). When the tunnel hits a wall, NDR accepts Apify for the
  big three (said so explicitly) — use the 99acres projects-search actor
  with locality-first `-ffid` searchUrls. Never silently retry a blocked
  portal twice; escalate rung and tell the user.
- **Playwright on the VPS needs the venv that has playwright installed** —
  `uv pip install --python /opt/hermes/.venv/bin/python3 playwright`, verify
  `import playwright` in THAT interpreter, then launch the batch with it. A
  `uv pip install` that reports success can land in the wrong env (silent).
- **KML generator lat/lon coercion + total-only labels (patched Aug-2026):**
  sheet reads come back with lat/lon as STRINGS ("13.2256882") and the
  generator's coord_bucket crashed (`type str doesn't define __round__`) —
  `kml_generator.py` now runs every lat/lon through `parse_coord` before
  bucketing. Also: projects with only a total price and no per-sqft now label
  as `Name | Rs X L/Cr` (total fallback) instead of a bare name — matches
  NDR's "NAG Green Park | Rs 32 - 50 L" pattern. Guard: a psf cell like
  "4BHK from 2.7Cr" parses as Rs 4/sqft — write total-only rows as total
  (empty psf) so the fallback fires, don't cram "4BHK..." into the psf cell.
- **Portals block the VPS IP**: never raw-curl 99acres/MagicBricks/Housing
  (403/406). Use Apify actors or Google snippets.
- **LLM-generated XML breaks escaping** — the reason KML is tool-generated.
  Same for sheet writes: append via sheet_io, never inline API calls.
- **MagicBricks listing URL format changed (2026-08-11): old `propertyDetails/property-for-Sale-in-Bangalore&id=<decimal>` and `propertyDetails&id=<decimal>` both 404.** New format: `propertyDetails/property-for-Sale-in-Bangalore&id=<hex('MB'+decimal)>` — the id is the hex encoding of "MB" + the decimal listing id (e.g. 84700953 → `4d423834373030393533`). The `pdpid-<hex>` slug URLs found on search pages also work but the slug is project-specific and can't be reconstructed — the propertyDetails+hex form is the reliable one. Fix helper:
  ```python
  def mb_url(decimal_id): return f"https://www.magicbricks.com/propertyDetails/property-for-Sale-in-Bangalore&id={bytes('MB'+str(decimal_id),'utf-8').hex()}"
  ```
  When scraping MB listings, save the propertyDetails URL in this form (or verify any old-style URL resolves before trusting it). 99acres `spid-...` listing URLs still resolve (verify via web_extract, not curl — 99acres captchas the VPS IP).
- **URL validation is part of the deliverable (NDR mandate 2026-08-11).** Every listing URL in the Listings & Sources tab must resolve. Validate at build time: web_extract (Tavily) batch over the URLs, flag 404s, fix or re-find. Known traps: MB decimal-id URLs (fix via hex conversion), URLs with embedded `(id)` or `cardid` prefixes (broken — strip and convert), Tavily itself may 404 on MB pages that a browser loads fine — cross-check suspicious ones in the browser.
- **sheet_io header synonyms must cover the Listings tab headers.** `Price (₹/sqft)` normalizes to `pricesqft`, `URL` → `url`, `Total` → `total`, `Area (sqft)` → `areasqft`. If any of these aren't in `_HEADER_SYNONYMS`, `read_records` silently drops them and the KML's "Pricing sources" lines lose the psf/URL. Patched Aug-2026; keep the map in sync if the schema header changes again.
- **Scrape agent timeout**: an Apify run keeps going server-side after the
  agent dies — poll the run's dataset and fetch the raw JSON yourself.
- **KML must be ASCII**: Rs not Rs; minidom-validate before write.
- **`sheet_io.append_rows` with dicts shifts columns when the tab has a
  leading `#` column (patched Aug-2026).** The `#` header maps to None and
  was dropped from `header_fields`, so every appended dict row landed one
  column LEFT (project→col A, type→col B, lat→Units...). Fixed: None-mapped
  columns now emit empty cells. If you ever append dicts to a tab whose
  first column is a bare index/`#`, dump the raw rows afterward
  (`Competitors!A{n}:Q{n+3}`) and verify alignment before trusting the KML.
  Also: a wrong-row-range `values().update` after an append can CLOBBER a
  real row (Prestige Golfshire was overwritten when a fix targeted rows
  71-73 while the appended rows actually sat at 72-74). Always locate rows
  by re-reading, never by assuming append position.
- **POIs tab schema differs from Competitors — check the header before
  cell updates.** `POIs & Infrastructure` is `Name | Category | Lat | Lon |
  Dist km | Source` (6 cols), NOT the 17-col Competitors layout. Writing
  "lat to B, lon to C, dist to E" (the Competitors column letters) put the
  lat value into Category and left lon stale. Read `A1:H1` of the target
  tab first; never reuse Competitors column indices for the POIs tab.
- **KML Drive upload needs `MediaIoBaseUpload`, not raw bytes**
  (sheet_io patched Aug-2026). If you call `files().update(media_body=
  content_bytes)` with bytes you get `TypeError: media_filename must be str
  or MediaUpload`. Working pattern: `MediaIoBaseUpload(io.BytesIO(data),
  mimetype='application/vnd.google-earth.kml+xml', resumable=True)`.
- **update_cell row offset on tabs with a `#` column (hit Aug-2026):** the
  sheet's PHYSICAL row = `#` value + 1 (row 1 is the header). Writing to
  `F13` when the target project's `#` is 13 lands on the WRONG project (the
  `#12` row) and clobbers it. ALWAYS compute physical_row = int(#) + 1, and
  after any batch of `update_cell` writes, re-read the target rows raw
  (`read_range(tab, "A{r}:F{r}")`) and confirm project name + value before
  trusting the sheet. A single off-by-one silently corrupts ~10 rows.
- **`append_rows` takes the rows list directly — NOT a file path (hit
  Aug-2026).** Passing `"/tmp/rows.json"` as `rows` returns
  `Invalid value at 'data.values'` from the Sheets API. Pass the actual
  `list[list]` (or list of dicts for header-mapped tabs). For tabs WITHOUT a
  leading `#` column (e.g. `Listings & Sources`: Project|Type|Portal|Price|
  Total|Date|URL) list-of-lists appends land perfectly; verify raw after
  append anyway — `read_records` may cosmetically map Price into a "total"
  key while the raw cells are correct.
- **Live-listing pricing re-run recipe (NDR mandate, full walkthrough):
  `references/live-listing-pricing-recipe.md`** — how to verify one project
  end-to-end (browser_use_cloud on the project page, extract the "Listings
  in <Project>" section with area/total/psf/age), triangulate 3-4 most
  recent, then scale to 70+ projects in parallel browser waves with
  MagicBricks-search + Google-snippet fallbacks and npspid deep-scrape.
- **Re-geocode audit for "GPS coords failed" reports**: the sheet may look
  fully populated while several pins are wrong. Full-audit recipe that
  worked Aug-2026 (Uganavadi): (1) re-read BOTH tabs, (2) re-geocode EVERY
  competitor with `"<project> <locality>"` queries (never bare name, never
  locality alone — see maps skill pitfall), (3) diff old vs new coords
  (>300 m = changed), (4) web-verify the user-named projects (Manyata
  Silversprings → Indrasanahalli 562110; Mango Summers → Upparhalli/Kasaba
  Hobli; "Velocity Orb" is actually Velociti Aurum Valley), (5) re-add
  projects dropped for >15 km that were only misresolved (Manyata
  Silversprings 44 km→8.05 km; Century Seasons 24.8 km→5.17 km), (6) keep
  genuinely-out-of-belt drops (Neralu Farms = Chikkaballapur), (7) rebuild
  KML and re-upload to the SAME Drive file id, md5-verify the download.

## Verification

- Every new project is genuinely absent from the sheet (post-locality-strip
  dedupe — `sheet_io.key_name`).
- All placemarks within the radius; no-coords rows listed, not dropped.
- Every psf figure in the KML label has a source URL in its description.
- KML parses (the tool validates), count matches the sheet rows.
- Sheet + KML re-uploaded; the Drive share link unchanged.

## References

- `references/kml-icon-fetch-diagnostics.md` — Google My Maps / Earth "could not fetch image" errors: full diagnosis ladder (external probe via r.jina.ai / Google Translate proxy, raw DNS query to 8.8.8.8, TLS chain), why the listed icons ≠ broken icons, and the re-import fix. Consult BEFORE touching icons when a KML reports fetch errors.
- `references/row-villa-rera-comparables.md` — row-villa / rowhouse typology bank: 11 K-RERA registered comparable projects (FAR 0.66–2.25, unit mixes, carpet areas, land areas), the RoVilla RERA Prelim folder + summary sheet IDs, and the basement-parking design anchor used for the Palya brief. Load before any row-villa / rowhouse concept or FAR justification.
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
