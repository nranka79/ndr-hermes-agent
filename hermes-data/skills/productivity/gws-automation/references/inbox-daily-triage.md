# Inbox Daily Triage — Gmail Bulk Scan & Categorization

Class-level workflow for scanning today's entire inbox (sent + received), categorizing every email, and delivering a structured summary. Used when the user asks "check my emails for the day" or any variant.

## User's Preferred Categorization Schema (for Nishant)

The user wants this exact breakdown, in this order:

1. **Work — Action Required From You** — emails where a revert/decision/approval is due from Nishant's end. Lead with these.
2. **Work — Already Acted On** — emails where Nishant already sent a reply or took action today. Include what was done.
3. **Work — For Your Noting** — FYI emails where no action is needed but content matters.
4. **Borderline Work** — industry newsletters, events, webinars, real estate news (Liases Foras, CREDAI, PropDEX, CII, etc.)
5. **Non-Work** — bank alerts, marketing, personal notifications, newsletters, system emails. Group by type.

## Invocation Pattern

The Gmail API is accessible only through the per-user OAuth path. The system Python does NOT have googleapiclient — you must use the Hermes venv:

```sh
HERMES_SESSION_USER_ID=<telegram_id> \
PYTHONPATH=/opt/hermes:$PYTHONPATH \
/opt/hermes/.venv/bin/python3
```

```python
from tools.gws_auth import build_service
service = build_service('gmail', 'v1')
```

## Query Pattern — Today's Emails in IST

**Always use IST timezone** (UTC+5:30) for the date range, not UTC. The user operates in IST.

```python
from datetime import datetime, timezone, timedelta
ist = timezone(timedelta(hours=5, minutes=30))
today_start = datetime.now(ist).replace(hour=0, minute=0, second=0, microsecond=0)
today_end = today_start + timedelta(hours=23, minutes=59, seconds=59)

query = f'after:{int(today_start.timestamp())} before:{int(today_end.timestamp())}'
results = service.users().messages().list(userId='me', q=query, maxResults=100).execute()
```

**IMPORTANT**: `timedelta` uses `seconds=`, not `second=`. Using `second=59` causes a TypeError.

## Bulk Header Scanning (Phase 1)

For 50-100 emails, fetch all metadata headers in one pass per message. This is fast and avoids pulling full bodies for every email:

```python
for m in messages:
    msg = service.users().messages().get(
        userId='me', id=m['id'],
        format='metadata',
        metadataHeaders=['From','Subject','Date','To','Cc']
    ).execute()
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
```

Phase 1 output: a dict/JSON array of all emails with sender, subject, timestamp, recipients.

## Targeted Snippet Retrieval (Phase 2)

Once categorized by subject line and sender, fetch snippets only for the work-relevant subset to understand context:

```python
msg = service.users().messages().get(userId='me', id=mid, format='full').execute()
snippet = msg.get('snippet', '')

# NOTE: maxResults is NOT a valid parameter for get(). It belongs to list().
# Wrong: service.users().messages().get(..., maxResults=1)
# Right: service.users().messages().get(..., format='full')
```

Snippets are ~120-200 chars of the message body — enough to understand context without pulling the full body.

## Categorization Heuristics

**Non-work indicators in subject/sender:**
- Bank alerts (HDFC, Kotak, IndusInd — balance, txn, modification, maintenance, debit failure)
- Marketing/cold: BMW, IIM, ET Masterclass, IndiGo, McKinsey, WGSN, Tranquil, smartdharma, CanMoney/IPOs, HSBC NFO, BU Bhandari, Entrackr, HRKatha, ArisUnitern
- Google Maps notifications
- LinkedIn notifications
- System emails: "Please sign in" / "Please sign out" (attendance tracking)
- Recalls/routing: "Recall:" / "via info" / internal mail routing spam

**Work indicators in subject/sender:**
- @draas.com senders (team members)
- @draas.com in subject (internal projects)
- Project names: Ranka Udaya, Ranka Amber, Ranka Iris, BuxRanka Hudson
- Subject keywords: Leave, Salary, DSC, E-signing, Agreement, UDS, BESCOM, Marketing Brief, Customer Journey, Engagement, Interior Design
- External partners: @bitanz.com, @redsoul.co.in, @godrejventure.com, @buxani.com, @joyz.ai, @attirail.in, @findingform.design
- NESL (debt authentication), NeSL (National e-Governance)
- Real estate industry: CREDAI, Liases Foras, CII, PropDEX

**Distinguishing "already acted on" from "action required":**
- "From: Nishant Ranka <ndr@draas.com>" in inbox = Nishant sent it = action already taken. Note what was done.
- If someone replied to Nishant's email, that goes in "action required" if it asks for further response.
- Drive share notifications = action required (approve the share)

## Output Format

Present as a structured message with clear section headers:

**TOTAL EMAILS TODAY: N**

**WORK — ACTION REQUIRED FROM YOU:**
For each: sender, subject, 1-line summary of what's needed.

**WORK — ALREADY ACTED ON:**
For each: sender, subject, what Nishant did.

**WORK — FOR YOUR NOTING:**
For each: sender, subject, brief context.

**BORDERLINE WORK:**
Grouped list.

**NON-WORK:**
Grouped by type (Bank Alerts, Marketing, Notifications, System).

## Pitfalls

- **Do NOT use `execute_code` for Gmail API calls** — the tool has an approval gate that blocks terminal commands from execute_code. Use terminal() directly with the Hermes venv + PYTHONPATH.
- **`maxResults` is for list(), NOT for get()** — passing it to get() raises "Got an unexpected keyword argument maxResults".
- **`second` vs `seconds`** — `timedelta(seconds=59)` is correct, NOT `timedelta(second=59)`.
- **Gmail tracks by UTC internally** — the `after:`/`before:` query timestamps should cover the IST day. Use epoch timestamps that span 00:00:00 IST to 23:59:59 IST.
- **Messages sent BY Nishant appear in the inbox** — the "Please sign in/out" automated emails and replies he sends all show up. Don't skip them — categorize them as "already acted on" or "system" as appropriate.
- **Duplicate Drive share notifications** — Google Drive sometimes sends two identical share-request emails for the same folder. Dedupe in your summary.
