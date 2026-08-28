# Product Specs Research via Wikipedia API

When Tavily, Apify, and browser tools are all down (or excluded per NDR directive), **Wikipedia's REST API is the most reliable free source** for structured product specifications — dimensions, weight, OS, chipset, display, battery, camera, pricing in multiple currencies, and availability.

## Core API Calls

### Full article text (clean, no HTML)

```
https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles=<ArticleName>&format=json
```

Returns the full article body as plain text. Good for: descriptions, launch history, specs narrative, release dates, naming variants.

### Infobox / structured specs (mobile HTML route)

Wikipedia's mobile page (`en.m.wikipedia.org`) has cleaner HTML than the desktop version. Extract the `<table class="infobox">` via regex:

```python
import urllib.request, re, html

url = f"https://en.m.wikipedia.org/wiki/{article_name}"
req = urllib.request.Request(url, headers={'User-Agent': 'Your-Name/1.0'})
resp = urllib.request.urlopen(req, timeout=15)
html_content = resp.read().decode('utf-8')

# Extract infobox
match = re.search(r'<table class="infobox[^"]*"[^>]*>.*?</table>', html_content, re.DOTALL)
if match:
    text = re.sub(r'<[^>]+>', '\n', match.group(0))
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = html.unescape(text)
```

Gives you: OS, SoC, CPU/GPU, RAM/storage, display (size + resolution), battery, cameras, dimensions (height/width/depth per fold state), weight, SIM type, charging specs, connectivity, sensors.

### Mobile page for full body content

Same mobile page also contains the full article text in `<div class="mw-parser-output">`. Extract it the same way for specs not in the infobox (price history, market availability by region, competitor comparisons).

## Tips for Product Research

### Pricing

Wikipedia often lists pricing in **multiple currencies** in the infobox or body:
- CNY (Chinese Yuan) — manufacturer's home market price
- USD/RMB conversion
- INR (for India-bound products)
- Convert CNY → SGD using ~0.19 rate (CNY 20,000 ≈ SGD 3,800)

### Dimensions for foldables

Foldable phone dimensions in Wikipedia infoboxes are structured by fold-state:
- `Height` × `Width` (per panel configuration) × `Depth`
- Depth values: single screen (fully folded), dual screen (half-open), triple screen (fully open)
- Weight always included

### Availability

Wikipedia tracks:
- Announcement date
- First release date and region (usually China first)
- Global release date
- Pre-order event locations (e.g. Kuala Lumpur for Huawei globally)

### OS caveats

- **HarmonyOS** devices (Huawei) — Wikipedia explicitly notes HarmonyOS, not Android
- Check for Google Play Services mention or EMUI version
- Wikipedia body text often discusses Android compatibility or lack thereof

## Fallback chain for product research

```
1. Wikipedia API (prop=extracts)       ← fast, reliable, no blocks
2. Wikipedia mobile page (infobox)     ← structured spec extraction
3. Jina reader (r.jina.ai/URL)         ← tech news articles, reviews
4. Google News RSS                      ← launch announcements, pricing news
   (news.google.com/rss/search?q=...)
```

## What NOT to do

- **GSMArena** curl frequently redirects to wrong product or hits CAPTCHA blocks. Avoid.
- **91mobiles / Notebookcheck** curl requests return 403. Use Jina reader proxy instead.
- **Google search via curl** returns 403 or JS redirect soup. Use Jina reader as Google proxy instead.
- **HardwareZone / Straits Times** articles behind SPH paywall. Accept the paywall and move to another source.

## Worked examples (Aug 2026)

### Huawei Mate XT Ultimate Design
```
API: titles=Huawei_Mate_XT
→ Extract: HarmonyOS 4.2, Kirin 9010, 16GB RAM, 5600mAh battery
→ Dimensions: 156.7 × 73.5/143.0/219.0 × 12.8/7.45/3.6 mm
→ Weight: 298g
→ Display: 10.2" 3184×2232 @ 90Hz LTPO OLED
→ Pricing: CNY 19,999/21,999/23,999 (256/512/1TB) ≈ USD $2,800/$3,090/$3,370
→ Availability: China Sep 2024, global Feb 2025 (KL launch)
```