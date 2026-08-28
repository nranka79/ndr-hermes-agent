# gws_auth Compatibility — Vault vs Env-Var Credential Paths

## Two Paths for Credentials

| Source | Mechanism | Availability |
|--------|-----------|-------------|
| **Vault daemon** | Unix socket `/run/gws-vault/vault.sock` | `GWS_VAULT_SOCKET` must be set explicitly in the calling process |
| **Env-var JSON files** | `/data/hermes/oauth-*.json` written by `setup_oauth_credentials.py` at container startup | Available as fallback when vault is unreachable |

## The vault socket env var trap

`GWS_VAULT_SOCKET` is **NOT set** in the Hermes process environment by default. It is not inherited into `terminal()` subprocesses and is absent from the `execute_code()` sandbox.

**When it works:**
- `gws_skill_bridge.call()` from inside `execute_code()` — the sandbox does get the socket passed through (but during this session the env var itself was unset, so use has been unreliable)
- Explicitly setting it before any Python invocation: `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock python3 ...`

**When it fails:**
- `gws_auth.build_service()` or `has_token()` from `execute_code()` without setting the env var → `VaultError: GWS_VAULT_SOCKET is not set`
- `terminal("python3 -c '...'")` — subprocess doesn't inherit the env var

**Fix pattern for terminal():**
```bash
GWS_VAULT_SOCKET=/run/gws-vault/vault.sock python3 /tmp/my_script.py
```

**Fix pattern for execute_code():**
```python
import os
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'

# Then import and use gws_skill_bridge or gws_auth
from tools.gws_skill_bridge import call
```

## Env-var credential files (secondary path)

The container startup script `/opt/hermes/setup_oauth_credentials.py` reads Docker environment variables and writes JSON credential files to `/data/hermes/`. These are used by `tools.gws_auth.load_credentials()` as a fallback when the vault is unreachable.

The `.env` file at `/data/hermes/.env` maps accounts to credential file paths:
```
GOOGLE_WORKSPACE_CLI_DRAAS_CREDENTIALS=/data/hermes/oauth-draas.json
GOOGLE_WORKSPACE_CLI_PSINGH_CREDENTIALS=/data/hermes/oauth-psingh.json
GOOGLE_WORKSPACE_CLI_GMAIL_CREDENTIALS=/data/hermes/oauth-gmail.json
GOOGLE_WORKSPACE_CLI_AHFL_CREDENTIALS=/data/hermes/oauth-ahfl.json
```

## Which path takes precedence?

`build_service()` / `load_credentials()` tries:
1. Vault daemon first (if `GWS_VAULT_SOCKET` is set and reachable)
2. Falls back to JSON credential files

So if both are working, the vault path is used. The JSON files are the **durable backup** that survives container rebuilds.

## EMAIL_TO_SERVICE mapping

```python
from tools.gws_auth import EMAIL_TO_SERVICE
# {'ndr@draas.com': 'google-draas', 'psingh@draas.com': 'google-draas',
#  'rnr@draas.com': 'google-draas', 'vkdas@draas.com': 'google-draas',
#  'pm2.blr@draas.com': 'google-draas', 'sales1.blr@draas.com': 'google-draas',
#  'ndr@ahfl.in': 'google-ahfl', 'nishantranka@gmail.com': 'google-gmail'}
```

All @draas.com emails map to the **same** `google-draas` service key. But the token stored under that key belongs to a **single user** — it does not grant cross-account access to other @draas.com accounts.

## Adding a new @draas.com user to the credential system

See `google-workspace-api` skill → `references/env-var-credential-setup.md` for the full workflow. High-level steps:
1. Add entry to `setup_oauth_credentials.py` ACCOUNTS dict + account_env_keys dict
2. Add user as test user in Google Cloud OAuth consent screen
3. Run OAuth flow via `get_auth_url()` (from terminal, not execute_code)
4. Set env vars in Docker host and redeploy
