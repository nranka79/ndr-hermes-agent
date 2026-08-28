#!/usr/bin/env python3
"""T1 radius_query — scan the R&D sheet by Haversine distance around a pin.

Scans a sheet tab (Competitors + POIs & Infrastructure) for everything within
a radius (default 10 km). Coordinates, not names — this closes the class of
gap where name-driven discovery missed mid-market projects (Sammy's Palm
Hills, 6.3 km from the Thylagere subject land, was found only by radius).

Usage:
  python3 radius_query.py --sheet <id> --lat 13.3216384 --lon 77.6789048 \
      [--radius 10] [--json out.json] [--service google-draas] [--email ...]
  python3 radius_query.py --sheet <id> --place "Sampigehalli, Devanahalli" \
      [--radius 10] [--json out.json]

Place-name pins resolve via Nominatim (OSM). Prefer explicit lat/lon when the
pin comes from a Google Maps link; Nominatim resolves towns but NOT villages
or project names (use the Places crawler / geocode_batch_subproc for those).

Reports both 5 km and 10 km counts even when one radius is requested. Rows
without valid coords are reported in `unpinnable_rows`, never silently
dropped.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_io import (  # noqa: E402
    dedupe_records, haversine_km, read_records,
)


def resolve_place(place):
    """Nominatim geocode a place name -> (lat, lon) or raise."""
    import urllib.parse
    import urllib.request

    q = urllib.parse.quote(place)
    url = (f"https://nominatim.openstreetmap.org/search?q={q}"
           "&format=json&limit=1")
    req = urllib.request.Request(url, headers={
        "User-Agent": "HermesAgent/1.0 (property-rd)"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not data:
        raise RuntimeError(f"Nominatim found nothing for {place!r} — use "
                           "explicit --lat/--lon (Places/geocode batch)")
    return float(data[0]["lat"]), float(data[0]["lon"])


def _coord(rec, key):
    try:
        return float(rec[key])
    except (KeyError, TypeError, ValueError):
        return None


def _richer(rec):
    """Richer-row score for radius dedupe (psf > total > url)."""
    score = 0
    if rec.get("psf") not in (None, "", "N/A"):
        score += 4
    if rec.get("total") not in (None, "", "N/A"):
        score += 2
    if rec.get("source_url"):
        score += 1
    return score


def query(records, lat, lon, radius_km):
    """Return (within, unpinnable) for records.

    within: [{**rec, "dist_km": d}] sorted by distance, deduped by normalized
    name (keeps the richer row), within radius.
    """
    pinned = []
    unpinnable = []
    for rec in records:
        rlat = _coord(rec, "lat")
        rlon = _coord(rec, "lon")
        if rlat is None or rlon is None:
            unpinnable.append(rec)
            continue
        d = haversine_km(lat, lon, rlat, rlon)
        rec["dist_km"] = round(d, 2)
        pinned.append(rec)
    pinned.sort(key=lambda r: r["dist_km"])
    dedup = dedupe_records(pinned, score_fn=_richer)
    within = [r for r in dedup if r["dist_km"] <= radius_km]
    return within, unpinnable


def _fmt_rec(rec):
    return (
        f"{rec.get('project', rec.get('name', '?'))} | "
        f"{rec.get('type', '-')} | {rec.get('locality', '-')} | "
        f"psf={rec.get('psf', '-')} | total={rec.get('total', '-')} | "
        f"{rec['dist_km']} km | ({rec.get('lat')}, {rec.get('lon')})"
    )


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sheet", required=True)
    p.add_argument("--tab", default="Competitors",
                   help="tab to scan (repeat with --extra-tab for POIs)")
    p.add_argument("--extra-tab", action="append", default=[],
                   help="additional tabs (e.g. POIs & Infrastructure)")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--place", help="place name (Nominatim) instead of lat/lon")
    p.add_argument("--radius", type=float, default=10.0)
    p.add_argument("--range", default="A1:Z2000")
    p.add_argument("--json", help="write {within, unpinnable, counts} JSON")
    p.add_argument("--service", default="google-draas")
    p.add_argument("--email", help="vault-client fallback email")
    args = p.parse_args(argv)

    if args.lat is not None and args.lon is not None:
        lat, lon = args.lat, args.lon
    elif args.place:
        lat, lon = resolve_place(args.place)
        print(f"resolved {args.place!r} -> {lat:.6f}, {lon:.6f}")
    else:
        p.error("need --lat/--lon or --place")

    tabs = [args.tab] + args.extra_tab
    all_within, all_unpinnable = [], []
    for tab in tabs:
        records = read_records(args.sheet, tab, args.range,
                               service_name=args.service, email=args.email)
        print(f"-- {tab}: {len(records)} records read")
        within, unpinnable = query(records, lat, lon, args.radius)
        all_within.extend(within)
        all_unpinnable.extend(unpinnable)
        for rec in within:
            print("  " + _fmt_rec(rec))

    within_5 = [r for r in all_within if r["dist_km"] <= 5.0]
    within_10 = [r for r in all_within if r["dist_km"] <= 10.0]
    print(f"\nSUMMARY pin=({lat:.6f},{lon:.6f}) radius={args.radius:g} km")
    print(f"  within {args.radius:g} km: {len(all_within)} rows")
    print(f"  within 5 km: {len(within_5)} rows")
    print(f"  within 10 km: {len(within_10)} rows")
    print(f"  unpinnable (no valid coords): {len(all_unpinnable)} rows")
    for rec in all_unpinnable:
        print(f"    no-coords: {rec.get('project', rec)}")

    if args.json:
        payload = {
            "pin": {"lat": lat, "lon": lon},
            "radius_km": args.radius,
            "within": all_within,
            "unpinnable_rows": all_unpinnable,
            "counts": {
                "within_radius": len(all_within),
                "within_5km": len(within_5),
                "within_10km": len(within_10),
                "unpinnable": len(all_unpinnable),
            },
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
