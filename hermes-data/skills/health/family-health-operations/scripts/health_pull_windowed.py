#!/usr/bin/env python3
"""Windowed full-history Google Health puller (read-only).

Splits each data type into time-windowed chunks, uses the hardened paginator
(pageSize=10000; 25 for sleep/exercise), and writes one JSON file per type plus
coverage.json. It never writes to a sheet.

Usage:
  python3 health_pull_windowed.py --start 2026-10-01 --end 2026-11-15 \
      --service-name google-gmail --out-dir /data/hermes/health_pulls/20261115
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, "/opt/hermes")
import tools.gws_auth as ga  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))

# data type -> (kind, chunk_days)
TYPES = {
    "steps": ("interval", 15),
    "distance": ("interval", 15),
    "active-minutes": ("interval", 15),
    "active-zone-minutes": ("interval", 15),
    "active-energy-burned": ("interval", 15),
    "sedentary-period": ("interval", 15),
    "activity-level": ("interval", 15),
    "time-in-heart-rate-zone": ("interval", 15),
    "exercise": ("exercise", 15),
    "sleep": ("sleep", 15),
    "heart-rate": ("physical", 3),
    "oxygen-saturation": ("physical", 4),
    "heart-rate-variability": ("physical", 7),
    "respiratory-rate-sleep-summary": ("physical", 7),
    "weight": ("physical", 30),
    "body-fat": ("physical", 30),
    "height": ("physical", 30),
    "blood-glucose": ("physical", 30),
    "core-body-temperature": ("physical", 30),
    "daily-resting-heart-rate": ("daily", 30),
    "daily-heart-rate-variability": ("daily", 30),
    "daily-oxygen-saturation": ("daily", 30),
    "daily-respiratory-rate": ("daily", 30),
    "daily-sleep-temperature-derivations": ("daily", 30),
    "daily-heart-rate-zones": ("daily", 30),
    "daily-vo2-max": ("daily", 30),
}


def _snake(dt):
    return dt.replace("-", "_")


def _filter(kind, dt, start, end_excl):
    s = start.isoformat()
    e = end_excl.isoformat()
    snake = _snake(dt)
    if kind == "sleep":
        return ('sleep.interval.civil_end_time >= "%s" AND '
                'sleep.interval.civil_end_time < "%s"' % (s, e))
    if kind == "daily":
        return ('%s.date >= "%s" AND %s.date < "%s"' % (snake, s, snake, e))
    if kind == "physical":
        return ('%s.sample_time.physical_time >= "%sT00:00:00Z" AND '
                '%s.sample_time.physical_time < "%sT00:00:00Z"' % (snake, s, snake, e))
    if kind == "exercise":
        return ('exercise.interval.civil_start_time >= "%s" AND '
                'exercise.interval.civil_start_time < "%s"' % (s, e))
    return ('%s.interval.start_time >= "%sT00:00:00Z" AND '
            '%s.interval.start_time < "%sT00:00:00Z"' % (snake, s, snake, e))


def pull_type(dt, kind, chunk_days, start, end, service_name, max_pages):
    points, pages, chunks, errors = [], 0, 0, []
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=chunk_days - 1), end)
        filt = _filter(kind, dt, cur, chunk_end + timedelta(days=1))
        try:
            r = ga.google_health_list_data_points(
                dt, data_filter=filt,
                page_size=25 if dt in ("sleep", "exercise") else 10000,
                max_pages=max_pages, service_name=service_name,
            )
            points.extend(r["data_points"])
            pages += r["pages"]
            if r["truncated"]:
                errors.append("chunk %s..%s truncated at max_pages" % (cur, chunk_end))
        except Exception as e:  # noqa: BLE001
            errors.append("chunk %s..%s: %s" % (cur, chunk_end, str(e)[:200]))
        chunks += 1
        cur = chunk_end + timedelta(days=1)
    seen = set()
    unique = []
    for p in points:
        key = p.get("name") or json.dumps(p, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return {
        "data_type": dt,
        "kind": kind,
        "points": unique,
        "count": len(unique),
        "pages": pages,
        "chunks": chunks,
        "errors": errors,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=(date.today() - timedelta(days=60)).isoformat())
    ap.add_argument("--end", default=date.today().isoformat())
    ap.add_argument("--service-name", default="google-gmail")
    ap.add_argument("--out-dir",
                    default="/data/hermes/health_pulls/%s" % datetime.now(IST).strftime("%Y%m%d-%H%M%S"))
    ap.add_argument("--types", default="", help="Comma-separated subset (default: all)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--max-pages", type=int, default=None)
    a = ap.parse_args()

    sy, sm, sd = map(int, a.start.split("-"))
    ey, em, ed = map(int, a.end.split("-"))
    start, end = date(sy, sm, sd), date(ey, em, ed)
    if end < start:
        raise SystemExit("--end must be >= --start")
    os.makedirs(a.out_dir, exist_ok=True)
    wanted = [t.strip() for t in a.types.split(",") if t.strip()] or list(TYPES)
    unknown = [t for t in wanted if t not in TYPES]
    if unknown:
        raise SystemExit("unknown types: %s" % ", ".join(unknown))

    print("window %s -> %s | %d type(s) | workers=%d | out=%s" % (
        start, end, len(wanted), a.workers, a.out_dir), flush=True)
    coverage = {"start": start.isoformat(), "end": end.isoformat(),
                "service_name": a.service_name, "types": {}}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as pool:
        futs = {
            pool.submit(pull_type, dt, TYPES[dt][0], TYPES[dt][1],
                        start, end, a.service_name, a.max_pages): dt
            for dt in wanted
        }
        for fut in as_completed(futs):
            dt = futs[fut]
            try:
                r = fut.result()
            except Exception as e:  # noqa: BLE001
                print("%-37s ERROR %s" % (dt, str(e)[:160]), flush=True)
                coverage["types"][dt] = {"count": 0, "pages": 0, "chunks": 0,
                                         "errors": [str(e)[:300]]}
                continue
            with open(os.path.join(a.out_dir, dt + ".json"), "w", encoding="utf-8") as fh:
                json.dump(r["points"], fh)
            coverage["types"][dt] = {
                "count": r["count"], "pages": r["pages"], "chunks": r["chunks"],
                "errors": r["errors"],
            }
            print("%-37s %6d pts  %3d pages  %2d chunks%s" % (
                dt, r["count"], r["pages"], r["chunks"],
                "  ERR" if r["errors"] else ""), flush=True)
    coverage["elapsed_seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(a.out_dir, "coverage.json"), "w", encoding="utf-8") as fh:
        json.dump(coverage, fh, indent=1)
    total = sum(v["count"] for v in coverage["types"].values())
    print("done: %d points across %d types in %.1fs" % (
        total, len(coverage["types"]), coverage["elapsed_seconds"]), flush=True)
    print("coverage: %s" % os.path.join(a.out_dir, "coverage.json"), flush=True)


if __name__ == "__main__":
    main()