# Google Maps Coordinate Resolution + KML Output (Playwright headless)

Battle-tested Aug 2026 while resolving 13 competitor projects near Thylagere
(Devanahalli corridor) for NDR's R&D competitor map. This is the proven path
when `web_extract` / plain HTTP gets bot-walled by Google, and private gated
communities are absent from OSM/Nominatim.

## When to use

- Geocoding real-estate competitor projects by name (private gated
  communities, plotted layouts — these rarely exist on OSM).
- Resolving coordinates from a user-shared `maps.app.goo.gl/...` shortlink.
- Building a KML / MyMaps overlay of projects.

## Environment

The `/tmp/pptxenv` venv has python-pptx + playwright + a headless chromium
shell. The chromium binary path that works:

```python
executable_path='/opt/hermes/.playwright/chromium_headless_shell-1234/chrome-linux/headless_shell'
```

If the agent-browser tool daemon has a stale cached engine, bypass it and use
Playwright directly (`sync_playwright` + `p.chromium.launch(...)`).

## Coordinate resolution recipe

```python
import re, time
from playwright.sync_api import sync_playwright

QUERIES = [
    ("Project Name", ["Project Name Locality", "Project Name Locality variant 2"]),
]

def grab_coords(pg):
    url = pg.url
    m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if m:
        return float(m.group(1)), float(m.group(2)), url, pg.title()
    return None, None, url, pg.title()

with sync_playwright() as p:
    b = p.chromium.launch(
        executable_path='/opt/hermes/.playwright/chromium_headless_shell-1234/chrome-linux/headless_shell',
        args=['--no-sandbox','--disable-dev-shm-usage','--lang=en-US'])
    ctx = b.new_context(viewport={'width':1400,'height':900}, locale='en-US')
    # Pre-seed consent cookies to skip the German/EU consent wall
    ctx.add_cookies([
        {'name':'CONSENT','value':'YES+cb.20240101-01-p0.en+FX+100','domain':'.google.com','path':'/'},
        {'name':'SOCS','value':'CAISHAgBEhJnd3NfMjAyMzAxMDEtMF9HQzIBBGgBEg','domain':'.google.com','path':'/'},
    ])
    pg = ctx.new_page()
    for name, variants in QUERIES:
        lat = lon = None
        for q in variants:
            if lat is not None:
                break
            try:
                pg.goto('https://www.google.com/maps/search/' + q.replace(' ', '+') + '?hl=en',
                        timeout=20000, wait_until='domcontentloaded')
                pg.wait_for_timeout(6000)
                lat, lon, url, title = grab_coords(pg)
                if lat is not None:
                    break
                # click first result card if URL has no @coords yet
                try:
                    pg.keyboard.press('Enter')
                    pg.wait_for_timeout(3000)
                    lat, lon, url, title = grab_coords(pg)
                except Exception:
                    pass
            except Exception:
                time.sleep(2)
        print(f"{name}: {lat},{lon}", flush=True)
    b.close()
```

## Key pitfalls

- **Use 2–3 query variants per project.** One variant fails often; the next
  often hits. E.g. `"Montira Chikkasagarahalli"` → `"Montira Nandi hills"`.
- **`wait_until='domcontentloaded'` + a wait_for_timeout** beats
  `wait_until='load'` (which times out on Google Maps). Keep per-attempt
  timeouts ~20s.
- **Write results incrementally** (append to a JSON file after each project,
  not at the end) — killed runs lose the final JSON write otherwise.
