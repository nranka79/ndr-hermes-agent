#!/usr/bin/env python3
"""T2 kml_generator — deterministic KML from the R&D sheet. NO LLM in the
KML path (LLM-generated XML breaks escaping — seen in earlier builds).

The LLM extracts data (web_search / apify / firecrawl), writes rows to the
sheet via sheet_io.py append, and THIS tool turns the sheet into KML.

Each placemark carries:
  - name:  `Project | Rs X/sqft` (label) — per-sqft rate alongside the name
  - styleUrl: fixed icon per project type (user-approved icon map, see
    references/kml-icons.md)
  - description: ALL project details + the pricing source URL(s) the
    per-sqft rate was computed from (joined from the Listings & Sources tab)

Rules (validated on Aug-2026 belt runs):
  - 100% ASCII (Rs for Rs, no em dashes), XML-escaped, minidom-validated
  - `new_project`/`other` types are RECLASSIFIED by name/price signals before
    icon assignment (plots-in-price -> plot, BHK/sqft -> apartment, villa in
    name -> villa)
  - coordinate-bucket dedupe (round to 4 dp), keep the richest row
  - rows without valid coords go to the sheet, NOT the KML (reported)
  - upload via drive.files().update() on the SAME file id keeps the link

Usage:
  python3 kml_generator.py --sheet <id> --subject-name "Thylagere Land" \
      --subject-lat 13.3216384 --subject-lon 77.6789048 \
      [--radius 10] [--labels price] [--out rd.kml] [--drive-file-id <id>]
  python3 kml_generator.py --from-json preview.json --subject-name "T" \
      --subject-lat 13.32 --subject-lon 77.67   # preview mode, no sheet
"""

import argparse
import json
import os
import re
import sys
from xml.dom import minidom
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_io import (  # noqa: E402
    ascii_fold, coord_bucket, key_name, parse_psf, read_records,
)

KML_NS = "http://www.opengis.net/kml/2.2"
# Icons are self-hosted on the VPS (nginx serves /kml-icons/ from
# /opt/hermes/kml-icons/, root-owned 755/644 — outside hermes-data so the
# restricted perms there are untouched). Google's mapfiles CDN is no longer
# referenced, so KML files don't depend on an external host (previously
# farms.png/warehouse.png 404'd).
ICON_BASE = "https://transcribe.ahfl.in/kml-icons/"

# User-approved icon map (maps skill references/realestate-kml-categories.md;
# hrefs curl-verified 200 + visually confirmed Aug-2026; farm/warehouse/mall/
# temple hrefs re-verified 200 on 2026-08-04 — farms.png and warehouse.png
# returned 404 and were replaced by agriculture.png / truck.png; icons now
# self-hosted at ICON_BASE, all 18 files validated 200 on 2026-08-04).
TYPE_ICONS = {
    "subject": ("shapes/star.png", 1.4),
    "apartment": ("pushpin/blue-pushpin.png", 1.0),
    "villa": ("shapes/realestate.png", 1.0),
    "plot": ("pushpin/grn-pushpin.png", 1.0),
    "farm": ("shapes/agriculture.png", 1.0),
    "gated": ("shapes/homegardenbusiness.png", 1.0),
    "hospital": ("shapes/hospitals.png", 1.0),
    "school": ("shapes/schools.png", 1.0),
    "college": ("shapes/library.png", 1.0),          # college + university
    "industry": ("shapes/factory.png", 1.0),         # manufacturing
    "warehouse": ("shapes/truck.png", 1.0),          # logistics truck
    "techpark": ("shapes/electronics.png", 1.0),     # tech parks / IT
    "sez": ("shapes/museum.png", 1.0),               # SEZ / industrial park
    "mall": ("shapes/shopping.png", 1.0),
    "temple": ("shapes/landmark.png", 1.0),          # classical building —
    #                                                    closest worship-adjacent icon in mapfiles
    "hotel": ("shapes/lodging.png", 1.0),
    "transport": ("shapes/subway.png", 1.0),
    "new_project": ("shapes/info.png", 1.0),         # only after reclass fails
    "other": ("shapes/info.png", 1.0),
}

