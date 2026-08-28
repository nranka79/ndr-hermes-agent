#!/opt/hermes/.venv/bin/python3
"""
Employment Generator Tracker — RSS → Sheet → Summary cron job.
Run daily at 9:30 AM IST via: cd /opt/hermes && /opt/hermes/.venv/bin/python3 scripts/employment-generator.py

Covers Karnataka (Bangalore peri-urban, beyond Bangalore), Tamil Nadu (Krishnagiri district,
Chennai periphery), and Andhra Pradesh border (Anantapur district).

Writes to 3 tabs in sheet 10LbBakverJ3GHJYz7ZgvzuSnemAWqjxUpGDUVTVr3ks:
  - Employment Announcements (Date, Company/Org, Location, Category, Jobs, Investment, Link, Headline, Notes)
  - Infrastructure (Date, Project Type, Promoter/Contractor, Location, Investment, Status, Link, Headline, Notes)
  - Policy & Approvals (Date, Title, Issuing Body, Geography, Type, Link, Headline, Notes)

Usage:
  cd /opt/hermes && /opt/hermes/.venv/bin/python3 scripts/employment-generator.py

Filters: 48h window, exclusion patterns, positive indicator check, geography match, dedup by key+link+title.
"""
import sys
sys.path.insert(0, '/opt/hermes')

import os
import re
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

from tools.gws_auth import build_service

# ─── Configuration ────────────────────────────────────────────────
SHEET_ID = "10LbBakverJ3GHJYz7ZgvzuSnemAWqjxUpGDUVTVr3ks"
# Identity comes from the session env (gateway/cron) — never hardcoded.
CUTOFF = datetime.now(timezone.utc) - timedelta(hours=48)
NOW_STR = datetime.now(timezone.utc).strftime('%Y-%m-%d')

# ─── RSS Queries (by category) ────────────────────────────────────
QUERIES = {
    "Employment": [
        "new factory OR new manufacturing unit OR new plant site Karnataka 2026",
        "GCC OR global capability centre OR back office Bangalore Chennai 2026",
        "new office set up OR new campus OR new facility Karnataka Tamil Nadu 2026",
        "IT park OR tech park opening OR new software centre Bangalore Chennai 2026",
        "investment announcement OR new industry Karnataka Tamil Nadu 2026",
    ],
    "Infrastructure": [
        "new road project OR highway awarded Karnataka Tamil Nadu 2026",
        "metro extension OR suburban rail Bangalore Chennai 2026",
        "freight corridor OR logistics park OR industrial corridor Karnataka 2026",
        "infrastructure project awarded OR approved Karnataka 2026",
    ],
    "Policy": [
        "industrial policy Karnataka Tamil Nadu 2026",
        "environmental approval OR pollution board consent Karnataka 2026",
        "KIADB land OR TIDCO OR Guidance Tamil Nadu allotment 2026",
        "land acquisition industry OR SEZ notification Karnataka 2026",
    ],
}

# ─── Exclusion patterns ──────────────────────────────────────────
EXCLUSION_RE = re.compile(
    r'\b(dispute|Cauvery|election|voter|DMK|fight|row|protest|agitati|controvers|'
    r'scrap|cancel|cancelling|scrapped|poll\s+bond|corruption|scam|'
    r'CAG|audit|irregularities|misappropriation|embezzlement|'
    r'murder|accident|collision|criminal|arrest|encounter|violence|'
    r'flood|drought|cyclone|earthquake|'
    r'temple|mosque|prayer|religious|church|'
    r'admission|exam|result|degree|syllabus|'
    r'cricket|IPL|match|tournament|'
    r'opinion|editorial|column|'
    r'hospitalization|disease|pandemic)\b',
    re.IGNORECASE
)

