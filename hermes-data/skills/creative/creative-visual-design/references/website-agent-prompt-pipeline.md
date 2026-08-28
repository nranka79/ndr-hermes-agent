# Website → Coding Agent Prompt Pipeline

**When to use:** User provides a live website URL and wants to extract all artwork/assets, study content/messaging, and produce a comprehensive coding agent prompt that replicates the design/animation DNA for a new project.

**Trigger phrases:** "analyze this website and see if we can get all the artwork assets", "create a detailed prompt for a coding agent based on this site", "build something similar to [reference site] for [new project]"

## Phase 1: Scrape & Asset Discovery

Fetch the full page source and extract all image URLs:

```bash
curl -sL "https://example.com" > /tmp/page.html
```

Extract all unique image asset URLs (works for Framer, Webflow, custom sites):

```python
import re, json
html = open('/tmp/page.html').read()

# Framer-specific: framerusercontent.com
urls = re.findall(r'https://framerusercontent\.com/images/[a-zA-Z0-9]+\.(?:png|jpg|jpeg|webp|avif|svg)', html)

# General: any src attribute with image extension
all_imgs = re.findall(r'src="(https?://[^"]+\.(?:png|jpg|jpeg|webp|avif|svg|gif))"', html)

# Unique base URLs (strip query params like ?scale-down-to=...)
bases = {}
for u in urls:
    key = re.sub(r'\?.*', '', u)
    bases[key] = bases.get(key, 0) + 1
```

## Phase 2: Download Assets

Download each unique asset to a local folder. For large images, append `?scale-down-to=1024` to framerusercontent URLs to get reasonable sizes:

```bash
mkdir -p /tmp/project-assets
for url in $(cat unique_urls.txt); do
    fname=$(echo "$url" | grep -oP '[a-zA-Z0-9]+\.[a-z]+$')
    curl -sL "${url}?scale-down-to=1024" -o "/tmp/project-assets/$fname"
done
```

## Phase 3: Content Extraction

Strip HTML and extract all meaningful text (headings + body paragraphs):

```python
import re, html as htmllib

text = html
text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', '\n', text)
text = htmllib.unescape(text)

lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 3]
```

Classify each line as `HEADING` (≤60 chars) or `BODY` (>60 chars) for structure mapping. Extract meta tags (og:title, og:description) for messaging hooks.

Also extract structured data (JSON-LD), page links, and the navigation structure.

## Phase 4: Asset Identification

Use PIL (Python Imaging Library) to examine each asset:

```python
from PIL import Image
img = Image.open(fp)
print(f'{f}: {img.size} {img.mode} {os.path.getsize(fp)} bytes')
```

Classify by dimensions:
- Large panoramic (1900px+ wide) → Hero / background
- Medium (~800-1024px wide) → Content section images
- Square / small (200-500px) → Icons, logos
- SVGs → Arrows, simple UI elements

Check SVG contents to identify icons (arrow paths, menu icons, etc.)

## Phase 5: Design DNA Analysis

From the reference site, extract these elements for the "Design DNA" spec:

| Element | Source | Example |
|---------|--------|---------|
| Typography | CSS @font-face declarations | Playfair Display + Geist |
| Colour palette | CSS custom properties, inline styles | Deep navy + gold |
| Layout architecture | Section structure from HTML | Hero → zigzag → grid → CTA |
| Motion system | JS imports (Lenis, GSAP) | Lenis lerp:0.05, GSAP ScrollTrigger |
| Image treatment | Image style patterns | Warm golden-hour, hybrid photo-illustration |
| Responsive behaviour | Media queries | 992px / 768px / 479px breakpoints |

## Phase 6: Build the Agent Prompt

Structure the prompt HTML document with these sections:

1. **Project Details** (pre-filled from extraction — no placeholders)
2. **Assets Provided** (table with filename, size, type, usage for each image)
3. **Colour Palette** (CSS custom property tokens)
4. **Design Reference** (the "design DNA" to replicate — typography, layout, motion, responsive)
5. **Agent Instructions** (what to build, what to borrow vs customise, deliverables)
6. **Quality Checklist** (15-20 must-pass items)

## Phase 7: Package & Deliver

```bash
zip -r project-package.zip project-assets/ coding-agent-prompt.html
# Send via Telegram
send_message(target='telegram', message='MEDIA:/tmp/project-package.zip\n\nDescription...')
```

## Pitfalls

- **Framer sites** use obfuscated CSS class names — don't try to parse Framer's internal structure. Extract images via regex on the raw HTML and text by stripping all tags.
- **Framer image URLs** have size modifiers (`?scale-down-to=1024`) — append these for reasonable downloads, but keep the base URL for srcset references.
- **Password-protected PDFs** (bank statements, etc.) — IndusInd uses `first 4 chars of name (lowercase) + DOB in DDMM` as password. Always check the email body for password instructions before claiming you can't open the PDF.
- **Format preference:** WhatsApp links must be delivered as raw clickable URLs in the Telegram message, NOT inside code blocks (Telegram mobile cannot tap links in code blocks).
- **Not all attachments are what they claim** — check the email subject and body carefully. A "statement" email may be an annual summary rather than a monthly statement. Look for the correct period.
