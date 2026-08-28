#!/usr/bin/env python3
"""Retry missing K-RERA plan downloads, skipping files already on disk.

Same endpoint contract as krera_download_plans.py (GET /home -> session
cookie, POST /projectViewDetails per district, POST /projectDetails with
action=<detail_id>, download /download_jc?DOC_ID=... links) but:
  - skips any dest file that exists with size > 0 (resumable across
    tunnel drops / node flaps),
  - retries each download up to 3x with 4-8s jittered backoff,
  - prints SKIP/OK/FAIL per doc + final tally.

Run through the tunnel when the VPS datacenter IP is blocked:
  HTTPS_PROXY=socks5h://hermes-utilities:1000 HTTP_PROXY=socks5h://hermes-utilities:1000 \
    python3 krera_retry_missing.py
Requires PySocks for the SOCKS route:
  uv pip install --python /opt/hermes/.venv/bin/python PySocks

Edit PROJ_SPEC / OUT at the top for other projects. Exit codes:
  0 = all requested docs present (ok or skip, zero fail)
  2 = some downloads failed
  3 = site unreachable (caller may retry later)
"""
import json, os, random, re, sys, time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://rera.karnataka.gov.in"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
DISTRICTS = ["Bengaluru Urban", "Bengaluru  Rural"]
OUT = "/opt/data/rera_rowvilla_plans/out"
PROJ_SPEC = {"name": "The Roots", "rera": "PRM/KA/RERA/1250/303/PR/090925/008075", "promoter": "SRK Infra Projects / Svam Realty"}

DOC_PLAN_PATTERNS = [
    ("elevation", re.compile(r"elevation", re.I)),
    ("section", re.compile(r"section", re.I)),
    ("site_plan", re.compile(r"site\s*plan|site\s*layout|layout\s*plan", re.I)),
    ("approval_plan", re.compile(r"approval|approved", re.I)),
    ("plan", re.compile(r"plan|drawing|architectural", re.I)),
]


def safe_name(s):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", s).strip("_")[:80]


def classify_doc(text):
    for kind, pat in DOC_PLAN_PATTERNS:
        if pat.search(text):
            return kind
    return "other"


def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    return s


def fetch_index(session, district):
    r = session.post(f"{BASE_URL}/projectViewDetails", data={"district": district}, timeout=180)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", id="approvedTable")
    if table is None or table.find("tbody") is None:
        return []
    rows = []
    for tr in table.find("tbody").find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        cells, detail_id = {}, None
        for td in tds:
            a = td.find("a", title="View Project Details")
            if a and a.get("id"):
                detail_id = a["id"]
            cells.setdefault(len(cells), td.get_text(strip=True))
        rows.append({
            "ack_no": cells.get(1, ""),
            "rera_id": cells.get(2, ""),
            "promoter_name": cells.get(4, ""),
            "project_name": cells.get(5, ""),
            "status": cells.get(6, ""),
            "district": cells.get(7, ""),
            "taluk": cells.get(8, ""),
            "project_type": cells.get(9, ""),
            "detail_id": detail_id,
        })
    return rows


def find_project(rows, spec):
    rera = (spec.get("rera") or "").upper()
    if rera:
        exact = [r for r in rows if r["rera_id"].upper() == rera]
        if exact:
            return exact
    name_tokens = [t for t in re.split(r"\W+", spec.get("name", "").lower()) if t]
    scored = []
    for r in rows:
        rn = r["project_name"].lower()
        toks = [t for t in re.split(r"\W+", rn) if t]
        score = sum(1 for t in name_tokens if t in toks)
        if score:
            scored.append((score, r))
    scored.sort(key=lambda x: -x[0])
    return [r for _, r in scored]


def fetch_detail(session, detail_id):
    r = session.post(f"{BASE_URL}/projectDetails", data={"action": detail_id}, timeout=180)
    r.raise_for_status()
    return r.text


def extract_documents(soup):
    docs = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "download_jc" in href or "DOC_ID" in href.upper():
            url = href if href.startswith("http") else f"{BASE_URL}{href}"
            docs.append({"text": a.get_text(strip=True) or "download_jc", "url": url})
    return docs


def download(session, url, dest, retries=3):
    last = None
    for attempt in range(retries):
        try:
            with session.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1 << 16):
                        f.write(chunk)
            return os.path.getsize(dest)
        except Exception as e:
            last = e
            time.sleep(random.uniform(4, 8))
    raise last


def main():
    session = get_session()
    try:
        r = session.get(f"{BASE_URL}/home", timeout=60)
        r.raise_for_status()
    except Exception as e:
        print("SITE_DOWN", e)
        return 3

    index_cache = {}
    for dist in DISTRICTS:
        try:
            index_cache[dist] = fetch_index(session, dist)
            time.sleep(random.uniform(2.5, 4.5))
        except Exception as e:
            index_cache[dist] = []
            print("index fail", dist, e)

    cands = []
    for dist in DISTRICTS:
        cands += find_project(index_cache.get(dist, []), PROJ_SPEC)
    if not cands:
        print("NO MATCH")
        return 2

    best = cands[0]
    for c in cands:
        if c["rera_id"].upper() == PROJ_SPEC["rera"].upper():
            best = c
            break
    print("matched:", best["project_name"], "|", best["rera_id"], "| detail_id", best["detail_id"])

    html = fetch_detail(session, best["detail_id"])
    soup = BeautifulSoup(html, "html.parser")
    docs = extract_documents(soup)
    print("total docs on page:", len(docs))

    proj_dir = os.path.join(OUT, "The_Roots")
    plans_dir = os.path.join(proj_dir, "plans")
    docs_dir = os.path.join(proj_dir, "docs")
    os.makedirs(plans_dir, exist_ok=True)
    os.makedirs(docs_dir, exist_ok=True)

    seen = set()
    n_ok = n_skip = n_fail = 0
    for i, d in enumerate(docs):
        kind = classify_doc(d["text"])
        base = safe_name(d["text"][:60]) or f"doc_{i}"
        fname = f"{i:02d}_{base}.pdf"
        if fname in seen:
            fname = f"{i:02d}_{base}_{int(time.time())}.pdf"
        seen.add(fname)
        dest = os.path.join(plans_dir if kind != "other" else docs_dir, fname)
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            n_skip += 1
            print(f"SKIP {kind:14s} {os.path.getsize(dest):>8d} B  {d['text'][:60]}")
            continue
        try:
            nbytes = download(session, d["url"], dest)
            n_ok += 1
            print(f"OK   {kind:14s} {nbytes:>8d} B  {d['text'][:60]}", flush=True)
            time.sleep(random.uniform(1.5, 3.0))
        except Exception as e:
            n_fail += 1
            print(f"FAIL {kind:14s} {d['text'][:60]} -> {e}", flush=True)
            time.sleep(random.uniform(5, 10))

    print(f"\nDONE: ok={n_ok} skip={n_skip} fail={n_fail}")
    return 0 if n_fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
