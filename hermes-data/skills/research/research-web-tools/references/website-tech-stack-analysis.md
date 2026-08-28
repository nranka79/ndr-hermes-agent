# Website Tech-Stack Analysis

A multi-dimensional analysis methodology for any live website. Do NOT settle for a content summary — systematically cover each layer below.

## Workflow

```bash
# 1. Fetch full HTML
curl -sL "https://example.com/page" > /tmp/page.html

# 2. Extract fonts
grep -oP 'families:[^]]*]' /tmp/page.html
grep -oP 'WebFont\.load' /tmp/page.html

# 3. Extract all image URLs (asset format mix)
grep -oP 'src="[^"]*\.(avif|webp|png|jpg|jpeg|svg|gif)[^"]*"' /tmp/page.html | sort -u

# 4. Extract JS libraries
grep -oP 'src="[^"]*\.js[^"]*"' /tmp/page.html | sort -u

# 5. Extract CSS links (framework/integrity hashes)
grep -oP 'href="[^"]*\.css[^"]*"' /tmp/page.html | sort -u

# 6. Extract inline animation CSS (GSAP/scroll patterns)
grep -oP 'style="[^"]*transform[^"]*opacity[^"]*"' /tmp/page.html | head -10

# 7. Extract structured data / Schema.org
grep -oP '"@type":"[^"]*"' /tmp/page.html | sort -u

# 8. Extract tracking / analytics IDs
grep -oP '(GTM-[A-Z0-9]+|UA-[0-9-]+|G-[A-Z0-9]+|fbq\(.init.[^)]+\)|clarity[^"]*"[^"]*")' /tmp/page.html
```

## Dimensions to Cover

### 1. Text Stack
| Aspect | What to extract |
|--------|----------------|
| CMS/Platform | Look for `data-wf-*` (Webflow), `wp-content` (WordPress), `<meta name="generator"`, build IDs |
| CSS framework | Output CSS file names, SRI hashes, CDN origin |
| Font loading | Google WebFont Loader, `@font-face`, preconnect/preload hints |
| Font families | Names, weights loaded, classification (serif/sans/display) |
| Typography meta | `<title>`, OG/Twitter descriptions, meta description |

### 2. Artwork & Visuals (Technical)
| Aspect | What to extract |
|--------|----------------|
| Image formats | AVIF > WebP > PNG > SVG hierarchy |
| Image CDN | cdn.prod.website-files.com, cloudinary, imgix, etc. |
| Total assets | Count unique image URLs |
| Art direction | Photography vs illustration vs vector vs texture overlays |
| Favicon/apple-touch-icon | Check for branded icons |
| Responsive images | srcset/sizes attributes, breakpoints |
| Image dimensions | grep `width="N"` — hero (full-width ~1900+), content (~500-800px), thumbnails |
| Loading strategy | `loading="lazy"` vs `loading="eager"` — which are above/below fold |

### 3. Visual Language & Artwork Analysis (Style)

This section goes beyond technical format — it analyzes the *look and feel* of imagery, what makes it appealing, and the overall visual language. Essential when the goal is to **reproduce or adapt the visual system** via a coding agent.

#### 3a. Art Style Categories

Most marketing websites blend multiple visual styles. Identify each:

| Style | Clues in HTML |
|-------|--------------|
| **Full photography** | Large AVIF/WebP images, realistic lighting, landscape aspect ratios |
| **Graphic illustrations** | "Group" or "Illustration" named assets, composite/tiered dimensions |
| **Vector graphics** | `.svg` files, inline SVGs, icon libraries (Iconify, FontAwesome) |
| **Watercolour / organic textures** | Filenames containing "watercolor", "brush", "paper", "texture" |
| **Mixed / hybrid** | Semi-realistic base + illustrated overlays — check alt text for "illustration" |
| **Isometric / 3D** | Angular lines, isometric grid patterns in images |

**Key question**: Is the art style *photorealistic*, *illustrated/cartoonish*, *vector-flat*, or a *hybrid*? Premium real estate sites often blend photo backgrounds with illustrated overlays.

#### 3b. Colour Palette Inference

Extract colour clues from HTML/CSS:

```bash
# Logo colours (SVG fills/strokes)
grep -oP 'fill="[^"]*"' /tmp/page.html | sort -u
grep -oP 'stroke="[^"]*"' /tmp/page.html | sort -u

# Background section colours (class names + inline)
grep -oP '(background|background-color):[^;"]*' /tmp/page.html | sort -u
grep -oP 'class="[^"]*(dark|light|green|gold|warm|soft|cream)[^"]*"' /tmp/page.html | sort -u

# Button variants — often reveal accent palette
grep -oP 'class="[^"]*(btn|button|cta|link-block)[^"]*"' /tmp/page.html | sort -u
```

Document as a table:
| Colour | Role | Evidence |
|--------|------|----------|
| `#F0F4EE` (pale green-white) | Logo / brand accent | SVG fill attribute |
| Dark green | Section backgrounds | Class name `background-grass-green` |
| Gold | CTA variants | Class `gold` on link-block |
| Warm yellow | Overlay / atmosphere | Watercolour overlay image, hero toning |

#### 3c. Texture & Material Quality

| Clue | What it indicates |
|------|-------------------|
| Watercolour-named assets | Hand-painted organic feel, warmth |
| Grain/noise filters | Editorial/film texture |
| Gradient meshes | Modern, smooth, premium |
| Flat colours + sharp lines | Vector/flat design, modern/startup |
| Glassmorphism (backdrop-filter: blur) | Contemporary UI sheen |

#### 3d. Image Asset Sizing & Composition

```bash
# Get all image widths (aspect ratio clues)
grep -oP 'width="[0-9]+"' /tmp/page.html | sort -t= -k2 -n | uniq
```

Interpretation:
- **~1900px+** — Full-bleed hero/background panoramas
- **500-800px** — Content-width illustrations, half-page
- **~300-400px** — Card thumbnails, popup images
- **~100-150px** — Logos, preloader icons, favicons

#### 3e. Visual Appeal Analysis

Describe *why* the artwork works:
- **Lighting** — Golden-hour warmth vs cool/modern vs high-key/bright
- **Depth** — Layering (background photo → illustrated elements → UI overlays)
- **Consistency** — Do all images share a unified colour temperature?
- **Contrast** — Photorealism vs illustration creates aspirational-but-approachable feel
- **Texture variety** — Mix of clean vector UI and organic/hand-painted elements

### 4. Page Layout & Composition

Map the page structure to understand how sections are composed visually:

```bash
# Extract heading hierarchy (h1 → h2 → h3)
grep -oP '<h[1-3][^>]*>[^<]*</h[1-3]>' /tmp/page.html | sed 's/<[^>]*>//g'

# Extract section layout classes
grep -oP 'class="[^"]*(grid|layout|section|hero|content|container)[^"]*"' /tmp/page.html | sort -u

# Identify alternating layout patterns (zigzag, full-width, grid cards)
```

Describe as an ASCII layout map:
```
┌──────────────────────────────┐
│  HERO — Full-bleed image     │
│  Title overlaid (center)      │
├──────────────────────────────┤
│  ┌─────┐  ┌──────────────┐  │  ← ZIGZAG alternating
│  │TEXT │  │ ILLUSTRATION │  │     (text-left/image-right)
│  └─────┘  └──────────────┘  │
│  ┌──────────────┐  ┌─────┐  │
│  │ ILLUSTRATION │  │TEXT │  │  ← (image-left/text-right)
│  └──────────────┘  └─────┘  │
├──────────────────────────────┤
│  STATS GRID (3-column)       │
├──────────────────────────────┤
│  CTA — Full-width, green bg  │
└──────────────────────────────┘
```

Key questions:
- Does the layout alternate between full-width and contained sections?
- Do content blocks alternate direction (zigzag pattern)?
- Where does the page use asymmetry vs symmetry?
- What is the whitespace density? (check `padding-section-large`, `margin-bottom` classes)

