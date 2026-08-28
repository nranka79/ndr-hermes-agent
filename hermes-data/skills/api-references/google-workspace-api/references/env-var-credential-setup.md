# Env-Var OAuth Credential Setup

On this Hermes instance, Google Workspace OAuth credentials flow through **two complementary paths**:

| Path | Mechanism | Upstream source |
|------|-----------|----------------|
| **Primary: gws-vault daemon** | Unix socket at `/run/gws-vault/vault.sock` | Tokens stored at runtime; accessible via `gws_skill_bridge.call()` or `gws_auth.build_service()` with `GWS_VAULT_SOCKET` set |
| **Secondary: env-var → JSON file** | Container-startup script writes JSON credential files | Docker host environment variables (`docker-compose.yml` / `.env`) |

The secondary path is what makes tokens **survive container rebuilds** — the vault's in-memory store is ephemeral. Both paths must stay in sync: the env-var JSON files are the durable source of truth, and the vault is the live-access layer.

## How it works (secondary path)

1. The Docker host (Hetzner) has environment variables set in `docker-compose.yml` or its `.env`:
   - `DRAAS_OAUTH_REFRESH_TOKEN`, `DRAAS_OAUTH_CLIENT_ID`, `DRAAS_OAUTH_CLIENT_SECRET` → ndr@draas.com
   - `GMAIL_OAUTH_REFRESH_TOKEN`, `GMAIL_OAUTH_CLIENT_ID`, `GMAIL_OAUTH_CLIENT_SECRET` → nishantranka@gmail.com  
   - `AHFL_OAUTH_REFRESH_TOKEN`, `AHFL_OAUTH_CLIENT_ID`, `AHFL_OAUTH_CLIENT_SECRET` → ndr@ahfl.in
   - `PSINGH_OAUTH_REFRESH_TOKEN`, `PSINGH_OAUTH_CLIENT_ID`, `PSINGH_OAUTH_CLIENT_SECRET` → psingh@draas.com

2. At container startup, `/opt/hermes/setup_oauth_credentials.py` runs and:
   - Reads the env vars for each known account
   - Writes a JSON credential file per account (e.g. `/data/hermes/oauth-draas.json`)
   - Sets restrictive permissions (`0o600`)
   - Writes a `.env` file at `/data/hermes/.env` with `GOOGLE_WORKSPACE_CLI_*_CREDENTIALS` paths

3. `tools.gws_auth.py` reads these JSON files when `build_service()` is called as a fallback.

## How it works (primary path — vault daemon)

The vault daemon runs as a persistent Unix socket service at `/run/gws-vault/vault.sock`. Tokens are stored in its runtime store and accessed via JSON-RPC:

```python
import os
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'

from tools.gws_skill_bridge import call
result = call('gmail_search', service_name='google-draas', query='', max=5)
```

The vault enforces session-user matching via `SO_PEERCRED` on the Unix socket. When calling from `terminal()` (where `HERMES_SESSION_USER_ID` may be stale or unset), always prefix with `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock`:

```bash
GWS_VAULT_SOCKET=/run/gws-vault/vault.sock python3 -c "
import sys; sys.path.insert(0, '/opt/hermes');
from tools.gws_auth import build_service;
svc = build_service('gmail', 'v1', service_name='google-draas');
print(svc.users().getProfile(userId='me').execute())
"
```

**⚠️ The `GWS_VAULT_SOCKET` env var is NOT set by default** — not in `execute_code()` sandbox, not in `terminal()` subprocesses. You must set it explicitly every time: `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock`. If you forget, you'll get `VaultError: GWS_VAULT_SOCKET is not set`.

**Important — each token is per-user, not per-domain:** The vault stores one OAuth token per `service_name` per user. The `google-draas` service key holds the token for whichever @draas.com email the user authorized. It does NOT provide cross-account access to all @draas.com accounts. For example, if Prakash (psingh@draas.com) authorizes the google-draas service, his token only works for his account — attempting to access ndr@draas.com's data returns `"Delegation denied for psingh@draas.com"`.

## Adding a new user (e.g. psingh@draas.com)

This requires 4 steps:

### 1. Update `setup_oauth_credentials.py`

Add a new entry to the `ACCOUNTS` dict at the top of `/opt/hermes/setup_oauth_credentials.py`:

```python
"psingh@draas.com": {
    "refresh_token_env": "PSINGH_OAUTH_REFRESH_TOKEN",
    "client_id_env": "PSINGH_OAUTH_CLIENT_ID",
    "client_secret_env": "PSINGH_OAUTH_CLIENT_SECRET",
    "file_path": "/data/hermes/oauth-psingh.json"
}
```

Also add the env key mapping in the `account_env_keys` dict (around line 141):
```python
"psingh@draas.com": "GOOGLE_WORKSPACE_CLI_PSINGH_CREDENTIALS",
```

### 2. Add the user to the Google Cloud OAuth consent screen

The Google Cloud project that owns the OAuth client ID (used for ndr@draas.com) needs the new email added as a **test user** under **APIs & Services → OAuth consent screen → Test users**.

### 3. Run the OAuth flow to get a refresh token

Use `tools.gws_auth.get_auth_url()` via `terminal()` (the env vars `HERMES_OAUTH_CLIENT_ID` and `HERMES_OAUTH_CLIENT_SECRET` are available there but NOT in `execute_code()` sandbox):

```python
# ✅ Works from terminal() — env vars are present
# ❌ Fails from execute_code() — env vars are absent

import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import get_auth_url
url = get_auth_url('psingh@draas.com')
print(url)
```

**What happens next:**
- The URL points to Google's OAuth consent screen with `login_hint` pre-filled
- After the user authorizes, Google redirects to `https://transcribe.ahfl.in/gws/auth/callback?code=...&state=...`
- The callback server at transcribe.ahfl.in should catch the code and store the token
- If the callback server is down or returns an error, ask the user to paste the redirect URL they land on — extract the `code=` parameter from it and exchange it manually

### 4. Set env vars in Docker host + redeploy

Add to the Hetzner host's `.env` / `docker-compose.yml`:
```
PSINGH_OAUTH_REFRESH_TOKEN=...
PSINGH_OAUTH_CLIENT_ID=...
PSINGH_OAUTH_CLIENT_SECRET=...
```

Then redeploy the container. The startup script picks up the new vars and creates the credential file.

**Step 1 (the setup_oauth_credentials.py update) is the durable fix** — it ensures the account entry survives container rebuilds. Steps 2-4 populate the actual tokens.

## Checking if a token already exists in the vault

```bash
GWS_VAULT_SOCKET=/run/gws-vault/vault.sock python3 -c "
import sys; sys.path.insert(0, '/opt/hermes');
from tools.gws_auth import has_token, EMAIL_TO_SERVICE;
svc = EMAIL_TO_SERVICE.get('psingh@draas.com', 'google-draas');
print(f'{svc}: has_token={has_token(svc)}');
"
```

## Verifying which user a token actually belongs to

The vault can report `has_token: true` but the token may belong to a different Google account than expected. Use the Gmail profile API to verify:

```python
GWS_VAULT_SOCKET=/run/gws-vault/vault.sock python3 -c "
import sys; sys.path.insert(0, '/opt/hermes');
from tools.gws_auth import build_service;

svc = build_service('gmail', 'v1', service_name='google-draas');

# Method 1: userId='me' returns the token's actual owner
me = svc.users().getProfile(userId='me').execute()
print('Token owner:', me['emailAddress'])

# Method 2: Try accessing another user — the error message reveals the owner
try:
    svc.users().getProfile(userId='ndr@draas.com').execute()
except Exception as e:
    # Error says: 'Delegation denied for <actual_owner>'
    print('Delegation check:', str(e))
"
```

The tokeninfo endpoint (`https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=...`) does NOT reveal the user — it only shows client_id and scopes.

## Current account mappings (gws_auth.EMAIL_TO_SERVICE)

- `ndr@draas.com`, `psingh@draas.com`, `rnr@draas.com`, `vkdas@draas.com`, `pm2.blr@draas.com`, `sales1.blr@draas.com` → `'google-draas'`
- `ndr@ahfl.in` → `'google-ahfl'`
- `nishantranka@gmail.com` → `'google-gmail'`

All @draas.com addresses share the same `google-draas` service key in the vault, but **each user has their own token** for that service. The service key is not a shared credential — it's just a label that maps to a specific Google Workspace org.