# ─── Positive indicators by category ──────────────────────────────
POSITIVE_RE = {
    "Employment": re.compile(
        r'\b(new\s+(factory|plant|manufacturing|facility|campus|office|unit)|'
        r'expansion|inaugurat|opened|launch|commission|'
        r'investment|GCC|global capability centre|'
        r'create\s+\d+|employ\s+\d+|job|workforce|'
        r'IT park|tech park|SEZ|'
        r'set\s+up|establish|'
        r'back\s+office|BPO)\b', re.IGNORECASE
    ),
    "Infrastructure": re.compile(
        r'\b(new\s+(road|highway|bridge|flyover|metro|railway|rail)|'
        r'inaugurat|opened|launch|commission|awarded|approved|'
        r'expansion|extension|'
        r'freight\s+corridor|logistics\s+(park|hub)|'
        r'industrial\s+corridor|port|airport|'
        r'power\s+(plant|project|station)|renewable\s+energy|'
        r'water\s+(project|supply|treatment))\b', re.IGNORECASE
    ),
    "Policy": re.compile(
        r'\b(industrial\s+policy|investment\s+policy|SEZ|'
        r'environmental\s+(clearance|approval)|'
        r'pollution\s+(board|consent|clearance)|'
        r'KIADB|TIDCO|Guidance|'
        r'land\s+acquisition|incentive|subsidy|'
        r'approved|notified|notification)\b', re.IGNORECASE
    ),
}

# ─── Geography patterns ───────────────────────────────────────────
GEOGRAPHY_RE = re.compile(
    r'\b('
    r'Devanahalli|Doddaballapur|Kolar|Tumkur|Nelamangala|'
    r'Bidarahalli|Yelahanka|Ramnagar|'
    r'Sarjapur|Whitefield|Huskur|Hosa\s*Road|Jigani|'
    r'Attibele|Electronic\s*City|Anekal|Chandapura|Huskote|Hebbagodi|'
    r'Mysore|Mangalore|Hubli|Dharwad|Belgaum|Belagavi|Hassan|'
    r'Hosur|Krishnagiri|Shoolagiri|Berigai|Denkanikottai|Pochampalli|'
    r'Sriperumbudur|Oragadam|Maraimalai\s*Nagar|Chengalpattu|'
    r'Kancheepuram|Kattankulathur|'
    r'Hindupur|Lepakshi|Puttaparthi|Kalyandurg|Rayadurg|Tadpatri|Madakasira|'
    r'Karnataka|Bangalore|Bengaluru|Tamil\s*Nadu|Chennai|'
    r'Anantapur|Andhra\s*Pradesh'
    r')\b', re.IGNORECASE
)

# ─── Geography tagging ────────────────────────────────────────────
def geo_to_tagged(match_str, full_text):
    """Map a geography mention to a tagged location string."""
    t = full_text.lower()
    m = match_str.lower().replace(" ", "")

    if "devanahalli" in m or ("bengaluru" in m and "international" in t):
        return "Devanahalli, Bangalore North"
    if "doddaballapur" in m:
        return "Doddaballapur, Bangalore North"
    if "yelahanka" in m:
        return "Yelahanka, Bangalore North"
    if "nelamangala" in m:
        return "Nelamangala, Bangalore North"
    if "tumkur" in m:
        return "Tumkur, Karnataka"
    if "kolar" in m:
        return "Kolar, Karnataka"
    if "whitefield" in m:
        return "Whitefield, Bangalore East"
    if "sarjapur" in m:
        return "Sarjapur, Bangalore South"
    if "electroniccity" in m or ("electronic" in t and "city" in t):
        return "Electronic City, Bangalore South"
    if "jigani" in m:
        return "Jigani, Bangalore South"
    if "hosur" in m and "shoolagiri" not in t:
        return "Hosur, Krishnagiri District, TN"
    if "shoolagiri" in m:
        return "Shoolagiri, Krishnagiri District, TN"
    if "krishnagiri" in m:
        return "Krishnagiri, TN"
    if "sriperumbudur" in m or "sri perumbudur" in t:
        return "Sriperumbudur, Chennai Periphery"
    if "oragadam" in m:
        return "Oragadam, Chennai Periphery"
    if "maraimalai" in m:
        return "Maraimalai Nagar, Chennai Periphery"
    if "chengalpattu" in m:
        return "Chengalpattu, Chennai Periphery"
    if "kancheepuram" in m:
        return "Kancheepuram, Chennai Periphery"
    if "hindupur" in m:
        return "Hindupur, Anantapur, AP"
    if "mysore" in m:
        return "Mysore, Karnataka"
    if "mangalore" in m:
        return "Mangalore, Karnataka"
    if "hubli" in m:
        return "Hubli, Karnataka"
    if "dharwad" in m:
        return "Dharwad, Karnataka"
    if "belgaum" in m or "belagavi" in m:
        return "Belgaum, Karnataka"
    if "hassan" in m:
        return "Hassan, Karnataka"
    if "chennai" in m:
        return "Chennai, TN"
    if "bangalore" in m or "bengaluru" in m:
        return "Bangalore (general)"
    if "karnataka" in m:
        return "Karnataka (unspecified)"
    if "tamil" in m or "tamilnadu" in m:
        return "Tamil Nadu (unspecified)"
    if "andhra" in m or "anantapur" in m:
        return "Andhra Pradesh (unspecified)"
    return match_str


