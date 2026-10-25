# Extracting GPS Coordinates & Boundary from a Drive Google My Map

**Use case:** NDR asks "get me the GPS coordinates of <project/land>". The
authoritative source is the project's **survey map stored in Drive as a Google
My Map** (`application/vnd.google-apps.map`, i.e. `...Survey` files made with
My Maps, often owned by `admin2.blr@draas.com`). External listing pages are
NOT authoritative — their embedded coordinates can be wrong.

## The technique: My Map → KML → parse (no API key needed)

Drive My Maps export as KML through a public endpoint. The file id from
`drive_list` IS the `mid`:

```bash
curl -sL "https://www.google.com/maps/d/kml?mid=<FILE_ID>&forcekml=1" -o survey.kml
```

Then parse with Python stdlib (no gws auth, no Drive download needed):

```python
import re
kml = open('survey.kml').read()
placemarks = re.findall(r'<Placemark>(.*?)</Placemark>', kml, re.S)
for pm in placemarks:
    name = re.search(r'<name>(.*?)</name>', pm, re.S).group(1).strip()
    coords_m = re.search(r'<coordinates>\s*([\d.,\s\-]+?)\s*</coordinates>', pm, re.S)
    pts = [tuple(map(float, c.split(','))) for c in coords_m.group(1).strip().split()]
    print(name, len(pts), 'pts', 'first:', pts[0][0], pts[0][1])
```

`<coordinates>` tuples are `lon,lat,elev` — **lon comes FIRST**. Convert to
lat,lon before reporting. Polygons close (first == last point).

## Deriving the "GPS pin" from a boundary

- The KML usually has several placemarks: survey-number polygons (named like
  `SYNO`, `SAYNO1`, `BR`, `hissa`), `Boundary`, `Road`, and sometimes
  plot/owner polygons (`Manohar Plot`).
- **`Boundary` placemark = the parcel boundary.** If it exists, compute the
  centroid (mean of vertices) for a clean `lat,lon` pin:
  ```python
  lon = sum(p[0] for p in pts)/len(pts); lat = sum(p[1] for p in pts)/len(pts)
  ```
- Report the lat/lon RANGE too (min/max of boundary) — NDR appreciates it, and
  it cross-validates the pin.
- Link: `https://www.google.com/maps?q=<lat>,<lon>`.
- The My Map itself opens at `https://www.google.com/maps/d/viewer?mid=<FILE_ID>`.

## Pitfall: external listing pages give unreliable coordinates

Avacasa/99acres/marketing pages embed a `maps?q=<lat>,<lon>` pin that can be
completely off for rural farm plots (Riverstone Farms: avacasa.life said
13.2668,77.7128 — ~wrong region; the Drive survey KML said ~13.6772,77.8338).
**Trust the Drive survey map / KML, not the listing page.** If wanting to
cross-check, verify the listing pin is within the survey KML lat/lon range.

## Worked example: Riverstone Farms (Katenhalli) — 2026-10-13

Project aliases (use all in Drive `name contains` searches):
Riverstone Farms / Riverstone Farm / Terra Green Ventures / Terra Green LLP /
Terragreens / Katenhalli / Kattanhalli / Katenahalli. Notes:
- Architect = **Finding Form Design Studio (FFDS)**; files owned by
  `bk@findingform.design` (Bhuvanesh). FFDS project root is the `Riverstone`
  folder owned by bk; `Architectural/PDF` subfolder holds `Riverstone -
  Masterplan.pdf` (2026-03-10).
- Renders live under `Terragreens Riverstone Renders` (bk-owned, folder id
  `18zEhDpaI_JO9H_BDUvbKTmftFeGh81pM`) with subfolders per area
  (Entrance / Villa 1 / Villa 2 / Villa 3 / Reception and Cafe).
- Key file ids: Riverstone Survey My Map `1d-V_Xl_HaVbly2RT_-MnLfKe7vJlTOs`;
  Masterplan `1K8-gPqudRSi2jfWCzfltoC60v_rTO6F0`;
  Brochure `1vWDLMXTv_ap7clcGxWbCwxDYfNZy-4PK`.
- Verified: site centre ≈ **13.6772, 77.8338**; boundary spans roughly
  lat 13.675–13.680, lon 77.831–77.837 (Sy 114-1, 157, 158 area).
- Project structure note: DRAAS often owns the Riverstone folder via NDR
  (`ndr@draas.com`), but FFDS architecture files are owned by
  `bk@findingform.design` and hosted under a findingform.design drive that is
  shared in — list both folders when pulling architect deliverables.
- Kelsa land-proposal memory: "Vardhan Ventures" trick — GMaps link should
  always be filled from NDR's link; for Riverstone the survey My Map KML is
  the coordinate source.

## Multi-name Drive search pattern

`entity_resolver`/noun-resolver can fail mid-session; the reliable fallback
for artifact lookups is raw Drive queries:

```
name contains 'Riverstone' or name contains 'Katenhalli' or name contains 'Terragreens'
```

Then walk the project folders (list by `folder_id`) rather than relying on
flat search — renders/masterplans are nested several levels deep under BK's
drive. Structure seen: `Riverstone (bk root) → Architectural → PDF | Renders
→ <area>/*.png`.