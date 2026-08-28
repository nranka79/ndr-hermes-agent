#!/usr/bin/env python3
"""
AI Job Loss Tracker — permanent cron runner for the news-tracker umbrella.

RSS → Google Sheets → Telegram summary.
Invoke via cron at 04:00 UTC daily:

cd /opt/hermes && HERMES_SESSION_USER_ID=<owner-telegram-id> \
    /opt/hermes/.venv/bin/python3 \
    /data/hermes/skills/news-tracker/scripts/ai-job-loss-tracker.py

Requires:
- HERMES_SESSION_USER_ID set to the Telegram user ID in the shell environment (the cron job owner)
- /opt/hermes on sys.path (imports tools.gws_auth)

Pitfall: The env var must be a numeric Telegram ID, not an email address — the token path is /data/hermes/users/{telegram_id}/the gws-vault daemon (no token files exist on disk).
"""
import os
import re
import sys
import xml.etree.ElementTree as ET
import urllib.request
from datetime import datetime, timezone, timedelta

sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

# ── Identity ──────────────────────────────────────────────────────────────
# Identity must be provided by the caller (gateway session / cron owner env).
# Never default to a specific user's id here.
UID = os.environ.get('HERMES_SESSION_USER_ID', 'UNSET')

# ── Config ────────────────────────────────────────────────────────────────
SHEET_ID = "1uiUJuUC8nOW7N4vLUBl7a8QPvuYJu1UAc6Kmj-IXB-M"
NUM_COLS = 10  # A-J
CURRENT_Q = f"Q{(datetime.now(timezone.utc).month - 1) // 3 + 1} {datetime.now(timezone.utc).year}"
CUTOFF = datetime.now(timezone.utc) - timedelta(hours=48)

RSS_FEEDS = [
    ("IN", "https://news.google.com/rss/search?q=AI%20layoffs%202026&hl=en-IN&gl=IN&ceid=IN:en"),
    ("US", "https://news.google.com/rss/search?q=AI%20layoffs%20OR%20AI%20job%20cuts%202026&ceid=US:en"),
]

SOURCE_RANK = {
    'Reuters': 10, 'Bloomberg': 10, 'Financial Times': 9,
    'NYT': 9, 'WSJ': 9, 'Guardian': 8, 'BBC': 8,
    'Economic Times': 8, 'Forbes': 7, 'CNBC': 7,
    'TechCrunch': 7, 'Business Insider': 7, 'VentureBeat': 6,
    'Yahoo Finance': 6,
}

# ── Skip patterns ─────────────────────────────────────────────────────────
COUNTRY_SKIP = re.compile(
    r'^(China|India|US|United States|Brazil|Indonesia|Russia|Japan|'
    r'Germany|France|UK|Europe|Asia)\s', re.I
)
SKIP_PROGRAMS = re.compile(
    r'cuts?\s+\d+\s+(?:university|college|school|program|institution)', re.I
)
SKIP_TRACKER = re.compile(
    r'(2026 Layoffs Tracker|Challenger Report|Challenger Links AI|'
    r'US Job Cuts Jump|AI-Driven Layoffs Hit|May Job Cuts Rise|'
    r'Tech Industry Loses.*Jobs.*Year|AI cited as top reason|'
    r'Are AI tech layoffs real|How to Survive|'
    r'AI anxiety|AI won\'t take|Enterprise AI Costs|'
    r'No better opportunity than India|Govt Gears Up|'
    r'Professional Accountability|A CEO told employees|'
    r'Canada Launches|AI job losses are|'
    r'AI-driven tech.*hit two-year|AI Engineering Jobs Look|'
    r'Expert Warns.*AI Washing|California Launches.*Tracker|'
    r'Watch Former Governors|To the editor|AI Cuts Animation|'
    r'Stanford 2026 AI Index|Tokenpocalypse|'
    r'Meta Calls Its Own.*Reorg|'
    r'Tech layoffs cross.*lakh|Layoff looms.*industry sheds|'
    r'Companies laying off staff.*see the list)', re.I
)
# Skip financial-forecast cuts, not job cuts: "Upwork cuts 2026 revenue forecast",
# "Upwork Cuts Profit Forecast" — the number after the verb is a YEAR, not a job count.
# Without this guard the generic catch-all `cuts\s+[\d,]+` matches "cuts 2026 ..." and
# the tracker adds a false "jobs lost" row (2026-08-11/12 Upwork false positive).
SKIP_FORECAST = re.compile(
    r'cut[s]?\s+(?:\d{4}\s+)?(?:revenue|profit|earnings|sales|guidance|outlook|forecast|estimates?)\b', re.I
)

