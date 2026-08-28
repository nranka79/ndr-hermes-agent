---
name: employment-generator
description: "Karnataka/TN economic activity tracker — employment announcements, infrastructure projects, policy & approvals. 3-tab Google Sheet, 13 RSS queries, strict 48-hour window."
---

# Employment Generator Tracker — Subject Profile

Tracks economic activity across Karnataka, Tamil Nadu (Krishnagiri, Chennai periphery), and Andhra Pradesh border (Anantapur).

## Quick Reference

| Property | Value |
|----------|-------|
| Sheet ID | `1lLAfh8d9wR84O_bbITo2lQtvJ3dmYw1QHTfLIDhbL2c` |
| Sheet Owner | nishantranka@gmail.com (personal) |
| Required service_name | `google-gmail` |
| Cron User | Nishant (telegram_id=[REDACTED-TID]) |
| Cron Schedule | 30 9 * * * (daily 9:30 AM IST) |
| Cron Entry Point | `scripts/empgen_runner.py` |

## Tabs & Schema

| Tab | Columns (A-I or A-H) | Dedup Key |
|-----|----------------------|-----------|
| **Employment Announcements** | Date, Company/Org, Location, Category, Jobs, Investment, Link, Headline, Notes | Company + Location + Category |
| **Infrastructure** | Date, Project Type, Promoter/Contractor, Location, Investment, Status, Link, Headline, Notes | Project Type + Location + Promoter |
| **Policy & Approvals** | Date, Title, Issuing Body, Geography, Type, Link, Headline, Notes | Title + Issuing Body + Month-Year |

## RSS Queries (13 total)

### Employment (5 queries)
- New factories / manufacturing units / plants in Karnataka
- GCCs / global capability centres / back office in Bangalore/Chennai
- New offices / campuses / facilities in Karnataka/TN
- IT parks / tech parks / software centres in Bangalore/Chennai
- Investment announcements / new industry in Karnataka/TN

### Infrastructure (4 queries)
- New roads / highways awarded in Karnataka/TN
- Metro extensions / suburban rail in Bangalore/Chennai
- Freight corridors / logistics parks / industrial corridors in Karnataka
- Infrastructure projects awarded / approved in Karnataka

### Policy (4 queries)
- Industrial policy in Karnataka/TN
- Environmental approvals / pollution board consent in Karnataka
- KIADB / TIDCO / Guidance TN land allotments
- Land acquisition for industry / SEZ notifications in Karnataka

Full query strings and exclusion patterns in `references/employment-generator-article-filtering.md`.

## Filtering Pipeline

1. **48-hour window** — strict cutoff; older items discarded
2. **Exclusion check** — skip political, negative, crime, weather, religion, education, health articles (see `references/employment-generator-article-filtering.md`)
3. **Hiring drive filter** — skip job fairs, recruitment drives, walk-in interviews (not new employment generation)
4. **Positive indicator check** — must contain category-specific keywords
5. **Geography gate** — must mention a location from `references/employment-generator-geographies.md`

## Geography Coverage

See `references/employment-generator-geographies.md` for full location list covering:
- **North Bangalore Peri-Urban**: Devanahalli, Doddaballapur, Kolar, Tumkur, Nelamangala, Yelahanka
- **South/East Bangalore**: Whitefield, Electronic City, Sarjapur, Jigani, Anekal, Attibele
- **Beyond Bangalore**: Mysore, Mangalore, Hubli, Dharwad, Belgaum, Hassan
- **TN — Krishnagiri District**: Hosur, Shoolagiri, Krishnagiri, Berigai
- **TN — Chennai Periphery**: Sriperumbudur, Oragadam, Maraimalai Nagar, Chengalpattu, Kancheepuram
- **AP Border**: Hindupur, Lepakshi, Puttaparthi (Anantapur district)

## Running

### Recommended (empgen_runner wrapper — handles auth patch):
```bash
cd /opt/hermes && HERMES_SESSION_USER_ID=[REDACTED-TID] \
    /opt/hermes/.venv/bin/python3 \
    /data/hermes/skills/news-tracker/scripts/empgen_runner.py
```

### Runtime — the runner is slow; use background execution

The runner fetches 13 RSS queries serially, each `curl` capped at 30s (worst case ~390s of fetching alone, plus sheet reads/writes). A foreground `terminal()` call with a 420s timeout can time out mid-run (observed 2026-08-02). Run it as a background process with unbuffered output to a log, then poll:

```bash
cd /opt/hermes && HERMES_SESSION_USER_ID=[REDACTED-TID] \
    /opt/hermes/.venv/bin/python3 -u /data/hermes/skills/news-tracker/scripts/empgen_runner.py \
    > /tmp/empgen_run.log 2>&1
```

Monitor via `process(action='poll')` and read `/tmp/empgen_run.log` with `read_file`. Typical full-run time: ~3–8 minutes depending on RSS latency. A run that finds nothing prints `No new employment generation announcements in the last 48 hours.` — the cron wrapper should then reply exactly `[SILENT]` (the cron delivery instruction supersedes the "send a Telegram summary" line in SKILL.md).

