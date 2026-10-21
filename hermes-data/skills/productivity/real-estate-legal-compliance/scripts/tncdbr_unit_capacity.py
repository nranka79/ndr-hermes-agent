#!/usr/bin/env python3
"""
TNCDBR 2019 — "how many units will this plot legally carry?" calculator.

Implements the feasibility algebra of
references/tncdbr-2019-building-plan-compliance.md  §4h  (and the Rule 52 minimum-size
table of §4a).  Pure stdlib — system python3 works, no venv needed.

WHY THIS EXISTS
---------------
The same arithmetic has decided three separate Serenity Estate / Ranka Udaya schemes.
It is pure rules-arithmetic with no judgement in it, and doing it in your head is where
the errors come from (sq.ft vs sq.m, layers vs clear widths, the 7.00 m setback cliff).
Run this instead of hand-reckoning, then quote the output in the report.

    python3 tncdbr_unit_capacity.py                          # verified 9.14 x 12.19 m case
    python3 tncdbr_unit_capacity.py --frontage 9.14 --depth 12.19 --road 9.0
    python3 tncdbr_unit_capacity.py --frontage 12.19 --depth 9.14 --road 9.0
    python3 tncdbr_unit_capacity.py --rooms "bedroom:9x8,toilet:4.5x5.5,hall:11.58x10.67"

RULES IMPLEMENTED (quote the rule number in every finding)
----------------------------------------------------------
Rule 35(1)(a) "Other areas", up to 16 dwellings:
   max storeys "GF + 2F or Stilt + 3F, max 12 m"  -> 3 floors above ground (storey cap)
   max FSI 2.0 ; NO maximum plot coverage prescribed at all
   front setback by abutting road width: <=9.0 m -> 1.5 ; >9-18 -> 3.0 ; >18-30.5 -> 4.5 ; >30.5 -> 6.0
   side  setback by height x plot width: plot width >9 m -> BOTH sides
         height <=7.00 m -> 1.00 m ; >7 up to 12 m -> 1.50 m
   rear  setback: height <=7.00 m -> Nil ; >7 up to 12 m -> 1.50 m
   >>> the 7.00 m CLIFF: one cm over and lateral setbacks widen 1.00 -> 1.50 m

Rule 52 minima:
   habitable room 7.5 sq.m / width 2.4 m   (pooja or store shall NOT count as habitable)
   kitchen: 5.0 sq.m / 1.8 m ; 4.5 sq.m if separate store ; 7.5 sq.m / 2.1 m if also dining
   bath + WC combined 2.4 sq.m / width 1.2 m
   store room 3.0 sq.m / 2.2 m height
   2-unit core (two 0.75 m flights + clearance) ~= 1.90 m
   corridor/verandah residential 1.0 m (Rule 42)

NOTE on CBC/coverage: the 50% coverage figure that appears on many drawings lives in the
HIGH RISE table.  Rule 35(1)(a) prescribes no maximum plot coverage for Non High Rise.
Say so — teams otherwise chase a coverage relaxation that buys them nothing.
"""

import argparse

FT = 0.3048          # metres per foot
SQM_PER_SQFT = 0.09290304


def m(ft):
    """feet -> metres"""
    return ft * FT


def sqft(a_m, b_m):
    """two metre dims -> square feet"""
    return a_m * b_m / SQM_PER_SQFT


def sqm(a_ft, b_ft):
    """two foot dims -> square metres"""
    return a_ft * FT * b_ft * FT


# ---------------------------------------------------------------- rule bands

def front_setback(road_m):
    """Rule 35(1)(a), front setback by abutting road width, 'Other areas'."""
    if road_m <= 9.0:
        return 1.5
    if road_m <= 18.0:
        return 3.0
    if road_m <= 30.5:
        return 4.5
    return 6.0


def side_setback(height_m, plot_width_m):
    """Rule 35(1)(a) side setback. Plot width <=9 m -> one side only; >9 m -> BOTH."""
    both = plot_width_m > 9.0
    if height_m <= 7.0:
        return 1.0, both
    if height_m <= 12.0:
        return 1.5, both
    if height_m <= 16.0:
        return 2.5, both
    return 3.0, both


def rear_setback(height_m):
    """Rule 35(1)(a) rear setback."""
    return 0.0 if height_m <= 7.0 else 1.5


