#!/bin/bash
# Watchdog for the K-RERA plan downloader.
#
# Design: silent while rera.karnataka.gov.in is down; the moment it is
# reachable, run the downloader and print the result. Used as a cron
# `no_agent` job where EMPTY stdout = silent tick and non-empty stdout is
# delivered verbatim (watchdog pattern).
#
# Cron setup gotchas (hit live 2026-08-11):
#   - the cron `script` path must be a BARE FILENAME under the Hermes
#     scripts dir (/data/hermes/scripts/), not an absolute path
#   - schedule "20m" creates a ONE-SHOT job; "every 20m" is recurring
#   - bound `repeat` so a dead site doesn't poll forever
#
# Copy to /data/hermes/scripts/ as e.g. rera_watchdog.sh, then:
#   cronjob create no_agent=True script=rera_watchdog.sh schedule='every 20m' repeat=500
set -u
DIR="${RERA_PLAN_DIR:-/opt/data/rera_rowvilla_plans}"
OUT="$DIR/out"
DONE_MARKER="$DIR/.done"

if [ -f "$DONE_MARKER" ]; then
  exit 0   # already downloaded once -- stay silent
fi

# Quick reachability probe (independent of the python script's own check)
if ! curl -s -o /dev/null --max-time 25 -A "Mozilla/5.0" "https://rera.karnataka.gov.in/home"; then
  exit 0   # still down -- silent
fi

# Site is up: run the downloader
cd "$DIR" 2>/dev/null || cd /tmp
python3 "$DIR/krera_download_plans.py" --out "$OUT" 2>&1
rc=$?
if [ $rc -eq 0 ]; then
  touch "$DONE_MARKER"
  echo "Karnataka RERA is back up. Plan downloads complete:"
  echo
  python3 - <<'PYEOF'
import json
p = "/opt/data/rera_rowvilla_plans/out/report.json"
try:
    rep = json.load(open(p))
except Exception as e:
    print("report unreadable:", e); raise SystemExit
for proj in rep.get("projects", []):
    print("###", proj["name"], "| RERA spec:", proj.get("rera_spec") or "-")
    if proj.get("error"):
        print("  ERROR:", proj["error"])
    for m in proj.get("matches", [])[:2]:
        print("  matched:", m["project_name"], "|", m["rera_id"], "|", m.get("promoter_name",""), "|", m.get("status",""))
    for d in proj.get("plans_downloaded", []):
        print("  PLAN:", d["kind"], "->", d["file"], f"({d['bytes']} B)")
    if not proj.get("plans_downloaded") and not proj.get("error"):
        print("  (no plan-classified docs; all docs saved under docs/)")
print()
print("Output dir:", p)
PYEOF
else
  echo "Karnataka RERA is up but the downloader exited rc=$rc -- see output above."
fi
