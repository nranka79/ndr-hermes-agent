---
name: home-interior-design-workflows
description: "End-to-end home interior design for non-architects — from empty-house measurements and functional briefing through 3D modeling, material specification, construction methodology selection, to an execution-ready package for contractors. Covers space-by-space planning, theme/style selection, tool comparisons, AI-assisted ideation, and Indian-market cost/material references."
version: 1.0.0
author: Nishant Ranka & Hermes Agent
license: MIT
platforms: [linux, macos, web]
metadata:
  hermes:
    tags: [interior-design, DIY, home-renovation, space-planning, construction, materials, bangalore, india]
    related_skills: [interior-design-scope-checklist]
---

# Home Interior Design Workflows

A complete methodology for non-architects/non-designers to design their own home interior from scratch — from an empty shell to a specification package an execution team can build from.

**Subsumed skill:** The former `interior-design-scope-checklist` is now integrated as **Appendix A: Vendor Scope Checklist** below. This skill covers the *DIY* side; the appendix covers the *vendor evaluation* side.

---

## Appendix A: Interior Design Firm — Vendor Scope Checklist

Use this when shortlisting or onboarding interior design firms. The checklist ensures the firm's scope covers everything from concept to execution.

### The 10-Point Scope

1. **Mood Boards & Concept Direction** — Reference images / mood boards to establish overall look & feel
2. **Full-House Design** — All rooms designed cohesively, not just selective spaces
3. **Civil & Structural Modifications** — Wall changes, arches, cutouts, or structural work
4. **Material Specification for All Finishes** — Wallpaper, paint, cladding, frames, lighting — every item specified
5. **Vendor Details for Every Material** — Vendor name + make + model number / series / line
6. **Make vs. Buy Decisions** — What's fabricated on-site vs factory-order vs purchase-and-install
7. **Execution Vendors for Every Finish** — Every trade assigned for each material/finish
8. **Electrical & Plumbing Design** — All points and modifications designed and vendor-assigned
9. **Application Methodology** — Surface prep, coats, curing time, technique for every finish
10. **Post-Award Change Management** — At least 2-3 rounds of revisions for material unavailability or constraints

### YES/NO Checklist Table

| # | Requirement | YES / NO |
|---|-------------|----------|
| 1 | Mood boards / concept references provided | ☐ |
| 2 | Full-house design (all rooms) | ☐ |
| 3 | Civil / structural modification recommendations | ☐ |
| 4 | Detailed material specification for every finish | ☐ |
| 5 | Vendor name + make + model/series for every material | ☐ |
| 6 | Make vs. buy guidance for each element | ☐ |
| 7 | Execution vendor identified for every material/finish | ☐ |
| 8 | Electrical points + plumbing designed and vendor-assigned | ☐ |
| 9 | Application methodology documented for every finish | ☐ |
| 10 | At least 2-3 rounds of post-award revisions for constraints | ☐ |

Forward the checklist to the firm, have them mark YES/NO in writing, retain the signed confirmation.

When drafting an email with the checklist, the template at `~/.hermes/skills/.archive/interior-design-scope-checklist/templates/html-email-template.html` can be used with Gmail API (see `gws-automation` skill for sending pattern).

---

## When to Use This Skill

Trigger when the user asks or implies any of:
- "I want to design my own home / flat / house"
- "Help me plan the interiors of my new house"
- "What software can I use to create a 3D model of my home?"
- "How do I figure out what goes in each room?"
- "Give me a step-by-step process for home interior design"
- "I have a floor plan, now what?"
- "What materials should I use for walls/floors/ceilings?"
- "How do I brief a contractor for my interior work?"

---

## The Complete 7-Phase Workflow

### Phase 1: Document & Measure Your Space

**Goal:** Create a complete digital record of the empty house.

1. Gather existing documents: floor plan, survey drawing, structural/electrical plans
2. Systematically photograph every room from all 4 corners + close-ups of switches, plumbing, AC points, windows, columns
3. Record a video walkthrough
4. Verify measurements: room length/width, ceiling height, window/door dimensions, column projections
5. Annotate floor plan with: north direction, switch positions, plumbing points, gas line entry, floor-to-slab height
6. Check building rules (OBR for apartments) for restrictions on structural changes, plumbing modifications, façade alterations
7. **Deliverable:** Google Drive folder with annotated floor plan, organized photos, video walkthrough, restriction notes

### Phase 2: Define Functional Use — Space by Space

**Goal:** Document exactly what happens in each room. Form follows function.

