#!/usr/bin/env python3
"""Daily not-spam whitelist check for ndr@draas.com (google-draas).

Reads whitelist rules from the DRAAS Not-Spam spreadsheet, fetches the SPAM
folder (max 200), applies the rules, and moves matching messages to INBOX.
Never deletes anything.

PROVEN IN PRODUCTION Aug 2026. RUN VIA TERMINAL (trusted process), NOT the
execute_code sandbox: the sandbox's hermes_tools stub has no gws_fetch_token
import, so tools.gws_auth.load_credentials() raises ImportError there.
Terminal has GWS_VAULT_SOCKET=/run/gws-vault/vault.sock and works.

Usage:
    cd /opt/hermes && python3 /opt/data/not_spam_check.py
"""
import sys, re
sys.path.insert(0, '/opt/hermes')

from tools.gws_auth import build_service

SPREADSHEET_ID = '1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0'
SERVICE = 'google-draas'

gmail = build_service('gmail', 'v1', service_name=SERVICE)
sheets = build_service('sheets', 'v4', service_name=SERVICE)

# ---------- 1. Read whitelist rules ----------
res = sheets.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID, range='Whitelist!A:I').execute()
rows = res.get('values', [])
data_rows = rows[1:] if len(rows) > 1 else []  # skip header

# Column C = From Email / Domain (index 2), E = Subject Keywords (index 4),
# G = Rule Type (index 6) -- 0-based from A=0.
rules = []
for r in data_rows:
    if len(r) < 7:
        continue
    rule_type = (r[6] or '').strip().lower()
    from_field = (r[2] or '').strip()
    subject_kw = (r[4] or '').strip()
    if not from_field and not subject_kw:
        continue
    rules.append({'type': rule_type, 'from': from_field, 'keywords': subject_kw})

print(f"Loaded {len(rules)} whitelist rules")

# ---------- 2. Fetch SPAM ----------
spam_ids = []
page_token = None
while True:
    resp = gmail.users().messages().list(
        userId='me', labelIds=['SPAM'], maxResults=200, pageToken=page_token
    ).execute()
    batch = resp.get('messages', [])
    spam_ids.extend(m['id'] for m in batch)
    page_token = resp.get('nextPageToken')
    if not page_token or len(spam_ids) >= 200:
        break
spam_ids = spam_ids[:200]
print(f"Spam messages fetched: {len(spam_ids)}")

# ---------- 3. Fetch metadata for each ----------
def parse_sender(from_header):
    """Extract bare email from a From header like 'Name <a@b.com>'."""
    if not from_header:
        return ''
    m = re.search(r'<([^<>]+)>', from_header)
    if m:
        return m.group(1).strip().lower()
    return from_header.strip().lower()

def sender_domain(email):
    if '@' in email:
        return email.split('@', 1)[1].lower()
    return email.lower()

def normalize_domain(field):
    """domain_from column C may be '@draas.com', 'draas.com', or 'sub.draas.com'."""
    return field.strip().lower().lstrip('@')

def subject_contains(subject, keywords):
    if not keywords or not subject:
        return False
    subj = subject.lower()
    kws = [k.strip().lower() for k in keywords.split(',') if k.strip()]
    return any(k in subj for k in kws)

def match_rule(msg_info, rule):
    rt = rule['type']
    sender = msg_info['sender']
    subject = msg_info['subject']
    if rt == 'exact_from':
        return sender == rule['from'].strip().lower()
    if rt == 'domain_from':
        dom = normalize_domain(rule['from'])
        if not dom:
            return False
        return sender_domain(sender).endswith(dom) or sender.endswith('@' + dom)
    if rt == 'subject_contains':
        return subject_contains(subject, rule['keywords'])
    if rt == 'combined':
        dom = normalize_domain(rule['from'])
        dom_ok = bool(dom) and (sender_domain(sender).endswith(dom) or sender.endswith('@' + dom))
        kw_ok = subject_contains(subject, rule['keywords'])
        return dom_ok and kw_ok
    return False

# Fetch metadata in batches of 100
messages = []
for i in range(0, len(spam_ids), 100):
    batch_ids = spam_ids[i:i+100]
    for mid in batch_ids:
        try:
            msg = gmail.users().messages().get(
                userId='me', id=mid, format='metadata',
                metadataHeaders=['From', 'Subject', 'To']
            ).execute()
            hdrs = {h['name'].lower(): h['value'] for h in msg.get('payload', {}).get('headers', [])}
            messages.append({
                'id': mid,
                'sender_raw': hdrs.get('from', ''),
                'sender': parse_sender(hdrs.get('from', '')),
                'subject': hdrs.get('subject', '(no subject)'),
                'to': hdrs.get('to', ''),
            })
        except Exception as e:
            print(f"ERROR fetching msg {mid}: {e}")

print(f"Metadata fetched for {len(messages)} messages")

# ---------- 4. Apply rules ----------
def is_internal(sender):
    d = sender_domain(sender)
    return d == 'draas.com' or d.endswith('.draas.com')

moved = []
errors = []
for m in messages:
    sender = m['sender']
    reasons = []
    if not sender:
        continue
    if is_internal(sender):
        reasons.append('internal @draas.com catch-all')
    else:
        for rule in rules:
            if match_rule(m, rule):
                reasons.append(f"{rule['type']}:{rule['from']}")
    if reasons:
        try:
            gmail.users().messages().modify(
                userId='me', id=m['id'],
                body={'removeLabelIds': ['SPAM'], 'addLabelIds': ['INBOX']}
            ).execute()
            moved.append({'id': m['id'], 'sender': m['sender_raw'], 'subject': m['subject'], 'reasons': reasons})
        except Exception as e:
            errors.append(f"modify failed for {m['id']} ({sender}): {e}")

# ---------- 5. Report ----------
print("\n==================== SUMMARY ====================")
print(f"Spam checked: {len(messages)}")
print(f"Moved to inbox: {len(moved)}")
print(f"Errors: {len(errors)}")
print("\n--- Moved messages ---")
for mv in moved:
    print(f"- {mv['sender']} | {mv['subject'][:100]} | {', '.join(mv['reasons'])}")
if errors:
    print("\n--- Errors ---")
    for e in errors:
        print(f"- {e}")
