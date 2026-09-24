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
  `ndr@draas.com → ndr-[REDACTED-TID]`, `psingh@draas.com → psingh-[REDACTED-TID]`.
- Gateway process exec environ has NO HERMES_SESSION_USER_ID (checked
  `/proc/<pid>/environ`), but **/proc environ only shows exec-time values, not
  runtime `os.environ[...] =` mutations** — pollution is invisible there.
- Agent access log showed the API client was `Python/3.11 aiohttp` from
  172.18.0.4 (programmatic pipe, NOT a browser) — so "what login is in my
  browser" is not the same question as "what email did the pipe forward".
- Concurrent Telegram session `20260806_055231_8c93d052` (user [REDACTED-TID]) was
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
for i in ['ndr@draas.com','psingh@draas.com','[REDACTED-TID]','[REDACTED-TID]']:
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

---

## 2026-09-15/16 — Open WebUI "Ranka Oasis Structuring" false "Prakash identity" (resolved)

**Symptom the user saw:** agent output in an Open WebUI chat said *"Session
identity has changed — this session is now under Prakash Singh's token"* /
*"Google Contacts for NDR's account is blocked from this session (it's under
Prakash's identity)"*, while contact lookups returned empty.

**What actually happened (evidence):**
- The session's real `HERMES_SESSION_USER_ID` was `ndr-7449813913` — proven by
  the tool error text (`User 'ndr-7449813913' has no gws_service configured`).
  The identity resolver never returned psingh: 3+ days of
  `API server identity resolved:` lines are all `ndr@draas.com → ndr-7449813913`
  (plus one `pebblyshark69@gmail.com`).
- The "Prakash" line was **agent hallucination**. The trigger was a
  `google-draas` People API scan returning `total contacts: 0` (NDR's work
  account People list is genuinely empty — his 4,248 contacts live in the
  "NDR DRAAS Google contacts" sheet / personal account). The agent invented
  "must be Prakash's token then".

**Root causes fixed (all deployed 2026-09-16):**
1. `tools/_user_registry.get_user_config()` hardcoded the `identities.telegram`
   bucket → OpenWebUI/SSO canonical ids (`ndr-7449813913`) returned `{}` →
   "no gws_service configured" → empty contacts. Fixed by 2-step lookup
   (canonical id first, then vault `resolve_any`) — commit `275983dec`.
2. The durable Pipe `hermes_agent_durable` built its `/v1/runs` call with only
   `Authorization` — it never forwarded `X-OpenWebUI-User-Email`, so pipe runs
   were anonymous. Now forwards the SSO email from `__user__`/`body["user"]`
   (`patches/open-webui/hermes_agent_durable_pipe.py`, v0.2.0).
3. The Pipe also used the **LLM-gateway** key (`lgw-…`, from
   `OPENAI_API_KEY="%(ENV_LLM_GATEWAY_API_KEY)s"`) against the Hermes API and
   always got **401**. Fixed by setting the pipe valves
   `hermes_base_url=http://hermes:8642/v1` + `hermes_api_key=<API_SERVER_KEY>`.
4. `api_server._handle_runs` (the `/v1/runs` handler) never called
   `user_identity(request)` and passed no `user_id` to `_create_agent` /
   `set_session_vars` → durable runs were anonymous even with the header. Now
   resolves identity and binds it.
5. **Cross-session leak (the real danger):** `tools/terminal_tool.py` only
   wrote `env.env["HERMES_SESSION_USER_ID"]` when the current identity was
   truthy. Terminal environments are **shared** (local backend collapses
   `task` to `default`), so a value left by a concurrent session (e.g. Bharat
   `8717455402`) leaked into an NDR run — reproduced live:
   `printenv HERMES_SESSION_USER_ID` → `8717455402` for an `ndr@draas.com`
   request. Fixed by ALWAYS (over)writing, clearing to `""` when the session
   has no identity (fail-closed). Also added an INFO
   `terminal identity inject:` line for auditing.
6. `gateway/platforms/identity_resolver.py`: resolution now logs at **INFO**
   (was DEBUG, invisible in prod), and the anonymous/no-header case logs
   explicitly.
7. Added a `[session identity]` preamble to the API-server system prompt
   (`api_server._with_identity_note`) so the model is told who it is and
   **cannot invent an identity when a tool fails**.

**Residual risk:** the shared terminal env (`task=default`) is still mutated
in place; two *concurrent* sessions issuing terminal commands could still race
on `env.env`. Proper fix = per-session terminal env keying or a per-call env
override in `BaseEnvironment.execute()`. Track separately.

**Audit rule:** on any "wrong identity" report, run
`docker logs hermes-hermes-1 | grep -aE "API server identity (resolved|:)"`
and `docker logs hermes-hermes-1 | grep -a "terminal identity inject"` — those
two lines now show, per request, exactly which identity was resolved and which
was injected into each terminal subprocess.