### Direct (only if wrapper is unavailable):
The core script at `scripts/employment-generator.py` has a broken `build_service` call (passes `telegram_id` as positional arg). Use the wrapper above for all cron runs.

## Critical: Cron User Context

**The Employment Generator Tracker cron MUST run under Nishant's telegram ID ([REDACTED-TID]).** Only Nishant has the `google-gmail` OAuth token with access to the sheet (nishantranka@gmail.com personal account). Running under any other user's session fails with:

```
ERROR: No google-gmail token for user <other-user-id>. Authorize first.
```

**Why this happens:** The cron framework runs under the session user that created/owns the cron job. If the cron is set up under a different user (e.g., Anbarasan / pm2.blr), `HERMES_SESSION_USER_ID` is set to that user's ID, but only Nishant's Google account has the `google-gmail` service registered with sheet access.

**Fix:** The cron config must store Nishant's telegram ID ([REDACTED-TID]) as the `telegram_id` / `user_id` for the job schedule entry. Alternatively, override it at runtime:
```bash
HERMES_SESSION_USER_ID=[REDACTED-TID] cd /opt/hermes && \
    /opt/hermes/.venv/bin/python3 \
    /data/hermes/skills/news-tracker/scripts/empgen_runner.py
```

**Verification:**
```bash
echo "HERMES_SESSION_USER_ID=${HERMES_SESSION_USER_ID:-UNSET}"
# users.json paths are NOT reliable (/data/hermes/users.json is an empty dir;
# /opt/hermes/hermes-data/users.json does not exist) — use the vault instead:
cd /opt/hermes && /opt/hermes/.venv/bin/python3 -c "
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_vault_client import list_services, resolve
uid = resolve('telegram', '[REDACTED-TID]')   # -> 'ndr-[REDACTED-TID]'
print(uid, list_services(uid))
# Confirm 'google-gmail' is present — if not, run under the right user or re-auth
"
```

**Pitfall — cron env var user may lack Google tokens entirely.** A session may set `HERMES_SESSION_USER_ID` to a user with `list_services() == []` (e.g. `psingh-[REDACTED-TID]` on 2026-07-31). Run the vault check above BEFORE running the runner; if the env user has no `google-gmail`, override with `HERMES_SESSION_USER_ID=[REDACTED-TID]`.

## Support File Index

| File | Purpose |
|------|---------|
| `references/employment-generator-article-filtering.md` | Exclusion/inclusion regex patterns |
| `references/employment-generator-geographies.md` | Full geography list and tagging rules |
| `references/employment-generator-dedup-notes.md` | Dedup keys per sheet, source priority, traps |
| `references/employment-generator-rss-behavior.md` | RSS age patterns, pubDate parsing, XML gotchas |
| `references/employment-generator-sheets-setup.md` | Spreadsheet creation, tab setup, Drive sharing |
| `scripts/empgen_runner.py` | Recommended cron entry point |
| `scripts/employment-generator.py` | Core logic (do not edit directly) |

## Subject-Specific Pitfalls

### Empgen runner requires Nishant's telegram ID
The `empgen_runner.py` wrapper patches `build_service` to use `service_name='google-gmail'`. This only works for Nishant's account. Running under any other user → `No google-gmail token` error.

### SHEET_ID is patched by the wrapper
The underlying `employment-generator.py` has SHEET_ID hardcoded to `10LbBakverJ3GHJYz7ZgvzuSnemAWqjxUpGDUVTVr3ks` (an older/incorrect ID). The `empgen_runner.py` patches it to `1lLAfh8d9wR84O_bbITo2lQtvJ3dmYw1QHTfLIDhbL2c`. Always use the wrapper.

### The email in users.json may differ from expected
`ndr@draas.com` (Nishant) has telegram_id `[REDACTED-TID]`. The vault uid format is `<draas-user-id>-<telegram-id>` — e.g., `ndr-[REDACTED-TID]`. Use `list_services('ndr-[REDACTED-TID]')` to check available services.

### First-time authorization / vault has no Google tokens at all

The empgen_runner can also fail at `build_service` because **no Google OAuth token has ever been stored** in the vault for this user. This is a different failure mode from `invalid_grant` (expired token) — it means the vault has no `google-gmail` service, and `list_services` returns only non-Google entries (e.g. `['vocab']`).

**Diagnosis — distinguish "never authorized" from "expired":**

```python
from tools.gws_vault_client import list_services
services = list_services('ndr-[REDACTED-TID]')
# If this returns no google-* services, the user has never authorized Google
print(services)  # e.g. ['vocab'] — only non-Google services
```

The vault may also print a warning like:
```
canonical_uid: vault has no identity mapping for 'ndr-[REDACTED-TID]' -- using raw id as fallback key.
```

This means the vault's identity store doesn't have the mapping yet — it falls back to the raw uid. This is harmless for self-read ops but confirms the user hasn't completed any Google OAuth flow yet.

**Recovery is the same URL flow, but the root cause is different — it's not a refresh error, it's a missing token:**

