"""
Pull recent activity from the Ranka Udaya pipeline (both tabs) and bucket
new / followed-up leads for the last N days.

The original version only looked at Meta-tab Remarks, but as of 14-Jul-2026
that's a dead signal for fresh intake rows (Remarks is empty, Status is
empty, Notes is empty). Real activity is in the intake columns on the
Meta tab, primarily Visit Preference and Budget.

Usage from a Hermes session (execute_code):

    exec(open('/data/hermes/skills/productivity/ranka-udaya-leads-pipeline/scripts/last_n_days_remarks.py').read())

Prints a JSON blob to stdout. Caller formats for Telegram.

Assumes:
- sheet_id = 1yaUwSos6DO56Oni2iiVJ0L26K-rRn7wzYsHKweNxUB0
- Meta tab: A=Date (dd/mm/yyyy), B=Budget, C=Visit Pref, D=Full name,
            E=Phone, F=Email, G=City, H=Status, I=Remarks, J=Next Follow Up
- Main tab: A=Lead ID, B=Lead Date (YYYY-DD-MM HH:MM AM/PM),
             C=Visit Pref, D=Budget, E=Full name, F=Email, G=Phone,
             H=City, I=Status, J=Next Followup, K=Notes,
             L=Last Synced (YYYY-DD-MM HH:MM AM/PM), M=Sync Status
"""
import sys
import json
from datetime import date, timedelta

sys.path.insert(0, '/opt/hermes')
import importlib.util
spec = importlib.util.spec_from_file_location(
    "gws_skill_bridge", "/opt/hermes/tools/gws_skill_bridge.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SHEET_ID = "1yaUwSos6DO56Oni2iiVJ0L26K-rRn7wzYsHKweNxUB0"
META_RANGE = "'Ranka Udaya - Meta'!A1:J1300"
MAIN_RANGE = "'Ranka Udaya | July'!A1:M1100"

URGENT_VISIT = ("This Weekend",)
NEAR_VISIT = ("Next Weekend",)
WARM = ("I need more details first",)


def fetch(range_str):
    raw = mod.call("sheets_get", service_name="google-draas",
                   sheet_id=SHEET_ID, range=range_str)
    return json.loads(raw)


def filter_meta_by_date_window(rows, days=3):
    """Return Meta rows whose col A (Date, dd/mm/yyyy) is within the last N days."""
    today = date.today()
    window = {(today - timedelta(days=i)).strftime("%d/%m/%Y") for i in range(days)}
    return [r for r in rows[1:] if len(r) > 0 and r[0] in window]


def _parse_ymd_dash(s):
    """Parse 'YYYY-DD-MM HH:MM AM/PM' -> date. Returns None on failure.

    The Main tab's Last Synced and Lead Date columns are YYYY-DD-MM (year, day, month).
    Confirmed 2026-07-14 — naive YYYY-MM-DD parsing misreads dates by ~5 months.
    """
    if not s:
        return None
    s = s.split()[0]
    parts = s.split("-")
    if len(parts) != 3 or len(parts[1]) != 2 or len(parts[2]) != 2:
        return None
    try:
        y, d, m = int(parts[0]), int(parts[1]), int(parts[2])
        return date(y, m, d)
    except (ValueError, TypeError):
        return None


def filter_main_by_last_synced(rows, days=3):
    """Return Main rows whose col L (Last Synced, YYYY-DD-MM) is within the last N days."""
    today = date.today()
    out = []
    for r in rows[1:]:
        if len(r) <= 11:
            continue
        d = _parse_ymd_dash(r[11])
        if d is None or d > today:
            continue
        if (today - d).days <= days - 1:
            out.append(r)
    return out


def bucket_meta_visit_pref(rows):
    """Bucket fresh intake rows by Visit Preference + Budget (the live signal)."""
    out = {"this_weekend": [], "next_weekend": [], "needs_details": [], "other": []}
    for r in rows:
        if len(r) < 7:
            continue
        vp = (r[2] or "").strip() if len(r) > 2 else ""
        bg = (r[1] or "").strip() if len(r) > 1 else ""
        rec = {"name": r[3], "phone": r[4], "budget": bg, "city": r[6]}
        if vp in URGENT_VISIT:
            out["this_weekend"].append(rec)
        elif vp in NEAR_VISIT:
            out["next_weekend"].append(rec)
        elif vp in WARM:
            out["needs_details"].append(rec)
        else:
            out["other"].append(rec)
    return out


def bucket_main_notes(rows):
    """Find Main rows with non-empty Notes — Bharat's only follow-up log.

    As of 14-Jul-2026 the entire pipeline has 2 such rows (Satishkumar Melligeri,
    Ashish). These are the only live action items in the entire pipeline.
    """
    return [
        {"name": r[4], "phone": r[6], "status": r[8], "notes": r[10],
         "last_synced": r[11] if len(r) > 11 else ""}
        for r in rows
        if len(r) > 10 and (r[10] or "").strip()
    ]


def main():
    days = 3
    meta_rows = fetch(META_RANGE)
    main_rows = fetch(MAIN_RANGE)

    recent_meta = filter_meta_by_date_window(meta_rows, days=days)
    visit_pref_buckets = bucket_meta_visit_pref(recent_meta)
    main_recent_sync = filter_main_by_last_synced(main_rows, days=days)
    main_with_notes = bucket_main_notes(main_rows)

    hot_high_budget = [
        b for b in (visit_pref_buckets["this_weekend"] + visit_pref_buckets["next_weekend"])
        if ("1 CR" in b["budget"] or "70 L" in b["budget"])
    ]

    status_dist = {}
    for r in main_rows[1:]:
        s = (r[8] if len(r) > 8 else "").strip()
        status_dist[s] = status_dist.get(s, 0) + 1

    print(json.dumps({
        "window_days": days,
        "meta_recent_count": len(recent_meta),
        "this_weekend": [b["name"] for b in visit_pref_buckets["this_weekend"]],
        "next_weekend": [b["name"] for b in visit_pref_buckets["next_weekend"]],
        "needs_details_count": len(visit_pref_buckets["needs_details"]),
        "hot_high_budget": hot_high_budget,
        "main_last_synced_in_window": len(main_recent_sync),
        "main_rows_with_notes_total": len(main_with_notes),
        "main_status_distribution": status_dist,
    }, indent=2))


if __name__ == "__main__":
    main()
