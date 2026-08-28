# Property R&D — Skill + Tool Design Blueprint
Draft v0.2 · 2026-08-04 · Implemented state. v0.1 was the approved spec; v0.2
records what shipped. Implementation lives in
`/data/hermes/skills/productivity/property-rd/` (local mirror:
`hermes-data/skills/productivity/property-rd/`). Keep this file in sync with
implementation.

## Goal
Given any property pin / location:
1. **radius_query (T1)** — scan the R&D Google Sheet (Competitors + POIs tabs) by Haversine distance for everything within configurable radius (5/10 km). Coordinates, not names.
2. **kml_generator (T2)** — deterministic KML from the sheet rows. NO LLM in the KML path (LLM-generated XML breaks escaping — seen in earlier builds).
3. **pricing_refresh (T3)** — periodic pricing refresh: LLM collects raw listings (30-day window), tool applies outlier rejection (prices almost never drop >5–10%; off-values discarded, median written), updates sheet + audit log.

Origin story: Sammy's Palm Hills (6.3 km from Thylagere subject land) was missed by name-driven search. Radius-driven scanning closes that class of gap.

## Implementation status (v0.2)

| Item | Status | Location |
|---|---|---|
| `sheet_io.py` (shared Sheets/Drive I/O + pure helpers) | **BUILT, tested** | `property-rd/scripts/sheet_io.py` |
| T1 `radius_query.py` | **BUILT, tested** | `property-rd/scripts/radius_query.py` |
| T2 `kml_generator.py` | **BUILT, tested** (E2E KML verified) | `property-rd/scripts/kml_generator.py` |
| T3 `pricing_refresh.py` | **BUILT, tested** | `property-rd/scripts/pricing_refresh.py` |
| `coords_from_urls.py` (map-link coord extraction) | **BUILT, tested** | `property-rd/scripts/coords_from_urls.py` |
| Unit tests (20) | **PASSING** | `property-rd/scripts/test_property_rd.py` |
| `kml-icons.md` (approved icon map) | **BUILT** | `property-rd/references/kml-icons.md` |
| `sources-registry.md` (sources-of-truth KB) | **BUILT** | `property-rd/references/sources-registry.md` |
| SKILL.md (tool-first orchestration) | **BUILT** | `property-rd/SKILL.md` |
| Monthly cron wiring (T3 schedule) | **WIRED 2026-08-04** (gateway cron, `30 0 1 * *`, deliver telegram:Nishant) | container cron store |
| RERA integration | deferred (NDR) | — |

## Architecture (v0.2 — tool-first, per NDR 2026-08-04)

The LLM orchestrates + extracts (web_search / apify / firecrawl / browser);
**the tools do every write and every derived artifact**:

1. LLM writes discovery JSON (`rows_to_add.json` / `listings.json` schemas
   in property-rd SKILL.md) — never sheet API calls from chat.
2. `sheet_io.py append` moves rows into the sheet (Competitors / Listings &
   Sources / POIs & Infrastructure).
3. `kml_generator.py` regenerates the KML FROM the sheet after every edit:
   label `Name | Rs X/sqft`, icon per type, and the **description carries
   ALL details + the pricing source URL(s)** (joined from Listings & Sources
   — portal, price, total, date, URL per listing).
4. `radius_query.py` gap-checks by coordinates (5/10 km counts).

## Source-of-truth sheet
- Sheet: `1EQv1zm7j5vV9NUuAsWpSLalENqg8xgKWvaL_QvvGYaM`
- Tabs: `Competitors` (Project|Type|Launch Price|Current Price (per sq.ft)|Current Sale Price (Total)|Appreciation|Developer|Units|GPS Lat|GPS Lon|Google Maps Link|Location|Latitude) · `POIs & Infrastructure` (name, category, lat, lon) · `Listings & Sources` (Project|Type|Portal|Price|Total|Date|Source URL)
- The tools' header matcher also accepts the belt-run schema (# | Project |
  Type | Locality | Listing Price | Per Sqft | Lat | Lng | Dist km | Maps
  link | Source URL | Confidence).