# ── Generic company descriptor skip ────────────────────────────────────────
# Skip headlines like "Software company soars amid plans to cut X jobs"
# where the subject is a generic descriptor, not a named company.
GENERIC_DESCRIPTOR_SKIP = re.compile(
    r'^(Software company|Tech company|Cloud company|AI company|'
    r'Fintech company|Financial company|Banking company|'
    r'Software firm|Tech firm|Cloud firm|AI firm|'
    r'Internet company|E-commerce company|Ecommerce company|'
    r'Softwar[em]\s+(?:company|firm)|'
    r'Tech\s+(?:giant|startup|start-up|firm|company)|'
    r'Cloud\s+(?:giant|firm|company)|'
    r'AI\s+(?:startup|start-up|firm|company))\s+', re.I
)

# ── Company extraction patterns ───────────────────────────────────────────
# IMPORTANT: All patterns are anchored at START of title.
# Do NOT add a generic 'extract_company()' — too many false positives.
COMPANY_PATTERNS = [
    re.compile(r'^(Meta Platforms?|Meta)\s+(dumps|lays off|cuts|slashes|to cut|to slash)', re.I),
    re.compile(r'^(Google)\s+(dumps|lays off|cuts|slashes|to cut)', re.I),
    re.compile(
        r'^(Amazon|Microsoft|Oracle|Wix|GitLab|Cloudflare|Cisco|Intuit|Groupon|'
        r'Synopsys|SentinelOne|ClickUp|Innovaccer|AI21 Labs|'
        r'Standard Chartered|Acrisure|Nasdaq|Rackspace|ServiceNow)\s+'
        r'(dumps|lays off|cuts|slashes|to cut|to slash)', re.I
    ),
    # "Company to cut X jobs" (generic catch-all)
    re.compile(r'^([A-Z][a-zA-Z0-9\s&\-]+?)\s+to\s+cut\s+[\d,]+', re.I),
    re.compile(r'^([A-Z][a-zA-Z0-9\s&\-]+?)\s+to\s+slash\s+[\d,]+', re.I),
    re.compile(r'^([A-Z][a-zA-Z0-9\s&\-]+?)\s+to\s+lay\s+off\s+[\d,]+', re.I),
    # "Company cuts/slashes X workers"
    re.compile(r'^([A-Z][a-zA-Z0-9\s&\-]+?)\s+(?:cut[s]?|slashes|lays off|dumps)\s+[\d,]+', re.I),
    # "Company cuts nearly/about/around/over/up to X jobs" — qualifier between verb and number
    re.compile(
        r'^([A-Z][a-zA-Z0-9\s&\-]+?)\s+(?:cut[s]?|slashes|lays off|dumps)\s+'
        r'(?:nearly|about|around|almost|over|more than|up to)?\s*[\d,]+', re.I
    ),
    # Possessive: "Company's new CEO cuts X%"
    re.compile(r"^([A-Z][a-zA-Z0-9\s&\-]+)'s\s+(?:new\s+)?CEO\s+cuts\s+[\d,]+\s*%?", re.I),
    # Parenthetical ticker: "Oracle (ORCL) Cuts..."
    re.compile(r'^(Oracle)\s+\(ORCL\)\s+(?:Cuts?|cut)\s+[\d,]+', re.I),
    # "Tech giant Oracle sheds..."
    re.compile(r'^Tech giant (Oracle|Google|Microsoft|Amazon|Meta)\s+(?:sheds|shrinks|confirms|cuts|slashes)', re.I),
    # "Payments giant Visa cuts..." / "Payment processor Visa lays off..."
    re.compile(
        r'^(Payments?\s+(?:giant|processor|firm)|Payment\s+processor)\s+'
        r'(Visa|Mastercard|Amex|American\s+Express|PayPal|Block|Square)\s+'
        r'(?:sheds|shrinks|confirms|cuts|slashes|to\s+cut|to\s+slash|'
        r'lays\s+off|to\s+lay\s+off|dumps)', re.I
    ),
    # Passive: "Oracle confirms..." / "Oracle workforce shrinks..."
    re.compile(
        r'^(Oracle|Google|Microsoft|Amazon|Meta|Cisco|Intuit|Wix|GitLab|'
        r'Cloudflare|Rackspace)\s+'
        r'(?:confirms?|workforce\s+shrinks?|sheds?)\s+[\d,]+', re.I
    ),
    # Visa — handles "Visa Set to cut" (where "Set" is NOT part of company name)
    re.compile(
        r'^(Visa)\s+(?:Set\s+)?(?:to\s+cut|to\s+slash|to\s+lay\s+off|'
        r'cuts|slashes|lays\s+off|dumps)\s+', re.I
    ),
    # Named patterns for non-obvious companies
    re.compile(r'^(British American Tobacco)\s+to\s+(?:lay off|cut|slash)\s+[\d,]+', re.I),
    re.compile(r'^(British American Tobacco)\s+(?:cut[s]?|slash[es]?|lay[s]?\s+off)\s+[\d,]+', re.I),
    # T-Mobile — "T-Mobile US cut more than 4,500 jobs" (bare past-tense verb + qualifier)
    re.compile(
        r'^(T-Mobile)\s+(?:US\s+)?(?:cut[s]?|to\s+cut|to\s+slash|slashes|lay[s]?\s+off)\s+'
        r'(?:more than|nearly|about|around|almost|over|up to)?\s*[\d,]+', re.I
    ),
    # "Company layoffs 2026: N roles cut..." — noun-form headlines (Apple/People Matters style)
    re.compile(r'^(Apple)\s+layoffs?\s+\d{4}:', re.I),
    re.compile(
        r'^([A-Z][a-zA-Z0-9\s&\-]+?)\s+layoffs?\s+\d{4}:', re.I
    ),
]

