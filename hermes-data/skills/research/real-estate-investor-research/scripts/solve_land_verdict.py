#!/usr/bin/env python3
"""
Land acquisition verdict solver.

Answers: what is the MAX land price (Rs Cr/acre) this parcel can carry, given
the end-product sale rate and a target developer margin? And what is land as a
% of revenue at the asking price?

Usage:
    python3 solve_land_verdict.py                        # IVC Road defaults
    python3 solve_land_verdict.py --net-acre 6.67 --ask 8.75 --sale-rate 10000
    python3 solve_land_verdict.py --ask 13 --plot-sft 1500 --bua-ratio 1.66

Pure stdlib - no numpy needed (the execute_code sandbox has no numpy).
All money internally in Rs; divided by 1e7 only at print time.
"""

import argparse

SQFT_PER_ACRE = 43560.0
CR = 1e7


def plots_count(net_acre, saleable_eff, plot_sft):
    return (net_acre * SQFT_PER_ACRE * saleable_eff) / plot_sft


def revenue_cr(plots, bua, sale_rate):
    return plots * bua * sale_rate / CR


def total_cost_cr(net_acre, land_cr_ac, layout_cr_ac, plots, bua,
                  const_per_sft, soft_pct_of_rev, rev):
    land = net_acre * land_cr_ac
    layout = net_acre * layout_cr_ac
    construct = plots * bua * const_per_sft / CR
    soft = soft_pct_of_rev * rev
    return land, layout, construct, soft, land + layout + construct + soft


def margin_at(largs, land_cr_ac):
    plots = plots_count(largs.net_acre, largs.saleable_eff, largs.plot_sft)
    bua = largs.plot_sft * largs.bua_ratio
    rev = revenue_cr(plots, bua, largs.sale_rate)
    land, layout, constru, soft, cost = total_cost_cr(
        largs.net_acre, land_cr_ac, largs.layout_cr_ac, plots, bua,
        largs.const_per_sft, largs.soft_pct_of_rev, rev)
    return (rev - cost) / rev, rev, plots, (land, layout, constru, soft)


def solve_max_land(largs, target):
    """Bisect the land price that yields exactly `target` margin."""
    lo, hi = 0.1, 60.0
    for _ in range(90):
        mid = (lo + hi) / 2
        m, _, _, _ = margin_at(largs, mid)
        if m > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--net-acre", type=float, default=6.67,
                   help="NET developable acres after kharab (NOT the RTC extent)")
    p.add_argument("--ask", type=float, default=8.75, help="asking Rs Cr/acre")
    p.add_argument("--sale-rate", type=float, default=9500,
                   help="end-product Rs/sqft (use the REALISTIC rate, not tier-1)")
    p.add_argument("--plot-sft", type=float, default=2400.0)
    p.add_argument("--bua-ratio", type=float, default=1.45,
                   help="BUA / plot_sft")
    p.add_argument("--saleable-eff", type=float, default=0.55,
                   help="saleable plot area as fraction of gross")
    p.add_argument("--const-per-sft", type=float, default=2200.0)
    p.add_argument("--layout-cr-ac", type=float, default=0.90,
                   help="layout/infra Rs Cr per acre (0.9-1.0 small parcel; "
                        "2.71 was a 33-acre township)")
    p.add_argument("--soft-pct", type=float, default=0.20,
                   help="approvals+marketing+overhead+GST as fraction of revenue")
    largs = p.parse_args()

    plots = plots_count(largs.net_acre, largs.saleable_eff, largs.plot_sft)
    bua = largs.plot_sft * largs.bua_ratio
    rev = revenue_cr(plots, bua, largs.sale_rate)

    print("=" * 74)
    print("LAND ACQUISITION VERDICT SOLVER")
    print("=" * 74)
    print(f"  Net developable     : {largs.net_acre:.3f} ac "
          f"({largs.net_acre * SQFT_PER_ACRE:,.0f} sqft)")
    print(f"  Plot / BUA          : {largs.plot_sft:,.0f} sft / {bua:,.0f} sft")
    print(f"  Plots               : {plots:.1f}  "
          f"({plots / largs.net_acre:.1f} plots/acre)")
    print(f"  Sale rate           : Rs {largs.sale_rate:,.0f}/sft  (your realistic)")
    print(f"  Revenue             : Rs {rev:,.1f} Cr")
    print(f"  ASK                 : Rs {largs.ask:.2f} Cr/acre "
          f"= Rs {largs.ask * CR / SQFT_PER_ACRE:,.0f}/sft raw land")
    print(f"  Total ask on net    : Rs {largs.net_acre * largs.ask:,.1f} Cr")

    print("\n" + "-" * 74)
    print("LAND AS % OF REVENUE (healthy = 20-25%)")
    print("-" * 74)
    for lp in (largs.ask, 7.0, 6.0):
        pct = largs.net_acre * lp / rev * 100
        flag = "OK" if pct <= 25 else "OVER 25% - paying full retail"
        print(f"  Land @ Rs {lp:5.2f} Cr/ac -> Rs {largs.net_acre * lp:6.1f} Cr "
              f"= {pct:5.1f}% of revenue   [{flag}]")

    print("\n" + "-" * 74)
    print("MAX LAND PRICE BY TARGET MARGIN @ this sale rate")
    print("-" * 74)
    for t in (0.30, 0.25, 0.20, 0.15):
        mx = solve_max_land(largs, t)
        ok = "ASK PASSES" if largs.ask <= mx else "ASK TOO HIGH"
        print(f"  {t * 100:>3.0f}% margin -> max land Rs {mx:5.2f} Cr/acre "
              f"(Rs {mx * CR / SQFT_PER_ACRE:,.0f}/sft)   [{ok}]")

    print("\n" + "-" * 74)
    print("SENSITIVITY: max land price at 25% margin by sale rate")
    print("-" * 74)
    for sr in (8000, 9000, 9500, 10000, 10500, 11000, 12000):
        largs.sale_rate = float(sr)
        mx = solve_max_land(largs, 0.25)
        ok = "PASS" if mx >= largs.ask else "FAIL"
        print(f"  Rs {sr:>6,}/sft -> max Rs {mx:5.2f} Cr/ac "
              f"(Rs {mx * CR / SQFT_PER_ACRE:,.0f}/sft)   [{ok} vs ask {largs.ask}]")

    print("\n" + "-" * 74)
    print("STRUCTURE TEST")
    print("-" * 74)
    outright = largs.net_acre * largs.ask
    jd = largs.net_acre * 1.0 + largs.net_acre * 1.0
    print(f"  Outright @ ask      : Rs {outright:6.1f} Cr cash locked in land")
    print(f"  JD (1 Cr/ac goodwill + 1 Cr/ac advance): Rs {jd:6.1f} Cr")
    print(f"  Capital at risk swing: Rs {outright - jd:6.1f} Cr "
          f"for the SAME land and the SAME exit")
    if jd < outright * 0.5:
        print("  -> JD is materially cheaper on capital. Lead with the JD counter,")
        print("     regardless of how defensible the per-acre rate looks.")
    print()


if __name__ == "__main__":
    main()
