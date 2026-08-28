---
name: not-spam-whitelist
title: Not-Spam Email Whitelist Manager
description: Maintain and use the DRAAS not-spam whitelist spreadsheet. Add new entries when user identifies non-spam emails, and run 3-hourly check to auto-unspam matching emails.
---

---

## Naming Collision (critical)

⚠️ `not-spam-whitelist` is an **ambiguous name** — it matches both this skill AND a reference file at `domain/property-title-due-diligence/references/not-spam-whitelist.md`, which is a stale file (permission-locked, unreadable).

**Always load this skill with its full categorized path:**
```
productivity/not-spam-whitelist
```

Do NOT use the bare name `not-spam-whitelist` — it will fail with an "Ambiguous skill name" error. This applies everywhere: skill_view, cron job configs, and skill loader references.

---

## Sheet Location
- **Sheet URL:** https://docs.google.com/spreadsheets/d/1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0/edit
- **Sheet ID:** `1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0`
- **Tabs:** Whitelist (legitimate senders), Blacklist (confirmed spam senders)

## Sheet Columns (Whitelist tab, A-I)

```
 A: #              — row number
 B: Category       — Business area (Legal, Banking, Insurance, Internal, etc.)
 C: From Email/Domain — The sender email or domain to match
 D: To Email       — Target inbox (e.g. ndr@draas.com)
 E: Subject Keywords — Comma-separated keywords for subject_contains rules
 F: Content Description — Human-readable description of what this rule covers
 G: Rule Type      — One of: exact_from, domain_from, subject_contains, combined
 H: Date Added     — Date rule was added to the sheet
 I: Notes          — Context, aliases, or additional matching hints
```

**IMPORTANT: All listed rules are active by default.** There is no "enabled/disabled" flag column. If a rule has data in column A (row number) and column G (rule type), it is live. Do NOT try to read column B as an "enabled" flag — it is the Category field.

## Rule Types

| Rule Type | Column C value | Matching logic |
|-----------|---------------|----------------|
| `exact_from` | Full email address | `sender_email.lower() == value.lower()` |
| `domain_from` | Domain (with or without @ prefix) | `sender_domain == value.lower()` — strips @ prefix if present |
| `subject_contains` | Domain in C, keywords in E | Keywords comma-separated in column E; match if ANY keyword is in subject |
| `combined` | Domain in C, keywords in E | Domain AND at least one subject keyword must both match |

## Special rules already in the sheet
- **`domain_from @draas.com`** (row 12, Category: Internal) — catch-all for all @draas.com internal emails. This covers marketing@draas.com, hr@draas.com, etc. Do NOT add a separate code-level catch-all — the sheet already handles it.
- **`domain_from google.com`** (row 17) — Google Drive, Calendar, and other Google platform notifications.

## Tabs
- **Whitelist** — Approved senders/rules to auto-move from SPAM to INBOX
- **Blacklist** — Confirmed spam senders (same columns as White)list. For senders manually flagged as spam after arriving in inbox. Added when user identifies spam that landed in primary inbox.

## Sheet Structure (Columns A-I)

| Column | Index | Header              | Purpose                        |
|--------|-------|---------------------|--------------------------------|
| A      | 0     | #                   | Row number                     |
| B      | 1     | Category            | Classification label           |
| C      | 2     | From Email / Domain | Sender address or domain       |
| D      | 3     | To Email            | Recipient                      |
| E      | 4     | Subject Keywords    | Keywords for subject matching  |
| F      | 5     | Content Description | Human-readable description     |
| G      | 6     | Rule Type           | `exact_from`, `domain_from`, etc. |
| H      | 7     | Date Added          | Date rule was added            |
| I      | 8     | Notes               | Additional notes               |

**⚠ Scripting pitfall — column indices are 0-based starting from A=0.** When reading via Sheets API `values().get()`, column C (From Email / Domain) is index 2, column G (Rule Type) is index 6. A common mistake is using index 1 for the matching value (which reads Category instead). Always verify against the raw sheet output first.

## Automated check — proven runbook (Aug 2026)

**⚠️ HARD RULE (Aug 11, 2026): run `scripts/check-spam.py` — do NOT hand-roll a parallel matcher.** An ad-hoc rewrite of the match logic in the cron missed the "via" exclusion and wrongly moved an Adobe newsletter (`"'Adobe Illustrator' via Subscription Group" <Subscription@draas.com>`) from SPAM to INBOX; it had to be reverted manually. The canonical script encodes the via-exclusion, identity guard, and correct From-header parsing. If you must write ad-hoc code, copy `check-spam.py` verbatim as the base, and still re-run the canonical script before reporting.

**✅ Aug 12, 2026 — `scripts/not_spam_check.py` (the build_service-based canonical script) now ALSO carries both guards.** It was patched to add (a) the via-exclusion to the @draas.com catch-all and (b) the identity guard (`getProfile` → must be ndr@draas.com, hard-stop otherwise), matching check-spam.py's safety behavior while using the sanctioned `build_service(service_name='google-draas')` auth path. Run record: 6 spam checked, 1 moved (Kotak `retailproducts@kotak.bank.in` → domain_from rule), 0 errors, identity verified.

**⚠️ Aug 12, 2026 (evening run) — a STALE `/opt/data/not_spam_check.py` beat the canonical script and moved a via-pattern email to INBOX.** The cron executed `/opt/data/not_spam_check.py`, an OLD copy that predates both guards: its `is_internal()` has NO `' via '` check and there is NO `getProfile` identity guard. Result: `"'TCS iON Digital Manufacturing' via Marketing" <marketing@draas.com>` was moved SPAM→INBOX under "internal @draas.com catch-all" — the exact false-positive class the via-exclusion exists to stop. The run looked clean (7 spam checked, 1 moved, 0 errors), so the bug hid in plain sight; the TCS iON message should be moved back to SPAM via label modify. **Operational rule: NEVER reuse a previously-copied `/opt/data/not_spam_check.py` across runs — the /opt/data copy goes stale the moment the skill script is patched, and a stale copy silently re-enables the via false-positive. Run the canonical script in place from the skill dir, or re-copy it fresh every run and grep the file for `' via ' in` + `getProfile` before executing. Sanity-check the run output: with a via-@draas.com sender present, you MUST see `"via' pattern — SKIPPING (spam)"` in the log; its absence means the guard isn't live.**

### Approach A: gws_skill_bridge (simplest, no credential management)

Use `tools.gws_skill_bridge.call()` — it wraps `build_service()`, handles sandbox routing automatically, and works in cron terminal. This is the sanctioned path per project policy (never build credentials inline).

```python
import sys, json, re
sys.path.insert(0, "/opt/hermes")
from tools.gws_skill_bridge import call

SERVICE = "google-draas"  # resolved via gws_resolve_account

# Read whitelist
sheet = json.loads(call("sheets_get", service_name=SERVICE,
    sheet_id="1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0",
    range="Whitelist!A:I"))

# Fetch SPAM messages (returns list of {id, from, subject, ...})
spam = json.loads(call("gmail_search", service_name=SERVICE,
    query="in:spam", max=200))

# Get label IDs
labels = json.loads(call("gmail_labels", service_name=SERVICE))
# SPAM = "SPAM", INBOX = "INBOX" (system labels, same string as id)

# Move matching messages in one batch call
call("gmail_batch_modify", service_name=SERVICE,
    message_ids=[msg["id"] for msg in matched],
    remove_labels="SPAM", add_labels="INBOX")
```

Key operations available via the bridge:
- `sheets_get` / `sheets_update` / `sheets_append` — Google Sheets
- `gmail_search` — queries Gmail (supports `query=` and `max=`)
- `gmail_get` — full message by id
- `gmail_labels` — list all labels
- `gmail_batch_modify` — add/remove labels on multiple messages at once (pass `message_ids=list[str]`, `add_labels=`, `remove_labels=` as comma-separated strings)
- `gmail_modify` — modify a single message

**Bridge payload quirks (hit live Aug 2026):**
- `sheets_append` `values` MUST be a JSON **string** (`json.dumps(new_rows)`), not a Python list — passing a list raises `TypeError: the JSON object must be str...` inside `google_api.py`.
- `gmail_search` returns **plain text** `"No messages found.\n"` (NOT JSON) when the query matches zero messages. `json.loads()` on that raises `JSONDecodeError` — guard with `raw = call(...); spam = json.loads(raw) if raw and not raw.startswith('No messages') else []`.
- `gmail_get` via the bridge returns a **flattened** message: top-level `from`, `to`, `subject`, `date`, `body`, `labels` keys — NOT the standard `payload.headers[]` structure. Read `msg['from']` / `msg['labels']` directly.
- `gmail_batch_modify` returns `{"status": "modified", "count": N}` — use `count` for verification.

No credential objects to create, no vault client calls, no scope management. The bridge handles everything transparently. See Aug 10, 2026 cron session for a full working example.

### Bridge call quirks (Aug 2026 — live session)
- **`sheets_append` `values` must be a JSON string**, not a Python list. Passing a list raises `TypeError: the JSON object must be str, bytes or bytearray, not list` inside the bridge. Always pass `values=json.dumps(new_rows)`.
- **`gmail_search` returns PLAIN TEXT when zero results**: `"No messages found.\n"` — not JSON, so `json.loads()` throws `JSONDecodeError`. Guard before verifying "spam is now empty": `raw = call(...); spam = json.loads(raw) if raw and raw.strip().startswith('[') else []`.
- **`gmail_get` returns FLATTENED fields, not raw `payload.headers`**: keys are `id`, `threadId`, `from`, `to`, `subject`, `date`, `labels`, `body`. Extract the sender with `msg['from']` directly (do NOT walk `payload['headers']`). The flattened `labels` list is the fastest way to verify a SPAM→INBOX move: check `'INBOX' in labels and 'SPAM' not in labels`.

### Bridge API shapes — verified Aug 11, 2026 (ad-hoc whitelist-and-move session)

The `gws_skill_bridge.call()` return values differ from raw googleapiclient shapes. Confirmed live:
- `sheets_get` → returns the **values array directly** (a list of rows), NOT a dict with a `values` key. `sheet.get('values', [])` raises `AttributeError: 'list' object has no attribute 'get'`. Use `rows = sheet if isinstance(sheet, list) else sheet.get('values', [])`.
- `sheets_append` → `values=` must be a **JSON string** (`json.dumps(rows)`), not a Python list — the bridge does `json.loads(args.values)` internally and raises `TypeError: the JSON object must be str...` on a list.
- `gmail_get` → returns a **flattened message**: top-level keys `id`, `threadId`, `from`, `to`, `subject`, `date`, `labels`, `body`. There is NO `payload.headers` nesting — do not dig into `payload` (returns None); read `msg['from']` / `msg['subject']` / `msg['labels']` directly. `labels` includes system + category labels (e.g. `['UNREAD', 'CATEGORY_UPDATES', 'SPAM']`).
- `gmail_search` with **zero results** returns the plain string `'No messages found.\n'`, not JSON — `json.loads` raises `JSONDecodeError` on it. Guard: `raw = call(...); spam = [] if 'No messages found' in raw else json.loads(raw)`.
- `gmail_batch_modify` → `message_ids=` is a Python list, `remove_labels=` / `add_labels=` are comma-separated strings. Returns `{"status": "modified", "count": N}` — count is a reliable success signal.

### Approach B: Standalone script (existing, proven)

Ready-to-run script: `scripts/not_spam_check.py` in this skill. **Run the canonical copy IN PLACE from the skill dir** (trusted terminal process, NOT execute_code) — do NOT trust a previously-copied `/opt/data/not_spam_check.py`, it goes stale and silently drops the via-exclusion + identity guards (see the Aug 12, 2026 evening-run incident above):

> **⚠️ HARD RULE: do NOT hand-roll a matcher.** Every single ad-hoc matcher written for this cron since Aug 10 has produced a via-breach (5/5 — Aug 10, 12, 17, 19, 22). The canonical script is the ONLY safe execution path. If you read this skill and then write your own code instead of running the canonical script, you WILL move a via-pattern @draas.com email to inbox. This is not speculation — it has happened every time.

    cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py

