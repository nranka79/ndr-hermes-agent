# Ranka Udaya — Worked Example (June 2026)

Full extraction from https://rankaudaya.com/ (Framer-built site) for a coding agent prompt.

## Source Site Details

| Property | Value |
|---|---|
| URL | https://rankaudaya.com/ |
| Builder | Framer (published Jun 5, 2026) |
| Project | Ranka Udaya — premium plotted development by DRA Group |
| Location | Sarjapura, Bengaluru |
| Target Audience | Investors, end-users, NRIs |
| Reference for animation | Whispering Greens |

## Extracted Assets: 22 files total

### Icons & SVGs (4 files)
| File | Size | Type | Notes |
|---|---|---|---|
| `11KSGbIZoRSg4pjdnUoif6MKHI.svg` | 215 B | SVG Arrow right | White, 40×40 |
| `6tTbkXggWgQCAJ4DO2QEdXXmgM.svg` | 214 B | SVG Arrow left | White, 40×40 |
| `PVs1xkFcrlekEXYy3eDTiIcboFg.png` | 1.2 KB | Icon check | 208×208 |
| `biE3Z1oyDUGwxpuw1KTNDSTQYDs.png` | 2.1 KB | Icon plot/land | 242×270 |
| `pyApE8qFqrYn67ZX3oj5QwL6gA.png` | 6 KB | Icon building | 512×512 |

### Logo (1 file)
| File | Size | Type |
|---|---|---|
| `tEzAjVmq3BTvnGDdugXB2PoSI.png` | 21 KB | Brand logo, 1875×1875 |

### Hero & Background Images (2 files)
| File | Size | Usage |
|---|---|---|
| `9T2JT6zZWGiMK7rRONlfx0SKw.jpg` | 126 KB | Hero background, 6000×4000 original |
| `p5lxYAWkIZXkqOvc6JmYEGrbg.jpg` | 203 KB | Alternate hero/background, 1500×1001 |

### Content Section Images (5 files, all ~1024×683)
| File | Size | Likely role |
|---|---|---|
| `qCCtXJ4u0Ev9y1M9E7srYnTFtY.png` | 394 KB | Architecture/building shot, 6400×4267 original |
| `1bG9vUaDWUbaZJcrfVEsJyNsik.png` | 390 KB | Community/lifestyle |
| `8Bs5E2taSFPMTktpqhYu40etMo.png` | 402 KB | Interiors/design |
| `JXKzoowLn0roxF9P7xwRTRZT7OU.png` | 390 KB | Location/neighbourhood |
| `R6TKwbAe1yOW9Wfb7ap9qu3rpIE.png` | 401 KB | Amenities |

### Gallery Images (4 files, all ~1024×682)
| File | Size |
|---|---|
| `Dg0x22gVO88BUqRlBx43hVrLdtY.png` | 300 KB |
| `Dmi2Z9jn3KIrT6sIjvUDcm0w4U8.png` | 268 KB |
| `UPy9jPKABOrbwvaZ43LThaFLNE.png` | 301 KB |
| `Upwvj0F4tdfRUnfh9QmifQ7aMY.png` | 344 KB |

### Background Sections (2 files, both 1024×576)
| File | Size |
|---|---|
| `glbBI4wqnA099vrIo5s1G46SSs.png` | 214 KB |
| `Nc60JT8IUWbTFCbR6pXNMQM6aA.png` | 40 KB |

### Graphics (3 files)
| File | Size | Description |
|---|---|---|
| `Km4Eb0pvEZM5Cltqr6IkrAJlO6U.png` | 458 KB | Location map, 1276×1164 |
| `WSxy0RGnsfMIlrlonQ3quIige6A.png` | 321 KB | Master plan, 1264×842 |
| `ekoiBP3Cn5iibUZLD4719P14uE.webp` | 127 KB | Stats infographic, 1343×1346 |

## Extracted Content Summary

### Hero
- Tag badges: "LIMITED PLOTS" / "PRIME ADDRESS" / "SMART PRICE"
- Headline: premium freehold plots narrative
- Metrics: Exclusive Plots / 1.75 Ac Total Area / Wide Roads / RERA Approved
- CTAs: "Explore Building Options" / "View Master Plan"

### Key Sections
1. **Premium Plotted Development** — "Limited Plots. Prime Address. Smart Value." + 4 USPs (Freehold, Appreciation, Flexibility, Rental Income)
2. **What You Get** — Plot stats (600-1200 sqft, 2400 max buildable, G to G+3, Freehold, 38 plots, 9M roads)
3. **Building Possibilities** — 4 options: G (personal), G+1 (joint family, ₹15-20K/mo rent), G+2 (live+invest, ₹40-50K/mo), G+3 (max returns, ₹80K/mo)
4. **Why Ranka Udaya** — Fixed Price Contract, Guaranteed Timeline, RERA & HNTDA Approved, Eco-Friendly
5. **Growth Catalysts** — SWIFT City by KIADB + Hosur Airport
6. **About DRA** — 30+ years, 10M+ sqft, 1000s families
7. **Location** — Hospitals (12), Schools (17), IT Parks (10), Restaurants, Shopping

### Brand Details
- Developer: DRA Group ("Right Quality, Right Price, Right Time")
- RERA: TNRERA/30/LO/0642/2026
- WhatsApp: +919900029200
- Typography: Geist + Playfair Display
- Colour palette: Deep navy (#1a1a2e) + Gold (#c9a84c)

## Colours Identified from Site

| Token | Colour | Usage |
|---|---|---|
| Primary | Deep navy (#1a1a2e) | Background sections, footer |
| Accent | Gold (#c9a84c) | CTAs, highlights |
| Light bg | Warm off-white (#faf8f5) | Content areas |
| Text light | White | On dark backgrounds |
| Text dark | Near-black | Body text |

## Animation DNA Applied (Whispering Greens)

- Lenis smooth scroll (lerp: 0.05)
- GSAP ScrollTrigger v3.15.0
- Scroll-reveal: translate3d(0, 200px, 0) + opacity 0 → identity + opacity 1
- Hero: translate3d(0, 250px, 0) — larger offset
- Horizontal slide-ins for side panels
- Count-up stats on scroll

## Download Command Pattern

```bash
# Download with moderate size
curl -sL "https://framerusercontent.com/images/<hash>.<ext>?scale-down-to=1024" -o "friendly-name.<ext>"
```

## Coding Agent Prompt Output

See `rankaudaya-coding-agent-prompt.html` in the ZIP — all content pre-filled, no placeholders.
Includes: 15-item quality checklist, asset file mapping table, Whispering Greens animation DNA, complete colour palette, full layout architecture.
