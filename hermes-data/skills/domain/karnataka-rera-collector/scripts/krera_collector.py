#!/usr/bin/env python3
"""K-RERA (Karnataka RERA) comparable-project collector.

BUILD STATUS (see honest-answer-no-not-cheeky-star.md plan, Build order):
  Step 1 -- Tier-1 INDEX SYNC -- DONE, verified live (Bengaluru Urban 4,359
    rows, Bengaluru  Rural, idempotent re-sync on both).
  Step 2 -- Tier-2 DETAIL ENRICHMENT -- DONE, parse logic verified against
    2 fixture templates + 5 real live fetches (see SKILL.md).
  Step 3 -- Bengaluru  Rural sync, `query` interface + staleness flag,
    retry/backoff/hard-fail, 30-min job ceiling with truncation -- DONE,
    see SKILL.md Verification for what was actually exercised live.
  NOT built: `property-rd` wiring, `locality` field (no structured source
  found anywhere on the site -- always blank, by design, not a gap to
  "finish" without a separate gazetteer).

Source: rera.karnataka.gov.in public statutory project register.
robots.txt does not exist (404) -- no disallow rules. Compliant regardless:
single worker, one request at a time, honest UA with a contact URL, no
captcha solving, no proxying/IP rotation, no concealment of automated
origin. If the site blocks us despite compliant behaviour, the job fails
and reports -- no workaround is attempted (see hard-fail below).

Endpoints (confirmed live 2026-08-04 -- see references/kanarera-endpoints.md):
  GET  /home                    -> establishes JSESSIONID
  POST /projectViewDetails      -> district=<name> returns the FULL bulk
                                    project table for that district (no
                                    pagination hit for Bengaluru Urban/Rural)
  POST /projectDetails          -> action=<numeric id> returns one
                                    project's full detail page (Tier-2)

CLI:
  python3 krera_collector.py start --task index --district "Bengaluru Urban" [--db PATH]
  python3 krera_collector.py start --task enrich --limit 5 [--db PATH]
  python3 krera_collector.py check_job <job_id> [--db PATH]
  python3 krera_collector.py query [--locality S] [--taluk S] [--district S]
      [--survey-no S] [--limit N] [--db PATH]
  python3 krera_collector.py _run_worker <job_id> [--db PATH]   # internal; spawned by start

`start` returns a job_id immediately and forks a detached worker process --
the caller never blocks on collection. NOTE: `--db` is a parent-parser
option and must come BEFORE the subcommand (`krera_collector.py --db X
start ...`), not after -- see Pitfalls in SKILL.md.

Testing the retry/backoff path against a mock server instead of the real
site: set env var KRERA_BASE_URL (see references/kanarera-endpoints.md /
SKILL.md Verification for the mock-server session that proved this).
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
import sqlite3
import time
import uuid
from datetime import datetime, timedelta, timezone

import requests

# beautifulsoup4 is NOT in hermes-agent's core pyproject.toml deps (by that
# file's own "scope rule": only packages every session needs belong there,
# skill-specific deps get lazy-installed) -- self-contained lazy import here
# rather than coupling this standalone script to tools/lazy_deps.py's
# LAZY_DEPS allowlist (which assumes an in-process caller, not a
# subprocess-invoked skill script). One-time install into the active venv
# on first run if missing; every run after that just imports normally.
# Two install paths tried in order: plain `pip` (works most places, e.g.
# local dev), then `uv pip install --python <this interpreter>` (the
# hermes-agent production venvs are uv-managed with NO pip module at all --
# confirmed live on the Hetzner deploy, `python3 -m pip` fails there with
# "No module named pip").
try:
    from bs4 import BeautifulSoup
except ImportError:
    import shutil as _shutil
    import subprocess as _subprocess
    try:
        _subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "beautifulsoup4==4.14.3"]
        )
    except (_subprocess.CalledProcessError, FileNotFoundError):
        if _shutil.which("uv") is None:
            raise
        _subprocess.check_call(
            ["uv", "pip", "install", "--python", sys.executable, "-q",
             "beautifulsoup4==4.14.3"]
        )
    from bs4 import BeautifulSoup

BASE_URL = os.environ.get("KRERA_BASE_URL", "https://rera.karnataka.gov.in")
USER_AGENT = (
    "HermesPropertyRD-KRERACollector/0.1 "
    "(+https://github.com/nranka79/ndr-hermes-agent; single-worker, "
    "throttled, public-statutory-data-only)"
)
REQUEST_TIMEOUT = 30  # seconds, per-request ceiling
MIN_DELAY, MAX_DELAY = 3.0, 5.0  # jittered politeness delay before each request
MAX_CONSECUTIVE_ERRORS = 5  # hard-fail the job after this many in a row
JOB_CEILING_SECONDS = 30 * 60  # enrich loop stops early past this, reports truncated

DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "krera.db")

# Index-tier columns -- written/refreshed by task=index, never touched by
# task=enrich (see _upsert_project vs _upsert_enrichment).
_INDEX_COLUMNS = [
    "rera_id", "ack_no", "project_name", "promoter_name", "project_type",
    "district", "taluk", "status", "registration_date",
    "proposed_completion", "extended_completion", "detail_id",
    "source_url", "fetched_at",
]

# Tier-2 columns -- written/refreshed by task=enrich, never touched by
# task=index (see _upsert_project vs _upsert_enrichment). `locality` is
# always '' -- no structured locality field exists anywhere on the detail
# page (only free-text addresses); a real extraction needs a Bengaluru-wide
# locality gazetteer, out of scope here. Don't fabricate it.
_TIER2_COLUMNS = [
    "survey_numbers", "total_land_area", "total_units", "unit_breakdown",
    "last_qpr_date", "completion_pct", "approved_plan_url", "locality",
]


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            task TEXT NOT NULL,
            params TEXT NOT NULL,
            status TEXT NOT NULL,
            n_fetched INTEGER DEFAULT 0,
            truncated INTEGER DEFAULT 0,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )"""
    )
    # Migration: `truncated` was added in Build order step 3 -- existing
    # jobs.db files created by step 1/2 pilots won't have the column yet
    # and CREATE TABLE IF NOT EXISTS does not retrofit columns.
    cols = {row[1] for row in conn.execute("PRAGMA table_info(jobs)")}
    if "truncated" not in cols:
        conn.execute("ALTER TABLE jobs ADD COLUMN truncated INTEGER DEFAULT 0")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS projects (
            rera_id TEXT PRIMARY KEY,
            ack_no TEXT,
            project_name TEXT,
            promoter_name TEXT,
            project_type TEXT,
            district TEXT,
            taluk TEXT,
            locality TEXT,
            survey_numbers TEXT,
            total_land_area TEXT,
            total_units TEXT,
            unit_breakdown TEXT,
            registration_date TEXT,
            proposed_completion TEXT,
            extended_completion TEXT,
            last_qpr_date TEXT,
            completion_pct TEXT,
            approved_plan_url TEXT,
            source_url TEXT,
            fetched_at TEXT,
            status TEXT,
            detail_id TEXT,
            enriched INTEGER DEFAULT 0
        )"""
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Networking -- shared retry/backoff/hard-fail wrapper
# ---------------------------------------------------------------------------

class HardFail(Exception):
    """Raised after MAX_CONSECUTIVE_ERRORS in a row -- the job fails and
    reports; no workaround (proxy rotation, captcha solving, etc.) is ever
    attempted, per the collector's constraints."""