_TYPE_SYNONYMS = {
    "villa": ["villa", "villas", "luxuryvilla", "rowhouse", "rowhouses"],
    "apartment": ["apartment", "apartments", "flat", "flats", "residential"],
    "plot": ["plot", "plots", "plotted", "plotteddevelopment",
             "residentialplot", "land", "residentialland", "plotdevelopment",
             "plotsofland"],
    "farm": ["farm", "farmland", "farmhouse", "agrifarm", "farms"],
    "gated": ["gated", "gatedcommunity", "community", "gatedplots"],
    "hospital": ["hospital", "multispeciality", "hospitality", "clinic"],
    "school": ["school", "schools"],
    "college": ["college", "colleges", "university", "universities",
                "engineeringcollege", "medicalcollege"],
    "industry": ["industry", "industrial", "manufacturing", "factory",
                 "industrialarea"],
    "warehouse": ["warehouse", "warehousing", "logistics"],
    "techpark": ["techpark", "techparkit", "ittechpark", "ittech",
                 "informationtechnology", "technologyspark"],
    "sez": ["sez", "specialeconomiczone", "industrialpark", "economiczone"],
    "mall": ["mall", "shoppingmall", "retail", "shopping"],
    "temple": ["temple", "ashram", "spiritual", "religious", "church",
               "mosque", "gurudwara", "monastery"],
    "hotel": ["hotel", "5starhotel", "resort", "lodging"],
    "transport": ["transport", "metro", "railwaystation", "airport",
                  "busterminal"],
    "new_project": ["newproject", "newprojects", "prelaunch",
                    "underconstruction", "newlaunch"],
    "subject": ["subject", "subjectland", "landparcel", "subjectparcel"],
}


def norm_type(raw_type):
    """Map a raw type string to a canonical icon category."""
    if raw_type is None:
        return "other"
    t = re.sub(r"[^a-z0-9]", "", str(raw_type).lower())
    if not t:
        return "other"
    for cat, syns in _TYPE_SYNONYMS.items():
        if t in syns:
            return cat
        for s in syns:
            if t == s:
                return cat
    return "other"


def reclassify(rec):
    """new_project/other -> real category by name+price signals.

    From the Aug-2026 Bestamanahalli run: "plots" in price text -> plot;
    BHK/apt/sqft configs -> apartment; "villa" in name -> villa.
    """
    name = str(rec.get("project") or rec.get("name") or "").lower()
    price = str(rec.get("total") or "") + " " + str(rec.get("psf") or "")
    price = price.lower()
    if "villa" in name:
        return "villa"
    if "farm" in name:
        return "farm"
    if "plot" in name or "plot" in price or "acres" in price:
        return "plot"
    if "bhk" in price or "sqft" in price or "apartment" in price:
        return "apartment"
    return None


def effective_type(rec):
    t = norm_type(rec.get("type"))
    if t in ("new_project", "other"):
        reclass = reclassify(rec)
        if reclass:
            return reclass
    return t


def label_for(rec, with_price=True):
    """KML name label: `Project | Rs X/sqft` (NDR preference)."""
    name = str(rec.get("project") or rec.get("name") or "?")
    if not with_price:
        return name
    psf = parse_psf(rec.get("psf"))
    if psf is None and rec.get("total") and rec.get("area"):
        # compute rate = total / area, mark approx (never fabricate)
        total = parse_psf(rec.get("total"))
        area = parse_psf(rec.get("area"))
        if total is not None and area and area > 0:
            return f"{name} | Rs {round(total / area):,}/sqft (approx)"
        return name
    if psf is not None:
        return f"{name} | Rs {psf:,.0f}/sqft"
    return name


