# Batch Geocoding — Crash, Throttle & Recovery Lessons (Aug 2026 Thylagere run)

Full transcript of geocoding 104 POIs around Thylagere/Devanahalli via headless
Google Maps search. Four failed runs taught the patterns below; the fifth
(slow-paced, subprocess-isolated) landed 19/19 on the final retry.

## The failure sequence (what NOT to do)

1. **Run 1 — single process, JSON at end.** 36/104 resolved, then Playwright
   EPIPE crash killed the whole python process. JSON never written → ALL
   results lost. *Fix: save after every name.*
2. **Run 2 — JSON dicts vs strings.** Names file was `[{"name","cat"}]` but
   script did `name + " Devanahalli"` → TypeError on the first row. *Fix:
   unpack dicts; carry category into results.*
3. **Run 3 — resume with EPIPE still fatal.** Even with save-after-every-name,
   an EPIPE in the shared Playwright driver process killed the loop; ~62/104
   done when it died. *Fix: one subprocess per name (`subprocess.run([py,
   geocode_one.py, name, cat], timeout=...)`) so a driver crash kills at
   most one lookup.*
4. **Run 4 — 45s subprocess cap too tight.** Each name tries base + 2
   variants, each variant ≈ 12s nav + 2.5s + 5.5s wait + launch ≈ 25s →
   two attempts ≈ 50s > 45s cap → mass `TIMEOUT` on names that would have
   resolved. *Fix: 100–120s cap.*
5. **The throttle wall.** After ~50 successful queries in a run, everything
   after goes FAIL in a consecutive block — even well-known projects
   (Brigade Orchards, Sattva Park Cubix, JW Marriott Golfshire). This is
   Google rate-limiting the datacenter IP. *Fix: STOP, wait, re-run the
   high-value failures slowly.*

## The working pattern (final pass)

- `geocode_one.py` — one name per subprocess; sets CONSENT + SOCS cookies;
  interactive search (type into `#searchboxinput`, press Enter, wait);
  reads `@lat,lon` from URL; rejects coords outside Bangalore bounds
  (12.5 < lat < 14.5, 76.5 < lon < 78.5) so the German geolocation default
  never counts as a hit.
- Driver script: loads existing `outfile`, skips names already resolved,
  runs each pending name via subprocess with timeout=100–120, **writes the
  JSON after every name**, sleeps `max(10 - elapsed, 2)` between names.
- Variants tried per name, in order: `name`, `name + " Devanahalli"`,
  `name + " Bangalore"`. First in-bounds hit wins.

## Recovery from a truncated/0-byte output JSON

`open(f, 'w')` truncates before writing — a kill between truncate and dump
leaves a 0-byte file even though "saves after every name" ran. Recovery:

1. Parse ALL run logs for lines that carry coords + name.
2. Log line format must be stable across runs:
   `13.34162,77.69956 | [cat] Name | via: query_used`
   (the `via:` tail doubles as provenance).
3. Multiple different formats in old logs force a multi-regex parse — this
   is why keeping ONE format matters:
   - `13.35,77.72 | [cat] Name | via: q` (run/resume style)
   - `i/N 13.35,77.72 | Name` (chunked/final style, no cat)
   - `i/N HIT 13.35,77.72 | Name` (slow/targeted style)
4. Rebuild the full dict from the names file (categories), overlaying
   recovered coords; re-run only the still-missing names.

## Junk-label filtering

Maps category-scrape produces pseudo-POIs: `Hotel`, `Resort hotel`,
`Government Hospital`, `Villa`, `€182`. These are category/price labels,
not places. Filter them from the dataset BEFORE the geocode pass and from
the results after — they pollute counts and burn throttle budget.

## Nominatim fallback reality

OSM/Nominatim has essentially zero coverage for rural plotted developments
in the Devanahalli/Nandi belt — a 29-name Nominatim pass returned zero hits
(while Google Maps resolved 19/19 on retry). For rural plotted/gated
developments, Google Maps headless is the ONLY resolver; skip the OSM
fallback pass entirely.

## Deliverable shape (sheet + KML)

- R&D sheet: `Competitors` tab keeps price/developer/units; append GPS
  columns (lat, lon, `https://www.google.com/maps?q=lat,lon&hl=en`).
  New `POIs & Infrastructure` tab: #, Name, Category, Type label, GPS,
  Maps link, Geocoded flag.
- Watch cell-level write glitches: one float lat landed as `13` (truncated)
  while its Maps link had the full value — verify GPS columns after write
  and fix stray cells directly.
- KML with all points: `lon,lat` order, style per category (subject =
  red paddle, villa = ylw, plot = grn, other = blu), subject land pinned
  first. Upload to the R&D TMP Drive folder alongside the sheet.

## Environment pitfall: playwright missing from venvs (Aug 2026 Thylagere rerun)

The geocode scripts import `playwright.sync_api`, but playwright was NOT
installed in any venv (`/opt/hermes/.venv`, `/data/hermes/.venv`,
`/opt/data/.venv`) even though the browser binary exists at
`/opt/hermes/.playwright/chromium_headless_shell-1234/`. Running the
batch with system `python3` produces `CRASH-noout` for EVERY name (the
subprocess dies on ModuleNotFoundError with empty stdout) — looks like a
massive failure, it's just a missing module. Fix:

1. Install once: `uv pip install --python /opt/data/.venv/bin/python playwright`
   (validated 1.62.0; greenlet + pyee come along)
2. Run the batch with the venv python:
   `/opt/data/.venv/bin/python geocode_batch_subproc.py names.json out.json`
   — `sys.executable` propagates the right interpreter to each geocode_one
   subprocess.
3. Confirm with a single test lookup first (should print a JSON line with
   lat/lon, not a traceback).

Also: `execute_code` sandbox lacks `GWS_VAULT_SOCKET` — Google Sheets/Drive
scripts that use `tools.gws_auth.build_service()` or vault-client must run
via `terminal`, not execute_code. The socket is at `/run/gws-vault/vault.sock`.
