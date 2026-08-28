---
name: maps
description: "Geocode, POIs, routes, timezones via OpenStreetMap/OSRM."
version: 1.3.0
author: Mibayy
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [maps, geocoding, places, routing, distance, directions, nearby, location, openstreetmap, nominatim, overpass, osrm, kml, mymaps]
    category: productivity
    requires_toolsets: [terminal]
    supersedes: [find-nearby]
---

# Maps Skill

Location intelligence using free, open data sources. 8 commands, 46 POI
categories (plus custom OSM tag queries — see reference), zero dependencies
(Python stdlib only), no API key required.

Data sources: OpenStreetMap/Nominatim, Overpass API, OSRM, TimeAPI.io.

This skill supersedes the old `find-nearby` skill — all of find-nearby's
functionality is covered by the `nearby` command below, with the same
`--near "<place>"` shortcut and multi-category support.

## When to Use

- User sends a Telegram location pin (latitude/longitude in the message) → `nearby`
- User wants coordinates for a place name → `search`
- User has coordinates and wants the address → `reverse`
- User asks for nearby restaurants, hospitals, pharmacies, hotels, etc. → `nearby`
- User wants driving/walking/cycling distance or travel time → `distance`
- User wants turn-by-turn directions between two places → `directions`
- User wants timezone information for a location → `timezone`
- User wants to search for POIs within a geographic area → `area` + `bbox`
- **User wants a KML map** with pins, lines, and distance labels for Google My Maps → `generate_kml.py`

## Prerequisites

Python 3.8+ (stdlib only — no pip installs needed).

## Commands

```bash
MAPS=/data/hermes/skills/productivity/maps/scripts/maps_client.py
KML=/data/hermes/skills/productivity/maps/scripts/generate_kml.py
```

### search — Geocode a place name

```bash
python3 $MAPS search "Eiffel Tower"
python3 $MAPS search "1600 Pennsylvania Ave, Washington DC"
```

Returns: lat, lon, display name, type, bounding box, importance score.

### reverse — Coordinates to address

```bash
python3 $MAPS reverse 48.8584 2.2945
```

Returns: full address breakdown (street, city, state, country, postcode).

### nearby — Find places by category

```bash
# By coordinates (from a Telegram location pin, for example)
python3 $MAPS nearby 48.8584 2.2945 restaurant --limit 10
python3 $MAPS nearby 40.7128 -74.0060 hospital --radius 2000

# By address / city / zip / landmark — --near auto-geocodes
python3 $MAPS nearby --near "Times Square, New York" --category cafe
python3 $MAPS nearby --near "90210" --category pharmacy

# Multiple categories merged into one query
python3 $MAPS nearby --near "downtown austin" --category restaurant --category bar --limit 10
```

46 categories: restaurant, cafe, bar, hospital, pharmacy, hotel, guest_house,
camp_site, supermarket, atm, gas_station, parking, museum, park, school,
university, bank, police, fire_station, library, airport, train_station,
bus_stop, church, mosque, synagogue, dentist, doctor, cinema, theatre, gym,
swimming_pool, post_office, convenience_store, bakery, bookshop, laundry,
car_wash, car_rental, bicycle_rental, taxi, veterinary, zoo, playground,
stadium, nightclub.

Each result includes: `name`, `address`, `lat`/`lon`, `distance_m`,
`maps_url` (clickable Google Maps link), `directions_url` (Google Maps
directions from the search point), and promoted tags when available —
`cuisine`, `hours` (opening_hours), `phone`, `website`.

### distance — Travel distance and time

```bash
python3 $MAPS distance "Paris" --to "Lyon"
python3 $MAPS distance "New York" --to "Boston" --mode driving
python3 $MAPS distance "Big Ben" --to "Tower Bridge" --mode walking
```

Modes: driving (default), walking, cycling. Returns road distance, duration,
and straight-line distance for comparison.

### directions — Turn-by-turn navigation

```bash
python3 $MAPS directions "Eiffel Tower" --to "Louvre Museum" --mode walking
python3 $MAPS directions "JFK Airport" --to "Times Square" --mode driving
```

Returns numbered steps with instruction, distance, duration, road name, and
maneuver type (turn, depart, arrive, etc.).

### timezone — Timezone for coordinates

```bash
python3 $MAPS timezone 48.8584 2.2945
python3 $MAPS timezone 35.6762 139.6503
```

Returns timezone name, UTC offset, and current local time.

### area — Bounding box and area for a place

```bash
python3 $MAPS area "Manhattan, New York"
python3 $MAPS area "London"
```

Returns bounding box coordinates, width/height in km, and approximate area.
Useful as input for the bbox command.

### bbox — Search within a bounding box

```bash
python3 $MAPS bbox 40.75 -74.00 40.77 -73.98 restaurant --limit 20
```

Finds POIs within a geographic rectangle. Use `area` first to get the
bounding box coordinates for a named place.

## KML Map Generation

When the user wants a visual map with pins, lines with distance labels,
and something they can open on their phone — generate a **KML file** for
Google My Maps import.

Use the `scripts/generate_kml.py` script:

