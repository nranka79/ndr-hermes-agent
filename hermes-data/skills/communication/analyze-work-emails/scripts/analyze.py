#!/opt/hermes/.venv/bin/python3
"""Analyze work emails from the last N days across ndr@draas.com and ndr@ahfl.in.

Usage: /opt/hermes/.venv/bin/python3 analyze.py [days]

Categorizes by: FII (For Info), NEEDS RESPONSE, AWAITING RESPONSE, NEEDS CLARIFICATION
Priority: CRITICAL / HIGH / MEDIUM / NORMAL
"""
import sys, os, re, json
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from collections import defaultdict

# Ensure hermes libs are importable
sys.path.insert(0, '/opt/hermes')

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)
since = (datetime.now(timezone.utc) - timedelta(days=DAYS)).strftime('%Y/%m/%d')

NON_WORK_DOMAINS = [
    "thedailyupside.com", "yourstory.com", "economictimes.com",
    "mckinsey.com", "liasesforas.com", "gritcap.io", "instamart.in",
    "plusportals.com", "substack.com", "beehiiv.com", "codepen.io",
    "the-captable.com", "a360.com", "danmartell.com", "thesequence.com",
    "medium.com", "premiuminfo.fool.com", "turingpost.com",
    "mail.beehiiv.com", "su.org", "judge.me", "quora.com",
    "fool.com", "gripinvest.in", "hsbc.co.in", "booking.com",
    "newsletter", "ifttt.com", "bangaloreinternationalcentre.org",
    "aditi.edu.in", "etrealty.com", "noreply", "no-reply",
    "donotreply", "mailer", "marketing", "events@google",
    "linkedin.com", "twitter.com", "facebookmail.com",
    "zoho.com", "hsbc", "icici", "info@blinkit.com",
]


def build_service(service_name):
    from tools.gws_auth import build_service as _bs
    try:
        return _bs('gmail', 'v1', service_name=service_name)
    except Exception as e:
        print(f'WARN: no token for {service_name}: {e}', file=sys.stderr)
        return None


def is_work_email(frm):
    frm_lower = frm.lower()
    return not any(d in frm_lower for d in NON_WORK_DOMAINS)


def parse_sender(fr):
    m = re.match(r'^"?([^"<]*)"?\s*<([^>]+)>', fr)
    if m:
        return m.group(1).strip() or m.group(2), m.group(2)
    return fr, fr


def classify(subj, snippet, labels):
    sl = subj.lower()
    sn = snippet.lower()
    if 'SENT' in labels:
        return 'NORMAL', 'AWAITING RESPONSE'
    pri = 'NORMAL'
    if any(k in sl or k in sn for k in ['urgent', 'asap', 'critical', 'immediately', 'deadline']):
        pri = 'CRITICAL'
    elif any(k in sl or k in sn for k in ['request', 'approval', 'pending', 'follow up', 'reminder', 'kindly', 'please review', 'action required', 'needed from you']):
        pri = 'HIGH'
    elif any(k in sl or k in sn for k in ['re:', 'fwd:', 'payment', 'meeting', 'report', 'legal', 'agreement', 'invoice']):
        pri = 'MEDIUM'
    act = 'FII'
    if any(k in sl or k in sn for k in ['please', 'kindly', 'request you', 'can you', 'could you', 'needed', 'required', 'let me know', 'awaiting', 'approval needed', 'confirm', 'your inputs', 'your feedback', 'review and']):
        act = 'NEEDS RESPONSE'
    elif any(k in sl or k in sn for k in ['?', 'clarify', 'clarity', 'not sure', 'check', 'please advise', 'any update']):
        act = 'NEEDS CLARIFICATION'
    return pri, act


def skip_kelsa_or_balance(subj, snippet):
    """Skip Kelsa sign-in/out and daily bank balance noise."""
    sl = subj.lower()
    return any(k in sl for k in [
        'please sign in', 'please sign out', 'account balance - daily',
    ])


def fetch_from_account(svc, label):
    """Fetch recent work emails from one Gmail account."""
    results = []
    try:
        resp = svc.users().messages().list(userId='me', q=f'after:{since}', maxResults=100).execute()
    except Exception as e:
        print(f'  ERROR searching {label}: {e}', file=sys.stderr)
        return results
    msgs = resp.get('messages', [])
    for m in msgs:
        try:
            detail = svc.users().messages().get(userId='me', id=m['id']).execute()
        except Exception as e:
            print(f'  ERROR fetching msg {m["id"]}: {e}', file=sys.stderr)
            continue
        headers = {h['name'].lower(): h['value'] for h in detail.get('payload', {}).get('headers', [])}
        subject = headers.get('subject', '')
        fr = headers.get('from', '')
        date_str = headers.get('date', '')
        snippet = detail.get('snippet', '')[:300]
        labels = detail.get('labelIds', [])
        # Date filter
        dt = None
        try:
            dt = parsedate_to_datetime(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except Exception:
            pass
        if dt and dt < cutoff:
            continue
        # Skip newsletters
        if not is_work_email(fr):
            continue
        # Skip Kelsa / bank balance noise
        if skip_kelsa_or_balance(subject, snippet):
            continue
        results.append({
            'account': label, 'subject': subject, 'from': fr,
            'date': date_str, 'snippet': snippet, 'labels': labels,
            'is_unread': 'UNREAD' in labels,
        })
    return results


# === MAIN ===
all_work = []
for svc_name, label in [('google-draas', 'ndr@draas.com'), ('google-ahfl', 'ndr@ahfl.in')]:
    svc = build_service(svc_name)
    if svc:
        all_work.extend(fetch_from_account(svc, label))

# Sort newest first
all_work.sort(key=lambda x: x['date'], reverse=True)

# Classify and group
groups = defaultdict(list)
for e in all_work:
    pri, act = classify(e['subject'], e['snippet'], e['labels'])
    sname, semail = parse_sender(e['from'])
    entry = (
        f"\n[{pri}] [{act}] {e['account']}{' ** UNREAD **' if e['is_unread'] else ''}\n"
        f"  From: {sname} <{semail}>\n"
        f"  Subj: {e['subject'][:120]}\n"
        f"  Date: {e['date'][:35]}\n"
        f"  {e['snippet'][:250]}"
    )
    groups[act if act in ['NEEDS RESPONSE', 'NEEDS CLARIFICATION', 'AWAITING RESPONSE', 'FII'] else 'FII'].append((pri, entry))

# Sort by priority within groups
pri_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'NORMAL': 3}
for g in groups:
    groups[g].sort(key=lambda x: pri_order.get(x[0], 99))

# Output
total = sum(len(v) for v in groups.values())
print(f"{'='*70}")
print(f"WORK EMAIL ANALYSIS - Last {DAYS} Days")
print(f"{'='*70}")
for gn in ['NEEDS RESPONSE', 'NEEDS CLARIFICATION', 'AWAITING RESPONSE', 'FII']:
    items = groups.get(gn, [])
    if not items:
        continue
    print(f"\n{'─'*70}")
    print(f" {gn} ({len(items)})")
    print(f"{'─'*70}")
    for pri, entry in items:
        print(entry)
print(f"\n{'='*70}")
print(f"Total: {total} work emails")
print(f"{'='*70}")
