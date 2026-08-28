#!/opt/hermes/.venv/bin/python3
"""
Email Thread Summary Script
Usage: python3 thread_summaries.py <service_name> "<subject keyword>" ["more queries"...]

Example: python3 thread_summaries.py google-draas "RANKA HOLDINGS Mou" "Oasis Drawings"

Finds each thread by subject search (falls back to any keyword match), then
prints every message in the thread: date, from, subject, first ~350 chars of
the decoded body. Use this whenever the user asks for "a summary from the
entire conversation thread" or wants to understand context behind a triage item.
"""

import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
import base64, re

SERVICE = sys.argv[1] if len(sys.argv) > 1 else 'google-draas'
QUERIES = sys.argv[2:]
if not QUERIES:
    print("Usage: thread_summaries.py <service_name> \"<subject keyword>\" [...]")
    sys.exit(1)

service = build_service('gmail', 'v1', service_name=SERVICE)
profile = service.users().getProfile(userId='me').execute()
print(f"Account: {profile.get('emailAddress', '?')}\n")


def get_header(msg, name, default='?'):
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    return headers.get(name, default)


def decode_body(payload):
    if 'parts' in payload:
        text = ''
        for part in payload['parts']:
            mime = part.get('mimeType', '')
            if mime == 'text/plain' and 'data' in part.get('body', {}):
                text += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
            elif 'parts' in part:
                text += decode_body(part)
            elif mime.startswith('text/') and 'data' in part.get('body', {}):
                text += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
        return text
    elif 'body' in payload and 'data' in payload['body']:
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
    return '(no text)'


def clean(text, n=350):
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:n]


def find_thread(q):
    res = service.users().messages().list(userId='me', q=q, maxResults=3).execute()
    msgs = res.get('messages', [])
    if not msgs:
        print(f"  !! no results for: {q}\n")
        return
    tid = msgs[0]['threadId']
    thread = service.users().threads().get(userId='me', id=tid, format='full').execute()
    tmsgs = thread['messages']
    print(f"=== {q}")
    print(f"    thread: {len(tmsgs)} msgs")
    for m in tmsgs:
        date = get_header(m, 'Date', '?')
        frm = get_header(m, 'From', '?')
        subj = get_header(m, 'Subject', '?')
        body = clean(decode_body(m['payload']))
        print(f"  [{date[:16]}] {frm[:45]}")
        print(f"      S: {subj[:90]}")
        print(f"      B: {body}")
    print()


for q in QUERIES:
    try:
        find_thread(q)
    except Exception as e:
        print(f"  !! error for {q}: {e}\n")
