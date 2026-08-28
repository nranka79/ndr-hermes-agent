#!/usr/bin/env python3
"""Daily not-spam check for DRAAS Gmail (cron job 'not-spam-whitelist').

Reads whitelist rules from a Google Sheet (tab Whitelist, cols A-I), scans the
SPAM folder (max 200), applies rule types (exact_from / domain_from /
subject_contains / combined / @draas.com catch-all), and MOVES matches from
SPAM to INBOX via the Gmail modify API. Never deletes spam.

Credential access: gws-vault daemon via tools.gws_auth.build_service with
service_name='google-draas' (ndr@draas.com). The flat gws_token.json path that
cron specs reference does NOT exist — do not hunt for it.

Run:  cd /opt/hermes && python3 /opt/data/not_spam_check.py
(or wherever this file lives; /opt/hermes must be on sys.path for tools.gws_auth)

Verified 2026-08-06: 33 spam checked, 1 moved (nach.alerts@kotak.bank.in),
0 errors. Post-run verification: re-query subject, confirm labelIds contain
INBOX and not SPAM.
"""
import sys, re, traceback
sys.path.insert(0, '/opt/hermes')

from tools.gws_auth import build_service

SHEET_ID = '1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0'
SPREADSHEET_RANGE = 'Whitelist!A:I'
MAX_SPAM = 200

# ---------- 1. Build services ----------
gmail = build_service('gmail', 'v1', service_name='google-draas')
sheets = build_service('sheets', 'v4', service_name='google-draas')

# ---------- 2. Read whitelist rules ----------
res = sheets.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=SPREADSHEET_RANGE).execute()
rows = res.get('values', [])
rules = []
for r in rows[1:]:
    if len(r) < 7:
        continue
    rec = {
        'num': (r[0] if len(r) > 0 else '').strip(),
        'category': (r[1] if len(r) > 1 else '').strip(),
        'from': (r[2] if len(r) > 2 else '').strip(),
        'to': (r[3] if len(r) > 3 else '').strip(),
        'subject_kw': (r[4] if len(r) > 4 else '').strip(),
        'desc': (r[5] if len(r) > 5 else '').strip(),
        'rule_type': (r[6] if len(r) > 6 else '').strip().lower(),
        'date_added': (r[7] if len(r) > 7 else '').strip(),
    }
    if not rec['from']:
        continue
    rules.append(rec)
print(f"Whitelist: {len(rules)} rules loaded", flush=True)

def norm_domain(d):
    d = d.strip().lower().strip('@').rstrip('.')
    return d

def domain_matches(sender_email, rule_dom):
    """Boundary-aware: sdom == rd or sdom.endswith('.' + rd). 'jio.com' must NOT
    match 'fakejio.com' but MUST match 'emailer.jio.com'."""
    if not sender_email or '@' not in sender_email:
        return False
    sdom = sender_email.lower().rsplit('@', 1)[1].rstrip('.')
    rd = norm_domain(rule_dom)
    if not rd:
        return False
    return sdom == rd or sdom.endswith('.' + rd)

def subject_matches(subject, kw_text):
    if not kw_text:
        return False
    subj = (subject or '').lower()
    kws = [k.strip().lower() for k in re.split(r'[,/;]', kw_text) if k.strip()]
    return any(k in subj for k in kws)

def sender_email_of(hdrs):
    frm = ''
    for h in hdrs:
        if h.get('name') == 'From':
            frm = h.get('value', '')
            break
    m = re.search(r'[\w.+-]+@[\w.-]+', frm)
    return m.group(0) if m else frm.strip()

def get_header(hdrs, name):
    for h in hdrs:
        if h.get('name') == name:
            return h.get('value', '')
    return ''

def check_message(msg_id, hdrs):
    frm = sender_email_of(hdrs)
    subject = get_header(hdrs, 'Subject')
    for rule in rules:
        rt = rule['rule_type']
        if rt == 'exact_from':
            if frm.lower() == rule['from'].lower():
                return rule, f"exact_from match: {frm}"
        elif rt == 'domain_from':
            if domain_matches(frm, rule['from']):
                return rule, f"domain_from match: {frm} ∈ {rule['from']}"
        elif rt == 'subject_contains':
            if subject_matches(subject, rule['subject_kw']):
                return rule, f"subject_contains match: '{subject}' ∋ {rule['subject_kw']}"
        elif rt == 'combined':
            if domain_matches(frm, rule['from']) and subject_matches(subject, rule['subject_kw']):
                return rule, f"combined match: {frm} ∈ {rule['from']} AND subject ∋ {rule['subject_kw']}"
    # catch-all internal: sender domain @draas.com
    if domain_matches(frm, '@draas.com'):
        return {'category': 'Internal', 'from': '@draas.com', 'rule_type': 'catch-all'}, f"catch-all: {frm} ∈ @draas.com"
    return None, None

# ---------- 3. Fetch SPAM messages ----------
spam_ids = []
try:
    resp = gmail.users().messages().list(userId='me', labelIds=['SPAM'], maxResults=MAX_SPAM).execute()
    spam_ids = [m['id'] for m in resp.get('messages', [])]
    print(f"SPAM folder: {len(spam_ids)} messages found", flush=True)
except Exception as e:
    print(f"ERROR listing SPAM: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

# ---------- 4. Check each message ----------
moved = []
errors = []
checked = 0
for mid in spam_ids:
    try:
        msg = gmail.users().messages().get(
            userId='me', id=mid, format='metadata',
            metadataHeaders=['From', 'Subject', 'To', 'Date']
        ).execute()
        checked += 1
        hdrs = msg.get('payload', {}).get('headers', [])
        frm = sender_email_of(hdrs)
        subject = get_header(hdrs, 'Subject') or '(no subject)'
        rule, reason = check_message(mid, hdrs)
        if rule:
            moved.append({'id': mid, 'from': frm, 'subject': subject, 'rule': rule, 'reason': reason})
    except Exception as e:
        errors.append(f"msg {mid}: {e}")
        print(f"ERROR fetching msg {mid}: {e}", flush=True)

print(f"Checked: {checked}, Matches: {len(moved)}", flush=True)

# ---------- 5. Move matches ----------
moved_ok = []
for m in moved:
    try:
        gmail.users().messages().modify(
            userId='me', id=m['id'],
            body={'removeLabelIds': ['SPAM'], 'addLabelIds': ['INBOX']}
        ).execute()
        m['status'] = 'moved'
        moved_ok.append(m)
        print(f"MOVED {m['from']} | {m['subject'][:60]} | {m['rule'].get('category','')}/{m['rule'].get('rule_type','')}", flush=True)
    except Exception as e:
        m['status'] = 'error'
        errors.append(f"move {m['id']} ({m['from']}): {e}")
        print(f"ERROR moving {m['id']} ({m['from']}): {e}", flush=True)

# ---------- 6. Report ----------
print("\n===== SUMMARY =====", flush=True)
print(f"Emails checked in spam: {checked}", flush=True)
print(f"Emails moved to inbox: {len(moved_ok)}", flush=True)
print(f"Errors: {len(errors)}", flush=True)
for e in errors:
    print(f"  ERR: {e}", flush=True)
print("\n--- Moved senders/subjects ---", flush=True)
for m in moved_ok:
    print(f"  - {m['from']} | {m['subject']} | reason: {m['reason']}", flush=True)
