# Geocoding Methodology — How Playwright geocodes a project name (Aug 2026)

Why pins go off and how the geocoder actually works. Asked for by Nishant
explicitly ("explain how you use playwright to get the geocode for any
project name") after several pins on the NorthStar KML were visibly wrong.

## Coordinate resolution priority (per property-rd §4)

1. **Map link on the project's own page** — builder/portal pages embed a
   Google Maps link; `coords_from_urls.py` extracts @lat,lon / q=lat,lon /
   !3d!4d / maps.app.goo.gl.
2. **Apify Places crawler** — ALWAYS with `locationQuery` + `countryCode`;
   unanchored runs wander to the wrong city; town anchors give silent
   zero-result traps; use city anchor + `searchMatching: all` + post-hoc
   Haversine filter.
3. **Playwright headless batch** — the fallback that resolves most misses.
4. No coords after all three → sheet-only row, NOT pinned on KML, reported.

## How the Playwright step works (the part Nishant asked about)

`maps` skill `geocode_batch_subproc.py`, run with `/opt/data/.venv` +
chromium headless shell:

- **Fresh browser context per query.** Google Maps rate-limits a single
  browser session after ~2 map queries (blank maps / consent walls).
  A fresh context per query resets that. Cost: ~10 s per point.
- Set Google consent cookies (CONSENT/SOCS) first so the page clears the
  cookie wall.
- Navigate to `google.com/maps/search/<project name> + <locality> +
  <city>`. The **locality qualifier is mandatory** — passed as argv[3]
  (the script's baked default is Devanahalli; running other belts without
  the arg wrong-resolves them).
- Wait for map settle, read coords from the URL — Google encodes the
  resolved map centre as `@lat,lng,zoom`.
- Close context, next point.

## Why pins go off (validated failure modes)

| Failure mode | Example | Mitigation |
|---|---|---|
| Same-name pollution | "Embassy Grove" → Kodihalli/Old Airport Rd (NOT Yelahanka); Adarsh Tropica=Sarjapur; Birla Tisya=Rajajinagar | locality-qualify; filter 15+ km rows with retry |
| Google resolves wrong instance | Bagmane Sierra Yelahanka → OLD Bagmane Tech Park near HAL airport (12.98, 77.66); no official pin for new campus | manual pin 13.1183, 77.5991 marked approx |
| Under-construction not on Maps | new launches return nearest guess or nothing | accept approx, mark as such |
| Batch headless artifact | constant **−0.002575° lon offset (~265–280 m west)** documented in design doc §2.3 | never ground truth; re-verify with Places |

## Safety net

- Post-geocode Haversine distance check from the anchor site; flag rows
  > expected radius or >2× the median distance → re-geocode with tighter
  locality queries.
- Distance checks catch pins in the WRONG PLACE outside the radius, but
  NOT pins inside the radius in the wrong spot (e.g. Embassy Grove pinned
  15 km away was caught; a pin that lands inside 10 km but on the wrong
  locality would not be). After any big geocode run, spot-check visually.
- Nominatim (OSM) first pass is cheap and free but only ~17% hit rate for
  Indian project names (schools/projects absent from OSM) — Google Maps is
  the authority for project names.
- VPS is RAM-constrained (~3.7 GB) — no parallel browser contexts; run
  sequential fresh-context-per-query or you get OOM/EPIPE.
