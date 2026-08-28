---
name: pending-actions-tracker
description: |-
  Track pending/outstanding actions, follow-ups, and items requiring periodic
  status checks across email threads, conversations, business operations, and
  ongoing processes. Maintains a durable record so the agent can report status
  when the user asks "what's pending?" or follow up on specific items.

  Trigger: user says "track this", "follow up on", "what's pending", "check
  status of", "add to tracker", "you haven't tracked X", "email analysis",
  "inbox triage", "check my emails", "what's in my inbox", "pending
  action analysis", "follow-up work analysis".
metadata:
  hermes:
    tags: [tracking, follow-up, pending, actions, productivity, reminders]
    author: Hermes curator
version: 1.0.0
---

# Pending Actions Tracker

## What This Skill Is For

The user often initiates processes that span days or weeks — card replacements,
insurance claims, regulatory filings, legal cases, vendor onboarding, email
replies awaiting a response, deliveries, etc. These need to be **tracked
durably** so the agent can:

- Report all outstanding items when asked "what's pending?"
- Check status on specific items proactively or on demand
- Connect related items across sessions (e.g., IndusInd card replacement
  awaiting dispatch → check email for dispatch SMS → update status)

## How Items Are Tracked

Each pending item is stored as a **memory entry** under target=`memory` with a
consistent format:

```
PENDING: <short title> | Initiated: <date> | Status: <status> | Next action:
<what to do next or watch for> | Source: <email thread id / conversation ref>
```

**Status values:** `in-progress`, `awaiting-reply`, `awaiting-delivery`,
`pending-review`, `resolved`, `stalled`

**When to add an item:**
- User sends an email requesting something that requires a response/timeline
- User initiates a process (card replacement, insurance claim, form filing)
- User asks you to "follow up on X" or "check the status of X"
- A reply arrives that moves the status forward — update the entry
- User mentions something in conversation that implies follow-up

## Specific Items Currently Tracked

See `references/current-items.md` for the live list.

## Workflow

### 1. Adding a new pending item

```text
PENDING: IndusInd Bank card replacement (card 1460 + add-on for Roshni)
| Initiated: 15 Jul 2026
| Status: awaiting-delivery
| Next action: Check email for dispatch SMS, follow up if not received by 24 Jul
| Source: Gmail thread Case ID 87895068, service refs 19617514654 / 19617632971
```

Call `memory(action='add', target='memory', content='...')` with the full entry.

### 2. Updating status

When new info arrives (e.g., a reply email, a phone call update, a passing
mention from the user), call `memory(action='replace', target='memory',
old_text='PENDING: <short title>', content='<updated entry>')` — match on the
short title text.

### 3. Reporting

When the user asks "what's pending?" or "any follow-ups?", search memory with
`session_search(query='PENDING:')` or `memory` tool for entries matching
`PENDING:` prefix. Return a clean summary grouped by status.

### 4. Resolving

When an item is fully done (cards received, claim settled, filing confirmed),
update the entry to `Status: resolved` so it can be pruned later.

### 5. Email Triage (Upstream Analysis)

When the user asks "email analysis", "inbox analysis", "check my emails",
"what's pending in my inbox", "inbox triage", or "follow-up work analysis",
run this workflow to scan, categorize, and identify items for tracking.

**Step 1 — Scope:**
- Ask which account(s): primary (ndr@draas.com / google-draas), others if
  specified. The user often says "primary only" by default.
- Ask time period: default is last 7 days unless specified.

**Step 2 — Scan inbox via Gmail API:**
```
service = build_service('gmail', 'v1', service_name='google-draas')
results = service.users().messages().list(
    userId='me', q='in:inbox after:YYYY/MM/DD', maxResults=50
).execute()
```

For each message, check the thread to determine direction:
```
thread = service.users().threads().get(
    userId='me', id=thread_id, format='metadata',
    metadataHeaders=['From']
).execute()
last_msg = thread['messages'][-1]
last_from = last_msg['payload']['headers'][...]['value']
last_from_ndr = 'ndr@draas.com' in last_from.lower()
```

**Step 3 — Categorize into 4 buckets:**

| Category | Condition |
|---|---|
| 🔴 **Needs reply** | Last message on thread is NOT from user |
| 🟡 **Follow-up due** | User sent last message, awaiting their reply |
| 🟠 **Action required** | Keyword match: invoice, bill, approval, deadline, payment, sign, urgent, "action required", execute, compounding, notice |
| ⚪ **FYI** | Newsletters, notifications, CC'd, delivery reports, automated alerts, bank txns |

