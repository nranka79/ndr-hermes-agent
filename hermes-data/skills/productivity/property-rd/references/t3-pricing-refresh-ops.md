# T3 Pricing-Refresh Operating Notes (monthly cron)

Sheet: `1EQv1zm7j5vV9NUuAsWpSLalENqg8xgKWvaL_QvvGYaM` (Thylagere R&D).
Run record: 2026-08-04 (first full T3 cron pass).

## Auth (cron-safe)

`build_service` resolves identity from the session's Telegram id. In cron
there is no session → it returns a Resource with wrong creds, no exception,
and every API call 403s. The plain `PYTHONPATH=/opt/hermes` invocation is NOT
enough. Use the shim:

```bash
PYTHONPATH=/opt/hermes python3 scripts/vault_fallback_runner.py \
    scripts/sheet_io.py read <sheet> --tab Competitors --email ndr@draas.com
```

The `google-draas` vault token (ndr@draas.com) is the one with access; the
`google-ahfl` / `google-gmail` tokens 403 on this sheet.

## Pre-run checks (avoid the false ALERT)

1. **Pricing Audit tab must exist.** pricing_refresh appends to it and 400s
   ("Unable to parse range") when missing. Create via Sheets API:

```python
from tools.gws_vault_client import resolve, get_token
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
uid = resolve('email', 'ndr@draas.com')
raw = get_token(uid, 'google-draas', session_uid=uid)
creds = Credentials.from_authorized_user_info(json.loads(raw))
sv = build('sheets','v4',credentials=creds)
sv.spreadsheets().batchUpdate(spreadsheetId=SHEET, body={
  "requests": [{"addSheet": {"properties": {"title": "Pricing Audit"}}}]}).execute()
```

2. **Scan the Competitors psf column for total-price text.** Rows whose
   `Current Price (per sq.ft)` cell contains `₹\d+(\.\d+)?\s*(L|Cr|Lakh)`
   without `/sqft`/`per sq` parse to baselines of Rs 1–82 → every collected
   value is rejected → the project counts toward the >30% ALERT. These are
   data-quality rejects, not portal-markup rejects. Known offenders
   (2026-08): Arvind The Park, Barca At Godrej Msr City, Earthsong By Manyata,
   Embassy Edge, Embassy Greenshore, Embassy Verde, Lodha Fiorana, Sattva
   Aeropolis, Sattva Vasanta Skye, Total Environment Tangled Up In Green.
   Clean the cell (move the total to `Current Sale Price (Total)`) or exclude
   the row before running; otherwise the ALERT banner is a false positive.

## Listing collection order (per sources-registry)

1. Direct portals (curl OK): NoBroker project pages render a live
   "avg ₹X per sq ft" — strong priority-1 source
   (`nobroker.in/flats-for-sale-in-<slug>-prjtl`).
2. Google snippets for 99acres/MagicBricks/Housing rate pages — validate each
   against raw context; locality-table rows (₹9,424/sqft Devanahalli avg,
   ₹67,613/sqft Assetz Promise of Spring, ₹60,220/sqft Northern Boulevard)
   are artifacts and must be skipped.
3. Apify 99acres deep-scrape (totals only; no per-sqft).

Only projects with at least one defensible in-window figure go in
`listings-<date>.json`. ~59 listings for ~45 projects is a normal harvest.

## Exact-name matching

Use the EXACT project name from the Competitors tab in listings.json.
`key_name` strips locality tokens; "Futurearth North Woods" does not match
"Futurearth North Woods : Premium Plots in Chikkaballapura - North Bengaluru."
and the write silently no-ops (harmless if the value is unchanged).

## Verify after the run

Read back the D column of Competitors and diff against the pre-run snapshot
(keep `/tmp/t3_competitors_raw.json`). Expect exactly the accepted projects'
cells to change, each on ITS OWN row — a one-row-off write pattern means the
`_locate_project_rows` off-by-one regressed (fixed 2026-08; sheet row = i+1).
Also confirm: Listings & Sources grew by N listings, Pricing Audit by
N+1 rows (header + per-project audits).

## 2026-08-04 run record

- 59 listings appended (Listings & Sources), 46 rows appended (Pricing Audit).
- 25 Competitors psf cells updated on correct rows.
- ALERT fired: 19/45 rejected. 10 were bogus (total-in-psf-column baselines,
  see pre-run check #2); 9 genuine stale-baseline signals (Prestige Sanctuary
  17,000→25,455 collected; Godrej Royale Woods 15,500 vs 8,947/11,656
  collected; Merusri Bharathi Enclave 3,500 vs 8,203; RAK Felicity 4,738 vs
  6,420; Century Trails 3,800 vs 7,333; Sumadhura Panorama 9,200 vs 6,833;
  Chartered Fireflies 11,350 vs 9,550; Aero Spring City 4,500 vs 3,066;
  Century Seasons 6,681 vs 3,550).
- Prestige Golfshire moved 32,837 → 40,027 from a single ₹30Cr villa listing —
  flag single-listing moves for human review.
- Script bugs fixed during the run (already in code, do not regress):
  - `sheet_io._NUM_RE` `[\d,]+` matched bare commas in corrupted psf cells →
    ValueError; now `\d[\d,]*(?:\.\d+)?`.
  - `pricing_refresh._locate_project_rows` row index off-by-one (wrote one row
    above the project); now `row: i + 1`.
