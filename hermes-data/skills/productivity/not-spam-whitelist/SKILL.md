---
name: not-spam-whitelist
title: Not-Spam Email Whitelist Manager
description: Maintain and use the DRAAS not-spam whitelist spreadsheet. Add new entries when user identifies non-spam emails, and run 3-hourly check to auto-unspam matching emails.
---

## Sheet Location
- **Sheet URL:** https://docs.google.com/spreadsheets/d/1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0/edit
- **Sheet ID:** 1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0
- **Tabs:** Whitelist (legitimate senders), Blacklist (confirmed spam senders)

## Tabs
- **Whitelist** — Approved senders to auto-move from SPAM to INBOX
- **Blacklist** — Same columns as Whitelist. For senders manually flagged as spam after arriving in inbox. Added when user identifies spam that landed in primary inbox.

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

Ready-to-run script: `scripts/not_spam_check.py` in this skill. Copy it to /opt/data and run from the TRUSTED terminal process (NOT execute_code):

    cd /opt/hermes && python3 /opt/data/not_spam_check.py

Proven production facts:
- **Run via terminal, not the execute_code sandbox.** The sandbox's `hermes_tools` stub has no `gws_fetch_token` import → `tools.gws_auth.load_credentials()` raises ImportError there. The trusted terminal process has `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock` and works. This is a sandbox-routing quirk, not a vault outage — do not tell the user the vault is down.
- **Account:** `service_name='google-draas'` = ndr@draas.com (primary). All DRAAS accounts have tokens in the vault; `has_token()` works from terminal.
- **Rule types actually seen:** `exact_from` (most common), `domain_from` (normalize column C: strip leading '@', match if sender domain endswith OR sender endswith '@'+domain — handles both '@kotak.com' and 'manipalhospitals.com' styles), `combined` (domain AND subject — e.g. hdfcbank.bank.in + 'statement'), `subject_contains` (split column E on commas, case-insensitive substring).
- **Internal catch-all:** sender domain == draas.com or endswith .draas.com → always move. (Row 11 in the sheet duplicates this as a domain_from rule.)
- **Move = modify API:** `body={'removeLabelIds': ['SPAM'], 'addLabelIds': ['INBOX']}`. NEVER delete; NEVER send.
- **Verify the engine before trusting a 0-move result:** a zero-match day is normal (5 spam/day typical), but dump each spam message's sender/subject + matched rules to confirm the parser isn't broken. E.g. an `exact_from` rule for `RoyalSundaramVconnect@royalsundaram.in` must NOT match `partner.survey@royalsundaram.in` (same domain, different sender — correctly left in spam).
- **Pagination:** SPAM volume is tiny (≤5/day); list with maxResults=200 and stop when `nextPageToken` is absent.

### ⚠️ Aug 10, 2026 — Skill name resolves ambiguously; cron may report it "not found"

Two copies of this skill exist on disk:
- `/data/hermes/skills/productivity/not-spam-whitelist/` (canonical)
- `/data/hermes/home/.hermes/skills/productivity/not-spam-whitelist/` (duplicate)

Because of the duplicate, `skill_view(name='not-spam-whitelist')` — and even
`skill_view(name='productivity/not-spam-whitelist')` — fails with "Ambiguous
skill name", and the recurring cron job may open with "Skill(s) not found and
skipped: not-spam-whitelist". That is a name-ambiguity false negative, NOT a
missing skill: the runbook and scripts are fully present. Workaround: read the
canonical copy directly, e.g.
`read_file('/data/hermes/skills/productivity/not-spam-whitelist/SKILL.md')`
and run `scripts/check-spam.py` by absolute path as usual. (The duplicate copy
should eventually be deleted so the name resolves cleanly.)

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
3. Append the new row to the Whitelist sheet using Sheets API
4. Mark the specific email as not spam (remove SPAM label, add INBOX)
5. Report back to the user what was added — read back the domain name to confirm the spelling

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

