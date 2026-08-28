# Sterlitee Regal Park — Plotted-Development Pricing Recipe (2026-08-26)

Session record for the plotted-land pricing benchmark on the NH-44 / Hosur Rd
corridor (Hulimangala/Jigani/Bommasandra/Electronic City belt). Captures the
data that worked and the durable extraction recipe (summary in SKILL.md).

## Subject

- **Sterlitee Regal Park** — BDA-approved residential **plotted development**,
  251 sites (22A-20G net), at Hulimangala village, Jigani Hobli, Anekal taluk.
  RERA PRM/KA/RERA/1251/308/PR/180925/008098, GPS 12.778263, 77.651026.
- **Vicinity:** Bommasandra industrial + Electronic City Phase 2 (N), Jigani
  industrial/SEZ (adjacent), Thirupalya, Chandapura, Attibele, then
  Chichuriganapalli (Hosur Block, Krishnagiri TN, PIN 635103) ~12 km toward
  Hosur on NH-44. **"Keshwari" could not be located** — unknown locality on
  this belt (possible voice variant).

## Key finding — no in-project plot resales on portals

Plotted devs often have **ZERO in-project plot resales listed** on the portals
(only in-project VILLA resales). Sterlitee had 2 in-project villas (₹3.37–3.90
Cr) but no in-project plots. Benchmark such projects with their **own village +
immediate-adjacent locality plot comps** (Hulimangala, Jigani, Bommasandra,
Hebbagodi, Electronic City), and label each listing's locality clearly.

## Resulting per-project averages (25 verified listings, all < 3 mo old)

- **Sterlitee zone** (Hulimangala/Jigani/Bommasandra plots) — 8 listings,
  avg **₹5,974/sqft**, range 3,667–9,000. Individual 1200–2000 sqft plots list
  ₹4,500–9,000/sqft; dev-direct new-property rows at the top end.
- **Prestige Kings County** (Jigani plots) — 5 listings, avg ₹10,998/sqft.
- **Sobha Townpark** (Yadavanahalli apartments) — 6 listings, avg ₹13,267/sqft
  on SUPER built-up area (user requires SBA as the psf basis for apartments).
- **Guru Punvaanii Ernika** (Muthagatti, Anekal gated plots) — 4 listings,
  avg ₹3,675/sqft (all ~₹3,650, owner + agents). Note this sits ABOVE the
  documented Anekal gated-plots band (₹1,250–2,500) — a developed gated layout.
- **Vakil Encasa** (Jigani villa/plot) — 2 listings, avg ₹8,738/sqft.

## Extraction recipe that worked (fully reproducible)

1. **NoBroker detail pages** via plain `requests` (no tunnel): for plots,
   `/property/plot/buy/plot-for-sale-in-<project>-bangalore/<32hex>/detail`.
   Regex JSON: `price`, `plotArea`/`propertySize`, `uploadedBy` (OWNER|AGENT),
   `creationDate`/`lastUpdateDate` (ms ts), `active`. Filter `active:true` +
   date < 3 mo. Discover detail URLs via
   `curl "https://r.jina.ai/https://html.duckduckgo.com/html/?q=<proj> plot for sale nobroker"`
   → grep/unquote `uddg=`.
2. **NoBroker villa/flat list pages** (`/villas-for-sale-in-<loc>_bangalore`,
   `/flats-for-sale-in-<loc>_bangalore`) → embedded `propertyTitle`/`price`/
   `carpetArea` arrays (plain requests, datacenter IP, no tunnel).
3. **MagicBricks plots** via SOCKS tunnel: list pages
   `https://www.magicbricks.com/plots-for-sale-in-<loc>-...` and individual
   `propertyDetails-<area>-FOR-Sale-<loc>-in-Bangalore&id=<b64>` — encode
   `+`→`%2B`, `=`→`%3D` in the id, then **liveness-verify each URL (200)**;
   `Resale`=broker vs `New Property`=dev in the title.
4. **Portals blocked on the datacenter IP:** `plots-for-sale-in-*` NoBroker
   list pages 410; 99acres/Housing.com still blocked. Use the detail-page /
   tunnel paths above instead. Do NOT burn retries on the blocked list pages.

## Deliverable shape (matches NDR's two-sheet convention)

xlsx with Sheet1 **Project Averages** (project, type, locality, # listings,
avg psf, avg price, psf range) + Sheet2 **All Listings** (title, source,
seller broker/dev, unit size, SBA, total price, psf, date, hyperlinked URL).
Sobha-style apartments: compute psf on SUPER built-up area, state it.
Every URL hyperlinked + liveness-verified.
