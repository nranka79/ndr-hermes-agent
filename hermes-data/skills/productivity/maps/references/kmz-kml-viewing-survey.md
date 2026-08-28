# Viewing / validating a user-supplied KMZ or KML (land-survey files)

When a user uploads a **KMZ** (typically a georeferenced land survey — points,
parcel polygons, boundary edge lines) and says "I can't open / get this fixed in
Google Earth", do NOT try to open a desktop Google Earth app. You run on a
headless server with no display — that is a local action the user must take at
their end. Instead: **validate the file, reassure them it's healthy, and hand
them working, viewable alternatives** (interactive HTML map + static PNG + a
cleanly re-packaged KMZ).

## 1. KMZ = a ZIP containing doc.kml

```bash
mkdir -p kmz_extract && cd kmz_extract
unzip -o ../<file>.kmz      # produces doc.kml (the inner file is almost always named doc.kml)
wc -l doc.kml
```

A KMZ has no special magic — it is a zipped single KML document.

## 2. Validate the KML before telling the user anything

When a user says "I can't get it to open", the FIRST thing to establish is
whether the file is actually broken. A well-formed georeferenced KML validates
cleanly; an empty XML, truncated zip, or bad projection shows up immediately.

```python
import xml.etree.ElementTree as ET, re
ns = {'k': 'http://www.opengis.net/kml/2.2'}
tree = ET.parse('doc.kml')                 # raises if XML malformed
root = tree.getroot()
pm = root.findall('.//k:Placemark', ns)    # total placemarks
coords = re.findall(r'<coordinates>([^<]+)</coordinates>', open('doc.kml').read())
bad = [c for c in coords for t in c.strip().split() if len(t.split(',')) != 3]
# good if bad == [] and len(coords) == len(pm)
```

Quick structural census for the reassuring summary to the user:
- Count `<Point>`, `<Polygon>`, `<LineString>` elements → tells them how many
  survey points, parcel boundaries, and edge lines are in the file.
- Check coordinates are `lon,lat,alt` WGS84 triplets and fall in the expected
  region (e.g. ~77.58, 12.94 → Siddapura / Jayanagar, Bangalore). Verify bounds:

```python
# verify coords fall in the expected region (e.g. ~77.58, 12.94 -> Bangalore)
import re
raw = re.findall(r'<coordinates>([^<]+)</coordinates>', open('doc.kml').read())
allpts = [tuple(map(float, t.split(',')[:2])) for c in raw for t in c.strip().split()]
lons = [p[0] for p in allpts]; lats = [p[1] for p in allpts]
print('bounds:', min(lats), min(lons), max(lats), max(lons))
```

**The verdict to give the user:** if validation passes, the file is NOT
corrupted — a "won't open in Google Earth" problem is on the VIEWING side
(Google Earth not installed / file association / graphics driver / hardware
acceleration), not the data. State this explicitly; it ends the "is my file
broken?" loop and redirects effort productively.

## 3. Extract to JSON for rendering

```python
import xml.etree.ElementTree as ET, json
ns = {'k': 'http://www.opengis.net/kml/2.2'}
root = ET.parse('doc.kml').getroot()
points, polys, lines = [], [], []
for pm in root.findall('.//k:Placemark', ns):
    name = pm.find('k:name', ns); n = name.text if name is not None else ''
    pt = pm.find('.//k:Point/k:coordinates', ns)
    if pt is not None:
        p = pt.text.strip().split(',')
        points.append({'name': n, 'lon': float(p[0]), 'lat': float(p[1])})
    pg = pm.find('.//k:Polygon', ns)
    if pg is not None:
        c = pg.find('.//k:outerBoundaryIs/k:LinearRing/k:coordinates', ns)
        if c is not None:
            polys.append({'name': n, 'ring': [[float(x) for x in t.split(',')[:2]]
                                              for t in c.text.strip().split()]})
    ls = pm.find('.//k:LineString', ns)
    if ls is not None and pt is None:
        c = ls.find('k:coordinates', ns)
        if c is not None:
            lines.append([[float(x) for x in t.split(',')[:2]]
                          for t in c.text.strip().split()])
# bounds: min/max over all lat and all lon
```

