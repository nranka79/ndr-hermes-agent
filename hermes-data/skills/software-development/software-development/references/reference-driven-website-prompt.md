# Reference-Driven Website Prompt Generation

**Context:** When the user wants a new website that mirrors the animation quality, visual language, and layout DNA of a **reference website** (e.g. Whispering Greens) but for a **different project/product** (e.g. Ranka Udaya).

## Workflow

### Phase 1 — Extract Reference Design DNA

Study the reference website and document:

1. **Animation stack** — Lenis smooth scroll + GSAP ScrollTrigger config (lerp, offsets, transform values)
2. **Typography** — Display font (serif for premium), body font (sans), weights
3. **Colour palette** — As CSS custom property tokens (`--brand-primary`, `--brand-accent`, etc.)
4. **Artwork / imagery style** — Photo-real vs hybrid photo-illustration, watercolour overlays, warm toning
5. **Layout architecture** — Full-bleed hero → zigzag sections → grid features → full-width CTA → footer
6. **Responsive behaviour** — Breakpoints and layout shifts per size
7. **Image format hierarchy** — AVIF primary, WebP fallback, SVG for logos

### Phase 2 — Scrape Target Website Content & Assets

1. **Fetch the page** via `curl -sL "<url>"` — works for Framer, Webflow, custom sites
2. **Extract all image URLs** — regex for `framerusercontent.com/images/` or `<img src="...">` patterns
3. **Download unique assets** — skip size-modifier query params, download base images
4. **Extract all text content** — strip HTML tags, capture headings, body paragraphs, stats, CTAs
5. **Identify key brand elements** — logo, RERA number, phone, email, WhatsApp number
6. **Analyze page structure** — WAG / LIFT / adjacent state pattern detection

### Phase 3 — Build the Coding Agent Prompt

Create a self-contained HTML file with:

1. **Project details** (pre-filled from scraped content — no placeholders):
   - Product name, type, location, target audience, USPs, brand tone, RERA
   - All copy: hero headline, section headings, body paragraphs, CTA text, contact info

2. **Design reference (Whispering Greens DNA)** to replicate:
   - Typography stack with exact font names and weights
   - Colour palette as CSS tokens (adapted to the new brand)
   - Artwork style description and image treatment brief
   - Layout architecture diagram (ASCII)
   - Motion specification (Lenis + GSAP with exact parameters)
   - Responsive breakpoints
   - Performance and SEO requirements

3. **Asset listing** (pre-filled):
   - All downloaded images mapped to their intended usage (hero, sections, gallery, background, icons)
   - File naming for HTML reference

4. **Agent instructions**:
   - What to build (single-page `index.html` with embedded CSS+JS)
   - What to borrow from reference (animation, layout rhythm, scroll-reveal patterns)
   - What to customise (colours, fonts, images, content)
   - Quality checklist (15-20 must-pass items)

5. **Additional features** specific to the project (e.g., e-brochure download modal, live plot availability grid, map section)

### Phase 4 — Package & Deliver

1. Zip assets + prompt HTML → deliver as `MEDIA:/path/to/project-name-assets.zip`
2. Provide a summary of what's inside

## Example (Whispering Greens → Ranka Udaya, June 2026)

| Element | Reference (Whispering Greens) | Target (Ranka Udaya) |
|---------|------|-------|
| Typography | Bellefair + Questrial + Raleway | Playfair Display + Geist |
| Animations | Lenis lerp:0.05 / GSAP fade-up 200px | Same (copied) |
| Palette | Warm greens, gold, off-white | Deep navy + gold, warm off-white |
| Images | AVIF hero + photo-illustration composites | PNG/JPG photographs + icons |
| Layout | Full-bleed hero → zigzag → grid → CTA → footer | Same structure adapted to 4-building-options |
| Content | Nature-focused copy | Investment-focused copy (SWIFT City, Hosur Airport, rental yield) |

## Pitfalls

- **Placeholders vs pre-filled:** The user will say "no placeholders" — scrape thoroughly so every headline, body paragraph, stat, and section heading is already in the prompt. The only thing the coding agent needs to do is build.
- **Image file naming:** Downloaded framerusercontent hashes are not human-readable. Map them to friendly names (hero.jpg, section-1.png, etc.) in the prompt so the coding agent knows which file goes where.
- **Colour adaptation:** The reference palette (green/earthy) must shift to the target brand (navy/gold for premium real estate) — spell out the new palette explicitly, don't leave it to the agent's taste.
- **Animation DNA:** Document exact Lenis lerp, GSAP ScrollTrigger offsets (200px vs 250px for hero), horizontal slide directions for side panels, and post-load fix (`window.addEventListener('load', lenis.update)`). Don't leave animation as "smooth scroll" — specify numbers.
- **Quality checklist:** Include explicit pass/fail items (15-20) that the coding agent must verify before delivering. This catches half-implemented animations, missing responsive breakpoints, broken links, and missing SEO tags.
