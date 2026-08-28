# Not-Spam Whitelist Check (Daily Cron)

Reference for the daily cron job that reads whitelist rules from a Google Sheet, checks Gmail's SPAM folder, and moves matching messages back to INBOX.

## When to Use

- User says "run the not-spam check", "check whitelist", "move matching spam to inbox"
- Cron job: runs daily to recover false-positive spam from trusted senders
- The `email` skill's "Sender Blacklisting" section references this as the reverse operation

## Sheet Structure

Spreadsheet: `1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0`  
Tab: `Whitelist`  
Range: `A:I`

### Column Layout (confirmed Aug 2026)

| Col | Header | Usage |
|-----|--------|-------|
| A | `#` | Row number (identifier, referenced in rule names) |
| B | `Category` | Broad category of the whitelist rule (e.g. "Financial", "Legal", "Internal") |
| C | `From Email / Domain` | **The match target** — email address (exact) or domain (with @ prefix for exact-match or raw for domain) |
| D | `To Email` | Target recipient email (usually NDR's address) |
| E | `Subject Keywords` | Comma or pipe-separated keywords for subject matching |
| F | `Content Description` | Human-readable description of what this rule covers |
| G | `Rule Type` | One of: `exact_from`, `domain_from`, `subject_contains`, `combined` |
| H | `Date Added` | When the rule was created |
| I | `Notes` | Additional context |

## Rule Types

| Rule Type | Column C meaning | Match Logic |
|-----------|-----------------|-------------|
| `exact_from` | Full email address | `sender_email == value` |
| `domain_from` | Domain name (with or without @) | `sender_email.endswith('@' + value)` |
| `subject_contains` | Email (not used for match) | Keywords from column E searched in subject |
| `combined` | Domain | Both domain match AND keyword match required |
| `domain` | (alias for domain_from) | Same as domain_from |

Plus a hardcoded catch-all: any sender with `@draas.com` domain is always whitelisted.

## Core Workflow

### Step 1: Build services

```python
from tools.gws_auth import build_service

gmail = build_service("gmail", "v1", service_name="google-draas")
sheets = build_service("sheets", "v4", service_name="google-draas")
```

Primary account is `google-draas` (ndr@draas.com). Fall back to `google-ahfl` / `google-gmail` if needed.

### Step 2: Read whitelist rules

```python
result = sheets.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range="Whitelist!A:I"
).execute()
values = result.get("values", [])
header = values[0]
# Skip header, parse rows into rules
rules = []
for row in values[1:]:
    if len(row) < 7:  # Need at least columns A, C, G
        continue
    email_or_domain = row[2].strip().lower()
    rule_type = row[6].strip().lower()
    subject_kw = [k.strip().lower() for k in row[4].replace("|", ",").split(",") if k.strip()]
    rules.append(dict(rule_type=rule_type, email_or_domain=email_or_domain, keywords=subject_kw))
```

### Step 3: Fetch SPAM messages

```python
spam_messages = []
page_token = None
while True:
    query = gmail.users().messages().list(
        userId="me", labelIds=["SPAM"], maxResults=200,
        pageToken=page_token
    ).execute()
    batch = query.get("messages", [])
    spam_messages.extend(batch)
    page_token = query.get("nextPageToken")
    if not page_token or len(spam_messages) >= 200:
        break
```

### Step 4: Check each message against rules

```python
for msg in spam_messages:
    msg_id = msg["id"]
    msg_detail = gmail.users().messages().get(
        userId="me", id=msg_id, format="metadata",
        metadataHeaders=["From", "Subject"]
    ).execute()
    
    headers = {h["name"].lower(): h["value"] for h in msg_detail["payload"]["headers"]}
    sender = headers.get("from", "")
    subject = headers.get("subject", "")
    
    # Extract email from "Name <email>" format
    email_match = re.search(r"<([^>]+)>", sender)
    sender_email = email_match.group(1).lower() if email_match else sender.lower().strip()
    sender_domain = sender_email.split("@")[-1] if "@" in sender_email else sender_email
```

### Step 5: Match & move

```python
matched = False
# Catch-all: @draas.com internal
if sender_domain == "draas.com":
    matched = True

if not matched:
    for r in rules:
        if r["rule_type"] == "exact_from" and sender_email == r["email_or_domain"]:
            matched = True
        elif r["rule_type"] in ("domain_from", "domain"):
            # Handle domain values with or without @ prefix
            domain = r["email_or_domain"]
            if domain.startswith("@"):
                matched = sender_email.endswith(domain)
            else:
                matched = sender_email.endswith("@" + domain) or sender_email.endswith("." + domain)
        elif r["rule_type"] in ("subject_contains", "subject"):
            for kw in r["keywords"]:
                if kw in subject.lower():
                    matched = True
                    break
        elif r["rule_type"] == "combined":
            domain = r["email_or_domain"]
            domain_match = (sender_email.endswith("@" + domain) if not domain.startswith("@")
                          else sender_email.endswith(domain))
            if domain_match:
                for kw in r["keywords"]:
                    if kw in subject.lower():
                        matched = True
                        break
        if matched:
            break

if matched:
    gmail.users().messages().modify(
        userId="me", id=msg_id,
        body={"removeLabelIds": ["SPAM"], "addLabelIds": ["INBOX"]}
    ).execute()
```

## Known Pitfalls

1. **`batchGet` does NOT exist on Gmail messages resource** — `gmail.users().messages().batchGet(...)` raises `AttributeError: 'Resource' object has no attribute 'batchGet'`. You MUST iterate one message at a time with individual `get()` calls.
2. **Sheet column order** — Do NOT assume the column layout matches a configuration param or mental model. Always print the header row first and verify column indices. As of Aug 2026 the layout is: A=#, B=Category, C=From Email/Domain, D=To Email, E=Subject Keywords, F=Content Description, G=Rule Type, H=Date Added, I=Notes.
3. **`gmail.users().messages().get(format="metadata", metadataHeaders=[...])`** — This is the sanctioned way to get only headers without fetching the full body. The `metadata` format is efficient and avoids large payloads.
4. **Rate limits / timeout for large batch** — Individual `get()` + `modify()` calls for ~100 messages works fine (no quota errors), but a Python script doing 108 individual modify calls can hit the 180s terminal timeout. For volumes > 100, split into batches: move the first batch in one script run, then re-fetch remaining spam and move those in a second run. This also ensures newly-arrived spam is caught. Alternatively, use `gmail.users().messages().batchModify()` for the full batch in one API call.
5. **Duplicate `#` in the sheet** — Some rows can share the same row number (e.g. `#17` is used twice, `#25` used twice). Row number is NOT a unique key — index by sheet row position instead.
6. **No deletions** — The script must NEVER delete spam. It only moves matching messages back to INBOX. Non-matching messages are left untouched in SPAM.
7. **Column B is NOT an enable/disable flag** — Column B is `Category` (e.g. "Legal", "Banking - HDFC", "Internal"). It is a human-readable label, NOT a boolean `enabled`/`disabled` column. Do NOT parse it as `enabled = row[1].lower() == 'yes'` — that incorrectly disables all rules (since no category value equals "yes") and results in zero matches. All rules in this sheet are effectively enabled.
8. **`@draas.com` catch-all must NOT have a `to_email` filter** — The `@draas.com` domain rule (row 12) catches internal DRAAS emails sent TO any @draas.com address, not just `ndr@draas.com`. In practice, services like Internshala send emails as `marketing@draas.com` which get forwarded/delivered to `ndr@draas.com`. The matching logic must NOT apply a `to_email` filter on this rule — otherwise all marketing@draas.com spam incorrectly stays in spam. Only apply `to_email` filtering on rules where the whitelist explicitly specifies it (column D is non-empty).
9. **Domain values may or may not have `@` prefix** — Some `domain_from` rules store the value with `@` (e.g. `@draas.com`, `@drahomes.in`, `@kotak.com`) and some without (e.g. `manipalhospitals.com`, `jio.com`, `google.com`). The matching logic must handle both: if the value starts with `@`, check `sender_email.endswith(value)`; otherwise check `sender_email.endswith('@' + value)` or `sender_email.endswith('.' + value)`.
10. **`q='in:spam'` vs `labelIds=['SPAM']`** — Both work for fetching spam. `q='in:spam'` is more reliable because it can be combined with other search operators (date ranges, senders, etc.). Use `labelIds=['SPAM']` only when you want unfiltered access to the SPAM label without the additional Gmail query parsing.

## JSON Output Format

At the end of the check, print structured JSON for the cron report:

```json
{
  "checked": 66,
  "moved": 1,
  "moved_details": [
    {
      "sender": "marketing@draas.com",
      "subject": "Get a complimentary upgrade to Internshala Premium!",
      "rule": "catch-all: draas.com internal"
    }
  ],
  "errors": []
}
```

## Related

- `gmail-sender-blacklist.md` — the reverse operation (move inbox messages to SPAM)
- `email` skill Section 5 — Sender Blacklisting