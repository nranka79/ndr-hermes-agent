# MyMaps KML Delivery + Indian Real-Estate Geocoding Ladder

How to deliver a Google My Maps to the user without logging into Google: build a KML where **each `<Folder>` becomes one My Maps layer**, user imports at mymaps.google.com → Create new map → Add layer → Import.

## KML structure
- `<Document>` → one `<Folder>` per requested layer (e.g. 1. Proposed land, 2. Grade A commercial, 3. Key developments, 4. Upcoming infra) → `<Placemark>` per pin.
- Land parcel: `<Polygon>` ring (close it by repeating the first point). Road corridor: `<LineString>` with `<tessellate>1</tessellate>`.
- Put rich data in `<description><![CDATA[...]]></description>` (specs, rents, tenants, source links).
- Per-placemark `<Style>` with `<IconStyle>` color (aabbggrr hex) + pushpin icon; different color per layer.
- Optionally add a final reference folder (e.g. the road corridor polyline) with `<open>0</open>`.

## Pitfalls
- **Escape `&` in every name/description** (the `<name>` of the Document counts) — unescaped `&` makes the whole KML unparseable. Validate with `xml.etree.ElementTree.parse` before delivering.
- Label pins with haversine distance from the site (km) in the name or description — users read the map without opening every pin.
- Flag uncertain pins `[approx — verify]` instead of silently presenting them as exact.

## Geocoding ladder for Indian real-estate POIs (most miss in Nominatim)
1. **Nominatim** (`search?format=json&limit=1&q=...`, 1 req/s) — works for hospitals, malls, tech parks with recognizable names.
2. **Wikipedia/Wikidata coords API** for metro stations and govt infrastructure — reliable (`action=query&prop=coordinates&titles=A|B|C`).
3. **Overpass API** with name-regex in a bbox — catches OSM-tagged private projects (`nwr["name"~"RMZ NXT|Prestige White Meadows|...",i](bbox); out center;`). Note: use `el.get("lat") or el.get("center", {}).get("lat")` because ways return center.
4. **Google Maps via the real browser** for verification of the critical few.
5. Otherwise place at a known neighborhood anchor and mark approx.

## Geocoder garbage detection (critical)
- geocode.xyz throttles quickly and then returns the SAME city-centroid for every query — discard results that are identical across different queries or that aren't the named project.
- Nominatim/geocode can return wrong-city matches: "Shriram One City" → Shriram Hebbal (North BLR); "Sattva Knowledge City" → Chennai campus. Verify the `display_name`/city before trusting.
- Google Maps place pins themselves can be corrupt (Shriram One City pinned at lon 79.97°E). Don't trust any single source; cross-check against the project's known corridor.
- Knowledge-base lists from subagents are frequently wrong about location ("Assetz 63 East on Whitefield-Hoskote Rd" was actually Sarjapur Rd; "Prestige Lakeside Habitat near site" was actually Varthur ~11 km away). Always geocode/verify before drawing conclusions about proximity.