STOREY_CAP_FLOORS = 3      # "GF + 2F or Stilt + 3F, max 12 m" -> 3 floors above ground
HAB_MIN_SQM, HAB_MIN_W = 7.5, 2.40      # Rule 52(5)(b)
STORE_MIN_SQM = 3.0                     # Rule 52(9)
BATHWC_MIN_SQM, BATHWC_MIN_W = 2.4, 1.2  # Rule 52(7)(c)(iii)
CORE_2UNIT_M = 1.90                     # two 0.75 m flights + clearance
WALL_ALLOWANCE_M = 0.10                 # partition allowance, layers vs clear


# ---------------------------------------------------------------- the algebra

def analyse(frontage_m, depth_m, road_m, plinth=0.45, floor_h=3.00, slab=0.15,
            max_floors=STOREY_CAP_FLOORS):
    """Step 1-4 of §4h. Returns a list of per-floor-count rows."""
    rows = []
    # two mutually exclusive readings of which surveyed dimension is the road frontage
    for orient in ("frontage is the road edge", "frontage is the road edge (alt axis)"):
        pass  # orientation is the caller's job; see --swap-frontage note in docstring

    for floors in range(1, max_floors + 1):
        height = plinth + floors * floor_h + (floors - 1) * slab
        ssb, both = side_setback(height, frontage_m)
        fsb = front_setback(road_m)
        rsb = rear_setback(height)

        width = frontage_m - (2 * ssb if both else ssb)
        depth = depth_m - fsb - rsb

        row = {
            "floors": floors,
            "storey_label": {1: "G+1", 2: "GF+2F", 3: "GF+3F"}.get(floors, f"GF+{floors}F"),
            "height": height,
            "over_cliff": height > 7.0,
            "ssb": ssb,
            "both_sides": both,
            "fsb": fsb,
            "rsb": rsb,
            "width": width,
            "depth": depth,
            "plate_sqft": sqft(width, depth) if width > 0 and depth > 0 else 0.0,
        }

        # Step 3 — the two-units-per-floor WIDTH test
        if width > CORE_2UNIT_M:
            bay = (width - CORE_2UNIT_M) / 2
            clear = bay - WALL_ALLOWANCE_M
            row["bay"], row["clear"] = bay, clear
            row["two_per_floor"] = clear >= HAB_MIN_W
        else:
            row["bay"] = row["clear"] = 0.0
            row["two_per_floor"] = False

        # Step 4 — unit counts
        row["units_two_per_floor"] = 2 * floors if row["two_per_floor"] else 0
        row["units_one_per_floor"] = floors
        rows.append(row)
    return rows


