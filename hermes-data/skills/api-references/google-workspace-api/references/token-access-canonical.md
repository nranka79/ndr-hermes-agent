# Google Workspace Token Access — Canonical Reference

**This document supersedes every older token/auth troubleshooting note.**
Anything you find elsewhere (or remember) about token files, vault bypasses,
HTTP proxies, symlinks, or telegram-id overrides is obsolete — do not
resurrect it, do not re-document it.

## The rules

1. **Tokens live ONLY in the gws-vault daemon** (Unix socket). There are NO
   token files on disk anywhere. `the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)` does not exist and has not
   existed since the vault migration (June 2026). Never search for one.
2. **Identity is ALWAYS the current session user**, resolved inside
   `tools/gws_auth.py` from session context. Never pass, hardcode, or guess
   a telegram id / user id — `build_service()` ignores overrides, and
   `send_oauth_url` takes no id parameter at all.
3. **Preferred call path:** `tools.gws_skill_bridge.call(operation,
   service_name=..., ...)`. Fallback for operations the bridge doesn't wrap:
   `tools.gws_auth.build_service(api, version, service_name=...)`.
4. **`service_name` selects the Google ACCOUNT** (`google-draas`,
   `google-ahfl`, `google-gmail`), never the user. Resolve it with the
   `gws_resolve_account` tool — don't guess, and never pass an email as
   `service_name`.
5. **No token / `needs_auth`** means the session user genuinely hasn't
   authorized that account: call the `send_oauth_url` tool (optionally with
   `login_hint=`). Never construct an OAuth URL yourself.
6. **The `execute_code` sandbox lacks the GWS auth stub.** In the sandbox,
   `tools.gws_auth.build_service(...)` fails with
   `ImportError: cannot import name 'gws_fetch_token' from 'hermes_tools'`.
   The RELIABLE route — especially in cron / no-oauth-toolset contexts — is
   `terminal()` running the Hermes venv python with the vault socket and
   session identity set explicitly:
   ```bash
   cd /opt/hermes && HERMES_SESSION_USER_ID=<tid> \
     GWS_VAULT_SOCKET=/run/gws-vault/vault.sock \
     /opt/hermes/.venv/bin/python3 /path/script.py
   ```
   `build_service('gmail','v1',service_name='google-draas')` then authenticates
   normally. Always pre-flight with `getProfile` to confirm the right mailbox.
   (Verified working 2026-08-20 from a cron job; the earlier note claiming the
   vault socket is "not available" in `terminal()`/subprocess is stale — the
   socket at `/run/gws-vault/vault.sock` IS reachable there when the env var is set.)
7. **If something still fails, stop and report the exact error.** Do not
   invent workarounds. A genuinely unreachable vault is an infrastructure
   problem for the admin, not something to code around.
