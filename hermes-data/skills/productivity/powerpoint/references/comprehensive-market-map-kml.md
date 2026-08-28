# Comprehensive Market Map KML — My Maps Import

Create a full-market KML for importing into Google My Maps — organizes 50+ placemarks into categorized layers with rich info cards. Use when the user asks to "update My Maps with all projects and key developments."

## When to Use

- User has a My Maps for a proposed land parcel and wants ALL competitor projects, key developments, and social infrastructure added
- You've researched 20+ projects and need to visualize them spatially
- The existing My Maps has only a few markers and needs comprehensive expansion

## Workflow

### 1. Export Existing KML

```bash
curl -sL "https://www.google.com/maps/d/kml?mid=MID_VALUE&forcekml=1" -o /tmp/existing.kml
```

This works without authentication for public maps. Parse the KML to understand existing placemarks and avoid duplicating them.

### 2. Define Color-Coded Layer Structure

Organize into 5-7 layers, each with a distinct purpose and color:

| Layer | Color | Icon Style | Contents |
|-------|-------|-----------|----------|
| 🟢 Proposed Land | Red outline+fill | `ff0000ff` | Site marker + boundary polygon |
| 🟡 Ongoing Projects | Gold/Blue | `ff14aad4` | Current competitor projects (12+) with pricing |
| 🔵 Completed Projects | Orange | `ffff8040` | Past projects with resale/appreciation data |
| 🟣 Upcoming Projects | Purple | `ff8060cf` | Prestige City, Puravankara, etc. |
| 🔴 Economic Drivers | Green | `ff00a527` | Industrial areas, Smart City, business parks |
| ⚪ Social Infra | Orange | `ff0090ff` | Schools, hospitals, retail, recreation |
| 🟠 Infrastructure | Teal | `ffa08029` | Expressways, ring roads, metro stations |

### 3. Define KML Styles

Each layer needs three style definitions in the KML `<Document>`:

```xml
<Style id="layer-name">
  <IconStyle>
    <color>AABBGGRR</color>  <!-- KML hex color = AABBGGRR -->
    <scale>1</scale>
    <Icon>
      <href>https://www.gstatic.com/mapspro/images/stock/503-wht-blank_maps.png</href>
    </Icon>
    <hotSpot x="32" y="64" xunits="pixels" yunits="insetPixels"/>
  </IconStyle>
  <LabelStyle><scale>1</scale></LabelStyle>
  <BalloonStyle>
    <text><![CDATA[<div style="font-family:Calibri,sans-serif;padding:8px;max-width:300px;">
      <h3 style="color:#C9A84C;margin:0 0 4px 0;">$[name]</h3>
      <p style="color:#555;font-size:11px;">$[description]</p>
    </div>]]></text>
  </BalloonStyle>
</Style>
```

