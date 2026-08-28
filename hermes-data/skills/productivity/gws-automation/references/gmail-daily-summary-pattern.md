# Gmail Daily Summary Pattern

When the user asks "summary of my emails for the day" or "how many emails today" or "email count + summary".

## Workflow

### 1. Query construction

Use Unix timestamps (seconds since epoch) for the `after:` / `before:` Gmail search operators:

```python
from datetime import datetime, timezone, timedelta

today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
today_end = today_start + timedelta(days=1)

query = f"after:{int(today_start.timestamp())} before:{int(today_end.timestamp())}"
```

Gmail's `after:`/`before:` accepts seconds since epoch. This is more reliable than date strings (`YYYY/MM/DD`) across timezone boundaries.

### 2. Fetch all messages (paginate)

```python
svc = build_service("gmail", "v1")

messages = []
page_token = None
while True:
    result = svc.users().messages().list(
        userId="me", q=query, pageToken=page_token, maxResults=500
    ).execute()
    if "messages" in result:
        messages.extend(result["messages"])
    page_token = result.get("nextPageToken")
    if not page_token:
        break
```

Use `maxResults=500` to reduce API calls. Daily volume rarely exceeds this.

### 3. Get metadata headers (not full body)

Use `format="metadata"` with specific `metadataHeaders` — this is faster and cheaper than `format="full"`:

```python
def get_msg(msg_id):
    msg = svc.users().messages().get(
        userId="me", id=msg_id,
        format="metadata",
        metadataHeaders=["From", "Subject", "Date", "To", "Cc"]
    ).execute()
    hdrs = {h["name"].lower(): h["value"] for h in msg.get("payload",{}).get("headers",[])}
    return {
        "from": hdrs.get("from", "Unknown"),
        "subject": hdrs.get("subject", "(No Subject)"),
        "labels": msg.get("labelIds", [])
    }
```

### 4. Categorise by label

```python
inbox   = [e for e in emails if "INBOX" in e["labels"] and "SENT" not in e["labels"]]
sent    = [e for e in emails if "SENT" in e["labels"]]
unread  = [e for e in inbox if "UNREAD" in e["labels"]]
```

### 5. Sender frequency

```python
from collections import Counter
sender_counts = Counter()
for e in inbox:
    # Extract name part before <email>
    sender = e["from"].split("<")[0].strip().strip('"')
    sender_counts[sender] += 1
```

### 6. Telegram output format

Use bullet-friendly markdown. No tables (Telegram strips them). Lead with totals:

```
📬 DATE — Email Summary

Total: N | Inbox: N | Unread: N

Top Senders:
• Sender A: N
• Sender B: N

Inbox:
⏺ Sender Name
   Subject line

📩 Sender Name
   Subject line
```

- `⏺` = unread
- `📩` = read (no prefix = read is also fine)
- Sender name extracted before `<email>` to keep it readable
- Subject truncated to ~100 chars max
- Separate sent emails as a separate block

## Environment notes

This code runs in `execute_code` (import from `tools.gws_auth` works there). If calling from terminal via `python3 -c`, use the Hermes venv:

```bash
/opt/hermes/.venv/bin/python3 -c "from tools.gws_auth import build_service; ..."
```

The system `python3` at `/usr/bin/python3` does NOT have the Google API client library installed.

## Pitfalls

- **Rate limits:** The `users().messages().get()` call has no batch wrapper above. For >50 emails, add a small `time.sleep(0.05)` between calls to avoid 429s.
- **The `from` header format:** Gmail returns `"Full Name" <email@domain.com>`. Strip the `<>` wrapped email for display, keep the full value for deduplication.
- **Unread detection:** `labelIds` contains `"UNREAD"` string. Simple `if "UNREAD" in labels` works — no need to check the `messages.list` `q:` parameter's `is:unread`.
- **Sent emails also appear in inbox query:** Gmail's `after:`/`before:` finds ALL messages in that time window including sent. Always filter by `SENT` label to separate.
- **build_service bug:** If you hit `AttributeError: type object 'Credentials' has no attribute 'from_authorized_user_json'`, the fix (already applied to `/opt/hermes/tools/gws_auth.py`) is to change `from_authorized_user_json(path.read_text(), ...)` to `from_authorized_user_file(path, ...)`.