def _backoff_delay(attempt, retry_after_header):
    if retry_after_header:
        try:
            return float(retry_after_header)
        except (TypeError, ValueError):
            pass
    return min(2 ** attempt, 60) + random.uniform(0, 1)


def _request_with_backoff(session, method, url, error_state, **kwargs):
    """error_state = {"consecutive": int}, shared across an entire job so
    the 5-in-a-row hard-fail counts errors job-wide, not per-call. Retries
    on 429/5xx and connection-level errors; honours Retry-After; any other
    4xx is a real failure (no retry -- e.g. a genuine 404 shouldn't spin)."""
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    while True:
        try:
            resp = session.request(method, url, **kwargs)
        except requests.exceptions.RequestException as exc:
            error_state["consecutive"] += 1
            if error_state["consecutive"] >= MAX_CONSECUTIVE_ERRORS:
                raise HardFail(
                    f"{error_state['consecutive']} consecutive request errors, last: {exc}"
                ) from exc
            time.sleep(_backoff_delay(error_state["consecutive"], None))
            continue

        if resp.status_code == 429 or 500 <= resp.status_code < 600:
            error_state["consecutive"] += 1
            if error_state["consecutive"] >= MAX_CONSECUTIVE_ERRORS:
                raise HardFail(
                    f"{error_state['consecutive']} consecutive HTTP errors, "
                    f"last: {resp.status_code} on {url}"
                )
            time.sleep(_backoff_delay(error_state["consecutive"], resp.headers.get("Retry-After")))
            continue

        resp.raise_for_status()  # other 4xx -> real failure, propagate immediately
        error_state["consecutive"] = 0
        return resp


