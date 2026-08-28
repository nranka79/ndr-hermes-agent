# Overpass API — Custom POI Queries

When the user asks for a POI type not in the 46 predefined `nearby` categories,
query OpenStreetMap directly via the Overpass API. This file documents common
patterns and real-world examples.

## Base URL

```
https://overpass-api.de/api/interpreter
https://overpass.kumi.systems/api/interpreter  (fallback mirror)
```

## Common Query Template

```sql
[out:json][timeout:25];
(
  node["KEY"="VALUE"](around:RADIUS_M,LAT,LON);
  way["KEY"="VALUE"](around:RADIUS_M,LAT,LON);
);
out center 20;
```

Replace `KEY=VALUE` with the OSM tag. `around` filters by radius in metres
from lat/lon. `out center` gives centroid for ways. The number at the end
is max results.

## OSM Tags for Common Missing Categories

| User wants | Overpass tags |
|---|---|
| Barber / Hair salon | `shop=hairdresser`, `shop=barber`, `shop=beauty` |
| Men's salon | `shop=hairdresser` (check name for "Men") |
| Pet store | `shop=pet` |
| Optician | `shop=optician` |
| Tattoo studio | `shop=tattoo` |
| Vape / Tobacco | `shop=tobacco` |
| Dry cleaner | `shop=dry_cleaning` |
| Repair shop | `shop=repair` |
| Electronics store | `shop=electronics` |
| Furniture store | `shop=furniture` |
| Mobile phone repair | `shop=mobile_phone`, `craft=electronics_repair` |

## Barbers — Full Worked Example

**User request:** "Find a hygienic barber near Embassy Habitat, Vasanth Nagar, Bangalore"

**1. Geocode reference point:**
```bash
python3 /data/hermes/skills/productivity/maps/scripts/maps_client.py search "Embassy Habitat Vasanth Nagar Bangalore"
# → 12.9945, 77.5877
```

**2. Overpass query for all hair/beauty shops within 1km:**
```sql
[out:json][timeout:25];
(
  node["shop"="hairdresser"](around:1000,12.9945,77.5877);
  way["shop"="hairdresser"](around:1000,12.9945,77.5877);
  node["shop"="barber"](around:1000,12.9945,77.5877);
  way["shop"="barber"](around:1000,12.9945,77.5877);
  node["shop"="beauty"](around:1000,12.9945,77.5877);
  way["shop"="beauty"](around:1000,12.9945,77.5877);
);
out center 30;
```

**3. Python processing (extract + calculate walking distance):**
```python
import json, urllib.request, urllib.parse, math

query = """
[out:json][timeout:25];
(
  node["shop"="hairdresser"](around:1000,12.9945,77.5877);
  way["shop"="hairdresser"](around:1000,12.9945,77.5877);
  node["shop"="barber"](around:1000,12.9945,77.5877);
  way["shop"="barber"](around:1000,12.9945,77.5877);
  node["shop"="beauty"](around:1000,12.9945,77.5877);
  way["shop"="beauty"](around:1000,12.9945,77.5877);
);
out center 30;
"""

url = "https://overpass-api.de/api/interpreter"
data = urllib.parse.urlencode({"data": query}).encode()
req = urllib.request.Request(url, data=data,
    headers={"User-Agent": "HermesAgent/1.0"})
with urllib.request.urlopen(req, timeout=25) as resp:
    result = json.loads(resp.read().decode())

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

ref_lat, ref_lon = 12.9945, 77.5877
places = []
for e in result.get("elements", []):
    t = e.get("tags", {})
    lat = e.get("lat") or e.get("center", {}).get("lat")
    lon = e.get("lon") or e.get("center", {}).get("lon")
    dist = haversine(ref_lat, ref_lon, lat, lon)
    places.append({
        "name": t.get("name", "(unnamed)"),
        "type": t.get("shop", ""),
        "phone": t.get("phone", ""),
        "hours": t.get("opening_hours", ""),
        "address": f"{t.get('addr:street','')} {t.get('addr:housenumber','')}".strip(),
        "dist_m": round(dist),
        "walk_min": round(dist * 1.3 / 80),
        "lat": lat,
        "lon": lon,
        "maps_url": f"https://www.google.com/maps/search/{urllib.parse.quote(t.get('name',''))}/@{lat},{lon},17z"
    })

places.sort(key=lambda p: p["dist_m"])
print(json.dumps(places, indent=2))
```

**4. Filter to quality candidates:** Skip unnamed entries (small local shops).
Prioritise named chains (Naturals, Jawed Habib, Toni&Guy, Green Trends) for
hygiene standards. Call to confirm men's haircut pricing.

**5. Present with direction links** so the user can check photos/reviews themselves
if web tools are unavailable:
```
**{Name}**
📍 Address | 🚶 ~{N} min walk
📞 {Phone} | 🕐 {Hours}
🔗 {Google Maps direction link}
```

## Alternate Fallback: Use Python Requests via execute_code

If terminal or curl encoding is fiddly (Overpass POST body needs careful escaping),
use `execute_code` which handles encoding automatically via `urllib.parse.urlencode`.

## Overpass Quota / Rate Limits

- Default timeout: 25s (increase to 30-60 for complex queries over large areas)
- Max `out` elements: ~50k per query
- Rate limit: soft — one query at a time is fine; burst of 3+ may get throttled
- If both mirrors return 504/408, the Overpass instance is under load — retry
  after 10-15s or reduce the radius/query complexity
