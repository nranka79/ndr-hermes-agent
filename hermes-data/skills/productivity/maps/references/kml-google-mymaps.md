# KML for Google My Maps

## Overview

Google My Maps (mymaps.google.com) supports KML 2.2 import. You create a
custom map with pins, lines, polygons, and labels that sync across devices.

## Import workflow (for the user)

1. You send the `.kml` file via Telegram (as MEDIA: attachment)
2. User opens mymaps.google.com → **Create Map** → **Add Layer → Import**
3. Select the `.kml` file
4. Google renders all placemarks, lines, and labels

## Key KML tags for My Maps

### Placemark (pin)
```xml
<Placemark>
  <name>Pin Name</name>
  <description>Optional snippet</description>
  <Point>
    <coordinates>77.5977,13.0777,0</coordinates>
  </Point>
</Placemark>
```

### Line (path between pins)
```xml
<Placemark>
  <name>Line Label — 12.4 km</name>
  <LineString>
    <extrude>1</extrude>
    <tessellate>1</tessellate>
    <coordinates>
      77.5870,13.0910,0
      77.5977,13.0777,0
    </coordinates>
  </LineString>
  <Style>
    <LineStyle>
      <color>ff0066ff</color>  <!-- AABBGGRR -->
      <width>3</width>
    </LineStyle>
  </Style>
</Placemark>
```

### Colour format
KML colours are **AABBGGRR** hex (alpha, blue, green, red), NOT the usual
AARRGGBB. Examples:
- Blue:  `ff0000ff` → `ff0000ff`
- Orange: `ff0044ff` → `ffff4400`
- Green:  `ff00cc00` → `ff00cc00`

### Distance labels
Put the distance in the `<name>` tag of the LineString Placemark:
```xml
<name>Ranka Northstar → Jakkur — 2.1 km</name>
```
My Maps shows the name above the line midpoint.

## Pin icon styles
Use Google's built-in marker icons:
```
http://maps.google.com/mapfiles/ms/icons/red-dot.png
http://maps.google.com/mapfiles/ms/icons/blue-dot.png
http://maps.google.com/mapfiles/ms/icons/green-dot.png
http://maps.google.com/mapfiles/ms/icons/orange-dot.png
http://maps.google.com/mapfiles/ms/icons/purple-dot.png
http://maps.google.com/mapfiles/ms/icons/yellow-dot.png
```

## Pitfalls
- KML `<name>` values in LineString Placemarks appear as labels in My Maps,
  but the label position may be at the line centroid (not always ideal).
  For critical labels, add an extra Placemark at the midpoint with
  `<IconStyle><scale>0</scale></IconStyle>` to hide its own pin.
- Google My Maps can import KML up to ~5 MB.
- Coordinates order: `lon,lat,alt` (longitude **first**, then latitude).
  Getting this wrong places pins on the other side of the globe.
- `<extrude>1</extrude>` ensures the line sits on terrain surface in 3D view.
- If the user edits the map in My Maps and re-exports, the KML format
  changes slightly (Google adds its own style IDs). That's fine — the
  round-trip still works.
