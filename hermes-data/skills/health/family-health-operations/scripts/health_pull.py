#!/usr/bin/env python3
"""Pull a user's Google Health (Fitbit) data using the hardened helper.

Usage: python3 health_pull.py [service_name=google-gmail] [days=7]

Uses tools.gws_auth.google_health_request / google_health_list_data_points:
explicit pageSize, nextPageToken paging, retry/backoff, and a cached health-only
token (one mint per run, not per page).
"""
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, "/opt/hermes")
import tools.gws_auth as ga  # noqa: E402

SERVICE = sys.argv[1] if len(sys.argv) > 1 else "google-gmail"
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 7


def main():
    ident = ga.google_health_request("GET", "users/me/identity", service_name=SERVICE)
    print("IDENTITY:", ident)

    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    start = today - timedelta(days=DAYS)

    # Sleep sessions (civil end-time window); the API caps pageSize at 25.
    sleep_filter = (
        'sleep.interval.civil_end_time >= "%s" AND '
        'sleep.interval.civil_end_time < "%s"' % (start, today + timedelta(days=1))
    )
    sb = ga.google_health_list_data_points(
        "sleep", data_filter=sleep_filter, page_size=25, service_name=SERVICE,
    )
    print("\nSLEEP:")
    for dp in sb["data_points"]:
        sl = dp.get("sleep", {}) or {}
        sm = sl.get("summary", {}) or {}
        iv = sl.get("interval", {}) or {}
        stages = {x.get("type"): x.get("minutes") for x in (sm.get("stagesSummary") or [])}
        print("  %s -> %s | %s | asleep=%s | %s" % (
            iv.get("startTime"), iv.get("endTime"), sl.get("type"),
            sm.get("minutesAsleep"), stages,
        ))

    def roll(name, dt):
        roll_days = min(DAYS, 14)  # dailyRollUp rejects ranges > 14 days
        roll_start = today - timedelta(days=roll_days)
        body = {"range": {
            "start": {"date": {"year": roll_start.year, "month": roll_start.month,
                               "day": roll_start.day},
                      "time": {"hours": 0, "minutes": 0, "seconds": 0, "nanos": 0}},
            "end": {"date": {"year": today.year, "month": today.month, "day": today.day},
                    "time": {"hours": 0, "minutes": 0, "seconds": 0, "nanos": 0}},
        }}
        rb = ga.google_health_request(
            "POST", "users/me/dataTypes/%s/dataPoints:dailyRollUp" % dt,
            json_body=body, service_name=SERVICE,
        )
        print("\n%s:" % name)
        for rp in rb.get("rollupDataPoints", []) or []:
            d = (rp.get("civilStartTime") or {}).get("date") or {}
            day = "%s-%02d-%02d" % (d.get("year"), d.get("month") or 1, d.get("day") or 1)
            vals = {k: v for k, v in rp.items()
                    if k not in ("civilStartTime", "civilEndTime")}
            print("  %s: %s" % (day, vals))

    roll("STEPS", "steps")
    roll("ACTIVE MINUTES", "active-minutes")
    roll("ACTIVE ENERGY", "active-energy-burned")
    roll("ACTIVE ZONE MINUTES", "active-zone-minutes")

    # Daily metric types (camelCase value keys)
    for name, dt, ff in [("RESTING HR", "daily-resting-heart-rate",
                          "daily_resting_heart_rate.date")]:
        f2 = '%s >= "%s"' % (ff, start)
        rb = ga.google_health_list_data_points(
            dt, data_filter=f2, page_size=10000, service_name=SERVICE,
        )
        print("\n%s:" % name)
        for dp in rb["data_points"]:
            val = next((v for k, v in dp.items()
                        if k != "dataSource" and isinstance(v, dict)), {})
            print("  ", val)


if __name__ == "__main__":
    main()