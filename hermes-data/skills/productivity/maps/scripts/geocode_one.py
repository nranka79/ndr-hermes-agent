#!/usr/bin/env python3
"""Geocode ONE name in an isolated subprocess; print a single JSON line to stdout.

Why a subprocess per name: the Google Maps headless flow dies with EPIPE
crashes from the playwright node driver. Those unhandled 'error' events kill
the ENTIRE python process even when every query is wrapped in try/except
(observed Aug 2026: 104-name batch, two different in-process scripts, both
died mid-run). Isolating each lookup in its own subprocess means one crash
costs at most one name.

Usage: python3 geocode_one.py "Name" "category"
Output: {"name":..., "cat":..., "lat":..., "lon":..., "query_used":...}
lat/lon are None when unresolvable. Only coords inside the Bangalore region
(12.5-14.5, 76.5-78.5) are accepted — rejects the headless browser's
default Germany resolution.
"""
import re, time, json, sys
from playwright.sync_api import sync_playwright

EXE = '/opt/hermes/.playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell'

def resolve(query, variants=None, max_attempts=2):
    tries = [query] + (variants or [])
    for t in tries[:max_attempts]:
        try:
            with sync_playwright() as p:
                b = p.chromium.launch(executable_path=EXE, args=['--no-sandbox','--disable-dev-shm-usage','--lang=en-US'])
                ctx = b.new_context(viewport={'width':1200,'height':800}, locale='en-US')
                ctx.add_cookies([
                    {'name':'CONSENT','value':'YES+cb.20240101-01-p0.en+FX+100','domain':'.google.com','path':'/'},
                    {'name':'SOCS','value':'CAISHAgBEhJnd3NfMjAyMzAxMDEtMF9HQzIBBGgBEg','domain':'.google.com','path':'/'},
                ])
                pg = ctx.new_page()
                pg.goto('https://www.google.com/maps?hl=en&gl=in', timeout=12000, wait_until='domcontentloaded')
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
                    if 12.5 < lat < 14.5 and 76.5 < lon < 78.5:
                        return lat, lon, t
        except Exception:
            pass
        time.sleep(0.3)
    return None, None, None

if __name__ == "__main__":
    name = sys.argv[1]
    cat = sys.argv[2] if len(sys.argv) > 2 else ""
    fallback_loc = sys.argv[3] if len(sys.argv) > 3 else "Devanahalli"
    variants = [name + " " + fallback_loc, name + " Bangalore"]
    lat, lon, used = resolve(name, variants)
    print(json.dumps({"name": name, "cat": cat, "lat": lat, "lon": lon, "query_used": used}))
