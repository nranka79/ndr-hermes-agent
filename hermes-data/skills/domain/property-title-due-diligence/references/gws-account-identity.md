# GWS account-identity pitfall (incident 2026-08-06)

## What happened
User asked to upload a deck + images to "the tmp folder on my drive". The
upload script called `build_service('drive','v3', service_name='google-draas')`
and uploaded 14 files — which landed in **psingh@draas.com**'s Drive, not
ndr@draas.com's. The user was rightly alarmed (cross-user data exposure).

## Root cause chain
1. The request came through the **API server** platform (platform=api_server,
   session api-d5a37e621de6a660), not Telegram.
2. The API server resolves identity **per request**, not per session:
   `gateway/platforms/identity_resolver.py` reads the `X-OpenWebUI-User-Email`
   header on every call and looks it up in the vault registry
   (`user_identity(request)` → telegram id → `set_session_vars(user_id=...)`).
3. That resolved id becomes `HERMES_SESSION_USER_ID` for the turn; the
   **terminal tool injects it into every subprocess** (tools/terminal_tool.py,
   `env.env["HERMES_SESSION_USER_ID"] = _session_tid`).
4. At the upload moment the request resolved to Prakash (8502281203), so the
   subprocess ran with HERMES_SESSION_USER_ID=8502281203 → canonical_uid →
   `psingh-8502281203` → `get_token(uid, 'google-draas')` returned **Prakash's**
   OAuth token. Files went into his TMP folder
   (155SBzMDhM5pebj3wLz8o_9310ZsFwqh6).
5. The same session on a later turn resolved to 7449813913 (Nishant) — the
   identity **flipped between turns** of one conversation. My probe right
   after showed google-draas == ndr@draas.com, which is why the earlier claim
   "uploaded to your drive" looked plausible but was wrong.

## Why the token isn't pinned to an email
- `tools/gws_auth.py` `EMAIL_TO_SERVICE` maps MANY draas.com emails
  (ndr, psingh, rnr, vkdas, pm2.blr, sales1.blr) to the SAME vault key
  `google-draas`.
- The vault stores tokens per `(canonical_uid, service)`:
  `ndr-7449813913/google-draas` = ndr's token, `psingh-8502281203/google-draas`
  = psingh's token. `build_service('google-draas')` returns whichever user the
  SESSION resolves to — the service name does NOT pin the account.

## Hard rules going forward
1. **Before any Drive write** (upload/create/move/delete), verify the
   authenticated account:
   `svc.about().get(fields='user(emailAddress)').execute()` and compare to the
   intended owner email. Abort if mismatch.
2. Never claim "uploaded to <email>" without having checked `about()` — the
   script earlier picked the first working service (`['google-draas',
   'google-gmail']`) and reported success without checking ownership. That
   report was wrong.
3. For API-server sessions, be aware identity is per-request from the SSO
   header — the same session can act as different users on different turns.
   When the user says "my login is X", the request header may still say Y.
4. Cleanup path if a wrong-account upload happens: re-upload via the correct
   token, then delete the stray files from the wrong account (with user OK).

## Diagnostic recipe (how this was traced)
- Ground truth of ownership: Drive API `files().get(fileId, fields='id,name,createdTime,owners')`
  → owners list shows the REAL account.
- Session record: `/data/hermes/state.db` `sessions` (user_id can be None for
  API sessions) and `messages` (tool outputs are stored verbatim — grep the
  upload terminal output for `OK account:` / `UP <file>`).
- Vault: `tools.gws_vault_client.resolve(identity_type, value)`,
  `list_services(uid, session_uid=uid)`, `list_identities()` (admin).
- Logs: /data/hermes/logs/agent.log (session turns, tool completion sizes),
  gateway.log (inbound messages, sessions per user).
- Terminal env injection: tools/terminal_tool.py ~line 2322.
- Identity resolution: gateway/platforms/identity_resolver.py (header
  X-OpenWebUI-User-Email), api_server.py `user_identity(request)` per request.
- The header value itself is deliberately NOT logged (only remote/peer/UA),
  so you may not see the exact email — the token used is the proof.
