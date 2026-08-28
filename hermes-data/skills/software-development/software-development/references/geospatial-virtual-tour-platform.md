# Geospatial Drone + Ground Imagery Virtual Tour Platform

**Context:** User (Bharat/Nishant) wants to build a self-hosted platform similar to digitour.housing.com for showcasing real-estate projects via drone footage and 360° ground imagery. Reference site: `https://digitour.housing.com/droneview/ranka_oasis`

**Reference site analysis:** Fully reverse-engineered via curl + source inspection. Complete architecture documented in `/data/hermes/users/ndr/drone_platform_llm_prompt.md` (35KB, full LLM prompt document).

---

## Reference Site Architecture

**Engine:** Pano2VR 7.0.2 Pro (commercial, Garden Gnome Software). NOT open-source, NOT custom WebGL.

**CDN:** AWS CloudFront (`daecrzzg3cbmx.cloudfront.net`), project ID `6a14255f25ca0a31f3105a4c`

**Asset structure:**
```
https://daecrzzg3cbmx.cloudfront.net/prod/droneview/{projectId}/{version}/
  ├── pano.xml              # Panorama config + hotspots
  ├── pano.json             # Inventory data (access denied externally)
  ├── pano2vr_player.js     # Viewer engine
  ├── skin.js               # Custom UI skin (.ggsk compiled)
  └── tiles/{nodeId}/
        └── l_{level}/c_{x}_r_{y}.jpg   # 510×510px tiles, 4 LOD levels
```

**Tile pyramid per node:**
- Level 0: 375×375 px (preview)
- Level 1: 750×750 px
- Level 2: 1500×1500 px
- Level 3: 3000×3000 px (full)

**Geolocation in XML:**
```xml
<userdata latitude="13.317018" longitude="77.609233" altitude="1011.57" title="Day - 22nd Floor" />
```

**Two hotspot types:**
- **Point hotspots** — compass markers with pan/tilt/description (e.g., amenity POI at distance)
- **Polyhotspot** — floor plan polygon overlay with vertex array in panorama angle space

**Inventory mode:** `sessionStorage.setItem('isInventoryView', 'true')` toggles view; dropdown populated from polyhotspot IDs

**UI:** jQuery 1.11 + custom CSS + Font Awesome 5 + custom icomoon subset (~80 amenity icons)

---

## Open-Source Alternative Stack

| Layer | Recommendation | Notes |
|---|---|---|
| Panorama viewer | **Marzipano** (BSD) or **Pannellum** (Apache 2) | Both pure WebGL, tile pyramid support |
| 3D / KML overlay | **three.js** | Sprite-based 3D placemarks |
| Map base layer | **Leaflet** (minimap) + **MapboxGL** (satellite fallback) | |
| KML parsing | **kmlexport.js** or **togeojson** | Browser-side, no deps |
| Tile CDN | AWS S3 + CloudFront | Same as reference |
| Backend | Node.js + Express + PostgreSQL | |
| State | Zustand (React) or pinia (Vue) | |
| Build | Vite | |

---

## Key Files

- Full LLM prompt (35KB): `/data/hermes/users/ndr/drone_platform_llm_prompt.md`
- Reference HTML source: fetchable via `curl -L -A "Mozilla/5.0" https://digitour.housing.com/droneview/ranka_oasis`
- Reference pano.xml: `curl -L -A "Mozilla/5.0" https://daecrzzg3cbmx.cloudfront.net/prod/droneview/6a14255f25ca0a31f3105a4c/1/pano.xml`
- Reference skin.js + pano2vr_player.js: same CloudFront path

---

## Critical Pitfalls

1. **Tile URL pattern in reference uses `%c` (column) placeholder** — GDAL `gdal2tiles` uses `c_{x}_r_{y}` pattern. Always verify tile naming convention against the actual server response before building the viewer.
2. **Polyhotspot vertices are in PANORAMA angle space (pan/tilt degrees), not geographic lat/long.** Requires homography transform to project geographic polygons onto panorama.
3. **pano.json endpoint is access-denied** in reference (likely auth-gated for inventory data). Build auth or accept it as admin-only endpoint.
4. **XEF format** — DJI drone software XEF structure confirmed; other vendors may use different schema. Always verify against actual export before building parser.