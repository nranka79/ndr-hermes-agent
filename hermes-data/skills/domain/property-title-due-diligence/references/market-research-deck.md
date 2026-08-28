# Market Research Report Deck (Thylagere / Bestamanahalli format)

Trigger: "Generate market analysis report for <proposed land>", "as we prepared for Thyalagere" — a
per-land market-research Google Slides deck, NOT a project-spec deck and NOT a docs deck.

## Deck structure (observed in Thylagere ~10A v6, replicated for Bestamanahalli ~55A)
1. **Cover** — dark navy full-bleed, title 54pt bold white, gold subtitle, location line, acreage/dev-type line,
   "August 2026 | Prepared by: <user> | DRA Group", CONFIDENTIAL footer.
2. **Subject Land Overview** — "PROJECT AT A GLANCE" rows: Project Name / Location / Land Area / Acquisition
   (MOU party) / Deal Terms / Development Type / Connectivity / Nearest Hubs.
3. **Google Map Location** — map image (see tiles below) + edit/view link.
4. **Proposed Land Summary** — extent, seller/MOU terms, corridor, anchors, competition count.
5. **Location USP & Connectivity** — 6–7 anchor pairs (🏢 🚇 🚉 🏥 🎓 🏭 🛣️), each with detail + impact tag.
6. **Section dividers per project type** — PLOTTED → VILLAS → APARTMENTS (order = user's map layer order).
7. **Per-project slide (12-field)**: navy header (name + type chip PLOT/VILLA/APARTMENT) / 3 price cards
   (💰 CURRENT PRICE, 🏷️ LISTING PRICE, 📍 DISTANCE FROM SUBJECT) / QUICK FACTS (Type, Status, Locality,
   Distance) / PROJECT DETAILS rows (Per Sqft, Listing Price, Type, Status, Locality, Distance, Source,
   Source Link) / footer "📍 Maps │ 🏠 MagicBricks │ 🏘️ 99acres | Verified: <date> R&D".
8. **Infra sections separated by type**: Tech Parks & SEZ, Metro & Rail, Hospitals, Colleges, Schools,
   Retail & Hotels — one slide each, bullet + distance-right-aligned.
9. **Key Infrastructure & Demand Drivers** — HIGH/MEDIUM/LONG-TERM impact chips.
10. **Price Comparison table** — type bands, subject row highlighted gold.
11. **Product-Fit Analysis** — Options A/B/C with RECOMMENDED chip.
12. **Pricing Recommendation** + **Thank You**.

## Exact palette (extract from the reference deck, don't guess)
- Navy `#1A1A2E` (header band), Navy2 `#16213A`, Gold `#D4A53C`, Blue `#3495DB`, Grey `#95A5A6`,
  White/Black; font Calibri; slide size 13.333 × 7.5 in (Emu 12191675 × 6858000).
- Extraction recipe: `unzip <deck>.pptx -d x && grep -o '<a:solidFill><a:srgbClr val="[0-9A-F]*"' x/ppt/slides/slideN.xml`
  → Counter the vals. (Google Slides export keeps solid fills intact.)

## Toolchain — Slides API disabled fallback (verified working)
1. **Study the reference deck**: Drive API `files().export_media(fileId, mimeType=...pptx)` → inspect with
   python-pptx (text, positions, sizes per shape).
2. **Build the new deck with python-pptx**: use `uv venv /tmp/pptxenv && uv pip install --python
   /tmp/pptxenv/bin/python python-pptx` — the Hermes venv has no pip binary.
3. **Upload as NATIVE Google Slides WITHOUT the Slides API**: Drive `files().create` with
   `body={'mimeType':'application/vnd.google-apps.presentation'}` + the .pptx as media. Drive converts
   automatically — this bypasses a disabled Slides API entirely. Slides API may 403 `SERVICE_DISABLED` on
   `presentations().get` — don't fight it, use the Drive-import path.
4. **Verify**: export the uploaded file back to .pptx via Drive and count slides / spot-check text with
   python-pptx (round-trip integrity).
5. **Visual QA without LibreOffice**: `uv pip install --python /tmp/pptxenv/bin/python spire.presentation`
   → `Slides[i].SaveAsImage()` → PNG → vision_analyze. NOTE: rendered PNGs carry a Spire "Evaluation
   Warning" watermark in the corner — that's a render artifact, NOT in the real file; ignore it.
6. Permission share: `permissions().create` type=user role=writer for the requesting user (session auth
   already owns the file).

## Map image for the deck
- OSM tile server (`tile.openstreetmap.org`) 403s non-browser UAs with "tile usage policy / Blocked" —
  use **CartoDB**: `https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png` with a Mozilla
  UA header; works from the VPS. Composite with PIL: fetch ~20 tiles, paste, draw pins (circle per type,
  triangle per infra), red star for subject, white legend box.
- Verify the composite with vision_analyze BEFORE embedding (tile failures produce blank/grey areas).

## Data sources for the deck
- My Maps KML export: `curl -sL "https://www.google.com/maps/d/kml?mid=<MID>&forcekml=1"` (works from VPS).
  Parse folders → placemarks; descriptions carry `Type | Listing price | Per sqft | From subject |
  Locality | Source | Link` fields.
- R&D sheet tabs: Competitors (name, type, locality, listing, psf, lat, lon, dist, maps, src, confidence)
  + Social Infrastructure (name, category, dist, lat, lon, maps).

## Verification-fallback pattern (when live channels are down)
- `web_search`/`web_extract` are Tavily-backed: HTTP 432 = credits exhausted. Do NOT retry the same path —
  check Apify, then browser, then fall back to baseline data.
- Apify `magicbricks-99acres` preset: `cities` must be MagicBricks city names ("Bangalore"); locality
  strings ("Anekal") return 0 results; generic city runs return a single random listing, not
  project-targeted data — don't burn credits probing it for per-project verification.
- Google/Bing/DuckDuckGo/Brave all bot-wall VPS datacenter IPs (sorry page / CAPTCHA / Cloudflare).
- Browser Use Cloud: needs ≥$0.10 balance (HTTP 402 otherwise).
- **When everything is blocked**: the R&D sheet data (even 3 days old, source-linked) stands as the
  verified baseline — build the deck from it, keep every source URL, and TELL the user explicitly that
  live re-verification was blocked this session and offer a re-run. NEVER fabricate refreshed prices.

## Pitfalls (hit live Aug 2026)
- KML placemark names carry a price suffix (`NAG Green Park Anekal, Bangalore South | ₹32 - 50 L`) — strip
  `\s*\|\s*₹.*$` for slide titles; also strip locality suffixes (`Anekal, Bangalore South`) when deduping
  (the same project appears under base name and suffixed name).
- `skill_view`/`skill_manage` on property-rd may 403 when `/data/hermes/skills` is root-owned — the skill
  is served from `~/.hermes/skills/property-rd/`; read SKILL.md directly from that filesystem path.
- Session identity: `build_service(service_name='google-draas')` resolves to the SESSION user
  (psingh@draas.com in this session) — created files are owned by them automatically; confirm with
  `about().get(fields="user")` and don't hardcode an owner email.
