# Session lessons: Aug 2026 Thylagere competitor expansion (geocode + radius)

Working notes from the Devanahalli competitor expansion run. These are
portable lessons for any "expand competitor coverage around project X"
task, regardless of which tooling skill executes it.

## Pipeline order that avoids the radius trap

area search → dedupe vs existing sheet (strip locality suffixes first) →
classify NEAR/FAR by URL locality → geocode → apply radius filter → THEN
append sheet + KML.

Rows appended WITHOUT coordinates bypass the vicinity filter entirely
(no lat/lon = no distance check). When a later geocode pass resolves
them, some land OUTSIDE the intended radius — observed: Konig Pearl
County resolved to 12.5 km from the Thylagere anchor (13.3216384,
77.6789048) when the cutoff was 10 km. If no-coords rows are already in
the sheet, run the distance check on each new geocode and flag
out-of-radius ones to the user.

**The URL-locality NEAR classification barely predicts true radius.**
In the Aug-2026 pass, 29 previously-ungeocoded rows were classified NEAR
by portal-URL locality (Devanahalli/Yelahanka/north-Bangalore strings).
Once geocoded via headless Google Maps: 28/29 resolved, but only **2/29
landed inside the 10 km radius** (Prestige Gardenia Estate 4.6 km,
Arvind The Park 6.5 km). The other 26 resolved at 10–35 km (Arvind
Orchards 23 km, Srk The Roots 25 km, Hollywood Town 31 km, Manyata
Silversprings 35 km). Takeaway: do NOT treat a no-coords row as
in-radius just because its listing URL says Devanahalli — locality names
on portal URLs cover a wide region. Either geocode BEFORE the sheet
append, or expect to trim the majority of late-geocoded rows.

**Sheet/KML split decision when late geocodes arrive (validated
pattern):** fill GPS lat/lon + Maps link for ALL resolved rows in the
sheet (data completeness — they're already appended), but add ONLY the
in-radius pins to the KML (the map is scoped to the 10 km vicinity;
26 far-away pins would clutter it). Then present the user with the
out-of-radius list and offer: keep as a "North Bangalore 10–35 km"
section, trim to strict radius, or leave as-is.

## 99acres area-search records embed NO coordinates

The `searchUrls[]` area-search scraper returns project names, prices,
localities, URLs — but no lat/lon. Geocoding must come from a separate
pass. Options, in order of reliability for rural plotted developments
(Devanahalli/Nandi belt):
1. maps-skill headless Google Maps batch geocoder
   (geocode_batch_subproc.py + geocode_one.py — resolves private/gated
   communities that OSM/Nominatim has zero coverage for)
2. Apify google-places crawler WITH `locationQuery` anchor

**How to get the area-search dataset (2026-08-03 validated):** the
`magicbricks-99acres` preset with plain city names returns scattered
listings and misses many projects. Use the 99acres projects-search
scraper with locality-first `searchUrls[]` instead — e.g.
`https://www.99acres.com/property-in-devanahalli-ffid/` (one URL per
locality). 134 records from 5+ locality URLs; project-name-per-record;
prices and URLs included. When the `apify_run_actor` wrapper returns
empty/failed status, drive the actor directly via the Apify REST API
(`APIFY_API_KEY` in env): POST run → poll run status → GET dataset
items. Always verify items actually match the target area — one
MagicBricks run "succeeded" with scattered unrelated Bangalore listings
(project-keyed input); locality-first search URLs fix this.

## Apify Places crawler wanders without a location anchor

A `searchStringsArray`-only run drifted to Kolkata (22.9, 88.3) and
returned irrelevant places. Always pass the anchor, e.g.
`"locationQuery": "Devanahalli, Bangalore"`. The working input format:
`searchStringsArray` + `locationQuery`; coordinates live in
`location.lat` / `location.lng` fields of the dataset.

## Batch geocode infra facts

- The batch geocoder must run with a venv python that has playwright
  (`uv pip install --python /opt/data/.venv/bin/python playwright`);
  system python3 lacks it → every name returns CRASH-noout.
- Places crawler geocode coverage is partial even when anchored: 14 of
  43 NEAR candidates resolved in one batch; the rest returned no match
  (project name not on Google Maps as searched).
- Sheet writes on this box go through the GWS client
  (`tools.gws_auth.build_service("sheets","v4",service_name="google-draas")`)
  — the run-with-socket approach is not needed.
