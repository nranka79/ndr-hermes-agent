# Tunnel-direct portal scraping recipes (verified 2026-08-12, Ranka Oasis / Hosur belt run)

Verified on the live Hosur-belt R&D run: the residential tunnel reaches
MagicBricks and NoBroker directly (no Apify), while 99acres stays blocked
even through it. These are the exact working recipes.

## SOCKS endpoint

- `socks5h://hermes-utilities:1000` (resolves to 172.18.0.3). Use with
  curl as `-x socks5h://hermes-utilities:1000` — works for HTTP and HTTPS.
- **Pre-wired browsers (NDR correction 2026-08-12):** Hermes' browser
  tools (browser_navigate, smart_browser) and the Playwright env are
  ALREADY routed through the residential tunnel (`AGENT_BROWSER_PROXY`
  env = socks5://hermes-utilities:1000). Do NOT manually add
  `proxy={...}` to those — NDR: "the browsers are already configured to
  do that." Only standalone curl and raw Playwright scripts launched from
  a bare shell (where the env var isn't inherited) need the explicit
  proxy flag — and when they do, `proxy={"server":
  "socks5://hermes-utilities:1000"}` is the exact value, matching
  AGENT_BROWSER_PROXY.
- The router is **domain-policy based**: residential-listed domains
  (MagicBricks, NoBroker, rera.tn.gov.in) exit from the residential node;
  everything else (api.ipify.org, ipinfo.io) exits from the VPS IP.
  **DO NOT judge tunnel health via IP-echo services** — they show the VPS
  IP (91.99.219.247 = Hetzner) even when the tunnel is fine. Test with the
  actual portal domain (MagicBricks returns 200 through it).
- Playwright: `proxy={"server": "socks5://hermes-utilities:1000"}`, and set
  `PLAYWRIGHT_BROWSERS_PATH=/opt/hermes/.playwright` when running from a
  shell whose HOME differs (the execute_code sandbox HOME has no browsers —
  run Playwright scripts via terminal).

## MagicBricks (works via tunnel — curl AND Playwright)

URL patterns (verified live; old ones 404):
- `/villa-for-sale-in-<loc>-pppfs` → 200 (type-specific page, carries geo)
- `/property-for-sale-in-<loc>-pppfs` → 200 (all types, 30 rows/page)
- `/plots-for-sale-in-<loc>-pppfs`, `/apartments-for-sale-in-<loc>-pppfs` → 404 (do not exist)
- old `/property-for-sale/residential-real-estate/<city>` → 404
- pagination: `?page=2..N` works (Hosur 170 results ≈ 6 pages; last page
  returns < 30 rows — stop there)
- Locality slugs that work: `hosur`, `attibele-bangalore`,
  `electronic-city-bangalore`, `chandapura-bangalore`,
  `bommasandra-bangalore`, `sarjapur-bangalore`. `shoolagiri` rendered 0
  rows (naming differs) — treat 0-row pages as a slug problem, not a
  no-listings signal.

Extraction (pair two sources):
1. JSON-LD `<script type="application/ld+json">` blocks:
   - block 0 = `ItemList` → 30 `{position, url, name}` per page
   - type-specific pages ALSO have a LIST of `SingleFamilyResidence` with
     `geo {latitude, longitude}` and `potentialAction.seller.name`
   - generic property-for-sale pages have EMPTY residence blocks (block 1/2
     are just whitespace) → no geo there; geo only on villa pages
2. Prices/psf/area/status are NOT in JSON-LD — parse the rendered body text
   card window after the listing title:
   - `₹ X Lac|Cr` (price), `₹ Y per sqft` (psf), `Carpet Area|Super Area N sqft`
   - `Ready to Move|Under Construction` (status)
   - Match card text to JSON-LD items by listing name to merge
     url/geo/seller with price/psf/area.

Yield: 1,138 rows across 6 localities in one paginated sweep (~30/page ×
up to 6 pages × 2 URL types per locality).

### Project listings hub (`-pppfs`) — per-project price+psf extraction (verified 2026-08-15, Fortune Seven Sarjapur)

For "what is the per-sqft rate for project X" the locality pages are the
wrong tool; the project hub page is the right one. URL pattern:
`https://www.magicbricks.com/project-<slug>-for-sale-in-<city>-pppfs`
(e.g. `project-fortune-seven-sarjapur-for-sale-in-bangalore-pppfs`),
paginate with `/page-2`, `/page-3` … same as locality pages.

The SSR HTML carries EVERY listing's price AND per-sqft published side by
side — no JSON-LD needed, no card-merging needed:

- JSON-LD `ItemList` gives 30 `{position, url, name}` per page; the
  `name` embeds the SBA (`3 BHK Flat for Sale ... 1744 Sq-ft`). Prices
  are NOT in JSON-LD items (description empty on project pages).
- Flatten body text (strip script/style tags first) and regex:
  `₹\s*([\d.,]+)\s*(Cr|Lac|Lakh)\s+₹\s*([\d,]+)\s*per sqft`
  → each match is one listing: total price + psf. SBA = price / psf
  (round-trips to the JSON-LD name area — cross-check).
- FAQ JSON-LD block has per-BHK price ranges (`2 BHK flats … Rs. 95.3
  lakhs – 1.05 Cr`, `4 BHK … Rs. 1.54 Cr – 1.83 Cr`) — useful for the
  "range" row before you compute listing-level psf.
- Dedupe matches on (price, unit, psf) triple — the page repeats cards.
- Yield (Seven Sarjapur): 24 unique listings in 2 pages, psf range
  ₹8,026–9,580, median ₹8,077. The project's own "price trend" block
  (₹8,454/sqft steady 4 quarters) is the anchor; listing median is the
  practical resale figure. Higher-floor listings (30–41) run ₹8,800–9,600.
- MagicBricks project FAQ also confirms RERA no. in SSR text
  (`PRM/KA/RERA/... is the RERA number`) — handy cross-check.

### Project hub JSON-LD is rich — parse cards by anchor window (verified 2026-08-15, Brigade Meadows belt)

The ItemList JSON-LD on project hubs carries per-listing: URL, name,
`floorSize.value` (CARPET area), `numberOfBedrooms` (**key can have a
trailing space: `numberOfBedrooms `** — use `item.get('numberOfBedrooms')
or item.get('numberOfBedrooms ')`), `geo`, seller
(`potentialAction.seller.name`), and RERA ID (`additionalProperty`).
Price + psf are NOT in JSON-LD; the `₹ X Cr/Lac ₹ Y per sqft` adjacency
exists ONLY in FLATTENED text — raw HTML has markup between the two, so a
raw-html regex finds 0 pairs while the flatten-then-regex finds them all.

Working parser shape:
1. Parse ItemList JSON-LD → list of {url, bhk, carpet_area, seller, rera, geo}.
2. Find all `<a href="/propertyDetails/...&id=...">` positions in DOM order.
3. For each anchor: flatten `html[max(0,pos-2600):pos+3800]`, regex
   price (`₹ X Cr|Lac`), psf (`₹ Y per sqft`), status (Ready to
   Move/Under Construction). Match anchor → JSON-LD item by id suffix
   (`url.split('id=')[-1]`).
4. Dedupe by id; sanity-filter price 0.2–20 Cr and psf 3,000–40,000 —
   hub pages embed "similar properties" sidebar noise (₹40 Cr @
   ₹5,00,000/sqft rows appeared on every hub).
5. Report area from the URL slug (headline SUPER area, e.g.
   `3-BHK-1609-Sq-ft`) not the JSON-LD carpet figure.

PITFALL — catastrophic regex backtracking hangs the parser: a "Posted …
ago" pattern with nested quantifiers
(`r'Posted\s*:?\s*([A-Za-z0-9]+(?:\s*[A-Za-z0-9]+)*)\s*ago'`) explodes on
any window containing "Posted" without "ago" after it. Symptom: the whole
script times out with zero output (buffered stdout hides it; run -u and
bisect per file). Fix: bounded pattern
`r'Posted\s*:?\s*(\d+\s*[A-Za-z]+\s*ago)'` — or drop posting-age capture.

Other notes from the belt run:
- Hub listing cards can mix in nearby-resale rows from OTHER corridors
  (Provident Park Square hub showed Kanakapura Road listings) — check each
  listing's URL slug locality before trusting it as project data.
- Verify the final listing URLs are live with
  `curl -x socks5h://hermes-utilities:1000` — 25/25 returned 200 in the run.
- A `python3 -c "import socks"` success does NOT guarantee requests has a
  SOCKS adapter; if requests raises "No connection adapters were found"
  for a socks5h proxy dict, fall back to curl for liveness checks.

## NoBroker (works via tunnel — JS-rendered, Playwright required)

- API `/api/v3/multi/property/BUY/filter?city=hosur` FAILS without a
  locality token: `No Polygon or point found using token: null`. Don't
  chase the token — use the SEO pages instead.
- SEO pages render cards client-side: `/villas-for-sale-in-hosur_bangalore`
  (200, ~647 KB), `/property/sale/hosur` (shell only, no cards).
- Redirects: `/villas-for-sale-in-attibele_bangalore` →
  `/villas-for-sale-near-attibele_bangalore`; `electronic-city` →
  `electronic_city`. Follow the redirect (curl -L).
- Recipe: goto → wait ~10s → press Escape (dismisses the login popup that
  hides cards) → scroll 12×1500px → read `document.body.innerText`.
- Card pattern in body text: line matching
  `N BHK (Villa|Apartment|Plot|House|Gated) In <Project> For Sale In <Locality>`,
  then within the next ~28 lines: `₹ X Lacs|Cr`, `₹ Y per sq.ft.`,
  `N sqft Builtup`.
- Hosur yield: 25 villas with real project names (Upkar Spring Valley,
  Titan Township, Pushpam Ranches, Nexus Sky Villa).

## 99acres (still blocked even through residential tunnel — Akamai edge)

- 403 `Access Denied` on EVERY path: `/property-in-<loc>-ffid/`, `/`,
  API guesses — both via curl AND Playwright through the tunnel.
- This is **browser fingerprinting at the edge, not IP-blocking** —
  residential IPs get 403 too. `m.99acres.com` does NOT resolve through
  the SOCKS tunnel at all (`ERR_SOCKS_CONNECTION_FAILED`). No workaround
  found on 2026-08-12 (even playwright-stealth did not help); do not
  burn retries on it. Get 99acres coverage from Tavily web_search snippets
  or cross-portal (MB/NoBroker) data instead.
- Diagnostic: the Housing.com/99acres WAF error pages print a
  "Real Client IP" field — use it to confirm WHICH node the site sees
  (91.99.219.247 = VPS Hetzner vs 119.82.120.164 = Bengaluru Spectranet
  residential node) before concluding the tunnel is at fault.

## Housing.com (verified 2026-08-12: blocked even through residential render)

- 406 `Security Alert` on EVERY path — homepage, listing pages, API
  guesses (`/api/v1/search/results?...`), even `/sitemap.xml`.
- The error page shows `Real Client IP 119.82.120.164` (Bengaluru
  Spectranet residential) — so the tunnel DID egress residential and the
  WAF STILL blocked: fingerprint-based, not IP-based. Same class as
  99acres. playwright-stealth did not help. Cover via Tavily snippets.

## NoBroker (works via tunnel — JS-rendered, Playwright required)

- API `/api/v3/multi/property/BUY/filter?city=hosur` FAILS without a
  locality token: `No Polygon or point found using token: null`. Don't
  chase the token — use the SEO pages instead.
- SEO pages render cards client-side: `/villas-for-sale-in-hosur_bangalore`
  (200, ~647 KB), `/property/sale/hosur` (shell only, no cards).
- **City suffix is MANDATORY (hit 2026-08-12).** Plain
  `/villas-for-sale-in-hosur` (no `_bangalore`) returns **410 Gone** and
  redirects to the homepage — zero cards, looks like a dead site. Always
  use the `_<city>` form (`hosur_bangalore`, `attibele_bangalore`).
  Note Hosur is in TN but its NoBroker SEO slug is `_bangalore`.
- Redirects: `/villas-for-sale-in-attibele_bangalore` →
  `/villas-for-sale-near-attibele_bangalore`; `electronic-city` →
  `electronic_city`. Follow the redirect (curl -L).
- Recipe: goto → wait ~10s → press Escape (dismisses the login popup that
  hides cards) → scroll 12×1500px → read `document.body.innerText`.
- Card pattern in body text: line matching
  `N BHK (Villa|Apartment|Plot|House|Gated) In <Project> For Sale In <Locality>`,
  then within the next ~28 lines: `₹ X Lacs|Cr`, `₹ Y per sq.ft.`,
  `N sqft Builtup`.
- Hosur yield: 25 villas with real project names (Upkar Spring Valley,
  Titan Township, Pushpam Ranches, Nexus Sky Villa).
- **Merge hazard (hit 2026-08-12):** a re-run that returns 0 cards for a
  locality (transient render failure / 410) will OVERWRITE the previously
  captured rows for that locality if you merge by `merged[loc] = rows`.
  Only overwrite when the new result is non-empty:
  `if rows: merged[loc] = rows`.

## MagicBricks redirect / zero-row localities

- Wrap `page.goto` in try/except and read `page.url` after — slugs for
  towns with no MB locality page (denkanikottai, kelamangalam, zuzuvadi,
  bagalur) redirect or interrupt navigation; 0 rows = slug problem, not a
  no-listings signal (same rule as shoolagiri).
- `mathigiri` needs the `-hosur` suffix (`/property-for-sale-in-mathigiri-hosur-pppfs`).

## playwright-stealth (installed 2026-08-12)

- Install: `uv pip install --python /opt/hermes/.venv/bin/python playwright-stealth`
  (the venv has NO pip module — `python -m pip` fails; uv is the way).
- v2.0.3 API: `from playwright_stealth import Stealth; stealth = Stealth();
  await stealth.apply_stealth_async(page)` — the old `stealth_async(page)`
  import does not exist in 2.x.
- Did NOT unblock 99acres/Housing.com — their WAFs detect deeper than
  basic stealth. Worth trying on other portals, not these two.

## Takeaway for the tool ladder

The old "never curl portals from the VPS" rule is now **tunnel-aware**:
- Reachable via tunnel: MagicBricks, NoBroker, TN RERA (rera.tn.gov.in)
- Still blocked (fingerprint, not IP): 99acres (Akamai 403), Housing.com
  (WAF 406) — verified 2026-08-12 with residential egress confirmed on
  the error page's Real Client IP field. Cover both via Tavily snippets.
- Apify = last resort (credit-walled), per NDR 2026-08-12 directive.
