#!/usr/bin/env python3
"""Weekly work-email analysis (thread-level, inbox+sent, noise-filtered).

Usage: /opt/hermes/.venv/bin/python3 .../scripts/weekly_analysis.py [N days]
Default N=7. Run with the Hermes venv python (system python is PEP 668 locked).

Pattern verified 17 Aug 2026: ndr@draas.com, 7 days, inbox+sent
= ~450 unique messages -> ~220 after noise filter, 165 threads.
Direct Gmail API with list() pagination is fast enough at this volume
(no bridge, no window splits needed below ~600 msgs/window).

Output shape (stdout): AWAITING RESPONSE / NEEDS RESPONSE / INFO / NOISE.
Redirect stdout to a file if you want to read just the analysis sections —
the NOISE dump can run long.
"""
import json, re, sys
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from collections import defaultdict

sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 7
SINCE = (datetime.now() - timedelta(days=DAYS)).strftime('%Y/%m/%d')
ACCOUNTS = [
    ('google-draas', 'ndr@draas.com'),
    ('google-ahfl', 'ndr@ahfl.in'),
]

# Noise: auto-generated / marketing — skip entirely.
# Weekly-run verified list (Aug 2026). Add new offenders here, not in prose.
NOISE_DOMAINS = [
    'kelsa.io', 'royalsundaram.in', 'smarterdharma.com', 'tcsion.com',
    'apify.com', 'ihcltata.com', 'goindigo.in', 'mapmygenome.in',
    'entrackr.com', 'credai.org', 'openrouter.ai', 'adobe.com',
    'communication.microsoft.com', 'canmoney.in', 'justdial.com',
    'obo-bettermann', 'blackbox', 'inflow', 'astral', 'sonel', 'dell',
    'kotak.bank.in', 'hdfcbank.bank.in', 'indusind.com', 'nesl.co.in',
    'flamebackcapital.com', 'liasesforas.com', 'imagesbazaar.com',
    'ishraeconnect.in', 'refcold', 'yatra', 'swiggy.in', 'shine.com',
    'naukri.com', 'internshala.com', 'letsventure', 'lvxventures.com',
]
NOISE_SUBJECTS = [
    'attendance report', 'daily attendance', 'your opinion matters',
    'please sign', 'sign in/out', 'otp', 'one time password',
    'upi txn', 'recurring debit', 'transaction successful',
    'account balance', 'terms of use', 'pre-approved', 'tax payments',
    'safe banking', 'fraud', 'credit card', 'netflix', 'amazon',
    're-kyc', 'periodic kyc', 'kyc update', 'nominee', 'e-mandate',
    'fixed deposit', 'services suspended', 'downtime notification',
    'digital general file', 'ipo', 'gst invoice', 'account statement',
    'weekly account statement', 'security alert', 'storage limit',
    'terms of service', 'privacy policy', 'works in your inbox',
]

def is_noise(m):
    subj = (m.get('subject') or '').lower()
    frm = (m.get('from') or '').lower()
    em = re.findall(r'[\w.+-]+@[\w.-]+', frm)
    for e in em:
        for d in NOISE_DOMAINS:
            if d in e:
                return True
    for s in NOISE_SUBJECTS:
        if s in subj:
            return True
    return False

def fetch(service, query, maxr=500):
    try:
        results = []
        resp = service.users().messages().list(userId='me', q=query, maxResults=maxr).execute()
        results.extend(resp.get('messages', []))
        while 'nextPageToken' in resp:
            resp = service.users().messages().list(userId='me', q=query, maxResults=maxr,
                                                   pageToken=resp['nextPageToken']).execute()
            results.extend(resp.get('messages', []))
        return results
    except Exception as e:
        print(f"FETCH_ERROR {query}: {e}", file=sys.stderr)
        return []

def get_meta(service, msg_id):
    try:
        msg = service.users().messages().get(userId='me', id=msg_id,
                format='metadata', metadataHeaders=['From','To','Subject','Date']).execute()
        h = {x['name'].lower(): x['value'] for x in msg['payload']['headers']}
        return {
            'id': msg['id'], 'threadId': msg['threadId'],
            'from': h.get('from',''), 'to': h.get('to',''),
            'subject': h.get('subject',''), 'date': h.get('date',''),
            'labels': msg.get('labelIds', []),
        }
    except Exception as e:
        print(f"GET_ERROR {msg_id}: {e}", file=sys.stderr)
        return None

