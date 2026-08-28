# Brigade Meadows belt R&D (2026-08-15) — nearest-5 apartment projects

NDR asked: R&D around Brigade Meadows — 5 apartment projects, 5 recent
portal listings each (URLs tracked), per-project averages, and RERA
start/end dates. Deliverable shape: per project = RERA reg + start/end,
5 listings (BHK/area/price/psf/seller/URL), avg price + avg psf
(+median, range). All listing URLs verified live (25/25 HTTP 200).

## Workflow that worked (no Apify/Tavily — direct browser + tunnel)

1. Anchor: Brigade Meadows K-RERA pin from Plumeria Phase 1 (detail 1110)
   = 12.81496, 77.50935 (Kaggalipura/Udayapura, Bannerghatta Road).
   Nominatim agrees (12.814, 77.508). The township's registrations:
   Plumeria Phase 1 PRM/KA/RERA/1251/310/PR/171015/000863 (start
   25-01-2014, comp 31-07-2018); Plumeria Lifestyle
   PRM/KA/RERA/1251/310/PR/181022/002096 (start 27-07-2018, comp
   30-03-2021 incl Covid ext).
2. Candidate discovery: MagicBricks locality pages through the tunnel
   (`/property-for-sale-in-<loc>-pppfs`, pages 1–2), collect `/project-`
   hub hrefs. Bannerghatta-corridor slugs that work: hulimavu-bangalore,
   gottigere-bangalore, arekere-bangalore, begur-bangalore,
   jigani-bangalore, bannerghatta-bangalore, kaggalipura-bangalore (all
   200). `bannerghatta-road-bangalore` 404s. Locality pages alone are too
   noisy for project extraction — use them only for hub discovery.
3. Shortlist → K-RERA detail fetch per candidate (POST /projectDetails,
   tunnel) for pin + dates. Older layouts: DMS coords in text fields
   (see karnataka-rera-collector SKILL.md). Haversine-rank vs anchor.
4. Per project: MB project hub (`/project-<slug>-for-sale-in-bangalore-pppfs`)
   anchor-window card parse (see tunnel-portal-scraping-recipes.md),
   5 clean listings, averages.

## Gotchas hit

- Prestige Falcon City is on KANAKAPURA Road, not Bannerghatta — portal
  locality hints ("Chandapura/Konanakunte") misled; DDG-via-Jina caught
  it. Verify corridor before including a marquee name.
- Hiranandani's Bangalore registrations are under "SUADELA CONSTRUCTIONS"
  (Queens Gate Block 4 detail 1238, Evita, Torino) — name searches for
  HIRANANDANI return zero in the K-RERA index.
- Esteem Enclave (Bannerghatta Main Rd, listed on MB) is NOT in the
  K-RERA index under that name — exclude unregistered marketing names.
- Sattva Springs (0.7 km!) is a VILLA project — check Project Sub Type.
- Requests "No connection adapters were found" for socks5h proxies in one
  heredoc run (import socks OK) — curl liveness checks are the reliable
  path.

## Chosen 5 (straight-line km from Brigade Meadows pin)

1. Provident Park Square (Puravankara/Provident) — Talagattapura/Judicial
   Layout, 6.4 km. RERA multi-phase: Ph1 180217/002476 (start
   31-12-2017) … Ph5 200226/003305 (comp 30-06-2026). MB avg ₹1.22 Cr;
   ₹11,138/sqft avg (10,589–11,674).
2. Oceanus White Meadows (Oceanus Dwellings) — Anjanapura, 8.3 km.
   270623/006023, start 01-06-2023, comp 31-12-2028, 135 units. MB avg
   ₹1.23 Cr; flat ₹7,587/sqft (all 3BHK 1,403–1,884 sqft, single seller).
3. Prestige Park Square (Prestige Southcity) — Gottigere, 9.2 km.
   180313/002634, start 15-03-2018, comp 23-02-2023 (completed). MB avg
   ₹2.24 Cr; ₹14,984/sqft (14,159–15,750).
4. Casagrand Hazen (Casa Grande Garden City) — Gottigere, 10.7 km.
   220722/005099, start 28-08-2022, comp 13-07-2027, 622 units. MB avg
   ₹1.37 Cr; ₹10,118/sqft (one ₹5,000/sqft outlier; ex-outlier ~11,400).
5. Prestige Elysian (Prestige Nottinghill) — Bannerghatta Main Rd /
   Hulimavu, 11.2 km. 190722/002709, start 01-06-2019, comp 30-09-2023
   (completed). MB avg ₹2.58 Cr; ₹17,593/sqft (16,079–19,613).

Corridor takeaway: two bands — mid-market Gottigere/Talagattapura
(₹7.6–11.4K/sqft) vs premium Bannerghatta Rd/Hulimavu (₹15–17.6K/sqft).
Prices are asking, not transaction. CSV with all 25 listings + URLs was
written to /tmp/bm_rd/brigade_meadows_rd.csv (extractor scripts in
/tmp/bm_rd/: extract_listings.py, krera_detail.py, parse_hubs.py).

## Spreadsheet deliverable (second half of the request)

NDR then asked for the results "in a spreadsheet... every listing and the
rate identified in that listing... averaged to give me the rate per
project", two sheets. Built with `uv run --with openpyxl python3
rebuild_xlsx.py` → /tmp/bm_rd/Brigade_Meadows_RD.xlsx. Sheet 1 "Project
Averages" (5 projects, avg/median/min/max rate/sqft + avg price + RERA
dates), Sheet 2 "All Listings" (25 rows, each with rate/sqft + clickable
hyperlink, all verified 25/25). First build attempt used `ws.append()` and
silently LOST the first row of each sheet — caught by reopen-and-assert
self-verification, rebuilt with explicit `ws.cell()` writes. Recipe:
references/xlsx-deliverable-build.md.
