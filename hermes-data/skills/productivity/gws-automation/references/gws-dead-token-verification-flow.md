# Dead Token Verification Flow

**Scenario:** User says they authorized an account. `has_token` returns True. `build_service` doesn't raise `FileNotFoundError`. But API calls fail.

## The Three-Step Chain

Step 1 — Vault check (fast, but NOT sufficient):
```
vault.list_services(uid)  → [list of services with token records]
vault.has_token(uid, svc) → True if record exists
```

Step 2 — build_service check:
```
build_service("gmail", "v1", service_name="google-ahfl")
```
Succeeds silently even with a dead token. No error.

Step 3 — Actual API call (the definitive test):
```
svc.users().getProfile(userId="me").execute()
```
This is where `RefreshError: invalid_grant` surfaces if the refresh token was revoked.

## Concrete Example (ahfl.in, Jul 2026)

```python
# Step 1: Vault check — PASSES
from tools.gws_vault_client import resolve, has_token, list_services

uid = resolve("telegram", "[REDACTED-TID]")
services = list_services(uid, session_uid=uid)
# → ['google-ahfl', 'google-draas', 'google-gmail', 'mcp-kelsa-read', 'vocab']

has_token(uid, "google-ahfl", session_uid=uid)
# → True

# Step 2: build_service — PASSES
from tools.gws_auth import build_service

svc = build_service("gmail", "v1", service_name="google-ahfl")
# → no error

# Step 3: API call — FAILS
svc.users().getProfile(userId="me").execute()
# → google.auth.exceptions.RefreshError:
#   ('invalid_grant: Token has been expired or revoked.',
#    {'error': 'invalid_grant', 'error_description': 'Token has been expired or revoked.'})
```

## Root Cause

- Access token expired (stale)
- Refresh token was revoked by Google
- Possible triggers: user revoked in Google Account settings, password changed, OAuth client recreated, token idle > 6 months

## The Only Fix

Generate a fresh OAuth URL and have the user re-authorize:

```python
# From terminal (not execute_code)
cd /opt/hermes && /opt/hermes/.venv/bin/python3 -c "
import sys; sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import get_auth_url
print(get_auth_url('TELEGRAM_ID', login_hint='ndr@ahfl.in'))
"
```

The new authorization overwrites the old token in the vault.
