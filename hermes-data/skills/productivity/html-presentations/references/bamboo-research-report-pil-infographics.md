# Bamboo Research Report — PIL Infographic Generation

Two sessions (Jun 28, 2026 initial + Jun 28, 2026 expanded) generating comprehensive bamboo entrepreneur guides as self-contained HTML files with PIL-generated infographics, uploaded to Drive TMP folder.

## What was built (v2 — expanded)

**File:** `Bamboo_Entrepreneur_Guide_June2026.html` (657 KB single file)
**Drive folder:** TMP (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`)
**View link:** https://drive.google.com/file/d/1kmEIJMzghOycIWW9T5ASjfA8xpGV9Hh8/view

## 10 PIL infographics generated

| Image | Size | Content |
|-------|------|---------|
| `hero.png` | 33 KB | Dark green gradient with bamboo stalk silhouettes, title, decorative elements |
| `scheme_overview.png` | 42 KB | 3 stat cards (ministry, duration, budget), 6 feature grid items |
| `subsidy.png` | 50 KB | 10-row table of NBM subsidy components with funding pattern, color-coded |
| `species.png` | 47 KB | 8 species compared across 10 columns (height, diameter, rainfall, spacing, yield, rating), top pick callout |
| `costs.png` | 45 KB | Header row with "₹/acre" sub-labels, 12 expense line items across Years 0-3, totals row, subsidy impact box |
| `roi.png` | 52 KB | 6-year cash flow table, 3 scenario blocks (conservative/moderate/optimistic), 5 key metric cards |
| `value_add.png` | 51 KB | 3-column layout with 22 businesses across low/medium/high capital tiers, setup costs and profits |
| `roadmap.png` | 83 KB | 8-step numbered timeline with circle markers, detailed checklists per step |
| `research.png` | 32 KB | 4 institution cards (IFGTB, UAS Bangalore, TNAU, ICFRE) with key findings |
| `economics_chart.png` | 27 KB | Horizontal bar chart comparing bamboo vs 7 other crops (eucalyptus, coconut, arecanut, etc.) |

## Key PIL techniques used

### Multi-line table headers
For columns needing sub-labels (e.g. "Year 1" + "₹/acre" on second line):
```python
headers = ["Category", "Yr 0(Setup)\n₹/acre", "Year 1\n₹/acre", "Year 2\n₹/acre", "Total\n₹/acre"]
# Render:
y = 68
header_h = 40  # taller for multi-line
for i, (col_w, hdr) in enumerate(zip(cols, headers)):
    cx = 30 + sum(cols[:i])
    draw.rectangle([cx, y, cx+col_w, y+header_h], fill=MED_GREEN)
    for li, ln in enumerate(hdr.split('\n')):
        draw.text((cx+8, y+5+li*16), ln, fill=WHITE, font=font(12, True))
```

### Table with alternating row colors
```python
alt = False
for ri, row in enumerate(expenses):
    yr = 110 + ri * 30
    bg = LIGHT_BG if alt else WHITE
    draw.rectangle([30, yr, w-30, yr+30], fill=bg)
    for i, (col_w, val) in enumerate(zip(cols, row)):
        cx = 30 + sum(cols[:i])
        draw.text((cx+8, yr+7), val, fill=DARK_TEXT, font=font(11, i == 0))
    alt = not alt
```

### Color-coded scenario blocks
```python
scenarios = [
    ("CONSERVATIVE", MED_GREEN, body_text),
    ("MODERATE", GOLD, body_text),
    ("OPTIMISTIC", ACCENT_BLUE, body_text),
]
for i, (title, color, body) in enumerate(scenarios):
    scx = 40 + i * 350
    round_rect(draw, (scx, y, scx+330, y+150), fill=WHITE, radius=10, outline=color, width=3)
    draw.text((scx+15, y+10), title, fill=color, font=font(13, True))
```

### Horizontal bar chart
```python
chart_left = 260; chart_right = w-50
chart_w = chart_right - chart_left; max_val = 140000
for i, (label, val, color) in enumerate(chart_data):
    y = chart_top + i * (bar_h + gap)
    bar_width = int((val / max_val) * chart_w)
    draw.rectangle([chart_left, y, chart_left + max(bar_width, 3), y + bar_h], fill=color)
    draw.text((chart_left - 250, y + 4), label, fill=DARK_TEXT, font=font(11))
    draw.text((chart_left + bar_width + 8, y + 4), f"₹{val:,}/ac/yr", fill=color, font=font(10, True))
```

## File paths from this session

- Image generation script: `/opt/data/bamboo_generate_images.py`
- HTML build script: `/opt/data/bamboo_build_html.py`
- Output images: `/opt/data/bamboo_images/`
- Final HTML: `/opt/data/Bamboo_Entrepreneur_Guide_June2026.html`

## HTML template pattern

Used `__PLACEHOLDER__` replacement to avoid f-string conflict with CSS `{}`:
```python
html_template = '...<img src="data:image/png;base64,__HERO__">...'
for key, b64 in images.items():
    html_template = html_template.replace(f"__{key.upper()}__", b64)
```

## Research sources compiled

- National Bamboo Mission (NBM) — Ministry of Agriculture & Farmers Welfare
- PIB press releases on NBM
- IFGTB Coimbatore (ifgtb.icfre.gov.in) — high-yielding clones BB-1 to BB-5, DS-1 to DS-3
- UAS Bangalore, GKVK (uasbangalore.edu.in) — bamboo agroforestry, germplasm bank
- TNAU Agritech Portal (agritech.tnau.ac.in) — cultivation guide, economics, carbon sequestration
- NABARD model project reports
- Karnataka Forest Department — bamboo policies, KFDC purchase rates
- ICAR carbon sequestration studies
- AgriFarming.in, Krishijagran — cost economics data

## HTML sections included

1. National Bamboo Mission 2025 Overview
2. Complete Subsidy Structure (10 components with ₹ limits)
3. Bamboo Species for Bangalore/Karnataka (8 species, top 3 picks)
4. Complete Cost Breakdown ₹/acre (Year 0-3 with subsidy impact)
5. Revenue Projections & ROI Analysis (3 scenarios, 5-acre cash flow)
6. Value-Added Businesses (22 across 3 capital tiers)
7. Step-by-Step Action Roadmap (8 phases, IKEA-style)
8. Research Institutions & Key Studies
9. Resources & Next Steps (offices, links, immediate actions)

## Unit-labeling discipline (learned from user correction)

- Every financial table header MUST include sub-label showing unit (₹/acre, ₹ total)
- Separate callout box above cost tables restating the denomination
- Cash flow tables for different scales (per-acre vs. 5-acre total) must be explicitly labeled
- Use `₹` symbol (not `Rs`) for Indian Rupees throughout for consistency
- Example: "All figures in ₹ for 5 acres total (multiply by 0.2 for per-acre)"

## Drive upload command

```python
HERMES_SESSION_USER_ID = 'ndr'
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3')
# Delete old version
for f in drive.files().list(q=f"'{FOLDER_ID}' in parents and name='{FILE_NAME}' and trashed=false", fields='files(id)').execute().get('files', []):
    drive.files().delete(fileId=f['id']).execute()

media = MediaFileUpload(LOCAL_PATH, mimetype='text/html', resumable=True)
file = drive.files().create(
    body={'name': FILE_NAME, 'parents': [FOLDER_ID]},
    media_body=media, fields='id,name,webViewLink'
).execute()
drive.permissions().create(fileId=file['id'], body={'type': 'anyone', 'role': 'reader'}).execute()
print(file['webViewLink'])
```

## User IDs

- Nishant: `ndr`
- Bharat: `sales1.blr`
- Prakash: `psingh`

## TMP folder ID

`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`