def extract_geography(title_desc):
    """Extract tagged geography from title+description."""
    matches = GEOGRAPHY_RE.findall(title_desc)
    if not matches:
        return None
    tagged = []
    seen = set()
    for m in matches:
        norm = geo_to_tagged(m, title_desc)
        if norm not in seen:
            tagged.append(norm)
            seen.add(norm)
    return "; ".join(tagged)


# ─── RSS fetching ─────────────────────────────────────────────────
def fetch_rss(query):
    """Fetch Google News RSS for a query, return parsed items."""
    url = (
        "https://news.google.com/rss/search?q="
        + quote(query)
        + "&hl=en-IN&gl=IN&ceid=IN:en"
    )
    tmpfile = f"/tmp/empgen_{abs(hash(query))}.xml"

    try:
        subprocess.run(
            ["curl", "-s", "-L", url, "-o", tmpfile],
            timeout=30, capture_output=True
        )
        tree = ET.parse(tmpfile)
        root = tree.getroot()
        channel = root.find("channel")
        if channel is None:
            return []
        items = channel.findall("item")

        articles = []
        for item in items:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            description = item.findtext("description", "")
            pub_date_str = item.findtext("pubDate", "")

            if not title or not pub_date_str:
                continue

            # Clean description of HTML tags
            description_clean = re.sub(r'<[^>]+>', '', description)

            # Parse pubDate — format: 'Sat, 30 May 2026 04:45:06 GMT'
            try:
                pub_dt = datetime.strptime(pub_date_str.strip(), '%a, %d %b %Y %H:%M:%S %Z')
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
            except Exception:
                try:
                    pub_dt = datetime.strptime(pub_date_str.strip(), '%a, %d %b %Y %H:%M:%S %z')
                except Exception:
                    continue  # skip unparseable

            articles.append({
                "title": title.strip(),
                "link": link.strip(),
                "description": description_clean.strip(),
                "pub_dt": pub_dt,
            })

        return articles
    except Exception as e:
        print(f"WARN: failed to fetch RSS for query: {query[:50]}... - {e}")
        return []
    finally:
        try:
            os.remove(tmpfile)
        except OSError:
            pass


# ─── Filtering ────────────────────────────────────────────────────
HIRING_RE = re.compile(r'\b(hiring|recruitment drive|job fair|walk-in interview)\b', re.IGNORECASE)
RESIDENTIAL_RE = re.compile(r'\b(residential|housing society|apartment complex)'.replace(' ', r'\s*'), re.IGNORECASE)


