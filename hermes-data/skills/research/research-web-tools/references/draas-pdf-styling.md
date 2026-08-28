# PDF Template Styling Extraction + Styled HTML Generation

Extract the exact design system from an existing DRAAS PDF and generate a matching
HTML competitive analysis presentation. Used when user provides a PDF template and
asks to present a list of projects "in the same style."

---

## Step 1 — Extract PDF Design System via PyMuPDF

```python
import fitz  # PyMuPDF

doc = fitz.open('/data/hermes/document_cache/Some_DRAAS_Template.pdf')

for page_num, page in enumerate(doc):
    # Extract text blocks with positions
    blocks = page.get_text("dict")["blocks"]
    
    # Extract all drawing paths (rectangles, lines, fills)
    paths = page.get_drawings()
    
    # Get page dimensions
    print(f"Page {page_num+1}: {page.rect.width:.0f} x {page.rect.height:.0f} pt")
    
    # Get all font names used
    font_names = set()
    for block in blocks:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    font_names.add(span["font"])
    print(f"Fonts: {font_names}")
    
    # Print all text with font + color for palette extraction
    for block in blocks:
        if "lines" in block:
            for line in block["lines"]:
                for span in line["spans"]:
                    color = span.get("color", 0)
                    rgb = tuple(int(color.to_bytes(4, "big")[1:]).zfill(3) for _ in "RGB") if color else (0,0,0)
                    print(f"  color=#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}  size={span['size']:.1f}  font={span['font']}  text={span['text'][:60]!r}")
    
    # Extract rectangles from drawings (cards, borders)
    for path in paths:
        for item in path.get("items", []):
            if item[0] == 0:  # rectangle
                rect = item[1]
                fill = path.get("fill")
                if fill:
                    f = tuple(int(x*255) for x in fill)
                    print(f"  RECT fill=#{f[0]:02x}{f[1]:02x}{f[2]:02x}  at ({rect.x0:.0f},{rect.y0:.0f})-({rect.x1:.0f},{rect.y1:.0f})")
```

**Key metrics to capture:**
- Color palette (hex codes for backgrounds, borders, text, accents)
- Font family and weights used
- Page dimensions (in pt — 1 pt = 1/72 inch)
- Card/box layout patterns (borders, rounded corners, padding)
- KPI callout strip structure (colored top borders, icon placement)
- Section header styling (background color, left border accent, uppercase)
- Table structure (header background, row shading, column layout)

---

## Step 2 — Build CSS Design System from Extracted Tokens

After running the PyMuPDF analysis, compile the tokens into a CSS custom properties block:

```css
:root {
  --navy: #1D1F22;
  --gold: #F8B930;
  --sky-blue: #41A6E0;
  --white: #FFFFFF;
  --light-bg: #F5F5F5;
  --grey-card: #F5F5F5;
}
```

Then write the full CSS following the same patterns extracted from the PDF.

---

## Step 3 — HTML Document Structure (Competitive Analysis Format)

For a multi-project competitive analysis presentation, use this layout:

```html
<html>
<head>
  <!-- Poppins from Google Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>/* extracted CSS tokens + layout rules */</style>
</head>
<body>

<!-- Header bar -->
<header>
  <div class="gold-strip"></div>
  <div class="navy-bar">DRAAS — Competitive Analysis</div>
</header>

<!-- Project cards grid (2-column) -->
<div class="projects-grid">
  {{#each projects}}
  <div class="project-card">
    <div class="card-header">
      <span class="project-name">{{name}}</span>
      <span class="status-badge {{status_class}}">{{status}}</span>
    </div>
    <div class="mini-kpi-row">
      <!-- key metrics --></div>
    </div>
    <!-- Listings table with per-sqft rate --></div>
  {{/each}}
</div>

<!-- Full comparison table at bottom -->
<!-- Insight/notes box -->
</body>
</html>
```

---

## Step 4 — Save and Deliver

```python
output_path = '/data/hermes/document_cache/draas_competitive_analysis.html'
with open(output_path, 'w') as f:
    f.write(html_content)
print(f"Saved: {output_path} ({len(html_content)} bytes)")
```

Send the file to the user via Telegram as a direct file attachment (not a Drive link), per DRAAS user preference.

---

## Verified Design Tokens — DRAAS Gunjur PDF (Extracted May 2026)

These tokens were extracted from the actual Gunjur Village investor PDF using PyMuPDF + PIL/numpy
color analysis. Use these as the canonical DRAAS design system — NOT the old Poppins/sky-blue values.