### 5. Motion & Animation
| Aspect | What to extract |
|--------|----------------|
| Smooth scroll | Lenis (`@studio-freight/lenis`), Locomotive Scroll, barba.js |
| Animation engine | GSAP (and plugins: ScrollTrigger, Flip, MotionPath), Framer Motion, anime.js |
| Inline animation styles | `data-w-id` (Webflow native), inline `transform` + `opacity` on elements |
| Animation patterns | `translate3d(0, Npx, 0)` reveals, horizontal slide-ins, parallax, fade |
| Config | lerp value (smoothness), wheelMultiplier, RAF loop |
| Responsive animation | Check media query blocks for breakpoint-specific animation values |

### 6. Other Tech & Tracking
| Aspect | What to extract |
|--------|----------------|
| Analytics | Google Tag Manager, GA4, Facebook Pixel, Microsoft Clarity, Hotjar |
| Chat/widgets | Elfsight, Tidio, Intercom, WhatsApp floating buttons |
| Structured data | Schema.org types used (WebPage, RealEstateAgent, Product, LocalBusiness) |
| SEO | Canonical URL, breadcrumb list, Open Graph tags |
| Regulations | RERA numbers, disclaimers, privacy policy links |
| Social proof | Instagram/LinkedIn/Facebook links |

## Common CMS Signatures

| CMS | HTML signature |
|-----|---------------|
| **Webflow** | `data-wf-domain`, `data-wf-page`, `data-wf-site`, `w-mod-js`, webflow.[hash].css |
| **WordPress** | `wp-content`, `wp-embed`, `wp-block-library` |
| **Shopify** | `shopify.com`, `cdn.shopify.com`, `Shopify.shop` |
| **Squarespace** | `squarespace.com`, `static1.squarespace.com` |
| **Wix** | `wixstatic.com`, `Wix.com` |

## Coding Agent Prompt Generation

When the **goal is to generate a detailed prompt for a coding agent** to reproduce the website's design system for another product/service:

### Workflow

1. **Complete all analysis dimensions above first** — text stack, visual language, motion, layout, tracking
2. **Identify the user's provided assets** — what imagery/artwork will be available for the new site
3. **Generate the prompt** structured as:

```
## DESIGN SYSTEM REFERENCE

### Art Style
<from Visual Language analysis — describe the hybrid style, what makes it appealing>

### Colour Palette
<from Colour Palette Inference — table of colours, roles, hex codes>

### Typography
<from Text Stack analysis — fonts, weights, usage>

### Layout Architecture
<from Page Layout & Composition — ASCII map, section descriptions>

### Motion & Animation
<from Motion & Animation analysis — engine, patterns, config>

### Image Assets Provided
<list of provided assets and how to use/adapt them>

### Image Generation Instructions
<if new images need to be created — style guidance, colour matching, 
 texture requirements, what to keep consistent with the reference site>

### Technical Requirements
-CMS/platform choice
-Performance (AVIF, lazy loading, SRI)
-Responsive breakpoints
-Analytics/tracking needed
```

### Important Rules

- Do NOT embed absolute URLs from the analyzed site in the agent prompt (they become stale)
- Do describe the visual *language* (what makes it appealing) rather than just listing technologies
- Include the "texture quality" dimension — modern web design relies heavily on material feel
- If the user has specific provided imagery, include instructions on how to repurpose it:
  - "Use these photos as hero/background assets, maintaining the golden-hour warm tone"
  - "The illustrations should be regenerated in the same hybrid vector style with saturated greens"
  - "Keep the same watercolour overlay texture technique for atmospheric depth"

### Agent Prompt Delivery

Write the prompt as a single well-structured document file, deliver to the user for review before the agent uses it. Get approval before executing.

## User Preference Notes

When a user sends a URL (especially a real-estate / marketing website) asking for analysis:
- Do a FULL multi-dimensional analysis — don't stop at content summary
- Cover ALL dimensions: text stack, artwork technical, visual language, motion/animation, layout, and other tech — as separate sections
- Be concise and structured (bullets/labels, not paragraphs)
- For Nishant (NDR): action-first, comprehensive, deep — no "what would you like", no shallow content summary. The user WILL call you out if you only give a surface-level summary instead of the full multi-layered breakdown they asked for. When they ask for "analysis" of a website, assume they want: text stack + artwork/visuals + motion/animation + layout + visual language combined.