def description_for(rec, sources):
    """Full detail balloon. sources: list of {portal, price, total, date,
    url} for this project (from the Listings & Sources tab)."""
    lines = [f"Project: {rec.get('project', rec.get('name', '?'))}"]
    lines.append(f"Type: {rec.get('type', '-')}")
    if rec.get("developer"):
        lines.append(f"Developer: {rec.get('developer')}")
    if rec.get("locality"):
        lines.append(f"Locality: {rec.get('locality')}")
    if rec.get("dist_km"):
        lines.append(f"Distance from subject: {rec['dist_km']} km")
    if rec.get("units"):
        lines.append(f"Units: {rec.get('units')}")
    if rec.get("launch_price"):
        lines.append(f"Launch Price: {rec.get('launch_price')}")
    if rec.get("psf"):
        lines.append(f"Current Price (per sq.ft): {rec.get('psf')}")
    if rec.get("total"):
        lines.append(f"Current Sale Price (Total): {rec.get('total')}")
    if rec.get("appreciation"):
        lines.append(f"Appreciation: {rec.get('appreciation')}")
    if rec.get("maps_link"):
        lines.append(f"Google Maps: {rec.get('maps_link')}")
    if rec.get("source_url") and not sources:
        sources = [{"portal": "listing", "price": rec.get("psf", ""),
                    "total": rec.get("total", ""), "date": "",
                    "url": rec.get("source_url")}]
    lines.append("Pricing sources:")
    if sources:
        for i, s in enumerate(sources, 1):
            parts = []
            if s.get("portal"):
                parts.append(s["portal"])
            if s.get("price"):
                parts.append(f"Rs {s['price']}")
            if s.get("total"):
                parts.append(f"({s['total']})")
            if s.get("date"):
                parts.append(f"[{s['date']}]")
            if s.get("url"):
                parts.append(s["url"])
            lines.append(f"{i}. {' - '.join(parts)}")
    else:
        lines.append("1. none on file")
    return "\n".join(lines)


def _stylesheet():
    """<Style> blocks for every icon category."""
    styles = []
    for cat, (icon, scale) in TYPE_ICONS.items():
        styles.append(
            f'    <Style id="{cat}">\n'
            f"      <IconStyle>\n"
            f"        <scale>{scale}</scale>\n"
            f"        <Icon><href>{ICON_BASE}{icon}</href></Icon>\n"
            f"      </IconStyle>\n"
            f"      <LabelStyle><scale>1.0</scale></LabelStyle>\n"
            f"    </Style>")
    return "\n".join(styles)


def build_kml(competitors, pois, subject=None, title="R&D Map",
              labels="price"):
    """Build KML string from sheet records. Returns (kml, stats)."""
    stats = {"placemarks": 0, "no_coords": [], "types": {}}

    parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    parts.append(f'<kml xmlns="{KML_NS}">')
    parts.append("  <Document>")
    parts.append(f"    <name>{escape(ascii_fold(title))}</name>")
    parts.append(_stylesheet())

    def emit(rec, cat, is_subject=False):
        label = (str(rec.get("project") or rec.get("name") or "?")
                 if is_subject else label_for(rec, labels == "price"))
        desc = (rec.get("description") if is_subject and rec.get("description")
                else description_for(rec, rec.get("_sources", [])))
        name = escape(ascii_fold(label))
        desc = escape(ascii_fold(desc))
        lon, lat = rec["lon"], rec["lat"]
        parts.append("    <Placemark>")
        parts.append(f"      <name>{name}</name>")
        parts.append(f"      <description>{desc}</description>")
        parts.append(f"      <styleUrl>#{cat}</styleUrl>")
        parts.append("      <Point>")
        parts.append(f"        <coordinates>{lon},{lat},0</coordinates>")
        parts.append("      </Point>")
        parts.append("    </Placemark>")
        stats["placemarks"] += 1
        stats["types"][cat] = stats["types"].get(cat, 0) + 1

    if subject:
        subj_rec = {"project": subject.get("name"), "lat": subject["lat"],
                    "lon": subject["lon"], "type": "subject",
                    "description": subject.get("description")}
        emit(subj_rec, "subject", is_subject=True)

    seen = set()
    for rec in competitors:
        if rec.get("lat") is None or rec.get("lon") is None:
            stats["no_coords"].append(
                rec.get("project", rec.get("name", "?")))
            continue
        bucket = coord_bucket(rec["lat"], rec["lon"])
        if bucket in seen:
            continue
        seen.add(bucket)
        emit(rec, effective_type(rec))

    for rec in pois:
        if rec.get("lat") is None or rec.get("lon") is None:
            stats["no_coords"].append(
                f"POI {rec.get('project', rec.get('name', '?'))}")
            continue
        emit(rec, effective_type(rec))

    parts.append("  </Document>")
    parts.append("</kml>")
    kml = "\n".join(parts)

    # Validate: must parse and be well-formed
    minidom.parseString(kml)
    return kml, stats


