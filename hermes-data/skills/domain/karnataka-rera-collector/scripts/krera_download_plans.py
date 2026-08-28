#!/usr/bin/env python3
"""
K-RERA row-villa plan document downloader.

Finds a set of Bangalore projects on the Karnataka RERA site, fetches each
project's detail page, extracts the uploaded documents (approval plan, site
plan, section, elevation plan, etc.) and downloads every plan PDF into an
output directory.

Built/verified live 2026-08-11 (see karnataka-rera-collector SKILL.md
"Plan-document downloads"). Endpoint contract in
references/kanarera-endpoints.md.

Exit codes:
  0  = success (all matched projects processed, plans downloaded)
  2  = hard failure (network/parse error that is NOT site-down)
  3  = site is down / unreachable (caller may retry later)
"""
import argparse, json, os, random, re, sys, time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://rera.karnataka.gov.in"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
DISTRICTS = ["Bengaluru Urban", "Bengaluru  Rural"]
SITE_DOWN_MARKER = "SITE_DOWN"

# Worked example: recent Bangalore row-villa / row-house projects.
# RERA number optional -- name matching covers projects aggregators don't
# publish numbers for (Sattva La Vita, Ashish ANR Row House).
DEFAULT_PROJECTS = [
    {"name": "Sattva Springs", "rera": "PRM/KA/RERA/1251/310/PR/240724/006948", "promoter": "Sattva"},
    {"name": "Assetz Earth & Essence", "rera": "PRM/KA/RERA/1251/309/PR/180621/001907", "promoter": "Assetz"},
    {"name": "Prestige Park Grove", "rera": "PRM/KA/RERA/1251/446/PR/100823/006141", "promoter": "Prestige"},
    {"name": "Sattva La Vita", "rera": "", "promoter": "Sattva"},
    {"name": "Ashish ANR Row House", "rera": "", "promoter": ""},
]

DOC_PLAN_PATTERNS = [
    ("elevation", re.compile(r"elevation", re.I)),
    ("section", re.compile(r"section", re.I)),
    ("site_plan", re.compile(r"site\s*plan|site\s*layout|layout\s*plan", re.I)),
    ("approval_plan", re.compile(r"approval|approved", re.I)),
    ("plan", re.compile(r"plan|drawing|architectural", re.I)),
]


def site_up(session):
    try:
        r = session.get(f"{BASE_URL}/home", timeout=30)
        return r.status_code == 200
    except Exception:
        return False


def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    return s


def fetch_index(session, district):
    """POST /projectViewDetails -> rows [{project_name, rera_id, ack_no,
    promoter_name, taluk, status, detail_id}]."""
    r = session.post(f"{BASE_URL}/projectViewDetails", data={"district": district}, timeout=180)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", id="approvedTable")
    if table is None or table.find("tbody") is None:
        return []
    headers = [th.get_text(strip=True).lower() for th in table.find("thead").find_all("th")]
    rows = []
    for tr in table.find("tbody").find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        cells, detail_id = {}, None
        for h, td in zip(headers, tds):
            a = td.find("a", id=True)
            if a is not None and str(a.get("id", "")).isdigit():
                detail_id = a["id"]
            cells[h] = td.get_text(" ", strip=True)
        rera_id = cells.get("registration no", "") or cells.get("acknowledgement no", "")
        if not rera_id:
            continue
        rows.append({
            "project_name": cells.get("project name", ""),
            "rera_id": rera_id,
            "promoter_name": cells.get("promoter name", ""),
            "taluk": cells.get("taluk", ""),
            "status": cells.get("status", ""),
            "project_type": cells.get("project type", ""),
            "detail_id": detail_id,
            "district": district,
        })
    return rows


def find_project(rows, spec):
    """Best-effort match of a project spec against index rows. Returns list
    of candidate rows (already ranked) -- caller decides."""
    cands = []
    name = (spec.get("name") or "").strip().lower()
    rera = (spec.get("rera") or "").strip().upper()
    for row in rows:
        rn = (row.get("project_name") or "").lower()
        rr = (row.get("rera_id") or "").upper()
        score = 0
        if rera and rr and rera in rr:
            score = 100
        elif name and (name in rn or rn in name):
            score = 60
        elif name:
            tokens = [t for t in name.split() if len(t) > 2]
            if tokens and all(t in rn for t in tokens):
                score = 80
        if score:
            cands.append((score, row))
    cands.sort(key=lambda x: -x[0])
    return [r for _, r in cands]


def fetch_detail(session, detail_id):
    r = session.post(
        f"{BASE_URL}/projectDetails",
        data={"action": detail_id},
        headers={"Referer": f"{BASE_URL}/viewAllProjects", "X-Requested-With": "XMLHttpRequest"},
        timeout=120,
    )
    r.raise_for_status()
    return r.text


