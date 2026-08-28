# Direct Browser / No-API Research (no Apify, no Tavily)

Verified 2026-08-15 on the Hermes VPS for NDR. Trigger: "don't use apify or
tavily, use direct browser search" — applies to ALL web research, not just
portals. This file is the working recipe; the SKILL.md carries the summary.

## Working stack (all free, all reachable from the datacenter IP)

1. **Google News RSS** — news search with zero captcha.
   ```
   https://news.google.com/rss/search?q=bangalore%20metro%20phase%203%20sarjapur&hl=en-IN&gl=IN&ceid=IN:en
   ```
   Parse with `re.findall(r'<item>.*?</item>', text, re.S)` then pull
   `<title>` and `<link>`. The `<link>`s are `news.google.com/rss/articles/...`
   JS redirects — NOT resolvable to the publisher URL via Location header and
   NOT fetchable via Jina (blocked). Use them only as titles; find real URLs
   via DDG-via-Jina (step 4).

2. **Wikipedia API** — reliable article text + image discovery.
   ```
   action=query&prop=extracts&explaintext=1&titles=Red%20Line%20(Namma%20Metro)&format=json
   action=query&prop=images&titles=Red%20Line%20(Namma%20Metro)&format=json   # find map files
   ```
   Wikitext (`prop=revisions&rvprop=content`) gives full station tables when
   extracts are truncated.

3. **OSM Overpass + Nominatim** — geocoding + geometry.
   - Nominatim: `https://nominatim.openstreetmap.org/search?q=...&format=json` — ALWAYS set a real `User-Agent`. Verify `display_name` — homonyms are common (e.g. "Ambedkar Nagar" matched central Bengaluru instead of the Sarjapur Road one). Rate-limit: sleep ~1.1 s between calls.
   - Overpass: POST `data=` form-encoded (NOT JSON body — JSON gets 406). The default `https://overpass-api.de/api/interpreter` returns **406 without a User-Agent header**; `https://overpass.kumi.systems` 504s under load; **`https://overpass.private.coffee/api/interpreter` worked** (2026-08-16) — always set `User-Agent` and fall through mirrors in that order.
   - Overpass area-filter queries (`area["name"="Bengaluru"]...`) fail with 406 on some mirrors — use an explicit bbox `(12.75,77.35,13.25,77.90)` instead.
   - `out body; >; out skel qt;` returns nodes+ways+relations; rebuild way geometry by looking up node coords from the same response.
   - Big regex name queries 504 — prefer targeted `way(id:...)` and small bboxes.
   - OSM users sometimes sketch proposed alignments as named ways (e.g. 5 ways named "Red Line (Sarjapur ⇔ Hebbal)") — chain them by matching consecutive endpoints; label as unofficial/indicative.

4. **Jina reader** (`r.jina.ai/<url>`) — page→markdown AND search proxy.
   - Page fetch: `curl https://r.jina.ai/https://www.deccanherald.com/...` → clean markdown (works on sites that block the VPS, incl. DH, Moneycontrol).
   - Search proxy: `curl https://r.jina.ai/https://html.duckduckgo.com/html/?q=Rathibele+Lake+Sarjapur` → REAL DDG results; links are `https://duckduckgo.com/l/?uddg=<urlencoded>` — unquote `uddg` to get the real URL.
   - Pitfall: Jina rate-limits per domain (news.google.com got AbuseAlleviationError). Prefer direct publisher URLs, space out calls.

5. **GitHub API** — `https://api.github.com/search/repositories?q=...` works unauthenticated for repo search; raw.githubusercontent.com for files (e.g. `geohacker/namma-metro` → `metro-lines-stations.geojson` — OSM-derived lines+stations, KML-style properties).

6. **Wayback Machine CDX API** — when a gov/official site is DOWN (connection refused, even via Jina), pull its content from archive snapshots:
   ```
   http://web.archive.org/cdx/search/cdx?url=<domain>&output=json&filter=statuscode:200&from=2024
   ```
   → JSON rows `[timestamp, original_url, ...]`. Fetch the raw snapshot with the `id_` suffix so you get the page, not Wayback chrome:
   `http://web.archive.org/web/<timestamp>id_/<original_url>`. Verified 2026-08-16 on RLDA (rlda.indianrailways.gov.in, site down). Note: deep-link snapshots sometimes return Wayback's own UI instead of the page — use CDX to find the exact archived timestamped URL first.