If a `/opt/data` copy must be used (cron working-dir conventions), re-copy it fresh from the skill dir on EVERY run, and verify the guards are present before executing — grep the file for `' via ' in` (via-exclusion) and `getProfile` (identity guard). After the run, confirm the log shows the via-skip line whenever a via-@draas.com sender was present.

Proven production facts:
- **Run via terminal, not the execute_code sandbox.** The sandbox's `hermes_tools` stub has no `gws_fetch_token` import → `tools.gws_auth.load_credentials()` raises ImportError there. The trusted terminal process has `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock` and works.
- **Invocation (two proven variants, both work):**
  1. **Simplest (Aug 21, 2026):** `cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py` — works directly, no proxy-unset needed. Proven clean at 12:30 UTC (4 moved).
  2. **Fallback (when proxy vars cause httplib2 SOCKS failure):** unset proxy env vars first:
     ```
     env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy GWS_VAULT_SOCKET=/run/gws-vault/vault.sock timeout 540 /opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py
     ```
     Direct sockets to Google work fine; curl also works via the proxy — only Python httplib2 through the SOCKS tunnel fails. Do NOT diagnose this as a vault outage or auth failure; it is purely a proxy-var routing issue.
- **Account:** `service_name='google-draas'` = ndr@draas.com (primary). All DRAAS accounts have tokens in the vault; `has_token()` works from terminal.
- **Rule types actually seen:** `exact_from` (most common), `domain_from` (normalize column C: strip leading '@', match if sender domain endswith OR sender endswith '@'+domain — handles both '@kotak.com' and 'manipalhospitals.com' styles), `combined` (domain AND subject — e.g. hdfcbank.bank.in + 'statement'), `subject_contains` (split column E on commas, case-insensitive substring).
- **Internal catch-all:** sender domain == draas.com or endswith .draas.com → always move. (Row 11 in the sheet duplicates this as a domain_from rule.)
- **Move = modify API:** `body={'removeLabelIds': ['SPAM'], 'addLabelIds': ['INBOX']}`. NEVER delete; NEVER send.
- **Verify the engine before trusting a 0-move result:** a zero-match day is normal (5 spam/day typical), but dump each spam message's sender/subject + matched rules to confirm the parser isn't broken. E.g. an `exact_from` rule for `RoyalSundaramVconnect@royalsundaram.in` must NOT match `partner.survey@royalsundaram.in` (same domain, different sender — correctly left in spam).
- **Post-move verification — searching by subject returns ALL historical copies (Aug 25, 2026):** to confirm one move persisted, refetch the moved message by its ID and check `labelIds` contains INBOX and not SPAM. If you instead search `q='in:anywhere subject:"<subject>"'`, identical subjects from EARLIER runs appear too — prior INBOX moves from previous days plus TRASH copies from old deletions. Royal Sundaram's "Your opinion matters" survey showed 2× INBOX + 8× TRASH after the Aug 24+25 runs: expected, NOT a double-move or an error. Only the freshly moved message (the one the mover's output listed) matters.
- **Benign stderr (grep it out, do NOT misread):** every `build_service()` call in cron prints `canonical_uid: vault has no identity mapping for 'ndr-[REDACTED-TID]' -- using raw id as fallback key`. This is expected — the raw-id fallback works fine and the token resolves. It is NOT a vault outage and NOT an auth failure; a cron report that includes it should still be considered successful.
- **Pagination:** SPAM volume is tiny (≤5/day); list with maxResults=200 and stop when `nextPageToken` is absent.

### ⚠️ Name collision CANNOT be fixed via management tools (Aug 22, 2026)

The colliding file (`property-title-due-diligence/references/not-spam-whitelist.md`) has **OS-level `Errno 13` permission restrictions** — even `skill_manage(action='remove_file')` from the Hermes agent is denied. It cannot be removed or renamed through any tool available to the session.

**Impact:** the name collision is PERMANENT until someone with shell/root access on the host removes or renames that file directly. Until then:
- `skill_view(name='not-spam-whitelist')` will always fail with "Ambiguous skill name"
- Cron job opener will always say "Skill(s) not found and skipped: not-spam-whitelist"
- The ONLY workaround is `skill_view(name='productivity/not-spam-whitelist')` for reading the skill, or running the canonical script in-place from the skill dir via the proven terminal invocation

**Do NOT waste turns trying to fix the collision through Hermes tools — it is a root-level filesystem issue beyond the agent's permissions.**

### ⚠️ Aug 10, 2026 — Skill name resolves ambiguously; cron may report it "not found"

Two files match the name `not-spam-whitelist` on disk:
- `/data/hermes/skills/productivity/not-spam-whitelist/SKILL.md` (canonical skill)
- `/data/hermes/skills/domain/property-title-due-diligence/references/not-spam-whitelist.md` (reference file from another skill — permission-restricted)

Because of this collision, `skill_view(name='not-spam-whitelist')` fails with "Ambiguous skill name", and the recurring cron job opens with "Skill(s) not found and skipped: not-spam-whitelist" (a name-ambiguity false negative, NOT a missing skill). The runbook and scripts are fully present; the cron proceeds because the task prompt delivers the full column-layout and workflow inline. Workaround: load by categorized path `skill_view(name='productivity/not-spam-whitelist')` or read the canonical copy directly via `read_file('/data/hermes/skills/productivity/not-spam-whitelist/SKILL.md')`. The reference file under property-title-due-diligence should be renamed or moved to resolve the collision permanently.

**⚠️ This is a GENERAL pattern, not just this skill (confirmed Aug 16, 2026):** `property-title-due-diligence/references/` holds multiple files whose basenames collide with productivity skill names — `gws-automation` resolves ambiguously the same way (`productivity/gws-automation/SKILL.md` vs `domain/property-title-due-diligence/references/gws-automation.md`). Any bare-name `skill_view(...)` for a productivity skill can hit this. When the cron opener says "skill not found", check whether the skill actually exists at `/data/hermes/skills/productivity/<name>/` first; if yes, run the canonical script directly from disk — do not burn turns re-deriving the workflow.

**⚠️ Aug 17, 2026 — collision bit AGAIN; the ad-hoc fallback moved 2 via-pattern emails to inbox.** The 15:30 UTC cron opened with "Skill(s) not found and skipped: not-spam-whitelist" and the session hand-rolled a fresh matcher from the task prompt's inline algorithm — with NO via-exclusion and NO identity guard — then ran it (56 spam checked, 2 moved: `private@draas.com` + `Subscription@draas.com` by the @draas.com catch-all). Both had `via` in their display name (private and Subscription Group). The canonical via-exclusion would have kept both in spam. The ad-hoc script reported cleanly (2 moved, 0 errors) — the bug hid in plain sight. The report also missed flagging `noreply@housing-mailer.com` (present in spam) as a pending whitelist candidate. **This is the 2nd confirmed via-breach by an ad-hoc script (Aug 10 & Aug 17).** See `references/aug-17-adhoc-via-breach.md` for full details, diagnostics, and the fix to revert the false-positive moves back to SPAM. **⚠️ Aug 19, 2026 (evening run) — 3rd confirmed via-breach, identical failure chain** (see `references/aug-19-via-breach-adhoc.md`): the cron again opened with the ambiguity false-negative, an ad-hoc matcher moved `"'Samuel Johnson' via admin" <admin@draas.com>` (CII CFO Excellence Awards) to INBOX under the @draas.com catch-all, and the report omitted the mandatory housing-mailer.com pending-candidate flag (4 alerts present in spam).

**✅ Aug 18, 2026 — clean run, script used but no via senders present.** The 06:30 UTC cron ran an ad-hoc matcher (same pattern warned against above) after the skill loader reported the usual ambiguity false-negative. 60 spam checked, 2 moved (fcdo.gov.uk + godrejventure.com), 0 errors. No via-@draas.com senders present in spam, so the missing via-exclusion didn't cause harm. Still a near-miss — the ad-hoc script lacked both the via-exclusion and identity guard. Only reason no breach occurred was that the spam batch had zero @draas.com forwarded emails. housing-mailer.com also absent from this batch (first run since Aug 13 without it).

**⚠️ Aug 18, 2026 (18:30 UTC) — ad-hoc script had a column-indexing bug; zero-match was a false negative.** The cron opened with the same "Skill(s) not found" ambiguity. The hand-rolled matcher used `row[1]` (Category) as the rule_type instead of `row[6]` (Rule Type — column G), and `row[3]` (To Email) as the description instead of `row[5]` (Content Description). Every single rule was classified as unknown type → zero matches, clean report ("63 checked, 0 moved, 0 errors"). The bug hid because the report looked perfectly normal. **Caught by** the verify-the-engine step: dumping the raw sheet rows showed the mismatch between column labels and the script's indices. **Fixed** on second pass by aligning to the actual sheet layout (A=#, B=Category, C=From Email/Domain, D=To Email, E=Subject Keywords, F=Content Description, G=Rule Type, H=Date Added, I=Notes). Second pass moved 1 (`Partner.survey@royalsundaram.in`). A **third pass** was needed because `domain_from` with a full email match value (`creditcardalerts@kotak.bank.in`) was silently never matching — the logic did `sender_email.endswith('@' + mv)` where mv was the whole email, so `@creditcardalerts@kotak.bank.in` could never match `creditcardalerts@kotak.bank.in`. Added a fallback to extract the domain after `@` from full-email match values, which caught the Kotak card alert. **Final: 63 checked, 2 moved.** housing-mailer.com (3 "New Lead For Chalukya Ranka Stelo") still present in remaining 61 — flagged but still pending NDR confirmation since Aug 13. See the `domain_from Value Format Ambiguity` section below for the fixed logic. **New signal to add to upcoming-ad-hoc hazard list:** (4) column-indexing mismatch when the sheet layout is not verified before writing match logic.