- **EPIPE crash** (`write EPIPE` in Playwright's node driver) = the browser
  process died (often from a previous pkill or timeout). Kill all
  `headless_shell` processes, wait, relaunch fresh.
- **Don't run long resolution loops in a foreground terminal** — Google Maps
  pages are slow; a 13-project loop takes 5+ min. Use
  `background=true` + `notify_on_complete=true`, then poll the log.
- **Playwright EPIPE/hang recovery:** `pkill -9 -f resolve_coords6.py;
  pkill -9 -f headless_shell` then relaunch.

## Shortlink resolution (user shares maps.app.goo.gl link)

1. `curl -sL --max-time 20 "<shortlink>" -o /tmp/redirect.html` — read
   `FINAL_URL` from the redirect.
2. Often the redirect URL has NO `@lat,lon` (e.g. a `maps/place/...` URL with
   only a place id). Open it in the headless browser:
   `pg.goto(shortlink)` then `pg.wait_for_timeout(9000)` and read
   `pg.url` — after Maps renders, the URL contains `@lat,lon` (verified:
   Montira shortlink → `13.3416197,77.6995568`).

## KML generation

Verified live icon URLs (checked HTTP 200 Aug 2026, all `maps.google.com/mapfiles/kml/...`):

| Use | URL |
|-----|-----|
| Villa (house w/ $) | `pal2/icon50.png` |
| Plot (flag) | `pal4/icon21.png` |
| Subject land (star) | `pal4/icon50.png` |
| Also live: trees, gas pump, cars, etc. | `pal2/icon4.png`, `pal2/icon7.png`, `pal2/icon34.png`, `pal3/icon34.png`, `pal4/icon47.png` |
| Does NOT exist | `shapes/home.png` (404) |

KML structure — label must include **name + ₹/sqft** (user requirement):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>Project Competitor Map</name>
  <Style id="villaStyle"><IconStyle><scale>1.1</scale><Icon><href>http://maps.google.com/mapfiles/kml/pal2/icon50.png</href></Icon></IconStyle></Style>
  <Style id="plotStyle"><IconStyle><scale>1.1</scale><Icon><href>http://maps.google.com/mapfiles/kml/pal4/icon21.png</href></Icon></IconStyle></Style>
  <Placemark><name>Prestige Sanctuary — ₹25,455/sq.ft (resale avg)</name>
    <styleUrl>#villaStyle</styleUrl>
    <description>Type: Luxury Gated Villa&#10;Status: SOLD OUT — Resale Only&#10;Developer: Prestige Group</description>
    <Point><coordinates>77.6969201,13.3138264,0</coordinates></Point>
  </Placemark>
  ...
</Document>
</kml>
```

- Coordinates are `lon,lat` (KML order — lon first, easy to flip by accident).
- Include a subject-land placemark with a distinct style/color so the user's
  own parcel shows against competitors.
- **XML-escape ALL text content AND strip non-ASCII.** Real-estate names are
  full of `&` ("R&D", "Estate Plots & Farm Villas", "College Of Engineering &
  Technology", "Resort & Spa"). A raw `&` inside `<name>`/`<description>`
  makes Google Earth / My Maps import fail with `not well-formed (invalid
  token)` at that exact position. But the em dash and emoji ARE a cause too
  when the file still fails after the `&` fix — Aug 2026: after escaping
  `&`, the SAME "invalid token at line 4, column 21" persisted; the residual
  culprit was the em dash in the Document name plus emoji in placemark names
  (🦅 Prestige Golfshire, Picket Fence 🦜🦩🦎, Ajmal Flora 🖼️, Brigade
  Atmosphere 🏞️). Google's importer rejects non-ASCII tokens even though
  ElementTree parses them fine. Fix: escape `&` preserving entities AND
  transcode to pure ASCII (em dash → `-`, ₹ → `Rs.`, drop emoji / keep only
  bytes < 128), validate with `xml.etree.ElementTree` AND
  `xml.dom.minidom`, then byte-check `all(b < 128 for b in open(f,'rb').read())`.
  Escape during generation, or fix in place with a regex that preserves
  already-valid entities:
  ```python
  import re
  fixed = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)', '&amp;', kml_text)
  ```
- Validate with `xml.etree.ElementTree.parse()` (reports exact line+column)
  BEFORE uploading — one raw `&` in an otherwise perfect file still fails
  import, and the user WILL hit it the moment they try to open the map.
- **If a Drive copy was already shared, fix in place and re-upload to the
  SAME file ID** (`svc.files().update(fileId=<existing>, media_body=...)`)
  so the user's existing link keeps working — no new link, no re-download.
- Deliver the .kml via `MEDIA:/path/file.kml` so it lands as a file in chat.

## Companion R&D sheet

When NDR wants a KML + research data, also create a Google Sheet in the TMP
Drive folder (see draas-drive-organization / google-workspace-api for sheet
mechanics):

- Tab 1 **Competitors**: project, type, launch/current price, sale price,
  appreciation, developer, units, sizes, land area, status, location,
  lat/lon, Google Maps link.
- Tab 2 **Listings & Sources**: per-project portal, listed price, listing
  date/note, source link.
- Pitfall: a brand-new spreadsheet's first sheet is named `Sheet1` — rename
  it (updateSheetProperties) before writing by name, or `values().update()`
  with `Competitors!A1:P14` fails with "Unable to parse range". Make
  addSheet idempotent (check existing titles) so re-runs don't 400.

## Batch geocoding at scale (100+ POIs) — Aug 2026 battle report

Geocoding 104 POIs (projects + schools + hospitals + industries) around
Thylagere produced three failure modes NOT covered by the single-project
recipe above. Use the subprocess-isolation + incremental-save pattern:

### 1. Google throttles after ~50 rapid queries
After roughly 50 successful lookups, a wall of CONSECUTIVE fails/timeouts
begins (classic IP throttle). Symptoms: later names in the list all fail even
when they're well-known projects (Brigade Orchards, Sattva Park Cubix).
**Fix: pace the batch** — ≥4s (ideally 10s) between names, and when a run
starts failing, stop, wait, then retry only the high-value names with slow
spacing. A 20-name targeted retry with 10s spacing recovers most of them.

### 2. Playwright EPIPE kills the WHOLE python process — isolate per name
`write EPIPE` in the playwright node driver is fatal to a long batch even
when each lookup has its own try/except: the node driver process dies and
takes the batch down with it. A 1700s `timeout` then silently kills the run
mid-loop.
**Fix: one subprocess per name.** Run a small `geocode_one.py <name> <cat>`
script (it does one resolve and prints one JSON line to stdout) via
`subprocess.run([...], capture_output=True, timeout=120)` from a chunked
driver. An EPIPE inside the child kills only that one lookup; the parent
catches TimeoutExpired/Exception, records a fail, and continues. Driver
saves the results JSON after EVERY name.

### 3. Results JSON gets truncated to 0 bytes when killed mid-write
If the driver is killed during `json.dump(open(outfile,'w'))`, the file is
left at 0 bytes and the whole run's progress looks lost.
**Fix: recover from the run logs.** Every success line follows one of three
formats — parse all of them:
```python
patA = re.compile(r'^(13\.\d+),(77\.\d+) \| \[([^\]]*)\] (.*?) \| via: (.*)$')  # run/resume: "13.3,77.7 | [cat] Name | via: q"
patB = re.compile(r'^\d+/\d+ (13\.\d+),(77\.\d+) \| (.*)$')                    # chunks/final/last: "12/67 13.3,77.7 | Name"
patC = re.compile(r'^\d+/\d+ HIT (13\.\d+),(77\.\d+) \| (.*)$')                 # slow: "1/29 HIT 13.3,77.7 | Name"
```
Filter to the Bangalore box (12.5<lat<14.5, 76.5<lon<78.5) — Google's
German default (49.x, 8.x) and coarse-zoom URLs must be rejected as fails.
Rebuild the out JSON from logs + the original names file (which carries
`cat`), then resume only the still-missing names.

### 4. Names-file shape bug
The POI names file is often `[{"cat": "...", "name": "..."}]` (dicts), not a
list of strings. Any loop that does `name + " Devanahalli"` crashes with
`TypeError: unsupported operand type(s) for +: 'dict' and 'str'`. Unpack
both fields, carry `cat` through, and skip empty names.

### 5. OSM/Nominatim has ZERO coverage for this corridor
Rural plotted developments / gated communities around Devanahalli-Nandi are
absent from OSM — a Nominatim batch returned 0/29 hits. Don't burn time on
the OSM fallback for private projects; Google Maps is the only resolver.
Generic scraped labels ("Villa", "Hotel", "€182" price artifacts) should be
dropped from the batch rather than geocoded.

### 6. Never-fabricated remainder
Names that fail every pass after throttle-aware retries get recorded as
`{"lat": null}` and listed in the R&D sheet without coords — do NOT invent
coordinates for them. A 46/104 verified-coordinate dataset with 58 explicit
nulls is honest; padding with made-up points is not.

## Pricing fallback (when portals bot-wall)

99acres/MagicBricks/Housing.com aggressively block datacenter IPs (Akamai /
bot challenges) and Bing/DDG/Startpage bot-challenge too. If Firecrawl is out
of credits and every portal blocks, fall back to prices already compiled in
the project deck/PPT (if within 3 months of the request) and label them
"portal-derived July 2026" rather than fabricating fresh listings.
