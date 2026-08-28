# xAI OAuth on Headless Docker Container (Hetzner)

Recorded 2026-07-10 during initial xAI OAuth setup.

## Setup Context

- Host: Hetzner dedicated server
- Hermes running inside a Docker container
- No Docker socket access from within the container (`docker ps` → "Cannot connect to daemon")
- No browser access to server's `127.0.0.1` from user's machine
- `hermes auth add xai-oauth --manual-paste` used but stdin interaction broken in non-interactive terminal

## Error: unknown flag --manual-paste

When running via `docker compose exec`:
```
docker compose exec hermes hermes auth add xai-oauth --manual-paste
→ unknown flag: --manual-paste
```

**Cause:** `docker compose exec` intercepts the flag before passing the command to the container.

**Fix 1:** Wrap in `sh -c`:
```
docker compose exec hermes sh -c "hermes auth add xai-oauth --manual-paste"
```

**Fix 2 (actual):** We were already inside the container (hostname `47ee4f9db239`). Run directly:
```
/opt/hermes/bin/hermes auth add xai-oauth --manual-paste
```

## Error: docker compose not available

```
docker: 'compose' is not a docker command.
```

**Cause:** Docker Compose V2 plugin not installed on this host.

**Fix:** Check if already inside container via `cat /etc/hostname`.

## Error: PKCE verification failed

```
xAI token exchange failed (HTTP 400). Response: {"error":"invalid_grant","error_description":"PKCE verification failed"}
```

**Root cause:** The `--manual-paste` flow generates a fresh PKCE code_verifier + code_challenge pair on **every** process invocation. Piping the code from a prior run's URL into a new CLI process causes a PKCE mismatch.

**Solution:** Two-phase Python script (see SKILL.md for full code):

1. `xai_auth_step1.py` — generates URL and saves PKCE state to `/tmp/xai_oauth_state.json`
2. User opens URL, authorizes, gets code
3. `xai_auth_step2.py '<code>'` — reads saved state, exchanges code for tokens

## Successful Exchange Output

```
✓ Token exchange successful!
  access_token:  eyJ0eXAiOiJhdCtqd3QiLCJhbGciOiJFUzI1NiIsImtpZCI6Im...
  refresh_token: OR-VwFg61NfbQZQ8UDmi07QJgtijaCP_8pD6PEEJlkL2PrE32L
✓ Saved to auth store.
✓ Set model.provider = xai-oauth in /data/hermes/config.yaml
```

## Key Functions Used

From `/opt/hermes/hermes_cli/auth.py`:

| Function | Purpose |
|----------|---------|
| `_xai_oauth_discovery()` | Fetches OIDC endpoints from `auth.x.ai/.well-known/openid-configuration` |
| `_oauth_pkce_code_verifier()` | Generates 128-char base64url PKCE verifier |
| `_oauth_pkce_code_challenge(v)` | SHA-256 hash → base64url challenge |
| `_xai_oauth_build_authorize_url(...)` | Constructs the full authorize URL with params |
| `_xai_oauth_exchange_code_for_tokens(...)` | POSTs code + verifier + challenge to token endpoint |
| `_save_xai_oauth_tokens(tokens, ...)` | Persists to auth store (~/.hermes/auth.json) |