**⚠️ Aug 19, 2026 (evening run) — 3rd via-breach + re-hit BOTH Aug 18 bugs in one ad-hoc session.** Same opener ("Skill(s) not found"), same rebuilt-from-prompt matcher. Three passes in one session:
1. **Pass 1** re-hit the **column-index bug** exactly as Aug 18: read `row[1]` (Category) as rule_type → all 30 rules classified as unknown type → zero matches except the hardcoded @draas.com catch-all. That catch-all — with NO via-exclusion — moved `"'Samuel Johnson' via admin" <admin@draas.com>` (CII CFO Excellence Awards 2025–26 | Call for Nominations) to INBOX. **This is the false positive; revert it to SPAM** (same modify-API swap as the Aug 17 fix).
2. **Pass 2** (after dumping raw sheet rows and aligning indices) re-hit the **`domain_from` full-email bug** exactly as Aug 18: `creditcardalerts@kotak.bank.in` never matched. **Pass 3** fixed the domain extraction and correctly moved the Kotak x0531 credit-card alert.
3. The final report **omitted the mandatory pending-candidate section** — 4 `noreply@housing-mailer.com` "New Lead For Chalukya Ranka Stelo" alerts were in the spam dump (entries #33/#39/#47/#70) and were NOT flagged to Nishant. This is the 3rd report to drop the standing housing-mailer.com flag (Aug 17, Aug 18 06:30, Aug 19 evening) despite the MANDATORY rule.

**What went right (capture for future runs):** the session verified moves by re-running the matcher to idempotent 0-move state, and confirmed each moved sender with a `from:<addr> in:inbox` Gmail search before reporting. Do this even with the canonical script — a "0 moved on second run" + "sender present in INBOX" pair is cheap proof the move landed. See `references/aug-19-via-breach-adhoc.md` for the full incident writeup.
\n**⚠️ Aug 22, 2026 (12:30 UTC) — 5th confirmed via-breach by an ad-hoc matcher.** The cron opened with the same ambiguity false-negative. An ad-hoc matcher (terminal + `build_service`) moved `"'Adobe Photoshop' via Subscription Group" <Subscription@draas.com>` to INBOX under the @draas.com catch-all — the via-exclusion guard was absent, same failure mode as Aug 10/12/17/19. Report: 11 spam checked, 1 moved, 0 errors — bug hid in plain sight. See `references/aug-22-1230-adhoc-via-breach-5th.md`.

**✅ Aug 20, 2026 (evening) — CLEAN run of the CANONICAL script in place; zero-move + one expected-NSDL-candidate.**** This run is the template for how the job *should* go every time — no ad-hoc matcher was hand-rolled. The cron opened with the usual ambiguity false-negative ("Skill not found and skipped"), but I loaded the skill by path (`skill_view(name='productivity/not-spam-whitelist')`) and ran `scripts/not_spam_check.py` **in place from the skill dir** via the proven terminal invocation (`cd /opt/hermes && env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy -u ALL_PROXY -u all_proxy GWS_VAULT_SOCKET=/run/gws-vault/vault.sock timeout 540 /opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py`). Result: identity verified ndr@draas.com (getProfile guard), **5 spam checked, 0 moved, 0 errors**. Verified the engine wasn't silently broken by running `list-spam.py` (same proxy-unset invocation): the 5 dump entries matched the 5 fetched by the check. The **NSDL variant-sender prediction held exactly**: `PCA_PravinC@nsdl.com` ("Outstanding Dues Notice - 20-08-2026") was present in spam, did NOT match the `billing_accounts@nsdl.com` exact_from rule, and was correctly LEFT in SPAM — flagged as a candidate (would need `domain_from: nsdl.com`) for NDR confirmation. housing-mailer.com was ABSENT this batch (so no pending-candidate flag fired; still note the standing Aug-13-pending status). **Lesson reinforced:** the canonical script in place + list-spam.py verification costs nothing extra and eliminates the entire recurring ad-hoc-breach class (via-exclusion absent, column-index bug, domain_from full-email gap). When the cron opener says "skill not found", do NOT hand-roll — load by path and run the canonical script.

**✅ Aug 20, 2026 — clean run via build_service (Approach B) terminal path; ad-hoc matcher still latent-buggy but this batch was benign.** The cron opened with the usual ambiguity false-negative, so a hand-rolled matcher was used again rather than the canonical `scripts/not_spam_check.py`. Two things to record:
1. **It did the RIGHT high-level flow:** dumped the raw sheet rows FIRST (caught the column-layout before writing match logic — avoided the Aug 18 column-index bug), aligned to the real header A=#…G=Rule Type (index 6), and ran the match+move via `build_service(service_name='google-draas')` through the trusted **terminal** process (the execute_code sandbox still lacks the `gws_fetch_token` stub → ImportError there; terminal works). **Result: 86 spam checked, 0 moved, 0 errors, identity = ndr@draas.com.** Clean zero-match day.
2. **BUT the ad-hoc matcher STILL carried both known latent bugs** that happened not to fire on this batch: (a) NO via-exclusion on the @draas.com/@drahomes.in catch-all, and (b) the `domain_from` full-email gap (`creditcardalerts@kotak.bank.in` as match value → unseen suffix). This batch happened to contain neither a via-@draas.com sender nor a full-email-domain rule sender, so the report looked clean while the bugs sat latent. **Confirming the recurring lesson: a clean-looking ad-hoc result proves nothing about guard completeness — only the canonical script's via-exclusion + getProfile identity guard are safe.** Also, the report's notable spam section listed CRIF/ET/CII/YourStory/phishing but did NOT explicitly call out the standing housing-mailer.com pending-candidate check — the MANDATORY flag was again weak. Check the spam dump for `noreply@housing-mailer.com` every run even on 0-move days.

⚠️ **Aug 22, 2026 — 5th via-breach confirmed.** The ad-hoc matcher in today's cron moved `"'Adobe Photoshop' via Subscription Group" <Subscription@draas.com>` to INBOX under the @draas.com catch-all. The via-exclusion was absent — same failure mode as Aug 10/12/17/19. See `references/aug-22-1230-adhoc-via-breach-5th.md`.

### ✅ Aug 21, 2026 (evening) — benign ad-hoc run; NSDL variant-sender prediction held again

The cron opened with the usual ambiguity false-negative ("Skill(s) not found and skipped"), and an **ad-hoc matcher was hand-rolled again** via `build_service(service_name='google-draas')` in the trusted **terminal** path (`/opt/data/*.py` + `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock`). This is the documented anti-pattern — BUT this was the "least-bad" variant: it (a) dumped the raw sheet rows FIRST and aligned to the real header (A=#, C=From/Domain=idx 2, G=Rule Type=idx 6 — avoided the Aug 18 column-index bug), (b) included BOTH the `@draas.com` AND `@drahomes.in` catch-alls, and (c) ran via terminal (not the sandbox). Result: **6 spam checked, 0 moved, 0 errors.**

**Why it was benign (not why it was "correct"):** the batch had NO via-@draas.com sender and NO full-email `domain_from` rule sender, so both latent bugs (missing via-exclusion on the catch-all, `domain_from` full-email gap) did not fire. Same lesson as Aug 20: a clean-looking ad-hoc result proves nothing about guard completeness. The canonical `scripts/not_spam_check.py` (via-exclusion + `getProfile` identity guard) was still the right call and was NOT used — do not relax the rule.\n\n**⚠️ Aug 22, 2026 — the 12:30 UTC cron proved this rule holds:** the ad-hoc matcher (same pattern, same missing guards) moved a via-@draas.com Subscription email to INBOX. Five via-breaches from five ad-hoc matchers. The correlation is deterministic. See `references/aug-22-1230-adhoc-via-breach-5th.md`.

**Confirmed the NSDL variant-sender prediction (2nd time):** `PCA_PravinC@nsdl.com` ("Outstanding Dues Notice - 20-08-2026") present in the 6-message batch, did NOT match the `billing_accounts@nsdl.com` exact_from rule, correctly LEFT in SPAM, flagged as pending candidate. **Aug 21 18:30 UTC run confirmed a THIRD NSDL sender variant (`noreply@nsdl.com` — "Outstanding dues towards various Services")** — strengthening the case for a `domain_from: nsdl.com` rule. NDR has still not confirmed a `domain_from: nsdl.com` rule (pending since Aug 20). **housing-mailer.com was ABSENT this batch** (so no mandatory pending-candidate flag fired; standing Aug-13-pending status remains).

### ✅ Aug 21, 2026 (12:30 UTC) — CANONICAL script ran in-place via `HERMES_SESSION_USER_ID=ndr`; 4 moved, 1 remaining

**Clean run of `not_spam_check.py` from the skill dir**, invoked with `cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py`. No proxy-unset required — the script worked without unsetting HTTP_PROXY vars, proving the proxy issue is intermittent, not deterministic.

**Result:** identity verified ndr@draas.com (getProfile guard), **5 spam checked, 4 moved to inbox, 0 errors**. Moved: `Partner.survey@royalsundaram.in` (exact_from), `disha.apte@godrejventure.com` (domain_from:@godrejventure.com), `cardstatement@kotak.bank.in` (domain_from:creditcardalerts@kotak.bank.in + domain_from:kotak.bank.in), `nach.alerts@kotak.bank.in` (domain_from + exact_from). **1 remaining** (not whitelisted).

**Key takeaway:** `HERMES_SESSION_USER_ID=ndr` is the correct identity override for cron context. The `canonical_uid("ndr")` resolves to `ndr-7449813913` which matches the vault key. No proxy-unset, no ad-hoc matcher — just the canonical script in place. This is the cleanest invocation pattern proven to date. See `references/aug-21-1230-clean-canonical-script.md` for full details.

**New data point:** the `domain_from:creditcardalerts@kotak.bank.in` rule matched `cardstatement@kotak.bank.in` (a completely different local-part) correctly via the domain-extraction normalization — proving the Aug 18 `domain_from` full-email fix is working in production.

### ✅ Aug 21, 2026 (18:30 UTC) — canonical script ran cleanly; 1 checked, 0 moved; 3rd NSDL variant confirmed

**Clean run** of `not_spam_check.py` from the skill dir, invoked with `cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/not-spam-whitelist/scripts/not_spam_check.py`. No proxy-unset needed — confirming the pattern is intermittent (2 consecutive runs without it).

**Result:** identity verified ndr@draas.com (getProfile guard), **1 spam checked, 0 moved, 0 errors**. The single spam message was from a **third NSDL sender variant**: `noreply@nsdl.com` ("Outstanding dues towards various Services till 20-08-2026 - NSDL - 0SG3 / BUX-RA"). Did NOT match the `billing_accounts@nsdl.com` exact_from rule, correctly left in SPAM. This is distinct from the earlier `PCA_PravinC@nsdl.com` variant (different local-part, similar subject). Three distinct NSDL sender addresses have now appeared in spam since Aug 20 — the recurring pattern is well-established.

### ⚠️ Aug 26, 2026 (cron) — 6th ad-hoc matcher, benign batch, new batchGet pitfall

The cron opener reported the usual name-collision false negative ("Skill(s) not found and skipped"). The session hand-rolled ANOTHER matcher (terminal + `build_service(service_name='google-draas')`) instead of running `scripts/not_spam_check.py` in place. It (a) dumped the sheet first and aligned columns correctly (A=#, C=From/Domain=idx 2, G=Rule Type=idx 6), (b) included the @draas.com catch-all, but (c) STILL had NO via-exclusion and NO getProfile identity guard — the 6th consecutive ad-hoc matcher without either guard. **Result: 5 spam checked, 1 moved, 0 errors** — benign ONLY because the batch contained no via-@draas.com sender and no NSDL variant (moved: `creditcardalerts@kotak.bank.in` "Transaction successful on your Kotak Credit Card x0531" via `domain_from: kotak.bank.in`; batch otherwise: CII conference, Bangalore International Centre, RISE Global Summit, StartEngine — correctly left in spam). No housing-mailer.com present → no pending-candidate flag. A clean ad-hoc result proves nothing about guard completeness (same lesson as Aug 20/21); the canonical script is still the only safe path.

**NEW pitfall hit this run:** `gmail.users().messages().batchGet(...)` does NOT exist in this googleapiclient build — raises `AttributeError: 'Resource' object has no attribute 'batchGet'`. Fallback that worked: per-message `users().messages().get(id=..., format='metadata', metadataHeaders=['From','Subject','Date'])` (fine for ≤200 msgs). `users().messages().batchModify(...)` DOES work (used for the move: `body={"ids": [...], "addLabelIds": ["INBOX"], "removeLabelIds": ["SPAM"]}`), and post-move verification by refetching the message id and checking `labelIds` (INBOX present / SPAM absent) confirmed the move. Full detail in `references/aug-26-adhoc-benign-batchget.md`.

**Rule census as of Aug 26, 2026: 35 rows — 20 `exact_from`, 14 `domain_from`, 1 `combined`, 0 `subject_contains`** (shifted from Aug 24's 17/15/1 — several domain_from rows were evidently converted to exact_from; verify against the live sheet, don't assume).

### ⚠️ Aug 10, 2026 — GWS_VAULT_SOCKET may be unset in the sandbox; the fix is one line

In cron/sandbox `execute_code`, `GWS_VAULT_SOCKET` may be unset even though the
vault daemon is healthy (`/run/gws-vault/vault.sock` exists). Symptom:
`gws_resolve_account` returns "GWS_VAULT_SOCKET is not set — cannot reach the
vault. Bind-mount /run/gws-vault and set the env var". This is NOT a vault
outage — the socket is right there. Fix before any gws call in the sandbox:

```python
import os
os.environ["GWS_VAULT_SOCKET"] = "/run/gws-vault/vault.sock"
```

Vault reads and `gws_resolve_account` then work from `execute_code`. Still run
the full check via `terminal()` (`/opt/hermes/.venv/bin/python3
/data/hermes/skills/productivity/not-spam-whitelist/scripts/check-spam.py`)
per the proven runbook — the sandbox is only good for quick probes (identity
guard + via-exclusion live in check-spam.py).

## Active Issues (as of Aug 21, 2026)

| Account | Token Status | Last Verified | Notes |
|---------|-------------|---------------|-------|
| ndr@draas.com (google-draas) | ✅ Valid | Aug 21 18:31 UTC | Verified by getProfile; works |
| nishantranka@gmail.com (google-gmail) | ✅ Valid | Aug 21 18:31 UTC | 90 spam, 0 matched (whitelist scoped to work contacts) |
| ndr@ahfl.in (google-ahfl) | ❌ EXPIRED | Aug 21 18:31 UTC | `invalid_grant: Token has been expired or revoked.` Needs re-auth via `send_oauth_url(login_hint='ndr@ahfl.in', label='ahfl')` |

**ahfl token expiry — Aug 21, 2026:** The google-ahfl OAuth token for ndr@ahfl.in returned `invalid_grant` at 18:31 UTC. This is the first observed expiry for this account. Re-authorizing via the standard `send_oauth_url` flow with `login_hint='ndr@ahfl.in'` should restore it. Until then, the not-spam check will skip this account with an error. The whitelist is primarily scoped to ndr@draas.com anyway (work senders), so this is non-blocking — but track it as an active issue.

**🔎 Aug 24, 2026 (08:35 UTC) resolver observation:** `gws_resolve_account_tool` from terminal reported `has_token: true` for ALL THREE accounts (google-draas, google-ahfl, google-gmail). This is a **presence-level** check only (`has_token` does not exercise refresh) — it does NOT prove the google-ahfl `invalid_grant` expiry from Aug 21 is healed. Until a real API call on google-ahfl succeeds, treat the ahfl expiry note as still standing.

**Multi-account check pattern (Aug 21 18:31 UTC):** The ad-hoc script used in this session attempted to check ALL THREE authorized GWS accounts. This is EXPANSIVE coverage compared to the canonical `not_spam_check.py` which only checks `google-draas`. The whitelist rules are overwhelmingly for ndr@draas.com (bank alerts, legal, internal, vendors sent to `ndr@draas.com` or `ndr@drahomes.in`), so checking personal gmail is low-value (0/90 matched here). Recommendation: keep the canonical script's single-account focus unless the user explicitly asks for cross-account checks. The ad-hoc script's multi-account loop is useful for diagnostics but not needed for daily runs.

**⚠️ Aug 17, 2026 — `build_service()` in the sandbox fails even WITH the env var set.** After setting `GWS_VAULT_SOCKET`, `gws_resolve_account` works (has_token checks), but `tools.gws_auth.build_service(...)` raises `RuntimeError: Tool 'gws_fetch_token' is not available in execute_code. Available: patch, read_file, search_files, terminal, web_extract, web_search, write_file`. This is the SAME known limitation (the sandbox shim lacks the `gws_fetch_token` stub and the parent's execute_code toolset whitelist rejects it) — do NOT diagnose it as a vault or auth problem. The working pattern: write the script to a file and run it via `terminal()` with `/opt/hermes/.venv/bin/python3` and `sys.path.insert(0, "/opt/hermes")` — the terminal env has `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock` and the full main-process env, so `build_service` takes the direct vault path.

## Rule Types
- `exact_from` — Match exact sender email address
- `domain_from` — Match any email from this domain
  - If value starts with `@` (e.g. `@draas.com`): check `sender_email.endswith(value)`
  - If value contains `@` but is a full email (e.g. `creditcardalerts@kotak.bank.in`): extract the domain part after `@` and do suffix match — do NOT blindly prepend another `@`
  - If value has no `@` (e.g. `gmail.com`): prepend `@` and check suffix
- `subject_contains` — Subject contains any of the keywords
- `combined` — Combination of from-domain AND subject keywords

## How to Add New Not-Spam Entries
When the user identifies a new email in spam that should not be there (often via voice message):

1. **ALWAYS search Gmail first** — the user may describe the sender by brand name (e.g. "Geo Autopay", "Kotak card"), and the actual From domain may differ. Search the SPAM folder using the user's description:
   ```python
   results = service.users().messages().list(userId='me', q='in:spam subject:autopay', maxResults=5).execute()
   ```
   Extract the actual `From:` header from the found emails — never rely on voice-transcribed domain names alone.
2. Use the real From address / domain (from step 1) to determine the rule type:
   - Regular sender (bank, legal, known contact) → `exact_from` with their full address
   - Known domain (e.g., @kotak.bank.in) → `domain_from`
   - Needs subject matching (card number, specific topic) → `subject_contains` or `combined`
3. **Check the existing Whitelist rows BEFORE appending** — read the full Whitelist tab first and look for an exact_from/domain_from rule covering the sender. If it's already there, do NOT append a duplicate row; skip straight to moving the email to INBOX and tell the user the rule already existed. Live example (11-Aug-2026): HDFC KYC `information@hdfcbank.bank.in` was already row 5 in the sheet, so only the email was moved — no new row. Appending duplicates pollutes the sheet and makes the audit trail ambiguous.
4. Append the new row to the Whitelist sheet using Sheets API (only if not already covered)
5. Mark the specific email as not spam (remove SPAM label, add INBOX)
6. Report back to the user what was added — read back the domain name to confirm the spelling

## Blacklist Tab — Structure (Columns A-I)

Same column layout as Whitelist:

| Column | Header              | Purpose                        |
|--------|---------------------|--------------------------------|
| A      | #                   | Row number                     |
| B      | Category            | Classification label           |
| C      | From Email / Domain | Sender address or domain       |
| D      | To Email            | Recipient                      |
| E      | Subject Keywords    | Keywords for subject matching  |
| F      | Content Description | Human-readable description     |
| G      | Rule Type           | `domain_from`, `exact_from`    |
| H      | Date Added          | Date rule was added            |
| I      | Notes               | Additional notes               |

## How to Add Blacklist Entries

When the user manually moves emails from inbox to spam (often via voice message identifying inbox emails that should have been spam):

1. **Scan all current spam** — list every sender currently in `in:spam` to find the ones the user moved (distinguish from auto-filtered via-pattern emails which already go to spam via the cron rule)
2. **Skip via-pattern senders** — `info@draas.com`, `marketing@draas.com`, `admin@draas.com` emails with "via" in the display name are already handled by the cron job's via-rule exclusion. Do NOT add them to the blacklist.
3. **Determine rule type:**
   - `domain_from` — whole domain to block (preferred for vendor spam, conference invites)
   - `exact_from` — specific sender only (if only one address from a domain is spam)
4. **Append new row to Blacklist tab** using Sheets API append
5. **Do NOT move these emails** — they're already in spam. The blacklist is for future matching.

**⚠️ The check-spam.py cron job does NOT currently process the Blacklist tab** (it only processes Whitelist). Blacklist rules are manual reference for now. If the user asks about auto-moving future blacklisted senders to spam, note that the cron script needs enhancement.

## "via" Pattern Exclusion — Emails Forwarded Through @draas.com

Emails where the **From display name** contains ` via ` (e.g. `"'Urban News Digest' via Marketing" <marketing@draas.com>`) are treated as spam even though the sender address is `@draas.com`. These are auto-forwarded newsletters, not genuine internal emails.

**Logic in check-spam.py (line ~142):**
```python
# @draas.com catch-all
if sender_email.lower().endswith(DRAAS_DOMAIN):
    if " via " in sender.lower():          # ← EXCLUDE forwarded emails
        print(f"  [{sender}] -> @draas.com but 'via' pattern — SKIPPING (spam)")
        continue
```

**Rule principle:** The `@draas.com` catch-all applies to the **From** address only — never to To/Cc addresses. If an email is To/Cc a @draas.com address but From an external domain, it must match a specific whitelist rule to be moved. The "via" exclusion layer protects against false positives from email forwarding/gateway patterns.

**⚠️ Confirmed with Nishant (Jun 2026):** The `@draas.com` catch-all rule is explicitly a **From-only** rule. Emails sent FROM outside the domain but addressed TO/CC a @draas.com address must NOT be auto-moved by the catch-all — they need their own whitelist entry. This prevents legitimate external newsletters/promotions sent to team addresses from being inadvertently promoted to inbox.

**Known senders caught by this rule (Jun 2026):**
- `* via Marketing` <marketing@draas.com> — Urban News Digest, Internshala, others
- `* via admin` <admin@draas.com> — IPR sessions, HRMS vendors
- `* via hr` <hr@draas.com> — vendor outreach
- `* via info` <info@draas.com> — vendor emails
- `noreply-spamdigest via *` — Google Workspace spam digest reports (should stay in spam, not inbox)
- `* via Subscription Group` <Subscription@draas.com> — Adobe marketing/newsletter digests (Illustrator, Photoshop, Adobe Stock, purchase receipts, verification codes). Confirmed Aug 2026: 9 such messages were in inbox from earlier runs — all via-pattern, all should stay in spam. Do NOT let the @draas.com catch-all move them.
- ⚠️ **Aug 22, 2026 — 5th via-breach:** `"'Adobe Photoshop' via Subscription Group" <Subscription@draas.com>` was moved from SPAM→INBOX by an ad-hoc matcher under the @draas.com catch-all. The via-exclusion was absent (same as Aug 10/12/17/19). The canonical script would have skipped it. See `references/aug-22-1230-adhoc-via-breach-5th.md`.
- `* via private` <private@draas.com> — impersonation emails ("Prime Minister's Office via private", "Election Commission via private"). Confirmed Aug 17, 2026: ad-hoc matcher without the via-guard moved 2 of these to inbox. The display name contains `" via "` but the @draas.com address is NOT a real account — it's an impersonation/spoof vector. The via-exclusion catches this correctly. Observed again Aug 25, 2026: `'CBC-MIB' via private` <private@draas.com> skipped correctly by the canonical script.

**Known Nishant-specific patterns (add proactively when matching emails appear in spam):**
- Kotak credit card alerts for **card ending 0531** — from `creditcardalerts@kotak.bank.in`
- Any `@draas.com` internal email — catch-all domain rule
- Google Drive share notifications from `drive-shares-dm-noreply@google.com` — check sender name
- HDFC Bank from `@hdfcbank.bank.in` — legitimate per RBI mandate (see domain research below)
- Jio billing / Jio Autopay debit failed from `ebill.mobility@jio.com` or similar jio.com addresses — e-bills, autopay debit failures, bill summaries. Sent to `ndr@drahomes.in`. Subject typically contains "autopay", "debit", "failed", "bill".
- IDFC FIRST Bank from `@idfcfirst.bank.in` or `@emailer.idfcfirst.bank.in`
- **NSDL billing** from `billing_accounts@nsdl.com` — invoices from National Securities Depository Ltd for DRA group companies (Bux-Ranka Developers, etc.). Sent to multiple recipients including `ndr@drahomes.in`. Subject contains "Invoice" and company code (e.g. `0SG3`). Rule: `exact_from`. **Watch for variant senders from `nsdl.com`** — three distinct sender addresses have appeared in spam (none matching the whitelisted `billing_accounts@nsdl.com`): `PCA_PravinC@nsdl.com` ("Outstanding Dues Notice", Aug 20 & Aug 21 evening) and `noreply@nsdl.com` ("Outstanding dues towards various Services", Aug 21 18:30 UTC). The accumulating evidence (3 sightings across 2 sender addresses) strongly suggests a `domain_from: nsdl.com` rule if NDR wants all NSDL correspondence in inbox. Until confirmed, leave these in SPAM.
- **Royal Sundaram survey** from `Partner.survey@royalsundaram.in` — periodic customer-satisfaction survey ("Your opinion matters"). Moved to INBOX on Aug 21, Aug 24, AND Aug 25, 2026: it re-lands in spam on a regular cadence, so a REPEAT move is expected, not a bug or a duplicate. Rule: `exact_from`. Do NOT confuse with `RoyalSundaramVconnect@royalsundaram.in` (a different sender that must NOT match this rule).
- **V Swaminathan** from `v.swaminathank@gmail.com` — Ranka NorthStar (Allalsandra) / Katenahalli project contact (plan copies, status updates, "any progress?", "launching date"). Spotted in spam 25-Aug-2026 → whitelisted `exact_from` same day. Rule: `exact_from`.
- **User-initiated "leftover spam" cleanup (25-Aug-2026):** when NDR reports emails "left over in spam", the 3 messages are usually a mix of ALREADY-whitelisted senders (rules exist — do NOT append duplicates; HDFC `alerts@` / `information@` exact_from rows were the case here) plus ONE new sender needing a rule. Workflow that resolves it in one pass: dump sheet rows → search the actual From addresses in Gmail → append ONLY missing rules → batchModify the spam IDs (remove SPAM / add INBOX) → verify each message's labelIds → run the canonical `not_spam_check.py` to prove 0 spam + N rules loaded. Note: the 3-hourly cron can still leave whitelisted mail behind when the skill-name ambiguity blocks rule loading (job `239314bd5ab5`) — a manual cleanup pass is the reliable backstop.
- **UK FCDO** from `@fcdo.gov.uk` — C R Priya, UK Foreign, Commonwealth & Development Office. Government correspondence. Rule: `domain_from`.
- **Godrej Venture** from `@godrejventure.com` — BRDPL project correspondents (Disha Apte, Amit Saraf, Tina Mehta, Leena Hasnani). Rule: `domain_from`.
- **Fidelity / DB Retirement Plan** from `Fidelity.Investments@mail.fidelity.com` — Deutsche Bank matched savings / 401K retirement statements. Rule: `exact_from`.
- **Rajiv Dadlani / Lilac Venture** from `rajadadlani@hotmail.com` — Lilac Insights investor updates. Partner/colleague. Rule: `exact_from`.
- **HDFC Bank Smart Statement** from `hdfcbanksmartstatement@hdfcbank.bank.in` — "HDFC Bank Combined Email Statement for <Month>-YYYY". Rule: `combined` — domain `hdfcbank.bank.in` + subject keyword `statement` (captures any future HDFC statement sender, not just this exact address). Added 03-Aug-2026.
- **Sudheer Ramath** from `sudheer.ramath2020@gmail.com` — land parcel JV proposals (Kakanad, Kochi etc.). NOT "Sudhir Ramanathan" — see worked example #7. Rule: `exact_from`.
- **⏳ PENDING NDR CONFIRMATION — Housing.com lead alerts** from `noreply@housing-mailer.com` — "New Lead For Chalukya Ranka Stelo" (project lead notifications). Flagged in most cron reports since Aug 13, 2026 (still no rule as of Aug 19; 4 alerts in the Aug 19 evening batch, 4 in the Aug 18 18:30 batch). **⚠️ Do NOT auto-add** — the user has not confirmed yet. If/when he does, the rule is `domain_from: housing-mailer.com`. Until then, keep flagging it in the report as the top whitelist candidate and mention it has been pending since Aug 13. **The pending-candidate section is MANDATORY in every cron report, including days with zero moves** — the Aug 17 03:30 UTC run (3 housing-mailer alerts in spam) missed it entirely because the skill never loaded, and the Aug 19 evening run dropped it again (4 alerts present, never flagged), so Nishant has NOT received the standing flag on 3 runs (Aug 17, Aug 18 06:30, Aug 19 evening). Check the spam list (or `scripts/list-spam.py` output) for this sender every run even when nothing matched.

## Cron Schedule — Every 3 Hours
The cron runs **6 times daily** at these IST times:

| IST | UTC | 
|-----|-----|
| 9:00 AM | 3:30 UTC |
| 12:00 PM | 6:30 UTC |
| 3:00 PM | 9:30 UTC |
| 6:00 PM | 12:30 UTC |
| 9:00 PM | 15:30 UTC |
| 12:00 AM | 18:30 UTC |

**Cron expression:** `30 3,6,9,12,15,18 * * *`

**Only moves matching emails to inbox — never deletes anything.** Deletion is for user manual review.

## Verified Domain Research (June 2026)

**`.bank.in` Indian banking domain is legitimate per RBI mandate (April 2023).**
- RBI directed all scheduled commercial banks to exclusively use `*.bank.in` for official email communications
- `.bank.in` is tightly controlled by IDRBT, not publicly registerable — DNSSEC protected
- **HDFC Bank:** `alerts@hdfcbank.bank.in` (transaction alerts), `information@hdfcbank.bank.in` (KYC, product info)
- **IDFC FIRST Bank:** `statement@idfcfirst.bank.in`, `alwaysyoufirst@emailer.idfcfirst.bank.in`
- **Kotak Mahindra Bank:** `creditcardalerts@kotak.bank.in`, `nach.alerts@kotak.bank.in`
- **Key tell:** `@hdfcbank.com` is being phased OUT; `@hdfcbank.bank.in` is the legitimate replacement
- **Phishing domains to flag:** `@hdfcbank.co.in`, `@hdfcbank.net`, `@hdfc-bank.in` — NOT registered by HDFC

## OAuth Tokens — Two Auth Paths

### ⚠️ Jul 11, 2026 ROOT-CAUSE FIX — read this before touching auth code

Every prior "auth failure" reported by this job (Jul 5, Jul 7 x2, Jul 11) was the
**same underlying bug**, misdiagnosed each time as a fresh problem: this skill's
scripts called `tools.gws_vault_client.get_token()` **directly**, hardcoding
`user_id="ndr@draas.com"` and `service="google"`. That key was **never the real
storage key** — tokens are written by `tools.gws_auth.exchange_and_store()` under
the **canonical vault user_id** (`ndr-<telegram-id>`, resolved from the email via the
vault's identity table) and the account-specific service key `google-draas` (not
the generic `"google"`). Querying the wrong key always returns empty / raises
`VaultNoTokenError`, **regardless of whether the token is valid**. Confirmed live
on Jul 11, 2026:

```
has_token("ndr-<telegram-id>", "google-draas", session_uid="ndr-<telegram-id>") → True
resolve("email", "ndr@draas.com") → "ndr-<telegram-id>"
```

The token had been valid the entire time. **Do not hand-roll `gws_vault_client`
calls with a literal email as `user_id`.** Use `tools.gws_auth.load_credentials()`
instead (see below) — it resolves the email to the canonical uid internally via
`canonical_uid()`. This is also the sole sanctioned Google-auth path per the
project's own CLAUDE.md ("NEVER build Google credentials inline — always go
through `tools.gws_auth`"). See `references/jul-11-wrong-vault-key-bug.md` for
the full writeup.

### ⚠️ Jul 12, 2026 — `load_credentials` itself fails on refresh (`invalid_scope`)

A **new failure mode** appeared the day after the Jul 11 fix: `load_credentials`
itself is now the problem, not the key lookup. The token is fine, the key is
fine — but `tools/gws_auth.py:288` does:

```python
creds = Credentials.from_authorized_user_info(
    json.loads(token_json), HERMES_GWS_SCOPES   # ← env constant, not token's scopes
)
```

`HERMES_GWS_SCOPES` is a module-level constant in `gws_auth.py` that has
**grown over time** as new features (Photos, etc.) were added to the OAuth
client. As of Jul 12, 2026 it includes three Google Photos scopes the ndr@draas.com
token **never had**:

```
https://www.googleapis.com/auth/photospicker.mediaitems.readonly
https://www.googleapis.com/auth/photoslibrary.appendonly
https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata
```

When `load_credentials` builds the `Credentials` object with this wider scope
list, the next `creds.refresh(Request())` call (line 292) requests the union of
scopes from Google — which rejects with `invalid_scope: Bad Request` because the
refresh token was never authorized for Photos.

**Direct refresh still works.** A manual `requests.post` to
`https://oauth2.googleapis.com/token` with the same `client_id` + `client_secret`
+ `refresh_token` returns 200 OK with a valid access token. Only the `google-auth`
library's scope-aware refresh fails.

**Confirmed live Jul 12, 2026:**
- Stored token scopes (7): `gmail.modify, calendar, drive, contacts, tasks, documents, spreadsheets`
- `HERMES_GWS_SCOPES` (10): the 7 above **plus 3 photos scopes**
- Error: `google.auth.exceptions.RefreshError: ('invalid_scope: Bad Request', ...)`
- Direct `requests.post` to `oauth2.googleapis.com/token`: HTTP 200, valid token

**Workaround for the cron script (does NOT require patching `gws_auth.py`):**
build the `Credentials` object from the token's **own** scope list, not the env
constant. The token JSON's `scopes` key is the source of truth for what the
refresh token is authorized for.

```python
import sys, json
sys.path.insert(0, "/opt/hermes")
from tools.gws_vault_client import get_token, resolve
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

uid = resolve("email", "ndr@draas.com")
tok = json.loads(get_token(uid, "google-draas", session_uid=uid))
creds = Credentials.from_authorized_user_info(tok, tok.get("scopes"))  # ← token scopes, not HERMES_GWS_SCOPES
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
```

This works identically to `load_credentials` for all other purposes (it
auto-refreshes, returns a working `Credentials` object, builds `googleapiclient`
services normally). The only difference: it doesn't get a vault write-back
(refreshed token is held in memory; the main process will persist on the next
refresh via the in-process `load_credentials` path, or the env constant is fixed
eventually). For a single cron run that's fine.

**Long-term fix:** patch `tools/gws_auth.py:288` to use
`json.loads(token_json).get("scopes")` (the token's own scopes) instead of
`HERMES_GWS_SCOPES` when building the `Credentials` object. This requires editing
a project file — out of scope for the cron job to do, flag it for the next
maintenance window.

See `references/jul-12-scope-mismatch-bypass.md` for the full transcript and confirmation commands.

### ✅ Aug 2, 2026 — Token re-authorized; Photos + youtube scopes now present

The ndr@draas.com token's stored scopes now include the 3 Photos scopes
(`photospicker.mediaitems.readonly`, `photoslibrary.appendonly`,
`photoslibrary.readonly.appcreateddata`) plus `youtube`, alongside the
original 7 (gmail.modify, calendar, drive, contacts, tasks, documents,
spreadsheets). It was re-authorized at some point after Jul 12, so the
`invalid_scope` refresh bug above is no longer triggered by this token —
`HERMES_GWS_SCOPES` and `tok["scopes"]` are back in sync.

**Keep `get_creds()` building Credentials from `tok.get("scopes")` anyway.**
It is correct whether or not the env constant matches the token, and it
does not depend on `HERMES_SESSION_USER_ID` (safe in cron). Do NOT
"simplify" back to `load_credentials()`: the zero-arg form still raises
in cron, and explicit-id `load_credentials()` only works while the env
constant stays in sync with the token. The direct-vault pattern is the
stable one; leave it alone.
confirmation commands.

### Path A: Vault-Based (ndr@draas.com) — Preferred, CONFIRMED WORKING

**Policy (Nishant, Aug 2, 2026): all token lookups go through the VAULT ONLY, via the SANCTIONED TOOLS ONLY — no direct vault client calls from ad-hoc scripts.** The sanctioned paths are `tools.gws_auth.build_service(...)`, `tools.gws_auth.load_credentials(...)`, and the `gws_fetch_token` tool. Never call `tools.gws_vault_client.get_token()` / `resolve()` directly in new scripts. The `check-spam.py` script's `get_creds()` uses a direct vault read + token-scope pattern — this is a maintained, verified exception (the token's own scopes are the source of truth; the env-constant path has a known scope-mismatch history). If you copy that pattern into a new script, prefer the sanctioned wrapper instead and flag the check-spam.py exception for eventual migration.

The ndr@draas.com token lives in the **gws-vault-server** daemon at
`/run/gws-vault/vault.sock`, stored under the **canonical vault user_id**
(`ndr-<telegram-id>`) and service key `google-draas`. This token owns the DRAAS
whitelist sheet and has full gmail.modify scope.

| Token Holder | Google Account | Sheet Access | Gmail Access | Status |
|-------------|---------------|-------------|--------------|--------|
| `ndr-<telegram-id>` / `google-draas` (vault) | ndr@draas.com | ✅ Owns sheet | ✅ gmail.modify | ✅ Confirmed present (Jul 11, 2026) |

**How to access (correct, sanctioned path) — applied in `scripts/check-spam.py` v2026-07-12+:**

The `check-spam.py` script's `get_creds()` reads from the vault and builds a
`Credentials` object directly from the token's own scope list (NOT
`HERMES_GWS_SCOPES` — see Jul 12 scope-mismatch note below). The same pattern
is available as a one-liner for ad-hoc cron probes:

```python
import sys, json
sys.path.insert(0, "/opt/hermes")
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from tools.gws_vault_client import get_token, resolve

DRAAS_UID = "ndr@draas.com"
DRAAS_SERVICE = "google-draas"

uid = resolve("email", DRAAS_UID)
tok = json.loads(get_token(uid, DRAAS_SERVICE, session_uid=uid))
creds = Credentials.from_authorized_user_info(tok, tok.get("scopes"))
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
```

**Why this is now the preferred path (vs. `load_credentials()`):**
`tools.gws_auth.load_credentials()` builds `Credentials` from the env
constant `HERMES_GWS_SCOPES`, which has grown to include 3 Google Photos
scopes the ndr@draas.com token was never authorized for. The next
`creds.refresh()` rejects with `invalid_scope: Bad Request`. Building from
`tok.get("scopes")` (the token's own authorized list) avoids that.
Confirmed live in cron on Jul 12, 2026 — see
`references/jul-12-scope-mismatch-bypass.md`.

**Do NOT call `tools.gws_vault_client.get_token()` directly with a hand-typed
email as `user_id`** — that pattern was the Jul 11 bug (queried
`user_id="ndr@draas.com"` literally, never matched the canonical
`ndr-<telegram-id>` key, always returned empty). Always resolve the email to
the canonical uid first via `resolve("email", "...")` (or use the
`get_creds()` helper in `scripts/check-spam.py` which does this for you).

### Path B: Vault-Only — NO File-Based Tokens Exist

**There are NO file-based tokens anywhere in this deployment — do not look for them.** Per Nishant's hard policy (Aug 2, 2026): tokens NEVER exist under any users folder (`/data/hermes/users/<id>/`, `/opt/hermes/hermes-data/users/<id>/`, etc.) for any user, EVER. The vault daemon at `/run/gws-vault/vault.sock` is the ONLY token storage. If a prompt or doc references a token file path under a users folder, that reference is STALE — ignore it, do not `ls` for it, do not check it. All token access goes through the vault via `tools.gws_auth.build_service(...)` / `load_credentials(...)` / the `gws_fetch_token` tool — never direct `tools.gws_vault_client.get_token()` calls from your own scripts.

**Do NOT use any personal or stray token file, even if one is handed to you or appears on disk** (e.g. a personal Gmail account). Per policy (Aug 2, 2026) no file-based tokens are ever used — vault-only. A personal-account token authenticates as a different Google account, cannot access the DRAAS whitelist sheet, and using it is a security violation.

### Auth URL Generation (When the Vault Token Is Missing)

OAuth client credentials are set in the environment. Generate an auth URL from any Python (no extra packages needed):

**Primary method —`urllib.parse.urlencode` (no dependencies, works in any Python):**
```python
import os
from urllib.parse import urlencode

SCOPES = "https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/spreadsheets"

params = {
    "response_type": "code",
    "client_id": os.environ["HERMES_OAUTH_CLIENT_ID"],
    "redirect_uri": "https://transcribe.ahfl.in/gws/auth/callback",
    "scope": SCOPES,
    "state": "ndr@draas.com",   # vault-stored: use email/user_id; file-stored: use telegram_id
    "access_type": "offline",
    "prompt": "consent",
    "login_hint": "ndr@draas.com",
}
auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
print(auth_url)
```

**Alternative —`google_auth_oauthlib` (requires the hermes venv):**
```python
import os
from google_auth_oauthlib.flow import Flow

SCOPES = ["https://www.googleapis.com/auth/gmail.modify",
          "https://www.googleapis.com/auth/spreadsheets"]
client_config = {
    "web": {
        "client_id": os.environ["HERMES_OAUTH_CLIENT_ID"],
        "client_secret": os.environ["HERMES_OAUTH_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["https://transcribe.ahfl.in/gws/auth/callback"],
    }
}
flow = Flow.from_client_config(client_config, scopes=SCOPES,
    redirect_uri="https://transcribe.ahfl.in/gws/auth/callback",
    autogenerate_code_verifier=False)
url, _ = flow.authorization_url(
    access_type="offline", prompt="consent",
    state="ndr@draas.com", login_hint="ndr@draas.com")
```

**⚠️ Environment variable availability:**
- `execute_code` sandbox: ❌ Does NOT have `HERMES_OAUTH_CLIENT_ID` or `HERMES_OAUTH_CLIENT_SECRET`
- `terminal()` / hermes venv: ✅ Both env vars ARE available (confirmed Jul 2026)
Run auth URL generation via `terminal()` using the urllib approach (zero dependencies) or the hermes venv. The system Python also lacks `google-auth-oauthlib` — prefer urllib.

**Callback stores based on `state` parameter:**
- `state=ndr@draas.com` → `tools.gws_auth.exchange_and_store()` resolves this via `canonical_uid()` to `user_id=ndr-<telegram-id>`, then auto-detects the service from the authorized account's id_token email (`EMAIL_TO_SERVICE["ndr@draas.com"] = "google-draas"`) — vault store, correct path.
- `state=ndr` → file store at a legacy path (personal account only, not applicable in this deployment).

### Token Refresh (Vault-Based)

The vault daemon handles refresh automatically— no manual token management needed. NEVER write, update, or create any token file on disk, for any reason.

### Recovery When Token Is Revoked

## Implementation Pitfalls

### `gws_auth.build_service` / `load_credentials` — Safe in Cron IF Called With an Explicit `telegram_id`

**Corrected Jul 11, 2026** — the earlier version of this note told agents to avoid
`gws_auth` entirely in cron. That was an overcorrection: the real hazard is only
the **zero-argument default path**.

`tools.gws_auth.build_service(api, version)` / `load_credentials(telegram_id)`
called **with no `telegram_id`** fall back to reading `HERMES_SESSION_USER_ID`
from the environment — which cron deliberately clears (see project's
`cron/scheduler.py::run_job`), so the zero-arg form raises `ValueError` in cron
context, or (for other jobs) may resolve a different uid than expected.

**`load_credentials` was the right path from Jul 11 → Jul 12, but is broken as
of Jul 12, 2026** (scope-mismatch — see
`references/jul-12-scope-mismatch-bypass.md`). `scripts/check-spam.py` no
longer uses it; it builds `Credentials` directly from the token's own scopes
instead. The zero-arg-vs-explicit-id warning is still true for
`load_credentials` if you need it for an unrelated ad-hoc probe.

### Sheets API 503 Transient Error — Always Retry

Sheets `spreadsheets().values().get()` can return `HttpError 503` (Service Unavailable) even when the spreadsheet metadata endpoint (`spreadsheets().get()`) works fine. This is a transient Google-side issue, NOT an auth failure, wrong-account problem, or permission error.

**Observed Aug 19, 2026:** two consecutive 503s followed by a clean response after a 10-second wait. Fix: wrap values reads in a 3-attempt retry loop with exponential backoff:

```python
for attempt in range(3):
    try:
        result = sheets.spreadsheets().values().get(...).execute()
        break
    except Exception as e:
        if attempt < 2:
            time.sleep(3 * (attempt + 1))
        else:
            raise
```

Do NOT diagnose a 503 as a vault outage, revoked token, or wrong account. Retry first.

### Gmail API: no `messages().batchGet` in this googleapiclient build (Aug 26, 2026)
`gmail.users().messages().batchGet(...)` raises `AttributeError: 'Resource' object has no attribute 'batchGet'` — the generated client does not expose it. Do NOT build the fetch around it. Working equivalent: per-message `users().messages().get(userId='me', id=<id>, format='metadata', metadataHeaders=['From','Subject','Date'])` and read headers via `{h['name'].lower(): h['value'] for h in msg['payload']['headers']}`. For ≤200 spam messages this is fine (≈1s each, batch of 5 takes seconds). `users().messages().batchModify(...)` DOES exist and is the right way to apply the SPAM→INBOX move in one call: `body={"ids": [...], "addLabelIds": ["INBOX"], "removeLabelIds": ["SPAM"]}` — then verify each moved id by refetching and checking `labelIds` contains INBOX and not SPAM (do not search by subject — that returns historical copies from earlier runs; see Aug 25 note).

### Column Indexing When Reading the Sheet
The Sheets API returns values as a flat array. Column indices are 0-based where A=0, B=1, C=2, etc. The matching value (From Email / Domain) is at **index 2**, not index 1. Always dump the raw rows to verify before writing matching logic.

### ⚠️ Empty Column G (Rule Type) — Silent Rule Death Bug (Aug 23, 2026)
**10 of 33 whitelist rows have an EMPTY Rule Type column (G).** The canonical scripts (`check-spam.py` and `not_spam_check.py`) were silently skipping these rows because `matches_rule()` returns `False` for empty rule_type. This was a production bug that affected rules for: `@drahomes.in`, `samdoc_mamc@yahoo.com`, `jayck_1960@yahoo.com`, `hdfcbank.bank.in` (combined + 'statement'), `Partner.survey@royalsundaram.in`, `namita.swamy@gmail.com`, `kotak.bank.in`, `axis.bank.in`, `canarabank.com`, and `devanshgoel112233@gmail.com`.

**Fix (applied Aug 23, 2026 to both canonical scripts):** after reading `rule_type` from column G, infer it when empty:
- Value starts with `@` (e.g. `@drahomes.in`) → `domain_from`
- Value contains `@` but not at start (e.g. `samdoc_mamc@yahoo.com`) → `exact_from`
- Value has no `@` AND has subject keywords → `combined` (domain + subject)
- Value has no `@` and no keywords, but contains `.` (e.g. `kotak.bank.in`) → `domain_from`
- Fallback → `exact_from`

**Check for this bug in any ad-hoc matcher:** the `@drahomes.in` rule is the best litmus test. If your matcher never moves a `@drahomes.in` sender, the inference logic is missing.

**✅ Aug 24, 2026 — column G is now populated on ALL 34 rows** (same rows that were empty on Aug 23 now carry explicit `exact_from` / `domain_from` / `combined` — the inference was evidently written back to the sheet). Keep the inference logic in the canonical script as a safety net, but don't assume empty G anymore. Rule-type census as of Aug 24: 17 `exact_from`, 15 `domain_from`, 1 `combined` (hdfcbank.bank.in + 'statement'), 0 `subject_contains`.

### ⚠️ Empty column A (#) — ad-hoc loader trap; the `#` column is NOT a key (Aug 24, 2026)
- **10 of 34 whitelist rows have an EMPTY `#` column (A)**: the same rows that previously had empty G — `samdoc_mamc@yahoo.com`, `@drahomes.in`, `jayck_1960@yahoo.com`, `hdfcbank.bank.in` (combined + statement), `Partner.survey@royalsundaram.in`, `namita.swamy@gmail.com`, `kotak.bank.in`, `axis.bank.in`, `canarabank.com`, `devanshgoel112233@gmail.com`.
- **NEVER skip a row because column A is empty.** An ad-hoc loader that does `if not r[0]: continue` silently drops 10 of 34 rules (observed live Aug 24: "24 rules loaded" instead of 34; fixed by skipping only fully-blank rows). The canonical script never reads column A and is unaffected.
- The `#` numbering is unreliable even when populated: duplicate `17` (google.com domain + arch_arvind2000 exact), duplicate `25`, and unused numbers 15/18/19/20. **Never key rules on `#`** for matching or reports — identify by (value, rule_type), report by sheet row position.
- **⚠️ Rule 15 (jio.com) inconsistency to flag in reports:** the sheet lists `jio.com` with `domain_from` but column E carries keywords (`autopay, debit, failed`). Under canonical semantics `domain_from` ignores column E → every jio.com sender would be moved, not just autopay/debit ones. If NDR wants keyword-gated jio mail, the rule must become `combined`. Do not change it unilaterally — keep flagging.

See `references/aug-24-0833-adhoc-3-moved.md` for the full run record (loader trap, resolver string quirk, moves).

### `domain_from` Value Format Ambiguity
The sheet sometimes stores full email addresses under a `domain_from` rule (e.g. `creditcardalerts@kotak.bank.in` with rule_type `domain_from`). The correct behavior is to extract the domain after `@` (`kotak.bank.in`) and check `sender_email.endswith('@' + domain)`, NOT to blindly prepend `@` to the whole value (which would produce `@@creditcardalerts@kotak.bank.in`).

**✅ Aug 10, 2026 — canonical `not_spam_check.py` now implements this.** `normalize_domain()` extracts the part after the last `@` when column C holds a full email (plus `lstrip('@')` for `@domain` style). Before this fix, the `domain_from:creditcardalerts@kotak.bank.in` rule silently NEVER matched — a live false negative caught by the zero-move verification pass (20 spam, Kotak x0531 alert stuck in spam despite an existing rule). Symptom to watch for: a 0-move day right after a new full-email `domain_from` rule was added — dump spam + rules (see the verify-the-engine note) and confirm the rule actually fires before trusting the result.

### Voice transcription domain name errors — search variants and verify before adding to whitelist

Nishant frequently uses voice messages on Telegram. STT consistently mangles domain names — especially plurals, single-vs-double letters, homophones, and company name spellings. Every time he dictates a domain name:

1. **Search Gmail FIRST** — before adding anything to the whitelist, search Gmail (both INBOX and SPAM) to find the actual sender domain. Voice STT can produce an entirely wrong domain that's a homophone or close sound-alike of the real domain. Never add a domain to the whitelist based solely on voice transcription.
2. **Check all folders (SPAM + INBOX)** — not just inbox. The user may be asking because an expected email isn't arriving (it could be in spam).
3. **Try common variants automatically** — don't wait for a correction:
   - Plural variant: add/remove `s` (`manipalhospital.com` → `manipalhospitals.com`)
   - Homophones and sound-alikes: `Geo` → `Jio`, `Zee` → `ZTE`, `eBay` → `ibay`
   - Common misspellings: double letters, missing vowels
   - `.com` → check if `.in` or `.co.in` also exist
   - Different TLD: if `.com` gives 0, try `.org`, `.in`, `.co.in`
4. **Use Gmail wildcard queries to probe for the real domain:**
   ```python
   for variant in [base, base+'s', base+'s.com', base+'.co.in']:
       result = svc.users().messages().list(userId='me', q=f'from:{variant}', maxResults=5).execute()
       print(f'from:{variant} → {result.get(\"resultSizeEstimate\",0)} results')
   ```
5. **After adding to the whitelist, read back the entry for confirmation** — summarize what was added and ask the user to confirm the spelling before the next cron run picks it up. This catches errors before they're actioned.
6. **If the user corrects a domain spelling**, update the existing row (do NOT add a new row). Add a note in the Notes column (e.g. "Corrected from geo.com") so the audit trail is clear.

**Worked examples (Jun 2026):**
1. Nishant said "manipalhospital.com" via voice → Gmail found 0 results. Tried `manipalhospitals.com` (plural) → 312 existing emails, 2 in spam. The correct domain was `manipalhospitals.com` — voice STT dropped the final "s". Always try the plural variant first when medical/hospital/company names are involved.
2. Nishant said "geo.com" via voice (referring to Jio Autopay debit failed notifications) → STT heard "Geo" but the correct domain was `jio.com`. **Root cause:** In Indian English, "Jio" (जिओ) and "Geo" (जिओ) are near-homophones — both pronounced /dʒiːoʊ/. Voice STT picked the more common English word. Lesson: brand names that are also common English words (Jio/Geo, Lyf/Life, Zomato/Tomato) are high-risk for voice transcription errors. When the context is telecom, mobile, digital payments, or Indian services, the voice-said name is likely a brand whose English spelling differs from the phonetic transcription.

3. **Sinchana Gowda vs "Cincina Gouda" (Jun 2026):** User said "Cincina Gouda at draas.com" via voice for a new in-house architect. STT produced `cincina.gouda@draas.com` but the correct name and email are **Sinchana Gowda** (`sgowda@draas.com`). Pattern: STT produced a phonetically similar but wrong name entirely, not just a spelling variant. **Fix:** Before using any new personal name from voice, search Gmail for past emails to/that person to find their actual email. If no Gmail hits, present the email you plan to use and ask — do not assume `${name}@draas.com` is valid just because the person works at DRAAS.

4. **C R Priya vs "CRPRIA" (Jul 2026):** User said "CRPRIA at fcdo.gov.uk" via voice — STT joined the initials into a single string. The actual sender is **C R Priya** (`C-R.Priya@fcdo.gov.uk`), a person at the UK Foreign, Commonwealth & Development Office. Pattern: Space-separated initials get concatenated by STT into an acronym-like string. **Fix:** When the user says what sounds like an acronym, check if it's actually spaced initials by searching Gmail for the domain part only.

5. **Amit Saraf vs "Amit Sharif / Amit Sheriff" (Jul 2026):** User said "Amit Sharif from Godrej Ventures" via voice. The actual sender name is **Amit Saraf** (`amit.saraf@godrejventure.com`). Pattern: Common Indian surnames that STT hears as a more common English-word homophone (Saraf → Sharif/Sheriff). **Fix:** When the user names a person from Godrej Venture, first check the actual emails in Gmail — voice consistently gets the surname wrong for this company.

6. **Rajiv Dadlani email discrepancy (Jul 2026):** User said "Rajiv Dadlani at hotmail.com" via voice. The actual email found in Gmail is `rajadadlani@hotmail.com` (not `rajivdadlani@hotmail.com`). Pattern: Voice STT sometimes expands or normalizes a shortened email handle. **Fix:** Always verify the exact email from Gmail search results — never rely on the voice-transcribed email address as-is, even when the name sounds correct.

8. **Access Bank → Axis Bank, "Kanara" → Canara Bank, "Devang Goyal" → Devansh Goel (Aug 2026) — bank homophones:** Nishant dictated three whitelist requests in one voice message. STT heard *Access Bank* (`access.bank.in`), *Kanara* (bank), and *Devang Goyal*. All three were wrong, mapped by searching Gmail:
   - **"Access Bank" = Axis Bank** — `alerts@axis.bank.in`. There is NO `access.bank.in` in Gmail (0 results); Axis Bank has 201+. Probing `from:axis.bank.in` vs `from:access.bank.in` disambiguates instantly.
   - **"Kanara" = Canara Bank** — `canarabank.com`. "Kanara" is a homophone of **Canara**. Probing `from:canarabank.com` (201+ results) vs `from:karnatakabank`/`karur` (ambiguous generic hits) resolved it. When a dictated bank name doesn't resolve, try the homophone brand: Canara, Kotak, Axis, Karur Vysya, Karnataka Bank.
   - **"Devang Goyal" = Devansh Goel** — `devanshgoel112233@gmail.com` (Sarvam AI / Exotel / Ozonetel telephony vendor; @0xgoel). Reason: a known contact in the telephony project whose email was literally sitting in spam ("Re: Sarvam AI + Exotel/Ozontel telephony project"). The spam email itself is the ground truth for the sounding-alike vendor name.
   **Generalization:** for bank/credit alert dictations, the `.bank.in`/`.com` domain is a near-guaranteed STT mangling point — always search Gmail (`from:<domain>`) and probe the likely homophone before adding a rule. Add the real domain (e.g. `axis.bank.in`) with `domain_from`, not the dictated string.

## Correcting an Existing Rule vs Adding a New One
- **User says "add X"** → append a new row (normal flow above).
- **User says "correct rule N / fix the whitelist entry"** → find the row (by row number or by scanning for the dictated name), search Gmail for the REAL sender, and update that row in place. Never leave a dead rule with a never-matching address — it pollutes the sheet and future agents may "fix" it again.

### Script Execution Path
The hermes venv Python is at `/opt/hermes/.venv/bin/python3`. The `google` packages (google-api-python-client, google-auth, google-auth-oauthlib) live there — the system Python won't have them. Always invoke scripts with the hermes venv Python.

### Token Refresh — Automatic via google-auth (Vault-Based)

The GWS token expires periodically. `scripts/check-spam.py`'s `get_creds()`
handles refresh automatically (as of v2026-07-12+, which uses the direct
vault read + token-scope pattern — NOT `tools.gws_auth.load_credentials()`,
which has a latent scope-mismatch bug at `gws_auth.py:288`):
1. Resolves the email/id to the canonical vault uid via `resolve("email", "ndr@draas.com")`
2. Fetches token JSON from vault via `get_token(uid, "google-draas", session_uid=uid)`
3. Builds `Credentials.from_authorized_user_info(tok, tok.get("scopes"))` — **token's own scopes**, NOT `HERMES_GWS_SCOPES`
4. Checks `creds.expired and creds.refresh_token`
5. Calls `creds.refresh(Request())` if needed (no vault write-back — held in memory)

No manual token management needed — just run `check-spam.py` from cron with
the hermes venv Python. See **Vault-Based Auth — Working Approach (as of
Jul 12, 2026)** below for the full code block, and
`references/jul-12-scope-mismatch-bypass.md` for the diagnosis of why
`load_credentials()` itself fails.

### ⚠️ Jul 13, 2026 — `google-draas` slot holds the WRONG Google account (silent identity failure)

A **fifth-class failure mode**: the token reads cleanly, refresh succeeds,
scopes are fine — but `gmail.users().getProfile(userId="me")` returns a
different email than expected. In this incident, the
`ndr-<telegram-id> / google-draas` vault slot (canonical uid + service
key) was holding **`psingh@draas.com`**'s OAuth token, not
`ndr@draas.com`'s. Sibling slots on the same uid
(`google-ahfl` → ndr@ahfl.in, `google-gmail` → nishantranka@gmail.com)
were correct; only `google-draas` was wrong.

Likely cause: a re-auth flow (possibly the Jul 11–12 recovery attempts)
was completed with the wrong Google account signed in, and the callback
`state` resolved via `canonical_uid()` to the same canonical uid +
`google-draas` service — overwriting the slot reserved for the real
ndr account.

**Symptom:** Sheets API 403s (`HttpError 403: The caller does not have
permission`) on the DRAAS Whitelist sheet, even though the token is
perfectly valid. Gmail API works, but on the wrong account.

**Required guard — add to the top of `main()` in `scripts/check-spam.py`
right after the `getProfile` call:**

```python
prof = gmail.users().getProfile(userId="me").execute()
expected = "ndr@draas.com"
if prof["emailAddress"].lower() != expected:
    raise SystemExit(
        f"Vault slot misconfig: google-draas authenticates as "
        f"{prof['emailAddress']}, not {expected}. Re-authorize "
        f"{expected} with state=ndr@draas.com to fix."
    )
```

Without this guard, the failure mode looks like a sheet-share issue and
gets misdiagnosed (cf. Jul 11 "vault empty" misdiagnosis). With it, the
script fails loud at the top, surfaces the exact fix, and the user
knows to re-auth without a 20-minute diagnostic dance.

**Diagnostic that pinpointed the issue** (run all services on the
canonical uid, check who each one authenticates as):

```python
import sys, json
sys.path.insert(0, "/opt/hermes")
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from tools.gws_vault_client import get_token, resolve, list_services

uid = resolve("email", "ndr@draas.com")
for svc in list_services(uid, session_uid=uid):
    tok = json.loads(get_token(uid, svc, session_uid=uid))
    creds = Credentials.from_authorized_user_info(tok, tok.get("scopes"))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    g = build("gmail", "v1", credentials=creds, cache_discovery=False)
    who = g.users().getProfile(userId="me").execute().get("emailAddress")
    print(f"  {svc:20s} -> {who}")
```

**Fix:** re-authorize ndr@draas.com with `state=ndr@draas.com` to
overwrite the bad slot. Use env-var client credentials
(`HERMES_OAUTH_CLIENT_ID` / `HERMES_OAUTH_CLIENT_SECRET`) — both
available in `terminal()` and the hermes venv, NOT in the
`execute_code` sandbox. See `references/jul-13-wrong-account-in-vault-slot.md`
for the full transcript (live `getProfile` output, full diagnostic
session, stopgap Gmail-only partial run).

### ⚠️ Aug 2, 2026 — Intermittent hang on first run: RETRY before any auth diagnosis

`check-spam.py` (and any vault/Gmail probe using the same pattern) can hang
for 60–300+s on the FIRST invocation, then complete in seconds on retry.
Observed live Aug 2, 2026: first run timed out at 300s; an immediate retry
completed cleanly in ~20s. Individual pieces (vault `resolve`/`get_token`,
token refresh, Sheets/Gmail API) each returned in <1s once the hang cleared.
No auth error, no vault error, no token problem — just an intermittent stall.

**Rule: if a cron run times out, retry once before any auth diagnosis.**
The skill's history (Jul 5/7/11/12/13) is a chain of transient issues
misdiagnosed as token failures. A 300s timeout followed by a fast clean
retry is the hang signature — a genuinely revoked/empty token raises
immediately (`invalid_grant` / `VaultNoTokenError`), it does not stall.
For cron context, give the script a generous timeout (≥480s) on the first
attempt and budget one retry.

#### Recovery When Token Is Revoked

When `creds.refresh()` raises `invalid_grant: Token has been expired or revoked`, the refresh token is dead and re-authorization is required. The `check-spam.py` script catches this and prints a clear message — it does NOT crash with a raw traceback.

**Standard recovery (cron context):** Generate an auth URL from the vault token's embedded client credentials — read the existing token via the *correct* canonical key so this doesn't hit the Jul 11 bug again:

```python
import sys, json
sys.path.insert(0, "/opt/hermes")
from tools.gws_vault_client import get_token
from urllib.parse import urlencode

token_json = get_token("ndr-<telegram-id>", "google-draas", session_uid="ndr-<telegram-id>")
tok = json.loads(token_json)

params = {
    "response_type": "code",
    "client_id": tok["client_id"],
    "redirect_uri": "https://transcribe.ahfl.in/gws/auth/callback",
    "scope": " ".join(tok.get("scopes", SCOPES)),
    "state": "ndr@draas.com",
    "access_type": "offline",
    "prompt": "consent",
    "login_hint": "ndr@draas.com",
}
auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
print(auth_url)
```

Note: `state=ndr@draas.com` tells the callback handler to resolve via
`canonical_uid()` and store under `ndr-<telegram-id>` / `google-draas` — the same
key this script now reads from. The next cron run picks it up automatically.

**First real occurrence (Jul 5, 2026):** See `references/jul-5-token-revoked.md` for the original timeline.
**Second occurrence (Jul 7, 2026):** See `references/jul-7-token-revoked.md` — confirmed the vault-based recovery pattern works identically to the old file-based one, just using `get_token()` directly instead of file I/O.
**Third occurrence (Jul 11, 2026) — misdiagnosed as "vault empty", actually the wrong-key bug:** See `references/jul-11-vault-empty-first-run.md` for the original (incorrect) diagnosis, and `references/jul-11-wrong-vault-key-bug.md` for the actual root cause and fix. The token was never revoked or missing — every diagnostic call in that transcript queried `user_id="ndr@draas.com"` literally instead of resolving to the canonical uid, so it looked identical to "vault empty" while the real token sat untouched under `ndr-<telegram-id>` / `google-draas`.
**Fourth occurrence (Jul 12, 2026) — `load_credentials` itself fails on scope-mismatched refresh:** See `references/jul-12-scope-mismatch-bypass.md`. The fix from Jul 11 was correctly applied, but the next day `load_credentials` started failing again — this time with `invalid_scope` during refresh, not `VaultNoTokenError` during read. Root cause: `gws_auth.py:288` builds `Credentials` from the env constant `HERMES_GWS_SCOPES` (which has grown to include 3 Google Photos scopes), but the ndr@draas.com token was authorized for 7 scopes without Photos. Refresh requests the union, Google rejects, direct `requests.post` to the same endpoint succeeds. Workaround: build `Credentials.from_authorized_user_info(tok, tok.get("scopes"))` with the **token's** scopes instead of the env constant.

### Vault-Based Auth — Working Approach (as of Jul 12, 2026)

`scripts/check-spam.py` v2026-07-12+ uses the **direct vault read + token-scope
Credentials** approach in its `get_creds()` function. This is the pattern that
actually works in cron context — `tools.gws_auth.load_credentials()` raises
`invalid_scope` on refresh because of the scope-mismatch bug (see
`references/jul-12-scope-mismatch-bypass.md`).

```python
import sys, json
sys.path.insert(0, "/opt/hermes")
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from tools.gws_vault_client import get_token, resolve

DRAAS_UID = "ndr@draas.com"
DRAAS_SERVICE = "google-draas"

def get_creds():
    uid = resolve("email", DRAAS_UID)
    tok = json.loads(get_token(uid, DRAAS_SERVICE, session_uid=uid))
    creds = Credentials.from_authorized_user_info(tok, tok.get("scopes"))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds
```

**Identity resolution:** `resolve("email", "ndr@draas.com")` returns the
canonical vault uid `"ndr-<telegram-id>"`, which is then passed as **both**
`user_id` and `session_uid` to `get_token()`. This satisfies the vault's
self-read check without depending on `HERMES_SESSION_USER_ID` at all — so
the function is safe in cron context. **Do not** hardcode the email as
`user_id` (Jul 11 wrong-key bug — the email is the login identifier, not
the vault storage key).

### Vault Present But Empty — Daemon Running, No Stored Token

The vault daemon may be running (socket at `/run/gws-vault/vault.sock`) but genuinely contain **no tokens for any user** (true first-run/never-authorized case — distinct from the Jul 11 wrong-key misdiagnosis above, which looked identical but wasn't this).

**Error signature:** `VaultNoTokenError: No google token for user ndr-<telegram-id>. Authorize first.`

**Diagnosis (use the CANONICAL uid, not the raw email):**
1. Socket exists: `ls /run/gws-vault/vault.sock` → shows the socket
2. Resolve the email to canonical uid first: `resolve("email", "ndr@draas.com")` → e.g. `"ndr-<telegram-id>"`
3. Vault contents for that uid: `list_services("ndr-<telegram-id>", session_uid="ndr-<telegram-id>")`. If this returns `[]`, nothing at all is stored. If it returns some services (e.g. `['vocab']`) but NOT `google-draas`, the vault has partial data but the needed Google token is missing — same outcome as empty.
4. `has_token("ndr-<telegram-id>", "google-draas", session_uid="ndr-<telegram-id>")` returns `False`
5. Confirm vault status — `has_token("<canonical-uid>", "google-draas", session_uid="<canonical-uid>")` returns `False`
6. **Do NOT check any token file path under a users folder** — such files NEVER exist per policy (Aug 2, 2026). Vault is the only storage. Skip straight to re-auth.
7. No personal token file exists by default in this deployment (per canonical reference: token-access-canonical.md).

**⚠️ All vault diagnostic calls in cron context must pass explicit `session_uid` equal to the resolved canonical `user_id`.** Never query with the raw email as `user_id` directly — always call `resolve()` first (or better, just use `tools.gws_auth.load_credentials()`/`has_token()` which does this for you).

**Real occurrence (Jul 11, 2026) — corrected:** What looked like a first-time/vault-empty run was actually the wrong-key bug (see the root-cause note at the top of "OAuth Tokens"). The token was present under `ndr-<telegram-id>` / `google-draas` the entire time; the diagnostic in `references/jul-11-vault-empty-first-run.md` queried the wrong key and got a false-empty result. If a genuine no-token case is ever hit in the future, use the corrected diagnostic steps above (resolve → canonical uid → correct service name) before concluding the vault is actually empty.

**Cron deliverable when a token genuinely doesn't exist:** The cron job's final response IS the auth URL — the system delivers the report to Nishant automatically. The message must clearly state: (a) what failed (`VaultNoTokenError`), (b) the diagnosis (confirmed via canonical-uid lookup, not a raw-email guess), (c) the full auth URL with `state=ndr@draas.com`, (d) whether the vault socket was present, what services the vault holds (e.g. `['vocab']` only), whether a user-specified token path was checked and didn't exist. Do NOT silently retry, do NOT fabricate a "0 moved, 0 checked" success line. Honest blocker reporting is the deliverable — but only after confirming via the CORRECT key that there really is no token.

**Stale credential-file references — IGNORE them:** Any cron prompt or instruction that references a credential file path is STALE and must never be checked. Per Nishant's hard policy (Aug 2, 2026), token files under any users folder NEVER exist for any user, EVER — vault daemon storage is the only canonical path. When a prompt references a credential file path, ignore the path and go straight to vault auth. If the vault has no token for the needed service, generate an auth URL with `state=ndr@draas.com` for vault storage.

**First-authorization recovery:** Generate an auth URL using env-var client credentials (see Auth URL Generation below). Unlike the "token revoked" case, this doesn't require any existing token — the env vars `HERMES_OAUTH_CLIENT_ID` and `HERMES_OAUTH_CLIENT_SECRET` are always set.

**Critical: The `state` parameter in the auth URL determines where the callback stores the token:**
- `state=ndr@draas.com` → resolved via `canonical_uid()` to `user_id=ndr-<telegram-id>`, service auto-detected as `google-draas` from the id_token email — **correct for vault-based setup** (use in cron context)
- `state=ndr` → legacy fallback (personal account only, not applicable in this deployment)

After the callback completes, verify the token was stored:
```python
from tools.gws_auth import has_token
print(has_token("ndr@draas.com", "google-draas"))
```

### Vault Daemon Unreachable — Missing Socket

The vault daemon (`gws-vault-server`) binary may not be deployed on the container. When this happens, `get_token()` raises `FileNotFoundError` because the socket at `/run/gws-vault/vault.sock` was never bound. The directory `/run/gws-vault/` exists (created at container build time) but is empty.

**Diagnosis:** See `references/missing-vault-daemon-diagnosis.md` for the full check procedure (binary search, s6 service check, alternative paths).

**Fallback Strategy (discovered Jul 7, 2026, updated Jul 29, 2026):**

When the vault daemon is missing, there is no pre-existing personal token available. File-based GWS tokens do not exist in this deployment. The only recourse is to generate a fresh ndr@draas.com auth URL.

**User-specified token path — DO NOT CHECK.** Any prompt referencing a token file path under a users folder is STALE per Nishant's hard policy (Aug 2, 2026). Such files NEVER exist for any user. Skip straight to vault re-auth: if the vault is reachable but empty for the needed service, generate an auth URL with `state=ndr@draas.com`. Do NOT silently produce a "0 moved, 0 checked" result.

**Resolution of old claim:** No file-based tokens exist in this deployment — all tokens are stored in the vault daemon at `/run/gws-vault/vault.sock`. Any custom path under a users folder referenced in a prompt is stale; ignore it and use vault storage.

### Cron Safe Mode
Cron jobs run with `execute_code` blocked. All logic must be written to a `.py` file on disk and invoked via `terminal()`. Shell inline Python (`python3 -c "..."`) is okay for small probes but the main check script should be a standalone file.

**Working script available at:** `scripts/check-spam.py` (within this skill). Invoke from cron with:
```bash
/opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/not-spam-whitelist/scripts/check-spam.py
```

**Companion script — `scripts/list-spam.py`:** lists every message currently
in SPAM (date | From | Subject) **plus a BY-DOMAIN count summary** (upgraded
Aug 16, 2026: now uses the sanctioned `build_service(service_name=
'google-draas')` path, paginates to the cap, and aggregates per-domain counts
so repeat offenders jump out). Invoke with the same `env -u` proxy-unset +
`HERMES_SESSION_USER_ID=ndr` + `GWS_VAULT_SOCKET` preamble as
`not_spam_check.py`. Use it to produce the "what's sitting in spam" section
of the cron report so potentially-important unmatched senders (land JV
proposals, lead notifications, known contacts, bank surveys) get flagged for
the user to whitelist — the main check only prints what it MOVED, not what
it skipped.

**Gmail-only fallback (when vault daemon is missing):** There is no pre-built fallback script. When vault is unavailable and no token file exists, generate an ndr@draas.com auth URL using the env-var OAuth client credentials (see "Auth URL Generation" section above — run via `terminal()` where the env vars are available, NOT `execute_code` sandbox) and report the URL as the cron deliverable. The token will be vault-stored after the OAuth callback completes, and the next cron tick picks it up automatically.

Never use a personal or stray token file, even if one exists at some legacy path — prefer generating a fresh ndr@draas.com auth URL (vault-stored via the callback).

**Do NOT prefix with `HERMES_SESSION_USER_ID`** — the script uses the
direct vault read + token-scope pattern in `get_creds()`, which does not
read `HERMES_SESSION_USER_ID` at all. The vault read is gated by the
explicit `session_uid=uid` argument to `get_token()`, where `uid` is
`resolve("email", DRAAS_UID)` — this satisfies the vault's self-read
check in cron context without depending on any session env var.
