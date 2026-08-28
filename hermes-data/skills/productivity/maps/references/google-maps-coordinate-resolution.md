# Google Maps Headless Coordinate Resolution + Category-Icon KML

Session-validated Aug 2026 (Thylagere competitor map, 13 projects: 6 villa / 7 plot).

## Problem

Nominatim/OSM fails to geocode **private gated communities** (Prestige
Sanctuary, Over the Rainbow, DNR Solace, etc.) — they simply don't exist in
OSM. Google Maps has them, but needs a browser session.

## Working Recipe: Playwright + headless chromium → Google Maps search URL

Use the same headless chromium + consent-cookie pattern that works for maps
screenshots. The Google Maps **search URL carries the coordinates**:

```python
import re, time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(
        executable_path='/opt/hermes/.playwright/chromium_headless_shell-1234/chrome-linux/headless_shell',
        args=['--no-sandbox','--disable-dev-shm-usage','--lang=en-US'])
    ctx = b.new_context(viewport={'width':1400,'height':900}, locale='en-US')
    ctx.add_cookies([
        {'name':'CONSENT','value':'YES+cb.20240101-01-p0.en+FX+100','domain':'.google.com','path':'/'},
        {'name':'SOCS','value':'CAISHAgBEhJnd3NfMjAyMzAxMDEtMF9HQzIBBGgBEg','domain':'.google.com','path':'/'},
    ])
    pg = ctx.new_page()
    q = "Montira Chikkasagarahalli"
    pg.goto('https://www.google.com/maps/search/' + q.replace(' ', '+') + '?hl=en',
            timeout=20000, wait_until='domcontentloaded')
    pg.wait_for_timeout(6000)
    url = pg.url
    m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if m:
        lat, lon = float(m.group(1)), float(m.group(2))
        print(lat, lon)
    b.close()
```

**Key details:**
- Query URL format: `https://www.google.com/maps/search/<query>?hl=en`
- Coordinates come from the **page URL** (`@lat,lon` after the place name),
  not from scraping the page body
- `wait_until='domcontentloaded'` + explicit wait beats `wait_until='load'`
  (which times out on heavy Maps pages)
- If first load returns a search-results URL with no `@lat,lon`, press
  `Enter` / click the first result card and re-read the URL

## Pitfalls (all hit in the Aug 2026 session)

1. **Reusing one page for sequential queries causes navigation
   interruptions** — "Navigation to X is interrupted by another navigation
   to Y" errors cascade through the whole batch. Either open a fresh page
   per query or run queries one at a time with a small sleep.

2. **Batches MUST save after every name, not at the end** — a mid-run
   crash (EPIPE, timeout, browser death) wipes all partial results if the
   JSON dump only happens after the loop. Aug 2026: a 104-name batch
   crashed at ~36 and lost everything because the writer ran last. Fix:
   use `scripts/geocode_batch_subproc.py` — it loads existing output,
   skips already-resolved names, saves after EVERY name, and survives
   per-query exceptions. Restart the same command to resume. If an older
   script already died without writing output, reconstruct partials from
   its stdout log with the regex `^(\d+\.\d+),(\d+\.\d+) \| \[([^\]]*)\] (.*?) \| via: (.*)$`
   (lines look like `13.3528911,77.7254375 | [IT_companies] Nagarjuna Tech
   Solutions | via: ...`).

2b. **Per-name try/except is NOT enough — use subprocess isolation.** An
    EPIPE crash from the playwright node driver is an unhandled 'error'
    event that kills the ENTIRE python process even when every query is
    wrapped in try/except (observed Aug 2026: two different in-process
    batch scripts, both died mid-run at ~36/104 and ~62/104). The fix
    that actually completed: one subprocess per name
    (`scripts/geocode_one.py` + `scripts/geocode_batch_subproc.py`), each
    with its own `timeout=` cap, so one crash costs at most one name.

2c. **Google throttles this IP after ~50 rapid queries.** A wall of
    consecutive FAILs after ~50 successes is the throttle signature, not
    genuine misses — Brigade Orchards, Sattva Park Cubix, JW Marriott
    definitely exist on Maps. Fix: pace ~4s between names, and run big
    lists (100+) in multiple chunked passes with a `timeout 1700` cap
    rather than one marathon. Prioritize high-value names first
    (major projects before generic hospitals) so a throttle hit lands on
    the least important entries.

