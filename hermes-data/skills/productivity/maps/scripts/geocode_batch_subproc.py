#!/usr/bin/env python3
"""Chunked batch geocoder: one subprocess per name, save after every name.

Architecture (validated Aug 2026 on a 104-name Thylagere R&D batch):
- Each name runs in its OWN subprocess (geocode_one.py). A playwright
  EPIPE crash — which kills the whole python process even with per-name
  try/except — now costs at most one name.
- Results are written to the output JSON after EVERY name. A batch can be
  killed by `timeout`, Ctrl-C, or crash at any point and the partial
  results survive. Re-run the same command to resume (already-resolved
  names are skipped).
- Google Maps throttles this datacenter IP after ~50 rapid queries
  (consecutive-fail walls). The runner sleeps ~4s between names and the
  caller should chunk a large list into multiple runs rather than trying
  all 100+ in one go.

Usage:
  python3 geocode_batch_subproc.py names.json out.json
where names.json is a list of strings OR [{"name":..., "cat":...}, ...].
Input format pitfall: if your source file has dicts with "name"/"cat"
keys and you pass them straight into string concatenation you get
`TypeError: unsupported operand type(s) for +: 'dict' and 'str'` — unpack
them first (this runner does).
"""
import json, subprocess, sys, time, os

NAMES_FILE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/geocode_names.json"
OUTFILE = sys.argv[2] if len(sys.argv) > 2 else "/tmp/geocode_out.json"
HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
ONE = os.path.join(HERE, "geocode_one.py")
SUB_TIMEOUT = 100  # 45s was too tight: 2 attempts x ~25s + launch overhead
FALLBACK_LOC = sys.argv[3] if len(sys.argv) > 3 else "Devanahalli"

names = json.load(open(NAMES_FILE))
try:
    results = json.load(open(OUTFILE))
except Exception:
    results = {}

def pending():
    out = []
    for item in names:
        if isinstance(item, dict):
            name, cat = item.get("name",""), item.get("cat","")
        else:
            name, cat = str(item), ""
        if not name:
            continue
        if name in results and results[name].get("lat"):
            continue
        out.append((name, cat))
    return out

todo = pending()
print(f"Pending: {len(todo)}", flush=True)
for i, (name, cat) in enumerate(todo, 1):
    start = time.time()
    try:
        r = subprocess.run([PY, ONE, name, cat, FALLBACK_LOC], capture_output=True, text=True, timeout=SUB_TIMEOUT)
        line = (r.stdout or "").strip().splitlines()
        if line:
            res = json.loads(line[-1])
            results[res["name"]] = {"cat": res["cat"], "lat": res["lat"], "lon": res["lon"], "query_used": res["query_used"]}
            status = f"{res['lat']},{res['lon']}" if res['lat'] else "FAIL"
            print(f"{i}/{len(todo)} {status} | {res['name']}", flush=True)
        else:
            results[name] = {"cat": cat, "lat": None, "lon": None, "query_used": None}
            print(f"{i}/{len(todo)} CRASH-noout | {name}", flush=True)
    except subprocess.TimeoutExpired:
        results[name] = {"cat": cat, "lat": None, "lon": None, "query_used": None}
        print(f"{i}/{len(todo)} TIMEOUT | {name}", flush=True)
    except Exception as e:
        results[name] = {"cat": cat, "lat": None, "lon": None, "query_used": None}
        print(f"{i}/{len(todo)} ERR {str(e)[:60]} | {name}", flush=True)
    with open(OUTFILE, "w") as f:
        json.dump(results, f, indent=2)
    # Slow pace between names to avoid the Google throttle; sleep floor for
    # instant-crash loops so we don't hammer the endpoint.
    elapsed = time.time() - start
    if elapsed < 4:
        time.sleep(max(10 - elapsed, 0))

done = sum(1 for r in results.values() if r.get("lat"))
print(f"DONE -> {OUTFILE} ({done}/{len(results)} resolved)", flush=True)
