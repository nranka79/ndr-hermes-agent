# Google My Maps — KML round-trip, layer reorganization & pin verification

DRAAS real-estate research workflow (Prakash). My Maps has **NO public edit API** — pins/layers cannot be moved programmatically. The reliable path is a KML/KMZ round-trip: export → parse → verify → rebuild → user imports. Say this up front; don't imply you can edit the live map.

## Workflow

1. **Export**: `curl -sL "https://www.google.com/maps/d/kml?mid=<MID>&usp=sharing"` returns a **KMZ** (zip, magic `PK`). Unzip → `doc.kml`. No auth needed for link-shared maps.
2. **Parse**: regex `<Folder>.*?</Folder>` then `<Placemark>.*?</Placemark>` per folder. Strip `<![CDATA[...]]>` then `html.unescape`. Coordinates are `lon,lat,0` — **lon first**. The description text carries the semantic fields: `Type: apartment|villa|plot`, `Category: school|college|hospital|metro|rail|techpark|sez|industry|mall|hotel`, `Locality:`, `From subject: X km`, `Link:` (99acres URL with locality slug).
3. **Verify placement** (ladder below) — the step users care most about ("verify each marking, place at the right point").
4. **Rebuild**: one `<Folder>` per target layer, one `<Style>` per layer using Google pushpin icons `https://maps.google.com/mapfiles/kml/pushpin/<color>-pushpin.png` (org, purple, blue, red, ylw, grn, dkblu, ltblu, brwn, pink, dkred). Zip `doc.kml` as `.kmz`.
5. **Deliver** `MEDIA:/path/...kmz` + import instructions: open map → **Add layer → Import** → upload KMZ → delete old layers. Each KML folder becomes one layer on import.

## Pin-placement verification ladder

1. **Distance-ring check**: haversine(marker, subject) vs stated "From subject: X km". Matching proves only internal consistency (right ring), NOT the right place on that ring.
2. **Locality/direction check**: compare marker vs known locality centers; flag label-vs-coordinate conflicts (label "Anekal", coords 40 km NW).
3. **99acres slug check**: URL slug is the listing locality (`-marsur-`, `-iggalur-`, `-begihalli-`). Geocode slug, compare. CAUTION: slugs like `anekal` are **taluk-level** and Nominatim often resolves them to a wrong point — slug mismatches are *candidates*, not verdicts.
4. **Deep-verify only the flagged few**: `web_search` name + locality for RERA/developer/portal address evidence. Nominatim handles villages/landmarks but fails on small Indian project names. **Google Maps place search is ground truth**: `browser_navigate` `https://www.google.com/maps/search/?api=1&query=<name+locality>` then `browser_console` `window.location.href` → read `@lat,lng` or `3d<lat>!4d<lng>`. Same-name villages resolve differently across geocoders — confirm disputed pins with the Maps place URL.

## Pitfalls (all hit in real sessions)

- **lon,lat order in KML** — verification regexes assuming lat,lon falsely "fail" correct data. Parse lon,lat, compare against (lat,lon) expectations explicitly.
- **Name matching**: pin names carry price suffixes (`"Green Avenue | ₹3,670"`); substring collisions happen (`"Paramount Green Avenues"` contains `"Green Avenue"`). Clean prefix `name.split('|')[0].strip()`, exact or `startswith(prefix + ' ')`.
- **XML escaping**: escape `&` in doc/layer names (`&amp;`); unescaped `&` in `<name>` invalidates the whole KMZ (ElementTree ParseError line 4). Validate `ET.fromstring(doc)` before delivering.
- **User-imported maps drop layers**: verify the imported map's layer set against what you delivered (4 Industry pins silently missing in one session). Restore from the original source KML and re-emit.
- **Update descriptions when moving pins**: rewrite `Locality:` and recompute `From subject: X km`; stale text makes corrected pins look wrong.
- Keep subject / proposed-land reference pins in their own `Subject & Distances` layer; don't merge into project layers.
- Apify google-places and Firecrawl may be out of credits on the DRAAS account — prefer Nominatim + Google Maps place search via browser for geocoding; don't block the job on paid geocoders.

## Worked example — Bestamanahalli map (2026-08)

Source map had 4 layers: Untitled (Proposed Land), Competitor Projects (94), Social Infrastructure (44), Subject. Target 11 layers:
`Projects — Apartments / Villas / Plotted`, `Infra — Schools / Colleges / Hospitals / Metro & Rail / Tech Parks & SEZ / Industry & Industrial Areas / Retail & Hotels`, `Subject & Distances (reference)`.

Round 1 (first map): 4 pins moved (Whitewinds Aadya Heights → Budigere Cross 13.0462,77.7504; SLN Homes → Chandapura–Anekal Rd 12.8009,77.7115; Sri Rama Enclave Ph3 → Haldenahalli Anekal 12.7177,77.7084; Bestamanahalli gated plots → subject village 12.72834,77.72403) + 2 locality label fixes (VRR Green Crest → Electronic City; Shriram WYT Field → Whitefield/Budigere). Verified via 99acres, Commonfloor, RERA, developer sites.

Round 2 (user re-imported into new map, new mid): 8 more moved after deep geocoding:
- Green Avenue → Gudnahalli, Anekal 12.6896,77.7198 (was 12.9710,77.7108, North B'lore — Google Maps place URL)
- Nandi Garden → Haldenahalli, Anekal 12.7162,77.7081 (was 12.7919,77.5554, far west)
- Elegance The Roots → Chikkanagamangala, Anekal 12.8565,77.6928 (was 12.8397,77.5711, Kengeri side; 99acres address "Survey No. 98, Chikkanagamangala")
- Royaal Vasundhara Enklev → Begihalli, Anekal 12.7951,77.6147 (was 12.9065,77.5170, Magadi Rd side; slug `begihalli`)
- Mahendra Solterra Aarya → Andapura, Anekal 12.8252,77.7048 (Nominatim "Mahendra Solterra - Aarya Phase 2, Andhapura")
- Electronic City Phase 1 → center 12.8497,77.6650 (was edge 12.8394,77.6378; Nominatim "Electronics City Phase 1")
- Tapasya PU College Attibele → Tapasya Degree & PUC, Chandapura 12.8008,77.7055 (was 12.9694,77.4077 — 43 km away, wrong campus; Google Maps place URL)
- Ecospace Ecity → RMZ Ecospace, Bellandur ORR 12.9279,77.6770 (was 12.9738,77.5963, 30 km NW; web: RMZ Ecospace Bellandur)

Also restored 4 industry pins (Biocon Bommasandra 12.8188,77.6613; Bommasandra Industrial Area 12.8118,77.6584; Jigani Industrial Area 12.7990,77.6624; Attibele Industrial Area 12.7820,77.7377) that vanished in the user's re-import.

Layer count check: 140 pins total across 11 layers (25 plotted + 11 villas + 58 apartments + 2 subject + 10 techparks/sez + 5 metro/rail + 8 hospitals + 6 colleges + 8 schools + 3 retail/hotels + 4 industry).

Note: "rowhouses" layer requested by user, but source data only had apartment/villa/plot types — don't create empty layers; state the data doesn't contain that type.