def extract_documents(soup):
    docs, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if "download_jc" in href or "DOC_ID" in href.lower() or "upload" in href.lower():
            url = href if href.startswith("http") else BASE_URL + ("" if href.startswith("/") else "/") + href
            text = a.get_text(" ", strip=True) or os.path.basename(url)
            if url in seen:
                continue
            seen.add(url)
            docs.append({"text": text, "url": url})
    return docs


def classify_doc(text):
    t = text.lower()
    for kind, pat in DOC_PLAN_PATTERNS:
        if pat.search(t):
            return kind
    return "other"


def safe_name(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")


def download(session, url, path):
    r = session.get(url, stream=True, timeout=120)
    r.raise_for_status()
    n = 0
    with open(path, "wb") as f:
        for chunk in r.iter_content(65536):
            f.write(chunk)
            n += len(chunk)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/opt/data/rera_rowvilla_plans")
    ap.add_argument("--projects-json", default=None, help="JSON array of {name,rera,promoter}")
    ap.add_argument("--no-wait", action="store_true", help="exit 3 immediately if site down")
    args = ap.parse_args()

    projects = DEFAULT_PROJECTS
    if args.projects_json:
        with open(args.projects_json) as f:
            projects = json.load(f)

    out = args.out
    os.makedirs(out, exist_ok=True)

    session = get_session()
    if not site_up(session):
        print(SITE_DOWN_MARKER, flush=True)
        return 3

    report = {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"), "projects": []}
    index_cache = {}
    all_ok = True

    for spec in projects:
        entry = {
            "name": spec.get("name"),
            "rera_spec": spec.get("rera", ""),
            "matches": [],
            "documents": [],
            "plans_downloaded": [],
            "error": None,
        }
        proj_dir = os.path.join(out, safe_name(spec.get("name", "project")))
        plans_dir = os.path.join(proj_dir, "plans")
        docs_dir = os.path.join(proj_dir, "docs")
        try:
            cands = []
            for dist in DISTRICTS:
                if dist not in index_cache:
                    try:
                        index_cache[dist] = fetch_index(session, dist)
                        time.sleep(random.uniform(2.5, 4.5))
                    except Exception as e:
                        index_cache[dist] = []
                        entry["error"] = f"index fetch failed for {dist}: {e}"
                cands += find_project(index_cache[dist], spec)

            if not cands:
                entry["error"] = "no match found in RERA index"
                report["projects"].append(entry)
                all_ok = False
                continue

            # prefer exact RERA-number matches, else first name match
            best = cands[0]
            for c in cands:
                if spec.get("rera") and c.get("rera_id", "").upper() == spec["rera"].upper():
                    best = c
                    break
            entry["matches"] = [{
                "project_name": c["project_name"], "rera_id": c["rera_id"],
                "promoter_name": c["promoter_name"], "taluk": c["taluk"],
                "status": c["status"], "project_type": c["project_type"],
                "detail_id": c["detail_id"], "district": c["district"],
            } for c in cands[:6]]

            html = fetch_detail(session, best["detail_id"])
            time.sleep(random.uniform(2.5, 4.5))
            soup = BeautifulSoup(html, "html.parser")
            docs = extract_documents(soup)
            if not docs:
                entry["error"] = "detail page fetched but no download links found"
                report["projects"].append(entry)
                all_ok = False
                continue

            os.makedirs(plans_dir, exist_ok=True)
            os.makedirs(docs_dir, exist_ok=True)
            downloaded = []
            seen_files = set()
            for i, d in enumerate(docs):
                kind = classify_doc(d["text"])
                base = safe_name(d["text"][:60]) or f"doc_{i}"
                fname = f"{i:02d}_{base}.pdf"
                fname = fname if fname not in seen_files else f"{i:02d}_{base}_{int(time.time())}.pdf"
                seen_files.add(fname)
                dest = os.path.join(plans_dir if kind != "other" else docs_dir, fname)
                try:
                    nbytes = download(session, d["url"], dest)
                    rec = {"doc_text": d["text"], "url": d["url"], "kind": kind, "file": dest, "bytes": nbytes}
                    entry["documents"].append(rec)
                    if kind != "other":
                        entry["plans_downloaded"].append(rec)
                    downloaded.append(rec)
                    print(f"OK {spec['name']}: {kind:14s} {nbytes:>8d} B  {d['text'][:70]}", flush=True)
                    time.sleep(random.uniform(1.5, 3.0))
                except Exception as e:
                    entry["error"] = f"download failed for {d['text']}: {e}"
                    print(f"FAIL {spec['name']}: {d['text'][:60]} -> {e}", flush=True)
            if not downloaded:
                all_ok = False
        except Exception as e:
            entry["error"] = f"unexpected: {e}"
            all_ok = False
        report["projects"].append(entry)

    with open(os.path.join(out, "report.json"), "w") as f:
        json.dump(report, f, indent=2, default=str)
    print("REPORT:", os.path.join(out, "report.json"), flush=True)
    return 0 if all_ok else 2


if __name__ == "__main__":
    sys.exit(main())