def _load_sheet_records(args):
    competitors = read_records(args.sheet, args.competitors_tab,
                               args.range, service_name=args.service,
                               email=args.email)
    listings = []
    if args.listings_tab:
        try:
            listings = read_records(args.sheet, args.listings_tab,
                                    args.range, service_name=args.service,
                                    email=args.email)
        except Exception as exc:  # tab missing is not fatal
            print(f"warning: listings tab unreadable: {exc}")
    pois = []
    if args.pois_tab:
        try:
            pois = read_records(args.sheet, args.pois_tab,
                                args.range, service_name=args.service,
                                email=args.email)
        except Exception as exc:
            print(f"warning: POIs tab unreadable: {exc}")

    # join listings -> per-project source lists (normalized-name match)
    by_project = {}
    for row in listings:
        by_project.setdefault(key_name(row.get("project")), []).append(row)
    for rec in competitors:
        rec["_sources"] = by_project.get(key_name(rec.get("project")), [])

    # optional radius filter around subject pin
    if args.subject_lat is not None and args.subject_lon is not None and \
            args.radius:
        from sheet_io import haversine_km  # noqa: WPS433
        kept = []
        for rec in competitors:
            try:
                d = haversine_km(args.subject_lat, args.subject_lon,
                                 float(rec["lat"]), float(rec["lon"]))
            except (KeyError, TypeError, ValueError):
                kept.append(rec)
                continue
            rec["dist_km"] = round(d, 2)
            if d <= args.radius:
                kept.append(rec)
        competitors = kept
    return competitors, pois


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sheet", help="R&D spreadsheet id")
    p.add_argument("--competitors-tab", default="Competitors")
    p.add_argument("--pois-tab", default="POIs & Infrastructure")
    p.add_argument("--listings-tab", default="Listings & Sources")
    p.add_argument("--range", default="A1:Z2000")
    p.add_argument("--subject-name")
    p.add_argument("--subject-lat", type=float)
    p.add_argument("--subject-lon", type=float)
    p.add_argument("--radius", type=float,
                   help="only competitors within this many km of the pin")
    p.add_argument("--labels", choices=["price", "none"], default="price")
    p.add_argument("--title", default="Competitive R&D Map")
    p.add_argument("--out", default="rd.kml")
    p.add_argument("--drive-file-id",
                   help="upload via files().update() keeping the SAME id")
    p.add_argument("--service", default="google-draas")
    p.add_argument("--email", help="vault-client fallback email")
    p.add_argument("--from-json",
                   help="preview mode: read {competitors, pois, listings} "
                        "from a JSON file instead of the sheet (debug only)")
    args = p.parse_args(argv)

    if args.from_json:
        with open(args.from_json, encoding="utf-8-sig") as f:
            data = json.load(f)
        competitors, pois = data.get("competitors", []), data.get("pois", [])
        by_project = {}
        for row in data.get("listings", []):
            by_project.setdefault(key_name(row.get("project")), []).append(row)
        for rec in competitors:
            rec["_sources"] = by_project.get(key_name(rec.get("project")), [])
    else:
        if not args.sheet:
            p.error("need --sheet or --from-json")
        competitors, pois = _load_sheet_records(args)

    subject = None
    if args.subject_name and args.subject_lat is not None and \
            args.subject_lon is not None:
        subject = {"name": args.subject_name, "lat": args.subject_lat,
                   "lon": args.subject_lon}

    kml, stats = build_kml(competitors, pois, subject=subject,
                           title=args.title, labels=args.labels)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(kml)
    print(f"wrote {args.out} ({stats['placemarks']} placemarks)")
    print(f"  types: {stats['types']}")
    if stats["no_coords"]:
        print(f"  no-coords (sheet only, NOT in KML): {len(stats['no_coords'])}")
        for name in stats["no_coords"][:15]:
            print(f"    - {name}")

    if args.drive_file_id:
        from sheet_io import update_drive_file  # noqa: WPS433
        with open(args.out, "rb") as f:
            update_drive_file(args.drive_file_id, f.read(),
                              service_name=args.service, email=args.email)
        print(f"uploaded to Drive file {args.drive_file_id} (link preserved)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
