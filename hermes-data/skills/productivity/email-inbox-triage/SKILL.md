---
name: email-inbox-triage
description: |-
  Scan and categorize Gmail inbox messages by urgency and action type.
  Produces a categorized report (needs reply / follow-up due / action required / FYI)
  for the user and updates the pending-actions-tracker with items needing durable
  follow-up.

  Trigger: user says "email analysis", "inbox triage", "scan my emails",
  "what needs my attention", "check my inbox", "do my email analysis",
  "what's in my inbox that I need to act on", "review my pending emails".
metadata:
  hermes:
    tags: [gmail, inbox, triage, email-analysis, productivity]
    author: hermes-agents
version: '1.0.0'
related_skills:
  - pending-actions-tracker
  - google-workspace
---

# Email Inbox Triage

## What This Skill Is For

The user asks you to scan their email inbox(es) and categorize messages by what
needs their attention. This is a recurring request — done on 8 Jul, 10 Jul,
18 Jul, and 25 Jul 2026. Each time the workflow is:

1. **Scope** — which account(s), how far back (default: last 7 days)
2. **Scan** — pull inbox messages + sent items from that period
3. **Categorize** — classify each thread by who owes whom
4. **Report** — present a clean categorized summary
5. **Track** — update pending-actions-tracker with new items found

## Accounts

Use `gws_resolve_account` (no args) to list every known account and its live
auth status. Common accounts for this user:

| Key | Email | Purpose |
|-----|-------|---------|
| google-draas | ndr@draas.com | Primary work email |
| google-ahfl | ndr@ahfl.in | AHFL secondary |
| google-gmail | nishantranka@gmail.com | Personal |

**Always confirm scope with the user.** When in doubt, start with primary
(google-draas / ndr@draas.com) and offer to do others.

**"All my accounts" (2026-08-13):** when the user explicitly says "all accounts" /
"across all accounts", run the triage script for EACH vault account in parallel
(google-draas + google-ahfl + google-gmail). Deliver one combined report grouped by
importance (🔴 immediate → 🟡 follow-ups → 🟠 action → ⚪ later), with per-account
context labels on each item. The personal gmail account is almost entirely noise
(Amazon, newsletters, e-voting notices) — filter hard there; the work account carries
the actionable threads. When the user asks for "a short summary from the entire
conversation thread", fetch full threads for the important items (see Step 9) and give
a 2-4 line digest per thread, not just the subject line.

## Workflow

### Step 1 — Confirm scope

Ask: which account? how many days back? Default is primary account, last 7 days.

### Step 2 — Build Gmail service

```python
from tools.gws_auth import build_service
service = build_service('gmail', 'v1', service_name='google-draas')
```

Replace `google-draas` with the vault key resolved in step 1.

### Step 3 — Write the scan script to a file (avoid shell quoting issues)

Write the analysis script to `/tmp/email_triage.py` and run it via terminal.
This avoids the nested-quote problems that appear when passing inline Python
through `-c`.

### Step 4 — Core queries

**Inbox messages from the period:**
```python
query = f"in:inbox after:{date_from}"
results = service.users().messages().list(userId='me', q=query, maxResults=50).execute()
```

**Sent messages from the period:**
```python
sent_query = f"in:sent after:{date_from}"
sent_results = service.users().messages().list(userId='me', q=sent_query, maxResults=50).execute()
```

**Action-specific keywords:**
```python
action_q = f"in:inbox (invoice OR bill OR approval OR deadline OR payment OR 'action required' OR 'please review' OR sign OR execute OR urgent) after:{date_from}"
```

### Step 5 — Thread analysis (the key pattern)

For each inbox message, determine the last sender in its thread:

```python
thread = service.users().threads().get(
    userId='me', id=thread_id,
    format='metadata',
    metadataHeaders=['From']
).execute()
last_msg = thread['messages'][-1]
last_headers = {h['name']: h['value'] for h in last_msg['payload']['headers']}
last_from = last_headers.get('From', '')
```

**Decision matrix:**