**KML color format:** `AABBGGRR` — Alpha, Blue, Green, Red (reverse of HTML's RRGGBBAA).
- Red = `ff0000ff`, Blue = `ffff0000`, Green = `ff00ff00`, Gold = `ff14aad4`, Purple = `ff8060cf`

### 4. Create Folders (Layers)

Each layer is a `<Folder>` containing `<Placemark>` elements:

```xml
<Folder>
  <name>🟢 Proposed Land — Site Name</name>
  
  <Placemark>
    <name>Site Marker</name>
    <styleUrl>#layer-style-id</styleUrl>
    <description><![CDATA[
      <b>Area:</b> ~10 Acres<br>
      <b>Coordinates:</b> 12.80°N, 77.37°E<br>
      <b>Zoning:</b> BMRDA Layout Zone<br>
      <b>Access:</b> 2.5 km to NH-275 Expressway
    ]]></description>
    <Point><coordinates>lon,lat,0</coordinates></Point>
  </Placemark>
  
  <!-- Boundary polygon (for proposed land) -->
  <Placemark>
    <name>Land Boundary</name>
    <styleUrl>#boundary-style</styleUrl>
    <Polygon>
      <outerBoundaryIs>
        <LinearRing><tessellate>1</tessellate>
          <coordinates>lon1,lat1,0 lon2,lat2,0 ... lon1,lat1,0</coordinates>
        </LinearRing>
      </outerBoundaryIs>
    </Polygon>
  </Placemark>
</Folder>
```

### 5. Rich Info Cards

Placemark descriptions support HTML. Each card should include:

**For competitor projects:**
```html
<b>Developer:</b> Urbanrise / Alliance<br>
<b>Type:</b> Luxury Villa Community<br>
<b>Size:</b> 24 Acres (219 Villas)<br>
<b>Launch:</b> Feb 2023<br>
<b>Current Price:</b> ₹3.11-5.16 Cr<br>
<b>RERA:</b> PRM/KA/RERA/1251/310/PR/080223/005704
```

**For economic drivers:**
```html
<b>Area:</b> 1,400+ Acres<br>
<b>Occupants:</b> Toyota, Coca-Cola, Bosch<br>
<b>Workforce:</b> ~50,000 total, ~15,000 white-collar<br>
<b>Impact:</b> Primary demand driver for premium executive housing
```

**For social infrastructure:**
```html
<b>Distance:</b> ~2.5 km from site<br>
<b>Significance:</b> Major educational anchor in corridor
```

### 6. Getting Coordinates

Use these sources for placemark coordinates (lat/lon in decimal degrees):
- **Competitor projects**: Google Maps search for the project name + area + "Bangalore"
- **Existing markers**: Extract from the downloaded KML
- **Key developments**: Google Maps / Wikipedia coordinates
- **Road infrastructure**: Mid-point coordinates along the route, or nearest junction

### 7. Upload KML to Drive

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload('/tmp/map.kml', 
    mimetype='application/vnd.google-earth.kml+xml',
    resumable=True)
body = {
    'name': 'Project — Complete Market Map.kml',
    'description': 'Comprehensive map with 7 layers for My Maps import.'
}
f = drive.files().create(body=body, media_body=media, 
    fields='id, name').execute()
drive.permissions().create(fileId=f['id'], 
    body={'type': 'anyone', 'role': 'reader'}).execute()
```

### 8. User Import Instructions

Provide these steps in the deliverable:

1. Open your My Maps: `https://www.google.com/maps/d/edit?mid=MAP_ID`
2. Click ⋮ (3 dots) → **Import** → select the KML file from Drive
3. The new layers appear alongside existing data
4. Reorder layers by dragging in the layer panel
5. Each pin shows a detailed info card on click

## Pitfalls

- **KML color format is AABBGGRR** — not RRGGBBAA. `ff14aad4` = Alpha=ff, Blue=aa, Green=d4, Red=14. To get HTML red #D4A53C: Blue=0xA5, Green=0x3C, Red=0xD4 → `ff3ca5d4`. Test colors by importing into a test layer first.
- **Polygon coordinates must close**: The first and last coordinate pair must be identical for the polygon outline to render correctly.
- **Special characters in CDATA**: Use `&lt;` for `<`, `&gt;` for `>`, `&amp;` for `&` inside HTML descriptions. The CDATA wrapper (`<![CDATA[...]]>`) handles most cases but XML entities still apply outside CDATA.
- **Import replaces layer content**: When importing into an existing My Maps layer, it REPLACES all features in that layer. Tell users to create new layers for the KML import, or delete old layer content first.
- **Max placemarks per layer**: My Maps supports ~2,000 features per map. For 50-100 placemarks, performance is fine.
- **Name truncation**: Pin labels on My Maps get truncated if too long. Keep `<name>` under 40 characters. Put detailed info in the `<description>`.
- **KML must validate**: A single XML-syntax error (unclosed tag, missing CDATA) causes the entire import to fail silently. Validate the KML before upload with `xmllint --noout file.kml`.
