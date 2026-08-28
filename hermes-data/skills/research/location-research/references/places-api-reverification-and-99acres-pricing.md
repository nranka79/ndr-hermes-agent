# Places API Re-verification + 99acres Pricing (Aug 2026 battle report)

Two hard-won fixes from the Thylagere 104-POI R&D dataset. Use when a batch
geocode looks "slightly off" or when portal pricing actors return nothing.

## 1. Systematic westward longitude shift in batch geocode — diagnosis & fix

**Symptom (user report):** "points seem marginally off, shifted west by some
distance; points further from center shifted more." Every batch-geocoded
POI was ~280 m west of truth.

**Root cause:** NOT GPS precision and NOT map drift. The headless-browser
batch geocoder (Playwright + `google.com/maps/search/...?hl=en`) captured
`@lat,lon` from the page URL — but Google Maps search URLs carry the
**viewport center**, which is offset from the actual pin when the left
results sidebar is present. Magnitude at the zoom used was a constant
**−0.002575° lon ≈ 280 m west**, with **zero** latitude error. That is the
signature: constant longitude-only delta across independent points = a
pipeline extraction artifact, not geocoding error.

**How it was proven:**
- The earlier 13-competitor KML had been verified via shortlink resolution
  (Montira `13.3416197,77.6995568`, Prestige Sanctuary `77.696920`, Triton
  `77.684965`).
- Batch KML values for the same projects differed by EXACTLY −0.002575 lon.
- Google Places API re-resolution returned exactly the verified values
  (Prestige Sanctuary `77.6969201`; Harrow batch `77.618069` + 0.002575 =
  `77.620644` = Places truth).

**Diagnostic recipe:**
1. If you have ≥2 independently-verified points (shortlink-resolved),
   overlay batch vs verified and diff. A constant dLon with dLat ≈ 0 is a
   pipeline bug.
2. Re-resolve via Google Places API (below) — authoritative pin coords.
3. Never hand-apply a "+0.002575 correction" blindly: verify per point.

## 2. Re-resolving with Google Places (Apify compass/crawler-google-places)

The `apify_run_actor` tool preset `google-places` was BROKEN (returns
`Apify run None ended with status ''` with no run created). Workaround: call
the Apify REST API directly with the token from env (`$APIFY_API_KEY`):

```bash
curl -s -X POST "https://api.apify.com/v2/acts/compass~crawler-google-places/runs?token=$APIFY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"searchStringsArray":["Prestige Sanctuary Devanahalli Bangalore"],"maxCrawledPlacesPerSearch":1,"language":"en","countryCode":"in"}'
```

Then poll `/v2/actor-runs/<id>` until SUCCEEDED and fetch
`/v2/datasets/<defaultDatasetId>/items`.

**Input gotchas:**
- `countryCode` must be **lowercase** ISO-2 (`"in"`, not `"IN"`) — uppercase
  returns a 400 "allowed values" validation error.
- `maxCrawledPlacesPerSearch: 1` keeps cost tiny and each item maps to one
  search string.
- Item field `searchString` echoes your query → map results back to POIs by
  searchString key, not by order.

**Match hygiene (critical — Places returns the WRONG entity sometimes):**
- Compute title-vs-query similarity (SequenceMatcher on normalized text);
  flag ratio < ~0.55. Real case: query "SLK Software Devanahalli Bangalore"
  returned "Altimetrik India Pvt Ltd" (different company) as top hit —
  title similarity caught it (0.19). Re-ran with tighter query
  "SLK Software Devanahalli Bengaluru" → correct SLK campus `13.24372,77.71724`.
- Check lat/lon bounding box: "Phil Technologies Devanahalli Bangalore"
  returned a place in **Raipur (21.07, 82.75)** — same company name, wrong
  state. Bounding-box filter (Bangalore ~12.9–13.5, 77.4–77.9) rejects it.
  Mark genuinely unresolvable names as `lat: null` (no fabrication).
- For ambiguous companies, re-run with 2–4 query variants and
  `maxCrawledPlacesPerSearch: 2`, then pick the hit inside the box with
  best title similarity.