**Color palette (verified from Gunjur Village investor PDF):**
```css
:root {
  --navy:     #1A3A5C;   /* Primary dark background / headers */
  --navy-dark:#0D2137;   /* Darker navy gradient variant */
  --gold:     #F9BA2F;   /* Primary accent — used everywhere */
  --gold-dark:#C8A400;   /* Gold text on dark backgrounds */
  --black:    #1D1F22;   /* Near-black for cover/dark slides */
  --green:    #1E7A3C;   /* Positive indicators */
  --red:      #C0392B;   /* Negative / deduct indicators */
  --white:    #FFFFFF;
  --off-white:#F8F9FA;   /* Table alternate rows, callout backgrounds */
  --border:   #E0E0E0;   /* Card / table borders */
  --mid-gray: #888888;   /* Secondary labels, metadata */
  --text-dark:#1D1F22;   /* Body text on white */
  --text-mid: #555555;   /* Secondary body text */
}
```

**Fonts (verified from PDF + text extraction):**
- Display / Slide titles: `Playfair Display` (serif, weights 700/800) — Google Fonts
- Body / UI / tables: `Inter` (sans-serif, weights 300–900) — Google Fonts
- NEVER use Poppins for DRAAS investor documents

**Page dimensions:** 1280px × 720px (16:9 presentation format)

**Slide header variants:**
- Dark header (black `#1D1F22`): Cover, financials, competitor analysis slides
- Navy header (`#1A3A5C`): Location, infrastructure, employment, social infra slides
- Footer: DRAAS logo left + disclaimer right, 8.5px gray text, border-top

**KPI metric cards:** White card, 1px border, 4px left border in accent color, 22–26px bold value
- `border-left: 4px solid var(--gold)` = default card
- `border-left: 4px solid var(--navy)` = `nl` variant
- `border-left: 4px solid var(--green)` = `gr` variant
- Badge (if any): top-right, gold background, 7.5px bold uppercase

**Data tables:**
- Header: navy `#1A3A5C` background, white 8.5px uppercase bold text
- Alternate rows: `#F8F9FA` / `#FFFFFF`
- Label cells: `font-weight:600; color:#1D1F22`
- Value highlights: navy `#1A3A5C`, gold-dark `#C8A400`, green `#1E7A3C`
- Deduct values: red `#C0392B`
- Total rows: navy background, white bold text
- Net rows: green background, white extra-bold

**Status badges:**
- Active / LIVE: green bg `#1E7A3C`, white text
- Upcoming: gold bg `#F9BA2F`, black text
- Planned / RIN: navy tint `rgba(26,58,92,0.1)`, navy text

**Cover slide (black `#1D1F22`):**
- 6px gold top bar
- Playfair Display 50px title
- 4-metric strip with gold left-border boxes
- Bottom bar: location + coordinates

**CTA slide (black `#1D1F22`):**
- Same as cover
- Gold top bar + gold left-border contact boxes
- Disclaimer at bottom (18% opacity white text)

**Divider slides:** Full navy `#1A3A5C`, Playfair Display 130px ghost number, 36px title, gold divider line

**Section kickers:** 8.5px, weight 700, letter-spacing 3px, gold-dark `#C8A400`, uppercase
**Section titles:** Playfair Display, 26–28px, weight 800
**Section divider lines:** 50px wide, 3px gold

**Callout blocks:**
- Default: 4px gold left-border, `rgba(249,186,47,0.05)` background
- Navy: 4px navy left-border, `rgba(26,58,92,0.05)` background
- Green: 4px green left-border, `rgba(30,122,60,0.05)` background

**Infrastructure cards:** 3-column grid, white card, 3px gold top-border, 32px icon circle (gold-tint bg), `badge act/upc/pln` bottom-right

**Employer cards:** 2-column grid, white card, 40px navy circle logo, flex row layout

**Competitor bar charts:**
- Horizontal bars: track = `#F8F9FA`, fill = navy/green
- Gold marker line with "YOU" label above
- Label: 10.5px bold, 150px fixed width

---

## When to Use This vs `investment-document-creation`

| | PDF Styling Extraction | Investment Document Creation |
|---|---|---|
| **Trigger** | User provides a styled PDF template | User shares a DRAAS land deal proposal PDF |
| **Design system** | Navy/gold (extracted from PDF) | Dark green `#c8ff57` |
| **Format** | Multi-project competitive analysis | 2-page investor pitch deck |
| **Font** | Poppins (from PDF) | Inter + JetBrains Mono |
| **PDF output** | Optional (print from browser) | Playwright-based generation |
| **Drive upload** | Optional | Always uploaded to Drive |

Both skills share the step "extract PDF via PyMuPDF" but diverge immediately after.