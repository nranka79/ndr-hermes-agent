#!/usr/bin/env python3
"""tn_rera_fetch.py — fetch + parse TN RERA registers through the residential tunnel.

Downloads the three ONLINE registers and all OFFLINE year folders from
rera.tn.gov.in, parses the server-rendered tables, filters by the given
district code (default TN/30 = Hosur/Krishnagiri) plus belt keywords, and
writes a deduped JSON of belt projects.

Usage:
  python3 tn_rera_fetch.py [--out DIR] [--district 30] [--include-all]

Requires: the Hermes residential tunnel (hermes-utilities:1000) reachable —
the VPS datacenter IP and fetch proxies are blocked by the site.

Output JSON rows: {"cat": building|layout|regularisation, "year": online|YYYY,
  "row": [S.No, RegNo, Promoter, ProjectDetails, Approval, Completion, Other, Status]}
plus a derived "name" when the details cell carries 'Project Name: "X"'.

Verified 2026-08-12: building online 279 rows, layout online 3,150,
regularisation online 4,369; offline layout 2022/2023 are the big ones
(4,000+ rows each). District code TN/30 = Hosur/Krishnagiri.
"""
import argparse, json, os, re, subprocess, sys
from html.parser import HTMLParser

TUNNEL = "socks5-hostname=hermes-utilities:1000"
BASE = "https://rera.tn.gov.in"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0"

ONLINE = {
    "building": "registered-building/tn",
    "layout": "registered-layout/tn",
    "regularisation": "registered_reglayout",
}
YEARS = list(range(2017, 2026))

# Belt keywords — fallback when the reg-code district doesn't match (e.g.
# Chennai-headquartered promoter building in Hosur registers under TN/01).
DEFAULT_KEYWORDS = ["hosur", "krishnagiri", "denkanikottai", "denkani",
    "kagganur", "kagganoor", "shoolagiri", "sivaganapalli", "seveganapalli",
    "chichuraganapalli", "mathigiri", "veerapandi", "berigai", "bargur",
    "karimangalam", "mookandapalli", "mookondapalli", "sipcot", "thally",
    "kelamangalam", "rayakottai", "zuzuvadi", "sundekuppam", "perandapalli",
    "erragondapalli", "attibele hosur", "bagalur hosur"]


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_td = False; self.in_th = False; self.cur = []
        self.rows = []; self.in_table = False
    def handle_starttag(self, tag, attrs):
        if tag == "table": self.in_table = True
        if tag == "td" and self.in_table: self.in_td = True; self.cur.append("")
        if tag == "th" and self.in_table: self.in_th = True; self.cur.append("")
    def handle_data(self, data):
        if self.in_td and self.cur: self.cur[-1] += data
        elif self.in_th and self.cur: self.cur[-1] += data
    def handle_endtag(self, tag):
        if tag == "td": self.in_td = False
        if tag == "th": self.in_th = False; self.cur = []
        if tag == "tr" and self.cur:
            self.rows.append([" ".join(c.split()) for c in self.cur])
            self.cur = []
        if tag == "table": self.in_table = False


def fetch(url, out_path):
    r = subprocess.run(["curl", "-sL", "--max-time", "60", "--" + TUNNEL, url,
                        "-H", f"User-Agent: {UA}", "-o", out_path],
                       capture_output=True, text=True, timeout=90)
    return os.path.getsize(out_path) if os.path.exists(out_path) else 0


def parse(path):
    p = TableParser()
    with open(path, encoding="utf-8", errors="replace") as f:
        p.feed(f.read())
    return p.rows


def reg_code(row):
    j = " ".join(row).lower()
    m = re.search(r"tn(?:rera)?/(\d+)/(?:building|layout|regularisation|blg|lo)", j)
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/opt/data/tnrera")
    ap.add_argument("--district", default="30")
    ap.add_argument("--include-all", action="store_true",
                    help="emit ALL rows, not just belt matches")
    ap.add_argument("--keywords", nargs="*", default=DEFAULT_KEYWORDS)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    out = []

    # Online registers
    for cat, slug in ONLINE.items():
        path = os.path.join(args.out, f"online_{cat}.html")
        size = fetch(f"{BASE}/{slug}", path)
        rows = parse(path)
        for r in rows:
            j = " ".join(r).lower()
            if args.include_all or reg_code(r) == args.district or any(k in j for k in args.keywords):
                m = re.search(r"Project Name:\s*[\"'\u201c\u201d]?([^\"'\u201d]+)", j)
                out.append({"cat": cat, "year": "online",
                            "name": m.group(1).strip() if m else "",
                            "row": r})
        print(f"online {cat}: {len(rows)} rows")

    # Offline year folders
    for cat in ("building", "layout", "regularisation"):
        for yr in YEARS:
            path = os.path.join(args.out, f"{cat}_{yr}.html")
            size = fetch(f"{BASE}/{cat}/offline/{yr}", path)
            rows = parse(path)
            for r in rows:
                j = " ".join(r).lower()
                if args.include_all or reg_code(r) == args.district or any(k in j for k in args.keywords):
                    m = re.search(r"Project Name:\s*[\"'\u201c\u201d]?([^\"'\u201d]+)", j)
                    out.append({"cat": cat, "year": str(yr),
                                "name": m.group(1).strip() if m else "",
                                "row": r})
            print(f"offline {cat}/{yr}: {len(rows)} rows")

    # Dedupe by normalized reg number
    seen, deduped = set(), []
    for e in out:
        key = re.sub(r"\s+", "", e["row"][1].lower()) if len(e["row"]) > 1 else ""
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(e)

    with open(os.path.join(args.out, "tn_rera_belt_projects.json"), "w") as f:
        json.dump(deduped, f, indent=1)
    print(f"TOTAL unique belt projects: {len(deduped)}")


if __name__ == "__main__":
    main()
