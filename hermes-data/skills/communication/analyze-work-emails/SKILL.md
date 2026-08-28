---
name: analyze-work-emails
title: Analyze Work Emails
description: Analyze emails from the last N days across ndr@draas.com (work), ndr@ahfl.in (work), and nishantranka@gmail.com (personal). Filters newsletters, segregates work vs non-work, categorizes by priority and action category (FII / NEEDS RESPONSE / AWAITING RESPONSE / NEEDS CLARIFICATION), and detects thread-level follow-ups (who is waiting on whom).
trigger: "analyze work emails [for N days] | analyze my emails [for N days] | email analysis [for N days] — include the personal Gmail account when the user asks for it"
expected_input: "Optional number of days (default 2). E.g. 'analyze work emails for 5 days' parses N=5. 'analyze work emails' defaults to 2. User may ask for 'work and personal email' — then search all THREE accounts."
---

# Analyze Work Emails

## When to use
When the user says "analyze work emails" or "check my emails" or "analyze emails for N days".

## Steps

### 1. Parse the number of days
Check if the user specified "for N days" or a number in their message. Extract N. Default to 2.

### 2. Method A — Run the script (preferred if working)
The script lives at `/data/hermes/skills/communication/analyze-work-emails/scripts/analyze.py`. Run it via terminal using the **Hermes venv Python**:

```
/opt/hermes/.venv/bin/python3 /data/hermes/skills/communication/analyze-work-emails/scripts/analyze.py 5
```

(Replace `5` with the requested number of days; pass N as the first argument — if omitted, the script defaults to 2.)

**⚠️ Known script issues (Jul 2026):** The script may be incomplete (missing `build_draas_service()` function or other functions). If it fails with a `NameError` or `ModuleNotFoundError`, switch to **Method B — inline analysis** below. Even when it runs clean, treat the output as a first pass and curate per the pitfall below — the flat classifier mislabels Kelsa attendance reports and marketing/survey mail as NEEDS RESPONSE.

### 2. Method B — Inline analysis (fallback when script fails)

**Weekly (7-day) asks: use `scripts/weekly_analysis.py N` instead of the bundled analyze.py.** The bundled script currently runs, but its classifier still flags Kelsa attendance reports, Royal Sundaram surveys, TCS iON / Apify / smarterdharma marketing, and HDFC UPI alerts as NEEDS RESPONSE/NEEDS CLARIFICATION — noisy. `weekly_analysis.py` (direct API, thread-level, noise-filtered, re-runnable: `/opt/hermes/.venv/bin/python3 .../scripts/weekly_analysis.py 7`) produces the clean AWAITING / NEEDS / INFO shape in one pass. Verified calibration + curation rules: `references/weekly-7day-inline-analysis.md`.

If the script is broken, run the inline pattern. See `references/inline-analysis-pattern.md` for the exact code, and `references/three-account-thread-analysis.md` for the verified 3-account (work+work+personal) thread-level follow-up pattern — fetch windows, JSON-string parsing, thread grouping, and the output shape for "who owes me a response". Key steps:

1. **Search Gmail** — use `call('gmail_search', service_name='google-draas', query=f'after:{since_date}', max=100)`
   - **⚠️ USE `after:YYYY/MM/DD` format** (e.g. `after:2026/07/14`). The `newer_than:Nd` format silently returns 0 results for some accounts.
   - `gmail_search` returns full message data (from, to, subject, date, snippet, labels) — no need for `gmail_get` per message.
2. **Filter** — remove old forwards via `parsedate_to_datetime()` on Date header, skip newsletters via domain blocklist
3. **Classify** — keyword match for priority (CRITICAL/HIGH/MEDIUM/NORMAL) and action (NEEDS RESPONSE / NEEDS CLARIFICATION / AWAITING RESPONSE / FII)
4. **Group & present** — group by action category, sort by priority within each group

### 2c. Same-day delta check ("what came in after X") — added 2026-08-17

Trigger: "check the latest emails that have come in after [the morning review / my last check]". This is NOT an N-day analysis — it's a cutoff delta over one mailbox-day:

