# Three-Account Email Analysis + Thread Follow-ups (verified 2026-08-01)

Proven pattern for "analyze work + personal email for N days, tell me what to
respond to and who owes me a response". Covers all 3 of Nishant's accounts:

| Account | Email | Vault service |
|---------|-------|---------------|
| Work primary | ndr@draas.com | google-draas |
| Work secondary | ndr@ahfl.in | google-ahfl |
| Personal | nishantranka@gmail.com | google-gmail |

## Step 1 — Fetch all accounts, inbox + sent, weekly windows

```python
import sys, re, json
from datetime import datetime, timezone, timedelta
sys.path.insert(0, '/opt/hermes')
from tools.gws_skill_bridge import call

ACCOUNTS = {'google-draas': 'ndr@draas.com', 'google-ahfl': 'ndr@ahfl.in',
            'google-gmail': 'nishantranka@gmail.com'}
now = datetime.now(timezone.utc)
since = (now - timedelta(days=DAYS)).strftime('%Y/%m/%d')
mid  = (now - timedelta(days=7)).strftime('%Y/%m/%d')

def fetch(service_name, query, maxr=200):
    raw = call('gmail_search', service_name=service_name, query=query, max=maxr)
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw or raw.lower().startswith('no messages'):
            return []
        raw = json.loads(raw)
    return raw if isinstance(raw, list) else []

msgs = []
for svc, label in ACCOUNTS.items():
    for folder in ['in:inbox', 'in:sent']:
        for q in [f'{folder} after:{since} before:{mid}', f'{folder} after:{mid}']:
            for m in fetch(svc, q):
                m['_account'] = label          # NOTE: stores EMAIL, not service name
                msgs.append(m)
# dedupe by id
seen = {}
for m in msgs:
    if m.get('id') and m['id'] not in seen:
        seen[m['id']] = m
msgs = list(seen.values())
```

## Step 2 — Noise filter

- Domain blocklist: `noreply`, `no-reply`, `donotreply`, `newsletter`,
  `substack.com`, `beehiiv.com`, `economictimes.com`, `linkedin.com`,
  `amazon`, `flipkart`, `swiggy`, `zomato`, `netmeds`, `netflix`, bank
  alerts (`bankalerts@`, `kotak.bank`), MF/KFintech notices (`kfintech`,
  `camsonline`, `evoting`, `nsdl`), event/marketing (`crematrix`,
  `worldhrdcongress`, `marriott`, `headout`, `quintessentially`).
- Subject noise: `attendance report`, `daily attendance`, `general file`,
  `otp`, `one time password`, `dividend`, `annual report`, `agm`, `shareholder`.
- Kelsa sign-in/out + daily bank balance alerts.
- Validate Date header against the cutoff (`parsedate_to_datetime`) — old
  forwarded mail from ndr@drahomes.in lands unread in inbox.

## Step 3 — Thread grouping & follow-up classification

```python
from collections import defaultdict
from email.utils import parsedate_to_datetime
by_thread = defaultdict(list)
for m in msgs:
    by_thread[(m['_account'], m.get('threadId'))].append(m)

for (acct, tid), tmsgs in by_thread.items():
    tmsgs.sort(key=lambda m: parsedate_to_datetime(m.get('date') or '') or now)
    last = tmsgs[-1]
    is_sent = 'SENT' in last.get('labels', [])
    # AWAITING_RESPONSE if user sent last; NEEDS_RESPONSE if incoming asks
```

To name the person who owes a response, fetch the last full body with
`gmail_get(service_name=..., message_id=last['id'])` — snippets often show
only the forwarder (e.g. Prakash fwd'ing ICICI Bank queries "kindly do the
needful"), while the body shows the actual requester.

## Step 4 — Output shape that worked

1. Volume per account (raw vs real after noise).
2. **AWAITING RESPONSE** — user sent last; group by "this week" vs "11+ days",
   name the recipient and what's pending. These are the chase-them items.
3. **NEEDS RESPONSE** — incoming asks; mark urgency (RERA "final notice",
   LEI renewal lapsed, approvals needed).
4. Watch/informational (time-bound but no action yet).
5. One-line "short version": 3 people owe you X; you owe replies on Y.

## Pitfalls hit
- `gmail_search` returns a JSON string; "No messages found.\n" crashes json.loads.
- `_account` = email, NOT vault service name — map email→service for gmail_get.
- `max=500` truncates busy accounts — use weekly window splits.
- Don't infer project context the email doesn't state; classify from
  From/Subject/Snippet only (matches skill convention).