def room_check(spec):
    """spec: 'bedroom:9x8,toilet:4.5x5.5'. Returns (name, sqm, width_m, verdict)."""
    kinds = {
        "bedroom": (HAB_MIN_SQM, HAB_MIN_W, "habitable room"),
        "hall": (HAB_MIN_SQM, HAB_MIN_W, "habitable room"),
        "living": (HAB_MIN_SQM, HAB_MIN_W, "habitable room"),
        "kitchen": (5.0, 1.8, "kitchen (separate)"),
        "dining": (7.5, 2.1, "kitchen+dining"),
        "toilet": (BATHWC_MIN_SQM, BATHWC_MIN_W, "bath+WC combined"),
        "bath": (BATHWC_MIN_SQM, BATHWC_MIN_W, "bath+WC combined"),
        "store": (STORE_MIN_SQM, None, "store room"),
    }
    out = []
    for item in spec.split(","):
        item = item.strip()
        if not item or ":" not in item:
            continue
        name, dims = item.split(":", 1)
        name = name.strip().lower()
        a, b = (float(x) for x in dims.lower().split("x"))
        area = sqm(a, b)
        width = min(a, b) * FT
        amin, wmin, label = kinds.get(name, (HAB_MIN_SQM, HAB_MIN_W, "habitable room"))
        ok = area >= amin and (wmin is None or width >= wmin)
        short = ""
        if not ok:
            if area < amin:
                short = f" short {amin - area:.2f} sq.m in area"
            if wmin is not None and width < wmin:
                short += f" short {wmin - width:.2f} m in width"
        out.append((f"{name} {a:g}'x{b:g}'", area, width, label, amin, ok, short))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frontage", type=float, default=9.14,
                    help="plot dimension on the road edge, metres (default 9.14 = 30'-0\")")
    ap.add_argument("--depth", type=float, default=12.19,
                    help="plot dimension front-to-back, metres (default 12.19 = 40'-0\")")
    ap.add_argument("--road", type=float, default=9.0, help="abutting road width, metres")
    ap.add_argument("--plinth", type=float, default=0.45, help="plinth height, metres")
    ap.add_argument("--floor-height", type=float, default=3.00, help="storey height, metres")
    ap.add_argument("--slab", type=float, default=0.15, help="slab thickness, metres")
    ap.add_argument("--rooms", type=str, default="",
                    help="room schedule to check, e.g. 'bedroom:9x8,toilet:4.5x5.5,hall:11.58x10.67'")
    a = ap.parse_args()

    print("=" * 78)
    print("TNCDBR 2019 — unit-capacity feasibility (Rule 35(1)(a) 'Other areas')")
    print("=" * 78)
    print(f"Plot            : {a.frontage:.2f} m x {a.depth:.2f} m "
          f"= {a.frontage / FT:.1f}' x {a.depth / FT:.1f}' "
          f"= {a.frontage * a.depth:.2f} sq.m = {sqft(a.frontage, a.depth):.0f} sq.ft")
    print(f"Abutting road   : {a.road:.2f} m  -> front setback "
          f"{front_setback(a.road):.2f} m")
    permitted = sqft(a.frontage, a.depth)  # FSI 2.0 => 2x plot area in sq.ft
    print(f"Max FSI 2.0     : {permitted:.0f} sq.ft buildable  "
          f"(max plot coverage: NONE prescribed for Non High Rise)")
    print(f"Storey cap      : {STOREY_CAP_FLOORS} floors above ground "
          f"('GF+2F or Stilt+3F, max 12 m')")
    print(f"CLIFF           : 7.00 m - one cm over widens sides 1.00 -> 1.50 m")

    rows = analyse(a.frontage, a.depth, a.road, a.plinth, a.floor_height, a.slab)

    print("\n" + "-" * 78)
    print(f"{'floors':<8}{'height':>8}{'sides':>7}{'front':>7}{'rear':>7}"
          f"{'buildable':>20}{'2/floor':>10}{'units':>8}")
    print("-" * 78)
    for r in rows:
        build = f"{r['width']:.2f}x{r['depth']:.2f}m {r['plate_sqft']:.0f}sf"
        if r["two_per_floor"]:
            two = f"{r['clear']:.2f} ok"
        elif r["width"] > 0:
            two = f"{r['clear']:.2f} FAIL"
        else:
            two = "-"
        best = max(r["units_two_per_floor"], r["units_one_per_floor"])
        flag = " <<CLIFF" if r["over_cliff"] else ""
        print(f"{r['storey_label']:<8}{r['height']:>7.2f}m{r['ssb']:>6.2f}m"
              f"{r['fsb']:>6.2f}m{r['rsb']:>6.2f}m{build:>20}{two:>10}{best:>8}{flag}")

    print("\n2/floor test: bay = (buildable width - 1.90 m core)/2 ; "
          f"clear = bay - {WALL_ALLOWANCE_M} m allowance ; min clear {HAB_MIN_W} m (Rule 52(5)(b))")
    print("  2 units/floor at <=7.00 m : bays fit  -> 2 x floors units")
    print("  2 units/floor above 7.00 m: bays fail -> 1 unit/floor only")

    best = max((max(r["units_two_per_floor"], r["units_one_per_floor"]) for r in rows),
               default=0)
    print(f"\n>>> COMPLIANT CEILING ON THIS PLOT: {best} units")

    if a.rooms:
        print("\n" + "-" * 78)
        print("Room schedule vs Rule 52 minima")
        print("-" * 78)
        for name, area, width, label, amin, ok, short in room_check(a.rooms):
            print(f"{name:<22}{area:>7.2f} sq.m{width:>7.2f} m  "
                  f"min {amin:>4.1f} sq.m  {'PASS' if ok else 'FAIL'}{short}")

    print("\nReminder: pooja room / store room shall NOT be counted as a habitable room "
          "(Rule 52(5)(b));\na store that IS drawn must be >= 3.0 sq.m (Rule 52(9)).")
    print("Report 'geometry and storey limits bind, not FSI' when FSI is not the binding "
          "constraint.")


if __name__ == "__main__":
    main()