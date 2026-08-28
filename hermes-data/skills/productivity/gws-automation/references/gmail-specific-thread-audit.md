# Gmail Specific Thread Audit

**When the user asks:** "Check my emails for the last N days" + "track these specific threads" + "what's the status on [company/person]"

**Example trigger:** "Check my emails for the last 3 days. Track Bajaj Life Insurance renewal and Godrej Fund Ventures approval. Highlight anything needing my response."

## Workflow

### Phase 1 — Broad Scan (last N days)

```python
from tools.gws_auth import build_service
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

svc = build_service('gmail', 'v1')
tz = timezone(timedelta(hours=5, minutes=30))  # IST

end_date = datetime.now(tz)
start_date = end_date - timedelta(days=N)
query = f"after:{start_date.strftime('%Y/%m/%d')} before:{end_date.strftime('%Y/%m/%d')}"

results = svc.users().messages().list(userId='me', q=query, maxResults=100).execute()
messages = results.get('messages', [])
```

**Read each message** (use `format='metadata'` with `metadataHeaders=['From','To','Subject','Date']`), then:

- Mark `🔴 UNREAD` for unread messages
- Present chronologically (oldest first or newest first — ask user preference, default newest)
- Key header fields: Date, From, Subject, ID

### Phase 2 — Identify Work-Critical Emails Needing Response

Filter the broad scan for emails that:
- Are from work contacts (DRAAS team members, partners, vendors, consultants)
- Have action-requesting subjects ("needs response", "please review", "approval needed", "action required", "pending", "update needed")
- Are from external parties with project-specific subjects
- Are thread continuations where the user was the last respondent

**Priority levels:**
| Priority | When |
|----------|------|
| 🔴 **High** | External party awaiting user's reply; team member awaiting user's input for next action; regulatory/time-sensitive deadline |
| 🟡 **Medium** | Update/deliverable received needing review; CC on important thread |
| 🔵 **Low** | FYI/confirmation/agreement; no action needed |

### Phase 3 — Deep-Dive on Specific Named Threads

For each thread the user asks to track:

1. **Search broadly** — don't restrict to last N days. The thread likely started earlier.
   ```python
   # Try specific query first
   results = svc.users().messages().list(
       userId='me',
       q='(company OR person_name OR project) after:YYYY/MM/DD',
       maxResults=20
   ).execute()
   
   # If not found, try broader
   results = svc.users().messages().list(
       userId='me',
       q='domain OR simpler term',
       maxResults=20
   ).execute()
   ```

2. **Read the full thread chronologically** — get each message's body to understand the full narrative.

3. **Key checks:**

   - **Bounce detection:** Check for `postmaster@domain.com` or `mailer-daemon` senders in the thread. Read the bounce body — it often reveals the actual error (recipient not found, mailbox full, server rejected).
   
   - **Overdue response detection:** If an external party promised an answer in "1-2 days" but it's been N days with no follow-up, flag it. Compare `Date` header timestamps.
   
   - **Stale thread detection:** If the user was the last to send and received no reply, note the gap.

4. **For each tracked thread, present:**
   - Thread subject
   - Chronological timeline (date + key event per email)
   - ✅ What's resolved
   - ⚠️ What's blocked/stuck (and why — e.g., bounced email, awaiting external reply)
   - ❓ Next action (who needs to do what)

### Phase 4 — Structured Summary

Present to the user in this format:

```
## 📧 Email Scan: Last N Days

### 🔴 [TRACKED THREAD 1] — Status: Stuck / Awaiting / Resolved

| Date | From/To | Detail |
|---|---|---|
| ... | ... | ... |

**Bottom line:** What happened and what's needed next.

### 🔴 [TRACKED THREAD 2] — Same format

### ⚠️ OTHER EMAILS NEEDING ATTENTION

| Priority | Sender | Subject | Action Needed |
|---|---|---|---|
| High/Medium/Low | ... | ... | ... |
```

### Pitfalls

| Pitfall | Fix |
|---------|-----|
| **Email search returns nothing** when you know the thread exists | Expand date range to `all`; try single-word terms instead of phrases; try the sender's email domain alone |
| **Bounce detection** — the bounce may name a DIFFERENT address than the one the user sent to (internal forwarding alias) | Read the bounce body carefully. The `Remote Server returned '550 5.1.10 RESOLVER.ADR.RecipientNotFound'` line shows the actual failed address |
| **Timezones in Date headers** — Gmail stores in sender's local time | Normalize all dates to IST (UTC+5:30) using `parsedate_to_datetime` + `.astimezone(tz)` for consistent comparison |
| **Thread with 50+ emails** — reading all bodies is expensive | Read only messages where the user's address is in To/CC (means it's directed at them) OR messages with new subject lines |
| **Session-user mismatch** — searching the wrong person's inbox | ALWAYS run pre-flight identity check before first API call |
| **100 message limit** — Gmail API returns max 100 per page | If the period has >100 messages, the broad scan is truncated. Note to user: "Showing last 100 of N+ messages from this period." |
| **Contact name not found in inbox** (e.g., "Littika" from Bajaj) | The conversation may be on WhatsApp or another platform, not email. State this clearly — don't keep searching with different queries. |