For each room, answer a structured questionnaire covering:
- **Living Room:** Primary use, seating capacity, TV placement & height, storage needs, lighting layers (ambient/task/accent), wall elements (art, shelves, accent wall), electrical points, window treatment, flooring
- **Kitchen:** Open vs closed, layout shape (L/U/straight/galley), work triangle distances (sink-stove-fridge), appliance list, storage strategy (upper/base/pull-out/carousel), countertop material, lighting (task under-cabinet essential), backsplash, electrical (6-8 sockets + 15A for microwave)
- **Bedroom:** Bed size & placement (head on solid wall, 2ft walk each side), wardrobe type & internal layout, dressing table, lighting (warm 2700K bedside, auto-on wardrobe lights), blackout curtains, feature wall
- **Bathroom:** Wet/dry zones, shower partition, vanity with under-sink storage, mirror with anti-fog LED, exhaust fan sizing, waterproofing (tanking on floors + walls up to 6ft), slope to drain
- **Home Office:** Desk placement (perpendicular to window, min 48"x24"), ergonomics (adjustable chair, monitor at eye level), wall elements (whiteboard/pin-up/projector), task lighting (4000K), cable management, tech setup (webcam light, ethernet)
- **Dining:** Table size + clearance (3ft each side), crockery storage, pendant height (30-36" above table)
- **Entryway:** Shoe rack, coat hooks, key tray, mirror, easy-clean flooring
- **Balcony:** Utility vs leisure, outdoor-rated furniture, planters, shade solution, anti-skid flooring, waterproofing of slab

**Deliverable:** One-page functional brief per room, rough furniture placement on floor plan, must-have vs nice-to-have list

### Phase 3: Ideation & Theme Selection

**Goal:** Define the look and feel — architectural theme, color palette, emotional character.

1. **Browse inspiration sources:** Pinterest (per room), Houzz, Architectural Digest, Home-Designing, DesignCafe, Livspace blogs, Vogue trends
2. **Collect 10-20 reference images** per room with annotations on *why* you like each element
3. **Choose a style** from the spectrum:
   - Warm Minimalist (2025-26 #1 trend — clean lines, warm materials, natural textures)
   - Japandi (Japanese + Scandinavian — low furniture, neutral, balanced)
   - Modern Contemporary (clean, sleek, gray/white/black)
   - Scandinavian (bright, white + wood, functional cozy)
   - Industrial (exposed concrete/brick, metal, urban loft)
   - Indian Contemporary (jaali screens, carved wood, kotah stone, saffron/indigo accents)
4. **Build mood boards** per room — Google Slides or Pinterest boards
5. **Select color palette** using 60-30-10 rule (60% dominant wall, 30% secondary furniture, 10% accent)
6. **2025-2026 trend keywords:** lived-in luxury, dark wood revival, curved forms, earthy tones (terracotta/olive/ochre), mixed metals, textural walls (lime wash/Venetian plaster), bold tile patterns, biophilic design
7. **Color tools:** ColorHunt (colorhunt.co), Coolors (coolors.co), Asian Paints Colour Visualizer, Sherwin-Williams ColorSnap
8. **Deliverable:** Mood board per room, written theme statement, annotated reference images

### Phase 4: Choose Tools & Build 3D Models

**Goal:** Convert 2D floor plan and ideas into a 3D model for walkthrough and contractor sharing.

**Tool recommendations (for non-architects, rated by learning curve):**

| Tool | Cost | Platform | Learning Curve | Best For |
|------|------|----------|---------------|----------|
| Sweet Home 3D | Free | Desktop | 2-3 hrs | Starting point, accurate modeling |
| Planner 5D | Freemium | Web+Mobile | 1 hr | Quick layouts, visual catalog |
| SketchUp Free | Free | Web | 5-10 hrs | When Sweet Home 3D limits hit |
| RoomSketcher | $10-20/mo | Web | 2-3 hrs | Professional output, contractor-ready |
| HomeByMe | Freemium | Web | 2-4 hrs | Photo-quality renders |
| Homestyler | Free | Web+Mobile | 1-2 hrs | AR furniture placement in real room |
| Live Home 3D | $20 | Desktop | 2-3 hrs | Best Windows option |
| Roomtodo | Free | Web | 1-2 hrs | Quick online mockup |

**AI-assisted design tools (for rapid inspiration from room photos):**
- RoomGPT (roomsgpt.io) — upload room photo, get 10+ styled redesigns
- Interior AI — upload photo + choose style, see your room transformed
- DecAI (decai.ai) — AI interior/exterior/garden design + list of 15 free tools
- GenRoom (genroom.io) — quick AI redesign from photo
- XHome Design (xhome.design) — AI interior generator
- Canva AI Interior Design — restyle rooms instantly

**Workflow:** Use AI tools for *inspiration* (what could this room look like?), then Sweet Home 3D for *accurate modeling* (measurements, exact placement).

**YouTube tutorials:** Search "Sweet Home 3D tutorial for beginners", "Planner 5D full house design", "RoomGPT AI Interior Design"

**Deliverable:** 3D model in chosen tool, AI inspiration images, rendered views of key rooms, annotated screenshots

### Phase 5: Select Construction & Finishing Methods

**Goal:** Decide how every surface will be finished.

**Wall finishes** (cost per sq ft, Bangalore 2026):
- Paint emulsion: Rs 25-60 — cheapest, recolor anytime
- Texture/roller paint: Rs 60-120 — adds depth
- Wallpaper: Rs 80-300+ — vinyl in bathrooms (humidity resistant)
- Wood/MDF/PVC cladding: Rs 150-500 — premium, hides uneven walls
- Stone/brick cladding: Rs 200-600 — feature wall, needs structural check
- Lime wash/Venetian plaster: Rs 150-400 — natural matte upscale, specialist needed
- 3D wall panels: Rs 150-350 — quick architectural feature
- Tile on wall: Rs 80-250 — durable waterproof (bathroom only)

**Flooring** options and cost ranges available in the full reference guide.

**Ceilings:** POP (Rs 60-120/sq ft), Gypsum board (Rs 80-180, recommended for Bangalore — clean, crack-resistant), PVC/stretch (Rs 100-250, waterproof for bathrooms), Exposed concrete (Rs 50-100, industrial), Wood (Rs 200-500, warm premium).

**Kitchen cabinets** material comparison available in full guide.

**Bathroom waterproofing:** Cementitious polymer-modified compound — 2 coats on floors + walls up to 6ft in wet zone. 48-hour ponding test mandatory. Seal pipe penetrations. Brands: Dr. Fixit, Bostik, Fosroc, Weber.

**DIY vs Pro reality check:** Painting, IKEA assembly, vinyl click-lock flooring, wallpaper (pre-pasted) = DIY. Plumbing, electrical, false ceiling, tiling, modular kitchen, carpentry, cladding = hire pro.

### Phase 6: Materials & Specification Sheet

**Goal:** Create the master spreadsheet for handover to execution team.

**Sheet columns:** Room | Surface | Material Type | Brand/Product Code | Color/Finish | Quantity | Installation Method | Notes

**Tab structure** per room:
1. Floor: tile/wood, brand, code, size, laying pattern, grout color
2. Walls: paint brand+code, wallpaper product code, cladding type
3. Ceiling: type, height, lighting channels, paint
4. Electrical: switch brand (Anchor/MK/GM), socket count per wall, fan/light/data points
5. Plumbing: faucet brand+model, pipe material, drain position
6. Furniture: dimensions, material, color, delivery date
7. Lighting: fixture type, lumens, color temp (2700K warm/4000K neutral), brand
8. Windows: curtain type, fabric, track type, motorization
9. Doors: door type, paint/finish, handle brand+model

**Bangalore sourcing:**
- Tiles: Old Madras Road, JC Road. Brands: Kajaria, Somany, RAK, Nitco, AGL
- Paints: Asian Paints, Berger, Dulux (use their color visualizer apps)
- Hardware: Hafele, Hettich, Ebco brand stores
- Lighting: Syska, Philips, Wipro, Havells
- Furniture: IKEA Nagasandra, Urban Ladder, Pepperfry, Woodsworth, local carpenters
- Online: Amazon, Flipkart, Livspace marketplace

**Budget guide (Bangalore 3BHK ~1200 sq ft):**
- Budget: Rs 6-10 Lakhs (Rs 500-800/sq ft)
- Mid-range: Rs 12-20 Lakhs (Rs 1,000-1,800/sq ft)
- Premium: Rs 25+ Lakhs (Rs 2,000+/sq ft)

### Phase 7: Create the Execution Package

**Goal:** Package everything so an interior team can execute with minimal back-and-forth.

**Folder structure on Google Drive:**
```
PROJECT_Interior_Package/
├── 00_Reference_Drawings/
├── 01_Photos_Video/
│   └── Room_by_Room/
├── 02_Functional_Brief/
├── 03_Inspiration_Moodboard/
├── 04_3D_Model_Renders/
├── 05_Elevations/
├── 06_Electrical_Layout/
├── 07_Specification_Sheet/
├── 08_Budget_Quotes/
└── 09_Execution_Notes/
```

**What contractors need from you:**
1. Dimensioned floor plan with furniture layout
2. Wall elevation drawings (sketch or 3D render per wall)
3. Specification sheet (materials, colors, product codes)
4. Electrical layout (switch/socket positions per wall with heights)
5. Lighting layout (fixture positions, types, switching groups)
6. Mood board / reference images

**Briefing the team:**
- Share Drive folder with "View" access
- 1-hour room-by-room walkthrough
- Explicit: "this exact tile in this laying pattern" vs "similar look, you suggest"
- Agree: timeline, payment milestones, material procurement responsibility, site access, waste disposal
- Get everything in writing (email, not WhatsApp)

**You do NOT need to provide exact measurements** — that's what pros do. But you MUST provide **clear intent**: what, where, in what material, and how it should look.

---

## Key Research Sources

Web research for this workflow covered 26 queries across 6 categories (120+ results) using the **hybrid parallel research pattern** (see `research-web-tools/references/multi-agent-research-compilation.md`): sub-agents deep-dived while the main agent ran broad searches simultaneously. Key sources:

## Deliverable Format Options

When handing the full guide to the user:

**Option A — Google Doc** (collaborative, editable): Use Docs API to create a structured doc with sections per phase. Rate limits may require splitting batchUpdate calls.

**Option B — HTML Document** (standalone, CSS-styled, browser-viewable): Preferred when the guide has complex tables, cost matrices, embedded color swatches, or needs to work without Google account. Upload to Drive TMP folder and share the link. The complete 7-phase guide at `/opt/data/DIY_Home_Design_Guide.html` (55KB) is the reference template — it covers all phases with CSS-styled tables, color-coded cost brackets, and embeddable research source URLs.

**Option C — Folder Package** (Drive folder with phase-by-phase subfolders): See Phase 7 folder structure above.

**Step-by-step guides:**
- greenhousestudio.co — How To Design A Room Like An Interior Designer
- stylebyemilyhenderson.com — 8 Steps To Design A Room
- decai.ai/blog/15-best-free-interior-design-software — 15 free tools for beginners

**Trends:**
- Vogue: 11 Key Interior Design Trends Set to Define 2026
- King Living: 9 interior design trends defining 2026
- Architectural Digest: Japandi Style Guide

**Indian context:**
- Draftora Designs: 3 BHK Interior Design Cost Bangalore
- PropertyGeek: Types of Floor Tiles in India
- DesignCafe: Different Types of Tiles for Indian Homes
- Livspace: Bedroom False Ceiling Cost POP vs Gypsum vs PVC
- Nobroker: Gypsum vs POP Ceiling India
- Zikhra: HomeLane vs Livspace vs Local comparison

**Reddit communities:** r/InteriorDesign, r/malelivingspace, r/HomeImprovement, r/Homebuilding, r/DesignMyRoom, r/bangalore

---

## Pitfalls

- **Skipping the functional brief:** Jumping to 3D modeling before documenting room-by-room function leads to redesigns. Always do Phase 2 before Phase 4.
- **Offering only Google Docs:** For cost tables, color references, and material matrices, HTML with CSS is clearer than Docs API's table support. Create the option early — the user can pick Doc vs HTML vs both.
- **Not cleaning up temp upload scripts:** After uploading to Drive, remove the temp .py upload scripts from /opt/data/ to keep the workspace clean.
- **Over-relying on AI tools:** RoomGPT/Interior AI are for *inspiration*, not accurate planning. Always ground AI ideas in a measured 3D model.
- **Incomplete specs:** Contractors exploit ambiguity. Specify exact brand + product code + color for every finish. "White tiles" means different things to different people.
- **Underestimating lead times:** Modular kitchen (4-6 weeks), custom wardrobes (3-4 weeks), imported tiles (6-8 weeks). Order early.
- **Bangalore waterproofing:** Don't skip the 48-hour ponding test. Many apartments have slab leakage from above — test before doing ceilings.
- **False ceiling without planning:** Cove lighting channel, AC duct space, and curtain track recess must be planned *before* false ceiling layout, not after.
- **Electrical point layout:** Common regret — not enough sockets in kitchen counter, no USB bedside, no point for robotic vacuum in living room. Place sockets every 6ft along each wall.

---

## Version History
- v1.0.0 — 2026-06-28 — Initial creation from comprehensive web research (120+ sources) and 7-phase methodology compilation
