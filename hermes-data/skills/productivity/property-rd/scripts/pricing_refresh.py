#!/usr/bin/env python3
"""T3 pricing_refresh — monthly pricing refresh with outlier rejection.

The LLM collects raw listings (direct portals, Google snippets for blocked
portals, Apify 99acres deep-scrape) and writes them to a listings JSON. THIS
tool applies the outlier rules, updates the Competitors tab per-sqft/totals,
appends every listing to the Listings & Sources tab, and appends an audit
row per project to the Pricing Audit tab.

Outlier rules (validated in the property-rd-tool-design blueprint):
  baseline = current sheet psf, else median of collected values
  kept     = [v for v in vals if 0.90*baseline <= v <= 1.25*baseline]
  new      = median(kept); written ONLY if kept is non-empty
  v < 0.90*baseline -> suspected drop, discarded (logged to audit)
  v > 1.25*baseline -> suspected error, flagged for review, NOT written
  If >30% of projects are fully rejected -> ALERT (portal markup likely
  changed); prints a banner and writes the raw snippets to --alert-file.

Only listings with a date inside the 30-day window (or no date) are
considered; older listings are logged and skipped.

Usage:
  python3 pricing_refresh.py --sheet <id> --listings listings.json [--dry-run]
"""

import argparse
import json
import os
import statistics
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_io import (  # noqa: E402
    append_rows, key_name, parse_num, parse_psf, read_range, read_records,
    update_cell,
)

FLOOR, CEIL = 0.90, 1.25


def _psf_value(row):
    """Numeric psf from a listing row (price can be number or display str)."""
    raw = row.get("price")
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    return parse_psf(str(raw))


def _within_window(date_str, now=None):
    """True if the listing date is inside the last 30 days (or absent)."""
    if not date_str:
        return True
    s = str(date_str).strip()
    if not s:
        return True
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            d = datetime.strptime(s[:10], fmt)
            break
        except ValueError:
            continue
    else:
        return True  # unparseable date — don't silently drop
    now = now or datetime.utcnow()
    return (now - d) <= timedelta(days=30)


def _col_letter(idx):
    return chr(ord("A") + idx)


