# GWS Account Identity Mixup — Forensics Path (Aug 2026 psingh incident)

When a GWS operation (Drive upload, Sheets write, Gmail draft) lands in the WRONG
user's account (e.g. files appeared in psingh@draas.com instead of ndr@draas.com),
run this forensics chain instead of guessing. The vault NEVER "picks" a user —
it returns the token for the `user_id` it was asked for. The bug is always
upstream of the vault.

## The identity chain (read in this order)

1. **API server** (`gateway/platforms/api_server.py`): per-request identity from
   `X-OpenWebUI-User-Email` header via `identity_resolver.user_identity(request)`.
   No header → anonymous → user_id="".
2. `_run_agent` → `set_session_vars(user_id=...)` → ContextVar
   `HERMES_SESSION_USER_ID` (task-local, gateway/session_context.py).
3. **terminal tool** (`tools/terminal_tool.py` ~line 2318): injects
   `env.env["HERMES_SESSION_USER_ID"] = get_gws_identity_env()` ONLY if truthy.
   If empty, it does NOT touch the var — a polluted/persistent env dict leaks.
4. **gws_auth** (`tools/gws_auth.py`): `_current_telegram_id()` → `canonical_uid()`
   → `vault.get_token(uid, service, session_uid=uid)`.
5. **vault server**: strictly user-scoped; `session_uid` must equal `user_id`
   (SO_PEERCRED enforcement) — so the token returned belongs to whoever the
   *caller* claimed to be.

Key property: identity is **per-request**, not per-session. state.db shows
`user_id=None` on API session rows — the session record is anonymous; only the
per-turn header decides whose token loads. A probe run later in the same session
can resolve to a DIFFERENT user than the turn that did the damage.

## Decisive evidence in the psingh incident

- Upload script had `os.environ.setdefault('HERMES_SESSION_USER_ID',
  os.environ.get('HERMES_SESSION_USER_ID','ndr'))` → if the var were absent the
  fallback resolves to **ndr** → files would be in NDR's Drive. They were in
  psingh's → the subprocess MUST have carried a psingh-resolving value.
- Vault resolve is clean and unambiguous (no collision):
  `ndr@draas.com → ndr-7449813913`, `psingh@draas.com → psingh-8502281203`.
- Gateway process exec environ has NO HERMES_SESSION_USER_ID (checked
  `/proc/<pid>/environ`), but **/proc environ only shows exec-time values, not
  runtime `os.environ[...] =` mutations** — pollution is invisible there.
- Agent access log showed the API client was `Python/3.11 aiohttp` from
  172.18.0.4 (programmatic pipe, NOT a browser) — so "what login is in my
  browser" is not the same question as "what email did the pipe forward".
- Concurrent Telegram session `20260806_055231_8c93d052` (user 8502281203) was
  mid-turn at 07:10, ~4 min before the upload ran — only other live identity.

## Four hypotheses (ranked)

- **H1 — header named Prakash (client-side, strongest).** The pipe/Open WebUI
  conversation was bound to psingh at that moment; everything downstream worked
  as designed. Test: INFO-log resolved user_id per request; send one message.
- **H2 — anonymous request inherited polluted process os.environ.** If header
  absent, terminal tool skips injection and subprocess inherits gateway
  os.environ. This codebase has a documented history of scripts doing
  `os.environ.setdefault('HERMES_SESSION_USER_ID', '<hardcoded id>')`
  (see scripts/hetzner_id_cleanup.sh — cleanup exists because empgen_runner.py /
  ai-job-loss-tracker.py did exactly this). Cron scheduler also mutates and
  restores os.environ (cron/scheduler.py `_job_profile_context`).
- **H3 — concurrent-session context bleed.** Prakash was the only other user
  live in the same gateway process at that moment; thread-pool reuse without
  contextvars.copy_context() would pick the one live identity. Explains "why
  HIS identity vs any of the multiple vault identities".
- **H4 — conversation/session-key binding.** Open WebUI pipe forwards the
  conversation OWNER's email, not the viewer's; chat created under psingh stays
  psingh.

## Fixes / prevention (per hypothesis)

- H1/H4: bind the Open WebUI conversation to ndr; verify which account owns it.
- H2: terminal_tool must always OVERWRITE/CLEAR HERMES_SESSION_USER_ID in
  subprocess env when session value is empty; audit cron/script os.environ writes.
- All: add INFO-level `user_identity` logging to api_server (currently DEBUG
  only, invisible in agent.log at INFO config) — the resolved email is
  otherwise un-auditable.
- Always `svc.about().get(fields='user(emailAddress)')` before Drive writes and
  verify it matches the intended owner — this single check catches the whole
  class instantly. See gws-account-identity.md.

## Reusable probe commands

```bash
# vault resolve test (needs socket env):
GWS_VAULT_SOCKET=/run/gws-vault/vault.sock GWS_VAULT_SECRET=<secret> \
  /opt/hermes/.venv/bin/python -c "
import sys; sys.path.insert(0,'/opt/hermes')
from tools import gws_vault_client as vault
for i in ['ndr@draas.com','psingh@draas.com','7449813913','8502281203']:
    print(i, '->', vault.resolve('email' if '@' in i else 'telegram', i))"

# who owns the uploaded files (Drive side):
#   files().get(fileId=..., fields='owners(emailAddress)') on both tokens

# find the exact tool call that did the damage:
#   sqlite3 /data/hermes/state.db "SELECT id,role,tool_name,substr(content,1,800),timestamp
#     FROM messages WHERE session_id='<sid>' AND (content LIKE '%HERMES_SESSION_USER_ID%' OR ...)"
```

## Sandbox note

`execute_code` sandbox has NO GWS_VAULT_SOCKET — vault probes must run via
terminal with the socket env, not in the sandbox.
