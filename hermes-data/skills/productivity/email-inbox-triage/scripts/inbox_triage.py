#!/opt/hermes/.venv/bin/python3
"""
Email Inbox Triage Script
Usage: python3 inbox_triage.py <service_name> <date_from>

Example: python3 inbox_triage.py google-draas 2026/07/22

Scans the specified Gmail account for messages since <date_from>,
categorizes them into:
  - Needs reply (someone wrote last, user owes response)
  - Follow-up due (user wrote last, awaiting reply)
  - Action items (invoices, approvals, deadlines)
  - FYI (notifications, CC'd, newsletters)

Outputs a clean categorized report to stdout.
"""

import sys
import os

sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

SERVICE_NAME = sys.argv[1] if len(sys.argv) > 1 else 'google-draas'
DATE_FROM = sys.argv[2] if len(sys.argv) > 2 else '2026/07/22'


def get_header(msg, name, default='?'):
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    return headers.get(name, default)


def trunc(s, n=100):
    return str(s)[:n]


# ---- Auth & resolve actual email ----
service = build_service('gmail', 'v1', service_name=SERVICE_NAME)
profile = service.users().getProfile(userId='me').execute()
USER_EMAIL = profile.get('emailAddress', '').lower()
print(f"Account: {profile.get('emailAddress', '?')}")
print(f"Using email for identity check: {USER_EMAIL}")


def is_from_user(from_addr):
    """Check if sender is the account owner (by email address, not vault key)."""
    return USER_EMAIL in from_addr.lower()


# Patterns to deprioritise as bulk/automated - checked against sender + subject
BULK_PATTERNS = {
    'sender_domain': [
        'liasesforas.com', 'entrackr.com', 'email.mckinsey.com',
        'bankalerts@', 'no-reply@', 'noreply@', 'donotreply@',
        'calendar-notification@google.com', 'plusportals.com',
        'messenger@plusportals', 'indusind_bank@', 'kotak.bank.in',
    ],
    'subject': [
        'realty news update', 'account balance - daily', 'security alert',
        'switch to the latest app', 'important notice: login',
        'daily attendance report', 'update now for the best experience',
    ],
}

# Entirely skip certain subject patterns (they dominate sent-item results)
SKIP_SENT_SUBJECTS = ['please sign in', 'please sign out', 'sign in for the day']


def is_bulk(frm, subj):
    frm_l = frm.lower()
    subj_l = subj.lower()
    for d in BULK_PATTERNS['sender_domain']:
        if d in frm_l:
            return True
    for s in BULK_PATTERNS['subject']:
        if s in subj_l:
            return True
    return False


def should_skip_sent(subj):
    subj_l = subj.lower()
    return any(s in subj_l for s in SKIP_SENT_SUBJECTS)


def fetch_messages(query, max_results=100):
    """Fetch up to max_results messages matching query with pagination."""
    all_msgs = []
    page_token = None
    while len(all_msgs) < max_results:
        params = {'userId': 'me', 'q': query, 'maxResults': min(100, max_results - len(all_msgs))}
        if page_token:
            params['pageToken'] = page_token
        res = service.users().messages().list(**params).execute()
        msgs = res.get('messages', [])
        if not msgs:
            break
        all_msgs.extend(msgs)
        page_token = res.get('nextPageToken')
        if not page_token:
            break
    return all_msgs


# ---- 1. SCAN INBOX ----
print(f"Scanning inbox since {DATE_FROM}...")
inbox_msgs = fetch_messages(f'in:inbox after:{DATE_FROM}', max_results=100)
print(f"Inbox messages found: {len(inbox_msgs)}\n")


