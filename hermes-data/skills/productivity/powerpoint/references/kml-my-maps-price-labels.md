# KML Placemark Rename — My Maps Price Labels

When you need to update Google My Maps pin labels to show current prices instead of project names — useful for real estate competitive landscape maps where the user wants price visibility on the map.

## Workflow

### 1. Get the KML

The My Maps KML is typically already synced to Google Drive. Search for it:

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3', service_name='google-draas')

results = drive.files().list(
    q="name contains 'KML' or mimeType='application/vnd.google-earth.kml+xml'",
    fields='files(id, name)'
).execute()
```

Or download directly via the Drive file ID.

### 2. Parse and update placemark names

KML placemarks have this structure:

```xml
<Placemark>
  <name>Project Name</name>
  <styleUrl>#villaStyle</styleUrl>
  <description><![CDATA[
    ...<b>💰 CURRENT PRICE:</b> <span ...>₹8,500 — ₹12,000/sq.ft</span>...
  ]]></description>
  <Point><coordinates>...</coordinates></Point>
</Placemark>
```

The `<name>` is the pin label on the map. The `<description>` contains the price in a `<span>` after `💰 CURRENT PRICE:`.

Use regex to extract the price and replace the name:

```python
import re

with open('map.kml', 'r') as f:
    kml = f.read()

# Split by <Placemark> to process individually
parts = kml.split('<Placemark>')
updated = [parts[0]]

for block in parts[1:]:
    block = '<Placemark>' + block
    
    # Find the price in the description
    price_match = re.search(
        r'💰 CURRENT PRICE:</b>\s*<span[^>]*>\s*([^<]+)\s*</span>',
        block, re.DOTALL
    )
    name_match = re.search(r'<name>([^<]+)</name>', block)
    
    if price_match and name_match:
        old_name = name_match.group(1)
        price = price_match.group(1).strip()
        
        # Clean price for pin display
        price_clean = re.sub(r'\s*\([^)]*\)', '', price).strip()
        
        # Decide label format
        if '/sq.ft' in price_clean:
            new_name = price_clean
        else:
            new_name = f"{price_clean}/sft"
        
        block = block.replace(f'<name>{old_name}</name>', f'<name>{new_name}</name>', 1)
    
    updated.append(block)

new_kml = ''.join(updated)
```

### 3. Verify

```python
for m in re.finditer(r'<Placemark>\s*<name>([^<]+)</name>', new_kml):
    print(f"  📍 {m.group(1)}")
```

### 4. Upload back to Drive

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload('updated_map.kml', mimetype='application/vnd.google-earth.kml+xml')
uploaded = drive.files().create(
    body={'name': 'Map_With_Prices.kml', 'description': 'Price labels for My Maps'},
    media_body=media,
    fields='id,name,webViewLink'
).execute()
```

### 5. User imports into My Maps

Guide the user:

1. Open the My Maps: `https://www.google.com/maps/d/edit?mid=MAP_ID`
2. For each layer: 3-dot menu → **Delete all features**
3. Click **Import** → select the KML from Drive → assign to layer
4. Or: **Add layer** → Import → select KML

## Pitfalls

- **Price text may span multiple lines** in the CDATA section. Use `\s*` generously between tags.
- **RANKA Oasis (anchor project)** may have a different price format (`~₹12,000/sq.ft (built-up)`) — strip parentheses suffixes via `re.sub(r'\s*\([^)]*\)', '', price)`.
- **Importing KML to existing My Maps layers** replaces ALL features in that layer — the user must delete old pins first, or create a new layer.
- **My Maps has limited character width** for pin labels. Keep names short: "₹8,500-₹12,000/sq.ft" fits; very long strings may get truncated on the map.
- **Ampersands** in project names (e.g. "Assetz 18 & Oak") appear as `&amp;` in KML XML. Handle them as-is — the regex matches on text content, not XML entities.
