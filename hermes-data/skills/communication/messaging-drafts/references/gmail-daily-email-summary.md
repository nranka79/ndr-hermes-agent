# Gmail Daily Email Summary — All Emails for Today with Action Categorization

**Trigger:** User says "summarize all my emails for the day" or "what came in today" or "any email that required any action" — requesting a categorized briefing of all emails received today, not a specific email.

## Workflow

### Step 1 — Fetch Today's Incoming Emails

Query Gmail with `after:YYYY/MM/DD` for today's date:

```python
from tools.gws_auth import build_service
gmail = build_service("gmail", "v1")
results = gmail.users().messages().list(
    userId="me",
    q="after:2026/06/17",
    maxResults=50
).execute()
```

**Filter out SENT items** — only show received emails:
```python
for m in msgs:
    msg = gmail.users().messages().get(userId="me", id=m["id"], format='metadata', metadataHeaders=['From','To','Subject','Date']).execute()
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    label_ids = msg.get('labelIds', [])
    is_sent = 'SENT' in label_ids
    if not is_sent:
        # Process as incoming email
        ...
```

### Step 2 — Categorize by Action Level

Sort emails into tiers:

| Tier | Label | Criteria |
|------|-------|----------|
| 🔴 Requires Action | Action needed from the user | Directly addressed to user, asks for response/decision/approval. Examples: bounced draft, payment failure, tax notice, content approval request |
| 🟡 FYI / On CC | User is CC'd or forwarded | No direct ask but relevant context. Examples: team updates, project status emails where user is in CC |
| ⚪ Info / Newsletters | No action | Newsletters, marketing emails, bank alerts, generic notifications |

**How to determine action level:**
- Check if the email asks a question or requests a decision
- Check if the user's name is in the To: header (not just Cc:)
- Check if the email contains a task or follow-up item
- For forwarded emails: check the original message context
- Bank alerts (NACH, debit failures, recurring payment failures) are 🔴 if a payment failed, ⚪ if it's just a balance update

### Step 3 — Get Full Body for Actionable Emails

For each 🔴 email, fetch the full body to summarize the key points:

```python
parts = [msg['payload']]
text = ''
while parts:
    part = parts.pop(0)
    if part.get('mimeType') == 'text/plain' and part.get('body',{}).get('data'):
        text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
        break
    if part.get('parts'):
        parts.extend(part['parts'])
```

### Step 4 — Present Structured Daily Briefing

Format consistently:

```
📧 Email Summary for {Day, Date}

---

🔴 Requires Action

1. {Subject line}
   From: {Sender}
   {Brief summary of what's needed}

2. ...

---

🟡 FYI / On CC

3. {Subject}
   From: {Sender}
   {Brief context — no action needed unless...}

---

⚪ Info / Newsletters

- {Subject} — {Sender}
- ...

---

Top priority: {Single line about the most urgent item}
```

### Step 5 — Offer Next Steps

After the summary, ask:
- "Want me to draft a reply for any of these?"
- Include specific links: "🔗 View email(gmail_link)" for each actionable item

## Pitfalls

- **Do NOT show sent items:** Filter out 'SENT' in label_ids — the user's own sent emails clutter the briefing
- **Newsletter overlap:** If the same newsletter service sends duplicates (e.g., Liases Foras sends twice), deduplicate by subject line
- **Bounced delivery notifications:** Bounce emails from postmaster@ look like incoming mail but are about YOUR sent email. Flag them as 🔴 — they need re-sending
- **Not all emails need full body fetch:** Only fetch the body for 🔴 emails. 🟡 and ⚪ can stay at metadata level to save API calls
- **Voice name ambiguity:** If the user refers to an email by a name that doesn't match, check all addresses in To/Cc headers — the user may be using a short name
- **Undeliverable bounces:** The bounce notification's From: is postmaster@domain.com but the original recipient's address is in the body. Include that context when summarizing