7. **Wikipedia raw wikitext station tables** — for transit systems, `https://en.wikipedia.org/w/index.php?title=<Page>&action=raw` returns the full wikitext incl. station tables. Table formats VARY per article and need two parsers:
   - Stacked rows: `| 1` newline `| Station Name` newline `| ಕನ್ನಡ` — capture the line after the number.
   - Inline rows: `|1|| style="text-align:center;" |[[Whitefield (Kadugodi) metro station|Whitefield (Kadugodi)]]|| ಕನ್ನಡ || 26 March 2023` — strip `style="..."` attrs, split on `||`, take cell 0, strip `[[X|Y]]` → Y.
   - One regex does NOT fit all line articles; write the parser per-article and sanity-check station count against the article lead (e.g. "The line will have 18 stations").

6. **Wikimedia Commons API** — official map images:
   ```
   action=query&titles=File:NammaMetro-RedLine-2025-08-18.png&prop=imageinfo&iiprop=url|size&iiurlwidth=2000
   ```
   Use `thumburl` for a downloadable size.

## Engine-by-engine behavior from the VPS (verified — do not retry these)

| Engine | Result | Cause |
|---|---|---|
| google.com/search (browser or curl) | "unusual traffic" captcha page | exit node flagged |
| bing.com (browser or via Jina) | unrelated junk results (Hungarian forums etc.) | anti-bot garbage |
| lite.duckduckgo.com (browser) | "If this persists, please email us" block | IP/automation block |
| html.duckduckgo.com (browser) | empty | block |
| html.duckduckgo.com via Jina | WORKS | Jina fetches server-side |
| searx.be and friends | "Verifying your browser…" antibot | captcha |
| mojeek.com (browser) | net::ERR_SOCKS_CONNECTION_FAILED | tunnel refuses |
| news.google.com RSS | WORKS (curl, no proxy needed) | — |
| en.wikipedia.org / commons / api.github.com / overpass / nominatim / r.jina.ai | WORKS | — |

## Playwright headless recipe (only needed for pages Jina can't render)

The `playwright` CLI installed via `uv tool` has a broken greenlet binary —
don't debug it, make a fresh venv:

```bash
uv venv /tmp/bvenv -p python3.13
uv pip install --python /tmp/bvenv/bin/python playwright
# browser binary already present:
#   /opt/hermes/.playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell
#   (PLAYWRIGHT_BROWSERS_PATH=/opt/hermes/.playwright)
```

Launch (standalone scripts need the explicit proxy — the env var is not
inherited by every shell context):

```python
from playwright.sync_api import sync_playwright
EXEC = "/opt/hermes/.playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXEC, headless=True,
                          proxy={"server": "socks5://hermes-utilities:1000"},
                          args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
    pg = b.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36")
    pg.goto(url, timeout=45000, wait_until="domcontentloaded")
```

## Building KML deliverables from OSM + geocoded points

- GeoJSON → KML: convert `[lon, lat]` coords to `<coordinates>lon,lat,0</coordinates>`; KML is lon,lat order.
- Chain OSM sketch ways by matching endpoint equality before concatenating; merge fragmented OSM way segments into continuous polylines by endpoint proximity (threshold ~0.01°).
- Geocode station lists via Nominatim; when a hit is a homonym or missing, interpolate between neighbors and mark `APPROX` in the description.
- XML: escape `&` in names (folder names break parsing), wrap descriptions in CDATA, validate with `xml.etree.ElementTree.parse` before shipping, zip the folder + images.
- Deliverable pattern used for NDR (Bangalore Metro, 2026-08-16): **5-file KML pack** — `01_metro_operational`, `02_metro_under_construction`, `03_metro_approved_proposed`, `04_suburban_rail_bsrp`, `05_indian_railways_stations` — each with a matching `.kmz` (`zip -j out.kmz in.kml`), a README, an `images/` subfolder of route maps, and a `sources/` subfolder of official PDFs. Upload to Drive with `mimetype='application/vnd.google-earth.kml+xml'` / `.kmz`; create the folder chain first (`R&D > Bangalore > Metro`); make the folder structure in one pass (create root → get ID → create children). Local mirror + folder ID recorded in `references/bangalore-suburban-rail-bsrp.md`.
- KML line colors: use KML aabbggrr hex (alpha first), e.g. Purple `FF6A2C8C`, Yellow `FF1F9EE0`.

## Session pitfalls worth remembering

- Google News RSS article `<link>` redirects: don't chase them; DDG-via-Jina finds the real publisher URL.
- DH/Moneycontrol article bodies are mostly nav junk after Jina markdown — grep for route/station keywords in the tail, not the head.
- The "72 km" headline corridor and "8-corridor feasibility study" are distinct things; always fetch the article body to disambiguate proposal vs approval stage.