msgs = []
for svc, acct in ACCOUNTS:
    try:
        service = build_service('gmail', 'v1', service_name=svc)
        ids = []
        for q in (f'in:inbox after:{SINCE}', f'in:sent after:{SINCE}'):
            ids += fetch(service, q)
        seen = set()
        for item in ids:
            if item['id'] not in seen:
                seen.add(item['id'])
                m = get_meta(service, item['id'])
                if m:
                    m['_account'] = acct
                    msgs.append(m)
        print(f"ACCOUNT_OK {acct}: {len(seen)} unique", file=sys.stderr)
    except Exception as e:
        print(f"ACCOUNT_FAIL {acct}: {e}", file=sys.stderr)
        # invalid_grant = token dead even if gws_resolve_account said has_token:true

real = [m for m in msgs if not is_noise(m)]

threads = defaultdict(list)
for m in real:
    try:
        dt = parsedate_to_datetime(m['date'])
    except Exception:
        dt = None
    m['_dt'] = dt
    threads[(m['_account'], m['threadId'])].append(m)

ASK_WORDS = ['please', 'kindly', 'could you', 'can you', 'request you', 'let me know',
             'awaiting', 'needed from you', 'your inputs', 'your feedback', 'approval',
             'confirm', 'review and', 'would you', 'are you', 'do you', 'have you',
             'need your', 'share the', 'send me', 'pls', 'revert', 'at the earliest',
             'escalate', 'asked', 'requested', 'pending', 'action required', 'fwd:',
             'fw:', 'update me', 'need', 'required', 'deadline', 'due', 'clarify',
             'any update', 'check', 'discrep', 'not sure', 'advise']

def classify(thread_msgs):
    thread_msgs.sort(key=lambda x: x['_dt'] or datetime.min)
    last = thread_msgs[-1]
    is_sent = 'SENT' in last.get('labels', [])
    text = (f"{last.get('subject','')} {last.get('snippet','')}").lower()
    asks = [w for w in ASK_WORDS if w in text]
    return last, is_sent, asks

cat = {'AWAITING': [], 'NEEDS_RESPONSE': [], 'INFO': []}
for key, tmsgs in threads.items():
    last, is_sent, asks = classify(tmsgs)
    if is_sent:
        other = last.get('to','')
        days = (datetime.now() - (last['_dt'].replace(tzinfo=None) if last['_dt'] else datetime.now())).days
        cat['AWAITING'].append((last, other, days, len(tmsgs), asks))
    elif asks:
        cat['NEEDS_RESPONSE'].append((last, asks, len(tmsgs)))
    else:
        cat['INFO'].append((last, len(tmsgs)))

cat['AWAITING'].sort(key=lambda x: x[2], reverse=True)
def prio(m):
    t = (m.get('subject','') + ' ' + m.get('from','')).lower()
    if any(w in t for w in ['urgent','asap','final','deadline','expiry','notice','rera','complianc']): return 0
    if any(w in t for w in ['approval','pending','payment','invoice','legal','agreement','meeting','confirm']): return 1
    return 2
cat['NEEDS_RESPONSE'].sort(key=lambda x: prio(x[0]))
cat['INFO'].sort(key=lambda x: prio(x[0]))

def fmt_date(d):
    return d.strftime('%d %b') if d else '?'

print("="*70)
print(f"WORK EMAIL THREAD ANALYSIS — last {DAYS} days (from {SINCE})")
print("="*70)
print(f"total fetched: {len(msgs)}, after noise filter: {len(real)} in {len(threads)} threads")

print(f"\n### AWAITING RESPONSE ({len(cat['AWAITING'])}) — people who owe YOU (you sent last)")
for last, other, days, n, asks in cat['AWAITING']:
    tag = 'chase' if days >= 3 else f'{days}d'
    print(f"- [{tag}] {last.get('subject','')[:90]}")
    print(f"    to: {other[:110]} | last: {fmt_date(last['_dt'])} ({n} msgs)")

print(f"\n### NEEDS RESPONSE ({len(cat['NEEDS_RESPONSE'])}) — people waiting on YOU")
for last, asks, n in cat['NEEDS_RESPONSE']:
    print(f"- [{fmt_date(last['_dt'])}] {last.get('from','')[:50]} | {last.get('subject','')[:90]}")
    print(f"    asks: {', '.join(asks[:5])} | {n} msgs")

print(f"\n### INFO / WATCH ({len(cat['INFO'])})")
for last, n in cat['INFO']:
    print(f"- [{fmt_date(last['_dt'])}] {last.get('from','')[:40]} | {last.get('subject','')[:95]}")

print("\n### NOISE SKIPPED (sample)")
for m in msgs[:200]:
    if is_noise(m):
        print(f"- {m.get('from','')[:40]} | {m.get('subject','')[:80]}")