---

## Level 2 — Categorized summary with action items (the richer variant)

When the user asks for "categorize my emails and tell me what needs action." Add this workflow after the basic Level-1 count.

### Full Python workflow (write to `/tmp`, run via Hermes venv)

**Recommended structure:** Write to `/tmp/script.py` and execute with:

```bash
/opt/hermes/.venv/bin/python3 /tmp/script.py
```

### Phase 1: Fetch + categorize + de-noise

```python
from tools.gws_auth import build_service
from datetime import datetime, timezone, timedelta
from collections import Counter

svc = build_service("gmail", "v1")

# Query: today in local timezone (e.g. IST = UTC+5:30)
ist_offset = timedelta(hours=5, minutes=30)
now_local = datetime.now(timezone.utc) + ist_offset
today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
today_start_utc = today_start_local - ist_offset
query = f'after:{today_start_utc.strftime("%Y/%m/%d")}'

results = svc.users().messages().list(userId="me", q=query, maxResults=100).execute()
messages = results.get("messages", [])
print(f"Total: {len(messages)}")

# Phase 1a: Fetch metadata headers
email_list = []
for msg in messages:
    md = svc.users().messages().get(
        userId="me", id=msg["id"], format="metadata",
        metadataHeaders=["From", "Subject", "Date"]
    ).execute()
    h = {hh["name"]: hh["value"] for hh in md.get("payload", {}).get("headers", [])}
    email_list.append({
        "id": msg["id"],
        "subject": h.get("Subject", ""),
        "from": h.get("From", ""),
    })

# Phase 1b: Identify and separate noise (auto-notifications)
auto_sign = [e for e in email_list
             if "Please sign" in e["subject"]
             and "nishant" in e["from"].lower()]

other = [e for e in email_list if e not in auto_sign]

print(f"  Auto-notifications (ignored): {len(auto_sign)}")
print(f"  Remaining: {len(other)}")
```

### Phase 2: Categorization function

```python
def categorize(subject, sender):
    s = subject.lower()
    f = sender.lower()

    if any(x in f for x in ["draas.com", "drahomes.in", "roma"]):
        return "💼 Work (Internal)"
    if any(x in s for x in ["invoice", "payment", "fee", "bill", "receipt",
                            "transaction alert", "consignment", "kyc"]) \
       or any(x in f for x in ["kotak", "hdfc", "indusind", "axis", "icici", "sbi"]):
        return "🏦 Banking/Finance"
    if any(x in s for x in ["newsletter", "offer", "promotion", "discount", "unsubscribe"]):
        return "📢 Marketing"
    if any(x in s for x in ["notification", "alert", "verify", "otp", "password",
                            "verification", "security", "slack"]):
        return "🔔 Notifications/Alerts"
    if any(x in f for x in ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]):
        return "👤 Personal"
    return "📎 Other"

# Group by category
cat_groups = {}
for e in other:
    cat = categorize(e["subject"], e["from"])
    cat_groups.setdefault(cat, []).append(e)

# Display grouped, deduplicating identical subjects
for cat, items in sorted(cat_groups.items()):
    print(f"\n{cat} ({len(items)} emails):")
    subj_counts = Counter(i["subject"] for i in items)
    for subj, count in sorted(subj_counts.items(), key=lambda x: -x[1]):
        sender = next(i["from"] for i in items if i["subject"] == subj)
        name = sender.split("<")[0].strip().strip('"') or sender
        if count > 1:
            print(f"  • {subj[:80]} — {name} (×{count})")
        else:
            print(f"  • {subj[:80]} — {name}")
```

### Phase 3: Smart action-item extraction

The trap: naive keyword matching catches auto-notifications like "Service Request Status Update" or "Transaction successful". Filter those out.

