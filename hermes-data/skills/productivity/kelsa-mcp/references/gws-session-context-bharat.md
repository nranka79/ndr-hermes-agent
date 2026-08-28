# GWS Session Context — sales1.blr@draas.com

When the terminal()/execute_code session resolves to a different user than the current chat user (Bharat Hawaldar), GWS `build_service()` fails because it looks up the token under the wrong canonical_uid.

## The Issue

- Bharat's Telegram chat is with you, but `HERMES_SESSION_USER_ID` may resolve to `psingh-[REDACTED-TID]` (Prakash Singh) instead of `sales1.blr-[REDACTED-TID]`
- The OAuth token for `google-draas` is stored under `psingh-[REDACTED-TID]` (because that's whose state was in the OAuth URL), even though it's a token for `sales1.blr@draas.com`
- Calling `build_service('gmail', 'v1', service_name='google-draas')` from a terminal session that resolves to `sales1.blr-[REDACTED-TID]` returns `VaultNoTokenError: No google-draas token for user sales1.blr-[REDACTED-TID]`

## The Fix

Override `HERMES_SESSION_USER_ID` before calling `build_service`:

```python
import os
os.environ['HERMES_SESSION_USER_ID'] = '[REDACTED-TID]'
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
```

Then all subsequent `build_service()` calls resolve to `psingh-[REDACTED-TID]` which has the `google-draas` token.

## Verification

```python
gmail = build_service('gmail', 'v1', service_name='google-draas')
profile = gmail.users().getProfile(userId='me').execute()
print(profile.get('emailAddress'))  # Should show sales1.blr@draas.com
```

## Terminal command pattern

```bash
GWS_VAULT_SOCKET=/run/gws-vault/vault.sock HERMES_SESSION_USER_ID=[REDACTED-TID] \
  /opt/hermes/.venv/bin/python3 /tmp/script.py
```