def passes_filters(article, category):
    """Check if article passes exclusion and positive indicator filters."""
    text = (article["title"] + " " + article["description"]).lower()

    # Skip hiring drives (not new employment generation)
    if HIRING_RE.search(text):
        return False

    # Skip purely residential real estate
    if RESIDENTIAL_RE.search(text) and not POSITIVE_RE[category].search(text):
        return False

    # Exclusion patterns (political, negative, crime, etc.)
    if EXCLUSION_RE.search(text):
        # Exception: strong infrastructure/employment indicators override marginal negatives
        if category == "Infrastructure" and POSITIVE_RE["Infrastructure"].search(text):
            if re.search(r'\b(scrap|cancel|scrapped)\b', text):
                return False  # cancellation stories are not employment-generating
            return True  # infrastructure article with marginal political mention
        return False

    # Must have positive indicator
    if not POSITIVE_RE[category].search(text):
        return False

    # Must mention geography of interest
    geo = extract_geography(text)
    if not geo:
        return False

    article["geography"] = geo
    return True


def normalize_title(title):
    """Normalize title for same-run dedup."""
    t = title.lower()
    t = re.sub(r'[^a-z0-9 ]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t[:60]


# ─── Extract company name from headline ───────────────────────────
def extract_company(title, description):
    """Try to extract company/organization name from headline."""
    text = title + " " + description
    for sep in [' targets ', ' announces ', ' plans ', ' to invest ', ' to set up ',
                ' inaugurates ', ' opens ', ' launches ', ' starts ']:
        idx = text.lower().find(sep)
        if idx > 0 and idx < 60:
            text = text[:idx]
            break
    text = re.sub(r'\s*-\s*\w+$', '', text)
    text = re.sub(r'\|.*$', '', text)
    return text[:50].strip()


# ─── RSS → Sheet row converters ───────────────────────────────────
def rss_to_employment_row(article):
    """Convert RSS article to Employment Announcements row."""
    company = extract_company(article["title"], article["description"])

    t = (article["title"] + " " + article["description"]).lower()
    if re.search(r'\b(gcc|global capability centre|captive centre|back office|bpo)\b', t):
        category = "GCC"
    elif re.search(r'\b(manufacturing|factory|plant)\b', t):
        category = "Manufacturing"
    elif re.search(r'\b(it park|tech park|software|IT)\b', t):
        category = "IT Park"
    elif re.search(r'\b(r&d|research|development|innovation)\b', t):
        category = "R&D"
    elif re.search(r'\b(logistics|warehouse|supply chain)\b', t):
        category = "Logistics"
    else:
        category = "Other"

    jobs_match = re.search(r'(\d[\d,]*)\s*(jobs?|employ|workforce|people|positions?)', t)
    jobs = jobs_match.group(1).replace(",", "") if jobs_match else ""

    inv_match = re.search(r'(Rs\s*[\d,]+|₹\s*[\d,]+|INR\s*[\d,]+|\d[\d,]*\s*(crore|lakh|crore|billion|million|bn|mn))', t)
    investment = inv_match.group(0) if inv_match else ""

    return [NOW_STR, company, article["geography"], category, jobs, investment,
            article["link"], article["title"], ""]


def rss_to_infrastructure_row(article):
    """Convert RSS article to Infrastructure row."""
    t = (article["title"] + " " + article["description"]).lower()

    if re.search(r'\b(metro|suburban rail)\b', t):
        proj_type = "Metro"
    elif re.search(r'\b(road|highway)\b', t):
        proj_type = "Road/Highway"
    elif re.search(r'\brail(?:way)?s?\b', t) or 'traction' in t:
        proj_type = "Railway"
    elif re.search(r'\b(freight corridor)\b', t):
        proj_type = "Freight Corridor"
    elif re.search(r'\b(logistics park|logistics hub)\b', t):
        proj_type = "Logistics Park"
    elif re.search(r'\b(industrial corridor)\b', t):
        proj_type = "Industrial Corridor"
    elif re.search(r'\b(flyover|bridge)\b', t):
        proj_type = "Flyover/Bridge"
    elif re.search(r'\b(port|airport)\b', t):
        proj_type = "Port/Airport"
    elif re.search(r'\b(power|renewable|solar|wind)\b', t):
        proj_type = "Power"
    elif re.search(r'\b(water|sewage|treatment)\b', t):
        proj_type = "Water"
    else:
        proj_type = "Other"

    promoter = extract_company(article["title"], article["description"])

    if re.search(r'\b(awarded|approved|sanctioned)\b', t):
        status = "Awarded"
    elif re.search(r'\b(inaugurat|opened|start|begin|launch)\b', t):
        status = "In Progress"
    elif re.search(r'\b(complete|operational|inaugurated)\b', t):
        status = "Completed"
    elif re.search(r'\b(on hold|stalled|delay)\b', t):
        status = "On Hold"
    else:
        status = "Announced"

    inv_match = re.search(r'(Rs\s*[\d,]+|₹\s*[\d,]+|INR\s*[\d,]+|\d[\d,]*\s*(crore|crore|billion|million|bn|mn))', t)
    investment = inv_match.group(0) if inv_match else ""

    return [NOW_STR, proj_type, promoter, article["geography"], investment, status,
            article["link"], article["title"], ""]


def rss_to_policy_row(article):
    """Convert RSS article to Policy & Approvals row."""
    t = (article["title"] + " " + article["description"]).lower()

    if re.search(r'\b(industrial policy|investment policy)\b', t):
        ptype = "Industrial Policy"
    elif re.search(r'\b(SEZ)\b', t):
        ptype = "SEZ Notification"
    elif re.search(r'\b(environmental clearance|environmental approval)\b', t):
        ptype = "Environmental Approval"
    elif re.search(r'\b(land acquisition)\b', t):
        ptype = "Land Acquisition"
    elif re.search(r'\b(pollution board|pollution consent|kspcb)\b', t):
        ptype = "Pollution Board Consent"
    elif re.search(r'\b(KIADB)\b', t):
        ptype = "KIADB Allotment"
    elif re.search(r'\b(TIDCO|Guidance[^a-z]*(TN|Tamil))\b', t, re.IGNORECASE):
        ptype = "TIDCO/Guidance TN"
    elif re.search(r'\b(incentive|subsidy)\b', t):
        ptype = "Government Incentive"
    else:
        ptype = "Other"

    if re.search(r'\b(KIADB)\b', t):
        issuing = "KIADB"
    elif re.search(r'\b(KSPCB|Karnataka pollution|pollution control board)\b', t):
        issuing = "KSPCB"
    elif re.search(r'\b(TIDCO)\b', t):
        issuing = "TIDCO"
    elif re.search(r'\b(Guidance)\b', t):
        issuing = "Guidance Tamil Nadu"
    elif re.search(r'\b(invest karnataka|investkarnataka)\b', t):
        issuing = "Invest Karnataka"
    elif re.search(r'\b(government of karnataka|karnataka government)\b', t):
        issuing = "Karnataka Government"
    elif re.search(r'\b(government of tamil nadu|tamil nadu government)\b', t):
        issuing = "Tamil Nadu Government"
    else:
        issuing = extract_company(article["title"], article["description"])

    return [NOW_STR, article["title"], issuing, article["geography"], ptype,
            article["link"], article["title"], ""]


# ─── Sheet operations ────────────────────────────────────────────
SHEET_CONFIG = {
    "Employment Announcements": {
        "row_fn": rss_to_employment_row,
        "cols": 9,
    },
    "Infrastructure": {
        "row_fn": rss_to_infrastructure_row,
        "cols": 9,
    },
    "Policy & Approvals": {
        "row_fn": rss_to_policy_row,
        "cols": 8,
    },
}


def read_sheet_tab(sheets, tab_name):
    """Read all rows from a sheet tab."""
    try:
        result = sheets.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f"'{tab_name}'!A1:Z500"
        ).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"ERROR reading '{tab_name}': {e}")
        return []


