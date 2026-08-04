#!/usr/bin/env python3
"""Shared Sheets/Drive I/O for the property-rd toolset.

Auth: per-user OAuth via the gws-vault (tools.gws_auth.build_service) with a
vault-client fallback (resolve email -> get_token) for sessions where the
default build_service path 403s (observed in Aug-2026 belt runs).

Pure helpers (haversine, normalize, ascii fold, price parse, header matching)
have NO external dependencies so they can be unit-tested anywhere; google-api
imports are lazy.

CLI modes:
  python3 sheet_io.py tabs <spreadsheet_id> [--service google-draas]
  python3 sheet_io.py read <spreadsheet_id> [--tab <name>] [--range A1:Z1000]
  python3 sheet_io.py append <spreadsheet_id> <tab> <rows.json> [--service ...]

rows.json is a list of lists (row values) or a list of dicts keyed by header
(highest-confidence row wins per matching header column).

The LLM writes data to sheets via `append` (JSON on disk), never by direct
sheet API calls in chat; KML is generated from the sheet by kml_generator.py.
"""

import argparse
import json
import math
import os
import re
import sys

# ---------------------------------------------------------------------------
# Pure helpers (no external deps — importable anywhere)
# ---------------------------------------------------------------------------

_R = 6371.0  # Earth radius km