def _locate_project_rows(raw_rows):
    """Map normalized project -> [(row_idx, psf_col, total_col), ...]."""
    if not raw_rows:
        return {}
    from sheet_io import match_header  # noqa: WPS433
    mapping = [match_header(h) for h in raw_rows[0]]
    proj_idx = mapping.index("project") if "project" in mapping else None
    psf_idx = mapping.index("psf") if "psf" in mapping else None
    total_idx = mapping.index("total") if "total" in mapping else None
    out = {}
    for i, row in enumerate(raw_rows[1:], start=1):
        if proj_idx is None or proj_idx >= len(row):
            continue
        name = row[proj_idx]
        out.setdefault(key_name(name), []).append({
            "row": i + 1,  # 1-based sheet row (header = row 1; i is 0-based
                           # within data rows so data row i maps to sheet row i+1)
            "psf_col": _col_letter(psf_idx) if psf_idx is not None else None,
            "total_col": (_col_letter(total_idx)
                          if total_idx is not None else None),
        })
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sheet", required=True)
    p.add_argument("--listings", required=True, help="listings JSON file")
    p.add_argument("--competitors-tab", default="Competitors")
    p.add_argument("--listings-tab", default="Listings & Sources")
    p.add_argument("--audit-tab", default="Pricing Audit")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--alert-file", help="write ALERT report here")
    p.add_argument("--service", default="google-draas")
    p.add_argument("--email", help="vault-client fallback email")
    args = p.parse_args(argv)

    with open(args.listings, encoding="utf-8-sig") as f:
        listings = json.load(f)
    if not listings:
        print("no listings in JSON — nothing to do")
        return 0

    raw = read_range(args.sheet, args.competitors_tab, "A1:Z2000",
                     service_name=args.service, email=args.email)
    records = read_records(args.sheet, args.competitors_tab, "A1:Z2000",
                           service_name=args.service, email=args.email)
    locator = _locate_project_rows(raw)
    current_psf = {}
    for rec in records:
        v = parse_psf(rec.get("psf"))
        if v is not None:
            current_psf.setdefault(key_name(rec.get("project")), v)

    # group listings per project
    by_project = {}
    for row in listings:
        k = key_name(row.get("project"))
        if k:
            by_project.setdefault(k, []).append(row)

    audit_rows, rejected_all = [], 0
    rejected_project_count = 0
    for k, rows in sorted(by_project.items()):
        sample = rows[0]
        display = sample.get("project", k)
        in_window = [r for r in rows if _within_window(r.get("date"))]
        skipped_old = len(rows) - len(in_window)
        vals = []
        reasons = []
        for r in in_window:
            v = _psf_value(r)
            if v is None:
                reasons.append("no price parsed")
                continue
            if r.get("date") and not _within_window(r.get("date")):
                continue
            vals.append(v)
        if skipped_old:
            reasons.append(f"{skipped_old} older than 30 days")
        if not vals:
            rejected_project_count += 1
            reasons.append("no in-window values")
            audit_rows.append([display, current_psf.get(k, ""), "",
                               len(rows), "", "ALL", "; ".join(reasons),
                               datetime.utcnow().isoformat() + "Z"])
            print(f"[{display}] SKIP: {reasons}")
            continue

        baseline = current_psf.get(k) or statistics.median(vals)
        kept = [v for v in vals
                if FLOOR * baseline <= v <= CEIL * baseline]
        dropped = sorted(set(round(v, 0) for v in vals
                             if not (FLOOR * baseline <= v <= CEIL * baseline)))
        new = statistics.median(kept) if kept else None
        old = current_psf.get(k, "")
        reason = "; ".join(reasons)
        if dropped:
            reason += ("; dropped " + ", ".join(f"Rs {d:,.0f}" for d in dropped)
                       + " (outside "
                       + f"{FLOOR:.2f}x-{CEIL:.2f}x baseline Rs {baseline:,.0f})")
        if not kept:
            rejected_project_count += 1
            rejected_all += 1
            reason += "; ALL rejected"
        audit_rows.append([display, old,
                           f"{new:,.0f}" if new is not None else "",
                           len(in_window),
                           f"{statistics.median(vals):,.0f}" if vals else "",
                           "Rejected" if not kept else "Accepted",
                           reason,
                           datetime.utcnow().isoformat() + "Z"])

        if new is not None and kept and not args.dry_run:
            for loc in locator.get(k, []):
                if loc["psf_col"]:
                    update_cell(args.sheet, args.competitors_tab,
                                f"{loc['psf_col']}{loc['row']}",
                                f"{new:,.0f}", service_name=args.service,
                                email=args.email)
            print(f"[{display}] psf {old or 'n/a'} -> {new:,.0f} "
                  f"(kept {len(kept)}/{len(vals)}, baseline {baseline:,.0f})")
        elif kept:
            print(f"[{display}] (dry-run) psf {old or 'n/a'} -> {new:,.0f}")
        else:
            print(f"[{display}] NO WRITE: {reason}")

    ratio = (rejected_project_count / len(by_project)) if by_project else 0
    if ratio > 0.30:
        msg = (f"ALERT: {rejected_project_count}/{len(by_project)} projects "
               "fully rejected (>30%) — portal markup likely changed.")
        print("\n" + "=" * 70 + f"\n{msg}\n" + "=" * 70)
        if args.alert_file:
            with open(args.alert_file, "w", encoding="utf-8") as f:
                json.dump({"alert": msg, "listings": listings}, f, indent=1)
            print(f"alert report -> {args.alert_file}")

    if not args.dry_run:
        listing_rows = [[r.get("project"), r.get("type", ""),
                         r.get("portal", ""), r.get("price", ""),
                         r.get("total", ""), r.get("date", ""),
                         r.get("url", "")] for r in listings]
        appended = append_rows(args.sheet, args.listings_tab, listing_rows,
                               service_name=args.service, email=args.email)
        print(f"appended {appended} listings to {args.listings_tab}")
        audit_headers = [["Project", "Old psf", "New psf", "n_listings",
                          "median", "verdict", "reasons", "timestamp"]]
        appended_a = append_rows(args.sheet, args.audit_tab,
                                 audit_headers + audit_rows,
                                 service_name=args.service, email=args.email)
        print(f"appended {appended_a} rows to {args.audit_tab}")
    else:
        print("(dry-run — no sheet writes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