1. **Establish the cutoff.** If the user references a prior review, find when that ran (cron list, session history, or the review delivery time in the conversation). If unknowable, fall back to start-of-day and say so explicitly.
2. **Fetch with direct API, identity-checked first** (`WHOAMI` must print `ndr@draas.com`; else prefix `HERMES_SESSION_USER_ID=7449813913`). Query `in:inbox after:<cutoff_date>` with `messages().list`, then filter by parsed Date header > cutoff; `format='metadata'` with From/Subject/Date/To is enough (no per-message full fetch until a body is actually needed).
3. **Filter the same noise blocklist + subject markers as the N-day flow**, then classify into only two buckets: 🔴 NEEDS ACTION (a person asked something, or delivered docs the user must review/respond) vs 🟢 INFO ONLY (progress updates, drive shares, confirmations that put the ball elsewhere).
4. **Reconstruct the exact recipient set BEFORE drafting any reply** — last-message To/Cc headers plus `threads().get(format='metadata')` for full participant history. Then `draft_reply_create` (when the last sender is the intended primary recipient, the bridge's auto-To is correct) or the direct MIME pattern for custom reply-all. **Always verify the draft's To/Cc via `drafts().get(format='full')` before reporting it as ready.**
5. If a work account fails auth (`invalid_grant` on google-ahfl while `gws_resolve_account` still says `has_token: true` — recurring), state the coverage gap explicitly and offer re-auth; never present the partial scan as the full picture.

Working script shape: `references/same-day-delta-check.md`.

### 3. The output displays work emails grouped by action category

The script categorizes every email into ONE of these action categories:

| Category | Meaning | Examples |
|----------|---------|---------|
| **NEEDS RESPONSE** | Someone asked you something. You need to reply. | Questions, requests, approvals needed, "please", "kindly" |
| **NEEDS CLARIFICATION** | Ambiguous thread needing back-and-forth | Follow-ups with open questions, discrepancies, queries |
| **AWAITING RESPONSE** | You sent it. You're waiting for them. | SENT items |
| **FII** (For Information/Info Only) | Just informing you. No reply needed. | Reports, statements, updates, newsletters, bank alerts |

Each email also gets a **priority** level:
- 🔴 **CRITICAL** — urgent, ASAP, action required
- 🟡 **HIGH** — request, approval, pending, follow-up, reminder
- 🟢 **MEDIUM** — re/fwd, legal, payment, meeting, report
- ⚪ **NORMAL** — everything else

### 4. Present summary to the user

Group by action category in order: NEEDS RESPONSE → NEEDS CLARIFICATION → AWAITING RESPONSE → FII.
Within each group, order by priority (CRITICAL first).

Never infer project names or make connections the email itself doesn't state. Base every description solely on the email's From/Subject/Body. Do NOT categorise an email under "Century Regalia" unless the email explicitly mentions it.

### 5. Filter out noise
Skip Kelsa sign in/out notifications and daily bank balance alerts (handled in script).

## Script structure

1. Build Gmail service via `tools.gws_auth.build_service('gmail', 'v1', service_name='google-draas')` and `google-ahfl`
2. Search using `users().messages().list(q=f'after:{date}', maxResults=100)` — use `after:YYYY/MM/DD` format (NOT `newer_than:Nd` which silently returns 0 results)
3. **gmail_search bridge shortcut:** When using `gws_skill_bridge.call('gmail_search', ...)`, the returned data already includes `from`, `to`, `subject`, `date`, `snippet`, and `labels` — no need for a separate `gmail_get` call per message
4. Filter out newsletter/marketing domains and old forwards via Date header
5. Classify action category: NEEDS RESPONSE | NEEDS CLARIFICATION | AWAITING RESPONSE | FII
6. Classify priority: CRITICAL | HIGH | MEDIUM | NORMAL based on subject heuristics
7. Group output by action category, sorted by priority within each group

## Important notes
- Both Gmail accounts authenticate via `tools.gws_auth.build_service()` which auto-refreshes tokens (unlike raw vault socket calls)
- User has two accounts: ndr@draas.com (primary) and ndr@ahfl.in (secondary)
- **Third account — personal Gmail (added 2026-08-01):** user may ask for analysis of `nishantranka@gmail.com` too (`service_name='google-gmail'`). Resolve all accounts first via `gws_resolve_account` (no args lists every account + auth status). The user's phrasing "work emails and personal email at gmail.com" means: work accounts + the personal Gmail, analysed together and separated. Personal Gmail is mostly FII (mutual fund annual reports, AGM notices, dividend intimation, shopping promos) — classify work-vs-personal by sender domain and label the personal pile as non-work.
- The user's old address ndr@drahomes.in forwards to ndr@draas.com — old forwarded emails appear unread in inbox
- The script validates sent-date via Date header, so old forwards are filtered out automatically
- **Gmail search query pitfall:** `newer_than:2d` returned 0 results in testing. Use `after:2026/07/14` format instead (YYYY/MM/DD from today - N days). If the date-based query also fails, verify the token is valid via `gws_resolve_account`.

## Long-window analysis (30–60 days) — performance patterns (Aug 2026)

The user asks for "last 60 days" analysis. This is a BIG fetch on ndr@draas.com (~3,000 messages, ~1,000 threads after noise filter). The patterns below were verified in the Aug 2026 run:

1. **Do NOT use the bridge for long windows.** `gws_skill_bridge.call('gmail_search', ...)` with 18 weekly window queries (in:inbox + in:sent × 9 weeks, max=500) timed out at 300s. The bridge enriches per message and is too slow at this volume.
2. **Use direct Gmail API with list() pagination + per-message metadata.** `messages().list(q=..., maxResults=500, pageToken=...)` for IDs, then `messages().get(format='metadata', metadataHeaders=['Subject','From','To','Date'])` per ID to get threadId + headers. Group by threadId, classify by LAST message. See `references/long-window-thread-analysis.md` for the working script.
3. **RUN IN BACKGROUND.** Fetching metadata for ~3,000 messages takes ~8 minutes. `terminal(background=True, notify_on_complete=True)` — a foreground 300s timeout kills it mid-fetch. Poll with `process(action='poll')` while doing targeted deep-dives in parallel.
4. **Loose name searches blow up.** `"Kanta"` matched 4,014 messages; even `"Kanta Ranka"` (quoted exact phrase) matched 3,376 — because Kotak bank alerts, Royal Sundaram surveys, and calendar notifications contain the account-holder name. When hunting a person/claim, combine the name with `-from:` noise exclusions and `after:` bounds, and cap the fetch (max_ids ~30). Better: search the specific domain (e.g. `claims@mediassistindia.com OR claims@mediassist.in`).
5. **Noise list additions (60-day run):** `bankalerts@kotak.bank.in`, `BankStatements@kotak.bank.in`, `bankconsignments@kotak.bank.in`, `nach.alerts@kotak.bank.in`, `creditcard.alerts@indusind.com`, `transactionalert@indusind.com`, `ebill@airtel.com`, `update@airtel.com`, `calendar-notification@google.com` (Google Calendar invites/notifications — these are real appointments but noise for thread classification), `partner.survey@royalsundaram.in` ("Your opinion matters" surveys), `crmoperations@centuryrealestate.in` (payment receipts/invoices), `imagesbazaar.com`, `entrackr.com`, `lvxventures.com`, `exedinfo@iima.ac.in`, `assemblyai.com`, `naredco`. Plus subject markers: 'BLACKbox Live Demo', 'ASTRAL PIPES', 'your opinion matters'.
6. **Vendor marketing CC'd to info@draas.com** lands in AWAITING RESPONSE because NDR's own address is in To — these are marketing forwards (Astral Pipes, Dell/Inflow, Sonel, BLACKbox). Filter `to:info@draas.com` or recognize vendor domains before presenting.

### Thread-level follow-up analysis (who owes what) — added 2026-08-01

The user's full ask is often deeper than "list emails": *"looking at the conversation thread, identify if anything I need to follow up on, anything I need to respond to, or if I need to follow up with someone — I'm awaiting some data or response from someone, who is that someone?"* Per-message classification is NOT enough. Reconstruct threads and classify by who holds the ball:

1. **Fetch both sides:** run `in:inbox after:YYYY/MM/DD` AND `in:sent after:YYYY/MM/DD` for each account (split into two windows if volume is large, e.g. `before:midpoint` + `after:midpoint`).
2. **Group by thread:** `threads[(account, threadId)] = [messages]`. Threads never cross accounts. Sort each thread by parsed date.
3. **Classify by LAST message in thread:**
   - Last message has `SENT` in labels → **AWAITING RESPONSE** — user sent last, waiting on the counterparty. This answers "who owes me a response / data?" List the OTHER party + days since the sent message.
   - Last message incoming + contains ask language (please, kindly, could you, let me know, needed, approval, confirm, ?) → **NEEDS RESPONSE** — someone asked the user something. This answers "what do I owe?"
   - Last message incoming, no ask → FII / INFO_CONVO.
4. **Dedupe** by message id — inbox+sent queries overlap.
5. **Present grouped by action, not by inbox order:** lead with AWAITING RESPONSE (named people + how long), then NEEDS RESPONSE (named senders + what they asked). The user's mental model is "who is that someone" — always name the person, not just the subject line.
6. **Chase-tier the waiting list** by age (this week vs 8+ days) — the user escalates on items pending 8-9 days (see personal-messaging Pattern D for the tone they want on those chases).
7. For follow-up drafting after analysis: use `email-drafter` skill (draft_reply_create with explicit `to=` when the thread's last message is the user's own sent message — the bridge defaults to a self-reply otherwise).

### Session identity trap — terminal subprocesses may hit the WRONG mailbox (confirmed 2026-08-17)

In this deployment, terminal subprocesses can inherit a stale/wrong `HERMES_SESSION_USER_ID` (observed value `8502281203` → `build_service('gmail','v1',service_name='google-draas')` returns `getProfile()['emailAddress'] = psingh@draas.com` — PRAKASH SINGH's mailbox, NOT ndr@draas.com). This silently reads/search queues the wrong person's data and would drop drafts into the wrong account. The symptom is NOT an error — everything "works", just against the wrong mailbox.

**Before ANY Gmail/Drive fetch, verify identity:**
```python
svc = build_service('gmail', 'v1', service_name='google-draas')
print('WHOAMI:', svc.users().getProfile(userId='me').execute()['emailAddress'])
# MUST print ndr@draas.com. If it prints anything else, abort.
```
If it resolves wrong, prefix the command with the correct session id:
```
cd /opt/hermes && HERMES_SESSION_USER_ID=7449813913 /opt/hermes/.venv/bin/python3 script.py
```
(Gateway-level tools — `gws_resolve_account`, `gws_fetch_token`, the `execute_code` sandbox — resolve identity from the session correctly; only plain terminal subprocess runs can flip.)

### Account token failure mid-analysis (invalid_grant)

When one work account returns `invalid_grant: Token has been expired or revoked`, the account is unavailable — do NOT present the single-account output as the full analysis. State clearly that ndr@ahfl.in was skipped, then call `send_oauth_url` (label e.g. "Re-authorize ndr@ahfl.in (Google)") so the user can re-auth in one tap, and offer to re-scan once authorized.

## Pitfalls

### Gmail search query pitfall: `newer_than:Nd` returns 0 results silently

Use `after:YYYY/MM/DD` format instead (e.g. `after:2026/07/14`). The `newer_than:Nd` Gmail search operator silently returns 0 results for some accounts. Compute the date in Python: `since_date = (date.today() - timedelta(days=N)).strftime('%Y/%m/%d')`.

### gmail_search returns full data — no gmail_get needed

When using `gws_skill_bridge.call('gmail_search', ...)`, the returned data already includes `from`, `to`, `subject`, `date`, `snippet`, `labels`, `id`, and `threadId` for each message. Do NOT call `gmail_get` for each message individually — it's wasteful and slow. The search response IS the enriched data.

### gmail_search returns a JSON STRING — parse it (confirmed 2026-08-01)

The bridge's `gmail_search` returns a **JSON-encoded string**, not a Python list/dict. `json.loads()` the result before iterating. Also, **empty result sets return the literal string `"No messages found.\n"`** (not `[]`) — handle that or `json.loads` raises `Expecting value: line 1 column 1`.

```python
raw = call('gmail_search', service_name='google-draas', query='in:inbox after:2026/07/18', max=200)
if isinstance(raw, str):
    raw = raw.strip()
    if not raw or raw.lower().startswith('no messages'):
        msgs = []
    else:
        msgs = json.loads(raw)
```

### Multi-account / thread-analysis pattern (2026-08-01)

For "analyze work + personal email across accounts and find follow-ups":
1. Resolve accounts first: `gws_resolve_account` with no args → all 3 (google-draas, google-ahfl, google-gmail) usually have tokens
2. Fetch **both** `in:inbox` and `in:sent` per account, split into two 7-day windows (`after:X before:mid`, `after:mid`) to avoid pagination truncation with max=200
3. Dedupe by message `id` across windows
4. Group by `threadId` per account; sort by date; the LAST message in a thread determines the state:
   - last is SENT → **AWAITING RESPONSE** (you sent it, they owe you)
   - last is INBOX + question/request keywords → **NEEDS RESPONSE**
5. `_account` holds the **email address** (ndr@draas.com), NOT the service name — map email→service_name before calling `gmail_get`

### gmail_search returns a JSON STRING, not a list (added 2026-08-01)

`call('gmail_search', service_name=..., query=..., max=...)` returns a **serialized JSON string**, not a Python list. `dict(m)` on it raises `ValueError: dictionary update sequence element #0 has length 1`. You MUST parse first:

```python
raw = call('gmail_search', service_name='google-draas', query=q, max=200)
if isinstance(raw, str):
    raw = raw.strip()
    if not raw or raw.lower().startswith('no messages'):
        return []          # empty result comes back as plain "No messages found.\n"
    raw = json.loads(raw)  # real result is a JSON array as a string
```

Also:
- **Empty results** return the literal string `"No messages found.\n"` (not `"[]"`) — `json.loads` on it throws `Expecting value: line 1 column 1 (char 0)`. Check for the `no messages` prefix before parsing.
- **`gmail_get` also returns a JSON string** — same parse pattern; body lives under `raw['body']`.
- When building a message dict for storage, do `m['_account'] = label` BEFORE `dict(m)`-style processing, or build fresh dicts with the keys you need (id, threadId, from, subject, date, snippet, labels, account).
- Beware `max=` truncation: with high-volume accounts (600+ msgs/14d on ndr@draas.com), a single `in:inbox after:` query with max=500 silently truncates. Split into two windows (`before:mid` / `after:mid`) and dedupe by id afterwards.

**⚠️ BUT the bridge returns a JSON STRING, not a parsed object (confirmed Aug 2026).** Always `json.loads()` it, and handle empty results which come back as the literal string `"No messages found.\n"` — calling `json.loads()` on that raises `Expecting value: line 1 column 1 (char 0)`. A naive `dict(m)` on each element crashes with "dictionary update sequence element #0 has length 1" — that is the string-return symptom. Canonical fetch helper:

```python
def fetch(service_name, query, maxr=100):
    raw = call('gmail_search', service_name=service_name, query=query, max=maxr)
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw or raw.lower().startswith('no messages'):
            return []
        raw = json.loads(raw)
    return raw if isinstance(raw, list) else []
```

For full thread-level follow-up analysis (AWAITING RESPONSE = who Nishant is waiting on; NEEDS RESPONSE = who is waiting on him) across work AND personal accounts, see `references/thread-followup-analysis.md`.

### `threadId:` is NOT a valid Gmail search query (confirmed 2026-08-01)

`service.users().messages().list(q='threadId:19fb...')` silently returns ZERO results — Gmail search does not support a `threadId:` operator. To inspect a specific thread use the threads API directly:

```python
t = service.users().threads().get(userId='me', id=THREAD_ID, format='metadata').execute()
for msg in t['messages']:
    h = {x['name']: x['value'] for x in msg['payload']['headers']}
    print(msg['id'], h.get('Date'), h.get('From'), h.get('To'))
```

Use this whenever you need the exact message IDs for `draft_reply_create` threading, or to find who the last non-user participant in a thread was. When you already know the threadId from a prior search result, skip the search entirely — go straight to `threads().get()`.

### Must use Hermes venv Python, not system Python
The system Python at `/usr/bin/python3` is externally-managed (PEP 668). Always use `/opt/hermes/.venv/bin/python3`.

### Terminal subprocesses can resolve to the WRONG Google account (Aug 2026)
The gateway injects `HERMES_SESSION_USER_ID` into subprocesses; in this deployment it has gone stale (8502281203 → resolves vault to psingh@draas.com instead of NDR). Symptoms: `build_service('gmail','v1', service_name='google-draas').users().getProfile()` returns `psingh@draas.com`; Gmail searches that worked minutes earlier return empty; message/thread-id gets 404 ("Requested entity was not found"). **Fix:** prefix every Gmail/Drive/Sheets python run with the correct id:
```
HERMES_SESSION_USER_ID=7449813913 /opt/hermes/.venv/bin/python3 script.py
```
Always sanity-check the account first: print `getProfile()['emailAddress']` and expect `ndr@draas.com` before trusting any mailbox read. Gateway-level tools (`gws_resolve_account`, `gws_fetch_token`, the execute_code sandbox) use the correct session identity automatically — prefer them when in doubt.

### Gmail attachment downloads get silently truncated → fall back to Drive
`messages().attachments().get()` returned base64 that decodes to a CORRUPT file: zip starts with `PK` but raises "Bad magic number for central directory" (EOCD present, but central-directory offset beyond EOF — bytes lost mid-stream), or base64 length %4==1 raising "Invalid base64-encoded string". Do NOT keep retrying the attachment endpoint — search Drive for the same document by filename and download/export from there (`files().get_media()` for native files, `files().export(mimeType='...wordprocessingml...')` for Google Docs). Drive media is a file stream and does not truncate. Recipe + diagnostics: `references/gmail-attachment-truncation-drive-fallback.md`.

### Drafts with attachments + reply-all threading via raw Gmail API
Follow-up drafts on a thread whose last message is the user's own SENT mail must repeat the exact To + ALL Cc of that message. Fetch headers with `messages().get(format='metadata', metadataHeaders=['To','Cc','Message-ID'])` — do not guess recipients. When the draft needs an attachment, the bridge's draft ops may not support it, so build the MIME yourself and use `drafts().create()` (still draft-only — never `messages().send()`): MIMEMultipart body + MIMEApplication attachment, set `References`/`In-Reply-To` to the last message-ID header, base64-urlsafe the whole message. Verify the created draft (recipients, attachment filename present in parts) before reporting. Recipe: `references/draft-with-attachment-gmail-api.md`.

### Verify every recipient against contacts before drafting
Every non-thread recipient must be found via People API (`searchContacts`) or the contacts sheet first — e.g. akber@ahindia.com and khan.hussain.aamir@gmail.com are both in NDR's contacts. Addresses already present in an existing thread are safe to reply-all to without a fresh lookup.

### Don't infer project names from email context
When categorizing and presenting email results, base descriptions **solely** on the email subject and body content. Do NOT infer project names (e.g. "Century Regalia"), connections, or ongoing work context that aren't explicitly mentioned in the email.

### Forwarded old emails appear unread
Emails forwarded from ndr@drahomes.in to ndr@draas.com land in the inbox as unread regardless of age. The script validates sent-date via `email.utils.parsedate_to_datetime()` on the Date header to filter these out.

### Verify the mailbox identity BEFORE the big fetch (2026-08-17)

The terminal subprocess env can carry a WRONG `HERMES_SESSION_USER_ID` (this deployment: stubbed to 8502281203 → resolves `google-draas` to **psingh@draas.com**, not ndr@draas.com). The script prints `ACCOUNT_OK` even when it's reading the wrong person's mailbox — queries either 404 (`Requested entity was not found`) or silently return someone else's emails. Before any multi-minute analysis run, pre-flight check:

```python
gmail = build_service('gmail', 'v1', service_name='google-draas')
print(gmail.users().getProfile(userId='me').execute()['emailAddress'])
# Must print ndr@draas.com. If it prints anything else, re-run the ENTIRE
# command with: HERMES_SESSION_USER_ID=7449813913 /opt/hermes/.venv/bin/python3 ...
```

Nishant's numeric ID = 7449813913. Full fix + explanation in `api-references/google-workspace-api` (Common Pitfalls #11, Step 0). Also relevant: pdf/docx attachments fetched via `messages().attachments().get()` can be truncated (see google-workspace-api "Attachment Handling") — if a downloaded attachment fails to parse, look for the same file in Drive instead.

### Token expiry / re-authorization
If `build_service()` fails with a refresh error, the token needs re-authorization. Use `send_oauth_url` with the appropriate service_name.

**`invalid_grant: Token has been expired or revoked` is the definitive dead-token signal — and `gws_resolve_account` may STILL report `has_token: true` for that service (observed Aug 2026 with google-ahfl).** Trust the build_service error, not the resolve flag. Send `send_oauth_url` (label the button with the account, e.g. "Re-authorize ndr@ahfl.in"), and re-scan that account after the user authorizes — don't drop the account from the analysis silently.

### gmail_search / gmail_get return JSON STRINGS, not dicts
`gws_skill_bridge.call('gmail_search', ...)` returns a **JSON-encoded string**, not a Python list. Always `json.loads()` it before iterating:
```python
raw = call('gmail_search', service_name='google-draas', query=query, max=200)
if isinstance(raw, str):
    raw = json.loads(raw)   # ← required
```
**Empty results come back as the literal string `"No messages found.\n"`** — json.loads on that raises `Expecting value: line 1 column 1 (char 0)`. Guard before parsing:
```python
if isinstance(raw, str):
    raw = raw.strip()
    if not raw or raw.lower().startswith('no messages'):
        return []
    raw = json.loads(raw)
```
Same applies to `gmail_get` (returns JSON string with `body` key; `message_id=X` is the kwarg, not `id=`).

### Fetch window splits to avoid truncation
`gmail_search` with `max=500` still truncates busy accounts. Split each folder query into weekly windows: `in:inbox after:START before:MID` + `in:inbox after:MID`. Dedupe by message `id` after merging.

### Method A (analyze.py) output is a FIRST PASS — curate before presenting (confirmed Aug 2026)
When the script runs successfully it still mislabels noise as actionable: Kelsa "DRA – Daily Attendance Report" (Dhanuja K), Royal Sundaram "Your opinion matters" surveys, TCS iON, Apify, SmarterDharma, and HDFC UPI alerts land in NEEDS RESPONSE/NEEDS CLARIFICATION. Don't present its raw output. Re-run a thread-level inbox+sent pass (or filter the script's output) with the noise blocklist + subject markers ('attendance report', 'your opinion matters', 'upi txn') and present ONLY genuinely actionable items. The user reads the summary for "who owes me / who's waiting on me" — never bury that under marketing noise.

### Did we receive X from <person>? — name-variant & chain-of-communication search (confirmed 2026-08-20)

When the user asks "have we received <document/petition> from <person>?", the named party is often NOT the actual sender — it can be the principal a stage upstream while their agent/advocate/associate's office sends the reply. Don't stop at "no email from the named party" — reconstruct the chain:

1. **Search all plausible name spellings**, not just the one the user said. Indian names transliterate several ways (Setia / Sethia / Seetia / Seta) and an account often holds unrelated hits under a variant (here Sethia Gangotree's 2013 SMS logs dominated the `setia` search). Try `A OR B OR C` in one query.
2. **Search the matter, not just the person** — `"succession petition"`, `subject:petition`, `"re-draft"`. The re-drafted doc may live under a *different* thread title than the user framed (they said "re-drafted petition" to Setia; it arrived as "Succession Certificate (Dinesh Ranka)" from the advocate).
3. **Read full thread bodies** (`format='full'`, walk text/plain parts) to map who-sent-what-when: e.g. draft sent 12-Aug by user → to the principal (Mr. Sethia) → principal's advocate (Nishanth @ lawsquare.in) replied 19-Aug with the re-draft. Answer "did we receive it" = YES, but the sender is the advocate's office — stating that precisely matters to the user.
4. **Confirm the attachment, don't just find the email.** Walk `payload['parts']` and list `filename` for `application/*` / `msword` parts — the re-draft was `ver 1.docx`. Report the actual filename + date so the user can open it.
5. **Bound loose name searches** (name + `-from:` noise exclusions + `after:` bounds — see the Kanta-4,014-match pitfall below) so a variant spelling or a same-surname party doesn't drown the real thread.

Combine with the thread-level and `threadId`-via-`threads().get()` techniques above when you must also answer "who sent what and where does a reply thread sit".

### Fetching full bodies / attachments for "elaborate this email" requests
When the user asks "what is this email / elaborate", fetch bodies with `messages().get(format='full')` per message id and walk the payload (text/plain first, else text/html then strip tags). Full bodies download reliably this way. **Known pitfall (confirmed Aug 2026): binary attachment downloads via `users().messages().attachments().get` can come back TRUNCATED mid-base64** — symptoms: `BadZipFile: Bad magic number for central directory` on a docx that starts with valid `PK` header, base64 length `%4 == 1` raising "Invalid base64-encoded string", or decoded bytes shorter than the reported `size`. Retrying does NOT fix it. **Fix: search Drive for the same document** (contract drafts/agreements are almost always mirrored in Drive, often shared via Google Docs with the same filename) and download via `drive.files().get_media()` / `drive.files().export()` — the media endpoint returns intact bytes. See `references/fetch-email-context.md` for the working pattern.

### Long-range scans (30–60 days) — direct API, run in background (confirmed Aug 2026)
For a 60-day full analysis (2,900+ messages, ~1,000 threads on ndr@draas.com):
- **Do NOT use the bridge for the bulk scan.** `gws_skill_bridge.call('gmail_search', ...)` with weekly windows over 60 days TIMED OUT at 300s. The bridge enriches every message; 18 window queries × up to 500 messages is too slow.
- **Use `build_service('gmail','v1')` directly**: `messages().list(q=..., maxResults=500, pageToken=...)` pagination to collect IDs (fast, ids only), then one `messages().get(format='metadata', metadataHeaders=[...])` per message to get From/To/Subject/Date/labels. ~2,900 metadata gets ≈ 8 min.
- **Run it as a background terminal job** (`terminal(background=True, notify_on_complete=True)`) — never foreground, it will hit the 300s timeout.
- Group by threadId, sort by parsed date, classify on the LAST message (SENT → AWAITING RESPONSE; incoming+ask → NEEDS RESPONSE).
- Target message IDs for a specific thread: `threads().get(id=THREAD_ID, format='metadata', metadataHeaders=[...])` lists every message id/date/from in one call — use this to find the exact `message_id` for `draft_reply_create` or `threads` navigation.

### Thread-level follow-up detection (who owes whom)
The per-message classifier misses the user's real question: "am I awaiting someone's response, or does someone await mine?" Group by `(account, threadId)`, sort messages by Date, then classify on the **LAST message of the thread**:
- Last message has `SENT` in labels → **AWAITING RESPONSE** (user sent last; chase the other party). Days-since = how stale the follow-up is.
- Last message is incoming with question/request keywords → **NEEDS RESPONSE**.
- For AWAITING RESPONSE, also fetch the last full body via `gmail_get` to name the actual person and what they owe — snippets alone often show only the forwarder (e.g. Prakash fwd'ing ICICI queries).
- Recency grouping is what the user acts on: "this week / older than 11 days" matters more than exact date.

### `_account` stores the EMAIL, not the service name
When tagging fetched messages with `_account`, the value is the email (`ndr@draas.com`), NOT the vault service name (`google-draas`). Thread lookups keyed on the service name silently return empty — map email→service explicitly (`{'ndr@draas.com':'google-draas', ...}`) before calling `gmail_get` per thread.

### Personal-account work segregation
For nishantranka@gmail.com, work content is rare but real (DRA board minutes, compliance mails cc'd there). Don't skip the account — classify by sender domain + subject, then report the work items alongside the work accounts and dismiss the rest as personal/FII.

### Kelsa sign-in/out noise
The script should filter out the many "Please sign in/out for the day" auto-generated emails. These have subject starting with "Please sign" and should be skipped along with bank balance alerts.
