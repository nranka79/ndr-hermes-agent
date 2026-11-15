#!/usr/bin/env python3
"""Probe EVERY Google Health data type for a date window and report what exists.

Read-only. Run inside execute_code (needs HERMES_RPC_SOCKET for the right vault user).

    python3 /tmp/health_inventory.py --start 2026-09-05 --end 2026-11-11
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta

sys.path.insert(0, "/opt/hermes")
import tools.gws_auth as ga  # noqa: E402

FULL = [
    "https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly",
    "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly",
    "https://www.googleapis.com/auth/googlehealth.sleep.readonly",
    "https://www.googleapis.com/auth/googlehealth.profile.readonly",
    "https://www.googleapis.com/auth/googlehealth.nutrition.readonly",
    "https://www.googleapis.com/auth/googlehealth.ecg.readonly",
    "https://www.googleapis.com/auth/googlehealth.irn.readonly",
]
NARROW = FULL[:4]

# dataType path -> filter family
INTERVAL = ["steps", "distance", "active-minutes", "active-zone-minutes",
            "active-energy-burned", "total-calories", "sedentary-period", "floors",
            "altitude", "activity-level", "calories-in-heart-rate-zone",
            "time-in-heart-rate-zone", "vo2-max", "run-vo2-max", "daily-vo2-max",
            "exercise", "swim-lengths-data", "sleep",
            "hydration-log", "nutrition-log",
            "electrocardiogram", "irregular-rhythm-notification"]
DAILY = ["daily-resting-heart-rate", "daily-heart-rate-variability",
         "daily-oxygen-saturation", "daily-respiratory-rate",
         "daily-sleep-temperature-derivations", "daily-heart-rate-zones",
         "daily-vo2-max"]
# sample / measurement types MUST use <snake>.sample_time.physical_time. Classifying them as
# interval yields FILTER-ERR 400, which reads identically to "no data" and once hid a real
# 40-night respiratory-rate series plus manual weight/height records (verified 2026-11-15).
PHYSICAL = ["heart-rate", "weight", "body-fat", "height", "blood-glucose",
            "core-body-temperature", "heart-rate-variability",
            "respiratory-rate-sleep-summary", "oxygen-saturation"]

TYPES = [(t, "interval") for t in INTERVAL] + [(t, "daily") for t in DAILY] + \
        [(t, "physical") for t in PHYSICAL]


_SERVICE = "google-gmail"


def mint():
    """Use the hardened helper; no manual token needed."""
    return None, "helper"


def api(tok, path, params=None):
    try:
        return ga.google_health_request("GET", path, params=params, service_name=_SERVICE), None
    except Exception as e:  # noqa: BLE001
        return None, str(e)[:160]


def fetch(tok, dt, filt, cap=6):
    try:
        r = ga.google_health_list_data_points(
            dt, data_filter=filt, max_pages=cap,
            page_size=25 if dt in ("sleep", "exercise") else 10000,
            service_name=_SERVICE)
        return r["data_points"], None
    except Exception as e:  # noqa: BLE001
        return None, str(e)[:160]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-09-05")
    ap.add_argument("--end", default=date.today().isoformat())
    a = ap.parse_args()
    y, m, d = map(int, a.end.split("-"))
    end_excl = (date(y, m, d) + timedelta(days=1)).isoformat()

    tok, tag = mint()
    print("token minted with:", tag)
    ident, err = api(tok, "users/me/identity")
    print("identity:", ident or err)
    if err:
        return

    rows = []
    for dt, fam in TYPES:
        snake = dt.replace("-", "_")
        if fam == "daily":
            filt = '%s.date >= "%s" AND %s.date < "%s"' % (snake, a.start, snake, end_excl)
        elif fam == "physical":
            filt = '%s.sample_time.physical_time >= "%sT00:00:00Z" AND ' \
                   '%s.sample_time.physical_time < "%sT00:00:00Z"' % (snake, a.start, snake, end_excl)
        else:
            filt = '%s.interval.civil_start_time >= "%s" AND ' \
                   '%s.interval.civil_start_time < "%s"' % (snake, a.start, snake, end_excl)
        pts, err = fetch(tok, dt, filt)
        if err:  # fall back: no filter, tiny page — shows whether the type is reachable at all
            pts2, err2 = fetch(tok, dt, None, cap=1)
            note = "FILTER-ERR %s" % err if err2 else "no-filter probe: %d pt (filter rejected)" % len(pts2 or [])
            print("%-38s %-9s %s" % (dt, fam, note))
            rows.append((dt, 0, note))
            continue
        keys = sorted((pts[0].get(dt.replace("-", "")) or pts[0].get(
            "".join(w.capitalize() if i else w for i, w in enumerate(dt.split("-")))) or {}).keys()) if pts else []
        print("%-38s %-9s %5d pts   %s" % (dt, fam, len(pts), ",".join(keys[:8])))
        rows.append((dt, len(pts), ",".join(keys[:8])))

    live = [r for r in rows if r[1] > 0]
    print("\n=== %d of %d types carry data ===" % (len(live), len(rows)))
    for dt, n, k in live:
        print("  %-36s %5d" % (dt, n))
    open("/tmp/health_inventory.json", "w").write(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