def write_new_rows(sheets, tab_name, new_rows):
    """Write new rows using update() with explicit range — NEVER use append()."""
    if not new_rows:
        return 0

    existing = read_sheet_tab(sheets, tab_name)
    next_row = len(existing) + 1
    num_cols = SHEET_CONFIG[tab_name]["cols"]
    end_col = chr(64 + num_cols)

    try:
        req = sheets.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=f"'{tab_name}'!A{next_row}:{end_col}{next_row + len(new_rows) - 1}",
            valueInputOption='RAW',
            body={'values': new_rows}
        )
        result = req.execute()
        print(f"Wrote {len(new_rows)} rows to '{tab_name}', updated {result.get('updatedCells')} cells")
        return len(new_rows)
    except Exception as e:
        print(f"ERROR writing to '{tab_name}': {e}")
        return 0


# ─── Dedup against existing sheet data ───────────────────────────
def dedup_vs_existing(new_articles, existing_rows, tab_name):
    """Dedup new articles against existing sheet rows using key+link+title."""
    existing_links = set()
    existing_titles = set()

    for row in existing_rows[1:]:  # skip header
        if len(row) >= 7:
            existing_links.add(row[6].strip())
        if len(row) >= 8:
            existing_titles.add(normalize_title(row[7]))

    # Build dedup keys per tab
    if tab_name == "Employment Announcements":
        existing_keys = set()
        for row in existing_rows[1:]:
            if len(row) >= 4:
                company = row[1].lower().strip()[:40]
                location = row[2].lower().strip()[:40]
                category = row[3].lower().strip()
                existing_keys.add(f"{company}|{location}|{category}")

        result = []
        for art in new_articles:
            row = SHEET_CONFIG[tab_name]["row_fn"](art)
            key = f"{row[1].lower().strip()[:40]}|{row[2].lower().strip()[:40]}|{row[3].lower().strip()}"
            link = row[6].strip()
            title_norm = normalize_title(row[7])
            if key in existing_keys or (link and link in existing_links) or (title_norm and title_norm in existing_titles):
                continue
            result.append(art)
        return result

    elif tab_name == "Infrastructure":
        existing_keys = set()
        for row in existing_rows[1:]:
            if len(row) >= 4:
                proj_type = row[1].lower().strip()
                location = row[3].lower().strip()[:40]
                promoter = row[2].lower().strip()[:40]
                existing_keys.add(f"{proj_type}|{location}|{promoter}")

        result = []
        for art in new_articles:
            row = SHEET_CONFIG[tab_name]["row_fn"](art)
            key = f"{row[1].lower().strip()}|{row[3].lower().strip()[:40]}|{row[2].lower().strip()[:40]}"
            link = row[6].strip()
            title_norm = normalize_title(row[7])
            if key in existing_keys or (link and link in existing_links) or (title_norm and title_norm in existing_titles):
                continue
            result.append(art)
        return result

    elif tab_name == "Policy & Approvals":
        existing_keys = set()
        for row in existing_rows[1:]:
            if len(row) >= 3:
                date_part = row[0][:7] if row[0] else ""
                title = row[1].lower().strip()[:60] if len(row) > 1 else ""
                body = row[2].lower().strip() if len(row) > 2 else ""
                existing_keys.add(f"{title}|{body}|{date_part}")

        result = []
        for art in new_articles:
            row = SHEET_CONFIG[tab_name]["row_fn"](art)
            key = f"{row[1].lower().strip()[:60]}|{row[2].lower().strip()}|{row[0][:7]}"
            link = row[5].strip() if len(row) > 5 else ""
            title_norm = normalize_title(row[6]) if len(row) > 6 else ""
            if key in existing_keys or (link and link in existing_links) or (title_norm and title_norm in existing_titles):
                continue
            result.append(art)
        return result

    return new_articles