Also check sent folder for threads where user sent last message with no
replies yet: `in:sent after:YYYY/MM/DD` — check each thread, if user's
message is the last one, flag as follow-up due.

**CRITICAL — Cross-reference sent folder before flagging:**

Before marking any inbox thread as "needs reply" or "action required",
check the sent folder to see if the user has already taken action:

```python
# For every flagged thread, check sent messages on same thread
sent_on_this_thread = service.users().messages().list(
    userId='me', q=f'in:sent after:YYYY/MM/DD threadid:{thread_id}'
).execute().get('messages', [])
```

Alternatively, batch-check all today's sent messages and flag threads
the user has already handled:

```python
sent_msgs = service.users().messages().list(
    userId='me', q='in:sent after:YYYY/MM/DD', maxResults=50
).execute().get('messages', [])
# Build a set of thread_ids the user has replied to / forwarded today
handled_threads = set()
for s in sent_msgs:
    sm = service.users().messages().get(
        userId='me', id=s['id'], format='metadata',
        metadataHeaders=['Subject']
    ).execute()
    handled_threads.add(sm.get('threadId'))
```

**Handled signals to recognize:**
| Signal | Meaning | Category |
|---|---|---|
| User forwarded email to someone ("Fwd: ...") | Delegated | ✅ Handled — not pending on user |
| User replied on same thread today | Ball is in their court | 🟡 Follow-up due (awaiting them) |
| User sent thread had a reply from recipient | Ongoing conversation | 🟡 Follow-up due |
| No sent activity on thread | User hasn't acted | 🔴 Needs reply or 🟠 Action required |

**Thread-breaking edge case:** If a user composes a fresh email (not a
reply-all) with the same subject, Gmail may assign a different thread ID.
To catch this, also match by subject keyword among today's sent messages.

**Step 4 — Report (apply sent-folder filter first):**
- Present in clean categories with subject, from, date
- Note UNREAD status with 🔔 marker
- Filter out noise: daily "Please sign in/out" automated messages,
  delivery status notifications, routine bank alerts
- Flag time-sensitive items (RERA notices, payment reminders, show cause
  notices, sign-off requests) with priority markers

**Step 5 — Track:**
For any item needing durable follow-up across sessions, add a PENDING entry:
- Card/delivery awaiting fulfillment → `awaiting-delivery`
- Regulatory/legal notices with deadlines → `pending-review`
- Emails sent awaiting reply → `awaiting-reply`
- Processes initiated but stalled → `stalled`

**Email Attachment Extraction (scanned PDFs):**

When an email has a PDF attachment that turns out to be scanned images (no
extractable text via PyMuPDF), use this workflow:

```
# 1. Download attachment via Gmail API
att_data = service.users().messages().attachments().get(
    userId='me', messageId=msg_id, id=att['body']['attachmentId']
).execute()
data = base64.urlsafe_b64decode(att_data['data'])

# 2. Save and convert to images
pdftoppm -png -r 300 input.pdf /tmp/pages/page

# 3. OCR each page via vision_analyze
vision_analyze(image_url='/tmp/pages/page-1.png',
               question='Extract ALL text...')
```

This is faster and more reliable than OCRmyPDF for short documents and avoids
library dependency issues.

## Pitfalls

- **Don't over-track.** Only track items with a defined next-action state or
  waiting-on-external-party status. One-off questions the user asked and got
  answered in the same session don't need tracking.
- **Don't track in cron jobs.** Cron jobs have their own lifecycle. Pending
  items are checked on-demand via user query, not via automated polling
  (unless the user explicitly asks for a cron tracker).
- **Expiry:** If a pending item has been `resolved` for 30+ days, remove it
  from memory to free space.
- **Memory is capped at 2,200 chars.** Consolidate multiple PENDING entries
  into a single compact block when space runs low, or remove resolved ones
  first.

## Related Skills

- The **Email Triage** workflow (§5 above) is the upstream analysis that
  scans Gmail and identifies items needing tracking. Run inbox triage first
  to discover new pending items, then add them here as PENDING entries.
- `google-workspace` — Gmail API access (used by the triage workflow)
- `ocr-and-documents` — OCR techniques for scanned PDF attachments
