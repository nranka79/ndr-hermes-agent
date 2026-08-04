#!/usr/bin/env python3
"""coords_from_urls — extract GPS coordinates from Google Maps links.

Project websites often embed a Google Maps link (or plain
"maps.google.com/?q=...") — parse lat/lon straight out of it instead of
re-geocoding. Patterns handled:

  https://maps.google.com/?q=12.8566,77.6584
  https://www.google.com/maps/place/.../@12.8566,77.6584,15z
  https://maps.google.com/?ll=12.8566,77.6584
  https://www.google.com/maps?q=...&center=12.85,77.65
  .../maps/...!3d12.8566!4d77.6584...
  https://maps.app.goo.gl/AbCdEf   (short link -> followed via redirect)

Usage:
  python3 coords_from_urls.py urls.json        # [{"url": "..."}]
  python3 coords_from_urls.py links.txt        # one URL per line
  python3 coords_from_urls.py urls.json --out coords.json

Output JSON: {"url": {"lat": 12.8566, "lon": 77.6584} | null, ...}
"""

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request

# Order matters: !3d/!4d is the precise place pin when present; the @tlng
# after it is only the viewport center and can differ.
_PATTERNS = [
    re.compile(r"!3d([+-]?\d{1,3}\.\d{2,})!4d([+-]?\d{1,3}\.\d{2,})"),
    re.compile(r"[@/]([+-]?\d{1,3}\.\d{2,}),\s*([+-]?\d{1,3}\.\d{2,})"),
    re.compile(r"(?:[?&](?:q|ll|center|daddr|saddr)=)"
               r"([+-]?\d{1,3}\.\d{2,}),\s*([+-]?\d{1,3}\.\d{2,})"),
]


def _parse_coords(url):
    """Return (lat, lon) parsed from a full URL, or None."""
    for pat in _PATTERNS:
        m = pat.search(url)
        if m:
            lat, lon = float(m.group(1)), float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
    # query-param fallback (q=lat,lon inside ?q= encoded)
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    for key in ("q", "ll", "center", "daddr"):
        if key in qs:
            val = qs[key][0]
            m = re.match(r"\s*([+-]?\d{1,3}\.\d{2,})\s*,\s*"
                         r"([+-]?\d{1,3}\.\d{2,})", val)
            if m:
                return float(m.group(1)), float(m.group(2))
    return None


def expand_short(url, timeout=15):
    """Follow a redirect (goo.gl / maps.app.goo.gl) to the real URL."""
    req = urllib.request.Request(url, method="HEAD", headers={
        "User-Agent": "Mozilla/5.0 (compatible; HermesAgent/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.geturl()
    except Exception:
        return url


def extract(url, follow=True):
    """(lat, lon) for a URL, following short links when asked."""
    latlon = _parse_coords(url)
    if latlon:
        return latlon
    if follow and re.search(r"(maps\.app\.goo\.gl|goo\.gl/maps|g\.co/kgs)", url):
        expanded = expand_short(url)
        return _parse_coords(expanded)
    return None


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", help="JSON list of {url} or plain text file")
    p.add_argument("--out", help="output JSON path (default stdout)")
    p.add_argument("--no-follow", action="store_true",
                   help="don't follow short links")
    args = p.parse_args(argv)

    with open(args.input, encoding="utf-8") as f:
        content = f.read()
    try:
        data = json.loads(content)
        urls = [u["url"] if isinstance(u, dict) else u for u in data]
    except json.JSONDecodeError:
        urls = [ln.strip() for ln in content.splitlines()
                if ln.strip() and not ln.lstrip().startswith("#")]

    result = {}
    for u in urls:
        latlon = extract(u, follow=not args.no_follow)
        result[u] = ({"lat": latlon[0], "lon": latlon[1]}
                     if latlon else None)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=1)
        print(f"wrote {args.out}")
    else:
        print(json.dumps(result, indent=1))

    parsed = sum(1 for v in result.values() if v)
    print(f"parsed {parsed}/{len(result)} URLs", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