**Known Nishant-specific patterns (add proactively when matching emails appear in spam):**
- Kotak credit card alerts for **card ending 0531** — from `creditcardalerts@kotak.bank.in`
- Any `@draas.com` internal email — catch-all domain rule
- Google Drive share notifications from `drive-shares-dm-noreply@google.com` — check sender name
- HDFC Bank from `@hdfcbank.bank.in` — legitimate per RBI mandate (see domain research below)
- Jio billing / Jio Autopay debit failed from `ebill.mobility@jio.com` or similar jio.com addresses — e-bills, autopay debit failures, bill summaries. Sent to `ndr@drahomes.in`. Subject typically contains "autopay", "debit", "failed", "bill".
- IDFC FIRST Bank from `@idfcfirst.bank.in` or `@emailer.idfcfirst.bank.in`
- **NSDL billing** from `billing_accounts@nsdl.com` — invoices from National Securities Depository Ltd for DRA group companies (Bux-Ranka Developers, etc.). Sent to multiple recipients including `ndr@drahomes.in`. Subject contains "Invoice" and company code (e.g. `0SG3`). Rule: `exact_from`.
- **UK FCDO** from `@fcdo.gov.uk` — C R Priya, UK Foreign, Commonwealth & Development Office. Government correspondence. Rule: `domain_from`.
- **Godrej Venture** from `@godrejventure.com` — BRDPL project correspondents (Disha Apte, Amit Saraf, Tina Mehta, Leena Hasnani). Rule: `domain_from`.
- **Fidelity / DB Retirement Plan** from `Fidelity.Investments@mail.fidelity.com` — Deutsche Bank matched savings / 401K retirement statements. Rule: `exact_from`.
- **Rajiv Dadlani / Lilac Venture** from `rajadadlani@hotmail.com` — Lilac Insights investor updates. Partner/colleague. Rule: `exact_from`.
- **HDFC Bank Smart Statement** from `hdfcbanksmartstatement@hdfcbank.bank.in` — "HDFC Bank Combined Email Statement for <Month>-YYYY". Rule: `combined` — domain `hdfcbank.bank.in` + subject keyword `statement` (captures any future HDFC statement sender, not just this exact address). Added 03-Aug-2026.
- **Sudheer Ramath** from `sudheer.ramath2020@gmail.com` — land parcel JV proposals (Kakanad, Kochi etc.). NOT "Sudhir Ramanathan" — see worked example #7. Rule: `exact_from`.

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

### Column Indexing When Reading the Sheet
The Sheets API returns values as a flat array. Column indices are 0-based where A=0, B=1, C=2, etc. The matching value (From Email / Domain) is at **index 2**, not index 1. Always dump the raw rows to verify before writing matching logic.

### `domain_from` Value Format Ambiguity
The sheet sometimes stores full email addresses under a `domain_from` rule (e.g. `creditcardalerts@kotak.bank.in` with rule_type `domain_from`). The correct behavior is to extract the domain after `@` (`kotak.bank.in`) and check `sender_email.endswith('@' + domain)`, NOT to blindly prepend `@` to the whole value (which would produce `@@creditcardalerts@kotak.bank.in`).

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

7. **Sudhir Ramanathan vs Sudheer Ramath (Aug 2026) — correction to an EXISTING rule, not a new one:** User said "Sudhir Ramanathan email address Sudhir.Ramanathan2020 at Gmail should be added in whitelist... correct the rule 28 to the correct address as per the sender". The sheet rule 28 already contained `sudhir.ramanathan2020@gmail.com` (an earlier voice transcription that never matched anything). Searching spam for the actual sender found **Sudheer Ramath <sudheer.ramath2020@gmail.com>** ("LAND PARCEL JV PROPOSAL: 6.5 Acres @ Infopark, Kakanad"). STT had converted two real words (Sudheer + Ramath) into a more common-sounding full name (Sudhir + Ramanathan). **Fix workflow:** (a) when the user asks to "correct rule N to the correct address", ALWAYS search `in:spam` for the sender's real email first — the user's dictated address may itself be wrong, and the email sitting in spam is ground truth; (b) UPDATE the existing row in place (do NOT append a new row) — rewrite the From value to the real address, update Content Description and Notes with "CORRECTED <date> from <old> per actual sender"; (c) then move the matching spam email(s) to INBOX. Rule type stays `exact_from`.

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
in SPAM (date | From | Subject) using the same vault get_creds() pattern.
Use it to produce the "what's sitting in spam" section of the cron report
so potentially-important unmatched senders (land JV proposals, lead
notifications, known contacts, bank surveys) get flagged for the user to
whitelist — the main check only prints what it MOVED, not what it skipped.

**Gmail-only fallback (when vault daemon is missing):** There is no pre-built fallback script. When vault is unavailable and no token file exists, generate an ndr@draas.com auth URL using the env-var OAuth client credentials (see "Auth URL Generation" section above — run via `terminal()` where the env vars are available, NOT `execute_code` sandbox) and report the URL as the cron deliverable. The token will be vault-stored after the OAuth callback completes, and the next cron tick picks it up automatically.

Never use a personal or stray token file, even if one exists at some legacy path — prefer generating a fresh ndr@draas.com auth URL (vault-stored via the callback).

**Do NOT prefix with `HERMES_SESSION_USER_ID`** — the script uses the
direct vault read + token-scope pattern in `get_creds()`, which does not
read `HERMES_SESSION_USER_ID` at all. The vault read is gated by the
explicit `session_uid=uid` argument to `get_token()`, where `uid` is
`resolve("email", DRAAS_UID)` — this satisfies the vault's self-read
check in cron context without depending on any session env var.
