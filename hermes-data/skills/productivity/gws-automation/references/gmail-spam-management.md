# Gmail Spam Management — Identify, Unspam, Track, Auto-Clean

Recurring workflow: examine the spam folder, identify legitimate emails that were misclassified, mark them as "not spam," log the sender patterns in a whitelist spreadsheet, and set up a 3-hourly cron to auto-unspam matching future emails.

## Quick Start

This workflow is now managed by the **`not-spam-whitelist`** skill (skill name: `not-spam-whitelist`). Load it before handling any spam-related tasks.

- **Whitelist Sheet:** https://docs.google.com/spreadsheets/d/1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0/edit
- **Sheet ID:** `1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0`
- **Cron schedule:** Every 3 hours at 9/12/3/6/9/12 AM/PM IST (`30 3,6,9,12,15,18 * * *`)

## Step 1 — List spam messages

Use the Gmail API with `labelIds=['SPAM']`. Fetch headers (From, Subject, Date) for each:

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import json, os
token_path = f"/data/hermes/users/{os.environ['HERMES_SESSION_USER_ID']}/the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)"
with open(token_path) as f:
    info = json.load(f)
creds = Credentials.from_authorized_user_info(info)
if not creds.valid:
    creds.refresh(Request())

service = build('gmail', 'v1', credentials=creds)

results = service.users().messages().list(userId='me', labelIds=['SPAM'], maxResults=200).execute()
msgs = results.get('messages', [])
print(f"Total spam: {len(msgs)}")

for m in msgs:
    msg = service.users().messages().get(
        userId='me', id=m['id'],
        format='metadata',
        metadataHeaders=['From','To','Subject','Date']
    ).execute()
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    print(f"ID:{m['id']} | From: {headers.get('From','?')[:70]} | Subject: {headers.get('Subject','?')[:60]}")
```

## Step 2 — Mark identified emails as "not spam"

```python
for mid in not_spam_ids:
    service.users().messages().modify(userId='me', id=mid, body={
        'removeLabelIds': ['SPAM'],
        'addLabelIds': ['INBOX']
    }).execute()
```

## Step 3 — Known not-spam patterns (Nishant R, June 2026)

These patterns are in the whitelist sheet. For reference during initial bulk cleanup:

| Sender/Pattern | Category | Rule Type |
|----------------|----------|-----------|
| `apsaraa.sridhar@cms-induslaw.com` | Legal | `exact_from` |
| `statement@idfcfirst.bank.in` | Banking - IDFC | `exact_from` |
| `alerts@hdfcbank.bank.in` | Banking - HDFC | `exact_from` |
| `information@hdfcbank.bank.in` | Banking - HDFC | `exact_from` |
| `drive-shares-dm-noreply@google.com` (Bharat H) | HR - Payroll | `domain_from` |
| `bk@findingform.design` | Architecture | `exact_from` |
| `creditcardalerts@kotak.bank.in` (card x0531) | Banking - Kotak | `domain_from` |
| `alwaysyoufirst@emailer.idfcfirst.bank.in` | Banking - IDFC | `domain_from` |
| `RoyalSundaramVconnect@royalsundaram.in` | Insurance | `exact_from` |
| `nach.alerts@kotak.bank.in` | Banking - Kotak | `exact_from` |
| `@draas.com` | Internal | `domain_from` |

## Step 4 — Add new entries to whitelist

See the **`not-spam-whitelist`** skill for the full workflow. In summary:
1. Get the email details from spam folder
2. Determine rule type
3. Append to sheet using Sheets API
4. Mark the email as not spam

## Important Domain Research (June 2026)

**`.bank.in` is legitimate — RBI mandated all Indian banks to use this domain (April 2023).**
- HDFC Bank: `alerts@hdfcbank.bank.in`, `information@hdfcbank.bank.in`
- IDFC FIRST Bank: `statement@idfcfirst.bank.in`, `alwaysyoufirst@emailer.idfcfirst.bank.in`
- Kotak Mahindra Bank: `creditcardalerts@kotak.bank.in`, `nach.alerts@kotak.bank.in`
- Do NOT flag `@hdfcbank.bank.in` as spam — it is the official domain
- Phishing domains to watch: `@hdfcbank.co.in`, `@hdfcbank.net`, `@hdfc-bank.in`

## Key pitfalls

- **`format='metadata'` is header-only** — the body is NOT returned. Use `format='full'` for body content.
- **Modify API is idempotent** — calling it on an already-inboxed message is harmless.
- **Never delete spam** — only move matching emails to inbox. Deletion is for user manual review.
