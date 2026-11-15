#!/usr/bin/env python3
"""Full Google Health -> tracker-sheet backfill for one family member.

Verified 2026-11-08 in Ruhaan's session: session token account rankaruh@gmail.com,
health legacyUserId DHD2R9, healthUserId 5628948378093662985, device Fitbit Air.

WHY THIS EXISTS
  A "put all my Google Health data in my medical tracker" ask is TWO destinations:
    1. log sheet  tabs Sleep / Daily Vitals / Daily Activity  -> raw device data
    2. report index tab Sleep (Wearable)                      -> curated clinical view
  Hand-rolling the pull each time re-introduces four silent bugs (pagination,
  string-typed numbers, sleep metadata nesting, rollup key nesting). This script
  has the verified shapes baked in.

USAGE
  Run from inside execute_code's python (it sets HERMES_RPC_SOCKET and routes the
  token lookup to the trusted gateway). A bare `terminal()` run can resolve the
  WRONG vault user — see google-health-api.md pitfall on terminal subprocesses.

      python3 health_backfill_sheets.py --start 2026-08-25 --end 2026-11-09          # diff only
      python3 health_backfill_sheets.py --start 2026-08-25 --end 2026-11-09 --write   # append gaps

  --end is INCLUSIVE (converted to exclusive internally).

DIFF-FIRST DISCIPLINE
  Default is read-only: it prints, per tab, the dates present in the API but
  missing from the sheet, plus sheet dates the API no longer has. Inspect that
  before --write. After writing, always read the tail rows back and confirm.
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, "/opt/hermes")
import tools.gws_auth as ga  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
SRC = "Google Health API / Fitbit Air"

# Only readonly scopes that are actually granted. Minting against the full
# including-.writeonly/.ecg/.irn list returns a token the API rejects with a
# 404 HTML body (not JSON) — the single most misleading failure mode here.
SCOPES = [
    "https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly",
    "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly",
    "https://www.googleapis.com/auth/googlehealth.sleep.readonly",
    "https://www.googleapis.com/auth/googlehealth.profile.readonly",
]

LOG_SHEET = "19OE2ItXkWf7UcdUc0fg-Yj_01MtPgQwNTidej8M-S8M"
INDEX_SHEET = "1E14iA3xDdoBaC0Sdlim6r6MipmSzNkKqFLaV2dXvHQU"

# health key (vitals dict index) -> (dataType path, filter snake, camelCase value key, getter)
DAILY = {
    1: ("daily-resting-heart-rate", "daily_resting_heart_rate", "dailyRestingHeartRate",
        lambda v: v["beatsPerMinute"]),
    2: ("daily-heart-rate-variability", "daily_heart_rate_variability", "dailyHeartRateVariability",
        lambda v: v["averageHeartRateVariabilityMilliseconds"]),
    3: ("daily-oxygen-saturation", "daily_oxygen_saturation", "dailyOxygenSaturation",
        lambda v: v["averagePercentage"]),
    5: ("daily-respiratory-rate", "daily_respiratory_rate", "dailyRespiratoryRate",
        lambda v: v["breathsPerMinute"]),
}


_SERVICE = "google-gmail"


def mint(service_name="google-gmail"):
    """Set the account for this run. The hardened helper mints and caches the
    health-only token internally, so there is no token to return."""
    global _SERVICE
    _SERVICE = service_name or "google-gmail"
    return None


def api(tok, path, params=None):
    return ga.google_health_request("GET", path, params=params, service_name=_SERVICE)


def fetch_all(tok, data_type, filt):
    """Paginate with the hardened helper: pageSize=10000 (25 for sleep/exercise),
    nextPageToken loop, retry/backoff and a cached health token."""
    page_size = 25 if data_type in ("sleep", "exercise") else 10000
    return ga.google_health_list_data_points(
        data_type, data_filter=filt, page_size=page_size,
        service_name=_SERVICE)["data_points"]


def _civ(d):
    return {"date": {"year": d.year, "month": d.month, "day": d.day},
            "time": {"hours": 0, "minutes": 0, "seconds": 0, "nanos": 0}}


def rollup(tok, data_type, d0, d1):
    """d0..d1 inclusive. Chunks at <=7 days (API cap is 14) and sends
    end = chunk_end + 1 day because the range end is EXCLUSIVE at midnight."""
    pts = []
    cur = d0
    while cur <= d1:
        chunk_end = min(cur + timedelta(days=6), d1)
        body = {"range": {"start": _civ(cur), "end": _civ(chunk_end + timedelta(days=1))},
                "windowSizeDays": 1}
        resp = ga.google_health_request(
            "POST", "users/me/dataTypes/%s/dataPoints:dailyRollUp" % data_type,
            json_body=body, service_name=_SERVICE)
        pts += resp.get("rollupDataPoints", [])
        cur = chunk_end + timedelta(days=1)
    return pts


def num(x):
    """EVERY numeric field in this API can arrive as a STRING ("495").
    Coerce before arithmetic or you get TypeError: 'str' / 'str'."""
    try:
        return int(round(float(x)))
    except (TypeError, ValueError):
        return None


def dec(x, nd=3):
    try:
        return round(float(x), nd)
    except (TypeError, ValueError):
        return ""


def to_ist(t):
    return datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(IST)


def dkey(o):
    d = (o or {}).get("date") or {}
    try:
        return "%04d-%02d-%02d" % (int(d["year"]), int(d["month"]), int(d["day"]))
    except (KeyError, TypeError, ValueError):
        return None


def build_sleep(tok, start, end):
    """Rows for the log sheet 'Sleep' tab (22 cols). mainSleep lives INSIDE
    sleep.metadata, NOT at the top level of the dataPoint."""
    filt = ('sleep.interval.civil_end_time >= "%s" AND '
            'sleep.interval.civil_end_time < "%s"' % (start, end))
    rows = {}
    for p in fetch_all(tok, "sleep", filt):
        s = p.get("sleep", {})
        md = p.get("metadata") or s.get("metadata") or {}
        if not md.get("mainSleep"):
            continue  # nap / sensor artifact — report separately, never merge
        iv, summ = s.get("interval", {}), s.get("summary", {}) or {}
        stg = {x["type"]: x for x in summ.get("stagesSummary", [])}
        st, en = to_ist(iv["startTime"]), to_ist(iv["endTime"])
        inbed = num(summ.get("minutesInSleepPeriod"))
        asleep = num(summ.get("minutesAsleep"))
        deep = num(stg.get("DEEP", {}).get("minutes"))
        rem = num(stg.get("REM", {}).get("minutes"))
        mid = st + timedelta(minutes=(en - st).total_seconds() / 120)
        rows[en.strftime("%Y-%m-%d")] = [
            en.strftime("%Y-%m-%d"), st.strftime("%H:%M"), en.strftime("%H:%M"),
            "%d:%02d" % (asleep // 60, asleep % 60) if asleep is not None else "",
            inbed,
            deep, num(stg.get("LIGHT", {}).get("minutes")), rem,
            num(summ.get("minutesAwake")), len(s.get("shortAwakenings") or []),
            num(summ.get("minutesToFallAsleep")), num(summ.get("minutesAfterWakeUp")),
            round(100 * asleep / inbed, 1) if inbed and asleep is not None else "",
            round(100 * deep / inbed, 1) if inbed and deep is not None else "",
            round(100 * rem / inbed, 1) if inbed and rem is not None else "",
            num(stg.get("DEEP", {}).get("count")), num(stg.get("REM", {}).get("count")),
            num(stg.get("LIGHT", {}).get("count")), num(stg.get("AWAKE", {}).get("count")),
            mid.strftime("%H:%M"), "Main (overnight)", SRC,
        ]
    return rows


def build_vitals(tok, start, end):
    v = {}
    for idx, (dt, snake, camel, getter) in DAILY.items():
        for p in fetch_all(tok, dt, '%s.date >= "%s" AND %s.date < "%s"' % (snake, start, snake, end)):
            vv = p.get(camel, {})
            try:
                v.setdefault(dkey(vv), {})[idx] = getter(vv)
            except (KeyError, TypeError):
                pass
    for p in fetch_all(tok, "daily-oxygen-saturation",
                       'daily_oxygen_saturation.date >= "%s" AND daily_oxygen_saturation.date < "%s"' % (start, end)):
        vv = p.get("dailyOxygenSaturation", {})
        v.setdefault(dkey(vv), {}).update({4: vv.get("lowerBoundPercentage"),
                                           8: vv.get("upperBoundPercentage")})
    for p in fetch_all(tok, "daily-heart-rate-variability",
                       'daily_heart_rate_variability.date >= "%s" AND daily_heart_rate_variability.date < "%s"' % (start, end)):
        vv = p.get("dailyHeartRateVariability", {})
        v.setdefault(dkey(vv), {})[7] = vv.get("nonRemHeartRateBeatsPerMinute")
    for p in fetch_all(tok, "daily-sleep-temperature-derivations",
                       'daily_sleep_temperature_derivations.date >= "%s" AND daily_sleep_temperature_derivations.date < "%s"' % (start, end)):
        vv = p.get("dailySleepTemperatureDerivations", {})
        d = v.setdefault(dkey(vv), {})
        try:  # baseline can be a STRING or absent -> NaN
            nightly, base = float(vv["nightlyTemperatureCelsius"]), float(vv["baselineTemperatureCelsius"])
            d[6] = round(nightly - base, 2)
        except (KeyError, TypeError, ValueError):
            pass
        d[16], d[17] = vv.get("nightlyTemperatureCelsius"), vv.get("baselineTemperatureCelsius")
    return v


def build_activity_hr(tok, start, end):
    """Rollup value keys are NESTED under a camelCase wrapper named after the
    dataType — NOT top-level. Getting this wrong yields silently empty columns."""
    a, h = {}, {}

    def k(o):
        return dkey(o) or ""

    for p in rollup(tok, "steps", start, end):
        a.setdefault(k(p["civilStartTime"]), {})["steps"] = num(p["steps"]["countSum"])
    for p in rollup(tok, "distance", start, end):
        mm = p.get("distance", {}).get("millimetersSum")
        if mm is not None:
            a.setdefault(k(p["civilStartTime"]), {})["dist"] = round(float(mm) / 1e6, 2)
    for p in rollup(tok, "active-minutes", start, end):
        lv = {x["activityLevel"]: num(x["activeMinutesSum"])
              for x in p["activeMinutes"]["activeMinutesRollupByActivityLevel"]}
        a.setdefault(k(p["civilStartTime"]), {}).update(
            L=lv.get("LIGHT"), M=lv.get("MODERATE"), V=lv.get("VIGOROUS"))
    for p in rollup(tok, "active-energy-burned", start, end):
        a.setdefault(k(p["civilStartTime"]), {})["ak"] = num(p["activeEnergyBurned"]["kcalSum"])
    for p in rollup(tok, "total-calories", start, end):
        a.setdefault(k(p["civilStartTime"]), {})["tk"] = num(p["totalCalories"]["kcalSum"])
    for p in rollup(tok, "sedentary-period", start, end):
        dur = p.get("sedentaryPeriod", {}).get("durationSum") or "0s"
        a.setdefault(k(p["civilStartTime"]), {})["sed"] = int(float(dur.rstrip("s")) // 60)
    for p in rollup(tok, "heart-rate", start, end):
        hv = p["heartRate"]
        h.setdefault(k(p["civilStartTime"]), {}).update(
            avg=dec(hv.get("beatsPerMinuteAvg"), 1), mn=hv.get("beatsPerMinuteMin"),
            mx=hv.get("beatsPerMinuteMax"))
    for p in rollup(tok, "time-in-heart-rate-zone", start, end):
        z = {x["heartRateZone"]: int(float(x["duration"].rstrip("s")) // 60)
             for x in p["timeInHeartRateZone"]["timeInHeartRateZones"]}
        h.setdefault(k(p["civilStartTime"]), {}).update(
            zL=z.get("LIGHT"), zM=z.get("MODERATE"), zV=z.get("VIGOROUS"), zP=z.get("PEAK"))
    return a, h


def gap(svc, sid, tab, api_dates):
    have = svc.spreadsheets().values().get(
        spreadsheetId=sid, range="'%s'!A2:A3000" % tab).execute().get("values", [])
    have = {r[0] for r in have if r and r[0]}
    return sorted(set(api_dates) - have), sorted(have - set(api_dates))


def append(svc, sid, tab, rows, last_col):
    """RAW keeps ISO dates / h:mm as text and JSON numbers as numbers.
    USER_ENTERED re-parses DD/MM as MM/DD and reorders date columns."""
    if not rows:
        return 0
    n = len(svc.spreadsheets().values().get(
        spreadsheetId=sid, range="'%s'!A1:A3000" % tab).execute()["values"]) + 1
    r = svc.spreadsheets().values().update(
        spreadsheetId=sid, range="'%s'!A%d:%s%d" % (tab, n, last_col, n + len(rows) - 1),
        valueInputOption="RAW", body={"values": rows}).execute()
    return r.get("updatedRows", 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--service-name", default="google-gmail")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    y, m, d = map(int, args.end.split("-"))
    end_excl = (date(y, m, d) + timedelta(days=1)).isoformat()

    tok = mint(args.service_name)
    ident = api(tok, "users/me/identity")
    print("health identity:", ident)  # PROVE whose data this is before quoting numbers

    svc = ga.build_service("sheets", "v4", service_name=args.service_name)

    sleep = build_sleep(tok, args.start, end_excl)
    vit = build_vitals(tok, args.start, end_excl)
    act, hr = build_activity_hr(tok, date.fromisoformat(args.start), date.fromisoformat(args.end))

    for tab, dates, sid in [("Sleep", list(sleep), LOG_SHEET),
                            ("Daily Vitals", list(vit), LOG_SHEET),
                            ("Daily Activity", list(act), LOG_SHEET)]:
        missing, orphan = gap(svc, sid, tab, dates)
        print("%-15s api=%d  MISSING=%s  orphan=%s" % (tab, len(dates), missing, orphan))

    if not args.write:
        print("\ndiff only — re-run with --write to append the gaps")
        return

    srows = [sleep[k] for k in sorted(sleep) if k in set(gap(svc, LOG_SHEET, "Sleep", list(sleep))[0])]
    print("Sleep           appended", append(svc, LOG_SHEET, "Sleep", srows, "V"))

    miss_v = set(gap(svc, LOG_SHEET, "Daily Vitals", list(vit))[0])
    vrows = []
    for dt in sorted(miss_v):
        v, g = vit.get(dt, {}), hr.get(dt, {})
        p = lambda i: "" if v.get(i) is None else v.get(i)
        vrows.append([dt, p(1), dec(p(2), 2), dec(p(3), 2), dec(p(4), 2), dec(p(5), 2),
                      dec(p(6), 2), p(7), dec(p(8), 2), g.get("avg", ""), g.get("mn", ""),
                      g.get("mx", ""), g.get("zL", ""), g.get("zM", ""), g.get("zV", ""),
                      g.get("zP", ""), dec(p(16)), dec(p(17)), SRC])
    print("Daily Vitals    appended", append(svc, LOG_SHEET, "Daily Vitals", vrows, "S"))

    miss_a = set(gap(svc, LOG_SHEET, "Daily Activity", list(act))[0])
    arows = []
    for dt in sorted(miss_a):
        a = act.get(dt, {})
        g = lambda k: "" if a.get(k) is None else a[k]
        arows.append([dt, g("steps"), g("dist"), g("L"), g("M"), g("V"),
                      g("ak"), g("tk"), g("sed"), SRC])
    print("Daily Activity  appended", append(svc, LOG_SHEET, "Daily Activity", arows, "J"))

    # ---- curated clinical view: Sleep (Wearable), 20 cols A..T.
    # Column S = night cough log, column T = Clinical note. NEVER write over an
    # existing T value — it is the clinician-facing annotation.
    have = {r[0] for r in svc.spreadsheets().values().get(
        spreadsheetId=INDEX_SHEET, range="'Sleep (Wearable)'!A2:A3000").execute().get("values", []) if r}
    crows = []
    for dt in sorted(sleep):
        dd, mm, yy = dt.split("-")[2], dt.split("-")[1], dt.split("-")[0]
        label = "%s/%s/%s" % (dd, mm, yy)
        if label in have:
            continue
        r = sleep[dt]
        v = vit.get(dt, {})
        p = lambda i: "" if v.get(i) is None else v.get(i)
        hh, mi = r[3].split(":")
        crows.append([label, r[1], r[2], round((int(hh) * 60 + int(mi)) / 60, 2), r[4],
                      r[5], r[13], r[6], r[7], r[14], r[8], r[9],
                      p(1), p(2), p(3), p(4), p(5), p(6), "", ""])
    print("Sleep (Wearable) appended", append(svc, INDEX_SHEET, "Sleep (Wearable)", crows, "T"))
    print("\nNow READ THE TAIL ROWS BACK and confirm before reporting.")


if __name__ == "__main__":
    main()