- Access via `tools.gws_auth.build_service('sheets','v4', service_name='google-draas')` — never raw creds. Fallback: vault resolve(email) + get_token (worked in sessions where build_service 403'd).

## T1 radius_query
Input: `--sheet <id> --lat X --lon Y [--radius 10] [--place "Name"] [--json out.json]`
Algorithm: pull tabs → drop rows w/o valid coords (report them in `unpinnable_rows`, never silently) → Haversine (R=6371) → keep <= radius → sort by distance → dedupe by normalized name keeping richer row (observed duplicate: two "Prestige Sanctuary" rows) → report both 5 km and 10 km counts even if one radius requested.
Place-name pins: Nominatim via `--place` (towns only — villages/projects need Places/geocode batch).

## T2 kml_generator
Input: `--sheet <id> --subject-name .. --subject-lat .. --subject-lon .. [--radius 10] [--labels price|none] [--out file.kml] [--drive-file-id <id>]` (+ `--from-json` preview mode, debug only).
Rules (validated): 100% ASCII (₹→"Rs"); `&`→`&amp;`; minidom-validate before write; label = `Name | Rs X/sqft` per user preference; icon map per **references/kml-icons.md** (user-approved Aug-2026 set, hrefs curl-verified 200 on 2026-08-04 — `farms.png`/`warehouse.png` were 404 and replaced with `agriculture.png`/`truck.png`, mall=`shopping.png`, temple=`landmark.png`; all documented in kml-icons.md); `new_project`/`other` auto-reclassified by name/price signals before icon assignment; coordinate-bucket dedupe (4 dp) keeps the richest row; description = full details + numbered pricing-source list with URLs from Listings & Sources.
Drive: `files().update(fileId=<same id>, media_body=...)` preserves link.

## T3 pricing_refresh
Schedule: monthly cron (1st 06:00 IST) — planned; currently on-demand via CLI.
Source priority (LLM-side): (1) direct-reachable portals (NoBroker, 99sqft, Propzilla, QuikrHomes, Homznspace, PropertyCrow, Proplocators, HousingMan, official builder PDFs) → (2) Google snippet extraction for blocked portals (99acres/MagicBricks/Housing/SquareYards) → (3) Apify 99acres deep-scrape (totals only, no per-sqft).
30-day window: only listings with visible recency signal (e.g. "Updated 3 weeks ago").
Outlier logic (implemented in the tool):
```
baseline = current sheet value or median(last4)
kept = [v for v in vals if 0.90*baseline <= v <= 1.25*baseline]
new = median(kept)  # write only if kept non-empty
```
- v < 0.90×baseline → suspected drop, discard (log to audit)
- v > 1.25×baseline → suspected error, flag for review, don't write
- All rejected for >30% of projects → ALERT with raw snippets (portal markup likely changed)
Sheet updates: write per-sqft + totals after rules pass; append each listing to Listings & Sources; append to `Pricing Audit` tab (project, old, new, n_listings, median, rejected, reasons, timestamp).

## Skill layout (property-rd) — shipped
```
skills/productivity/property-rd/
├── SKILL.md                     # triggers, workflow, tool-first architecture
├── references/
│   ├── kml-icons.md             # approved icon map + KML rules
│   ├── sources-registry.md      # known portals/forums/groups KB (grows per run)
│   └── property-rd-tool-design.md → lives in property-pricing-sources (canonical)
├── scripts/
│   ├── sheet_io.py              # shared Sheets/Drive helpers + CLI
│   ├── radius_query.py          # T1
│   ├── kml_generator.py         # T2
│   ├── pricing_refresh.py       # T3
│   ├── coords_from_urls.py      # Google Maps link -> lat/lon
│   └── test_property_rd.py      # 20 local unit tests
└── templates/
    └── kml_template.xml
```

## Open items (awaiting NDR)
1. Radius default: report both 5 & 10 km; KML default 10 km — implemented.
2. Outlier band 0.90×/1.25×, median window 5 — implemented as specified.
3. KML label per-sqft only (`Rs 17,000/sqft`) — implemented.
4. New-project discovery: refresh existing rows + flag new finds for manual approval before adding — partially (discovery appends; approval gate optional).
5. Sheet: keep current R&D sheet, or dedicated R&D Database master with per-region tabs — keep current sheet.
6. Warehouse / mall / temple icons — **resolved 2026-08-04**: full icon set
   curl-verified; `farms.png` and `warehouse.png` were 404 (replaced by
   `agriculture.png` / `truck.png`); mall=`shopping.png`, temple=
   `landmark.png` (no worship icon exists in mapfiles). All in kml-icons.md.
7. Monthly cron for T3 + alerting — **wired 2026-08-04**: gateway cron job
   `property-rd T3 monthly pricing refresh`, schedule `30 0 1 * *`
   (1st 06:00 IST, server runs UTC), skill `property-rd`, deliver
   `telegram:Nishant` (channel-directory label).

## Build order (v0.1 → v0.2) — completed
Phase 1: sheet_io.py + radius_query ✓ (test w/ Thylagere pin 13.3216384,77.6789048)
Phase 2: kml_generator ✓ (icon map port + description-with-source-links + escaping tests)
Phase 3: pricing_refresh ✓ (listings JSON in, outlier logic, audit tab)
Phase 4: cron monthly + alerting + SKILL.md finalized ✓ (cron job created
         2026-08-04, pilot run verified delivery)
Phase 5 (opt): Chennai corridor, price-history chart tab.
