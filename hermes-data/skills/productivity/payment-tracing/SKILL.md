---
name: payment-tracing
description: "Trace financial transactions through Gmail bank alerts — search bank notification emails, extract structured transaction data, cross-reference outgoing vs incoming payments for the same counterparty, look up contact info, and generate WhatsApp follow-up messages."
version: 1.0.0
---

# Payment Tracing

Trace specific payments/transactions using bank alert emails in Gmail. A recurring CEO task: "find when X paid me back," "find the payment from Y," "trace the three inflows from Z."

## Workflow

### 1. Identify the Correct Account

**Critical first step.** The user often remembers partial account info (e.g. "ending 5634" or "XX0957"). The actual account may be different from what you initially search.

- If the user mentions a specific account number / last 4 digits, search that account
- If the user says an SMS mentioned a different account number, that's the correct one
- When in doubt, search ALL accounts mentioned in the conversation

### 2. Search Gmail for Bank Alerts

Use `gmail_search` via the skill bridge:

```python
from tools.gws_skill_bridge import call
res = call('gmail_search', service_name='google-draas', query='XX0957 Payment Received', max=50)
```

**⚠️ `gmail_search` returns a JSON *string*, not a list or dict.** The skill bridge
serializes the result — `res` is `str`, so `res.get(...)` / `for m in res` fail with
`AttributeError: 'str' object has no attribute 'get'`. Always `json.loads()` first:

```python
import json
results = json.loads(res)   # → list of dicts
for m in results:
    print(m['id'], m['threadId'], m.get('from'), m.get('date'), m.get('snippet'))
```

Each item has keys: `id`, `threadId`, `from`, `to`, `subject`, `date`, `snippet`, `labels`.
Then use `gmail_get(message_id=...)` for the full body (parameter is `message_id`, not `msg_id`).

**Parameter note:** The argument is `max` (not `max_results`). Using `max_results` raises `AttributeError: 'types.SimpleNamespace' object has no attribute 'max'`.

Useful query patterns:
- `XX0957 Payment Received` — all incoming credits to an account
- `from:bankalerts credited XX0957` — credit alerts for an account
- `XX0957 after:2024/12/31` — narrowed date range
- `SALMAN credited` — specific sender name
- `from:bankalerts credited XX0957 after:2024/02/12 before:2026/07/24` — date-constrained search

The email snippets contain structured data: `Rs. 1000000 has been credited to your Kotak Bank a/c XX0957 on 15-DEC-25 via NEFT transaction from SALMAN KHALID. Your Unique Transaction Reference Number (UTR) is: HDFCH00676280292.`

### 3. Parse Transaction Details

Extract from each email snippet:
- **Date** (e.g. `15-DEC-25`)
- **Amount** (e.g. `1000000`)
- **Sender** (e.g. `SALMAN KHALID`)
- **Mode** (NEFT / RTGS)
- **UTR** (unique reference number)
- **Account** last 4 digits (e.g. XX0957)

### 4. Cross-Reference Outgoing vs Incoming

When the user mentions "I paid X and they repaid in Y installments":
1. Search for outgoing debits to that person (from Large Debit alerts or InterBank Transfer Credit Alert emails — these show money sent TO someone)
2. Search for incoming credits FROM that person
3. Compare the totals

Outgoing alerts look like:
```
Rs. 4900000.00 is debited from your account XXXX0957 on 12-02-2024 towards Sent RTGS ... /SALMAN KHA
```
or
```
Rs. 4900000 has been credited to beneficiary ( SALMAN KHALID ) account
```

### 5. Look Up Counterparty Contact Info

Use People API directly (the `contacts_list` bridge function is unreliable):

```python
from tools.gws_auth import build_service
service = build_service('people', 'v1', service_name='google-draas')
results = service.people().searchContacts(
    query="Salman Khalid",
    readMask="names,phoneNumbers,emailAddresses"
).execute()
```

### 6. Generate WhatsApp Follow-Up

Once you have the phone number and transaction context, generate a `wa.me` link with a pre-filled message asking for the missing details.

## Pitfalls

### Wrong Account
The user's first guess at the account number may be wrong. If you search one account and find nothing, and the user says "maybe it's another account," immediately switch to the correct one. Don't continue explaining the wrong account's data.

### Missing Statements
Bank statement PDFs sent via email are **password-protected** (password = CRN). You cannot open them without the CRN. The email body does not contain transaction data inline — only a link to netbanking.

Monthly statement emails may not exist for all months in the inbox (e.g. Jan-Jun 2025 may be missing for some accounts). In such cases, only the individual "Payment Received" / "Large Debit Alerts" are available.

### `gmail_search` Parameter Name
The parameter for max results is `max`, not `max_results`. Wrong parameter raises `AttributeError: 'types.SimpleNamespace' object has no attribute 'max'`.

### `gmail_get` Parameter Name
When getting a full email, use `message_id` (not `msg_id`). Wrong parameter raises `AttributeError: 'types.SimpleNamespace' object has no attribute 'message_id'`.

### Contacts API Limitations
- `searchContacts()` only searches "My Contacts" — not "Other Contacts"
- Empty results != contact doesn't exist; it may be in Other Contacts
- `contacts_list` via gws_skill_bridge returns garbage data — use People API directly

### Bank Naming Variations
The same sender may appear under slightly different names in different alerts:
- "SALMAN KHALID" vs "SALMAN KHA" (truncated)
- "Salman khalid" vs "Salman Khalid Redifice" (in contacts)
- Search partial names when the exact match fails
