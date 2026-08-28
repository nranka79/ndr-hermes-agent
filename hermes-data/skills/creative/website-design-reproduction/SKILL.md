---
name: website-design-reproduction
description: "Extract design assets, visual DNA, and content from a reference website, then produce a comprehensive coding agent brief for reproducing the animated quality (Lenis+GSAP, Whispering Greens-style) in a new project."
umbrella: website-design-reproduction
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Website Analysis, Asset Extraction, Coding Agent Prompt, Animation Reproduction, Framer Scraping]
---

# Website Design Reproduction — Umbrella

Covers the full workflow of analyzing a live reference website, extracting all image assets + content + visual DNA, and producing a comprehensive coding agent prompt for building an animated single-page website with similar quality.

**Trigger phrases:** "make something like X for Y", "extract assets from this website", "create a coding agent prompt from this reference", "build an animated website similar to [name] using [project]'s content"

## Workflow Steps

### Step 1: Fetch the website

If browser tools are unavailable, use `curl -sL "<url>"` to get the full HTML source. Most modern static sites (Framer, Webflow) render all assets in the source.

```bash
curl -sL "https://example.com/" > /tmp/site.html
```

### Step 2: Extract all image asset URLs

Use regex to find all framerusercontent.com / image CDN URLs from the HTML. Deduplicate by base URL (strip size modifiers).

```python
import re
urls = re.findall(r'https://framerusercontent\.com/images/[a-zA-Z0-9]+\.(?:png|jpg|jpeg|webp|avif|svg)', html)
```

**Framer site quirk:** URLs carry size query params like `?scale-down-to=1024&width=1536&height=1024`. Strip these to get the base URL, then download with `?scale-down-to=1024` for a reasonable file size.

### Step 3: Download all assets

Create a local folder (`assets/`) and download each unique URL. For large images, use `?scale-down-to=1024` to keep file sizes manageable:

```bash
curl -sL "${url}?scale-down-to=1024" -o "assets/filename.png"
```

### Step 4: Identify each asset's purpose

Use dimension data (from PIL/Pillow) + context clues from the HTML (nearby headings, alt text, filename patterns) to map each asset to a role:

| Role | Dimensions | Placement |
|---|---|---|
| Hero background | ~1900px+ wide, panoramic | Full-bleed at top |
| Section image | ~800×600px, landscape | Content zigzag panels |
| Gallery image | ~1000×680px | Gallery/masonry section |
| Logo | Square, ~100-500px | Brand element |
| Icons | Small (<100px) | UI elements |
| Map/graphic | Variable | Location/map section |

### Step 5: Extract all content and messaging

Strip `<script>` and `<style>` tags, then extract text. Deduplicate and organize by section:

```python
text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', '\n', text)
lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 3]
```

Categorize lines as:
- **Headings** (short, <60 chars) — section titles, feature names, value props
- **Body copy** (longer, >60 chars) — descriptive paragraphs, sales copy

Key elements to capture:
- Core hook / headline (the first thing users see)
- Tag badges / sub-headlines
- USP bullet points
- Stats and numbers
- CTA text
- Contact details and RERA info
- Nearby amenities (hospitals, schools, IT parks, etc.)

### Step 6: Extract visual DNA from the reference site

The reference site's design language becomes the template. Document:

| Element | What to capture |
|---|---|
| **Typography** | Font names, weights, roles (heading vs body) — from `@font-face` / Google Fonts in source |
| **Colour palette** | CSS custom properties, inline styles in key elements (nav, CTA, footer) |
| **Layout architecture** | Page flow: hero → zigzag sections → grid features → full-width CTA → footer |
| **Animation system** | Libraries used (Lenis, GSAP, ScrollTrigger), config values (lerp, offset, transforms) |
| **Image treatment** | Colour grading (warm/cool), hybrid photo-illustration style, watermark overlays |
| **Responsive behaviour** | Breakpoints, grid/stack changes |

### Step 7: Build the coding agent prompt

Create a comprehensive HTML document with these sections:

1. **Project details (pre-filled)** — All extracted content, stats, USPs, colour palette, assets
2. **Design reference (the "DNA" to borrow)** — Typography, layout, animation spec, responsive behaviour
3. **Asset references** — File mapping table (friendly name → actual file, dimensions, usage)
4. **Agent instructions** — What to build, what to borrow vs customise, deliverables
5. **Quality checklist** — 12-15 must-pass items

**Prompt structure rules:**
- **Pre-fill ALL content from the scraped site** — no placeholders for copy, stats, USPs, contact details
- Include exact animation config values (Lenis lerp, GSAP offsets, transform values)
- Include the full colour palette as CSS custom properties
- Include a file mapping table for the agent to know which file goes where
- End with a quality checklist

### Step 8: Package and deliver

```bash
# Create zip with assets + prompt
zip -r project-assets.zip assets/ prompt.html
```

Deliver via Telegram as MEDIA: attachment.

## The "Whispering Greens DNA" — Animation Reference Profile

When a user says "make it like Whispering Greens" or "similar to Whispering Greens," use this exact animation spec:

| Element | Specification |
|---|---|
| **Smooth scroll** | Lenis v1.0.33, `lerp: 0.05`, `wheelMultiplier: 1`, RAF loop |
| **Scroll triggers** | GSAP ScrollTrigger v3.15.0 |
| **Content reveals** | `translate3d(0, 200px, 0)` + `opacity: 0.1` → identity + `opacity: 1` |
| **Hero headline** | `translate3d(0, 250px, 0)` + `opacity: 0` (larger offset) |
| **Side panels** | Right: `translate3d(100%, 0, 0)` → identity; Left: `translate3d(-100%, 0, 0)` → identity |
| **Post-load fix** | `window.addEventListener('load', lenis.update)` — prevents whitespace |
| **Per-element targeting** | `data-w-id` attributes for independent animation |

## Pitfalls

- **Framer sites use auto-generated image URLs** with hash filenames. The same image may appear at multiple URLs with different size modifiers. Deduplicate by base hash.
- **Password-protected PDF statements** are a different pattern (see `productivity/gws-automation/references/bank-statement-password-in-email-body.md`).
- **Annual summary vs monthly statement confusion**: The most recent email by date may be a year-end summary, not the billing statement. Check the subject for date range length.
- **Font loading in the new site**: Use WebFont loader with preconnect to Google Fonts CDN. Don't expect the same fonts to render instantly.
- **AVIF is the reference format** but the extracted assets are usually PNG/JPEG/WEBP. The agent prompt should note the format hierarchy but the delivered assets are whatever was scraped.
- **Browser tools may not be available.** Always fall back to `curl` for the initial scrape. Browser is only needed for JS-rendered content.

## Reference Files

| File | Content |
|---|---|
| `references/whispering-greens-analysis.md` | Full visual DNA analysis of whisperinggreens.com/green-framework |
| `references/ranka-udaya-extraction.md` | Worked example: extracting 22 assets + all content from rankaudaya.com (Framer site) |

## Absorbed Skills

(none yet)

### reference-website-extraction → website-design-reproduction

**Absorbed:** `reference-website-extraction` (2026-06-12)

**Content:** The `reference-website-extraction` skill covered the same website-asset-extraction → coding-agent-prompt workflow. Its content is absorbed as `references/reference-website-extraction.md`. Key preserved insights: general (non-Framer) HTML asset extraction patterns, content categorization logic, design DNA extraction techniques, and password-protected PDF statement notes.

**Archived.**