COMPANY_ALIASES = {
    "Google Cloud": "Google",
    "Meta Platforms": "Meta",
    "Oracle (ORCL)": "Oracle",
    "Visa Set": "Visa",
    "Payments giant Visa": "Visa",
    "Payment processor Visa": "Visa",
    "Payments processor Visa": "Visa",
    "Payment firm Visa": "Visa",
    "Payments firm Visa": "Visa",
    "T-Mobile US": "T-Mobile",
    "Monday.com": "monday.com",
    "Monday": "monday.com",
}


# ── Helpers ───────────────────────────────────────────────────────────────

def fetch_rss(url):
    """Fetch RSS 2.0 XML from Google News. Returns list of item dicts."""
    items = []
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        for item in root.iter('item'):
            title_el = item.find('title')
            link_el = item.find('link')
            pub_el = item.find('pubDate')
            src_el = item.find('source')
            source = src_el.text.strip() if src_el is not None and src_el.text else ''
            items.append({
                'title': title_el.text.strip() if title_el is not None and title_el.text else '',
                'link': link_el.text.strip() if link_el is not None and link_el.text else '',
                'pubDate': pub_el.text.strip() if pub_el is not None and pub_el.text else '',
                'source': source,
            })
    except ET.ParseError:
        print(f"  XML parse error — might be Atom format, not RSS 2.0")
    except Exception as e:
        print(f"  RSS fetch error: {e}")
    return items


def parse_pubdate(pub_str):
    """Parse RSS 2.0 pubDate format: 'Sat, 30 May 2026 04:45:06 GMT'."""
    if not pub_str:
        return None
    try:
        dt = datetime.strptime(pub_str, '%a, %d %b %Y %H:%M:%S %Z')
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(pub_str)
    except Exception:
        return None


def normalize_company(name):
    return COMPANY_ALIASES.get(name.strip(), name.strip())


def extract_jobs_number(title):
    """Extract a job count or percentage from a headline."""
    # Pattern: "N U.S./UK/etc. Jobs" — abbreviated country between number and noun
    m = re.search(
        r'([\d,]+)\s+(?:U\.?S\.?|UK|US|India|China|Japan|global|worldwide)?\s*'
        r'(?:jobs?|workers?|employees?|staff(?:ers?)?|workforce|roles|positions?|people)',
        title, re.I
    )
    if m:
        return int(m.group(1).replace(',', ''))
    m = re.search(
        r'([\d,]+)\s*(?:jobs?|workers?|employees?|staff(?:ers?)?|workforce|'
        r'roles|positions?|people)', title, re.I
    )
    if m:
        return int(m.group(1).replace(',', ''))
    # "N+" counts ("200+ roles") — strip the plus, treat as N
    m = re.search(
        r'([\d,]+)\s*\+\s*(?:jobs?|workers?|employees?|staff(?:ers?)?|workforce|'
        r'roles|positions?|people)', title, re.I
    )
    if m:
        return int(m.group(1).replace(',', ''))
    m = re.search(r'([\d,]+)%', title)
    if m:
        return m.group(1) + '%'
    return None