2d. **Subprocess timeout tuning:** 45s was too tight — 2 attempts ×
    ~25s (12s goto + 2.5s + 5.5s wait + launch overhead) exceeds it, so
    names that should resolve were marked TIMEOUT. Use 100-120s per name.

2e. **OSM/Nominatim fallback is a dead end for rural plotted
    developments** (Devanahalli/Nandi area, Aug 2026): 29 consecutive
    OSM misses for real projects and hospitals. OSM simply has no
    coverage there. Don't burn ~150s on the Nominatim loop for rural
    names — Google Maps headless is the only route.

2f. **Filter scrape junk before geocoding.** Google Maps category-search
    inner_text parses contain non-POI noise: price artifacts (`€182`),
    generic strings (`Hotel`, `Resort hotel`, `Government Hospital`).
    Drop them from the batch list before geocoding — they waste queries
    and pollute the dataset.

2g. **Names file shape pitfall:** source JSON may be a list of
    `[{"name":..., "cat":...}]` dicts, not strings. Passing dicts into
    string concatenation gives
    `TypeError: unsupported operand type(s) for +: 'dict' and 'str'`
    at line one of the loop. Unpack `name`/`cat` before building query
    variants (the subproc runner handles both shapes).

3. **Use short per-attempt timeouts (20s) + multiple query variants**
   (project name alone, project + village, project + developer). A project
   that fails on one variant often resolves on the next. Cap the whole run
   with `timeout 280` so it can't hang forever.

4. **User-shared `maps.app.goo.gl` links are the fastest coordinate
   source.** `curl -sL <goo.gl>` follows the redirect and the final URL is
   usually a `/maps/place/<Name>/@lat,lon,...` — read coords straight from
   the redirect, or open the redirect URL in the headless browser. The
   user's own pin is authoritative; cross-validate against an independent
   Google Maps search.

5. **Search engines bot-challenge this datacenter IP** (DuckDuckGo
   anomaly page, Google "unusual traffic"). Don't burn time on DDG/Google
   SERP scraping from here; the Google Maps search URL is the reliable
   route.

6. **Bare `/maps/search/<q>?hl=en` URL often returns NO `@lat,lon` and NO
   results panel** (observed Aug 2026) — the page lands on the search-URL
   form with no resolved placemark. The interactive recipe below (type into
   the search box + Enter) is the reliable variant; the URL-only approach
   works only sometimes. Also add `&gl=in` — without the country hint the
   headless browser may resolve queries to the datacenter country (e.g.
   Germany) and return garbage coords like 51.17,10.45.

## Interactive Google Maps Search (validated Aug 2026 — POI + project capture)

For searching POIs, schools, plotted developments, etc. **anchored at a
subject coordinate**, the working recipe:

```python
import re
from playwright.sync_api import sync_playwright
EXE = '/opt/hermes/.playwright/chromium_headless_shell-1234/chrome-linux/headless_shell'

def gmaps_category(category, anchor="13.3216,77.6789"):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EXE, args=['--no-sandbox','--disable-dev-shm-usage','--lang=en-US'])
        ctx = b.new_context(viewport={'width':1400,'height':900}, locale='en-US')
        ctx.add_cookies([
            {'name':'CONSENT','value':'YES+cb.20240101-01-p0.en+FX+100','domain':'.google.com','path':'/'},
            {'name':'SOCS','value':'CAISHAgBEhJnd3NfMjAyMzAxMDEtMF9HQzIBBGgBEg','domain':'.google.com','path':'/'},
        ])
        pg = ctx.new_page()
        # 1) anchor map at subject coords
        pg.goto(f'https://www.google.com/maps/@{anchor},13z?hl=en&gl=in', timeout=20000, wait_until='domcontentloaded')
        pg.wait_for_timeout(6000)
        # 2) type category into search box, press Enter
        box = pg.locator('input#searchboxinput, input[name="q"]').first
        box.wait_for(state='visible', timeout=15000)
        box.fill(category)
        box.press('Enter')
        pg.wait_for_timeout(9000)
        # 3) read the LEFT PANEL via inner_text of body — feed selectors return 0
        body = pg.inner_text('body')
        # 4) scroll to load more results
        for _ in range(4):
            pg.mouse.wheel(0, 1500)
            pg.wait_for_timeout(1500)
        body2 = pg.inner_text('body')
        b.close()
        return body, body2
```

