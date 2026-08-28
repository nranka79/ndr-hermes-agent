# From-Scratch PPTX IM Builder (pptxgenjs)

Build an investor-ready Information Memorandum as a .pptx presentation from scratch using pptxgenjs. DRAAS brand colors and standard IM slide structure.

## When to Use

- User asks for an "IM", "information memorandum", "investor presentation", "deck", "presentation with brand colors"
- User provides market research data and wants it turned into a polished slide deck
- User wants DRAAS-branded output (navy + gold + cream)

## DRAAS Brand Colors

```javascript
const C = {
  navy: "1B2A4A",       // Primary — deep navy
  gold: "C9A84C",       // Secondary — warm gold
  goldLight: "D4B96A",  // Gold light
  goldPale: "E8D5A3",   // Gold pale (for text)
  cream: "F5F3EE",      // Card background — warm off-white
  creamLight: "FAF9F6", // Very light cream
  white: "FFFFFF",      // White
  text: "2D2D2D",       // Dark text
  textLight: "6B7280",  // Medium gray text
  gray: "E5E7EB",       // Borders / dividers
  teal: "1A7A7A",       // Accent teal
  tealLight: "E8F4F4",  // Teal tint background
};
```

## Standard IM Slide Structure (13 slides — Basic)
...

## Expanded Investor Deck Structure (14 slides — Comprehensive)

For projects requiring deeper analysis — add TOC, Introduction, Sketch breakdown, Infrastructure, Development Potential table, Tenant Profile, and Premium Vision sections.

| # | Slide Type | Content |
|---|-----------|---------|
| 1 | **Title** | Project name, location tagline (e.g. "Next to [Metro Station]"), company, confidential |
| 2 | **Table of Contents** | 10 numbered chapters with two-column card layout |
| 3 | **Introduction to Land Location** | Left: 5-point location overview (address, extent, metro, road, land use). Right: Key metrics panel (area, value, metro distance, floors) |
| 4 | **Land Details** | From survey: full tabular (parameter/detail/value/extent). Plus valuation bar at bottom (rate, total value, per acre, per gunta, guidance range) |
| 5 | **Survey Sketch & Area Breakdown** | Horizontal bar chart (Garments/Front Open/Balance) with scale. Right panel: Sketch reference (components, access, landmarks) |
| 6 | **Location Advantage** | Metro hero card (gold accent) + 6-point connectivity grid + micro-market stats strip |
| 7 | **Key Location Highlights** | 6 numbered cards (Metro proximity, Road frontage, IT corridor, Industrial ecosystem, Mixed-use, Growth corridor) |
| 8 | **Infrastructure & Social Accessibility** | Two-column: Current (roads/metro/power/water/drainage/telecom) + Upcoming (5 projects: Metro Phase 2, Elevated Road, PRR, etc.). Social strip at bottom (schools/hospitals/retail) |
| 9 | **Development Potential — FAR, Zoning & Approvals** | **Two tables:** (A) Zoning/FAR matrix — 12-row table (authority, FAR, coverage, height, setbacks, parking). (B) Development Scenarios — 3 scenarios (Conservative FAR 2.0 / Moderate 2.5 / Aggressive 3.0+) with built-up sqft, floors, carpet area |
| 10 | **Comprehensive Market Analysis** | Rental values table (7 properties) + Recent lease deals table (6 transactions with dates) + Capital values strip |
| 11 | **Target Audience & Tenant Profile** | 6 tenant segment cards (Co-working, Medical, Retail/F&B, Banks, Education, IT/ITES) — each with space need, rent bracket, demand indicator |
| 12 | **Premium A-Grade Development Vision** | Vision statement hero + 4 pillar cards (Ground Retail, Upper Office, Parking/Logistics, Sustainability) |
| 13 | **Financial Overview & Investment Thesis** | Two-column cost + revenue. Returns row (Land Value, Metro Premium, Appreciation, Yield). Thesis bar at bottom |
| 14 | **Disclaimer & Sources** | Full branded disclaimer with gold dividers on navy background |

## Helper Functions (Always Use)

```javascript
function makeShadow() {
  return { type: "outer", color: "000000", blur: 8, offset: 2, angle: 135, opacity: 0.12 };
}

function addFooter(slide, slideNum) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.25, w: 10, h: 0.375,
    fill: { color: C.navy }
  });
  slide.addText("DRAAS | Confidential", {
    x: 0.5, y: 5.25, w: 5, h: 0.375,
    fontSize: 8, color: C.goldLight, fontFace: "Calibri", valign: "middle"
  });
  slide.addText(String(slideNum), {
    x: 8.5, y: 5.25, w: 1, h: 0.375,
    fontSize: 8, color: C.goldLight, fontFace: "Calibri",
    align: "right", valign: "middle"
  });
}

function addSectionBar(slide) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.06, h: 5.625,
    fill: { color: C.gold }
  });
}

function addTitleBar(slide, title, subtitle) {
  // Top gold accent line
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.04, fill: { color: C.gold }
  });
  // Gold vertical accent beside title
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 0.2, w: 0.08, h: 0.5, fill: { color: C.gold }
  });
  slide.addText(title, {
    x: 0.65, y: 0.15, w: 8.5, h: 0.55,
    fontSize: 20, fontFace: "Calibri", bold: true, color: C.navy, valign: "middle"
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.65, y: 0.6, w: 8.5, h: 0.3,
      fontSize: 11, fontFace: "Calibri", color: C.textLight, valign: "top"
    });
  }
}
```

## Key Design Patterns

### Title Slide (Slide 1)
- Full navy background with gold accent stripe near bottom
- Gold vertical bar on left for structure
- Company name in gold with charSpacing
- Project name in 38-40pt white bold
- Subtitle + description in gold/goldPale

### Stat Cards (Executive Summary, Market Overview)
- Cream (#F5F3EE) background with shadow
- Large 18-22pt navy value, 9pt gray label below
- 4 cards per row at 2.35" width each

### Content Cards (Highlights, Location)
- Cream background + shadow
- Gold left accent bar (0.05" wide)
- Bold navy title + gray description
- 2x3 or 3x2 grid layout

### Data Tables (Rentals, Land Rates, Transactions)
- Navy header row with white text
- Alternating white/cream rows
- 0.5px gray borders
- Right-aligned ₹ values in bold

### Tables with `rowH`
- Always set `rowH` as an array matching row count, e.g. `[0.3, 0.28, 0.28, 0.28]`
- Set `autoPage: false` to prevent splitting across slides

### Table row coloring (alternating)
```javascript
.row.map((cell, ci) => ({
  text: cell,
  options: { fontSize: 8.5, color: C.text,
    fill: rowIdx % 2 === 0 ? { color: C.white } : { color: C.cream } }
}))
```

## Installation

```bash
npm install pptxgenjs
```

## Running

```javascript
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";

// ... build slides ...

pres.writeFile({ fileName: "path/to/output.pptx" })
  .then(() => console.log("Saved"))
  .catch(err => console.error(err));
```

## Pitfalls

- **NEVER use "#" with hex colors** — e.g. `"#FF0000"` corrupts the file
- **NEVER reuse option objects across calls** — PptxGenJS mutates in-place. Use factory functions or inline objects for each call.
- **Shadow offset must be non-negative** — for upward shadows use `angle: 270` with positive offset
- **Text has internal margin by default** — set `margin: 0` when aligning text to shapes at same x-position
- **Gradient fills not natively supported** — use overlapping shapes or gradient background images
- **Verify content**: After creating, unzip the pptx and check `ppt/slides/slide*.xml` for text content — quick text validation
