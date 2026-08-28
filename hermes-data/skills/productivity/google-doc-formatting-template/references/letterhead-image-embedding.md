# Letterhead Image Embedding into Google Docs

When you need a branded letterhead on a Google Doc (no PDF letterhead file available), build it programmatically:

## Workflow

1. **Generate the letterhead image** — two methods: SVG+cairosvg (preferred — professional results) or Pillow (fallback)
2. **Upload to Drive** and make publicly accessible
3. **Embed into the Google Doc** via Docs API `insertInlineImage`

## Preferred Method: SVG + cairosvg

SVG produces professional letterheads with gradients, curved decorative bars, and CSS-driven layout — no pixel math or font-path fiddling. cairosvg is available on the system.

### SVG template

```python
import cairosvg

svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="2480" height="700" viewBox="0 0 2480 700">
  <defs>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#1a3a5c;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#2b6cb0;stop-opacity:1" />
    </linearGradient>
  </defs>

  <!-- Top accent bar -->
  <rect x="0" y="0" width="2480" height="10" fill="url(#headerGrad)" />

  <!-- Company Name -->
  <text x="1240" y="100" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif"
        font-size="72" font-weight="bold" fill="#1a3a5c">COMPANY NAME</text>

  <!-- Tagline -->
  <text x="1240" y="155" text-anchor="middle" font-family="Arial, sans-serif"
        font-size="26" fill="#555">Tagline or description</text>

  <!-- Divider line -->
  <line x1="200" y1="180" x2="2280" y2="180" stroke="#ccc" stroke-width="1" />

  <!-- GST / PAN -->
  <text x="1240" y="220" text-anchor="middle" font-family="Arial, sans-serif"
        font-size="24" fill="#555">GSTIN: 29XXXXX0000X1ZX  |  PAN: AAAAA0000X</text>

  <!-- Address -->
  <text x="1240" y="255" text-anchor="middle" font-family="Arial, sans-serif"
        font-size="24" fill="#555">Address line 1, City, State - PIN</text>

  <!-- Bottom accent bar -->
  <rect x="0" y="380" width="2480" height="4" fill="url(#headerGrad)" />

  <!-- Footer -->
  <rect x="0" y="670" width="2480" height="30" fill="url(#headerGrad)" />
  <text x="1240" y="690" text-anchor="middle" font-family="Arial, sans-serif"
        font-size="18" fill="white">COMPANY NAME  |  Address  |  Contact</text>
</svg>'''

cairosvg.svg2png(bytestring=svg.encode(), write_to='/tmp/letterhead.png', dpi=300)
# Output: 2480×700 PNG at 300 DPI — A4-width, top portion only
```

**Gradient accent bars** and serif fonts for the company name create a premium look. Adjust colors to match the company brand. The `dpi=300` produces print-ready resolution.

### Considerations for SVG letterheads

- **No font files needed** — CSS `font-family` fallbacks work natively in SVG
- **Easier layout** — SVG text-anchor="middle" centers without bbox calculations
- **Brand colors** — Define gradients and color palette once in `<defs>`
- **Text shadow / glow** — Add `<filter>` for subtle effects if desired
- **Company logo** — Embed via `<image href="data:...">` with a base64 PNG
- **Phone / email** — Add below the address in a smaller font (20px, #666)

## Fallback Method: Pillow (PIL)

Use when cairosvg is unavailable or for simple monochrome letterheads with system fonts.

## Step 1 (Pillow approach): Generate the letterhead image

```python
from PIL import Image, ImageDraw, ImageFont

width, height = 2480, 700  # A4-width at ~300 DPI, top portion only
img = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(img)

# Fonts
title_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 72)
detail_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 28)
small_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)

# Colors
dark_blue = (26, 58, 92)
gray = (100, 100, 100)

# Top decorative bar
draw.rectangle([(0, 0), (width, 8)], fill=dark_blue)

# Company name - centered
text = 'COMPANY NAME'
bbox = draw.textbbox((0, 0), text, font=title_font)
x = (width - (bbox[2] - bbox[0])) // 2
draw.text((x, 60), text, fill=dark_blue, font=title_font)

# Tagline
tagline = 'Tagline here'
bbox = draw.textbbox((0, 0), tagline, font=detail_font)
x = (width - (bbox[2] - bbox[0])) // 2
draw.text((x, 150), tagline, fill=dark_blue, font=detail_font)

# GST / PAN details
gst_text = 'GSTIN: XXAAAAX0000X1ZX  |  PAN: AAAAA0000X'
bbox = draw.textbbox((0, 0), gst_text, font=detail_font)
x = (width - (bbox[2] - bbox[0])) // 2
draw.text((x, 235), gst_text, fill=gray, font=detail_font)

# Address
addr = 'Address line 1, City, State - PIN'
bbox = draw.textbbox((0, 0), addr, font=detail_font)
x = (width - (bbox[2] - bbox[0])) // 2
draw.text((x, 280), addr, fill=gray, font=detail_font)

# Bottom bar
draw.rectangle([(0, 400), (width, 406)], fill=dark_blue)

# Footer
draw.rectangle([(0, height-30), (width, height)], fill=dark_blue)
footer = 'Company Name  |  Address  |  GSTIN: XXAAAAX0000X1ZX'
draw.text((x, height-24), footer, fill='white', font=small_font)

img.save('/tmp/letterhead.png')
```

## Step 2: Upload to Drive with public access

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', service_name='google-draas')

media = MediaFileUpload('/tmp/letterhead.png', mimetype='image/png', resumable=True)
file_meta = {'name': 'Company Name - Letterhead.png', 'mimeType': 'image/png'}
uploaded = drive.files().create(body=file_meta, media_body=media,
                                fields='id,name,webViewLink').execute()

# Make publicly viewable
drive.permissions().create(fileId=uploaded['id'],
                           body={'type': 'anyone', 'role': 'reader'}).execute()

img_url = f"https://drive.google.com/uc?export=download&id={uploaded['id']}"
```

## Step 3: Embed in Google Doc

Create the doc first (via `gws_skill_bridge.call("docs_create", ...)`), then embeds:

```python
docs = build_service('docs', 'v1', service_name='google-draas')

requests = [
    {
        "insertInlineImage": {
            "location": {"index": 1},  # Beginning of document
            "uri": img_url,
            "objectSize": {
                "height": {"magnitude": 140, "unit": "PT"},
                "width": {"magnitude": 500, "unit": "PT"}
            }
        }
    }
]
docs.documents().batchUpdate(documentId=DOC_ID, body={"requests": requests}).execute()
```

## Pitfalls

- **Image must be publicly accessible** — Google Docs API `insertInlineImage` fetches the image URL server-side. URL must be readable without auth.
- **Index matters** — `index=1` places the image at the very start. If the doc has existing content, check the content structure first.
- **Font availability** — DejaVuSans is the safest bet on this system. For Indian-language or stylized fonts, install them first.
- **Avoid letterhead in header** — The Docs API header system is complex. Simpler to insert as the first element in the body with appropriate spacing.
- **Proxy download URL** — `https://drive.google.com/uc?export=download&id=...` works for the Docs API. The `/thumbnail` variant may not. `uc?export=view` works for browsers but not for the Docs API image fetch.
- **Size** — Keep letterhead height under 150 PT (about 2 inches) so the letter content starts high enough on the page. 500×140 PT works well for A4.