# ---------------------------------------------------------------------------
# Fetch + parse -- Tier 1 (index sync)
# ---------------------------------------------------------------------------

def fetch_index(session, district, error_state):
    """One district -> list of project dicts (index-tier fields only).

    Two requests total: GET /home (session cookie) then POST
    /projectViewDetails with just `district`. Confirmed live to return the
    full district table in one response for Bengaluru Urban (4,074 rows)
    and Bengaluru  Rural (651 rows, NOTE double space in the site's own
    district value) -- no pagination mechanism observed.
    """
    _request_with_backoff(session, "GET", f"{BASE_URL}/home", error_state)
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    r1 = _request_with_backoff(
        session, "POST", f"{BASE_URL}/projectViewDetails", error_state,
        data={"district": district},
    )
    return parse_index_table(r1.text, district)


def parse_index_table(html, district):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="approvedTable")
    if table is None or table.find("tbody") is None:
        return []

    headers = [th.get_text(strip=True).lower() for th in table.find("thead").find_all("th")]
    rows = []
    for tr in table.find("tbody").find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        cells = {}
        detail_id = None
        for h, td in zip(headers, tds):
            a = td.find("a", id=True)
            if a is not None and str(a.get("id", "")).isdigit():
                detail_id = a["id"]
            cells[h] = td.get_text(" ", strip=True)

        reg_no = cells.get("registration no", "")
        ack_no = cells.get("acknowledgement no", "")
        rera_id = reg_no or ack_no
        if not rera_id:
            continue  # malformed row (e.g. stray header/spacer tr) -- skip

        extended = (
            cells.get("further extension date")
            or cells.get("section 6 extension date")
            or cells.get("covid-19 extension date")
            or ""
        )
        rows.append({
            "rera_id": rera_id,
            "ack_no": ack_no,
            "project_name": cells.get("project name", ""),
            "promoter_name": cells.get("promoter name", ""),
            "project_type": cells.get("project type", ""),
            "district": cells.get("district", "") or district,
            "taluk": cells.get("taluk", ""),
            "status": cells.get("status", ""),
            "registration_date": cells.get("approved on", ""),
            "proposed_completion": cells.get("proposed completion date", ""),
            "extended_completion": extended,
            "detail_id": detail_id or "",
            # POST-only endpoint (GET is 405) -- recorded as a reference for
            # the Tier-2 enrichment job, not a fetchable link.
            "source_url": (
                f"POST {BASE_URL}/projectDetails action={detail_id}" if detail_id else ""
            ),
            "fetched_at": _now_iso(),
        })
    return rows


def _upsert_project(conn, row):
    """Insert new / update index-tier columns only -- never clobbers Tier-2
    fields (survey_numbers, total_land_area, etc.) written by a later
    enrichment pass."""
    cols = _INDEX_COLUMNS
    placeholders = ", ".join(["?"] * len(cols))
    update_clause = ", ".join(f"{c}=excluded.{c}" for c in cols if c != "rera_id")
    sql = (
        f"INSERT INTO projects ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT(rera_id) DO UPDATE SET {update_clause}"
    )
    conn.execute(sql, [row[c] for c in cols])


# ---------------------------------------------------------------------------
# Fetch + parse -- Tier 2 (per-project detail enrichment)
#
# The site uses at least 2 different tab-id layouts across projects (older
# projects: home/menu1=Project Details/menu2=Uploaded Documents/...; newer
# projects: home/menu1=Land Details/menu2=Project Details/menu4=Bank
# Details/menu5=Uploaded Documents/...) -- confirmed by comparing Godrej
# United (id=6, 2017 registration) vs Embassy Eden (id=13471, 2025
# registration). Tab ids are therefore NOT relied on below; every extractor
# finds its data by a stable structural/text signature instead (table
# headers, `<h1>` text, css class), which held across both templates.
# ---------------------------------------------------------------------------

