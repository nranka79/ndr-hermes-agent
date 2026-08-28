#!/usr/bin/env python3
"""Crash-resilient batch geocoder for Google Maps headless (Playwright).

WHY THIS EXISTS
---------------
A naive batch geocoder that writes its JSON only at the END loses ALL
partial results when Playwright crashes mid-run (EPIPE on the node
transport, page timeouts, browser death). Aug 2026 session: first run
resolved 36/104 POIs then EPIPE'd — zero results persisted because the
dump happened after the loop.

THIS VERSION:
  * loads any existing output file and SKIPS names already resolved
  * SAVES AFTER EVERY NAME (crash-proof; restart resumes where it left off)
  * wraps each resolve in try/except so one bad query can't kill the batch
  * accepts input as plain strings OR [{"cat":..., "name":...}] dicts
  * validates coords against the target region (default: Bangalore box)

USAGE
-----
python3 geocode_batch_resume.py names.json [out.json]

names.json  : ["Place A", "Place B"] or [{"cat":"schools","name":"X"}, ...]
out.json    : {"<name>": {"cat":..., "lat":..., "lon":..., "query_used":...}}

RECOVERING A CRASHED PRE-RESUME RUN
-----------------------------------
If an older script died before writing output, reconstruct partial results
from its stdout log — every line has shape:
    13.3528911,77.7254375 | [IT_companies] Nagarjuna Tech Solutions | via: Nagarjuna Tech Solutions
    13.0300549,77.4493791 | [colleges] S.J.C. Institute of Technology | via: S.J.C. Institute of Technology

import re, json
partial = {}
for ln in open('run.log'):
    m = re.match(r'^(13\.\d+),(77\.\d+) \| \[([^\]]*)\] (.*?) \| via: (.*)$', ln)
    if m:
        lat, lon, cat, name, used = m.groups()
        partial[name] = {"cat": cat, "lat": float(lat), "lon": float(lon), "query_used": used}
json.dump(partial, open('out.json','w'), indent=2)
"""
import re, time, json, sys, traceback
from playwright.sync_api import sync_playwright

EXE = '/opt/hermes/.playwright/chromium_headless_shell-1234/chrome-linux/headless_shell'
# Bangalore region box — reject Google's default geolocation (Germany) and
# coarse search-result zooms. Adjust for other target geographies.
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 12.5, 14.5, 76.5, 78.5


def resolve(query, variants=None, max_attempts=2):
    """Try query then variants; return first coords found in target region."""
    tries = [query] + (variants or [])
    for t in tries[:max_attempts]:
        try:
            with sync_playwright() as p:
                b = p.chromium.launch(
                    executable_path=EXE,
                    args=['--no-sandbox', '--disable-dev-shm-usage', '--lang=en-US'])
                ctx = b.new_context(viewport={'width': 1200, 'height': 800}, locale='en-US')
                ctx.add_cookies([
                    {'name': 'CONSENT', 'value': 'YES+cb.20240101-01-p0.en+FX+100',
                     'domain': '.google.com', 'path': '/'},
                    {'name': 'SOCS', 'value': 'CAISHAgBEhJnd3NfMjAyMzAxMDEtMF9HQzIBBGgBEg',
                     'domain': '.google.com', 'path': '/'},
                ])
                pg = ctx.new_page()
                pg.goto('https://www.google.com/maps?hl=en&gl=in',
                        timeout=12000, wait_until='domcontentloaded')
                pg.wait_for_timeout(2500)
                box = pg.locator('input#searchboxinput, input[name="q"]').first
                box.fill(t)
                box.press('Enter')
                pg.wait_for_timeout(5500)
                url = pg.url
                b.close()
                m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
                if m:
                    lat, lon = float(m.group(1)), float(m.group(2))
                    if LAT_MIN < lat < LAT_MAX and LON_MIN < lon < LON_MAX:
                        return lat, lon, t
                print(f"    variant '{t}' -> no valid coords ({url[:70]})", flush=True)
        except Exception as e:
            print(f"    variant '{t}' ERR: {str(e)[:70]}", flush=True)
        time.sleep(0.5)
    return None, None, None


if __name__ == "__main__":
    names = json.load(open(sys.argv[1]))
    outfile = sys.argv[2] if len(sys.argv) > 2 else "/tmp/geocode_out.json"
    try:
        results = json.load(open(outfile))
    except Exception:
        results = {}
    print(f"Existing results: {len(results)}", flush=True)
    for item in names:
        if isinstance(item, dict):
            name = item.get("name", "")
            cat = item.get("cat", "")
        else:
            name = str(item)
            cat = ""
        if not name:
            continue
        if name in results and results[name].get("lat"):
            continue
        variants = [name + " Devanahalli", name + " Bangalore"]  # area-specific; adapt
        try:
            lat, lon, used = resolve(name, variants)
        except Exception:
            traceback.print_exc()
            lat, lon, used = None, None, None
        results[name] = {"cat": cat, "lat": lat, "lon": lon, "query_used": used}
        # SAVE AFTER EVERY NAME — never lose progress
        with open(outfile, "w") as f:
            json.dump(results, f, indent=2)
        status = f"{lat},{lon}" if lat else "FAIL"
        print(f"{status} | [{cat}] {name} | via: {used} | saved", flush=True)
        time.sleep(0.5)
    done = sum(1 for r in results.values() if r.get("lat"))
    print(f"DONE -> {outfile} ({done}/{len(results)} resolved)", flush=True)