def haversine_km(lat1, lon1, lat2, lon2):
    """Straight-line distance in km (Haversine)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return 2 * _R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_name(name):
    """Lowercase, strip non-alphanumerics — for dedupe/compare."""
    if name is None:
        return ""
    return _NON_ALNUM.sub("", str(name).lower())


def _word_tokens(name):
    """Lowercased alnum word tokens of a name (for locality stripping)."""
    if name is None:
        return []
    return re.findall(r"[a-z0-9]+", str(name).lower())


# Locality tokens to strip BEFORE comparing names across the sheet (Aug-2026
# belt runs: "Assetz City Of Palms Ivc" vs "Assetz City of Palms IVC Road,
# Bangalore North" are the same project).
_LOCALITY_SINGLE = {
    "devanahalli", "sadahalli", "singarahalli", "kamenahalli", "ivc",
    "hosahudya", "neraganahalli", "thylagere", "bidaganahalli",
    "beedaganahalli", "nandi", "msrcity", "bangalore", "bengaluru",
    "anekal", "attibele", "chandapura", "electroniccity", "hosur",
    "sarjapur", "whitefield", "yelahanka", "hebbal", "doddaballapur",
    "road", "village",
}

# Multi-word phrases ("ivc road", "bangalore north") must be stripped as a
# unit — single-token stripping leaves "road"/"north" behind and the names
# don't match.
_LOCALITY_PHRASES = [
    "bangalore north", "bangalore south", "bangalore east",
    "bangalore west", "ivc road", "msr city", "electronic city",
    "northern peripheral ring road", "devanahalli taluk", "anekal taluk",
]


def strip_locality_tokens(name):
    """Remove locality tokens from a name (word-boundary aware).

    normalize_name collapses whitespace entirely, so phrase stripping works
    on the word tokens (re.findall) instead of the normalized string.
    """
    tokens = _word_tokens(name)
    if not tokens:
        return ""
    for phrase in _LOCALITY_PHRASES:
        token = phrase.replace(" ", "_")
        joined = "_".join(tokens)
        joined = (joined.replace(f"_{token}_", "_")
                        .replace(f"_{token}", "")
                        .replace(f"{token}_", ""))
        tokens = joined.split("_")
    tokens = [t for t in tokens if t and t not in _LOCALITY_SINGLE]
    return "_".join(tokens)


def key_name(name):
    """Dedupe key: normalized name with locality tokens stripped."""
    return strip_locality_tokens(name)


def ascii_fold(text):
    """Fold non-ASCII to safe ASCII for KML (₹->Rs, em-dash->-, ×->x)."""
    if text is None:
        return ""
    table = {
        "\u20b9": "Rs ",          # ₹
        "\u2014": "-",            # em dash
        "\u2013": "-",            # en dash
        "\u00d7": "x",            # ×
        "\u2018": "'", "\u2019": "'",   # curly quotes
        "\u201c": '"', "\u201d": '"',
        "\u2026": "...",          # …
        "\u2192": "->",           # →
        "\u2190": "<-",
        "\u00a0": " ",
        "\u20ac": "EUR ", "\u00a3": "GBP ", "\u0024": "$",
    }
    out = []
    for ch in text:
        if ch in table:
            out.append(table[ch])
        elif ord(ch) < 128:
            out.append(ch)
        else:
            out.append("?")
    return "".join(out)


_NUM_RE = re.compile(r"[\d,]+(?:\.\d+)?")


def parse_num(text):
    """Parse an Indian price string to an absolute number (Rs).

    Handles "Rs 1.38-3.40 Cr", "Rs 72L", "1,700", "1.61-6.45 Cr".
    Returns None if no number is present. For ranges returns the FIRST value
    converted to absolute (caller decides how to use).
    """
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    low = s.lower()
    m = _NUM_RE.search(s)
    if not m:
        return None
    val = float(m.group(0).replace(",", ""))
    if "cr" in low:
        val *= 1e7
    elif re.search(r"\dlakh|\dlac|\d\s*l(?![a-z])", low):
        val *= 1e5
    return val


def parse_psf(text):
    """Best-effort numeric per-sqft from a cell ("Rs 9,200 - 9,500/sqft").

    Returns the FIRST numeric value if present (callers treat ranges by
    median/band rules), else None. Never fabricates.
    """
    if text is None:
        return None
    m = _NUM_RE.search(str(text))
    if not m:
        return None
    return float(m.group(0).replace(",", ""))


def parse_coord(text):
    """Parse a lat/lon cell to float, or None."""
    if text is None:
        return None
    try:
        return float(str(text).strip())
    except (TypeError, ValueError):
        return None


def coord_bucket(lat, lon, digits=4):
    """Coordinate bucket key for dedupe (round to 4 dp ~ 11 m)."""
    return (round(lat, digits), round(lon, digits))


def row_score(row):
    """Richer-row score for dedupe: psf>price>url presence."""
    score = 0
    if row.get("psf") not in (None, "", "N/A"):
        score += 4
    if row.get("total") not in (None, "", "N/A"):
        score += 2
    if row.get("source_url"):
        score += 1
    return score


def dedupe_records(records, key_fn=key_name, score_fn=row_score):
    """Dedupe dict records keeping the richest row (first-wins on ties)."""
    best = {}
    for rec in records:
        k = key_fn(rec.get("project") or rec.get("name") or "")
        if not k:
            continue
        cur = best.get(k)
        if cur is None or score_fn(rec) > score_fn(cur):
            best[k] = rec
    return list(best.values())


# Header-synonym map: normalized header -> canonical field. Supports BOTH the
# R&D sheet schema (Project|Type|Launch Price|Current Price (per sq.ft)|...)
# and the belt-run schema (# | Project | Type | Locality | Listing Price |
# Per Sqft | Lat | Lng | Dist km | Maps link | Source URL | Confidence).
_HEADER_SYNONYMS = {
    "project": ["project", "projectname", "name"],
    "type": ["type", "category", "propertytype"],
    "locality": ["locality", "location", "area", "belt"],
    "launch_price": ["launchprice"],
    "psf": ["currentpricepersqft", "persqft", "persqftrate", "psf",
            "pricepersqft", "per sq ft"],
    "total": ["currentsalepricetotal", "listingprice", "totalprice",
              "price", "saleprice"],
    "appreciation": ["appreciation", "appreciationrate"],
    "developer": ["developer", "builder", "developername"],
    "units": ["units", "noofunits", "unitcount"],
    "lat": ["gpslat", "lat", "latitude"],
    "lon": ["gpslon", "lng", "lon", "longitude"],
    "maps_link": ["googlemapslink", "mapslink", "gmaplink", "googlemaplink"],
    "dist_km": ["distkm", "distancekm", "dist"],
    "source_url": ["sourceurl", "source", "listingurl"],
    "confidence": ["confidence"],
    "date": ["date", "listingdate", "updated"],
    "portal": ["portal", "sourceportal", "website"],
    "area": ["area", "areaindicator", "sqftarea"],
    "notes": ["notes", "remarks"],
}


def match_header(raw_header):
    """Map a raw header string to a canonical field name (or None)."""
    if raw_header is None:
        return None
    norm = _NON_ALNUM.sub("", str(raw_header).lower())
    for field, syns in _HEADER_SYNONYMS.items():
        if norm in syns:
            return field
        for s in syns:
            if _NON_ALNUM.sub("", s) == norm:
                return field
    return None


def records_from_rows(rows, header_row=0):
    """Rows (list of lists) -> list of dicts keyed by canonical field.

    Header row is matched via match_header(); unmatched columns are kept
    under their raw header string (normalized) so no data is silently lost.
    """
    if not rows or len(rows) < header_row + 1:
        return []
    headers = rows[header_row]
    mapping = [match_header(h) for h in headers]
    out = []
    for row in rows[header_row + 1:]:
        rec = {}
        for idx, field in enumerate(mapping):
            if idx >= len(row):
                continue
            val = row[idx]
            if val is None or str(val).strip() == "":
                continue
            rec[field] = str(val).strip()
        if rec:
            out.append(rec)
    return out


# ---------------------------------------------------------------------------
# Sheets / Drive service (lazy google imports)
# ---------------------------------------------------------------------------

def _vault_credentials(service_name, email):
    """Fallback auth: vault resolve(email) -> get_token -> Credentials."""
    from tools.gws_vault_client import get_token, resolve  # noqa: WPS433
    uid = resolve("email", email)
    if not uid:
        raise RuntimeError(
            f"vault resolve failed for email {email!r} — no such user")
    raw = get_token(uid, service_name, session_uid=uid)
    if not raw:
        raise RuntimeError(
            f"no vault token for user {uid} service {service_name}")
    from google.oauth2.credentials import Credentials  # noqa: WPS433
    return Credentials.from_authorized_user_info(json.loads(raw))


def get_service(api, version, service_name="google-draas", email=None):
    """Build a googleapiclient service.

    Primary: tools.gws_auth.build_service (sandbox-safe RPC dispatch).
    Fallback: vault resolve(email) + get_token (worked in sessions where
    build_service 403'd on the R&D sheet, Aug-2026).
    """
    try:
        from tools.gws_auth import build_service  # noqa: WPS433
        return build_service(api, version, service_name=service_name)
    except Exception as exc:
        if not email:
            raise RuntimeError(
                f"build_service failed ({exc}); retry with --email to use the "
                "vault-client fallback") from exc
        creds = _vault_credentials(service_name, email)
        from googleapiclient.discovery import build  # noqa: WPS433
        return build(api, version, credentials=creds)


def list_tabs(sheet_id, service_name="google-draas", email=None):
    svc = get_service("sheets", "v4", service_name, email)
    meta = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
    return [s["properties"]["title"] for s in meta.get("sheets", [])]


def read_range(sheet_id, tab, range_="A1:Z1000", service_name="google-draas",
               email=None):
    svc = get_service("sheets", "v4", service_name, email)
    resp = svc.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=f"{tab}!{range_}").execute()
    return resp.get("values", [])


def read_records(sheet_id, tab, range_="A1:Z1000",
                 service_name="google-draas", email=None):
    """Rows of a tab as dicts keyed by canonical field (see match_header)."""
    return records_from_rows(read_range(sheet_id, tab, range_,
                                        service_name, email))


def append_rows(sheet_id, tab, rows, start="A1",
                service_name="google-draas", email=None):
    """Append rows (list of lists) below the last row of the tab.

    Rows given as dicts are converted using the tab's current header row
    (canonical field -> column order).
    """
    svc = get_service("sheets", "v4", service_name, email)
    values = rows
    if rows and isinstance(rows[0], dict):
        existing = read_range(sheet_id, tab, "A1:Z1000",
                              service_name, email)
        mapping = [match_header(h) for h in (existing[0] if existing else [])]
        header_fields = [m for m in mapping if m is not None]
        values = []
        for rec in rows:
            values.append([rec.get(f, "") for f in header_fields])
    body = {"values": values}
    resp = svc.spreadsheets().values().append(
        spreadsheetId=sheet_id, range=f"{tab}!{start}",
        valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS",
        body=body).execute()
    return resp.get("updates", {}).get("updatedRows", 0)


def update_cell(sheet_id, tab, cell, value,
                service_name="google-draas", email=None):
    """Write a single cell (e.g. per-sqft updates by pricing_refresh)."""
    svc = get_service("sheets", "v4", service_name, email)
    body = {"values": [[value]]}
    resp = svc.spreadsheets().values().update(
        spreadsheetId=sheet_id, range=f"{tab}!{cell}",
        valueInputOption="USER_ENTERED", body=body).execute()
    return resp.get("updatedCells", 0)


def get_drive_file_media(file_id, service_name="google-draas", email=None):
    """Download a native Drive file (KML) as bytes."""
    svc = get_service("drive", "v3", service_name, email)
    return svc.files().get_media(fileId=file_id).execute()


def update_drive_file(file_id, content_bytes, service_name="google-draas",
                      email=None):
    """Overwrite a Drive file, keeping the SAME file id (link survives)."""
    svc = get_service("drive", "v3", service_name, email)
    return svc.files().update(fileId=file_id,
                              media_body=content_bytes).execute()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("tabs", help="list tabs")
    t.add_argument("sheet_id")
    t.add_argument("--service", default="google-draas")
    t.add_argument("--email")

    r = sub.add_parser("read", help="read a tab as JSON records")
    r.add_argument("sheet_id")
    r.add_argument("--tab", required=True)
    r.add_argument("--range", default="A1:Z1000")
    r.add_argument("--service", default="google-draas")
    r.add_argument("--email")

    a = sub.add_parser("append", help="append rows from JSON")
    a.add_argument("sheet_id")
    a.add_argument("tab")
    a.add_argument("rows_json")
    a.add_argument("--start", default="A1")
    a.add_argument("--service", default="google-draas")
    a.add_argument("--email")
    return p.parse_args(argv)


def main(argv=None):
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    kw = {"service_name": args.service, "email": args.email}
    if args.cmd == "tabs":
        for t in list_tabs(args.sheet_id, **kw):
            print(t)
    elif args.cmd == "read":
        recs = read_records(args.sheet_id, args.tab, args.range, **kw)
        print(json.dumps(recs, ensure_ascii=False, indent=1))
    elif args.cmd == "append":
        with open(args.rows_json, encoding="utf-8-sig") as f:
            rows = json.load(f)
        n = append_rows(args.sheet_id, args.tab, rows, args.start, **kw)
        print(f"appended {n} rows to {args.tab}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
