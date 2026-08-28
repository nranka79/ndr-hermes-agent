#!/opt/hermes/.venv/bin/python3
"""Daily cleanup: Delete 'Please sign in for the day' emails older than 1 day.

Runs daily via cron. Deletes emails matching the subject
that are dated before today (previous day's sign-in reminders).

WHY THIS COPY EXISTS: the cron job runs /opt/data/scripts/cleanup-signin-emails.py,
but that path has been wiped from disk repeatedly (Jul 9/12/14, Aug 10 2026).
This skill copy is the canonical, known-good source. When the cron path is
missing, copy this file to /opt/data/scripts/cleanup-signin-emails.py and run it.

Run command (must include env vars — cron context has no session-level GWS
service and no default vault socket):
  cd /opt/data && HERMES_SESSION_USER_ID=[REDACTED-TID] GWS_VAULT_SOCKET=/run/gws-vault/vault.sock \
      /opt/hermes/.venv/bin/python3 scripts/cleanup-signin-emails.py
"""
import sys, os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

# Setup — service_name is REQUIRED in cron context. build_service('gmail','v1')
# without it works in interactive sessions but raises in cron (no session-level
# GWS service configured). google-draas = ndr@draas.com.
gmail = build_service('gmail', 'v1', service_name='google-draas')

SUBJECT = '"Please sign in for the day"'
CUTOFF = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

print(f'[{datetime.now().isoformat()}] Starting sign-in email cleanup...')
print(f'  Subject: {SUBJECT}')
print(f'  Cutoff (older than): {CUTOFF}')

# Query: emails with this subject, older than 1 day
query = f'subject:{SUBJECT} before:{CUTOFF[:10]}'

page_token = None
total_trashed = 0
batch = []
batch_size = 50

while True:
    results = gmail.users().messages().list(
        userId='me', q=query, pageToken=page_token,
        maxResults=500, fields='nextPageToken,messages/id'
    ).execute()

    msgs = results.get('messages', [])
    if not msgs:
        break

    for m in msgs:
        batch.append(m['id'])
        if len(batch) >= batch_size:
            # Batch trash
            gmail.users().messages().batchModify(
                userId='me',
                body={'ids': batch, 'addLabelIds': ['TRASH'], 'removeLabelIds': ['INBOX', 'UNREAD']}
            ).execute()
            total_trashed += len(batch)
            print(f'  Trashed {len(batch)} emails (total: {total_trashed})')
            batch = []

    page_token = results.get('nextPageToken')
    if not page_token:
        break

# Final batch
if batch:
    gmail.users().messages().batchModify(
        userId='me',
        body={'ids': batch, 'addLabelIds': ['TRASH'], 'removeLabelIds': ['INBOX', 'UNREAD']}
    ).execute()
    total_trashed += len(batch)
    print(f'  Trashed {len(batch)} emails (total: {total_trashed})')

print(f'[{datetime.now().isoformat()}] Completed. Total trashed: {total_trashed}')