**Batch runner pattern (works, ~99/104 in one pass):**
- `rnd_pois_clean.json` = `[{num, name, cat, type, search}]` with junk labels
  dropped (bare "Hotel", "Villa", "€182", "Resort hotel", "Government
  Hospital" — scraped artifacts, not real POIs).
- Chunk 15 per run, save results dict after every batch (searchString key →
  `{title, lat, lng, address, categoryName}`), resume by skipping keys already
  present. Watch for per-chunk success vs full-run timeouts; poll at 12s.

## 3. 99acres pricing via codingfrontend actor (when the custom one is stale)

The account's custom `fascinating_lentil/magicbricks-99acres-property-scraper`
became stale: MagicBricks page parsed 0 records ("No records parsed from
page") and 99acres was blocked even through residential proxy. 

**Working alternative — `codingfrontend/99acres-projects-search-scraper`:**
- Input key is `searchUrls` (array) + `maxItems` + `deepScraping` (boolean —
  NOT `enableDeepScraping`; the actor rejects unknown keys). Proxy:
  `{"useApifyProxy": true, "apifyProxyCountry": "IN"}`.
- Correct URL formats (99acres changed structure; `search/project/buy/...`
  404s now):
  - Listing: `https://www.99acres.com/projects-in-devanahalli-bangalore-north-ffid`
  - Project page: `https://www.99acres.com/<slug>-npxid-rXXXXXX`
- Listing scrape returns projects with EMPTY price; **deep scrape**
  (`deepScraping: true`) on project detail URLs returns `price.min/max`
  and `displayPrice` (e.g. Prestige Sanctuary ₹6.94–11.36 Cr, Brigade Oasis
  ₹90L–1.35 Cr).
- **`deepScraping: false` output is junk for pricing**: the actor falls back
  to search-result pages — you get "Society Reviews" pages, "Location Map"
  pages, duplicate re-scrapes of the SAME known projects, and even
  wrong-city projects (observed: 10 Jaipur projects r4xxxxx from a
  Devanahalli input). Never trust a non-deep run for prices.
- **Some projects genuinely have no price even with `deepScraping: true`**
  (Sattva Park Cubix → only a "Society Reviews" page; Sumadhura Panorama →
  only a "Location Map" page; Century Seasons / Century Sports Village →
  nothing). Do NOT fabricate — report them as unpriced.
- **`area.min/max` is NULL in every deep-scrape record** — you cannot
  compute ₹/sqft from this actor's output. Price labels must carry the
  total price range ("Rs 6.94 - 11.36 Cr"); per-sqft figures, if needed,
  must come from a different source (MagicBricks project page).
- Batch ≤10 detail URLs per run; deep scrape is slow (~1–2 min each) — run
  in background with notify_on_complete.
- Poll runs sequentially, append items to a JSON accumulator after each
  batch; verify final count == expected URLs (a merge bug lost one batch).
- **Merge/dedupe pattern that works**: key the accumulator by `projectId`
  (fallback: `id`/`npxid`/`url`); when a duplicate arrives, keep the priced
  version (`displayPrice` containing Cr/L) over the unpriced one. Run each
  new batch through this merge — a naive `list.extend` double-counts and
  loses prices.
- **Attaching prices to sheet/KML rows needs an explicit ALIASES map**:
  sheet names are Google-Places labels ("Brigade Orchards", "Godrej Royale
  Woods, Devanahalli, Bangalore", "Birla Trimaya Devanahalli") while 99acres
  names are marketing names ("Brigade Orchards Laurel And Maple", "Birla
  Trimaya Phase 2"). Pure fuzzy token overlap matched only 1/13 rows. Build
  a hand-written `ALIASES = {normalized_sheet_name: normalized_99acres_name}`
  for the known pairs, then a token-overlap fallback (≥2 significant tokens,
  after stripping stopwords like devanahalli/bangalore/the/at/by/of/villa/
  plots/luxury/lifestyle/garden/county/palms/woods/city/park/view/vista).

**Other actor notes:**
- `themineworks/99acres-scraper` needs `city` field, returned rent listings
  citywide — not useful for project pricing.
- The `apify_run_actor` preset `magicbricks-99acres` maps to the custom
  (stale) actor — check actor freshness before trusting output.

## 4. Icon inventory (verified HTTP 200, symbol-verified via vision)

| Category | Icon URL (maps.google.com/mapfiles/kml/...) |
|----------|---------------------------------------------|
| Villa (house w/ $) | `pal2/icon50.png` |
| Plot (flag) | `pal4/icon21.png` |
| Subject land (red star) | `pal4/icon50.png` |
| Gated community (house) | `shapes/homegardenbusiness.png` |
| IT / data / tech | `pal4/icon10.png` (doc + magnifier) |
| Apartment building | `pal3/icon21.png` |
| College / School | `shapes/schools.png` |
| Hospital | `shapes/hospitals.png` |
| Hotel (bed) | `shapes/lodging.png` |
| Industrial / factory | `shapes/factory.png` |
| Farm land (tree) | `pal2/icon4.png` |
| DOES NOT EXIST (404) | `shapes/industrial.png`, `shapes/farm.png`, `shapes/office.png`, `shapes/colleges.png`, `shapes/universities.png` |

Palette icons (`palN/iconM.png`) can be misread from the name alone — when
you need the right symbol, download the PNGs, tile them into a grid, and
have vision describe each before mapping.

## 5. Executing Python against the research pipeline (terminal gotchas)

- **Any literal `&` in a `terminal()` heredoc/command trips the
  backgrounding guard** ("Foreground command uses '&' backgrounding") and
  the whole command is rejected. This bites twice in this workflow:
  (a) `displayPrice` strings contain `&` (price ranges like `₹6.94 - 11.36
  Cr` don't, but `Arvind The Park | ₹82.2 L - 1.23 Cr` formatting or any
  shell interpolation does); (b) Google Sheets range strings contain `&` —
  the tab is named `Listings & Sources`, so `range='Listings &
  Sources!A1:Z30'` inside a heredoc fails. Fix: use `write_file` to drop the
  Python script to /tmp, then `terminal("python3 /tmp/script.py")` — never
  pass `&` inside the shell command itself. Same for `curl -d` payloads.
- **Uploading a rebuilt KML to Drive**: use `files().update(fileId=...)`
  with `MediaFileUpload`, NOT delete+recreate — preserves the shared link.
  Mimetype `application/vnd.google-earth.kml+xml`. Full pattern in the
  `google-workspace` skill's `references/drive-update-non-google-file.md`.
