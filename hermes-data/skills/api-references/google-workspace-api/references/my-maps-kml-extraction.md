# Google My Maps — KML Data Extraction

Extract all marker data (names, coordinates, descriptions) from a Google My Maps layer set by exporting as KML. Useful when you need precise coordinates for location links, need to batch-process marker data, or the My Maps web UI is too slow for 50+ markers.

## Workflow

### Step 1: Get the My Maps MID

The MID is the `mid=` parameter in the My Maps URL:
```
https://www.google.com/maps/d/edit?mid=1kac9GDDN-uA_G01mx1qcAJijJRIcgiA&usp=sharing
                                mid=^--- THIS VALUE -------------------------^
```

### Step 2: Download KML via curl

```bash
curl -sL "https://www.google.com/maps/d/kml?mid=1kac9GDDN-uA_G01mx1qcAJijJRIcgiA&forcekml=1" -o projects.kml
```

The `forcekml=1` parameter ensures all layers are included in a single file.

### Step 3: Parse with Python

```python
import xml.etree.ElementTree as ET

tree = ET.parse('/tmp/projects.kml')
root = tree.getroot()
ns = {'kml': 'http://www.opengis.net/kml/2.2'}

projects = []
for folder in root.findall('.//kml:Folder', ns):
    layer_name = folder.find('kml:name', ns)
    layer_name = layer_name.text if layer_name is not None else "Unknown"
    
    for placemark in folder.findall('kml:Placemark', ns):
        name = placemark.find('kml:name', ns)
        name = name.text.strip() if name is not None and name.text else "Unnamed"
        
        desc = placemark.find('kml:description', ns)
        desc_text = desc.text if desc is not None else ""
        
        # Get coordinates
        coords = placemark.find('.//kml:coordinates', ns)
        coords_text = coords.text.strip() if coords is not None else ""
        
        # For point markers, first line is the coordinate
        first_coord = coords_text.split('\n')[0].strip().split(',')
        lon, lat = "", ""
        if len(first_coord) >= 2:
            lon = first_coord[0].strip()
            lat = first_coord[1].strip()
        
        # For polygon markers, calculate centroid
        all_coords = coords_text.strip().split()
        if len(all_coords) > 1:
            lats = [float(c.split(',')[1]) for c in all_coords if len(c.split(',')) >= 2]
            lons = [float(c.split(',')[0]) for c in all_coords if len(c.split(',')) >= 2]
            if lats and lons:
                lat = str(sum(lats) / len(lats))
                lon = str(sum(lons) / len(lons))
        
        # Extract URLs from description (for image links or source URLs)
        import re
        urls = re.findall(r'https?://[^\s<>"\']+', desc_text)
        
        projects.append({
            'layer': layer_name,
            'name': name,
            'lat': lat,
            'lon': lon,
            'urls': urls,
            'desc_preview': desc_text[:200]
        })
```

### Step 4: Generate Google Maps links

```python
for p in projects:
    if p['lat'] and p['lon']:
        maps_url = f"https://www.google.com/maps?q={p['lat']},{p['lon']}"
        print(f"{p['name']}: {maps_url}")
```

This creates a direct `https://www.google.com/maps?q=lat,lon` link that opens Google Maps centered on that exact coordinate. Works on both desktop and mobile.

## Coordinate extraction details

| Marker type | Coordinate extraction | When to use |
|-------------|---------------------|-------------|
| **Point** (`<Point>`) | Single pair from `<coordinates>` | Individual location pins |
| **Polygon** (`<Polygon>`) | Centroid (average of all vertex coords) | Area boundaries, site outlines |
| **LineString** (`<LineString>`) | Midpoint or first point | Road/path markers, route maps |

For polygons, the centroid approach gives a rough center point. For large polygons (e.g., a 50-acre site), the centroid is usually close enough for a `maps?q=lat,lon` link that shows the area.

## Known pitfalls

- **Force download not always needed:** Without `forcekml=1`, the KML only includes layers visible in the current viewport. Add it to guarantee all data.
- **Polygon coordinate winding:** Google My Maps exports polygons with the first and last coordinate being identical (closed loop). The centroid calculation handles this correctly.
- **No coordinates for collapsed layers:** If a layer is collapsed in the UI, its markers still appear in the KML — the KML exports all data regardless of UI state.
- **Description HTML:** The KML `<description>` is HTML-encoded (may contain `<img>` tags, line breaks as `<br>`). Strip tags with `re.sub(r'<[^>]+>', '', desc_text)` for plain text.
- **Cache concerns:** The KML endpoint returns currently published data. If the map was edited seconds ago, wait a moment for the KML to reflect changes.

> **Companion reference:** See [`my-maps-kml-modification-and-upload.md`](my-maps-kml-modification-and-upload.md) for adding descriptions (with highlighted prices) to placemarks and the current update-workflow landscape.