def analyze_inbox_thread(m, thread_id, is_unread):
    """Categorise an inbox message by analysing its full thread."""
    subj = get_header(m, 'Subject')
    frm = get_header(m, 'From')
    date = get_header(m, 'Date')

    try:
        thread = service.users().threads().get(
            userId='me', id=thread_id, format='metadata',
            metadataHeaders=['From']
        ).execute()
        msgs_in_thread = thread['messages']
        last_msg = msgs_in_thread[-1]
        last_from = get_header(last_msg, 'From')
        last_from_user = is_from_user(last_from)

        thread_count = len(msgs_in_thread)
        user_replied = any(is_from_user(get_header(x, 'From', '')) for x in msgs_in_thread)

        # Skip if this is user's own sent message sitting in inbox (rare)
        if is_from_user(frm):
            return ('fyi', date, frm, subj, is_unread)

        if is_bulk(frm, subj):
            return ('fyi', date, frm, subj, is_unread)

        if not last_from_user and user_replied:
            # Multi-message convo, other person wrote last
            return ('needs_reply', date, frm, subj, is_unread,
                    'Active' if thread_count >= 3 else 'Roundtrip')
        elif not last_from_user and not user_replied:
            # Single message from someone, never replied
            return ('needs_reply', date, frm, subj, is_unread, 'New')
        elif last_from_user and user_replied and thread_count >= 2:
            # User wrote last, waiting on reply
            first_from = get_header(msgs_in_thread[0], 'From')
            return ('follow_up', date, first_from, subj, False, 'Active')
        else:
            return ('fyi', date, frm, subj, is_unread)
    except Exception:
        # Fallback: if not from user, flag as needs_reply
        if not is_from_user(frm) and not is_bulk(frm, subj):
            return ('needs_reply', date, frm, subj, is_unread, 'New')
        return ('fyi', date, frm, subj, is_unread)


needs_reply = []
follow_up_due = []
fyi = []

processed_threads = set()
for msg in inbox_msgs:
    tid = msg.get('threadId')
    if tid in processed_threads:
        continue
    processed_threads.add(tid)

    m = service.users().messages().get(
        userId='me', id=msg['id'], format='metadata',
        metadataHeaders=['Subject', 'From', 'Date']
    ).execute()
    is_unread = 'UNREAD' in m.get('labelIds', [])

    result = analyze_inbox_thread(m, tid, is_unread)
    cat = result[0]

    if cat == 'needs_reply':
        needs_reply.append(result[1:])
    elif cat == 'follow_up':
        follow_up_due.append(result[1:])
    else:
        fyi.append(result[1:])


# ---- 2. SCAN SENT ITEMS for threads awaiting reply ----
print("Checking sent items for follow-ups due...")
sent_msgs = fetch_messages(f'in:sent after:{DATE_FROM}', max_results=100)
print(f"Sent messages found: {len(sent_msgs)}\n")

sent_processed = set()
for msg in sent_msgs:
    m = service.users().messages().get(
        userId='me', id=msg['id'], format='metadata',
        metadataHeaders=['Subject', 'To', 'Date', 'From']
    ).execute()
    subj = get_header(m, 'Subject')
    tid = m.get('threadId')

    # Skip known noise patterns in sent items (auto-attendance, etc.)
    if should_skip_sent(subj):
        continue
    if tid in processed_threads or tid in sent_processed:
        continue
    sent_processed.add(tid)

    frm = get_header(m, 'From')
    if not is_from_user(frm):
        continue  # only consider threads user initiated

    try:
        thread = service.users().threads().get(
            userId='me', id=tid, format='metadata',
            metadataHeaders=['From', 'Subject']
        ).execute()
        t_msgs = thread['messages']
        last_from = get_header(t_msgs[-1], 'From')
        first_from = get_header(t_msgs[0], 'From')

        if is_from_user(last_from) and len(t_msgs) >= 1:
            # User sent the last message — awaiting reply
            follow_up_due.append((
                get_header(m, 'Date'), first_from, get_header(m, 'Subject'),
                False, 'Sent'
            ))
    except Exception:
        pass


