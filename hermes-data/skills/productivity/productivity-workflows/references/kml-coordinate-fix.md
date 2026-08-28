# KML Coordinate Fix for Google Maps

## Problem
KML files use `longitude,latitude,altitude` order for coordinates.
Google Maps expects `latitude,longitude,altitude` when importing KML route files.

## Symptom
Placemark points appear in the wrong location; the route line is distorted or in the ocean.

## Fix
Swap all coordinate tuples in the KML before sending to user:

```python
import re

def swap_kml_coords(content):
    def swap(match):
        inner = match.group(1).strip()
        parts = inner.split()
        new_parts = []
        for p in parts:
            segs = p.split(',')
            if len(segs) == 3:
                # lon,lat,alt → lat,lon,alt
                new_parts.append(f"{segs[1]},{segs[0]},{segs[2]}")
        return f"<coordinates>\n{' '.join(new_parts)}\n</coordinates>"
    return re.sub(r'<coordinates>.*?</coordinates>', swap, content, flags=re.DOTALL)
```

## Verification
After fix, coordinates for Ubud should look like:
- `-8.5067,115.2625,0` ✓ (latitude, longitude)
- `115.2625,-8.5067,0` ✗ (longitude, latitude — original KML format)

## Notes
- Both `<Point>` placemarks and `<LineString>` route coordinates must be swapped
- After swapping, save as `.kml` and send to user for Google Maps import
- Telegram doesn't accept `.kml` uploads — user must rename to `.xml` or paste content