1. Verify the user's identity is resolvable in the vault:
   ```python
   from tools.gws_vault_client import resolve
   uid = resolve('telegram', '[REDACTED-TID]')      # should return 'ndr-[REDACTED-TID]'
   uid2 = resolve('email', 'nishantranka@gmail.com')  # returns None if no Google account linked
   ```
   If `resolve` returns the expected uid for `telegram` but `nishantranka@gmail.com` returns `None`, the personal Google account has never been linked. This is expected for a fresh vault setup.

2. Generate the auth URL — `get_auth_url()` takes NO arguments (verified 2026-08-16; passing `login_hint=` raises `TypeError`). The login hint for nishantranka@gmail.com is auto-derived from the session user's registered email, so the URL already pre-fills the personal account:
   ```python
   from tools.gws_auth import get_auth_url
   url = get_auth_url()   # NO arguments — login_hint/telegram_id both raise TypeError
   # NOTE: identity is derived from session context
   # (HERMES_SESSION_USER_ID env var in cron / Hermes session in interactive mode)
   ```
   The OAuth callback handler automatically links the email to the user's vault identity and stores the token under `google-gmail`.

3. After the user authorizes via the URL, `list_services` should show `['google-gmail', ...]` and the empgen_runner will proceed past `build_service` on the next run.

**Key difference from `invalid_grant`:** There is no data to preserve (the auth failure happens before any RSS fetch), and no refresh-token rotation is needed — this is a first-time setup, not a recovery.

### `KeyError: 'geography'` — Infrastructure exclusion-override path (fixed 2026-08-25)

The core script's `passes_filters()` has an Infrastructure-specific exclusion-override: if an article matches `EXCLUSION_RE` but has a strong Infrastructure positive indicator (and is not a scrap/cancel story), it returns `True` **before** the geography gate — so `article["geography"]` is never set. `rss_to_infrastructure_row()` then raises `KeyError: 'geography'` inside `dedup_vs_existing()`, killing the whole run mid-way (Employment may already be processed; Policy never runs).

**Fix (lives in `empgen_runner.py`, two runtime patches — core script stays untouched):**
1. The override path now extracts & sets geography before returning: `article["geography"] = extract_geography(text)`
2. All 3 row functions use the defensive `article.get("geography", "")` (the `.replace(', article["geography"], ', ...)` patch — it does NOT touch the `article["geography"] = geo` assignment in `passes_filters`)

**Caveat — cancel-guard gap:** the override's scrap/cancel guard is `\b(scrap|cancel|scrapped)\b`, which does NOT match "cancelling"/"cancelled". A headline like "TN govt to set up new airport near Chennai after cancelling Parandur Airport project" passes. That is acceptable — it is a new-project announcement (the tracker's target) — but be aware a pure cancellation story could sneak through if it also carries a positive infra keyword; check the Headline column if sceptical.

## Token Recovery — `invalid_grant` on `google-gmail`

When the `google-gmail` OAuth token expires or is revoked, the empgen_runner fails with:

```
ERROR: ('invalid_grant: Token has been expired or revoked.', ...)
```

This means Google rejected the refresh token entirely. Common causes: Nishant revoked access from Google Account settings, a password change invalidated tokens, or the token was unused for 6+ months.

### Recovery procedure

1. **Generate a re-auth URL** — `get_auth_url()` takes NO arguments (verified 2026-08-16; `get_auth_url(login_hint=...)` raises `TypeError`). The login hint is auto-derived from the session user's registered email, so the URL already pre-fills nishantranka@gmail.com for Nishant:
   ```python
   from tools.gws_auth import get_auth_url
   url = get_auth_url()   # NO arguments — identity from HERMES_SESSION_USER_ID env var in cron
   ```
   - `get_auth_url()` does NOT accept `service_name` — the callback handler auto-detects which Google account the user signs in with and stores the token under the correct vault key
   - Login hint is derived from the session user's registered email via the vault registry (`tools._user_registry.get_user_config(tid)['email']`), so the personal account is pre-filled automatically — no manual hint needed

2. **Preserve any found-but-unwritten data**: If the auth fails AFTER RSS fetch (before sheet write), save candidate entries to `/opt/data/employment-generator-pending-YYYY-MM-DD.txt`. Include: company, location, category, jobs, link, headline. This session confirmed the auth failure happens before RSS fetch (at `build_service` call), so data preservation is only needed if the script structure changes.

3. **Report the auth URL in the Telegram summary** alongside the error. The cron job should not silently swallow the failure — the user must know they need to re-authorize.

4. **After re-authorization** via the link, the next daily run (30 9 * * *) will pick up any fresh announcements within the new 48-hour window.

### What scopes are covered

The standard `get_auth_url(login_hint=...)` grants all Hermes GWS scopes (Gmail, Calendar, Drive, Contacts, Tasks, Docs, Sheets, Photos, YouTube). No need to request sheets-specific scopes separately — the full scope bundle is always issued. Identity comes from session context (HERMES_SESSION_USER_ID or active Hermes session), never from a passed parameter.

### If the same token expires repeatedly

Set up a monthly reminder for Nishant to visit the auth URL and refresh the OAuth grant. Google invalidates refresh tokens on tokens unused for 6+ months, but the personal account (nishantranka@gmail.com) can also be affected by consumer-level token policies.