def dedup_same_run(articles):
    """Remove duplicate articles within a single run (by link and normalized title)."""
    seen_links = set()
    seen_titles = set()
    result = []
    for art in articles:
        if art["link"] and art["link"] in seen_links:
            continue
        norm = normalize_title(art["title"])
        if norm in seen_titles:
            continue
        seen_links.add(art["link"])
        seen_titles.add(norm)
        result.append(art)
    return result


# ─── Main ─────────────────────────────────────────────────────────
def main():
    print(f"{'='*60}")
    print(f"Employment Generator Tracker — {NOW_STR}")
    print(f"Cutoff (48h): {CUTOFF.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    # Authenticate
    try:
        sheets = build_service('sheets', 'v4', service_name='google-gmail')
        sheets.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
        print("✓ Sheets API authenticated")
    except Exception as e:
        if 'ACCESS_TOKEN_SCOPE_INSUFFICIENT' in str(e):
            print("ERROR: Token missing spreadsheets scope — user must re-authorize")
            sys.exit(1)
        if 'RefreshError' in str(e) or 'No refresh token' in str(e):
            print(f"ERROR: Token refresh failed — {e}")
            sys.exit(1)
        print(f"ERROR: {e}")
        sys.exit(1)

    # Map categories to tab names
    TAB_MAP = {
        "Employment": "Employment Announcements",
        "Infrastructure": "Infrastructure",
        "Policy": "Policy & Approvals",
    }

    total_written = 0
    new_by_tab = {}

    for category, queries in QUERIES.items():
        tab_name = TAB_MAP[category]
        print(f"\n─── {category} ───")

        all_articles = []
        for query in queries:
            articles = fetch_rss(query)
            print(f"  Query: {query[:60]}... → {len(articles)} raw articles")
            for art in articles:
                art["category"] = category
            all_articles.extend(articles)

        if not all_articles:
            print(f"  No articles fetched")
            new_by_tab[tab_name] = []
            continue

        # 48h filter
        recent = [a for a in all_articles if a["pub_dt"] >= CUTOFF]
        print(f"  After 48h filter: {len(recent)}/{len(all_articles)}")

        if recent:
            sorted_by_date = sorted(recent, key=lambda x: x["pub_dt"], reverse=True)
            print(f"  Freshest: {sorted_by_date[0]['pub_dt'].strftime('%Y-%m-%d %H:%M')}")

        # Content + geography filters
        passed = [a for a in recent if passes_filters(a, category)]
        print(f"  After content/geo filters: {len(passed)}/{len(recent)}")

        if not passed:
            new_by_tab[tab_name] = []
            continue

        # Same-run dedup
        unique = dedup_same_run(passed)
        print(f"  After same-run dedup: {len(unique)}/{len(passed)}")

        # Sheet dedup
        existing = read_sheet_tab(sheets, tab_name)
        print(f"  Existing rows (incl header): {len(existing)}")
        deduped = dedup_vs_existing(unique, existing, tab_name)
        print(f"  After sheet dedup: {len(deduped)}/{len(unique)}")

        if not deduped:
            new_by_tab[tab_name] = []
            continue

        schema = SHEET_CONFIG[tab_name]
        new_rows = [schema["row_fn"](art) for art in deduped]
        n = write_new_rows(sheets, tab_name, new_rows)
        total_written += n
        new_by_tab[tab_name] = new_rows

    # ─── Summary ───────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    if total_written == 0:
        print("\nNo new employment generation announcements in the last 48 hours.")
    else:
        print(f"\nNew entries added: {total_written}")
        for tab_name, rows in new_by_tab.items():
            if not rows:
                continue
            print(f"\n── {tab_name} ({len(rows)} new) ──")
            for row in rows:
                if tab_name == "Employment Announcements":
                    print(f"  [{row[0]}] {row[1]} — {row[2]} — {row[3]} — Jobs: {row[4] or 'N/A'} — Invest: {row[5] or 'N/A'}")
                elif tab_name == "Infrastructure":
                    print(f"  [{row[0]}] {row[1]} — {row[3]} — {row[2]} — {row[5]} — Invest: {row[4] or 'N/A'}")
                elif tab_name == "Policy & Approvals":
                    print(f"  [{row[0]}] {row[1][:70]}... — {row[2]} — {row[3]} — {row[4]}")

    print(f"\n{'='*60}")
    print(f"Run complete at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")


if __name__ == "__main__":
    main()
