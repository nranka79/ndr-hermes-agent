# Google My Maps — KML Modification & Upload Workflow

Companion to `my-maps-kml-extraction.md`. Covers adding descriptions (with highlighted prices) to placemarks and the available update paths.

## KML Description Structure

Every `<Placemark>` can carry a `<description>` element containing HTML. The `<BalloonStyle>` must include `$[description]` for it to display.

### Before (name only — no description visible)

```xml
<Style id="icon-1899-0288D1-nodesc-normal">
  <BalloonStyle>
    <text><![CDATA[<h3>$[name]</h3>]]></text>
  </BalloonStyle>
</Style>

<Placemark>
  <name>Prestige Sanctuary</name>
  <styleUrl>#icon-1899-0288D1-nodesc</styleUrl>
  <Point><coordinates>77.6969201,13.3138264,0</coordinates></Point>
</Placemark>
```

### After (description visible with highlighted price)

```xml
<Style id="icon-1899-0288D1-nodesc-normal">
  <BalloonStyle>
    <text><![CDATA[<h2>$[name]</h2><p>$[description]</p>]]></text>
  </BalloonStyle>
</Style>

<Placemark>
  <name>Prestige Sanctuary</name>
  <styleUrl>#icon-1899-0288D1-nodesc</styleUrl>
  <description><![CDATA[
    <b>📍 Nandi Hills Road, Devanahalli</b><br><br>
    🏡 Status: <b>Sold Out</b> (Resale only)<br>
    🏠 4 BHK Luxury Villas — 2,896 to 4,750 sqft<br><br>
    💰 <span style="background-color:#FFEB3B;padding:2px 6px;font-weight:bold;font-size:1.1em">
      Current Price: ₹11.70 Cr – ₹19.57 Cr</span><br>
    📊 Rate: ~₹25,455/sqft (Resale)
  ]]></description>
  <Point><coordinates>77.6969201,13.3138264,0</coordinates></Point>
</Placemark>
```

### HTML Tips for My Maps Descriptions

| Feature | Code |
|---------|------|
| **Highlighted price** | `<span style="background-color:#FFEB3B;padding:2px 6px;font-weight:bold;">…</span>` |
| **Bold text** | `<b>text</b>` |
| **Line break** | `<br>` |
| **Emoji indicators** | Use unicode emoji (📍🏡💰📊) |
| **Heading** | `<h2>` or `<h3>` |
| **CDATA wrapper** | ALWAYS wrap in `<![CDATA[ … ]]>` to avoid XML parse errors |

### Update Both normal AND highlight styles

My Maps uses style maps with both `-normal` and `-highlight` variants. Update both BalloonStyle blocks:

```xml
<Style id="icon-1899-0288D1-nodesc-normal">
  <BalloonStyle>
    <text><![CDATA[<h2>$[name]</h2><p>$[description]</p>]]></text>
  </BalloonStyle>
</Style>
<Style id="icon-1899-0288D1-nodesc-highlight">
  <BalloonStyle>
    <text><![CDATA[<h2>$[name]</h2><p>$[description]</p>]]></text>
  </BalloonStyle>
</Style>
```

### Get Current KML with OAuth (Python)

```python
from tools import gws_auth
import urllib.request

service = gws_auth.build_service('drive', 'v3', service_name='google-draas')
creds = service._http.credentials

kml_url = 'https://www.google.com/maps/d/kml?mid=MAP_ID&forcekml=1'
req = urllib.request.Request(kml_url)
req.add_header('Authorization', f'Bearer {creds.token}')
with urllib.request.urlopen(req) as resp:
    kml = resp.read().decode('utf-8')
```

## Update Methods — Current State (July 2026)

### ✅ Method 1: Browser Import (RELIABLE)

The only reliable way to update a My Maps file content. The user needs to:

1. Sign in to Google in a real browser
2. Open the map edit URL: `https://www.google.com/maps/d/edit?mid=MAP_ID`
3. Click **Add layer** → **Import**
4. Select the KML file from Drive
5. Choose to **replace the existing layer**

If descriptions were already added, the import overwrites with new data including descriptions.

### ❌ Method 2: Drive API `files.update()` (DOES NOT WORK)

```python
# This returns 200 but DOES NOT update the map content
service.files().update(
    fileId=map_id,
    media_body=kmz_buffer,          # or KML
).execute()
```

The Drive API **returns success** (200) but only updates file metadata (name, description). The actual map content (placemarks, layers, descriptions) remains unchanged.

### ❌ Method 3: Create My Maps from KML via Drive API

```python
# This fails with 400 Bad Request
service.files().create(
    body={'name': 'New Map', 'mimeType': 'application/vnd.google-apps.map'},
    media_body=kml_file,
)
```

Drive API does NOT support creating My Maps files by KML upload with mimeType conversion.

### ❌ Browser OAuth Token Sign-in

An OAuth access token (from gws-vault) **cannot** be used to sign into Google via the browser UI. The browser My Maps editor requires a full Google session cookie (password-based or SSO). There is no programmatic way to convert an OAuth token into a browser session.

## Recommended Working Pattern

```
1. Get current KML (OAuth)     → Modify XML (add descriptions, BalloonStyle)
2. Upload KML to Drive          → Service account / OAuth
3. Tell user to import KML      → "Open drive link, click Add layer → Import"
4. User imports into My Maps    → Descriptions now visible
```

Save the KML to the same Drive folder as the My Maps file for easy access:

```python
from googleapiclient.http import MediaIoBaseUpload
import io

media = MediaIoBaseUpload(
    io.BytesIO(kml_content.encode('utf-8')),
    mimetype='application/vnd.google-earth.kml+xml',
    resumable=True
)
file = service.files().create(
    body={'name': 'Projects - Updated with Prices.kml',
          'parents': ['FOLDER_ID']},
    media_body=media,
    fields='id,name,webViewLink'
).execute()
```

## Known Limitations (as of July 2026)

| Limitation | Impact |
|------------|--------|
| No public My Maps write API | Can only update via browser UI |
| OAuth token ≠ browser session | Cannot programmatically sign into browser |
| Drive API update is a no-op | Returns 200 but doesn't change content |
| KML → My Maps conversion fails | 400 Bad Request on create with mimeType |
| Need password to sign in | gws-vault can't provide a Google password — only OAuth tokens |
