# Attendance Geo-Location Troubleshooting — Session Notes (Jul 2026)

## Context

Bharat H (sales1.blr@draas.com) reported that the Kelsa attendance sign-in link showed his location as "400+" meters away from the pinned office location, even when he selected "Cunningham Road office." This file documents the investigative technique and the root cause pattern.

## Initial Triage

1. **Find the daily attendance email in Gmail:**
   - Sender: Nishant Ranka `<ndr@draas.com>`
   - Subject: "Please sign in for the day"
   - Contains link like `https://kelsa.io/s/<shortcode>`
   - For this session: `https://kelsa.io/s/uqb3zd7zkb`
   ```
   gmail_search(query='from:ndr@draas.com attendance OR sign OR geo OR location OR checkin', max=20)
   ```

2. **Identify the Kelsa record via MCP:**
   - Pipeline 7711 (Attendance Tracker New)
   - Search: `search_leads(pipeline_id=7711, query="Bharat")`
   - Today's record naming pattern: `Bharat H-2026-07-22`
   - Record ID extracted from search results

3. **Get full record details:**
   ```
   get_lead(lead_id=53932515)
   ```
   **Current stage:** Start (not yet signed in)

## Analyzing a Previous Successful Sign-In

Get a record that's already past Sign In:

```
get_lead(lead_id=53868539)  # Bharat H-2026-07-20
```

**Key fields revealed:**
```
Login Location: Lat: 12.9894567 Long: 77.5931176
Sign in Distance: 29
Sign In Validation: true
Project Location: Hotel Chandrika, Kaverappa Layout, Vasanth Nagar, Bengaluru, Karnataka, India
Project Name: Bharat H-main office 11 cunnigham
```

The `cf_project_location` text revealed where Kelsa thinks the office is pinned. The `cf_login_location` showed where the employee's GPS actually was when they successfully signed in.

## Cross-Referencing with OpenStreetMap

Use Nominatim API to get coordinates of the Kelsa-pinned address vs actual office:

```python
import urllib.request, json
from math import radians, sin, cos, sqrt, asin

# Get Kelsa pin coordinates (from cf_project_location)
url = "https://nominatim.openstreetmap.org/search?q=Hotel+Chandrika+Vasanth+Nagar+Bangalore&format=json&limit=1"
req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0"})
data = json.loads(urllib.request.urlopen(req).read())
kelsa_lat, kelsa_lon = float(data[0]["lat"]), float(data[0]["lon"])

# Get actual office coordinates
url2 = "https://nominatim.openstreetmap.org/search?q=Ranka+Chambers+Cunningham+Road+Bangalore&format=json&limit=1"
req2 = urllib.request.Request(url2, headers={"User-Agent": "Hermes/1.0"})
data2 = json.loads(urllib.request.urlopen(req2).read())
office_lat, office_lon = float(data2[0]["lat"]), float(data2[0]["lon"])

# Haversine distance
R = 6371000
dlat = radians(kelsa_lat - office_lat)
dlon = radians(kelsa_lon - office_lon)
a = sin(dlat/2)**2 + cos(radians(office_lat)) * cos(radians(kelsa_lat)) * sin(dlon/2)**2
c = 2 * asin(sqrt(a))
print(f"Distance between pin and office: {R * c:.0f}m")
```

## Pattern Found

For this specific case:
| Item | Coordinates | 
|------|------------|
| **Kelsa pin** (Hotel Chandrika, Millers Road) | 12.9896641, 77.5928185 |
| **Actual office** (Ranka Chambers, 31 Cunningham Road) | 12.9852331, 77.5961299 |
| **Distance between pin and office** | **609m** |
| **Bharat's sign-in GPS (Jul 20)** | 12.9894567, 77.5931176 |
| **Sign-in GPS vs Kelsa pin** | **40m** ✅ (close enough) |
| **Sign-in GPS vs actual office** | **572m** ❌ |

**Root cause:** The office pin in Kelsa is set to **Hotel Chandrika** (a nearby landmark), not the actual DRAAS office at Ranka Chambers. Employees at the actual office are 500-600m from the pin. Previously working sign-ins (29m distance) happened because the employee was physically near the Hotel Chandrika pin location when they signed in.

## Presentation to Employee

Give the employee:
1. The exact coordinates of both locations
2. The distance between the pin and actual office
3. Why it worked before (they were near the wrong pin) and why it fails now (poorer GPS lock, different spot)
4. Three options:
   - **Fix the pin** — update `employee_location_mapping` / `dra_projects` master coordinates to actual office
   - **Phone GPS fix** — enable High Accuracy, retry near the pin location
   - **Manual override** — use the "different location" option with a reason

## Technical Data (DRAAS Office - Cunningham Road)

- **Address:** Ranka Chambers, 4th floor, No. 31 Cunningham Road, Bangalore - 560052
- **OSM coordinates:** 12.9852331, 77.5961299
- **Nearby landmarks:** Hotel Chandrika (~609m north-west), Vasanth Nagar, Millers Road

## Phone GPS Accuracy — The "Approximate Accuracy" Pitfall

Even when the Kelsa pin is **correct** (pointing to the exact building where the employee is), the employee's phone may still report 400+ m distance due to **approximate location accuracy**.

**Symptom:** Employee is AT the pinned location, phone shows location permission ON, but distance reads 400-500m.

**Root cause identified by Kelsa implementation team (Anjali, Jul 2026):**
The phone is returning **network-based approximate location** instead of precise GPS coordinates. This happens when:
- Phone is in **Battery Saving** location mode (uses WiFi/cell towers only)
- GPS signal is weak indoors (concrete buildings, basement-level floors)
- Chrome cached a stale approximate location and hasn't re-acquired GPS
- The phone is stuck on a WiFi-based location that's off by several hundred meters

**Fix sequence (try in order):**
1. Check phone location mode → set to **High Accuracy** (GPS + WiFi + Mobile Networks)
2. **Toggle location OFF then ON** → this forces GPS to re-acquire
3. **Close and reopen Chrome** completely (killing cached location data)
4. **Switch between WiFi and mobile data** → changes the network-assist source
5. **Step to an open area / near a window** → GPS locks better with sky visibility
6. If nothing works → Kelsa implementation team (Anjali confirmed they can adjust GPS tolerance/radius server-side) — ask them to check the "approximate accuracy" tolerance setting for that employee's location mapping

**Key insight:** When the employee reports "distance is 400+" but is adamant they're at the correct location, DO NOT assume the pin is wrong. First check whether the phone is using approximate vs precise GPS. The implementation team's diagnosis in this case was "your phone is still taking approximate accuracy of the pin location" — meaning the phone, not the pin, was the culprit.
