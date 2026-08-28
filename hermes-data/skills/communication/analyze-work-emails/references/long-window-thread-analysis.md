# Long-Window Thread Analysis (30–60 days) — verified Aug 2026

Verified working pattern for "analyze last 60 days of email, who owes what" on
ndr@draas.com. ~3,000 messages → ~1,060 threads after noise filter; fetch takes
~8 minutes, MUST run in background.

## Why not the bridge
`gws_skill_bridge.call('gmail_search', ...)` enriches every message and times
out (300s) on 18 weekly window queries at this volume. Use the direct API.

## Working script skeleton (run in background)

```python
#!/opt/hermes/.venv/bin/python3
import sys, re, json, base64
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from collections import defaultdict
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

DAYS = 60
today = datetime.now(timezone.utc)
cutoff = today - timedelta(days=DAYS)
since = cutoff.strftime('%Y/%m/%d')
gmail = build_service('gmail', 'v1', service_name='google-draas')  # or google-ahfl / google-gmail

def list_ids(query):
    ids, page = [], None
    while True:
        resp = gmail.users().messages().list(userId='me', q=query,
                                             maxResults=500, pageToken=page).execute()
        ids.extend(m['id'] for m in resp.get('messages', []))
        page = resp.get('nextPageToken')
        if not page:
            break
    return ids

ids = {}
for q in (f'in:inbox after:{since}', f'in:sent after:{since}'):
    for mid in list_ids(q):
        ids[mid] = True

# Per-message metadata -> threadId + headers (the slow part: ~3000 calls)
id2thread = {}
for mid in ids:
    m = gmail.users().messages().get(userId='me', id=mid, format='metadata',
        metadataHeaders=['Subject', 'From', 'To', 'Date']).execute()
    h = {x['name'].lower(): x['value'] for x in m.get('payload', {}).get('headers', [])}
    id2thread[mid] = (m.get('threadId', ''), h, m.get('labelIds', []))

# Group by thread, filter date+noise, sort, classify on LAST message
threads = defaultdict(list)
for mid, (tid, h, labels) in id2thread.items():
    threads[tid].append({'from': h.get('from',''), 'to': h.get('to',''),
                         'subject': h.get('subject',''), 'date': h.get('date',''),
                         'labels': labels})
# ... classify: 'SENT' in last labels -> AWAITING RESPONSE; incoming+ask -> NEEDS RESPONSE
```

## Report shape that worked
1. Header: totals — `Total threads: 1061 | awaiting: 135 | needs-response: 18 | info/fii: 908`
2. **AWAITING RESPONSE** — every thread where user sent last, with recipient names
   from To header (strip self via regex `r',(?![^<]*>)'`), days since sent, subject.
3. **NEEDS RESPONSE** — incoming-last threads with ask keywords (please, kindly,
   confirm, approval, any update, status...).
4. INFO/CONVO tail (last 25 each).
5. Save report + full thread JSON to /data/hermes/tmp/ for later deep-dives.

## Chase-tier presentation
- 0–7d "this week (send nudges)"
- 8–14d "1–2 weeks old"
- 15d+ "older (nudge or close out)"
User acts on recency tiers, not exact dates.

## Targeted deep-dive (one person/claim, full bodies)
Separate small script, foreground OK if capped:
```python
def search_ids(q, maxr=100):  # same pagination
ids = search_ids('"Kanta Ranka" OR claims@mediassistindia.com')
for mid in ids[:30]:
    msg = gmail.users().messages().get(userId='me', id=mid, format='full').execute()
    # walk payload parts for text/plain, base64.urlsafe_b64decode
# group by threadId, sort by Date, print From/To/Subject/Body[:800]
```
Use `format='full'` here (not metadata) — you want bodies for the specific thread.

## Pitfalls
- Exact quoted phrase still matches thousands if the name is the account holder
  (bank alerts contain it). Narrow with `-from:` + `after:` + cap ids.
- Bounced mail (postmaster@domain) threads pollute AWAITING — filter
  `from:postmaster OR from:mailer-daemon` or mark them as delivery-failure noise.
- Google Calendar notifications (`calendar-notification@google.com`) are real
  appointments but should NOT drive thread classification — filter, then surface
  as a separate watch list.
- Batch the metadata gets into the SAME background process that does classification;
  don't split into two scripts (the JSON dump is needed for both).
