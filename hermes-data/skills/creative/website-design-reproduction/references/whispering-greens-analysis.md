# Whispering Greens — Visual DNA Analysis

Full visual DNA analysis of whisperinggreens.com/green-framework (the reference site for animated website reproduction).

## Site Details

| Property | Value |
|---|---|
| URL | https://www.whisperinggreens.com/green-framework |
| Builder | Webflow |
| Type | Real estate / plotted development |
| Target Audience | Nature-conscious home buyers, premium segment |

## Artwork & Imagery Style

The site uses **3 distinct visual styles layered together**:

### A. Large-format landscape photography (AVIF)
- Hero image (1918×? px), grasslands background (1921×? px) — full-bleed, panoramic
- Photorealistic, golden-hour lighting, warm tones
- Used as atmospheric backdrops, not focal content
- Slight desaturation + warm tint — editorial, premium real-estate style

### B. Graphic composite illustrations (the "Group" series)
- 3 location illustrations: Hesarghatta (801px), Avalahalli (803px), Botanical Garden (782px)
- **Hybrid style**: semi-realistic landscape base + illustrated/stylized vector elements overlaid
- Characters/figures as simplified vector silhouettes
- Bright, saturated greens (foliage) vs soft warm sky gradients

### C. Vector graphics & icons
- SVG logo — organic flowing leaf/foliage shapes, monochrome fill #F0F4EE
- Arrow icons — white and black variants in WebP
- Social icons — Instagram, LinkedIn via Iconify inline SVGs
- Watercolour texture overlay — `yellow-watercolor-circle-white-paper 1.avif` (935×? px, 12KB)

## Colour Palette

| Colour | Role |
|---|---|
| Pale green-white #F0F4EE | Logo, brand accent |
| Dark green | Background sections |
| Gold | CTA button variant |
| White | Text on dark backgrounds |
| Warm golden-yellow | Sun overlay, hero lighting |
| WhatsApp green #25D366 | Floating FAB |

## Typography Stack

| Role | Font | Weights |
|---|---|---|
| Hero + Display headings | **Bellefair** | 300–700 (serif, editorial) |
| Body / UI text | **Questrial** | 300–700 (geometric sans) |
| Secondary headings | **Raleway** | 300–700 (sans-serif, versatile) |

## Layout Architecture

```
┌──────────────────────────────────────┐
│ NAVBAR (transparent, overlays hero)  │
├──────────────────────────────────────┤
│                                      │
│ HERO — Full-bleed panoramic AVIF     │
│ "the green framework" title          │
│ (centered, scroll-reveal anim)       │
│                                      │
├──────────────────────────────────────┤
│ Intro text (2-column split)          │
│ "nature isn't an afterthought..."    │
├──────────────────────────────────────┤
│ "Nature's Neighbours" sections       │
│                                      │
│ ┌─────────┐  ┌──────────────────┐    │
│ │ TEXT    │  │ ILLUSTRATION     │    │
│ │ (left)  │  │ (right, 580px)   │    │
│ └─────────┘  └──────────────────┘    │
│                                      │
│ ┌──────────────────┐  ┌─────────┐    │
│ │ ILLUSTRATION     │  │ TEXT    │    │
│ │ (left, 537px)    │  │ (right) │    │
│ └──────────────────┘  └─────────┘    │
│                                      │
│ ┌─────────┐  ┌──────────────────┐    │
│ │ TEXT    │  │ ILLUSTRATION     │    │
│ │ (left)  │  │ (right, 577px)   │    │
│ └─────────┘  └──────────────────┘    │
│                                      │
├──────────────────────────────────────┤
│ GREEN COMMITMENTS (3-column grid)    │
│ greener plots | organic farming |    │
│ smart landscapes | biodiversity      │
│ gardens | Miyawaki                   │
├──────────────────────────────────────┤
│ Grassland photo (full-width)         │
│ + Watercolour sun overlay            │
├──────────────────────────────────────┤
│ CTA: "Find your home..."             │
│ (green background, centered text)    │
├──────────────────────────────────────┤
│ FOOTER (structured grid)             │
└──────────────────────────────────────┘
```

**Layout rhythm:** The 3 location sections alternate layout direction (zigzag) — text-right/image-left, then image-left/text-right, then text-right/image-left.

## Motion & Animation Specification

| Element | Animation | Details |
|---|---|---|
| Smooth scroll | Lenis | v1.0.33, lerp: 0.05, wheelMultiplier: 1, RAF loop |
| Scroll triggers | GSAP ScrollTrigger | v3.15.0 |
| Content reveals | Fade + slide up | Start: translate3d(0, 200px, 0) + opacity: 0.1 → End: identity + opacity: 1 |
| Hero headline | Fade + slide up (larger) | Start: translate3d(0, 250px, 0) + opacity: 0 |
| Side panel images | Horizontal slide | Right panel: translate3d(100%, 0, 0) → identity; Left panel: translate3d(-100%, 0, 0) → identity |
| Post-load fix | window.addEventListener('load', lenis.update) | Prevents bottom whitespace |
| Per-element targeting | data-w-id attributes | Each section element independently animated |

## Responsive Breakpoints

| Breakpoint | Changes |
|---|---|
| ≥992px (desktop) | Horizontal slide-ins; full hero image |
| 991–768px (tablet) | Animation offset 200px vertical; grid reorder |
| 767–480px (mobile landscape) | Stacked layout; smaller images; reduced animation |
| ≤479px (mobile) | Full-width stacked; 50px WhatsApp button; reduced padding |

## Performance Specs

- **Image format hierarchy:** AVIF (primary) → WebP (srcset fallback) → PNG/SVG (logos/icons)
- **Lazy loading:** below-fold images; hero loading="eager"
- **Responsive images:** srcset with 500w, 800w, 1080w variants
- **Font loading:** WebFont loader with preconnect
- **SEP:** Schema.org structured data, OG/Twitter meta tags

## Visual Language Summary for Repurposing

| Attribute | Whispering Greens DNA |
|---|---|
| Art style | Hybrid: photographic landscapes + vector-graphic composite illustrations |
| Tone | Warm, aspirational, serene, premium-nature |
| Colour family | Warm greens, golds, off-whites, dark green accents |
| Texture | Clean digital + watercolour organic overlays |
| Image format | AVIF primary, WebP fallback, PNG/SVG for brand |
| Layout | Full-bleed hero → alternating zigzag content → grid stats → full-width CTA |
| Typography | Bellefair (serif display) + Questrial + Raleway (sans body) |
| Animation | Lenis smooth scroll + GSAP scroll-triggered fade-up + horizontal slides |

## Application Pattern (used in Ranka Udaya)

When applying this DNA to another project (see `references/ranka-udaya-extraction.md`):
- Adapt colour palette to the new brand (e.g., navy+gold instead of greens)
- Adapt typography to available fonts (e.g., Playfair Display + Geist)
- Keep ALL animation config values exactly the same
- Keep layout architecture the same (hero → zigzag → grid → full-width CTA)
- Replace imagery with the new project's assets
- Pre-fill all content in the prompt — no placeholders
