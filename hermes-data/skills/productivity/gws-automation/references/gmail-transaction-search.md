# Gmail Transaction Search & Financial Data Extraction

**Class:** Search pattern — Find a specific financial or investment transaction thread in Gmail using multi-strategy search, read the full conversation, and extract structured figures (quantity, rate, total).

**Trigger:** User asks "check my email about buying [shares/stock/investment] with [person]" or "find the email about [transaction type] and confirm the final figure."

---

## Phase 1 — Multi-Strategy Search

Don't rely on a single query. Run several in parallel to maximize coverage:

```python
from tools.gws_auth import build_service
gmail = build_service('gmail', 'v1')

queries = [
    # Sender-based (the person the user mentioned)
    'from:kishan@flamebackcapital.com NSE',
    # Subject-specific
    'subject:"NSE" subject:"shares"',
    'subject:"Confirmation Mail" NSE',
    # Body keywords
    '"NSE" "pre-IPO" OR "private placement" OR "unlisted"',
    '"NSE" "shares" "buy" OR "sale"',
    # Search SENT mail too (for user's confirmations)
    'from:ndr@draas.com "NSE" OR "Valiant Fintech" OR "Infinyte"',
    # Narrow by date range if you have a rough timeframe
    'NSE after:2024/01/01 before:2025/01/01',
]

all_hits = set()
for q in queries:
    results = gmail.users().messages().list(userId='me', q=q).execute()
    for m in results.get('messages', []):
        all_hits.add(m['id'])
```

### Search Query Tips

| Goal | Query Pattern |
|------|--------------|
| By person | `from:person@domain.com` or `to:person@domain.com` |
| Subject match | `subject:"exact phrase"` or `subject:keyword` |
| Body content | `keyword OR "phrase"` (Gmail ANDs terms by default) |
| Sent mail | `from:YOUR@email.com keyword` |
| Date range | `after:YYYY/MM/DD before:YYYY/MM/DD` (Gmail format, NOT YYYY-MM-DD) |
| Exclude newsletters | `-from:noreply -from:newsletter -from:marketing` |
| Thread grouping | Use `threads().list()` not `messages().list()` to group replies |

## Phase 2 — Identify the Right Thread

Fetch metadata for each hit and look for the correct thread:

```python
threads_found = {}
for mid in all_hits:
    msg = gmail.users().messages().get(userId='me', id=mid, format='metadata',
        metadataHeaders=['From','To','Subject','Date']).execute()
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    tid = msg['threadId']
    if tid not in threads_found:
        threads_found[tid] = {
            'subject': headers.get('Subject',''),
            'from': headers.get('From',''),
            'date': headers.get('Date',''),
            'msg_count': 0
        }
    threads_found[tid]['msg_count'] += 1

# Show user the candidate threads
for tid, info in sorted(threads_found.items(), key=lambda x: x[1]['date'], reverse=True):
    print(f"Thread: {tid} | {info['date'][:25]} | {info['subject'][:80]} | {info['msg_count']} msgs")
```

## Phase 3 — Read Full Thread Content

Once the right thread is identified, use `threads().get()` with `format='full'` and sort messages by `internalDate` (epoch ms) for chronological order:

```python
import base64

thread = gmail.users().threads().get(userId='me', id=target_thread_id, format='full').execute()
messages = sorted(thread['messages'], key=lambda m: int(m['internalDate']))

for msg in messages:
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    print(f"\n{headers.get('Date','')}")
    print(f"From: {headers.get('From','')}")
    print(f"Subject: {headers.get('Subject','')}")

    # Extract plain text body — walk nested MIME parts
    body = ''
    def extract_parts(part):
        nonlocal body
        if 'parts' in part:
            for subpart in part['parts']:
                extract_parts(subpart)
        elif part['mimeType'] == 'text/plain' and 'data' in part.get('body', {}):
            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
    extract_parts(msg['payload'])
```

**Key:** Always use `format='full'` (not `'metadata'` or `'raw'`) — it returns the proper `payload.parts[]` structure with `body.data` for inline text and `body.attachmentId` for files. `'raw'` requires manual RFC 2822 parsing.

## Phase 4 — Extract Financial Data

Look for structured data in the email body — usually in tabular or list format:

```
Buyer Name        | Nishant Ranka
Seller name       | Valiant Fintech Private Limited
No of Shares      | 450
Rate              | 5650/-
Consideration     | 25,42,500.00/-
Statutory Charges | 3,881/-
Total             | 25,46,381/-
```

Patterns to extract:
- **Quantity:** "No of Shares", "Number of Shares", "Qty"
- **Rate/Price per unit:** "Rate", "Price per share", "@ ₹"
- **Total Consideration:** "Consideration Amount", "Total Amount"
- **Statutory charges:** separate line item
- **Grand total:** "Total Consideration + charges"

Extract with regex:
```python
import re

# Find quantity
qty_m = re.search(r'(\d+)\s*[Ss]hares?', body)
if qty_m: qty = qty_m.group(1)

# Find rate
rate_m = re.search(r'[Rr]ate[:\s]*₹?\s*([\d,]+)', body)
if rate_m: rate = rate_m.group(1).replace(',', '')

# Find total amount (look for Indian number format with commas)
total_m = re.search(r'[Tt]otal.*?₹?\s*([\d,]+\.?\d*)', body)
if total_m: total = total_m.group(1)
```

## Pitfalls

- **Gmail search ambiguity:** The same search term ("NSE") may find both transaction emails and newsletters mentioning NSE. Always scan metadata before fetching full content.
- **Sent vs received messages:** Your sent messages may not appear in the same thread as received messages if the user replied from a different email client or the sent message was saved as a separate copy. Check both `from:user@domain` and the thread directly.
- **Attachment confirmation:** Payment confirmations, signed documents, or share certificates are often attached rather than inline. Use `body.attachmentId` to download them — don't expect the data to be in the body text.
- **No final "completed" email:** Many unlisted/pre-IPO transactions conclude via physical delivery or broker demat credit, not email. Don't assume the transaction didn't happen just because the email thread has no "shares credited" message — check the last practical action (e.g., DP letters submitted, stage 2 docs signed).
- **Thread size limits:** Gmail threads with 35+ messages are common for investment deals spanning months. The `format='full'` call can return large payloads — if timeout is a concern, paginate by fetching individual messages within the thread instead.
- **internalDate is epoch ms:** `int(msg['internalDate'])` gives milliseconds since Unix epoch. Divide by 1000 for seconds, then use `datetime.fromtimestamp()` if needed.