**Key details:**
- Anchor FIRST at `@lat,lon,13z`, THEN search — searching "schools" etc.
  without an anchor resolves to Germany / nowhere.
- Read `inner_text('body')` — `div[role="feed"]` and `.Nv2PK` selectors
  return 0 results on this engine (panel is rendered differently).
- Parse names by filtering UI noise: ratings (`4.9`, `No reviews`), phone
  regexes, address-ish lines (contain `·`, `+code`, `Open/Closed`,
  `Website`, `Directions`), `You're seeing a limited view`, `Map data ©`.
- Geocode each discovered name afterward with the same interactive recipe
  (type name + Enter, read `@lat,lon` from URL), accepting only coords in
  the target region (e.g. lat 12.5–14.5, lon 76.5–78.5 for Bangalore).
- Reuse ONE page per query — sequential queries on the same page produce
  "navigation interrupted" cascades. Fresh browser per query is slow but
  reliable; batch with ~1s sleeps and print results to stdout as you go.
- EPIPE crashes when the browser dies: `pkill -9 -f headless_shell` before
  relaunching; wrap long batches with `timeout 280` per attempt.

**Aug 2026 result:** 13 category searches around Thylagere (13.3216,77.6789)
yielded 104 unique POIs/projects — schools (Harrow Intl, Gitanjali Intl),
colleges (Nagarjuna CET, SJC, GITAM), hospitals, industrial/IT (Foxconn,
SLK Software, Astemo), plus 35+ real-estate projects (Brigade Orchards,
Godrej Royale Woods, Sattva Park Cubix, Purva Tivoli Hills, Birla Trimaya,
Sumadhura Panorama, Assetz Promise of Spring, etc.). The 99acres/MagicBricks/
Housing.com portals Akamai-block this IP, so Google Maps anchored search is
the fallback discovery route when portals refuse.

## Category-Icon KML (villa ≠ plot)

Standard Google mapfiles icons — verify with a HEAD request first, they're
almost all live:

| Category | Icon URL | Looks like |
|---|---|---|
| Villa (built home) | `http://maps.google.com/mapfiles/kml/pal2/icon50.png` | house with $ |
| Plot (land) | `http://maps.google.com/mapfiles/kml/pal4/icon21.png` | waving flag |
| Subject / highlight | `http://maps.google.com/mapfiles/kml/pal4/icon50.png` | star-ish |

KML structure for category styles:

```xml
<Style id="villaStyle">
  <IconStyle><scale>1.1</scale><Icon><href>http://maps.google.com/mapfiles/kml/pal2/icon50.png</href></Icon></IconStyle>
  <LabelStyle><color>ff1a1a1a</color><scale>1.0</scale></LabelStyle>
</Style>
...
<Placemark><name>Prestige Sanctuary — ₹25,455/sq.ft</name>
  <styleUrl>#villaStyle</styleUrl>
  <description>Type: Luxury Gated Villa&#10;Developer: Prestige Group&#10;...</description>
  <Point><coordinates>77.6969201,13.3138264,0</coordinates></Point>
</Placemark>
```

- **Label = name + price** goes in `<name>` (renders next to the pin).
- Description balloon carries full detail (developer, units, status, RERA).
- KML coordinate order is **lon,lat,alt** — swap and pins land in the
  ocean.
- `&#10;` for newlines inside description (or escape real newlines).
- XML-escape `&`, `<`, `>` in names/descriptions.
- Validate with `python3 -c "import xml.dom.minidom; xml.dom.minidom.parse('file.kml')"`.
- Deliver to Drive TMP (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`) per user
  preference, or `MEDIA:` in Telegram.

## Companion R&D sheet

Competitor price research goes in a separate Google Sheet (TMP folder):
Tab 1 = per-project summary (type, launch/current price, appreciation,
developer, units, sizes, land area, status, lat/lon, Maps link), Tab 2 =
listing-level sources with portal links. Create via Drive API
(mimeType `application/vnd.google-apps.spreadsheet`, parents=[TMP_ID]),
rename the default sheet (Sheet1) before writing, and make `addSheet`
idempotent for retries.