def fetch_detail(session, detail_id, error_state):
    r = _request_with_backoff(
        session, "POST", f"{BASE_URL}/projectDetails", error_state,
        data={"action": detail_id},
        headers={
            "Referer": f"{BASE_URL}/viewAllProjects",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    return r.text


def _row_pairs(soup):
    """Whole-page label -> value map from the site's repeating
    `<p class="text-right">Label:</p>` + following value-`<p>` div pairs.
    Not tab-scoped (see module docstring) -- fine for the handful of
    globally-unique labels this pilot reads (see parse_detail_html)."""
    pairs = {}
    for row in soup.find_all("div", class_="row"):
        divs = [d for d in row.find_all("div", recursive=False)
                if d.get("class") and any(c.startswith("col-md") for c in d.get("class"))]
        i = 0
        while i < len(divs) - 1:
            label_p = divs[i].find("p", class_=lambda c: c and "text-right" in c)
            if label_p is not None:
                label = label_p.get_text(" ", strip=True).rstrip(":").strip().lower()
                if label:
                    pairs[label] = divs[i + 1].get_text(" ", strip=True)
            i += 2
    return pairs


def _get_fuzzy(pairs, *substrings):
    """First pairs-dict value whose key contains ALL given substrings."""
    for key, val in pairs.items():
        if all(s in key for s in substrings):
            return val
    return ""


_SURVEY_TEXT_RE = re.compile(r"S(?:y|urvey)\.?\s*No\.?\s*[:\-]?\s*([0-9]+(?:/[0-9]+)?)", re.IGNORECASE)


def _extract_survey_numbers(soup):
    """Distinct values from the 'Survey Number' column of the Project Land
    Owner / Co-promoter Details table (verified present on both templates
    tested, but the table can be genuinely EMPTY for older projects --
    Godrej United/2017 has the section header with no rows at all). Falls
    back to a regex over the page's free-text addresses ("Survey No. 28/2")
    for that case -- first match only, explicitly partial, not
    authoritative like the table."""
    for table in soup.find_all("table"):
        thead = table.find("thead")
        if thead is None:
            continue
        ths = [th.get_text(strip=True).lower() for th in thead.find_all("th")]
        if "survey number" not in ths:
            continue
        idx = ths.index("survey number")
        seen, out = set(), []
        tbody = table.find("tbody") or table
        for tr in tbody.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) > idx:
                v = tds[idx].get_text(strip=True)
                if v and v not in seen:
                    seen.add(v)
                    out.append(v)
        if out:
            return ", ".join(out)

    m = _SURVEY_TEXT_RE.search(soup.get_text(" "))
    return m.group(1) + " (partial -- from address text, table was empty)" if m else ""


def _extract_total_units(soup, pairs):
    """Primary: the standalone `<table><tr><td>Total No of Units</td>
    <td>N</td></tr></table>` printed after the tower accordion (verified on
    both templates). Fallback: the 'Total Number of Inventories/Flats/
    Villas' label/value row."""
    for table in soup.find_all("table"):
        first_tr = table.find("tr")
        if first_tr is None:
            continue
        tds = first_tr.find_all("td")
        if len(tds) == 2 and tds[0].get_text(strip=True).lower() == "total no of units":
            return tds[1].get_text(strip=True)
    return _get_fuzzy(pairs, "total number of inventories")


def _extract_tower_breakdown(soup):
    """One entry per tower from the 'Tower Details - <name>' accordion
    panels (verified identical 4-summary-row structure on both templates):
    [{"tower", "floors", "units", "parking"}, ...] -- floor-level and
    unit-level tables are intentionally NOT captured (out of scope for
    comp-level data, would be huge for large projects)."""
    out = []
    for h1 in soup.find_all("h1"):
        text = h1.get_text(" ", strip=True)
        b = h1.find("b")
        # Require the "- <name>" form with a <b> tag -- the bare section
        # heading "Tower Details" (no dash/name) also starts with the same
        # prefix and is not an actual tower entry.
        if not text.startswith("Tower Details -") or b is None:
            continue
        tower_name = b.get_text(strip=True)
        # The Quarterly Update tab echoes the same "Tower Details - <name>"
        # heading (per-floor progress-bar widgets, not the summary table) --
        # verify the FIRST cell of the first candidate table really is
        # "Tower Name" before accepting it, rather than guessing by panel
        # class (both echoes use panel-default).
        panel = h1.find_parent("div", class_="panel-default") or h1.find_parent("div", class_="panel")
        table = panel.find("table", class_="table-bordered") if panel else None
        first_tds = [td.get_text(strip=True) for td in table.find("tr").find_all("td")] if table and table.find("tr") else []
        if not first_tds or first_tds[0].lower() != "tower name":
            continue  # not the tower-summary table -- skip, don't fabricate an empty row
        kv = {}
        for tr in table.find_all("tr", recursive=True)[:4]:
            tds = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(tds) >= 2:
                kv[tds[0].lower()] = tds[1]
            if len(tds) >= 4:
                kv[tds[2].lower()] = tds[3]
        out.append({
            "tower": tower_name,
            "floors": kv.get("no. of floors", ""),
            "units": kv.get("total no. of units", ""),
            "parking": kv.get("total no. of parking", ""),
        })
    return out


_QUARTER_HEADING_RE = re.compile(
    r"Quarter\s+Q\d\s*\(\s*\d{4}-\d{2}\s*\).*?Submitted on\s*([\d\-]+)", re.IGNORECASE
)


def _extract_quarterly(soup):
    """Latest Quarterly Update panel -> (last_qpr_date, completion_pct).
    Panels are matched by their heading TEXT ("Quarter Qn ( YYYY-YY )
    ... Submitted on DD-MM-YYYY"), not by tab id (see module docstring)."""
    best_date, best_pct = None, ""
    for panel in soup.find_all("div", class_="panel-primary"):
        heading = panel.find("div", class_="panel-heading")
        if heading is None:
            continue
        m = _QUARTER_HEADING_RE.search(heading.get_text(" ", strip=True))
        if not m:
            continue
        try:
            d = datetime.strptime(m.group(1), "%d-%m-%Y")
        except ValueError:
            continue
        if best_date is None or d > best_date:
            fill = panel.find("div", class_="progress_fill")
            best_date = d
            best_pct = fill.get_text(strip=True) if fill else ""
    return (best_date.strftime("%d-%m-%Y") if best_date else "", best_pct)


def _extract_approved_plan_url(soup):
    """Best-effort: first uploaded-document link whose visible text mentions
    'plan'. No reliable structured field ties a single document to
    'the approved plan' -- treat this as a heuristic, not authoritative."""
    for a in soup.find_all("a", href=True):
        if not a["href"].startswith("/download_jc"):
            continue
        if "plan" in a.get_text(" ", strip=True).lower():
            return BASE_URL + a["href"]
    return ""


def parse_detail_html(html):
    soup = BeautifulSoup(html, "html.parser")
    pairs = _row_pairs(soup)
    last_qpr_date, completion_pct = _extract_quarterly(soup)
    return {
        "survey_numbers": _extract_survey_numbers(soup),
        "total_land_area": _get_fuzzy(pairs, "total area of land"),
        "total_units": _extract_total_units(soup, pairs),
        "unit_breakdown": json.dumps(_extract_tower_breakdown(soup)),
        "last_qpr_date": last_qpr_date,
        "completion_pct": completion_pct,
        "approved_plan_url": _extract_approved_plan_url(soup),
        "locality": "",  # no structured source found -- see module docstring
    }


def _upsert_enrichment(conn, rera_id, fields):
    set_clause = ", ".join(f"{c}=?" for c in _TIER2_COLUMNS) + ", enriched=1"
    conn.execute(
        f"UPDATE projects SET {set_clause} WHERE rera_id=?",
        [fields[c] for c in _TIER2_COLUMNS] + [rera_id],
    )


# ---------------------------------------------------------------------------
# Query interface
# ---------------------------------------------------------------------------

_STALE_AFTER = timedelta(days=183)  # ~6 months


def _parse_site_date(s):
    """Site dates are DD/MM/YYYY (index table) or DD-MM-YYYY (detail page).
    Returns None for blank/unparseable -- never raises."""
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


def query_projects(db_path, locality=None, taluk=None, district=None, survey_no=None, limit=200):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    clauses, params = [], []
    if locality:
        clauses.append("locality LIKE ?")
        params.append(f"%{locality}%")
    if taluk:
        clauses.append("taluk LIKE ?")
        params.append(f"%{taluk}%")
    if district:
        clauses.append("district LIKE ?")
        params.append(f"%{district}%")
    if survey_no:
        clauses.append("survey_numbers LIKE ?")
        params.append(f"%{survey_no}%")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = [dict(r) for r in conn.execute(f"SELECT * FROM projects {where}", params)]
    conn.close()

    now = datetime.now()
    for r in rows:
        r["unit_breakdown"] = json.loads(r["unit_breakdown"]) if r["unit_breakdown"] else []
        r["_reg_date_parsed"] = _parse_site_date(r["registration_date"])
        if not r["enriched"]:
            # Haven't fetched Tier-2 yet -- staleness is genuinely unknown,
            # not "stale". Don't conflate "we haven't looked" with "the
            # promoter stopped reporting".
            r["stale"] = None
        else:
            qpr = _parse_site_date(r["last_qpr_date"])
            r["stale"] = (qpr is None) or (now - qpr > _STALE_AFTER)

    # Unparseable/blank registration_date sorts last, not first (a naive
    # string sort on DD/MM/YYYY text is wrong across year boundaries).
    rows.sort(key=lambda r: r["_reg_date_parsed"] or datetime.min, reverse=True)
    for r in rows:
        del r["_reg_date_parsed"]
    return rows[:limit]


# ---------------------------------------------------------------------------
# Job store
# ---------------------------------------------------------------------------

def _job_update(db_path, job_id, **fields):
    conn = sqlite3.connect(db_path)
    fields["updated_at"] = _now_iso()
    set_clause = ", ".join(f"{k}=?" for k in fields)
    conn.execute(f"UPDATE jobs SET {set_clause} WHERE job_id=?", [*fields.values(), job_id])
    conn.commit()
    conn.close()


def run_worker(job_id, db_path):
    """Runs in the detached child process."""
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT task, params FROM jobs WHERE job_id=?", (job_id,)).fetchone()
    conn.close()
    if row is None:
        return
    task, params_json = row
    params = json.loads(params_json)

    _job_update(db_path, job_id, status="running")
    error_state = {"consecutive": 0}
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    try:
        if task == "index":
            district = params["district"]
            records = fetch_index(session, district, error_state)
            conn = sqlite3.connect(db_path)
            for rec in records:
                _upsert_project(conn, rec)
            conn.commit()
            conn.close()
            _job_update(db_path, job_id, status="complete", n_fetched=len(records), truncated=0)

        elif task == "enrich":
            limit = int(params.get("limit", 5))
            conn = sqlite3.connect(db_path)
            candidates = conn.execute(
                "SELECT rera_id, detail_id FROM projects "
                "WHERE enriched=0 AND detail_id != '' ORDER BY rowid LIMIT ?",
                (limit,),
            ).fetchall()
            conn.close()

            _request_with_backoff(session, "GET", f"{BASE_URL}/home", error_state)

            job_start = time.time()
            n, truncated = 0, 0
            for rera_id, detail_id in candidates:
                if time.time() - job_start > JOB_CEILING_SECONDS:
                    truncated = 1  # remaining rows stay enriched=0 -- next
                    break          # `start --task enrich` naturally resumes
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                html = fetch_detail(session, detail_id, error_state)
                fields = parse_detail_html(html)
                conn = sqlite3.connect(db_path)
                _upsert_enrichment(conn, rera_id, fields)
                conn.commit()
                conn.close()
                n += 1
                _job_update(db_path, job_id, n_fetched=n)  # live progress
            _job_update(db_path, job_id, status="complete", n_fetched=n, truncated=truncated)

        else:
            raise NotImplementedError(f"task={task!r} not implemented")

    except HardFail as exc:
        _job_update(db_path, job_id, status="failed", error=str(exc))
    except Exception as exc:
        _job_update(db_path, job_id, status="failed", error=str(exc))


def _spawn_worker(job_id, db_path):
    script = os.path.abspath(__file__)
    log_dir = os.path.join(os.path.dirname(db_path), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{job_id}.log")
    log_file = open(log_path, "ab")

    cmd = [sys.executable, script, "--db", db_path, "_run_worker", job_id]
    kwargs = {"stdout": log_file, "stderr": log_file, "stdin": subprocess.DEVNULL}
    if os.name == "nt":
        kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(cmd, **kwargs)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_start(args):
    init_db(args.db)
    if args.task == "index":
        if not args.district:
            print(json.dumps({"error": "--district is required for task=index"}))
            sys.exit(1)
        params = json.dumps({"district": args.district})
    elif args.task == "enrich":
        params = json.dumps({"limit": args.limit})
    else:
        print(json.dumps({"error": f"task={args.task!r} not implemented in this pilot"}))
        sys.exit(1)

    job_id = uuid.uuid4().hex[:12]
    now = _now_iso()
    conn = sqlite3.connect(args.db)
    conn.execute(
        "INSERT INTO jobs (job_id, task, params, status, created_at, updated_at) "
        "VALUES (?, ?, ?, 'pending', ?, ?)",
        (job_id, args.task, params, now, now),
    )
    conn.commit()
    conn.close()

    _spawn_worker(job_id, args.db)
    print(json.dumps({"job_id": job_id, "status": "pending"}))


def cmd_check_job(args):
    conn = sqlite3.connect(args.db)
    row = conn.execute(
        "SELECT job_id, task, params, status, n_fetched, truncated, error, created_at, updated_at "
        "FROM jobs WHERE job_id=?",
        (args.job_id,),
    ).fetchone()
    conn.close()
    if row is None:
        print(json.dumps({"error": f"no such job_id {args.job_id!r}"}))
        sys.exit(1)

    (job_id, task, params_json, status, n_fetched, truncated,
     error, created_at, updated_at) = row
    print(json.dumps({
        "job_id": job_id,
        "task": task,
        "params": json.loads(params_json),
        "status": status,
        "n_fetched": n_fetched,
        "truncated": bool(truncated),
        "error": error,
        "created_at": created_at,
        "updated_at": updated_at,
    }))


def cmd_query(args):
    init_db(args.db)
    rows = query_projects(
        args.db, locality=args.locality, taluk=args.taluk,
        district=args.district, survey_no=args.survey_no, limit=args.limit,
    )
    print(json.dumps({"count": len(rows), "results": rows}, default=str))


def cmd_run_worker(args):
    run_worker(args.job_id, args.db)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default=os.path.abspath(DEFAULT_DB), help="SQLite store path")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("start", help="Enqueue a collection job, returns job_id immediately")
    p_start.add_argument("--task", default="index", choices=["index", "enrich"])
    p_start.add_argument("--district", help="e.g. 'Bengaluru Urban' or 'Bengaluru  Rural' (note double space)")
    p_start.add_argument("--limit", type=int, default=5, help="task=enrich: max un-enriched projects to fetch this run")
    p_start.set_defaults(func=cmd_start)

    p_check = sub.add_parser("check_job", help="Poll job status")
    p_check.add_argument("job_id")
    p_check.set_defaults(func=cmd_check_job)

    p_query = sub.add_parser("query", help="Filter/sort the local store -- no network calls")
    p_query.add_argument("--locality", help="substring match (note: always empty right now, see SKILL.md)")
    p_query.add_argument("--taluk", help="substring match, e.g. 'Anekal'")
    p_query.add_argument("--district", help="substring match, e.g. 'Bengaluru Urban'")
    p_query.add_argument("--survey-no", dest="survey_no", help="substring match against survey_numbers")
    p_query.add_argument("--limit", type=int, default=200)
    p_query.set_defaults(func=cmd_query)

    p_worker = sub.add_parser("_run_worker", help=argparse.SUPPRESS)  # internal
    p_worker.add_argument("job_id")
    p_worker.set_defaults(func=cmd_run_worker)

    args = p.parse_args()
    args.db = os.path.abspath(args.db)
    args.func(args)


if __name__ == "__main__":
    main()