```python
# Know which subjects are auto-confirmations that need NO action
NO_ACTION_SUBJECTS = [
    "service request status update",
    "transaction successful on your",
    "your consignment status",
    "cheque book request",
    "account balance",
    "payment received",
    "interbank",
    "rtgs transfer",
    "neft transfer",
]

# Real action triggers (things a human actually needs to respond to or pay)
ACTION_TRIGGERS = [
    "reminder", "fee", "payment due", "overdue", "urgent",
    "review", "approval", "approve", "modification", "request",
    "kyc", "lease", "draft", "sign", "renew",
]

action_items = []
for e in other:
    subj_lower = e["subject"].lower()

    # Skip auto-confirmations
    if any(no in subj_lower for no in NO_ACTION_SUBJECTS):
        continue

    # Check for real action triggers
    if any(trig in subj_lower for trig in ACTION_TRIGGERS):
        action_items.append(e)

# Display action items
for i, e in enumerate(action_items, 1):
    sender_name = e["from"].split("<")[0].strip().strip('"') or e["from"]
    print(f"\n{i}. [{sender_name}]")
    print(f"   {e['subject']}")
```

### Phase 4: Get action-item context (two-pass fetch)

For only the action items, fetch full message snippet to provide actionable context:

```python
if action_items:
    action_emails = []
    for e in action_items:
        full = svc.users().messages().get(
            userId="me", id=e["id"], format="full"
        ).execute()
        e["snippet"] = full.get("snippet", "")[:250]
        action_emails.append(e)

    for i, e in enumerate(action_emails, 1):
        sender_name = e["from"].split("<")[0].strip().strip('"') or e["from"]
        print(f"\n{i}. [{sender_name}] — {e['subject']}")
        print(f"   → {e['snippet']}")
```

### Real-world examples (from Roshini R session, Jun 2026)

After running this pipeline on 100 emails (35 auto-sign-in noise removed → 65 meaningful):

**Top action items surfaced:**
1. **🔴 Fee Payment** — "Reminder!!! Transport fee for 2026-27" / "Reminder!!! 1st instalment of tuition fee for 2026-27" from Finance MAIS
2. **🔴 Autodesk License** — "RE: Autodesk Software License Review at DRA REALTY PVT Ltd" (final reminder EOD)
3. **🟡 Hudson Project** — "RE: BuxRanka Hudson Project - Modification Approval Costs and Advance Release" from Harsimran Singh (Godrej)
4. **🟡 Lease Draft** — "RE: Millers Road India Chai Office Building - Terms Discussed for Lease of Premises" (correction draft lease deed to review)
5. **🟡 Document Access** — "Share request for 'KDR PAN Copy.pdf'" / "Share request for 'KDR Passport 2028 First Page.jpg'" from Bharat
6. **🟡 Payroll Validation** — "Spreadsheet shared with you: 'DRA Payroll Validation Updated'" from Bharat
7. **📌 HDFC KYC** — "Urgent: Complete Your KYC Update, XX2101!" (belongs to Nishant, forward if not handled)
8. **📌 Occupancy Certificate** — "Ranka Iris Occupancy Certificate" (good news received, no action needed)

**Work-internal emails (DRAAS) correctly grouped:**
- Century Regalia unit details ×4 (from NDR)
- New lead from Housing.com for Ranka Aqua Greens
- Ranka Amber Architectural GFC (from Bhuvanesh)

**Banking correctly grouped and collapsed:**
- InterBank-NEFT Transfer Credit Alert ×4
- Account Balance Daily ×3
- Your consignment Status ×3

**Output template used (Telegram, no tables):**

```
📊 EMAIL SUMMARY — 06 Jun 2026, 10:00 PM IST

Total emails: 100
  |→ Sign in/out notifications: 35 (auto)
  |→ Meaningful: 65

📁 CATEGORIES:
🏦 Banking/Finance — 21
💼 Work (Internal) — 7
💰 Finance/Payments — 5
👤 Personal — 4
📎 Other — 24
📢 Marketing — 1
🔔 Notifications — 1

⚡ ACTION ITEMS:
1️⃣ 🔴 Fee Payment — Ruhan's School
   Transport fee + tuition fee reminder
   → Check amounts and pay

2️⃣ 🔴 Autodesk License — Final Reminder (EOD)
   → Reply with DRA's position on license review

3️⃣ 🟡 Hudson Project — Modification Costs
   Harsimran Singh (Godrej) / Haresh Buxani
   → Review thread, check with Nishant

...
```
