#!/usr/bin/env python3
"""Enumerate the files of a DRAAS project that are NOT owned by ndr@draas.com.

Produces the read-only work list for a bulk ownership-consolidation sweep
("take ownership of every <project> file owned by anyone else"). Touch nothing.

Usage (MUST run via terminal, not execute_code — the vault socket is not
available inside execute_code):

    cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 \
      <this script> --keyword Amber [--service google-draas] [--out /opt/data]

Outputs on stdout:
  * a whole-account owner histogram (sharedWithMe minus own-owned) — context only
  * the project corpus: every descendant of folders whose NAME matches the
    keyword, plus loose files matching the keyword anywhere
  * a per-SOURCE-FOLDER table: owner mix + proposed destination bucket
  * totals split internal (@draas.com & friends) vs external (cannot be
    DWD-transferred — see references/drive-ownership-consolidation.md)

Writes <out>/<keyword>_corpus.json and <out>/<keyword>_plan.csv.

Design notes learned the hard way (2026-10-05):
  * Seed folders carry `_root` = seed NAME, not seed ID. Seeding the BFS with
    the id makes every top-level child print as "1fKJi6v1uoUPs-..." in the plan.
  * Classify by SOURCE FOLDER first, filename second. A filename-only regex
    misroutes whole classes (RERA sets and render PNGs land in Misc).
  * Report counts BEFORE mutating; the externally-owned slice is the part the
    user did not anticipate and needs a decision, not an action.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "/opt/hermes")

ME = "ndr@draas.com"
FOLDER = "application/vnd.google-apps.folder"
INTERNAL_SUFFIXES = ("@draas.com", "@drahomes.in", "@ahfl.in", "@o3infotech.com")

FIELDS = ("nextPageToken, files(id,name,mimeType,size,modifiedTime,createdTime,"
          "owners(emailAddress,displayName),parents,webViewLink,"
          "capabilities(canEdit,canShare))")

# Ranka Amber canonical buckets. Re-resolve for another project instead of
# trusting these ids — query '<project folder>' in parents.
CANON = {
    "1A3Foefaxfs39rzNPQOIxRNR8zTybXxPo": "Architectural and Engineering",
    "19xb8_3IXmKvUo8wXFFhPXr5q8ok_IpyW": "Banking and Finance",
    "1cgXfVqjykxWE5FmQbIQFaaZgwUF8POj5": "Communication",
    "1_RDP-7hLj3DmXgdXfD5ue5ZhYRq_X_BV": "Misc",
    "1B0zA0iybCjI3wNeVU9LI8ALWyC5Yk74G": "Customer",
    "1lNIemJ10KuGXrDQJLQZ-jOOMBfK5hCvr": "Marketing and Content",
    "1jOQzLjRAhy761CUU8aobTtDdmYqLyROm": "Legal Notices",
    "1oBDneKVz7wpC0IheGIE0rW9LNWrHXcHo": "Approvals",
    "1IK0xUcNOGUJ0XlW3K6rcpgu-qzadeVxl": "Title",
}

# Filename fallback ONLY — weaker than the source folder. Order matters.
BUCKETS = [
    ("Approvals", r"sanction|approv|licen[cs]e|commencement|plinth|bpas|bbmp|gba|"
                  r"bescom|labour cess|eodb|bmtf|rera|form ?[456]|quarterly|qpr"),
    ("Title", r"\bJDA\b|\bSSA\b|sharing agreement|sale deed|title|katha|khata|"
              r"\bEC\b|encumbrance|\bGPA\b|\bSPA\b|mutation|joint development"),
    ("Banking and Finance", r"cost ?sheet|cash ?flow|\bAPF\b|ICICI|means of finance|"
                            r"financ|invest|\bIRR\b|budget|estimate|\bBOQ\b|loan|fund"),
    ("Customer", r"customer|unit.?wise|allot|agreement to sell|buyer|charge"),
    ("Legal Notices", r"notice|police|legal|court|advocate|opinion"),
    ("Marketing and Content", r"brochure|render|marketing|collateral|spec|inventory|"
                              r"presentation|teaser|logo"),
    ("Architectural and Engineering", r"dwg|drawing|plan|GFC|floor|elevation|section|"
                                      r"structur|MEP|working|area statement|design|"
                                      r"basement|column|layout|checklist"),
    ("Communication", r"letter|email|minute|communicat|correspond"),
]


def bucket_from_name(name: str) -> str:
    for label, pat in BUCKETS:
        if re.search(pat, name, re.I):
            return label
    return "Misc"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", required=True, help="project name fragment, e.g. Amber")
    ap.add_argument("--service", default="google-draas")
    ap.add_argument("--out", default="/opt/data")
    args = ap.parse_args()
    kw = args.keyword
    pat = re.compile(kw, re.I)

    from tools.gws_auth import build_service
    drv = build_service("drive", "v3", service_name=args.service)

    def ls(**kwarg):
        out, tok = [], None
        while True:
            kw2 = dict(q=kwarg.pop("q"), fields=FIELDS, pageSize=1000)
            kw2.update(kwarg)
            r = drv.files().list(pageToken=tok, **kw2).execute()
            out.extend(r.get("files", []))
            tok = r.get("nextPageToken")
            if not tok:
                break
        return out

    def owner(f):
        return (f.get("owners") or [{}])[0].get("emailAddress", "?")

    # --- 1. whole-account context -------------------------------------------
    shared = ls(q="sharedWithMe and trashed=false")
    shared = [f for f in shared if ME not in [o.get("emailAddress") for o in f.get("owners", [])]]
    print(f"=== shared with {ME} but owned by someone else: {len(shared)} items ===")
    for e, n in Counter(owner(f) for f in shared).most_common(15):
        print(f"  {n:5d}  {e}")

    # --- 2. project corpus --------------------------------------------------
    seeds = [f for f in ls(q=f"mimeType='{FOLDER}' and name contains '{kw}' and trashed=false")
             if pat.search(f["name"])]
    seedname = {s["id"]: s["name"] for s in seeds}
    print(f"\n=== seed folders matching {kw!r}: {len(seeds)} ===")
    for s in sorted(seeds, key=lambda x: x["name"]):
        print(f"   {s['name']!r}  owner={owner(s)}")

    seen, corpus = set(seedname), []
    queue = [(s["id"], s["name"], s["name"]) for s in seeds]   # root = NAME, not id
    while queue:
        fid, fname, root = queue.pop(0)
        for k in ls(q=f"'{fid}' in parents and trashed=false"):
            if k["id"] in seen:
                continue
            seen.add(k["id"])
            k["_root"], k["_parent"] = root, fname
            corpus.append(k)
            if k["mimeType"] == FOLDER:
                queue.append((k["id"], k["name"], root))

    loose = [f for f in ls(q=f"name contains '{kw}' and trashed=false") if pat.search(f["name"])]
    loose = [f for f in loose if ME not in [o.get("emailAddress") for o in f.get("owners", [])]]

    items = {}
    for f in corpus + loose:
        if f["id"] in items:
            continue
        if owner(f) == ME or f["mimeType"] == FOLDER:
            continue
        items[f["id"]] = f
    items = list(items.values())
    print(f"\ncorpus={len(corpus)}  loose={len(loose)}  "
          f"UNIQUE non-folder not-owned-by-me = {len(items)}")

    # --- 3. plan ------------------------------------------------------------
    rows = []
    for f in items:
        par = (f.get("parents") or [""])[0]
        already = CANON.get(par, "")
        rows.append({
            "source_folder": f.get("_root") or "(loose)",
            "file_id": f["id"], "name": f["name"], "owner": owner(f),
            "internal": owner(f).endswith(INTERNAL_SUFFIXES),
            "already_in": already,
            "proposed_bucket": already or bucket_from_name(f["name"]),
            "mime": f["mimeType"], "size": f.get("size"), "link": f.get("webViewLink"),
        })

    byroot = defaultdict(list)
    for r in rows:
        byroot[r["source_folder"]].append(r)
    print("\n=== SOURCE FOLDER -> DESTINATION ===")
    for root, rs in sorted(byroot.items(), key=lambda kv: -len(kv[1])):
        placed = sum(1 for r in rs if r["already_in"])
        print(f"\n{root}   [{len(rs)} files; {placed} already in a canonical bucket]")
        print("   owners :", dict(Counter(r["owner"] for r in rs)))
        print("   target :", dict(Counter(r["proposed_bucket"] for r in rs)))

    conv = re.compile(r"^\d{8}[-_]")
    internal = [r for r in rows if r["internal"]]
    print("\n=== TOTALS ===")
    print(f"files={len(rows)}  internal={len(internal)}  "
          f"external(CANNOT DWD-transfer)={len(rows) - len(internal)}")
    print("external owners:", dict(Counter(r["owner"] for r in rows if not r["internal"])))
    print(f"need MOVE={sum(1 for r in rows if not r['already_in'])}  "
          f"already placed (ownership only)={sum(1 for r in rows if r['already_in'])}")
    print(f"filenames violating YYYYMMDD_ convention: "
          f"{sum(1 for r in rows if not conv.match(r['name']))}")

    json.dump({"keyword": kw, "seeds": seeds, "corpus": corpus, "loose": loose},
              open(f"{args.out}/{kw}_corpus.json", "w"), indent=1)
    with open(f"{args.out}/{kw}_plan.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n-> {args.out}/{kw}_corpus.json\n-> {args.out}/{kw}_plan.csv")
    print("\nNEXT: report these counts and get the go-ahead BEFORE any transfer/move.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