```bash
# Hub-and-spoke: center → each airport / location
python3 /data/hermes/skills/productivity/maps/scripts/generate_kml.py \
  --hub 13.091 77.587 "Ranka Northstar" \
  --spoke 13.0777 77.5977 "Jakkur" \
  --spoke 13.1376 77.6040 "Yelahanka AFS" \
  --mode driving \
  --output map.kml

# Sequential route: A → B → C
python3 /data/hermes/skills/productivity/maps/scripts/generate_kml.py \
  --pin 13.091 77.587 "Point A" \
  --pin 13.0777 77.5977 "Point B" \
  --pin 13.1376 77.6040 "Point C" \
  --connect-all \
  --output route.kml
```

**Modes:**
- `--mode driving` (or walking/cycling) → OSRM road distance (auto-fallbacks to straight-line if OSRM is unreachable)
- `--mode straight` → Haversine straight-line only (no network call)

**Deliver the `.kml` file** to the user:
- **Preferred by DRAAS/Nishant**: upload to Drive TMP folder (`folder ID: 18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`), share the `webViewLink`. Use naming convention `YYYYMMDD_DescriptiveName.kml`.
- **Fallback**: send as `MEDIA:<path>` in Telegram (works for one-off shares).
- **Iterating on an already-delivered KML: update the SAME Drive file id**
  (`drive.files().update(fileId=..., media_body=...)`) instead of
  delete+recreate — the user's existing `drive.google.com/file/d/...` link
  keeps working and they don't have to re-import a new file. Verify the
  update landed by downloading the file back and grepping the local copy
  for the change. **Download gotcha:** `files().get(fileId=..., alt='media')
  .execute()` can return a DICT (error/empty) instead of bytes for binary
  files; use `get_media()` + `MediaIoBaseDownload` instead:
  ```python
  req = svc.files().get_media(fileId=fid)
  buf = io.BytesIO(); dl = MediaIoBaseDownload(buf, req)
  done = False
  while not done:
      _, done = dl.next_chunk()
  open('/tmp/x.kml','wb').write(buf.getvalue())
  ```
  Then `md5sum` the download vs the local build — identical hashes mean the
  live Drive file is current (a stale upload looks identical to \"labels
  missing\" to the user, so confirm the file itself before re-doing the build).
- Tell them: open mymaps.google.com → Create Map → Import → select or upload the file.

**Colours:** each line gets a distinct colour automatically. Pin icons
use Google's built-in marker set (red, blue, green, purple, orange, yellow).

Detailed KML format and pitfalls: see `references/kml-google-mymaps.md`.

**Category icons (villa vs plot etc.) and Google Maps headless coordinate
resolution for private gated communities** (which Nominatim/OSM lacks):
see `references/google-maps-coordinate-resolution.md`.

**MERGING an existing My Map with newly-built layers** ("merge this two",
"add infra/social/connectivity to my map"): export the existing map via
`https://www.google.com/maps/d/kml?mid=<MID>` — note it returns a **KMZ zip**
(Drive API cannot export My Maps), dedupe the accidental duplicate folders the
user's map almost certainly has, re-host relative icon hrefs to public Drive
URLs, merge styles+folders with minidom, validate, upload KML+KMZ and
MD5-verify the Drive copies. Full recipe: `references/kml-map-merge.md`
(also covers the map-embed screenshot URL for deck slides and the
deck-access 401/404 diagnostic when adding the map to a private Slides deck). This covers the
Playwright + Google Maps search-URL recipe, goo.gl link coordinate
extraction, and the standard mapfiles icon set for category-styled
pins. **The user-approved DRAAS R&D category set, new_project
reclassification, SEZ sourcing from the official notified list, and the
5-star hotel pick (The Oterra) are in
`references/realestate-kml-categories.md`.**

**MERGING a user's existing My Maps layers with a newly built KML** (the
"MERGE THIS TWO" pattern — combine both into one importable file):
see `references/mymaps-merge-workflow.md`. Highlights: Drive API CANNOT
export My Maps (403 "Export only supports Docs Editors files") — use the
public endpoint `curl -sL "https://www.google.com/maps/d/kml?mid=<mid>"`
which returns a KMZ (zip: `doc.kml` + `images/`). Existing maps usually
carry ACCIDENTAL duplicate folders (users re-import KMLs repeatedly) —
diff by name+coords and drop exact dups BEFORE merging, or the user gets
double pins. Merge = xml.dom.minidom DOM surgery: copy `<Style>` defs into
the target `<Document>` (watch ID collisions), move `<Folder>` nodes,
re-host relative `images/*.png` icon hrefs to a public Drive URL
(`uc?export=view&id=...`). **Heredoc guard pitfall:** foreground
`terminal` heredocs containing `&` inside strings (Drive URLs, "Infrastructure
& Connectivity") are rejected as backgrounding — write the script with
write_file and run `python3 script.py`.
For BATCH geocoding of many POIs/projects (e.g. 100+ names), use
`scripts/geocode_batch_subproc.py` + `scripts/geocode_one.py` —
crash-resilient: one subprocess per name (EPIPE kills at most one name,
not the whole process), saves after every name, resumes from partial
output, accepts names as strings OR `[{"name","cat"}]` dicts. Never write
a batch geocoder that dumps JSON only at the end or runs every query in
one process; you will lose the whole run to the first browser crash.

**Playwright is required in the invoking interpreter.** These scripts
import `playwright.sync_api`, and `geocode_batch_subproc.py` launches each
`geocode_one.py` via `sys.executable` — so the SAME python you use to run
the batch must have playwright installed. System `python3` on the VPS
does NOT (every name returns `CRASH-noout`; the subprocess stderr is
`ModuleNotFoundError: No module named 'playwright'`). Fix: install into a
venv and run the batch with that venv python:
```bash
uv pip install --python /opt/data/.venv/bin/python playwright
/opt/data/.venv/bin/python scripts/geocode_batch_subproc.py names.json out.json
```
The chromium binary already exists at
`/opt/hermes/.playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell`
(`geocode_one.py` points at it), so no `playwright install` step is needed.
**Path-layout warning (hit Aug-2026):** older docs and scripts referenced
`chrome-linux/headless_shell` — that layout is GONE in current Playwright
builds; the binary lives under `chrome-headless-shell-linux64/`. If a whole
batch returns `CRASH-noout` with the interpreter otherwise fine, verify the
`EXE` constant in `geocode_one.py` actually exists on disk before debugging
the browser. Playwright must be importable in the venv used to launch the
batch (`uv pip install --python <venv> playwright` then verify with
`python -c "import playwright"` — a silent install can land in the wrong env).
Diagnostic: if the whole run is `CRASH-noout` from the first name, check
the interpreter, not the browser.

**VERIFIED KML icon URLs (curl-tested 200, Aug-2026) — use these, they
render in Google My Maps / Earth:** `shapes/star.png` (subject anchor),
`pushpin/blue-pushpin.png` (apartment), `shapes/realestate.png` (villa/house —
signpost-with-house pictogram), `pushpin/grn-pushpin.png` (plot),
`shapes/schools.png` (school), `shapes/library.png` (college),
`shapes/electronics.png` (tech park — chip pictogram, clearer than museum),
`shapes/factory.png` (industry), `shapes/hospitals.png` (hospital),
`shapes/subway.png` (metro/transport hub), `shapes/rail.png` (rail),
`shapes/shopping.png` (mall/retail), `shapes/lodging.png` (hotel — bed
pictogram), `shapes/museum.png` (SEZ / institutional — classical columns
building; there is NO dedicated SEZ icon in Google's mapfiles),
`shapes/info.png` (other).
**2026-08-04: DRAAS/Nishant SUPERSEDED the mapfiles set with a custom
9-pin teardrop set (agreed pin images: apartment=blue buildings, villa=green
house, plot=orange map, hospital=red cross, school=yellow book, college=purple
grad cap, industry=gray factory, tech park=teal servers, transport=dark blue
train).** For DRAAS R&D maps use the custom pins, NOT the Google mapfiles
icons — the user explicitly re-reported "wrong pins" until the custom set was
in. Individual PNGs live at `/tmp/pin_icons/`, hosted on Drive folder `DRAAS
KML Pin Icons` (public). Full id→pin map, SEZ/hotel reuse decisions, and the
extraction recipe: `references/realestate-kml-categories.md`. Hosting pattern:
upload PNGs to Drive, share `role=reader,type=anyone`, use
`https://drive.google.com/uc?export=view&id=<FILE_ID>` as the KML href.
**Drive URL verification gotcha:** `curl -o /dev/null -w "%{http_code}"`
returns **303** (redirect) on these URLs; you MUST pass `-L` to follow and see
200. A plain HEAD/no-follow check will look like failure.
**COMMON 404s that look right but break KML icons:** `pushpin/star.png`,
`pushpin/yellow-pushpin.png`, `pushpin/green-pushpin.png`, `pushpin/blu-pushpin.png`,
`pushpin/orng-pushpin.png`, `shapes/school.png` (singular), `shapes/hospital.png`,
`shapes/homegarden.png`, `shapes/civic.png`, `shapes/office.png`, `shapes/warehouse.png`.
Note: `blue-pushpin.png` and `grn/ylw/red/purple/wht/ltblu-pushpin.png` exist,
but the two-letter abbreviations `blu-` / `orng-` do NOT. When a KML shows
broken/blank pins, curl each `<href>` — the 404s are almost always color
pushpins named like `yellow-pushpin` or the `star` in the wrong folder.
**HTTP 200 is NECESSARY but NOT SUFFICIENT — visually verify the pictogram
too.** Aug-2026 Bestamanahalli: `pal4/icon6.png` returned 200 and was listed
as "villa/house" here, but it renders as a generic blue circle with a
folder/package symbol — nearly identical to the apartment's blue pushpin.
The user looked at the map and called out the villa pins as wrong. Technique:
download each candidate, upscale 3–5×, view INDIVIDUALLY (labeled montages
get OCR-hijacked into reading the text labels instead of describing the
pictograms; tiny 32px icons are invisible to vision — upscale first). The
`ms/icons/` set is mostly 404 — only `realestate.png` (house signpost),
`shopping.png`, `lodging.png`, `info.png`, `flag.png` and the color dots
(blue/green/red/yellow/orange/pink/purple + `-dot` variants) exist. The
`pal2/pal3/pal4` sets are 32px colored circles with generic pictograms
(cars, weather, documents) — no clean building/house icons; don't reach for
them when a user needs semantic real-estate pins.

**Batch-geocode hard lessons from the Aug-2026 Thylagere 104-POI run**
(see `references/batch-geocode-lessons.md` for the full transcript):
- **Pacing beats everything.** ~4s between names still triggers Google's
  ~50-query IP throttle (a WALL of consecutive `FAIL` lines is the
  signature). 10s spacing + 120s per-name subprocess cap recovered 19/19
  on the retry. Slow is fast for this.
- **Fallback locality is baked in and defaults to Devanahalli** —
  `geocode_one.py` appends `name + " Devanahalli"` as the first variant
  (for the Thylagere belt). For any OTHER belt you MUST pass the target
  locality as argv[3] to the batch script:
  `geocode_batch_subproc.py names.json out.json Anekal` (or Attibele,
  Chandapura, Electronic City...). Without it, unresolved names silently
  resolve to wrong-place matches in Devanahalli (observed in the
  Aug-2026 Bestamanahalli run: "Bestamanahalli gated plots" resolved
  48 km away). The fix is already in the scripts (fallback_loc = argv[3],
  default Devanahalli); use it.
- **Locality-qualified query beats bare name + " Bangalore".** In the
  Aug-2026 Bestamanahalli/Anekal run, `"<project> Bangalore"` queries
  frequently resolved to same-named projects elsewhere in the city
  (e.g. Green Avenue → 27 km off, Godrej Ananda → Bagalur). Re-query as
  `"<project> Anekal"` / `"<project> Attibele"` / `"<project> Chandapura"`
  to get the correct pin. Build the query from the project's known
  locality, not the city.
- **Bare-name misresolution is NOT proof a project is out of radius.**
  Aug-2026 Uganavadi audit: Manyata Silversprings (real project, Sy.73
  Indrasanahalli 562110) bare-resolved 44 km away and had been dropped
  from the sheet; Century Seasons (Doddaballapura-Devanahalli Main Rd)
  resolved 24.8 km off but re-geocoded to 5.17 km with
  `"Century Seasons Doddaballapura Devanahalli Main Road"`. When a user
  says "GPS searches failed / make coords accurate", re-run the WHOLE list
  with locality-qualified queries, diff old vs new (>300 m = changed), and
  re-add dropped projects whose qualified query lands in radius. Also
  `"<project> Devanahalli"` can still collapse to the locality centroid
  (Godrej Royale Woods / Sobha Lifestyle Legacy / Sobha Oakshire / Brigade
  Oasis all landed on the same Devanahalli point in one round) — always
  qualify with the project name AND its sub-locality (Sadahalli, IVC Road,
  Shettigere, Kannamangala) when the project sits off the main locality.

**Competitor-expansion pipeline lessons (geocode-then-filter ordering,
99acres no-coords, Places-crawler wander):** see
`references/geocode-radius-pipeline-lessons.md`.
- **99acres area-search pattern**: the `magicbricks-99acres` preset with
  plain city names returns scattered listings; for NEW-project discovery
  around a locality, use the 99acres projects-search scraper with
  locality-first `searchUrls[]` (e.g. `property-in-devanahalli-ffid/`).
  134 records from 5+ locality URLs, project-name-per-record, prices,
  NO coordinates (geocode separately). Dedupe by stripping locality
  suffixes before comparing. If the `apify_run_actor` wrapper returns
  empty/failed, drive actors directly via the Apify REST API
  (`APIFY_API_KEY` in env): run → poll → fetch dataset; verify items
  actually match before trusting (one run "succeeded" with scattered
  unrelated Bangalore listings).
- **Subprocess timeout must exceed the 2-attempt budget.** 2 Google tries
  × (nav+wait+search) ≈ 50s; a 45s subprocess cap produces fake
  `TIMEOUT` failures. Use 100–120s.
- **Save-after-every-name only protects the JSON if the write completes.**
  `open(f,'w')` truncates FIRST, so a kill between truncate and dump
  leaves a 0-byte file. Always ALSO print one stable, parseable line per
  name to stdout (e.g. `13.34,77.71 | [cat] Name | via: q`) and recover
  from run logs when the JSON dies. Log lines must keep ONE format across
  all retry iterations — each different format forces a multi-regex parse.
- **Filter junk before geocoding.** Maps category-scrape "names" like
  `Hotel`, `Villa`, `Government Hospital`, `€182` are labels, not POIs.
  Drop them; don't burn queries on them.
- **Nominatim/OSM has ~zero coverage for rural plotted developments**
  (Devanahalli/Nandi belt). For those, Google Maps is the ONLY resolver;
  don't waste a pass on the Nominatim fallback.

## Viewing / validating a USER-SUPPLIED KMZ or KML (land surveys)

When a user uploads a KMZ (often a georeferenced land survey) and says "can't
open it / get it fixed in Google Earth": you CANNOT launch the Google Earth
desktop app for them (headless server, no display). Instead validate the file,
reassure them it's healthy, and deliver working alternatives — a self-contained
Leaflet HTML map, a static OSM-tile PNG, and a cleanly re-packaged KMZ.
Full recipe (unzip KMZ→doc.kml, validate XML/coords, extract to JSON, render
both viewers, re-zip, communication wording): `references/kmz-kml-viewing-survey.md`.
Key gotchas: KMZ is just a ZIP with `doc.kml`; tile y-row min/max flip causes a
negative canvas; matplotlib needs a `uv pip install --python <venv>`
install into a throwaway venv.

## When the user asks to "open the KML in Google Maps / My Maps and take a
picture" but the headless browser has no Google login
requires auth): don't dead-end. Render the KML placemarks as a Leaflet +
OSM-tiles HTML page (permanent tooltips `{permanent:true}` so labels show
in a static screenshot), open `file://` in headless chromium, wait for
`.leaflet-tile-loaded` count > 20, screenshot. Delivers a labelled map
image (name + ₹/sqft per pin, villa=🏠/plot=🚩/subject=★) that matches the
KML — see the Aug 2026 Thylagere competitor-map session. The interactive
Google Maps search (type into searchbox + Enter, read `@lat,lon` from URL)
is the same-session fix for the bare-URL search not resolving.

## Resolving Coordinates For Private / Gated Communities

Nominatim and OSM frequently have **no entry** for private gated real
estate projects (Prestige Sanctuary, DNR Solace, gated villa communities,
etc.) — `maps search` returns nothing even for well-known projects. When
`search` fails:

1. Try the Google Maps search-URL recipe via Playwright headless chromium
   (full code + pitfalls in `references/google-maps-coordinate-resolution.md`)
2. If the user shares a `maps.app.goo.gl` link, resolve it first —
   `curl -sL` follows the redirect and the final URL carries `@lat,lon`
   (a 302 `location:` header also carries the coords — parse it directly
   without needing the body)
3. After extracting coords, **reverse-geocode to confirm the landmark claim**
   (`maps reverse` / Nominatim): a "behind Brigade Meadows" / "next to X"
   claim should reconcile with the returned suburb+PIN (e.g. pin → Kaggalipura,
   Udayapura, PIN 560116 = Brigade Meadows belt). Flag mismatches to the user
   (voice vs pin disagreeing is a recurring DRA source of error — Aug-2026:
   "Brigade Omega" in voice vs "Brigade Meadows" per pin + follow-up).
4. Search-engine SERP scraping is unreliable from this datacenter IP
   (bot challenges) — prefer the Maps search URL directly

## Working With Telegram Location Pins

When a user sends a location pin, the message contains `latitude:` and
`longitude:` fields. Extract those and pass them straight to `nearby`:

```bash
# User sent a pin at 36.17, -115.14 and asked "find cafes nearby"
python3 $MAPS nearby 36.17 -115.14 cafe --radius 1500
```

Present results as a numbered list with names, distances, and the
`maps_url` field so the user gets a tap-to-open link in chat. For "open
now?" questions, check the `hours` field; if missing or unclear, verify
with `web_search` since OSM hours are community-maintained and not always
current.

## Workflow Examples

**"Find Italian restaurants near the Colosseum":**
1. `nearby --near "Colosseum Rome" --category restaurant --radius 500`
   — one command, auto-geocoded

**"What's near this location pin they sent?":**
1. Extract lat/lon from the Telegram message
2. `nearby LAT LON cafe --radius 1500`

**"How do I walk from hotel to conference center?":**
1. `directions "Hotel Name" --to "Conference Center" --mode walking`

**"What restaurants are in downtown Seattle?":**
1. `area "Downtown Seattle"` → get bounding box
2. `bbox S W N E restaurant --limit 30`

**"Find places and get their reviews/ratings/pricing":**
1. Use `nearby` or raw Overpass to find candidate places
2. Enrich each named place with `web_search` (Tavily) for reviews and
   pricing; for portal listing data use `apify_run_actor` (preset
   `magicbricks-99acres`)
3. Present enriched results: walk time, ⭐ rating, pricing, phone

**"Make a map from these locations with distance labels":**
1. Geocode each location with `search` to get coordinates
2. Run `generate_kml.py` with the coordinates
3. Deliver the `.kml` file per the **Deliver** section above (prefer Drive TMP upload)

## Querying Custom OSM Tags (Beyond the 46 Predefined Categories)

The `nearby` and `bbox` commands only accept the 46 categories listed above.
If the user asks for a POI type not in that list (e.g. **barber / hairdresser /
salon, tattoo, vape shop, pet shop, optician**), use a **raw Overpass API
query** via terminal or execute_code instead.

Full examples, fallback mirrors, and a worked barber-shop example: see
`references/overpass-custom-poi.md`.

### Common Missing POI Tags

| User asks for | OSM tags |
|---|---|
| Barber / Hair Salon | `shop=hairdresser`, `shop=barber`, `shop=beauty` |
| Pet shop | `shop=pet` |
| Optician | `shop=optician` |
| Tattoo / Piercing | `shop=tattoo` |
| Vape / Tobacco | `shop=tobacco`, `shop=e-cigarette` |
| Key cutting | `shop=key_cutter` |
| Repair shop | `shop=repair` (+ `repair=*` for type) |

### Raw Overpass Query (via Python execute_code)

```python
import json, urllib.request, urllib.parse, math

# Step 1: query Overpass for custom tags near a location
query = """
[out:json][timeout:25];
(
  node["shop"="hairdresser"](around:1000,12.9945,77.5877);
  way["shop"="hairdresser"](around:1000,12.9945,77.5877);
  node["shop"="barber"](around:1000,12.9945,77.5877);
  way["shop"="barber"](around:1000,12.9945,77.5877);
);
out center 20;
"""
url = "https://overpass-api.de/api/interpreter"
req_data = urllib.parse.urlencode({"data": query}).encode()
req = urllib.request.Request(url, data=req_data,
    headers={"User-Agent": "HermesAgent/1.0"})
with urllib.request.urlopen(req, timeout=25) as resp:
    result = json.loads(resp.read().decode())

# Step 2: calculate walking distances from reference point
ref_lat, ref_lon = 12.9945, 77.5877  # e.g. Embassy Habitat
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

places = []
for e in result.get("elements", []):
    t = e.get("tags", {})
    lat = e.get("lat") or e.get("center", {}).get("lat")
    lon = e.get("lon") or e.get("center", {}).get("lon")
    dist = haversine(ref_lat, ref_lon, lat, lon)
    places.append({
        "name": t.get("name", "(unnamed)"),
        "phone": t.get("phone", ""),
        "hours": t.get("opening_hours", ""),
        "address": f"{t.get('addr:street','')} {t.get('addr:housenumber','')}".strip(),
        "dist_m": round(dist),
        "walk_min": round(dist * 1.3 / 80),  # ~80m/min with road factor
        "lat": lat, "lon": lon,
        "maps_url": f"https://www.google.com/maps/search/{urllib.parse.quote(t.get('name',''))}/@{lat},{lon},17z"
    })

places.sort(key=lambda p: p["dist_m"])
print(json.dumps(places, indent=2))
```

### Raw Overpass Query (via terminal curl)

```bash
curl -s 'https://overpass-api.de/api/interpreter' \
  --data-urlencode 'data=[out:json][timeout:25];
(
  node["shop"="hairdresser"](around:1000,12.9945,77.5877);
  way["shop"="hairdresser"](around:1000,12.9945,77.5877);
  node["shop"="barber"](around:1000,12.9945,77.5877);
  way["shop"="barber"](around:1000,12.9945,77.5877);
);
out center 20;' | python3 -m json.tool
```

### Overpass API Fallback Mirrors

The script uses these in order — use the same fallback in raw queries:
```
https://overpass-api.de/api/interpreter
https://overpass.kumi.systems/api/interpreter
```

### When Web Tools Are Down

If `web_search`, `web_extract`, and browser are unavailable (no Tavily
key, camofox not running), the recovery sequence is:
1. Geocode the reference point with `maps search` (Nominatim, no key needed)
2. Query Overpass directly for custom POI tags (Python execute_code preferred)
3. Calculate walking distances with Haversine + road-factor estimate
4. Generate Google Maps direction URLs for the user to tap

## Pitfalls

- **`geocode_batch_subproc.py` must be run with a python that has
  playwright installed** (it inherits `sys.executable` for subprocesses).
  A full wall of `CRASH-noout` with no coords = missing module, not a
  browser problem. See the batch-geocode section above for the venv
  command.
- **Geocoding previously-uncoordinated rows can invalidate a radius
  filter.** Rows added without coordinates never got the distance check;
  a later geocode may land them OUTSIDE the radius (observed: Konig Pearl
  County geocoded to 12.5 km from the Thylagere reference when the 10 km
  band was the cutoff; in the same 29-name pass only 2 of 29 resolved
  in-radius — portal-URL locality labels like "Devanahalli" are NOT a
  radius proxy). After any late geocode pass, re-run the distance filter
  and flag/remove out-of-radius rows before updating sheet + KML; fill
  GPS for all resolved in the sheet, but add only in-radius pins to the
  KML. See `references/geocode-radius-pipeline-lessons.md`.
- `nearby` only accepts the 46 predefined categories above. For any other
  POI type (barbers, pet shops, tattoo, etc.) use raw Overpass queries.
- Nominatim ToS: max 1 req/s (handled automatically by the script)
- `nearby` requires lat/lon OR `--near "<address>"` — one of the two is needed
- OSRM routing coverage is best for Europe and North America
- Overpass API can be slow during peak hours; the script automatically
  falls back between mirrors (overpass-api.de → overpass.kumi.systems).
  For Python execute_code, build your own fallback loop over the mirror list.
- `distance` and `directions` use `--to` flag for the destination (not positional)
- If a zip code alone gives ambiguous results globally, include country/state
- Unnamed OSM nodes (tagged as shop=hairdresser but no name=*) are usually
  small local shops, not upscale salons — filter them out unless the user
  explicitly wants budget/local options.
- The OSRM duration field is unreliable for walking: OSRM returns driving
  speed by default even in foot mode in some edge cases. Prefer calculating
  walking time yourself at 80m/min with a 1.3x road factor.

### KML Generation Pitfalls

- **Never trust an icon URL on face value — verify HTTP 200 AND the actual
  pictogram.** A 404 makes pins blank, but a 200 with the wrong pictogram
  makes pins show but look wrong (Aug-2026: `pal4/icon6.png` = blue circle
  with folder symbol, not a house — user reported "villa pins don't match").
  After any icon change, curl every `<href>` (must be 200) AND inspect the
  images: download → upscale 3–5× → view one at a time (montages with text
  labels trigger OCR instead of visual description; 32px icons are invisible
  to vision models until upscaled). Re-verify BEFORE telling the user it's
  fixed — the Aug-2026 rebuild was delivered with the bad villa icon and the
  user had to re-report it.
- **Colour similarity between category pins is a UX bug.** Blue pushpin
  (apartment) + blue-circle villa icon = indistinguishable at map zoom. When
  categories must be told apart at a glance, pick visually distinct
  pictograms OR clearly different colours (blue/green/yellow pushpins work;
  two blue-ish icons don't).
- **DRAAS/Nishant's fixed R&D-map category set (Aug-2026): NO "New Project"
  category.** User: "I don't need a new project icon. We only need
  apartments, villas, residential plot, hospitals, schools, college,
  industry, tech park, transport hub, special economic zone... and a
  five-star hotel." The map legend must be exactly: Apartment, Villa, Plot,
  Hospital, School, College, Industry, Tech Park, Transport (metro/rail),
  SEZ, 5-star Hotel, Subject. Do NOT invent extra categories for launch
  status.
- **99acres tags plotted layouts and prelaunch towers as "New Project" —
  reclassify them into real product types before building the KML.** A
  name/price-signal pass maps each one to apartment/villa/plot: "plots" in
  the price text → plot; "BHK"/"apt"/sqft configs → apartment; "villa" in
  the name → villa. Observed Aug-2026 Bestamanahalli: 20 surviving
  "new_project" pins reclassed as 8 plots + 12 apartments, none kept the
  yellow icon. Keep a RECLASS dict keyed by exact row name so the mapping
  is auditable and re-runnable. Dedupe by coordinate bucket AFTER applying
  reclass, and remember a new_project duplicate at the same coords as a
  real-typed row is dropped by the score-based dedupe anyway.
- **Escape XML entities OUTSIDE CDATA — names, folder titles, hrefs.** Only
  `<description>` is CDATA-wrapped. `<name>` tags (pin labels, folder names,
  Document name) and `<href>` attributes are raw XML: a bare `&` (e.g.
  "Infrastructure & Connectivity", "Ph-1 & 2", Drive URLs with `&id=`) makes
  the KML not well-formed and the whole import fails. Escape with `&amp;` in
  every name/folder/href, then validate BEFORE upload with
  `python3 -c "import xml.dom.minidom; xml.dom.minidom.parse('x.kml')"`
  (the error tells you the line — grep non-`&amp;` ampersands there).
  Observed Aug-2026: three parse failures in a row from raw `&` in folder
  names + icon hrefs before the fix.
- **Sanity-check batch-geocode results against the belt's lon/lat window.** A
  locality-qualified query can still resolve to the wrong place: Aug-2026
  Chikkaballapur run — "Chikkaballapur KIADB Industrial Area" resolved to
  lon 77.28 (40+ km west of the 77.71 belt) and "Pharmaceutical SEZ" to 77.19;
  both were silently wrong and had to be re-checked against web sources.
  After a batch run, eyeball every coordinate against the subject land's
  bounding box (±0.3° is a red flag) and re-resolve or web-verify outliers
  before putting them on the KML. Nominatim returns NOTHING for rural
  Karnataka belts (Chikkaballapur/Nandi) — the Playwright Google Maps
  resolver is the only path, and even it misplaces non-landmark POIs.
- **Distance lines for a connectivity layer**: hub-and-spoke LineStrings from
  the subject centroid to each anchor, with the straight-line km in the
  `<name>` (visible label). Haversine is fine; tell the user road distance
  runs ~15–25% higher. Keep the subject boundary polygon from the user's map
  to derive the centroid — don't geocode the land name (it returns a village
  centroid, not the parcel).
- **Merging a My Maps export with a fresh KML build**: Google's
  `https://www.google.com/maps/d/kml?mid=<mid>` endpoint returns a **KMZ
  (zip)** — unzip it to get `doc.kml` + `images/`. User maps accumulate
  **accidental duplicate folders** (observed Aug-2026: 2× "Proposed Land"
  folders and 2× near-identical "Plotted development" layers differing only
  in coordinate precision, one with a stray pin moved into the boundary
  folder) — diff folders by placemark names/coords and keep ONE copy so the
  merged import doesn't double pins. Relative icon hrefs (`images/icon-1.png`)
  in the export break a standalone KML — re-host the PNG on Drive (public,
  `role=reader,type=anyone`) and rewrite the href to
  `https://drive.google.com/uc?export=view&id=<FILE_ID>`. When the user's map
  already carries the boundary polygon + location pin, DROP the new build's
  own "Subject Land" folder (keep only the 4 new layer folders) to avoid two
  subject pins. Merge via `xml.dom.minidom` (append the new Style defs +
  Folder elements into the existing Document; style IDs like `st-*` don't
  collide with My Maps' `icon-1899-*`/`poly-*`), validate with minidom.parse,
  then upload BOTH the merged KML and a KMZ (zip doc.kml) and MD5-verify the
  Drive copies byte-identical.
- **The on-map label is the `<name>` tag, NOT the `<description>`.** Google My
  Maps renders `<name>` as the visible label next to the pin; `<description>`
  only shows in the popup on click. If a KML rebuild "loses" data from the
  labels (₹/sqft, price, distance), it's because the data was put in the
  description balloon instead of the name. Keep the KEY data in the label,
  full detail in the description. Observed Aug-2026 Bestamanahalli: icon-fix
  rebuild dropped the `| ₹/sqft` suffix from labels; user explicitly asked to
  restore it from the R&D sheet.
- **Compact rate-label recipe** (put in the `<name>`): strip `**` markdown,
  cut at first `;`, drop parentheticals, keep from the first `₹` onward
  (handles `**~₹3,692** (official) / ₹3,926 MB avg; resale ₹4,250` →
  `~₹3,692 / ₹3,926`). Fall back to listing price when no per-sqft exists
  (`NAG Green Park | ₹32 - 50 L`); leave name bare only when neither exists.
- **Dedupe by NORMALIZED NAME first, coordinate bucket SECOND — never
  coordinate-bucket-only.** The same project recurs as multiple rows at
  slightly different coords (each geocode pass of a differently-spelled name
  lands a few metres off, e.g. `Dlf Woodland Heights` with ₹5,188–7,119 vs
  `DLF Woodland Heights Rajapura, Bangalore South` empty). Coordinate-bucket
  dedupe keeps BOTH — the empty duplicate wins its own bucket and you get a
  label-less pin. Fix (Aug-2026 Bestamanahalli): normalize names by stripping
  locality suffixes (`, Bangalore South`, ` Anekal`, ` Attibele`,
  ` Chandapura`, ` Rajapura`, ` Begihalli`, etc.) and merge by that key,
  keeping the highest-scoring row (per_sqft=2 > price=1 > url=0.5 > dist=0.2);
  only then dedupe by rounded coords. This recovered rates for DLF Woodland
  Heights, NAG Green Park, Royaal Vasundhara in one pass (115 rows → 100 by
  name → 94 by coords).
- **Infrastructure/social-layer enumeration must be RADIUS-FIRST, not
  name-first.** Building the schools/colleges/hospitals layer from
  web_search queries ("colleges near Anekal") re-introduces the
  name-seeded discovery trap: search results are biased to marquee,
  well-indexed names and portals, and miss institutions whose official
  name/locality string doesn't match the query. Observed Aug-2026
  Bestamanahalli: **Alliance University** (55-acre campus, 10,400+
  students, 2.95 km from the subject — squarely inside the 10 km radius)
  was missing because its campus is indexed under "Chikkahagade"
  (Chandapura side), so an "Anekal" query dropped it. Fixes, in order:
  (1) enumerate with a coordinate-anchored Places/Overpass query around
  the subject pin, THEN haversine-filter; (2) run "university" as its OWN
  query term separate from "college" (they index differently on portals);
  (3) keep a heavyweight-anchor checklist — name the belt's known big
  institutions explicitly and confirm each is present or flagged absent;
  (4) re-run the POI sweep after competitor discovery re-seeds localities.
  Full post-mortem: `references/realestate-kml-categories.md`.
- **When a pin genuinely has no rate data, research it — don't leave the
  label bare.** `web_search "<project> <locality> price per sqft"`; portals
  (NoBroker/MagicBricks/99acres/Housing) return project-level ₹/sqft.
  Mark locality-average fallbacks with `~` and name the source
  (`~₹7,600 (Anekal villa avg)`, `~₹6,450 (NoBroker Aug'26)`) so the number
  is traceable. NEVER invent a rate: pre-launch/price-on-request projects
  stay labeled `Pre-launch POR` (Prestige Attibele case). After injecting,
  rebuild and grep the KML for `st-villa|st-apartment|st-plot` placemarks
  whose `<name>` lacks `₹` — that is the acceptance check (94 pins → 93
  with rate, 1 legit POR). Re-download the Drive copy afterwards and grep
  again; the Drive hash must match the local build (this catches a stale
  upload, which looked identical to "labels missing" to the user).
- KML uses **`lon,lat,alt`** coordinate order (longitude first, then latitude).
  Swapping the order places pins on the other side of the globe.
- Line colours are **AABBGGRR** hex (alpha, blue, green, red), not the usual
  AARRGGBB. The script handles this internally.
- Distance labels go into the `<name>` tag of the LineString Placemark so
  My Maps renders it as a visible label near the line.
- If OSRM is unreachable, the script silently falls back to Haversine
  straight-line distance. Verify the output distances look reasonable.
- The full `<kml>` document needs proper XML namespace
  (`xmlns="http://www.opengis.net/kml/2.2"`) or Google My Maps rejects it.

## Verification

```bash
python3 /data/hermes/skills/productivity/maps/scripts/maps_client.py search "Statue of Liberty"
# Should return lat ~40.689, lon ~-74.044

python3 /data/hermes/skills/productivity/maps/scripts/maps_client.py nearby --near "Times Square" --category restaurant --limit 3
# Should return a list of restaurants within ~500m of Times Square

python3 /data/hermes/skills/productivity/maps/scripts/generate_kml.py \
  --hub 40.689 -74.044 "Statue of Liberty" \
  --spoke 40.758 -73.985 "Times Square" \
  --spoke 40.748 -73.985 "Empire State" \
  --mode straight \
  -o /tmp/verify.kml
# Should produce a KML with 3 pins and 2 lines with Haversine distances
ls -la /tmp/verify.kml
