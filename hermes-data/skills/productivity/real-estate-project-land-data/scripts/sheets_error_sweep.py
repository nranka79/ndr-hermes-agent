#!/usr/bin/env python3
"""Sweep EVERY tab of a Google Sheet for error values, and report shape.

Run this after any structural change to a sheet. Renaming or replacing a tab
silently breaks formulas in OTHER tabs, and those broken rows are easy to miss
because the tab you edited looks perfect. (Real case: a Payment Schedule tab
pointed at 'Oasis - Villa Price List' after that tab had been renamed to
'Oasis - All Units (Area Stmt)' -- three rows sat at #REF! unnoticed.)

Usage:
    /opt/hermes/.venv/bin/python sheets_error_sweep.py <SPREADSHEET_ID>
    /opt/hermes/.venv/bin/python sheets_error_sweep.py <SPREADSHEET_ID> --tab "Payment Schedule"
    /opt/hermes/.venv/bin/python sheets_error_sweep.py <SPREADSHEET_ID> --service google-draas

Exit code 1 if any error cell is found, so it can gate a build pipeline.
"""
import argparse
import sys

sys.path.insert(0, "/opt/hermes")
from tools import gws_auth  # noqa: E402

ERRORS = ("#REF!", "#VALUE!", "#N/A", "#DIV/0!", "#NAME?", "#ERROR!", "#NULL!", "#NUM!")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spreadsheet_id")
    ap.add_argument("--tab", help="limit to one tab title")
    ap.add_argument("--service", default="google-draas",
                    help="vault service_name -- resolve with gws_resolve_account, never guess")
    ap.add_argument("--range", default="A1:AZ300", help="range scanned per tab")
    args = ap.parse_args()

    svc = gws_auth.build_service("sheets", "v4", service_name=args.service)
    meta = svc.spreadsheets().get(spreadsheetId=args.spreadsheet_id).execute()

    total_bad = 0
    for sh in meta.get("sheets", []):
        title = sh["properties"]["title"]
        if args.tab and title != args.tab:
            continue

        # UNFORMATTED_VALUE is the render that exposes computed results;
        # FORMULA shows formula text, the default render shows formatted strings.
        vals = svc.spreadsheets().values().get(
            spreadsheetId=args.spreadsheet_id,
            range=f"'{title}'!{args.range}",
            valueRenderOption="UNFORMATTED_VALUE",
        ).execute().get("values", [])

        bad = []
        for i, row in enumerate(vals):
            for j, cell in enumerate(row):
                if isinstance(cell, str) and cell.strip() in ERRORS:
                    bad.append((i + 1, j, cell))

        populated = sum(1 for r in vals if r and str(r[0]).strip())
        total_bad += len(bad)
        status = "OK" if not bad else f"{len(bad)} ERROR CELLS"
        print(f"{title!r}: rows={len(vals)} populated={populated}  -> {status}")
        for rn, cn, code in bad[:15]:
            col = chr(65 + cn) if cn < 26 else str(cn)
            print(f"    row {rn}, col {col}: {code}")
        if len(bad) > 15:
            print(f"    ... and {len(bad) - 15} more")

    print(f"\nTOTAL ERROR CELLS: {total_bad}")
    print("share link: https://docs.google.com/spreadsheets/d/" + args.spreadsheet_id + "/edit")
    return 1 if total_bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
