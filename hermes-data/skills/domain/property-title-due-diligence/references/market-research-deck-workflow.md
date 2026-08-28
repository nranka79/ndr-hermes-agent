# Market Research Deck Workflow (Google Slides)

Turns an R&D sheet + My Maps KML into a **market research presentation** for a proposed
land parcel — same format as the Thylagere deck
(`1dA1l9LATVfvHa3GLiSHFJukCFtrCgFYiEAm_5vzLh2g`, "Thylagere ~10 Acres — Villa Development
Market Research v6"). Used end-to-end for Bestamanahalli ~55A (Sanchaya Lands), Aug 2026.

## Deck structure (canonical order)

1. **Cover** — full-bleed navy, 54pt bold title, gold subtitle, location line, size|type|corridor line, gold rule, date | Prepared by | DRA Group, CONFIDENTIAL.
2. **Proposed Land Overview** (PROJECT AT A GLANCE) — Project Name, Location, Land Area, Acquisition (MOU seller), Deal Terms (₹/acre, phases), Development Type, Connectivity, Nearest Hubs, Google Maps link.
3. **Google Map Location** — map image (rendered) + map link.
4. **Proposed Land Summary** — total extent, location, seller, MOU terms, zone/corridor, anchors, social infra, competition count.
5. **PROJECT SUMMARY — CATEGORY WISE** (user requirement: placed **immediately after slide 4**):
   - divider slide, then one table per category — Plotted / Villas / Apartments
   - columns: `# | Project Name | Developer | GPS Coords | Dist | Land | Units | Launch | Launch ₹ | Current ₹/sqft | Comp | RERA`
   - split at ~14 data rows/slide; follow with a **Data Notes** slide explaining every '—' field
6. **Location USP & Connectivity** — bullet anchors (emoji + bold name + distance + impact line).
7. Per-category sections: divider → **one 12-field slide per project** (header + 3 price cards CURRENT/LISTING/DISTANCE + QUICK FACTS + PROJECT DETAILS + source footer).
8. **Infra sections, one per type**: Tech Parks & SEZ, Metro & Rail, Hospitals, Colleges, Schools, Retail & Hotels (name + distance lines).
9. **Key Infrastructure & Demand Drivers** — each driver with HIGH/MEDIUM/LONG-TERM tag chip.
10. **Price Comparison** table — subject land row highlighted (gold), note on land-to-retail spread.
11. **Product-Fit Analysis** — Option A (RECOMMENDED) / B / C with peer-set pricing.
12. **Pricing Recommendation** — positioning, target buyer, market context, risks, next steps.
13. **Thank You**.

## Build path when the Slides API is disabled

Symptom: `slides.googleapis.com ... SERVICE_DISABLED` (403) even with valid OAuth.
Do NOT fight it — build through Drive:

1. **Study an existing deck**: Drive `files().export_media(fileId, mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation')` → .pptx; inspect with python-pptx (shape positions, sizes, text runs, fills). This recovers exact layout + colors without the Slides API.
2. **Rebuild with python-pptx** in a dedicated venv:
   `uv venv /tmp/pptxenv --python 3.13 && uv pip install --python /tmp/pptxenv/bin/python python-pptx`
   (the /opt/hermes/.venv has no pip; install into the pptxenv).
3. **Upload → native Slides**: Drive `files().create` with `mimeType='application/vnd.google-apps.presentation'` and the .pptx as media — Drive converts it. Share writer with the session user.
4. **Verify round-trip**: export the created Slides file back to .pptx, re-count slides with python-pptx, spot-check titles.

## Palette (from Thylagere deck, matches DRA branding)

- NAVY `#1A1A2E` (header bands, dividers), NAVY2 `#16213A`
- GOLD `#D4A53C` (accent rules, "current price" card, subject row, tags)
- BLUE `#3495DB` (secondary cards), GREY `#95A5A6`, LIGHT `#F2F3F5` (zebra rows)
- Font: Calibri. Slide: 12191675 × 6858000 EMU = 13.33 × 7.5 in (16:9).
- Price cards at y≈1.0: gold (current), blue (listing), navy (distance).

## Map image for the location slide

- OSM `tile.openstreetmap.org` returns "Access blocked — tile usage policy" for scripted UAs. **Use CartoDB**: `https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png` with a Mozilla UA. Works from the VPS.
- Render tiles with PIL: zoom 12, ~1240×820 px centered on subject, circle pins per type (plot orange #E67E22, villa green #2E7D32, apt blue #1E88E5), triangle pins for infra, red star for subject, white legend box. CartoDB tiles are light-beige; verify with vision_analyze (OCR-only mode returns little — pass `also_describe_visually=true`).

## Pitfalls (all hit live Aug-2026)

- **KML placemark names carry a price suffix** after `| ₹...` — strip before using as slide titles:
  `re.sub(r'\s*\|\s*₹.*$', '', name)`.
- **Duplicate placemarks**: My Maps KML contains both `X` and `X Anekal, Bangalore South` entries; dedupe by canonical name (strip the locality suffix) before generating slides.
- **Summary-table column mapping**: the col_defs list must carry BOTH header text AND data key (3-tuples). Using the header string as the dict key produces a perfectly-laid-out table where every data cell is '—' (hit live). Also unpack the 3-tuple in both the width loop and the header loop.
- **Do not fabricate RERA/units/launch/completion** when portal/RERA access is blocked (Tavily 432, RERA site unreachable, portals wall VPS). Mark '—' and add the Data Notes slide; offer to re-run after credit top-up. Prices are asking, not transactions — state that on slides.
- Round-trip export byte-size grows (~1.1 MB from 0.88 MB) — normal; check slide count + titles, not bytes.

## Source of the numbers

Pull project data from the R&D sheet's Competitors tab + the My Maps KML (descriptions carry
Type | Listing price | Per sqft | From subject | Locality | Source | Link). KML fetch:
`https://www.google.com/maps/d/kml?mid=<MAP_ID>&forcekml=1` (works from VPS).
