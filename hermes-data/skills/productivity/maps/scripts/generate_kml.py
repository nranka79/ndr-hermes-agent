#!/usr/bin/env python3
"""
generate_kml.py — Generate KML files for Google My Maps import.

Produces a KML with:
  - Placemarks (pins) at each coordinate
  - Lines (paths) connecting them with distance labels
  - Configurable line colour/width

Usage:
  # Hub-and-spoke: central pin with lines to each satellite
  python3 generate_kml.py --hub 13.091 77.587 "Ranka Northstar" \
    --spoke 13.0777 77.5977 "Jakkur" \
    --spoke 13.1376 77.6040 "Yelahanka AFS" \
    --spoke 13.1976 77.7075 "BIAL" \
    --spoke 12.9515 77.6706 "HAL" \
    --mode driving \
    --output map.kml

  # Sequential route: A → B → C → D
  python3 generate_kml.py \
    --pin 13.091 77.587 "Ranka Northstar" \
    --pin 13.0777 77.5977 "Jakkur" \
    --pin 13.1376 77.6040 "Yelahanka AFS" \
    --pin 13.1976 77.7075 "BIAL" \
    --connect-all \
    --mode straight \
    --output route.kml

Specify --mode driving/walking/cycling to use OSRM road distances.
Specify --mode straight for Haversine straight-line distances.

If neither --hub nor --connect-all is set, each spoke line is drawn
from the FIRST pin to every subsequent pin (default hub = first pin).
"""

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def haversine_km(lat1, lon1, lat2, lon2):
    """Straight-line distance in km (Haversine formula)."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_osrm_distance(lat1, lon1, lat2, lon2, profile="driving"):
    """Get road distance in km via OSRM. Returns None on failure."""
    profile_map = {"driving": "driving", "walking": "foot", "cycling": "bike"}
    prof = profile_map.get(profile, "driving")
    url = (f"https://router.project-osrm.org/route/v1/{prof}/"
           f"{lon1},{lat1};{lon2},{lat2}?overview=false")
    try:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(url, headers={"User-Agent": "HermesAgent/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("code") == "Ok" and data.get("routes"):
            return data["routes"][0]["distance"] / 1000.0
    except Exception:
        pass
    return None


def fmt_distance(km):
    """Format distance for display label."""
    if km < 1:
        return f"{round(km * 1000)} m"
    return f"{round(km, 2)} km"


def colour_hex(r, g, b):
    """KML AABBGGRR colour string from 0-255 RGB."""
    return f"ff{b:02x}{g:02x}{r:02x}"


# ---------------------------------------------------------------------------
# KML Builder
# ---------------------------------------------------------------------------

def make_kml(pins, lines, name="My Map"):
    """Build a KML document string.

    pins: list of {name, lat, lon, description?}
    lines: list of {name, coords: [(lat,lon),...], distance_km?, colour?}
    """
    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append('<kml xmlns="http://www.opengis.net/kml/2.2">')
    parts.append('  <Document>')
    parts.append(f'    <name>{escape(name)}</name>')

    # Style for pins
    parts.append("""
    <Style id="pinStyle">
      <IconStyle>
        <Icon>
          <href>http://maps.google.com/mapfiles/ms/icons/red-dot.png</href>
        </Icon>
      </IconStyle>
      <LabelStyle>
        <scale>1.0</scale>
      </LabelStyle>
    </Style>""")

    parts.append("""
    <Style id="labelStyle">
      <IconStyle>
        <scale>0</scale>
      </IconStyle>
      <LabelStyle>
        <scale>1.1</scale>
        <color>ff000000</color>
      </LabelStyle>
    </Style>""")

    # --- Placemarks (pins) ---
    for i, pin in enumerate(pins):
        desc = escape(pin.get("description", pin["name"]))
        parts.append(f"""
    <Placemark>
      <name>{escape(pin['name'])}</name>
      <description>{desc}</description>
      <styleUrl>#pinStyle</styleUrl>
      <Point>
        <coordinates>{pin['lon']},{pin['lat']},0</coordinates>
      </Point>
    </Placemark>""")

    # --- Lines ---
    colours = [
        colour_hex(0x00, 0x66, 0xFF),  # blue
        colour_hex(0xFF, 0x44, 0x00),  # orange
        colour_hex(0x00, 0xCC, 0x00),  # green
        colour_hex(0xCC, 0x00, 0xCC),  # purple
        colour_hex(0xFF, 0xCC, 0x00),  # amber
        colour_hex(0x66, 0x00, 0xCC),  # indigo
        colour_hex(0x00, 0x88, 0x88),  # teal
        colour_hex(0xDD, 0x22, 0x22),  # red
    ]

    for li, line in enumerate(lines):
        colour = line.get("colour", colours[li % len(colours)])
        coords_str = " ".join(f"{lon},{lat},0" for lat, lon in line["coords"])
        dist_label = ""
        if line.get("distance_km") is not None:
            dist_label = f" — {fmt_distance(line['distance_km'])}"

        line_name = escape(f"{line['name']}{dist_label}")

        parts.append(f"""
    <Placemark>
      <name>{line_name}</name>
      <styleUrl>#labelStyle</styleUrl>
      <LineString>
        <extrude>1</extrude>
        <tessellate>1</tessellate>
        <coordinates>{coords_str}</coordinates>
      </LineString>
      <Style>
        <LineStyle>
          <color>{colour}</color>
          <width>3</width>
        </LineStyle>
      </Style>
    </Placemark>""")

    parts.append('  </Document>')
    parts.append('</kml>')
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_coord(s):
    """Parse a coordinate string to float."""
    try:
        return float(s)
    except ValueError:
        print(f"error: invalid coordinate '{s}'", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate KML files for Google My Maps import.")
    parser.add_argument("--pin", action="append", nargs=3,
                        metavar=("LAT", "LON", "NAME"),
                        help="Add a pin at LAT,LON named NAME.")
    parser.add_argument("--hub", nargs=3, metavar=("LAT", "LON", "NAME"),
                        help="Central pin (hub) — lines drawn from here to each --spoke.")
    parser.add_argument("--spoke", action="append", nargs=3,
                        metavar=("LAT", "LON", "NAME"),
                        help="Satellite pin connected to the hub.")
    parser.add_argument("--mode", default="driving",
                        choices=["driving", "walking", "cycling", "straight"],
                        help="Routing mode (default: driving). 'straight' = Haversine.")
    parser.add_argument("--connect-all", action="store_true",
                        help="Connect pins sequentially in order given.")
    parser.add_argument("--output", "-o", default="map.kml",
                        help="Output KML file path.")
    parser.add_argument("--map-name", default="Custom Map",
                        help="Name for the map in KML header.")

    args = parser.parse_args()

    # Collect pins
    pins = []
    if args.pin:
        for p in args.pin:
            pins.append({"name": p[2], "lat": parse_coord(p[0]),
                         "lon": parse_coord(p[1])})

    if args.hub:
        hub = {"name": args.hub[2], "lat": parse_coord(args.hub[0]),
               "lon": parse_coord(args.hub[1])}
        pins.insert(0, hub)
        for s in (args.spoke or []):
            pins.append({"name": s[2], "lat": parse_coord(s[0]),
                         "lon": parse_coord(s[1])})

    if not pins:
        print("error: no pins defined. Use --pin, --hub+--spoke, or both.",
              file=sys.stderr)
        sys.exit(1)

    # Determine lines
    lines = []
    if args.connect_all:
        # Sequential A→B→C→D...
        for i in range(len(pins) - 1):
            a, b = pins[i], pins[i + 1]
            dist = (get_osrm_distance(a["lat"], a["lon"], b["lat"], b["lon"])
                    if args.mode != "straight"
                    else haversine_km(a["lat"], a["lon"], b["lat"], b["lon"]))
            if dist is None:
                dist = haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
            lines.append({
                "name": f"{a['name']} → {b['name']}",
                "coords": [(a["lat"], a["lon"]), (b["lat"], b["lon"])],
                "distance_km": dist,
            })
    else:
        # Hub-and-spoke: first pin → each subsequent pin
        hub = pins[0]
        for i in range(1, len(pins)):
            spoke = pins[i]
            dist = (get_osrm_distance(hub["lat"], hub["lon"],
                                      spoke["lat"], spoke["lon"])
                    if args.mode != "straight"
                    else haversine_km(hub["lat"], hub["lon"],
                                      spoke["lat"], spoke["lon"]))
            if dist is None:
                dist = haversine_km(hub["lat"], hub["lon"],
                                    spoke["lat"], spoke["lon"])
                # If OSRM failed, note it was fallback
            lines.append({
                "name": f"{hub['name']} → {spoke['name']}",
                "coords": [(hub["lat"], hub["lon"]),
                           (spoke["lat"], spoke["lon"])],
                "distance_km": dist,
            })

    # Build KML
    kml = make_kml(pins, lines, name=args.map_name)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(kml)

    print(f"wrote {args.output}")
    print(f"  pins: {len(pins)}")
    print(f"  lines: {len(lines)}")
    for line in lines:
        label = fmt_distance(line["distance_km"])
        print(f"    {line['name']}: {label}")


if __name__ == "__main__":
    main()