Survey point names are revealing: land surveys carry control points like
`SI-1, SI-2, SI-3, SI-5` (georeference anchors) plus sequentially numbered
boundary points (`1..47`). Name prefixes matter — keep them.

## 4. Two viewable deliverables

### (a) Interactive Leaflet HTML (self-contained, works in ANY browser)
No Google Earth needed. Grab Leaflet from unpkg CDN, embed the extracted JSON
(`const data = __DATA__;` then string-replace `__DATA__` with `json.dumps(data)`),
and add layers:
- points → `L.circleMarker` + a `L.divIcon` HTML label for the number/SI code
  (avoid clobber: offset labels by `(count[name] % 3) * 9` px to stop duplicate
  numbered points overprinting)
- polygons → `L.polygon` with semi-transparent fill, distinct `hsl()` colors
- lines → `L.polyline`
- `zoomToAll()` via `map.fitBounds([[lat_min,lon_min],[lat_max,lon_max]])`

Toggles for each layer are nice-to-have. ~3,400 placemarks embeds as ~2.2 MB
HTML — fine to send. Deliver as `MEDIA:<path>` in Telegram.

### (b) Static PNG (matplotlib + OSM raster tiles)
For a screenshot-style preview the user can see inline, downsize to the
interesting zoom and render tiles onto a matplotlib axis:

```python
# tile bbox (mind y-flip: north tile has SMALLER y, but compute both then min/max)
def deg2num(lat, lon, z):
    n = 2.0**z
    xt = int((lon+180)/360*n)
    yt = int((1 - math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n)
    return xt, yt
x0, y_north = deg2num(lat_max, lon_min, z)
x1, y_south = deg2num(lat_min, lon_max, z)
x0, x1 = min(x0,x1), max(x0,x1)
y0, y1 = min(y_north,y_south), max(y_north,y_south)   # <-- always min/max; south/north order is not obvious
# stitched OSM tile: big = Image.new('RGB',(W,H)); paste each tile; imshow(big, origin='upper')
# geo->px: px = (tilex - x0)*256, py = (tiley - y0)*256 with tilex/tiley from deg2num (float)
```

Fetch tiles from `https://tile.openstreetmap.org/{z}/{x}/{y}.png` with a
normal `User-Agent` header.

**PITFALL — tile y-ordering:** computing the tile range from north and south
edges can return `y0 > y1` numerically (or look flipped). ALWAYS take
`min/max` of the north and south tile rows before looping, or you get a
negative-sized canvas (`Width and height must be >= 0`) or a blank strip.

**PITFALL — matplotlib needs install on this box:** no matplotlib in system
python. Use a throwaway venv:
```bash
uv venv /tmp/mapenv --python python3
uv pip install --python /tmp/mapenv/bin/python matplotlib
/tmp/mapenv/bin/python render.py
```
(`uv pip install --python` targets the venv; plain `pip install` inside the
venv silently misses. Verify with `import matplotlib`).

Install matplotlib in the venv, then run the render from it. Verify the PNG
with vision_analyze — confirm the points/polygons actually sit on the map and
align with streets before sending.

## 5. Re-package a clean KMZ for Google Earth

```bash
zip -j -9 <name>_fixed.kmz doc.kml   # -j: strip paths so inner file is at zip root
```
Google Earth accepts a KMZ whose inner file is a valid `doc.kml`. Send this so
the user has a fresh copy to double-click even if their original got mangled in
transit.

## 6. Communication (the headless constraint)

Never pretend you opened the desktop app. Say plainly:
- **You cannot launch the Google Earth desktop app for them** (headless server, no display).
- The file is **valid** (give the counts: X points, Y boundaries, Z edges).
- Offer the HTML/PNG preview as "works right now in any browser".
- For their Google Earth: install Google Earth Pro (free), File → Open → select
  the .kmz, or double-click it (file association). If it crashes/whitescreens,
  it's usually the graphics driver → disable hardware acceleration under
  Tools → Options → 3D View.
- Offer downstream conversions the survey might need: DXF/Shapefile/GeoJSON
  (AutoCAD/QGIS), areas/perimeter, or a coordinate table.

## Reference: full working script location
The rendered artifacts from the Aug-2026 Siddapura run live in
`/data/hermes/document_cache/kmz_extract/` (doc.kml, data.json, view_map.html,
survey_preview.png) — copy and adapt that recipe for the next survey.