| Last sender is user? | Current sender is user? | Category |
|---|---|---|
| No | No | **FYI** (CC'd, notification, group thread) |
| No | Yes | Rare — skip (user's own msg in inbox) |
| Yes | No | **Follow-up due** (user waiting on reply) |
| Yes | Yes | **FYI** (user replied to own thread) |

If the thread API call fails, fall back to a conservative categorization:
if current sender is NOT the user → **Needs reply** (conservative)

**For sent messages:** check if the user's sent message is the last one on the
thread. If yes → **Follow-up due** (awaiting reply). Deduplicate by thread_id.

### Step 6 — Categorization

| Label | Color | Meaning |
|---|---|---|
| 🔴 Needs reply | High urgency | Someone wrote to user last, they owe a response |
| 🟡 Follow-up due | Medium | User sent last message, waiting on others |
| 🟠 Action/Urgent | High | Invoices, approvals, deadlines, payments, sign-offs |
| ⚪ FYI | Low | Newsletters, CC'd, notifications, delivery reports |

Filter out noise: automated "Please sign in / sign out" attendance reminders,
transaction alerts, marketing emails, daily security summaries. These should go
to FYI or be omitted entirely if they dominate the results.

### Step 7 — Check pending tracker

After the inbox scan, load the `pending-actions-tracker` skill and check its
`references/current-items.md` for items whose "next action" was time-based (e.g.
"check for dispatch SMS by ~24 Jul"). Add a status line in the report.

### Step 8 — Report format

Present as a clean categorized list. One line per item, grouped by category.
Labeled emoji headers. Brief subject + sender + date. Avoid table syntax
(Telegram doesn't render tables — use key: value lines or bullet lists).

End with a summary line:
```
SUMMARY: 0 needs reply | 3 follow-ups due | 5 action items | 10 FYI
```

Close with actionable offers: "Want me to read/summarize any thread? Draft a reply? Check a specific status?"

### Step 9 — Reading full thread content on demand

When the user says "elaborate", "read the whole chain", "what's the latest",
"give me a summary from the entire conversation thread", or asks about a
specific email from the report:

**Fastest path: run `scripts/thread_summaries.py <service_name> "<subject keyword>" ["more queries"...]`** — finds each thread by subject search and prints every message (date, from, subject, first ~350 chars of body). Write it once, reuse it. It handles search → thread fetch → MIME decode for you.

1. **Search for the thread** — Subject keywords alone often fail if the API search differs from web UI. Use a multi-strategy approach:
   - First try `subject:(keyword)` syntax
   - Fall back to `from:sender subject:keyword`
   - Fall back to just the sender email and scan subjects
   - **Do NOT use `in:any`** — the Gmail API rejects it, unlike the web UI.

2. **Fetch the full thread** with `format='full'`:
   ```python
   thread = service.users().threads().get(userId='me', id=thread_id, format='full').execute()
   ```

3. **Decode bodies recursively** — messages have nested MIME parts:
   ```python
   import base64
   def decode_body(payload):
       if 'parts' in payload:
           text = ''
           for part in payload['parts']:
               mime = part.get('mimeType', '')
               if mime == 'text/plain' and 'data' in part.get('body', {}):
                   text += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
               elif 'parts' in part: text += decode_body(part)
               elif mime.startswith('text/') and 'data' in part.get('body', {}):
                   text += base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='replace')
           return text
       elif 'body' in payload and 'data' in payload['body']:
           return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
       return '(no text)'
   ```

4. **Present a digest** — per-message: date, from, to, first ~500 chars. Flag the latest message. Summarise what happened and current status.

5. **Write script to `/tmp/`, run via terminal** — `execute_code` sandbox lacks `gws_fetch_token` and can't access Gmail. Same pattern as the main triage script.

6. **Offer next action** — after showing thread, offer to draft a reply, forward, or escalate.

## Pitfalls & Lessons

- **CRITICAL: Use actual email, not SERVICE_NAME, for user-identity checks** —
  `SERVICE_NAME` is the vault key (`google-draas`, `google-ahfl`) — NOT an email
  address. Comparing `SERVICE_NAME in from_header.lower()` will *never* match.
  Always resolve the real email first via the Gmail profile API:
  ```python
  profile = service.users().getProfile(userId='me').execute()
  USER_EMAIL = profile.get('emailAddress', '').lower()
  def is_from_user(addr): return USER_EMAIL in addr.lower()
  ```
  The script uses this pattern; if you hand-roll a quick analysis, don't
  skip this step.

- **Automated emails** — Attendance systems ("Please sign in for the day"),
  sign-out reminders, and daily bot emails can flood the "follow-up due"
  category because the system sends them to the user and they dominate the
  sent-items scan. Filter by subject on BOTH inbox and sent scans. The
  `SKIP_SENT_SUBJECTS` list in the script catches these.
  Note: "Please sign in for the day" reminders are also auto-trashed daily by a
  cron job (see `gws-automation` skill → `references/signin-cleanup-cron.md`),
  so they may legitimately be missing from older scans.

- **Corporate governance mail in personal gmail is ACTIONABLE, not FYI** — AGM
  notices (with proxy form MGT-11 attached), CDSL/NSDL e-voting reminders (Max
  Financial, Bharat Forge postal ballot), and share-related notifications land in
  nishantranka@gmail.com. They look like noise but carry deadlines (e-voting
  windows, proxy deposit ≥48h before AGM, AGM attendance). Flag these in the
  action/urgent bucket with their deadlines even though the account is otherwise
  personal noise. Real example 2026-08-13: DRA Aadithya South City AGM 28 Aug —
  filled the MGT-11 proxy (see email-drafter → `references/statutory-form-pdf-pipeline.md`).

- **Bulk sender filtering** — Newsletters (McKinsey, Liases Foras, Entrackr),
  bank alerts (Kotak, IndusInd), calendar notifications, and school-portal
  messages are not actionable. Filter by sender domain in addition to subject
  keywords so they land in FYI, not Needs Reply. The bulk pattern lists in
  the script should be extended as you encounter new recurring senders.

- **Multi-message vs single-message** — A single email from a new sender
  ("New" category) is different from an active back-and-forth thread
  ("Active"/"Roundtrip"). Split Needs Reply into these two subcategories
  so the user can prioritise active conversations first.

- **Thread dedup** — When scanning sent messages, a thread may appear multiple
  times. Track `processed_threads` / `sent_processed` sets to avoid duplicates.
  Also cross-dedup between inbox-scan and sent-scan to avoid double-counting.

- **Action keyword search** is a supplement, not a replacement. Important
  emails often don't contain the keywords — the thread-analysis pass catches
  those. Dedup action items against needs_reply to avoid showing the same
  email twice.

- **Pagination** — The default 50-result API limit may miss emails. Fetch up
  to 100 with pagination (the script's `fetch_messages()` helper handles this).

- **Multi-account runs** — "check all my accounts" means run the script once
  per vault key (google-draas, google-ahfl, google-gmail). Fire the terminal
  calls in parallel (independent). Confirm scope with the user only when they
  haven't specified; an explicit "all accounts" overrides the primary-only default.

- **Output is long — read in two passes** — the actionable top (NEEDS REPLY /
  ACTION items) comes first, FYI + SUMMARY line last. `tail` alone hides the
  actionable sections; use `head -110` for the top, `tail -80` for the summary
  counts. Don't panic when the first tail looks thin — the needs-reply section
  is above the fold.

- **gws_resolve_account** must be called before every triage session to confirm
  the account is still authorized. If it reports `has_token: false`, use
  `send_oauth_url` to get a fresh link.

- **Wrong-user vault error from terminal env contamination (2026-08-13):** When
  running triage scripts via terminal, `build_service()` resolves identity from
  `HERMES_SESSION_USER_ID` (or the gateway session ContextVar). If that env var
  leaks a DIFFERENT user's id (e.g. a cron session's id like `[REDACTED-TID]` —
  Prakash Singh — from a `HERMES_CRON_SESSION=1` background), every GWS call
  fails with `VaultNoTokenError: No <service> token for user <wrong-id>` even
  though `gws_resolve_account` shows `has_token: true` for the intended user.
  This is NOT a missing-auth situation — do NOT fire `send_oauth_url`. Fix:
  re-run the script with the correct session user's telegram id prefixed:
  ```bash
  HERMES_SESSION_USER_ID=[REDACTED-TID] python3 inbox_triage.py google-draas 2026/08/06
  ```
  Quick check: `echo $HERMES_SESSION_USER_ID` in the terminal before running —
  if it doesn't match the chat user's telegram id (NDR = [REDACTED-TID]), prefix it.
  Verify the resolved account with `users().getProfile()` → `emailAddress`
  before trusting results.

- **Gmail API search != web UI search** — The API has a different query parser.
  `in:any` works in the Gmail web UI but returns zero results in the API. Use
  plain `subject:(keyword)` or `from:sender subject:keyword` instead. If a
  search returns nothing, try broadening to just the sender email address and
  scan subject lines from the result set.

## Related Skills

- `pending-actions-tracker` — Items identified here that need durable follow-up
  should be added as pending entries via memory(action='add')
- `google-workspace` — General Gmail/Drive/Calendar tool usage
- `email-drafter` — Drafting replies to threads found during triage