def is_ai_driven(title):
    return bool(re.search(
        r'\b(AI|artificial intelligence|automation|AI-driven|AI pivot|'
        r'AI shift|AI restructuring)\b', title, re.I
    ))


def source_score(title):
    for name, rank in SOURCE_RANK.items():
        if name.lower() in title.lower():
            return rank
    return 1


def consolidate(entries):
    """From multiple entries for the same company+quarter, pick the best one."""
    def key_fn(c):
        return (c['jobs_num'], c['source_score'])
    return max(entries, key=key_fn)


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    print(f"HERMES_SESSION_USER_ID={UID}")
    print("=" * 50)
    print(f"AI Job Loss Tracker — {datetime.now(timezone.utc).isoformat()}")
    print(f"Quarter: {CURRENT_Q}  |  Cutoff: {CUTOFF.isoformat()}")

    # 1. Fetch RSS
    all_items = []
    for locale, url in RSS_FEEDS:
        print(f"\nFetching {locale} RSS ...", end=" ")
        sys.stdout.flush()
        items = fetch_rss(url)
        print(f"{len(items)} items")
        all_items.extend(items)

    print(f"\nTotal items: {len(all_items)}")

    # 2. 48h filter
    candidates = []
    for item in all_items:
        pub_dt = parse_pubdate(item['pubDate'])
        if pub_dt is None:
            continue
        if pub_dt < CUTOFF:
            continue
        candidates.append(item)

    print(f"After 48h filter: {len(candidates)} items")

    # 3. Extract by company pattern
    raw_entries = []
    for item in candidates:
        title = item['title'].strip()
        if COUNTRY_SKIP.search(title):
            continue
        if SKIP_PROGRAMS.search(title):
            continue
        if SKIP_TRACKER.search(title):
            continue
        if SKIP_FORECAST.search(title):
            print(f"    SKIP (financial forecast, not jobs): {title[:100]}")
            continue
        if GENERIC_DESCRIPTOR_SKIP.search(title):
            print(f"    SKIP (generic descriptor): {title[:100]}")
            continue

        # Skip "AI" as a company — the technology, not a company name
        if re.match(r'^AI\s+(?:to cut|to slash|to lay off|cuts|slashes|lays off|dumps)\s+', title, re.I):
            print(f"    SKIP (AI-as-technology): {title[:100]}")
            continue

        # "Tech/Software/Cloud/AI/Global Layoffs 2026: ..." — generic roundup headers,
        # no company anchor at start (e.g. Goodreturns "Tech Layoffs 2026: Over 200 Job
        # Cuts Hit Apple Siri..."). Would otherwise capture "Tech" as a company.
        if re.match(r'^(Tech|Software|Cloud|AI|Global|Company|Startup)\s+Layoffs?(?:\s+\d{4})?:', title, re.I):
            print(f"    SKIP (generic layoffs header): {title[:100]}")
            continue

        company = None
        for pat in COMPANY_PATTERNS:
            m = pat.search(title)
            if m:
                company = normalize_company(m.group(1).strip())
                break

        if company is None:
            continue

        jobs_raw = extract_jobs_number(title)
        raw_entries.append({
            'company': company,
            'quarter': CURRENT_Q,
            'jobs_raw': jobs_raw,
            'jobs_num': jobs_raw if isinstance(jobs_raw, int) else 0,
            'ai_driven': 'Yes' if is_ai_driven(title) else 'Partial',
            'link': item['link'],
            'pub_date': item['pubDate'],
            'headline': title,
            'source': item.get('source', ''),
            'source_score': source_score(title),
        })

    # 4. Consolidate
    groups = {}
    for e in raw_entries:
        key = f"{e['company']}|{e['quarter']}"
        groups.setdefault(key, []).append(e)

    print(f"\nUnique company+quarter keys found: {len(groups)}")
    best_entries = []
    for key, entries in sorted(groups.items()):
        best = consolidate(entries)
        best_entries.append(best)
        print(f"  {key} — best: {best['jobs_raw']} jobs ({best['source']})")

    if not best_entries:
        print("\nNo AI-driven job loss announcements found in the last 48 hours.")
        return False

    # 5. Read sheet & dedup
    print("\nConnecting to Sheets...")
    try:
        sheets = build_service('sheets', 'v4', service_name='google-draas')
        meta = sheets.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
        tab_name = meta['sheets'][0]['properties']['title']
        sheet_id_num = meta['sheets'][0]['properties']['sheetId']
        print(f"Tab: '{tab_name}' (sheetId: {sheet_id_num})")
    except Exception as e:
        if 'ACCESS_TOKEN_SCOPE_INSUFFICIENT' in str(e):
            print("ERROR: Token missing spreadsheets scope — user must re-authorize")
        else:
            print(f"ERROR: {e}")
        return False

    result = sheets.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=f'{tab_name}!A1:J'
    ).execute()
    existing = result.get('values', [])
    print(f"Existing rows: {len(existing)}")

    dedup = {}
    for i, row in enumerate(existing[1:], start=2):
        if len(row) >= 4:
            co = row[1].strip() if len(row) > 1 else ''
            q = row[2].strip() if len(row) > 2 else ''
            k = f"{co}|{q}"
            try:
                v = row[3].replace(',', '').replace('~', '').split()[0]
                j = int(v) if v.isdigit() else 0
            except (ValueError, IndexError):
                j = 0
            dedup[k] = (j, i)

    new_entries = []
    updates = []
    for entry in best_entries:
        key = f"{entry['company']}|{entry['quarter']}"
        if key in dedup:
            existing_jobs, row_idx = dedup[key]
            if entry['jobs_num'] > existing_jobs:
                updates.append((row_idx, entry))
                print(f"  UPDATE: {key} — {entry['jobs_raw']} > {existing_jobs}")
            else:
                print(f"  SKIP (dup): {key} — {entry['jobs_raw']} ≤ {existing_jobs}")
        else:
            new_entries.append(entry)
            dedup[key] = (entry['jobs_num'], len(existing) + len(new_entries))
            print(f"  NEW: {key} — {entry['jobs_raw']}")

    print(f"\nNew: {len(new_entries)}  |  Updates: {len(updates)}")

    # 6. Write new rows
    if new_entries:
        next_row = len(existing) + 1
        for idx, entry in enumerate(new_entries):
            row_num = next_row + idx
            pub_dt = parse_pubdate(entry['pub_date'])
            date_str = pub_dt.strftime('%Y-%m-%d') if pub_dt else datetime.now().strftime('%Y-%m-%d')
            row = [
                str(row_num),
                entry['company'],
                entry['quarter'],
                str(entry['jobs_raw']) if entry['jobs_raw'] is not None else '',
                entry['ai_driven'],
                entry['link'],
                date_str,
                entry['headline'],
                f"Source: {entry['source']}",
                datetime.now().strftime('%Y-%m-%d %H:%M IST'),
            ]
            col = chr(64 + NUM_COLS)
            sheets.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"{tab_name}!A{row_num}:{col}{row_num}",
                valueInputOption='RAW',
                body={'values': [row]}
            ).execute()
            print(f"  Wrote row {row_num}: {entry['company']}|{entry['quarter']} — {entry['jobs_raw']}")

    # 7. Apply updates (higher number found)
    for row_idx, entry in updates:
        sheets.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"{tab_name}!D{row_idx}",
            valueInputOption='RAW', body={'values': [[str(entry['jobs_raw'])]]}
        ).execute()
        sheets.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"{tab_name}!F{row_idx}",
            valueInputOption='RAW', body={'values': [[entry['link']]]}
        ).execute()
        sheets.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"{tab_name}!H{row_idx}",
            valueInputOption='RAW', body={'values': [[entry['headline']]]}
        ).execute()
        sheets.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"{tab_name}!I{row_idx}",
            valueInputOption='RAW',
            body={'values': [[f"Updated: higher number {entry['jobs_raw']} from {entry['source']}"]]}
        ).execute()
        sheets.spreadsheets().values().update(
            spreadsheetId=SHEET_ID, range=f"{tab_name}!J{row_idx}",
            valueInputOption='RAW',
            body={'values': [[datetime.now().strftime('%Y-%m-%d %H:%M IST')]]}
        ).execute()
        print(f"  Updated row {row_idx}: {entry['company']} → {entry['jobs_raw']}")

    return True


if __name__ == '__main__':
    had_new = main()
    print()
    print("=" * 50)
    if not had_new:
        print("No new AI-driven job loss announcements in the last 48 hours.")