# ---- 3. ACTION ITEMS KEYWORD SCAN ----
action_results = service.users().messages().list(
    userId='me',
    q=f'in:inbox (invoice OR bill OR approval OR deadline OR payment OR '
      f'"action required" OR "please review" OR sign OR execute OR urgent) '
      f'after:{DATE_FROM}',
    maxResults=30
).execute()
action_msgs = action_results.get('messages', [])
action_items = []
action_ids = set()
for msg in action_msgs:
    if msg['id'] in action_ids:
        continue
    action_ids.add(msg['id'])
    m = service.users().messages().get(
        userId='me', id=msg['id'], format='metadata',
        metadataHeaders=['Subject', 'From', 'Date']
    ).execute()
    subj = get_header(m, 'Subject')
    frm = get_header(m, 'From')
    if not is_bulk(frm, subj):
        action_items.append((
            get_header(m, 'Date'), frm, subj
        ))

# Dedup action items already in needs_reply
needs_reply_subjects = set(x[2].lower().strip() for x in needs_reply)
action_items = [x for x in action_items if x[2].lower().strip() not in needs_reply_subjects]


# ---- 4. SUBCATEGORISE FOR REPORT ----
# Split needs_reply into Active conversations vs New/single emails
real_replies = [x for x in needs_reply if x[4] in ('Active', 'Roundtrip')]
new_replies = [x for x in needs_reply if x[4] in ('New',)]

# ---- 5. REPORT ----
SEP = "=" * 80
print(SEP)
print(f"EMAIL INBOX TRIAGE — {SERVICE_NAME} ({profile.get('emailAddress', '?')})")
print(f"Period: {DATE_FROM} to today")
print(SEP)

# Needs reply — active conversations
if real_replies:
    print(f"\nNEEDS YOUR REPLY — active conversations ({len(real_replies)})\n" + "-" * 50)
    for item in real_replies[:15]:
        date, frm, subj, unread, cat = item
        flag = " [UNREAD]" if unread else ""
        print(f"  [{date[:16]}]{flag}  [{cat}]")
        print(f"  From: {trunc(frm, 70)}")
        print(f"  Subj: {trunc(subj, 100)}")
        print()

# Needs reply — new/single emails
if new_replies:
    print(f"\nNEW / SINGLE EMAILS — may need first response ({len(new_replies)})\n" + "-" * 50)
    for item in new_replies[:10]:
        date, frm, subj, unread, cat = item
        flag = " [UNREAD]" if unread else ""
        print(f"  [{date[:16]}]{flag}")
        print(f"  From: {trunc(frm, 70)}")
        print(f"  Subj: {trunc(subj, 100)}")
        print()
    if len(new_replies) > 10:
        print(f"  ... and {len(new_replies) - 10} more\n")

# Action items
if action_items:
    print(f"\nACTION / URGENT ITEMS ({len(action_items)})\n" + "-" * 50)
    for date, frm, subj in action_items[:10]:
        print(f"  [{date[:16]}]")
        print(f"  From: {trunc(frm, 70)}")
        print(f"  Subj: {trunc(subj, 100)}")
        print()

# Follow-up due
if follow_up_due:
    print(f"\nFOLLOW-UP DUE — awaiting reply ({len(follow_up_due)})\n" + "-" * 50)
    for item in follow_up_due[:10]:
        date, frm, subj, _, cat = item
        print(f"  [{date[:16]}]  [{cat}]")
        print(f"  To:   {trunc(frm, 70)}")
        print(f"  Subj: {trunc(subj, 100)}")
        print()

# FYI
if fyi:
    print(f"\nFYI / NOTIFICATIONS ({len(fyi)})\n" + "-" * 50)
    for item in fyi[:8]:
        date, frm, subj, _, = item[:4]
        print(f"  [{date[:16]}]  From: {trunc(frm, 50)}")
        print(f"     {trunc(subj, 90)}")
        print()
    if len(fyi) > 8:
        print(f"  ... and {len(fyi) - 8} more\n")

print(SEP)
print(f"SUMMARY:  {len(real_replies)} active conversations  |  "
      f"{len(new_replies)} new emails  |  "
      f"{len(action_items)} action items  |  "
      f"{len(follow_up_due)} follow-ups due  |  "
      f"{len(fyi)} notifications/FYI")
print(SEP)
